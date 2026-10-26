"""Gamma38 wire and three *external* lossless display/transport profiles.

Only parse_wire/emit_wire use the normative raw alphabet. Compact, postfix,
and tagged JSON are explicit dialects and never silently accepted as raw wire.
"""

from __future__ import annotations

import hashlib
import json
import re

from .grammar import App, Atom, Diff


class WireError(ValueError):
    pass


Node = Diff | Atom | App
ALNUM = re.compile(r"[a-z0-9]+")
BIN = re.compile(r"(?:0|1[01]*)")  # canonical, no leading zeros
MAX_BYTES = 1_000_000
MAX_DEPTH = 64


def parse_wire(source: str) -> Node:
    if len(source.encode("utf8")) > MAX_BYTES or not source:
        raise WireError("empty or oversized input")

    def one(pos: int, depth: int):
        if depth > MAX_DEPTH:
            raise WireError("recursion depth limit")
        if source.startswith("op<", pos):
            pos += 3
            children = []
            while pos < len(source) and source[pos] != ">":
                child, pos = one(pos, depth + 1)
                children.append(child)
            if pos == len(source):
                raise WireError("unclosed application")
            return App(tuple(children)), pos + 1
        if source.startswith("<>", pos):
            return Diff(), pos + 2
        if pos < len(source) and source[pos] == "<":
            m = ALNUM.match(source, pos + 1)
            if m and m.end() < len(source) and source[m.end()] == ">":
                return Atom(m.group()), m.end() + 1
        raise WireError(f"invalid raw wire at position {pos}")

    result, end = one(0, 0)
    if end != len(source):
        raise WireError("multiple packets or trailing data")
    return result


def emit_wire(node: Node) -> str:
    if isinstance(node, Diff):
        return "<>"
    if isinstance(node, Atom):
        if ALNUM.fullmatch(node.word) is None:
            raise WireError("invalid atom")
        return f"<{node.word}>"
    if isinstance(node, App):
        return "op<" + "".join(emit_wire(c) for c in node.children) + ">"
    raise WireError("unknown AST node")


def application(opcode: int, *args: Node) -> App:
    if opcode < 0:
        raise WireError("negative opcode")
    return App((Atom(format(opcode, "b")), *args))


def opcode_and_args(node: Node) -> tuple[int, tuple[Node, ...]]:
    if not isinstance(node, App) or not node.children:
        raise WireError("expected typed application")
    head = node.children[0]
    if not isinstance(head, Atom) or not BIN.fullmatch(head.word):
        raise WireError("opcode must be canonical binary")
    return int(head.word, 2), node.children[1:]


def _atom_word(node: Node) -> str:
    if not isinstance(node, Atom):
        raise WireError("expected atom")
    return node.word


def emit_compact(node: Node) -> str:
    if isinstance(node, Diff):
        return "!"
    if isinstance(node, Atom):
        return "@" + _atom_word(node)
    code, args = opcode_and_args(node)
    if code == 1 and len(args) == 1 and isinstance(args[0], Atom):
        return f"V({_atom_word(args[0])})"
    if code == 2 and len(args) == 2 and all(isinstance(c, Atom) for c in args):
        return f"E({_atom_word(args[0])},{_atom_word(args[1])})"
    if code == 3:
        return "G(" + ",".join(map(emit_compact, args)) + ")"
    if code == 4 and len(args) == 2 and isinstance(args[0], Diff):
        return "O(!," + emit_compact(args[1]) + ")"
    return (
        "A(" + format(code, "b") + ("," + ",".join(map(emit_compact, args)) if args else "") + ")"
    )


def parse_compact(source: str) -> Node:
    """MSS-C/1, a deterministic off-wire dialect with explicit delimiters."""
    if len(source.encode("utf8")) > MAX_BYTES or not source:
        raise WireError("empty or oversized compact input")
    pos = 0

    def take(literal: str) -> None:
        nonlocal pos
        if not source.startswith(literal, pos):
            raise WireError(f"expected {literal!r} at {pos}")
        pos += len(literal)

    def word() -> str:
        nonlocal pos
        m = ALNUM.match(source, pos)
        if not m:
            raise WireError(f"expected word at {pos}")
        pos = m.end()
        return m.group()

    def item(depth: int) -> Node:
        nonlocal pos
        if depth > MAX_DEPTH:
            raise WireError("recursion depth limit")
        if source.startswith("!", pos):
            take("!")
            return Diff()
        if source.startswith("@", pos):
            take("@")
            return Atom(word())
        if source.startswith("V(", pos):
            take("V(")
            result = application(1, Atom(word()))
            take(")")
            return result
        if source.startswith("E(", pos):
            take("E(")
            u = Atom(word())
            take(",")
            v = Atom(word())
            take(")")
            return application(2, u, v)
        if source.startswith("O(", pos):
            take("O(")
            take("!")
            take(",")
            carrier = item(depth + 1)
            take(")")
            return application(4, Diff(), carrier)
        if source.startswith("G(", pos):
            take("G(")
            args = []
            if pos < len(source) and source[pos] != ")":
                args.append(item(depth + 1))
                while pos < len(source) and source[pos] == ",":
                    take(",")
                    args.append(item(depth + 1))
            take(")")
            return application(3, *args)
        if source.startswith("A(", pos):
            take("A(")
            code = word()
            if not BIN.fullmatch(code):
                raise WireError("opcode not canonical binary")
            args = []
            while pos < len(source) and source[pos] == ",":
                take(",")
                args.append(item(depth + 1))
            take(")")
            return application(int(code, 2), *args)
        raise WireError(f"invalid compact profile at {pos}")

    parsed = item(0)
    if pos != len(source):
        raise WireError("compact trailing data")
    return parsed


def emit_postfix(node: Node) -> str:
    def tokens(x: Node):
        if isinstance(x, Diff):
            return ["!"]
        if isinstance(x, Atom):
            return ["@" + _atom_word(x)]
        code, args = opcode_and_args(x)
        result = []
        for arg in args:
            result.extend(tokens(arg))
        result.append(f"#{code:b}/{len(args)}")
        return result

    return " ".join(tokens(node))


def parse_postfix(source: str) -> Node:
    if len(source.encode("utf8")) > MAX_BYTES or not source:
        raise WireError("empty or oversized postfix input")
    stack = []
    for tok in source.split(" "):
        if tok == "!":
            stack.append(Diff())
        elif tok.startswith("@") and ALNUM.fullmatch(tok[1:]):
            stack.append(Atom(tok[1:]))
        else:
            m = re.fullmatch(r"#(0|1[01]*)/(0|[1-9][0-9]*)", tok)
            if not m:
                raise WireError("postfix illegal token")
            count = int(m.group(2))
            if count > len(stack):
                raise WireError("postfix stack underflow")
            children = tuple(stack[len(stack) - count :]) if count else ()
            if count:
                del stack[-count:]
            stack.append(application(int(m.group(1), 2), *children))
        if len(stack) > 4096:
            raise WireError("postfix stack limit")
    if len(stack) != 1:
        raise WireError("postfix leftover terms")
    return stack[0]


def _tree(node: Node):
    if isinstance(node, Diff):
        return ["d"]
    if isinstance(node, Atom):
        return ["a", _atom_word(node)]
    return ["p", [_tree(child) for child in node.children]]


def _from_tree(tree, depth=0):
    if depth > MAX_DEPTH or not isinstance(tree, list):
        raise WireError("invalid typed JSON node")
    if tree == ["d"]:
        return Diff()
    if len(tree) == 2 and tree[0] == "a" and isinstance(tree[1], str) and ALNUM.fullmatch(tree[1]):
        return Atom(tree[1])
    if len(tree) == 2 and tree[0] == "p" and isinstance(tree[1], list):
        return App(tuple(_from_tree(c, depth + 1) for c in tree[1]))
    raise WireError("invalid typed JSON tag or arity")


def emit_tagged_json(node: Node) -> str:
    return json.dumps(_tree(node), separators=(",", ":"), ensure_ascii=True)


def parse_tagged_json(source: str) -> Node:
    if len(source.encode("utf8")) > MAX_BYTES:
        raise WireError("oversized tagged JSON")
    try:
        value = json.loads(source)
    except (ValueError, TypeError) as exc:
        raise WireError("malformed JSON") from exc
    result = _from_tree(value)
    if emit_tagged_json(result) != source:
        raise WireError("noncanonical tagged JSON")
    return result


def _digest_record(record: dict) -> str:
    body = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(body.encode("utf8")).hexdigest()


def emit_dag(node: Node) -> str:
    """Off-wire hash-consed JSON DAG; SHA256 commits to tagged node records."""
    records = {}

    def visit(x: Node, depth=0):
        if depth > MAX_DEPTH:
            raise WireError("DAG depth limit")
        if isinstance(x, Diff):
            record = {"k": "d"}
        elif isinstance(x, Atom):
            record = {"k": "a", "v": _atom_word(x)}
        else:
            record = {"k": "p", "c": [visit(c, depth + 1) for c in x.children]}
        digest = _digest_record(record)
        records[digest] = record
        return digest

    root = visit(node)
    return json.dumps(
        {"nodes": records, "root": root},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def parse_dag(source: str) -> Node:
    if len(source.encode("utf8")) > 4 * MAX_BYTES:
        raise WireError("DAG too large")
    try:
        payload = json.loads(source)
    except (TypeError, ValueError) as exc:
        raise WireError("DAG malformed JSON") from exc
    if (
        not isinstance(payload, dict)
        or set(payload) != {"nodes", "root"}
        or not isinstance(payload["nodes"], dict)
    ):
        raise WireError("DAG envelope")
    nodes = payload["nodes"]
    if len(nodes) > 20_000 or any(
        not isinstance(key, str) or not isinstance(value, dict) or key != _digest_record(value)
        for key, value in nodes.items()
    ):
        raise WireError("DAG record hash mismatch")
    visiting = set()
    memo = {}

    def visit(key, depth=0):
        if not isinstance(key, str):
            raise WireError("DAG reference must be a content digest")
        if depth > MAX_DEPTH or key in visiting:
            raise WireError("DAG cycle or excessive depth")
        if key in memo:
            return memo[key]
        if key not in nodes:
            raise WireError("DAG missing reference")
        visiting.add(key)
        record = nodes[key]
        if record == {"k": "d"}:
            result = Diff()
        elif (
            set(record) == {"k", "v"}
            and record["k"] == "a"
            and isinstance(record["v"], str)
            and ALNUM.fullmatch(record["v"])
        ):
            result = Atom(record["v"])
        elif set(record) == {"k", "c"} and record["k"] == "p" and isinstance(record["c"], list):
            result = App(tuple(visit(child, depth + 1) for child in record["c"]))
        else:
            raise WireError("DAG invalid node")
        visiting.remove(key)
        memo[key] = result
        return result

    result = visit(payload["root"])
    if set(memo) != set(nodes) or emit_dag(result) != source:
        raise WireError("DAG unreachable node or noncanonical encoding")
    return result
