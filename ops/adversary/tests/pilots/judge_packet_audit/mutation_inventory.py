"""Mutation-suite inventory: size and number of distinct payloads."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

META_KEYS = frozenset(
    {
        "id",
        "mutation_id",
        "mut_id",
        "description",
        "desc",
        "explanation",
        "type",
        "mutation_type",
        "reason",
        "expected_rejection",
        "rejection_message",
        "kill_verified",
        "eval_verdict",
        "checker1",
        "checker2",
        "exact_checker_rejection",
        "independent_checker_rejection",
        "name",
    }
)


def _canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def inventory(
    pkg_dir: Path, entries: list[dict[str, Any]], other_files: list[str]
) -> dict[str, Any]:
    """Counts mutation entries and distinct (case, answer) payloads, metadata removed."""
    cache: dict[str, Any] = {}
    pairs: set[str] = set()
    answers: set[str] = set()
    files: set[str] = set()
    for entry in entries:
        path = pkg_dir / entry["path"]
        files.add(entry["path"])
        if entry["path"] not in cache:
            cache[entry["path"]] = json.loads(path.read_text(encoding="utf-8"))
        data = cache[entry["path"]]
        if entry["index"] is None:
            item = data
        elif isinstance(data, dict):
            item = data["mutations"][entry["index"]]
        else:
            item = data[entry["index"]]
        case = item[entry["case_key"]]
        answer = item[entry["answer_key"]]
        pairs.add(_canon({"case": case, "answer": answer}))
        answers.add(_canon(answer))
    return {
        "entries": len(entries),
        "files": len(files),
        "distinct_case_answer_pairs": len(pairs),
        "distinct_answers": len(answers),
        "duplicate_entries": len(entries) - len(pairs),
        "non_mutation_files_in_mutation_dirs": sorted(other_files, key=lambda s: s.encode("utf-8")),
    }
