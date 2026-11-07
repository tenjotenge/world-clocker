# Active Tasks

## 1. Collect the first full matched real-model pair

**Status** Open. Start with Qwen2.5-Coder 7B Q3_K_M and Q5_K_M, which each produced
16 valid decisions in the compact screen. Confirm exact IDs and runtime settings
on the new host, then use the same v0.3 config for both checkpoints. Measure
throughput in a bounded batch before budgeting all 24,000 responses.

**Done when** Both runs finish, coverage gates pass or failures are documented,
and a matched report gives raw metrics, weak repertoire, and population status.
Repeat the pair before interpreting a small separation.

## 2. Resolve readiness blockers separately

**Status** Open. Investigate response formatting for Mistral and MythoMax,
answer availability for GLM, and memory or a smaller artifact for Qwen3-Coder
30B. Compare any changed parsing or generation budget as a labeled condition.
Keep original strict results available.

## 3. Test generalization before recalibration

**Status** Deferred pending full data. Add matched 7B-9B generation comparisons
once the initial pair is reliable. Candidate checkpoints discussed were Llama 2
7B Chat, the existing Qwen2.5-Coder 7B, and Qwen3.5 9B. Llama 3.1 8B Instruct is
an optional general-instruction comparison. Use the same quantization class
where possible and verify availability on the new host. Training, architecture,
and specialization can confound a comparison by release date.
Compare independently repeated runs and probe families before deciding whether
the population mapping needs revision.
