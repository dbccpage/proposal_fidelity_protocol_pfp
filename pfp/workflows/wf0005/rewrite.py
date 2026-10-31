"""Bounded semantic frontend, full span custody, and independent packet decoding."""

import re
from copy import deepcopy
from importlib.resources import files

from pfp.domain.tower import grammar
from pfp.infrastructure.adapters.pfp_campaign import canonical, digest
from pfp.workflows.wf0004.workflow import validate_task

GRAMMAR_ID = "pfp-packet-v1"
DECODER_ID = "wf5-exact-integer-sum-v1"
STRATEGY_ID = "total-span-sum-lowering-v1"
PREFIX = "Calculate the exact sum of "
INTEGER = re.compile(r"-?(?:0|[1-9][0-9]*)")
MAX_WIRE_BYTES = 65536


def grammar_digest():
    return digest(files(__package__).joinpath("packet.ebnf").read_bytes())


def source_query(seed):
    """Recognize the entire declared source language, never ignore a suffix."""
    if not seed.startswith(PREFIX) or not seed.endswith("."):
        raise ValueError("WF5_UNSUPPORTED_SEED_LANGUAGE")
    body = seed[len(PREFIX) : -1]
    matches = list(INTEGER.finditer(body))
    tokens = [m.group() for m in matches]
    if not tokens or len(tokens) > 1024 or any(t == "-0" for t in tokens):
        raise ValueError("WF5_SOURCE_INTEGER_SYNTAX")
    rendering = (
        tokens[0]
        if len(tokens) == 1
        else " and ".join(tokens)
        if len(tokens) == 2
        else ", ".join(tokens[:-1]) + ", and " + tokens[-1]
    )
    if body != rendering or any(len(t.lstrip("-")) > 101 for t in tokens):
        raise ValueError("WF5_UNACCOUNTED_OR_NONCANONICAL_SOURCE")
    return query([int(t) for t in tokens])


def query(values):
    return dict(
        operation="sum",
        arithmetic="integer_exact",
        occurrence_policy="all_once",
        rounding="forbidden",
        values=values,
        output="task_result.total",
    )


def render_source(protected):
    tokens = [str(value) for value in protected["values"]]
    body = (
        tokens[0]
        if len(tokens) == 1
        else " and ".join(tokens)
        if len(tokens) == 2
        else ", ".join(tokens[:-1]) + ", and " + tokens[-1]
    )
    return PREFIX + body + "."


def encode(protected):
    values = grammar.App(
        (
            grammar.Atom("values"),
            *(
                grammar.Atom(("n" if value < 0 else "p") + str(abs(value)))
                for value in protected["values"]
            ),
        )
    )
    packet = grammar.App(
        (
            grammar.Atom("sum"),
            grammar.Atom("exact"),
            grammar.Atom("once"),
            values,
            grammar.Atom("total"),
        )
    )
    return grammar.serialize(packet)


def decode(wire):
    """Meaning is explicit, independently recovered from parsed target nodes."""
    if type(wire) is not str or len(wire.encode("utf-8")) > MAX_WIRE_BYTES:
        raise ValueError("WF5_PACKET_SIZE_OR_TYPE")
    # Bound depth before invoking the existing recursive parser on untrusted text.
    depth = 0
    for char in wire:
        depth += (char == "<") - (char == ">")
        if depth > 3 or depth < 0:
            raise ValueError("WF5_PACKET_DEPTH")
    packet = grammar.parse(wire)
    if type(packet) is not grammar.App or len(packet.children) != 5:
        raise ValueError("WF5_SUM_PACKET_ARITY")
    op, exact, once, values, terminal = packet.children
    if (
        op != grammar.Atom("sum")
        or exact != grammar.Atom("exact")
        or once != grammar.Atom("once")
        or terminal != grammar.Atom("total")
        or type(values) is not grammar.App
        or values.opcode != "values"
        or not 1 <= len(values.arguments) <= 1024
    ):
        raise ValueError("WF5_PACKET_DECODER_CONTRACT")
    result = []
    for node in values.arguments:
        if (
            type(node) is not grammar.Atom
            or not re.fullmatch(r"[pn](?:0|[1-9][0-9]{0,100})", node.word)
            or node.word == "n0"
        ):
            raise ValueError("WF5_PACKET_INTEGER_SYNTAX")
        value = int(node.word[1:]) * (-1 if node.word[0] == "n" else 1)
        if abs(value) > 10**100:
            raise ValueError("WF5_PACKET_INTEGER_BOUND")
        result.append(value)
    if grammar.serialize(packet) != wire:
        raise ValueError("WF5_NONCANONICAL_PACKET")
    return query(result)


def spans(seed):
    """A contiguous partition of source characters and original UTF-8 bytes."""
    parts = [(0, 14, "task"), (14, 19, "constraint"), (19, len(PREFIX), "task")]
    position = len(PREFIX)
    for i, match in enumerate(INTEGER.finditer(seed, position, len(seed) - 1)):
        if position < match.start():
            parts.append((position, match.start(), "list_syntax"))
        parts.append((match.start(), match.end(), f"operand:{i}"))
        position = match.end()
    parts.append((position, len(seed), "punctuation"))
    return [
        dict(
            start_char=a,
            end_char=b,
            start_byte=len(seed[:a].encode()),
            end_byte=len(seed[:b].encode()),
            role=role,
            text=seed[a:b],
        )
        for a, b, role in parts
    ]


def lower(spec):
    """No answer calculation or model call. Unknown meaning is a retained refusal."""
    spec = validate_task(spec)
    seed = spec["seed_prompt"]
    base = dict(
        schema="pfp.wf5.seed-rewrite.v1",
        grammar_id=GRAMMAR_ID,
        public_start="packet",
        grammar_sha256=grammar_digest(),
        decoder_id=DECODER_ID,
        strategy_id=STRATEGY_ID,
        original_seed_sha256=digest(seed.encode()),
        original_seed_utf8_bytes=len(seed.encode()),
        rewrite_provider_calls=0,
        authority_effect="None",
    )
    try:
        original = source_query(seed)
        if canonical(original["values"]) != canonical(spec["input"]["values"]):
            raise ValueError("WF5_SEED_INPUT_CONFLICT")
        wire = encode(original)
        decoded = decode(wire)
        ledger = spans(seed)
        coverage = (
            "".join(row["text"] for row in ledger) == seed
            and ledger[0]["start_byte"] == 0
            and ledger[-1]["end_byte"] == len(seed.encode())
            and all(a["end_byte"] == b["start_byte"] for a, b in zip(ledger, ledger[1:]))
        )
        obligations = dict(
            full_source_coverage=coverage,
            protected_query_equal=decoded == original,
            public_input_equal=decoded["values"] == spec["input"]["values"],
            exact_output_interface=decoded["output"] == "task_result.total",
            canonical_source_roundtrip=render_source(decoded) == seed,
        )
        if not all(obligations.values()):
            raise ValueError("WF5_PRESERVATION_FAILED")
        base.update(
            status="HOST_ACCEPTED",
            seed_spans=ledger,
            unresolved_spans=[],
            source_query=original,
            decoded_query=decoded,
            wire=wire,
            wire_sha256=digest(wire.encode()),
            wire_utf8_bytes=len(wire.encode()),
            preservation=obligations,
            output_origin="DECLARED_ANSWER_SCHEMA; not an added source quotation",
            steps=[
                dict(
                    rule=STRATEGY_ID,
                    position="root",
                    source_sha256=digest(seed.encode()),
                    target_sha256=digest(wire.encode()),
                )
            ],
        )
    except ValueError as exc:
        base.update(
            status="TYPED_REFUSAL",
            failure_class=str(exc),
            seed_spans=[],
            unresolved_spans=[dict(start_byte=0, end_byte=len(seed.encode()), text=seed)],
            wire=None,
        )
    return dict(payload=base, sha256=digest(canonical(base)))


def verify(spec, bundle):
    if bundle != lower(spec):
        raise ValueError("WF5_REWRITE_REPLAY_MISMATCH")
    if bundle["payload"]["status"] != "HOST_ACCEPTED":
        raise ValueError("WF5_REWRITE_NOT_PRESERVED")
    return deepcopy(bundle)


def rewritten_task(spec, bundle):
    verified = verify(spec, bundle)
    task = deepcopy(spec)
    task["seed_prompt"] = verified["payload"]["wire"]
    return task
