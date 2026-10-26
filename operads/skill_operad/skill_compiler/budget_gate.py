#!/usr/bin/env python3
"""Hot-context budget gate for governed skill roots.

Prose law ("keep SKILL.md under 300 lines / 20KB") is useless if unenforced.
This script measures live roots and exits non-zero on breach unless the skill
is listed in budget_exceptions.yaml with an expiry.

AuthorityEffect: None. Does not edit skills.
"""

from __future__ import annotations

import argparse
import ast
import sys
from datetime import date, datetime, timezone
from pathlib import Path

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None

# The five meta packages this gate was originally written for. Retained as the
# fallback when the garden cannot be listed, and as the set the gate is known to
# have governed historically.
DEFAULT_GOVERNED = (
    "auto-skill",
    "auto-improve-autoskill",
    "auto-symmetry-hunter",
    "auto-oe-autop",
    "blackrod",
)

SEED_GOVERNED = DEFAULT_GOVERNED


def governed_skills(repo_root: Path) -> list[str]:
    """Every skill package in the garden.

    The default used to be SEED_GOVERNED, so the mandated stage-3 run reported
    PASS while covering 5 of 239 packages -- about 2%. A gate whose default scope
    is 2% of its subject produces a green that stands for very little, which is
    the exact failure this pipeline exists to catch.

    Directories whose name begins with "_" are meta (``_shared``, ``_templates``),
    not skill packages, and carry no SKILL.md by design; counting them as breaches
    made a healthy garden look failing.
    """
    root = repo_root / "omega_engine_operads" / "skills"
    if not root.is_dir():
        return list(SEED_GOVERNED)
    names = sorted(
        p.name for p in root.iterdir() if p.is_dir() and not p.name.startswith("_")
    )
    return names or list(SEED_GOVERNED)


DEFAULT_MAX_LINES = 300
DEFAULT_MAX_BYTES = 20 * 1024


def repo_root_from(start: Path | None = None) -> Path:
    here = (start or Path.cwd()).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / ".git").exists() and (candidate / ".agents").is_dir():
            return candidate
    return Path.cwd().resolve()


def count_lines(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    if not text:
        return 0
    return text.count("\n") + (0 if text.endswith("\n") else 1)


def load_exceptions(path: Path) -> dict[str, dict]:
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    data = (
        yaml.safe_load(text)
        if yaml is not None
        else _load_flat_exceptions_without_yaml(text)
    )
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise TypeError("budget exceptions YAML must be a mapping")
    exceptions = data.get("exceptions") or {}
    if not isinstance(exceptions, dict):
        raise TypeError("exceptions must be a mapping")
    if not all(
        isinstance(name, str) and isinstance(value, dict)
        for name, value in exceptions.items()
    ):
        raise ValueError("each budget exception must be a named mapping")
    return dict(exceptions)


def _parse_scalar(value: str, line_no: int) -> object:
    if not value:
        raise ValueError(f"missing exception value at line {line_no}")
    if not value.startswith(("'", '"')) and " #" in value:
        value = value.split(" #", 1)[0].rstrip()
        if not value:
            raise ValueError(f"missing exception value at line {line_no}")
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if value.isdigit():
        return int(value)
    if value.startswith(("'", '"')):
        parsed = ast.literal_eval(value)
        if not isinstance(parsed, str):
            raise ValueError(
                f"quoted exception value must be a string at line {line_no}"
            )
        return parsed
    return value


def _load_flat_exceptions_without_yaml(text: str) -> dict[str, dict[str, dict]]:
    """Parse the bounded budget-exception schema without optional PyYAML.

    This deliberately supports only ``exceptions:`` followed by named mappings
    of scalar fields. Any other live YAML syntax fails closed.
    """
    result: dict[str, dict] = {"exceptions": {}}
    current: dict[str, object] | None = None
    saw_root = False
    for line_no, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        if indent == 0:
            if stripped == "exceptions:":
                saw_root = True
                current = None
                continue
            if stripped == "exceptions: {}":
                saw_root = True
                current = None
                continue
            raise ValueError(f"unsupported budget exceptions root at line {line_no}")
        if not saw_root:
            raise ValueError(
                f"exception entry before exceptions root at line {line_no}"
            )
        if indent == 2 and stripped.endswith(":"):
            name = stripped[:-1].strip()
            if not name or name in result["exceptions"]:
                raise ValueError(
                    f"invalid or duplicate exception name at line {line_no}"
                )
            current = {}
            result["exceptions"][name] = current
            continue
        if indent == 4 and current is not None and ":" in stripped:
            key, value = stripped.split(":", 1)
            key = key.strip()
            if key not in {"approved", "expires", "reason", "max_lines", "max_bytes"}:
                raise ValueError(
                    f"unsupported exception field {key!r} at line {line_no}"
                )
            if key in current:
                raise ValueError(f"duplicate exception field {key!r} at line {line_no}")
            current[key] = _parse_scalar(value.strip(), line_no)
            continue
        raise ValueError(
            f"unsupported budget exceptions syntax at line {line_no}: {stripped}"
        )
    if not saw_root:
        raise ValueError("budget exceptions YAML is missing exceptions root")
    return result


def parse_expiry(value: object) -> date | None:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


def valid_exception(
    name: str, exc: dict, today: date | None = None
) -> tuple[bool, str]:
    if exc.get("approved") is not True:
        return False, "approved must be the exact boolean true"
    expiry = parse_expiry(exc.get("expires"))
    if expiry is None:
        return False, "approved exception missing valid expires YYYY-MM-DD"
    today = today or datetime.now(timezone.utc).date()
    if expiry < today:
        return False, f"approved exception expired on {expiry.isoformat()}"
    reason = exc.get("reason", "")
    return True, f"expires {expiry.isoformat()} {reason}".strip()


def check_budgets(
    repo_root: Path,
    skills: list[str],
    max_lines: int,
    max_bytes: int,
    exceptions: dict[str, dict],
    today: date | None = None,
) -> int:
    skills_root = repo_root / "omega_engine_operads" / "skills"
    breaches = 0
    print(f"=== SKILL BUDGET GATE (max {max_lines} lines / {max_bytes} bytes) ===")
    for name in skills:
        skill_md = skills_root / name / "SKILL.md"
        if not skill_md.is_file():
            print(f"  [BREACH] {name}: missing required SKILL.md")
            breaches += 1
            continue
        lines = count_lines(skill_md)
        size = skill_md.stat().st_size
        exc = exceptions.get(name) or {}

        # Approval is decided BEFORE the raised limit is applied. It used to be
        # decided after: the exception's `max_lines`/`max_bytes` were adopted
        # unconditionally, and `valid_exception` was consulted only inside the
        # over-budget branch. A raise large enough to put the skill back under
        # its own raised limit meant that branch never ran, so an unapproved or
        # expired exception silently granted itself the raise. The exception
        # mechanism was bypassing its own approval check.
        if exc:
            allowed, detail = valid_exception(name, exc, today=today)
        else:
            allowed, detail = False, "no exception declared"

        line_lim = int(exc.get("max_lines", max_lines)) if allowed else max_lines
        byte_lim = int(exc.get("max_bytes", max_bytes)) if allowed else max_bytes
        over_lines = lines > line_lim
        over_bytes = size > byte_lim

        if over_lines or over_bytes:
            print(
                f"  [BREACH] {name}: {lines} lines, {size} bytes "
                f"(limit {line_lim}/{byte_lim}) - factorize to references/ "
                f"or add approved unexpired exception ({detail})"
            )
            breaches += 1
        elif allowed and (lines > max_lines or size > max_bytes):
            print(
                f"  [EXCEPTION] {name}: {lines} lines, {size} bytes "
                f"(limit {line_lim}/{byte_lim}) {detail}"
            )
        else:
            print(f"  [PASS] {name}: {lines} lines, {size} bytes")
    if breaches:
        print(f"\nFAIL: {breaches} governed skill(s) failed budget enforcement.")
        return 1
    print("\nPASS: all checked skills within budget or approved exceptions.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=None)
    parser.add_argument(
        "--skills",
        default=None,
        help="Comma-separated skill package names under omega_engine_operads/skills/ "
        "(default: every package in the garden)",
    )
    parser.add_argument("--max-lines", type=int, default=DEFAULT_MAX_LINES)
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument(
        "--exceptions",
        default=None,
        help="Path to budget_exceptions.yaml (default: beside this script)",
    )
    args = parser.parse_args()

    root = Path(args.repo_root).resolve() if args.repo_root else repo_root_from()
    if args.exceptions:
        exc_path = Path(args.exceptions)
    else:
        exc_path = Path(__file__).resolve().parent / "budget_exceptions.yaml"
        if not exc_path.is_file():
            fallback_exc = Path(__file__).resolve().parents[1] / "yaml" / "budget_exceptions.yaml"
            if fallback_exc.is_file():
                exc_path = fallback_exc
    skills = (
        [s.strip() for s in args.skills.split(",") if s.strip()]
        if args.skills
        else governed_skills(root)
    )
    return check_budgets(
        root,
        skills,
        args.max_lines,
        args.max_bytes,
        load_exceptions(exc_path),
    )


if __name__ == "__main__":
    sys.exit(main())
