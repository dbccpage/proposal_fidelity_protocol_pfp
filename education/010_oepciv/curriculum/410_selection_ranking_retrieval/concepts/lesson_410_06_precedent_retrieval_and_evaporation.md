---
documentation_contract: symbol-game-documentation/v1
title: "Lesson 410.06: Precedent Retrieval & Evaporation: Lexicographic Matching"
kind: pedagogical-lesson
track: 410
level: 6
status: active
maturity: production
claim_status: verified
authority_effect: "None"
---

# Lesson 410.06: Precedent Retrieval & Evaporation: Lexicographic Matching

**AuthorityEffect:** None.  
**Track:** 410 (Selection, Ranking & Retrieval)  
**Level Source:** Level 06 ([`level_06_precedent_retrieval_and_evaporation.md`](../../levels/level_06_precedent_retrieval_and_evaporation.md))  
**Rust Seam:** [`omega_prompt_civilization::matching`](../../../../omega_engine/crates_rs/omega_prompt_civilization/src/matching.rs)

## 1. Pedagogical Objective
Examine how precedent precedents are retrieved via lexicographic domain matching and decayed over epoch half-lives $H$.

## 2. Key Concepts
1. **Lexicographic Matching:** Matches domain tags, task signatures, and context keys deterministically.
2. **Pheromone Evaporation:** Precedent citation weights undergo half-life decay $W(t) = W_0 \cdot (1/2)^{t/H}$ per epoch.
3. **Core Falsifier (`F-BIO-04`):** Retrieving a precedent reuses the precedent's individual age; it cannot rejuvenate or reset the global mass decay clock.

## 3. Check for Understanding
- Why must precedent retrieval be deterministic rather than probabilistic?
- How does half-life evaporation prevent stale precedents from dominating active populations?

## 4. Laboratory Workbench
- Companion Workbench: [Interactive Laboratory Notebook](../notebooks/lesson_410_06_precedent_retrieval_and_evaporation.ipynb)
