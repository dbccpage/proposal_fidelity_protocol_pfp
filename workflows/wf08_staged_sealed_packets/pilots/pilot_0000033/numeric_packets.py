"""Two explicit, pilot-local numeric profiles, not a replacement for boundary.ebnf."""

import json
import re
from dataclasses import dataclass
from fractions import Fraction
from math import gcd

LEGACY = "sn09-legacy-numeric-v1"
HAG = "sn09-hag-numeric-v1"
PROFILES = (LEGACY, HAG)
MAX_BYTES = 4096
MAX_JSON_BYTES = 65536
MAX_DEPTH = 32
MAX_NODES = 512
MAX_INTEGER = 1_000_000_000


@dataclass(frozen=True)
class Node:
    tag: str
    children: tuple["Node", ...] = ()


def profile_check(profile):
    if profile not in PROFILES:
        raise ValueError("UNKNOWN_PROFILE")


def json_read(raw: bytes):
    def pairs(items):
        obj = {}
        for key, value in items:
            if key in obj:
                raise ValueError("DUPLICATE_JSON_KEY")
            obj[key] = value
        return obj

    if not isinstance(raw, bytes) or len(raw) > MAX_JSON_BYTES:
        raise ValueError("JSON_SIZE_OR_TYPE")
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise ValueError("INVALID_JSON") from error


def integer(node):
    if node.children or re.fullmatch(r"0|[1-9][0-9]{0,9}", node.tag) is None:
        raise ValueError("NONCANONICAL_INTEGER")
    value = int(node.tag)
    if value > MAX_INTEGER:
        raise ValueError("INTEGER_LIMIT")
    return value


def value(node):
    """Evaluate only registered constructors; a name never executes code."""
    if node.tag == "rat":
        if len(node.children) != 3:
            raise ValueError("RAT_ARITY")
        sign, numerator, denominator = node.children
        if sign.children or sign.tag not in ("pos", "neg"):
            raise ValueError("RAT_SIGN")
        n, d = integer(numerator), integer(denominator)
        if d == 0 or gcd(n, d) != 1 or (n == 0 and sign.tag != "pos"):
            raise ValueError("NONCANONICAL_RATIONAL")
        return Fraction(n if sign.tag == "pos" else -n, d)
    if node.tag == "sum6":
        if len(node.children) != 6:
            raise ValueError("SUM6_ARITY")
        return sum((value(child) for child in node.children), Fraction(0))
    return Fraction(integer(node))


def from_data(data):
    count = 0

    def visit(obj, depth):
        nonlocal count
        count += 1
        if depth > MAX_DEPTH or count > MAX_NODES:
            raise ValueError("TREE_LIMIT")
        if not isinstance(obj, dict) or set(obj) != {"tag", "children"}:
            raise ValueError("NODE_FIELDS")
        tag, children = obj["tag"], obj["children"]
        if not isinstance(tag, str) or re.fullmatch(r"[a-z0-9]{1,10}", tag) is None:
            raise ValueError("NODE_TAG")
        if not isinstance(children, list) or len(children) > 6:
            raise ValueError("NODE_CHILDREN")
        return Node(tag, tuple(visit(child, depth + 1) for child in children))

    node = visit(data, 1)
    value(node)
    return node


def to_data(node):
    return {"tag": node.tag, "children": [to_data(child) for child in node.children]}


def parse(raw: bytes, profile: str):
    profile_check(profile)
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_BYTES:
        raise ValueError("WIRE_SIZE_OR_TYPE")
    if any(byte not in b"<>abcdefghijklmnopqrstuvwxyz0123456789" for byte in raw):
        raise ValueError("WIRE_ALPHABET")
    position = packets = 0

    def visit(depth):
        nonlocal position, packets
        packets += 1
        if depth > MAX_DEPTH or packets > MAX_NODES:
            raise ValueError("WIRE_TREE_LIMIT")
        if position >= len(raw) or raw[position] != 60:
            raise ValueError("EXPECTED_OPEN")
        position += 1
        if position < len(raw) and raw[position] == 60:
            if profile != LEGACY:
                raise ValueError("LEGACY_HEAD_IN_HAG")
            head = visit(depth + 1)
            if head.children or not head.tag:
                raise ValueError("NONATOMIC_HEAD")
            tag = head.tag
            children = []
            while position < len(raw) and raw[position] == 60:
                children.append(visit(depth + 1))
        else:
            start = position
            while position < len(raw) and raw[position] not in (60, 62):
                position += 1
            tag = raw[start:position].decode("ascii")
            children = []
            while position < len(raw) and raw[position] == 60:
                if profile != HAG:
                    raise ValueError("HAG_HEAD_IN_LEGACY")
                children.append(visit(depth + 1))
        if position >= len(raw) or raw[position] != 62:
            raise ValueError("EXPECTED_CLOSE")
        position += 1
        return Node(tag, tuple(children))

    node = visit(1)
    if position != len(raw):
        raise ValueError("TRAILING_WIRE")
    # The wire grammar and the numeric constructor grammar are separate checks.
    checked = from_data(to_data(node))
    if serialize(checked, profile) != raw:
        raise ValueError("NONCANONICAL_WIRE")
    return checked


def serialize(node, profile):
    profile_check(profile)

    def emit(current):
        if not current.children:
            return "<" + current.tag + ">"
        head = "<" + current.tag + ">" if profile == LEGACY else current.tag
        return "<" + head + "".join(emit(child) for child in current.children) + ">"

    return emit(node).encode("ascii")
