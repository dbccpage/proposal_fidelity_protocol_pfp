"""Audit epic plans for acceptance criteria that no mutation could break.

An acceptance criterion is a promise about what would count as failure. A
criterion that names no falsifier is not a weak criterion -- it is not a
criterion, because nothing can turn it red and every implementation satisfies it.

`EPIC-OE-SYMGAM-011` states its gate as:

    All genesis, observer regime, and Landau quiz tests pass.

A suite containing one trivial assertion satisfies that exactly.

Measured across the Symbol Game series when this module was written:

    SYMGAM-001 .. SYMGAM-010   5 decisive mutations each, without exception
    SYMGAM-011 .. SYMGAM-016   0

The break is clean rather than a gradient, which is what a hardening pass that
stopped partway looks like. This module makes that measurement repeatable so the
next six sprints do not each rediscover it independently.

What it does NOT do: judge whether a declared mutation is a *good* one. It counts
declarations and finds criteria sections with none. Deciding that a named
mutation is decisive is a reviewer's job, and pretending otherwise would make
this module the same kind of unfalsifiable instrument it exists to find.

AuthorityEffect: None. Counting falsifiers is not certifying an epic.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

#: Where epic plans live, relative to the repository root.
EPIC_DIRECTORY = "omega_engine_product_planning_office/plans/epics"

#: The phrase the hardened epics use to introduce a falsifier.
MUTATION_PATTERN = re.compile(r"decisive\s+mutation", re.IGNORECASE)

#: The heading that opens an acceptance-criteria section.
CRITERIA_HEADING = re.compile(
    r"^#{1,6}\s*\d*\.?\s*.*acceptance\s+criteria.*$", re.IGNORECASE | re.MULTILINE
)

#: Phrases that describe a gate without saying what would fail it. Each is a
#: real formulation found in the estate, not an invented strawman.
VACUOUS_PATTERNS = (
    re.compile(r"all\s+\w[\w\s,]*tests?\s+pass", re.IGNORECASE),
    re.compile(r"test\s+suite\s+passes", re.IGNORECASE),
    re.compile(r"\bbuilds?\s+(?:successfully|cleanly)\b", re.IGNORECASE),
    re.compile(r"\bno\s+(?:errors?|warnings?)\b", re.IGNORECASE),
)


class EpicCriteriaError(ValueError):
    """The audit cannot produce a verdict from what it was given."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"EPIC_CRITERIA_ERROR[{code}]: {detail}")
        self.code = code
        self.detail = detail


@dataclass(frozen=True, slots=True)
class EpicCriteriaFinding:
    """One epic's falsifiability profile.

    ``mutations`` and ``vacuous_phrases`` are counts rather than booleans so an
    epic declaring one falsifier stays distinguishable from one declaring five.
    """

    path: str
    epic_id: str
    mutations: int
    vacuous_phrases: int
    has_criteria_section: bool

    @property
    def is_falsifiable(self) -> bool:
        """True when the epic names at least one way to fail."""
        return self.mutations > 0

    def render(self) -> str:
        verdict = "FALSIFIABLE" if self.is_falsifiable else "UNFALSIFIABLE"
        return (
            f"{verdict:14s} {self.epic_id}  "
            f"mutations={self.mutations} vacuous={self.vacuous_phrases}"
        )


def epic_id_of(path: Path) -> str:
    """Recover the epic id from its filename.

    Filenames follow ``epic_oe_<family>_<nnn>_<slug>_plan.md``. The id is the
    family and number, uppercased -- the form the plans cite each other by.

    The family is **not** always a single token: `epic_oe_oewas_rust_001_...`
    exists in this estate. So the number is located as the first all-digit
    segment and the family is everything before it, rather than assuming a
    fixed position. A parser that assumed one token silently mis-ids that epic.
    """
    stem = path.stem
    parts = stem.split("_")
    if len(parts) < 4 or parts[0] != "epic":
        raise EpicCriteriaError("UNPARSEABLE_NAME", f"{path.name} is not an epic plan")
    for index in range(2, len(parts)):
        if parts[index].isdigit():
            family = "_".join(parts[2:index])
            if not family:
                break
            return f"EPIC-OE-{family.upper()}-{parts[index]}"
    raise EpicCriteriaError(
        "UNPARSEABLE_NAME", f"{path.name} has no epic number where one is expected"
    )


def audit_epic_text(path: str, epic_id: str, text: str) -> EpicCriteriaFinding:
    """Profile one epic's text. Pure, so the policy is testable without a tree."""
    return EpicCriteriaFinding(
        path=path,
        epic_id=epic_id,
        mutations=len(MUTATION_PATTERN.findall(text)),
        vacuous_phrases=sum(
            len(pattern.findall(text)) for pattern in VACUOUS_PATTERNS
        ),
        has_criteria_section=bool(CRITERIA_HEADING.search(text)),
    )


def audit_epic_file(repo_root: Path, path: Path) -> EpicCriteriaFinding:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise EpicCriteriaError("UNREADABLE", f"{path}: {error}") from error
    relative = path.relative_to(repo_root).as_posix()
    return audit_epic_text(relative, epic_id_of(path), text)


def audit_epics(repo_root: Path, family: str | None = None) -> list[EpicCriteriaFinding]:
    """Profile every epic plan, optionally narrowed to one family.

    Refuses an empty inventory rather than reporting that zero epics are all
    falsifiable, which is the shape of vacuous pass this module exists to name.
    """
    directory = repo_root / EPIC_DIRECTORY
    if not directory.is_dir():
        raise EpicCriteriaError("NO_EPIC_DIRECTORY", str(directory))
    pattern = f"epic_oe_{family}_*.md" if family else "epic_*.md"
    paths = sorted(path for path in directory.glob(pattern) if path.is_file())
    if not paths:
        raise EpicCriteriaError(
            "EMPTY_INVENTORY",
            f"no epic plans matched {pattern!r}; refusing to report 0 of 0 as audited",
        )
    return [audit_epic_file(repo_root, path) for path in paths]


def unfalsifiable(findings: list[EpicCriteriaFinding]) -> list[EpicCriteriaFinding]:
    """The epics whose gates nothing could turn red."""
    return [finding for finding in findings if not finding.is_falsifiable]


def format_report(findings: list[EpicCriteriaFinding]) -> str:
    """Render a profile, leading with what is wrong."""
    if not findings:
        raise EpicCriteriaError("EMPTY_INVENTORY", "no findings to report")
    failing = unfalsifiable(findings)
    lines = ["Epic acceptance-criteria falsifiability", ""]
    lines.extend(finding.render() for finding in findings)
    lines.append("")
    lines.append(
        f"{len(findings) - len(failing)} of {len(findings)} epics name a falsifier; "
        f"{len(failing)} name none"
    )
    if failing:
        lines.append("")
        lines.append("Unfalsifiable gates -- nothing can turn these red:")
        lines.extend(f"  {finding.epic_id}  {finding.path}" for finding in failing)
    lines.append("AuthorityEffect: None")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Declared targets
#
# Three consecutive sprints found an epic's stated starting point disagreeing
# with the tree: 031 named a runtime home that did not exist, 032 named two
# deliverables that were already built under a different module name, and 033
# named two whose subject had left the repository entirely.
#
# That is checkable. An epic naming a target nobody can resolve is not
# necessarily wrong -- the work may be exactly to create it -- but it is worth
# knowing before planning rather than during discovery.
# ---------------------------------------------------------------------------

TARGET_LINE = re.compile(r"^\*\*Target Crates:\*\*\s*(?P<targets>.+)$", re.MULTILINE)
BACKTICKED = re.compile(r"`([^`]+)`")

#: Where the Cargo workspace keeps its crates.
CRATES_ROOT = "omega_engine/crates_rs"


def declared_targets(text: str) -> list[str]:
    """Every target an epic names on its `Target Crates` line."""
    match = TARGET_LINE.search(text)
    if match is None:
        return []
    return [item.strip() for item in BACKTICKED.findall(match.group("targets"))]


def resolve_target(repo_root: Path, target: str) -> bool:
    """Whether a declared target exists on disk.

    Two forms appear in this estate:

    * a repository-relative path, checked directly;
    * a Rust module path ``crate::module``, which resolves to
      ``omega_engine/crates_rs/<crate>/src/<module>.rs`` or that module as a
      directory.

    A module path naming only a crate resolves to the crate directory.
    """
    if "::" not in target:
        # A bare name is either a repository-relative path or a crate name. The
        # first version tried only the path, and reported `omega_symbol_game_runtime`
        # unresolved while the crate sat in `crates_rs` -- a false positive in the
        # tool written to find false starting points.
        if (repo_root / target).exists():
            return True
        return (repo_root / CRATES_ROOT / target).is_dir()
    parts = target.split("::")
    crate = repo_root / CRATES_ROOT / parts[0]
    if not crate.is_dir():
        return False
    if len(parts) == 1:
        return True
    module = crate / "src" / Path(*parts[1:])
    return module.with_suffix(".rs").is_file() or module.is_dir()


@dataclass(frozen=True, slots=True)
class TargetFinding:
    """One epic's declared targets, resolved against the tree."""

    epic_id: str
    resolved: tuple[str, ...]
    unresolved: tuple[str, ...]

    @property
    def declares_targets(self) -> bool:
        return bool(self.resolved or self.unresolved)


def audit_targets(repo_root: Path, family: str | None = None) -> list[TargetFinding]:
    """Resolve every epic's declared targets against the repository."""
    directory = repo_root / EPIC_DIRECTORY
    if not directory.is_dir():
        raise EpicCriteriaError("NO_EPIC_DIRECTORY", str(directory))
    pattern = f"epic_oe_{family}_*.md" if family else "epic_*.md"
    paths = sorted(path for path in directory.glob(pattern) if path.is_file())
    if not paths:
        raise EpicCriteriaError(
            "EMPTY_INVENTORY",
            f"no epic plans matched {pattern!r}; refusing to report 0 of 0 as audited",
        )
    findings: list[TargetFinding] = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        resolved: list[str] = []
        unresolved: list[str] = []
        for target in declared_targets(text):
            (resolved if resolve_target(repo_root, target) else unresolved).append(target)
        findings.append(
            TargetFinding(
                epic_id=epic_id_of(path),
                resolved=tuple(resolved),
                unresolved=tuple(unresolved),
            )
        )
    return findings


def format_target_report(findings: list[TargetFinding]) -> str:
    """Render target resolution, leading with what does not resolve."""
    if not findings:
        raise EpicCriteriaError("EMPTY_INVENTORY", "no findings to report")
    lines = ["Epic declared-target resolution", ""]
    missing = [f for f in findings if f.unresolved]
    for finding in missing:
        for target in finding.unresolved:
            lines.append(f"UNRESOLVED  {finding.epic_id}  {target}")
    if not missing:
        lines.append("every declared target resolves")
    total = sum(len(f.resolved) + len(f.unresolved) for f in findings)
    resolved = sum(len(f.resolved) for f in findings)
    lines.append("")
    lines.append(f"{resolved} of {total} declared targets resolve")
    lines.append(
        "An unresolved target is not necessarily wrong -- the work may be to "
        "create it. It is a question to settle before planning, not during."
    )
    lines.append("AuthorityEffect: None")
    return "\n".join(lines)


def main(argv: "list[str] | None" = None) -> int:
    """Report falsifiability for the epic estate.

    Exit 0 when every audited epic names a falsifier, 1 when any does not, 2 on
    a refusal. Reporting is the point: this is a diagnostic, and it is wired
    nowhere that would let it block a merge on its own.
    """
    import argparse

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Audit epic acceptance criteria.")
    parser.add_argument("--repo-root", default=".", help="repository root")
    parser.add_argument("--family", default=None, help="narrow to one epic family")
    parser.add_argument(
        "--targets",
        action="store_true",
        help="resolve declared Target Crates against the tree instead",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    if args.targets:
        try:
            targets = audit_targets(repo_root, args.family)
        except EpicCriteriaError as error:
            print(str(error))
            return 2
        print(format_target_report(targets))
        return 1 if any(f.unresolved for f in targets) else 0

    try:
        findings = audit_epics(repo_root, args.family)
    except EpicCriteriaError as error:
        print(str(error))
        return 2
    print(format_report(findings))
    return 1 if unfalsifiable(findings) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
