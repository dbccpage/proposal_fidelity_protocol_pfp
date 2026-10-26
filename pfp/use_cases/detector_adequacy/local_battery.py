"""Exploratory run of the local-only detectors on the Stage A families (decision B1).

    python -m omega_engine_pfp.use_cases.detector_adequacy.local_battery \\
        --lock-commit <sha> --n 300 --out <dir>

It uses the Stage A seed (derived from the same lock commit) and the same families, so a row
here pairs with the Stage A row for the same item. The rates are exploratory, not
certificates. AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from omega_engine_pfp.use_cases.detector_adequacy import battery, detectors, local_detector, traces

DETECTORS = ("D2_E1_disjoint_triangles", *local_detector.LOCAL_DETECTORS)


def _verdict(name: str, trace: traces.Trace) -> Dict[str, Any]:
    if name in local_detector.LOCAL_DETECTORS:
        v = local_detector.run_local(name, trace)
    else:
        v = detectors.run_detector(name, trace)
    cell: Dict[str, Any] = {"status": v.status}
    if v.refusal:
        cell["refusal"] = v.refusal
    if v.status == detectors.RED:
        cell["replayed"] = battery._replays(trace, v.witness)
    return cell


def run(n: int, seed: int) -> List[Dict[str, Any]]:
    families: Dict[str, battery.Family] = {**traces.CLEAN_FAMILIES, **traces.MUTANT_FAMILIES,
                                           **battery.heldout_families()}
    roles = {k: "clean" if k in traces.CLEAN_FAMILIES else "mutant" for k in families}
    rng = random.Random(seed)
    rows, index = [], 0
    for fam, fn in families.items():
        for _ in range(n):
            item = traces.make_item(rng, index)
            index += 1
            trace = fn(traces.clean_trace(item), rng)
            row: Dict[str, Any] = {"family": fam, "role": roles[fam], "item_id": item["item_id"],
                                   "answer_correct": battery._judge(trace)}
            for name in DETECTORS:
                row[name] = _verdict(name, trace)
            rows.append(row)
    return rows


def summarise(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Dict[str, Any]]]:
    table: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(dict)
    by_family: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by_family[r["family"]].append(r)
    for name in DETECTORS:
        for fam, rs in by_family.items():
            c = Counter(r[name]["status"] for r in rs)
            table[name][fam] = {
                "role": rs[0]["role"], "n": len(rs), "green": c[detectors.GREEN], "red": c[detectors.RED],
                "noncertifying": c[detectors.NONCERTIFYING],
                "red_replayed": sum(1 for r in rs if r[name].get("replayed")),
                "refusals": dict(Counter(r[name]["refusal"] for r in rs if "refusal" in r[name])),
            }
    return table


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--lock-commit", required=True)
    ap.add_argument("--n", type=int, default=battery.MIN_N)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    lock = battery.verify_lock(detectors.repo_root(), args.lock_commit)
    if lock["problems"]:
        print(json.dumps({"status": "REFUSED", "lock_problems": lock["problems"]}))
        return 1
    seed = battery.derive_seed(args.lock_commit)
    rows = run(args.n, seed)
    root = detectors.repo_root()
    report = {
        "prereg": battery.PREREG_ID, "amendment": "6.1", "authority_effect": "None",
        "exploratory": True, "lock_commit": args.lock_commit, "seed": seed, "n_per_family": args.n,
        "local_detector_sha256": detectors.sha256_file(
            root / "omega_engine_pfp/use_cases/detector_adequacy/local_detector.py"),
        "table": summarise(rows),
    }
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "local_summary.json").write_text(json.dumps(report, indent=1, sort_keys=True) + "\n",
                                            encoding="utf-8")
    print(json.dumps({k: sum(c["green"] for c in v.values() if c["role"] == "mutant")
                      for k, v in report["table"].items()}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
