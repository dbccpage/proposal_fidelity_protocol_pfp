---
documentation_contract: symbol-game-documentation/v1
title: "Lesson 520.00: Level 00 Innate Pharmacy Barriers Walkthrough"
kind: pedagogical-lesson
track: 520
status: active
maturity: production
claim_status: verified
authority_effect: "None"
---

# Lesson 520.00: Level 00 Innate Pharmacy Barriers Walkthrough

**AuthorityEffect:** None.  
**Track:** 520  
**Topic:** Level 00: The 12 Canonical Failure Classes in pharmacy.rs

## 1. Pedagogical Objective
Examine the 12 innate failure classes compiled in pure Rust (pharmacy.rs) and verify that clean reports never grant positive authority.

## 2. Key Concepts & Invariants
- 12 Innate Failure Classes (SelfCertification, FakeReceipt, ConclusionPreload, etc.)
- Clean Report Non-Admission (AuthorityEffect: None)
- Finding Structural Purity (zero repair fields)

## 3. Architecture & Implementation Seam
```python
from omega_engine.crates_rs import pharmacy
# Innate barrier detection
```

## 4. Check for Understanding & Falsifiers
- Verify F-BIO-07: Authority mimicry strings trigger SelfCertification or PersonaAuthorityLeak.
- Verify F-IMMUNE-01: Clean report has zero findings while is_admitted remains False.

## 5. Laboratory Workbench
- Companion Workbench: [Interactive Laboratory Notebook](../notebooks/lesson_520_00_level_00_innate_pharmacy_barriers_walkthrough.ipynb)


---

## Companion Notebook

- [Launch Companion Laboratory Notebook](../notebooks/lesson_520_00_innate_pharmacy_barriers.ipynb)
