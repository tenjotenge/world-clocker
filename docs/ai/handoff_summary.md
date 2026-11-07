# Handoff Summary

## Project baseline

The implementation baseline is `481a75f`. It preserves the v0.2 experiment and
revises the population transform in v0.3. The repository can be cloned and tested
with the mock provider on a machine without LM Studio or model weights.

## Last completed work

- Built the resumable CLI, measurement pipeline, versioned profile, and city catalog.
- Verified the factorial design against structured, constant, and random controls.
- Confirmed identical raw analysis on the saved controls after changing calibration.
- Completed the compact LM Studio inventory screen after resuming from SQLite.
  A duplicate worker briefly overlapped with the 14B Q5 and Mistral runs and was stopped.
- Kept calibration v2 unchanged because the live screen was too narrow and several
  checkpoints failed readiness checks.

## Pick up here

Start with [Active Tasks](active_tasks.md). Use the [runbook](../experiment_runbook.md)
to set up a fresh clone, recover local data if available, and launch a full matched
Qwen 7B quantization pair in bounded batches. The
[results record](../experiment_results.md) preserves the evidence even if the
original machine and its SQLite files are unavailable.
