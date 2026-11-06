"""Every module outside the root's import closure is named for audit.

Usage: python ci/check_parked_audit.py

``lean4/ParkedAudit.lean`` emits a ``#print axioms`` report for each theorem
of the modules ``lean4/Derivation.lean`` does not import.  Its own list is
checked against the compiled environment at build time, but that check has a
blind spot it cannot fix from inside Lean: a module that NOTHING imports is
absent from the environment altogether, so Lean cannot notice it is missing.

That is precisely the case this gate covers.  Adding a new parked module
fails the `elaborated_modules.txt` census pin, which names it -- but the
documented repair for that failure is to regenerate the pin, and a
regeneration alone would leave the module elaborated, pinned, and still
unaudited.  Here the population is enumerated from the source tree instead,
so the parked set is complete by construction rather than by maintenance.

Three sets, compared:

* census   -- every ``lean4/Derivation/**/*.lean``, as module names
* closure  -- the transitive import closure of ``lean4/Derivation.lean``
* declared -- the ``parkedModules`` array in ``lean4/ParkedAudit.lean``

``census - closure`` must equal ``declared``.

Imports are read as text, and comments are stripped first.

An earlier version of this paragraph claimed an ``import`` "cannot be wrapped,
commented into existence, or spelled inside a doc-string in a way Lean would
accept" and that the doc-string defect behind the environment-based theorem
census "has no analogue here". Both are **WITHDRAWN**: the pattern ran over
raw file text, so a prose line wrapping onto a column-0 ``import
Derivation.IsoCanon`` inside ``/-! ... -/`` would have inflated the root's
closure, dropped that module from ``expected``, and made this gate demand its
REMOVAL from ``parkedModules`` -- after which its reports vanish and the gate
is green. Five lines under ``lean4/`` already begin with ``import``,
``imports`` or ``imported`` from prose wrapping, so the analogue was not
hypothetical.

``_strip_comments`` removes ``--`` line comments and nested ``/- -/`` blocks
before matching, which is what makes the claim true rather than merely
narrower. Stripping also admits a legal trailing ``-- note`` after an import,
which the old end-anchored pattern rejected -- that direction failed loudly
but diagnosed the opposite cause.
"""

from __future__ import annotations

import pathlib
import re
import sys

LEAN = pathlib.Path("lean4")
ROOT_MODULE = "Derivation"
AUDIT_MODULE = "ParkedAudit"
LAKEFILE = LEAN / "lakefile.toml"
AXIOM_ARTIFACT = pathlib.Path("artifacts") / "lean_axioms.txt"

#: Reports the parked census contributes to `artifacts/lean_axioms.txt`.
#: Pinned because nothing else can tell the difference between "this module
#: declares no theorems" and "the census silently stopped running". Update
#: deliberately when a parked module gains or loses a theorem.
EXPECTED_PARKED_REPORTS = 48
#: No `$` anchor: a trailing comment is stripped to spaces by
#: `_strip_comments`, and requiring end-of-line rejected that legal form.
IMPORT = re.compile(r"^import[ \t]+(Derivation(?:\.[A-Za-z0-9_']+)*)[ \t]*(?=\n|$)",
                    re.MULTILINE)
PARKED_ENTRY = re.compile(r"`(Derivation(?:\.[A-Za-z0-9_']+)+)")


def module_path(name: str) -> pathlib.Path:
    return LEAN / (name.replace(".", "/") + ".lean")


def _strip_comments(text: str) -> str:
    """Blank out Lean comments, preserving line structure.

    Newlines are kept so that ``^import`` still anchors correctly on the
    lines that survive. Block comments nest in Lean, so the depth is counted
    rather than matched with a non-greedy regex.
    """
    out: list[str] = []
    depth = 0
    i = 0
    n = len(text)
    while i < n:
        if text.startswith("/-", i):
            depth += 1
            i += 2
            continue
        if text.startswith("-/", i) and depth:
            depth -= 1
            i += 2
            continue
        ch = text[i]
        if depth:
            out.append("\n" if ch == "\n" else " ")
            i += 1
            continue
        if text.startswith("--", i):
            j = text.find("\n", i)
            if j == -1:
                break
            out.append(" " * (j - i))
            i = j
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def imports_of(name: str) -> list[str]:
    path = module_path(name)
    if not path.exists():
        return []
    return IMPORT.findall(_strip_comments(path.read_text(encoding="utf-8")))


def closure_of(root: str) -> set[str]:
    """Transitive import closure, root included."""
    seen: set[str] = {root}
    stack = [root]
    while stack:
        for dep in imports_of(stack.pop()):
            if dep not in seen:
                seen.add(dep)
                stack.append(dep)
    return seen


def declared_parked() -> set[str]:
    text = (LEAN / "ParkedAudit.lean").read_text(encoding="utf-8")
    m = re.search(r"def parkedModules[^#]*#\[(?P<body>.*?)\]", text, re.DOTALL)
    if m is None:
        print("FAIL: could not find `parkedModules` in lean4/ParkedAudit.lean")
        sys.exit(1)
    return set(PARKED_ENTRY.findall(m.group("body")))


def audit_is_wired() -> list[str]:
    """The census must be a build target and must actually be reporting.

    Without this, the whole audit is one word deep. Nothing in `ci/`,
    `tests/`, or the workflow read `defaultTargets`, so deleting
    `"ParkedAudit"` from it dropped all parked reports while every gate
    stayed green: `check_lean_audit` passes (its floor is 40 reports),
    `check_axiom_report` compares the log against the artifact so both sides
    shrink together, the receipts regenerate to the smaller count, and the
    module census never looks at `lean4/*.lean`. The documented repair for the
    resulting diff -- regenerate the artifact -- would have completed the
    disable and left no trace.
    """
    failures = []

    if not LAKEFILE.exists():
        return [f"{LAKEFILE} is missing"]
    lakefile = LAKEFILE.read_text(encoding="utf-8")
    m = re.search(r"^defaultTargets\s*=\s*\[(?P<body>[^\]]*)\]",
                  lakefile, re.MULTILINE)
    if m is None:
        failures.append(f"{LAKEFILE} declares no defaultTargets")
    else:
        targets = re.findall(r'"([^"]+)"', m.group("body"))
        if AUDIT_MODULE not in targets:
            failures.append(
                f"{AUDIT_MODULE} is not in {LAKEFILE}'s defaultTargets "
                f"{targets}, so `lake build` never runs the parked census and "
                f"no parked module contributes an axiom report"
            )

    if not AXIOM_ARTIFACT.exists():
        failures.append(f"{AXIOM_ARTIFACT} is missing")
        return failures
    reports = sum(
        1 for line in AXIOM_ARTIFACT.read_text(encoding="utf-8").splitlines()
        if line.startswith(f"{AUDIT_MODULE}.lean:")
    )
    if reports != EXPECTED_PARKED_REPORTS:
        failures.append(
            f"{AXIOM_ARTIFACT} carries {reports} report(s) from "
            f"{AUDIT_MODULE}.lean, expected {EXPECTED_PARKED_REPORTS}. "
            "If a parked module gained or lost a theorem this is correct -- "
            "update EXPECTED_PARKED_REPORTS. If it dropped to 0 the census "
            "is not running."
        )
    return failures


def main() -> int:
    census = {
        ".".join(p.relative_to(LEAN).with_suffix("").parts)
        for p in (LEAN / ROOT_MODULE).rglob("*.lean")
    }
    if not census:
        print("FAIL: census enumerated no modules - the enumeration is broken")
        return 1

    closure = closure_of(ROOT_MODULE)
    expected = census - closure
    declared = declared_parked()

    failures = audit_is_wired()
    for name in sorted(expected - declared):
        failures.append(
            f"{name} is outside {ROOT_MODULE}.lean's import closure but is "
            f"not named in lean4/ParkedAudit.lean, so no axiom report covers it"
        )
    for name in sorted(declared - expected):
        failures.append(
            f"{name} is named in lean4/ParkedAudit.lean but IS inside "
            f"{ROOT_MODULE}.lean's import closure; remove it there"
        )

    for failure in failures:
        print(f"FAIL: {failure}")
    if failures:
        print(
            "  after editing lean4/ParkedAudit.lean, rebuild and regenerate "
            "artifacts/lean_axioms.txt"
        )
        return 1

    print(
        f"parked audit complete: {len(census)} modules, "
        f"{len(closure & census)} in the root's closure, "
        f"{len(expected)} parked and all named for audit"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
