"""Shared runtime for workflow families WF6-WF49.

Every family is a ``WorkflowFamily`` subclass with a ``WorkflowFamilySpecV1``.
``execute`` runs the same loop for all of them:

1. ``validate`` the public task (``bundle['task']``).
2. ``run`` asks the proposer for candidates through a ``Session``. Every ask is
   reserved and settled against one ``WholeRunBudget`` before the reply is
   read, and the prompt is refused if it contains any sealed literal.
3. The family's host check records exact predicates in a ``HostOracleContext``
   and returns a verdict.

Only the host check can certify. Proposers, detectors and adapters carry
``authority_effect = 'None'``; a reply that claims authority is refused by the
same code path as any other failed predicate.

Verdicts:

* ``HOST_CERTIFIED``: every recorded host predicate passed.
* ``TYPED_REFUSAL``: the workflow refused with a code and the host checked the
  obstruction witness behind it. This is a correct outcome, not a failure.
* ``REFUSED``: a host predicate failed, the budget refused a stage, or the
  candidate was malformed.

A bundle is ``{'task': public dict, 'sealed': host-only dict, 'replies': list}``.
``replies`` are fixture candidates for offline runs; a live or local open-weight
run passes a ``proposer`` instead. Nothing in ``sealed`` may reach a prompt.
"""
from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, ClassVar, Protocol

from ..fidelity import HostOracleContext, WholeRunBudget, sha256_hex

AUTHORITY_NONE = 'None'
CERTIFIED = 'HOST_CERTIFIED'
TYPED_REFUSAL = 'TYPED_REFUSAL'
REFUSED = 'REFUSED'
VERDICTS = frozenset({CERTIFIED, TYPED_REFUSAL, REFUSED})
POSITIVE = frozenset({CERTIFIED, TYPED_REFUSAL})


def canonical(obj: Any) -> bytes:
    """Canonical JSON bytes: sorted keys, no whitespace, exact ints, Fractions as 'p/q'."""
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                      default=_json_default).encode('utf-8')


def _json_default(value: Any) -> Any:
    if isinstance(value, Fraction):
        return f'{value.numerator}/{value.denominator}'
    if isinstance(value, (set, frozenset)):
        return sorted(value, key=repr)
    if isinstance(value, tuple):
        return list(value)
    raise TypeError(f'not canonical JSON: {type(value).__name__}')


def digest(obj: Any) -> str:
    return sha256_hex(canonical(obj))


@dataclass(frozen=True)
class WorkflowFamilySpecV1:
    """Registry metadata. Mirrors the workflow node in ``dag/reviews/workflows_audit.json``."""
    wf_id: str
    name: str
    layer: int
    depends_on: tuple[str, ...]
    merge_into: str | None
    host_check_id: str
    folder: str
    authority_effect: str = AUTHORITY_NONE

    def __post_init__(self):
        if self.authority_effect != AUTHORITY_NONE:
            raise ValueError('AUTHORITY_ESCALATION: a workflow family never holds authority')
        if not self.wf_id.startswith('WF') or not self.wf_id[2:].isdigit():
            raise ValueError(f'bad wf_id {self.wf_id!r}')
        if type(self.layer) is not int or not 0 <= self.layer <= 9:
            raise ValueError('layer must be an int in 0..9')
        if not self.folder.startswith('workflows/wf'):
            raise ValueError('folder must be under workflows/')

    @property
    def number(self) -> int:
        return int(self.wf_id[2:])


@dataclass(frozen=True)
class Usage:
    """Declared cost of one proposal. Fixture and local replies cost nothing."""
    quote_microusd: int = 0
    actual_microusd: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    wall_ms: int = 0


@dataclass(frozen=True)
class Proposal:
    content: Any
    usage: Usage = Usage()
    source: str = 'fixture'


@dataclass(frozen=True)
class ProposalRequest:
    wf_id: str
    stage: str
    prompt: str
    context: Mapping[str, Any] = field(default_factory=dict)


class Proposer(Protocol):
    def propose(self, request: ProposalRequest) -> Proposal | None: ...


class FixtureProposer:
    """Replays fixture replies in order; returns None when they run out.

    Its upper quote is the largest quote among its replies, so a priced fixture
    is refused by the budget before anything is read.
    """

    def __init__(self, replies: Iterable[Any]):
        self._replies = [r if isinstance(r, Proposal) else Proposal(r) for r in replies]
        self._next = 0
        self.quote_microusd = max((r.usage.quote_microusd for r in self._replies), default=0)

    def propose(self, request: ProposalRequest) -> Proposal | None:  # noqa: ARG002
        if self._next >= len(self._replies):
            return None
        reply = self._replies[self._next]
        self._next += 1
        return reply


class CallableProposer:
    """Adapter for a live or local open-weight model: ``fn(prompt) -> (content, Usage)``.

    ``quote_microusd`` is the honest upper cost of one call. The session reserves
    it before ``fn`` runs, so a call the budget cannot cover is never dispatched.
    The adapter is how ``OpenWeightMechanismRunnerV1`` or a provider client is
    plugged in. No adapter in this package makes a network call.
    """

    def __init__(self, fn: Callable[[str], tuple[Any, Usage]], quote_microusd: int, source: str = 'local'):
        if type(quote_microusd) is not int or quote_microusd < 0:
            raise ValueError('quote_microusd must be a nonnegative int')
        self.fn = fn
        self.quote_microusd = quote_microusd
        self.source = source

    def propose(self, request: ProposalRequest) -> Proposal | None:
        content, usage = self.fn(request.prompt)
        return Proposal(content, usage, self.source)


class SealedLeakError(RuntimeError):
    """A prompt contained a sealed literal; the run must not dispatch."""


ANSWER_KEYS = frozenset({'answer', 'answers', 'expected', 'expected_answer', 'solution', 'key', 'answer_key'})


def sealed_literals(sealed: Any) -> tuple[set[str], set[str]]:
    """(substrings, whole tokens) that must not occur in a prompt.

    Any sealed scalar of four or more characters is a substring leak. A scalar
    under an answer-like key is a leak at any length, matched as a whole token
    so that a short answer such as ``42`` is still caught.
    """
    substrings: set[str] = set()
    tokens: set[str] = set()

    def walk(v: Any, answer: bool) -> None:
        if isinstance(v, Mapping):
            for k, x in v.items():
                walk(x, answer or str(k).lower() in ANSWER_KEYS)
        elif isinstance(v, (list, tuple, set, frozenset)):
            for x in v:
                walk(x, answer)
        elif isinstance(v, bool) or v is None:
            return
        else:
            s = canonical(v).decode('utf-8').strip('"')
            if answer and s:
                tokens.add(s)
            if len(s) >= 4:
                substrings.add(s)
    walk(sealed, False)
    return substrings, tokens


def _leaks(prompt: str, substrings: set[str], tokens: set[str]) -> bool:
    if any(s in prompt for s in substrings):
        return True
    words = set(re.findall(r'[^\s,:;\[\]{}()"\']+', prompt))
    return bool(tokens & words)


def prompt_leaks(prompt: str, sealed: Any) -> bool:
    """True when ``prompt`` would be refused by the session's sealed-leak guard."""
    return _leaks(prompt, *sealed_literals(sealed))


class Session:
    """One run: proposer, budget, transcript and the sealed-leak guard."""

    def __init__(self, spec: WorkflowFamilySpecV1, task: Mapping[str, Any], sealed: Mapping[str, Any],
                 budget: WholeRunBudget, proposer: Proposer):
        self.spec = spec
        self.task = task
        self.sealed = sealed
        self.budget = budget
        self.proposer = proposer
        self.transcript: list[dict[str, Any]] = []
        self._leak_substrings, self._leak_tokens = sealed_literals(sealed)

    def ask(self, stage: str, prompt: str, **context: Any) -> Proposal | None:
        """One proposal, charged to the run. None means no reply or a budget refusal.

        The proposer's upper quote is reserved before dispatch; a call the budget
        cannot cover is never made. The actual charge is settled afterwards, and
        an overrun blocks the run.
        """
        if _leaks(prompt, self._leak_substrings, self._leak_tokens):
            raise SealedLeakError(f'{self.spec.wf_id}:{stage} prompt contains sealed literal(s)')
        request = ProposalRequest(self.spec.wf_id, stage, prompt, context)
        request_digest = sha256_hex(prompt)
        label = f'{self.spec.wf_id}:{stage}'
        quote = getattr(self.proposer, 'quote_microusd', 0)
        call_id = self.budget.reserve(label, request_digest, quote)
        if call_id is None:
            self.transcript.append({'stage': stage, 'request_sha256': request_digest, 'reply': 'BUDGET_REFUSED'})
            return None
        reply = self.proposer.propose(request)
        if reply is None:
            if quote:
                self.budget.hold_call(label, call_id, 'no reply from a priced proposer')
            else:
                self.budget.settle(label, call_id, 0, 0, 0)
            self.transcript.append({'stage': stage, 'request_sha256': request_digest, 'reply': None})
            return None
        u = reply.usage
        if not self.budget.settle(label, call_id, u.actual_microusd, u.input_tokens, u.output_tokens, u.wall_ms):
            self.transcript.append({'stage': stage, 'request_sha256': request_digest, 'reply': 'BUDGET_REFUSED'})
            return None
        self.transcript.append({'stage': stage, 'request_sha256': request_digest,
                                'reply_sha256': digest(reply.content), 'source': reply.source})
        return reply


@dataclass(frozen=True)
class FamilyOutcomeV1:
    wf_id: str
    verdict: str
    code: str
    host: dict[str, Any]
    detail: dict[str, Any]
    transcript: tuple[dict[str, Any], ...]
    budget: dict[str, Any]
    authority_effect: str = AUTHORITY_NONE

    @property
    def receipt_sha256(self) -> str:
        """Digest of everything except wall time; equal inputs give equal receipts."""
        return digest({'wf_id': self.wf_id, 'verdict': self.verdict, 'code': self.code,
                       'host': self.host, 'detail': self.detail, 'transcript': list(self.transcript),
                       'spent_microusd': self.budget.get('spent_microusd'),
                       'total_tokens': self.budget.get('total_tokens')})

    @property
    def positive(self) -> bool:
        return self.verdict in POSITIVE


@dataclass(frozen=True)
class Verdict:
    """What a host check returns: verdict, code and a JSON-able detail."""
    verdict: str
    code: str
    detail: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.verdict not in VERDICTS:
            raise ValueError(f'unknown verdict {self.verdict!r}')


def certified(code: str = 'CERTIFIED', **detail: Any) -> Verdict:
    return Verdict(CERTIFIED, code, detail)


def typed_refusal(code: str, **detail: Any) -> Verdict:
    return Verdict(TYPED_REFUSAL, code, detail)


def refused(code: str, **detail: Any) -> Verdict:
    return Verdict(REFUSED, code, detail)


def judge(host: HostOracleContext, ok_code: str = 'CERTIFIED', **detail: Any) -> Verdict:
    """CERTIFIED when every recorded predicate passed, else REFUSED naming the first failure."""
    if host.final_output_certified:
        return certified(ok_code, **detail)
    failed = host.failed
    return refused(failed[0].upper() if failed else 'NO_HOST_PREDICATE', failed=failed, **detail)


HOST_PASS = 'PASS'


def host_passed(host: HostOracleContext, name: str, outcome: Mapping[str, Any]) -> bool:
    """Record one outcome of the Rust operad host under ``name``; True when the host passed it."""
    return host.record(name, outcome['status'] == HOST_PASS, canonical(outcome).decode('utf-8'))


def host_code(outcome: Mapping[str, Any], failed: str | None = None) -> str:
    """The host's refusal code. For a check that ran and did not hold: ``failed``, or the host's status."""
    return outcome.get('refusal', {}).get('code', failed or outcome['status'])


class WorkflowFamily:
    """Base class. Subclasses set ``spec`` and implement ``check`` (or override ``run``)."""
    spec: ClassVar[WorkflowFamilySpecV1]
    stage: ClassVar[str] = 'solve'

    def validate(self, task: Mapping[str, Any]) -> Mapping[str, Any]:
        """Reject a malformed public task before any proposal is requested."""
        if not isinstance(task, Mapping):
            raise TypeError('task must be a mapping')
        return task

    def prompt(self, task: Mapping[str, Any]) -> str:
        """Public prompt: the task's own statement plus its canonical public data."""
        return f"{self.spec.wf_id} {self.spec.name}. {task.get('statement', '')}\n" + canonical(
            {k: v for k, v in task.items() if k != 'statement'}).decode('utf-8')

    def check(self, task: Mapping[str, Any], sealed: Mapping[str, Any], content: Any,
              host: HostOracleContext) -> Verdict:
        raise NotImplementedError

    def run(self, session: Session, host: HostOracleContext) -> Verdict:
        """Default: one proposal, one host check."""
        reply = session.ask(self.stage, self.prompt(session.task))
        if reply is None:
            return refused('NO_ADMISSIBLE_REPLY')
        return self.check(session.task, session.sealed, reply.content, host)

    def execute(self, bundle: Mapping[str, Any], *, budget: WholeRunBudget,
                proposer: Proposer | None = None) -> FamilyOutcomeV1:
        task = self.validate(bundle['task'])
        sealed = bundle.get('sealed', {})
        proposer = proposer if proposer is not None else FixtureProposer(bundle.get('replies', ()))
        session = Session(self.spec, task, sealed, budget, proposer)
        host = HostOracleContext()
        try:
            result = self.run(session, host)
        except MalformedCandidateError as exc:
            result = refused('MALFORMED_CANDIDATE', reason=str(exc))
        summary = budget.summary()
        return FamilyOutcomeV1(self.spec.wf_id, result.verdict, result.code, host.to_dict(),
                               dict(result.detail), tuple(session.transcript), summary)

    def fixtures(self) -> Mapping[str, tuple[Mapping[str, Any], str]]:
        """Named offline bundles with their expected verdict: at least one positive, one REFUSED."""
        raise NotImplementedError


class MalformedCandidateError(ValueError):
    """Raised by a host check when the candidate does not parse; becomes REFUSED."""


def require(cond: bool, reason: str) -> None:
    if not cond:
        raise MalformedCandidateError(reason)


def as_int(value: Any, name: str) -> int:
    require(type(value) is int, f'{name} must be an exact int')
    return value


def as_fraction(value: Any, name: str) -> Fraction:
    """Exact rational from an int or a 'p/q' string; floats are refused."""
    if type(value) is int:
        return Fraction(value)
    require(isinstance(value, str), f'{name} must be an int or a p/q string')
    try:
        out = Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise MalformedCandidateError(f'{name}: {exc}') from exc
    require('.' not in value and 'e' not in value.lower(), f'{name} must not be a decimal float')
    return out


def new_budget(run_id: str, task: Any, cap_microusd: int = 1) -> WholeRunBudget:
    """An in-memory budget for offline runs. The ledger needs a positive cap; one microUSD
    admits zero-cost fixture and local replies and refuses any priced call."""
    return WholeRunBudget(run_id, digest(task), cap_microusd=cap_microusd)


def run_fixture(family: WorkflowFamily, name: str) -> FamilyOutcomeV1:
    bundle, _expected = family.fixtures()[name]
    budget = new_budget(f'{family.spec.wf_id}:{name}', bundle['task'])
    try:
        return family.execute(bundle, budget=budget)
    finally:
        budget.close()


def spec_from(wf_id: str, name: str, layer: int, depends_on: Sequence[str], merge_into: str | None,
              host_check_id: str, folder: str) -> WorkflowFamilySpecV1:
    return WorkflowFamilySpecV1(wf_id, name, layer, tuple(depends_on), merge_into, host_check_id,
                                'workflows/' + folder)
