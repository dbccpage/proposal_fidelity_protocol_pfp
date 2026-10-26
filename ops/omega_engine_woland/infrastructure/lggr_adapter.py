r"""Local Green Global Red (LGGR) gluing defect and detector adequacy adapter.

Implements the Evaluated Path Kernel (EPK) gluing defect and asymmetric verdict
soundness from LGGR I and II. The null-space criterion im(D) \cap K == {0} of LGGR V
is not decided here: the caller passes the native `lggr_v::check_soundness` verdict.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from omega_engine_woland.domain.swarm_models import JointKernelVerdictV1, LggrGluingResult


class LggrGluingAdapter:
    """Evaluates evaluator gluing boundaries and detector adequacy certificates."""

    def evaluate_boundary(
        self,
        local_evaluators: Dict[str, int],
        global_evaluator: int,
        corpus_samples: Optional[List[Tuple[Dict[str, int], int]]] = None,
        joint_kernel: Optional[JointKernelVerdictV1] = None,
    ) -> LggrGluingResult:
        """Evaluates Delta_E = E_G - prod(E_i) and audits detector adequacy."""
        local_vals = list(local_evaluators.values())
        prod_local = 1
        for v in local_vals:
            prod_local *= int(v)

        gluing_delta = int(global_evaluator) - prod_local

        # Verdict classification (matching omega_local_green_global_red_lggr/src/verdict.rs)
        if gluing_delta == -1:
            verdict_name = "NegativeGluingDefect_LocalGreenGlobalRed"
            interpretation = (
                "Sound as a detection (LGGR II §3.1). Local evaluators all passed (Local Green), "
                "yet global end-to-end evaluation failed (Global Red). Non-factorization is exhibited."
            )
        elif gluing_delta == 1:
            verdict_name = "PositiveGluingDefect"
            interpretation = (
                "Positive gluing defect. Global composite succeeded while a local evaluator failed. "
                "Suggests local over-constraint, redundancy, or test harness fragility."
            )
        else:
            verdict_name = "ZeroDefectResidual"
            interpretation = (
                "Concordant boundary. Either both local and global passed, or both failed. "
                "WARNING: If all-green, this is UNSOUND as a certificate without an explicit "
                "Detector Adequacy Certificate proving im(D) \\cap K == {0} (LGGR V §4 Theorem 4)."
            )

        # Audit the 11 detector adequacy criteria
        adequacy_failures: List[str] = []

        if not corpus_samples:
            adequacy_failures.append("AdequacyUndeclared: No sample corpus provided to test detector discrimination")
            adequacy_failures.append("CapacityEvidenceMissing: Zero test trajectories evaluated")
        else:
            # Check for constant evaluator failure
            if len(corpus_samples) < 5:
                adequacy_failures.append(f"InsufficientTrajectories: Only {len(corpus_samples)} samples (minimum 5 required)")

            # Check if local evaluators ever toggle (non-vacuousness)
            for k in local_evaluators.keys():
                vals = [s[0].get(k, 0) for s in corpus_samples]
                if len(set(vals)) <= 1:
                    adequacy_failures.append(f"DegenerateWatcher: Evaluator '{k}' is constant across all corpus samples")

        # Null-space soundness im(D) \cap K == {0}: the native verdict, never a caller flag.
        if joint_kernel is None:
            adequacy_failures.append("AdequacyUndeclared: no (D, Q) pair supplied for the joint-kernel check")
            null_space_sound = False
        elif not joint_kernel.sound:
            adequacy_failures.append(
                "BlindSpotIntersection: rank(Q·D) = %d < rank(D) = %d; witness v has D·v != 0 and Q·D·v = 0"
                % (joint_kernel.qd_rank, joint_kernel.d_rank)
            )
            null_space_sound = False
        else:
            null_space_sound = True

        adequacy_certified = len(adequacy_failures) == 0

        return LggrGluingResult(
            local_evaluators=dict(local_evaluators),
            global_evaluator=int(global_evaluator),
            local_product=prod_local,
            gluing_defect_delta=gluing_delta,
            verdict_name=verdict_name,
            detector_adequacy_certified=adequacy_certified,
            adequacy_failures=adequacy_failures,
            null_space_soundness_satisfied=null_space_sound,
            interpretation=interpretation,
            native_evidence=None if joint_kernel is None else {"joint_kernel": joint_kernel.to_dict()},
        )
