"""Quiz 15: bounded byte-exact recognition of four declared syntax profiles.

Syntax acceptance does not check interpretation, opcode activation or authority.
The recognizers use ASCII, <=65536 bytes, <=4096 nodes and depth<=64.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from uuid import uuid4

PILOT_ID = "pilot_0000028"
PROFILES = ("mss-boundary-v1", "quiz-packet-v1", "glyph-graph-v1", "historical-packet-v1")
MAX_BYTES = 65536
MAX_NODES = 4096
MAX_DEPTH = 64


class InvalidInput(ValueError):
    pass


class LimitExceeded(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise InvalidInput(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


class Parser:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.nodes = 0

    def enter(self, depth):
        self.nodes += 1
        if depth > MAX_DEPTH or self.nodes > MAX_NODES:
            raise LimitExceeded("Declared depth/node limit exceeded")

    def starts(self, token):
        return self.text.startswith(token, self.pos)

    def take(self, token):
        require(self.starts(token), f"Expected {token!r} at offset {self.pos}")
        self.pos += len(token)

    def word(self, underscore=False):
        match = re.compile(r"[a-z0-9_]+" if underscore else r"[a-z0-9]+").match(self.text, self.pos)
        require(match is not None, f"Expected word at offset {self.pos}")
        self.pos = match.end()
        return match.group()

    def leaf(self):
        self.take("<")
        if self.starts(">"):
            self.take(">")
            return {"kind": "difference"}
        word = self.word()
        self.take(">")
        return {"kind": "atom", "value": word}

    def boundary(self, depth=0):
        self.enter(depth)
        if not self.starts("<<"):
            return self.leaf()
        self.take("<")
        children = [self.boundary(depth + 1)]
        while not self.starts(">"):
            children.append(self.boundary(depth + 1))
        self.take(">")
        return {"kind": "composite", "children": children}

    def historical(self, depth=0):
        self.enter(depth)
        if not self.starts("op<"):
            return self.leaf()
        self.take("op<")
        children = []
        while not self.starts(">"):
            children.append(self.historical(depth + 1))
        self.take(">")
        return {"kind": "application", "children": children}

    def quiz_item(self, depth):
        self.enter(depth)
        if self.starts("<"):
            self.take("<")
            children = [] if self.starts(">") else self.items(depth + 1)
            self.take(">")
            return {"kind": "packet", "children": children}
        word = self.word(underscore=True)
        if not self.starts("<"):
            return {"kind": "word", "value": word}
        self.take("<")
        children = [] if self.starts(">") else self.items(depth + 1)
        self.take(">")
        return {"kind": "tag", "value": word, "children": children}

    def items(self, depth):
        children = [self.quiz_item(depth)]
        while self.starts(","):
            self.take(",")
            children.append(self.quiz_item(depth))
        return children

    def quiz(self):
        self.enter(0)
        if self.starts("ref<"):
            self.take("ref<")
            code = self.word()
            require(code in ("1", "2", "3", "4", "5", "6"), "Unknown educational refusal code")
            self.take(">")
            return {"kind": "refusal_code", "value": code}
        head = self.word()
        require(head in ("ask", "ans"), "Expected ask, ans or ref")
        self.take("<")
        children = self.items(1)
        self.take(">")
        return {"kind": "message", "value": head, "children": children}

    def graph(self):
        self.enter(0)
        nodes = []
        for item in self.text.split("<>"):
            self.enter(1)
            match = re.fullmatch(r"([a-z0-9])(?:([<>])([a-z0-9])([a-z][0-9])?)?", item)
            require(match is not None, "Malformed or empty graph item")
            left, direction, right, weight = match.groups()
            if direction is None:
                nodes.append({"kind": "vertex", "value": left})
            else:
                source, target = (left, right) if direction == ">" else (right, left)
                nodes.append({"kind": "edge", "source": source, "target": target, "direction": direction, "spelling": item, "weight_suffix": weight})
        self.pos = len(self.text)
        return {"kind": "graph", "items": nodes}


def parse(raw, profile):
    require(type(raw) is bytes, "Input must be bytes")
    require(profile in PROFILES, "Unknown profile")
    if len(raw) > MAX_BYTES:
        raise LimitExceeded("Declared byte limit exceeded")
    text = raw.decode("ascii")
    parser = Parser(text)
    method = dict(zip(PROFILES, ("boundary", "quiz", "graph", "historical"), strict=True))[profile]
    ast = getattr(parser, method)()
    require(parser.pos == len(text), "Trailing bytes after the single root")
    return ast


def inspect(raw, profile):
    require(type(raw) is bytes, "Input must be bytes")
    result = {"profile": profile, "raw_hex": raw.hex(), "raw_sha256": sha(raw),
              "interpretation": "NOT_CHECKED", "authority_effect": "None"}
    try:
        result["ast"] = parse(raw, profile)
        result["status"] = "ACCEPTED"
    except LimitExceeded as error:
        result.update(status="LIMIT_EXCEEDED", reason=str(error))
    except (InvalidInput, UnicodeError) as error:
        result.update(status="REFUSED", reason=str(error))
    return result


def repair_record(original, proposed, profile):
    return {"original": inspect(original, profile), "proposed": inspect(proposed, profile),
            "same_bytes": original == proposed, "applied": False}


def seal_record(digest_text, artifact=None):
    require(type(digest_text) is str, "Digest must be a string")
    require(artifact is None or type(artifact) is bytes, "Artifact must be bytes")
    shape = re.fullmatch(r"[0-9a-f]{64}", digest_text) is not None
    binding = "NOT_CHECKED" if artifact is None else (
        "MATCH" if shape and sha(artifact) == digest_text else "MISMATCH")
    return {"digest": digest_text, "lexical_shape_matches": shape, "artifact_binding": binding,
            "semantic_claims": "NOT_CHECKED", "authority_effect": "None"}


def exercise_report():
    inputs = (b"<>", b"<ab>", b"<<a><b>>", b"ans<edge<a,b>>", b"a>b", b"<a><b>")
    nested = b"op<<10>op<<1><a>>op<<1><b>>>"
    valid_seal = sha(b"<>")
    return {"pilot_id": PILOT_ID, "kind": "NO_LLM", "cases": {
        "quiz15.1": [inspect(raw, profile) for raw in inputs for profile in PROFILES[:3]]
                     + [inspect(b"a>b<>", "glyph-graph-v1")],
        "quiz15.2": [repair_record(raw, b"<a>", "mss-boundary-v1")
                     for raw in (b" <a>", b"<a>\n", b"<a b>", b"<a><b>")],
        "quiz15.3": {
            "original": inspect(nested, "historical-packet-v1"),
            "renamed_first_atom": inspect(nested.replace(b"<10>", b"<foo>"), "historical-packet-v1"),
            "trailing_root": inspect(nested + b"<>", "historical-packet-v1"),
        },
        "quiz15.4": {"shape_only": seal_record(valid_seal),
                     "invalid_shape": seal_record("g" + valid_seal[1:]),
                     "bound_bytes": seal_record(valid_seal, b"<>"),
                     "wrong_bytes": seal_record(valid_seal, b"<a>")},
    }}


def write_run(root, report, raw):
    folder = root / uuid4().hex
    folder.mkdir(parents=True, exist_ok=False)
    (folder / "input.bin").write_bytes(raw)
    receipt = {"pilot_id": PILOT_ID, "code_sha256": sha(Path(__file__).read_bytes()),
               "input_sha256": sha(raw), "result_sha256": sha(canonical(report)),
               "network_calls": 0, "cost_usd": "0"}
    for name, payload in (("result.json", report), ("receipt.json", receipt)):
        with (folder / name).open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    with (folder / "summary.md").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(f"# {PILOT_ID}\n\nBounded syntax recognition only; no semantic or authority promotion.\n\nResult SHA-256: {receipt['result_sha256']}.\n")
    return folder


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Raw packet bytes, not JSON")
    parser.add_argument("--profile", choices=PROFILES)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent.parent / "pilot_output" / PILOT_ID)
    args = parser.parse_args(argv)
    try:
        require(bool(args.input) == bool(args.profile), "Supply both --input and --profile")
        if args.input:
            with args.input.open("rb") as stream:
                raw = stream.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise LimitExceeded("Input file exceeds the byte limit; no truncated custody record")
            report = {"pilot_id": PILOT_ID, "kind": "NO_LLM", "inspection": inspect(raw, args.profile)}
            status = report["inspection"]["status"]
        else:
            raw = canonical({"mode": "worked_exercises"})
            report = exercise_report()
            status = "COMPUTED"
        folder = write_run(args.output_dir, report, raw)
    except (OSError, InvalidInput, LimitExceeded) as error:
        print(json.dumps({"status": "REFUSED", "reason": str(error)}, ensure_ascii=True))
        return 2
    print(json.dumps({"status": status, "output": str(folder)}, ensure_ascii=True))
    return 0 if status in ("COMPUTED", "ACCEPTED") else 1


if __name__ == "__main__":
    sys.exit(main())
