"""Checked finite examples and historical-proposal audit. No live model calls.

Each example states the outcome the certificate gate must return. A mismatch is
printed as FAIL and makes run_demo2() return False.
"""
from __future__ import annotations

from certificate_gate import BqnfCertificateGate


def _check(label: str, observed_status: str, observed_valid: bool, expected_status: str, expected_valid: bool) -> bool:
    ok = observed_status == expected_status and observed_valid is expected_valid
    print(f"{'OK  ' if ok else 'FAIL'} {label}: status={observed_status}, admitted={observed_valid}")
    return ok


def run_demo2() -> bool:
    print("DEMO 2: checked certificate routes (finite fixtures; no Hubbard classification claim)")
    results = []

    stoquastic = BqnfCertificateGate("stoquastic", {"hamiltonian_matrix": [[0, -1], [-1, 0]]})
    identity = stoquastic.verify_sign_free({"xi_witness": {"mapping": "identity"}})
    results.append(_check("Identity pseudo-witness", identity.status, identity.valid,
                          "Refused_UnverifiedInvolution_IdentityNotSignReversing", False))
    positivity = stoquastic.verify_sign_free({"route": "positivity"})
    results.append(_check("Checked positivity", positivity.status, positivity.valid, "Positivity", True))

    hopping = [[0, -1, -1], [-1, 0, -1], [-1, -1, 0]]
    for u in (0, -2):
        gate = BqnfCertificateGate("c3_triangular", {"U": u, "h_up": hopping, "h_down": hopping, "mu_up": 0, "mu_down": 0})
        result = gate.verify_sign_free({"representation": "determinant", "route": "determinantal_positivity"})
        results.append(_check(f"U={u} determinant theorem", result.status, result.valid, "DeterminantalPositivity", True))

    toy = BqnfCertificateGate("finite_toy", {"configuration_weights": {"negative": "-1/2", "positive": "1/2", "residue": 2}})
    pairing = toy.verify_sign_free({"representation": "finite_signed", "route": "exact_cancellation",
                                    "xi_witness": {"pairs": {"negative": "positive", "positive": "negative"}}})
    results.append(_check("Finite toy pairing", pairing.status, pairing.valid, "ExactCancellation", True))

    repulsive = BqnfCertificateGate("repulsive_hubbard", {"U": 2})
    status, admitted, _ = repulsive.verify_proposal_item({"move_type": "OPEN_SIGN_OBSTRUCTION", "reason": "Repulsive Hubbard is NP-hard"})
    results.append(_check("Generic hardness is not an instance proof", status, admitted, "Refused_UnverifiedObstruction", False))

    c3 = BqnfCertificateGate("c3_triangular", {"t": 1, "U": 2, "beta": "1/4", "mu": 0, "bonds": [(0, 1), (1, 2), (2, 0)]})
    status, admitted, _ = c3.verify_proposal_item({"move_type": "OPEN_SIGN_OBSTRUCTION",
                                                   "obstruction_witness": {"type": "alternating_site_gauge", "cycle": [0, 1, 2]}})
    results.append(_check("Alternating gauge obstruction (gauge only)", status, admitted, "OpenGaugeObstruction", True))
    status, admitted, _ = c3.verify_proposal_item({"move_type": "OPEN_SIGN_OBSTRUCTION",
                                                   "obstruction_witness": {"type": "c3_integrated_path_gap"}})
    results.append(_check("Integrated sequence obstruction (designated path)", status, admitted, "OpenSignObstruction", True))

    print("Historical model outputs remain in results/*.jsonl; these examples are deterministic fixtures.")
    passed = all(results)
    print(f"DEMO 2 {'PASSED' if passed else 'FAILED'}: {sum(results)}/{len(results)} expected outcomes")
    return passed


if __name__ == "__main__":
    raise SystemExit(0 if run_demo2() else 1)
