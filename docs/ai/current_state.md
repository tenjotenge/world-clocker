# Current State

## Implemented

| Area | State |
|---|---|
| Package | v0.3.0, Python 3.11 or newer |
| Default research protocol | v0.2 factorial pilot, 100 configurations, 30 probes, four repeats |
| Population mapping | Calibration v2 through `benchmark_v03.yaml`. V1 remains available for historical runs. |
| Providers | Offline mock and OpenAI-compatible HTTP, tested against LM Studio |
| Persistence | Resumable SQLite with immutable manifests and terminal records |
| Output | Human profile, JSON/JSONL/CSV exports, static text/JSON and optional PNG |
| Last implementation verification | 28 local tests and four Windows/Linux CI jobs passed on `481a75f` |

## Evidence state

Three full synthetic controls verified stable weak repertoire counts of 32, 1,
and 0. Live Qwen smoke runs validated integration. The later matched inventory
screen attempted ten chat checkpoints and returned 97 valid decisions from
144 recorded responses. No full real-model factorial run or eligible real-model
population score has been recorded in this handoff.

The [experiment results](../experiment_results.md) distinguish response-format
failures, timeouts, a load block, and narrow-screen repertoire counts. The
tracked repository contains the summary. Raw run databases remain local.
