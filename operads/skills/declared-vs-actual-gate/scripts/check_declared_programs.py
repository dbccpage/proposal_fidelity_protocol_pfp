"""Executable form of declared-vs-actual-gate.

AuthorityEffect: None. This program refuses. It does not repair, admit,
promote, archive, or delete, and a green run certifies nothing beyond the
three checks below.

Why this file exists
--------------------
The gate was admitted 2026-09-01 as prose. Prose cannot fail closed. Between
that admission and 2026-09-03 the whole `goo-*` family -- 56 packages -- shipped
no executable check of any kind, and every condition the gate describes was
still present in the tree two days after the gate that describes it was
recorded as landed. A gate nothing runs fails open exactly as reliably as no
gate at all.

The three checks mirror the three in SKILL.md:

    Check 1  every program a stage declares as mandatory resolves on disk
    Check 2  the declared host-mirror set is not a strict subset of the actual
    Check 3  cross-host skill trees are byte-identical after LF normalisation

Exit codes: 0 all checks pass, 1 at least one BLOCKED, 2 the gate could not
run (which is itself a refusal, never a pass).

Usage
-----
    python operads/skills/declared-vs-actual-gate/scripts/check_declared_programs.py
    python ... --json          machine-readable receipt on stdout
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

# Programs the meta-pipeline skills name as mandatory. Each entry is
# (declaring skill, repo-relative path). Sourced from the stage lists in
# auto-oe-autop, auto-improve-autoskill and auto-review-skills, plus the two
# packaging programs the audit wrappers import at run time.
# Vendored from sentinelpy 2026-09-04. These paths were never "missing files"
# in CODA -- they are the shared skill-compiler machinery, which sentinelpy
# owns and this repository had only referenced. Reading absence from disk as
# non-existence produced a parallel reimplementation of all seven; the
# originals are now vendored and this list points at them.
DECLARED_PROGRAMS: tuple[tuple[str, str], ...] = (
    ("autoskill", "operads/skill_operad/skill_compiler/README.md"),
    ("autoskill", "operads/skill_operad/skill_compiler/promote.py"),
    ("autoskill", "operads/skill_operad/skill_compiler/episode.py"),
    ("autoskill", "operads/skill_operad/skill_compiler/resolve.py"),
    ("autoskill", "operads/skill_operad/yaml/routes.yaml"),
    ("autoskill", "runs/skill_compiler/episodes"),
    ("auto-oe-autop", "operads/skill_operad/skill_compiler/knowledge_parity.py"),
    (
        "auto-improve-autoskill",
        "operads/skill_operad/skill_compiler/budget_gate.py",
    ),
    ("auto-improve-autoskill", "operads/skill_operad/yaml/budget_exceptions.yaml"),
    ("auto-review-skills", "operads/skill_operad/skill_compiler/eval_runner.py"),
    ("auto-review-skills", "operads/skill_operad/skill_compiler/eval_bank/cases.json"),
    (
        "auto-review-agents",
        "operations/use_cases/packaging/agent_skill_manifest_audit.py",
    ),
    ("auto-review-skills", "operations/use_cases/packaging/sync_cross_host_skills.py"),
    ("auto-review-skills", "operads/skills/auto-review-skills/scripts/check_skill_usage.py"),
    ("_shared", "operads/skill_operad/verify_skill_names.py"),
    # Data the audits refuse to run without. An absent signature or slice
    # registry is reported blocked rather than treated as "nothing to check".
    ("auto-review-agents", "operads/skill_operad/json/operad_signature.json"),
    (
        "auto-review-agents",
        "operads/skill_operad/json/agent_capability_slices.json",
    ),
    ("auto-review-skills", "operads/registry/lifecycle.yaml"),
    ("auto-review-skills", "operads/registry/capabilities.yaml"),
    ("auto-review-skills", "operads/registry/roles.yaml"),
    ("auto-review-skills", "operads/registry/providers.yaml"),
    ("auto-review-skills", "operads/registry/aliases.yaml"),
    ("auto-review-skills", "operads/registry/compatibility-epoch.yaml"),
)

SKILLS_DIRNAME = "skills"


def repo_root() -> Path:
    """The worktree root: three levels above this file's package."""
    return Path(__file__).resolve().parents[4]


def host_roots(root: Path) -> list[str]:
    """The authoritative host set, derived from the filesystem only."""
    return sorted(
        p.name
        for p in root.iterdir()
        if p.is_dir() and p.name.startswith(".") and (p / SKILLS_DIRNAME).is_dir()
    )


def _source_owner(root: Path) -> str:
    """Use OEOP in the current estate; read legacy host-only fixtures explicitly."""
    return "operads" if (root / "operads").is_dir() else ".agents"


# --------------------------------------------------------------------------
# Check 1 -- declared programs must resolve
# --------------------------------------------------------------------------


def check_declared_programs(root: Path) -> dict:
    rows = []
    for skill, rel in DECLARED_PROGRAMS:
        target = root / rel
        if target.is_file():
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            rows.append({"skill": skill, "path": rel, "verdict": "RAN", "sha256": digest})
        elif target.is_dir():
            rows.append({"skill": skill, "path": rel, "verdict": "RAN", "sha256": None})
        else:
            rows.append({"skill": skill, "path": rel, "verdict": "BLOCKED", "sha256": None})
    blocked = [r for r in rows if r["verdict"] == "BLOCKED"]
    return {
        "name": "declared programs resolve",
        "rows": rows,
        "blocked": len(blocked),
        "verdict": "BLOCKED" if blocked else "PASS",
    }


# --------------------------------------------------------------------------
# Check 2 -- declared mirror set vs actual host set
# --------------------------------------------------------------------------

_HOST_TOKEN = re.compile(r"\.(agents|antigravity|claude|codex|gemini|grok)\b")


def _claim_units(text: str) -> list[str]:
    """Split a manifest into units that could each carry one mirror claim.

    Getting this scope right took two corrections, in both directions:

    * **Line-scoped was too narrow.** A declaration is a sentence, and
      sentences wrap. Wrapping a host line to satisfy the 80-column lint moved
      two of six roots onto a continuation line without the word "mirror", and
      the skill was refused for declaring four of the six it had just named.
    * **Paragraph-scoped was too wide.** A markdown table is one paragraph but
      many independent statements. A table whose third row says "mirror" and
      whose ninth row happens to name `.claude` is not a mirror declaration,
      and reading it as one refused a skill that declared nothing at all.

    So: blank lines separate blocks; within a block, a table row stands alone
    and everything else joins as wrapped prose.
    """
    units: list[str] = []
    for block in text.split("\n\n"):
        lines = block.splitlines()
        if any(ln.lstrip().startswith("|") for ln in lines):
            units.extend(lines)
        else:
            units.append(block)
    return units


def check_mirror_set(root: Path, actual: list[str]) -> dict:
    """A skill may not claim a mirror set smaller than the real host set.

    Only skills that actually make a mirror claim are examined; a skill that
    says nothing about mirroring is not in scope for this check.
    """
    actual_set = set(actual)
    rows = []
    garden = root / _source_owner(root) / SKILLS_DIRNAME
    for skill_md in sorted(garden.glob("*/SKILL.md")):
        text = skill_md.read_text(encoding="utf-8", errors="replace")
        claims = [u for u in _claim_units(text) if "mirror" in u.lower() and _HOST_TOKEN.search(u)]
        if not claims:
            continue
        named = {"." + m.group(1) for u in claims for m in _HOST_TOKEN.finditer(u)}
        # A mirror *set* claim names a set. A line mentioning one root in
        # passing ("`.agents/agents` has inventory. Mirror roots are ...") is
        # prose about mirroring, not a declaration of the mirror set, and
        # treating it as one produces a false refusal.
        if len(named) < 2:
            continue
        if named < actual_set:
            rows.append(
                {
                    "skill": skill_md.parent.name,
                    "declared": sorted(named),
                    "missing": sorted(actual_set - named),
                }
            )
    return {
        "name": "declared mirror set is not a strict subset",
        "actual_hosts": actual,
        "rows": rows,
        "verdict": "BLOCKED" if rows else "PASS",
    }


# --------------------------------------------------------------------------
# Check 3 -- cross-host content parity
# --------------------------------------------------------------------------

# Build debris is not content. Running the test suite creates __pycache__ in
# the canonical root only, which would otherwise be reported as five hosts
# missing two files each -- a gate that blocks on its own test run.
SKIP_DIR_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".ipynb_checkpoints",
}
SKIP_SUFFIXES = {".pyc", ".pyo"}


def _tree(root: Path, host: str) -> dict[str, str]:
    base = root / host / SKILLS_DIRNAME
    out = {}
    for path in base.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(base)
        if rel.suffix in SKIP_SUFFIXES or any(part in SKIP_DIR_NAMES for part in rel.parts):
            continue
        data = path.read_bytes().replace(b"\r\n", b"\n")
        out[rel.as_posix()] = hashlib.sha256(data).hexdigest()
    return out


def check_parity(root: Path, hosts: list[str]) -> dict:
    if len(hosts) < 2:
        return {
            "name": "cross-host parity",
            "verdict": "VACUOUS",
            "note": "fewer than two host roots carry a skills tree",
        }
    canon = _source_owner(root) if _source_owner(root) != ".agents" else hosts[0]
    trees = {h: _tree(root, h) for h in {canon, *hosts}}
    base = trees[canon]
    rows = []
    for host in hosts if canon == "operads" else hosts[1:]:
        other = trees[host]
        missing = sorted(set(base) - set(other))
        extra = sorted(set(other) - set(base))
        differing = sorted(k for k in set(base) & set(other) if base[k] != other[k])
        if missing or extra or differing:
            rows.append(
                {
                    "host": host,
                    "missing": missing[:20],
                    "missing_total": len(missing),
                    "extra": extra[:20],
                    "extra_total": len(extra),
                    "differing": differing[:20],
                    "differing_total": len(differing),
                }
            )
    return {
        "name": "cross-host content parity (LF-normalised)",
        "canonical": canon,
        "members": len(base),
        "rows": rows,
        "verdict": "BLOCKED" if rows else "PASS",
    }


# --------------------------------------------------------------------------
# Check 4 -- agent licence parity between canonical and deployed hosts
# --------------------------------------------------------------------------

AGENTS_DIRNAME = "agents"


def _licence(path: Path) -> frozenset[str] | None:
    """The colour set from an agent's License line, or None if absent."""
    for line in path.read_text(encoding="utf-8").splitlines():
        if "License}(" not in line or "subseteq" not in line:
            continue
        tail = line.split("subseteq", 1)[1]
        if "{" not in tail or "}" not in tail:
            return None
        inner = tail.split("{", 1)[1].split("}", 1)[0]
        toks = (x.strip().strip(chr(92)) for x in inner.replace(",", " ").split())
        return frozenset(t for t in toks if t)
    return None


def check_agent_licences(root: Path, hosts: list[str]) -> dict:
    """A licence is a capability ceiling, so the direction of drift matters.

    Deployed-grants-more is the case that matters: a host would be running an
    agent with colours the canonical panel never granted it. A pure
    re-ordering of the same set is cosmetic and reported as such.
    """
    owner = _source_owner(root)
    canon = root / owner / AGENTS_DIRNAME
    if not canon.is_dir():
        return {
            "name": "agent licence parity",
            "verdict": "VACUOUS",
            "note": f"no {owner}/agents directory",
        }
    populated = [h for h in hosts if h != owner and (root / h / AGENTS_DIRNAME).is_dir()]
    if not populated:
        return {
            "name": "agent licence parity",
            "verdict": "VACUOUS",
            "note": "no deployed host carries an agents directory",
        }
    rows = []
    for agent in sorted(canon.glob("*.md")):
        base = _licence(agent)
        for host in populated:
            other_path = root / host / AGENTS_DIRNAME / agent.name
            if not other_path.is_file():
                rows.append({"agent": agent.stem, "host": host, "direction": "ABSENT"})
                continue
            other = _licence(other_path)
            if base is None or other is None or base == other:
                continue
            if base < other:
                direction, delta = "deployed grants MORE", sorted(other - base)
            elif other < base:
                direction, delta = "deployed grants FEWER", sorted(base - other)
            else:
                direction = "incomparable"
                delta = [f"+{sorted(other - base)}", f"-{sorted(base - other)}"]
            rows.append(
                {
                    "agent": agent.stem,
                    "host": host,
                    "direction": direction,
                    "delta": delta,
                    # the only field the verdict reads: colours the
                    # deployed host holds that canonical never granted
                    "ungranted": sorted(other - base),
                }
            )
    # A deployed host holding colours canonical never granted is a refusal,
    # whether the sets are nested or incomparable. Reading only the "MORE"
    # bucket would wave through every incomparable case, and an incomparable
    # case still adds ungranted colours -- it merely drops some others too.
    blocking = [r for r in rows if r["direction"] == "ABSENT" or r.get("ungranted")]
    return {
        "name": f"agent licence parity (canonical {owner} vs deployed)",
        "rows": rows,
        "blocking": len(blocking),
        "verdict": "BLOCKED" if blocking else ("ADVISORY" if rows else "PASS"),
    }


# --------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true", help="emit the receipt as JSON on stdout")
    args = parser.parse_args(argv)

    root = repo_root()
    if not (root / _source_owner(root) / SKILLS_DIRNAME).is_dir():
        print(f"BLOCKED: no {_source_owner(root)}/skills under {root}", file=sys.stderr)
        return 2

    hosts = host_roots(root)
    checks = [
        check_declared_programs(root),
        check_mirror_set(root, hosts),
        check_parity(root, hosts),
        check_agent_licences(root, hosts),
    ]
    blocked = [c for c in checks if c["verdict"] == "BLOCKED"]
    receipt = {
        "authority_effect": "None",
        "repo_root": str(root),
        "host_roots": hosts,
        "checks": checks,
        "verdict": "BLOCKED" if blocked else "PASS",
    }

    if args.json:
        print(json.dumps(receipt, indent=2))
        return 1 if blocked else 0

    print("declared-vs-actual-gate   AuthorityEffect: None")
    print(f"host roots ({len(hosts)}): {', '.join(hosts)}\n")

    c1 = checks[0]
    print(f"Check 1  {c1['name']}: {c1['verdict']}")
    for row in c1["rows"]:
        mark = "  ok     " if row["verdict"] == "RAN" else "  BLOCKED"
        print(f"{mark} {row['path']}")
        if row["verdict"] == "BLOCKED":
            print(f"           declared mandatory by {row['skill']}")

    c2 = checks[1]
    print(f"\nCheck 2  {c2['name']}: {c2['verdict']}")
    for row in c2["rows"]:
        print(f"  BLOCKED {row['skill']}: declares {row['declared']}, missing {row['missing']}")

    c3 = checks[2]
    print(f"\nCheck 3  {c3['name']}: {c3['verdict']}")
    print(f"  canonical {c3.get('canonical')}: {c3.get('members')} members")
    for row in c3.get("rows", []):
        print(
            f"  BLOCKED {row['host']}: missing {row['missing_total']}, "
            f"extra {row['extra_total']}, differing {row['differing_total']}"
        )
        for key in ("missing", "extra", "differing"):
            for item in row[key]:
                print(f"           {key}: {item}")

    c4 = checks[3]
    print(f"\nCheck 4  {c4['name']}: {c4['verdict']}")
    if c4.get("note"):
        print(f"  {c4['note']}")
    seen = set()
    for row in c4.get("rows", []):
        key = (row["agent"], row["direction"], str(row.get("delta")))
        if key in seen:
            continue
        seen.add(key)
        mark = "BLOCKED" if row["direction"] == "ABSENT" or row.get("ungranted") else "advisory"
        print(f"  {mark} {row['agent']:26} {row['direction']} {row.get('delta', '')}")

    print(f"\nverdict: {receipt['verdict']}")
    return 1 if blocked else 0


if __name__ == "__main__":
    sys.exit(main())
