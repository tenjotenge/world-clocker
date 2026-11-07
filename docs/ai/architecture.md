# Architecture for Contributors

The [main architecture document](../architecture.md) owns the runtime and
persistence specification. Use the [repo index](repo_index.md) for file locations.

## Pipeline

1. The CLI validates a YAML definition and resolves the provider model ID.
2. The probe planner generates a deterministic trial plan. The runner snapshots it
   in SQLite and stores a terminal record for each trial.
3. Metrics consume persisted, canonical decisions. The provider is unnecessary
   for offline analysis.
4. The profile layer applies repertoire and evidence gates, then maps an eligible
   weak repertoire through the selected calibration and city catalog.
5. Reports and exports expose the raw metrics, score versions, coverage, and
   warnings together.

Preserve the separation between inference, measurement, and calibration. A
report-time calibration override leaves the run manifest and decisions intact.
