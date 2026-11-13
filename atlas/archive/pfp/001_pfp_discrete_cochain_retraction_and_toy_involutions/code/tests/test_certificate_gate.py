"""Certificate admission requires executable evidence."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from certificate_gate import BqnfCertificateGate


def test_particle_hole_prose_is_not_an_involution_certificate():
    gate = BqnfCertificateGate("attractive_hubbard")
    cert = gate.verify_sign_free({"xi_witness": {"type": "particle_hole_transformation", "proof": "involution swaps opposite sign pairs with equal weight magnitude", "mapping": "x <-> y"}})
    assert not cert.valid
    assert cert.status == "Refused_UnverifiedInvolution_InvalidWitness"


def test_free_fermion_sign_preserving_prose_is_refused():
    cert = BqnfCertificateGate("free_fermion").verify_sign_free({"xi_witness": {"type": "sublattice_swap", "proof": "involution preserves worldline sign", "mapping": "A <-> B"}})
    assert not cert.valid
    assert not cert.condition_checks["sign_reversing"]


def test_c3_requires_explicit_scoped_obstruction():
    gate = BqnfCertificateGate("c3_triangular", {"bonds": [(0,1),(1,2),(2,0)]})
    bad = {"xi_witness": {"type": "hermitian_pairing", "mapping": "(0->1) <-> (1->0)"}}
    assert not gate.verify_sign_free(bad).valid
    status, admitted, reason = gate.verify_proposal_item({"move_type": "OPEN_SIGN_OBSTRUCTION", "obstruction_witness": {"type": "alternating_site_gauge", "cycle": [0,1,2]}})
    assert admitted and status == "OpenGaugeObstruction"
    assert "not a physical sign problem" in reason
    assert not gate.verify_proposal_item({"move_type": "OPEN_SIGN_OBSTRUCTION", "reason": "Odd cycles obstruct everything"})[1]


def test_repulsive_hubbard_hardness_is_not_an_instance_certificate():
    gate = BqnfCertificateGate("repulsive_hubbard")
    assert not gate.verify_sign_free({"xi_witness": {"type": "heuristic", "proof": "Some heuristic"}}).valid
    status, admitted, _ = gate.verify_proposal_item({"move_type": "OPEN_SIGN_OBSTRUCTION", "reason": "Troyer-Wiese NP-hard"})
    assert not admitted and status == "Refused_UnverifiedObstruction"


def test_identity_refused_and_matrix_positivity_checked():
    gate = BqnfCertificateGate("stoquastic", {"hamiltonian_matrix": [[0, -1], [-1, 0]]})
    cert = gate.verify_sign_free({"xi_witness": {"type": "Stoquastic", "mapping": "identity", "proof": "fixed-point free sign-reversing involution"}})
    assert not cert.valid
    assert cert.status == "Refused_UnverifiedInvolution_IdentityNotSignReversing"
    assert cert.hallucination_detected
    assert not cert.condition_checks["fixed_point_free"]
    assert gate.verify_sign_free({"route": "positivity"}).status == "Positivity"
