"""Quiz 18: complete bounded rewrite graphs and explicitly retained originals.

Two fixed presentations; no silently installed completion rules, model calls,
or claim that a normal form alone reconstructs a lost input.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import deque
from pathlib import Path
from uuid import uuid4

PILOT_ID = "pilot_0000030"
MAX_WORD_BYTES = 32
MAX_STATES = 1024
ORIGINAL = (("ab_d", "ab", "d"), ("bc_e", "bc", "e"))
EXTENDED = ORIGINAL + (("dc_e", "dc", "e"), ("ae_e", "ae", "e"))


class InvalidInput(ValueError):
    """Malformed word, trace or retained-original record."""


def require(condition, message):
    if not condition:
        raise InvalidInput(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value):
    return hashlib.sha256(canonical(value).encode("ascii")).hexdigest()


def rules(presentation):
    require(presentation in ("original", "extended"), "Unknown presentation")
    return ORIGINAL if presentation == "original" else EXTENDED


def word(raw):
    require(type(raw) is bytes and len(raw) <= MAX_WORD_BYTES, "Word must be at most 32 raw bytes")
    require(all(c in b"abcde" for c in raw), "Use exactly ASCII alphabet a,b,c,d,e; no trimming")
    return raw.decode("ascii")


def steps(text, presentation):
    word(text.encode("ascii"))
    return [
        {"from": text, "to": text[:i] + right + text[i + len(left):], "rule": name, "offset": i}
        for name, left, right in rules(presentation)
        for i in range(len(text) - len(left) + 1) if text[i:i + len(left)] == left
    ]


def explore(raw, presentation, max_states=MAX_STATES):
    start = word(raw)
    selected = rules(presentation)
    require(type(max_states) is int and 1 <= max_states <= MAX_STATES, "State bound must be integer 1..1024")
    pending, seen, edges, normal = deque([start]), {start}, [], set()
    complete, cut_step = True, None
    while pending and complete:
        current = pending.popleft()
        outgoing = steps(current, presentation)
        if not outgoing:
            normal.add(current)
        for edge in outgoing:
            target = edge["to"]
            if target not in seen:
                if len(seen) >= max_states:
                    complete, cut_step = False, edge
                    break
                seen.add(target)
                pending.append(target)
            edges.append(edge)
    return {
        "presentation": presentation, "rules": [list(row) for row in selected],
        "presentation_sha256": digest(selected), "input_hex": raw.hex(),
        "input_sha256": hashlib.sha256(raw).hexdigest(), "protected_a_count": raw.count(b"a"),
        "states": sorted(seen), "steps": edges, "normal_forms": sorted(normal),
        "max_states": max_states, "complete": complete, "cut_step": cut_step,
        "unique_normal_form": len(normal) == 1 if complete else None,
        "global_confluence": "DISPROVED" if len(normal) > 1 else "NOT_CHECKED",
        "termination_basis": "Every admitted rule strictly reduces byte length",
        "rules_length_decreasing": all(len(right) < len(left) for _, left, right in selected),
    }


def replay(raw, trace, presentation):
    current = word(raw)
    rules(presentation)
    require(type(trace) is list and len(trace) <= MAX_WORD_BYTES, "Trace exceeds strictly decreasing length bound")
    for edge in trace:
        require(type(edge) is dict and set(edge) == {"from", "to", "rule", "offset"}, "Trace fields differ")
        require(type(edge["offset"]) is int, "Offset is an integer, not bool")
        require(edge["from"] == current and edge in steps(current, presentation), "Step is not admitted at this position")
        current = edge["to"]
    return current.encode("ascii")


def encode(raw, normal_form, presentation):
    word(raw)
    require(type(normal_form) is str, "Normal form must be text")
    word(normal_form.encode("ascii"))
    result = explore(raw, presentation)
    require(result["complete"], "Normal-form search is incomplete")
    require(normal_form in result["normal_forms"], "First component must be a reachable irreducible descendant")
    return {"presentation": presentation, "normal_form": normal_form,
            "original_hex": raw.hex(), "original_sha256": hashlib.sha256(raw).hexdigest()}


def decode(record):
    require(type(record) is dict and set(record) == {"presentation", "normal_form", "original_hex", "original_sha256"}, "Lossless record requires the retained original")
    raw_hex = record["original_hex"]
    require(type(raw_hex) is str and len(raw_hex) <= 2 * MAX_WORD_BYTES, "Original hex exceeds word bound")
    raw = bytes.fromhex(raw_hex)
    require(raw.hex() == raw_hex, "Use canonical lowercase hex without whitespace")
    expected = encode(raw, record["normal_form"], record["presentation"])
    require(record == expected, "Original digest or retained record differs")
    return raw


def exercise_report():
    original = explore(b"abc", "original")
    extended = explore(b"abc", "extended")
    other = explore(b"e", "extended")
    encoded = [encode(b"abc", "e", "extended"), encode(b"e", "e", "extended")]
    return {
        "pilot_id": PILOT_ID, "kind": "NO_LLM", "authority_effect": "None",
        "cases": {
            "quiz18.1": original,
            "quiz18.2": extended,
            "quiz18.3": {"left": extended, "right": other,
                        "same_normal_form": extended["normal_forms"] == other["normal_forms"] == ["e"],
                        "different_protected_counts": extended["protected_a_count"] != other["protected_a_count"],
                        "protected_query_descends": False},
            "quiz18.4": {"records": encoded, "decoded_hex": [decode(value).hex() for value in encoded],
                        "retained_original_required": True, "normal_form_alone_lossless": False},
        },
    }


def write_run(output_root, report, status, raw):
    folder = output_root / uuid4().hex
    folder.mkdir(parents=True, exist_ok=False)
    (folder / "input.bin").write_bytes(raw)
    receipt = {"pilot_id": PILOT_ID, "status": status, "network_calls": 0, "cost_usd": "0",
               "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "input_sha256": hashlib.sha256(raw).hexdigest(), "result_sha256": digest(report)}
    for name, payload in (("result.json", report), ("receipt.json", receipt)):
        with (folder / name).open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    with (folder / "summary.md").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(f"# {PILOT_ID}\n\nStatus: {status}.\n\nBounded rewrite exploration; original bytes remain separate from normal forms. No model call or rule installation.\n\nResult SHA-256: {receipt['result_sha256']}.\n")
    return folder


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Exact raw word bytes (requires --presentation)")
    parser.add_argument("--presentation", choices=("original", "extended"))
    parser.add_argument("--max-states", type=int, default=MAX_STATES)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent.parent / "pilot_output" / PILOT_ID)
    args = parser.parse_args(argv)
    try:
        require(bool(args.input) == bool(args.presentation), "Input and presentation must be supplied together")
        if args.input:
            with args.input.open("rb") as stream:
                raw = stream.read(MAX_WORD_BYTES + 1)
            checked = explore(raw, args.presentation, args.max_states)
            report = {"pilot_id": PILOT_ID, "kind": "NO_LLM", "authority_effect": "None", "exploration": checked}
            status = "COMPLETE" if checked["complete"] else "INCOMPLETE"
        else:
            require(args.max_states == MAX_STATES, "Custom state budget requires custom input")
            raw, report, status = canonical({"mode": "worked_exercises"}).encode("ascii"), exercise_report(), "COMPUTED"
        folder = write_run(args.output_dir, report, status, raw)
    except (InvalidInput, OSError, ValueError, TypeError) as error:
        print(json.dumps({"status": "REFUSED", "reason": str(error)}, ensure_ascii=True))
        return 2
    print(json.dumps({"status": status, "output": str(folder)}, ensure_ascii=True))
    return 1 if status == "INCOMPLETE" else 0


if __name__ == "__main__":
    sys.exit(main())

