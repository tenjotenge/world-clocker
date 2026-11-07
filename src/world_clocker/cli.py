import argparse
import csv
import json
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

import yaml

from .config import Settings, load_settings
from .metrics import analyze
from .probes import plan
from .providers import provider_for
from .reporting import render
from .runner import connect, create_run, execute, load_run, observations


def positive(text: str) -> int:
    value = int(text)
    if value < 1:
        raise argparse.ArgumentTypeError("must be positive")
    return value


def print_json(data: object) -> None:
    print(json.dumps(data, indent=2, allow_nan=False))


def arguments(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="world-clocker")
    parser.add_argument("--db", type=Path, default=Path("results/world-clocker.sqlite"))
    commands = parser.add_subparsers(dest="command", required=True)
    doctor = commands.add_parser("doctor")
    doctor.add_argument("--config", type=Path)
    models = commands.add_parser("models").add_subparsers(dest="action", required=True)
    models.add_parser("list").add_argument("--config", type=Path)
    benchmark = commands.add_parser("benchmark").add_subparsers(dest="action", required=True)
    benchmark.add_parser("validate").add_argument("config", type=Path)
    run = benchmark.add_parser("run")
    run.add_argument("config", type=Path)
    run.add_argument("--dry-run", action="store_true")
    run.add_argument("--budget", type=positive)
    run.add_argument("--model")
    resume = benchmark.add_parser("resume")
    resume.add_argument("run_id")
    resume.add_argument("--budget", type=positive)
    commands.add_parser("analyze").add_argument("run_id")
    export = commands.add_parser("export")
    export.add_argument("run_id")
    export.add_argument("--format", choices=("json", "jsonl", "csv"), default="json")
    report = commands.add_parser("report")
    report.add_argument("run_ids", nargs="+")
    report.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def export_rows(manifest: dict, rows: list[dict], mode: str) -> None:
    if mode == "json":
        print_json({"manifest": manifest, "observations": rows})
    elif mode == "jsonl":
        print(json.dumps({"type": "manifest", **manifest}))
        for row in rows:
            print(json.dumps({"type": "observation", **row}))
    else:
        fields = [
            "schema_version",
            "run_id",
            "id",
            "model",
            "configuration",
            "scenario",
            "repeat",
            "seed",
            "prompt",
            "mapping",
            "response",
            "decision",
            "error",
            "metadata",
            "started_at",
            "latency_seconds",
        ]
        writer = csv.DictWriter(sys.stdout, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                dict(row, error=json.dumps(row["error"]), metadata=json.dumps(row["metadata"]))
            )


def main(argv: list[str] | None = None) -> int:
    args = arguments(argv)
    try:
        if args.command in ("models", "doctor"):
            settings = load_settings(args.config) if args.config else Settings(provider="openai")
            models = provider_for(settings).models()
            if args.command == "doctor":
                import numpy

                ready = (
                    any(model["id"] == settings.model for model in models)
                    if settings.model
                    else len(models) == 1
                )
                print_json(
                    {
                        "ready": ready,
                        "numpy": numpy.__version__,
                        "sqlite": sqlite3.sqlite_version,
                        "models": models,
                        "detail": None if ready else "Select an available model in the config",
                    }
                )
                return 0 if ready else 1
            print_json(models)
            return 0

        if args.command == "benchmark" and args.action in ("validate", "run"):
            from dataclasses import replace

            settings = load_settings(args.config)
            if getattr(args, "model", None):
                settings = replace(settings, model=args.model)
            if args.action == "validate" or args.dry_run:
                print_json(
                    {
                        "valid": True,
                        "planned": len(
                            plan(settings.seed, settings.repeats, settings.configuration_ids)
                        ),
                    }
                )
                return 0
            provider = provider_for(settings)
            with closing(connect(args.db)) as db:
                run_id = create_run(db, settings, provider)
                print(f"Run ID {run_id}", file=sys.stderr, flush=True)
                print_json(execute(db, run_id, args.budget, provider))
            return 0

        if not args.db.is_file():
            raise ValueError(f"Database does not exist: {args.db}")
        with closing(connect(args.db)) as db:
            if args.command == "benchmark":
                print_json(execute(db, args.run_id, args.budget))
            elif args.command == "report":
                manifests = [load_run(db, run_id) for run_id in args.run_ids]
                reports = [analyze(item, observations(db, item["run_id"])) for item in manifests]
                render(reports, manifests, args.output)
                print_json({"output": str(args.output)})
            else:
                manifest = load_run(db, args.run_id)
                rows = observations(db, args.run_id)
                if args.command == "export":
                    export_rows(manifest, rows, args.format)
                else:
                    print_json(analyze(manifest, rows))
        return 0
    except (
        ValueError,
        OSError,
        RuntimeError,
        sqlite3.Error,
        yaml.YAMLError,
        KeyError,
        TypeError,
        AttributeError,
    ) as exc:
        print(f"world-clocker: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Interrupted. Resume using the run ID printed at startup.", file=sys.stderr)
        return 130
