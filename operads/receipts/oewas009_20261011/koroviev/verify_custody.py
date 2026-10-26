"""Verify scoped planning successors and immutable historical inputs without Git writes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
PPO = "omega_engine_product_planning_office/"
EPIC = PPO + "plans/epics/oewas/epic_oe_oewas_009_cross_engine_ingress_parity_oewas_oeeis_oewoland_plan.md"


def pin(path: Path) -> dict:
    raw = path.read_bytes()
    return {"sha256": hashlib.sha256(raw).hexdigest(), "size_bytes": len(raw)}


def load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_bytes())


records = {}
base = json.loads((OUT / "baseline_inventory.json").read_bytes())
for row in base["files"]:
    observed = pin(ROOT / row["snapshot_path"])
    assert observed == {"sha256": row["base_sha256"], "size_bytes": row["base_size_bytes"]}
records["base_snapshots"] = {"verified": len(base["files"]), "base_revision": base["base_revision"]}

canary = json.loads((OUT / "historical_canary_inventory.json").read_bytes())
for relative, expected in canary["files"].items():
    assert pin(ROOT / relative) == expected, relative
records["historical_canary"] = {"verified": len(canary["files"]), "all_bytes_equal": True}

historical = {
    PPO + "plans/epics/epic_relevance_5_prior_art.yaml": "995ca04f8ef001c50f8816051f263b16cfa8b6a0223b59ba07ddfcc9dc2e28cf",
    PPO + "receipts/epic_obstruction_walk_20261010_oewas007_integrated_ic_successor.json": "e5a9e9c57ac0c26e90797eded4d95af856b0340e1b8b0bc93e6b0abcf319a542",
    PPO + "receipts/prior_art_epic_map_20261010_oewas007_integrated_ic_successor.json": "bcd69a1123e6f8c52b1eae8b8893980ac41e76a1291eee81b5407f999524850f",
    "omega_engine_workflows_agents_skills/receipts/oewas007_20261010/planning_default_ic/receipt.json": "b4a6741d23eeefa65051c7264fa5a23a5b14eaf7607b7afcdd05dfb4f9f4f578",
    "_ic/odni/migrations/oewas007/inventory.json": "1f992ce4ec935b7a774fad256332435a948a41fb14492f1036265d15a31e5ca5",
}
records["unchanged_historical_inputs"] = {}
for relative, expected in historical.items():
    actual = pin(ROOT / relative)
    assert actual["sha256"] == expected, relative
    records["unchanged_historical_inputs"][relative] = actual

records["successors"] = []
for old_name, new_name, key in [
    ("epic_obstruction_walk_20261010_oewas007_integrated_ic_successor.json", "epic_obstruction_walk_20261011_oewas009_successor.json", "epics"),
    ("prior_art_epic_map_20261010_oewas007_integrated_ic_successor.json", "prior_art_epic_map_20261011_oewas009_successor.json", "prior_epic_inventory"),
]:
    old_path = PPO + "receipts/" + old_name
    new_path = PPO + "receipts/" + new_name
    old, new = load(old_path), load(new_path)
    assert new["immediate_predecessor"]["path"] == old_path
    assert new["immediate_predecessor"]["sha256"] == pin(ROOT / old_path)["sha256"]
    assert new["oewas009_inherited_immediate_predecessor"] == old["immediate_predecessor"]
    allowed = {key, "immediate_predecessor", "oewas009_inherited_immediate_predecessor", "oewas009_successor_review"}
    assert {k: v for k, v in old.items() if k not in allowed} == {k: v for k, v in new.items() if k not in allowed}
    changed = [a["path"] for a, b in zip(old[key], new[key], strict=True) if a != b]
    assert changed == [EPIC], changed
    row = next(r for r in new[key] if r["path"] == EPIC)
    assert row["sha256"] == pin(ROOT / EPIC)["sha256"]
    old_row = next(r for r in old[key] if r["path"] == EPIC)
    for field in ("predecessor_sha256", "base_sha256", "bounded_implementation", "lifecycle", "test_plan_status"):
        if field in old_row:
            assert row[field] == old_row[field], field
    records["successors"].append({"path": new_path, **pin(ROOT / new_path), "row_count": len(new[key]), "changed_rows": changed, "all_other_rows_and_original_metadata_equal": True})

for relative, old_name, new_name in [
    (PPO + "use_cases/epic_tdd_plan_audit.py", "epic_obstruction_walk_20261010_oewas007_integrated_ic_successor.json", "epic_obstruction_walk_20261011_oewas009_successor.json"),
    (PPO + "use_cases/prior_art_epic_audit.py", "prior_art_epic_map_20261010_oewas007_integrated_ic_successor.json", "prior_art_epic_map_20261011_oewas009_successor.json"),
]:
    original = next(r for r in base["files"] if r["path"] == relative)
    baseline = (ROOT / original["snapshot_path"]).read_bytes()
    assert (ROOT / relative).read_bytes() == baseline.replace(old_name.encode(), new_name.encode())
records["auditor_changes"] = "Exactly two receipt-default literals; no logic changes."

baseline_manifest_row = next(r for r in base["files"] if r["path"] == PPO + "plans/epics/epic_manifest.json")
old_manifest = load(baseline_manifest_row["snapshot_path"])
manifest = load(PPO + "plans/epics/epic_manifest.json")
changed = [a["path"] for a, b in zip(old_manifest["epics"], manifest["epics"], strict=True) if a != b]
assert changed == [EPIC]
assert manifest["epic_count"] == 61 and manifest["source_snapshot_count"] == 0
records["manifest"] = {"epics": 61, "source_snapshots": 0, "changed_rows": changed, "content_set_sha256": manifest["content_set_sha256"]}

records["owner_seals"] = {}
for relative, expected, field in [
    ("omega_engine_workflows_agents_skills/receipts/oewas009_20261011/hella/receipt.json", "8a1bed0ce655cb37070f54fef4c30cf97a39dc35c122c7b2fcf65bca608736e8", "authored_source_and_test_sha256"),
    ("omega_engine_workflows_agents_skills/receipts/oewas009_20261011/azazello/final_handoff.json", "7a3a545fabcfadd4f2e079575b47a71045b52db020cdf08f7052187adb6decd2", "authored_source"),
]:
    actual = pin(ROOT / relative)
    assert actual["sha256"] == expected
    owner = load(relative)
    rows = owner[field]
    if type(rows) is dict:
        rows = [{"path": path, "sha256": digest} for path, digest in rows.items()]
    for row in rows:
        assert pin(ROOT / row["path"])["sha256"] == row["sha256"], row["path"]
    records["owner_seals"][relative] = {**actual, "live_authored_pins_verified": len(rows)}
    if "binary" in owner:
        binary = owner["binary"]
        assert pin(Path(binary["path"])) == {"sha256": binary["sha256"], "size_bytes": binary["bytes"]}
        records["native_binary"] = binary

record = {"schema": "oewas009.koroviev.custody-verification.v1", "authority_effect": "None", "result": "PASS_SCOPED", "checks": records, "claim_ceiling": "Hash/navigation/source-preservation checks only; native and candidate test executions remain the independently pinned owner receipts. No Git mutation, provider, admission or theorem claim."}
p = OUT / "custody_verification.json"
assert not p.exists()
p.write_bytes((json.dumps(record, indent=2, sort_keys=True) + "\n").encode())
print(json.dumps(record, indent=2, sort_keys=True))
