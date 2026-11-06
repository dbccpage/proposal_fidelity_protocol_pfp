"""
DDC (Discrete Deformation Calculus) Tracer for C043 Ramsey & Van der Waerden Constructions.
Alphabet: {E, R, C, I, Lambda, D, M, T}.
"""

from typing import Any, Dict, List


class DDCTracer:
    """Records operational steps in the DDC alphabet."""

    def __init__(self, case_id: str):
        self.case_id = case_id
        self.trace: List[Dict[str, Any]] = []

    def record_c(self, problem_type: str, bounds: Dict[str, Any], fixed_count: int):
        """C: Constraints and bounds exposed."""
        self.trace.append(
            {"op": "C", "problem_type": problem_type, "bounds": bounds, "fixed_count": fixed_count}
        )

    def record_i(self, seed_name: str, initial_colours: str):
        """I: Initial candidate injection from algebraic seed or heuristic."""
        self.trace.append({"op": "I", "seed_name": seed_name, "sample_len": len(initial_colours)})

    def record_r(self, defect_count: int, phi1: int):
        """R: Obstruction residual / monochromatic structure count."""
        self.trace.append({"op": "R", "monochromatic_structures": defect_count, "phi_1": phi1})

    def record_d(self, move_type: str, delta_phi: int):
        """D: Descent step in search / relabelling."""
        self.trace.append({"op": "D", "move_type": move_type, "delta_phi": delta_phi})

    def record_lambda(self, lift_reason: str):
        """Lambda: Structural lift (e.g. seed family swap Paley -> local search -> SAT)."""
        self.trace.append({"op": "Lambda", "lift_reason": lift_reason})

    def record_e(self, final_status: str, certificate_sha256: str = ""):
        """E: Terminal evaluation."""
        self.trace.append(
            {"op": "E", "status": final_status, "certificate_sha256": certificate_sha256}
        )

    def record_t(self):
        """T: Trace termination."""
        self.trace.append({"op": "T"})

    def get_summary_letters(self) -> str:
        """Return the sequence of operational letters as a string, e.g. 'CIDET'."""
        return "".join(step["op"][0] for step in self.trace)
