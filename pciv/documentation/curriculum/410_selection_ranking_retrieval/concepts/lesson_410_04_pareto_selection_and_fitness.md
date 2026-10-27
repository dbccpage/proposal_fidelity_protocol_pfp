---
documentation_contract: symbol-game-documentation/v1
title: "Lesson 410.04: Pareto Selection & Fitness: Multi-Objective Exact Evaluation"
kind: pedagogical-lesson
track: 410
level: 4
status: active
maturity: production
claim_status: verified
authority_effect: "None"
---

# Lesson 410.04: Pareto Selection & Fitness: Multi-Objective Exact Evaluation

**AuthorityEffect:** None.  
**Track:** 410 (Selection, Ranking & Retrieval)  
**Level Source:** Level 04 ([`level_04_pareto_selection_and_fitness.md`](../../levels/level_04_pareto_selection_and_fitness.md))  
**Rust Seam:** [`core_prompt_civilization::fitness`](../../../../engine/crates_rs/core_prompt_civilization/src/fitness.rs)

## 1. Pedagogical Objective
Evaluate prompt fitness as exact rational vectors over $\mathbb{Q}$ partitioned into non-dominated Pareto fronts, treating honest contract refusals as compliance rather than prompt failure.

## 2. Key Concepts
1. **Multi-Objective Rational Frontiers:** Fitness vectors are represented as exact pairs $(p/q) \in \mathbb{Q}$ across dimensions (accuracy, compliance, latency, cost).
2. **Pareto Dominance:** Candidate $A$ dominates $B$ if $A \ge B$ on all dimensions and $A > B$ on at least one.
3. **Core Falsifier (`F-SELECT-01`):** Floating-point rounding errors in fitness comparisons trigger strict rational precision refusals.

## 3. Check for Understanding
- Why are floating-point numbers forbidden in Pareto dominance evaluations?
- How does the system measure honest contract refusals as compliance?

## 4. Laboratory Workbench
- Companion Workbench: [Interactive Laboratory Notebook](../notebooks/lesson_410_04_pareto_selection_and_fitness.ipynb)
