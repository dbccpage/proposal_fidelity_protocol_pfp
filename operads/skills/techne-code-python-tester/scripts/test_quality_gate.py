#!/usr/bin/env python3
"""Reject mechanically weak Python tests using the standard-library AST.

This gate is intentionally narrow. Passing it means only that the scanned tests
avoid the encoded anti-patterns; it does not certify behavioral adequacy.
AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import ast
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    code: str
    detail: str


def _is_bool_constant(node: ast.AST, expected: bool) -> bool:
    """Is `node` the literal `True`/`False` — not `1`, not any truthy constant?

    The `isinstance(..., bool)` guard is what makes this exact: `1 == True` in
    Python, so an equality test alone would call `assert 1` a weak assertion
    against `True`. Spelled this way rather than `node.value is True` so the
    gate's own EXPLICIT_BOOLEAN_COMPARISON rule stays clean.
    """
    return (
        isinstance(node, ast.Constant) and isinstance(node.value, bool) and node.value == expected
    )


def _is_true(node: ast.AST) -> bool:
    return _is_bool_constant(node, True)


def _is_false(node: ast.AST) -> bool:
    return _is_bool_constant(node, False)


def _assert_is_weak(node: ast.Assert) -> bool:
    if _is_true(node.test):
        return True
    if isinstance(node.test, ast.BoolOp) and isinstance(node.test.op, ast.Or):
        return any(_is_true(value) for value in node.test.values)
    return False


def _is_assert_false(node: ast.Assert) -> bool:
    return _is_false(node.test)


def _is_assert_on_tuple(node: ast.Assert) -> bool:
    """True when assertion test is a non-empty tuple (e.g. `assert (x, 'msg')`)."""
    return isinstance(node.test, ast.Tuple) and len(node.test.elts) > 0


def _is_assert_on_string(node: ast.Assert) -> bool:
    """True when assertion test is a string literal (e.g. `assert 'message'`)."""
    return isinstance(node.test, ast.Constant) and isinstance(node.test.value, str)


def _is_tautology_eq(node: ast.Assert) -> bool:
    """True when the assertion is `assert <literal> == <same literal>`."""
    test = node.test
    if not isinstance(test, ast.Compare):
        return False
    if len(test.ops) != 1 or not isinstance(test.ops[0], ast.Eq):
        return False
    if len(test.comparators) != 1:
        return False
    left = test.left
    right = test.comparators[0]
    if not isinstance(left, ast.Constant) or not isinstance(right, ast.Constant):
        return False
    return left.value == right.value


def _is_len_call(node: ast.AST) -> bool:
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "len"


def _get_constant_int(node: ast.AST) -> int | None:
    if (
        isinstance(node, ast.Constant)
        and isinstance(node.value, int)
        and not isinstance(node.value, bool)
    ):
        return node.value
    if (
        isinstance(node, ast.UnaryOp)
        and isinstance(node.op, ast.USub)
        and isinstance(node.operand, ast.Constant)
        and isinstance(node.operand.value, int)
        and not isinstance(node.operand.value, bool)
    ):
        return -node.operand.value
    return None


def _is_weak_len(node: ast.Assert) -> bool:
    """True when asserting always-true length bounds (e.g. len >= 0, len > -1, len >= -5)."""
    test = node.test
    if not isinstance(test, ast.Compare):
        return False
    if len(test.ops) != 1 or len(test.comparators) != 1:
        return False
    op = test.ops[0]
    left = test.left
    right = test.comparators[0]

    # len(x) >= c (c <= 0) or len(x) > c (c < 0)
    if _is_len_call(left):
        val = _get_constant_int(right)
        if val is not None:
            if isinstance(op, ast.GtE) and val <= 0:
                return True
            if isinstance(op, ast.Gt) and val < 0:
                return True

    # c <= len(x) (c <= 0) or c < len(x) (c < 0)
    if _is_len_call(right):
        val = _get_constant_int(left)
        if val is not None:
            if isinstance(op, ast.LtE) and val <= 0:
                return True
            if isinstance(op, ast.Lt) and val < 0:
                return True

    return False


def _test_body_is_empty(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    body = list(node.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        if isinstance(body[0].value.value, str):
            body = body[1:]
    return not body or all(isinstance(item, ast.Pass) for item in body)


def _test_has_no_assertions(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for child in ast.walk(node):
        if child is node:
            continue
        if isinstance(child, ast.Assert):
            return False
        if isinstance(child, ast.Call):
            # pytest.raises
            if isinstance(child.func, ast.Attribute) and child.func.attr == "raises":
                return False
            if isinstance(child.func, ast.Name) and child.func.id == "raises":
                return False
            # unittest self.assert* or pytest.fail
            if isinstance(child.func, ast.Attribute) and (
                child.func.attr.startswith("assert") or child.func.attr == "fail"
            ):
                return False
            if isinstance(child.func, ast.Name) and (
                child.func.id.startswith("assert") or child.func.id == "fail"
            ):
                return False
    return True


def _is_sys_path_hack(node: ast.Call) -> bool:
    if isinstance(node.func, ast.Attribute) and node.func.attr in ("insert", "append"):
        value = node.func.value
        if isinstance(value, ast.Attribute) and value.attr == "path":
            if isinstance(value.value, ast.Name) and value.value.id == "sys":
                return True
    return False


def _is_bare_raises(node: ast.Call) -> bool:
    is_pytest_raises = False
    if isinstance(node.func, ast.Attribute) and node.func.attr == "raises":
        if isinstance(node.func.value, ast.Name) and node.func.value.id == "pytest":
            is_pytest_raises = True
    elif isinstance(node.func, ast.Name) and node.func.id == "raises":
        is_pytest_raises = True

    if not is_pytest_raises:
        return False

    if node.args:
        first_arg = node.args[0]
        if isinstance(first_arg, ast.Name) and first_arg.id in ("Exception", "BaseException"):
            has_match = any(kw.arg == "match" and kw.value is not None for kw in node.keywords)
            return not has_match
    return False


def scan_file(path: Path) -> list[Finding]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, UnicodeError, SyntaxError) as err:
        line = getattr(err, "lineno", 0) or 0
        return [Finding(str(path), line, "UNPARSEABLE_TEST", str(err))]
    findings: list[Finding] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assert):
            if _is_assert_false(node):
                findings.append(
                    Finding(
                        str(path),
                        node.lineno,
                        "ASSERT_FALSE",
                        "assert False used; prefer pytest.fail('reason') or self.fail('reason')",
                    )
                )
            elif _assert_is_weak(node):
                findings.append(
                    Finding(
                        str(path),
                        node.lineno,
                        "WEAK_ASSERTION",
                        "assertion is constant-true or contains `or True`",
                    )
                )
            elif _is_assert_on_tuple(node):
                findings.append(
                    Finding(
                        str(path),
                        node.lineno,
                        "ASSERT_ON_TUPLE",
                        "assert on non-empty tuple is always truthy (e.g. `assert (x, 'msg')`)",
                    )
                )
            elif _is_assert_on_string(node):
                findings.append(
                    Finding(
                        str(path),
                        node.lineno,
                        "ASSERT_ON_STRING",
                        "assertion on string literal is always truthy (e.g. `assert 'message'`)",
                    )
                )
            elif _is_tautology_eq(node):
                findings.append(
                    Finding(
                        str(path),
                        node.lineno,
                        "TAUTOLOGY_EQ",
                        "assertion compares two equal literals (constant tautology)",
                    )
                )
            elif _is_weak_len(node):
                findings.append(
                    Finding(
                        str(path),
                        node.lineno,
                        "WEAK_LEN",
                        "assertion tests trivial length condition (e.g. len >= 0, len > -1)",
                    )
                )

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith(
            "test_"
        ):
            if _test_body_is_empty(node):
                findings.append(Finding(str(path), node.lineno, "EMPTY_TEST", node.name))
            elif _test_has_no_assertions(node):
                findings.append(
                    Finding(
                        str(path),
                        node.lineno,
                        "NO_ASSERTION",
                        f"test function '{node.name}' contains no assert or raises",
                    )
                )

        if isinstance(node, ast.Call):
            if _is_sys_path_hack(node):
                findings.append(
                    Finding(
                        str(path),
                        node.lineno,
                        "SYS_PATH_HACK",
                        "sys.path.insert or sys.path.append used in test file",
                    )
                )
            elif _is_bare_raises(node):
                findings.append(
                    Finding(
                        str(path),
                        node.lineno,
                        "BARE_RAISES",
                        "pytest.raises(Exception/BaseException) without match= parameter",
                    )
                )

    return sorted(findings, key=lambda row: (row.path, row.line, row.code))


def iter_test_files(paths: Iterable[Path]) -> list[Path]:
    files: set[Path] = set()
    for path in paths:
        if path.is_file() and path.suffix == ".py":
            files.add(path)
        elif path.is_dir():
            files.update(candidate for candidate in path.rglob("test_*.py") if candidate.is_file())
            files.update(candidate for candidate in path.rglob("*_test.py") if candidate.is_file())
    return sorted(files)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    files = iter_test_files(args.paths)
    findings = [finding for path in files for finding in scan_file(path)]
    result = {
        "schema": "omega.python_test_quality.v1",
        "files_scanned": len(files),
        "findings": [asdict(finding) for finding in findings],
        "authority_effect": "None",
    }
    if args.as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for finding in findings:
            print(f"{finding.path}:{finding.line}: {finding.code}: {finding.detail}")
        print(f"files_scanned={len(files)} findings={len(findings)}")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
