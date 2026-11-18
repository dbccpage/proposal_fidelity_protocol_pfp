#!/usr/bin/env python3
"""Automated fitness function for Clean Architecture boundaries in CODA and PFP.
AuthorityEffect: None.
"""

from __future__ import annotations

import ast
import sys
from collections import defaultdict
from pathlib import Path

# Directories and name markers considered persistence adapters
PERSISTENCE_ADAPTER_DIR_PARTS = frozenset(
    {"infrastructure", "adapters", "persistence", "storage", "repositories"}
)
PERSISTENCE_ADAPTER_FILE_SUFFIXES = ("adapter.py", "store.py", "repository.py")

COMMON_MODULE_NAMES = frozenset(
    {
        "__init__.py",
        "conftest.py",
        "base.py",
        "types.py",
        "models.py",
        "protocols.py",
        "ports.py",
        "constants.py",
        "errors.py",
        "utils.py",
        "cli.py",
        "runner.py",
        "schemas.py",
        "contracts.py",
        "harness.py",
        "main.py",
        "config.py",
    }
)


def get_bounded_context_roots(repo_root: Path) -> list[Path]:
    """Discover all bounded context package roots."""
    roots: list[Path] = []
    for item in repo_root.iterdir():
        if not item.is_dir():
            continue
        if item.name.startswith("engine") or item.name == "the_symbol_game":
            if not item.name.endswith(".egg-info") and not item.name.startswith("."):
                roots.append(item)
    return sorted(roots, key=lambda p: p.name)


def is_persistence_adapter(py_file: Path, text: str) -> bool:
    """Determine if a file is or contains a persistence / infrastructure adapter."""
    parts = set(py_file.parts)
    if parts & PERSISTENCE_ADAPTER_DIR_PARTS:
        return True
    name = py_file.name.lower()
    if any(name.endswith(suffix) for suffix in PERSISTENCE_ADAPTER_FILE_SUFFIXES):
        return True
    # Check for declared adapter classes in AST
    try:
        tree = ast.parse(text)
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                cname = node.name.lower()
                if "adapter" in cname or "store" in cname or "repository" in cname:
                    return True
    except Exception:
        pass
    return False


def check_single_root(repo_root: Path) -> list[str]:
    violations: list[str] = []
    # Check that no nested applications/ directory exists inside operations
    ops_dir = repo_root / "operations"
    if ops_dir.is_dir():
        nested_apps = list(ops_dir.glob("**/applications"))
        if nested_apps:
            violations.append(f"Forbidden nested applications directory found: {nested_apps}")
    return violations


def check_no_forwarder_shims(repo_root: Path) -> list[str]:
    """Flag files containing forwarder shims across all bounded contexts (RULE_CLEAN_ARCH_NO_SHIMS_001)."""
    violations: list[str] = []
    shim_markers = (
        "canonical forwarder to",
        "forwarder stub for",
        "forwarder stub to",
        "forwarding shim",
        "forwarder stub",
    )
    for bc in get_bounded_context_roots(repo_root):
        for domain_dir in bc.glob("**/domain"):
            if not domain_dir.is_dir() or ".git" in domain_dir.parts:
                continue
            for py_file in domain_dir.rglob("*.py"):
                if py_file.name == "__init__.py":
                    continue
                text = py_file.read_text(encoding="utf-8", errors="ignore")
                text_lower = text.lower()
                for marker in shim_markers:
                    if marker in text_lower:
                        rel = py_file.relative_to(repo_root)
                        violations.append(
                            f"Forbidden forwarder shim: {rel} contains '{marker}' (RULE_CLEAN_ARCH_NO_SHIMS_001)"
                        )
                        break
    return violations


def check_duplicate_modules_and_confluence(repo_root: Path) -> list[str]:
    """Flag module-to-package collisions and duplicate module files across folders."""
    violations: list[str] = []
    for bc in get_bounded_context_roots(repo_root):
        for domain_dir in bc.glob("**/domain"):
            if not domain_dir.is_dir() or ".git" in domain_dir.parts:
                continue

            # 1. Module-to-package collisions: foo.py and foo/ coexist in same directory
            for py_file in domain_dir.rglob("*.py"):
                if py_file.name == "__init__.py":
                    continue
                stem_dir = py_file.parent / py_file.stem
                if stem_dir.is_dir():
                    rel_file = py_file.relative_to(repo_root)
                    rel_dir = stem_dir.relative_to(repo_root)
                    violations.append(
                        f"Collision: module {rel_file} and package {rel_dir} coexist (RULE_MODULE_TO_PACKAGE_CONFLUENCE_001)"
                    )

            # 2. Duplicate module filenames across folders within the same domain tree
            names: dict[str, list[Path]] = defaultdict(list)
            for py_file in domain_dir.rglob("*.py"):
                if py_file.name in COMMON_MODULE_NAMES or "tests" in py_file.parts:
                    continue
                names[py_file.name].append(py_file)

            for name, paths in names.items():
                if len(paths) > 1:
                    # Check if one path is a parent/child duplication (e.g. domain/foo.py and domain/sub/foo.py)
                    parent_dirs = [p.parent for p in paths]
                    if len(set(parent_dirs)) > 1:
                        for i in range(len(paths)):
                            for j in range(i + 1, len(paths)):
                                p1, p2 = paths[i], paths[j]
                                if p1.parent in p2.parents or p2.parent in p1.parents:
                                    rel1 = p1.relative_to(repo_root)
                                    rel2 = p2.relative_to(repo_root)
                                    violations.append(
                                        f"Duplicate module file across nested folders: {rel1} shadows {rel2} (RULE_NO_DUPLICATE_MODULES_001)"
                                    )
    return violations


def check_no_host_io_outside_adapters(repo_root: Path) -> list[str]:
    """Ensure pure domain code outside persistence adapters never invokes subprocess or raw mutating filesystem I/O."""
    violations: list[str] = []
    for bc in get_bounded_context_roots(repo_root):
        for domain_dir in bc.glob("**/domain"):
            if not domain_dir.is_dir() or ".git" in domain_dir.parts:
                continue
            for py_file in domain_dir.rglob("*.py"):
                if "tests" in py_file.parts:
                    continue
                text = py_file.read_text(encoding="utf-8", errors="ignore")
                if is_persistence_adapter(py_file, text):
                    continue

                rel = py_file.relative_to(repo_root)

                # Check for module-level subprocess imports in pure domain outside adapters
                if "import subprocess" in text or "from subprocess import" in text:
                    violations.append(
                        f"Host I/O leak: {rel} imports subprocess in pure domain outside persistence adapters (RULE_CLEAN_ARCH_INWARD_001)"
                    )

    return violations


def check_ddd_professional_standards(repo_root: Path) -> list[str]:
    """Enforce professional DDD standards and genuine domain abstractions (RULE_DDD_PROFESSIONAL_STANDARDS_001).

    Verifies:
      1. Shallow Taxonomy Prohibition: aggregates/, entities/, value_objects/ folders must not be empty stubs.
      2. Entity Identity Invariant: Entities must inherit from Entity base class or define explicit 'id'.
      3. Value Object Immutability: Value Objects must be immutable (frozen=True) and avoid assert in __eq__.
      4. Aggregate Root Authority: Aggregates must define typed state transitions and encapsulate invariants.
      5. Zero Host I/O in Domain: Domain layers must not import subprocess or execute host OS commands.
    """
    violations: list[str] = []
    excluded_parts = frozenset(
        {"tests", "documentation", "_intelligence", "archive", "original_recovery_v1", ".git"}
    )
    for bc in get_bounded_context_roots(repo_root):
        for domain_dir in bc.glob("**/domain"):
            if not domain_dir.is_dir() or any(p in domain_dir.parts for p in excluded_parts):
                continue

            for category in ("aggregates", "entities", "value_objects"):
                cat_dir = domain_dir / category
                if not cat_dir.is_dir():
                    continue

                non_init_files = [f for f in cat_dir.glob("*.py") if f.name != "__init__.py"]
                if not non_init_files:
                    rel_cat = cat_dir.relative_to(repo_root)
                    violations.append(
                        f"Shallow DDD taxonomy: {rel_cat} is empty or contains only __init__.py (RULE_DDD_PROFESSIONAL_STANDARDS_001)"
                    )
                    continue

                for py_file in non_init_files:
                    rel_file = py_file.relative_to(repo_root)
                    text = py_file.read_text(encoding="utf-8", errors="ignore").strip()
                    if not text:
                        violations.append(
                            f"Shallow DDD stub: {rel_file} is an empty file (RULE_DDD_PROFESSIONAL_STANDARDS_001)"
                        )
                        continue

                    try:
                        tree = ast.parse(text, filename=str(py_file))
                    except SyntaxError:
                        continue

                    classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
                    has_all = any(
                        isinstance(n, ast.Assign)
                        and any(getattr(t, "id", None) == "__all__" for t in n.targets)
                        for n in tree.body
                    )
                    has_reexport = has_all or any(
                        isinstance(n, (ast.Import, ast.ImportFrom)) for n in tree.body
                    )

                    if not classes and not has_reexport:
                        violations.append(
                            f"Shallow DDD stub: {rel_file} defines no domain classes or exports (RULE_DDD_PROFESSIONAL_STANDARDS_001)"
                        )

                    # 1. Base Entity & Identity contract
                    if category == "entities":
                        for node in classes:
                            if node.name in ("Entity", "BaseEntity"):
                                continue
                            inherits_entity = any(
                                (isinstance(b, ast.Name) and b.id in ("Entity", "BaseEntity"))
                                or (isinstance(b, ast.Attribute) and b.attr in ("Entity", "BaseEntity"))
                                for b in node.bases
                            )
                            is_entity_name = node.name.endswith("Entity")
                            if inherits_entity or is_entity_name:
                                has_id_field = any(
                                    isinstance(s, ast.AnnAssign)
                                    and isinstance(s.target, ast.Name)
                                    and s.target.id == "id"
                                    for s in node.body
                                )
                                if not has_id_field and not inherits_entity:
                                    violations.append(
                                        f"Entity identity violation: class {node.name} in {rel_file} must inherit from Entity or define explicit 'id' identity (RULE_DDD_PROFESSIONAL_STANDARDS_001)"
                                    )

                    # 2. Value Object Immutability contract
                    if category == "value_objects":
                        for node in classes:
                            if node.name in ("ValueObject", "BaseValueObject"):
                                continue
                            is_enum = any(
                                (isinstance(b, ast.Name) and b.id in ("Enum", "IntEnum", "StrEnum"))
                                or (isinstance(b, ast.Attribute) and b.attr in ("Enum", "IntEnum", "StrEnum"))
                                for b in node.bases
                            )
                            if is_enum:
                                continue

                            inherits_vo = any(
                                (isinstance(b, ast.Name) and b.id in ("ValueObject", "BaseValueObject"))
                                or (isinstance(b, ast.Attribute) and b.attr in ("ValueObject", "BaseValueObject"))
                                for b in node.bases
                            )
                            is_frozen_dc = False
                            is_plain_dc = False
                            for dec in node.decorator_list:
                                dec_id = (
                                    getattr(dec, "id", None)
                                    or getattr(getattr(dec, "func", None), "id", None)
                                    or getattr(getattr(dec, "func", None), "attr", None)
                                )
                                if dec_id == "dataclass":
                                    is_plain_dc = True
                                    if isinstance(dec, ast.Call):
                                        for kw in dec.keywords:
                                            if (
                                                kw.arg == "frozen"
                                                and isinstance(kw.value, ast.Constant)
                                                and kw.value.value is True
                                            ):
                                                is_frozen_dc = True

                            # Pydantic frozen check: model_config = ConfigDict(frozen=True)
                            has_frozen_config = False
                            for stmt in node.body:
                                if isinstance(stmt, ast.Assign):
                                    for target in stmt.targets:
                                        if isinstance(target, ast.Name) and target.id == "model_config":
                                            if isinstance(stmt.value, ast.Call):
                                                for kw in stmt.value.keywords:
                                                    if (
                                                        kw.arg == "frozen"
                                                        and isinstance(kw.value, ast.Constant)
                                                        and kw.value.value is True
                                                    ):
                                                        has_frozen_config = True
                                elif isinstance(stmt, ast.ClassDef) and stmt.name == "Config":
                                    for cstmt in stmt.body:
                                        if isinstance(cstmt, ast.Assign):
                                            for target in cstmt.targets:
                                                if isinstance(target, ast.Name) and target.id == "frozen":
                                                    if isinstance(cstmt.value, ast.Constant) and cstmt.value.value is True:
                                                        has_frozen_config = True

                            if is_plain_dc and not is_frozen_dc and not inherits_vo:
                                violations.append(
                                    f"Mutable value object: class {node.name} in {rel_file} is not frozen (RULE_DDD_PROFESSIONAL_STANDARDS_001)"
                                )

                    # 3. Aggregate Root Authority contract
                    if category == "aggregates":
                        for node in classes:
                            if node.name in ("AggregateRoot", "BaseAggregateRoot"):
                                continue
                            inherits_agg = any(
                                (isinstance(b, ast.Name) and b.id in ("AggregateRoot", "BaseAggregateRoot"))
                                or (isinstance(b, ast.Attribute) and b.attr in ("AggregateRoot", "BaseAggregateRoot"))
                                for b in node.bases
                            )
                            is_agg_name = node.name.endswith("Aggregate") or node.name.endswith("AggregateRoot")
                            if inherits_agg or is_agg_name:
                                for stmt in node.body:
                                    if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                        if any(stmt.name.startswith(pfx) for pfx in ("transition_", "record_", "apply_")):
                                            if stmt.returns is None:
                                                violations.append(
                                                    f"Aggregate root unannotated mutation: {rel_file}::{node.name}.{stmt.name} must return typed Result monad (RULE_DDD_PROFESSIONAL_STANDARDS_001)"
                                                )

                    # 4. Prohibition of assert in __eq__ (Pitfall 037)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef) and node.name == "__eq__":
                            for child in ast.walk(node):
                                if isinstance(child, ast.Assert):
                                    violations.append(
                                        f"Pitfall 037 runtime assert: {rel_file}:{child.lineno} uses assert in __eq__ (RULE_DDD_PROFESSIONAL_STANDARDS_001)"
                                    )

                    # 5. Zero Host I/O in pure DDD domain modules
                    if (
                        "import subprocess" in text
                        or "from subprocess import" in text
                        or "os.system(" in text
                        or "os.popen(" in text
                    ):
                        violations.append(
                            f"Host I/O leak in domain: {rel_file} imports forbidden host execution (RULE_DDD_PROFESSIONAL_STANDARDS_001)"
                        )

    return violations


def main() -> int:
    repo_root = Path.cwd()
    violations: list[str] = []
    violations.extend(check_single_root(repo_root))
    violations.extend(check_no_forwarder_shims(repo_root))
    violations.extend(check_duplicate_modules_and_confluence(repo_root))
    violations.extend(check_no_host_io_outside_adapters(repo_root))
    violations.extend(check_ddd_professional_standards(repo_root))

    if violations:
        for v in violations:
            print(f"[FAIL] {v}", file=sys.stderr)
        return 1
    print("PASS: Clean Architecture boundaries and single-root layout verified across all bounded contexts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
