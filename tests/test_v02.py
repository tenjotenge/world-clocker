from contextlib import closing
from dataclasses import replace
from pathlib import Path

import pytest

from world_clocker.calibration import Calibration
from world_clocker.cli import main
from world_clocker.config import Settings, load_settings
from world_clocker.metrics import analyze
from world_clocker.pilot import probe_bank
from world_clocker.profile import capacity_profile, closest_city, condition_repertoire
from world_clocker.providers import MockProvider
from world_clocker.reporting import render
from world_clocker.runner import connect, create_run, evaluate, execute, load_run


@pytest.fixture(scope="module")
def pilot():
    settings = load_settings(Path("configs/benchmark_v02.yaml"))
    settings = replace(settings, provider="mock", model="structured", bootstrap=8)
    with closing(connect(Path(":memory:"))) as db:
        run = create_run(db, settings, MockProvider())
        yield load_run(db, run)


def test_factorial_protocol(pilot):
    configs, scenarios = probe_bank("0.2.0")
    assert len(pilot["plan"]) == 12_000
    assert len({config.id for config in configs}) == 100
    assert len({scenario.id for scenario in scenarios}) == 30
    for source in ("strong", "weak"):
        group = [config for config in configs if config.source == source]
        assert len({config.factors for config in group}) == len(group) == 48
        assert len({config.priorities for config in group}) == 48
    assert {scenario.axis for scenario in scenarios if scenario.split == "heldout"} == set(range(5))
    assert len([config for config in configs if config.source == "neutral"]) == 4


@pytest.mark.parametrize(
    ("model", "expected"), [("structured", 32), ("constant", 1), ("random", 0)]
)
def test_full_pilot_controls(pilot, model, expected):
    manifest = dict(pilot, model=model, model_metadata={"id": model, "version": "1"})
    configs = manifest["configurations"]
    rows = [evaluate(MockProvider(), manifest, trial) for trial in manifest["plan"]]
    # A single missing primary response is allowed when both halves remain represented.
    if model == "structured":
        row = next(item for item in rows if configs[item["configuration"]]["source"] == "weak")
        row.update(decision=None, error={"kind": "parse"})
    profile = capacity_profile(manifest, rows)
    score = profile["city_equivalent"]
    assert score["status"] == "provisional"
    assert score["confidence"] == "synthetic-control"
    assert score["condition_diagnostics"]["weak"]["stable_repertoire"] == expected
    assert score["equivalent_population"] == Calibration().population(expected)
    assert profile["metrics"]["saturation"]["discovered"][-1] == expected
    assert profile["metrics"]["saturation"]["candidates"][-1] == 100
    if model == "random":
        assert profile["metrics"]["effective_rank"] > 5
    elif model == "structured":
        assert 4 < profile["metrics"]["effective_rank"] <= 5
    else:
        assert profile["metrics"]["effective_rank"] == 0


def test_score_repertoire_deduplicates_and_ignores_unstable():
    metrics = {
        "configurations": ["a", "b", "b-copy", "random"],
        "repeat_half_probabilities": [
            [[[0]], [[0]]],
            [[[1]], [[1]]],
            [[[1]], [[1]]],
            [[[0.5]], [[0.5]]],
        ],
        "stability": {
            name: {"passes_gate": name != "random"} for name in ("a", "b", "b-copy", "random")
        },
    }
    distances = {("a", "b"): 1, ("a", "b-copy"): 1, ("b", "b-copy"): 0}
    pack, _ = condition_repertoire(metrics, set(metrics["configurations"]), distances, 0.2)
    assert pack == ["a", "b"]


def test_calibration_anchors_and_extrapolation():
    calibration = Calibration()
    assert calibration.population(0) == calibration.population(1) == 500
    assert calibration.population(40) == 40_000_000
    assert calibration.population(41) > 40_000_000
    assert (
        Calibration(
            minimum_population=100, reference_population=10_000, reference_repertoire=3
        ).population(2)
        == 1_000
    )
    with pytest.raises(ValueError):
        Calibration(version=2)
    with pytest.raises(ValueError):
        Calibration(reference_repertoire=1)


def test_city_matching_is_logarithmic():
    entries = [
        {"population": 100, "city": "A", "country": "A"},
        {"population": 1_000, "city": "B", "country": "B"},
    ]
    assert closest_city(400, entries)["city"] == "B"


def test_small_and_incomplete_profiles_are_uncalibrated(tmp_path, pilot, capsys):
    db_path = tmp_path / "test.sqlite"
    settings = Settings(
        model="structured", configuration_ids=("factor-000", "factor-111"), repeats=2, bootstrap=4
    )
    with closing(connect(db_path)) as db:
        run_id = create_run(db, settings, MockProvider())
        execute(db, run_id, None)
        original = load_run(db, run_id)
    args = ["--db", str(db_path), "profile", run_id]
    assert main(args) == 0
    assert "Equivalent population: uncalibrated" in capsys.readouterr().out
    partial = capacity_profile(pilot, [])
    assert partial["city_equivalent"]["equivalent_population"] is None
    assert "city_equivalent" not in analyze(pilot, [])
    with pytest.raises(ValueError, match="Incompatible benchmark versions"):
        render([], [original, pilot], tmp_path / "report")
