"""PFP envelope: protected contract, host oracle context and whole-run budget.

* ``ProtectedContract`` fences byte spans of the user's task (for example a
  frozen public signature block). Edits are applied through PCIV's
  ``PromptMutationEngineV1``, which refuses any edit or zero-width insertion
  inside a fence; a candidate artifact must reproduce every fenced span
  byte-for-byte.
* ``HostOracleContext`` separates predicates the host checked from obligations
  nobody checked. ``final_output_certified`` is True only when every listed
  predicate passed and no obligation is open; it is a statement about these
  predicates, not about arbitrary semantics of the output.
* ``WholeRunBudget`` binds every stage of one run (calls, repairs, sub-calls)
  to one ``RunLedger`` row with a hard microUSD cap, and tallies tokens and
  wall time. Failures and holds stay in the record.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from pathlib import Path
import time

from . import REPO_ROOT  # noqa: F401  (sets sys.path for the imports below)
from budget_ledger import MAX_RUN_MICROUSD, BudgetError, RunLedger
from pciv.domain.models import ProtectedSpanV1
from pciv.use_cases.forge import PromptMutationEngineV1


def sha256_hex(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class ProtectedContract:
    """User task bytes plus named fences that no proposal may change."""
    task_bytes: bytes
    fences: tuple[ProtectedSpanV1, ...]

    @classmethod
    def fence_markers(cls, task_text: str, begin: str, end: str, name: str = 'frozen') -> 'ProtectedContract':
        """Fence the bytes from ``begin`` through ``end`` (inclusive) in ``task_text``."""
        data = task_text.encode('utf-8')
        start = data.find(begin.encode('utf-8'))
        stop = data.find(end.encode('utf-8'), start + 1)
        if start < 0 or stop < 0 or data.count(begin.encode('utf-8')) != 1:
            raise ValueError('FENCE_MARKERS_NOT_UNIQUE')
        stop += len(end.encode('utf-8'))
        return cls(data, (ProtectedSpanV1(name, start, stop),))

    def fenced(self, span: ProtectedSpanV1) -> bytes:
        return self.task_bytes[span.start_byte:span.end_byte]

    def apply_edit(self, start: int, end: int, replacement: bytes) -> bytes:
        """Edit the task outside the fences; raises PermissionError inside one."""
        return PromptMutationEngineV1().apply_mutation(
            original_bytes=self.task_bytes, protected_spans=self.fences,
            edit_start_byte=start, edit_end_byte=end, replacement_bytes=replacement)

    def violations(self, candidate: str | bytes) -> list[str]:
        """Names of fences whose exact bytes do not occur once in ``candidate``."""
        data = candidate.encode('utf-8') if isinstance(candidate, str) else candidate
        return [s.name for s in self.fences if data.count(self.fenced(s)) != 1]


@dataclass
class HostOracleContext:
    """Host-checked predicates versus open (uncertified) semantic obligations."""
    certified_predicates: dict[str, bool] = field(default_factory=dict)
    uncertified_obligations: tuple[str, ...] = ()
    evidence: dict[str, str] = field(default_factory=dict)

    def record(self, name: str, passed: bool, evidence: str = '') -> bool:
        if type(passed) is not bool:
            raise TypeError('host predicate result must be an exact bool')
        if name in self.certified_predicates:
            raise ValueError(f'predicate {name} already recorded; host facts are write-once')
        self.certified_predicates[name] = passed
        self.evidence[name] = sha256_hex(evidence)
        return passed

    @property
    def failed(self) -> list[str]:
        return [k for k, v in self.certified_predicates.items() if not v]

    @property
    def final_output_certified(self) -> bool:
        return bool(self.certified_predicates) and not self.failed and not self.uncertified_obligations

    def to_dict(self) -> dict:
        return {'certified_predicates': dict(self.certified_predicates),
                'uncertified_obligations': list(self.uncertified_obligations),
                'final_output_certified': self.final_output_certified,
                'evidence_sha256': dict(self.evidence)}


class WholeRunBudget:
    """One run, one ledger row, one cap across every stage.

    ``charge`` reserves the stage's upper quote before dispatch and settles the
    actual charge afterwards. ``hold`` records an ambiguous delivery: the quote
    stays held and the run is blocked, so later stages are refused.
    """

    def __init__(self, run_id: str, task_digest: str, cap_microusd: int = MAX_RUN_MICROUSD,
                 ledger_path: Path | str = ':memory:'):
        self.ledger = RunLedger(Path(ledger_path))
        self.ledger.start(run_id, task_digest, cap_microusd)
        self.run_id = run_id
        self.input_tokens = 0
        self.output_tokens = 0
        self.calls = 0
        self.provider_wall_ms = 0
        self.refusals: list[str] = []
        self._started = time.perf_counter()

    def can_afford(self, quote: int) -> bool:
        s = self.ledger.summary(self.run_id)
        return not s['blocked'] and quote <= s['available_microusd']

    def reserve(self, stage: str, request_digest: str, quote: int) -> str | None:
        """Reserve the upper quote before dispatch; None (reason recorded) when refused."""
        call_id = f'{self.run_id}:call:{self.calls + len(self.refusals) + 1}'
        try:
            self.ledger.reserve(self.run_id, call_id, request_digest, quote)
        except BudgetError as exc:
            self.refusals.append(f'{stage}: {exc}')
            return None
        self.calls += 1
        return call_id

    def settle(self, stage: str, call_id: str, actual: int, input_tokens: int, output_tokens: int,
               provider_wall_ms: int = 0, response_digest: str | None = None) -> bool:
        """Settle a known charge. An overrun is recorded, blocks the run and returns False."""
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.provider_wall_ms += provider_wall_ms
        try:
            self.ledger.settle(call_id, actual, response_digest or sha256_hex(f'{call_id}:{actual}'))
        except BudgetError as exc:
            self.refusals.append(f'{stage}: {exc}')
            return False
        return True

    def hold_call(self, stage: str, call_id: str, reason: str = 'ambiguous delivery') -> None:
        """Unknown liability: keep the whole quote held and block the run."""
        self.ledger.mark_uncertain(call_id)
        self.refusals.append(f'{stage}: {reason}; quote held, run blocked')

    def block(self, stage: str, reason: str) -> None:
        self.ledger.block(self.run_id)
        self.refusals.append(f'{stage}: {reason}; run blocked')

    def charge(self, stage: str, request_digest: str, quote: int, actual: int,
               input_tokens: int, output_tokens: int, provider_wall_ms: int = 0) -> bool:
        """Reserve then settle one stage. Returns False (and records why) on refusal."""
        call_id = self.reserve(stage, request_digest, quote)
        return call_id is not None and self.settle(stage, call_id, actual, input_tokens, output_tokens,
                                                    provider_wall_ms)

    def hold(self, stage: str, request_digest: str, quote: int) -> None:
        call_id = self.reserve(stage, request_digest, quote)
        if call_id is not None:
            self.hold_call(stage, call_id)

    def summary(self) -> dict:
        s = self.ledger.summary(self.run_id)
        s.update(input_tokens=self.input_tokens, output_tokens=self.output_tokens,
                 total_tokens=self.input_tokens + self.output_tokens, calls=self.calls,
                 provider_wall_ms=self.provider_wall_ms,
                 host_wall_ms=int((time.perf_counter() - self._started) * 1000), refusals=list(self.refusals))
        return s

    def close(self) -> None:
        self.ledger.close()
