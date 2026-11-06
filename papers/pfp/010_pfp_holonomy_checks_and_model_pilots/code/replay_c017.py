"""Replay the five retained C017 cases and the model certificates recorded for them.

Run from the package root:  py -3.12 code/replay_c017.py
Reads only files under code/data/c017; makes no network call.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from holonomy import FLAT_TRIVIAL, check_flatness, connection_from_case, verify_claim  # noqa: E402

DATA = Path(__file__).resolve().parent / "data" / "c017"
CASES = ("pois_01", "base_01", "base_02", "base_03", "base_13")


def load(name: str) -> dict:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def host_rows() -> list[tuple[str, str, str, int, int, str]]:
    rows = []
    for name in CASES:
        connection = connection_from_case(load(f"{name}.json"))
        lattice = connection.lattice
        report = check_flatness(connection)
        shape = f"{lattice.rows}x{lattice.cols} {'periodic' if lattice.periodic else 'open'}"
        if report.hol_a is not None:
            detail = f"hol_a={report.hol_a}, hol_b={report.hol_b}"
        elif report.witness_holonomy is not None:
            detail = f"witness holonomy {report.witness_holonomy}"
        else:
            detail = "tree gauge makes every link the identity"
        rows.append(
            (
                name,
                connection.group.name + " " + shape,
                report.verdict,
                report.plaquettes,
                report.skipped_identity_plaquettes,
                detail,
            )
        )
    return rows


def certificate_rows() -> list[tuple[str, str, str, bool, bool | None]]:
    connections = {name: connection_from_case(load(f"{name}.json")) for name in CASES}
    host = {name: check_flatness(c).verdict for name, c in connections.items()}
    rows = []
    for run in load("model_claims.json")["runs"]:
        for entry in run["cases"]:
            verdict = entry["recorded_verdict"]
            label = FLAT_TRIVIAL if verdict == "PURE_GAUGE" else verdict
            ours = None
            if entry["claim"] is not None:
                ours = verify_claim(connections[entry["case"]], entry["claim"])[0]
            rows.append(
                (run["run"], entry["case"], str(verdict), label == host[entry["case"]], ours)
            )
    return rows


def main() -> int:
    print("case     group and lattice    host verdict      plaquettes  skipped  detail")
    for name, shape, verdict, total, skipped, detail in host_rows():
        print(f"{name:8} {shape:20} {verdict:17} {total:10}  {skipped:7}  {detail}")
    print()
    print("run       case     stated verdict   label matches host  certificate accepted here")
    for run, case, verdict, matches, ours in certificate_rows():
        shown = "not retained" if ours is None else str(ours)
        print(f"{run:9} {case:8} {verdict:16} {str(matches):19} {shown}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
