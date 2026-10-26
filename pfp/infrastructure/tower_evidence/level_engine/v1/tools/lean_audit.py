"""Audit the axioms of every reported Lean declaration.

    python tools/lean_audit.py          # compare with lean/axioms.txt
    python tools/lean_audit.py --write  # rewrite it (never under an injection)

Runs ``lake env lean lean/AxiomReport.lean`` (the build must be current),
parses every ``#print axioms`` line, and checks three things: every reported
declaration appears exactly once (the census is the generator's list);
every axiom set lies within ``{propext, Quot.sound}`` (``RR-AXIOM``
otherwise); and the report matches the committed ``lean/axioms.txt`` byte
for byte.

AuthorityEffect: None
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.lean_gen import reported  # noqa: E402

POLICY = frozenset({"propext", "Quot.sound"})
REPORT = ROOT / "lean" / "axioms.txt"
LINE = re.compile(r"'(?P<name>[^']+)' (?:depends on axioms: \[(?P<ax>[^\]]*)\]|does not depend on any axioms)")


def collect() -> tuple[int, dict[str, tuple[str, ...]], list[str]]:
    proc = subprocess.run(["lake", "env", "lean", "lean/AxiomReport.lean"], cwd=ROOT,
                          capture_output=True, text=True, check=False)
    found: dict[str, tuple[str, ...]] = {}
    dup: list[str] = []
    for line in (proc.stdout + proc.stderr).splitlines():
        m = LINE.search(line)
        if m:
            name = m.group("name")
            ax = tuple(sorted(a.strip() for a in m.group("ax").split(","))) if m.group("ax") else ()
            if name in found:
                dup.append(name)
            found[name] = ax
    return proc.returncode, found, dup


def render(found: dict[str, tuple[str, ...]]) -> bytes:
    lines = [f"{n}: {', '.join(found[n]) if found[n] else '(none)'}" for n in sorted(found)]
    return ("\n".join(lines) + "\n").encode("ascii")


def parse(data: bytes) -> dict[str, tuple[str, ...]]:
    out: dict[str, tuple[str, ...]] = {}
    for line in data.decode("ascii").splitlines():
        name, _, rest = line.partition(": ")
        out[name] = () if rest == "(none)" else tuple(a.strip() for a in rest.split(","))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args(argv)
    rc, found, dup = collect()
    ok = rc == 0
    if rc != 0:
        print(f"AXIOM REPORT DID NOT ELABORATE (exit {rc})")
    want = reported()
    missing = [n for n in want if n not in found]
    extra = [n for n in found if n not in want]
    for n in missing:
        print(f"CENSUS: {n} has no axiom report")
    for n in extra + dup:
        print(f"CENSUS: {n} is reported but not declared, or twice")
    for n, ax in sorted(found.items()):
        outside = [a for a in ax if a not in POLICY]
        if outside:
            print(f"RR-AXIOM: {n} depends on {', '.join(outside)}")
            ok = False
    ok = ok and not missing and not extra and not dup
    data = render(found)
    if args.write:
        REPORT.write_bytes(data)
    elif not REPORT.exists() or REPORT.read_bytes() != data:
        print("AXIOM REPORT DRIFT: lean/axioms.txt does not match the fresh report")
        ok = False
    print(f"{len(found)} declarations reported, {len(want)} in the census; policy propext, Quot.sound")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
