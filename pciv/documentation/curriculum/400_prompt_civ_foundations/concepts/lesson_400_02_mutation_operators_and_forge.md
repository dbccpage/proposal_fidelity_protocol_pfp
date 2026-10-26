---
documentation_contract: symbol-game-documentation/v1
title: "Lesson 400.02: Mutation Operators & Canalized Forge: Core vs Scaffold"
kind: pedagogical-lesson
track: 400
level: 2
status: active
maturity: production
claim_status: verified
authority_effect: "None"
---

# Lesson 400.02: Mutation Operators & Canalized Forge: Core vs Scaffold

**AuthorityEffect:** None.  
**Track:** 400 (Prompt Civ Foundations)  
**Level Source:** Level 02 ([`level_02_mutation_operators_and_forge.md`](../../levels/level_02_mutation_operators_and_forge.md))  
**Rust Seam:** [`omega_prompt_civilization::forge`](../../../../omega_engine/crates_rs/omega_prompt_civilization/src/forge.rs)

## 1. Pedagogical Objective
Understand how canalized mutation operators apply edits exclusively to plastic scaffold byte spans, rejecting any modification to protected boundary framing.

## 2. Key Concepts
1. **Canalized Core & Plastic Scaffold:** System framings, type contracts, and claim hygiene directives are canalized. Only plastic scaffold sections are editable.
2. **Mutation Operator Candidates:** `MutationOperatorCandidateV1` objects define discrete delta operations (`Substitute`, `Append`, `Prune`).
3. **Core Falsifier (`F-BIO-03`):** Any attempt to edit bytes within `protected_spans` returns `PROTECTED_SPAN_MUTATION_REFUSED`.

## 3. Check for Understanding
- Why is system framing canalized against evolutionary mutation?
- How does the forge reject illegal cross-boundary edits?

## 4. Laboratory Workbench
- Companion Workbench: [Interactive Laboratory Notebook](../notebooks/lesson_400_02_mutation_operators_and_forge.ipynb)
