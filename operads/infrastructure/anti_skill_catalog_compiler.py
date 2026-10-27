"""Compile the anti-pattern estate into anti-skill records.

Each ``operads/patterns/anti/**/AP_*.md`` becomes one record: the negative twin of a skill,
with its declared colours read through the canon (``Witness`` is a finding, so ``Audit``),
its residual, and its dual healthy pattern. A dual is ``reciprocal`` when the healthy
pattern names this anti-pattern back, ``one_sided`` when it names another, and
``unresolved`` when no healthy pattern has that id. Every record is ``Candidate`` with an
``UNBOUND`` detector: the detection signatures are prose with examples, not checks.

AuthorityEffect: None. ``--write`` writes ``anti_skill_catalog.v1.json``; ``--check`` fails
when the committed file differs from a fresh compile.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

from operads.canon import TYPES

SCHEMA = "core.oewas.anti_skill_catalog.v1"
ANTI_ROOT = Path("operads/patterns/anti")
HELPFUL_ROOT = Path("operads/patterns/helpful")
OUTPUT = Path("operads/skill_operad/json/anti_skill_catalog.v1.json")
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
COLOURS = frozenset(TYPES["operad_colour"]["values"])  # type: ignore[arg-type]
COLOUR_ALIASES: dict[str, str] = dict(TYPES["operad_colour"]["legacy_map"])  # type: ignore[arg-type]
STATUS = "Candidate"


class AntiSkillCatalogRefusal(ValueError):
    pass


def _lf_text(path: Path) -> str:
    return path.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")


def _frontmatter(path: Path, text: str) -> dict:
    match = FRONTMATTER.match(text)
    if match is None:
        raise AntiSkillCatalogRefusal(f"{path.as_posix()}: no frontmatter")
    data = yaml.safe_load(match.group(1))
    if type(data) is not dict:
        raise AntiSkillCatalogRefusal(f"{path.as_posix()}: frontmatter is not a mapping")
    return data


def _keys(pattern_id: str, name: str, stem: str) -> set[str]:
    """The ids a dual reference may use: the bare id, id_name, or the file stem."""
    return {pattern_id, f"{pattern_id}_{name}", stem, stem.upper()}


def _colour(value: object, path: Path) -> str:
    if type(value) is not str:
        raise AntiSkillCatalogRefusal(f"{path.as_posix()}: colour must be a string")
    colour = COLOUR_ALIASES.get(value, value)
    if colour not in COLOURS:
        raise AntiSkillCatalogRefusal(f"{path.as_posix()}: {value!r} is not an operad colour")
    return colour


def _helpful_index(repo_root: Path) -> dict[str, tuple[str, str]]:
    """Every key a healthy pattern answers to -> (its path, the dual it names)."""
    index: dict[str, tuple[str, str]] = {}
    for path in sorted((repo_root / HELPFUL_ROOT).rglob("*.md")):
        text = _lf_text(path)
        if not FRONTMATTER.match(text):
            continue
        data = _frontmatter(path, text)
        relative = path.relative_to(repo_root).as_posix()
        for key in _keys(str(data.get("pattern_id", "")), str(data.get("name", "")), path.stem):
            index[key] = (relative, str(data.get("dual_pattern", "")))
    return index


def compile_anti_skills(repo_root: Path) -> dict:
    helpful = _helpful_index(repo_root)
    records = []
    for path in sorted((repo_root / ANTI_ROOT).rglob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        text = _lf_text(path)
        data = _frontmatter(path, text)
        relative = path.relative_to(repo_root).as_posix()
        pattern_id = data.get("pattern_id")
        if type(pattern_id) is not str or not pattern_id:
            raise AntiSkillCatalogRefusal(f"{relative}: pattern_id is required")
        own_keys = _keys(pattern_id, str(data.get("name", "")), path.stem)
        dual = str(data.get("dual_pattern", "")).removesuffix(".md")
        dual_path, dual_names = helpful.get(dual, (None, ""))
        if dual_path is None:
            pairing = "unresolved"
        elif dual_names in own_keys:
            pairing = "reciprocal"
        else:
            pairing = "one_sided"
        sources = data.get("operad_source_colours")
        target = data.get("operad_target_colour")
        records.append(
            {
                "anti_skill_id": pattern_id,
                "name": data.get("name"),
                "language": data.get("language"),
                "source_path": relative,
                "source_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "source_colours": None if sources is None else [_colour(c, path) for c in sources],
                "target_colour": None if target is None else _colour(target, path),
                "residual_effect": data.get("operad_residual"),
                "failure_class": data.get("failure_class"),
                "dual_pattern": dual,
                "dual_path": dual_path,
                "pairing": pairing,
                "detection_signature": "## Detection Signature" in text,
                "status": STATUS,
                "detector": "UNBOUND",
                "authority_effect": "none",
            }
        )
    ids = [record["anti_skill_id"] for record in records]
    duplicates = sorted(identifier for identifier, n in Counter(ids).items() if n > 1)
    if duplicates:
        raise AntiSkillCatalogRefusal(f"duplicate anti-skill ids {duplicates}")
    records.sort(key=lambda record: record["anti_skill_id"])
    pairing = Counter(record["pairing"] for record in records)
    return {
        "schema_version": SCHEMA,
        "authority_effect": "none",
        "summary": {
            "anti_skills": len(records),
            "typed": sum(record["target_colour"] is not None for record in records),
            "reciprocal_pairs": pairing["reciprocal"],
            "one_sided_pairs": pairing["one_sided"],
            "unresolved_duals": pairing["unresolved"],
        },
        "anti_skills": records,
    }


def render(catalog: dict) -> bytes:
    return (json.dumps(catalog, indent=2, ensure_ascii=True) + "\n").encode("ascii")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    root = args.repo_root.resolve()
    try:
        payload = render(compile_anti_skills(root))
    except (AntiSkillCatalogRefusal, OSError, UnicodeError, yaml.YAMLError) as exc:
        print(f"ANTI_SKILL_CATALOG_REFUSED: {exc}", file=sys.stderr)
        return 1
    target = root / OUTPUT
    if args.write:
        target.write_bytes(payload)
    elif not target.is_file() or target.read_bytes().replace(b"\r\n", b"\n") != payload:
        print(f"ANTI_SKILL_CATALOG_DRIFT: {OUTPUT.as_posix()} differs; run --write", file=sys.stderr)
        return 1
    summary = json.loads(payload)["summary"]
    print(" ".join(f"{key}={value}" for key, value in summary.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
