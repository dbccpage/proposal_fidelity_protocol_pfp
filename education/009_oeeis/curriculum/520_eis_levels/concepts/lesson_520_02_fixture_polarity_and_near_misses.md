---
documentation_contract: symbol-game-documentation/v1
title: "Lesson 520.02: Level 02 Fixture Polarity & Near Misses Walkthrough"
kind: pedagogical-lesson
track: 520
status: active
maturity: production
claim_status: verified
authority_effect: "None"
---

# Lesson 520.02: Level 02 Fixture Polarity & Near Misses Walkthrough

**AuthorityEffect:** None.  
**Track:** 520  
**Topic:** Level 02: must_match vs must_not_match Polarity Map

## 1. Pedagogical Objective
Enforce explicit mapping between triggering defect fixtures (must_match) and valid near-miss control fixtures (must_not_match).

## 2. Key Concepts & Invariants
- FixturePolarityMapV1 requiring non-empty must_match and must_not_match arrays
- Near-miss verification ensuring valid code never triggers anti-skill detectors
- Fixture digest verification for content-addressed immutability

## 3. Architecture & Implementation Seam
```python
class FixturePolarityMapV1:
    must_match: Tuple[str, ...]
    must_not_match: Tuple[str, ...]
```

## 4. Check for Understanding & Falsifiers
- Verify F-FIX-01: Empty must_not_match fixture set rejects detector registration.
- Verify F-FIX-02: Detector triggering on must_not_match near miss fails polarity validation.

## 5. Laboratory Workbench
- Companion Workbench: [Interactive Laboratory Notebook](../notebooks/lesson_520_02_level_02_fixture_polarity_&_near_misses_walkthrough.ipynb)


---

## Companion Notebook

- [Launch Companion Laboratory Notebook](../notebooks/lesson_520_02_fixture_polarity_and_near_misses.ipynb)
