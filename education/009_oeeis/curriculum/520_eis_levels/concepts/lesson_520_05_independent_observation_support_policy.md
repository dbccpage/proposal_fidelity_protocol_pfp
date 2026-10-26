---
documentation_contract: symbol-game-documentation/v1
title: "Lesson 520.05: Level 05 Independent Observation Support Policy Walkthrough"
kind: pedagogical-lesson
track: 520
status: active
maturity: production
claim_status: verified
authority_effect: "None"
---

# Lesson 520.05: Level 05 Independent Observation Support Policy Walkthrough

**AuthorityEffect:** None.  
**Track:** 520  
**Topic:** Level 05: Causal Deduplication & Graph Support >= 3

## 1. Pedagogical Objective
Verify that candidate antibodies require at least 3 pairwise-uncorrelated observations across distinct causal host events before reaching provisional status.

## 2. Key Concepts & Invariants
- ObservationSupportPolicyV1 graph deduplication
- Host correlation key collapse (same model, prompt, or scaffold counts as 1)
- Support requirement >= 3 independent observations

## 3. Architecture & Implementation Seam
```python
def calculate_support(observations):
    unique_keys = set(obs.correlation_key for obs in observations)
    return len(unique_keys)
```

## 4. Check for Understanding & Falsifiers
- Verify F-SUPPORT-01: Duplicate correlation keys collapse to single observation.
- Verify support < 3 fails provisional promotion.

## 5. Laboratory Workbench
- Companion Workbench: [Interactive Laboratory Notebook](../notebooks/lesson_520_05_level_05_independent_observation_support_policy_walkthrough.ipynb)


---

## Companion Notebook

- [Launch Companion Laboratory Notebook](../notebooks/lesson_520_05_independent_observation_support_policy.ipynb)
