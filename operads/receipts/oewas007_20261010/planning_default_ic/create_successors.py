"""Add the user-directed default-IC planning successor; preserve older seals."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]
PREFIX = "product_planning_office/receipts/"
EVIDENCE = "workflows_agents_skills/receipts/oewas007_20261010/"
EPICS = "product_planning_office/plans/epics/oewas/"
CHANGED = {
    EPICS + "epic_oe_oewas_007_american_ic_partition_and_typed_schema_plan.md": [
        "Canonical _ic defaults and repository DEV-data cutover are authorized current scope, not held behind opt-in activation.",
        "Full scope remains RESEARCH_HOLD for arbitrary future-estate automation, broader recovery and research obligations; exact actual cutover is bound by its independent ledger.",
        "No native detector admission, malicious-writer isolation, power-loss durability or estate-wide zero-duplicate-ingestion theorem.",
    ],
    EPICS + "epic_oe_oewas_009_cross_engine_ingress_parity_oewas_oeeis_oeadversary_plan.md": [
        "Canonical storage defaults and DEV relocation/portable historical readback are bounded implemented scope; trusted native positive admission remains held.",
        "Full scope remains RESEARCH_HOLD for three-engine admission correlation and remaining complete producer/native/recovery obligations.",
        "Containment and finite writer/readback tests grant no CLEAR, actor license or automatic detector admission.",
    ],
}
def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def create(old_name: str, new_name: str, key: str) -> dict:
    source = ROOT / PREFIX / old_name
    raw = source.read_bytes()
    previous = json.loads(raw)
    current = copy.deepcopy(previous)
    delta = []
    for row in current[key]:
        path = row["path"]
        if path not in CHANGED:
            continue
        old_sha = row["sha256"]
        row["sha256"] = digest((ROOT / path).read_bytes())
        assert row["sha256"] != old_sha
        if key == "epics":
            row["retained_residuals"] = CHANGED[path]
            row["test_plan_status_scope"] = "PROPOSED_NOT_EXECUTED applies to remaining full-epic acceptance, not separately sealed bounded schema/default-router/migration/portable-history/producer tests."
            row["review_provenance"] = "User explicitly changed scope to default canonical _ic and actual DEV-data cutover; earlier opt-in planning preserved through exact predecessor bytes."
        else:
            row["review_scope"] = "Default canonical development storage/cutover and portable immutable history documented; full research/admission obligations held. Scientific-source interpretation is inherited."
        row["bounded_implementation"] = {
            "status": "IMPLEMENTED_BOUNDED",
            "authority_effect": "None",
            "full_epic_status": "RESEARCH_HOLD",
            "default_route": "_ic without an activation prerequisite",
            "development_cutover_evidence": "receipts/oewas007_20261010/development_cutover.json",
            "aggregate_evidence": EVIDENCE + "receipt.json",
            "portable_binding": "_ic/odni/migrations/oewas007",
            "original_byte_snapshots": "_ic/nara/historical/oewas007",
            "evidence_limit": "Exact sealed source/test/binary and cutover ledgers own execution; no universal migration automation, native admission or provenance authority is asserted.",
        }
        delta.append({"path": path, "immediate_predecessor_current_sha256": old_sha, "current_sha256": row["sha256"]})
    assert {row["path"] for row in delta} == set(CHANGED)
    current["previous_immediate_predecessor"] = previous["immediate_predecessor"]
    current["previous_successor_review"] = previous["successor_review"]
    current["immediate_predecessor"] = {"path": source.relative_to(ROOT).as_posix(), "sha256": digest(raw), "scope": "Earlier opt-in planning successor retained unchanged; exact earlier source inputs are separately preserved by predecessor_custody.json."}
    current["successor_review"] = {
        "work_base_revision": "4d207641277ef3d3af16e11aafb411ada1ee10ed",
        "authority_effect": "None",
        "scope": "User-directed canonical _ic defaults, actual repository DEV-data relocation and portable historical byte protection; earlier opt-in constraints are superseded.",
        "changed_inventory_rows": delta,
        "all_other_inventory_rows_unchanged": True,
        "historical_metadata_scope": "Inherited original/OEGOV base, registry/source/research metadata and predecessor pins remain historical; no new scientific-source verification.",
        "predecessor_input_byte_custody": EVIDENCE + "planning_default_ic/predecessor_custody.json",
    }
    for old, new in zip(previous[key], current[key], strict=True):
        assert old["path"] == new["path"]
        if old["path"] not in CHANGED:
            assert old == new
        for field in ("base_sha256", "predecessor_sha256"):
            if field in old:
                assert old[field] == new[field]
    for field in previous:
        if field not in {key, "immediate_predecessor", "successor_review"}:
            assert previous[field] == current[field]
    target = ROOT / PREFIX / new_name
    assert not target.exists(), "Never overwrite sealed successors"
    target.write_bytes((json.dumps(current, indent=2, ensure_ascii=False) + "\n").encode())
    assert source.read_bytes() == raw
    return {"path": target.relative_to(ROOT).as_posix(), "sha256": digest(target.read_bytes()), "changed_rows": len(delta)}

if __name__ == "__main__":
    results = [
        create("epic_obstruction_walk_20261010_oewas007_successor.json", "epic_obstruction_walk_20261010_oewas007_default_ic_successor.json", "epics"),
        create("prior_art_epic_map_20261010_oewas007_successor.json", "prior_art_epic_map_20261010_oewas007_default_ic_successor.json", "prior_epic_inventory"),
    ]
    for rel, old, new in [
        ("product_planning_office/use_cases/epic_tdd_plan_audit.py", "epic_obstruction_walk_20261010_oewas007_successor.json", "epic_obstruction_walk_20261010_oewas007_default_ic_successor.json"),
        ("product_planning_office/use_cases/prior_art_epic_audit.py", "prior_art_epic_map_20261010_oewas007_successor.json", "prior_art_epic_map_20261010_oewas007_default_ic_successor.json"),
    ]:
        path = ROOT / rel
        raw = path.read_bytes()
        assert raw.count(old.encode()) == 1
        path.write_bytes(raw.replace(old.encode(), new.encode()))
    print(json.dumps(results, indent=2))
