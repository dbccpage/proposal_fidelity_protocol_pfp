"""Enforce the SCORING.md section 1.5 acceptance floor on every governed source.

AuthorityEffect: None.
Contract: urn:pfp-governance:checker:v1

For every source in the governed population (``governance/policy.json``) the
checker requires a companion ``<name>.contract.score.json`` whose current
contract and score bind the source's path and the SHA-256 of its exact bytes,
whose score is complete and arithmetically consistent (composite = weakest
gate, token = level + composite), whose cited evidence still resolves to the
hashed bytes, whose mutation accounting balances, and whose level and grade
meet the floor of the source's category. A source listed in
``governance/baseline.json`` with unchanged bytes is grandfathered.

A pass shows that such a record exists and binds the bytes. Whether the grades
are deserved is decided by reading the cited evidence.

Every input (policy, baseline, companions, run records) is admitted through
the Pydantic v2 models below (RULE_PY_001). The score model follows the
CodeScoringRecordV2 schema of SCORING.md section 6 and adds the per-gate
``basis`` and the ``evidence`` list that review needs.

Commands: ``check [--changed-since REF] [--json]``, ``population``,
``explain PATH`` and ``record SOURCE --contract FILE --score FILE``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess  # noqa: S404 - git is the only command, called with fixed arguments
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from fractions import Fraction
from pathlib import Path
from typing import Annotated, Literal, TextIO

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, ValidationError

GRADES: tuple[str, ...] = ("E", "D", "C", "B", "A", "A+")
LEVELS: tuple[str, ...] = ("L1", "L2", "L3", "L4", "L5")

Grade = Literal["E", "D", "C", "B", "A", "A+"]
Level = Literal["L1", "L2", "L3", "L4", "L5"]
Language = Literal["Python", "C#"]
Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
GateName = Literal["G1", "G2", "G3", "G4", "G5"]


class Record(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid", populate_by_name=True)


class Artifact(Record):
    path: str
    language: Language
    sha256: Digest


class EvidenceRef(Record):
    path: str
    sha256: Digest
    note: str = ""


class Gates(Record):
    G1: Grade | None
    G2: Grade | None
    G3: Grade | None
    G4: Grade | None
    G5: Grade | None

    def values(self) -> tuple[Grade | None, ...]:
        return (self.G1, self.G2, self.G3, self.G4, self.G5)


class MutationAccounting(Record):
    killed: int = Field(ge=0)
    survived: int = Field(ge=0)
    demonstrably_equivalent: int = Field(ge=0)
    invalid: int = Field(ge=0)
    inconclusive: int = Field(ge=0)
    unrun: int = Field(ge=0)
    conservative_ratio: float | None = Field(ge=0.0, le=1.0)
    report: EvidenceRef


class ScoreRecord(Record):
    schema_version: Literal["2.0.0"]
    authority_effect: Literal["None"] = Field(alias="AuthorityEffect")
    artifact: Artifact
    profile: Literal["Exact", "Quantized", "Numerical", "Symbolic/Formal", "Non-Numeric"]
    level: Level
    level_basis: str = Field(min_length=1)
    gates: Gates
    basis: dict[GateName, str]
    composite_grade: Grade | None
    score_token: str | None
    is_complete: bool
    grade_ceiling: Grade
    evaluation_timestamp: AwareDatetime
    evidence: tuple[EvidenceRef, ...]
    mutation_accounting: MutationAccounting | None = None


class ContractRecord(Record):
    authority_effect: Literal["None"] = Field(alias="AuthorityEffect")
    artifact: Artifact
    contract_urn: str = Field(pattern=r"^urn:[a-z0-9-]+:[A-Za-z0-9:._-]+$")
    symbols: tuple[str, ...]
    owned_invariants: tuple[str, ...] = Field(min_length=1)
    boundaries: tuple[str, ...]


class HistoryEntry(Record):
    recorded_at: datetime
    contract: ContractRecord
    score: ScoreRecord


class Companion(Record):
    schema_version: Literal["pfp.contract-score.v1"]
    authority_effect: Literal["None"] = Field(alias="AuthorityEffect")
    artifact: str
    contract: ContractRecord
    score: ScoreRecord
    history: tuple[HistoryEntry, ...]


class Population(Record):
    language: Language
    globs: tuple[str, ...]


class SupportCategory(Record):
    name: str
    globs: tuple[str, ...]
    min_level: Level
    min_grade: Grade
    status: str
    reason: str


class Floor(Record):
    min_level: Level
    min_grade: Grade
    statement: str


class Exclusions(Record):
    path_parts: tuple[str, ...]


class NotYetGoverned(Record):
    paths: tuple[str, ...]
    reason: str


class PinnedBoilerplate(Record):
    """Files admitted by their exact bytes alone, such as empty package markers."""

    glob: str
    sha256: Digest
    reason: str


class Policy(Record):
    schema_version: Literal["pfp.governance-policy.v1"]
    authority_effect: Literal["None"] = Field(alias="AuthorityEffect")
    description: str
    rubric: str
    level_order: tuple[Level, ...]
    grade_order: tuple[Grade, ...]
    floor: Floor
    companion_suffix: str
    companion_schema: Literal["pfp.contract-score.v1"]
    populations: tuple[Population, ...]
    exclusions: Exclusions
    support_categories: tuple[SupportCategory, ...]
    pinned_boilerplate: tuple[PinnedBoilerplate, ...]
    not_yet_governed: NotYetGoverned


class BaselineEntry(Record):
    sha256: Digest
    reason: str


class Baseline(Record):
    schema_version: Literal["pfp.governance-baseline.v1"]
    authority_effect: Literal["None"] = Field(alias="AuthorityEffect")
    rule: str
    entries: dict[str, BaselineEntry]


class FileHash(Record):
    path: str
    sha256: Digest


class RunRecord(Record):
    """One captured tool execution (SCORING.md section 6, tool execution integrity)."""

    schema_version: Literal["pfp.evidence-run.v1"]
    authority_effect: Literal["None"] = Field(alias="AuthorityEffect")
    name: str
    command: tuple[str, ...] = Field(min_length=1)
    working_directory: str
    tool_versions: dict[str, str]
    started: AwareDatetime
    finished: AwareDatetime
    exit_status: int
    inputs: tuple[FileHash, ...]
    report: FileHash


ROOT = Path(__file__).resolve().parents[2]
RATIO_TOLERANCE = Fraction(1, 10**9)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def glob_regex(pattern: str) -> re.Pattern[str]:
    """``**/`` spans whole directories, ``*`` stays within one, ``?`` is one character."""
    out = []
    index = 0
    while index < len(pattern):
        if pattern.startswith("**/", index):
            out.append("(?:.*/)?")
            index += 3
            continue
        char = pattern[index]
        out.append({"*": "[^/]*", "?": "[^/]"}.get(char, re.escape(char)))
        index += 1
    return re.compile("".join(out) + r"\Z")


def matches(path: str, globs: Sequence[str]) -> bool:
    return any(glob_regex(pattern).match(path) for pattern in globs)


class Repository:
    """Policy, baseline and file access rooted at one checkout."""

    def __init__(self, root: Path) -> None:
        self.root = root
        governance = root / "governance"
        self.policy = Policy.model_validate_json((governance / "policy.json").read_bytes())
        self.baseline = Baseline.model_validate_json((governance / "baseline.json").read_bytes())

    def git(self, *args: str) -> str:
        executable = shutil.which("git")
        if executable is None:
            raise FileNotFoundError("git is required to list the governed population")
        completed = subprocess.run(  # noqa: S603 - resolved git executable, fixed argv, no shell
            [executable, *args],
            cwd=self.root,
            capture_output=True,
            check=True,
        )
        return completed.stdout.decode("utf-8")

    def language(self, path: str) -> str | None:
        if set(path.split("/")) & set(self.policy.exclusions.path_parts):
            return None
        for population in self.policy.populations:
            if matches(path, population.globs):
                return population.language
        return None

    def population(self) -> list[str]:
        listed = self.git("ls-files", "--cached", "--others", "--exclude-standard", "-z").split("\0")
        found = {name.replace("\\", "/") for name in listed if name}
        return sorted(name for name in found if self.language(name) and (self.root / name).is_file())

    def changed_since(self, ref: str) -> set[str]:
        base = self.git("merge-base", ref, "HEAD").strip()
        names = self.git("diff", "--name-only", "--no-renames", "-z", base).split("\0")
        names += self.git("ls-files", "--others", "--exclude-standard", "-z").split("\0")
        return {name.replace("\\", "/") for name in names if name}

    def floor_for(self, path: str) -> tuple[str, str, str]:
        """``(category, min_level, min_grade)`` for a governed path."""
        for category in self.policy.support_categories:
            if matches(path, category.globs):
                return category.name, category.min_level, category.min_grade
        return "runtime", self.policy.floor.min_level, self.policy.floor.min_grade

    def companion_path(self, path: str) -> Path:
        source = self.root / path
        return source.with_name(source.stem + self.policy.companion_suffix)

    def grandfathered(self, path: str, digest: str) -> bool:
        entry = self.baseline.entries.get(path)
        return entry is not None and entry.sha256 == digest

    def pinned(self, path: str, digest: str) -> bool:
        """Admitted by exact bytes under a ``pinned_boilerplate`` entry; needs no companion."""
        return any(matches(path, [pin.glob]) and pin.sha256 == digest for pin in self.policy.pinned_boilerplate)


def score_problems(score: ScoreRecord, min_level: str, min_grade: str) -> list[str]:
    """Completeness, arithmetic and floor problems of one score record."""
    if any(grade is None for grade in score.gates.values()) or not score.is_complete:
        return ["score is incomplete: every gate must be graded and is_complete true"]
    return _arithmetic_problems(score) + _floor_problems(score, min_level, min_grade)


def _rank(grade: str | None) -> int:
    return GRADES.index(grade) if grade is not None else -1


def _arithmetic_problems(score: ScoreRecord) -> list[str]:
    problems: list[str] = []
    weakest = min(score.gates.values(), key=_rank)
    if score.composite_grade != weakest:
        problems.append(f"composite_grade {score.composite_grade} is not the weakest gate {weakest}")
    if score.score_token != f"{score.level}{score.composite_grade}":
        problems.append(f"score_token {score.score_token} is not level + composite")
    if set(score.basis) != {"G1", "G2", "G3", "G4", "G5"}:
        problems.append("basis must give the reasoning for all five gates")
    if _rank(score.grade_ceiling) < _rank(score.composite_grade):
        problems.append("grade_ceiling is below the composite grade")
    return problems


def _floor_problems(score: ScoreRecord, min_level: str, min_grade: str) -> list[str]:
    problems: list[str] = []
    if LEVELS.index(score.level) < LEVELS.index(min_level):
        problems.append(f"level {score.level} is below the floor {min_level}")
    if _rank(score.composite_grade) < GRADES.index(min_grade):
        problems.append(f"grade {score.composite_grade} is below the floor {min_grade}")
    return problems


def mutation_problems(accounting: MutationAccounting) -> list[str]:
    """Balance and the conservative ratio R = killed / (killed + survived + inconclusive + unrun)."""
    eligible = accounting.killed + accounting.survived + accounting.inconclusive + accounting.unrun
    if eligible == 0:
        if accounting.conservative_ratio is not None:
            return ["an empty eligible campaign must report a null ratio"]
        return []
    if accounting.conservative_ratio is None:
        return ["conservative_ratio is null for a non-empty campaign"]
    expected = Fraction(accounting.killed, eligible)
    # The schema reports R as a JSON number. Read its shortest decimal spelling (RULE_PY_004)
    # and compare with the exact ratio within a tolerance far below any grade boundary.
    reported = Fraction(repr(accounting.conservative_ratio))
    if abs(expected - reported) > RATIO_TOLERANCE:
        return [f"conservative_ratio {accounting.conservative_ratio} is not {accounting.killed}/{eligible}"]
    return []


def evidence_problems(repo: Repository, path: str, digest: str, score: ScoreRecord) -> list[str]:
    """Every cited file must exist with the cited hash; run records must have seen these bytes."""
    problems: list[str] = []
    references = list(score.evidence)
    if score.mutation_accounting is not None:
        references.append(score.mutation_accounting.report)
    for reference in references:
        target = repo.root / reference.path
        if not target.is_file():
            problems.append(f"evidence {reference.path} does not exist")
        elif sha256_file(target) != reference.sha256:
            problems.append(f"evidence {reference.path} does not match its cited hash")
        elif target.suffix == ".json" and target.name.endswith(".run.json"):
            problems.extend(_run_problems(target, path, digest))
    return problems


def _run_problems(target: Path, path: str, digest: str) -> list[str]:
    try:
        run = RunRecord.model_validate_json(target.read_bytes())
    except ValidationError:
        return [f"evidence {target.name} is not a valid run record"]
    seen = {item.path: item.sha256 for item in run.inputs}
    if path in seen and seen[path] != digest:
        return [f"evidence {target.name} ran against different bytes of {path} (stale)"]
    return []


def check_source(repo: Repository, path: str) -> list[str]:
    """All problems for one governed source; empty means accepted."""
    digest = sha256_file(repo.root / path)
    if repo.pinned(path, digest):
        return []
    companion_file = repo.companion_path(path)
    if not companion_file.is_file():
        return [f"missing companion {companion_file.relative_to(repo.root).as_posix()}"]
    try:
        companion = Companion.model_validate_json(companion_file.read_bytes())
    except ValidationError as error:
        return [f"companion is malformed: {error.error_count()} problem(s): {error.errors()[0]['msg']}"]
    problems = _binding_problems(path, digest, repo.language(path), companion)
    _, min_level, min_grade = repo.floor_for(path)
    problems += score_problems(companion.score, min_level, min_grade)
    if companion.score.mutation_accounting is not None:
        problems += mutation_problems(companion.score.mutation_accounting)
    problems += evidence_problems(repo, path, digest, companion.score)
    return problems


def _binding_problems(path: str, digest: str, language: str | None, companion: Companion) -> list[str]:
    problems: list[str] = []
    if companion.artifact != path:
        problems.append(f"companion names {companion.artifact}, not {path}")
    for kind, artifact in (("contract", companion.contract.artifact), ("score", companion.score.artifact)):
        if artifact.path != path or artifact.sha256 != digest:
            problems.append(f"{kind} does not bind the current bytes of {path}")
        if artifact.language != language:
            problems.append(f"{kind} language {artifact.language} is not {language}")
    return problems


def command_check(repo: Repository, changed_since: str | None, as_json: bool, out: TextIO) -> int:
    selected = _selected(repo, changed_since)
    failing = {path: problems for path, problems in _results(repo, selected).items() if problems}
    checked = len(selected)
    if as_json:
        out.write(json.dumps({"checked": checked, "failing": failing}, indent=2, sort_keys=True) + "\n")
    else:
        for path, problems in failing.items():
            out.writelines(f"FAIL {path}: {problem}\n" for problem in problems)
        out.write(f"{checked - len(failing)}/{checked} governed sources meet the floor\n")
    return 1 if failing else 0


def _selected(repo: Repository, changed_since: str | None) -> list[str]:
    """The whole population, or only sources (or companions) changed since ``changed_since``."""
    sources = repo.population()
    if changed_since is None:
        return sources
    changed = repo.changed_since(changed_since)
    return [path for path in sources if path in changed or _companion_name(repo, path) in changed]


def _results(repo: Repository, selected: list[str]) -> dict[str, list[str]]:
    """Problems per selected source; a grandfathered source with unchanged bytes has none."""
    results: dict[str, list[str]] = {}
    for path in selected:
        problems = check_source(repo, path)
        results[path] = [] if problems and repo.grandfathered(path, sha256_file(repo.root / path)) else problems
    return results


def _companion_name(repo: Repository, path: str) -> str:
    return repo.companion_path(path).relative_to(repo.root).as_posix()


def command_explain(repo: Repository, path: str, out: TextIO) -> int:
    language = repo.language(path)
    if language is None or not (repo.root / path).is_file():
        out.write(f"{path} is not a governed source\n")
        return 1
    category, min_level, min_grade = repo.floor_for(path)
    out.write(f"{path}\n  language {language}; category {category}; floor {min_level}{min_grade}\n")
    out.write(f"  sha256 {sha256_file(repo.root / path)}\n")
    companion_file = repo.companion_path(path)
    if companion_file.is_file():
        try:
            token = Companion.model_validate_json(companion_file.read_bytes()).score.score_token
            out.write(f"  recorded score {token}\n")
        except ValidationError:
            out.write("  companion is malformed\n")
    problems = check_source(repo, path)
    out.writelines(f"  problem: {problem}\n" for problem in problems)
    out.write("  ACCEPTED\n" if not problems else "  NOT ACCEPTED\n")
    return 0 if not problems else 1


def command_record(repo: Repository, path: str, contract_file: Path, score_file: Path, out: TextIO) -> int:
    """Make the given contract and score current for ``path``, keeping earlier records as history."""
    contract = ContractRecord.model_validate_json(contract_file.read_bytes())
    score = ScoreRecord.model_validate_json(score_file.read_bytes())
    companion_file = repo.companion_path(path)
    history: tuple[HistoryEntry, ...] = ()
    if companion_file.is_file():
        previous = Companion.model_validate_json(companion_file.read_bytes())
        entry = HistoryEntry(recorded_at=datetime.now(UTC), contract=previous.contract, score=previous.score)
        history = (*previous.history, entry)
    companion = Companion(
        schema_version="pfp.contract-score.v1",
        authority_effect="None",
        artifact=path,
        contract=contract,
        score=score,
        history=history,
    )
    text = companion.model_dump_json(by_alias=True, indent=2) + "\n"
    companion_file.write_text(text, encoding="utf-8", newline="\n")
    problems = check_source(repo, path)
    out.write(f"recorded {score.score_token} for {path}: {'accepted' if not problems else 'NOT accepted'}\n")
    out.writelines(f"  problem: {problem}\n" for problem in problems)
    return 0 if not problems else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="governance-check", description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", type=Path, default=ROOT)
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check")
    check.add_argument("--changed-since", metavar="REF")
    check.add_argument("--json", action="store_true")
    commands.add_parser("population")
    explain = commands.add_parser("explain")
    explain.add_argument("path")
    record = commands.add_parser("record")
    record.add_argument("path")
    record.add_argument("--contract", type=Path, required=True)
    record.add_argument("--score", type=Path, required=True)
    return parser


USAGE_ERROR = 2


def main(argv: Sequence[str] | None = None, out: TextIO | None = None) -> int:
    """Run one command; a git failure (for example an unknown ref) is reported with exit code 2."""
    stream = out if out is not None else sys.stdout
    args = build_parser().parse_args(argv)
    try:
        return _run(args, Repository(args.root.resolve()), stream)
    except subprocess.CalledProcessError as error:
        detail = error.stderr.decode("utf-8", errors="replace").strip() if error.stderr else ""
        stream.write(f"governance-check: git {' '.join(error.cmd[1:])} failed: {detail}\n")
        return USAGE_ERROR


def _run(args: argparse.Namespace, repo: Repository, stream: TextIO) -> int:
    if args.command == "check":
        return command_check(repo, args.changed_since, args.json, stream)
    if args.command == "population":
        stream.writelines(f"{path}\n" for path in repo.population())
        return 0
    if args.command == "explain":
        return command_explain(repo, args.path.replace("\\", "/"), stream)
    return command_record(repo, args.path.replace("\\", "/"), args.contract, args.score, stream)


if __name__ == "__main__":
    sys.exit(main())
