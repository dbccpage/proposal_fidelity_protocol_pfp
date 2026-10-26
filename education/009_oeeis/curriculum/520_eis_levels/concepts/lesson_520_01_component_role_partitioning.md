---
documentation_contract: symbol-game-documentation/v1
title: "Lesson 520.01: Level 01 Component Role Partitioning Walkthrough"
kind: pedagogical-lesson
track: 520
status: active
maturity: production
claim_status: verified
authority_effect: "None"
---

# Lesson 520.01: Level 01 Component Role Partitioning Walkthrough

**AuthorityEffect:** None.  
**Track:** 520  
**Topic:** Level 01: Decoupling the 7 Immune Roles

## 1. Pedagogical Objective
Verify the structural separation of the 7 immune roles (Spec, FixtureBank, EvaluationReceipt, ExternalDecision, Registry, ActivationProfile, Hit).

## 2. Key Concepts & Invariants
- AntiSkillSpecV2 constructor purity (status=PROPOSED, runtime_enforcement=False)
- Prohibition of adjunct repair hints in Specs, Hits, and Decisions
- Constructor purity rejecting direct admitted status instantiation

## 3. Architecture & Implementation Seam
```python
@dataclass(frozen=True)
class AntiSkillSpecV2:
    status: str = 'PROPOSED'
    runtime_enforcement: bool = False
```

## 4. Check for Understanding & Falsifiers
- Verify F-PROMPT-02: Instantiating AntiSkillSpecV2 with status='ADMITTED' raises ValueError.
- Verify F-IMMUNE-01: Direct creation of admitted Antibody raises AdmissionPurityError.

## 5. Laboratory Workbench
- Companion Workbench: [Interactive Laboratory Notebook](../notebooks/lesson_520_01_level_01_component_role_partitioning_walkthrough.ipynb)


---

## Companion Notebook

- [Launch Companion Laboratory Notebook](../notebooks/lesson_520_01_component_role_partitioning.ipynb)
