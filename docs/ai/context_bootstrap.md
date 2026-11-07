# Context Bootstrap

## Required reading order

1. [README](../../README.md) for purpose, setup, and the default benchmark.
2. [Handoff Summary](handoff_summary.md) and [Current State](current_state.md)
   for the latest implementation and experimental status.
3. [Architecture](architecture.md) and [Repo Index](repo_index.md) before
   changing a module.
4. [Methodology](../methodology.md) before changing a probe, metric, gate, or
   calibration.
5. [Experiment Runbook](../experiment_runbook.md) and [Active Tasks](active_tasks.md)
   before collecting more responses.

## First checks in a new clone

Check the Git branch and worktree. Install Python dependencies and run the offline
smoke test. Run model discovery before relying on any previously observed checkpoint
ID. Check whether a copied SQLite database contains the relevant run IDs before
trying to resume. The Git history includes the implementation and evidence summaries.
Local databases and one-off screen drivers require a separate transfer.
