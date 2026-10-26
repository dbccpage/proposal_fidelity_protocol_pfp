# Empirical Findings: Challenge C056 DFA Minimization and Equivalence with Distinguishing Strings

> **Notice (2026-09-29): corrections and status of these results**
>
> The model `stealth/space-bunny-alpha` ("Space Bunny") is a free stealth model offered on OpenRouter since 2026-09-28; the provider does not disclose its identity, size or training. Results obtained with it are exploratory, fall outside the challenge protocol SG-CP v1 §2 (which requires identified models), and may not be reproducible after the stealth period. This note is kept as a record of what was run; its numbers are not challenge results.
>
> *How the runs were made.* Checked against `run_c056_matrix.py` as committed before this batch and the retained `empirical_results/matrix_results.json`. Prompts were not stored; responses were kept only as parsed JSON, or as a 200-character excerpt when parsing failed. Each prompt contained the case ID, and several IDs name the expected verdict (`c056_m04_equiv_equal_universal` expects `EQUAL`, `c056_m05_equiv_different_order` expects `DIFFERENT`, and `c056_m10_poison_unclosed_paren` expects `OUT_OF_SCOPE`), so pass counts are upper bounds under leaked labels. Each model answered each of ten hand-picked cases once, at temperature 0. The runner records a provider error as a failed case (see below). All 9 Space Bunny usage records report 0 reasoning tokens (`completion_tokens_details.reasoning_tokens`), although the note calls it a reasoning model.
>
> *API error counted as a failure.* Space Bunny's `c056_m06_minimize_parity` record carries `"error": "'choices'"`, a latency of 0.16 s and no output or usage: the provider's reply contained no answer. It is counted as a failed case in the 4/10 score; Space Bunny passed 4 of the 9 cases it answered.
>
> *Prompt.* The prompt did not define the symbols `#` (empty language) and `%` (empty word), which are the whole regular expressions of m02 and m03.
>
> *Checker defects (repaired in this batch).* Both checkers imported the reference solver (the exact checker its parser and DFA compiler, the independent checker its parser), so neither was independent of it. The independent checker confirmed `EQUAL` verdicts only by testing words up to length 4. In the retained records it accepted LLaMA 3.3 70B's one-state automaton for `%` (m03), which the exact checker rejected as having too few states. The repair uses an independent construction and an exact equivalence check.
>
> *Gate verdict.* The "commit-reveal" gate cited at the top of this note is a self-check: `commit_reveal_c056.py` hashes the reference solver and then evaluates the judge cases in the same process, so the commitment binds only the reference solver's files and does not show that the cases or checkers were fixed before the model runs. The verdict `PASS_TO_MASTER` and the hidden-case and mutation figures quoted below describe the reference solver checked by the package's own checkers; they are not results for any model.
>
> *Counts.* The retained JSON supports the table's pass counts (4/10, 4/10, 2/10), per-case times and token totals.
>
> The original note follows unchanged.

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
