"""Recognize bounded fixtures against the checked-in EBNF subset.

Development evidence only; not a production parser or semantic verifier.
AuthorityEffect: None. No external packages for the default command.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
# One canonical owner and one public start for each retained profile.
PROFILES = {
    "mss-boundary-v1": ("../python/domain/boundary.ebnf", "packet"),
    "historical-packet-v1": ("historical_packet.ebnf", "packet"),
    "pkt00-k0-v1": ("cycle_repair.ebnf", "cycle_repair"),
    "quiz-packet-v1": ("quiz_packet.ebnf", "quiz_message"),
    "glyph-graph-v1": ("glyph_graph.ebnf", "glyph_graph"),
    "ddc-tape-shape-v1": ("ddc_trace.ebnf", "ddc_trace"),
}
# Explicit declarations, never guessed from a filename or extension.
SOURCE_STARTS = {
    "../cycle_balance/00_genesis_cycle_balance_wire.mssn": "pkt00-k0-v1",
}

TOKEN = re.compile(r'\s+|\(\*[\s\S]*?\*\)|"(?:[^"\\]|\\.)*"|[a-z][a-z0-9_]*|[=;,|{}\[\]()]')


class Grammar:
    """Small recognizer for this directory's explicitly documented EBNF subset."""

    def __init__(self, source: str):
        self.tokens = []
        pos = 0
        while pos < len(source):
            match = TOKEN.match(source, pos)
            if match is None:
                raise ValueError(f"Unsupported EBNF at offset {pos}: {source[pos : pos + 40]!r}")
            token = match.group()
            if not token.isspace() and not token.startswith("(*"):
                self.tokens.append(token)
            pos = match.end()
        self.pos = 0
        self.rules = {}
        while self.pos < len(self.tokens):
            name = self.take()
            if not re.fullmatch(r"[a-z][a-z0-9_]*", name) or name in self.rules:
                raise ValueError(f"Invalid or duplicate rule: {name}")
            self.take("=")
            self.rules[name] = self.expression()
            self.take(";")

        def references(node):
            if node[0] == "ref":
                return {node[1]}
            if node[0] in {"seq", "alt"}:
                return set().union(*(references(n) for n in node[1]))
            if node[0] in {"rep", "opt"}:
                return references(node[1])
            return set()

        missing = set().union(*(references(n) for n in self.rules.values())) - self.rules.keys()
        if missing:
            raise ValueError(f"Undefined rules: {sorted(missing)}")

    def take(self, expected=None):
        if self.pos >= len(self.tokens):
            raise ValueError("Unexpected end of grammar")
        token = self.tokens[self.pos]
        self.pos += 1
        if expected is not None and token != expected:
            raise ValueError(f"Expected {expected!r}, got {token!r}")
        return token

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def expression(self):
        alternatives = [self.sequence()]
        while self.peek() == "|":
            self.take("|")
            alternatives.append(self.sequence())
        return ("alt", tuple(alternatives))

    def sequence(self):
        nodes = [self.factor()]
        while self.peek() == ",":
            self.take(",")
            nodes.append(self.factor())
        return ("seq", tuple(nodes))

    def factor(self):
        token = self.take()
        if token.startswith('"'):
            return ("lit", json.loads(token))
        if token in {"[", "{", "("}:
            node = self.expression()
            self.take({"[": "]", "{": "}", "(": ")"}[token])
            return node if token == "(" else ("opt" if token == "[" else "rep", node)
        if re.fullmatch(r"[a-z][a-z0-9_]*", token):
            return ("ref", token)
        raise ValueError(f"Unsupported factor: {token!r}")

    def end_positions(self, start, text, offset=0):
        @lru_cache(None)
        def ends(node, pos):
            kind, value = node
            if kind == "lit":
                return frozenset({pos + len(value)}) if text.startswith(value, pos) else frozenset()
            if kind == "ref":
                return ends(self.rules[value], pos)
            if kind == "alt":
                return frozenset().union(*(ends(child, pos) for child in value))
            if kind == "seq":
                positions = frozenset({pos})
                for child in value:
                    positions = frozenset().union(*(ends(child, p) for p in positions))
                return positions
            if kind == "opt":
                return ends(value, pos) | {pos}
            if kind == "rep":
                seen, todo = {pos}, [pos]
                while todo:
                    p = todo.pop()
                    next_positions = ends(value, p)
                    if p in next_positions:
                        raise ValueError("Nullable repetition is outside this checker subset")
                    for end in next_positions - seen:
                        seen.add(end)
                        todo.append(end)
                return frozenset(seen)
            raise ValueError(kind)

        return ends(("ref", start), offset)

    def accepts(self, start, text):
        return len(text) in self.end_positions(start, text)


def read_text(path):
    return path.read_text(encoding="utf-8")


def source_body(path):
    # Explicit .mssn source adapter. Never used for submitted fixture text.
    return strip_source_comments(read_text(path))


def strip_source_comments(text):
    return "\n".join(
        line.split("#", 1)[0].strip() for line in text.splitlines() if line.split("#", 1)[0].strip()
    )


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def check_runtime(cases, grammars):
    boundary = load_module("grammar_check_boundary", HERE.parent / "python/domain/rewrite.py")
    cycle = load_module(
        "grammar_check_cycle", HERE.parent / "python/infrastructure/mssn_transcoder.py"
    )
    # Use the existing parser and its own golden corpus, not a second implementation.
    for parent in HERE.parents:
        if (parent / "omega_engine_pfp").is_dir():
            sys.path.insert(0, str(parent))
            break
    from omega_engine_pfp.domain.tower import golden_corpus
    from omega_engine_pfp.domain.tower import grammar as historical

    def cycle_parse(text):
        suite = cycle.MssnCycleRepairTranscoder.wire_to_four_object(text)
        receipt = suite.receipt
        if (
            receipt["verification_status"] != "UNVERIFIED"
            or receipt["terminal_status"] is not None
            or receipt["exact_witness"] is not None
        ):
            raise AssertionError("Parsing promoted an unchecked witness")
        rendered = cycle.MssnCycleRepairTranscoder.four_object_to_wire(suite)
        # Only remove comments from known source, never from a submitted case.
        body = strip_source_comments(rendered)
        if not grammars["pkt00-k0-v1"].accepts("cycle_repair", body):
            raise AssertionError("Transcoder output is outside its declared grammar")
        replay = cycle.MssnCycleRepairTranscoder.wire_to_four_object(rendered)
        if suite != replay:
            raise AssertionError("Parsed suite changed during render/parse round trip")
        return suite

    parsers = {
        "mss-boundary-v1": (boundary.parse_boundary, ValueError),
        "historical-packet-v1": (historical.parse, historical.GrammarError),
        "pkt00-k0-v1": (cycle_parse, cycle.MssnTranscoderError),
    }
    checked = 0
    for case in cases:
        if case["profile"] not in parsers:
            continue
        parse, refusal = parsers[case["profile"]]
        try:
            result = parse(case["text"])
        except refusal:
            actual = False
        else:
            actual = True
            if case["profile"] == "mss-boundary-v1" and result.render() != case["text"]:
                raise AssertionError("Boundary round trip changed bytes")
            if case["profile"] == "historical-packet-v1" and result.serialize() != case["text"]:
                raise AssertionError("Historical round trip changed bytes")
        if actual != case.get("runtime_accept", case["accept"]):
            raise AssertionError(f"Runtime mismatch: {case['id']}")
        checked += 1
    for name in SOURCE_STARTS:
        cycle_parse(read_text(HERE / name))

    corpus = [(t, True) for t in golden_corpus.VALID + golden_corpus.CANONICAL_SEQUENCE]
    # This corpus also labels an inactive MSS-1 glyph invalid. It IS raw syntax;
    # level activation belongs to a different checker.
    corpus += [(t, t == "op<<101><2><0><1><10>>") for t, _ in golden_corpus.INVALID]
    for text, expected in corpus:
        if grammars["historical-packet-v1"].accepts("packet", text) != expected:
            raise AssertionError(f"Historical golden corpus mismatch: {text}")
        try:
            node = historical.parse(text)
        except historical.GrammarError:
            accepted = False
        else:
            accepted = True
            if node.serialize() != text:
                raise AssertionError("Historical golden round trip changed bytes")
        if accepted != expected:
            raise AssertionError(f"Historical runtime golden mismatch: {text}")

    # These are runtime limits, deliberately not claims about the unbounded EBNF.
    limits = [
        ("<" + "a" * 65534 + ">", True),
        ("<" + "a" * 65535 + ">", False),
        ("<" * 33 + ">" * 33, True),
        ("<" * 34 + ">" * 34, False),
        ("<" + "<>" * 4095 + ">", True),
        ("<" + "<>" * 4096 + ">", False),
    ]
    for text, expected in limits:
        try:
            boundary.parse_boundary(text)
        except ValueError:
            actual = False
        else:
            actual = True
        if actual != expected:
            raise AssertionError("Boundary budget edge changed")
    print(
        f"PASS: {checked} runtime cases, {len(corpus)} historical corpus cases, "
        f"{len(limits)} boundary budget edges; source and accepted PKT-00 round trips"
    )


def main(runtime=False):
    declared = {name for name, _ in PROFILES.values() if "/" not in name}
    if not declared.issubset({p.name for p in HERE.glob("*.ebnf")}):
        raise AssertionError("Undeclared or missing EBNF profile")
    declared_sources = {name for name in SOURCE_STARTS if "/" not in name}
    if {p.name for p in HERE.glob("*.mssn")} != declared_sources:
        raise AssertionError("Undeclared or missing source fixture")
    grammars = {profile: Grammar(read_text(HERE / name)) for profile, (name, _) in PROFILES.items()}
    for profile, (_, start) in PROFILES.items():
        if start not in grammars[profile].rules:
            raise AssertionError(f"Missing start rule: {profile}/{start}")
    cases = json.loads(read_text(HERE / "conformance_cases.json"))
    ids = set()
    coverage = {profile: set() for profile in PROFILES}
    for case in cases:
        required = {"id", "profile", "text", "accept"}
        if (
            not required <= case.keys()
            or case.keys() - required - {"runtime_accept", "note"}
            or not all(isinstance(case[k], str) for k in ("id", "profile", "text"))
            or not case["id"]
            or case["id"] in ids
            or type(case["accept"]) is not bool
            or case["profile"] not in PROFILES
        ):
            raise AssertionError(f"Invalid conformance case: {case!r}")
        if "runtime_accept" in case and (
            type(case["runtime_accept"]) is not bool or case["profile"] != "pkt00-k0-v1"
        ):
            raise AssertionError(f"Invalid runtime expectation: {case['id']}")
        ids.add(case["id"])
        profile = case["profile"]
        coverage[profile].add(case["accept"])
        actual = grammars[profile].accepts(PROFILES[profile][1], case["text"])
        if actual != case["accept"]:
            raise AssertionError(f"{case['id']}: expected {case['accept']}, got {actual}")
    if any(outcomes != {False, True} for outcomes in coverage.values()):
        raise AssertionError("Every profile needs both accepting and refusing cases")
    for name, profile in SOURCE_STARTS.items():
        if not grammars[profile].accepts(PROFILES[profile][1], source_body(HERE / name)):
            raise AssertionError(f"Source fixture failed: {name} as {profile}")
    print(
        f"PASS: {len(grammars)} profiles, {len(cases)} accept/refuse cases, "
        f"{len(SOURCE_STARTS)} declared source fixture"
    )
    if runtime:
        check_runtime(cases, grammars)
    print("Scope: retained syntax and declared parser checks. AuthorityEffect: None.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runtime", action="store_true", help="compare application parsers; needs pydantic"
    )
    main(parser.parse_args().runtime)
