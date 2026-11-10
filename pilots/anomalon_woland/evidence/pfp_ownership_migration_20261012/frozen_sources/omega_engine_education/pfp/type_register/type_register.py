"""Typed register of every PFP data type, plus the census that keeps it complete.

AuthorityEffect: None.

A *type* here is a Pydantic model or an ``Enum`` subclass defined at module
level in a tracked ``.py`` file of the PFP (its root, plus
``omega_engine_education/code/``; see :func:`resolve`). Test files, ``demos/`` and
``papers/`` are outside the census: demo-local types live and die with their demo, and
each paper package is a hermetic deposit that must not import another paper's code, so
its types are not shared PFP types (three papers each define their own ``MoveType``).

The register (``type_register.yaml``) holds one row per module that defines
types, the public class names defined in more than one module, groups of types
that describe one fact under different names, and types derived from another
type. The census reads the source tree with ``ast`` only, so it imports nothing
it scans.
"""

from __future__ import annotations

import ast
from collections import defaultdict
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Annotated, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, StrictStr, model_validator

_MODEL_ROOTS = frozenset({"BaseModel", "RootModel"})
_ENUM_ROOTS = frozenset({"Enum", "StrEnum", "IntEnum"})
_EXCLUDED_TOP = frozenset({"demos", "papers", "pilots", "workflows"})

ModulePath = StrictStr
TypeRef = Annotated[StrictStr, Field(pattern=r"^[a-z0-9_/]+\.py::[A-Z][A-Za-z0-9]*$")]
"""``<module path>::<ClassName>``."""


class _Frozen(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class World(str, Enum):
    """Which import world a module belongs to."""

    COLOCATED = "colocated"  # beside the files it types; loaded by file path
    RUNTIME = "runtime"  # the python/ import root (domain, use_cases, infrastructure)
    GENERATED = "generated"  # written by a generator from a YAML source


class Source(str, Enum):
    """Which side states the shape of the module's types."""

    PYDANTIC = "pydantic"  # only the .py states it; YAML, if any, is data or generated
    YAML = "yaml"  # a YAML file states it; the .py is generated from that file
    BOTH_PARITY_TESTED = "both_parity_tested"  # both hand-written; a test compares them
    BOTH_UNCHECKED = "both_unchecked"  # both hand-written; no test compares them


class YamlRole(str, Enum):
    JSON_SCHEMA = "json_schema"  # hand-written JSON Schema 2020-12
    GENERATED_JSON_SCHEMA = "generated_json_schema"  # written by a generator
    CUSTOM_SCHEMA = "custom_schema"  # a repo-specific field-spec dialect, not JSON Schema
    DATA = "data"  # instances the module validates (registers, catalogs, specs)


class Status(str, Enum):
    CANONICAL = "canonical"
    REVIEW = "review"  # placement, overlap or drift awaits the owner's decision


class YamlRef(_Frozen):
    path: StrictStr = Field(min_length=1)  # a file, or a glob for many data files
    role: YamlRole


class ModuleRow(_Frozen):
    path: ModulePath = Field(pattern=r"^[a-z0-9_/]+\.py$")
    world: World
    source: Source
    yaml: tuple[YamlRef, ...] = ()
    tests: tuple[StrictStr, ...] = ()
    status: Status
    note: StrictStr | None = None

    @model_validator(mode="after")
    def _source_is_named(self) -> ModuleRow:
        roles = {y.role for y in self.yaml}
        stated = roles & {YamlRole.JSON_SCHEMA, YamlRole.CUSTOM_SCHEMA}
        if (self.world is World.GENERATED) != (self.source is Source.YAML):
            raise ValueError(f"GENERATED_IFF_YAML_SOURCE: {self.path}")
        if self.source is not Source.PYDANTIC and not stated:
            raise ValueError(f"YAML_SOURCE_NOT_NAMED: {self.path}")
        if self.source is Source.PYDANTIC and stated:
            raise ValueError(f"PYDANTIC_SOURCE_LISTS_A_HAND_WRITTEN_SCHEMA: {self.path}")
        if self.source is Source.BOTH_PARITY_TESTED and not self.tests:
            raise ValueError(f"PARITY_CLAIM_WITHOUT_TEST: {self.path}")
        if self.status is Status.REVIEW and not self.note:
            raise ValueError(f"REVIEW_ROW_NEEDS_A_NOTE: {self.path}")
        return self


class NameCollision(_Frozen):
    """A public type name defined in two or more modules. The list may only shrink."""

    name: StrictStr = Field(pattern=r"^[A-Z][A-Za-z0-9]*$")
    modules: tuple[ModulePath, ...] = Field(min_length=2)
    disposition: StrictStr = Field(min_length=1)


class OverlapGroup(_Frozen):
    """Types that describe one fact under different names. Each group should end as one type."""

    fact: StrictStr = Field(pattern=r"^[a-z][a-z0-9_]*$")
    types: tuple[TypeRef, ...] = Field(min_length=2)
    disposition: StrictStr = Field(min_length=1)


class DerivedType(_Frozen):
    """A stored type that is a function of other data. It should become a view or computed field."""

    type: TypeRef
    of: tuple[StrictStr, ...] = Field(min_length=1)  # type refs, or file globs
    kind: Literal["projection", "join", "aggregate", "computed"]
    checked_by: StrictStr | None = None  # "<test file>::<test function>"


class TypeRegister(_Frozen):
    schema_: Literal["pfp.type-register.v1"] = Field(alias="schema")
    authority_effect: Literal["None"]
    modules: tuple[ModuleRow, ...]
    name_collisions: tuple[NameCollision, ...]
    overlaps: tuple[OverlapGroup, ...]
    derived: tuple[DerivedType, ...]

    @model_validator(mode="after")
    def _unique_and_sorted(self) -> TypeRegister:
        for label, keys in (
            ("MODULE", [m.path for m in self.modules]),
            ("COLLISION", [c.name for c in self.name_collisions]),
            ("OVERLAP", [o.fact for o in self.overlaps]),
            ("DERIVED", [d.type for d in self.derived]),
        ):
            if keys != sorted(set(keys)):
                raise ValueError(f"{label}_ROWS_MUST_BE_UNIQUE_AND_SORTED")
        return self


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


def code_dir(root: Path) -> Path:
    """Where the PFP Python moved (relocated from legacy code/ to pfp/python)."""
    if len(root.parents) > 1:
        pfp_python = root.parents[1] / "pfp" / "python"
        if pfp_python.is_dir():
            return root.parents[1] / "pfp"
    return root.parents[1] / "code"


def _unwrap_forwarder(path: Path) -> Path:
    if path.is_file() and path.suffix == ".py" and path.name != "__init__.py":
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            has_class = any(isinstance(node, ast.ClassDef) for node in tree.body)
            if not has_class:
                for node in tree.body:
                    if isinstance(node, ast.ImportFrom) and node.module and node.level > 0:
                        parts = node.module.split(".")
                        target = path.parent
                        for p in parts:
                            target = target / p
                        target_file = target.with_suffix(".py")
                        if target_file.is_file():
                            return target_file
        except Exception:
            pass
    return path


def resolve(root: Path, rel: str) -> Path:
    """The file a register path names.

    Register paths keep the spelling they had under the PFP root, so ids built
    from them stay stable. ``python/`` lives in :func:`code_dir` (now under ``pfp/python``),
    ``notebook_lib/`` lives in ``education_app/frontend/notebook_lib``, and
    tests live in ``pfp/tests`` or ``education_app/tests/curriculum``.
    """
    if rel == "type_register/type_register.py" and len(root.parents) > 1:
        reg_file = root.parents[1] / "pfp" / "type_register" / "type_register.py"
        if reg_file.is_file():
            return reg_file
    head, _, rest = rel.partition("/")
    pfp_dir = root.parents[1] / "pfp" if len(root.parents) > 1 else root
    education_root = root.parents[1] if len(root.parents) > 1 else root.parent

    if head == "python":
        cand = pfp_dir / "python" / rest
        if cand.is_file():
            return _unwrap_forwarder(cand)
        cand = code_dir(root) / rel
        if cand.is_file():
            return _unwrap_forwarder(cand)
    if head == "notebook_lib":
        cand = education_root / "education_app" / "frontend" / "notebook_lib" / rest
        if cand.is_file():
            return _unwrap_forwarder(cand)
        cand = code_dir(root) / rel
        if cand.is_file():
            return _unwrap_forwarder(cand)
    if head == "code":
        tname = Path(rest).name
        for cand in (
            pfp_dir / rest,
            pfp_dir / "tests" / tname,
            pfp_dir / "tests" / "types" / tname,
            pfp_dir / "tests" / "protocol" / tname,
            pfp_dir / "tests" / "sn" / tname,
            education_root / "education_app" / "tests" / "curriculum" / tname,
            code_dir(root) / rest,
        ):
            if cand.is_file():
                return _unwrap_forwarder(cand)
        return _unwrap_forwarder(code_dir(root) / rest)
    if Path(rel).name in {"pfp_data_types.py", "pfp_data_types.yaml"} and len(root.parents) > 1:
        pfp_data = pfp_dir / "_canonical_types" / Path(rel).name
        if pfp_data.is_file():
            return _unwrap_forwarder(pfp_data)
    if rel.startswith("pilots/") and len(root.parents) > 1:
        pilots_dir = education_root / "pilots"
        target_name = Path(rel).name
        for cand_pilot in (
            pilots_dir / rel.removeprefix("pilots/"),
            pilots_dir / "matrix" / target_name,
            pilots_dir / target_name,
        ):
            if cand_pilot.is_file():
                return _unwrap_forwarder(cand_pilot)
    cand = root / rel
    if cand.is_file():
        return _unwrap_forwarder(cand)
    if len(root.parents) > 1:
        for check in (
            pfp_dir / "infrastructure" / "yaml_data" / rel,
            pfp_dir / rel,
            pfp_dir / "domain" / rel,
            pfp_dir / "domain" / Path(rel).name,
            pfp_dir / "infrastructure" / "yaml_data" / Path(rel).name,
            pfp_dir / "type_register" / Path(rel).name,
            pfp_dir / Path(rel).name,
        ):
            if check.is_file():
                return _unwrap_forwarder(check)
    return cand


def glob(root: Path, pattern: str) -> list[Path]:
    """``Path.glob`` over register paths, resolved as :func:`resolve` does."""
    head, _, rest = pattern.partition("/")
    pfp_dir = root.parents[1] / "pfp" if len(root.parents) > 1 else root
    education_root = root.parents[1] if len(root.parents) > 1 else root.parent

    if head == "python":
        matches = list((pfp_dir / "python").glob(rest))
        if matches:
            return matches
        return list(code_dir(root).glob(pattern))
    if head == "notebook_lib":
        matches = list((education_root / "education_app" / "frontend" / "notebook_lib").glob(rest))
        if matches:
            return matches
        return list(code_dir(root).glob(pattern))
    if head == "code":
        matches = list(pfp_dir.glob(rest))
        if matches:
            return matches
        return list(code_dir(root).glob(rest))
    if pattern.startswith("pilots/") and len(root.parents) > 1:
        pilots_dir = education_root / "pilots"
        sub = pattern.removeprefix("pilots/")
        matches = list(pilots_dir.glob(sub))
        if matches:
            return matches
        matches = list((pilots_dir / "matrix").glob(Path(sub).name))
        if matches:
            return matches
    res = list(root.glob(pattern))
    if res:
        return res
    if len(root.parents) > 1:
        for base in (
            pfp_dir / "infrastructure" / "yaml_data",
            pfp_dir / "domain",
            pfp_dir / "type_register",
            pfp_dir,
        ):
            if base.is_dir():
                matches = list(base.glob(pattern))
                if matches:
                    return matches
                if "/" in pattern:
                    _, _, sub = pattern.partition("/")
                    sub_matches = list(base.glob(sub))
                    if sub_matches:
                        return sub_matches
    return []


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
    import subprocess

    out = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", "*.py"],
        cwd=cwd,
        capture_output=True,
        check=True,
    ).stdout.decode("utf-8")
    return [p for p in out.split("\0") if p]


def tracked_python_files(root: Path) -> list[str]:
    """Tracked and not-yet-ignored ``.py`` files of the PFP, as register paths, in census scope."""
    found = set(_ls_python(root))
    cd = code_dir(root)
    if (cd / "python").is_dir():
        for p in _ls_python(cd / "python"):
            found.add(f"python/{p}")
    if (cd / "notebook_lib").is_dir():
        for p in _ls_python(cd / "notebook_lib"):
            found.add(f"notebook_lib/{p}")
    elif cd.is_dir():
        for p in _ls_python(cd):
            head = p.partition("/")[0]
            if head in ("python", "notebook_lib"):
                found.add(p)
    if len(root.parents) > 1:
        pfp_dir = root.parents[1] / "pfp"
        yaml_data = pfp_dir / "infrastructure" / "yaml_data"
        if yaml_data.is_dir():
            for p in _ls_python(yaml_data):
                found.add(p)
        if (pfp_dir / "type_register" / "type_register.py").is_file():
            found.add("type_register/type_register.py")
        if (pfp_dir / "_canonical_types" / "pfp_data_types.py").is_file():
            found.add("_canonical_types/pfp_data_types.py")
    return sorted(p for p in found if in_census(p) and resolve(root, p).is_file())


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
