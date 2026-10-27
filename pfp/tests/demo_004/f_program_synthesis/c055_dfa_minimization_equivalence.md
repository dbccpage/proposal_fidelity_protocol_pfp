# C055: DFA Minimization and Equivalence with Distinguishing Strings

**AuthorityEffect:** None. **Status:** planned. **Domain:** f_program_synthesis. **Tier:** T2.
**Budget:** $0.50 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to synthesize a frozen module that turns regular expressions into certified minimal DFAs and decides equivalence with an isomorphism or a distinguishing string, for under $0.50.

## 2. Why This Task

Minimality has a Myhill–Nerode certificate. Every state has an access word, and every pair of states has a distinguishing suffix. Together these show that the DFA has exactly as many states as the language has Nerode classes. Inequivalence has a one-string certificate. Equivalence is certified by an isomorphism between minimal DFAs.

The work lies in the pipeline: parse the regex, build an automaton, determinize (which can blow up exponentially), minimize (Hopcroft 1971), and extract certificates. It has several stages and several conventions (complete DFAs with explicit sink states, alphabet order, the empty language), so it suits decomposition.

This stresses the Symbol Game's staged synthesis (U10 sub-turns), the OEWAS (Engine Workflows, Agents, Skills) workflow that orders those stages, and the OEEIS (Engine Epistemic Immune System) against "equivalent" claims without an isomorphism. A pass shows certified synthesis, not new automata theory.

## 3. Formal Problem and Bounds

The alphabet `Σ` has at most 4 letters (`a` to `d`). Regex grammar: union `|`, concatenation by juxtaposition, Kleene star `*`, parentheses, `%` for the empty word and `#` for the empty language. Regexes have at most 60 syntax nodes.

- **MINIMIZE `r`:** return a complete DFA `M` with `L(M) = L(r)`, plus the minimality certificate: access words `w_q` with `δ(q₀, w_q) = q` for every state, and suffixes `z_pq` for every pair `p ≠ q`, with exactly one of `δ(p, z_pq)` and `δ(q, z_pq)` accepting.
- **EQUIV `(r₁, r₂)`:** return `EQUAL` with both minimal DFAs and a state bijection that preserves the start state, the accepting set and every transition; or `DIFFERENT` with a word in the symmetric difference.

The checker decides `L(M) = L(r)` itself, through its own construction and product-automaton reachability, because this part cannot be certified by the solver.

The hidden set must contain:

- the empty language;
- `{ε}`;
- `Σ*`;
- nested stars;
- regexes that are equal only after algebraic rewriting (for example `(a|b)*` and `(a*b*)*`);
- the language "the `k`-th letter from the end is `a`", whose minimal DFA has `2ᵏ` states, with `k ≤ 10`.

## 4. Deliverable and Output Contract

**Mode: frozen module.** `def solve(case: dict) -> dict` is synthesized by the model, makes no model calls at scoring, and runs in the U09 sandbox. States are `0 … k−1`, the start state is 0, and transitions follow the declared alphabet order.

```json
{"case_id": "dfa_ex_01", "task": "MINIMIZE", "alphabet": ["a","b"], "regex": "(a|b)*abb"}
{"case_id": "dfa_ex_01", "status": "SOLVED", "states": 4, "accept": [3], "delta": [[1,0],[1,2],[1,3],[1,0]], "access": ["", "a", "ab", "abb"], "separators": {"0,1": "bb", "0,2": "b", "0,3": "", "1,2": "b", "1,3": "", "2,3": ""}}
{"case_id": "dfa_ex_04", "task": "EQUIV", "alphabet": ["a","b"], "r1": "a*b*", "r2": "(a|b)*"}
{"case_id": "dfa_ex_04", "status": "SOLVED", "kind": "DIFFERENT", "word": "ba"}
{"case_id": "dfa_ex_07", "status": "OUT_OF_SCOPE", "witness": {"reason": "PARSE_ERROR", "offset": 5}}
{"case_id": "dfa_ex_09", "status": "UNKNOWN", "code": "STATE_LIMIT"}
```

A certificate is complete when:

- the DFA is complete and deterministic;
- `L(M) = L(r)` according to the checker's own construction;
- every access word reaches its state;
- every separator distinguishes its pair;
- for `EQUAL`, the bijection preserves structure;
- for `DIFFERENT`, the word lies in exactly one language, by direct membership tests.

## 5. Participant Packet

- `TASK.md` with the regex grammar, operator precedence, the complete-DFA convention and the JSON Schema.
- 12 public examples with verbatim input and output JSON: `(a|b)*abb`; `#`; `%`; `Σ*`; `a*b*` against `(a|b)*`; `(a|b)*` against `(a*b*)*`, which is `EQUAL`; `k = 3` from the end; a three-letter alphabet; nested stars; a parse error; a state-limit `UNKNOWN`; one regex with a redundant union.
- `runner.py` and `accounting.json`.

## 6. Judge Packet

- **Hidden base:** 36 cases: 20 MINIMIZE (including `k`-from-the-end with `k` up to 10) and 16 EQUIV (8 equal, 8 different).
- **Relabel and gauge controls:** 12.
  - a consistent letter renaming in both regexes, with the verdict unchanged;
  - union operands reordered;
  - `r` rewritten by regex identities (`r** = r*`, `(r|r) = r`, `r% = r`);
  - DFA state IDs permuted in the expected answer. Any valid numbering is accepted; only the certificate is checked.
- **Poisoned but schema-valid:** 8. `note` fields claiming equivalence, regexes whose equality holds only on words up to length 6 (the length-7 word is the witness), star-of-empty edge cases, and letters that are declared in `Σ` but unused.
- **Exact checker:** Rust. It builds a Thompson automaton, determinizes by subset construction, and decides equivalence by product reachability.
- **Independent second checker:** Python by a different author, using Brzozowski derivatives (Brzozowski 1964), a different construction.
- **Mutation suite:** the checker must reject: one transition redirected; a missing sink state (an incomplete DFA); an accepting set with one state dropped; a separator that does not separate; an access word ending in the wrong state; a non-minimal DFA with two equivalent states (its separator must fail); a `DIFFERENT` word in both languages; a non-bijective state map.

## 7. Arms and Baselines

Arms A to D follow the protocol. **Arm E** is a pinned deterministic automata implementation (the operator's reference: Thompson construction, subset construction, Hopcroft minimization, and certificate extraction by breadth-first search over pairs) with no model. It should pass everything. A tie with E is expected, and the question is whether synthesis gets there. Arm F is not in the catalog row.

## 8. Budget, Models and Provenance

$0.50 per arm, about 1.4 million tokens at the Q40 blended rate ([review](../00_q40_review.md)). Candidate models: `meta-llama/llama-3.3-70b-instruct`, `qwen/qwen3-30b-a3b`, `deepseek/deepseek-r1-distill-llama-70b`.

Q40 harness defects this spec closes: (1) schema and verbatim examples in every prompt; (2) every repair turn carries the task, the schema, the full module, the failing case, the expected and actual output, and the typed rejection; (3) at least 4 candidates per turn in A, and best-of-N in D; (4) u09 sandbox only; (5) pre-call `BudgetController`; (6) checker exceptions pause scoring.

## 9. Pass Gates and Statistics

- **Capability gate:** in at least 2 of 3 seeds, 36/36 base, 12/12 controls, and 8/8 poisoned with no false `SOLVED`.
- **Primary metric (pre-registered):** base cases passed. The test is an exact McNemar test on paired (seed, case) rows for A vs B, A vs C and A vs D, with Holm correction at α = 0.05.
- **Reported alongside:** results on the `k`-from-the-end rows by `k`, and cost per verified success.
- **Seeds:** 3.

## 10. Interpretation

Expected failure points are precedence parsing, incomplete DFAs, and missing separators for pairs that are distinguished only by long suffixes. If A beats B, staged sub-turns with typed residuals help multi-stage synthesis. If A ties D, sampling suffices. If every arm fails the `k = 10` rows, the limit is determinization cost within the sandbox time, not model reasoning.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog declares no OEEIS hook. Observed mechanisms:

- **Danger gate.** Signal 1 is an `EQUAL` claim; Signal 2 is an isomorphism check failure.
- **Kinetic proofreading.** Staged acceptance in the style of `HopfieldNinioProofreader` runs parse round-trips, then public minimization, then relabel controls.
- **Expected antimorphisms:**
  - AM-2 (equal "by inspection");
  - AM-3 (a minimal DFA without separators);
  - AM-FSP-2 (a distinguishing word that is in both languages).
- **Layer 2:** grammar-masked JSON via `carrier_gbnf` (unwired, and dependent on U06).
- **Layer 1:** not applicable.
- **Scratch space:** the host keeps, per public case, the smallest word on which the module's automaton disagrees with the reference.

## 12. Run Folder, DDC Trace and Operand Mining

Expected Discrete Deformation Calculus (DDC) pattern: `C`, `Λ` (split into parse, construct, determinize, minimize and certify sub-turns), `I`, `R`, `D` steps, `E`, `T`. The `ObstructionScore` sets Φ₁ to the total number of disagreeing words up to length 8 across the public cases, and `active_count` to missing or invalid separators and access words. Γ₂ is unused (0).

Operands to mine:

- always complete the DFA with a sink state before minimizing;
- extract separators by breadth-first search on the pair graph from accepting/non-accepting pairs;
- parse with explicit precedence (star, then concatenation, then union);
- report the shortest distinguishing word.

## 13. Estate Reuse and Prerequisites

- The catalog row lists no estate reuse, and the estate has no automata module. The checker is new Rust work.
- The search crate `engine/crates_rs/core_search` has no automata support either.
- Upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md), plus the row extra [U10](../../upgrades/u10_synthesis_loop_v2.md).

## 14. Claim Hygiene

- **Supports:** a named model synthesized a frozen module that produced certified minimal DFAs and equivalence verdicts for k of 36 hidden cases, at the recorded cost.
- **Does not support:** general compiler-construction ability, performance on large alphabets, or any arm advantage without the paired test.
- **Narrowest defensible claim:** for regexes of at most 60 nodes over at most 4 letters, certified synthesis succeeded in s of 3 seeds.
- **Next test:** regexes with intersection and complement, and a nondeterministic finite-automaton input format.
