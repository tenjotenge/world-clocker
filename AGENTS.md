# World-Clocker Agent Guide

Start with [Context Bootstrap](docs/ai/context_bootstrap.md), then read
[Handoff Summary](docs/ai/handoff_summary.md) and [Active Tasks](docs/ai/active_tasks.md).
Use the [Repo Index](docs/ai/repo_index.md) to find implementation boundaries.

- Treat saved observations and manifests as research evidence. Preserve their
  provenance and keep raw metrics separate from the population interpretation.
- Verify the local provider, model ID, and intended budget before live inference.
  Use one executor per database and one live evaluation worker per local server.
- Run the offline checks in the [README](README.md) for code changes.
- Update the current state and evidence notes when a result or blocker changes.
  Keep machine-specific data, raw responses, and credentials out of Git.
