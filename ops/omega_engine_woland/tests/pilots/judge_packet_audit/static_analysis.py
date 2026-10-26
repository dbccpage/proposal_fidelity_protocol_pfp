"""Static (AST and text) analysis of challenge-package source files.

Nothing here imports or executes package code. Module names are
package-relative dotted names such as ``judge_packet.checkers.exact_checker``
or ``reference_solver.solver``; absolute imports through the repository path
of the package are reduced to the same form.
"""

from __future__ import annotations

import ast
import re
import warnings
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

CHALLENGES_PREFIX = "omega_engine_pfp.tests.demo_004."
# Historical fallback imports remain in sealed scoring/checker sources. Resolve
# their syntax for analysis only; executable descriptors always use the current owner.
SOURCE_CHALLENGES_PREFIXES = (
    CHALLENGES_PREFIX,
    "omega_engine_projects.mssn_sn_symgam.challenges.",
)
REFUSAL_STATUS_WORDS = frozenset(
    {"UNKNOWN", "OUT_OF_SCOPE", "REFUSED", "REFUSAL", "ABSTAIN", "ABSTAINED"}
)
CODE_KEYS = (
    "refusal",
    "refusal_code",
    "code",
    "reason",
    "refusal_reason",
    "unknown_reason",
    "reason_code",
)
STATUS_KEYS = ("status",)
CONSTANT_NAME = re.compile(r"(REFUS|ENUM|REASON|CODE|OOS)", re.IGNORECASE)
UPPER_TOKEN = re.compile(r"^[A-Z][A-Z0-9_]{1,63}$")
SOLVE_NAME = re.compile(r"solve", re.IGNORECASE)


@dataclass(frozen=True)
class ImportRecord:
    """One imported name, resolved to a package-relative module when possible."""

    module: str
    name: str | None
    alias: str
    lineno: int
    internal: bool

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        return (self.module, self.name, self.alias, self.lineno, self.internal) == (
            other.module,  # type: ignore[attr-defined]
            other.name,  # type: ignore[attr-defined]
            other.alias,  # type: ignore[attr-defined]
            other.lineno,  # type: ignore[attr-defined]
            other.internal,  # type: ignore[attr-defined]
        )

    def __hash__(self) -> int:
        return hash((type(self), self.module, self.name, self.alias, self.lineno, self.internal))


def module_file(package_dir: Path, module: str) -> Path | None:
    """Resolves a package-relative module name to its source file."""
    if not module:
        return None
    base = package_dir.joinpath(*module.split("."))
    if base.with_suffix(".py").is_file():
        return base.with_suffix(".py")
    if (base / "__init__.py").is_file():
        return base / "__init__.py"
    return None


def module_name_for(package_dir: Path, path: Path) -> str:
    rel = path.relative_to(package_dir).with_suffix("")
    parts = list(rel.parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def strip_package_prefix(module: str, package_rel_dotted: str) -> str | None:
    """Reduces an absolute import of the package to a package-relative name."""
    for prefix in SOURCE_CHALLENGES_PREFIXES:
        full = prefix + package_rel_dotted
        if module == full:
            return ""
        if module.startswith(full + "."):
            return module[len(full) + 1 :]
    return None


def parse_source(path: Path) -> ast.Module | None:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            return ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError, OSError):
        return None


def resolve_import(
    node: ast.ImportFrom | ast.Import,
    current_module: str,
    is_package: bool,
    package_dir: Path,
    package_rel_dotted: str,
) -> list[ImportRecord]:
    records: list[ImportRecord] = []
    if isinstance(node, ast.Import):
        for alias in node.names:
            rel = strip_package_prefix(alias.name, package_rel_dotted)
            module = rel if rel is not None else alias.name
            internal = rel is not None or module_file(package_dir, alias.name) is not None
            records.append(
                ImportRecord(module, None, alias.asname or alias.name, node.lineno, internal)
            )
        return records
    base = node.module or ""
    if node.level > 0:
        parts = current_module.split(".") if current_module else []
        if not is_package:
            parts = parts[:-1]
        drop = node.level - 1
        if drop > len(parts):
            parent_parts: list[str] = []
            internal_base = False
        else:
            parent_parts = parts[: len(parts) - drop] if drop else parts
            internal_base = True
        module = ".".join([p for p in parent_parts + ([base] if base else []) if p])
        internal = internal_base
    else:
        rel = strip_package_prefix(base, package_rel_dotted)
        if rel is not None:
            module, internal = rel, True
        else:
            module = base
            internal = module_file(package_dir, base) is not None
    for alias in node.names:
        records.append(
            ImportRecord(module, alias.name, alias.asname or alias.name, node.lineno, internal)
        )
    return records


def imports_of(path: Path, package_dir: Path, package_rel_dotted: str) -> list[ImportRecord]:
    tree = parse_source(path)
    if tree is None:
        return []
    current = module_name_for(package_dir, path)
    is_package = path.name == "__init__.py"
    out: list[ImportRecord] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            out.extend(resolve_import(node, current, is_package, package_dir, package_rel_dotted))
    return sorted(out, key=lambda r: (r.lineno, r.module, r.name or "", r.alias))


def imported_target(record: ImportRecord, package_dir: Path) -> tuple[str, str | None]:
    """For ``from M import X``: returns (module, function) or (M.X, None) if X is a module."""
    if record.name is not None:
        sub = f"{record.module}.{record.name}" if record.module else record.name
        if module_file(package_dir, sub) is not None:
            return sub, None
        return record.module, record.name
    return record.module, None


def called_names(tree: ast.AST) -> list[tuple[int, str]]:
    calls: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                calls.append((node.lineno, func.id))
            elif isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                calls.append((node.lineno, f"{func.value.id}.{func.attr}"))
    return sorted(calls)


def internal_closure(
    start: list[str], package_dir: Path, package_rel_dotted: str, stop_prefixes: tuple[str, ...]
) -> dict[str, list[ImportRecord]]:
    """Transitive internal imports from ``start`` modules; does not descend into ``stop_prefixes``."""
    seen: dict[str, list[ImportRecord]] = {}
    queue = list(start)
    while queue:
        module = queue.pop(0)
        if module in seen:
            continue
        path = module_file(package_dir, module)
        if path is None:
            seen[module] = []
            continue
        records = [r for r in imports_of(path, package_dir, package_rel_dotted) if r.internal]
        seen[module] = records
        for record in records:
            target, _ = imported_target(record, package_dir)
            if any(target == p or target.startswith(p + ".") for p in stop_prefixes):
                continue
            if module_file(package_dir, target) is not None and target not in seen:
                queue.append(target)
    return seen


def checker_dependence(
    package_dir: Path,
    package_rel_dotted: str,
    checker_module: str,
    other_checker_modules: list[str],
) -> dict[str, object]:
    """Import and call dependence of one checker module on the reference solver and the other checker."""
    closure = internal_closure(
        [checker_module], package_dir, package_rel_dotted, ("reference_solver",)
    )
    reference_imports: set[str] = set()
    other_checker_imports: set[str] = set()
    via_helpers: set[str] = set()
    for module, records in closure.items():
        for record in records:
            target, name = imported_target(record, package_dir)
            label = f"{target}:{name}" if name else target
            if target == "reference_solver" or target.startswith("reference_solver."):
                reference_imports.add(label)
                if module != checker_module:
                    via_helpers.add(module)
            for other in other_checker_modules:
                if target == other:
                    other_checker_imports.add(label)
    solve_calls: list[str] = []
    for module in closure:
        path = module_file(package_dir, module)
        tree = parse_source(path) if path else None
        if tree is None:
            continue
        ref_aliases: dict[str, str] = {}
        for record in closure[module]:
            target, name = imported_target(record, package_dir)
            if target == "reference_solver" or target.startswith("reference_solver."):
                ref_aliases[record.alias] = f"{target}:{name}" if name else target
        for lineno, called in called_names(tree):
            head = called.split(".")[0]
            leaf = called.split(".")[-1]
            if head in ref_aliases and SOLVE_NAME.search(leaf):
                solve_calls.append(f"{module}:{lineno}:{called}")
    if solve_calls:
        klass = "ANSWER_KEY"
    elif other_checker_imports:
        klass = "IMPORTS_OTHER_CHECKER"
    elif reference_imports:
        klass = "SHARES_REFERENCE_CODE"
    else:
        klass = "NO_IMPORT_DEPENDENCE"
    return {
        "class": klass,
        "reference_solver_imports": sorted(reference_imports),
        "reference_solve_calls": sorted(solve_calls),
        "other_checker_imports": sorted(other_checker_imports),
        "internal_modules_reached": sorted(m for m in closure if m != checker_module),
        "reference_reached_via_helper_modules": sorted(via_helpers),
    }


def nontrivial_lines(text: str) -> list[str]:
    """Stripped source lines of at least 16 characters that are not comments or imports."""
    out = []
    for raw in text.splitlines():
        line = raw.strip()
        if len(line) < 16:
            continue
        if line.startswith("#") or line.startswith("import ") or line.startswith("from "):
            continue
        if line in ('"""', "'''"):
            continue
        out.append(line)
    return out


def shared_line_fraction(a_text: str, b_text: str) -> tuple[int, int]:
    """(shared, total): how many of A's non-trivial lines (as a multiset) occur in B."""
    a_lines = nontrivial_lines(a_text)
    b_counts = Counter(nontrivial_lines(b_text))
    shared = 0
    for line in a_lines:
        if b_counts[line] > 0:
            b_counts[line] -= 1
            shared += 1
    return shared, len(a_lines)


def _str_constants(node: ast.AST) -> list[str]:
    out = []
    for sub in ast.walk(node):
        if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
            out.append(sub.value)
    return out


def _key_of_access(node: ast.AST) -> str | None:
    """Returns K for ``x.get("K"...)`` or ``x["K"]``."""
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "get"
        and node.args
    ):
        first = node.args[0]
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            return first.value
    if isinstance(node, ast.Subscript):
        sl = node.slice
        if isinstance(sl, ast.Constant) and isinstance(sl.value, str):
            return sl.value
    if isinstance(node, ast.BoolOp):
        for value in node.values:
            key = _key_of_access(value)
            if key is not None:
                return key
    return None


def vocabulary(paths: list[Path]) -> dict[str, list[str]]:
    """Status words, refusal-code candidates and code keys read from checker sources."""
    statuses: set[str] = set()
    codes: set[str] = set()
    code_keys: set[str] = set()
    enum_constants: dict[str, list[str]] = {}
    for path in paths:
        tree = parse_source(path)
        if tree is None:
            continue
        name_keys: dict[str, str] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target = node.targets[0]
                if isinstance(target, ast.Name):
                    key = _key_of_access(node.value)
                    if key is not None:
                        name_keys[target.id] = key
                    if CONSTANT_NAME.search(target.id) and target.id.isupper():
                        values = _collection_strings(node.value)
                        if values:
                            enum_constants[f"{path.name}:{target.id}"] = sorted(values)
                            codes.update(values)
            if (
                isinstance(node, ast.AnnAssign)
                and isinstance(node.target, ast.Name)
                and node.value is not None
            ):
                if CONSTANT_NAME.search(node.target.id) and node.target.id.isupper():
                    values = _collection_strings(node.value)
                    if values:
                        enum_constants[f"{path.name}:{node.target.id}"] = sorted(values)
                        codes.update(values)
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "get"
            ):
                key = _key_of_access(node)
                if key in CODE_KEYS:
                    code_keys.add(key)
            if isinstance(node, ast.Subscript):
                key = _key_of_access(node)
                if key in CODE_KEYS:
                    code_keys.add(key)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Compare):
                continue
            sides = [node.left, *node.comparators]
            keys = set()
            for side in sides:
                key = _key_of_access(side)
                if key is None and isinstance(side, ast.Name):
                    key = name_keys.get(side.id)
                if key is not None:
                    keys.add(key)
            words = {s for side in sides for s in _str_constants(side) if UPPER_TOKEN.match(s)}
            if keys & set(STATUS_KEYS):
                statuses.update(words)
            if keys & set(CODE_KEYS):
                codes.update(words)
    return {
        "statuses": sorted(statuses),
        "refusal_statuses": sorted(statuses & REFUSAL_STATUS_WORDS),
        "codes": sorted(codes),
        "code_keys": sorted(code_keys),
        "enum_constants": [f"{k}={','.join(v)}" for k, v in sorted(enum_constants.items())],
    }


def _collection_strings(node: ast.AST) -> list[str]:
    target = node
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in ("frozenset", "set", "tuple", "list")
        and node.args
    ):
        target = node.args[0]
    if isinstance(target, (ast.Set, ast.List, ast.Tuple)):
        values = []
        for elt in target.elts:
            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                values.append(elt.value)
            else:
                return []
        return values
    if isinstance(target, ast.Dict):
        values = []
        for key in target.keys:
            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                values.append(key.value)
            else:
                return []
        return values
    return []
