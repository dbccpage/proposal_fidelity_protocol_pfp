"""Triangle teaching runtime, separate from the native Symbol Game host.

This model checks a declared triangle circulation only. It does not compute
the native Phi1, Gamma2, or Xi functionals or certify arbitrary assertions.
"""

from fractions import Fraction
from typing import Any, Dict, List


class EducationalHostGovernor:
    """Minimal educational implementation of the Symbol Game Host Governor."""

    def __init__(
        self, vertices: List[int], edges: List[str], initial_claims: Dict[str, int], fuel: int = 10
    ):
        if (
            set(vertices) != {0, 1, 2}
            or len(vertices) != 3
            or any(type(v) is not int for v in vertices)
            or set(edges) != {"0->1", "1->2", "2->0"}
            or len(edges) != 3
            or set(initial_claims) != set(edges)
            or type(fuel) is not int
            or fuel < 0
        ):
            raise ValueError(
                "This teaching board requires the complete directed triangle and nonnegative integer fuel"
            )
        self.vertices = set(vertices)
        self.edges = set(edges)
        self.claims = {e: self._rational(v) for e, v in initial_claims.items()}
        self.initial_fuel = fuel
        self.fuel = fuel
        self.is_terminal = False
        self.terminal_status = None
        self.history = []
        self.invariants = set()
        self._checkpoints = [(dict(self.claims), set(self.invariants))]
        self.events = []

    @staticmethod
    def _rational(value):
        if type(value) not in (int, str, Fraction):
            raise ValueError(
                "Use an integer, rational string, or Fraction; floats and booleans are refused"
            )
        return Fraction(value)

    def _checkpoint(self):
        self._checkpoints.append((dict(self.claims), set(self.invariants)))

    def compute_cycle_holonomy(self, cycle: List[str], orientations: List[int]) -> Fraction:
        """Compute the signed circulation around a directed cycle."""
        return sum(Fraction(orientations[i]) * self.claims[edge] for i, edge in enumerate(cycle))

    def compute_total_defect(self) -> Fraction:
        """Compute Phi_1 on the standard triangle 0->1, 1->2, 2->0."""
        # For a standard directed cycle 0->1, 1->2, 2->0:
        return abs(self.compute_cycle_holonomy(["0->1", "1->2", "2->0"], [1, 1, 1]))

    def execute_move(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a move proposal against the discrete governor."""
        if self.is_terminal:
            return {
                "decision": "REFUSED_TERMINAL_STATE",
                "message": "Board is in sealed terminal state",
                "fuel_remaining": self.fuel,
            }

        if self.fuel <= 0:
            return {
                "decision": "REFUSED_FUEL_EXHAUSTED",
                "message": "Zero turn fuel remaining",
                "fuel_remaining": 0,
            }

        self.fuel -= 1
        if type(proposal) is not dict:
            return {"decision": "REFUSED_MALFORMED_SYNTAX", "fuel_remaining": self.fuel}
        move_type = proposal.get("move_type")
        payload = proposal.get("payload", {})
        if type(payload) is not dict:
            return {"decision": "REFUSED_MALFORMED_SYNTAX", "fuel_remaining": self.fuel}
        self.events.append({"move": move_type, "fuel_remaining": self.fuel})

        if move_type == "ASSERT":
            relation = payload.get("relation")
            if type(relation) is not str or not relation:
                return {"decision": "REFUSED_MALFORMED_SYNTAX", "fuel_remaining": self.fuel}
            self.invariants.add(relation)
            self.history.append({"move": "ASSERT", "relation": relation})
            self._checkpoint()
            return {
                "decision": "ADMITTED",
                "defect_phi1": str(self.compute_total_defect()),
                "fuel_remaining": self.fuel,
            }

        elif move_type == "CUT":
            proposed_claims = payload.get("proposed_claims", {})
            if type(proposed_claims) is not dict or not proposed_claims:
                return {"decision": "REFUSED_MALFORMED_SYNTAX", "fuel_remaining": self.fuel}

            # Carrier boundary check
            for edge in proposed_claims.keys():
                if edge not in self.edges:
                    return {
                        "decision": "REFUSED_CARRIER_DOMAIN",
                        "message": f"Edge {edge} not in pinned carrier",
                        "fuel_remaining": self.fuel,
                    }

            # Monotonicity check (Lyapunov descent)
            old_defect = self.compute_total_defect()
            candidate = dict(self.claims)
            try:
                for edge, val in proposed_claims.items():
                    candidate[edge] = self._rational(val)
            except (ValueError, TypeError, ZeroDivisionError):
                return {"decision": "REFUSED_MALFORMED_SYNTAX", "fuel_remaining": self.fuel}
            new_defect = abs(sum(candidate.values(), Fraction(0)))

            if new_defect >= old_defect:
                # Violates strict descent: atomic rollback
                return {
                    "decision": "REFUSED_MONOTONICITY_VIOLATION",
                    "message": f"Proposed defect {new_defect} does not strictly decrease from {old_defect}",
                    "current_defect": str(old_defect),
                    "fuel_remaining": self.fuel,
                }

            # Admitted
            self.claims = candidate
            self.history.append({"move": "CUT", "new_defect": str(new_defect)})
            self._checkpoint()
            return {
                "decision": "ADMITTED",
                "defect_phi1": str(new_defect),
                "fuel_remaining": self.fuel,
            }

        elif move_type == "VERIFY":
            defect = self.compute_total_defect()
            if defect == 0:
                self.is_terminal = True
                self.terminal_status = "ACCEPTED_ZERO_DEFECT"
                return {
                    "decision": "ACCEPTED_ZERO_DEFECT",
                    "defect_phi1": "0",
                    "fuel_remaining": self.fuel,
                    "receipt": {
                        "status": "CERTIFIED",
                        "scope": "educational-directed-triangle-circulation-only",
                        "native_host": False,
                        "turns_used": self.initial_fuel - self.fuel,
                        "history_depth": len(self.history),
                    },
                }
            return {
                "decision": "REFUSED_NONZERO_DEFECT",
                "defect_phi1": str(defect),
                "fuel_remaining": self.fuel,
            }

        elif move_type == "RETRACT":
            target = payload.get("target_step", max(0, len(self._checkpoints) - 2))
            if type(target) is not int or not 0 <= target < len(self._checkpoints):
                return {"decision": "REFUSED_UNKNOWN_CHECKPOINT", "fuel_remaining": self.fuel}
            claims, invariants = self._checkpoints[target]
            self.claims, self.invariants = dict(claims), set(invariants)
            self.history.append({"move": "RETRACT", "target_step": target})
            self._checkpoint()
            return {"decision": "ADMITTED", "fuel_remaining": self.fuel}

        return {"decision": "REFUSED_UNKNOWN_MOVE", "fuel_remaining": self.fuel}
