---
documentation_contract: symbol-game-documentation/v1
title: "Lesson 520.08: Level 08 Regulatory Supervision & Reversible Anergy Walkthrough"
kind: pedagogical-lesson
track: 520
status: active
maturity: production
claim_status: verified
authority_effect: "None"
---

# Lesson 520.08: Level 08 Regulatory Supervision & Reversible Anergy Walkthrough

**AuthorityEffect:** None.  
**Track:** 520  
**Topic:** Level 08: Treg False-Positive Oversight & Epoch Proposals

## 1. Pedagogical Objective
Verify the TregSupervisor false-positive oversight mechanism, emitting AnergyProposalV1 records to external queues without self-suspension.

## 2. Key Concepts & Invariants
- TregSupervisor false-positive monitoring
- Detectors never self-suspend (proposals emitted to external epoch queue)
- Reversible anergy state restoration

## 3. Architecture & Implementation Seam
```python
class TregSupervisor:
    def emit_anergy_proposal(self, detector_id, fp_rate):
        return AnergyProposalV1(detector_id, fp_rate)
```

## 4. Check for Understanding & Falsifiers
- Verify F-BIO-06: Detector self-suspension attempt raises ProtocolError.
- Verify AnergyProposalV1 payload format compliance.

## 5. Laboratory Workbench
- Companion Workbench: [Interactive Laboratory Notebook](../notebooks/lesson_520_08_level_08_regulatory_supervision_&_reversible_anergy_walkthrough.ipynb)


---

## Companion Notebook

- [Launch Companion Laboratory Notebook](../notebooks/lesson_520_08_regulatory_supervision_and_anergy.ipynb)
