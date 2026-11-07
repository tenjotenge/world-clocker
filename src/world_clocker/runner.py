import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import time
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from . import __version__
from .config import Settings
from .pilot import probe_bank
from .probes import plan
from .providers import Provider, parse_choice, provider_for


def now() -> str:
    return datetime.now(UTC).isoformat()


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def revision() -> str | None:
    package = Path(__file__).resolve().parent
    if package.parent.name != "src" or not (package.parent.parent / "pyproject.toml").is_file():
        return None
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=package,
            capture_output=True,
            text=True,
            check=True,
            timeout=2,
        )
        return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    try:
        version = db.execute("PRAGMA user_version").fetchone()[0]
        if version == 0:
            db.executescript("""
                BEGIN IMMEDIATE;
                CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, manifest TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS observations (
                    run_id TEXT NOT NULL REFERENCES runs(id),
                    trial_id INTEGER NOT NULL,
                    record TEXT NOT NULL,
                    PRIMARY KEY (run_id, trial_id)
                );
                PRAGMA user_version = 1;
                COMMIT;
            """)
        elif version != 1:
            raise ValueError(f"Unsupported database schema {version}")
    except Exception:
        db.close()
        raise
    return db


def create_run(db: sqlite3.Connection, settings: Settings, provider: Provider) -> str:
    available = provider.models()
    model = settings.model
    if model is None:
        if len(available) != 1:
            raise ValueError("Set model explicitly unless the endpoint lists exactly one model")
        model = available[0]["id"]
    metadata = next((item for item in available if item["id"] == model), None)
    if metadata is None:
        raise ValueError(f"Model {model!r} is absent from the provider model list")
    run_id = uuid4().hex
    trials = plan(settings.seed, settings.repeats, settings.configuration_ids, settings.benchmark)
    candidates, probes = probe_bank(settings.benchmark)
    scenario_bank = {item.id: asdict(item) for item in probes}
    selected = {trial["configuration"] for trial in trials}
    configs = {item.id: asdict(item) for item in candidates if item.id in selected}
    protocol_version = 2 if settings.benchmark == "0.2.0" else 1
    manifest = {
        "run_id": run_id,
        "schema_version": 1,
        "created_at": now(),
        "benchmark_version": settings.benchmark,
        "package_version": __version__,
        "git_revision": revision(),
        "code_hash": digest(
            {
                path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in Path(__file__).parent.glob("*.py")
            }
        ),
        "python_version": sys.version.split()[0],
        "scenario_version": protocol_version,
        "generator_version": protocol_version,
        "prompt_version": protocol_version,
        "parser_version": 1,
        "scenario_hash": digest(scenario_bank),
        "generator_hash": digest(configs),
        "model": model,
        "model_metadata": metadata,
        "settings": asdict(settings),
        "capabilities": {
            "json_mode": "prompt-only",
            "seed": (
                "synthetic"
                if settings.provider == "mock"
                else "requested, unverified"
                if settings.send_seed
                else "omitted"
            ),
            "token_usage": "when returned",
        },
        "scenarios": scenario_bank,
        "configurations": configs,
        "plan": trials,
        "plan_hash": digest(trials),
    }
    with db:
        db.execute("INSERT INTO runs VALUES (?, ?)", (run_id, json.dumps(manifest)))
    return run_id


def load_run(db: sqlite3.Connection, run_id: str) -> dict:
    row = db.execute("SELECT manifest FROM runs WHERE id = ?", (run_id,)).fetchone()
    if row is None:
        raise ValueError(f"Unknown run {run_id}")
    return json.loads(row[0])


def observations(db: sqlite3.Connection, run_id: str) -> list[dict]:
    rows = db.execute(
        "SELECT record FROM observations WHERE run_id = ? ORDER BY trial_id",
        (run_id,),
    )
    return [json.loads(row[0]) for row in rows]


def evaluate(provider: Provider, manifest: dict, trial: dict) -> dict:
    record = {
        **trial,
        "schema_version": 1,
        "run_id": manifest["run_id"],
        "model": manifest["model"],
        "started_at": now(),
        "response": None,
        "decision": None,
        "error": None,
        "metadata": {},
    }
    started = time.perf_counter()
    try:
        completion = provider.complete(
            manifest["model"],
            trial,
            manifest["scenarios"][trial["scenario"]],
            manifest["configurations"][trial["configuration"]],
        )
        record.update(response=completion.text, metadata=completion.metadata)
    except (RuntimeError, OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        key = os.environ.get("WORLD_CLOCKER_API_KEY")
        message = str(exc)
        record["error"] = {
            "kind": "provider",
            "message": message.replace(key, "[redacted]") if key else message,
        }
    else:
        try:
            record["decision"] = parse_choice(completion.text, trial["mapping"])
        except ValueError as exc:
            record["error"] = {"kind": "parse", "message": str(exc)}
    record["latency_seconds"] = time.perf_counter() - started
    return record


def execute(
    db: sqlite3.Connection,
    run_id: str,
    budget: int | None,
    provider: Provider | None = None,
) -> dict:
    manifest = load_run(db, run_id)
    if manifest["parser_version"] != 1:
        raise ValueError("Run requires a different parser version")
    settings = Settings(**manifest["settings"])
    provider = provider if provider is not None else provider_for(settings)
    done = {
        row[0]
        for row in db.execute(
            "SELECT trial_id FROM observations WHERE run_id = ?",
            (run_id,),
        )
    }
    submitted = 0
    for trial in manifest["plan"]:
        if budget is not None and submitted >= budget:
            break
        if trial["id"] in done:
            continue
        with db:
            db.execute("BEGIN IMMEDIATE")
            args = (run_id, trial["id"])
            if db.execute(
                "SELECT 1 FROM observations WHERE run_id = ? AND trial_id = ?",
                args,
            ).fetchone():
                continue
            record = evaluate(provider, manifest, trial)
            db.execute("INSERT INTO observations VALUES (?, ?, ?)", (*args, json.dumps(record)))
            submitted += 1
    count = db.execute(
        "SELECT COUNT(*) FROM observations WHERE run_id = ?",
        (run_id,),
    ).fetchone()[0]
    return {
        "run_id": run_id,
        "submitted": submitted,
        "recorded": count,
        "planned": len(manifest["plan"]),
    }
