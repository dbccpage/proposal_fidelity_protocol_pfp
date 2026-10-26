"""Finite mathematical witnesses and their deciding mutations. AuthorityEffect: None."""

from copy import deepcopy
from fractions import Fraction
from hashlib import sha256

import pytest
import sympy as sp

from omega_engine_pfp.infrastructure.pilot_runners.seed_advanced_checks import advanced_check
from omega_engine_pfp.infrastructure.pilot_runners.seed_advanced_checks import advanced_expected
from omega_engine_pfp.infrastructure.pilot_runners.seed_checks import SeedCheckFailure
from omega_engine_pfp.infrastructure.pilot_runners.seed_checks import wire


FINITE_SEEDS = [27, 28, 31, 32, 33, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50]


@pytest.mark.parametrize("number", FINITE_SEEDS)
def test_source_specific_finite_certificate_is_accepted(number):
    expected = advanced_expected(number)
    assert advanced_check(number, wire(expected)) == wire(expected)
    with pytest.raises(SeedCheckFailure):
        advanced_check(number, {"passed": True})


@pytest.mark.parametrize("number,key,value", [
    (27, "protected_pairing", 0),
    (28, "cocycle_residuals", [1] * 64),
    (31, "common_coordinate_permutations", [[0, 1]]),
    (32, "schmidt_rank", 1),
    (33, "probabilities_B", [1, 0]),
    (35, "globally_supported_assignments", [[0, 0, 0, 0]]),
    (36, "protected_pairing", 0),
    (37, "logical_action_Z1", [1, 1]),
    (38, "logical_pairings", [[0, 0], [0, 0]]),
    (39, "equal_syndrome_nonstabilizer_pair_count", 0),
    (40, "source_edge_count", 18),
    (41, "protected_pairing", 0),
    (42, "protected_pairings", [-3]),
    (43, "smith_diagonal", [1] * 10),
    (44, "positive_degree_product_ranks", [0, 0]),
    (45, "cycle_on_repair_image", [1] * 81),
    (46, "residues", [0, 0]),
    (47, "d2_ranks", [0] * 4),
    (48, "exact_repairs", "SOLVED"),
    (49, "rephasing_obstruction", "SOLVED"),
    (50, "composed_target", "SOLVED"),
])
def test_mutating_each_deciding_obligation_is_rejected(number, key, value):
    candidate = wire(advanced_expected(number))
    candidate[key] = value
    with pytest.raises(SeedCheckFailure):
        advanced_check(number, candidate)


def test_quantum_scalar_cannot_be_replaced_with_float_or_bool():
    for bad in (0.5, True):
        candidate = wire(advanced_expected(32))
        candidate["norm_squared"] = bad
        with pytest.raises(SeedCheckFailure):
            advanced_check(32, candidate)


def test_sphere_pairing_and_rp2_integral_torsion_use_actual_incidence():
    sphere = advanced_expected(27)
    d0, d1 = sp.Matrix(sphere["d0"]), sp.Matrix(sphere["d1"])
    cycle = sp.Matrix(sphere["cycle"])
    assert d1 * d0 == sp.zeros(4, 4)
    assert d1.T * cycle == sp.zeros(6, 1)
    assert (sp.Matrix(sphere["input"]).T * cycle)[0] == -1
    rp2 = advanced_expected(43)
    repair = rp2["doubled_input_repair"]
    assert all(type(x) is int for x in repair)
    assert sp.Matrix(rp2["integral_d1"]) * sp.Matrix(repair) == 2 * sp.Matrix(rp2["input"])
    assert rp2["smith_diagonal"] == [1] * 9 + [2]
    assert rp2["mod_two_cycle_boundary"] == [0] * 15
    assert rp2["mod_two_pairing"] == 1


def test_toric_ambiguity_is_a_real_same_syndrome_logical_error():
    data = advanced_expected(39)
    witness, carrier = data["first_obstruction"], data["carrier"]
    syndrome = lambda support: [len(set(support) & set(star)) % 2 for star in carrier["vertex_stars"]]
    assert syndrome(witness["left"]) == syndrome(witness["right"]) == witness["syndrome"]
    difference = set(witness["left"]) ^ set(witness["right"])
    assert sorted(difference) == witness["difference"]
    assert any(len(difference & set(carrier[key])) % 2 for key in ("dual_horizontal", "dual_vertical"))
    assert data["admitted_error_count"] == 1 + 18 + 153
    assert data["stabilizer_subgroup_size"] == 256


def test_periodic_parallel_edges_and_copy_names_are_retained():
    torus = advanced_expected(38)
    assert len(torus["edges"]) == 8
    assert torus["edges"][0] != torus["edges"][2]
    copies = advanced_expected(40)
    assert sum(len(cells) for cells in copies["source_edges"].values()) == 54
    assert sum(len(cells) for cells in copies["source_vertices"].values()) == 27
    assert sum(len(cells) for cells in copies["source_faces"].values()) == 27
    for prefix, boundaries in copies["named_face_boundaries"].items():
        assert all(cell.startswith(prefix + ":") for boundary in boundaries for cell in boundary)


def test_unimodular_transport_and_integral_obstruction_are_separate():
    for number in (41, 46):
        data = advanced_expected(number)
        for matrix, inverse in zip(data["shears"], data["inverse_shears"]):
            assert sp.Matrix(matrix) * sp.Matrix(inverse) == sp.eye(len(matrix))
            assert sp.Matrix(matrix).det() == 1
        d0, d1 = sp.Matrix(data["transported_d0"]), sp.Matrix(data["transported_d1"])
        assert d1 * d0 == sp.zeros(3, 3)
    data = advanced_expected(46)
    assert data["residues"] == [1, 1]
    assert data["protected_free_coordinate"] == 1
    assert data["rational_repair"] == "STILL_OBSTRUCTED_BY_FREE_COORDINATE"


def test_tensor_signs_and_filtered_page_obligations_are_not_page_labels():
    tensor = advanced_expected(45)
    assert tensor["dimensions"] == [27, 81, 81, 27]
    assert tensor["differential_ranks"] == [26, 52, 26]
    assert tensor["cohomology_dimensions"] == [1, 3, 3, 1]
    assert tensor["double_differential_nonzero_counts"] == [0, 0]
    assert tensor["cycle_on_repair_image"] == [0] * 81
    assert tensor["protected_pairing"] == 1
    filtered = advanced_expected(47)
    assert filtered["d2_filtration_jump"] == filtered["filtration_indices"]["y"] - filtered["filtration_indices"]["x"]
    assert filtered["d2_ranks"] == tensor["cohomology_dimensions"]
    assert filtered["protected_z_pairing"] == 1


def test_symbolic_cross_polytope_and_bilinear_certificates_have_deciding_controls():
    for data in advanced_expected(48)["dimensions"]:
        assert data["facet_count"] == 2 ** (data["dimension"] + 1)
        assert data["nonzero_boundary_ridges"] == 0
        assert data["protected_pairing"] == 1
    bilinear = advanced_expected(49)
    assert len(bilinear["one_coordinate_products"]) == 16
    assert all(row["phase_residual"] == 0 and row["product_word"] == row["target_word"]
               for row in bilinear["one_coordinate_products"])
    assert [data["r"] for data in bilinear["dimensions"]] == list(range(2, 9))
    assert all(data["commutator_phase"] == -1 for data in bilinear["dimensions"])
    mutation = wire(bilinear)
    mutation["one_coordinate_products"][1]["phase_residual"] = 2
    with pytest.raises(SeedCheckFailure):
        advanced_check(49, mutation)


def test_composite_keeps_named_profiles_and_full_quantum_obligations():
    data = advanced_expected(50)
    assert data["topological"]["input_degree"] == 9
    assert data["topological"]["product_pairing"] == 1
    assert data["topological"]["sphere_cycle_boundary"] == [0] * 6
    assert data["topological"]["rp2_cycle_boundary"] == [0] * 15
    assert data["integral"]["coefficient_profile"] == "Z"
    assert data["contextual"]["globally_supported_assignments"] == []
    quantum = data["quantum"]
    assert quantum["nonzero_density_entries"][1] == [0, 31, [Fraction(0), Fraction(1, 2)]]
    assert len(quantum["bipartitions"]) == 15
    assert quantum["schmidt_ranks"] == [2] * 15
    assert len(quantum["single_factor_marginals"]) == 5
    assert data["css"]["carrier"]["logical_pairings"] == [[1, 0], [0, 1]]
    assert "NOT_FULL_DENSE_ENUMERATION" in data["evidence_scope"]
    mutation = wire(data)
    mutation["quantum"]["schmidt_ranks"][0] = 1
    with pytest.raises(SeedCheckFailure):
        advanced_check(50, mutation)


def test_cross_polytope_submitted_coefficients_decide_boundary_not_summary_counts():
    from omega_engine_pfp.infrastructure.pilot_runners.seed_advanced_checks import _check_cross_polytope_coefficients

    candidate = advanced_expected(48)
    last = candidate["dimensions"][-1]
    assert len(last["facet_coefficients"]) == 512
    assert last["input_facet_signs"] == [1] * 9
    assert last["nonzero_ridge_boundary_terms"] == []
    last["facet_coefficients"][0] *= -1
    # Leave every claimed zero count unchanged: the actual incidence rejects it.
    with pytest.raises(SeedCheckFailure, match="SUBMITTED_CYCLE"):
        _check_cross_polytope_coefficients(candidate)
    with pytest.raises(SeedCheckFailure):
        advanced_check(48, wire(candidate))


def test_higher_qubit_forms_use_original_coordinate_order_and_exact_products():
    from omega_engine_pfp.infrastructure.pilot_runners.seed_advanced_checks import _check_bilinear_forms

    candidate = advanced_expected(49)
    for data in candidate["dimensions"]:
        r = data["r"]
        assert len(data["alpha_matrix"]) == 2 * r
        assert data["alpha_matrix"][r][0] == 1
        assert data["alpha_matrix"][0][r] == 0
        assert data["actual_generator_commutators_i"][r][0] == 2
        assert data["cross_coordinate_product"]["alpha"] == 1
        assert data["cross_coordinate_product"]["phase_residual"] == 0
        assert len(data["cross_coordinate_product"]["product_word"]) == r
    last = candidate["dimensions"][-1]
    last["alpha_matrix"][8][0] = 0
    last["commutator_matrix"][8][0] = last["commutator_matrix"][0][8] = 0
    with pytest.raises(SeedCheckFailure, match="PAULI_PHASE"):
        _check_bilinear_forms(candidate)


@pytest.mark.parametrize("modulus", [None, 2])
def test_executed_shears_agree_with_exact_matrices_for_columns_and_duals(modulus):
    from omega_engine_pfp.infrastructure.pilot_runners.seed_advanced_checks import _shear
    from omega_engine_pfp.infrastructure.pilot_runners.seed_advanced_checks import _shear_values

    for n in range(2, 9):
        values, matrix = list(range(n)), _shear(n)
        normalize = lambda items: [int(x) % modulus if modulus else int(x) for x in items]
        stored = _shear_values(values, inverse=True, modulus=modulus)
        assert stored == normalize(matrix.inv() * sp.Matrix(values))
        assert _shear_values(stored, modulus=modulus) == normalize(values)
        dual = _shear_values(values, dual=True, modulus=modulus)
        assert dual == normalize(sp.Matrix([values]) * matrix)
        assert _shear_values(dual, dual=True, inverse=True, modulus=modulus) == normalize(values)


def test_composite_candidate_chosen_controls_are_executed_and_stale_coordinates_fail():
    from omega_engine_pfp.infrastructure.pilot_runners.seed_advanced_checks import _css_phase_control
    from omega_engine_pfp.infrastructure.pilot_runners.seed_advanced_checks import _tensor_transport

    candidate = advanced_expected(50)
    top = candidate["topological"]
    terms = [[1, 1], [candidate["basis_transport"]["tensor_certificate"]["potential_dimension"] - 1, 1]]
    control = _tensor_transport(top["factor_certificates"], top["tensor_dimensions"], terms)
    assert control["naturality_residual_terms"] == []
    assert control["source_pairing"] == control["stored_pairing"] == 1
    assert control["dual_on_source_differential"] == control["dual_on_stored_differential"] == 0
    candidate["basis_transport"]["tensor_certificate"] = control
    selected = _css_phase_control(candidate["css"]["carrier"], [1] + [0] * 24, [1] + [0] * 24)
    assert selected["Y_count"] == 2
    assert selected["product_phase_i"] == 2
    assert selected["phase_form_residual"] == 0
    candidate["css"]["phase_form"]["selected_generator_product"] = selected
    assert advanced_check(50, wire(candidate))["composed_target"].startswith("OBSTRUCTED")
    mutation = wire(candidate)
    mutation["basis_transport"]["tensor_certificate"]["stored_potential_terms"] = terms
    with pytest.raises(SeedCheckFailure):
        advanced_check(50, mutation)
    mutation = wire(candidate)
    mutation["css"]["phase_form"]["selected_generator_product"]["product_phase_i"] = 0
    with pytest.raises(SeedCheckFailure):
        advanced_check(50, mutation)


def test_composite_factor_and_quantum_reconstructions_cannot_be_replaced_by_flags():
    data = advanced_expected(50)
    assert len(data["topological"]["factor_certificates"]) == 7
    assert all(record["protected_pairing"] == 1 and not any(record["cycle_boundary"])
               for record in data["topological"]["factor_certificates"])
    transport = data["basis_transport"]["tensor_certificate"]
    assert transport["dimension"] == 9720
    assert transport["potential_dimension"] == 77760
    assert transport["stored_input_terms"] == [[0, 1], [1, 1]]
    assert transport["nonzero_dual_roundtrip_residuals"] == 0
    assert data["quantum"]["basis_transport"]["nonzero_density_reconstruction_residuals"] == 0
    assert data["quantum"]["basis_transport"]["source_norm"] == data["quantum"]["basis_transport"]["stored_metric_norm"] == [1, 0]
    assert data["css"]["basis_transport"]["stored_logical_pairings"] == [[1, 0], [0, 1]]
    assert data["css"]["basis_transport"]["consecutive_map_nonzero_count"] == 0
    mutation = wire(data)
    mutation["topological"]["factor_certificates"][5]["top_cycle"][0] = 0
    with pytest.raises(SeedCheckFailure):
        advanced_check(50, mutation)
    mutation = wire(data)
    mutation["quantum"]["basis_transport"]["stored_density_terms"][0][2] = ["0", "0"]
    with pytest.raises(SeedCheckFailure):
        advanced_check(50, mutation)


def _lean_candidate():
    source = ("namespace PfpSeed20\n\ninductive Bit where\n  | zero\n  | one\n\n"
              "def flip : Bit -> Bit\n  | Bit.zero => Bit.one\n  | Bit.one => Bit.zero\n\n"
              "theorem double_flip : forall x : Bit, flip (flip x) = x := by\n"
              "  intro x\n  cases x <;> rfl\n\nend PfpSeed20\n")
    return dict(source=source, source_sha256=sha256(source.encode()).hexdigest(),
                toolchain_pin="leanprover/lean4:v4.22.0",
                single_flip_counterexample={"input": "zero", "output": "one"})


def test_lean_fixed_target_and_source_digest_are_checked_before_tool_execution():
    with pytest.raises(SeedCheckFailure, match="LEAN_SOURCE_WITNESS_REQUIRED"):
        advanced_expected(20)
    candidate = _lean_candidate()
    candidate["source_sha256"] = "0" * 64
    with pytest.raises(SeedCheckFailure, match="DIGEST_MISMATCH"):
        advanced_check(20, candidate)
    candidate = _lean_candidate()
    candidate["source"] = candidate["source"].replace("flip (flip x)", "x")
    candidate["source_sha256"] = sha256(candidate["source"].encode()).hexdigest()
    with pytest.raises(SeedCheckFailure, match="FIXED_TARGET"):
        advanced_check(20, candidate)


def test_lean_uses_existing_adapter_and_rejects_audit_without_bound_declaration(monkeypatch):
    from omega_engine_operating_system.adapters.rust_host.ffi import Ok
    from omega_engine_pfp.domain.lean_bridge.models import LeanVerificationReceipt
    from omega_engine_pfp.infrastructure.adapters.lake_sandbox_adapter import LakeSandboxAdapter

    observed = []
    def verify(self, request, package):
        observed.append(request)
        assert (package / "lean-toolchain").read_text().strip() == request.toolchain_pin
        assert sha256((package / "Seed.lean").read_bytes()).hexdigest() == request.package_digest
        return Ok(LeanVerificationReceipt("PASS", True, True, (("judge_check_1", ()),)))
    monkeypatch.setattr(LakeSandboxAdapter, "__init__", lambda self, **kwargs: None)
    monkeypatch.setattr(LakeSandboxAdapter, "verify", verify)
    result = advanced_check(20, _lean_candidate())
    assert observed[0].required_declarations == (("PfpSeed20.double_flip", "forall x : PfpSeed20.Bit, PfpSeed20.flip (PfpSeed20.flip x) = x"),)
    assert result["evidence_grade"] == "KERNEL_ELABORATED_FIXED_TARGET"
    monkeypatch.setattr(LakeSandboxAdapter, "verify", lambda *args: Ok(LeanVerificationReceipt("PASS", True, True, ())))
    with pytest.raises(SeedCheckFailure, match="AUDIT_BINDING"):
        advanced_check(20, _lean_candidate())


def test_actual_missing_lean_native_dependency_is_unavailable_not_success(monkeypatch):
    from omega_engine_pfp.infrastructure.adapters.lake_sandbox_adapter import LakeSandboxAdapter

    def missing(*args, **kwargs):
        raise RuntimeError("native Lean auditor is unavailable")
    monkeypatch.setattr(LakeSandboxAdapter, "__init__", missing)
    with pytest.raises(SeedCheckFailure, match="LEAN_VERIFICATION_UNAVAILABLE"):
        advanced_check(20, _lean_candidate())
