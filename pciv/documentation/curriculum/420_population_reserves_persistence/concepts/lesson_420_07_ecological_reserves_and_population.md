---
documentation_contract: symbol-game-documentation/v1
title: "Lesson 420.07: Ecological Reserves & Population: Largest-Remainder Allocation"
kind: pedagogical-lesson
track: 420
level: 7
status: active
maturity: production
claim_status: verified
authority_effect: "None"
---

# Lesson 420.07: Ecological Reserves & Population: Largest-Remainder Allocation

**AuthorityEffect:** None.  
**Track:** 420 (Reserves, Security & Ecology)  
**Level Source:** Level 07 ([`level_07_ecological_reserves_and_population.md`](../../levels/level_07_ecological_reserves_and_population.md))  
**Rust Seam:** [`core_prompt_civilization::forge`](../../../../engine/crates_rs/core_prompt_civilization/src/forge.rs)

## 1. Pedagogical Objective
Analyze how population quotas are allocated across disjoint reserve buckets (Frontier $3/5$, Unmeasured $1/4$, Baseline $3/20$) via the largest-remainder method to prevent monoculture and competitive release.

## 2. Key Concepts
1. **Disjoint Ecological Reserves:** Working populations are partitioned to maintain diverse exploration reserves.
2. **Largest-Remainder Allocation:** Exact discrete seat distribution allocating fractional remainders deterministically.
3. **Core Falsifier (`F-BIO-05`):** High-scoring frontier candidates cannot cannibalize the unmeasured or baseline reserve allocations.

## 3. Check for Understanding
- Why is an explicit reserve quota maintained for unmeasured prompt candidates?
- How does largest-remainder allocation prevent integer rounding loss when partitioning population caps?

## 4. Laboratory Workbench
- Companion Workbench: [Interactive Laboratory Notebook](../notebooks/lesson_420_07_ecological_reserves_and_population.ipynb)
