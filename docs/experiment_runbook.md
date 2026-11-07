# Experiment Runbook

## Fresh machine

Install Python 3.11 or newer and follow the [README](../README.md#offline-smoke-test).
The smoke test uses a mock provider. The optional plots extra adds PNG rendering.
On Linux or macOS, install with `.venv/bin/python -m pip install ".[dev,plots]"`
and invoke `.venv/bin/world-clocker` in place of the PowerShell variable below.

For live inference, start the LM Studio local server and confirm that it exposes
a chat-capable model on the OpenAI-compatible endpoint. The default is
`http://localhost:1234/v1`. Set `base_url` in the YAML definition when using
another server. Supply `WORLD_CLOCKER_API_KEY` through the environment when
authentication is needed. Model IDs and available memory vary by machine.

```powershell
& $wc models list --config configs/benchmark_v03.yaml
& $wc benchmark validate configs/benchmark_v03.yaml
& $wc benchmark run configs/benchmark_v03.yaml --dry-run
```

The dry run should report 12,000 planned trials. For `doctor` on a server with
multiple models, set `model` in the configuration first.

For the original 72-trial live smoke protocol, run
`benchmark run configs/local_smoke.yaml --model "MODEL_ID"`. That v0.1
definition is useful for integration checks and leaves population uncalibrated.

## Matched live runs

Use the same backend policy, plan seed, repeats, sampling, token budget, parsing,
and scoring settings across the comparison. Record the checkpoint's exact ID,
artifact and quantization, backend version, context length, and concurrency
when available. Capture model-specific details in a local YAML copy using
`model_annotations`. Supported keys are `family`, `release_date` (YYYY-MM-DD),
`parameter_count` (positive integer), `architecture`, `quantization`,
`training_specialization`, and `inference_backend`. Set `model` in that
copy to bind the annotations to the correct checkpoint. The previous inventory IDs are recorded in
[Experiment Results](experiment_results.md).

Run one worker at a time on the local server. In PowerShell, set each model ID
to one returned by discovery. Run the second checkpoint after finishing the first.

```powershell
$db = "results/qwen7b-matched.sqlite"
& $wc --db $db benchmark run configs/benchmark_v03.yaml --model "MODEL_ID" --budget 32
& $wc --db $db profile RUN_ID
& $wc --db $db benchmark resume RUN_ID --budget 500
& $wc --db $db benchmark resume RUN_ID
```

Replace `RUN_ID` with the printed ID. A run without a budget attempts every
pending trial. Budget counts terminal trials. Measure the first batch's
throughput before scheduling the entire pair, which totals 24,000 trials.
A bounded prefix is useful for timing and parsing checks and will usually
lack complete probe cells. The historical inventory screen used a targeted
subset instead of the randomized prefix.

After both runs finish:

```powershell
& $wc --db $db analyze RUN_A --raw
& $wc --db $db profile RUN_A --json
& $wc --db $db report RUN_A RUN_B --output results/qwen7b-matched
& $wc --db $db export RUN_A --format jsonl
```

Compare only compatible runs. Inspect parse errors and coverage before
interpreting repertoire differences. A historical run keeps its saved
calibration unless `--calibration-version 2` is explicitly supplied to a
profile, analysis, report, or JSON/JSONL export command.

## Restart and move between machines

1. Stop the current worker before copying or resuming the run. Confirm that an
   earlier background worker is actually gone before starting a replacement.
2. Copy the SQLite database using a clean shutdown or SQLite's backup API. Avoid
   copying an open main database file while ignoring active journal sidecars.
3. Keep a copy of the relevant Git commit, config, model ID and artifact
   details, plus backend settings. Store raw responses and database files in
   private experiment storage outside Git.
4. On the destination machine, verify that the database and run ID are available
   using `profile`. Resume with the same `--db` and run ID after verifying the
   saved endpoint and checkpoint are reachable. Existing manifests are immutable.
   If the stored endpoint or model cannot be reproduced, start a separately
   labeled run and document the difference.
5. Resume skips terminal records, including failures. Retry a changed parser,
   model configuration, or token budget in a separate diagnostic or run.

Offline profiles work without LM Studio. JSON and JSONL exports carry provenance
for auditing. Use SQLite for direct resume. Without the original database, use
the tracked summary for context and start a fresh run.

## Common failures

| Symptom | First check |
|---|---|
| Connection refused after a restart | Start the LM Studio server and run model discovery. |
| Load fails before a response | Capture the provider message and check model fit. Respect load guardrails. |
| Many timeouts | Verify there is one worker, then check memory, context length, and request concurrency. |
| Empty visible answer with a length finish | Inspect reasoning-token use. Try a separately labeled budget diagnostic. |
| Reply contains a choice inside prose | Keep the raw response and original parse failure. Audit recoverable formats separately. |
