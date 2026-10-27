---
documentation_contract: symbol-game-documentation/v1
title: "Lesson 400.03: Lamarckian Retro-Inheritance & Hop-Bounded Immunity"
kind: pedagogical-lesson
track: 400
level: 3
status: active
maturity: production
claim_status: verified
authority_effect: "None"
---

# Lesson 400.03: Lamarckian Retro-Inheritance & Hop-Bounded Immunity

**AuthorityEffect:** None.  
**Track:** 400 (Prompt Civ Foundations)  
**Level Source:** Level 03 ([`level_03_lamarckian_retro_inheritance.md`](../../levels/level_03_lamarckian_retro_inheritance.md))  
**Rust Seam:** [`core_prompt_civilization::immunity`](../../../../engine/crates_rs/core_prompt_civilization/src/immunity.rs)

## 1. Pedagogical Objective
Understand how typed phenotypic modifications—specifically antibody references derived from falsified execution receipts—propagate forward and backward across the Inheritance DAG with hop-bounded $(1/2)^d$ distance attenuation.

## 2. Key Concepts
1. **Lamarckian Adaptation:** Phenotypic failure receipts ($\Phi_1 > 0$, $\Gamma_2 > 0$) mint antibody rules that are retro-inherited by ancestors and descendants.
2. **Hop-Bounded Attenuation:** Retro-propagation extends at most $d \le 10$ edge hops. Weight decays as $(1/2)^d$ without horizon resetting.
3. **Core Falsifier (`F-IMMUNE-09`):** Intermediary nodes cannot reset the hop counter or re-amplify attenuated antibody weights.

## 3. Check for Understanding
- Why is retro-inheritance hop-bounded to $d \le 10$?
- How does geometric attenuation prevent distant ancestors from being overwhelmed by recent child failure antibodies?

## 4. Laboratory Workbench
- Companion Workbench: [Interactive Laboratory Notebook](../notebooks/lesson_400_03_lamarckian_retro_inheritance.ipynb)
