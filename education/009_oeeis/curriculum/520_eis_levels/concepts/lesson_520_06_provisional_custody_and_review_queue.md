---
documentation_contract: symbol-game-documentation/v1
title: "Lesson 520.06: Level 06 Provisional Custody & Review Queue Walkthrough"
kind: pedagogical-lesson
track: 520
status: active
maturity: production
claim_status: verified
authority_effect: "None"
---

# Lesson 520.06: Level 06 Provisional Custody & Review Queue Walkthrough

**AuthorityEffect:** None.  
**Track:** 520  
**Topic:** Level 06: Diagnostic Scope & Queue Fencing

## 1. Pedagogical Objective
Enforce provisional custody boundaries, ensuring provisional antibodies yield FINDING telemetry only and never write ACTIVE state.

## 2. Key Concepts & Invariants
- Provisional antibody arms FINDING disposition only
- HOLD and REFUSE dispositions strictly require HumanAdmitted external decision
- F-CUSTODY-01 preventing provisional detector from modifying registry state

## 3. Architecture & Implementation Seam
```python
def evaluate_provisional(disposition):
    if disposition in ('HOLD', 'REFUSE'):
        raise AuthorityError('Provisional detectors cannot emit HOLD or REFUSE')
    return 'FINDING'
```

## 4. Check for Understanding & Falsifiers
- Verify F-CUSTODY-01: Provisional detector emitting HOLD raises AuthorityError.
- Verify registry state write blocked for non-admitted detectors.

## 5. Laboratory Workbench
- Companion Workbench: [Interactive Laboratory Notebook](../notebooks/lesson_520_06_level_06_provisional_custody_&_review_queue_walkthrough.ipynb)


---

## Companion Notebook

- [Launch Companion Laboratory Notebook](../notebooks/lesson_520_06_provisional_custody_and_review_queue.ipynb)
