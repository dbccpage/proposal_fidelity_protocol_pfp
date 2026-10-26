"""Externally signed custody, exact bytes, and restart replay witnesses."""

import hashlib
import hmac
from dataclasses import replace

import pytest

from omega_engine_operating_system.adapters.prompt_civ.cas import ContentAddressedStorageV1
from omega_engine_operating_system.adapters.prompt_civ.custody import (
    PromptCustodyLedgerV1,
    PromptReviewReceiptV1,
)
from omega_engine_operating_system.adapters.prompt_civ.forge import (
    MutationOperatorCandidateV1,
)
from omega_engine_operating_system.adapters.prompt_civ.operator_custody import (
    MutationOperatorAdmissionV1,
    MutationOperatorRegistryV1,
)
from omega_engine_operating_system.adapters.prompt_civ.record import (
    CustodyTier,
    PromptGenomeV1,
    ProtectedSpanV1,
)


class TestHostVerifier:
    __test__ = False
    key = b"test-only-explicit-external-review-key"

    def sign(self, receipt):
        return replace(receipt, external_receipt=hmac.new(self.key, receipt.signed_bytes(), hashlib.sha256).hexdigest())

    def verify(self, receipt):
        return hmac.compare_digest(receipt.external_receipt, self.sign(receipt).external_receipt)


def decision(verifier, genome, outcome, decision_id, actor="human-reviewer"):
    return verifier.sign(PromptReviewReceiptV1(
        decision_id, genome.prompt_id, actor, outcome, ("math",), "",
    ))


@pytest.mark.parametrize("invalid_scope", ["mathematics", ["math"], ("",), (None,), (1,)])
def test_signed_custody_types_refuse_ambiguous_scope_containers(invalid_scope):
    with pytest.raises(ValueError, match="REVIEW_SCOPE_INVALID"):
        PromptReviewReceiptV1("decision", "genome", "reviewer", CustodyTier.ADMITTED, invalid_scope, "")
    with pytest.raises(ValueError, match="OPERATOR_SCOPE_INVALID"):
        MutationOperatorAdmissionV1("decision", "operator", "digest", "reviewer", invalid_scope, "")


def test_admission_matches_a_complete_scope_label_not_a_substring(tmp_path):
    verifier = TestHostVerifier()
    genome = PromptGenomeV1([{"sha256": "source"}], {})
    ledger = PromptCustodyLedgerV1(tmp_path / "scoped.sqlite", verifier)
    ledger.submit_candidate(genome, "producer")
    for outcome in (CustodyTier.REVIEWED, CustodyTier.ADMITTED):
        receipt = PromptReviewReceiptV1(outcome.value, genome.prompt_id, "reviewer", outcome, ("mathematics",), "")
        ledger.apply(genome, verifier.sign(receipt))
    assert ledger.approved(genome, "mathematics").scope == ("mathematics",)
    with pytest.raises(PermissionError, match="REFUSE_SCOPE_ESCALATION"):
        ledger.approved(genome, "math")
    ledger.close()


def test_review_admission_restart_and_revocation_are_append_only(tmp_path):
    verifier = TestHostVerifier()
    genome = PromptGenomeV1([{"sha256": "source"}], {"domain": "math"})
    path = tmp_path / "custody.sqlite"
    ledger = PromptCustodyLedgerV1(path, verifier)
    assert ledger.view(genome).current_custody is CustodyTier.WILD
    ledger.submit_candidate(genome, "mutation-operator")
    assert ledger.view(genome).current_custody is CustodyTier.CANDIDATE
    assert ledger.view(genome, 0).current_custody is CustodyTier.WILD
    reviewed = ledger.apply(genome, decision(verifier, genome, CustodyTier.REVIEWED, "review"))
    assert reviewed.current_custody is CustodyTier.REVIEWED
    admitted = ledger.apply(genome, decision(verifier, genome, CustodyTier.ADMITTED, "admit"))
    assert ledger.approved(genome, "math").prompt_id == genome.prompt_id
    with pytest.raises(PermissionError, match="REFUSE_SCOPE_ESCALATION"):
        ledger.approved(genome, "medicine")
    ledger.close()
    ledger = PromptCustodyLedgerV1(path, verifier)
    assert ledger.genome(genome.prompt_id) == genome
    assert ledger.view(genome) == admitted
    ledger.apply(genome, decision(verifier, genome, CustodyTier.REVOKED, "revoke"))
    assert ledger.view(genome, reviewed.ledger_revision) == reviewed
    with pytest.raises(PermissionError, match="PROMPT_NOT_ADMITTED"):
        ledger.approved(genome, "math")
    assert ledger.connection.execute("SELECT COUNT(*) FROM prompt_decisions").fetchone()[0] == 4
    ledger.close()


def test_self_admission_forgery_and_skipped_review_are_refused(tmp_path):
    verifier = TestHostVerifier()
    genome = PromptGenomeV1([{"sha256": "source"}], {})
    ledger = PromptCustodyLedgerV1(tmp_path / "custody.sqlite", verifier)
    ledger.submit_candidate(genome, "operator")
    with pytest.raises(PermissionError, match="SELF_ADMISSION_REFUSED"):
        ledger.apply(genome, decision(verifier, genome, CustodyTier.REVIEWED, "self", "operator"))
    forged = replace(decision(verifier, genome, CustodyTier.REVIEWED, "forged"), external_receipt="fake")
    with pytest.raises(PermissionError, match="EXTERNAL_REVIEW_NOT_AUTHENTICATED"):
        ledger.apply(genome, forged)
    with pytest.raises(ValueError, match="PROMPT_CUSTODY_TRANSITION_REFUSED"):
        ledger.apply(genome, decision(verifier, genome, CustodyTier.ADMITTED, "skip"))
    assert ledger.view(genome).current_custody is CustodyTier.CANDIDATE
    assert ledger.connection.execute("SELECT COUNT(*) FROM prompt_decisions").fetchone()[0] == 1
    ledger.close()


def test_changed_bytes_cannot_inherit_review_and_duplicate_decisions_are_idempotent(tmp_path):
    verifier = TestHostVerifier()
    genome = PromptGenomeV1([{"sha256": "source"}], {})
    changed = PromptGenomeV1([{"sha256": "changed"}], {})
    ledger = PromptCustodyLedgerV1(tmp_path / "custody.sqlite", verifier)
    ledger.submit_candidate(genome, "operator")
    receipt = decision(verifier, genome, CustodyTier.REVIEWED, "review")
    view = ledger.apply(genome, receipt)
    assert ledger.apply(genome, receipt) == view
    assert ledger.view(changed).current_custody is CustodyTier.WILD
    with pytest.raises(ValueError, match="REVIEW_SUBJECT_MISMATCH"):
        ledger.apply(changed, receipt)
    conflicting = decision(verifier, genome, CustodyTier.ADMITTED, "review")
    with pytest.raises(ValueError, match="REVIEW_DECISION_IDENTITY_CONFLICT"):
        ledger.apply(genome, conflicting)
    assert ledger.connection.execute("SELECT COUNT(*) FROM prompt_decisions").fetchone()[0] == 2
    ledger.close()


def test_operator_independent_admission_and_offspring_keep_parent_bytes(tmp_path):
    verifier = TestHostVerifier()
    ledger = PromptCustodyLedgerV1(tmp_path / "prompts.sqlite", verifier)
    cas = ContentAddressedStorageV1(tmp_path / "cas")
    registry = MutationOperatorRegistryV1(tmp_path / "operators.sqlite", verifier, ledger, cas)
    original = b"core one"
    source_digest = cas.store(original)
    parent = PromptGenomeV1(
        [{"packet_id": "parent", "sha256": source_digest}], {"domain": "math"},
        protected_spans=(ProtectedSpanV1("core", 0, 4),),
    )
    ledger.submit_candidate(parent, "parent-author")
    operator = MutationOperatorCandidateV1("op-1", "task")
    digest = registry.submit(operator, "operator-author", b"replace declared mutable task span")
    with pytest.raises(PermissionError, match="OPERATOR_NOT_ADMITTED"):
        registry.realize_offspring("op-1", parent, original, scope="math", edit_start=5, edit_end=8, replacement=b"two")
    admission = MutationOperatorAdmissionV1("admit-op", "op-1", digest, "operator-author", ("math",), "")
    with pytest.raises(PermissionError, match="SELF_ADMISSION_REFUSED"):
        registry.admit(verifier.sign(admission))
    registry.admit(verifier.sign(replace(admission, actor_id="human-reviewer")))
    with pytest.raises(PermissionError, match="REFUSE_SCOPE_ESCALATION"):
        registry.realize_offspring("op-1", parent, original, scope="ma", edit_start=5, edit_end=8, replacement=b"two")
    child = registry.realize_offspring("op-1", parent, original, scope="math", edit_start=5, edit_end=8, replacement=b"two")
    assert child.birth_custody is CustodyTier.WILD
    assert ledger.view(child).current_custody is CustodyTier.CANDIDATE
    assert child.parents[0]["prompt_id"] == parent.prompt_id
    assert cas.retrieve(child.source_packet_refs[0]["sha256"]) == b"core two"
    assert cas.retrieve(source_digest) == original
    assert ledger.genome(parent.prompt_id) == parent
    for actor in ("operator-author", "op-1"):
        with pytest.raises(PermissionError, match="SELF_ADMISSION_REFUSED"):
            ledger.apply(child, decision(verifier, child, CustodyTier.REVIEWED, actor, actor))
    with pytest.raises(ValueError, match="PARENT_BYTES_MISMATCH"):
        registry.realize_offspring("op-1", parent, b"core bad", scope="math", edit_start=5, edit_end=8, replacement=b"two")
    registry.close()
    ledger.close()
