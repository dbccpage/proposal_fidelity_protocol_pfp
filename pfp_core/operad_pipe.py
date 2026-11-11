"""OPERADS typed skill wiring and an operational trace quotient.

Every stage of a workflow (a prompt skill, a host normalizer, a host checker,
a repair or a synthesis call) is a unary ``TypedOp`` from one canonical operad
colour to another. ``compose`` admits a pipeline only when each adjacent pair
composes under ``operads.domain.operad.planar.compose_colour_signatures``.

``quotient_workflows`` groups workflows whose canonical operational traces are
equal, so duplicate or reordered context skills are collapsed before any token
is spent. The commutation rule is a declared assumption, not a law the
executor was shown to satisfy: adjacent ``context`` ops (skill text placed in
the prompt) are treated as an unordered set keyed by their prompt digest;
every other kind (normalize, check, repair, generate, synthesize) keeps its
position, so ``normalize -> check`` and ``check -> normalize`` stay distinct.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from . import REPO_ROOT  # noqa: F401
from operads.domain.operad.colours import ColourSignature
from operads.domain.operad.planar import compose_colour_signatures

KINDS = frozenset({'context', 'generate', 'normalize', 'check', 'repair', 'synthesize'})


@dataclass(frozen=True)
class TypedOp:
    op_id: str
    input_colour: str
    output_colour: str
    kind: str
    prompt_digest: str = ''
    normalizer_id: str = ''
    checker_id: str = ''
    cost_tokens: int = 0  # declared prompt-token profile (an estimate)
    idempotent_key: str = ''

    def __post_init__(self):
        if self.kind not in KINDS:
            raise ValueError(f'unknown op kind {self.kind!r}')
        if type(self.cost_tokens) is not int or self.cost_tokens < 0:
            raise ValueError('cost_tokens must be a nonnegative int')
        self.signature  # validates colours against the canon

    @property
    def signature(self) -> ColourSignature:
        return ColourSignature((self.input_colour,), self.output_colour)

    @property
    def trace_atom(self) -> tuple[str, str, str, str]:
        return (str(self.signature), self.prompt_digest, self.normalizer_id, self.checker_id)


def compose(ops: list[TypedOp]) -> ColourSignature:
    """Signature of the pipeline ``ops[-1] o ... o ops[0]``; raises on a type gap."""
    if not ops:
        raise ValueError('EMPTY_PIPELINE')
    sig = ops[0].signature
    for op in ops[1:]:
        result = compose_colour_signatures(op.signature, sig, 0)
        if result.is_err:
            raise TypeError(f'PIPELINE_ILL_TYPED at {op.op_id}: {result.error.message}')
        sig = result.unwrap()
    return sig


def canonical_trace(ops: list[TypedOp]) -> tuple:
    """Trace with each maximal run of context ops replaced by its sorted digest set."""
    out: list = []
    run: set = set()
    for op in ops:
        if op.kind == 'context':
            run.add(op.idempotent_key or op.prompt_digest)
            continue
        if run:
            out.append(('context-set', tuple(sorted(run))))
            run = set()
        out.append(op.trace_atom)
    if run:
        out.append(('context-set', tuple(sorted(run))))
    return tuple(out)


def trace_digest(ops: list[TypedOp]) -> str:
    compose(ops)
    raw = json.dumps(canonical_trace(ops), separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def quotient_workflows(workflows: dict[str, list[TypedOp]]) -> dict[str, list[str]]:
    """Map each trace digest to the sorted names of workflows sharing it."""
    classes: dict[str, list[str]] = {}
    for name in sorted(workflows):
        classes.setdefault(trace_digest(workflows[name]), []).append(name)
    return classes

