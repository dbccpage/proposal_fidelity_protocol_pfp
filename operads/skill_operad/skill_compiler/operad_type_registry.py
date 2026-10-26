#!/usr/bin/env python3
"""Operad type registry gate: the YAML type registry against the code and data that declare it.

The registry is ``skill_operad/yaml/operad_types/*.yaml``. Each type names its canonical value
set and every source that declares or uses it today: a Python enum, ``Literal`` or constant, a
Rust enum or struct, a field in a JSON or YAML data file, or a field in skill frontmatter. The
gate extracts each source and fails when its values differ from the values the registry records
for it, so a source cannot drift without the registry being updated in the same change.

A type is ``SETTLED`` when every source agrees with the canonical set, and ``PROPOSED`` when at
least one does not; a proposed type carries the decision a human must make. A source that
``declares`` a type must hold exactly the canonical values, one that ``uses`` it must hold a subset,
and ``part`` sources must together cover the set. An open Rust carrier agrees only with an open type.

AuthorityEffect: None. Reads the tree and writes nothing; ``--observe`` prints extracted values.
"""

from __future__ import annotations

import argparse
import importlib
import json
import re
import sys
import typing
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import yaml

REGISTRY_DIR = Path(__file__).resolve().parents[1] / "yaml" / "operad_types"
STATUSES = frozenset({"SETTLED", "PROPOSED"})
SOURCE_KINDS = ("python", "rust_enum", "rust_struct", "data", "skills")
ROLES = ("declares", "uses", "part")
_RUST_ENUM = r"pub enum {name}\b[^{{]*\{{(?P<body>.*?)\n\}}"


@dataclass(frozen=True)
class Finding:
    type_id: str
    code: str
    detail: str

    def __str__(self) -> str:
        return f"{self.code} {self.type_id}: {self.detail}"


def repo_root(start: Path = Path(__file__).resolve()) -> Path:
    return next(p for p in start.parents if (p / "omega_engine_operads").is_dir() and (p / "pyproject.toml").is_file())


def _resolve(module: str, path: str):
    """Follow ``Name.attr[key].attr`` from a module; ``[key]`` indexes a mapping."""
    value = importlib.import_module(module)
    for step in re.findall(r"[^.\[\]]+|\[[^\]]+\]", path):
        value = value[step[1:-1]] if step.startswith("[") else getattr(value, step)
    return value


def _python(ref: str, field: str = "value") -> list:
    module, _, attribute = ref.partition(":")
    value = _resolve(module, attribute)
    if hasattr(value, "annotation") and not isinstance(value, type):
        value = value.annotation  # a pydantic FieldInfo
    if isinstance(value, type) and issubclass(value, Enum):
        return [member.name if field == "name" else member.value for member in value]
    if typing.get_origin(value) is typing.Literal:
        return list(typing.get_args(value))
    if isinstance(value, dict):
        return sorted(key.__name__ if isinstance(key, type) else key for key in value)
    if isinstance(value, (tuple, list)):
        return list(value)
    if isinstance(value, (set, frozenset)):
        return sorted(value)
    raise TypeError(f"unsupported python source {ref}")


def _rust_enum(root: Path, ref: str) -> list:
    path, _, name = ref.partition("#")
    text = (root / path).read_text(encoding="utf-8")
    match = re.search(_RUST_ENUM.format(name=re.escape(name)), text, re.DOTALL)
    if match is None:
        raise ValueError(f"enum {name} not found in {path}")
    body = re.sub(r"//[^\n]*|#\[[^\]]*\]", "", match.group("body"))
    variants, depth, token = [], 0, ""
    for char in body:
        depth += char in "({"
        depth -= char in ")}"
        if depth == 0 and char == ",":
            variants.append(token)
            token = ""
        else:
            token += char
    variants.append(token)
    return [re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)", item).group(1) for item in variants if item.strip()]


def _rust_fn_map(root: Path, source: dict) -> dict[str, str]:
    """Read ``Enum::Variant => "literal"`` arms of one Rust function, e.g. ``DdcOp::letter``."""
    path, _, name = source["rust_enum"].partition("#")
    text = (root / path).read_text(encoding="utf-8")
    body = re.search(rf"fn {re.escape(source['rust_map'])}\b.*?\n    \}}", text, re.DOTALL)
    if body is None:
        raise ValueError(f"fn {source['rust_map']} not found in {path}")
    return dict(re.findall(rf"{re.escape(name)}::(\w+)\s*=>\s*\"([^\"]*)\"", body.group(0)))


def _rust_struct(root: Path, ref: str) -> list:
    path, _, name = ref.partition("#")
    if re.search(rf"pub struct {re.escape(name)}\b", (root / path).read_text(encoding="utf-8")) is None:
        raise ValueError(f"struct {name} not found in {path}")
    return []  # An open carrier: it declares no closed value set.


def _select(node, parts: list[str]):
    if not parts:
        yield node
        return
    head, rest = parts[0], parts[1:]
    if head == "*":
        items = node.values() if isinstance(node, dict) else node
        for item in items:
            yield from _select(item, rest)
    elif isinstance(node, dict) and head in node:
        yield from _select(node[head], rest)


def _document(path: Path):
    raw = path.read_text(encoding="utf-8")
    return json.loads(raw) if path.suffix == ".json" else yaml.safe_load(raw)


def _data(root: Path, source: dict) -> list:
    paths = sorted(root.glob(source["data"])) if "*" in source["data"] else [root / source["data"]]
    if not paths:
        raise ValueError(f"no file matches {source['data']}")
    found = [item for path in paths for item in _select(_document(path), source["select"].split("."))]
    mode = source.get("mode", "list")
    if mode == "keys":
        return [key for item in found for key in item]
    if mode == "qualified":
        return [f"{key}.{value}" for item in found for key, values in item.items() for value in values]
    flat = [value for item in found for value in (item if isinstance(item, list) else [item])]
    return sorted(set(flat), key=str) if mode == "distinct" else flat


def _frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    return yaml.safe_load(text.split("---", 2)[1]) or {}


def _skills(root: Path, source: dict) -> list:
    pattern = re.compile(source["skills"])
    skills = root / "omega_engine_operads" / "skills"
    names = sorted(p.name for p in skills.iterdir()
                   if p.is_dir() and pattern.search(p.name) and (p / "SKILL.md").is_file())
    field = source.get("field")
    if field is None:
        return names
    return sorted({str(_frontmatter(skills / name / "SKILL.md").get(field)) for name in names})


def extract(root: Path, source: dict) -> list:
    kinds = [kind for kind in SOURCE_KINDS if kind in source]
    if len(kinds) != 1:
        raise ValueError(f"a source names exactly one of {SOURCE_KINDS}: {source}")
    kind = kinds[0]
    if kind == "python":
        return _python(source["python"], source.get("field", "value"))
    if kind == "rust_enum":
        return _rust_enum(root, source["rust_enum"])
    if kind == "rust_struct":
        return _rust_struct(root, source["rust_struct"])
    if kind == "data":
        return _data(root, source)
    return _skills(root, source)


def load_registry(directory: Path = REGISTRY_DIR) -> list[dict]:
    types = []
    for path in sorted(directory.glob("*.yaml")):
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        for entry in document.get("types", []):
            types.append({**entry, "_file": path.name})
    return types


def _same(left: list, right: list) -> bool:
    return set(map(str, left)) == set(map(str, right))


def _agrees(role: str, observed: list, canonical: set[str]) -> bool:
    seen = set(map(str, observed))
    return seen <= canonical if role in ("uses", "part") else seen == canonical


def _label(source: dict) -> str:
    for kind in SOURCE_KINDS:
        if kind in source:
            return f"{kind}:{source[kind]}" + (f" [{source['select']}]" if "select" in source else "")
    return str(source)


def check_type(root: Path, entry: dict, canonical_of: dict[str, set[str]] | None = None) -> list[Finding]:
    type_id = entry.get("id", "?")
    findings = []
    canonical = entry.get("canonical") or {}
    status = canonical.get("status")
    if status not in STATUSES:
        return [Finding(type_id, "STATUS_INVALID", f"status must be one of {sorted(STATUSES)}")]
    values = set(map(str, canonical.get("values") or []))
    if not values:
        findings.append(Finding(type_id, "CANONICAL_EMPTY", "a type needs canonical values"))
    agree, parts = [], set()
    for source in entry.get("sources") or []:
        role = source.get("role", "declares")
        if role not in ROLES:
            findings.append(Finding(type_id, "ROLE_INVALID", f"{_label(source)}: role {role}"))
            continue
        try:
            observed = extract(root, source)
            compared = observed
            if "rust_map" in source:
                mapping = _rust_fn_map(root, source)
                compared = [mapping.get(item, item) for item in observed]
        except (ImportError, AttributeError, OSError, ValueError, TypeError, KeyError) as error:
            findings.append(Finding(type_id, "SOURCE_UNREADABLE", f"{source}: {error}"))
            continue
        recorded = source.get("values") or []
        if not _same(observed, recorded):
            findings.append(Finding(type_id, "SOURCE_DRIFT",
                f"{_label(source)} declares {observed}, registry records {recorded}"))
        if "rust_struct" in source:
            agree.append(not canonical.get("closed", True))  # an open carrier fits only an open type
            continue
        if role == "part":
            parts |= set(map(str, compared))
        agree.append(_agrees(role, compared, values))
    if parts and parts != values:
        agree.append(False)
    alphabet = canonical.get("letters_of")
    if alphabet:
        letters = (canonical_of or {}).get(alphabet, set())
        agree.append(all(char in letters for value in values for char in value))
    if not agree:
        findings.append(Finding(type_id, "NO_SOURCES", "every type names at least one source"))
    elif status == "SETTLED" and not all(agree):
        findings.append(Finding(type_id, "SETTLED_BUT_DIVERGENT", "a source differs from the canonical set"))
    elif status == "PROPOSED" and all(agree):
        findings.append(Finding(type_id, "PROPOSED_BUT_AGREED", "every source agrees; mark it SETTLED"))
    if status == "PROPOSED" and not str(canonical.get("decision", "")).strip():
        findings.append(Finding(type_id, "DECISION_MISSING", "a proposed type states the decision needed"))
    return findings


def run(root: Path, directory: Path = REGISTRY_DIR) -> tuple[list[dict], list[Finding]]:
    types = load_registry(directory)
    canonical_of = {entry.get("id"): set(map(str, (entry.get("canonical") or {}).get("values") or []))
                    for entry in types}
    findings = []
    seen = set()
    for entry in types:
        if entry.get("id") in seen:
            findings.append(Finding(entry.get("id", "?"), "DUPLICATE_ID", entry["_file"]))
        seen.add(entry.get("id"))
        findings.extend(check_type(root, entry, canonical_of))
    return types, findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--observe", action="store_true", help="print every source's extracted values")
    args = parser.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # DDC letters include U+039B
    root = (args.repo_root or repo_root()).resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    types, findings = run(root)
    if args.observe:
        for entry in types:
            for source in entry.get("sources") or []:
                try:
                    print(entry["id"], "|", _label(source), "|", json.dumps(extract(root, source), ensure_ascii=False))
                except Exception as error:  # observation only reports; the gate itself fails closed
                    print(entry["id"], "|", _label(source), "| ERROR", error)
        return 0
    statuses = {status: sum(1 for t in types if (t.get("canonical") or {}).get("status") == status)
                for status in sorted(STATUSES)}
    for finding in findings:
        print(finding)
    print(f"types={len(types)} " + " ".join(f"{k}={v}" for k, v in statuses.items())
          + f" findings={len(findings)} AuthorityEffect=None")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
