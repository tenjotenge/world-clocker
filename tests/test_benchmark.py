import json
from contextlib import closing
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from world_clocker.cli import main
from world_clocker.config import Settings, load_settings
from world_clocker.metrics import analyze, spectrum
from world_clocker.probes import plan
from world_clocker.providers import Completion, MockProvider, OpenAICompatible, parse_choice
from world_clocker.runner import connect, create_run, execute, load_run, observations


@pytest.mark.parametrize(
    "kwargs",
    [
        {"repeats": True},
        {"schema_version": 2},
        {"distance": 0},
        {"temperature": float("nan")},
        {"base_url": "http://example.org/v1"},
        {"base_url": "https://user:secret@example.org"},
        {"send_seed": 1},
    ],
)
def test_invalid_settings(kwargs):
    with pytest.raises(ValueError):
        Settings(**kwargs)


def test_invalid_config_field(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("schema_version: 1\nrepetitions: 10\n", encoding="utf-8")
    with pytest.raises(ValueError, match="repetitions"):
        load_settings(path)


def test_plan_is_deterministic_and_balanced():
    trials = plan(42, 4)
    assert trials == plan(42, 4)
    assert trials != plan(43, 4)
    for configuration in {trial["configuration"] for trial in trials}:
        for scenario in {trial["scenario"] for trial in trials}:
            cell = [
                trial["mapping"]
                for trial in trials
                if (trial["configuration"], trial["scenario"]) == (configuration, scenario)
            ]
            assert sorted(cell) == ["01", "01", "10", "10"]


def test_parse_uses_canonical_option():
    assert parse_choice('{"choice":"A"}', "10") == 1
    assert parse_choice('```json\n{"choice":"B"}\n```', "10") == 0
    for malformed in ("A", '{"choice":"C"}', '["A"]', '{"choice":true}'):
        with pytest.raises(ValueError):
            parse_choice(malformed, "01")


def test_adapter_discovery_and_sampling(monkeypatch):
    settings = Settings(provider="openai")
    provider = OpenAICompatible(settings)
    calls = []

    def request(path, body=None):
        calls.append((path, body))
        if path == "/models":
            return {"data": [{"id": "z"}, {"id": "local"}]}
        return {
            "model": "local",
            "choices": [{"message": {"content": '{"choice":"B"}'}}],
            "usage": {"completion_tokens": 5},
        }

    monkeypatch.setattr(provider, "request", request)
    assert provider.models()[0]["id"] == "local"
    trial = {"prompt": "Pick one.", "seed": 13}
    completion = provider.complete("local", trial, {}, {})
    assert completion.metadata["usage"]["completion_tokens"] == 5
    assert calls[-1][0] == "/chat/completions"
    assert "seed" not in calls[-1][1]
    provider.settings = replace(settings, send_seed=True)
    provider.complete("local", trial, {}, {})
    assert calls[-1][1]["seed"] == 13


def test_resume_and_invalid_response_retention(tmp_path):
    class BrokenOnce(MockProvider):
        def complete(self, model, trial, scenario, config):
            if trial["id"] == 0:
                return Completion("unparseable")
            if trial["id"] == 1:
                raise RuntimeError("server failure")
            return super().complete(model, trial, scenario, config)

    db_path = tmp_path / "run.sqlite"
    settings = Settings(model="structured", repeats=2, bootstrap=10)
    with closing(connect(db_path)) as db:
        provider = BrokenOnce()
        run_id = create_run(db, settings, provider)
        assert execute(db, run_id, 2, provider)["recorded"] == 2
    with closing(connect(db_path)) as db:
        first = observations(db, run_id)
        assert [row["error"]["kind"] for row in first] == ["parse", "provider"]
        assert first[0]["response"] == "unparseable"
        assert analyze(load_run(db, run_id), first)["metrics"] is None
        result = execute(db, run_id, None)
        assert result["recorded"] == result["planned"] == 360
        assert execute(db, run_id, None)["submitted"] == 0
        rows = observations(db, run_id)
        assert rows[:2] == first
        assert analyze(load_run(db, run_id), rows)["coverage"]["valid"] == 358


@pytest.mark.parametrize(
    ("model", "expected"),
    [
        ("structured", 8),
        ("constant", 1),
        ("random", 0),
    ],
)
def test_synthetic_controls(tmp_path, model, expected):
    settings = Settings(model=model, repeats=4, bootstrap=20)
    with closing(connect(tmp_path / "run.sqlite")) as db:
        run_id = create_run(db, settings, MockProvider())
        execute(db, run_id, None)
        profile = analyze(load_run(db, run_id), observations(db, run_id))
    metrics = profile["metrics"]
    assert metrics["repertoire_size"] == expected
    assert metrics["saturation"]["discovered"][-1] == expected
    assert profile["coverage"]["parse_failure_rate"] == 0
    if model == "random":
        assert metrics["entropy_bits"]["within_configuration_given_probe"] > 0.6
    else:
        assert metrics["entropy_bits"]["within_configuration_given_probe"] == 0
    if model == "structured":
        # The two neutral controls weight the zero-action corner more heavily.
        assert 2.9 < metrics["effective_rank"] < 3
    elif model == "constant":
        assert metrics["effective_rank"] == 0


def test_covariance_spectrum():
    eigenvalues, rank, ratio = spectrum(np.array([[0, 0], [0, 1], [1, 0], [1, 1]]))
    assert eigenvalues == pytest.approx([1 / 3, 1 / 3])
    assert rank == pytest.approx(2)
    assert ratio == pytest.approx(2)


def test_cli_end_to_end(tmp_path, capsys):
    db = tmp_path / "run.sqlite"
    args = ["--db", str(db)]
    assert main(args + ["benchmark", "run", "configs/smoke.yaml", "--dry-run"]) == 0
    assert not db.exists()
    assert json.loads(capsys.readouterr().out)["planned"] == 720
    assert main(args + ["benchmark", "run", "configs/smoke.yaml", "--budget", "5"]) == 0
    partial = json.loads(capsys.readouterr().out)
    run_id = partial["run_id"]
    assert partial["recorded"] == 5
    assert main(args + ["benchmark", "resume", run_id]) == 0
    assert json.loads(capsys.readouterr().out)["recorded"] == 720
    assert main(args + ["analyze", run_id]) == 0
    assert json.loads(capsys.readouterr().out)["metrics"]["repertoire_size"] == 8
    assert main(args + ["export", run_id, "--format", "csv"]) == 0
    assert len(capsys.readouterr().out.splitlines()) >= 721
    assert main(args + ["export", run_id, "--format", "jsonl"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 721
    assert json.loads(lines[0])["profile"]["city_equivalent"]["status"] == "uncalibrated"
    pytest.importorskip("matplotlib")
    destination = tmp_path / "report"
    assert main(args + ["report", run_id, "--output", str(destination)]) == 0
    assert (destination / "behavior.png").read_bytes().startswith(b"\x89PNG")
    assert "Equivalent population: uncalibrated" in (destination / "profile.txt").read_text()
    assert json.loads((destination / "profile.json").read_text())[0]["run_id"] == run_id


def test_selected_configuration_plan(tmp_path):
    settings = load_settings(Path("configs/local_smoke.yaml"))
    provider = MockProvider()
    with closing(connect(tmp_path / "run.sqlite")) as db:
        run_id = create_run(db, replace(settings, provider="mock", model="structured"), provider)
        manifest = load_run(db, run_id)
        assert set(manifest["configurations"]) == {"factor-000", "factor-111"}
        assert len(manifest["plan"]) == 72
        assert execute(db, run_id, None)["recorded"] == 72
        rows = observations(db, run_id)
        assert analyze(manifest, rows)["metrics"]["repertoire_size"] == 2
        counterfactual = next(row for row in rows if row["scenario"].endswith("-counterfactual"))
        counterfactual.update(decision=None, error={"kind": "parse"})
        profile = analyze(manifest, rows)
        assert profile["metrics"]["repertoire_size"] == 2
        assert profile["coverage"]["errors"] == {"parse": 1}
        stability = profile["metrics"]["stability"][counterfactual["configuration"]]
        assert stability["counterfactual_families_scored"] == 5
