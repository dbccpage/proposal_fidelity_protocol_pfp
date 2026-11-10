# Canonical 11-Stage PFP Pipeline Architecture

**AuthorityEffect:** `None`  
**Standard:** Ground Truth Verification and Claim Hygiene Standard  
**Source Files:** `pfp/use_cases/pfp_stages.py`, `pfp/domain/stages/stages.py`, `pfp/domain/stages/host_stages.py`, `pfp/gate.py`  

---

## 1. Overview and Design Invariants

The Canonical 11-Stage Proposal Fidelity Protocol (PFP) Pipeline provides a structured evaluation harness for complex scientific and mathematical proposals. Implemented primarily in `pfp/use_cases/pfp_stages.py` (`RunPfpPipelineUseCase`) and `pfp/domain/stages/stages.py`, the pipeline orchestrates interactions between untrusted model turns and deterministic host verifiers.

The pipeline enforces five foundational invariants:

1. **`AuthorityEffect: None`:** Model text holds zero intrinsic authority. No model turn can declare a claim "verified" or "proven". Acceptance requires deterministic execution of host checks.
2. **Strict Host/Model Separation:** Stages are explicitly partitioned into Host stages (executed deterministically by host runtime code) and Model stages (executed by language model dispatch). Host stages never delegate verification to models.
3. **Formal Panel Seat Attribution:** Model interactions are assigned to specialized panel seats with distinct adversarial and checking responsibilities.
4. **Deterministic Terminal Computation:** Terminal states (`VERIFIED`, `VERIFIED_WITH_RESIDUALS`, `OPEN_OBSTRUCTION`, `BLOCKED_BY_EVIDENCE`) are computed strictly from host evaluation facts by `finish()`, never read from model fields.
5. **Kinetic Proofreading:** Evaluated candidate digests are tracked by `CandidateEvaluationGateV1`. Re-evaluation of rejected proposals raises `STAGE_REENTRY_REFUSED`, preventing circular repair loops.

---

## 2. The 11 Pipeline Stages

The pipeline sequence comprises Stages 1 through 11:

```
[1. ADMIT] (Host)
    |
    v
[2. IDEATION] (Model: seat_gauge_breaker / PROPOSER)
    |
    v
[3. AUDIT] (Model: seat_defect_hunter / AUDITOR)
    |
    v
[4. L2_EXTRACTION] (Model: seat_gauge_breaker / PROPOSER)
    |
    v
[5. EVALUATION] (Host: seat_adversary / CHECKER)  <--- MUST EMIT PASS
    |
    +---- (If Failed) ----> [BLOCKED_BY_EVIDENCE] (Terminal Stop)
    |
    v
[6. ADVERSARIAL] (Model: seat_primal_dual / ADVERSARY)
    |
    v
[7. CHALLENGE_REPLAY] (Host: Replays Adversary Witnesses)
    |
    v
[8. SELECTION] (Host: seat_manuscript_truth / SYNTHESIZER)
    |
    v
[9. RECEIPT] (Host: Cryptographic Sealing & Terminal Assignment)
    |
    v
[10. HAND_OFF] (Host: Artifact Packaging)
    |
    v (Conditional)
[11. EVIDENCE_PLAN] (Model: Diagnostic-Only Planning)
```

### Stage Specification Matrix

| Stage | Name | Executor | Panel Seat | Minimum Inputs | Function | Host Failure Outcome |
|:---:|:---|:---:|:---|:---:|:---|:---|
| **1** | `ADMIT` | Host | None (Plumbing) | None | Ingress validation; audits task schema and declarations. Dispatches model only if declaration repair is needed. | Refusal if unparseable |
| **2** | `IDEATION` | Model | `seat_gauge_breaker` | (1) | Proposes initial candidate hypotheses, formal claims, and proof sketches. | N/A (Model output) |
| **3** | `AUDIT` | Model | `seat_defect_hunter` | (2) | Red-team review of candidate proposals for triviality, false assumptions, or gauge defects. | N/A (Model output) |
| **4** | `L2_EXTRACTION` | Model | `seat_gauge_breaker` | (3) | Lowers candidate claims to typed operad operations, concrete spans, bindings, and preservation invariants. | N/A (Model output) |
| **5** | `EVALUATION` | Host | `seat_adversary` | (2, 4) | Deterministic host execution of exact mathematical checkers and schemas. Must emit `PASS`. | `BLOCKED_BY_EVIDENCE` |
| **6** | `ADVERSARIAL` | Model | `seat_primal_dual` | (4, 5) | Constructs adversarial countermodels, stress cases, and potential obstruction witnesses. | N/A (Model output) |
| **7** | `CHALLENGE_REPLAY` | Host | None (Plumbing) | (4, 5, 6) | Host independently replays adversary witnesses against candidate. Detects open obstructions. | Identifies `OPEN_OBSTRUCTION` |
| **8** | `SELECTION` | Host | `seat_manuscript_truth` | (5, 7) | Filters candidate set: retains Stage 5 survivors that successfully resisted Stage 7 obstructions. | Empty survivor set |
| **9** | `RECEIPT` | Host | None (Plumbing) | (1, 5, 7) | Computes final terminal state, records remaining obligations, signs execution receipt. | Invalidation on mismatch |
| **10** | `HAND_OFF` | Host | None (Plumbing) | (9) | Packages verified artifacts and audit traces for downstream consumption. | Packaging error |
| **11** | `EVIDENCE_PLAN` | Model | Optional | (9) | Dispatched only if Stage 9 marks receipt `diagnostic_only`; outlines next tests. | Skipped if verified |

---

## 3. Specialized Panel Seats

Panel seats define distinct responsibilities within the evaluation council. They map directly to `council_layout_v1.json`:

1. **`PROPOSER` (`seat_gauge_breaker` - Stages 2 & 4):**
   - Responsible for generating novel candidate proposals and translating informal claims into structured L2 operad candidates.
   - Constrained to output typed JSON envelopes; prohibited from self-attesting verification.
2. **`AUDITOR` (`seat_defect_hunter` - Stage 3):**
   - Operates as an internal model-based inspection turn.
   - Searches for obvious surface defects, missing boundary cases, or unstated premises before formal host evaluation.
3. **`CHECKER` (`seat_adversary` - Stage 5):**
   - While named `seat_adversary` in the council configuration, Stage 5 is executed strictly by deterministic host code.
   - Evaluates exact integer equality, rational graph defects, or formal proof checkers (e.g. Lean 4, Coq, or Python exact checkers).
   - Serves as the primary filter: if Stage 5 fails, the pipeline immediately halts with `BLOCKED_BY_EVIDENCE`.
4. **`ADVERSARY` (`seat_primal_dual` - Stage 6):**
   - Model seat tasked with falsification.
   - Proposes concrete counterexamples, dual witnesses, or parameter assignments intended to break the candidate passed at Stage 5.
5. **`SYNTHESIZER` (`seat_manuscript_truth` - Stage 8):**
   - Host-evaluated selection seat.
   - Reconciles candidate claims with adversarial replay outcomes, confirming that survivors possess zero unrefuted obstructions.

---

## 4. Deterministic Terminal States

The terminal disposition of any pipeline run is derived deterministically by `receipt_terminal(responses)` in `pfp/domain/stages/host_stages.py` and finalized in `RunPfpPipelineUseCase.finish()`:

### Terminal State Definitions

1. **`VERIFIED`:**
   - All mandatory acceptance stages `(1, 2, 3, 4, 5, 6, 7, 9)` ran to completion.
   - Stage 5 deterministic host check passed (`host_verdict == "PASS"` and `exact_checks_passed is True`).
   - Stage 7 challenge replay produced zero open obstructions.
   - Stage 9 receipt carries zero remaining unresolved obligations.
2. **`VERIFIED_WITH_RESIDUALS`:**
   - Stage 5 host checks passed, and Stage 7 revealed no fatal obstructions.
   - However, either non-critical obligations remain (e.g. `ADVERSARY_CHECKED_NOTHING`, indicating the adversary produced no valid test cases), or the run was stopped early after Stage 5 by explicit policy before completing all acceptance stages.
3. **`OPEN_OBSTRUCTION`:**
   - The candidate passed initial Stage 5 checks, but at Stage 7, one or more adversarial witnesses generated in Stage 6 were independently verified by the host to falsify the proposal.
   - Indicates an active counterexample exists against the candidate.
4. **`BLOCKED_BY_EVIDENCE`:**
   - The candidate failed deterministic host checks at Stage 5 (`host_verdict != "PASS"` or `exact_checks_passed is not True`), or an explicit stop occurred before achieving a Stage 5 pass.
   - Execution terminates immediately; later stages (6–11) are not dispatched.

---

## 5. Kinetic Proofreading (`CandidateEvaluationGateV1`)

To prevent futile loops and adversarial exhaustion, `pfp/gate.py` implements the kinetic proofreading gate `CandidateEvaluationGateV1` (enforcing protocol rule `F-BIO-02`):

```python
class CandidateEvaluationGateV1:
    def __init__(self, frozen_checker_set_id: str) -> None:
        self.frozen_checker_set_id = frozen_checker_set_id
        self._history: dict[str, EvaluationDisposition] = {}

    def record_verdict(self, candidate_digest: str, disposition: EvaluationDisposition) -> None:
        self._history[candidate_digest] = disposition

    def evaluate_candidate(self, candidate_digest: str) -> EvaluationDisposition:
        prior_verdict = self._history.get(candidate_digest)
        if prior_verdict == EvaluationDisposition.REJECTED:
            raise PermissionError(
                f"STAGE_REENTRY_REFUSED: Candidate {candidate_digest} was marked REJECTED "
                f"by frozen checker set {self.frozen_checker_set_id} and cannot be re-evaluated"
            )
        return prior_verdict or EvaluationDisposition.INCONCLUSIVE
```

### Operational Rules of the Gate
- **`REJECTED` Proposals:** Once a proposal's SHA-256 digest is marked `REJECTED` by a frozen checker set, any subsequent request to re-evaluate that exact proposal in the same generation triggers an immediate `PermissionError("STAGE_REENTRY_REFUSED")`.
- **`INCONCLUSIVE` Proposals:** Only candidates whose evaluation outcome was inconclusive (e.g. timeout or unverified boundary condition) are permitted to retry within declared budget limits.
- **Epistemic Function:** Prevents models from repeatedly resubmitting rejected candidates with minor cosmetic alterations, enforcing directional progress in the derivation search.

---

## 6. Claim Hygiene Evaluation

1. **What the Evidence Supports:**
   - The codebase supports the existence of an executable 11-stage pipeline architecture with deterministic host verification, terminal state derivation, and kinetic proofreading checks.
   - Host checks are genuinely independent: Stage 5 and Stage 7 execute deterministic Python logic that cannot be overridden by model assertions.
2. **What the Evidence Does Not Support:**
   - The pipeline does not guarantee that candidate generation will converge on valid solutions.
   - The absence of an open obstruction at Stage 7 does not constitute a universal mathematical proof; it only indicates that the specific adversarial witnesses generated in Stage 6 failed to falsify the candidate.
3. **Narrowest Defensible Claim:**
   - The canonical 11-stage pipeline implements a structured multi-role audit process where model proposals are filtered by host-executed tests, subjected to host-replayed adversarial countermodels, and classified into terminal states without granting authority to untrusted model text.
4. **Next Test Needed:**
   - Run the 11-stage pipeline end-to-end against a suite of 20 seeded mathematical claims (10 known-true, 10 known-false), and verify that all 10 false claims terminate in either `BLOCKED_BY_EVIDENCE` or `OPEN_OBSTRUCTION`.
