# C001: Distractor-Key Attention Masking at Task Level

**AuthorityEffect:** None. **Status:** planned. **Domain:** a_mechanism. **Tier:** T2.
**Budget:** $0.50 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to freeze a
> distractor-key attention-mask pipeline, chosen on public tasks only, and measure whether it
> raises host-verified accuracy on 200 hidden constraint-repair tasks, for under $0.50.

## 2. Why This Task

`bench/mechanism/local_attention_control.py` showed a real causal intervention on one prompt: masking distractor key positions across all heads and layers of `Qwen/Qwen2.5-0.5B-Instruct` moved last-layer distractor attention from 0.043819 to 0, and the preferred digit stayed `7`; masking the carrier positions changed it to `1`. Nobody has measured whether such a mask changes how often an exact host accepts the answer. ChatGPT's assessment called task-level measurement of these interventions the next thing to measure. This challenge measures it.

Generation is hard because the model must find a consistent potential, or the one bad relation, in a system buried in irrelevant words, sentences and integers. Verification is cheap: the host decides consistency by exact potential propagation in O(|V| + |E|). The challenge stresses the Symbol Game's Layer-3 host verdict, the OEWAS (Omega Engine Workflows, Agents, Skills) local runtime seam, and the OEEIS (Omega Engine Epistemic Immune System) two-signal danger gate used to decide when to mask.

A pass would show that, for this task family, model and configuration, a host-declared key mask changes verified accuracy. It would not show that attention explains the answer, that the effect carries over to hosted models (which expose no attention), or that masking helps when the host cannot label distractor spans.

## 3. Formal Problem and Bounds

Each case is an integer rank-difference system: items V with 6 ≤ |V| ≤ 16, directed relations E with |V| ≤ |E| ≤ 40, claims c_e ∈ Z with |c_e| ≤ 10^4, and positive integer weights. The system is consistent iff a potential φ: V → Z exists with φ(v) − φ(u) = c_e for every relation e = (u, v), that is, iff Φ₁(c) = 0.

The prompt embeds the system in text with host-generated distractor spans. Each span is recorded by character offset and mapped to token positions through the tokenizer's offset mapping. Token-ID matching, which the bench script uses, is not allowed: it mislabels a distractor digit that also occurs in a claim.

Case kinds, in proportions fixed by the pre-registration:

1. **Verdict** (40%): `CONSISTENT` with a potential, or `CONTRADICTION` with a directed cycle whose signed claim sum is nonzero.
2. **Single repair** (40%): exactly one relation was perturbed. Return one edge and a new value that makes the system consistent. Any single-edge correction with Φ₁ = 0 is accepted, not only the planted one, because edges in series can repair the same cycles.
3. **Witness audit** (20%): the case carries a schema-valid claimed potential. Return `ACCEPT`, or `REJECT` naming one violated relation. At least half of these witnesses are false.

The hidden set must contain numeric distractors equal to true claim values, distractors placed inside a relation's sentence, contradictions on cycles of length at least 6, disconnected systems, and consistent systems (a false-alarm control: phase-1 gpt-4o-mini false alarms reached 1.00 at 20 items and 55 relations in `bench/matrix/README.md`).

## 4. Deliverable and Output Contract

The frozen deliverable is a pipeline. `pipeline.json` records the model ID, pinned revision, tokenizer revision and the SHA-256 of `tokenizer.json`, dtype, device class, attention implementation (`eager`), decoding parameters, prompt-template digest, intervention (`none`, `distractor_key_mask`, or the gated variant with its threshold), layer set, and host digest. `solve.py` exposes `def solve(case: dict) -> dict`, runs the frozen pipeline through the U11 runtime, and returns one of:

```json
{"status": "SOLVED", "kind": "verdict", "answer": "CONSISTENT", "potential": {"A": "0", "B": "3"}}
{"status": "SOLVED", "kind": "verdict", "answer": "CONTRADICTION", "cycle": ["A", "C", "F", "A"]}
{"status": "SOLVED", "kind": "repair", "edge": ["C", "F"], "value": "-4"}
{"status": "SOLVED", "kind": "audit", "answer": "REJECT", "violated": ["B", "D"]}
{"status": "OUT_OF_SCOPE", "witness": {"field": "edges[7]", "reason": "UNKNOWN_ENDPOINT"}}
{"status": "UNKNOWN", "refusal": "UNPARSEABLE_AFTER_FUEL"}
```

Integers are canonical decimal strings. A certificate is complete when the host can check it from the case input alone: a potential satisfies every relation; a cycle is closed, uses declared relations (a reversed traversal negates the claim) and has a nonzero sum; a repair yields Φ₁ = 0; a rejection names a relation the claimed potential violates. `UNKNOWN` scores as incorrect but not as a false acceptance.

## 5. Participant Packet

- `TASK.md`: the schema above, the three case kinds and the span-labelling rule.
- `examples/`: 40 public cases, each with the exact input JSON, the exact prompt bytes, the distractor and carrier token positions, and the exact expected output JSON (16 verdict, 16 repair, 8 audit of which 4 are false witnesses). The intervention and layer set are chosen on these cases only.
- `runner.py` (loads the frozen pipeline, writes `answers.jsonl`) and `accounting.json`.
- The U11 runtime with hooks to install key masks and to read per-layer, per-head attention rows.

## 6. Judge Packet

- **Hidden base cases:** 200 (80 verdict, 80 repair, 40 audit with at least 20 false witnesses).
- **Relabel controls:** 40 cases with renamed items, reordered relations and resampled distractors over the same system. Reported separately, never pooled.
- **Poisoned but schema-valid:** 30 cases. False potentials that satisfy every relation but one; numeric distractors that restate a true claim with the sign flipped; distractor text that itself asserts "verdict: CONSISTENT" on a contradictory system.
- **Exact checker:** a Rust port of the propagation verdict, cross-checked against `omega_functional::graph_phi1` on cases small enough for its spanning-forest enumeration (limit 100,000 forests).
- **Independent second checker:** the existing Python `Fraction` host, `bench/head_to_head/host.py`.
- **Checker mutation suite:** a potential off by one at one item, an unclosed cycle, a cycle through an undeclared relation, a repair that edits two edges, `"1/1"` or `"0.5"` in an integer field, and a `REJECT` naming a satisfied relation. The checker must reject every one.

## 7. Arms and Baselines

All arms share the pinned local model, tokenizer, prompt bytes, host, fuel (at most 4 turns per case), token caps and history policy. They are matched in the sense the [Q40 review](../00_q40_review.md) found missing.

- **A: Symbol Game.** The U05 turn driver calling the local model through U11, with no intervention.
- **B: Ordinary iterative.** Propose, host-check, repair, with the same history.
- **C: Representation ablation.** A's controller and host checks with the packet rendered as plain text.
- **D: Repeated sampling.** Best-of-N at the pre-registered temperature, filtered by the host's certificate check (which needs only the case input). N is set so D's token spend matches A's.
- **E: No-model baseline.** The exact host solver. It solves every case and is reported as the ceiling, not as a competitor.
- **F: Local mechanism (treatment).** Arm A plus the frozen intervention, with sub-arms on the same cases. F-null installs the hooks with an empty mask and must reproduce A's output token IDs exactly. F-distractor is the treatment. F-carrier masks relation tokens and is expected to hurt. F-random masks as many random non-relation positions as F-distractor does. F-delete removes the distractor spans from the prompt instead of masking them. F-gated masks only when the danger gate fires and is compared with arm A plus one unmasked retry, so a second attempt is not credited to the mask.

## 8. Budget, Models and Provenance

Primary model `Qwen/Qwen2.5-7B-Instruct`; replication model `meta-llama/Llama-3.1-8B-Instruct`. Both run locally in Hugging Face transformers with eager attention, with commit revisions pinned in the U06 registry at packet-build time. Hosted APIs expose no attention tensors and accept no key masks, so no hosted route can take part here; the hosted Layer-2 comparison is [C005](c005_hosted_decode_controls_bakeoff.md).

Local calls bill $0. The $0.50 ceiling still binds any hosted call (none is planned) and is enforced before each call by `BudgetController`. Local compute (wall-clock, device, dtype, peak memory) is recorded per case and priced at a rate fixed in the pre-registration, so cost per verified success includes it. A quantized checkpoint is a different configuration and must be pinned as one.

Per case the run records prompt bytes, input token IDs, distractor and carrier positions, attention mass on distractor, carrier and other keys for every layer and head (at the last prompt position and at each generated position), full output token IDs, the parsed answer, the host verdict and the seed.

## 9. Pass Gates and Statistics

- **Validity gate:** F-null reproduces arm A's output token IDs on every case, every receipt is complete, and the checker kills its whole mutation suite.
- **Primary metric (pre-registered):** host-verified correct rate on the 200 hidden base cases, F-distractor against A, exact two-sided McNemar on paired cases, α = 0.05, on the pre-registered primary seed.
- **Replication:** the paired effect has the same sign on all three sampling seeds and on the replication model.
- **Secondary (Holm-corrected):** F-distractor against F-delete, F-random and F-carrier; F-gated against A with one retry.
- **Safety gate:** the false-witness acceptance rate under F-distractor exceeds arm A's by no more than the pre-registered margin of 5 percentage points.
- **Relabel controls:** per arm, the fraction of relabel pairs with matching correctness.

## 10. Interpretation

- **F-distractor beats A, F-random and F-delete:** a Layer-1 key mask adds verified accuracy on this family beyond generic masking and beyond removing the text.
- **F-distractor beats A but ties F-delete:** the gain comes from removing distractors, which a host can do in the prompt; the mask adds nothing.
- **F-distractor ties F-random:** any perturbation of this size moves the result; there is no distractor-specific claim.
- **F-carrier hurts and F-distractor ties A:** attention to relation tokens matters for this model and attention to distractors does not.
- **Distractor attention reaches zero but accuracy does not move:** the 0.5B receipt holds at the mechanism level and not at the task level. That is a useful negative result.
- **All arms tie:** this family does not distinguish the mask. It does not show masks are useless elsewhere.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

- **Two-signal danger gate** (`TwoSignalDangerGate` in `omega_engine_symbol_game/domain/immune/danger_gate.py`). Signal 1 is the presence of host-labelled distractor spans. Signal 2 is damage: distractor attention mass above a threshold fixed on public cases, or a host refusal of the unmasked answer. F-gated masks only when both fire.
- **Antimorphisms expected:** AM-2 analogues (a confident `CONSISTENT` on a contradictory system), AM-FSP-2 (accepting a false witness), and distractor capture (a distractor integer copied into a repair value).
- **Layer 1:** key-position masks with fixed position IDs on every head and layer, as in the bench script, or on a layer subset chosen on public cases.
- **Layer 2:** none in the primary comparison, so decoding stays matched. A secondary run may add the slot grammar of `bench/matrix/run_repair_matrix.py` to every arm equally.
- **Scratch space (U12):** the host keeps the parsed relation list and the span table outside the model context. Every sub-arm except F-delete sees the same prompt bytes.

## 12. Run Folder, DDC Trace and Operand Mining

Every case in every arm writes a RunFolderV1 bundle under `_intelligence/symbol_game/runs/<run_id>/` (U01). The intervention is a step attribute (`control.layer1`, positions, layers), not a DDC letter.

Expected DDC pattern: `C` (host exposes the case), then `M` for each unparseable or refused answer and `D` when a proposed repair lowers the number of violated fundamental cycles, then `E` when the host verifies the certificate, then `T`. Traces of the form `C M M M M T` ending in `UNKNOWN` are expected on the weaker model and are kept. Logged measures per step: the Φ₁ = 0 flag, violated relations under the proposed potential, nonzero fundamental-cycle sums, and distractor and carrier attention mass per layer.

Operands this challenge should yield:

```text
operand distractor_span_mask.v1 | kind: control | when: host-labelled spans exist and signal 2 fired | do: mask their key positions, keep position IDs | check: host verdict, never attention mass
operand numeric_distractor_guard.v1 | kind: guard | when: a repair value occurs only inside a distractor span | do: refuse and re-ask with the span table | check: repaired system has Phi1 = 0
operand audit_every_relation.v1 | kind: move | when: the case carries a claimed potential | do: evaluate every relation before answering and report the first violation | check: the named relation fails under the potential
```

## 13. Estate Reuse and Prerequisites

- `bench/mechanism/local_attention_control.py` (mask construction, fixed position IDs, attention readout) and `bench/mechanism/local_carrier_control.py` (model pinning).
- `bench/head_to_head/tasks.py` (generator, to be extended with labelled spans) and `bench/head_to_head/host.py` (second checker).
- `omega_engine/crates_rs/omega_functional` (`graph_phi1`) for the Rust cross-check.
- `omega_engine_symbol_game/domain/immune/danger_gate.py`.
- `research/mssn_sn_tower/demos/attention_sparse_output_boundary.md`, whose Layer 1/2/3 boundary this spec follows.
- Base upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).
- Extra upgrades: [U11](../../upgrades/u11_local_open_weights_mechanism_runtime.md), [U12](../../upgrades/u12_host_scratch_space_working_memory.md).

## 14. Claim Hygiene

- **Supports:** for the pinned models, generator and case mix, whether a host-declared distractor-key mask changes host-verified accuracy against the same pipeline without it, and against deleting the distractors.
- **Does not support:** that attention mass explains correctness; any claim about hosted models; any claim about inputs whose distractors the host cannot label; any claim of entropy collapse or reduced internal dimension.
- **Narrowest defensible claim:** on this model revision and generator, masking these labelled key positions changed paired hidden-case accuracy by the measured amount, with the stated McNemar p.
- **Next test:** [C002](c002_attention_steering_sweep_correctness.md) (steering rather than masking) and [C003](c003_head_attribution_activation_patching.md) (which heads carry the effect), then the same mask on a second task family.
