# Decision Log

| Baseline | Decision | Rationale and consequence |
|---|---|---|
| `d633c38`, v0.1 | Begin with controlled binary decisions, a mock provider, and resumable SQLite | The basic pipeline could be tested without a GPU. Paired wording and repeat probes separate some decision stability from formatting. |
| `0265f9b`, v0.2 | Expand to a 100-configuration factorial design and score the stable weak repertoire | Strong prompts and neutral controls diagnose steering. Rank and entropy remain descriptive and do not raise the population estimate. |
| `481a75f`, v0.3 | Replace the default research config's v1 exponential mapping with the v2 quadratic mapping | A structured oracle with 32 policies mapped to 3,947,280 under v1. That result demonstrated the arbitrary scale. V2 maps 32 to 102,400 and preserves v1 for historical reports. |
| Local inventory screen | Leave population calibration unchanged | The two-prompt screen identified readiness problems and did not produce eligible real-model profiles. |
| Repository handoff | Track summaries and procedures, keep raw runs portable outside Git | A fresh clone can recover context without publishing raw responses or depending on host-specific paths. |

See [Methodology](../methodology.md) for exact formulas, gates, and uncertainty.
