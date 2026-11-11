"""Shared public helpers: code extraction, AST checks, and the jailed runner (``sandbox``).

Nothing here reads the sealed evaluator. Candidate code is never imported
into the host process.
"""
from __future__ import annotations

import ast
import re

_FENCE = re.compile(r'```(?:python|py)?[ \t]*\n(.*?)```', re.S)


def extract_code(text: str) -> str:
    """Public normalizer: the longest fenced Python block, else the whole text."""
    blocks = _FENCE.findall(text)
    return max(blocks, key=len) if blocks else text


def parses(code: str) -> str | None:
    """None when ``code`` parses, else a short error label."""
    try:
        ast.parse(code)
    except SyntaxError as exc:
        return f'SyntaxError line {exc.lineno}'
    return None


def signatures(code: str, names: tuple[str, ...]) -> dict[str, str]:
    """``name -> ast.dump(arguments, returns)`` for top-level functions in ``names``."""
    out = {}
    for node in ast.parse(code).body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            out[node.name] = ast.dump(node.args) + '->' + (ast.dump(node.returns) if node.returns else '')
    return out


from .sandbox import clear_cache, prewarm, run_isolated  # noqa: E402,F401

SMOKE_DRIVER_HEAD = '''
try:
    import candidate
except BaseException as exc:
    emit({"error": "import failed: " + type(exc).__name__})
    raise SystemExit(0)
'''
