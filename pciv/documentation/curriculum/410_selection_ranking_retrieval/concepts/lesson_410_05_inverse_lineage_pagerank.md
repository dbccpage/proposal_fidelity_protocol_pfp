---
documentation_contract: symbol-game-documentation/v1
title: "Lesson 410.05: Inverse Lineage PageRank: Certified Ancestral Utility"
kind: pedagogical-lesson
track: 410
level: 5
status: active
maturity: production
claim_status: verified
authority_effect: "None"
---

# Lesson 410.05: Inverse Lineage PageRank: Certified Ancestral Utility

**AuthorityEffect:** None.  
**Track:** 410 (Selection, Ranking & Retrieval)  
**Level Source:** Level 05 ([`level_05_inverse_lineage_pagerank.md`](../../levels/level_05_inverse_lineage_pagerank.md))  
**Rust Seam:** [`omega_prompt_civilization::rank`](../../../../omega_engine/crates_rs/omega_prompt_civilization/src/rank.rs)

## 1. Pedagogical Objective
Understand how ancestral utility is computed via an exact fixed-point certificate over $\mathbb{Q}$ under contract `omega.spectral.pagerank.v2`, allocating human review budget without minting proof authority.

## 2. Key Concepts
1. **Inverse Lineage Flow:** Importance flows *backward* from high-performing descendant prompts to credit foundational ancestor genomes.
2. **Exact Certificate over $\mathbb{Q}$:** Power iteration terminates only when exact rational duality gap certificates are satisfied.
3. **Core Falsifier (`F-RANK-01`):** PageRank scores serve strictly for review allocation; they never license automatic proof or promotion authority.

## 3. Check for Understanding
- Why does importance flow backward along the Inheritance DAG in Inverse PageRank?
- How does `F-RANK-01` enforce non-authoritative bounds on spectral ranking outputs?

## 4. Laboratory Workbench
- Companion Workbench: [Interactive Laboratory Notebook](../notebooks/lesson_410_05_inverse_lineage_pagerank.ipynb)
