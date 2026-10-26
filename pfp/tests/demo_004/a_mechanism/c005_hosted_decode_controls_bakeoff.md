# C005: Hosted Decoding Controls Bake-off

**AuthorityEffect:** None. **Status:** planned. **Domain:** a_mechanism. **Tier:** T1.
**Budget:** $0.10 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to compare
> `logit_bias`, JSON-schema structured output, a GBNF grammar and no control on identical
> hidden tasks, reporting parseable, correct and cost per verified success, for under $0.10.

## 2. Why This Task

Hosted APIs are Layer 2 only. They expose no attention tensors, no key masks and no full-vocabulary logits, so everything in [C001](c001_attention_distractor_mask_task_level.md) to [C003](c003_head_attribution_activation_patching.md) is out of reach through them. What a hosted route can offer is a decoding control, and the estate already types those controls honestly: `omega_engine_symbol_game/domain/carrier_decoding.py` ranks `GRAMMAR` (exact), `LOGIT_BIAS` (bounded, not exact; a −100 bias is a strong bias, not −∞) and `UNCONSTRAINED`. `bench/mechanism/api_logit_control.py` showed `logit_bias` changing an answer (`7` to `55`), which is steering, not a mask.

The practical question is which control, on a real open-weights route, gives the most host-verified answers per dollar, and whether the route actually applied the control at all. The request body in `OpenRouterBackend` today sends only model, messages and max_tokens, so no hosted control has ever been exercised through the governed path (U06). The challenge stresses the governed provider path, the Symbol Game host, OEWAS (Omega Engine Workflows, Agents, Skills) receipts and, lightly, the OEEIS (Omega Engine Epistemic Immune System) principle that a claimed control is checked, not trusted. A pass ranks controls on this family. Schema validity is not correctness, and a pass does not show otherwise.

## 3. Formal Problem and Bounds

Tasks are short-output cases from the C001 and C004 families: (a) consistency verdict with certificate on systems with at most 10 items and 18 relations; (b) k-integer cycle repair with k = 3 to 6. Outputs are at most 64 tokens.

Controls:

1. `none`.
2. `logit_bias`: −100 on a fixed list of prose-starting token IDs and +5 on digit, sign and separator IDs, for the pinned tokenizer. Finite bias, recorded as `LOGIT_BIAS`, never as exact.
3. `json_schema`: structured output with a strict JSON schema for the answer object.
4. `gbnf`: a GBNF grammar from `carrier_gbnf`, only on a route verified at packet-build time to accept grammars. Where no such hosted route exists, this control runs only in arm F on a local llama.cpp build and is reported there.

**Control-honored probes.** Before scoring, each route and control gets 10 probe requests constructed so that the unconstrained top answer is forbidden by the control. A control counts as honored on a route only if all 10 outputs respect it. Unhonored controls are reported as `UNCONSTRAINED` for that route, following `provider_capability`: a capability table is not a receipt.

## 4. Deliverable and Output Contract

The frozen deliverable per arm is `pipeline.json` (provider, model ID, route pin, the exact request body template for each control including the schema or grammar text and bias map, prompt digest) and `solve.py` returning the C001 verdict objects or the C004 repair object, or:

```json
{"status": "UNKNOWN", "refusal": "CONTROL_NOT_HONORED", "route": "<provider>", "control": "json_schema"}
{"status": "UNKNOWN", "refusal": "PROVIDER_REFUSAL_OR_INCOMPLETE", "finish_reason": "length"}
```

Certificates are checked by the host exactly as in C001 and C004. A schema-valid answer with a false potential is wrong.

## 5. Participant Packet

- `TASK.md`, the four request templates, the JSON schema, the GBNF text and the bias token lists for each pinned tokenizer.
- `examples/`: 30 public cases (15 per kind) with exact input and expected output JSON.
- `runner.py`, `accounting.json` with one row per call (provider, model ID, generation ID, tokens, billed cost, control, honored flag).

## 6. Judge Packet

- **Hidden base cases:** 100 (50 per kind); the operator may lower N before the run if the measured cost per call would breach the ceiling with a 20% reserve, and records the change in the pre-registration.
- **Relabel controls:** 20 renamings and cycle rotations.
- **Poisoned but schema-valid:** 16 cases whose natural answer is a schema-valid false witness (a potential that satisfies all relations but one; a repair that reaches zero at a cost above the optimum, labelled optimal).
- **Exact checker:** the C001 and C004 Rust checkers.
- **Independent second checker:** `bench/head_to_head/host.py` and a Python `Fraction` cycle checker.
- **Checker mutation suite:** valid JSON with a missing certificate field, an extra field, integers as JSON numbers instead of strings, and a correct shape with a wrong value.

## 7. Arms and Baselines

- **A: Symbol Game** through the U05 turn driver and the governed gateway. Each decoding control is its own arm variant (A-none, A-bias, A-schema, A-gbnf) with its own $0.10 ceiling.
- **B: Ordinary iterative** with `none`. **C: Representation ablation** with `none`. **D: Repeated sampling** with `none`, cost-matched to A-none.
- **E: No-model baseline:** the exact host; the ceiling.
- **F: Local mechanism:** the same model family run locally with llama.cpp GBNF (exact) and a local −∞ carrier mask. Local weights may be quantized and are then not the hosted weights, so F is reported beside the hosted arms, not paired with them.

## 8. Budget, Models and Provenance

Primary model `meta-llama/llama-3.1-8b-instruct`; replication `qwen/qwen-2.5-7b-instruct`; both open weights well under the ceiling. The historical `api_logit_control.py` receipt used `openai/gpt-4o-mini`, which is closed and not eligible here. Routing sets `allow_fallbacks: false` and, where the route supports it, `require_parameters: true`, so a provider that ignores a control is not silently chosen; that behavior is itself verified by the probes. Every call records provider, model ID, generation ID, tokens and billed cost. `BudgetController` enforces $0.10 per arm variant before each call. No price is assumed in this spec; the pre-registration records the prices observed at packet-build time.

## 9. Pass Gates and Statistics

- **Validity gate:** every scored control passed its honored probes on the scored route, or is reported as not honored; every call has a generation ID and billed cost.
- **Primary metric:** host-verified correct rate, A-schema against A-none, exact McNemar, α = 0.05, primary seed; three seeds at the pre-registered temperature.
- **Secondary (Holm):** A-bias and A-gbnf against A-none; A-schema against A-gbnf where both are honored.
- **Economics:** cost per verified success per variant with its interval; parseable rate with Wilson intervals.
- **Laundering:** the fraction of poisoned cases answered with a schema-valid false witness, per variant.

## 10. Interpretation

- **Schema raises parseable but not correct:** structure was the only gap the control closed; content errors remain.
- **Bias helps as much as schema at lower cost:** finite steering is enough for this output shape on this route.
- **A control fails its probes:** the route ignored it. Any earlier claim that relied on that control through that route is unsupported.
- **GBNF is only available locally (F) and wins:** exactness requires a grammar-capable sampler, as `carrier_decoding.py` states.
- **All controls tie on correctness:** decoding controls do not move this family; the next lever is the task representation or the host loop.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

- **OEEIS:** no catalog hook. The probes apply the same principle the immune code applies to candidates: a declared capability is an untrusted claim until checked.
- **Antimorphisms expected:** schema-valid false witnesses (AM-FSP-2 in structured form), empty or truncated JSON under `finish_reason: length`, and `"55"`-style outputs that satisfy a bias but not the shape.
- **Layer 2:** the four controls above. **Layer 1:** not available on hosted routes and not attempted.
- **Scratch space:** none.

## 12. Run Folder, DDC Trace and Operand Mining

Each case writes a RunFolderV1 bundle under `_intelligence/symbol_game/runs/<run_id>/` (U01) holding the full request body, so that what the route was asked to do is on record beside what it did.

Expected DDC pattern: `C E T` for verified answers, `C M T` for parse or control failures and `C M D E T` for a repaired second turn. Logged measures: parse flag, honored flag, the Φ₁ = 0 flag, excess repair cost, billed cost.

Operands this challenge should yield:

```text
operand probe_before_trust.v1 | kind: guard | when: a run depends on a hosted decoding control | do: send forbidden-answer probes first; downgrade to UNCONSTRAINED on any violation | check: 10 of 10 probes honored
operand schema_is_shape_only.v1 | kind: guard | when: output passed a JSON schema | do: still run the host certificate check | check: host verdict recorded separately from schema validity
operand require_parameters_pin.v1 | kind: control | when: routing through an aggregator | do: set allow_fallbacks false and require the control parameter | check: receipt names the serving provider
```

## 13. Estate Reuse and Prerequisites

- `bench/mechanism/api_logit_control.py` (hosted `logit_bias` request, receipt fields) and its receipt.
- `omega_engine_symbol_game/domain/carrier_decoding.py` (`ConstraintMode`, `provider_capability`, `carrier_gbnf`, `logit_bias_ban`, `verify_emission`).
- `omega_engine_providers/adapters/model_backends.py` (`OpenRouterBackend`, to gain seed, temperature, `logit_bias`, `response_format` and grammar fields under U06).
- Base upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md). U06 is both a base requirement and this row's named extra.

## 14. Claim Hygiene

- **Supports:** for the pinned open-weights routes, which hosted decoding controls were honored, and their parseable rate, correct rate and cost per verified success on this family.
- **Does not support:** any Layer-1 claim; that `logit_bias` is an exact mask; that schema-valid output is correct; any claim about closed models.
- **Narrowest defensible claim:** on these routes and dates, structured output (or the winning control) changed paired host-verified accuracy against no control by the measured amount, at the measured cost.
- **Next test:** repeat on the hosted rungs of [C004](c004_grammar_masked_decode_ladder.md) and feed the winning control into [C010](c010_repeated_sampling_frontier.md)'s cost frontier.
