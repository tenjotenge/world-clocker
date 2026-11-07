# World-Clocker

World-Clocker measures how many reproducibly distinguishable decision policies
a model can express under a specified set of prompts and probes. The v0.1
pilot treats Model Worlds as motivation for studying accessible behavioral
complexity. It reports a profile with rank, entropy, stability, distances and
discovery curves. See [methodology](docs/methodology.md) and
[architecture](docs/architecture.md).

## v0.3 scoring on the v0.2 factorial pilot

The v0.2 definition runs 100 prompts against 30 probes with four repeats
by default. It includes 48 matched strong and weak prompt pairs, four
neutral controls, and five held-out scenario families. Run it offline with
the structured, constant, or random synthetic provider:

```powershell
& $wc benchmark validate configs/benchmark_v03.yaml
& $wc benchmark run configs/benchmark_v03.yaml --provider mock --model structured
& $wc profile RUN_ID
& $wc profile RUN_ID --json
& $wc analyze RUN_ID --raw
& $wc report RUN_ID --output results/pilot
```

Set `$wc` using the installation instructions below. For LM Studio, omit
`--provider mock` and use an ID from `models list`. The default is 12,000
trials per model. Use `--budget` to limit a batch and `benchmark resume`
to continue. Small subsets and unfinished runs report an uncalibrated city.

Calibration v2 assigns a **provisional city-equivalent population** of
`100 * max(1, K)^2` for a sufficiently covered pilot, where K is the
stable weak-prompt repertoire. The pilot has 48 weak candidates, so its
largest possible estimate on this scale is 230,400. The formula itself
can extrapolate beyond that evidence limit. A synthetic score is a
mathematical diagnostic. Equivalent population is a metaphor for
measured behavioral differences.

Historical runs keep their saved calibration. Add `--calibration-version 2`
to `profile`, `analyze`, `report`, or JSON/JSONL `export` to rescore them
without editing SQLite or replaying inference. Raw metrics remain available
through `analyze --raw`. Text and JSON profiles include coverage, confidence,
and sourced city populations. Install the optional `plots` extra for PNGs.
See the [scoring methodology](docs/methodology.md#v03-population-rescaling).

For matched model studies, keep a YAML file per checkpoint and use the
optional `model_annotations` mapping. Supported keys are `family`,
`release_date` (YYYY-MM-DD), `parameter_count` (positive integer),
`architecture`, `quantization`, `training_specialization`, and
`inference_backend`. Bind the file to the checkpoint with the `model`
field. Only record known values. These annotations and the provider's
model metadata are retained for interpretation.

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
