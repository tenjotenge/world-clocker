# Pitfalls

| Pitfall | Correct handling |
|---|---|
| LM Studio lists an embedding checkpoint next to chat models | Use chat-capable checkpoint IDs for decision probes. |
| A timeout or malformed reply looks like a zero score | Inspect coverage and terminal errors first. Missing decisions are missing evidence. |
| A small screen yields a stable repertoire of zero | Interpret it only over the tested prompts and scenarios. It does not estimate a model's complete repertoire. |
| A resumed worker appears absent in one shell | Check the actual worker and process command line before launching a replacement. Concurrent workers interfered with two screen runs. |
| A reasoning model exhausts the answer budget | Inspect finish reason, visible response, and reasoning token usage. Record larger-budget diagnostics separately. |
| Two profiles show the same city | Compare raw repertoire, thresholds, and coverage. City names are catalog matches and can hide numerical distinctions. |
| An order-sensitivity band is narrow | It reflects packing order on fixed observations. Independent repeated runs are needed to assess repeatability. |
| A run ID is copied to a fresh clone | Resume also requires the database containing that ID and a compatible provider with the named model. |
