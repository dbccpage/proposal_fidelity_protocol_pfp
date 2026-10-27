"""Aim the lossless parser at the skill garden.

`EPIC-OE-OEWAS-002` states the Lossless Roundtrip Law:

    unparse(parse(doc)) == doc   byte-for-byte

`LosslessSkillDocument` partitions the bytes and `render` concatenates them.
`SkillBytePartition` is that partition as a type. There is no
`LosslessSkillParser` class. A repository-wide search for `round_trips` found
no caller outside the parser's own module, so the law held as a property of a
function nobody pointed at anything.

That is sprint 028's finding in a different package: hermetic machinery proves
the mechanism; only a run over the shipped estate proves the estate. This module
is the caller.

What it measures, over `operads/skills/`:

* every skill document round trips byte-for-byte;
* every skill declares the four required `operad_*` fields, correctly typed;
* how many declare the optional `families` field.

`families` is **optional, as a measured fact rather than an assumption.** The
epic lists it alongside the four `operad_*` fields as a typed operad signature.
It is present in 53 of 133 tracked skills. The schema therefore separates
required from optional and reports exact coverage rather than inventing a
verdict.

The caller supplies the tracked entrypoint inventory. When that inventory is
omitted, this module reads the skill directories on disk and does not invoke
git. `_shared` and `_templates` are still excluded. Injected test inventories
name meta-package exclusions explicitly.

AuthorityEffect: None. Parsing a skill is not admitting it.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from operads.canon import OPERAD_COLOUR
from operations.domain.cicd.disk_binding import require_byte_reader

#: Authored source; interactive host roots are generated views.
CANONICAL_SKILLS_ROOT = "operads/skills"

#: Fields every skill must declare, with the type each must hold.
REQUIRED_OPERAD_FIELDS: tuple[str, ...] = (
    "operad_source_colours",
    "operad_target_colour",
    "operad_arity",
    "operad_residual",
)

#: Declared by the epic alongside the required four, and present in a minority
#: of skills. Optional here because the garden says so, not because it seemed
#: convenient -- see the module docstring.
OPTIONAL_FIELDS: tuple[str, ...] = ("families",)

#: Directories under the skills root that are infrastructure, not skills. Named
#: explicitly so an unreadable package cannot be mistaken for an excluded one.
META_PACKAGES: frozenset[str] = frozenset({"_shared", "_templates"})

#: The closed operad colour vocabulary, read from the operad canon
#: (`code/rust/core_operad_canon`).
#:
#: Closed on purpose: an operation whose colour is outside this set cannot be
#: composed with anything, and silently admitting it would make composability
#: depend on spelling.
#:
#: Sprint 035's version of this audit type-checked colours as *strings* and never
#: compared them to the vocabulary. A skill declaring `"Governance"` -- not one
#: of the ten -- passed that audit and crashed `load_garden()` in sprint 037.
#: Checking the type without checking the domain is how that got through.
OPERAD_COLOURS: frozenset[str] = frozenset(OPERAD_COLOUR)


class FrontmatterAuditError(ValueError):
    """The audit cannot produce a verdict from what it was given."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"SKILL_FRONTMATTER_ERROR[{code}]: {detail}")
        self.code = code
        self.detail = detail


def _holds_nonempty_strings(value: list[Any]) -> bool:
    return all(isinstance(item, str) and item for item in value)


def _source_colours_problem(field: str, value: Any) -> str | None:
    # Empty is legitimate. `ooutwire` declares `[]` with `operad_arity: 0`:
    # a nullary operation consumes no source colours.
    if not isinstance(value, list):
        return f"{field} must be a list, got {type(value).__name__}"
    if not _holds_nonempty_strings(value):
        return f"{field} must hold non-empty strings"
    outside = sorted(set(value) - OPERAD_COLOURS)
    if not outside:
        return None
    return (
        f"{field} names colours outside the closed vocabulary: {outside}; "
        f"an operation with such a colour cannot be composed with anything"
    )


def _target_colour_problem(field: str, value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return f"{field} must be a non-empty string, got {type(value).__name__}"
    if value not in OPERAD_COLOURS:
        return (
            f"{field} {value!r} is outside the closed vocabulary; "
            f"an operation with such a colour cannot be composed with anything"
        )
    return None


def _residual_problem(field: str, value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return f"{field} must be a non-empty string, got {type(value).__name__}"
    return None


def _arity_problem(field: str, value: Any) -> str | None:
    # `bool` is an `int` in Python, and an arity of `True` is not an arity.
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return f"{field} must be a non-negative integer, got {value!r}"
    return None


def _families_problem(field: str, value: Any) -> str | None:
    if not isinstance(value, list) or not value:
        return f"{field} must be a non-empty list when declared"
    if not _holds_nonempty_strings(value):
        return f"{field} must hold non-empty strings"
    return None


_FIELD_PROBLEMS = {
    "operad_source_colours": _source_colours_problem,
    "operad_target_colour": _target_colour_problem,
    "operad_residual": _residual_problem,
    "operad_arity": _arity_problem,
    "families": _families_problem,
}


def _type_problem(field: str, value: Any) -> str | None:
    """The schema, dispatched per field so each rule stays under the complexity cap."""
    checker = _FIELD_PROBLEMS.get(field)
    if checker is None:
        return None
    return checker(field, value)


def _arity_agreement_problem(mapping: dict[str, Any]) -> str | None:
    """An operation's arity is how many source colours it consumes.

    Not stated anywhere in the epic, and held by 110 of the garden's 112 skills
    when this was first measured -- so it is the convention, discovered by
    running the audit rather than by reading the plan.

    The two skills that disagreed were the two added earlier in the same session
    that wrote this check, each declaring two source colours with arity 1. The
    audit found its author's own defect, which is the argument for pointing it
    at the estate rather than at fixtures.
    """
    colours = mapping.get("operad_source_colours")
    arity = mapping.get("operad_arity")
    if not isinstance(colours, list) or isinstance(arity, bool):
        return None
    if not isinstance(arity, int):
        return None
    if len(colours) != arity:
        return (
            f"operad_arity is {arity} but operad_source_colours holds "
            f"{len(colours)}; arity is how many source colours are consumed"
        )
    return None


@dataclass(frozen=True, slots=True)
class SkillFrontmatterFinding:
    """One skill document's audit result.

    `round_trips` is carried alongside the schema findings rather than gating
    them: a document can fail the byte-for-byte law and still have readable
    frontmatter, and conflating the two would hide whichever came second.
    """

    package: str
    round_trips: bool
    missing_required: tuple[str, ...]
    type_problems: tuple[str, ...]
    declares_families: bool

    @property
    def is_clean(self) -> bool:
        return (
            self.round_trips
            and not self.missing_required
            and not self.type_problems
        )

    def render(self) -> str:
        if self.is_clean:
            return f"OK        {self.package}"
        reasons = []
        if not self.round_trips:
            reasons.append("does not round trip")
        if self.missing_required:
            reasons.append(f"missing {list(self.missing_required)}")
        reasons.extend(self.type_problems)
        return f"VIOLATION {self.package}  {'; '.join(reasons)}"


class SkillParseFailure(Exception):
    """The registered parser refused a document. The message is the parser's."""


_SKILL_PARSER: Callable[[bytes], Any] | None = None


def register_skill_parser(parser: Callable[[bytes], Any]) -> None:
    """Register the skill-byte parser used by ``audit_document``."""
    global _SKILL_PARSER
    _SKILL_PARSER = parser


def _parse_skill_document(raw: bytes) -> Any:
    if _SKILL_PARSER is None:
        raise RuntimeError("No skill parser registered in domain port registry.")
    return _SKILL_PARSER(raw)


def _effective_signature(mapping: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Read legacy fields or the existing typed compiler's string metadata.

    This normalizes an audit view, not source bytes or runtime admission.
    Conflicting declarations remain errors rather than selecting one silently.
    """
    metadata = mapping.get("metadata")
    if not isinstance(metadata, dict) or metadata.get("core-generated") != "oewas.typed-capability.v1":
        return mapping, []
    effective, problems = dict(mapping), []
    for field, key, encoded in (
        ("operad_source_colours", "core-source-colours", True),
        ("operad_target_colour", "core-target-colour", False),
        ("operad_arity", "core-arity", True),
        ("operad_residual", "core-residual", False),
    ):
        if key not in metadata:
            continue
        value = metadata[key]
        if type(value) is not str:
            problems.append(f"metadata.{key} must be a string")
        elif encoded:
            try:
                value = json.loads(value)
            except ValueError:
                problems.append(f"metadata.{key} is not valid JSON")
        if field in mapping and (
            type(mapping[field]) is not type(value) or mapping[field] != value
        ):
            problems.append(f"{field} disagrees with metadata.{key}")
        effective[field] = value
    return effective, problems


def audit_document(package: str, raw: bytes) -> SkillFrontmatterFinding:
    """Audit one skill document's bytes. Pure, so the schema is testable."""
    try:
        document = _parse_skill_document(raw)
    except SkillParseFailure as error:
        return SkillFrontmatterFinding(
            package=package,
            round_trips=False,
            missing_required=REQUIRED_OPERAD_FIELDS,
            type_problems=(f"unparseable: {error}",),
            declares_families=False,
        )

    round_trips = document.render() == raw

    try:
        mapping = document.frontmatter_mapping()
    except SkillParseFailure as error:
        return SkillFrontmatterFinding(
            package=package,
            round_trips=round_trips,
            missing_required=REQUIRED_OPERAD_FIELDS,
            type_problems=(f"frontmatter unreadable: {error}",),
            declares_families=False,
        )

    mapping, problems = _effective_signature(mapping)
    missing = tuple(field for field in REQUIRED_OPERAD_FIELDS if field not in mapping)
    for field in REQUIRED_OPERAD_FIELDS + OPTIONAL_FIELDS:
        if field in mapping:
            problem = _type_problem(field, mapping[field])
            if problem is not None:
                problems.append(problem)

    arity_problem = _arity_agreement_problem(mapping)
    if arity_problem is not None:
        problems.append(arity_problem)

    return SkillFrontmatterFinding(
        package=package,
        round_trips=round_trips,
        missing_required=missing,
        type_problems=tuple(problems),
        declares_families="families" in mapping,
    )


def skill_packages(
    repo_root: Path,
    *,
    tracked_entrypoints: tuple[str, ...] | None = None,
) -> list[Path]:
    """Direct skill packages. A caller may inject the tracked inventory.

    This domain function does not invoke git. An omitted inventory is the
    skill directories on disk.
    """
    root = repo_root / CANONICAL_SKILLS_ROOT
    if not root.is_dir():
        raise FrontmatterAuditError("NO_SKILLS_ROOT", str(root))
    if tracked_entrypoints is None:
        tracked_entrypoints = tuple(
            path.relative_to(repo_root).as_posix()
            for path in sorted(root.glob("*/SKILL.md"))
            if path.parent.name not in META_PACKAGES
        )
    canonical: list[Path] = []
    for relative in tracked_entrypoints:
        parts = relative.replace("\\", "/").split("/")
        if (
            len(parts) != 4
            or parts[:2] != ["operads", "skills"]
            or parts[3] != "SKILL.md"
            or parts[2] in META_PACKAGES
            or parts[2].startswith(("_", "."))
        ):
            raise FrontmatterAuditError("TRACKED_ENTRYPOINT_REFUSED", relative)
        canonical.append(repo_root / "operads" / "skills" / parts[2])
    return sorted(set(canonical), key=lambda item: item.name)


def audit_garden(
    repo_root: Path,
    *,
    tracked_entrypoints: tuple[str, ...] | None = None,
) -> list[SkillFrontmatterFinding]:
    """Audit every skill in the canonical host.

    Refuses an empty garden. Reporting that all zero skills round trip is a
    claim true because nothing was examined.

    A package missing its `SKILL.md` is a **finding**, not a skip: the two look
    identical in a summary and only one of them is intended.
    """
    packages = skill_packages(repo_root, tracked_entrypoints=tracked_entrypoints)
    if not packages:
        raise FrontmatterAuditError(
            "EMPTY_GARDEN",
            "no skill packages found; refusing to report 0 of 0 as audited",
        )
    findings: list[SkillFrontmatterFinding] = []
    for package in packages:
        document = package / "SKILL.md"
        if not document.is_file():
            findings.append(
                SkillFrontmatterFinding(
                    package=package.name,
                    round_trips=False,
                    missing_required=REQUIRED_OPERAD_FIELDS,
                    type_problems=("no SKILL.md",),
                    declares_families=False,
                )
            )
            continue
        findings.append(
            audit_document(package.name, require_byte_reader().read_bytes(str(document)))
        )
    return findings


def violations(findings: list[SkillFrontmatterFinding]) -> list[SkillFrontmatterFinding]:
    return [finding for finding in findings if not finding.is_clean]


def families_coverage(findings: list[SkillFrontmatterFinding]) -> tuple[int, int]:
    """How many skills declare the optional field, as an exact pair.

    A pair rather than a percentage: 53 of 133 stays reproducible and a
    percentage does not.
    """
    return (
        sum(1 for finding in findings if finding.declares_families),
        len(findings),
    )


def format_report(findings: list[SkillFrontmatterFinding]) -> str:
    """Render an audit, leading with the violations."""
    if not findings:
        raise FrontmatterAuditError("EMPTY_GARDEN", "no findings to report")
    failing = violations(findings)
    lines = ["Skill frontmatter and lossless-roundtrip audit", ""]
    lines.extend(finding.render() for finding in failing)
    if not failing:
        lines.append("every skill round trips and declares the required operad fields")
    declared, total = families_coverage(findings)
    lines.append("")
    lines.append(f"{total - len(failing)} of {total} skills clean")
    lines.append(
        f"optional field 'families' declared by {declared} of {total} "
        "-- a measurement, not a requirement"
    )
    lines.append("AuthorityEffect: None")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Report the audit. Exit 1 when any skill violates, 2 on a refusal."""
    import argparse

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Audit skill frontmatter.")
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args(argv)
    repo_root = Path(args.repo_root).resolve()

    # The parser lives in a sibling package with no packaging metadata, so a
    # script invocation has to put the repository root on the path itself. Tests
    # get this from pytest's rootdir; a CLI does not.
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    try:
        findings = audit_garden(repo_root)
    except FrontmatterAuditError as error:
        print(str(error))
        return 2
    print(format_report(findings))
    return 1 if violations(findings) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
