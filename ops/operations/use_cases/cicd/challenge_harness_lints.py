#!/usr/bin/env python3
"""Ratchet lints for challenge judge packets, provider calls, prompts and run custody.

AuthorityEffect: None. The lints report findings; they establish no standing.

Five static, deterministic checks (standard library only, no imports of the
code they inspect). Each compares its findings with the checked-in baseline of
the violations that existed when the lint was introduced
(``challenge_harness_lints_baseline.json``) and fails only on findings that are
new or more frequent than the baseline records. Finding keys carry no line
numbers, so unrelated edits do not churn the baseline. Burn the baseline down;
do not add to it.

  import_boundary       Nothing under a ``judge_packet/`` directory imports a
                        ``reference_solver`` module or calls ``ref_solve``, and
                        no checker module (``*checker.py``) imports another one.
                        Findings are keyed per imported name; dynamic loading
                        (``importlib.import_module``, ``__import__`` and similar)
                        and non-docstring string literals naming
                        ``reference_solver`` are findings too.
  provider_path         Outside ``providers/`` no code names the
                        raw OpenRouter host, loads a dotenv file, or constructs
                        the OpenRouter backend directly.
  prompt_leak           Prompt builders (build_/format_/make_... *prompt*
                        functions, and assignments to prompt/message variables)
                        do not interpolate a case identifier, serialise a whole
                        case, or read expected*/note/type/answer fields; judge
                        case identifiers carry no verdict words; judge cases do
                        not duplicate participant examples.
  run_roots             Non-test code does not reach an ``_intelligence`` path
                        through ``parents[N]`` or ``.parent.parent`` arithmetic;
                        use ``resolve_intelligence_repo_root()`` instead.
  canonical_json_claim  No code in this repository implements the RFC 8785 JSON
                        canonicalization scheme, so no file may claim it (nor
                        JCS). A line that says the scheme is not implemented
                        (it contains not/no/never/without) is not a claim. If a
                        real implementation is ever added, name it here as the
                        one designated encoder and exempt its callers.

Usage:
    python operations/use_cases/cicd/challenge_harness_lints.py \
        --lint import_boundary --repo-root .
    ... --lint all --report            # print every finding, fail on new ones
    ... --lint all --write-baseline    # maintainers only; never used by a gate

Exit status: 0 no new findings, 1 new findings, 2 usage or baseline error.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

LINT_NAMES: tuple[str, ...] = (
    "import_boundary",
    "provider_path",
    "prompt_leak",
    "run_roots",
    "canonical_json_claim",
)
BASELINE_NAME = "challenge_harness_lints_baseline.json"
# Totals at introduction. A baseline may be burned down, never raised above these.
# import_boundary was re-derived once on 2026-09-29 when findings became keyed by
# imported name and dynamic loading became visible: the same tree gave 173
# statement-keyed and 291 name-keyed findings (no dynamic loaders, no string
# mentions). Pinned by test_challenge_harness_lints.py.
# Re-derived once on 2026-09-29 after merging origin/main (d995952f4): packages
# added on main after these lints were written (C060, W14-W17, moved demos)
# brought 6 import-boundary, 8 provider-path, 53 prompt-leak, 6 run-root and 11
# canonical-JSON findings. They are baselined, not fixed; nothing may rise above
# these totals.
INTRODUCTION_CEILINGS: Mapping[str, int] = {
    "import_boundary": 289,
    "provider_path": 65,
    "prompt_leak": 516,
    "run_roots": 9,
    "canonical_json_claim": 771,
}
BASELINE_SCHEMA = "core.local_ci.challenge_harness_lints_baseline.v1"
DEFAULT_BASELINE = Path(__file__).resolve().with_name(BASELINE_NAME)

PRUNED_DIRS = frozenset(
    {".git", "_intelligence", "_ic", "node_modules", "target", ".lake", "__pycache__", ".venv", "venv", "dist", "build"}
)
PROVIDERS_ROOT = "providers"
PROMPT_SCOPE_ROOT = "projects/mssn_sn_symgam"

CODE_SUFFIXES = frozenset({".py", ".ipynb", ".sh", ".ps1", ".js", ".ts", ".mjs"})
CLAIM_SUFFIXES = frozenset(
    {".py", ".rs", ".md", ".yaml", ".yml", ".toml", ".txt", ".lean", ".ts", ".js", ".sh", ".ps1", ".ipynb", ".tex", ".cfg", ".ini"}
)

# Built by concatenation so this file never matches its own provider patterns.
_PROVIDER_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("raw_openrouter_host", re.compile(re.escape("openrouter" + ".ai"), re.IGNORECASE)),
    ("load_dotenv_call", re.compile(re.escape("load_" + "dotenv("))),
    ("openrouter_backend_construction", re.compile(re.escape("OpenRouter" + "Backend("))),
)

# Built by concatenation so these definitions are not themselves claims.
_CLAIM_HINTS: tuple[str, ...] = ("87" + "85", "J" + "CS")
_CLAIM_RE = re.compile(r"(?i:rfc[\s_-]?" + "87" + "85)" + r"|(?<![A-Za-z])" + "J" + "CS" + r"(?![A-Za-z])")
CLAIM_DETAIL = "claims the RFC-numbered canonical JSON scheme"
_NEGATION_RE = re.compile(r"(?i)\b(?:not|no|never|without|nor|isn't|doesn't|rather than|instead of)\b")

_LEAK_FIELD_RE = re.compile(r"^(?:expected.*|note|notes|type|answer|answers)$")
_PROMPT_BUILDER_RE = re.compile(
    r"(?i)^_*(?:build|make|format|render|compose|create|construct|tokenize|generate|get)\w*prompt|prompt$"
)
_PROMPT_TARGET_RE = re.compile(r"(?i)(?:prompt|^(?:user|system)_?(?:msg|message|content)$|^messages?$)")

VERDICT_TOKENS = frozenset(
    {
        "sat", "unsat", "satisfiable", "unsatisfiable",
        "feasible", "infeasible", "infeas", "unbounded", "optimal", "opt",
        "consistent", "inconsistent",
        "solvable", "unsolvable", "solv", "insolvable",
        "obstructed", "unobstructed", "obstr", "extends", "nonextendable",
        "trivial", "nontrivial",
        "equal", "unequal", "equivalent", "inequivalent", "nonequivalent",
        "true", "false", "yes",
        "valid", "invalid",
        "flat", "nonflat",
        "balanced", "unbalanced", "frustrated",
        "singular", "nonsingular",
        "contextual", "noncontextual",
        "removable", "irremovable",
        "equiv", "inequiv", "unknown", "refuse", "refusal",
    }
)
_ID_KEYS = ("case_id", "id")


@dataclass(frozen=True)
class Finding:
    """One lint finding; ``key`` is line-number free so the baseline is stable."""

    lint: str
    path: str
    detail: str

    @property
    def key(self) -> str:
        return f"{self.path}::{self.detail}"


# --------------------------------------------------------------------------- files


def _git_tool(repo_root: Path) -> str | None:
    if __package__ in (None, ""):
        from host_tools import resolve_git_executable
    else:
        from .host_tools import resolve_git_executable
    tool = resolve_git_executable(repo_root)
    return str(tool) if tool is not None else None


def list_repo_files(repo_root: Path) -> list[str]:
    """Tracked and untracked-but-not-ignored files (git), else a pruned walk; POSIX relative paths."""
    git_tool = _git_tool(repo_root)
    if (repo_root / ".git").exists() and git_tool is not None:
        completed = subprocess.run(
            [git_tool, "-C", str(repo_root), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            capture_output=True,
            check=False,
        )
        if completed.returncode == 0:
            names = [n for n in completed.stdout.decode("utf-8", "surrogateescape").split("\0") if n]
            return sorted({n for n in names if not (set(PurePosixPath(n).parts[:-1]) & PRUNED_DIRS)})
    found: list[str] = []
    for dirpath, dirnames, filenames in os.walk(repo_root):
        dirnames[:] = sorted(d for d in dirnames if d not in PRUNED_DIRS)
        rel_dir = Path(dirpath).relative_to(repo_root)
        for name in filenames:
            found.append((rel_dir / name).as_posix())
    return sorted(found)


def _git_grep_files(
    repo_root: Path, needles: tuple[str, ...], *, ignore_case: bool = False, pathspec: str | None = None
) -> set[str] | None:
    """Paths whose text contains any needle, via git grep; None when git is unavailable.

    Only a prefilter: every lint still reads and checks each candidate itself.
    """
    git_tool = _git_tool(repo_root)
    if not (repo_root / ".git").exists() or git_tool is None:
        return None
    argv = [git_tool, "-C", str(repo_root), "grep", "-l", "-z", "-I", "--untracked", "-F"]
    if ignore_case:
        argv.append("-i")
    for needle in needles:
        argv.extend(["-e", needle])
    if pathspec is not None:
        argv.extend(["--", pathspec])
    completed = subprocess.run(argv, capture_output=True, check=False)
    if completed.returncode not in (0, 1):
        return None
    return {n for n in completed.stdout.decode("utf-8", "surrogateescape").split("\0") if n}


def _narrow(
    repo_root: Path,
    files: Iterable[str],
    needles: tuple[str, ...],
    *,
    ignore_case: bool = False,
    pathspec: str | None = None,
) -> list[str]:
    candidates = _git_grep_files(repo_root, needles, ignore_case=ignore_case, pathspec=pathspec)
    return [rel for rel in files if candidates is None or rel in candidates]


def _read_text(repo_root: Path, rel: str) -> str | None:
    path = repo_root / rel
    try:
        return path.read_bytes().decode("utf-8", "replace")
    except OSError:
        return None


def _parse(repo_root: Path, rel: str) -> ast.Module | None:
    text = _read_text(repo_root, rel)
    if text is None:
        return None
    try:
        return ast.parse(text, filename=rel)
    except (SyntaxError, ValueError):
        return None


def _parts(rel: str) -> tuple[str, ...]:
    return PurePosixPath(rel).parts


def _is_test_path(rel: str) -> bool:
    parts = _parts(rel)
    name = parts[-1]
    return (
        "tests" in parts[:-1]
        or "harness_tests" in parts[:-1]
        or name.startswith("test_")
        or name.endswith("_test.py")
        or name == "conftest.py"
    )


# ------------------------------------------------------------ (a) import boundary


# Calls that load code by name or path. Under judge_packet/ every such call is a
# finding, because it hides what is loaded from this static check.
DYNAMIC_LOADERS = frozenset(
    {"import_module", "__import__", "spec_from_file_location", "run_path", "run_module", "SourceFileLoader"}
)
REFERENCE_SOLVER = "reference_solver"


def _reference_suffix(text: str) -> str | None:
    """The part of a dotted name or path from ``reference_solver`` on, with ``/`` separators."""
    index = text.find(REFERENCE_SOLVER)
    return None if index < 0 else text[index:].replace("\\", "/")


def _docstring_ids(tree: ast.Module) -> set[int]:
    ids: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Module | ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                ids.add(id(first.value))
    return ids


def _import_keys(node: ast.AST, own_stem: str, is_checker: bool) -> list[str]:
    """One key per imported name, independent of how the import is spelled."""
    keys: list[str] = []
    if isinstance(node, ast.Import):
        for alias in node.names:
            parts = [c for c in alias.name.split(".") if c]
            if REFERENCE_SOLVER in parts:
                keys.append("imports " + ".".join(parts[parts.index(REFERENCE_SOLVER):]))
            elif is_checker and parts and parts[-1].endswith("checker") and parts[-1] != own_stem:
                keys.append(f"checker imports another checker {parts[-1]}")
    elif isinstance(node, ast.ImportFrom):
        module_parts = [c for c in (node.module or "").split(".") if c]
        for alias in node.names:
            parts = module_parts + [alias.name]
            if REFERENCE_SOLVER in parts:
                keys.append("imports " + ".".join(parts[parts.index(REFERENCE_SOLVER):]))
            elif is_checker and module_parts and module_parts[-1].endswith("checker") and module_parts[-1] != own_stem:
                keys.append(f"checker imports another checker {module_parts[-1]}.{alias.name}")
            elif is_checker and alias.name.endswith("checker") and alias.name != own_stem:
                keys.append(f"checker imports another checker {alias.name}")
    return keys


def _call_name(node: ast.Call) -> str | None:
    func = node.func
    return func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else None


def _judge_packet_module(rel: str) -> bool:
    return rel.endswith(".py") and "judge_packet" in _parts(rel)[:-1]


def _note_ref_solve_import(findings: list[Finding], rel: str, node: ast.AST) -> None:
    if not isinstance(node, ast.ImportFrom):
        return
    for alias in node.names:
        if alias.name == "ref_solve":
            findings.append(Finding("import_boundary", rel, "imports ref_solve"))


def _dynamic_shown(node: ast.Call, literals: list[ast.Constant]) -> str | None:
    shown = next((suffix for suffix in (_reference_suffix(item.value) for item in literals) if suffix), None)
    if shown is None and node.args and literals and node.args[0] is literals[0]:
        return literals[0].value
    return shown


def _note_dynamic_call(findings: list[Finding], rel: str, node: ast.AST, consumed: set[int]) -> None:
    if not isinstance(node, ast.Call):
        return
    name = _call_name(node)
    if name == "ref_solve":
        findings.append(Finding("import_boundary", rel, "calls ref_solve"))
        return
    if name not in DYNAMIC_LOADERS:
        return
    literals = [arg for arg in node.args if isinstance(arg, ast.Constant) and isinstance(arg.value, str)]
    shown = _dynamic_shown(node, literals)
    consumed.update(id(arg) for arg in literals)
    findings.append(Finding("import_boundary", rel, f"dynamic import {name}({shown or '<expression>'})"))


def _note_reference_strings(findings: list[Finding], rel: str, tree: ast.AST, consumed: set[int]) -> None:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        if id(node) in consumed:
            continue
        suffix = _reference_suffix(node.value)
        if suffix is not None:
            findings.append(Finding("import_boundary", rel, f"string mentions {suffix}"))


def lint_import_boundary(repo_root: Path, files: Iterable[str]) -> list[Finding]:
    findings: list[Finding] = []
    for rel in files:
        if not _judge_packet_module(rel):
            continue
        tree = _parse(repo_root, rel)
        if tree is None:
            findings.append(Finding("import_boundary", rel, "unparseable judge_packet module"))
            continue
        own_stem = PurePosixPath(rel).stem
        is_checker = own_stem.endswith("checker")
        consumed = _docstring_ids(tree)
        for node in ast.walk(tree):
            for key in _import_keys(node, own_stem, is_checker):
                findings.append(Finding("import_boundary", rel, key))
            _note_ref_solve_import(findings, rel, node)
            _note_dynamic_call(findings, rel, node, consumed)
        _note_reference_strings(findings, rel, tree, consumed)
    return findings


# -------------------------------------------------------------- (b) provider path


def lint_provider_path(repo_root: Path, files: Iterable[str]) -> list[Finding]:
    findings: list[Finding] = []
    needles = ("openrouter" + ".ai", "load_" + "dotenv(", "OpenRouter" + "Backend(")
    for rel in _narrow(repo_root, files, needles, ignore_case=True):
        parts = _parts(rel)
        if parts[0] == PROVIDERS_ROOT or PurePosixPath(rel).suffix not in CODE_SUFFIXES:
            continue
        text = _read_text(repo_root, rel)
        if text is None:
            continue
        for label, pattern in _PROVIDER_PATTERNS:
            for _ in pattern.finditer(text):
                findings.append(Finding("provider_path", rel, label))
    return findings


# ---------------------------------------------------------------- (c) prompt leak


def _constant_text(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _key_leak(value: str) -> str | None:
    if value in _ID_KEYS:
        return "case_id"
    if _LEAK_FIELD_RE.match(value):
        return f"field {value}"
    return None


def _subscript_leaks(node: ast.Subscript) -> list[str]:
    value = _constant_text(node.slice)
    if value is None:
        return []
    leak = _key_leak(value)
    return [] if leak is None else [leak]


def _get_leaks(node: ast.Call) -> list[str]:
    func = node.func
    if not isinstance(func, ast.Attribute) or func.attr != "get" or not node.args:
        return []
    value = _constant_text(node.args[0])
    if value is None:
        return []
    leak = _key_leak(value)
    return [] if leak is None else [leak]


def _dumps_leak(node: ast.Call) -> str | None:
    func = node.func
    if not isinstance(func, ast.Attribute) or func.attr != "dumps" or not node.args:
        return None
    root = node.args[0]
    while isinstance(root, ast.Subscript | ast.Attribute):
        root = root.value
    if isinstance(root, ast.Name) and root.id.lower().startswith("case"):
        return "json.dumps(case)"
    return None


def _leaks_in(expr: ast.AST) -> list[str]:
    leaks: list[str] = []
    for node in ast.walk(expr):
        if isinstance(node, ast.Name) and node.id == "case_id":
            leaks.append("case_id")
        elif isinstance(node, ast.Attribute) and node.attr == "case_id":
            leaks.append("case_id")
        elif isinstance(node, ast.Subscript):
            leaks.extend(_subscript_leaks(node))
        elif isinstance(node, ast.Call):
            leaks.extend(_get_leaks(node))
            dumped = _dumps_leak(node)
            if dumped is not None:
                leaks.append(dumped)
    return leaks


def _target_names(node: ast.Assign | ast.AnnAssign | ast.AugAssign) -> list[str]:
    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    names: list[str] = []
    for target in targets:
        if isinstance(target, ast.Name):
            names.append(target.id)
        elif isinstance(target, ast.Attribute):
            names.append(target.attr)
    return names


def _prompt_leaks(rel: str, tree: ast.Module) -> list[Finding]:
    findings: list[Finding] = []
    covered: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and _PROMPT_BUILDER_RE.search(node.name):
            for stmt in node.body:
                for leak in _leaks_in(stmt):
                    findings.append(Finding("prompt_leak", rel, f"prompt builder {node.name}: {leak}"))
                for sub in ast.walk(stmt):
                    covered.add(id(sub))
    for node in ast.walk(tree):
        if id(node) in covered or not isinstance(node, ast.Assign | ast.AnnAssign | ast.AugAssign):
            continue
        names = [n for n in _target_names(node) if _PROMPT_TARGET_RE.search(n)]
        if not names or node.value is None:
            continue
        for leak in _leaks_in(node.value):
            findings.append(Finding("prompt_leak", rel, f"prompt variable {names[0]}: {leak}"))
    return findings


def _load_json(repo_root: Path, rel: str) -> object | None:
    text = _read_text(repo_root, rel)
    if text is None:
        return None
    try:
        return json.loads(text)
    except ValueError:
        return None


def _problem_digest(value: Mapping[str, object]) -> str:
    stripped = {k: v for k, v in value.items() if k not in _ID_KEYS and not k.startswith("expected")}
    return hashlib.sha256(json.dumps(stripped, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _package_root(rel: str, marker: str) -> str | None:
    parts = _parts(rel)
    if marker not in parts[:-1]:
        return None
    return "/".join(parts[: parts.index(marker)])


def _python_prompt_file(rel: str, suffix: str, parts: list[str], prompt_candidates: set[str]) -> bool:
    if suffix != ".py" or rel not in prompt_candidates:
        return False
    if _is_test_path(rel):
        return False
    return "judge_packet" not in parts[:-1]


def _note_verdict_words(findings: list[Finding], rel: str, data: Mapping[str, object]) -> None:
    case_id = next((data[key] for key in _ID_KEYS if isinstance(data.get(key), str)), None)
    if not isinstance(case_id, str):
        return
    tokens = {token for token in re.split(r"[^a-z0-9]+", case_id.lower()) if token}
    for word in sorted(tokens & VERDICT_TOKENS):
        findings.append(Finding("prompt_leak", rel, f"case id carries verdict word {word}"))


def _note_json_prompt(
    findings: list[Finding],
    repo_root: Path,
    rel: str,
    parts: list[str],
    examples: dict[str, dict[str, str]],
    judge_cases: list[tuple[str, str, Mapping[str, object]]],
) -> None:
    pkg = _package_root(rel, "participant_packet")
    if pkg is not None:
        data = _load_json(repo_root, rel)
        if isinstance(data, dict):
            examples.setdefault(pkg, {}).setdefault(_problem_digest(data), rel)
        return
    pkg = _package_root(rel, "judge_packet")
    if pkg is None or "cases" not in parts[:-1]:
        return
    data = _load_json(repo_root, rel)
    if not isinstance(data, dict):
        return
    judge_cases.append((pkg, rel, data))
    _note_verdict_words(findings, rel, data)


def lint_prompt_leak(repo_root: Path, files: Iterable[str]) -> list[Finding]:
    findings: list[Finding] = []
    scoped = [rel for rel in files if rel == PROMPT_SCOPE_ROOT or rel.startswith(PROMPT_SCOPE_ROOT + "/")]
    prompt_candidates = set(
        _narrow(
            repo_root,
            [rel for rel in scoped if rel.endswith(".py")],
            ("prompt", "_msg", "messages", "user_content", "system_content"),
            ignore_case=True,
            pathspec=PROMPT_SCOPE_ROOT,
        )
    )
    examples: dict[str, dict[str, str]] = {}
    judge_cases: list[tuple[str, str, Mapping[str, object]]] = []
    for rel in scoped:
        suffix = PurePosixPath(rel).suffix
        parts = _parts(rel)
        if _python_prompt_file(rel, suffix, parts, prompt_candidates):
            tree = _parse(repo_root, rel)
            if tree is not None:
                findings.extend(_prompt_leaks(rel, tree))
            continue
        if suffix == ".json":
            _note_json_prompt(findings, repo_root, rel, parts, examples, judge_cases)
    for pkg, rel, data in judge_cases:
        example = examples.get(pkg, {}).get(_problem_digest(data))
        if example is not None:
            findings.append(Finding("prompt_leak", rel, f"duplicates participant example {example}"))
    return findings


# ------------------------------------------------------------------ (d) run roots


def _is_parent_arith(node: ast.AST) -> bool:
    if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Attribute) and node.value.attr == "parents":
        return True
    if isinstance(node, ast.Attribute) and node.attr == "parent":
        depth, cur = 0, node
        while isinstance(cur, ast.Attribute) and cur.attr == "parent":
            depth += 1
            cur = cur.value
        return depth >= 2
    return False


def _mentions(expr: ast.AST, tainted: set[str]) -> bool:
    for node in ast.walk(expr):
        if _is_parent_arith(node):
            return True
        if isinstance(node, ast.Name) and node.id in tainted:
            return True
        if isinstance(node, ast.Attribute) and node.attr in tainted:
            return True
    return False


def _intelligence_constant(expr: ast.AST) -> bool:
    for node in ast.walk(expr):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            head = node.value.replace("\\", "/").lstrip("/").split("/", 1)[0]
            if head in {"_intelligence", "_ic"}:
                return True
    return False


def _text_mentions_run_root(text: str | None) -> bool:
    if text is None or not any(root in text for root in ("_intelligence", "_ic")):
        return False
    return "parents[" in text or ".parent.parent" in text


def _absorb_taint(tainted: set[str], names: list[str]) -> bool:
    changed = False
    for name in names:
        if name not in tainted:
            tainted.add(name)
            changed = True
    return changed


def _taint_once(assigns: list[ast.AST], tainted: set[str]) -> bool:
    changed = False
    for node in assigns:
        if _mentions(node.value, tainted) and _absorb_taint(tainted, _target_names(node)):
            changed = True
    return changed


def _spread_taint(assigns: list[ast.AST]) -> set[str]:
    tainted: set[str] = set()
    changed = True
    while changed:
        changed = _taint_once(assigns, tainted)
    return tainted


def _call_label(func: ast.AST) -> str:
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return ""


def _join_base(node: ast.Call, name: str) -> ast.AST:
    if name != "joinpath":
        return node.args[0]
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.value
    return node.args[0]


def _division_reaches(node: ast.AST, tainted: set[str]) -> bool:
    if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Div):
        return False
    return _intelligence_constant(node.right) and _mentions(node.left, tainted)


def _join_reaches(node: ast.AST, tainted: set[str]) -> bool:
    if not isinstance(node, ast.Call) or not node.args:
        return False
    name = _call_label(node.func)
    if name not in {"join", "joinpath", "Path", "PurePath"}:
        return False
    rest = node.args if name == "joinpath" else node.args[1:]
    return any(_intelligence_constant(arg) for arg in rest) and _mentions(_join_base(node, name), tainted)


def _run_root_hits(tree: ast.AST, tainted: set[str]) -> int:
    count = 0
    for node in ast.walk(tree):
        if _division_reaches(node, tainted):
            count += 1
        elif _join_reaches(node, tainted):
            count += 1
    return count


def lint_run_roots(repo_root: Path, files: Iterable[str]) -> list[Finding]:
    findings: list[Finding] = []
    for rel in _narrow(repo_root, files, ("_intelligence", "_ic",)):
        if not rel.endswith(".py") or _is_test_path(rel):
            continue
        if not _text_mentions_run_root(_read_text(repo_root, rel)):
            continue
        tree = _parse(repo_root, rel)
        if tree is None:
            continue
        assigns = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Assign | ast.AnnAssign) and node.value is not None
        ]
        count = _run_root_hits(tree, _spread_taint(assigns))
        findings.extend(Finding("run_roots", rel, "parent arithmetic reaches _intelligence") for _ in range(count))
    return findings


# ------------------------------------------------------- (e) canonical JSON claims


def lint_canonical_json_claim(repo_root: Path, files: Iterable[str]) -> list[Finding]:
    findings: list[Finding] = []
    for rel in _narrow(repo_root, files, _CLAIM_HINTS):
        if PurePosixPath(rel).suffix not in CLAIM_SUFFIXES:
            continue
        text = _read_text(repo_root, rel)
        if text is None or not any(hint in text for hint in _CLAIM_HINTS):
            continue
        for line in text.splitlines():
            if _CLAIM_RE.search(line) and not _NEGATION_RE.search(line):
                findings.append(Finding("canonical_json_claim", rel, CLAIM_DETAIL))
    return findings


LINTS: Mapping[str, Callable[[Path, Iterable[str]], list[Finding]]] = {
    "import_boundary": lint_import_boundary,
    "provider_path": lint_provider_path,
    "prompt_leak": lint_prompt_leak,
    "run_roots": lint_run_roots,
    "canonical_json_claim": lint_canonical_json_claim,
}


# -------------------------------------------------------------------- baseline


class BaselineError(ValueError):
    """The baseline file is missing, malformed, or not for this lint set."""


def finding_counts(findings: Iterable[Finding]) -> dict[str, int]:
    counts = Counter(f.key for f in findings)
    return {key: counts[key] for key in sorted(counts, key=lambda s: s.encode("utf-8"))}


def load_baseline(path: Path) -> dict[str, dict[str, int]]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise BaselineError(f"cannot read baseline {path}: {error}") from error
    if not isinstance(raw, dict) or raw.get("schema") != BASELINE_SCHEMA or not isinstance(raw.get("lints"), dict):
        raise BaselineError(f"baseline {path} does not have schema {BASELINE_SCHEMA}")
    lints: dict[str, dict[str, int]] = {}
    for name, table in raw["lints"].items():
        if name not in LINTS or not isinstance(table, dict):
            raise BaselineError(f"baseline {path} has an unknown or malformed lint table {name!r}")
        for key, count in table.items():
            if type(count) is not int or count <= 0:
                raise BaselineError(f"baseline count for {name}:{key} must be a positive int")
        lints[name] = dict(table)
    return lints


def new_findings(current: Mapping[str, int], allowed: Mapping[str, int]) -> dict[str, int]:
    """Findings beyond the baseline: new keys, or more occurrences than recorded."""
    return {key: n - allowed.get(key, 0) for key, n in current.items() if n > allowed.get(key, 0)}


def stale_entries(current: Mapping[str, int], allowed: Mapping[str, int]) -> dict[str, int]:
    """Baseline entries that no longer occur as often (candidates to burn down)."""
    return {key: n - current.get(key, 0) for key, n in allowed.items() if current.get(key, 0) < n}


def run_lints(repo_root: Path, names: Iterable[str]) -> dict[str, list[Finding]]:
    files = list_repo_files(repo_root)
    return {name: LINTS[name](repo_root, files) for name in names}


def write_baseline(path: Path, results: Mapping[str, list[Finding]], existing: Mapping[str, dict[str, int]]) -> None:
    lints = dict(existing)
    for name, findings in results.items():
        lints[name] = finding_counts(findings)
    payload = {
        "_note": (
            "Violations that existed when the challenge harness lints were introduced. "
            "The gates fail only on findings beyond these counts. Burn this list down; "
            "do not add to it."
        ),
        "lints": {name: lints[name] for name in LINT_NAMES if name in lints},
        "schema": BASELINE_SCHEMA,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def _lint_names(selected: list[str]) -> list[str]:
    if "all" in selected:
        return list(LINT_NAMES)
    return list(dict.fromkeys(selected))


def _write_requested_baseline(names: list[str], results: dict[str, list[Finding]], baseline_path: Path) -> int:
    over = {
        name: len(results[name])
        for name in names
        if len(results[name]) > INTRODUCTION_CEILINGS[name]
    }
    if over:
        for name, total in over.items():
            print(
                f"challenge_harness_lints: refusing to write a baseline: {name} has {total} findings, "
                f"above its introduction ceiling {INTRODUCTION_CEILINGS[name]}",
                file=sys.stderr,
            )
        return 2
    existing = load_baseline(baseline_path) if baseline_path.is_file() else {}
    write_baseline(baseline_path, results, existing)
    for name in names:
        print(f"{name}: baseline written with {len(results[name])} finding(s)")
    return 0


def _ceiling_block(names: list[str], baseline: Mapping[str, Mapping[str, int]]) -> int | None:
    for name in names:
        total = sum(baseline.get(name, {}).values())
        if total > INTRODUCTION_CEILINGS[name]:
            print(
                f"challenge_harness_lints: baseline for {name} totals {total}, above its introduction ceiling "
                f"{INTRODUCTION_CEILINGS[name]}; a baseline may only be burned down",
                file=sys.stderr,
            )
            return 2
    return None


def _report_one_lint(
    name: str,
    results: Mapping[str, list[Finding]],
    baseline: Mapping[str, Mapping[str, int]],
    report: bool,
) -> bool:
    current = finding_counts(results[name])
    allowed = baseline.get(name, {})
    extra = new_findings(current, allowed)
    stale = stale_entries(current, allowed)
    status = "FAIL" if extra else "PASS"
    print(
        f"{name}: {status} findings={sum(current.values())} baseline={sum(allowed.values())} "
        f"new={sum(extra.values())} burned_down={sum(stale.values())}"
    )
    for key, count in extra.items():
        print(f"  NEW {key} (+{count})")
    if report:
        for key, count in current.items():
            print(f"  {key} x{count}")
    return bool(extra)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo-root", default=".", help="repository root to scan")
    parser.add_argument("--lint", action="append", choices=[*LINT_NAMES, "all"], required=True)
    parser.add_argument("--baseline", default=str(DEFAULT_BASELINE), help="baseline JSON path")
    parser.add_argument("--report", action="store_true", help="print every finding, not only new ones")
    parser.add_argument("--write-baseline", action="store_true", help="rewrite the baseline (maintainers only)")
    args = parser.parse_args(argv)

    names = _lint_names(args.lint)
    repo_root = Path(args.repo_root).resolve()
    if not repo_root.is_dir():
        print(f"challenge_harness_lints: repository root not found: {repo_root}", file=sys.stderr)
        return 2
    baseline_path = Path(args.baseline)
    results = run_lints(repo_root, names)
    if args.write_baseline:
        return _write_requested_baseline(names, results, baseline_path)
    try:
        baseline = load_baseline(baseline_path)
    except BaselineError as error:
        print(f"challenge_harness_lints: {error}", file=sys.stderr)
        return 2
    blocked = _ceiling_block(names, baseline)
    if blocked is not None:
        return blocked
    failed = False
    for name in names:
        failed = _report_one_lint(name, results, baseline, args.report) or failed
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())


__all__ = [
    "BASELINE_SCHEMA",
    "BaselineError",
    "DYNAMIC_LOADERS",
    "INTRODUCTION_CEILINGS",
    "Finding",
    "LINTS",
    "LINT_NAMES",
    "VERDICT_TOKENS",
    "finding_counts",
    "lint_canonical_json_claim",
    "lint_import_boundary",
    "lint_prompt_leak",
    "lint_provider_path",
    "lint_run_roots",
    "list_repo_files",
    "load_baseline",
    "main",
    "new_findings",
    "run_lints",
    "stale_entries",
]
