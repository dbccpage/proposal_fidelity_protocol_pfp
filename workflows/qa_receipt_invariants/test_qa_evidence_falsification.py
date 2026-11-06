"""Falsification tests for the qa_evidence receipt value objects.

Each test names an INVARIANT, a BREAK that violates it, the WITNESS that
shows the break is caught, and a MUTATION of the source that this test
would detect.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from qa_evidence import (
    ExaminerTestRecord,
    MutationEvidenceRecord,
    MutationRollbackFailure,
    ReceiptStatus,
    StrictAuditSummary,
    StrictVetoStatus,
    SoftwareQaReceiptV1,
    refuse_mutation_rollback,
)


def _audit(
    *,
    status: StrictVetoStatus = StrictVetoStatus.CLEAN,
    ornaments: int = 0,
    rounds: int = 0,
) -> StrictAuditSummary:
    return StrictAuditSummary(
        strict_veto_status=status,
        class_0_mock_ornaments_detected=ornaments,
        silent_skips_detected=0,
        bare_returns_detected=0,
        blanket_exceptions_detected=0,
        ast_boundary_violations=0,
        auto_repair_rounds_used=rounds,
    )


def _examiner(*, examiner_class: int = 1, duration_ms: float = 1.0) -> ExaminerTestRecord:
    return ExaminerTestRecord(
        test_node_id="node-a",
        examiner_class=examiner_class,
        classification_name="Invariant",
        status="PASSED",
        duration_ms=duration_ms,
    )


def _receipt(
    *,
    status: ReceiptStatus = ReceiptStatus.PASSED,
    audit: StrictAuditSummary | None = None,
    tree_dirty: bool = False,
    content_hash: str = "",
) -> SoftwareQaReceiptV1:
    return SoftwareQaReceiptV1(
        receipt_id="receipt-1",
        timestamp="2026-10-15T00:00:00Z",
        commit_sha="abc",
        tree_dirty=tree_dirty,
        target_scopes=("demos/qa_receipt_invariants/qa_evidence",),
        status=status,
        strict_audit=_audit() if audit is None else audit,
        examiner_tests=(_examiner(),),
        mutations=(),
        red_green_transitions=(),
        tree_state_sha256="tree",
        receipt_content_sha256=content_hash,
    )


# INVARIANT: examiner_class is an int in 1..5; Class 0 is forbidden.
# BREAK: examiner_class=0.
# WITNESS: ValueError names examiner_class and the record is not constructed.
# MUTATION: change `self.examiner_class not in (1, 2, 3, 4, 5)` to `self.examiner_class not in (0, 1, 2, 3, 4, 5)`.
def test_examiner_class_zero_is_refused() -> None:
    """Class 2. Class 0 is the named lower boundary, not a legal class."""

    with pytest.raises(ValueError, match="examiner_class must be in 1..5"):
        _examiner(examiner_class=0)


# INVARIANT: duration_ms is a non-negative number; zero is the closed lower bound.
# BREAK: duration_ms=-1.
# WITNESS: ValueError names duration_ms.
# MUTATION: change `self.duration_ms < 0` to `self.duration_ms < -1`.
def test_negative_duration_is_refused() -> None:
    """Class 2. One unit below the admitted duration bound is rejected."""

    with pytest.raises(ValueError, match="duration_ms must be a non-negative float"):
        _examiner(duration_ms=-1)


# INVARIANT: count fields are exact ints; bool is not an int here.
# BREAK: class_0_mock_ornaments_detected=True.
# WITNESS: ValueError names class_0_mock_ornaments_detected.
# MUTATION: change `type(self.class_0_mock_ornaments_detected) is not int` to `not isinstance(self.class_0_mock_ornaments_detected, int)`.
def test_bool_count_is_not_a_non_negative_int() -> None:
    """Class 2. bool is an int subclass and must still be refused."""

    with pytest.raises(ValueError, match="class_0_mock_ornaments_detected must be a non-negative int"):
        _audit(ornaments=True)  # type: ignore[arg-type]


# INVARIANT: auto_repair_rounds_used is an int and cannot exceed 3.
# BREAK: auto_repair_rounds_used=4.
# WITNESS: ValueError says the value cannot exceed 3.
# MUTATION: change `self.auto_repair_rounds_used > 3` to `self.auto_repair_rounds_used > 4`.
def test_auto_repair_round_four_is_refused() -> None:
    """Class 2. Four is the first integer past the named repair cap."""

    with pytest.raises(ValueError, match="cannot exceed 3"):
        _audit(rounds=4)


# INVARIANT: auto_repair_rounds_used accepts the closed bound 3.
# BREAK: treating 3 as already over the cap.
# WITNESS: a constructed summary stores auto_repair_rounds_used == 3.
# MUTATION: change `self.auto_repair_rounds_used > 3` to `self.auto_repair_rounds_used >= 3`.
def test_auto_repair_round_three_is_admitted() -> None:
    """Class 3. The cap is exclusive of the next integer, not of 3 itself."""

    admitted = _audit(rounds=3)

    assert admitted.auto_repair_rounds_used == 3


# INVARIANT: a rollback failure message is a non-empty str.
# BREAK: message="".
# WITNESS: ValueError, and no MutationRollbackFailure exists.
# MUTATION: change `not self.message` to `False` in MutationRollbackFailure.__post_init__.
def test_empty_rollback_message_is_refused() -> None:
    """Class 2. The empty message is the closed failure of the failure record."""

    with pytest.raises(ValueError, match="message must be a non-empty string"):
        MutationRollbackFailure("")


# INVARIANT: refuse_mutation_rollback returns Err of MutationRollbackFailure, not a str.
# BREAK: a non-empty refusal compared with the raw message string, or an Ok wrapper.
# WITNESS: is_err is True, unwrap_err() is MutationRollbackFailure, and it is not equal to str.
# MUTATION: change `return Err(MutationRollbackFailure(message))` to `return Err(message)`.
def test_refuse_rollback_is_err_of_the_failure_type() -> None:
    """Class 2. The refusal channel is a typed Err, not the message text."""

    refused = refuse_mutation_rollback("digest mismatch")

    assert refused.is_ok is False
    assert refused.is_err is True
    failure = refused.unwrap_err()
    assert type(failure) is MutationRollbackFailure
    assert failure == MutationRollbackFailure("digest mismatch")
    assert failure != "digest mismatch"
    assert failure != MutationEvidenceRecord(
        mutant_id="digest mismatch",
        intent="",
        target="t",
        anchor="a",
        applied="",
        expectation="",
        status="",
    )


# INVARIANT: status PASSED is legal only when strict_veto_status is CLEAN.
# BREAK: ReceiptStatus.PASSED together with StrictVetoStatus.VETOED.
# WITNESS: ValueError names PASSED and the receipt is not sealed.
# MUTATION: delete the conjunct `self.status == ReceiptStatus.PASSED` by changing it to `False`.
def test_passed_receipt_is_refused_when_strict_audit_is_not_clean() -> None:
    """Class 2. A vetoed audit cannot be sealed as PASSED."""

    with pytest.raises(ValueError, match="status cannot be PASSED when strict_veto_status is not CLEAN"):
        _receipt(status=ReceiptStatus.PASSED, audit=_audit(status=StrictVetoStatus.VETOED))


# INVARIANT: tree_dirty is an exact bool, not an int coerced to bool.
# BREAK: tree_dirty=1.
# WITNESS: TypeError names tree_dirty.
# MUTATION: change `type(self.tree_dirty) is not bool` to `not isinstance(self.tree_dirty, int)`.
def test_tree_dirty_rejects_int_coercion() -> None:
    """Class 2. 1 is not an admitted stand-in for True."""

    with pytest.raises(TypeError, match="tree_dirty must be an exact bool"):
        _receipt(tree_dirty=1)  # type: ignore[arg-type]


# INVARIANT: StrictAuditSummary equality is exact-type and payload-based.
# BREAK: the same counts carried by str, or by a subclass with the same fields.
# WITNESS: equal to another StrictAuditSummary; not equal to the string or the subclass.
# MUTATION: change `if type(self) is not type(other): return False` to `if False: return False` in StrictAuditSummary.__eq__.
def test_audit_summary_equality_rejects_other_types() -> None:
    """Class 1. Value-object equality does not coerce across types."""

    class TwinAudit(StrictAuditSummary):
        """Different class, same field payload."""

    summary = _audit(rounds=1)
    same = _audit(rounds=1)
    twin = TwinAudit(
        strict_veto_status=StrictVetoStatus.CLEAN,
        class_0_mock_ornaments_detected=0,
        silent_skips_detected=0,
        bare_returns_detected=0,
        blanket_exceptions_detected=0,
        ast_boundary_violations=0,
        auto_repair_rounds_used=1,
    )

    assert summary == same
    assert hash(summary) == hash(same)
    assert summary != "CLEAN"
    assert summary != twin
    assert twin != summary


# INVARIANT: an empty declared content hash does not verify.
# BREAK: receipt_content_sha256="".
# WITNESS: verify_integrity returns (False, "receipt_content_sha256 is empty").
# MUTATION: change `if not self.receipt_content_sha256:` to `if False:`.
def test_empty_content_hash_fails_integrity() -> None:
    """Class 2. The empty digest is a failed seal, not an implicit recompute."""

    receipt = _receipt(content_hash="")

    assert receipt.verify_integrity() == (False, "receipt_content_sha256 is empty")


# INVARIANT: only killed, survived, and equivalent statuses count toward the denominator.
# BREAK: status="" (empty) counted, or status="equivalent" dropped.
# WITNESS: equivalent counts; the empty status does not.
# MUTATION: change `{"killed", "survived", "equivalent"}` to `{"killed", "survived"}`.
def test_empty_mutation_status_does_not_count_toward_denominator() -> None:
    """Class 3. The empty status is outside the named denominator set."""

    counted = MutationEvidenceRecord(
        mutant_id="m-1",
        intent="shift the cap",
        target="qa_receipt.py",
        anchor="auto_repair",
        applied="> 4",
        expectation="killed",
        status="equivalent",
    )
    empty = MutationEvidenceRecord(
        mutant_id="m-2",
        intent="shift the cap",
        target="qa_receipt.py",
        anchor="auto_repair",
        applied="> 4",
        expectation="killed",
        status="",
    )

    assert counted.counts_toward_denominator is True
    assert empty.counts_toward_denominator is False
    assert counted != empty


# INVARIANT: qa_evidence domain modules do not import outer layers or forbidden frameworks.
# BREAK: an import whose module path contains use_cases, infrastructure, controllers, frontend, pydantic, pytest, requests, click, or sqlite3.
# WITNESS: ast walk of every package module yields no such import.
# MUTATION: add `import pytest` to qa_receipt.py.
def test_qa_evidence_domain_imports_no_outer_layer() -> None:
    """Class 1. The domain package's AST has no outward dependency."""

    forbidden = {
        "use_cases",
        "infrastructure",
        "controllers",
        "frontend",
        "pydantic",
        "pytest",
        "requests",
        "click",
        "sqlite3",
    }
    package = Path(SoftwareQaReceiptV1.__module__.replace(".", "/")).parent
    # SoftwareQaReceiptV1 lives in qa_receipt.py; the package is its parent directory.
    root = Path(__file__).resolve().parent / "qa_evidence"
    assert root.is_dir()
    violations: list[str] = []
    for source in sorted(root.glob("*.py")):
        tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.append(node.module)
            for name in names:
                bad = set(name.split(".")) & forbidden
                if bad:
                    violations.append(f"{source.name}: {name} -> {sorted(bad)}")
    assert violations == []
    assert package.name == "qa_evidence"
