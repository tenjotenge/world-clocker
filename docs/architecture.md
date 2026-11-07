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
