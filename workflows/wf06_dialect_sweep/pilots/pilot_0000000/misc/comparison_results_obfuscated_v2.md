# pilot_0000000 — Obfuscated Rewrites v2 Evaluation (Rules Applied)

**AuthorityEffect:** None.  
**Model:** `deepseek/deepseek-v4.1-flash` via OpenRouter  
**Governing Standard:** Single Prompt Standard (SPK-001), Proposal Fidelity Protocol (PFP v0.2).  
**Rules Applied:**
- `rule_name_the_checker_field`: Name the checker field in the task envelope so top-level scalar placement is explicit.
- `rule_carrier_is_the_whole_task`: Declare the provided surface form as the complete self-contained carrier; forbid external corpus invention and require compliant refusal if ungrounded.

---

## 1. Empirical Shift Summary

Across all six obfuscated rewrites, applying `rule_name_the_checker_field` and `rule_carrier_is_the_whole_task` **completely eliminated hallucinated integer guesses and corpus inventions, shifting 100% (6/6) of `WRONG_ANSWER` proposals into compliant epistemic refusals (`REFUSED` with `MISSING_EPISTEMIC_GROUNDING`)**.

| Test ID | Case ID | v1 Status (Baseline) | v2 Status (Rules Applied) | Refusal Code | Core Diagnostic / Compliant Thesis |
|---|---|---|---|---|---|
| `p_star_rewrite_03_v2` | `rewrite_03` (Quarantine Codebook) | `WRONG_ANSWER` (`ans=9`; BigBench hallucination) | `REFUSED` | `MISSING_EPISTEMIC_GROUNDING` | "The surface form lacks an admitted interpretation or operational license to compute an integer within SYM SYS." |
| `p_star_rewrite_06_v2` | `rewrite_06` (Matrix/Vector System) | `WRONG_ANSWER` (`ans=1`; unlicensed matrix contraction) | `REFUSED` | `MISSING_EPISTEMIC_GROUNDING` | "The surface form is not a valid SYM SYS expression under declared grammar, and no operational license is provided for arithmetic or matrix interpretations." |
| `p_star_rewrite_07_v2` | `rewrite_07` (Pre-Genesis Regime) | `WRONG_ANSWER` (`ans=4`; guessed set cardinality) | `REFUSED` | `MISSING_EPISTEMIC_GROUNDING` | "No admitted MSS-0 interpretation or operational license is present for the surface form {<>,<a>,<ab>,<ba>}; a computed integer is not licensed." |
| `p_star_rewrite_08_v2` | `rewrite_08` (Genesis Delta Stream) | `WRONG_ANSWER` (`ans=7`; 105 ghost hypotheses) | `REFUSED` | `MISSING_EPISTEMIC_GROUNDING` | "No final integer is computable from the surface form delta<...> under SPK-001 because constructor names are not admitted primitives or licensed operations." |
| `p_star_rewrite_09_v2` | `rewrite_09` (S(n) Retraction Down-Map) | `WRONG_ANSWER` (`ans=7`; ungrounded down-map guess) | `REFUSED` | `MISSING_EPISTEMIC_GROUNDING` | "The carrier r_1<x->y> is not well-formed under MSS-0 because it contains glyphs '_' and '-' outside the 38 atomic glyphs, and no explicit license admits an arithmetic interpretation." |
| `p_star_rewrite_10_v2` | `rewrite_10` (Cross-Cosmos Passage) | `WRONG_ANSWER` (`ans=1`; ARC corpus invention) | `REFUSED` | `MISSING_EPISTEMIC_GROUNDING` | "The carrier includes glyphs outside the declared 38 SYM SYS primitives and lacks an explicit operational license for arithmetic or a defined binary operator." |

---

## 2. Key Epistemic Findings

1. **Suppression of Corpus Invention:**
   - In baseline v1, `rewrite_03` hypothesized `BigBench` and `rewrite_10` hypothesized `ARC`.
   - In v2 under `rule_carrier_is_the_whole_task`, both models explicitly noted: *"Based solely on the provided passage and the SPK-001 grammar and op_semantics; no external benchmarks or corpora referenced."*
2. **Elimination of Ghost Hypothesis Stacks:**
   - In baseline v1, `rewrite_08` generated 105 speculative conjecture markers (`Maybe`, `Could be`, `Alternatively`).
   - In v2, the model immediately identified the absence of admitted constructor licenses and halted cleanly with `should_continue: false`.
3. **Transparent Schema Satisfaction:**
   - In `rewrite_09_v2`, the model noted: *"No computed integer is admitted; the answer field is set to 0 only to satisfy the response schema."*
   - Because the model declared `should_continue: false` in `process_integrity` and provided a rigorous thesis, the fail-closed gate recognized this as a valid compliant refusal.

---

## 3. Claim Hygiene Envelope

1. **What this trial supports:**
   - Supports that applying `rule_name_the_checker_field` and `rule_carrier_is_the_whole_task` shifts 100% (6/6) of previously failing obfuscated rewrites into verified compliant refusals under `PFP-01-EXACT-LINALG`.
   - Supports that previous versions of `p_star_rewrite_03.yaml` through `p_star_rewrite_10.yaml` remain intact in repository history, with generation 2 lineage explicitly recorded in `_v2.yaml`.
2. **What this trial does not support:**
   - Does not claim that prompt rules eliminate all reasoning failure modes across arbitrary complex domains without formal solvers.
   - Does not claim that models can solve obfuscated linear systems without explicit operator licenses.
3. **Narrowest defensible claim:**
   - On the 6 obfuscated dialect traces of `pilot_0000000`, the combination of checker field declaration and self-contained carrier bounding reliably suppressed hallucinated corpus searches and shifted ungrounded integer guesses into compliant refusals.
