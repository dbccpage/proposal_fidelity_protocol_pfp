"""
test_authority_gap.py

Unit tests for mod_authority_gap_core.py validating the 7-layer stack,
Negative Gluing Defect (NGD), Authority Coverage Ratio (ACR), and
Exactness Fraud Criterion.
"""

from dataclasses import replace
from fractions import Fraction

import pytest

try:
    from mod_authority_gap_core import (
        Attestation,
        AuthorityPacket,
        Institution,
        ObserverPacket,
        Proposal,
        Residual,
        Terminal,
        TerminalStatus,
        TraceRecord,
        calculate_acr,
        calculate_acr_rate,
        calculate_backlog_accumulation,
        calculate_ngd,
        create_bound_attestation,
        evaluate_exactness_fraud_criterion,
    )
except ImportError:
    from code.mod_authority_gap_core import (
        Attestation,
        AuthorityPacket,
        Institution,
        ObserverPacket,
        Proposal,
        Residual,
        Terminal,
        TerminalStatus,
        TraceRecord,
        calculate_acr,
        calculate_acr_rate,
        calculate_backlog_accumulation,
        calculate_ngd,
        create_bound_attestation,
        evaluate_exactness_fraud_criterion,
    )


@pytest.fixture
def sample_proposal():
    return Proposal(
        proposal_id="prop_001",
        generator_id="agent_generator_alpha",
        payload="Recommended action: Approve disbursement of funds based on doc_12.",
        context="Procurement request #8841",
    )


@pytest.fixture
def sample_trace(sample_proposal):
    return TraceRecord.create(
        trace_id="tr_001",
        actions=["read_file", "search_database", "draft_decision"],
        tool_calls=["db_lookup:vendor_id=44", "verify_invoice:hash=abcdef"],
        sources=["vendor_master.csv", "invoice_99.pdf"],
        proposal=sample_proposal,
    )


@pytest.fixture
def sample_observer():
    return ObserverPacket(
        carrier="ProcurementVerificationGraph",
        local_states=("vendor_active", "invoice_math_checked", "budget_available"),
        comparisons=("check_vendor_status", "sum_line_items", "verify_allocations"),
        defects=(),
        admissible_repairs=("recalculate_tax",),
        gauge="format_differences",
        closure_diagnostics=("global_budget_exhaustion",),
    )


@pytest.fixture
def sample_institution():
    return Institution(
        entity_id="AcmeCorp_AuditOffice",
        governing_jurisdiction="US-DE",
        accountable_officer="Jane Doe, Comptroller",
        appeal_path="https://compliance.example.org/appeals/procurement",
    )


def test_legitimate_authorized_packet(sample_proposal, sample_trace, sample_observer, sample_institution):
    """Test that a fully descended, zero-residual packet with bound attestation and decider passes structural check."""
    residual = Residual(
        defect_mass=Fraction(0, 1),
        unverified_scope=(),
        refusal_reasons=(),
    )
    terminal = Terminal(
        status=TerminalStatus.AUTHORIZED_UNDER_OBSERVER,
        decider_id="officer_jane_doe",
        is_human_or_delegated_body=True,
        justification="All invoice line items matched purchase order.",
    )
    attestation = create_bound_attestation(
        proposal=sample_proposal,
        trace=sample_trace,
        observer=sample_observer,
        residual=residual,
        terminal=terminal,
        institution=sample_institution,
        replay_receipt="receipt_ok_2026",
        descent_executed=True,
    )
    packet = AuthorityPacket(
        proposal=sample_proposal,
        trace=sample_trace,
        observer=sample_observer,
        residual=residual,
        terminal=terminal,
        attestation=attestation,
        institution=sample_institution,
    )

    valid, reason = evaluate_exactness_fraud_criterion(packet)
    assert valid is True
    assert "Structurally consistent but unverified until an independent verifier binds and checks the evidence" in reason


def test_trace_encoding_no_delimiter_ambiguity():
    """Test that distinct traces ['ab'], ['c'] and ['a'], ['bc'] receive distinct digests."""
    trace_1 = TraceRecord.create(
        trace_id="tr_ambig_1",
        actions=["ab"],
        tool_calls=["c"],
        sources=[],
    )
    trace_2 = TraceRecord.create(
        trace_id="tr_ambig_1",
        actions=["a"],
        tool_calls=["bc"],
        sources=[],
    )
    assert trace_1.content_hash != trace_2.content_hash


def test_trace_custody_tamper_detection(sample_proposal, sample_trace, sample_observer, sample_institution):
    """Test that a tampered trace hash fails the structural consistency check."""
    tampered_trace = TraceRecord(
        trace_id=sample_trace.trace_id,
        actions=sample_trace.actions,
        tool_calls=sample_trace.tool_calls,
        sources=sample_trace.sources,
        content_hash="tampered_hash_deadbeef",
        proposal_id=sample_trace.proposal_id,
    )
    residual = Residual(defect_mass=Fraction(0, 1), unverified_scope=(), refusal_reasons=())
    terminal = Terminal(
        status=TerminalStatus.AUTHORIZED_UNDER_OBSERVER,
        decider_id="officer_jane_doe",
        is_human_or_delegated_body=True,
        justification="Looks right.",
    )
    attestation = Attestation(descent_executed=True, verification_hash="hash_1", replay_receipt="rcpt_1")
    packet = AuthorityPacket(
        proposal=sample_proposal,
        trace=tampered_trace,
        observer=sample_observer,
        residual=residual,
        terminal=terminal,
        attestation=attestation,
        institution=sample_institution,
    )

    valid, reason = evaluate_exactness_fraud_criterion(packet)
    assert valid is False
    assert "Trace custody failure" in reason


def test_residual_refusal_reasons_make_inexact():
    """Test that Residual.is_exact is False when refusal_reasons is non-empty."""
    res_clean = Residual(defect_mass=Fraction(0, 1), unverified_scope=(), refusal_reasons=())
    assert res_clean.is_exact is True

    res_with_refusal = Residual(
        defect_mass=Fraction(0, 1),
        unverified_scope=(),
        refusal_reasons=("unresolved_boundary_curvature",),
    )
    assert res_with_refusal.is_exact is False


def test_counterfeit_descent_unattested_authorization(sample_proposal, sample_trace, sample_observer, sample_institution):
    """Test that claiming authorization without executed descent is refuted as counterfeit descent."""
    residual = Residual(defect_mass=Fraction(0, 1), unverified_scope=(), refusal_reasons=())
    terminal = Terminal(
        status=TerminalStatus.AUTHORIZED_UNDER_OBSERVER,
        decider_id="officer_jane_doe",
        is_human_or_delegated_body=True,
        justification="Looks right.",
    )
    attestation = Attestation(
        descent_executed=False,
        verification_hash="",
        replay_receipt=None,
    )
    packet = AuthorityPacket(
        proposal=sample_proposal,
        trace=sample_trace,
        observer=sample_observer,
        residual=residual,
        terminal=terminal,
        attestation=attestation,
        institution=sample_institution,
    )

    valid, reason = evaluate_exactness_fraud_criterion(packet)
    assert valid is False
    assert "Counterfeit descent" in reason
    assert "without executed descent attestation" in reason


def test_counterfeit_descent_masked_residual(sample_proposal, sample_trace, sample_observer, sample_institution):
    """Test that claiming authorization despite non-zero defect residual is refuted."""
    residual = Residual(
        defect_mass=Fraction(3, 10),
        unverified_scope=("tax_jurisdiction_check",),
        refusal_reasons=(),
    )
    terminal = Terminal(
        status=TerminalStatus.AUTHORIZED_UNDER_OBSERVER,
        decider_id="officer_jane_doe",
        is_human_or_delegated_body=True,
        justification="Approved despite minor mismatch.",
    )
    attestation = Attestation(
        descent_executed=True,
        verification_hash="hash_partial_55",
        replay_receipt=None,
    )
    packet = AuthorityPacket(
        proposal=sample_proposal,
        trace=sample_trace,
        observer=sample_observer,
        residual=residual,
        terminal=terminal,
        attestation=attestation,
        institution=sample_institution,
    )

    valid, reason = evaluate_exactness_fraud_criterion(packet)
    assert valid is False
    assert "Exactness fraud violation" in reason
    assert "Exactness claimed with non-zero residual" in reason


def test_scoped_authorization_with_tolerated_residual(sample_proposal, sample_trace, sample_observer, sample_institution):
    """Test that scoped authorization permits residual within declared tolerance, but refutes excess residual."""
    residual_tolerated = Residual(
        defect_mass=Fraction(3, 10),
        unverified_scope=(),
        refusal_reasons=(),
    )
    terminal_scoped = Terminal(
        status=TerminalStatus.AUTHORIZED_UNDER_OBSERVER,
        decider_id="officer_jane_doe",
        is_human_or_delegated_body=True,
        justification="Approved under policy allowing defect mass up to 1/2.",
        claims_exactness=False,
        tolerated_defect_mass=Fraction(1, 2),
    )
    attestation = create_bound_attestation(
        proposal=sample_proposal,
        trace=sample_trace,
        observer=sample_observer,
        residual=residual_tolerated,
        terminal=terminal_scoped,
        institution=sample_institution,
        replay_receipt="receipt_policy_waiver_12",
        descent_executed=True,
    )
    packet_tolerated = AuthorityPacket(
        proposal=sample_proposal,
        trace=sample_trace,
        observer=sample_observer,
        residual=residual_tolerated,
        terminal=terminal_scoped,
        attestation=attestation,
        institution=sample_institution,
    )
    valid, reason = evaluate_exactness_fraud_criterion(packet_tolerated)
    assert valid is True
    assert "Structurally consistent but unverified" in reason

    # Now exceed tolerated defect mass
    residual_excess = Residual(
        defect_mass=Fraction(7, 10),  # Exceeds 1/2
        unverified_scope=(),
        refusal_reasons=(),
    )
    attestation_excess = create_bound_attestation(
        proposal=sample_proposal,
        trace=sample_trace,
        observer=sample_observer,
        residual=residual_excess,
        terminal=terminal_scoped,
        institution=sample_institution,
        replay_receipt="receipt_policy_waiver_12",
        descent_executed=True,
    )
    packet_excess = AuthorityPacket(
        proposal=sample_proposal,
        trace=sample_trace,
        observer=sample_observer,
        residual=residual_excess,
        terminal=terminal_scoped,
        attestation=attestation_excess,
        institution=sample_institution,
    )
    valid_ex, reason_ex = evaluate_exactness_fraud_criterion(packet_excess)
    assert valid_ex is False
    assert "Scoped authorization violation" in reason_ex
    assert "exceeds declared tolerance 1/2" in reason_ex


def test_self_critique_non_authority_violation(sample_proposal, sample_trace, sample_observer, sample_institution):
    """Test that model cannot evaluate and authorize its own proposal."""
    residual = Residual(defect_mass=Fraction(0, 1), unverified_scope=(), refusal_reasons=())
    terminal = Terminal(
        status=TerminalStatus.AUTHORIZED_UNDER_OBSERVER,
        decider_id="agent_generator_alpha",  # Same as proposal generator!
        is_human_or_delegated_body=False,
        justification="The model determined its own reasoning is sound.",
    )
    attestation = Attestation(descent_executed=True, verification_hash="hash_self", replay_receipt=None)
    packet = AuthorityPacket(
        proposal=sample_proposal,
        trace=sample_trace,
        observer=sample_observer,
        residual=residual,
        terminal=terminal,
        attestation=attestation,
        institution=sample_institution,
    )

    valid, reason = evaluate_exactness_fraud_criterion(packet)
    assert valid is False
    assert "Proposal generator cannot be the terminal decider" in reason


def test_ngd_computation():
    """Test exact calculation of Negative Gluing Defect."""
    evals = [
        {"local_green": True, "global_red": False},
        {"local_green": True, "global_red": True},
        {"local_green": True, "global_red": True},
        {"local_green": False, "global_red": True},  # Rejected locally
        {"local_green": True, "global_red": False},
    ]
    # Local green = 4 cases. Among them, global red = 2 cases.
    # NGD = 2 / 4 = 1 / 2
    ngd = calculate_ngd(evals)
    assert ngd == Fraction(1, 2)


def test_ngd_zero_local_green_undefined():
    """Test that NGD reports None when there are no local-green cases (conditional rate undefined)."""
    evals = [
        {"local_green": False, "global_red": True},
        {"local_green": False, "global_red": False},
    ]
    assert calculate_ngd(evals) is None


def test_acr_computation():
    """Test exact calculation of Authority Coverage Ratio."""
    # 25 verified packets out of 100 proposals
    acr = calculate_acr(verified_count=25, proposal_count=100)
    assert acr == Fraction(1, 4)

    # Empty proposal set (undefined ratio 0 / 0 returns None)
    acr_zero = calculate_acr(verified_count=0, proposal_count=0)
    assert acr_zero is None


def test_acr_capacity_bounds():
    """Test that ACR rejects verified_count exceeding proposal_count."""
    with pytest.raises(ValueError, match="cannot exceed proposal_count"):
        calculate_acr(verified_count=2, proposal_count=1)

    with pytest.raises(ValueError, match="non-negative"):
        calculate_acr(verified_count=-1, proposal_count=10)


def test_rate_asymmetry_backlog():
    """Test authority backlog accumulation when generation outpaces verification."""
    # Generation rate = 50 proposals / min
    # Verification rate = 10 proposals / min
    r_g = Fraction(50, 1)
    r_v = Fraction(10, 1)
    delta_t = 12  # 12 minutes
    backlog = calculate_backlog_accumulation(r_g, r_v, delta_t)
    assert backlog == Fraction(480, 1)


def test_calculate_acr_rate():
    """Test instantaneous Authority Coverage Ratio calculation from rates."""
    r_g = Fraction(50, 1)
    r_v = Fraction(10, 1)
    acr_rate = calculate_acr_rate(rate_verification=r_v, rate_generation=r_g)
    assert acr_rate == Fraction(1, 5)

    with pytest.raises(ValueError, match="strictly positive"):
        calculate_acr_rate(rate_verification=Fraction(1, 1), rate_generation=Fraction(0, 1))

    with pytest.raises(ValueError, match="non-negative"):
        calculate_acr_rate(rate_verification=Fraction(-1, 1), rate_generation=Fraction(10, 1))


def test_metric_helpers_reject_malformed_inputs():
    """Test that calculate_ngd, calculate_acr, and calculate_acr_rate reject floats and non-booleans."""
    # 1. calculate_ngd rejects strings and non-booleans
    with pytest.raises(TypeError, match="Malformed local_green flag"):
        calculate_ngd([{"local_green": "false", "global_red": False}])

    with pytest.raises(TypeError, match="Malformed global_red flag"):
        calculate_ngd([{"local_green": True, "global_red": "true"}])

    with pytest.raises(TypeError, match="Malformed local_green flag"):
        calculate_ngd([{"local_green": 1.0, "global_red": False}])

    # 2. calculate_acr_rate rejects floats (e.g. .1, .3)
    with pytest.raises(TypeError, match="Floats and booleans are rejected"):
        calculate_acr_rate(0.1, 0.3)

    with pytest.raises(TypeError, match="Floats and booleans are rejected"):
        calculate_acr_rate(Fraction(1, 10), 0.3)

    # 3. calculate_acr rejects floats and booleans
    with pytest.raises(TypeError, match="Floats are rejected"):
        calculate_acr(2.5, 10)

    with pytest.raises(TypeError, match="Counts must be integers, not booleans"):
        calculate_acr(True, 10)


def test_proposal_context_binding_tamper_detection(sample_proposal, sample_trace, sample_observer, sample_institution):
    """Test that modifying Proposal.context alters the computed binding hash and fails validation."""
    residual = Residual(defect_mass=Fraction(0, 1), unverified_scope=(), refusal_reasons=())
    terminal = Terminal(
        status=TerminalStatus.AUTHORIZED_UNDER_OBSERVER,
        decider_id="officer_jane_doe",
        is_human_or_delegated_body=True,
        justification="All invoice line items matched purchase order.",
    )
    attestation = create_bound_attestation(
        proposal=sample_proposal,
        trace=sample_trace,
        observer=sample_observer,
        residual=residual,
        terminal=terminal,
        institution=sample_institution,
        replay_receipt="receipt_ok_2026",
        descent_executed=True,
    )
    packet_valid = AuthorityPacket(
        proposal=sample_proposal,
        trace=sample_trace,
        observer=sample_observer,
        residual=residual,
        terminal=terminal,
        attestation=attestation,
        institution=sample_institution,
    )
    valid, _ = evaluate_exactness_fraud_criterion(packet_valid)
    assert valid is True

    # Mutate proposal context
    from dataclasses import replace
    mutated_proposal = replace(sample_proposal, context="Tampered procurement context #9999")
    packet_tampered = replace(packet_valid, proposal=mutated_proposal)

    valid_tampered, reason_tampered = evaluate_exactness_fraud_criterion(packet_tampered)
    assert valid_tampered is False
    assert "Trace custody failure" in reason_tampered or "Attestation binding mismatch" in reason_tampered


def test_scoped_authorization_unverified_scope_and_refusals_rules(sample_proposal, sample_trace, sample_observer, sample_institution):
    """Test explicit rules on scoped authorization for unverified scope and refusal reasons."""
    # 1. Unverified scope without declared authorization in terminal: REJECTED
    residual_unverified = Residual(
        defect_mass=Fraction(1, 10),
        unverified_scope=("tax_audit_pending",),
        refusal_reasons=(),
    )
    terminal_no_scope_waiver = Terminal(
        status=TerminalStatus.AUTHORIZED_UNDER_OBSERVER,
        decider_id="officer_jane_doe",
        is_human_or_delegated_body=True,
        justification="Scoped approval with tolerated defect mass up to 1/2.",
        claims_exactness=False,
        tolerated_defect_mass=Fraction(1, 2),
        tolerated_unverified_scope=(),  # Does not authorize tax_audit_pending!
    )
    attestation_1 = create_bound_attestation(
        proposal=sample_proposal,
        trace=sample_trace,
        observer=sample_observer,
        residual=residual_unverified,
        terminal=terminal_no_scope_waiver,
        institution=sample_institution,
        replay_receipt="receipt_1",
        descent_executed=True,
    )
    packet_1 = AuthorityPacket(
        proposal=sample_proposal,
        trace=sample_trace,
        observer=sample_observer,
        residual=residual_unverified,
        terminal=terminal_no_scope_waiver,
        attestation=attestation_1,
        institution=sample_institution,
    )
    valid_1, reason_1 = evaluate_exactness_fraud_criterion(packet_1)
    assert valid_1 is False
    assert "Unverified scope items ['tax_audit_pending'] not authorized" in reason_1

    # 2. Unverified scope WITH declared authorization in terminal: ACCEPTED
    terminal_with_scope_waiver = replace(
        terminal_no_scope_waiver,
        tolerated_unverified_scope=("tax_audit_pending",),
    )
    attestation_2 = create_bound_attestation(
        proposal=sample_proposal,
        trace=sample_trace,
        observer=sample_observer,
        residual=residual_unverified,
        terminal=terminal_with_scope_waiver,
        institution=sample_institution,
        replay_receipt="receipt_2",
        descent_executed=True,
    )
    packet_2 = AuthorityPacket(
        proposal=sample_proposal,
        trace=sample_trace,
        observer=sample_observer,
        residual=residual_unverified,
        terminal=terminal_with_scope_waiver,
        attestation=attestation_2,
        institution=sample_institution,
    )
    valid_2, reason_2 = evaluate_exactness_fraud_criterion(packet_2)
    assert valid_2 is True
    assert "Structurally consistent but unverified" in reason_2

    # 3. Refusal reasons without declared authorization: REJECTED
    residual_refusal = Residual(
        defect_mass=Fraction(1, 10),
        unverified_scope=(),
        refusal_reasons=("unresolved_boundary_curvature",),
    )
    attestation_3 = create_bound_attestation(
        proposal=sample_proposal,
        trace=sample_trace,
        observer=sample_observer,
        residual=residual_refusal,
        terminal=terminal_no_scope_waiver,
        institution=sample_institution,
        replay_receipt="receipt_3",
        descent_executed=True,
    )
    packet_3 = AuthorityPacket(
        proposal=sample_proposal,
        trace=sample_trace,
        observer=sample_observer,
        residual=residual_refusal,
        terminal=terminal_no_scope_waiver,
        attestation=attestation_3,
        institution=sample_institution,
    )
    valid_3, reason_3 = evaluate_exactness_fraud_criterion(packet_3)
    assert valid_3 is False
    assert "Evaluator refusal reasons ['unresolved_boundary_curvature'] not authorized" in reason_3

    # 4. Refusal reasons WITH declared authorization: ACCEPTED
    terminal_with_refusal_waiver = replace(
        terminal_no_scope_waiver,
        tolerated_refusal_reasons=("unresolved_boundary_curvature",),
    )
    attestation_4 = create_bound_attestation(
        proposal=sample_proposal,
        trace=sample_trace,
        observer=sample_observer,
        residual=residual_refusal,
        terminal=terminal_with_refusal_waiver,
        institution=sample_institution,
        replay_receipt="receipt_4",
        descent_executed=True,
    )
    packet_4 = AuthorityPacket(
        proposal=sample_proposal,
        trace=sample_trace,
        observer=sample_observer,
        residual=residual_refusal,
        terminal=terminal_with_refusal_waiver,
        attestation=attestation_4,
        institution=sample_institution,
    )
    valid_4, reason_4 = evaluate_exactness_fraud_criterion(packet_4)
    assert valid_4 is True
    assert "Structurally consistent but unverified" in reason_4


