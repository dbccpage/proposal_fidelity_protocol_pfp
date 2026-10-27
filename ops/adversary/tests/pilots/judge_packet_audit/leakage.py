"""Leakage lint: can a responder read the answer instead of computing it?

Four checks, each reported with the evidence that triggered it:

1. Case identifiers that contain a token of the case's own reference answer
   (a token that does not also occur in the case input), or a generic
   verdict word.
2. Answer-bearing fields in judge cases: fields named like ``type``,
   ``expected*``, ``note`` or ``label``, and whether their value shares a
   token with the reference answer that the rest of the input does not.
3. Judge cases whose input equals a participant example (identifier and
   descriptive fields removed before comparison).
4. Runner files whose prompt strings interpolate a case identifier or the
   case JSON, and inline runner cases whose identifiers carry verdict words.
"""

from __future__ import annotations

import ast
import json
import re
import warnings
from pathlib import Path
from typing import Any

ID_KEYS = ("id", "case_id")
DESCRIPTIVE_KEYS = (
    "description",
    "desc",
    "note",
    "notes",
    "category",
    "family",
    "label",
    "name",
    "title",
    "comment",
)
FLAGGED_FIELD = re.compile(
    r"^(type|note|notes|label|class|verdict|status|category|ground_truth|description|desc)$|^(expected|answer|solution)"
)
VERDICT_WORDS = frozenset(
    {
        "solved",
        "unknown",
        "refusal",
        "refuse",
        "refused",
        "oos",
        "infeas",
        "infeasible",
        "feasible",
        "unbounded",
        "optimal",
        "unsat",
        "sat",
        "eq",
        "neq",
        "equal",
        "unequal",
        "obstructed",
        "extends",
        "trivial",
        "nontrivial",
        "valid",
        "invalid",
        "exists",
        "impossible",
        "accept",
        "reject",
    }
)
CATEGORY_HINTS = frozenset(
    {"poison", "poisoned", "corrupt", "corrupted", "fake", "trap", "deceptive", "bogus", "spoof"}
)
TOKEN_SPLIT = re.compile(r"[^A-Za-z0-9]+")
NUMERIC = re.compile(r"^-?\d+(/\d+)?$")


def id_tokens(identifier: str) -> list[str]:
    return [t.lower() for t in TOKEN_SPLIT.split(identifier) if len(t) >= 2 and not t.isdigit()]


def value_tokens(value: Any, skip_keys: tuple[str, ...] = ID_KEYS) -> set[str]:
    out: set[str] = set()

    def walk(v: Any) -> None:
        if isinstance(v, dict):
            for k, x in v.items():
                if k in skip_keys:
                    continue
                for t in TOKEN_SPLIT.split(str(k)):
                    if len(t) >= 3 and not t.isdigit():
                        out.add(t.lower())
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
        elif isinstance(v, str) and not NUMERIC.match(v):
            for t in TOKEN_SPLIT.split(v):
                if len(t) >= 2 and not t.isdigit():
                    out.add(t.lower())

    walk(value)
    return out


def case_id_leak(
    case_id: str | None, case: Any, answer_tokens: list[str] | None
) -> dict[str, Any] | None:
    if not case_id:
        return None
    tokens = set(id_tokens(case_id))
    input_tokens = value_tokens(case, skip_keys=ID_KEYS + DESCRIPTIVE_KEYS)
    own = sorted((tokens & set(answer_tokens or [])) - input_tokens)
    return {
        "names_own_answer": own,
        "verdict_words": sorted(tokens & VERDICT_WORDS),
        "category_hints": sorted(tokens & CATEGORY_HINTS),
    }


def flagged_fields(case: Any, answer_tokens: list[str] | None) -> list[dict[str, Any]]:
    if not isinstance(case, dict):
        return []
    out = []
    answer = set(answer_tokens or [])
    for key in sorted(case):
        if key in ID_KEYS or not FLAGGED_FIELD.search(key):
            continue
        rest = {k: v for k, v in case.items() if k != key}
        rest_tokens = value_tokens(rest, skip_keys=ID_KEYS + DESCRIPTIVE_KEYS)
        field_tokens = value_tokens({key: case[key]}) - set(TOKEN_SPLIT.split(key.lower()))
        shared = sorted((field_tokens & answer) - rest_tokens)
        out.append(
            {
                "field": key,
                "value_shares_answer_tokens": shared,
                "named_answer_field": bool(re.match(r"^(expected|answer|solution)", key)),
            }
        )
    return out


def normalized_input(case: Any) -> str:
    if isinstance(case, dict):
        body = {k: v for k, v in case.items() if k not in ID_KEYS + DESCRIPTIVE_KEYS}
    else:
        body = case
    return json.dumps(body, sort_keys=True, ensure_ascii=False)


def example_duplicates(
    cases: list[tuple[str, Any]], examples: list[tuple[str, Any, bool]]
) -> list[dict[str, Any]]:
    """Judge cases whose normalized input equals a participant example input.

    ``examples`` holds (path, input, has_expected_output).
    """
    by_body: dict[str, list[tuple[str, bool]]] = {}
    for path, example_input, has_output in examples:
        by_body.setdefault(normalized_input(example_input), []).append((path, has_output))
    out = []
    for key, case in cases:
        hits = by_body.get(normalized_input(case))
        if hits:
            out.append(
                {
                    "case": key,
                    "examples": sorted(p for p, _ in hits),
                    "example_ships_answer": any(h for _, h in hits),
                }
            )
    return out


def _expr_text(node: ast.AST, source: str) -> str:
    return ast.get_source_segment(source, node) or ""


PROMPT_NAME = re.compile(r"prompt|user_msg|user_message|message_text", re.IGNORECASE)


def _prompt_sites(tree: ast.Module) -> list[ast.AST]:
    """Subtrees that build prompt text.

    Functions whose name mentions a prompt, assignments to a prompt-like
    name, and the value of a ``"content"`` key in a message dictionary.
    """
    sites: list[ast.AST] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and PROMPT_NAME.search(
            node.name
        ):
            sites.append(node)
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            names = [t.id for t in targets if isinstance(t, ast.Name)]
            if node.value is not None and any(PROMPT_NAME.search(n) for n in names):
                sites.append(node.value)
        elif isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if isinstance(key, ast.Constant) and key.value == "content":
                    sites.append(value)
    return sites


def _assignments(tree: ast.Module, source: str) -> dict[str, str]:
    """Last source text assigned to each simple name (one level of dataflow)."""
    out: dict[str, str] = {}
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            out[node.targets[0].id] = _expr_text(node.value, source)
    return out


def runner_lint(
    path: Path, answer_vocabulary: set[str], *, inline_cases: bool = True
) -> dict[str, Any]:
    """Prompt interpolations of case identifiers or case JSON, and inline runner cases."""
    source = path.read_text(encoding="utf-8")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            tree = ast.parse(source)
    except SyntaxError:
        return {"parse_error": True}
    assigned = _assignments(tree, source)
    interpolations: list[dict[str, Any]] = []
    seen: set[tuple[int, int]] = set()
    for site in _prompt_sites(tree):
        for node in ast.walk(site):
            parts: list[ast.AST] = []
            if isinstance(node, ast.JoinedStr):
                parts = [v.value for v in node.values if isinstance(v, ast.FormattedValue)]
            elif (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "format"
            ):
                parts = [*node.args, *[k.value for k in node.keywords]]
            if not parts or (node.lineno, node.col_offset) in seen:
                continue
            seen.add((node.lineno, node.col_offset))
            kinds: set[str] = set()
            for part in parts:
                text = _expr_text(part, source)
                if isinstance(part, ast.Name) and part.id in assigned:
                    text = f"{text} {assigned[part.id]}"
                kinds |= _interpolation_kinds(part, text)
            if kinds:
                interpolations.append({"line": node.lineno, "kinds": sorted(kinds)})
    cases_found = []
    for node in ast.walk(tree) if inline_cases else []:
        if not isinstance(node, ast.Dict):
            continue
        keys = {
            k.value: v
            for k, v in zip(node.keys, node.values)
            if isinstance(k, ast.Constant) and isinstance(k.value, str)
        }
        id_node = keys.get("case_id") or keys.get("id")
        if not (isinstance(id_node, ast.Constant) and isinstance(id_node.value, str)):
            continue
        identifier = id_node.value
        if "<" in identifier or not re.search(r"[A-Za-z]", identifier):
            continue
        tokens = set(id_tokens(identifier))
        cases_found.append(
            {
                "line": node.lineno,
                "case_id": identifier,
                "verdict_words": sorted(tokens & VERDICT_WORDS),
                "category_hints": sorted(tokens & CATEGORY_HINTS),
                "answer_vocabulary_words": sorted(tokens & answer_vocabulary),
                "answer_bearing_fields": sorted(
                    k
                    for k in keys
                    if re.match(r"^(expected|answer|solution|note|type|label|verdict)", k)
                ),
            }
        )
    return {
        "prompt_sites": len(_prompt_sites(tree)),
        "prompt_interpolations": sorted(interpolations, key=lambda x: x["line"]),
        "inline_cases": cases_found,
    }


def _interpolation_kinds(node: ast.AST, text: str) -> set[str]:
    kinds = set()
    compact = text.replace(" ", "")
    if re.search(r"case_id|\[['\"]id['\"]\]|\.get\(['\"]id['\"]|\bcid\b", compact):
        kinds.add("case_id")
    if re.search(
        r"json\.dumps\((case|c|task|inp|problem|instance|payload|item|case_data|case_input)\b",
        compact,
    ):
        kinds.add("case_json")
    if re.search(r"\[['\"]note['\"]\]|\.get\(['\"]note['\"]|\bnote\b", compact):
        kinds.add("note")
    if re.search(r"expected", compact):
        kinds.add("expected_field")
    if re.search(r"\[['\"]type['\"]\]|\.get\(['\"]type['\"]", compact):
        kinds.add("type_field")
    return kinds


def answers_file_overlap(path: Path, judge_ids: set[str], example_ids: set[str]) -> dict[str, Any]:
    ids = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict):
            for key in ID_KEYS:
                if isinstance(row.get(key), str):
                    ids.append(row[key])
                    break
    return {
        "lines_with_id": len(ids),
        "ids_matching_judge_cases": sorted(set(ids) & judge_ids),
        "ids_matching_examples": len(set(ids) & example_ids),
    }
