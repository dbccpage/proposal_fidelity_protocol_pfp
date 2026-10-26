"""Build a source-pinned P0 disposition register. AuthorityEffect: None."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

import yaml

PILOTS = "omega_engine_education/pilots/"
CATALOG = PILOTS + "demo_004/catalog.yaml"
MATRIX = "omega_engine_woland/tests/pilots/matrix/max_pilot_matrix.yaml"


def build_baseline(root: Path, base: str) -> dict:
    if not re.fullmatch(r"[0-9a-f]{40}", base):
        raise ValueError("BASE_MUST_BE_A_FULL_COMMIT_SHA")
    listing = subprocess.run(
        ["git", "-C", str(root), "ls-tree", "-r", base, "--", PILOTS],
        check=True, capture_output=True, text=True, encoding="utf-8",
    ).stdout
    blobs = {line.split("\t", 1)[1]: line.split("\t", 1)[0].split()[2]
             for line in listing.splitlines()}
    numbered = sorted({p[len(PILOTS):].split("/")[0] for p in blobs
                       if re.match(r"pilot_\d+/", p[len(PILOTS):])})
    results = sorted({p[len(PILOTS + 'results/'):].split("/")[0] for p in blobs
                      if p.startswith(PILOTS + "results/pilot_")})
    needed = [CATALOG] + [PILOTS + f"results/{name}/seed.yaml" for name in results]
    batch = subprocess.run(
        ["git", "-C", str(root), "cat-file", "--batch"], check=True,
        input="".join(blobs[path] + "\n" for path in needed).encode(), capture_output=True,
    ).stdout
    contents = {}
    offset = 0
    for path in needed:
        boundary = batch.index(b"\n", offset)
        size = int(batch[offset:boundary].split()[2])
        offset = boundary + 1
        contents[path] = yaml.safe_load(batch[offset:offset + size])
        offset += size + 1
    catalog = contents[CATALOG]["challenges"]
    return {
        "schema": "pfp.p0-review-baseline.v1", "authority_effect": "None",
        "source_commit": base, "inventories_overlap": True,
        "counts": {"numbered": len(numbered), "catalog": len(catalog), "results": len(results)},
        "numbered_entries": [{
            "id": name, "source_path": PILOTS + name,
            "spec_blob": blobs.get(PILOTS + name + "/spec.yaml"),
            "runner_blob": blobs.get(PILOTS + name + "/run.py"),
            "dependency_registration": "pending_source_review",
            "disposition": "preserve_independent_checker_register_dependencies_before_migration",
            "claim_class": ("unreplayed_executable_control" if PILOTS + name + "/run.py" in blobs
                            else "source_only_specification"),
            "execution_status": "not_replayed_by_this_change", "efficacy_eligible": False,
        } for name in numbered],
        "catalog_entries": [{
            "id": row["id"], "declared_status": row.get("status"),
            "spec_reference": row["path"],
            "spec_blob": blobs.get(PILOTS + "demo_004/" + row["path"]),
            "disposition": "preserve_catalog_reconcile_identity_in_later_stage",
            "claim_class": ("planned_only" if row.get("status") == "planned"
                            else "declared_execution_unverified"),
            "efficacy_eligible": False,
        } for row in catalog],
        "result_entries": [{
            "id": name, "source_path": PILOTS + "results/" + name,
            "artifact_blobs": {p.rsplit("/", 1)[1]: blob for p, blob in blobs.items()
                               if p.startswith(PILOTS + "results/" + name + "/")},
            "eligibility": ("confirmed_answer_bearing_seed" if
                re.search(r'"output"\s*:', contents[PILOTS + f"results/{name}/seed.yaml"]["seed_prompt"])
                else "unverifiable_historical_request"),
            "efficacy_eligible": False, "historical_status_is_not_a_fresh_verdict": True,
        } for name in results],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--base", required=True)
    args = parser.parse_args()
    baseline = build_baseline(args.root, args.base)
    matrix = args.root / MATRIX
    existing = yaml.safe_load(matrix.read_text(encoding="utf-8"))
    if "p0_review_baseline" in existing:
        if existing["p0_review_baseline"] != baseline:
            raise ValueError("BASELINE_ALREADY_FROZEN")
    else:
        with matrix.open("ab") as stream:
            stream.write(("\n" + yaml.safe_dump({"p0_review_baseline": baseline}, sort_keys=False)).encode("utf-8"))
    print(json.dumps(baseline["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
