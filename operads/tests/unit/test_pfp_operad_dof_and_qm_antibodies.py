"""Unit tests for the 3 QM/DFM review antibodies and PFP per-prompt operad DoF elimination.

Verifies:
1. Qualification controls, byte-identical spec projection, inert candidate status, and native Rust
   test bindings for:
   - `anti_scalar_proxy_theorem_substitution.yaml` (`ab_scalar_proxy_theorem_substitution`)
   - `anti_target_fitting_constant_compensation.yaml` (`ab_target_fitting_constant_compensation`)
   - `anti_witness_certificate_desynchronization.yaml` (`ab_witness_certificate_desynchronization`)
2. Per-prompt `OperadPromptBinding` degree-of-freedom elimination:
   - Rejects scalar-proxy theorem substitution when boundary falsifier witness is absent (`DOF_SCALAR_PROXY_SUBSTITUTION`).
   - Rejects target-fitting constant compensation when sub-channel pins mismatch or `free_parameter_count != 0` (`DOF_UNPINNED_SUBCHANNEL_COMPENSATION` / `DOF_NONZERO_FREE_PARAMETERS`).
   - Rejects cross-layer witness drift when `paper_witness`, `code_witness`, and `proof_witness` disagree (`DOF_WITNESS_CERTIFICATE_DESYNCHRONIZATION`).
3. Multi-stage derivation map operad collection (`collect_derivation_map_operads`):
   - Collects every prompt's operad operation and bound antibodies into a `ColouredOperad`.
   - Verifies type-safe partial composition across stages and `residual_degrees_of_freedom == 0` when all locks hold.

AuthorityEffect: None.
"""

from __future__ import annotations

import re
from fractions import Fraction
from pathlib import Path

import pytest
import yaml

from operads.domain.prompt_hierarchy import (
    AntibodyBinding,
    AntiOpBinding,
    OperadPromptBinding,
    PromptTreeNode,
    PromptUri,
    collect_derivation_map_operads,
    evaluate_prompt_gates,
    load_prompt_node_from_binding_dict,
)
from operads.infrastructure.prompt_hierarchy.genesis_relational_derivation import (
    COUPLED_BIPARTITE_BINDING_FILENAMES,
    TRIPARTITE_BINDING_FILENAMES,
    load_coupled_native_rust_and_lean4_witnesses,
    load_predeclared_relational_operad_locks,
    run_coupled_bipartite_relational_derivation_workflow,
    run_genesis_relational_derivation_workflow,
    run_tripartite_relational_derivation_workflow,
)
from operads.infrastructure.parser.prompt_hierarchy_loader import (
    load_prompt_node_from_pfp_yaml,
)


def _find_repo_root() -> Path:
    current = Path(__file__).resolve().parent
    for parent in [current, *current.parents]:
        if (parent / ".agents").is_dir() and (parent / "pyproject.toml").is_file():
            return parent
    raise RuntimeError("Could not find repository root")


REPO = _find_repo_root()


@pytest.mark.parametrize(
    "filename",
    [
        "anti_scalar_proxy_theorem_substitution.yaml",
        "anti_target_fitting_constant_compensation.yaml",
        "anti_witness_certificate_desynchronization.yaml",
    ],
)
def test_qm_dfm_antibody_candidates_have_deciding_controls_and_native_bindings(filename: str) -> None:
    source = REPO / ".agents/antibodies" / filename
    projection = REPO / ".agents/antibodies/specs" / filename
    assert source.is_file(), f"Missing antibody file {source}"
    assert projection.is_file(), f"Missing antibody spec projection {projection}"
    assert source.read_bytes() == projection.read_bytes()

    spec = yaml.safe_load(source.read_text(encoding="utf-8"))
    assert spec["schema_version"] == "core.immune.antibody-spec.v1"
    assert spec["pharmacy_status"] == "candidate"
    assert spec["authority_effect"] == "None"
    assert (
        "inert" in spec["qualification_limit"].lower()
        or "candidate scope" in spec["qualification_limit"].lower()
    )

    trigger = re.compile(spec["target_pattern"])
    assert spec["detection_mechanisms"]["regex_triggers"] == [spec["target_pattern"]]
    assert trigger.search(spec["adversarial_mutation_fixture"])
    assert not trigger.search(spec["repaired_invariant_fixture"])
    assert not trigger.search(spec["benign_control_fixture"])

    native = (REPO / spec["native_test_binding"]).read_text(encoding="utf-8")
    for name in spec["harmful_control_tests"] + spec["benign_control_tests"]:
        assert re.search(r"fn\s+" + re.escape(name) + r"\s*\(", native)

    impl_text = (REPO / spec["implementation_binding"]).read_text(encoding="utf-8")
    assert not trigger.search(impl_text)


def test_pfp_research_04_sidecar_collects_three_new_antibodies() -> None:
    fixture = (
        REPO
        / "operads"
        / "tests"
        / "fixtures"
        / "prompt_hierarchy"
        / "p_research_04.yaml"
    )
    node = load_prompt_node_from_pfp_yaml(fixture)
    antibody_ids = {ab.antibody_id for ab in node.antibodies}
    assert "ab_scalar_proxy_theorem_substitution" in antibody_ids
    assert "ab_target_fitting_constant_compensation" in antibody_ids
    assert "ab_witness_certificate_desynchronization" in antibody_ids


def test_operad_dof_locks_refuse_all_three_cheat_modes_and_pass_full_answer() -> None:
    binding_dict = {
        "prompt_uri": "prompt://physics/finite_qm/derivation/stage_04/P_QM_FULL_LOCK",
        "title": "Finite QM Operad-Locked Derivation Prompt",
        "oewas_anti_ops": [
            {
                "op_id": "pfp.refuse_scalar_proxy_theorem_substitution",
                "inspects_slot": "candidate_text",
                "refusal_code": "ANTI_SCALAR_PROXY",
            },
            {
                "op_id": "pfp.refuse_target_fitting_constant_compensation",
                "inspects_slot": "candidate_text",
                "refusal_code": "ANTI_TARGET_FITTING",
            },
            {
                "op_id": "pfp.refuse_witness_certificate_desynchronization",
                "inspects_slot": "candidate_text",
                "refusal_code": "ANTI_WITNESS_DRIFT",
            },
        ],
        "oeeis_antibodies": [
            {
                "antibody_id": "ab_scalar_proxy_theorem_substitution",
                "signal1_epitope": "three_ray_positivity_proxy",
                "signal2_required_danger": "PROXY_COUNTEREXAMPLE_SURVIVES",
            },
            {
                "antibody_id": "ab_target_fitting_constant_compensation",
                "signal1_epitope": "unpinned_additive_residual",
                "signal2_required_danger": "COMPONENT_PIN_MISMATCH",
            },
            {
                "antibody_id": "ab_witness_certificate_desynchronization",
                "signal1_epitope": "prose_certificate_witness_mismatch",
                "signal2_required_danger": "PROSE_WITNESS_FALSIFIED",
            },
        ],
        "operad_binding": {
            "operation_id": "pfp.certify_finite_qm_triad",
            "source_colours": ["Proof", "Code", "Paper"],
            "target_colour": "Receipt",
            "slot_to_colour": {
                "proof_witness": "Proof",
                "code_witness": "Code",
                "paper_witness": "Paper",
            },
            "required_slot_pins": ["ln_k0_2s_minus_2p", "two_loop_and_recoil_mhz"],
            "cross_slot_equality_groups": [
                ["paper_witness", "code_witness", "proof_witness"],
            ],
            "required_boundary_witness_slots": ["fourth_ray_counterexample_witness"],
            "equivariant": True,
            "residual_effect": "contractive",
        },
    }
    node = load_prompt_node_from_binding_dict(binding_dict)
    assert node.operad_binding is not None
    assert node.operad_binding.locked_constraint_count == 7

    unit_bloch_witness = (Fraction(3, 5), Fraction(4, 5), Fraction(0, 1))
    valid_pins = {
        "ln_k0_2s_minus_2p": Fraction(28417865, 10000000),
        "two_loop_and_recoil_mhz": Fraction(1654, 1000),
    }

    # 1. Cheat Mode A: Missing boundary counterexample witness (scalar proxy substitution)
    proxy_cheat_payload = {
        "candidate_text": "Scoped derivation with explicit assumptions.",
        "proof_witness": unit_bloch_witness,
        "code_witness": unit_bloch_witness,
        "paper_witness": unit_bloch_witness,
        "ln_k0_2s_minus_2p": Fraction(28417865, 10000000),
        "two_loop_and_recoil_mhz": Fraction(1654, 1000),
        "slot_pins": valid_pins,
        "free_parameter_count": 0,
        "fourth_ray_counterexample_witness": None,
    }
    r_proxy = evaluate_prompt_gates(node, proxy_cheat_payload)
    assert not r_proxy.passed
    assert r_proxy.refusal_code == "DOF_SCALAR_PROXY_SUBSTITUTION"
    assert r_proxy.residual_degrees_of_freedom == 1

    # 2. Cheat Mode B: Target-fitting constant compensation (wrong ln k0 + inflated 2-loop offset)
    compensation_cheat_payload = {
        **proxy_cheat_payload,
        "ln_k0_2s_minus_2p": Fraction(29841280, 10000000),
        "two_loop_and_recoil_mhz": Fraction(3660, 1000),
        "fourth_ray_counterexample_witness": Fraction(-1, 2),
    }
    r_comp = evaluate_prompt_gates(node, compensation_cheat_payload)
    assert not r_comp.passed
    assert r_comp.refusal_code == "DOF_UNPINNED_SUBCHANNEL_COMPENSATION"

    # 3. Cheat Mode C: Prose witness (1, 4/3, 0) differs from code/proof witness (3/5, 4/5, 0)
    desync_cheat_payload = {
        **proxy_cheat_payload,
        "paper_witness": (Fraction(1, 1), Fraction(4, 3), Fraction(0, 1)),
        "fourth_ray_counterexample_witness": Fraction(-1, 2),
    }
    r_desync = evaluate_prompt_gates(node, desync_cheat_payload)
    assert not r_desync.passed
    assert r_desync.refusal_code == "DOF_WITNESS_CERTIFICATE_DESYNCHRONIZATION"

    # 4. Full valid answer: all 7 operad constraints satisfied -> 0 residual degrees of freedom
    valid_payload = {
        **proxy_cheat_payload,
        "fourth_ray_counterexample_witness": Fraction(-1, 2),
    }
    r_valid = evaluate_prompt_gates(node, valid_payload)
    assert r_valid.passed
    assert r_valid.operad_operation_id == "pfp.certify_finite_qm_triad"
    assert r_valid.residual_degrees_of_freedom == 0


def test_collect_derivation_map_operads_composes_stages_and_eliminates_dof() -> None:
    stage1 = PromptTreeNode(
        uri=PromptUri.parse("prompt://physics/finite_qm/derivation/stage_01/P_CONE_PROOF"),
        title="Stage 1 Cone & Galois Proof",
        anti_ops=(
            AntiOpBinding(
                op_id="pfp.refuse_scalar_proxy_theorem_substitution",
                inspects_slot="candidate_text",
                refusal_code="ANTI_SCALAR_PROXY",
            ),
        ),
        antibodies=(
            AntibodyBinding(
                antibody_id="ab_scalar_proxy_theorem_substitution",
                signal1_epitope="three_ray_positivity_proxy",
                signal2_required_danger="PROXY_COUNTEREXAMPLE_SURVIVES",
            ),
        ),
        operad_binding=OperadPromptBinding(
            operation_id="pfp.stage1_cone_proof",
            source_colours=("Contract", "Code"),
            target_colour="Proof",
            slot_to_colour={"axiom_contract": "Contract", "solver_code": "Code"},
            required_boundary_witness_slots=("boundary_witness",),
        ),
    )

    stage2 = PromptTreeNode(
        uri=PromptUri.parse("prompt://physics/finite_qm/derivation/stage_02/P_PINNED_PAPER"),
        title="Stage 2 Pinned Subchannel Manuscript",
        anti_ops=(
            AntiOpBinding(
                op_id="pfp.refuse_target_fitting_constant_compensation",
                inspects_slot="candidate_text",
                refusal_code="ANTI_TARGET_FITTING",
            ),
        ),
        antibodies=(
            AntibodyBinding(
                antibody_id="ab_target_fitting_constant_compensation",
                signal1_epitope="unpinned_additive_residual",
                signal2_required_danger="COMPONENT_PIN_MISMATCH",
            ),
        ),
        operad_binding=OperadPromptBinding(
            operation_id="pfp.stage2_pinned_paper",
            source_colours=("Proof", "State"),
            target_colour="Paper",
            slot_to_colour={"stage1_proof": "Proof", "subchannel_state": "State"},
            required_slot_pins=("contact_coeff",),
        ),
    )

    stage3 = PromptTreeNode(
        uri=PromptUri.parse("prompt://physics/finite_qm/derivation/stage_03/P_TIEOUT_RECEIPT"),
        title="Stage 3 Cross-Layer Tie-Out Receipt",
        anti_ops=(
            AntiOpBinding(
                op_id="pfp.refuse_witness_certificate_desynchronization",
                inspects_slot="candidate_text",
                refusal_code="ANTI_WITNESS_DRIFT",
            ),
        ),
        antibodies=(
            AntibodyBinding(
                antibody_id="ab_witness_certificate_desynchronization",
                signal1_epitope="prose_certificate_witness_mismatch",
                signal2_required_danger="PROSE_WITNESS_FALSIFIED",
            ),
        ),
        operad_binding=OperadPromptBinding(
            operation_id="pfp.stage3_tieout_receipt",
            source_colours=("Paper", "Code", "Proof"),
            target_colour="Receipt",
            slot_to_colour={"paper_witness": "Paper", "code_witness": "Code", "proof_witness": "Proof"},
            cross_slot_equality_groups=(("paper_witness", "code_witness", "proof_witness"),),
        ),
    )

    shared_witness = (Fraction(91, 120), Fraction(-1, 2))
    payloads = {
        stage1.uri.raw_uri: {
            "candidate_text": "Stage 1 exact cone derivation.",
            "axiom_contract": "QZeta12_Cone",
            "solver_code": "evaluate_qm219",
            "boundary_witness": Fraction(-1, 2),
        },
        stage2.uri.raw_uri: {
            "candidate_text": "Stage 2 pinned subchannel budget.",
            "stage1_proof": "qzeta12_rational_readout_cone_and_galois_selection",
            "subchannel_state": "lamb_shift_subchannels",
            "contact_coeff": Fraction(91, 120),
            "slot_pins": {"contact_coeff": Fraction(91, 120)},
            "free_parameter_count": 0,
        },
        stage3.uri.raw_uri: {
            "candidate_text": "Stage 3 synchronized witness tie-out.",
            "paper_witness": shared_witness,
            "code_witness": shared_witness,
            "proof_witness": shared_witness,
        },
    }

    report = collect_derivation_map_operads([stage1, stage2, stage3], payloads)
    assert report.status == "PASS"
    assert report.residual_degrees_of_freedom == 0
    assert report.total_locked_constraints == 10
    assert report.composite_signature == "(Contract, Code, State, Code, Proof) -> Receipt"
    assert report.collected_antibody_ids == (
        "ab_scalar_proxy_theorem_substitution",
        "ab_target_fitting_constant_compensation",
        "ab_witness_certificate_desynchronization",
    )


def test_goals_4_to_9_qm_226_to_231_sidecars_and_derivation_map_operad() -> None:
    fixtures_dir = (
        REPO
        / "operads"
        / "tests"
        / "fixtures"
        / "prompt_hierarchy"
    )
    sidecar_files = (
        "p_qm_226_qed_g_minus_2.binding.yaml",
        "p_qm_227_weak_v_minus_a_muon_decay.binding.yaml",
        "p_qm_228_hadronic_gell_mann_okubo.binding.yaml",
        "p_qm_229_regge_4simplex_gravity.binding.yaml",
        "p_qm_230_ghz_mermin_paradox.binding.yaml",
        "p_qm_231_chern_haldane_lattice.binding.yaml",
    )
    nodes = [
        load_prompt_node_from_binding_dict(
            yaml.safe_load((fixtures_dir / fname).read_text(encoding="utf-8")),
            source_file=str(fixtures_dir / fname),
        )
        for fname in sidecar_files
    ]
    assert len(nodes) == 6
    for node in nodes:
        assert node.operad_binding is not None
        assert {ab.antibody_id for ab in node.antibodies} == {
            "ab_scalar_proxy_theorem_substitution",
            "ab_target_fitting_constant_compensation",
            "ab_witness_certificate_desynchronization",
        }

    w226 = (Fraction(1, 2), Fraction(1, 1))
    w227 = (Fraction(3, 4), Fraction(0, 1), Fraction(1, 1), Fraction(3, 4))
    w228 = (4522, 4509, 146)
    w229 = ((5, 10, 10, 5), 0)
    w230 = (-1, 1)
    w231 = (1, 0)

    payloads = {
        nodes[0].uri.raw_uri: {
            "candidate_text": "QM-226 Schwinger g-2 and Ward identity.",
            "ward_contract": "f1_zero_eq_1",
            "paper_witness": w226,
            "code_witness": w226,
            "proof_witness": w226,
            "schwinger_f2_zero": Fraction(1, 2),
            "f1_zero_ward_charge": Fraction(1, 1),
            "slot_pins": {
                "schwinger_f2_zero": Fraction(1, 2),
                "f1_zero_ward_charge": Fraction(1, 1),
            },
            "free_parameter_count": 0,
            "ir_regulator_positiveness_witness": Fraction(1, 100),
        },
        nodes[1].uri.raw_uri: {
            "candidate_text": "QM-227 Weak V-A chiral projector and Michel spectrum.",
            "paper_witness": w227,
            "code_witness": w227,
            "proof_witness": w227,
            "michel_rho": Fraction(3, 4),
            "michel_eta": Fraction(0, 1),
            "michel_xi": Fraction(1, 1),
            "michel_delta": Fraction(3, 4),
            "slot_pins": {
                "michel_rho": Fraction(3, 4),
                "michel_eta": Fraction(0, 1),
                "michel_xi": Fraction(1, 1),
                "michel_delta": Fraction(3, 4),
            },
            "free_parameter_count": 0,
            "right_handed_annihilation_witness": (0, 0, 0, 0),
        },
        nodes[2].uri.raw_uri: {
            "candidate_text": "QM-228 Hadronic SU(3) weight lattice and Gell-Mann-Okubo.",
            "flavor_state": "su3_octet_decuplet",
            "paper_witness": w228,
            "code_witness": w228,
            "proof_witness": w228,
            "baryon_octet_gmo_lhs_mev": 4522,
            "baryon_octet_gmo_rhs_mev": 4509,
            "decuplet_equal_spacing_mev": 146,
            "slot_pins": {
                "baryon_octet_gmo_lhs_mev": 4522,
                "baryon_octet_gmo_rhs_mev": 4509,
                "decuplet_equal_spacing_mev": 146,
            },
            "free_parameter_count": 0,
            "su3_isospin_breaking_residual_witness": 13,
        },
        nodes[3].uri.raw_uri: {
            "candidate_text": "QM-229 Discrete 4D Regge 4-simplex gravity and Bianchi identity.",
            "simplex_contract": "simplex_4d_5_10_10_5",
            "paper_witness": w229,
            "code_witness": w229,
            "proof_witness": w229,
            "simplex_4d_counts_v_e_t_s": (5, 10, 10, 5),
            "regge_bianchi_residual": 0,
            "slot_pins": {
                "simplex_4d_counts_v_e_t_s": (5, 10, 10, 5),
                "regge_bianchi_residual": 0,
            },
            "free_parameter_count": 0,
            "deficit_hinge_curvature_witness": (1, 1, 1),
        },
        nodes[4].uri.raw_uri: {
            "candidate_text": "QM-230 Three-qubit GHZ Mermin parity paradox.",
            "parity_diagram": "ghz_4_commuting_stabilizers",
            "paper_witness": w230,
            "code_witness": w230,
            "proof_witness": w230,
            "ghz_quantum_product_eigenvalue": -1,
            "ghz_classical_parity_product": 1,
            "slot_pins": {
                "ghz_quantum_product_eigenvalue": -1,
                "ghz_classical_parity_product": 1,
            },
            "free_parameter_count": 0,
            "mermin_4_vs_2_contradiction_witness": (4, 2),
        },
        nodes[5].uri.raw_uri: {
            "candidate_text": "QM-231 Discrete lattice Berry-plaquette Chern number.",
            "ghz_audit": "verified_stage_08",
            "paper_witness": w231,
            "code_witness": w231,
            "proof_witness": w231,
            "topological_chern_number": 1,
            "trivial_chern_number": 0,
            "slot_pins": {
                "topological_chern_number": 1,
                "trivial_chern_number": 0,
            },
            "free_parameter_count": 0,
            "mass_inversion_phase_boundary_witness": (-1, 3),
        },
    }

    report = collect_derivation_map_operads(nodes, payloads)
    assert report.status == "PASS"
    assert report.residual_degrees_of_freedom == 0
    assert report.total_locked_constraints == 45
    assert report.composite_signature == (
        "(Contract, Code, Proof, Code, Proof, Code, Proof, Code, Proof, Code, Proof, Code, Proof) -> Receipt"
    )


def test_predeclared_relational_operad_locks_load_before_candidate_generation() -> None:
    fixtures_dir = (
        REPO
        / "operads"
        / "tests"
        / "fixtures"
        / "prompt_hierarchy"
    )
    nodes = load_predeclared_relational_operad_locks(fixtures_dir, yaml.safe_load)
    assert len(nodes) == 4
    expected_ops = (
        "pfp.rel01_genesis_survivor_tower_and_retraction",
        "pfp.rel02_collision_tagging_and_swap_projectors",
        "pfp.rel03_directed_cut_coboundary_vs_chord_obstruction",
        "pfp.rel04_three_element_swap_commutator_cyclotomic_receipt",
    )
    assert tuple(n.operad_binding.operation_id for n in nodes if n.operad_binding) == expected_ops
    assert tuple(n.operad_binding.locked_constraint_count for n in nodes if n.operad_binding) == (
        7,
        8,
        8,
        8,
    )


def test_genesis_relational_derivation_workflow_passes_with_zero_residual_dof() -> None:
    fixtures_dir = (
        REPO
        / "operads"
        / "tests"
        / "fixtures"
        / "prompt_hierarchy"
    )
    run = run_genesis_relational_derivation_workflow(fixtures_dir, yaml.safe_load)
    report = run.operad_report
    assert report.status == "PASS"
    assert report.residual_degrees_of_freedom == 0
    assert report.total_locked_constraints == 31
    assert report.composite_signature == (
        "(Contract, Code, Code, Proof, Code, Proof, Code, Proof) -> Receipt"
    )
    assert run.authority_effect == "None"
    assert run.genesis_effect == "None"
    for payload in run.stage_payloads.values():
        assert payload["authority_effect"] == "None"
        assert payload["genesis_effect"] == "None"
        assert payload["free_parameter_count"] == 0


def test_genesis_relational_derivation_refuses_all_four_adversarial_cheat_modes() -> None:
    fixtures_dir = (
        REPO
        / "operads"
        / "tests"
        / "fixtures"
        / "prompt_hierarchy"
    )
    nodes = load_predeclared_relational_operad_locks(fixtures_dir, yaml.safe_load)
    u1, u2, u3, u4 = (n.uri.raw_uri for n in nodes)

    # 1. Unmapped continuum / Lie algebra import in Stage 4
    r_continuum = run_genesis_relational_derivation_workflow(
        fixtures_dir,
        yaml.safe_load,
        payload_overrides={
            u4: {
                "candidate_text": "Import continuous physics Lie algebra su(2) smooth manifold.",
            },
        },
    )
    assert r_continuum.operad_report.status == "REFUSED"
    assert r_continuum.operad_report.refusal_code == "ANTI_UNMAPPED_CONTINUUM_IMPORT"

    # 2. Merging active obstruction register W_n^active with persistent history ledger H_n in Stage 1
    r_history_conflation = run_genesis_relational_derivation_workflow(
        fixtures_dir,
        yaml.safe_load,
        payload_overrides={
            u1: {
                "normative_survivor_vector": (0, 1, 2, 3, 3, 4, 5),
            },
        },
    )
    assert r_history_conflation.operad_report.status == "REFUSED"
    assert r_history_conflation.operad_report.refusal_code == "DOF_UNPINNED_SUBCHANNEL_COMPENSATION"

    # 3. Omitting boundary counterexample witness in Stage 2 or Stage 3 (scalar proxy substitution)
    r_missing_boundary = run_genesis_relational_derivation_workflow(
        fixtures_dir,
        yaml.safe_load,
        payload_overrides={
            u3: {
                "non_exact_1cochain_chord_witness": None,
            },
        },
    )
    assert r_missing_boundary.operad_report.status == "REFUSED"
    assert r_missing_boundary.operad_report.refusal_code == "DOF_SCALAR_PROXY_SUBSTITUTION"

    # 4. Desynchronizing paper_witness vs code_witness/proof_witness in Stage 4
    r_witness_drift = run_genesis_relational_derivation_workflow(
        fixtures_dir,
        yaml.safe_load,
        payload_overrides={
            u4: {
                "paper_witness": ("drifted_prose_witness", 999),
            },
        },
    )
    assert r_witness_drift.operad_report.status == "REFUSED"
    assert r_witness_drift.operad_report.refusal_code == "DOF_WITNESS_CERTIFICATE_DESYNCHRONIZATION"


def test_coupled_bipartite_d2xd3_and_d3xd3_workflow_passes_with_zero_residual_dof() -> None:
    fixtures_dir = (
        REPO
        / "operads"
        / "tests"
        / "fixtures"
        / "prompt_hierarchy"
    )
    nodes = load_predeclared_relational_operad_locks(
        fixtures_dir,
        yaml.safe_load,
        filenames=COUPLED_BIPARTITE_BINDING_FILENAMES,
    )
    assert len(nodes) == 6
    assert tuple(n.operad_binding.locked_constraint_count for n in nodes if n.operad_binding) == (
        7,
        8,
        8,
        8,
        9,
        9,
    )

    run = run_coupled_bipartite_relational_derivation_workflow(fixtures_dir, yaml.safe_load)
    report = run.operad_report
    assert report.status == "PASS"
    assert report.residual_degrees_of_freedom == 0
    assert report.total_locked_constraints == 49
    assert report.composite_signature == (
        "(Contract, Code, Code, Proof, Code, Proof, Code, Proof, Code, Proof, Code, Proof) -> Receipt"
    )
    assert run.authority_effect == "None"
    assert run.genesis_effect == "None"

    u5 = nodes[4].uri.raw_uri
    u6 = nodes[5].uri.raw_uri
    p5 = run.stage_payloads[u5]
    p6 = run.stage_payloads[u6]

    assert p5["prism_graph_v_e_b1_trees"] == (6, 9, 4, 75)
    assert p5["four_sector_projector_ranks"] == (1, 1, 2, 2)
    assert p5["coupled_prism_interlayer_twist_witness"] == ((0, 0), (-2, 1), 75)
    assert p5["free_parameter_count"] == 0

    assert p6["five_sector_projector_ranks"] == (1, 2, 2, 3, 1)
    assert p6["compound_commutator_square_minus_nine_w00_defect"] == Fraction(0, 1)
    assert p6["diagonal_3cycle_traces_on_sym_and_alt_w00"] == (0, 1, 0)
    assert p6["nonfactorizable_entangled_difference_witness"] == (
        1,
        0,
        "antisymmetric_singlet_minor_1_vs_separable_0",
    )
    assert p6["free_parameter_count"] == 0


def test_coupled_bipartite_workflow_refuses_adversarial_cheat_modes() -> None:
    fixtures_dir = (
        REPO
        / "operads"
        / "tests"
        / "fixtures"
        / "prompt_hierarchy"
    )
    nodes = load_predeclared_relational_operad_locks(
        fixtures_dir,
        yaml.safe_load,
        filenames=COUPLED_BIPARTITE_BINDING_FILENAMES,
    )
    u5 = nodes[4].uri.raw_uri
    u6 = nodes[5].uri.raw_uri

    # 1. Guessing wrong prism spanning tree count or unsplit W_0 (x) W_0 sector ranks
    r_bad_ranks = run_coupled_bipartite_relational_derivation_workflow(
        fixtures_dir,
        yaml.safe_load,
        payload_overrides={
            u6: {
                "five_sector_projector_ranks": (1, 2, 2, 2, 2),
            },
        },
    )
    assert r_bad_ranks.operad_report.status == "REFUSED"
    assert r_bad_ranks.operad_report.refusal_code == "DOF_UNPINNED_SUBCHANNEL_COMPENSATION"

    # 2. Omitting inter-layer prism twist witness on D_2 x D_3 (marginal flatness proxy)
    r_no_twist = run_coupled_bipartite_relational_derivation_workflow(
        fixtures_dir,
        yaml.safe_load,
        payload_overrides={
            u5: {
                "coupled_prism_interlayer_twist_witness": None,
            },
        },
    )
    assert r_no_twist.operad_report.status == "REFUSED"
    assert r_no_twist.operad_report.refusal_code == "DOF_SCALAR_PROXY_SUBSTITUTION"

    # 3. Omitting non-factorizable antisymmetric singlet minor witness on D_3 x D_3
    r_no_singlet = run_coupled_bipartite_relational_derivation_workflow(
        fixtures_dir,
        yaml.safe_load,
        payload_overrides={
            u6: {
                "nonfactorizable_entangled_difference_witness": None,
            },
        },
    )
    assert r_no_singlet.operad_report.status == "REFUSED"
    assert r_no_singlet.operad_report.refusal_code == "DOF_SCALAR_PROXY_SUBSTITUTION"

    # 4. Introducing a non-zero free tuning parameter in Stage 6
    r_free_param = run_coupled_bipartite_relational_derivation_workflow(
        fixtures_dir,
        yaml.safe_load,
        payload_overrides={
            u6: {
                "free_parameter_count": 1,
            },
        },
    )
    assert r_free_param.operad_report.status == "REFUSED"
    assert r_free_param.operad_report.refusal_code == "DOF_NONZERO_FREE_PARAMETERS"


def test_tripartite_d3_cubed_workflow_passes_with_zero_residual_dof() -> None:
    fixtures_dir = (
        REPO
        / "operads"
        / "tests"
        / "fixtures"
        / "prompt_hierarchy"
    )
    nodes = load_predeclared_relational_operad_locks(
        fixtures_dir,
        yaml.safe_load,
        filenames=TRIPARTITE_BINDING_FILENAMES,
    )
    assert len(nodes) == 7
    assert tuple(n.operad_binding.locked_constraint_count for n in nodes if n.operad_binding) == (
        7,
        8,
        8,
        8,
        9,
        9,
        9,
    )

    run = run_tripartite_relational_derivation_workflow(fixtures_dir, yaml.safe_load)
    report = run.operad_report
    assert report.status == "PASS"
    assert report.residual_degrees_of_freedom == 0
    assert report.total_locked_constraints == 58
    assert report.composite_signature == (
        "(Contract, Code, Code, Proof, Code, Proof, Code, Proof, Code, Proof, Code, Proof, Code, Proof) -> Receipt"
    )
    assert run.authority_effect == "None"
    assert run.genesis_effect == "None"

    u7 = nodes[6].uri.raw_uri
    p7 = run.stage_payloads[u7]
    assert p7["tripartite_binomial_sector_ranks"] == (1, 6, 12, 8)
    assert p7["w000_schur_weyl_sym_mixed_alt_ranks"] == (4, 4, 0)
    assert p7["levi_civita_mixed_sector_and_parity_pin"] == (1, 0, 0, 0)
    assert p7["w000_r3_invariant_split_and_k3_square_defect"] == (2, 1, 1, 0)
    assert p7["pigeonhole_w000_alt_vanishing_and_levi_civita_witness"] == (
        6,
        0,
        0,
        "pigeonhole_lambda3_w0_vanishes_supported_on_lplus_tensor_lambda2_w0",
    )
    assert p7["free_parameter_count"] == 0


def test_tripartite_d3_cubed_workflow_refuses_adversarial_cheat_modes() -> None:
    fixtures_dir = (
        REPO
        / "operads"
        / "tests"
        / "fixtures"
        / "prompt_hierarchy"
    )
    nodes = load_predeclared_relational_operad_locks(
        fixtures_dir,
        yaml.safe_load,
        filenames=TRIPARTITE_BINDING_FILENAMES,
    )
    u7 = nodes[6].uri.raw_uri

    # 1. Falsely claiming Lambda^3(W_0) has rank 1 on W_000 (violating dim(W_0)=2 < 3 pigeonhole)
    r_false_alt = run_tripartite_relational_derivation_workflow(
        fixtures_dir,
        yaml.safe_load,
        payload_overrides={
            u7: {
                "w000_schur_weyl_sym_mixed_alt_ranks": (4, 3, 1),
            },
        },
    )
    assert r_false_alt.operad_report.status == "REFUSED"
    assert r_false_alt.operad_report.refusal_code == "DOF_UNPINNED_SUBCHANNEL_COMPENSATION"

    # 2. Omitting the pigeonhole Lambda^3(W_0)=0 boundary witness
    r_no_pigeonhole = run_tripartite_relational_derivation_workflow(
        fixtures_dir,
        yaml.safe_load,
        payload_overrides={
            u7: {
                "pigeonhole_w000_alt_vanishing_and_levi_civita_witness": None,
            },
        },
    )
    assert r_no_pigeonhole.operad_report.status == "REFUSED"
    assert r_no_pigeonhole.operad_report.refusal_code == "DOF_SCALAR_PROXY_SUBSTITUTION"

    # 3. Desynchronizing tripartite_receipt_witness vs code_witness/proof_witness
    r_drift = run_tripartite_relational_derivation_workflow(
        fixtures_dir,
        yaml.safe_load,
        payload_overrides={
            u7: {
                "tripartite_receipt_witness": ("drifted_tripartite_witness", 0),
            },
        },
    )
    assert r_drift.operad_report.status == "REFUSED"
    assert r_drift.operad_report.refusal_code == "DOF_WITNESS_CERTIFICATE_DESYNCHRONIZATION"


def test_stage5_to_7_code_and_proof_witness_slots_bind_to_rust_and_lean4_modules() -> None:
    binding = load_coupled_native_rust_and_lean4_witnesses(REPO)
    assert (
        binding.rust_module_relpath
        == "engine/crates_rs/core_symbol_game/src/coupled_relational_operad.rs"
    )
    assert (
        binding.rust_test_relpath
        == "engine/crates_rs/tests/core_symbol_game/coupled_relational_operad.rs"
    )
    assert binding.rust_runtime_action == "coupled_relational_operad_verify"
    assert (
        binding.rust_receipt_schema
        == "core.symbol_game.coupled_relational_operad_receipt.v1"
    )
    assert (
        binding.lean4_module_relpath
        == "lean4/quantum_mechanics/CoupledRelationalProjectors.lean"
    )
    assert binding.lean4_theorem_names == (
        "stage1_survivor_tower_and_retraction_eq",
        "stage2_d2_collision_tagging_and_swap_projectors_eq",
        "stage3_diamond_coboundary_vs_chord_holonomy_eq",
        "stage4_d3_swap_commutator_and_cyclotomic_w0_eq",
        "stage5_d2_x_d3_four_sector_ranks_and_j23_cubic",
        "stage6_d3_x_d3_five_sector_ranks_and_rational_involution",
        "stage7_d3_cubed_schur_weyl_obstruction_and_levi_civita_localization",
        "coupled_bipartite_and_tripartite_relational_master_certificate",
    )
    assert binding.stage1_code_witness == binding.stage1_proof_witness
    assert binding.stage2_code_witness == binding.stage2_proof_witness
    assert binding.stage3_code_witness == binding.stage3_proof_witness
    assert binding.stage4_code_body == binding.stage4_proof_body
    assert binding.stage5_code_witness == binding.stage5_proof_witness
    assert binding.stage6_code_body == binding.stage6_proof_body
    assert binding.stage7_code_body == binding.stage7_proof_body
    assert binding.authority_effect == "None"
    assert binding.genesis_effect == "None"

    fixtures_dir = (
        REPO
        / "operads"
        / "tests"
        / "fixtures"
        / "prompt_hierarchy"
    )
    run = run_tripartite_relational_derivation_workflow(fixtures_dir, yaml.safe_load)
    for idx, expected_thm in enumerate(binding.lean4_theorem_names[:7]):
        uri = run.predeclared_nodes[idx].uri.raw_uri
        payload = run.stage_payloads[uri]
        nb = payload["native_witness_binding"]
        assert nb["rust_module"] == binding.rust_module_relpath
        assert nb["rust_runtime_action"] == "coupled_relational_operad_verify"
        assert nb["lean4_module"] == "lean4/quantum_mechanics/CoupledRelationalProjectors.lean"
        assert nb["lean4_theorem"] == expected_thm
        assert payload["code_witness"] == payload["proof_witness"]






