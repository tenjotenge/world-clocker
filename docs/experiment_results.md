# Experiment Results

## Verified software baselines

| Release | Commit | Evidence |
|---|---|---|
| v0.1 | `d633c38` | Offline controls and a 72-trial LM Studio smoke run |
| v0.2 | `0265f9b` | 26 local tests, four passing CI jobs, and three full synthetic controls |
| v0.3 | `481a75f` | 28 local tests and four passing CI jobs. Saved control raw analysis matched v0.2. |

The v0.1 Qwen2.5-Coder 7B Q4_K_M smoke run returned 71 valid decisions from
72 attempts. Both tested prompts passed the v0.1 stability gate. One
counterfactual response failed parsing. A later v0.2 Q4_K_M integration batch
parsed 12 of 12 responses, and v0.3 Q3_K_M and Q5_K_M checks parsed four of
four responses each. These were integration checks with uncalibrated city fields.

## Full synthetic controls

Each control completed 12,000 trials. The population column is a mathematical
diagnostic for the oracle. It does not represent real-model evidence.

| Control | Stable weak repertoire | v1 population | v2 population |
|---|---:|---:|---:|
| Structured | 32 | 3,947,280 | 102,400 |
| Constant | 1 | 500 | 100 |
| Random | 0 | 500 | 100 |

To recreate these controls, run `configs/benchmark_v03.yaml` with
`--provider mock --model structured`, then repeat with `constant` and `random`.
Use the same SQLite database to generate a matched static comparison.

## LM Studio inventory readiness screen

The final compact screen selected weak configurations `weak-00002` and
`weak-10002`, the base and paraphrase probes in the `equipment` discovery
and `shipment` held-out families, and repeat indices 0 and 1 from the v0.2
plan. That gives 16 planned responses per checkpoint. It used a 2,048-token
loaded context, the v0.3 configuration's 128-token completion cap, and at
most two concurrent requests. This one-off local screen used a targeted
subset. The normal `--budget 16` command selects a different prefix.

Nine chat checkpoints returned responses, yielding **97 valid decisions from
144 recorded attempts**. The tenth chat checkpoint failed to load. Nomic
Embed Text v1.5 was excluded because this protocol uses chat decisions.

| LM Studio checkpoint ID | Valid / recorded | Stable screen repertoire | Notes |
|---|---:|---:|---|
| `qwencoder2.5-7b@q3_k_m` | 16/16 | 1 | |
| `qwencoder2.5-7b@q4_k_m` | 16/16 | 0 | |
| `qwencoder2.5-7b@q5_k_m` | 16/16 | 0 | |
| `qwencoder2.5-14b@q3_k_m` | 12/16 | 0 | Four provider timeouts |
| `qwencoder2.5-14b@q4_k_m` | 16/16 | 0 | |
| `qwencoder2.5-14b@q5_k_m` | 14/16 | 0 | Two provider timeouts and duplicate worker overlap |
| `mythomax-l2-13b` | 4/16 | 0 | Ten parse failures and two timeouts |
| `mistral-small-3.1-24b-instruct-2503` | 3/16 | 0-1 | Thirteen parse failures and duplicate worker overlap |
| `glm-4.7-flash-reap-50_q4_k_m_gguf` | 0/16 | Undetermined | All 16 ran out of tokens with no visible answer |
| `qwen3-coder-30b-a3b-instruct-awq` | 0/0 | Unscorable | LM Studio blocked loading on retry, citing about 18.25 GB required |

Screen repertoire is bounded by two and describes only these risk cues. For
incomplete rows, the diagnostic enumerated possible binary completions of missing
decisions and reported the resulting repertoire bounds. A zero means no tested
prompt can meet the screen's stability gate given the observed decisions. It
cannot support a general ranking or an official city score.

Mistral had 11 parse failures with a single valid fenced JSON decision amid
prose. MythoMax gave the exact displayed A label or option in ten strict parse
failures, making response format and position bias worth checking separately.
GLM returned zero strict decisions in two follow-up requests at 512 tokens.
The larger-budget diagnostic and potential format recoveries were kept separate
from the matched screen. The duplicate worker was stopped and affected rows were
retained as operational evidence.

## Evidence still needed

No full real-model pilot or eligible real-model city-equivalent score was
produced. Calibration v2 remains in place. The first planned comparison is
a full matched pair of Qwen2.5-Coder 7B Q3_K_M and Q5_K_M. Repeat the pair
before interpreting a small difference. See [Active Tasks](ai/active_tasks.md).

For owners of the original machine, the final screen report, inventory,
and database were stored under `results/inventory-v03-compact/`. The saved
full synthetic runs used `results/pilot-v02.sqlite` and the v2 rescoring
report was in `results/v03-rescored/`. These paths are Git-ignored and may
be absent from a fresh clone. This document carries the verified summary.
