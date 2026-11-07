# Conventions

## Implementation

- Keep provider calls in the inference layer and numeric estimators in the offline
  layer. Add metadata to the manifest rather than using it as a scoring input.
- Give scoring and catalog changes explicit versions. Preserve historical defaults
  and compatibility with existing runs.
- Use deterministic fixtures for new metric tests. CI must remain runnable without
  a GPU, LM Studio, or paid endpoint.
- Keep scope focused. Record the reason for consequential changes in the
  [decision log](decision_log.md).

## Evidence and handoff

- Use exact checkpoint IDs and record backend, artifact, quantization, sampling,
  context, and concurrency when known.
- Keep failures and missing coverage visible. Label controls, smoke tests, and
  diagnostic reruns separately from eligible model profiles.
- Run Ruff checks, formatting verification, and pytest for code changes.
- Update [Current State](current_state.md), [Active Tasks](active_tasks.md), and
  the [results record](../experiment_results.md) when evidence changes.
