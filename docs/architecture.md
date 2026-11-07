# Architecture

The CLI validates a versioned YAML definition and resolves a model through the
provider interface. The probe module generates a deterministic prompt plan
independent of the provider. The runner snapshots that plan and its provenance
in SQLite before sending sequential requests. Each result is committed separately.
Analysis consumes stored canonical decisions and can run without a server.

The v1 definition has flat settings for provider, model, seed, sampling, repeats
and scoring thresholds. The v1 database has immutable run manifests and terminal
observations keyed by run and trial. A manifest contains the full prompt plan,
probe metadata, model metadata, code versions and a plan hash. Observation
records include raw text, presented-label mapping (via the manifest), canonical
action, timestamps, timing, returned model metadata and any errors.

Providers implement discovery and one completion method. New generators and
probes can produce the same typed configuration and scenario records. Metrics
consume the manifest and observation mappings. Run one executor per database.
SQLite holds a write reservation during each request to prevent concurrent
executors from submitting the same planned trial. An interruption after an HTTP
request but before commit can replay that request.

Population scoring is a report-layer transform. The analyzer produces
behavioral metrics from stored decisions. The profile layer applies the
existing stable weak-prompt packing rule, then hands only the repertoire
count to the selected calibration. City matching follows the population
transform and uses its versioned reference catalog. Calibration v1 keeps
catalog v1, while calibration v2 adds London through catalog v2.

The v0.3 package uses the existing v0.2 benchmark protocol. New runs
created with the v0.3 configuration snapshot calibration v2. Older
manifests resolve to their saved settings, defaulting to v1 when the
calibration is absent. An explicit report-time override leaves the
database and raw metrics intact. Comparison reports require the same
protocol, sampling conditions, metric versions, and calibration.
Optional model annotations live in the run manifest alongside provider
metadata and sampling settings. They never enter the scoring transform.
