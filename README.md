# World-Clocker

World-Clocker measures how many reproducibly distinguishable decision policies
a model can express under a specified set of prompts and probes. The v0.1
pilot treats Model Worlds as motivation for studying accessible behavioral
complexity. It reports a profile with rank, entropy, stability, distances and
discovery curves. See [methodology](docs/methodology.md) and
[architecture](docs/architecture.md).

## Offline smoke test

Python 3.11 or newer is required. From the repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install ".[dev,plots]"
$wc = ".\.venv\Scripts\world-clocker.exe"
& $wc benchmark run configs/smoke.yaml
& $wc analyze RUN_ID
& $wc report RUN_ID --output results/smoke
.\.venv\Scripts\python.exe -m pytest
```

Replace `RUN_ID` with the printed ID. Run with `--model constant` or
`--model random` for synthetic controls. Provide both run IDs to `report`
to overlay spectra, discovery curves and stability distributions for matched runs.

## LM Studio

Start the local API server in LM Studio and load a model. Discover model IDs
and check connectivity, then try a 72-trial smoke run:

```powershell
& $wc models list
& $wc doctor --config configs/benchmark_v01.yaml
& $wc benchmark run configs/benchmark_v01.yaml --dry-run
& $wc benchmark run configs/local_smoke.yaml --model "MODEL_ID" --budget 12
& $wc benchmark resume RUN_ID
& $wc analyze RUN_ID
& $wc export RUN_ID --format jsonl
```

The local smoke config uses two opposing prompts and two repeats. Use
`configs/benchmark_v01.yaml` for the full factorial pilot.

Set `model` in YAML or pass `--model` when multiple models are listed. For
another compatible endpoint, set `base_url` in YAML and pass that file via
`--config` to discovery and readiness commands. Authenticated endpoints use
the `WORLD_CLOCKER_API_KEY` environment variable. Use a separate database via
the global `--db` option when isolating experiments.

The budget counts terminal trials, with up to the configured retries per
trial. Completed and failed records are retained on resume. Export JSON
or JSONL for full provenance and CSV for tabular inspection. Raw responses
are untrusted research data. If using a spreadsheet, import text columns as text.
The database and generated reports default to the Git-ignored results directory.
