---
documentation_contract: symbol-game-documentation/v1
title: "Lesson 400.00: Governed Prompt Material vs Execution Occurrence"
kind: pedagogical-lesson
track: 400
level: 0
status: active
maturity: production
claim_status: verified
authority_effect: "None"
---

# Lesson 400.00: Governed Prompt Material vs Execution Occurrence

**AuthorityEffect:** None.  
**Track:** 400 (Prompt Civ Foundations)  
**Level Source:** Level 00 ([`level_00_substrate_and_packaging.md`](../../levels/level_00_substrate_and_packaging.md))  
**Rust Seam:** [`core_prompt_civilization::record`](../../../../engine/crates_rs/core_prompt_civilization/src/record.rs)

## 1. Pedagogical Objective
Distinguish between canonical governed prompt material (`PromptGenomeV1`) and execution instances (`ExecutionOccurrenceV1`), enforcing identity hash integrity under `core-sorted-json-no-float-v1`.

## 2. Key Concepts
1. **Governed Material vs Occurrence:** Executing an unchanged prompt string 1,000 times generates 1,000 occurrences but exactly **one** immutable genome.
2. **Genome Identity Envelope:** `prompt_id` is computed as SHA-256 over canonical JSON excluding timestamps, runtime metrics, and execution history.
3. **Canalized Core & Plastic Scaffold:** System framing and type fences are canalized; plastic scaffolds permit governed mutation.

## 3. Check for Understanding
- Why are timestamps and execution metrics excluded from `prompt_id` computation?
- How does `F-GENOME-02` prevent genome ID inflation upon prompt re-execution?

## 4. Laboratory Workbench
- Companion Workbench: [Interactive Laboratory Notebook](../notebooks/lesson_400_00_substrate_and_packaging.ipynb)
