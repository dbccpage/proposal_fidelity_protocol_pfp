---
documentation_contract: symbol-game-documentation/v1
title: "Lesson 420.08: Lineage Taint & Custody Invalidation: Causal vs Global"
kind: pedagogical-lesson
track: 420
level: 8
status: active
maturity: production
claim_status: verified
authority_effect: "None"
---

# Lesson 420.08: Lineage Taint & Custody Invalidation: Causal vs Global

**AuthorityEffect:** None.  
**Track:** 420 (Reserves, Security & Ecology)  
**Level Source:** Level 08 ([`level_08_lineage_taint_and_custody_invalidation.md`](../../levels/level_08_lineage_taint_and_custody_invalidation.md))  
**Rust Seam:** [`omega_prompt_civilization::immunity`](../../../../omega_engine/crates_rs/omega_prompt_civilization/src/immunity.rs)

## 1. Pedagogical Objective
Distinguish between forward causal lineage taint (propagating quarantine forward along descendant subtrees) and global rule custody disarming (disarming broken system directives across all nodes).

## 2. Key Concepts
1. **Forward Causal Lineage Taint:** Discovered defects or sycophancy in a parent genome taint all forward causal descendants in the Inheritance DAG.
2. **Global Rule Custody Invalidation:** Invalidating a system rule disarms the rule globally without erasing causal lineage history.
3. **Core Falsifier (`F-RES-07`):** Forward taint calculation must compute the exact forward causal fixpoint without leaking onto collateral ancestor branches.

## 3. Check for Understanding
- What differentiates causal forward lineage taint from global custody disarming?
- How does the system quarantine a compromised prompt subtree without invalidating un-compromised sibling branches?

## 4. Laboratory Workbench
- Companion Workbench: [Interactive Laboratory Notebook](../notebooks/lesson_420_08_lineage_taint_and_custody_invalidation.ipynb)
