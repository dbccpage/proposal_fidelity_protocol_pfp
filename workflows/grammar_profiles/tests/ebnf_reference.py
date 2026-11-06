"""Independent EBNF subset oracle, retained from PFP grammar/check_grammars.py.

Only the existing tokenizer and Grammar class are retained; no runtime adapters.
"""
import json
import re
from functools import lru_cache

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
