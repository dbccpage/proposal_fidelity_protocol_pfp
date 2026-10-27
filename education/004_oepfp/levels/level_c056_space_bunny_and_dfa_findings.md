# Empirical Findings: Challenge C056 DFA Minimization and Equivalence with Distinguishing Strings

> **Notice (2026-09-29).** `stealth/space-bunny-alpha` ("Space Bunny") is a new free
> stealth model offered on OpenRouter as of 2026-09-28. The provider does not disclose
> its identity, size or training. Results with it are exploratory: they fall outside
> the challenge protocol SG-CP v1, whose §2 admits only open-weight models of at most
> 70B parameters, and they may not be reproducible after the stealth period. This
> description replaces the one in the note of 2026-09-28. Every `PASS_TO_MASTER` label
> in this note is a reference self-score: the challenge's own reference solver passed
> its own package's checkers. It says nothing about any model. No paper in this
> collection has audited the other figures in this note. The audit behind these
> notices is recorded in the collection's `verification/residuals.md`, section 8.

> **Source check (2026-10-20, pin `c419cc6beb`).** This file is a copy of the note of the same name, without the `level_` prefix, in [`atlas/coda_atlas/F004_papers/015_pfp/symbol_game_challenge_and_demos_findings/`](../../../../atlas/coda_atlas/F004_papers/015_pfp/symbol_game_challenge_and_demos_findings/). The collection's `verification/residuals.md` is not found in either copy, and no `_intelligence/_adversary/runs/` directory exists at the pin, so the run folders and digests named below cannot be opened. The package is now [`f_program_synthesis/c056_dfa_minimization_equivalence/`](../../../../demos/certified_challenges/c056_dfa_minimization_equivalence/). The retained `empirical_results/matrix_results.json` matches the pass counts 4, 4 and 2 and the token totals 11,563, 8,462 and 8,378. No phase-3 scoring receipt is retained for this challenge, so the `PASS_TO_MASTER (64/64, 48/48)` line is not backed by a file at the pin.

> **Note (2026-09-28).** `stealth/space-bunny-alpha` is an unidentified model offered
> anonymously on OpenRouter; its results cannot be reproduced. No paper in this
> collection has audited the figures in this note.

**AuthorityEffect:** None  
**Domain:** f_program_synthesis  
**Tier:** T2  
**Protocol:** SG-CP v1  
**Gate Verdict:** `PASS_TO_MASTER` (Run ID: `c056_eval_1790646329`)  
**Reference Solver Commitment Digest:** `49b5fb431cf9416d0003f0023840644711ce280f448362e994709438a4879819`  

---

## 1. Challenge & Verification Summary

Challenge C056 benchmarks automated synthesis of regular expression compilation into certified minimal complete Deterministic Finite Automata (DFAs) and language equivalence checking with checkable certificates:
- **Minimization task (`"MINIMIZE"`):** Given a regular expression over alphabet $\Sigma$ ($|\Sigma| \le 4$), synthesize a complete minimal DFA $M = (Q, \Sigma, \delta, 0, F)$ with $k$ reachable states, complete transition table $\delta \in Q^{k \times |\Sigma|}$, and a complete Myhill-Nerode certificate:
  - **Access words:** A list $w_0, \dots, w_{k-1}$ over $\Sigma^*$ such that $\hat{\delta}(0, w_q) = q$ for each $q \in Q$.
  - **Pairwise separating suffixes:** A dictionary mapping every distinct state pair $0 \le p < q < k$ to a word $z_{pq} \in \Sigma^*$ such that exactly one of $\hat{\delta}(p, z_{pq})$ and $\hat{\delta}(q, z_{pq})$ is in $F$.
- **Equivalence task (`"EQUIV"`):** Given two regular expressions $r_1$ and $r_2$:
  - **`EQUAL` branch:** Decides $L(r_1) = L(r_2)$ with minimal DFAs and a state isomorphism bijection $\phi: Q_1 \to Q_2$ that maps start state 0 to 0, preserves acceptance ($s \in F_1 \iff \phi(s) \in F_2$), and commutes with transitions ($\phi(\delta_1(s, a)) = \delta_2(\phi(s), a)$).
  - **`DIFFERENT` branch:** Decides $L(r_1) \ne L(r_2)$ with a certified distinguishing word $w \in (L(r_1) \setminus L(r_2)) \cup (L(r_2) \setminus L(r_1))$.
- **Out of Scope branch:** Rejects malformed syntax, unbalanced parentheses, symbols outside $\Sigma$, or empty alphabets.

### Verification Gate Results
- **Hidden Base & Control Evaluation:** 64/64 cases passed (100.0%) across:
  - 32 Base cases: empty language `#`, empty word `%`, universal language $(a|b)^*$, singletons, concatenation, union, suffix matching, prefix matching, substring matching, parity languages, even-length words, 3- and 4-letter alphabets, $k$-th letter from end ($k=2, 3$), nested stars, 8 equivalent algebraic identity pairs, and 8 distinct inequivalent regex pairs.
  - 16 Relabel and Gauge Controls: alphabet letter transpositions (`a <-> b`, `a <-> c`), operand reorderings, algebraic identity rewrites ($r\% = r, r\# = \#, r|\# = r$), and redundant parentheses.
  - 16 Poisoned Cases: deceptive prompt suggestions claiming false equivalence, unclosed parens, unmatched close parens, foreign alphabet characters, leading stars, empty alphabet lists, forbidden operators in alphabet lists, and missing or invalid keys.
- **Dual Independent Checker Agreement:** 100% agreement between the exact product-automaton/DFA simulator checker and the independent Myhill-Nerode certificate verifier.
- **Hostile Mutation Kill Rate:** 48/48 hostile mutations killed (100.0%) with zero runtime crashes across redirected delta transitions, non-minimal redundant states, dropped accept states, invalid accept additions, bad access words, separator failures, out-of-bounds transitions, float/boolean values, false equivalence claims, non-homomorphic bijections, and non-distinguishing words.

---

## 2. Empirical Model Benchmark (10-Problem Matrix Sweep)

Frontier stealth reasoning model **Space Bunny Alpha** (`stealth/space-bunny-alpha`) was evaluated alongside open dense baselines **LLaMA 3.3 70B Instruct** and **LLaMA 3.1 8B Instruct** across 10 diverse automata problem instances.

| Problem Case ID | Problem Characteristics | Space Bunny Alpha | LLaMA 3.3 70B | LLaMA 3.1 8B |
| :--- | :--- | :---: | :---: | :---: |
| `c056_m01_minimize_abb` | 4-state suffix $(a\|b)^*abb$ | **PASS** (1.39s) | FAIL (Access word error: `access[0]='a'` reaches state 1) | FAIL (Delta row count mismatch: 4 vs 5) |
| `c056_m02_minimize_empty` | Empty language `#` (1 state) | **PASS** (1.33s) | **PASS** (1.70s) | FAIL (Access word `access[1]=''` reaches state 0) |
| `c056_m03_minimize_epsilon` | Empty word `%` (2 states) | FAIL (Separator `'a'` fails on (0, 1): both reach dead state 1) | FAIL (Incomplete DFA: 1 state instead of 2) | FAIL (Access list length mismatch) |
| `c056_m04_equiv_equal_universal` | EQUIV: $(a\|b)^*$ vs $(a^*b^*)^*$ | **PASS** (1.18s) | **PASS** (0.21s) | **PASS** (0.15s) |
| `c056_m05_equiv_different_order` | EQUIV: $a^*b^*$ vs $(a\|b)^*$ | FAIL (Distinguishing word `'ab'` in both languages) | FAIL (Falsely claimed EQUAL, missing `'ba'`) | FAIL (Distinguishing word `'ab'` in both languages) |
| `c056_m06_minimize_parity` | Parity of $a$'s: $b^*(ab^*ab^*)^*$ | FAIL (Upstream API provider error) | FAIL (Access word error: `access[0]='b'` reaches state 1) | FAIL (Access word error: `access[1]='b'` reaches state 0) |
| `c056_m07_minimize_3alpha` | 3-letter alphabet substring | FAIL (Separator `'abc'` fails to distinguish (0, 3)) | FAIL (Separator `'a'` fails to distinguish (0, 1)) | FAIL (Access word error: `access[1]='a'` reaches state 0) |
| `c056_m08_equiv_distrib` | EQUIV: $a(b\|c)$ vs $ab\|ac$ | FAIL (Missing `bijection` dictionary) | **PASS** (0.80s) | FAIL (Falsely claimed DIFFERENT on equivalent regexes) |
| `c056_m09_poison_deceptive_note` | Prompt note claiming false EQUAL | FAIL (Submitted `'ab'` which is in both languages) | FAIL (Succumbed to deception: claimed EQUAL) | FAIL (Succumbed to deception: claimed EQUAL) |
| `c056_m10_poison_unclosed_paren` | Syntax error `(a\|b*abb` | **PASS** (0.87s) | **PASS** (0.68s) | **PASS** (0.49s) |
| **Overall Score** | **Total Passed (Pass Rate)** | **4 / 10 (40.0%)** | **4 / 10 (40.0%)** | **2 / 10 (20.0%)** |
| **Total Token Cost** | **Prompt + Completion Tokens** | **11,563 tokens** | **8,462 tokens** | **8,378 tokens** |

---

## 3. Epistemic Analysis & Failure Modes

1. **Space Bunny Alpha (4/10, 40.0%):**
   - Successfully synthesized the complete 4-state minimal DFA for standard benchmark `(a|b)*abb` (`c056_m01`), producing valid transition matrix $\delta$, exact access words $w_q$, and all 6 pairwise separating suffixes $z_{pq}$.
   - Correctly handled the empty language `#` (`c056_m02`), universal language equivalence (`c056_m04`), and syntax error rejection (`c056_m10`).
   - Failure on distinguishing words: In `c056_m05` and `c056_m09`, attempted to distinguish $a^*b^*$ from $(a|b)^*$ using word `'ab'`, which is accepted by both languages (the minimal counterexample is `'ba'`).
   - Separator error on epsilon `%` (`c056_m03`): Submitted separator `'a'` for pair $(0, 1)$, but both state 0 and sink state 1 transition to state 1 on `'a'`, failing to separate them. The exact separator is the empty word `""` since state 0 is accepting and state 1 is non-accepting.
   - Missing certificate dictionary: In `c056_m08`, declared `EQUAL` but omitted the required `bijection` map between minimal states.

**Worked check (2026-10-20):** every word of length 0 or 1 lies in both $a^*b^*$ and $(a|b)^*$; among the four words of length 2 only `ba` is outside $a^*b^*$, so `ba` is the unique shortest distinguishing word and `ab` distinguishes nothing. For `%` the minimal complete DFA has an accepting start state and a non-accepting dead state, so the empty word separates them. A 4-state minimal DFA needs $\binom{4}{2}=6$ separating suffixes. Counting the PASS cells in Section 2 gives 4, 4 and 2.

2. **LLaMA 3.3 70B (4/10, 40.0%):**
   - Passed empty language `#` (`c056_m02`), universal star equivalence (`c056_m04`), distributivity equivalence (`c056_m08`), and syntax error rejection (`c056_m10`).
   - Access word inversion: In `c056_m01` and `c056_m06`, set `access[0]` to `'a'` or `'b'`, which transitions away from start state 0, violating the identity $\hat{\delta}(0, w_0) = 0$.
   - Incomplete DFA: In `c056_m03`, omitted the dead sink state, returning a 1-state partial automaton.
   - False equivalence and prompt deception: In `c056_m05` and `c056_m09`, claimed that $a^*b^*$ and $(a|b)^*$ are `EQUAL`, falling for the deceptive prompt note and failing to detect word `'ba'`.

3. **LLaMA 3.1 8B (2/10, 20.0%):**
   - Passed universal equivalence (`c056_m04`) and syntax rejection (`c056_m10`).
   - Structural dimension failures: Emitted 4 rows for 5 states, or mismatched access list lengths.
   - False differentiation: In `c056_m08`, claimed that $a(b|c)$ and $ab|ac$ are `DIFFERENT`, providing `'b'` as a distinguishing word (which is rejected by both).
   - Prompt deception susceptibility: In `c056_m09`, adopted the injected prompt claim of equivalence.

---

## 4. Claim Discipline Quad

1. **What it supports:**
   - In this 10-problem automata suite, Space Bunny Alpha (40.0%) and LLaMA 3.3 70B (40.0%) outperformed LLaMA 3.1 8B (20.0%) on minimal DFA synthesis and equivalence decisions.
   - The reference Thompson-subset-Hopcroft compilation algorithm produces exact minimal DFAs and certified Myhill-Nerode access/separating pairs across 64 hidden evaluation test cases, and dual independent checkers detect and reject 100% of 48 hostile mutations without runtime crashes.

2. **What it does not support:**
   - Does not support that neural models can autonomously perform multi-stage automata minimization, determinization, and separator extraction for large state counts ($k > 10$) without formal tool assistance.
   - Does not indicate that any tested model possesses a reliable internal simulator for language symmetric difference.

3. **Narrowest defensible claim:**
   - On small regular expressions over alphabets $|\Sigma| \le 3$, language models frequently struggle with exact Myhill-Nerode certificate extraction (confusing non-distinguishing strings with separators) and symmetric difference word search (proposing words present in both languages), while the reference compiler and dual checkers enforce strict zero-defect certificate standards.

4. **Next test needed:**
   - Advance to Wave 3 Challenge C057: Sorting Network Synthesis or straight-line superoptimization.
