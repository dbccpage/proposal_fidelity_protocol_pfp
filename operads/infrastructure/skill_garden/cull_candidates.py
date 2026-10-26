"""Read garden observations and run the native nomination policy. No archive effects."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from omega_engine_operations.domain.rop.result import Err
from omega_engine_operads.application.skill_garden.cull import nominate
from omega_engine_operads.domain.skill_garden.cull import (
    CullPolicy,
    CullPolicyError,
    CullReport,
    GardenSnapshot,
    SkillObservation,
)
from omega_engine_operads.infrastructure.skill_garden.native_cull import (
    NativeCullPolicyAdapter,
)
from omega_engine_operads.infrastructure.skill_garden.usage_ledger import (
    garden_roster,
    last_used_index,
    ledger_span,
)

POLICY_REL = (
    Path("omega_engine_operads")
    / "infrastructure"
    / "skill_garden"
    / "cull_policy.json"
)
SKILLS_REL = Path("omega_engine_operads") / "skills"
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def _micros(value: datetime) -> int:
    delta = value - _EPOCH
    return (delta.days * 86400 + delta.seconds) * 1000000 + delta.microseconds


def _observations(values: dict[str, datetime]) -> tuple[SkillObservation, ...]:
    return tuple(
        SkillObservation(key, _micros(value), value.date().isoformat())
        for key, value in values.items()
    )


def load_policy(repo_root: Path) -> CullPolicy:
    path = repo_root / POLICY_REL
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        raise CullPolicyError(f"cannot read {path}: {err}") from err
    result = NativeCullPolicyAdapter().validate_policy(payload)
    if isinstance(result, Err):
        raise CullPolicyError(f"malformed policy in {path}: {result.error.message}")
    data = result.value
    return CullPolicy(
        **dict(
            data,
            sensor_epoch=datetime.strptime(data["sensor_epoch"], "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            ),
        )
    )


def skill_birth_dates(repo_root: Path) -> dict[str, datetime]:
    """First commit that added each package, in one `git log` rather than 115.

    A package younger than the grace period must not be nominated, and its age
    is a property of history rather than of the ledger.
    """
    try:
        completed = subprocess.run(
            [
                "git",
                "log",
                "--diff-filter=A",
                "--reverse",
                "--format=%x00%aI",
                "--name-only",
                "--",
                SKILLS_REL.as_posix(),
            ],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return {}
    if completed.returncode != 0:
        return {}

    births: dict[str, datetime] = {}
    stamp: datetime | None = None
    for line in completed.stdout.splitlines():
        if line.startswith("\x00"):
            try:
                stamp = datetime.fromisoformat(line[1:].strip()).astimezone(timezone.utc)
            except ValueError:
                stamp = None
            continue
        if not line.strip() or stamp is None:
            continue
        parts = line.strip().split("/")
        if len(parts) < 3:
            continue
        name = parts[2]
        if name.startswith(("_", ".")):
            continue
        births.setdefault(name, stamp)
    return births


def _parity_is_green(repo_root: Path) -> bool:
    try:
        completed = subprocess.run(
            [
                "python",
                "omega_engine_operations/use_cases/packaging/sync_cross_host_skills.py",
                "--check",
            ],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return False
    return completed.returncode == 0


def compute_candidates(
    repo_root: Path, *, now: datetime, policy: CullPolicy, check_parity: bool = True
) -> CullReport:
    first, last = ledger_span(repo_root)
    snapshot = GardenSnapshot(
        now_us=_micros(now),
        first_us=_micros(first) if first else None,
        last_us=_micros(last) if last else None,
        roster=tuple(sorted(garden_roster(repo_root))),
        last_used=_observations(last_used_index(repo_root)),
        births=_observations(skill_birth_dates(repo_root)),
        parity_green=_parity_is_green(repo_root) if check_parity else None,
    )
    result = nominate(policy, snapshot, port=NativeCullPolicyAdapter())
    if isinstance(result, Err):
        raise CullPolicyError(result.error.message)
    return result.value
