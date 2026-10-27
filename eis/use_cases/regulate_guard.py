"""Scoped learned-detector suspension from an independent benign check.

The underlying authenticated admission remains unchanged. This adapter narrows
an existing guard state's effective authority for a bounded session only.
"""

from dataclasses import dataclass
from hashlib import sha256
from typing import Protocol

from operads.domain.operad.treg import (
    CheckedFalsePositive, OperadTregSupervisor,
)
from eis.domain.guard_activation import DetectorHitRefV1
from .guard_activation import GuardStatePort, subject_digest


@dataclass(frozen=True)
class BenignCheckResult:
    subject_sha256: str
    checker_id: str
    evidence_sha256: str
    verdict: str  # BENIGN, HARMFUL or UNAVAILABLE


class BenignChecker(Protocol):
    def check_benign(self, content: str) -> BenignCheckResult: ...


class RegulatedGuardState:
    """Only composition-selected optional learned guards can be suspended."""

    def __init__(self, underlying: GuardStatePort, *, scope: str,
                 optional_learned_ids: frozenset[str], protected_ids: frozenset[str],
                 supervisor: OperadTregSupervisor | None = None):
        if not scope or optional_learned_ids & protected_ids:
            raise ValueError('PROTECTED_GATE')
        self.underlying = underlying
        self.scope = scope
        self.optional_learned_ids = optional_learned_ids
        self.protected_ids = protected_ids
        self.supervisor = supervisor or OperadTregSupervisor()

    def is_externally_admitted(self, spec_id, subject_scope):
        return self.underlying.is_externally_admitted(spec_id, subject_scope)

    def is_suspended(self, spec_id, subject_scope):
        prior = self.underlying.is_suspended(spec_id, subject_scope)
        return prior or (subject_scope == self.scope and spec_id in self.optional_learned_ids
            and self.supervisor.is_downgraded(spec_id))

    def observe(self, hit: DetectorHitRefV1, content: str, *, checker: BenignChecker):
        """Execute the independent checker; missing checks never synthesize a regulator."""
        spec_id = hit.spec_id
        if spec_id in self.protected_ids or spec_id not in self.optional_learned_ids:
            raise ValueError('PROTECTED_GATE')
        if hit.subject_id != subject_digest(content):
            raise ValueError('SUBJECT_MISMATCH')
        if not self.underlying.is_externally_admitted(spec_id, self.scope):
            raise ValueError('NOT_EXTERNALLY_ADMITTED')
        try:
            checked = checker.check_benign(content)
        except Exception:
            # Operational absence does not establish benignity or a false positive.
            return None
        if type(checked) is not BenignCheckResult:
            raise ValueError('CHECKED_EVIDENCE_REQUIRED')
        if checked.subject_sha256 != sha256(content.encode('utf-8')).hexdigest():
            raise ValueError('SUBJECT_MISMATCH')
        if checked.verdict == 'UNAVAILABLE':
            return None
        if checked.verdict not in ('BENIGN', 'HARMFUL'):
            raise ValueError('CHECK_VERDICT_INVALID')
        if checked.checker_id in (spec_id, hit.failure_code) or 'sha256:' + checked.evidence_sha256 == hit.hit_id:
            raise ValueError('INDEPENDENT_CHECKER_REQUIRED')
        false_positive = (CheckedFalsePositive(spec_id, checked.subject_sha256,
            checked.checker_id, checked.evidence_sha256) if checked.verdict == 'BENIGN' else None)
        return self.supervisor.record_operation_step(spec_id, True,
            checked.verdict == 'HARMFUL', false_positive=false_positive, learned_detector=True)
