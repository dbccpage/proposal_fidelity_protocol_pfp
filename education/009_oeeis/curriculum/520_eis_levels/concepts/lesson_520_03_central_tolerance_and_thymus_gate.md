---
documentation_contract: symbol-game-documentation/v1
title: "Lesson 520.03: Level 03 Central Tolerance & Thymus Gate Walkthrough"
kind: pedagogical-lesson
track: 520
status: active
maturity: production
claim_status: verified
authority_effect: "None"
---

# Lesson 520.03: Level 03 Central Tolerance & Thymus Gate Walkthrough

**AuthorityEffect:** None.  
**Track:** 520  
**Topic:** Level 03: Pinned Self-Panel Screening & Autoimmune Elimination

## 1. Pedagogical Objective
Demonstrate the Thymus Gate central tolerance screening, destroying any candidate detector that matches admitted self repository artifacts.

## 2. Key Concepts & Invariants
- Pinned Self-Panel Screening against admitted prompts, skills, and code
- Auto-reactive detector elimination prior to evaluation
- Regex miss never admits (elimination is negative filter only)

## 3. Architecture & Implementation Seam
```python
def thymus_screen(candidate_detector, self_panel):
    for artifact in self_panel:
        if candidate_detector.matches(artifact):
            return 'ELIMINATED'
    return 'CLEARED'
```

## 4. Check for Understanding & Falsifiers
- Verify F-IMMUNE-02: Candidate matching self-artifact triggers instant elimination.
- Verify regex miss on self-panel does not grant positive admission.

## 5. Laboratory Workbench
- Companion Workbench: [Interactive Laboratory Notebook](../notebooks/lesson_520_03_level_03_central_tolerance_&_thymus_gate_walkthrough.ipynb)


---

## Companion Notebook

- [Launch Companion Laboratory Notebook](../notebooks/lesson_520_03_central_tolerance_and_thymus_gate.ipynb)
