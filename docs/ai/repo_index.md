# Repo Index

| Path | Role |
|---|---|
| [README.md](../../README.md) | Quick start and current scoring overview |
| [AGENTS.md](../../AGENTS.md) | Repository-level instructions and onboarding links |
| [docs](../README.md) | Human reference and agent handoff docs |
| [configs](../../configs) | Historical, smoke, and current benchmark definitions |
| [cli.py](../../src/world_clocker/cli.py) | Validation, inference, resume, analysis, and export commands |
| [config.py](../../src/world_clocker/config.py) | Settings and provenance validation |
| [probes.py](../../src/world_clocker/probes.py), [pilot.py](../../src/world_clocker/pilot.py) | Prompt plans and v0.2 factorial bank |
| [providers.py](../../src/world_clocker/providers.py), [runner.py](../../src/world_clocker/runner.py) | Provider adapters, parser, and SQLite execution |
| [metrics.py](../../src/world_clocker/metrics.py) | Offline behavioral measurements |
| [profile.py](../../src/world_clocker/profile.py), [calibration.py](../../src/world_clocker/calibration.py) | Evidence gates, weak packing, population transform, and city matching |
| [reporting.py](../../src/world_clocker/reporting.py), [city data](../../src/world_clocker/data) | Static reports and versioned reference populations |
| [tests](../../tests), [CI workflow](../../.github/workflows/ci.yml) | Offline regression checks and build matrix |

`results/` is ignored. Treat everything under it as local evidence or a local
helper unless it has been explicitly moved into the tracked project.
