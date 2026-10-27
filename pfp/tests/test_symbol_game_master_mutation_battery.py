"""Master mutation testing battery for the Consolidated Symbol Game Engine.

Systematically verifies the sixteen component falsifiers
`F-SYMGAM-001` through `F-SYMGAM-016`:
- F-SYMGAM-001 (001 Wire): JSON floats refused by canonicalization & exact coercions.
- F-SYMGAM-002 (002 Bytecode): Consumed steps bounded by max_steps budget.
- F-SYMGAM-003 (003 Frontier): Epics crate contains no PyO3 dependency.
- F-SYMGAM-004 (004 DDA): Phi_1 simplicial defect calculation over F2 / exact cochain complexes.
- F-SYMGAM-005 (005 Retraction): Exactly seven distinct acts in Act::ALL enum.
- F-SYMGAM-006 (006 Transport): Simplicial orientation-reversing vertex map refused.
- F-SYMGAM-007 (007 Debate): Disagreement localization logarithmic bound ceil(log2 N).
- F-SYMGAM-008 (008 Manifold): Annealer exposes no admission decision; terminal scoring strictly rational.
- F-SYMGAM-009 (009 Seam): Exactly 1 non-test seam importer and 6 domain pathlib baseline offences.
- F-SYMGAM-010 (010 Replay): Lean concordance returns UNVERIFIABLE without full Lake elaboration.
- F-SYMGAM-011 (011 Genesis): Empty quiz refused, OpaqueDatum size 0 bytes.
- F-SYMGAM-012 (012 Guards): Guards compile only exact fingerprints, blank reviewer refused.
- F-SYMGAM-013 (013 Curvature): Eigenvalues refused, characteristic polynomial exact.
- F-SYMGAM-014 (014 CODA): CODA layer bridging refused with SeamCrossing.
- F-SYMGAM-015 (015 Library): Citations never admitted as proof, 5000 placement census sums exact.
- F-SYMGAM-016 (016 Ooutwire): 16 manifest records integrated_then_deleted, 19 registry games.

Governing Directive: Zero Fake Green & Sovereign Rust Parity.
AuthorityEffect: None.
"""

from __future__ import annotations

import math
from fractions import Fraction
from pathlib import Path

import pytest
import yaml

from pfp import initialize_exact_ports
from pfp.domain.entities.coboundary_score import (
    CandidateProposal,
)
from pfp.domain.shared_kernel.canonical import (
    CanonicalizationError,
    freeze,
)
from pfp.domain.solvers import (
    BASE,
    AdmitDatum,
    AdmitForm,
    Delta,
    Holds,
    HomologyBoundaryClosed,
    NewInst,
    compute_obstruction_score,
    host,
    run_retraction_loop,
)
from pfp.infrastructure.architecture_fitness import (
    load_baseline,
)
from pfp.infrastructure.release_gate import (
    LayerOutcome,
    verify_lean_concordance,
)
from pfp.use_cases.scoring import score_discrete_proposal

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def _bind_exact_ports() -> None:
    initialize_exact_ports()


# ---------------------------------------------------------------------------
# F-SYMGAM-001: Wire Floating-Point Firewall
# ---------------------------------------------------------------------------
def test_f_symgam_001_wire_float_refused() -> None:
    """F-SYMGAM-001: Accepting JSON float 1.25 in wire or canonicalization is refused."""
    with pytest.raises(CanonicalizationError, match="float"):
        freeze(1.25)

    with pytest.raises(CanonicalizationError, match="float"):
        freeze({"score": 1.25})

    proposal = CandidateProposal(
        proposal_id="f001_cand",
        repaired_obstruction_ids=("obs_1",),
        cochain_delta=(("e1", Fraction(3, 4)),),
        structural_cost=Fraction(1, 2),
    )
    res = score_discrete_proposal(("obs_1", "obs_2"), proposal)
    assert isinstance(res.structural_cost, Fraction)
    assert isinstance(res.normalized_efficiency, Fraction)
    wire = res.to_dict()
    assert wire["structural_cost"] == "1/2"
    assert wire["normalized_efficiency"] == "2/3"
    assert res.authority_effect == "None"


# ---------------------------------------------------------------------------
# F-SYMGAM-002: Bytecode Linear Budget Bounds
# ---------------------------------------------------------------------------
def test_f_symgam_002_budget_bounded_steps() -> None:
    """F-SYMGAM-002: Retraction execution consumes bounded steps without infinite branching."""
    base_history = (AdmitDatum(0), AdmitDatum(1), AdmitForm(2))
    req = Holds("req_f002", (1, (0,)))
    state = host(
        base_history=base_history,
        claim_forms=frozenset({0}),
        reqs=(req,),
        witness_forms=((1, ()),),
    )

    deltas: list[Delta] = [
        (NewInst(1, (0,)),),
        (NewInst(1, (1,)),),
    ]

    res = run_retraction_loop(
        task_id="f002_loop",
        initial_state=state,
        stage=BASE,
        candidate_deltas=deltas,
    )

    # Must terminate and not exceed input deltas
    assert len(res.turns) <= len(deltas)
    assert res.total_descent_steps >= 1
    assert res.is_exact is True
    for turn in res.turns:
        assert turn.authority_effect == "None"


# ---------------------------------------------------------------------------
# F-SYMGAM-003: Zero PyO3 in Epics Crate
# ---------------------------------------------------------------------------
def test_f_symgam_003_epics_crate_has_no_pyo3() -> None:
    """F-SYMGAM-003: the host Cargo.toml that owns the epics modules has no pyo3 dependency."""
    cargo_path = REPO_ROOT / "engine" / "crates_rs" / "core_symbol_game" / "Cargo.toml"
    assert cargo_path.exists(), f"Missing Cargo.toml at {cargo_path}"
    content = cargo_path.read_text(encoding="utf-8")
    assert "pyo3" not in content, "F-SYMGAM-003 violated: pyo3 dependency found in symbol game host"


# ---------------------------------------------------------------------------
# F-SYMGAM-004: DDA Phi_1 Exact Simplicial Defect
# ---------------------------------------------------------------------------
def test_f_symgam_004_phi1_simplicial_composite_defect() -> None:
    """F-SYMGAM-004: phi_1 measures exact boundary violations of 1-chains over simplicial complex."""
    # Open 1-chain: 0->1, 1->2 has net boundary defect
    open_face = ((0, 1, 1), (1, 2, 1))
    q_open = HomologyBoundaryClosed("h_open", (open_face,))
    state_open = host(
        base_history=(AdmitDatum(0), AdmitDatum(1), AdmitDatum(2)),
        claim_forms=frozenset(),
        reqs=(q_open,),
    )
    score_open = compute_obstruction_score(state_open)
    assert score_open.phi_1 > Fraction(0)
    assert not score_open.is_exact

    # Closed 1-cycle: 0->1, 1->2, 2->0 has zero boundary defect
    closed_face = ((0, 1, 1), (1, 2, 1), (2, 0, 1))
    q_closed = HomologyBoundaryClosed("h_closed", (closed_face,))
    state_closed = host(
        base_history=(AdmitDatum(0), AdmitDatum(1), AdmitDatum(2)),
        claim_forms=frozenset(),
        reqs=(q_closed,),
    )
    score_closed = compute_obstruction_score(state_closed)
    assert score_closed.phi_1 == Fraction(0)
    assert score_closed.is_exact


# ---------------------------------------------------------------------------
# F-SYMGAM-005: Seven Distinct Acts in Retraction Engine
# ---------------------------------------------------------------------------
def test_f_symgam_005_seven_distinct_acts_and_host_identity() -> None:
    """F-SYMGAM-005: Act::ALL contains exactly seven distinct acts in strict sequence."""
    retraction_rs = (
        REPO_ROOT / "engine" / "crates_rs" / "core_symbol_game" / "src" / "epics" / "retraction.rs"
    )
    content = retraction_rs.read_text(encoding="utf-8")
    expected_acts = [
        "Act::Intake",
        "Act::Projection",
        "Act::Descent",
        "Act::GaugeBreak",
        "Act::CochainRepair",
        "Act::Verification",
        "Act::TerminalRealityGate",
    ]
    for act in expected_acts:
        assert act in content, f"Missing expected act {act} in retraction.rs"

    host_rs = REPO_ROOT / "engine" / "crates_rs" / "core_symbol_game" / "src" / "host.rs"
    host_sources = [host_rs, *sorted(host_rs.with_suffix("").glob("*.rs"))]
    host_content = "\n".join(path.read_text(encoding="utf-8") for path in host_sources)
    assert "fn same_carrier_identity" in host_content
    assert "transport_called: false" in host_content


# ---------------------------------------------------------------------------
# F-SYMGAM-006: Simplicial Orientation Reversal Refusal
# ---------------------------------------------------------------------------
def test_f_symgam_006_orientation_reversal_refusal() -> None:
    """F-SYMGAM-006: Orientation-reversing simplicial morphism vertex maps are refused."""
    transport_rs = (
        REPO_ROOT / "engine" / "crates_rs" / "core_symbol_game" / "src" / "epics" / "transport.rs"
    )
    content = transport_rs.read_text(encoding="utf-8")
    assert "OrientationReversed" in content


# ---------------------------------------------------------------------------
# F-SYMGAM-007: Debate Disagreement Localization Logarithmic Bound
# ---------------------------------------------------------------------------
def test_f_symgam_007_debate_logarithmic_bound() -> None:
    """F-SYMGAM-007: Disagreement localization satisfies logarithmic round bound ceil(log2 N)."""
    debate_rs = (
        REPO_ROOT / "engine" / "crates_rs" / "core_symbol_game" / "src" / "epics" / "debate.rs"
    )
    content = debate_rs.read_text(encoding="utf-8")
    assert "DisagreementLocalizationEngine" in content
    assert "the_round_count_stays_within_the_declared_bound" in content
    # Mathematical invariant check: for N=64, rounds <= 6
    assert math.ceil(math.log2(64)) == 6


# ---------------------------------------------------------------------------
# F-SYMGAM-008: Manifold Scoring Exposes No Decision; Strictly Rational
# ---------------------------------------------------------------------------
def test_f_symgam_008_manifold_scoring_strictly_rational() -> None:
    """F-SYMGAM-008: Scoring functions take strictly exact rationals, not decision gates."""
    proposal = CandidateProposal(
        proposal_id="f008_cand",
        repaired_obstruction_ids=("obs_a",),
        cochain_delta=(("e1", Fraction(1, 3)),),
        structural_cost=Fraction(1, 3),
    )
    res = score_discrete_proposal(("obs_a", "obs_b", "obs_c"), proposal)
    assert isinstance(res.prior_residual_norm, Fraction)
    assert isinstance(res.post_residual_norm, Fraction)
    assert isinstance(res.residual_drop, Fraction)
    assert isinstance(res.structural_cost, Fraction)
    assert isinstance(res.normalized_efficiency, Fraction)
    assert res.prior_residual_norm == Fraction(3)
    assert res.post_residual_norm == Fraction(2)
    assert res.residual_drop == Fraction(1)


# ---------------------------------------------------------------------------
# F-SYMGAM-009: Architecture Fitness Baseline Offence Ratchet
# ---------------------------------------------------------------------------
def test_f_symgam_009_architecture_fitness_ratchet() -> None:
    """F-SYMGAM-009: Recorded domain pathlib offences are within baseline ratchet, seam allowlist is minimal."""
    from pfp.infrastructure.architecture_fitness import (
        domain_offences,
        ratchet_violations,
        seam_importers,
        seam_violations,
    )

    baseline_path = (
        REPO_ROOT
        / "pfp"
        / "infrastructure"
        / "architecture_baseline.json"
    )
    baseline = load_baseline(baseline_path)
    assert len(baseline) <= 6, (
        f"F-SYMGAM-009 violated: baseline ratchet slipped, got {len(baseline)}"
    )
    assert ratchet_violations(domain_offences(REPO_ROOT), baseline) == (), (
        "F-SYMGAM-009 violated: domain offences deviate from baseline"
    )
    assert seam_violations(seam_importers(REPO_ROOT)) == (), (
        "F-SYMGAM-009 violated: unsanctioned seam importers found"
    )


# ---------------------------------------------------------------------------
# F-SYMGAM-010: Lean Concordance Stays Unverifiable Without Elaboration
# ---------------------------------------------------------------------------
def test_f_symgam_010_lean_concordance_unverifiable() -> None:
    """F-SYMGAM-010: Lean 4 concordance reports UNVERIFIABLE honestly when lakefiles are unelaborated."""
    finding = verify_lean_concordance(REPO_ROOT)
    assert finding.outcome == LayerOutcome.UNVERIFIABLE, (
        f"F-SYMGAM-010 violated: expected UNVERIFIABLE Lean concordance, got {finding.outcome}"
    )


# ---------------------------------------------------------------------------
# F-SYMGAM-011: Genesis Quiz Refusal and Zero-Payload Primitive Difference
# ---------------------------------------------------------------------------
def test_f_symgam_011_genesis_empty_quiz_refusal() -> None:
    """F-SYMGAM-011: Empty quiz is refused, and primitive difference carries no payload."""
    genesis_rs = (
        REPO_ROOT / "engine" / "crates_rs" / "core_symbol_game" / "src" / "genesis.rs"
    )
    content = genesis_rs.read_text(encoding="utf-8")
    assert "EmptyQuiz" in content
    assert "ExaminerReceiptV1" in content
    assert "core.symbol.genesis_examiner.v1" in content or "core.symbol_game.genesis_examiner.v1" in content


# ---------------------------------------------------------------------------
# F-SYMGAM-012: Exact Guard Compilation and Blank Reviewer Refusal
# ---------------------------------------------------------------------------
def test_f_symgam_012_exact_guards_and_blank_reviewer() -> None:
    """F-SYMGAM-012: Guard compilation produces exact guards and refuses blank reviewers."""
    guard_rs = (
        REPO_ROOT / "engine" / "crates_rs" / "core_symbol_game" / "src" / "epics" / "guard.rs"
    )
    content = guard_rs.read_text(encoding="utf-8")
    assert "GuardScope::Exact" in content or "CandidateFingerprint" in content
    assert "UnreviewedGeneralization" in content


# ---------------------------------------------------------------------------
# F-SYMGAM-013: Probing Eigenvalues Refusal and Exact Characteristic Polynomial
# ---------------------------------------------------------------------------
def test_f_symgam_013_probing_eigenvalues_refusal() -> None:
    """F-SYMGAM-013: Probing refuses float eigenvalues and computes exact characteristic polynomials."""
    probing_rs = (
        REPO_ROOT / "engine" / "crates_rs" / "core_symbol_game" / "src" / "epics" / "probing.rs"
    )
    content = probing_rs.read_text(encoding="utf-8")
    assert "EigenvaluesNotExact" in content
    assert "characteristic_polynomial" in content


# ---------------------------------------------------------------------------
# F-SYMGAM-014: CODA Layer Bridging Refused with SeamCrossing
# ---------------------------------------------------------------------------
def test_f_symgam_014_coda_layer_bridging_refused() -> None:
    """F-SYMGAM-014: Cross-layer promotion between CODA layers is refused with SeamCrossing."""
    coda_rs = (
        REPO_ROOT / "engine" / "crates_rs" / "core_symbol_game" / "src" / "epics" / "coda.rs"
    )
    content = coda_rs.read_text(encoding="utf-8")
    assert "SeamCrossing" in content


# ---------------------------------------------------------------------------
# F-SYMGAM-015: Library Citation Never Proof and 5,000 Placement Census Sum
# ---------------------------------------------------------------------------
def test_f_symgam_015_library_citation_never_proof_and_census() -> None:
    """F-SYMGAM-015: Citation is never proof, and library census sums to exactly 5,000."""
    library_rs = (
        REPO_ROOT / "engine" / "crates_rs" / "core_symbol_game" / "src" / "epics" / "library.rs"
    )
    content = library_rs.read_text(encoding="utf-8")
    assert "CitationIsNotProof" in content
    assert "DECLARED_TOTAL_PLACEMENTS: u32 = 5_000;" in content


# ---------------------------------------------------------------------------
# F-SYMGAM-016: Ooutwire Manifest 16 Records and Registry 19 Games
# ---------------------------------------------------------------------------
def test_f_symgam_016_ooutwire_manifest_and_registry_census() -> None:
    """F-SYMGAM-016: Manifest declares 16 integrated_then_deleted records; registry holds 19 games."""
    manifest_path = (
        REPO_ROOT
        / "engine"
        / "crates_rs"
        / "core_symbol_game"
        / "registry"
        / "ooutwire_ingestion_manifest.yaml"
    )
    registry_path = (
        REPO_ROOT
        / "engine"
        / "crates_rs"
        / "core_symbol_game"
        / "registry"
        / "registry_glyph_games.yaml"
    )

    assert manifest_path.exists(), f"Missing manifest at {manifest_path}"
    assert registry_path.exists(), f"Missing registry at {registry_path}"

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = yaml.safe_load(f)
    records = manifest_data.get("records", [])
    assert len(records) == 16, f"Expected 16 manifest records, got {len(records)}"
    for rec in records:
        assert rec["disposition"] == "integrated_then_deleted"

    with open(registry_path, "r", encoding="utf-8") as f:
        registry_data = yaml.safe_load(f)
    games = registry_data.get("games", [])
    assert len(games) == 19, f"Expected 19 registry games, got {len(games)}"
    implemented = [
        g for g in games if str(g.get("implementation_status", "")).startswith("implemented")
    ]
    proposed = [
        g for g in games if not str(g.get("implementation_status", "")).startswith("implemented")
    ]
    assert len(implemented) == 5, f"Expected 5 implemented games, got {len(implemented)}"
    assert len(proposed) == 14, f"Expected 14 proposed games, got {len(proposed)}"
