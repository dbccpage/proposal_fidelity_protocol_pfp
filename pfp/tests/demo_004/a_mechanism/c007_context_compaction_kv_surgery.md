# C007: Context Compaction and KV-Prefix Surgery over Long Horizons

**AuthorityEffect:** None. **Status:** planned. **Domain:** a_mechanism. **Tier:** T2.
**Budget:** $0.50 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to keep
> host-verified accuracy at 30 or more turns while cutting processed tokens, by comparing host
> compaction, full history and KV-prefix reuse, for under $0.50.

## 2. Why This Task

Long Symbol Game sessions repeat the task statement and grow the history every turn. Three remedies are available: send everything (full history); let the host rewrite history into a typed state (compaction, U12); or keep the model's key-value cache for a fixed prefix and edit it (KV-prefix reuse and eviction, a Layer-1 operation on a local model). Each has a failure mode. Full history costs tokens and buries early constraints, which models use less well in the middle of long contexts (Liu et al. 2024). Compaction can drop a constraint the host did not know mattered. KV eviction changes what later tokens can attend to, much as a key mask does in [C001](c001_attention_distractor_mask_task_level.md).

Nothing in the estate measures these trade-offs at task level. The Paper 032 benchmark (`attention_entropy_kv_norm_benchmark.py`) measured KV-cache Frobenius energy and attention entropy for one prompt pair and found **higher** entropy and **higher** KV energy under the carrier prompt (0.4430 to 0.4785; 16.67 to 22.92 million), with different prompt lengths. It supports no claim that compact prompts make attention sparser. This challenge measures accuracy, cost and constraint retention directly. It stresses the Symbol Game turn loop, OEWAS (Omega Engine Workflows, Agents, Skills) working memory, and the OEEIS (Omega Engine Epistemic Immune System) principle that the host, not the model, is the record of what was agreed.

## 3. Formal Problem and Bounds

A session is a multi-stage repair task with constraints released over time. Stage j (1 ≤ j ≤ 6) adds a board fragment (new vertices, relations and claims) that shares vertices with earlier fragments, so early relations constrain later repairs. Sessions run 30 to 48 turns, including 6 to 10 host status turns with no new constraints. The final goal is an exact cochain on the union board (Φ₁ = 0) with no earlier relation modified unless the host marked it repairable.

Each declared constraint (relation, claim, repairable flag) gets an ID. **Constraint retention** at turn t is the fraction of declared IDs whose content is present in the model-visible context at t: in the text for text strategies; in unevicted KV positions for KV strategies. The host computes it from the bytes and positions it sent. **Constraint violation** is any proposal that changes a non-repairable relation.

Bounds: total board at most 40 vertices and 70 relations; claims |c_e| ≤ 999; cycle rank of the union at most 10. The hidden set must contain sessions whose only contradiction involves a stage-1 relation, sessions where a status turn restates a constraint with a typo (a schema-valid false restatement the model must not adopt), and sessions of 48 turns.

## 4. Deliverable and Output Contract

The frozen deliverable is `pipeline.json` (model, revision, tokenizer hash, context strategy and its parameters, compaction schema version, KV eviction policy, fuel, decoding) and `solve.py`, which plays one session and returns:

```json
{"status": "SOLVED", "final_cochain": {"s1:a->b": "4"}, "potential": {"a": "0", "b": "4"}, "violations": "0"}
{"status": "UNKNOWN", "refusal": "FUEL_EXHAUSTED", "phi1_final": "3", "violations": "1"}
```

`SOLVED` requires Φ₁ = 0 on the union board, a matching potential and zero violations. A session with Φ₁ = 0 reached by editing a non-repairable relation is incorrect.

## 5. Participant Packet

- `TASK.md` with the stage protocol, the repairable flag, the constraint-ID scheme and the retention definition.
- `examples/`: 8 public sessions (30 to 40 turns) with exact per-turn host messages and a reference solved transcript.
- `runner.py`, `accounting.json` (billed tokens, prefill tokens, cached tokens, wall-clock).

## 6. Judge Packet

- **Hidden base cases:** 40 sessions.
- **Relabel controls:** 12 sessions with renamed vertices and permuted stage order where the stages are independent.
- **Poisoned but schema-valid:** 10 sessions with a typo restatement in a status turn and 6 with a stage-1 relation that must be repaired late.
- **Exact checker:** Rust Φ₁ via `omega_symbol_game` and a replay of every admitted move against the declared constraints.
- **Independent second checker:** Python `Fraction` propagation plus an independent violation scanner over the transcript.
- **Checker mutation suite:** a final cochain that is exact but edits a non-repairable relation, a potential off by one, and a transcript whose violation count was edited.

## 7. Arms and Baselines

- **A: Symbol Game with host compaction.** History replaced each turn by the typed ledger (all declared constraints, current claims, open cycles, last two turns).
- **B: Full history.** Every prior turn verbatim.
- **C: Representation ablation.** A's ledger rendered as prose.
- **D: Repeated sampling.** Independent whole sessions under full history, cost-matched to A.
- **E: No-model baseline.** The exact repair of the final union board; the ceiling.
- **F: Local mechanism (treatment).** Local model with KV-prefix reuse: the system prompt and stage statements are cached once and never re-sent. Sub-arms: F-reuse (prefix cached, nothing evicted; its outputs must equal full recomputation token for token, an identity check of the cache code); F-evict (status and superseded turns evicted from the cache, positions kept with gaps); F-window (only the last W turns kept, a baseline known to lose constraints); F-sink (the first few tokens kept plus a recent window, as in StreamingLLM, Xiao et al. 2024).

## 8. Budget, Models and Provenance

Arms A to D run `qwen/qwen-2.5-7b-instruct` hosted through the governed path, replication `meta-llama/llama-3.1-8b-instruct`; the $0.50 ceiling per arm is enforced before each call by `BudgetController`. Arm F runs the local `Qwen/Qwen2.5-7B-Instruct` at a pinned revision; to compare F with A to D on the same weights, arms A and B are also run locally as A-local and B-local. Hosted APIs expose no KV cache, so KV strategies are local only. Hosted prompt caching, where a route offers it, changes price, not computation, and is recorded as a price field only.

Per turn: context bytes or retained KV positions, retention, tokens processed (prefill and decode), billed cost, wall-clock, host verdict. For local runs, per-layer attention mass on stage-1 constraint positions, to test whether retained constraints are still attended.

## 9. Pass Gates and Statistics

- **Validity gate:** F-reuse matches full recomputation token for token on every public session.
- **Primary metric:** solved sessions, A against B, exact McNemar on the 40 hidden sessions, α = 0.05, primary seed; same sign on three seeds.
- **Secondary (Holm):** F-evict against B-local; F-evict against F-window; A-local against B-local.
- **Cost:** tokens processed per solved session and cost per verified success per arm, with intervals.
- **Retention:** mean retention and violation counts per arm; a strategy with a violation rate more than 5 points above B's fails regardless of accuracy.

## 10. Interpretation

- **A matches B at lower cost:** host compaction is a free efficiency gain on this family.
- **A beats B:** long history was hurting; a typed ledger helps, consistent with position effects in long contexts.
- **F-evict matches B-local and beats F-window:** targeted KV eviction keeps what matters; blind windows do not.
- **F-reuse passes the identity check and saves prefill:** prefix caching is an exact speed-up, which is an engineering result, not a model result.
- **Retention stays at 100% but violations rise:** the constraint was present and not used; context content is not attention.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

- **OEEIS:** no catalog hook. The violation scanner is the host's refusal path for constraint edits; a typo restatement adopted by the model is logged as a candidate antigen for later thymus screening.
- **Antimorphisms expected:** constraint drift (silently re-deriving a stage-1 claim), adoption of a restated typo, and AM-4 repeats late in long sessions.
- **Layer 1:** KV-prefix reuse and eviction, with the attention readout on retained constraint positions.
- **Layer 2:** none, so decoding stays matched.
- **Scratch space (U12):** the typed ledger of arm A.

## 12. Run Folder, DDC Trace and Operand Mining

Each session writes a RunFolderV1 bundle under `_intelligence/symbol_game/runs/<run_id>/` (U01) with the exact context bytes or retained KV position list for every turn.

Expected DDC pattern: `C` at each stage release, then `D` and `M` steps, `I` when a stage's fragment is merged into the union ledger, and `E T` at the end; a violation appears as `M` with refusal reason `CONSTRAINT_EDIT`. Logged measures: Φ₁, open cycles, retention, violations, tokens processed.

Operands this challenge should yield:

```text
operand ledger_carries_every_constraint.v1 | kind: guard | when: history is compacted | do: keep every declared constraint ID in the ledger verbatim | check: retention = 1 at every turn
operand evict_status_turns_first.v1 | kind: control | when: KV budget is exceeded | do: evict host status turns before any constraint position | check: no constraint position evicted
operand restatement_diff.v1 | kind: guard | when: a turn restates a known constraint | do: diff against the ledger and refuse on mismatch | check: violation count unchanged
```

## 13. Estate Reuse and Prerequisites

- `research/mssn_sn_tower/papers/032_the_symbol_game_three_layer_sovereignty_and_discrete_l1_projection/code/attention_entropy_kv_norm_benchmark.py` (KV energy and attention entropy measurement) and its receipt.
- `omega_engine_symbol_game/domain/topology/subturn.py` (`AttentionContextBoundary`).
- `bench/head_to_head/host.py`; `omega_engine/crates_rs/omega_symbol_game`.
- Base upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).
- Extra upgrades: [U11](../../upgrades/u11_local_open_weights_mechanism_runtime.md) (KV access), [U12](../../upgrades/u12_host_scratch_space_working_memory.md) (ledger).

## 14. Claim Hygiene

- **Supports:** for these models and sessions, the accuracy, cost and constraint retention of full history, host compaction and local KV strategies at 30 to 48 turns.
- **Does not support:** entropy collapse or sparse attention from compaction (Paper 032 points the other way); any hosted KV claim; general long-context claims beyond this family.
- **Narrowest defensible claim:** host compaction (or the winning strategy) changed paired solved rate and tokens per solved session by the measured amounts against full history.
- **Next test:** combine the winning strategy with the ledger of [C006](c006_host_scratch_space_vs_cot.md) on boards of cycle rank above 8.
