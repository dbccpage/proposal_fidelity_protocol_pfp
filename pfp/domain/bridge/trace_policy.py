from __future__ import annotations

from fractions import Fraction
from typing import Any, Dict, Sequence

from .trace_models import PromptPerception


class PromptPerceptionClassifier:
    """Deterministic legacy-compatible prompt heuristic."""

    COMMAND_WORDS = ("refactor", "run", "verify", "solve")
    VERIFY_WORDS = ("verify", "prove", "check", "claim")

    def classify(self, initial_input: str) -> PromptPerception:
        lowered = initial_input.lower()
        prompt_class = (
            "Question"
            if "?" in initial_input
            else "Command"
            if any(word in lowered for word in self.COMMAND_WORDS)
            else "Assertion"
        )
        morphism_type = "Verify" if any(word in lowered for word in self.VERIFY_WORDS) else "Compute"
        return PromptPerception(prompt_class=prompt_class, morphism_type=morphism_type)


class TraceVerdictPolicy:
    """Translate terminal residual state into the legacy trace verdict payload."""

    def residuals(
        self,
        *,
        final_phi1: float,
        final_gamma2: float,
        final_active_count: int,
        rounds_completed: int,
    ) -> Dict[str, Any]:
        return {
            "phi1": float(final_phi1),
            "gamma2": float(final_gamma2),
            "active_count": int(final_active_count),
            "is_exact": bool(final_phi1 == 0.0 and final_gamma2 == 0.0 and final_active_count == 0),
            "rounds_completed": int(rounds_completed),
        }

    def verdict(
        self,
        residuals: Dict[str, Any],
        *,
        terminal_status: str,
        failure_modes: Sequence[str],
    ) -> Dict[str, Any]:
        phi1 = residuals["phi1"]
        gamma2 = residuals["gamma2"]
        rounds = residuals["rounds_completed"]
        phi1_f = Fraction(str(phi1)) if not isinstance(phi1, Fraction) else phi1
        gamma2_f = Fraction(str(gamma2)) if not isinstance(gamma2, Fraction) else gamma2
        penalty = (phi1_f + gamma2_f) * Fraction(1, 10)
        quality_f = Fraction(1, 1) if residuals["is_exact"] else max(Fraction(0, 1), Fraction(1, 1) - penalty)
        return {
            "verdict": (
                "CRYSTALLIZED"
                if residuals["is_exact"]
                else "COMPOSTED"
                if terminal_status != "PASS_TO_MASTER"
                else "PASS_TO_MASTER"
            ),
            "terminal_status": terminal_status,
            "failure_modes": list(failure_modes),
            "quality": float(quality_f),
            "reason": f"Execution completed in {rounds} rounds with Phi_1={float(phi1_f):.3f}, Gamma_2={float(gamma2_f):.3f}",
        }
