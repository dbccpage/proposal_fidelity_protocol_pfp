"""Per-skill memory: bounded, opt-in, and selected on evidence rather than taste.

## Why this is deliberately small

The estate's Context Protection rule exists because loading many files at once
is what breaks these sessions. A `MEMORY.md` in every one of 128 packages, read
at session start, is precisely the failure that rule was written to prevent. So:

- memory is granted to a **selected few**, not to the garden;
- it is read **only when that skill is invoked**, never at session start;
- it is **capped**, and the cap is enforced on write rather than hoped for;
- it lives on the same 30-day clock as the package that owns it.

## The selection method, and its refusal

Selection is by invocation count from `runs/skill_usage/`, which is the only
evidence of use this estate has. The method refuses rather than guesses when:

1. the ledger spans fewer days than the policy's minimum -- a count over a short
   window measures the sensor, not the skill;
2. too few skills clear the floor for a cohort to mean anything;
3. no skill clears it at all.

Measured on the day this was written: of six skills ever invoked, **one** clears
a floor of three (`auto-oe-autop`, 13), and three clear a floor of two. That is
not enough to select on, and the policy says so rather than granting memory to a
skill because it happened to run twice.

## Testing whether the method is right

Granting memory and then asserting it helped is not evidence. `record_cohort`
writes both the **granted** set and a **control** set -- the skills that came
closest to the floor without clearing it -- at the moment of the grant. A later
comparison of repeat-signal rates in `runs/skill_compiler/episodes/` between the
two sets is then a real comparison, because the control was chosen before the
outcome was known.

`AuthorityEffect: None`. A memory is an observation a skill made about its own
work. It certifies nothing and authorises nothing.
"""

from __future__ import annotations

import collections
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, NamedTuple

from omega_engine_operads.infrastructure.skill_garden.usage_ledger import (
    garden_roster,
    ledger_span,
    load_usage_events,
)

SKILLS_REL = Path("omega_engine_operads") / "skills"
MEMORY_NAME = "MEMORY.md"
COHORT_REL = Path("runs") / "skill_memory" / "cohort.json"

#: A memory that grows without bound is a context leak with a nicer name.
MAX_LINES = 50
MAX_BYTES = 4 * 1024

#: Selection policy. Deliberately conservative; see the module docstring.
MIN_LEDGER_DAYS = 30
INVOCATION_FLOOR = 3
MIN_COHORT = 3

HEADER = """---
kind: memory
authority_effect: None
skill: {skill_id}
---

<!-- Bounded to {max_lines} lines / {max_bytes} bytes, enforced on write.
     Read only when this skill is invoked, never at session start.
     One durable observation per line. AuthorityEffect: None. -->
"""


class MemoryRefusal(RuntimeError):
    """Selection refused. Distinct from a skill simply not qualifying."""


class Selection(NamedTuple):
    granted: tuple[str, ...]
    control: tuple[str, ...]
    refusals: tuple[str, ...]
    counts: dict[str, int]
    span_days: float

    @property
    def refused(self) -> bool:
        return bool(self.refusals)


def memory_path(repo_root: Path, skill_id: str) -> Path:
    return repo_root / SKILLS_REL / skill_id / MEMORY_NAME


def invocation_counts(repo_root: Path) -> dict[str, int]:
    roster = garden_roster(repo_root)
    counts = collections.Counter(
        row["skill_id"] for row in load_usage_events(repo_root) if row.get("skill_id") in roster
    )
    return dict(counts)


def select(
    repo_root: Path,
    *,
    floor: int = INVOCATION_FLOOR,
    min_cohort: int = MIN_COHORT,
    min_days: int = MIN_LEDGER_DAYS,
) -> Selection:
    counts = invocation_counts(repo_root)
    first, last = ledger_span(repo_root)
    span = (last - first).total_seconds() / 86400.0 if first and last else 0.0

    refusals: list[str] = []
    if span < min_days:
        refusals.append(
            f"the ledger spans {span:.1f} days; an invocation count over that "
            f"measures the sensor, not the skill. Needs {min_days}."
        )
    if not counts:
        refusals.append(
            "no invocations recorded at all. That is a sensor failure, not a "
            "garden of skills with nothing to remember."
        )

    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    granted = tuple(name for name, count in ranked if count >= floor)
    # The control is chosen *before* any outcome is known: the skills that came
    # closest to the floor without clearing it. Picking it afterwards would make
    # any later comparison worthless.
    control = tuple(name for name, count in ranked if count < floor)[: max(len(granted), 1) * 2]

    if not granted:
        refusals.append(f"no skill reaches {floor} invocations.")
    elif len(granted) < min_cohort:
        refusals.append(
            f"only {len(granted)} skill(s) reach {floor} invocations; a cohort "
            f"of fewer than {min_cohort} cannot distinguish the method working "
            "from one skill being busy."
        )

    return Selection(
        granted=() if refusals else granted,
        control=() if refusals else control,
        refusals=tuple(refusals),
        counts=counts,
        span_days=span,
    )


def _trim(body: str) -> str:
    """Enforce the cap on write. A cap checked on read is not a cap."""
    lines = [line for line in body.split("\n")]
    if len(lines) > MAX_LINES:
        lines = lines[:MAX_LINES]
    trimmed = "\n".join(lines)
    while len(trimmed.encode("utf-8")) > MAX_BYTES and lines:
        lines.pop()
        trimmed = "\n".join(lines)
    return trimmed


def read_memory(repo_root: Path, skill_id: str) -> str:
    path = memory_path(repo_root, skill_id)
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def append_memory(repo_root: Path, skill_id: str, observation: str) -> dict[str, Any]:
    """Append one durable observation, oldest dropped first when the cap bites."""
    text = (observation or "").strip().replace("\n", " ")
    if not text:
        raise MemoryRefusal("an empty observation is not a memory")
    package = repo_root / SKILLS_REL / skill_id
    if not (package / "SKILL.md").is_file():
        raise MemoryRefusal(f"{skill_id} is not a package in the garden")

    path = memory_path(repo_root, skill_id)
    if path.is_file():
        existing = path.read_text(encoding="utf-8")
    else:
        existing = HEADER.format(skill_id=skill_id, max_lines=MAX_LINES, max_bytes=MAX_BYTES)
    stamped = f"- {datetime.now(timezone.utc).date().isoformat()} {text}"
    body = existing.rstrip("\n") + "\n" + stamped + "\n"
    trimmed = _trim(body)
    path.write_text(
        trimmed if trimmed.endswith("\n") else trimmed + "\n", encoding="utf-8", newline="\n"
    )
    return {
        "skill_id": skill_id,
        "lines": len(trimmed.split("\n")),
        "bytes": len(trimmed.encode("utf-8")),
    }


def record_cohort(repo_root: Path, selection: Selection) -> Path:
    """Freeze granted and control sets so a later comparison is honest."""
    path = repo_root / COHORT_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "omega.skill_garden.memory_cohort.v1",
        "authority_effect": "None",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "why": (
            "Granted and control sets are frozen at the moment of the grant. "
            "The control is the set that came closest to the floor without "
            "clearing it, chosen before any outcome is known -- picking it "
            "afterwards would make the comparison worthless."
        ),
        "floor": INVOCATION_FLOOR,
        "span_days": round(selection.span_days, 2),
        "granted": list(selection.granted),
        "control": list(selection.control),
        "counts": selection.counts,
        "measurement": (
            "Compare repeat-signal rates in runs/skill_compiler/episodes/ "
            "between granted and control after both have had equal exposure. "
            "A method that works shows fewer repeated signals in the granted set."
        ),
    }
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return path
