---
documentation_contract: symbol-game-documentation/v1
title: "Lesson 400.01: Lineage DAG & Causal Descent: Two-Graph Separation"
kind: pedagogical-lesson
track: 400
level: 1
status: active
maturity: production
claim_status: verified
authority_effect: "None"
---

# Lesson 400.01: Lineage DAG & Causal Descent: Two-Graph Separation

**AuthorityEffect:** None.  
**Track:** 400 (Prompt Civ Foundations)  
**Level Source:** Level 01 ([`level_01_lineage_dag_and_causal_descent.md`](../../levels/level_01_lineage_dag_and_causal_descent.md))  
**Rust Seam:** [`omega_prompt_civilization::genealogy`](../../../../omega_engine/crates_rs/omega_prompt_civilization/src/genealogy.rs)

## 1. Pedagogical Objective
Enforce the strict structural separation between the **Inheritance DAG** (causal mutation/descent) and the **Reference Graph** (associational citations).

## 2. Key Concepts
1. **Two-Graph Separation:** Causal mutation edges (`DirectMutation`, `Repair`, `Retry`) belong strictly to the Inheritance DAG. Precedent citations belong to the Reference Graph.
2. **Ancestral Rank Isolation:** Precedent reference citations never modify topological generation, parent links, or ancestral PageRank score.
3. **Core Falsifier (`F-LINEAGE-01`):** Injecting a reference citation edge into the inheritance DAG triggers an immediate topology refusal.

## 3. Check for Understanding
- Why is an associative reference citation forbidden from creating an edge in the Inheritance DAG?
- How does the Two-Graph separation guarantee acyclic causal lineage?

## 4. Laboratory Workbench
- Companion Workbench: [Interactive Laboratory Notebook](../notebooks/lesson_400_01_lineage_dag_and_causal_descent.ipynb)
