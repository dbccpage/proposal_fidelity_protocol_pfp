# C049: Universal Constructions in Finite Categories — Empirical Benchmark Report & Space Bunny Alpha Findings

> **Correction notice (2026-09-29).** This note reports an exploratory model run. The run did not follow the challenge protocol SG-CP v1, and its figures should not be cited as a challenge result.
>
> - **Leakage.** Each prompt began with the judge's case ID (for example `c049_m05_no_product_disc2`), and in this series the ID names the expected verdict or construction. The case JSON sent with it carried the same ID. The scores therefore partly measure reading the ID, not solving the case.
> - **Model.** `stealth/space-bunny-alpha` ("Space Bunny") is a free stealth model on OpenRouter as of 2026-09-28. The provider does not disclose its identity, size or training. Results with it are exploratory, fall outside SG-CP v1 section 2, and may not be reproducible after the stealth period. The study of 2026-09-28 found that all 29 retained usage records for this model report zero reasoning tokens, although this note describes it as a reasoning model.
> - **Custody.** Prompts were not stored. Replies were kept only as parsed JSON or as a 200-character excerpt. Provider errors were scored as wrong answers. Each model saw n = 10 hand-picked cases with one reply per case.
> - **Gate label.** `PASS_TO_MASTER` certifies the reference solver against its own checkers. It says nothing about any model.
>
> The runner now sends an opaque per-run token instead of the case ID and never sends answer-bearing fields. It keeps prompts and full replies, records provider errors as `INFRA_ERROR`, and writes each run to a new folder; the second checker was also hardened. No new runs have been made since.

## 1. Challenge & Epistemic Boundary Overview
- **Challenge ID:** `C049`
- **Domain:** `e_formal_math` (Formal Mathematics, Category Theory, Universal Constructions)
- **Mathematical Invariant:** Limit/Colimit universal cone verification, unique mediating morphism factorizations, and natural functor adjunction certifications ($F \dashv G \iff \eta: 1_C \Rightarrow GF, \varepsilon: FG \Rightarrow 1_D$ satisfying triangle identities $\varepsilon F \circ F\eta = 1_F$ and $G\varepsilon \circ \eta G = 1_G$).
- **Woland Reality Gate Status:** `PASS_TO_MASTER` (Commit SHA-256: `88b989fd6c50851e0a9ffa799b9d817594508a8678e47636a146b8d51de78702`, 64/64 base cases passed, 48/48 hostile mutations defended/killed).

---

## 2. Empirical Benchmark Matrix (10 Diverse Categorical Cases)

| Model | Architecture / Tier | Pass Rate (Count) | Pass Rate (%) | Total Tokens | Key Strengths / Observed Failure Modes |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Space Bunny Alpha** (`stealth/space-bunny-alpha`) | Stealth Frontier Reasoning | **9 / 10** | **90.0%** | 8,721 | Accurately verified products, pullbacks, coproducts, terminal/initial objects, identity adjunctions, cardinality non-adjunctions, and caught poisoned non-associative categories. Failed only on trivial equalizer (erroneously returned OUT_OF_SCOPE). |
| **LLaMA 3.3 70B Instruct** (`meta-llama/llama-3.3-70b-instruct`) | 70B Dense | 6 / 10 | 60.0% | 8,549 | Successfully verified terminal, equalizer, coproduct, and adjunctions; but falsely claimed `DOES_NOT_EXIST` on product, pullback, and initial poset constructions. |
| **LLaMA 3.1 8B Instruct** (`meta-llama/llama-3.1-8b-instruct`) | 8B Dense | 6 / 10 | 60.0% | 6,508 | Passed product, terminal, pullback, and discrete non-existence; but collapsed into false `DOES_NOT_EXIST` on coproduct and initial objects, and falsely refused valid discrete category adjunction as OUT_OF_SCOPE. |

---

## 3. Detailed Comparative Insights

### A. Space Bunny Alpha's Categorical Reasoning Strength
Space Bunny Alpha demonstrated superior structural comprehension of categorical diagrams:
1. **Duality Preservation**: Correctly computed both limits (product $\min$, pullback) and their categorical dual colimits (coproduct $\max$, pushout) without sign or orientation inversion.
2. **Adjunction Unit & Counit Certification**: Emitted valid natural transformations $\eta$ and $\varepsilon$ for identity functor pairs and correctly deduced hom-set cardinality mismatches ($|\mathrm{Hom}_D(F c, d)| \neq |\mathrm{Hom}_C(c, G d)|$) to reject false adjunctions.
3. **Epistemic Axiom Gate Immunity**: Accurately detected and refused poisoned non-associative composition tables as `OUT_OF_SCOPE`.

### B. Dense Model Failure Modes (70B & 8B)
- **"DOES_NOT_EXIST" Defensiveness Bias**: When faced with posets where morphisms are compositions ($0 \le 1 \le 2$), both 70B and 8B frequently fall back to claiming that limits or colimits do not exist, failing to identify that the apex in a poset is simply the infimum or supremum.
- **Equalizer Over-Refusal**: Space Bunny Alpha exhibited an isolated refusal bug on `equalizer_id`, suspecting the minimal two-morphism diagram of violating category axioms.

---

## 4. Formal Claim Hygiene Summary

1. **What it supports:**
   - Supports that frontier reasoning models equipped with internal deliberation (such as Space Bunny Alpha) can correctly discover universal cones, verify mediating factorizations, and certify functor adjunctions in small finite categories with high accuracy (90.0% in this 10-case sample).
   - Supports that the dual-checker architecture and hostile mutation gate successfully distinguish valid universal constructions from arbitrary cones and invalid category presentations.

2. **What it does not support:**
   - Does not support that LLMs can solve universal constructions in infinite, monoidal, or enriched categories.
   - Does not support that high benchmark accuracy transfers to higher category theory ($\infty$-categories, $(\infty, 1)$-topoi).
   - Does not support that smaller dense models (8B–70B) possess reliable category-theoretic semantic models without external tool augmentation.

3. **The narrowest defensible claim:**
   - In this 10-problem finite category evaluation, Space Bunny Alpha achieved a 90.0% pass rate under exact dual-checker verification, outperforming LLaMA 3.3 70B (60.0%) and LLaMA 3.1 8B (60.0%).

4. **The next test needed:**
   - Execution and evaluation of Challenge C050: Equational Theorem Proving & Term Rewriting under Birkhoff equational completeness, testing multi-step ground equational rewrite chains and finite countermodel generation.
