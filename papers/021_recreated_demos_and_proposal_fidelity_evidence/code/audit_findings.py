"""Replay the findings inventory's source and physical-span bindings."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from source_custody import CustodyError, _json, _read_regular, sha256


def audit(paper: Path, source_repo: Path, expected_inventory_sha256: str) -> dict:
    raw = _read_regular(paper, "docs/findings_demo_inventory.json")
    if sha256(raw) != expected_inventory_sha256:
        raise CustodyError("findings inventory differs from trusted pin")
    inventory = _json(raw)
    notes = inventory["source_notes"]
    if len(notes) != 20 or len({note["path"] for note in notes}) != 20:
        raise CustodyError("twenty-note inventory is not complete and unique")
    if len(inventory["challenges"]) != 60 or {row["id"] for row in inventory["challenges"]} != {
        f"C{number:03}" for number in range(1, 61)
    }:
        raise CustodyError("C001-C060 coverage differs")
    if len(inventory["genesis_challenges"]) != 25 or {
        row["id"] for row in inventory["genesis_challenges"]
    } != {f"G{number:02}" for number in range(1, 26)}:
        raise CustodyError("G01-G25 coverage differs")
    if len({row["id"] for row in inventory["aggregate_demo_families"]}) != 13:
        raise CustodyError("aggregate-family coverage differs")

    note_bytes = {}
    bindings = 0
    total_bytes = 0
    for note in notes:
        data = _read_regular(source_repo, note["path"])
        if sha256(data) != note["sha256"] or len(data) != note["size_bytes"]:
            raise CustodyError(f"note bytes differ: {note['path']}")
        lines = data.splitlines(keepends=True)
        if len(lines) != note["line_count"]:
            raise CustodyError("physical line count differs")
        total_bytes += len(data)
        note_bytes[note["path"]] = (note["sha256"], lines)
        for section in note["sections"]:
            start, end = section["start_line"], section["end_line"]
            if (
                type(start) is not int
                or type(end) is not int
                or not 1 <= start <= end <= len(lines)
            ):
                raise CustodyError("invalid section span")
            if sha256(b"".join(lines[start - 1 : end])) != section["section_sha256"]:
                raise CustodyError("physical section digest differs")
            bindings += 1

    checked_sources = {}

    def visit(node):
        nonlocal bindings
        if type(node) is dict:
            if "note_path" in node and "line_sha256" in node:
                digest, lines = note_bytes[node["note_path"]]
                number = node["line"]
                if (
                    node["note_sha256"] != digest
                    or type(number) is not int
                    or not 1 <= number <= len(lines)
                ):
                    raise CustodyError("invalid source-line binding")
                if sha256(lines[number - 1]) != node["line_sha256"]:
                    raise CustodyError("physical source-line digest differs")
                bindings += 1
            if node.get("availability") == "PRESENT" and "path" in node and "sha256" in node:
                path = node["path"]
                if path not in checked_sources:
                    checked_sources[path] = _read_regular(source_repo, path)
                data = checked_sources[path]
                if sha256(data) != node["sha256"]:
                    raise CustodyError(f"referenced source digest differs: {path}")
                if "size_bytes" in node and len(data) != node["size_bytes"]:
                    raise CustodyError("referenced source size differs")
            for value in node.values():
                visit(value)
        elif type(node) is list:
            for value in node:
                visit(value)

    visit(inventory)
    if total_bytes != inventory["source_snapshot"]["note_bytes_total"]:
        raise CustodyError("source-note byte total differs")
    return {
        "schema_version": "paper011.findings-audit.v1",
        "status": "VERIFIED_SOURCE_BINDINGS",
        "auditor_sha256": sha256(Path(__file__).read_bytes()),
        "inventory_sha256": expected_inventory_sha256,
        "source_git_head": inventory["source_snapshot"]["git_head"],
        "notes": len(notes),
        "note_bytes": total_bytes,
        "section_and_line_bindings": bindings,
        "referenced_source_files": len(checked_sources),
        "challenge_ids": 60,
        "genesis_ids": 25,
        "aggregate_families": 13,
        "execution_claim": "NONE_SOURCE_AUDIT_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-repo", type=Path, required=True)
    parser.add_argument("--inventory-sha256", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(
        Path(__file__).absolute().parents[1], args.source_repo.absolute(), args.inventory_sha256
    )
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
