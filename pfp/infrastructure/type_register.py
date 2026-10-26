"""Type-register files and AST census over the canonical application.

The domain owns the validated models; this module owns source/resource I/O.
"""

from __future__ import annotations

import ast
from collections import defaultdict
from functools import lru_cache
from pathlib import Path, PurePosixPath

import yaml

from omega_engine_pfp.domain.type_register.type_register import (
    DerivedType,
    ModulePath,
    ModuleRow,
    NameCollision,
    OverlapGroup,
    Source,
    Status,
    TypeRef,
    TypeRegister,
    World,
    YamlRef,
    YamlRole,
)

_MODEL_ROOTS = frozenset({"BaseModel", "RootModel"})
_ENUM_ROOTS = frozenset({"Enum", "StrEnum", "IntEnum"})
_EXCLUDED_TOP = frozenset({"demos", "papers", "pilots", "workflows"})


def load_register(path: Path) -> TypeRegister:
    return TypeRegister.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8")), strict=False
    )


# --- census -------------------------------------------------------------------


def _name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        return _name(node.value)
    return None


@lru_cache(maxsize=128)
def code_dir(root: Path) -> Path:
    """Use the canonical package for its documents and retain isolated scans."""
    application = Path(__file__).resolve().parents[1]
    resolved = root.resolve()
    education = application.parent / "omega_engine_education"
    if resolved.is_relative_to(application) or resolved.is_relative_to(education):
        return application
    return resolved




def resolve(root: Path, rel: str) -> Path:
    """Resolve an exact current register path within its declared package."""
    native = Path(rel)
    if native.is_absolute() or native.drive or ".." in native.parts or ".." in PurePosixPath(rel).parts:
        raise ValueError("REGISTER_PATH_OUTSIDE_PACKAGE")
    candidate = (code_dir(root) / rel).resolve()
    if not candidate.is_relative_to(code_dir(root)):
        raise ValueError("REGISTER_PATH_OUTSIDE_PACKAGE")
    return candidate


def glob(root: Path, pattern: str) -> list[Path]:
    """Expand only an explicit pattern beneath the current package."""
    native = Path(pattern)
    if native.is_absolute() or native.drive or ".." in native.parts or ".." in PurePosixPath(pattern).parts:
        raise ValueError("REGISTER_PATH_OUTSIDE_PACKAGE")
    matches = sorted(p.resolve() for p in code_dir(root).glob(pattern) if p.is_file())
    if any(not p.is_relative_to(code_dir(root)) for p in matches):
        raise ValueError("REGISTER_PATH_OUTSIDE_PACKAGE")
    return matches


def in_census(path: str) -> bool:
    parts = PurePosixPath(path).parts
    name = parts[-1]
    return (
        name.endswith(".py")
        and parts[0] not in _EXCLUDED_TOP
        and "tests" not in parts
        and not name.startswith("test_")
        and name != "conftest.py"
    )


def _ls_python(cwd: Path) -> list[str]:
    # Pure Python traversal to ensure zero host subprocess coupling in domain (RULE_CLEAN_ARCH_INWARD_001)
    res: list[str] = []
    if not cwd.is_dir():
        return res
    for p in cwd.rglob("*.py"):
        try:
            rel = p.relative_to(cwd).as_posix()
        except ValueError:
            continue
        parts = rel.split("/")
        if any(part.startswith(".") or part in ("__pycache__", "build", "dist", "node_modules", ".git") for part in parts):
            continue
        res.append(rel)
    return sorted(res)


def tracked_python_files(root: Path) -> list[str]:
    """Current Python files, including unstaged additions, in census scope."""
    return [p for p in _ls_python(code_dir(root)) if in_census(p)]


def scan_types(root: Path, files: list[str]) -> dict[str, list[str]]:
    """Return ``{module path: [type names]}`` for module-level models and enums.

    Inheritance is resolved by base-class name across the scanned files, per
    definition: a class is a type when one of its bases is a model or enum root,
    or names a class already found to be a type.
    """
    classes: dict[tuple[str, str], list[str]] = {}
    for rel in files:
        tree = ast.parse(resolve(root, rel).read_text(encoding="utf-8"), filename=rel)
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                classes[(rel, node.name)] = [n for b in node.bases if (n := _name(b))]
    found: set[tuple[str, str]] = set()
    changed = True
    while changed:
        changed = False
        known = {n for _, n in found} | _MODEL_ROOTS | _ENUM_ROOTS
        for key, bases in classes.items():
            if key not in found and any(b in known for b in bases):
                found.add(key)
                changed = True
    out: dict[str, list[str]] = defaultdict(list)
    for rel, name in sorted(found):
        out[rel].append(name)
    return dict(out)


def collisions(types: dict[str, list[str]]) -> dict[str, tuple[str, ...]]:
    """Public names (no leading underscore) defined in two or more modules."""
    where: dict[str, set[str]] = defaultdict(set)
    for rel, names in types.items():
        for name in names:
            if not name.startswith("_"):
                where[name].add(rel)
    return {n: tuple(sorted(m)) for n, m in sorted(where.items()) if len(m) > 1}


def _is_json_schema(path: Path) -> bool:
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    return isinstance(doc, dict) and ("$schema" in doc or "$defs" in doc)


def _ref_problem(root: Path, types: dict[str, list[str]], ref: str) -> str | None:
    rel, _, cls = ref.partition("::")
    if cls:
        return None if cls in types.get(rel, []) else f"NOT_A_TYPE {ref}"
    return None if glob(root, rel) else f"NO_FILE_MATCHES {ref}"


def census_problems(root: Path, register: TypeRegister) -> list[str]:
    """Every difference between the source tree and the register, named."""
    types = scan_types(root, tracked_python_files(root))
    problems: list[str] = []
    rows = {m.path: m for m in register.modules}
    for rel in sorted(set(types) - set(rows)):
        problems.append(f"UNREGISTERED_TYPE_MODULE {rel}: {', '.join(types[rel])}")
    for rel in sorted(set(rows) - set(types)):
        problems.append(f"REGISTERED_MODULE_DEFINES_NO_TYPE {rel}")
    for row in register.modules:
        for ref in row.yaml:
            matches = sorted(glob(root, ref.path))
            if not matches:
                problems.append(f"MISSING_YAML {row.path} -> {ref.path}")
                continue
            schema_role = ref.role in (YamlRole.JSON_SCHEMA, YamlRole.GENERATED_JSON_SCHEMA)
            for match in matches:
                if match.suffix == ".yaml" and _is_json_schema(match) != schema_role:
                    problems.append(f"YAML_ROLE_WRONG {row.path} -> {ref.path} ({ref.role.value})")
        for test in row.tests:
            if not resolve(root, test).is_file():
                problems.append(f"MISSING_TEST {row.path} -> {test}")
    actual = collisions(types)
    declared = {c.name: c.modules for c in register.name_collisions}
    for name in sorted(set(actual) - set(declared)):
        problems.append(f"NEW_NAME_COLLISION {name}: {', '.join(actual[name])}")
    for name in sorted(set(declared) - set(actual)):
        problems.append(f"STALE_COLLISION_ROW {name}: remove it from the register")
    for name in sorted(set(actual) & set(declared)):
        if actual[name] != declared[name]:
            problems.append(f"COLLISION_MODULES_DIFFER {name}: {', '.join(actual[name])}")
    refs = [t for o in register.overlaps for t in o.types]
    refs += [r for d in register.derived for r in (d.type, *d.of)]
    problems += [p for ref in refs if (p := _ref_problem(root, types, ref))]
    for row in register.derived:
        if row.checked_by is not None:
            rel, _, fn = row.checked_by.partition("::")
            path = resolve(root, rel)
            if not path.is_file() or f"def {fn}(" not in path.read_text(encoding="utf-8"):
                problems.append(f"DERIVED_CHECK_MISSING {row.checked_by}")
    return problems
