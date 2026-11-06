"""QA evidence value objects: a sealed software QA receipt and its parts.

AuthorityEffect: None.
"""

from __future__ import annotations

from qa_evidence.qa_receipt import (
    ExaminerTestRecord,
    MutationEvidenceRecord,
    MutationJournalError,
    MutationJournalFailure,
    MutationNotKilledFailure,
    MutationNotKilledVeto,
    MutationRollbackError,
    MutationRollbackFailure,
    ReceiptStatus,
    RedGreenTransition,
    SoftwareQaReceiptV1,
    StrictAuditSummary,
    StrictVetoStatus,
    refuse_mutation_journal,
    refuse_mutation_not_killed,
    refuse_mutation_rollback,
)

__all__ = [
    "ExaminerTestRecord",
    "MutationEvidenceRecord",
    "MutationJournalError",
    "MutationJournalFailure",
    "MutationNotKilledFailure",
    "MutationNotKilledVeto",
    "MutationRollbackError",
    "MutationRollbackFailure",
    "ReceiptStatus",
    "RedGreenTransition",
    "SoftwareQaReceiptV1",
    "StrictAuditSummary",
    "StrictVetoStatus",
    "refuse_mutation_journal",
    "refuse_mutation_not_killed",
    "refuse_mutation_rollback",
]
