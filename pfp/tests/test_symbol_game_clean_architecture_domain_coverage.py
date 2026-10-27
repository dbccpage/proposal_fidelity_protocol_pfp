"""Comprehensive domain and use-case test battery for Symbol Game canonical, scoring, and entities.

Drives statement coverage to >= 95% across:
- pfp.domain.shared_kernel.canonical
- pfp.domain.entities.coboundary_score
- pfp.use_cases.scoring
- pfp.domain.solvers.retraction

Governing Directive: Zero Fake Green & Sovereign Rust Math Delegation.
AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
import enum
from fractions import Fraction
import pytest

from pfp import initialize_exact_ports
from pfp.domain.entities.coboundary_score import (
    CandidateProposal,
    CoboundaryScoreResult,
    REFUSAL_AUTHORITY,
    REFUSAL_EXACT_WITHOUT_DUAL,
    REFUSAL_ILLEGAL_PROPOSAL,
    REFUSAL_INEXACT_COCHAIN_DELTA,
    REFUSAL_INEXACT_EXACTNESS_CLAIM,
    REFUSAL_INEXACT_RESIDUAL_NORM,
    REFUSAL_NEGATIVE_MAGNITUDE,
    ResidualDropV1,
    _norm_from_wire,
)
from pfp.domain.exact.q import Q
from pfp.domain.models import ObstructionScore, StepVerdict
from pfp.domain.shared_kernel.canonical import (
    _COMPOUND_TAGS,
    _FrozenValue,
    CanonicalizationError,
    _declared_slots,
    _validate_compound,
    _validate_dataclass_instance,
    _validate_enum_instance,
    _wire,
    canonical_bytes,
    canonical_json,
    canonical_unwire,
    canonical_wire,
    domain_digest,
    freeze,
    thaw,
)
from pfp.domain.shared_kernel.exact import NotExactError
from pfp.domain.solvers import (
    BASE,
    AdmitDatum,
    AdmitForm,
    AdmitInst,
    Delta,
    Holds,
    HolonomyLoopClosed,
    HomologyBoundaryClosed,
    NewInst,
    compute_obstruction_score,
    execute_retraction_turn,
    host,
    run_retraction_loop,
)
from pfp.use_cases.scoring import (
    EvaluateCoboundaryScoreUseCase,
    KILL_CONDITION_MAP,
    REFUSAL_AUTHORITY_NON_NONE,
    REFUSAL_INEXACT_COCHAIN,
    REFUSAL_PROSE_PROMPT_REFUSED,
    l1_float,
    l1_rational,
    magnitudes_from_ledger_active,
    mass_from_ids,
    mass_from_magnitudes,
    rank_by_efficiency,
    rank_candidate_proposals,
    residual_colour_from_mass,
    residual_drop_from_ids,
    residual_drop_from_ledger_maps,
    residual_drop_mass,
    score_cochain_proposal,
    score_discrete_proposal,
    set_delta,
)


@pytest.fixture(autouse=True)
def _bind_exact_ports() -> None:
    initialize_exact_ports()


# ---------------------------------------------------------------------------
# Canonical Shared Kernel Unit Tests
# ---------------------------------------------------------------------------
class ColorEnum(enum.Enum):
    RED = 1
    BLUE = 2


@dataclass(frozen=True, slots=True)
class PointData:
    x: int
    y: str


def test_canonical_freeze_primitives() -> None:
    assert freeze(None) is None
    assert freeze(True) is True
    assert freeze(False) is False
    assert freeze(42) == 42
    assert freeze("symbol") == "symbol"
    assert thaw(freeze(b"raw_bytes")) == {"$bytes_hex": "7261775f6279746573"}
    assert thaw(freeze(Fraction(3, 4))) == {"$fraction": [3, 4]}


def test_canonical_freeze_compounds() -> None:
    assert thaw(freeze([1, 2, 3])) == [1, 2, 3]
    assert thaw(freeze((1, 2))) == {"$tuple": [1, 2]}
    assert thaw(freeze({1, 2})) == {"$set": [1, 2]}
    assert thaw(freeze(frozenset({1, 2}))) == {"$frozenset": [1, 2]}
    assert thaw(freeze({"b": 2, "a": 1})) == {"a": 1, "b": 2}


def test_canonical_freeze_refusals() -> None:
    with pytest.raises(CanonicalizationError, match="float"):
        freeze(1.0)
    with pytest.raises(CanonicalizationError, match="float"):
        freeze(float("nan"))
    with pytest.raises(CanonicalizationError, match="float"):
        freeze(float("inf"))

    class Unsupported:
        pass

    with pytest.raises(CanonicalizationError, match="unsupported canonical value"):
        freeze(Unsupported())


def test_canonical_wire_and_unwire_roundtrip() -> None:
    data = {
        "count": 5,
        "label": "node",
        "ratio": Fraction(1, 3),
        "tags": ["a", "b"],
    }
    wire = canonical_wire(data)
    assert isinstance(wire, list)
    assert wire[0] == "core-canonical-v1"
    assert wire[1] == "mapping"
    unwired = canonical_unwire(wire)
    assert thaw(unwired) == thaw(freeze(data))


def test_canonical_json_and_digest() -> None:
    cjson = canonical_json({"y": 2, "x": 1})
    assert cjson.startswith('["core-canonical-v1","mapping"')
    digest = domain_digest("test.domain.v1", {"a": 1})
    assert len(digest) == 64
    assert digest == domain_digest("test.domain.v1", {"a": 1})

    with pytest.raises(CanonicalizationError, match="non-empty"):
        domain_digest("", {"a": 1})


def test_canonical_unwire_malformed() -> None:
    with pytest.raises(CanonicalizationError, match="three-item array"):
        canonical_unwire("not a list")  # type: ignore

    with pytest.raises(CanonicalizationError, match="three-item array"):
        canonical_unwire([1, 2])

    with pytest.raises(CanonicalizationError, match="unknown canonical wire tag"):
        canonical_unwire(["core-canonical-v1", "unknown_tag", []])


# ---------------------------------------------------------------------------
# Coboundary Score Entity Unit Tests
# ---------------------------------------------------------------------------
def test_candidate_proposal_validations() -> None:
    # 1. Empty proposal_id
    with pytest.raises(ValueError, match="proposal_id must be a non-empty string"):
        CandidateProposal(proposal_id="")

    # 2. Negative structural cost
    with pytest.raises(ValueError, match="structural_cost must be a non-negative"):
        CandidateProposal(proposal_id="p1", structural_cost=Fraction(-1))

    # 3. Invalid dual_witness_ref
    with pytest.raises(ValueError, match="dual_witness_ref must be a 64-character"):
        CandidateProposal(proposal_id="p1", dual_witness_ref="invalid_hex")

    # 4. Duplicate repaired obstruction IDs
    with pytest.raises(ValueError, match="repaired_obstruction_ids must be unique"):
        CandidateProposal(proposal_id="p1", repaired_obstruction_ids=("obs1", "obs1"))

    # 5. Non-tuple repaired obstruction IDs
    with pytest.raises(ValueError, match="repaired_obstruction_ids must be a tuple"):
        CandidateProposal(proposal_id="p1", repaired_obstruction_ids=["obs1"])  # type: ignore

    # 6. Float in cochain delta
    with pytest.raises(ValueError, match=REFUSAL_INEXACT_COCHAIN_DELTA):
        CandidateProposal(proposal_id="p1", cochain_delta=(("e1", 1.5),))  # type: ignore


def test_coboundary_score_result_validations() -> None:
    # 1. Non-None authority effect
    with pytest.raises(ValueError, match="AuthorityEffect None"):
        CoboundaryScoreResult(
            proposal_id="p1",
            prior_residual_norm=Fraction(1),
            post_residual_norm=Fraction(0),
            residual_drop=Fraction(1),
            structural_cost=Fraction(0),
            authority_effect="PROMOTED",
        )

    # 2. Unsupported schema
    with pytest.raises(ValueError, match="unsupported schema version"):
        CoboundaryScoreResult(
            proposal_id="p1",
            prior_residual_norm=Fraction(1),
            post_residual_norm=Fraction(0),
            residual_drop=Fraction(1),
            structural_cost=Fraction(0),
            schema_version="invalid.v1",
        )

    # 3. Negative prior/post residual norm
    with pytest.raises(ValueError, match="prior_residual_norm must be non-negative"):
        CoboundaryScoreResult(
            proposal_id="p1",
            prior_residual_norm=Fraction(-1),
            post_residual_norm=Fraction(0),
            residual_drop=Fraction(1),
            structural_cost=Fraction(0),
        )

    with pytest.raises(ValueError, match="post_residual_norm must be non-negative"):
        CoboundaryScoreResult(
            proposal_id="p1",
            prior_residual_norm=Fraction(1),
            post_residual_norm=Fraction(-1),
            residual_drop=Fraction(1),
            structural_cost=Fraction(0),
        )

    # 4. Inexact exactness claim
    with pytest.raises(ValueError, match=REFUSAL_INEXACT_EXACTNESS_CLAIM):
        CoboundaryScoreResult(
            proposal_id="p1",
            prior_residual_norm=Fraction(1),
            post_residual_norm=0.0,  # type: ignore
            residual_drop=Fraction(1),
            structural_cost=Fraction(0),
            is_exact_candidate=True,
            dual_witness_ref="a" * 64,
        )

    # 5. Exact candidate requires post == 0 and dual witness
    with pytest.raises(ValueError, match="post_residual_norm == 0"):
        CoboundaryScoreResult(
            proposal_id="p1",
            prior_residual_norm=Fraction(1),
            post_residual_norm=Fraction(1),
            residual_drop=Fraction(0),
            structural_cost=Fraction(0),
            is_exact_candidate=True,
            dual_witness_ref="a" * 64,
        )

    with pytest.raises(ValueError, match="EXACT_WITHOUT_DUAL_WITNESS"):
        CoboundaryScoreResult(
            proposal_id="p1",
            prior_residual_norm=Fraction(1),
            post_residual_norm=Fraction(0),
            residual_drop=Fraction(1),
            structural_cost=Fraction(0),
            is_exact_candidate=True,
            dual_witness_ref=None,
        )

    # 6. Illegal score without refusal reason
    with pytest.raises(ValueError, match="illegal score result must specify a refusal_reason"):
        CoboundaryScoreResult(
            proposal_id="p1",
            prior_residual_norm=Fraction(1),
            post_residual_norm=Fraction(1),
            residual_drop=Fraction(0),
            structural_cost=Fraction(0),
            is_legal=False,
            refusal_reason=None,
        )


def test_coboundary_score_result_wire_roundtrip() -> None:
    score = CoboundaryScoreResult(
        proposal_id="p1",
        prior_residual_norm=Fraction(3, 2),
        post_residual_norm=Fraction(1, 2),
        residual_drop=Fraction(1),
        structural_cost=Fraction(1, 4),
        normalized_efficiency=Fraction(4, 5),
        is_legal=True,
        is_exact_candidate=False,
    )
    wire = score.to_dict()
    assert wire["prior_residual_norm"] == "3/2"
    assert wire["post_residual_norm"] == "1/2"
    assert wire["structural_cost"] == "1/4"
    assert wire["normalized_efficiency"] == "4/5"

    rebuilt = CoboundaryScoreResult.from_dict(wire)
    assert rebuilt.prior_residual_norm == score.prior_residual_norm
    assert rebuilt.post_residual_norm == score.post_residual_norm
    assert rebuilt.structural_cost == score.structural_cost
    assert rebuilt.normalized_efficiency == score.normalized_efficiency


# ---------------------------------------------------------------------------
# Scoring Use Case Unit Tests
# ---------------------------------------------------------------------------
def test_evaluate_coboundary_score_use_case() -> None:
    use_case = EvaluateCoboundaryScoreUseCase()
    proposal = CandidateProposal(
        proposal_id="p_eval",
        repaired_obstruction_ids=("obs1", "obs2"),
        structural_cost=Fraction(1),
    )
    res = use_case.execute(proposal, total_open_obstructions=5)
    assert res.prior_residual_norm == Fraction(5)
    assert res.post_residual_norm == Fraction(3)
    assert res.residual_drop == Fraction(2)
    assert res.structural_cost == Fraction(1)
    # efficiency = 2 / (1 + 1) = 1
    assert res.normalized_efficiency == Fraction(1)


def test_score_discrete_proposal_kill_conditions() -> None:
    # Kill trigger
    proposal = CandidateProposal(
        proposal_id="p_killed",
        kill_triggers=("F-01_inherited_meaning",),
    )
    res = score_discrete_proposal(("obs1",), proposal)
    assert not res.is_legal
    assert res.refusal_reason == REFUSAL_PROSE_PROMPT_REFUSED
    assert res.normalized_efficiency is None

    # Authority non-None trigger
    proposal_auth = CandidateProposal(
        proposal_id="p_auth",
        authority_effect="PROMOTED",
    )
    res_auth = score_discrete_proposal(("obs1",), proposal_auth)
    assert not res_auth.is_legal
    assert res_auth.refusal_reason == REFUSAL_AUTHORITY_NON_NONE


def test_score_cochain_proposal_exact_and_inexact() -> None:
    # Inexact cochain
    proposal = CandidateProposal(proposal_id="p_cochain")
    res_bad = score_cochain_proposal({"e1": 1.5}, proposal)  # type: ignore
    assert not res_bad.is_legal
    assert REFUSAL_INEXACT_COCHAIN in (res_bad.refusal_reason or "")

    # Exact cochain
    cochain = {"e1": Fraction(2), "e2": Fraction(1)}
    proposal_good = CandidateProposal(
        proposal_id="p_good",
        cochain_delta=(("e1", Fraction(1)),),
        structural_cost=Fraction(0),
    )
    res_good = score_cochain_proposal(cochain, proposal_good)
    assert res_good.is_legal
    assert res_good.prior_residual_norm == Fraction(3)
    assert res_good.post_residual_norm == Fraction(2)
    assert res_good.residual_drop == Fraction(1)
    assert res_good.normalized_efficiency == Fraction(1)


def test_rank_candidate_proposals() -> None:
    p1 = CandidateProposal(
        proposal_id="p1",
        repaired_obstruction_ids=("obs1",),
        structural_cost=Fraction(1),
    )
    p2 = CandidateProposal(
        proposal_id="p2",
        repaired_obstruction_ids=("obs1", "obs2"),
        structural_cost=Fraction(0),
    )
    p_bad = CandidateProposal(
        proposal_id="p_bad",
        kill_triggers=("F-01_inherited_meaning",),
    )

    ranked = rank_candidate_proposals(("obs1", "obs2"), [p1, p2, p_bad])
    assert len(ranked) == 3
    # Legal candidates outrank illegal candidates; higher efficiency outranks lower
    assert ranked[0].proposal_id == "p2"
    assert ranked[1].proposal_id == "p1"
    assert ranked[2].proposal_id == "p_bad"
    assert not ranked[2].is_legal


def test_helpers_l1_and_mass() -> None:
    assert l1_float([1.0, -2.5, 3.5]) == 7.0
    assert l1_rational([Fraction(1, 2), Fraction(-3, 2)]) == Fraction(2)
    assert mass_from_ids(("a", "b", "c"), unit=2.0) == 6.0
    assert mass_from_magnitudes({"a": 1.5, "b": 2.5}) == 4.0
    assert set_delta(("a", "b"), ("b", "c")) == (("a",), ("c",), ("b",))
    assert residual_colour_from_mass(0.0, dual_witness_present=True, open_ids=()) == "Exact"
    assert residual_colour_from_mass(0.0, dual_witness_present=False, open_ids=()) == "Closed"
    assert residual_colour_from_mass(1.0) == "Open"
    with pytest.raises(ValueError, match=REFUSAL_NEGATIVE_MAGNITUDE):
        residual_colour_from_mass(-1.0)


def test_residual_drop_from_ids_and_ledger_maps() -> None:
    # 1. Illegal drop
    illegal_drop = residual_drop_from_ids(("obs1",), ("obs1",), legal=False)
    assert not illegal_drop.legal
    assert illegal_drop.efficiency == -float("inf")

    # 2. Legal drop
    legal_drop = residual_drop_from_ids(
        ("obs1", "obs2"), ("obs2",), cost=1.0, dual_witness_present=True
    )
    assert legal_drop.legal
    assert legal_drop.delta == 1.0
    assert legal_drop.residual_colour == "Open"

    # 3. Exact declared colour without dual witness
    with pytest.raises(ValueError, match=REFUSAL_EXACT_WITHOUT_DUAL):
        residual_drop_from_ids((), (), declared_colour="Exact", dual_witness_present=False)

    # 4. From ledger maps
    map_drop = residual_drop_from_ledger_maps(
        {"obs1": 2.0, "obs2": 1.0},
        {"obs2": 1.0},
        cost=0.5,
        dual_witness_present=True,
    )
    assert map_drop.legal
    assert map_drop.delta == 2.0

    # 5. Rank by efficiency
    ranked = rank_by_efficiency([illegal_drop, legal_drop, map_drop])
    assert len(ranked) == 2
    assert ranked[0] in (legal_drop, map_drop)


def test_magnitudes_from_ledger_active() -> None:
    active = {
        "a": 1,
        "b": 2.5,
        "c": {"magnitude": 3.5},
        "d": type("Obj", (), {"magnitude": 4.5})(),
        "e": "other",
    }
    mags = magnitudes_from_ledger_active(active)
    assert mags["a"] == 1.0
    assert mags["b"] == 2.5
    assert mags["c"] == 3.5
    assert mags["d"] == 4.5
    assert mags["e"] == 1.0


def test_admitted_constructors_filter() -> None:
    # Discrete proposal with unadmitted constructor
    proposal = CandidateProposal(
        proposal_id="p_const",
        admitted_constructors_used=("unadmitted_ctor",),
    )
    res_discrete = score_discrete_proposal(
        ("obs1",),
        proposal,
        admitted_constructors={"allowed_ctor"},
    )
    assert not res_discrete.is_legal
    assert res_discrete.refusal_reason == REFUSAL_PROSE_PROMPT_REFUSED

    # Cochain proposal with unadmitted constructor
    res_cochain = score_cochain_proposal(
        {"e1": Fraction(1)},
        proposal,
        admitted_constructors={"allowed_ctor"},
    )
    assert not res_cochain.is_legal
    assert res_cochain.refusal_reason == REFUSAL_PROSE_PROMPT_REFUSED


def test_residual_drop_v1_wire_roundtrip() -> None:
    drop = ResidualDropV1(
        core_mass=5.0,
        residual_mass=2.0,
        delta=3.0,
        relative_drop=0.6,
        eliminated_ids=("obs1",),
        opened_ids=(),
        retained_ids=("obs2",),
        cost=1.0,
        efficiency=1.5,
        residual_colour="Open",
        dual_witness_present=False,
        legal=True,
        refusal_code=None,
    )
    d = drop.to_dict()
    assert d["delta"] == 3.0
    assert d["efficiency"] == 1.5
    assert d["legal"] is True


def test_canonical_edge_cases() -> None:
    # Non-string key in dict
    with pytest.raises(CanonicalizationError, match="exact strings"):
        freeze({1: "val"})  # type: ignore

    # Subclass of builtin
    class SubList(list):
        pass

    with pytest.raises(CanonicalizationError, match="subclasses"):
        freeze(SubList([1, 2]))


def test_coboundary_score_edge_branches() -> None:
    # 1. Non-finite float cost in CandidateProposal
    with pytest.raises(ValueError, match="structural_cost must be a non-negative finite number"):
        CandidateProposal(proposal_id="p", structural_cost=float("nan"))

    # 2. NotExactError in CandidateProposal structural_cost
    with pytest.raises(ValueError, match="structural_cost must be an exact rational"):
        CandidateProposal(proposal_id="p", structural_cost="not_a_number")  # type: ignore

    # 3. Family mismatch in CoboundaryScoreResult
    with pytest.raises(ValueError, match="unsupported family"):
        CoboundaryScoreResult(
            proposal_id="p",
            prior_residual_norm=Fraction(1),
            post_residual_norm=Fraction(0),
            residual_drop=Fraction(1),
            structural_cost=Fraction(0),
            family="unsupported_family",
        )

    # 4. NotExactError in prior_residual_norm
    with pytest.raises(ValueError, match=REFUSAL_INEXACT_RESIDUAL_NORM):
        CoboundaryScoreResult(
            proposal_id="p",
            prior_residual_norm="bad_val",  # type: ignore
            post_residual_norm=Fraction(0),
            residual_drop=Fraction(1),
            structural_cost=Fraction(0),
        )

    # 5. Non-finite float in CoboundaryScoreResult structural_cost
    with pytest.raises(ValueError, match="structural_cost must be non-negative"):
        CoboundaryScoreResult(
            proposal_id="p",
            prior_residual_norm=Fraction(1),
            post_residual_norm=Fraction(0),
            residual_drop=Fraction(1),
            structural_cost=float("inf"),
        )

    # 6. NotExactError in CoboundaryScoreResult structural_cost
    with pytest.raises(ValueError, match="structural_cost must be an exact rational"):
        CoboundaryScoreResult(
            proposal_id="p",
            prior_residual_norm=Fraction(1),
            post_residual_norm=Fraction(0),
            residual_drop=Fraction(1),
            structural_cost="not_exact",  # type: ignore
        )

    # 7. Non-finite float in normalized_efficiency
    with pytest.raises(ValueError, match="normalized_efficiency must be finite"):
        CoboundaryScoreResult(
            proposal_id="p",
            prior_residual_norm=Fraction(1),
            post_residual_norm=Fraction(0),
            residual_drop=Fraction(1),
            structural_cost=Fraction(0),
            normalized_efficiency=float("nan"),
        )

    # 8. NotExactError in normalized_efficiency
    with pytest.raises(ValueError, match="normalized_efficiency must be an exact rational"):
        CoboundaryScoreResult(
            proposal_id="p",
            prior_residual_norm=Fraction(1),
            post_residual_norm=Fraction(0),
            residual_drop=Fraction(1),
            structural_cost=Fraction(0),
            normalized_efficiency="invalid",  # type: ignore
        )


def test_scoring_edge_branches() -> None:
    # 1. mass_from_magnitudes valid and errors
    mags = mass_from_magnitudes({
        "a": 2.0,
        "b": 3,
        "c": 4.0,
    })
    assert mags == 9.0
    with pytest.raises(TypeError, match="magnitude for 'bad' must be float/int"):
        mass_from_magnitudes({"bad": "not_a_number"})  # type: ignore
    with pytest.raises(ValueError, match=REFUSAL_NEGATIVE_MAGNITUDE):
        mass_from_magnitudes({"neg": -1.0})

    # 2. residual_drop_mass error branches
    with pytest.raises(ValueError, match=REFUSAL_NEGATIVE_MAGNITUDE):
        residual_drop_mass(-1.0, 1.0)
    with pytest.raises(ValueError, match=REFUSAL_NEGATIVE_MAGNITUDE):
        residual_drop_mass(1.0, -1.0)
    with pytest.raises(ValueError, match="cost must be nonnegative"):
        residual_drop_mass(1.0, 0.5, cost=-0.5)

    # 3. residual_colour_from_mass
    with pytest.raises(ValueError, match=REFUSAL_NEGATIVE_MAGNITUDE):
        residual_colour_from_mass(-1.0)
    assert residual_colour_from_mass(0.0, dual_witness_present=True, open_ids=()) == "Exact"
    assert residual_colour_from_mass(0.0, dual_witness_present=False, open_ids=()) == "Closed"
    assert residual_colour_from_mass(1.0, open_ids=("obs1",)) == "Open"

    # 4. score_cochain_proposal with authority_effect != "None"
    p_auth = CandidateProposal(proposal_id="p_co_auth", authority_effect="INVALID")
    res_auth = score_cochain_proposal({"e1": Fraction(1)}, p_auth)
    assert not res_auth.is_legal
    assert res_auth.refusal_reason == REFUSAL_AUTHORITY_NON_NONE

    # 5. score_cochain_proposal with kill trigger
    p_kill = CandidateProposal(proposal_id="p_co_kill", kill_triggers=("F-01_inherited_meaning",))
    res_kill = score_cochain_proposal({"e1": Fraction(1)}, p_kill)
    assert not res_kill.is_legal
    assert res_kill.refusal_reason == REFUSAL_PROSE_PROMPT_REFUSED

    # 6. score_cochain_proposal with unadmitted constructor
    p_unadmitted = CandidateProposal(proposal_id="p_unadmitted", admitted_constructors_used=("forbidden_constructor",))
    res_unadmitted = score_cochain_proposal({"e1": Fraction(1)}, p_unadmitted, admitted_constructors=("allowed_c1",))
    assert not res_unadmitted.is_legal
    assert res_unadmitted.refusal_reason == REFUSAL_PROSE_PROMPT_REFUSED

    # 7. rank_candidate_proposals with single sequence, kwargs, and invalid args
    res1 = score_discrete_proposal(("obs1",), CandidateProposal(proposal_id="r1"))
    ranked = rank_candidate_proposals([res1])
    assert len(ranked) == 1
    assert ranked[0].proposal_id == "r1"

    ranked_2 = rank_candidate_proposals(("obs1",), [CandidateProposal(proposal_id="r2")])
    assert len(ranked_2) == 1
    assert ranked_2[0].proposal_id == "r2"

    with pytest.raises(TypeError, match="Invalid arguments for rank_candidate_proposals"):
        rank_candidate_proposals()


def test_coboundary_score_float_and_edge_branches() -> None:
    # 1. _norm_from_wire with float
    wire_float = {"norm": 2.5}
    assert _norm_from_wire(wire_float, "norm") == Fraction(5, 2)
    with pytest.raises(ValueError, match="norm must be finite"):
        _norm_from_wire({"norm": float("inf")}, "norm")
    with pytest.raises(ValueError, match="norm must be finite"):
        _norm_from_wire({"norm": float("nan")}, "norm")

    # 2. CandidateProposal with float structural_cost
    p_float = CandidateProposal(proposal_id="p_fl", structural_cost=1.5)
    assert p_float.structural_cost == Fraction(3, 2)
    with pytest.raises(ValueError, match="structural_cost must be a non-negative finite number"):
        CandidateProposal(proposal_id="p_bad_cost", structural_cost=float("inf"))
    with pytest.raises(ValueError, match="structural_cost must be a non-negative finite number"):
        CandidateProposal(proposal_id="p_bad_cost_neg", structural_cost=-0.5)

    # 3. CoboundaryScoreResult with float structural_cost and normalized_efficiency
    r_float = CoboundaryScoreResult(
        proposal_id="r_fl",
        prior_residual_norm=Fraction(1),
        post_residual_norm=Fraction(0),
        residual_drop=Fraction(1),
        structural_cost=1.5,
        normalized_efficiency=0.5,
    )
    assert r_float.structural_cost == Fraction(3, 2)
    assert r_float.normalized_efficiency == Fraction(1, 2)

    with pytest.raises(ValueError, match="structural_cost must be non-negative"):
        CoboundaryScoreResult(
            proposal_id="r_bad",
            prior_residual_norm=Fraction(1),
            post_residual_norm=Fraction(0),
            residual_drop=Fraction(1),
            structural_cost=float("inf"),
        )
    with pytest.raises(ValueError, match="structural_cost must be non-negative"):
        CoboundaryScoreResult(
            proposal_id="r_bad_neg",
            prior_residual_norm=Fraction(1),
            post_residual_norm=Fraction(0),
            residual_drop=Fraction(1),
            structural_cost=-1.0,
        )
    with pytest.raises(ValueError, match="prior_residual_norm must be non-negative"):
        CoboundaryScoreResult(
            proposal_id="r_bad_prior",
            prior_residual_norm=Fraction(-1),
            post_residual_norm=Fraction(0),
            residual_drop=Fraction(0),
            structural_cost=Fraction(0),
        )
    with pytest.raises(ValueError, match="post_residual_norm must be non-negative"):
        CoboundaryScoreResult(
            proposal_id="r_bad_post",
            prior_residual_norm=Fraction(1),
            post_residual_norm=Fraction(-1),
            residual_drop=Fraction(0),
            structural_cost=Fraction(0),
        )


def test_canonical_shared_kernel_deep_coverage() -> None:
    # 1. _declared_slots
    class BaseWithStrSlot:
        __slots__ = "single_slot"

    class DerivedWithTupleSlots(BaseWithStrSlot):
        __slots__ = ("extra1", "extra2")

    slots = _declared_slots(DerivedWithTupleSlots)
    assert slots == frozenset({"single_slot", "extra1", "extra2"})

    # 2. _validate_enum_instance
    class CleanEnum(enum.Enum):
        A = 1
        B = 2

    _validate_enum_instance(CleanEnum.A)

    class CorruptDictEnum(enum.Enum):
        X = 10

    # Test undeclared instance state
    CorruptDictEnum.X.__dict__["rogue_key"] = "bad"
    with pytest.raises(CanonicalizationError, match="undeclared instance state"):
        _validate_enum_instance(CorruptDictEnum.X)
    del CorruptDictEnum.X.__dict__["rogue_key"]

    # Test inconsistent state (_sort_order_ not int)
    CorruptDictEnum.X.__dict__["_sort_order_"] = "not_int"
    with pytest.raises(CanonicalizationError, match="inconsistent"):
        _validate_enum_instance(CorruptDictEnum.X)
    CorruptDictEnum.X.__dict__["_sort_order_"] = 0

    # Test sort order mismatch
    CorruptDictEnum.X.__dict__["_sort_order_"] = 999
    with pytest.raises(CanonicalizationError, match="sort order"):
        _validate_enum_instance(CorruptDictEnum.X)
    CorruptDictEnum.X.__dict__["_sort_order_"] = 0

    # Test undeclared slot state on enum
    class EnumWithSlot(enum.Enum):
        __slots__ = ("extra_slot",)
        A = 1

    EnumWithSlot.A.extra_slot = "present"
    with pytest.raises(CanonicalizationError, match="undeclared slot state"):
        _validate_enum_instance(EnumWithSlot.A)

    # 3. _validate_dataclass_instance
    @dataclass
    class SimpleDataclass:
        x: int

    dc = SimpleDataclass(x=42)
    _validate_dataclass_instance(dc)
    dc.__dict__["extra_attr"] = "not_declared"
    with pytest.raises(CanonicalizationError, match="undeclared instance attributes"):
        _validate_dataclass_instance(dc)

    # Dataclass with undeclared slot attributes
    @dataclass
    class DataclassWithSlot:
        __slots__ = ("x", "rogue_slot")
        x: int

    dc_slot = DataclassWithSlot(x=1)
    dc_slot.rogue_slot = "rogue"
    with pytest.raises(CanonicalizationError, match="undeclared slot attributes"):
        _validate_dataclass_instance(dc_slot)

    # 4. thaw on internal _FrozenValue nodes
    assert thaw(_FrozenValue("tuple", (freeze(1), freeze(2)))) == {"$tuple": [1, 2]}
    assert thaw(_FrozenValue("set", (freeze(1), freeze(2)))) == {"$set": [1, 2]}
    assert thaw(_FrozenValue("frozenset", (freeze(1), freeze(2)))) == {"$frozenset": [1, 2]}
    assert thaw(_FrozenValue("float", ("0x1.0p0",))) == {"$float_hex": "0x1.0p0"}
    assert thaw(_FrozenValue("fraction", (1, 2))) == {"$fraction": [1, 2]}
    assert thaw(_FrozenValue("bytes", ("0102",))) == {"$bytes_hex": "0102"}
    assert thaw(_FrozenValue("enum", ("mod", "Cls", "A", freeze(1)))) == {
        "$enum": ["mod", "Cls", "A", 1]
    }
    assert thaw(_FrozenValue("field", ("fname", freeze(10)))) == ["fname", 10]
    assert thaw(_FrozenValue("entry", ("ekey", freeze(20)))) == ["ekey", 20]
    dc_frozen = _FrozenValue(
        "dataclass",
        ("mod", "Cls", _FrozenValue("field", ("f1", freeze(99)))),
    )
    assert thaw(dc_frozen) == {"$dataclass": ["mod", "Cls"], "fields": [["f1", 99]]}
    with pytest.raises(CanonicalizationError, match="unknown frozen tag"):
        thaw(_FrozenValue("unknown_tag_xyz", ()))

    # 5. canonical_wire primitives & escape
    assert canonical_wire(None) == ["core-canonical-v1", "null", None]
    assert canonical_wire(True) == ["core-canonical-v1", "bool", True]
    assert canonical_wire(False) == ["core-canonical-v1", "bool", False]
    assert canonical_wire(100) == ["core-canonical-v1", "int", "100"]
    assert canonical_wire("str_val") == ["core-canonical-v1", "string", "str_val"]

    # 6. canonical_unwire format validation
    with pytest.raises(CanonicalizationError, match="must be a three-item array"):
        canonical_unwire(["core-canonical-v1", "null"])
    with pytest.raises(CanonicalizationError, match="marker or tag is invalid"):
        canonical_unwire(["bad-marker", "null", None])
    with pytest.raises(CanonicalizationError, match="marker or tag is invalid"):
        canonical_unwire(["core-canonical-v1", 123, None])

    # null
    assert canonical_unwire(["core-canonical-v1", "null", None]) is None
    with pytest.raises(CanonicalizationError, match="non-null body"):
        canonical_unwire(["core-canonical-v1", "null", "not_null"])

    # bool
    assert canonical_unwire(["core-canonical-v1", "bool", True]) is True
    with pytest.raises(CanonicalizationError, match="bool body is invalid"):
        canonical_unwire(["core-canonical-v1", "bool", "true"])

    # int
    assert canonical_unwire(["core-canonical-v1", "int", "42"]) == 42
    with pytest.raises(CanonicalizationError, match="int body is invalid"):
        canonical_unwire(["core-canonical-v1", "int", 42])
    with pytest.raises(CanonicalizationError, match="int body is invalid"):
        canonical_unwire(["core-canonical-v1", "int", "invalid"])
    with pytest.raises(CanonicalizationError, match="not minimally encoded"):
        canonical_unwire(["core-canonical-v1", "int", "042"])

    # string
    assert canonical_unwire(["core-canonical-v1", "string", "test"]) == "test"
    with pytest.raises(CanonicalizationError, match="string body is invalid"):
        canonical_unwire(["core-canonical-v1", "string", 123])

    # unknown tag
    with pytest.raises(CanonicalizationError, match="unknown canonical wire tag"):
        canonical_unwire(["core-canonical-v1", "unregistered_tag", []])

    # non-list compound body
    with pytest.raises(CanonicalizationError, match="compound body must be an array"):
        canonical_unwire(["core-canonical-v1", "list", "not_a_list"])

    # float forbidden
    with pytest.raises(CanonicalizationError, match="float values are forbidden"):
        canonical_unwire(["core-canonical-v1", "float", [["core-canonical-v1", "string", "0x1.0p0"]]])

    # 7. _validate_compound edge cases
    # set / frozenset unordered or duplicate
    with pytest.raises(CanonicalizationError, match="items must be unique and ordered"):
        _validate_compound(_FrozenValue("set", (freeze(2), freeze(1))))
    with pytest.raises(CanonicalizationError, match="items must be unique and ordered"):
        _validate_compound(_FrozenValue("set", (freeze(1), freeze(1))))

    # fraction
    with pytest.raises(CanonicalizationError, match="canonical fraction payload is invalid"):
        _validate_compound(_FrozenValue("fraction", (1,)))
    with pytest.raises(CanonicalizationError, match="canonical fraction payload is invalid"):
        _validate_compound(_FrozenValue("fraction", (1, 0)))
    with pytest.raises(CanonicalizationError, match="canonical fraction payload is not normalized"):
        _validate_compound(_FrozenValue("fraction", (2, 4)))

    # bytes
    with pytest.raises(CanonicalizationError, match="canonical bytes payload is invalid"):
        _validate_compound(_FrozenValue("bytes", ()))
    with pytest.raises(CanonicalizationError, match="canonical bytes payload is invalid"):
        _validate_compound(_FrozenValue("bytes", ("not_hex_zz",)))
    with pytest.raises(CanonicalizationError, match="canonical bytes payload is not normalized"):
        _validate_compound(_FrozenValue("bytes", ("0A",)))  # uppercase

    # enum
    with pytest.raises(CanonicalizationError, match="canonical enum payload is invalid"):
        _validate_compound(_FrozenValue("enum", ("mod", "Cls")))
    with pytest.raises(CanonicalizationError, match="identity is invalid"):
        _validate_compound(_FrozenValue("enum", ("", "Cls", "A", freeze(1))))

    # field & entry
    with pytest.raises(CanonicalizationError, match="canonical field payload is invalid"):
        _validate_compound(_FrozenValue("field", ("fname",)))
    with pytest.raises(CanonicalizationError, match="canonical field name is invalid"):
        _validate_compound(_FrozenValue("field", ("", freeze(1))))
    with pytest.raises(CanonicalizationError, match="canonical entry payload is invalid"):
        _validate_compound(_FrozenValue("entry", ("ekey",)))

    # dataclass
    with pytest.raises(CanonicalizationError, match="canonical dataclass identity is invalid"):
        _validate_compound(_FrozenValue("dataclass", ("", "Cls")))
    with pytest.raises(CanonicalizationError, match="fields are invalid"):
        _validate_compound(_FrozenValue("dataclass", ("mod", "Cls", "not_a_field")))
    with pytest.raises(CanonicalizationError, match="fields are duplicated"):
        _validate_compound(
            _FrozenValue(
                "dataclass",
                ("mod", "Cls", _FrozenValue("field", ("f1", freeze(1))), _FrozenValue("field", ("f1", freeze(2)))),
            )
        )

    # mapping
    with pytest.raises(CanonicalizationError, match="exact built-in dict"):
        _validate_compound(_FrozenValue("mapping", ("custom", "dict")))
    with pytest.raises(CanonicalizationError, match="entries are invalid"):
        _validate_compound(_FrozenValue("mapping", ("builtins", "dict", "not_an_entry")))
    with pytest.raises(CanonicalizationError, match="keys must be unique and ordered"):
        _validate_compound(
            _FrozenValue(
                "mapping",
                (
                    "builtins",
                    "dict",
                    _FrozenValue("entry", ("k2", freeze(1))),
                    _FrozenValue("entry", ("k1", freeze(2))),
                ),
            )
        )
    with pytest.raises(CanonicalizationError, match="keys must be unique and ordered"):
        _validate_compound(
            _FrozenValue(
                "mapping",
                (
                    "builtins",
                    "dict",
                    _FrozenValue("entry", ("k1", freeze(1))),
                    _FrozenValue("entry", ("k1", freeze(2))),
                ),
            )
        )

    # unknown compound tag
    with pytest.raises(CanonicalizationError, match="unknown frozen tag"):
        _validate_compound(_FrozenValue("unknown_compound_xyz", ()))
