"""Census of SKILL.md sizes against constants assigned by the live budget gate.

The gate is
`operads/skill_operad/skill_compiler/budget_gate.py`
(`GATE_SOURCE`). This module parses that file. It does not restate the ceilings.
The census does not read a gate from `.agents/operad`.

`read_gate_terms` requires literal `DEFAULT_MAX_LINES` and `DEFAULT_MAX_BYTES`.
The governed names are the literal sequence assigned to `DEFAULT_GOVERNED`, or,
when that name is absent, the literal sequence assigned to `SEED_GOVERNED`.
The live file assigns both: `SEED_GOVERNED = DEFAULT_GOVERNED`. That alias is
not a second list. A missing file is `GATE_ABSENT`. A file that assigns neither
governed name is `GATE_UNREADABLE`.

`governed_skills` in the gate lists garden directories when it runs. This census
does not call that function, and it does not treat the historical five-name
constant as a headcount of the garden.

`read_eval_bank_index` reads case ids from `eval_bank/cases.json`.
It does not run `eval_runner.py`. An index of ids is not a 16/16 pass.

This module does not define `SkillCompilerEngine`, `TruthBoundaryCanaryHarness`,
or `GardenNaturalSelectionAuditor`.

The shrink-only ratchet is keyed by skill name. A new breach fails, a recorded
breach that grows fails, and a recorded breach that has been fixed fails until
its entry is removed. A count-only baseline would let one breach replace another.

`AuthorityEffect: None`. Measuring a skill does not decide whether it stays.
"""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

BASELINE_SCHEMA = "core.oewas.budget_baseline.v1"

# Relative to the repository root. The canon host; the other three are mirrors.
GATE_SOURCE = Path(
    "operads/skill_operad/skill_compiler/budget_gate.py"
)
SKILL_ROOT = Path("operads/skills")
EVAL_BANK = Path(
    "operads/skill_operad/skill_compiler/eval_bank/cases.json"
)
EVAL_BANK_SCHEMA = "core.skill_compiler.eval_bank.v1"

_GOVERNED_NAMES = ("DEFAULT_GOVERNED", "SEED_GOVERNED")
_LIMIT_NAMES = ("DEFAULT_MAX_LINES", "DEFAULT_MAX_BYTES")


class CensusError(RuntimeError):
    """A typed refusal naming what the census would not do."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class SkillMeasurement:
    """One skill, measured. Line and byte counts, nothing interpreted."""

    name: str
    lines: int
    size: int

    def breaches(self, max_lines: int, max_bytes: int) -> bool:
        return self.lines > max_lines or self.size > max_bytes


@dataclass(frozen=True, slots=True)
class GateTerms:
    """What the gate says the rule is, read from the gate rather than restated."""

    governed: frozenset[str]
    max_lines: int
    max_bytes: int


@dataclass(frozen=True, slots=True)
class EvalBankIndex:
    """Case ids named by the eval bank file. Not a run, and not a pass count."""

    schema: str
    case_ids: tuple[str, ...]
    executed: bool

    def __post_init__(self) -> None:
        if type(self.executed) is not bool or self.executed is not False:
            raise CensusError(
                "BANK_NOT_RUN",
                "an index of case ids is not a run of eval_runner.py",
            )

    def __eq__(self, other: object) -> bool:
        assert type(self) is type(other)
        assert isinstance(other, EvalBankIndex)
        return (
            self.schema == other.schema
            and self.case_ids == other.case_ids
            and self.executed is other.executed
        )

    def __hash__(self) -> int:
        return hash((type(self), self.schema, self.case_ids, self.executed))


def _static_value(node: ast.expr) -> object:
    """Evaluate a constant expression from the gate's source, arithmetic included.

    `ast.literal_eval` refuses `20 * 1024`, and the gate writes its byte ceiling
    exactly that way -- which is the more readable form and not something this
    module should force it to give up. So integer `*` and `+` are admitted, and
    nothing else is: no names, no calls, no attribute access. A gate that
    computed its limit from anything richer would be a gate whose limit cannot
    be read without running it, and that is worth refusing.
    """
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Mult, ast.Add)):
        left, right = _static_value(node.left), _static_value(node.right)
        if isinstance(left, int) and isinstance(right, int):
            return left * right if isinstance(node.op, ast.Mult) else left + right
        raise ValueError("arithmetic over non-integers")
    return ast.literal_eval(node)


def _assigned_constant(name: str, node: ast.expr) -> tuple[str, object]:
    if isinstance(node, ast.Name):
        return ("alias", node.id)
    try:
        return ("literal", _static_value(node))
    except (ValueError, TypeError, SyntaxError) as exc:
        raise CensusError(
            "GATE_UNREADABLE",
            f"{name} is not a literal: {exc}",
        ) from exc


def _governed_sequence(label: str, kind: str, value: object) -> frozenset[str]:
    if kind != "literal" or not isinstance(value, (tuple, list, set, frozenset)):
        raise CensusError("GATE_UNREADABLE", f"{label} is not a sequence")
    return frozenset(str(name) for name in value)


def _literal_limit(label: str, payload: tuple[str, object]) -> int:
    kind, value = payload
    if kind != "literal" or type(value) is not int:
        raise CensusError("GATE_UNREADABLE", f"{label} is not a literal integer")
    return value


def read_gate_terms(repo_root: Path) -> GateTerms:
    """Parse the gate's constants out of its source.

    Static parse rather than import: importing the gate to learn a number would
    execute its script body. There is no default ceiling and no default governed
    set. A default would survive a rename and report a result against `()`.

    `DEFAULT_GOVERNED` wins when it is assigned. `SEED_GOVERNED` is accepted
    only when `DEFAULT_GOVERNED` is absent, which is the name the live file
    would still have if the historical tuple were renamed in place. The live
    assignment `SEED_GOVERNED = DEFAULT_GOVERNED` is an alias, not a list.
    """
    source_path = repo_root / GATE_SOURCE
    if not source_path.is_file():
        raise CensusError("GATE_ABSENT", f"no budget gate at {GATE_SOURCE}")
    tree = ast.parse(source_path.read_text(encoding="utf-8"))

    found: dict[str, tuple[str, object]] = {}
    wanted = set(_GOVERNED_NAMES + _LIMIT_NAMES)
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in wanted:
                found[target.id] = _assigned_constant(target.id, node.value)

    missing = [name for name in _LIMIT_NAMES if name not in found]
    if "DEFAULT_GOVERNED" not in found and "SEED_GOVERNED" not in found:
        missing.append("DEFAULT_GOVERNED")
        missing.append("SEED_GOVERNED")
    if missing:
        raise CensusError(
            "GATE_UNREADABLE",
            f"the gate no longer declares {', '.join(missing)}",
        )

    if "DEFAULT_GOVERNED" in found:
        kind, value = found["DEFAULT_GOVERNED"]
        governed = _governed_sequence("DEFAULT_GOVERNED", kind, value)
    else:
        kind, value = found["SEED_GOVERNED"]
        if kind == "alias":
            raise CensusError(
                "GATE_UNREADABLE",
                "SEED_GOVERNED aliases a name that is not a literal sequence",
            )
        governed = _governed_sequence("SEED_GOVERNED", kind, value)

    return GateTerms(
        governed=governed,
        max_lines=_literal_limit("DEFAULT_MAX_LINES", found["DEFAULT_MAX_LINES"]),
        max_bytes=_literal_limit("DEFAULT_MAX_BYTES", found["DEFAULT_MAX_BYTES"]),
    )


def read_eval_bank_index(repo_root: Path) -> EvalBankIndex:
    """Read eval-bank case ids. This function does not run the bank."""
    path = repo_root / EVAL_BANK
    if not path.is_file():
        raise CensusError("BANK_ABSENT", f"no eval bank at {EVAL_BANK}")
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CensusError("BANK_UNREADABLE", str(exc)) from exc
    if not isinstance(document, dict) or document.get("schema") != EVAL_BANK_SCHEMA:
        raise CensusError("BANK_UNREADABLE", "unsupported eval bank schema")
    cases = document.get("cases")
    if not isinstance(cases, list) or not cases:
        raise CensusError("BANK_UNREADABLE", "eval bank cases must be a non-empty list")
    ids: list[str] = []
    for case in cases:
        if not isinstance(case, dict):
            raise CensusError("BANK_UNREADABLE", "an eval bank case is not an object")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id:
            raise CensusError("BANK_UNREADABLE", "an eval bank case has no id")
        ids.append(case_id)
    if len(ids) != len(set(ids)):
        raise CensusError("BANK_UNREADABLE", "eval bank case ids are not unique")
    return EvalBankIndex(schema=EVAL_BANK_SCHEMA, case_ids=tuple(ids), executed=False)


def measure_garden(repo_root: Path) -> tuple[SkillMeasurement, ...]:
    """Measure every `SKILL.md` under the canon host, in name order.

    Line counting matches the gate's: the number of lines the file contains, so
    a file with no trailing newline still counts its last line.
    """
    root = repo_root / SKILL_ROOT
    if not root.is_dir():
        raise CensusError("GARDEN_ABSENT", f"no skill garden at {SKILL_ROOT}")
    measurements = []
    for skill_md in sorted(root.rglob("SKILL.md")):
        raw = skill_md.read_bytes()
        lines = raw.count(b"\n") + (0 if not raw or raw.endswith(b"\n") else 1)
        measurements.append(SkillMeasurement(name=skill_md.parent.name, lines=lines, size=len(raw)))
    if not measurements:
        raise CensusError("GARDEN_EMPTY", "no SKILL.md found; refusing to report 0/0")
    return tuple(measurements)


@dataclass(frozen=True, slots=True)
class GardenCensus:
    """The measured garden, the gate's terms, and what follows from both."""

    terms: GateTerms
    measurements: tuple[SkillMeasurement, ...]

    def coverage(self) -> tuple[int, int]:
        """`(scanned, total)`. The number the gate does not print.

        Returned as a pair rather than a ratio so a caller cannot round away
        the difference between 5-of-110 and 109-of-110.
        """
        names = {m.name for m in self.measurements}
        return len(names & self.terms.governed), len(names)

    def unscanned(self) -> tuple[str, ...]:
        return tuple(sorted(m.name for m in self.measurements if m.name not in self.terms.governed))

    def breaches(self) -> tuple[SkillMeasurement, ...]:
        return tuple(
            m for m in self.measurements if m.breaches(self.terms.max_lines, self.terms.max_bytes)
        )

    def unenforced_breaches(self) -> tuple[SkillMeasurement, ...]:
        """Breaches the gate cannot see.

        When this is the whole of `breaches()`, the gate passes while the
        invariant is violated -- which is the state this module was written in.
        """
        return tuple(m for m in self.breaches() if m.name not in self.terms.governed)

    def measurement(self, name: str) -> SkillMeasurement | None:
        for entry in self.measurements:
            if entry.name == name:
                return entry
        return None


def take_census(repo_root: Path) -> GardenCensus:
    return GardenCensus(
        terms=read_gate_terms(repo_root),
        measurements=measure_garden(repo_root),
    )


# ----------------------------------------------------------------------
# The ratchet
# ----------------------------------------------------------------------


def load_baseline(path: Path) -> dict[str, SkillMeasurement]:
    if not path.is_file():
        raise CensusError("BASELINE_ABSENT", f"no baseline at {path}")
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CensusError("BASELINE_UNREADABLE", str(exc)) from exc
    if document.get("schema") != BASELINE_SCHEMA:
        raise CensusError("BASELINE_SCHEMA", "unsupported baseline schema")
    entries = document.get("breaches")
    if not isinstance(entries, list):
        raise CensusError("BASELINE_SCHEMA", "`breaches` must be a list")
    baseline: dict[str, SkillMeasurement] = {}
    for entry in entries:
        name = entry.get("name")
        if not isinstance(name, str) or not name:
            raise CensusError("BASELINE_SCHEMA", "a breach entry has no name")
        if name in baseline:
            raise CensusError("BASELINE_DUPLICATE", f"{name} is recorded twice")
        baseline[name] = SkillMeasurement(
            name=name, lines=int(entry["lines"]), size=int(entry["size"])
        )
    return baseline


def ratchet_violations(
    census: GardenCensus, baseline: Mapping[str, SkillMeasurement]
) -> tuple[str, ...]:
    """Compare the garden to the baseline. Empty means the ratchet holds.

    Three ways to violate it, and the third is the one that makes this a ratchet
    rather than a list of permanent excuses:

    1. a skill breaches that the baseline does not record -- a new breach;
    2. a recorded breach has grown past the size it was recorded at;
    3. a recorded breach no longer breaches -- the entry must be **removed**, or
       the baseline keeps reserving room that nothing needs.
    """
    problems: list[str] = []
    current = {m.name: m for m in census.breaches()}

    for name, measured in sorted(current.items()):
        recorded = baseline.get(name)
        if recorded is None:
            problems.append(
                f"{name}: new breach at {measured.lines} lines / {measured.size} "
                f"bytes, not in the baseline"
            )
            continue
        if measured.lines > recorded.lines:
            problems.append(f"{name}: grew from {recorded.lines} to {measured.lines} lines")
        if measured.size > recorded.size:
            problems.append(f"{name}: grew from {recorded.size} to {measured.size} bytes")

    for name in sorted(baseline):
        if name not in current:
            item = census.measurement(name)
            if item is None:
                problems.append(
                    f"{name}: recorded in the baseline but no longer in the garden; "
                    f"remove the entry"
                )
            else:
                problems.append(
                    f"{name}: no longer breaches ({item.lines} lines / "
                    f"{item.size} bytes); remove the entry so the ratchet "
                    f"cannot slip back"
                )
    return tuple(problems)


def render_baseline(census: GardenCensus) -> str:
    """Serialise the current breaches as a baseline document.

    Used to author the baseline once and to show a maintainer what a corrected
    one looks like. It is deliberately **not** wired into a `--update` flag: a
    check that can rewrite its own expectations is not a check.
    """
    document = {
        "schema": BASELINE_SCHEMA,
        "note": (
            "Identity-keyed, shrink-only. A new breach fails. A recorded breach "
            "that grows fails. A recorded breach that is fixed fails until its "
            "entry is deleted. Regenerating this file to make a check pass "
            "defeats it."
        ),
        "limits": {
            "max_lines": census.terms.max_lines,
            "max_bytes": census.terms.max_bytes,
        },
        "breaches": [{"name": m.name, "lines": m.lines, "size": m.size} for m in census.breaches()],
    }
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"


def format_report(census: GardenCensus, problems: Iterable[str] = ()) -> str:
    """A human-readable census, coverage first."""
    scanned, total = census.coverage()
    breaches = census.breaches()
    unenforced = census.unenforced_breaches()
    lines = [
        "=== SKILL GARDEN BUDGET CENSUS ===",
        f"limits            : {census.terms.max_lines} lines / {census.terms.max_bytes} bytes",
        f"skills in garden  : {total}",
        f"scanned by gate   : {scanned}",
        f"never scanned     : {total - scanned}",
        f"breaching         : {len(breaches)}",
        f"breaching unseen  : {len(unenforced)}",
    ]
    if breaches:
        lines.append("")
        lines.append("breaches:")
        for entry in sorted(breaches, key=lambda m: -m.lines):
            seen = "scanned" if entry.name in census.terms.governed else "UNSCANNED"
            lines.append(f"  {entry.lines:5d} lines {entry.size:7d} bytes  {entry.name} [{seen}]")
    problems = tuple(problems)
    if problems:
        lines.append("")
        lines.append("ratchet violations:")
        lines.extend(f"  {problem}" for problem in problems)
    return "\n".join(lines)


__all__ = [
    "BASELINE_SCHEMA",
    "CensusError",
    "EVAL_BANK",
    "EVAL_BANK_SCHEMA",
    "EvalBankIndex",
    "GATE_SOURCE",
    "GardenCensus",
    "GateTerms",
    "SKILL_ROOT",
    "SkillMeasurement",
    "format_report",
    "load_baseline",
    "measure_garden",
    "ratchet_violations",
    "read_eval_bank_index",
    "read_gate_terms",
    "render_baseline",
    "take_census",
]
