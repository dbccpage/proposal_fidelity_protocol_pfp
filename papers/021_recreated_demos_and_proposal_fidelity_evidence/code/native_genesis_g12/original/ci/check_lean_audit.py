"""Forbidden-token and axiom audit over the Lean development.

Usage: python ci/check_lean_audit.py <lake-build-log>

* No ``sorry``, ``admit``, ``axiom`` declaration, ``unsafe``, or
  ``partial`` anywhere in the Lean sources.
* Every ``#print axioms`` report in the build log depends only on the
  Lean-core axioms ``propext`` and ``Quot.sound``.
"""

import pathlib
import re
import sys

FORBIDDEN = (
    r"\bsorry\b",
    r"\badmit\b",
    r"^\s*axiom\s",
    r"\bunsafe\b",
    r"\bpartial\b",
)
ALLOWED_AXIOMS = {"propext", "Quot.sound"}
MIN_REPORTS = 40


def main() -> int:
    failures: list[str] = []
    sources = sorted(pathlib.Path("lean4").rglob("*.lean"))
    sources = [p for p in sources if ".lake" not in p.parts]
    for path in sources:
        text = path.read_text(encoding="utf-8")
        for pattern in FORBIDDEN:
            for match in re.finditer(pattern, text, flags=re.M):
                failures.append(f"{path}: forbidden token {match.group(0)!r}")
    log = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
    reports = 0
    for line in log.splitlines():
        if "does not depend on any axioms" in line:
            reports += 1
            continue
        m = re.search(r"depends on axioms: \[([^\]]*)\]", line)
        if m:
            reports += 1
            used = {a.strip() for a in m.group(1).split(",") if a.strip()}
            extra = used - ALLOWED_AXIOMS
            if extra:
                failures.append(f"disallowed axioms {sorted(extra)}: {line}")
    if reports < MIN_REPORTS:
        failures.append(
            f"only {reports} axiom reports found (expected >= {MIN_REPORTS})"
        )
    for failure in failures:
        print(f"FAIL: {failure}")
    if not failures:
        print(
            f"lean audit clean: {len(sources)} sources, "
            f"{reports} axiom reports, axioms within {sorted(ALLOWED_AXIOMS)}"
        )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
