# C046: Knuth-Bendix Completion with Joinability Certificates

**AuthorityEffect:** None. **Status:** planned. **Domain:** e_formal_math. **Tier:** T3.
**Budget:** $1.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to produce a frozen module that completes hidden string and term rewriting systems into convergent ones, certifying every critical pair joinable, or reports an honest failure or `UNKNOWN`, for under $1.00.

## 2. Why This Task

Checking a completed system is mechanical:

1. Every rule decreases in the declared reduction order.
2. Every critical pair joins, as shown by explicit joining paths.
3. Every input equation joins.
4. Every new rule is derivable from the inputs.

By Newman's lemma, termination plus local confluence gives confluence. Producing a finite complete system is search-hard. Knuth–Bendix completion (Knuth & Bendix 1970) can diverge, and some finitely presented monoids with decidable word problem have no finite complete rewriting system at all (Squier 1987).

This is the estate's home ground. Critical peaks are the Symbol Game's commuting-square obstructions, and `core_symbol_game_runtime` already refuses to read a failed join search as non-confluence. The challenge also stresses the OEWAS (Engine Workflows, Agents, Skills) loop between orienting and joining, and the OEEIS (Engine Epistemic Immune System) against the claim "confluent" when a join search merely ran out.

## 3. Formal Problem and Bounds

**String case.** A monoid presentation `⟨Σ | E⟩` with `|Σ| ≤ 4`, `|E| ≤ 6` and word length at most 8, together with a shortlex order given by a letter precedence.

**Term case.** A signature of at most 4 function symbols with arities at most 2, at most 5 equations, and a reduction order given as either:

- a lexicographic path order (LPO) with a declared precedence; or
- a Knuth–Bendix order (KBO) with declared weights and precedence.

**Outputs:**

- `COMPLETED`: a finite rule set `R`. Every rule satisfies `l > r` in the order. Every critical pair of `R`, enumerated by the checker itself, is joinable by the supplied paths. Every equation in `E` is joinable in `R`. Every rule carries an equational derivation from `E`.
- `FAILED_UNORIENTABLE`: a derived equation `s = t`, with its derivation from `E`, such that `s` and `t` are incomparable in the declared order. For example, a commutativity instance under LPO. Under shortlex all distinct words are comparable, so this outcome applies to terms only.
- `UNKNOWN` (`DIVERGED_WITHIN_LIMIT`): the rules so far plus one unjoined critical pair.

A standard public reference is the ten-rule complete system for group axioms (Knuth & Bendix 1970), under the order declared in the example file. Hidden verdicts come from the operator's reference completion run with a large budget, cross-checked by the second checker.

Edge cases:

- presentations that complete to a finite group;
- presentations that diverge under shortlex but complete under a different precedence (the precedence is fixed per case);
- equations with variables only on one side;
- trivial theories where `x = y` is derivable.

## 4. Deliverable and Output Contract

**Mode: frozen module.** `def solve(case: dict) -> dict` is synthesized by the model and makes no model calls at scoring. A path is a list of steps of the form `{"rule": index, "pos": position, "subst": map}` for terms, and `{"rule": index, "at": offset}` for strings.

```json
{"case_id": "kb_ex_01", "kind": "string", "alphabet": ["a", "b"], "precedence": ["a", "b"], "equations": [["aa", ""], ["bb", ""], ["ab", "ba"]]}
{"case_id": "kb_ex_01", "status": "SOLVED", "kind": "COMPLETED", "rules": [["aa", ""], ["bb", ""], ["ba", "ab"]], "joins": [{"peak": "aaa", "left": [{"rule": 0, "at": 0}], "right": [{"rule": 0, "at": 1}]}], "derivations": [{"rule": 2, "from_equation": 2, "reversed": true}]}
{"case_id": "kb_ex_05", "status": "SOLVED", "kind": "FAILED_UNORIENTABLE", "equation": ["f(x,y)", "f(y,x)"], "derivation": [{"equation": 0}]}
{"case_id": "kb_ex_08", "status": "UNKNOWN", "code": "DIVERGED_WITHIN_LIMIT", "rules": [["bab", "aba"]], "unjoined_peak": {"source": "babab", "left": "abaab", "right": "baaba"}}
```

The `joins` list in the example is truncated; a real answer covers every critical pair.

A complete `COMPLETED` certificate covers all of the following:

- per-rule order checks;
- a joining path for each critical pair in the checker's own enumeration (a missing pair rejects the answer);
- joinability of every input equation;
- a derivation of every rule.

`OUT_OF_SCOPE` covers malformed inputs. Examples are a precedence that is not a strict order, and a rule whose right side has variables absent from the left.

## 5. Participant Packet

- `TASK.md` with the term syntax, positions, the definitions of shortlex, LPO and KBO, the path and derivation formats, and the JSON Schema.
- 10 public examples with exact input and output JSON: the Klein four-group presentation above; a cyclic group presentation; the group axioms (ten-rule system); a commutativity failure; a string example cut at a deliberately tiny limit (it illustrates the `UNKNOWN` format and makes no claim of divergence); two malformed inputs; three small completions with overlap-heavy pairs.
- `runner.py`, which replays every path locally, and `accounting.json`.

## 6. Judge Packet

- **Hidden base:** 36 cases. 20 string and 16 term cases, 24 that complete, 4 that fail by unorientability and 8 that diverge within the reference limit.
- **Relabel and gauge controls:** 12. Letters and symbols renamed with the precedence renamed consistently, equation order shuffled, equations reoriented (they are unoriented inputs), and variables renamed. Tietze-transformed presentations are not used as invariance controls, because they can change whether a finite complete system exists.
- **Poisoned but schema-valid:** 8.
  - `note` fields asserting confluence;
  - rule sets that are locally confluent but non-terminating under the declared order;
  - a precedence containing a cycle;
  - a case whose equations make the theory trivial.
- **Exact checker:** Rust, built on `engine/crates_rs/core_symbol_game_runtime/src/rewriting/` (`critical_pairs`, `replay_path`, `reachable`), with its own critical-pair enumeration and order comparisons.
- **Independent second checker:** a Python implementation by a different author, and kbmag (Holt) for the string cases, pinned at packet-build time.
- **Mutation suite:** the checker must reject: an omitted critical pair; a path step applying a rule at the wrong offset; a rule that increases in the order; a rule with no derivation (unsound); an input equation left unjoinable (incomplete); a `DIVERGED` report whose "unjoined" pair actually joins.

## 7. Arms and Baselines

Arms A to D follow the protocol. **Arm E** is a deterministic completion with no model: the operator's reference implementation for terms and kbmag for strings, with the same limits. It is expected to settle most completing cases. A tie with E means the model contributed nothing beyond standard completion. Differences can appear on cases that need good critical-pair scheduling within the limit. Arm F is not in the catalog row.

## 8. Budget, Models and Provenance

$1.00 per arm, about 2.8 million tokens at the Q40 blended rate ([review](../00_q40_review.md)). Candidate models: `meta-llama/llama-3.3-70b-instruct`, `deepseek/deepseek-r1-distill-llama-70b`, `qwen/qwen3-30b-a3b`. The receipt binds the kbmag version and the reference completion's hash.

Q40 lessons apply:

- real JSON is shown for every status;
- repair turns carry the module, the failing case and the checker's typed rejection;
- several candidates are drawn per turn;
- execution is sandboxed with a 120-second per-case limit;
- budget is checked before every call.

## 9. Pass Gates and Statistics

- **Capability gate:** in at least 2 of 3 seeds, all 24 completing and 4 failing base cases are settled with valid certificates. On the 8 divergent cases the answer must be `UNKNOWN`: any `COMPLETED` claim there fails the arm, because the checker would reject it. All relabel controls must agree with their base.
- **Primary metric (pre-registered):** certified base cases. The test is an exact McNemar test on paired (seed, case) rows for A vs B, A vs C and A vs D, with Holm correction at α = 0.05.
- **Seeds:** 3.

## 10. Interpretation

If A completes more cases than B within the same limit, the peak-as-obstruction representation helps schedule critical pairs. If A ties E, the result is automation. A module that answers `UNKNOWN` everywhere passes nothing but also claims nothing, which is recorded as honest non-performance.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog declares no OEEIS hook. Observed mechanisms:

- **Danger gate.** Signal 1 is a `COMPLETED` claim; Signal 2 is a checker-enumerated critical pair missing from `joins`.
- **Treg-style damping** (`TregSupervisor`) of repeated identical orientation attempts.
- **Expected antimorphisms:** AM-2 (claiming confluence), AM-4 (re-adding the same rule) and AM-3 (skipping pairs).
- **Layer 2:** a grammar mask for step records, via `carrier_gbnf` (unwired).
- **Layer 1:** not applicable.
- **Scratch space:** the host keeps the pending critical-pair queue and the current rules as scratch state, so repair prompts show the open peaks rather than the whole history.

## 12. Run Folder, DDC Trace and Operand Mining

Expected Discrete Deformation Calculus (DDC) pattern: `C` (equations and order exposed), `I` (orient equations), `R` (unjoined peaks), then `Λ` (add an oriented rule) and `D` (a peak joined) repeated, `E` when all peaks are joined, `T`. `M` records failures and limits. The `ObstructionScore` sets Γ₂ to the number of unjoined critical peaks, Φ₁ to the number of input equations not yet joinable, and `active_count` to unoriented equations.

Operands to mine:

- schedule the smallest critical pairs first;
- interreduce after every added rule;
- when an equation is incomparable, report failure with its derivation, never force an orientation;
- a join search that ran out of budget is `UNKNOWN`, not non-confluence.

## 13. Estate Reuse and Prerequisites

- `projects/mssn_sn_symgam/demos/demo_polygraph_confluence`, the catalog reuse row, for its fixture and receipt discipline.
- `engine/crates_rs/core_symbol_game_runtime/src/rewriting/` (`reduction.rs`, `peak.rs` with `BoundedWithUnjoinedPeak`).
- `lean4/ConfluenceFlip.lean`.
- Upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md). No row extras; [U10](../../upgrades/u10_synthesis_loop_v2.md) is recommended.

## 14. Claim Hygiene

- **Supports:** the frozen module completed or correctly failed k of 28 decidable hidden cases with fully checked joinability, orientation and derivation certificates, and made no false completion claim on divergent cases.
- **Does not support:** decidability results, termination of completion in general, or any statement about presentations outside the hidden set.
- **Narrowest defensible claim:** under the declared orders and limits, the module's certified completion rate was X, against arm E's Y.
- **Next test:** completion modulo associativity and commutativity, and the C050 proofs that reuse completed systems.
