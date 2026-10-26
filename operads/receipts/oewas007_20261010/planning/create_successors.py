"""Create additive custody successors without altering historical receipt bytes."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]
BASE = "4d207641277ef3d3af16e11aafb411ada1ee10ed"
RECEIPTS = "omega_engine_product_planning_office/receipts/"
EVIDENCE = "omega_engine_workflows_agents_skills/receipts/oewas007_20261010/"
EPICS = "omega_engine_product_planning_office/plans/epics/"
BOUNDED = {
    EPICS + "oewas/epic_oe_oewas_007_american_ic_partition_and_typed_schema_plan.md": [
        "Full scope stays RESEARCH_HOLD: opt-in tooling is not the operator's live estate activation.",
        "All-writer quiescence/checkpoint evidence, complete producer/native parity and historical reader coverage remain independently owned obligations.",
        "No retirement/deletion, power-loss proof, hostile-writer isolation, cryptographic admission or estate-wide zero-duplicate-ingestion claim.",
    ],
    EPICS + "oewas/epic_oe_oewas_009_cross_engine_ingress_parity_oewas_oeeis_oewoland_plan.md": [
        "Full scope stays RESEARCH_HOLD: selected storage routing/readback is bounded; trusted native positive admission remains unavailable.",
        "Complete producer/native parity, live operator activation and PRE_DISPATCH/PRE_SEAL admission correlation need separate evidence.",
        "Containment and finite writer/reader controls cannot grant CLEAR/admission or prove estate-wide quiescence.",
    ],
}
LINKS = {
    EPICS + "oeos/epic_oe_oeos_001_immutable_diagnostic_custody_plan.md",
    EPICS + "oegov/epic_oe_oegov_004_blackrod_warrants_and_observed_enforcement_plan.md",
    EPICS + "oegov/epic_oe_oegov_005_four_e_situated_governance_plan.md",
}
def pin(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()

def create(old_name: str, new_name: str, inventory_key: str) -> dict:
    old_path = RECEIPTS + old_name
    raw = (ROOT / old_path).read_bytes()
    previous = json.loads(raw)
    current = copy.deepcopy(previous)
    changed = []
    for row in current[inventory_key]:
        path = row["path"]
        if path not in BOUNDED and path not in LINKS:
            continue
        old_sha = row["sha256"]
        row["sha256"] = pin(path)
        assert old_sha != row["sha256"], path
        if path in BOUNDED:
            if inventory_key == "epics":
                row["retained_residuals"] = BOUNDED[path]
                row["test_plan_status_scope"] = "PROPOSED_NOT_EXECUTED applies to the remaining full-scope acceptance plan, not separately sealed bounded implementation tests."
                row["review_provenance"] = "OEWAS007 migration implementation/custody review; source-matched bounded execution is separate from full held planning scope."
            else:
                row["review_scope"] = "Bounded migration/storage implementation documented; full scope RESEARCH_HOLD. No new review or verification of the inherited scientific sources."
            row["bounded_implementation"] = {
                "status": "IMPLEMENTED_BOUNDED",
                "authority_effect": "None",
                "full_epic_status": "RESEARCH_HOLD",
                "evidence_directory": EVIDENCE,
                "aggregate_evidence": EVIDENCE + "receipt.json",
                "evidence_limit": "Only exact-source sealed records establish executed controls. No live estate activation, complete producer/native parity or admission authority is asserted here.",
            }
        else:
            row["link_repair_review"] = "Verified removal of obsolete OEOS /python path component only; referenced symbols exist at current flattened paths. Existing residuals and unexecuted full-scope status are unchanged."
        changed.append({"path": path, "predecessor_current_sha256": old_sha, "current_sha256": row["sha256"], "reason": "bounded migration/storage scope and retained holds" if path in BOUNDED else "verified stale OEOS navigation only"})
    assert set(BOUNDED) <= {r["path"] for r in current[inventory_key]}
    if inventory_key == "epics":
        assert LINKS <= {r["path"] for r in current[inventory_key]}
    current["immediate_predecessor"] = {"path": old_path, "sha256": hashlib.sha256(raw).hexdigest(), "scope": "Exact historical OEGOV successor retained byte-for-byte; original predecessor and original-inventory pins remain unchanged."}
    current["successor_review"] = {
        "work_base_revision": BASE,
        "authority_effect": "None",
        "scope": "Current bytes/links for OEWAS007/009 bounded implementation plans plus three verified stale OEOS links. No broad research-source re-review or full epic closure.",
        "changed_inventory_rows": changed,
        "all_other_inventory_rows_unchanged": True,
        "historical_metadata_scope": "Inherited schema/base_revision/original_inventory_base_revision/predecessor/research/source registry metadata describe historical reviews and remain unchanged. Older not_executed statements are historical, not a claim about the separate bounded migration receipts.",
        "source_registry_and_original_base_pins_preserved": True,
    }
    for old, new in zip(previous[inventory_key], current[inventory_key], strict=True):
        assert old["path"] == new["path"]
        if old["path"] not in BOUNDED and old["path"] not in LINKS:
            assert old == new
        for key in ("base_sha256", "predecessor_sha256"):
            if key in old:
                assert old[key] == new[key]
    for key in previous:
        if key != inventory_key:
            assert previous[key] == current[key], key
    assert (ROOT / old_path).read_bytes() == raw
    target = ROOT / RECEIPTS / new_name
    assert not target.exists(), "Never overwrite a successor"
    target.write_bytes((json.dumps(current, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    return {"path": target.relative_to(ROOT).as_posix(), "sha256": pin(target.relative_to(ROOT).as_posix()), "changed_rows": len(changed), "immediate_predecessor_sha256": hashlib.sha256(raw).hexdigest()}

if __name__ == "__main__":
    results = [
        create("epic_obstruction_walk_20261010_oegov_successor.json", "epic_obstruction_walk_20261010_oewas007_successor.json", "epics"),
        create("prior_art_epic_map_20261010_oegov_successor.json", "prior_art_epic_map_20261010_oewas007_successor.json", "prior_epic_inventory"),
    ]
    replacements = {
        "omega_engine_product_planning_office/use_cases/epic_tdd_plan_audit.py": ("epic_obstruction_walk_20261010_oegov_successor.json", "epic_obstruction_walk_20261010_oewas007_successor.json"),
        "omega_engine_product_planning_office/use_cases/prior_art_epic_audit.py": ("prior_art_epic_map_20261010_oegov_successor.json", "prior_art_epic_map_20261010_oewas007_successor.json"),
    }
    for rel, (old, new) in replacements.items():
        path = ROOT / rel
        raw = path.read_bytes()
        assert raw.count(old.encode()) == 1
        path.write_bytes(raw.replace(old.encode(), new.encode()))
    print(json.dumps(results, indent=2))
