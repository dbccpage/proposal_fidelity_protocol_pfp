---
documentation_contract: symbol-game-documentation/v1
title: "Lesson 520.04: Level 04 Learned-Guard Two-Signal Activation Walkthrough"
kind: pedagogical-lesson
track: 520
status: active
maturity: production
claim_status: verified
authority_effect: "None"
---

# Lesson 520.04: Level 04 Learned-Guard Two-Signal Activation Walkthrough

**AuthorityEffect:** None.  
**Track:** 520  
**Topic:** Level 04: Conjunction & Two-Signal Collapse Prevention

## 1. Pedagogical Objective
Verify the two-signal activation conjunction law, preventing detector match from copying danger signals from itself.

## 2. Key Concepts & Invariants
- Signal-1: Detector pattern match on subject bytes
- Signal-2: Independent host danger signal from context
- TWO_SIGNAL_COLLAPSE rejection if danger signal is copied from detector match

## 3. Architecture & Implementation Seam
```python
def evaluate_activation(signal1_match, signal2_danger):
    if signal1_match and signal2_danger:
        return 'ACTIVATED'
    raise TwoSignalCollapseError('Missing independent danger signal')
```

## 4. Check for Understanding & Falsifiers
- Verify TWO_SIGNAL_COLLAPSE triggered when Signal-2 is missing or copied.
- Verify execution halt when learned guard is suspended.

## 5. Laboratory Workbench
- Companion Workbench: [Interactive Laboratory Notebook](../notebooks/lesson_520_04_level_04_learned-guard_two-signal_activation_walkthrough.ipynb)


---

## Companion Notebook

- [Launch Companion Laboratory Notebook](../notebooks/lesson_520_04_learned_guard_two_signal_activation.ipynb)
