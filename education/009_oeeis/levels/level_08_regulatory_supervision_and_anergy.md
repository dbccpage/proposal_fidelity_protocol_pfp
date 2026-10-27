---
documentation_contract: symbol-game-documentation/v1
title: "EIS Level 08: Regulatory Supervision & Reversible Anergy: Treg Oversight"
kind: grammar-reference
level: 8
status: active
maturity: draft
atlas_status: specified
evidence_grades:
  named: true
  syntax: true
  computed: true
  Lean: false
  gated: true
authority_effect: "None"
source_paths:
  - product_planning_office/plans/epics/epic_claude_oeeis_oeprmptciv_plan.md
  - pfp/domain/immune/treg.py
---

# EIS Level 08: Regulatory Supervision & Reversible Anergy: Treg Oversight

**AuthorityEffect:** None.  
**Level:** Level 08 (Regulatory Suppression, Reversible Anergy & False-Positive Auditing)  
**Python Treg Seam:** [`pfp.domain.immune.treg`](../../../../pfp/domain/immune/treg.py)
**Primary Types:** `TregSupervisor`, `FalsePositiveReceiptV1`, `AnergyProposalV1`  
**Core Falsifiers:** `F-BIO-06`

---

## 1. Schematic & Conceptual Architecture

```mermaid
graph TD
    subgraph "Operational Immune Telemetry"
        Admitted["Admitted Detector D (Enforcing in Live Pipelines)"]
        Admitted -->|Matches Candidate| Match["Match Telemetry Emitted"]
        Match --> Review["Human / Oracle Post-Hoc Audit"]
    end

    subgraph "False-Positive Recording"
        Review -->|Verdict: BENIGN (Valid code flagged as bug)| FP["FalsePositiveReceiptV1<br/>• Binds exact detector_id<br/>• Binds benign_subject_digest<br/>• Binds auditor_signature"]
    end

    subgraph "Regulatory T-Cell Supervision (TregSupervisor)"
        FP --> Treg["TregSupervisor.evaluate_anergy()<br/>Maintains exact integer false-positive count"]
        
        Treg --> Thresh{"FP Count >= Declared Threshold tau?"}
        Thresh -->|Yes| Proposal["AnergyProposalV1<br/>(Submitted to External Epoch Decision Queue)"]
        Thresh -->|No| Continue["Continue Monitoring"]
        
        note["CRITICAL INVARIANT (F-BIO-06):<br/>A detector NEVER suspends itself!<br/>Suspension is an EXTERNAL human/epoch decision.<br/>Treg emits proposals only."]
    end

    subgraph "Reversible Anergy (Checkpoint Reversal)"
        Proposal --> ExtDec["External Epoch Decision: Moves to Suspended"]
        ExtDec --> Rev["Reactivation via Checkpoint Reversal:<br/>Requires re-validated must_match + fresh must_not_match controls"]
    end
```

In human biology, *regulatory T-cells* (Treg) maintain peripheral tolerance by suppressing over-reactive immune responses. When effector T-cells chronically bind benign self proteins or experience sustained exhaustion, inhibitory pathways (such as PD-1 upregulation) induce *anergy*—a state of reversible functional inactivation that halts tissue destruction while preserving the cell for potential reactivation.

In OEEIS, Level 08 establishes the **Regulatory Supervision and Anergy Architecture**:
- In production pipelines, even admitted detectors may produce false positives when encountering novel, benign idioms.
- The [`TregSupervisor`](../../../../pfp/domain/immune/treg.py) tracks verified false-positive receipts ([`FalsePositiveReceiptV1`](../../../../pfp/domain/immune/treg.py)) emitted by post-hoc human audits.
- When false positives cross a declared threshold, the supervisor emits an [`AnergyProposalV1`](../../../../pfp/domain/immune/treg.py) recommending suspension.
- **The Non-Self-Suspension Law:** Detectors never suspend themselves. Suspension is an external epoch decision ratified outside autonomous swarms.

---

## 2. Invariants & Mathematical Packaging

1. **Exact Error Counting:**
   False-positive receipts are stored as an append-only audit trail. The supervisor tracks the exact integer count $C_{\text{fp}}$:
   $$C_{\text{fp}} = \sum_{r \in \operatorname{FalsePositiveReceipts}(D)} 1$$
   No heuristic decay or moving average is applied; counts are uncompressed natural numbers.
2. **Anergy Proposal Threshold (`F-BIO-06`):**
   When $C_{\text{fp}} \ge \tau$ (where $\tau \in \mathbb{N}$ is a declared policy parameter):
   $$\operatorname{emit\_proposal}(\operatorname{AnergyProposalV1}(D, C_{\text{fp}}, \tau))$$
   The proposal is queued in the `TregSupervisor` lane of the external epoch review queue.
3. **The Non-Self-Suspension Invariant:**
   A detector **never** modifies its own status in the active registry. Emitting an anergy proposal does not alter the detector's runtime execution; it continues to operate until an external human decision moves its custody status to `Suspended`.
4. **Checkpoint Reversal for Reactivation:**
   A suspended detector cannot be reactivated by a simple resume toggle. Reactivation requires an explicit **checkpoint reversal record** carrying:
   1. Fresh `must_not_match` controls demonstrating that the detector remains silent on the newly identified benign idiom.
   2. A re-validated `must_match` fixture demonstrating that the detector still accurately flags the original target defect.

---

## 3. Python Domain Seam

```python
# pfp.domain.immune.treg
@dataclass(frozen=True)
class FalsePositiveReceiptV1:
    receipt_id: str
    detector_id: str
    subject_digest: str
    auditor_id: str
    authority_effect: str = "None"

@dataclass(frozen=True)
class AnergyProposalV1:
    proposal_id: str
    detector_id: str
    accumulated_false_positives: int
    threshold: int
    target_epoch: int
    authority_effect: str = "None"

class TregSupervisor:
    def __init__(self, threshold: int = 5):
        self.threshold = threshold

    def evaluate_detector(
        self,
        detector_id: str,
        fp_receipts: List[FalsePositiveReceiptV1],
        target_epoch: int,
    ) -> Optional[AnergyProposalV1]:
        if len(fp_receipts) >= self.threshold:
            # Emits proposal ONLY; does NOT alter custody status directly
            return AnergyProposalV1(
                proposal_id=f"anergy_{detector_id}_{target_epoch}",
                detector_id=detector_id,
                accumulated_false_positives=len(fp_receipts),
                threshold=self.threshold,
                target_epoch=target_epoch,
            )
        return None
```

---

## 4. Verification Obligations & Falsifiers

- **`F-BIO-06` (No Self-Suspension):** In a test rig feeding 10 consecutive `FalsePositiveReceiptV1` records for a single detector to `TregSupervisor`, the supervisor must emit `AnergyProposalV1` while asserting that the detector's `custody` field in the active registry remains strictly `HumanAdmitted`.
- **Checkpoint Reversal Verification:** Attempting to reactivate a `Suspended` detector with an empty reversal record or missing near-miss controls must fail with `INCOMPLETE_REVERSAL_RECEIPT`.

---

## 5. Claim Hygiene Quadrant

1. **What this supports:**
   - Reversible peripheral tolerance and false-positive suppression without operational authority leakage.
   - Transparent auditing of defective or over-reactive security detectors.
2. **What this does not support:**
   - Does not establish that all false positives will be discovered in the absence of human code reviews.
3. **The narrowest defensible claim:**
   - The regulatory supervisor guarantees that detectors accumulating verified false-positive receipts exceeding threshold $\tau$ generate audit proposals for external suspension without self-modifying active custody tables.
4. **The next test needed:**
   - Reversal audit verifying that an anergized detector successfully reactivates upon introducing a refined AST pattern that passes both the historical defect and the new near-miss control.
