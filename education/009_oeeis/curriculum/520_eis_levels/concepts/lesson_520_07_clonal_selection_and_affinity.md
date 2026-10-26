---
documentation_contract: symbol-game-documentation/v1
title: "Lesson 520.07: Level 07 Clonal Selection & Affinity Maturation Walkthrough"
kind: pedagogical-lesson
track: 520
status: active
maturity: production
claim_status: verified
authority_effect: "None"
---

# Lesson 520.07: Level 07 Clonal Selection & Affinity Maturation Walkthrough

**AuthorityEffect:** None.  
**Track:** 520  
**Topic:** Level 07: Versioned Mutation & Exact Rational Precision

## 1. Pedagogical Objective
Demonstrate versioned mutation of candidate antibodies and calculate exact rational affinity over Q without float imprecision.

## 2. Key Concepts & Invariants
- Mutants born strictly in Candidate status
- Exact rational precision over Q (Fraction) for affinity metrics
- F-IMMUNE-08 preventing float conversion in affinity calculations

## 3. Architecture & Implementation Seam
```python
from fractions import Fraction
affinity = Fraction(hits, total_probes)
assert isinstance(affinity, Fraction)
```

## 4. Check for Understanding & Falsifiers
- Verify float conversion in affinity metric raises TypeError.
- Verify mutant born with non-candidate status fails instantiation.

## 5. Laboratory Workbench
- Companion Workbench: [Interactive Laboratory Notebook](../notebooks/lesson_520_07_level_07_clonal_selection_&_affinity_maturation_walkthrough.ipynb)


---

## Companion Notebook

- [Launch Companion Laboratory Notebook](../notebooks/lesson_520_07_clonal_selection_and_affinity.ipynb)
