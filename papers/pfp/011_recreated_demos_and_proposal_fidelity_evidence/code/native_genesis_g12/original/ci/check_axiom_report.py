"""Compare the freshly built axiom reports against the committed artifact.

Usage: python ci/check_axiom_report.py <lake-build-log>

Two comparisons, and the second is the point.  ``normalize()`` parses a
name out of every report line; log and artifact are then compared as
parsed sets.  That comparison is blind to anything ``normalize()`` cannot
parse: a report form the pattern misses drops out of BOTH sides and the
equality still holds.  That is not hypothetical -- primed theorem names
(``'Derivation.nodup_head''``) did exactly this on 2026-08-18, silently
absent from the artifact while this gate stayed green, and the defect was
found only because ``ci/check_lean_audit.py`` counts reports with a
different, name-blind pattern and disagreed (1417 vs 1413).

So the count is now compared independently of the name parser, by a
pattern that never looks at a name.  A form ``normalize()`` cannot read
still reaches the count, and the mismatch fails here instead of waiting
for a human to notice two numbers differing in two tools.
"""

import pathlib
import re
import sys


def normalize(text: str) -> list[str]:
    out = []
    for line in text.splitlines():
        m = re.search(
            r"'(?P<name>.+?)' (?P<rest>(depends on axioms: "
            r"\[[^\]]*\]|does not depend on any axioms))",
            line,
        )
        if m:
            out.append(f"{m.group('name')}: {m.group('rest')}")
    return sorted(out)


#: Name-blind: matches a report by its TAIL, never by a quoted name, so
#: it cannot share a blind spot with ``normalize()``.
REPORT_TAIL = re.compile(
    r"(?:depends on axioms: \[[^\]]*\]|does not depend on any axioms)\s*$"
)


def count_reports(text: str) -> int:
    """Report lines, counted without parsing a name."""
    return sum(1 for line in text.splitlines() if REPORT_TAIL.search(line))


def main() -> int:
    log_text = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
    artifact_text = pathlib.Path(
        "artifacts/lean_axioms.txt").read_text(encoding="utf-8")

    # Independent signal first: if the name parser has a blind spot, this
    # is what sees it.
    log_n, art_n = count_reports(log_text), count_reports(artifact_text)
    parsed_n = len(normalize(artifact_text))
    if not (log_n == art_n == parsed_n):
        print("FAIL: report counts disagree -- the name parser has a blind spot")
        print(f"  name-blind count, build log:  {log_n}")
        print(f"  name-blind count, artifact:   {art_n}")
        print(f"  normalize() parsed, artifact: {parsed_n}")
        print("  a report form normalize() cannot parse drops from BOTH "
              "sides of the set comparison and hides there; fix the parser.")
        return 1

    fresh = normalize(log_text)
    committed = normalize(artifact_text)
    if not committed:
        print("FAIL: committed axiom report is empty")
        return 1
    if committed != fresh:
        print("FAIL: axiom reports differ between CI build and artifact")
        for line in sorted(set(committed) ^ set(fresh)):
            print(f"  delta: {line}")
        return 1
    print(f"axiom reports match ({len(committed)} theorems; "
          f"name-blind count agrees at {log_n})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
