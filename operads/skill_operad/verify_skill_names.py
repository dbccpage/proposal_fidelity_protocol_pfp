#!/usr/bin/env python3
"""Verify every skill's frontmatter `name:` equals its directory name, across all hosts.

Why this exists: a `name:` that disagrees with its directory registers a slash-command
nobody can find at the path it lives in. On 2026-07-28 twelve skills shipped broken --
four as `auto-auto-<x>`, seven as `lib-lib-<x>`, one tripled as
`lib-lib-scientific-lib-hypothesis-tree` -- plus two truncated (`svp-sadc`,
`vp-engineering`). None of it was caught by any gate; it surfaced only when someone ran
a one-line loop by hand. Memory is not a gate. This is.

Run from the repo root: python -m operads.skill_operad.verify_skill_names
Exit 0 if every host agrees; exit 1 with a report otherwise (use in a gate).

Optional: --fix rewrites `name:` to the directory name (directory is authoritative,
matching the 2026-07-28 operator ruling "use simply one auto- prefix").
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

HOSTS = [".agents/skills", ".claude/skills", ".codex/skills", ".grok/skills"]
NAME_RE = re.compile(r"^name:\s*(.+)$", re.M)


def check(fix: bool = False) -> int:
    problems: list[str] = []
    fixed = 0

    roots = ["operads/skills", *HOSTS]
    for host in roots:
        root = pathlib.Path(host)
        if not root.is_dir():
            problems.append(f"Host directory missing: {host}")
            continue
        for pkg in sorted(root.iterdir()):
            if not pkg.is_dir() or pkg.name.startswith("_"):
                continue
            skill = pkg / "SKILL.md"
            if not skill.is_file():
                problems.append(f"{skill}: missing SKILL.md")
                continue
            text = skill.read_text(encoding="utf-8")
            m = NAME_RE.search(text)
            if not m:
                problems.append(f"{skill}: no `name:` field")
                continue
            declared = m.group(1).strip()
            if declared == pkg.name:
                continue
            if fix:
                new = NAME_RE.sub(f"name: {pkg.name}", text, count=1)
                # repair broken slash-command self-references too
                new = new.replace("/" + declared, "/" + pkg.name)
                skill.write_text(new, encoding="utf-8")
                fixed += 1
                print(f"FIXED {skill}: {declared} -> {pkg.name}")
            else:
                problems.append(
                    f"{skill}: name={declared!r} != dir={pkg.name!r}"
                )

    if fix:
        print(f"\n{fixed} file(s) repaired.")
        return 0

    if problems:
        print("SKILL NAME MISMATCHES:\n")
        for p in problems:
            print(f"  {p}")
        print(f"\n{len(problems)} mismatch(es). Re-run with --fix to repair.")
        return 1

    print("OK: every skill `name:` matches its directory across all hosts.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", action="store_true", help="rewrite name: to the directory name")
    sys.exit(check(fix=ap.parse_args().fix))
