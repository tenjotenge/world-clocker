# World-Clocker

World-Clocker measures how many reproducibly distinguishable decision policies
a model expresses on controlled probes. It reports behavioral rank, entropy,
stability, distances, and repertoire alongside a provisional city-equivalent
population index.

**Current baseline** v0.3.0 uses the v0.2 factorial protocol with 100
configurations, 30 probes, and four repeats. The default research run is
12,000 trials per checkpoint. The three full synthetic controls passed.
Live LM Studio screens established integration and exposed readiness issues.
Full real-model profiles are still pending.

## Offline smoke test

Python 3.11 or newer is required. From the repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install ".[dev,plots]"
$wc = ".\.venv\Scripts\world-clocker.exe"
& $wc benchmark run configs/smoke.yaml
& $wc profile RUN_ID
& $wc report RUN_ID --output results/smoke
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .
```

Replace `RUN_ID` with the ID returned by the run. This test uses the mock
provider. The `plots` extra is optional. The [runbook](docs/experiment_runbook.md)
covers other shells and moving experiments to another machine.

## Run the factorial pilot

Validate the definition, then run a full synthetic control or a bounded
live batch:

```powershell
& $wc benchmark validate configs/benchmark_v03.yaml
& $wc benchmark run configs/benchmark_v03.yaml --provider mock --model structured
& $wc models list --config configs/benchmark_v03.yaml
& $wc benchmark run configs/benchmark_v03.yaml --model "MODEL_ID" --budget 32
& $wc benchmark resume RUN_ID --budget 500
```

Start LM Studio's local server before live inference. Replace `MODEL_ID` with a
chat-capable ID from discovery. Use `--db` before the subcommand to choose a
database. Resume uses the saved run manifest and skips terminal records,
including failures. See the [runbook](docs/experiment_runbook.md) for matched
runs, recovery, export, and model annotations.

## Read a profile

```powershell
& $wc profile RUN_ID
& $wc analyze RUN_ID --raw
& $wc profile RUN_ID --json --calibration-version 2
& $wc report RUN_A RUN_B --output results/comparison
```

Calibration v2 maps the stable weak-prompt repertoire `K` to
`100 * max(1, K)^2` when the evidence gates pass. The current 48 weak
candidates give a pilot ceiling of 230,400. The mapping can extrapolate
if a future protocol measures larger repertoires. Population is an
illustrative metaphor. Smoke tests remain uncalibrated and synthetic scores
are mathematical diagnostics.

Historical runs keep their saved calibration. The report-time override
rescales without replaying inference. Raw metrics remain available
independently. See [Methodology](docs/methodology.md) for the gates and
the scope of the packing-order interval.

## Documentation and handoff

- [Documentation index](docs/README.md) for the source map and reference docs.
- [Experiment results](docs/experiment_results.md) for control values, the
  installed-model screen, and the evidence still needed.
- [Agent guide](AGENTS.md) and [handoff summary](docs/ai/handoff_summary.md)
  for picking up development from a fresh clone.

Git tracks code, configs, and evidence summaries. SQLite databases, raw
responses, and generated reports are local under the ignored `results/`
directory. Transfer them separately to resume a specific run.
