use core_adversary::stage::genealogy::{
    AntibodyEntry, AntibodyEntryInput, CemeteryHeadstone, GenealogyEntry, GenealogyInput,
    HeadstoneInput,
};
use core_adversary::stage::ports::Refusal;
use serde_json::{json, Value};

fn eval_genealogy_vector(kind: &str, construct: bool, row: &Value) -> Result<Value, Refusal> {
    match kind {
        "headstone" => {
            let res = if construct {
                CemeteryHeadstone::new(serde_json::from_value(row["input"].clone()).unwrap())
            } else {
                CemeteryHeadstone::from_json(&row["input"])
            };
            res.map(|record| {
                assert_eq!(json!(record.headstone_id()), row["expected"]["ok"]["headstone_id"]);
                assert_eq!(json!(record.input().cause_of_death), row["expected"]["ok"]["cause_of_death"]);
                record.to_dict()
            })
        }
        "antibody" => {
            let res = if construct {
                AntibodyEntry::new(serde_json::from_value(row["input"].clone()).unwrap())
            } else {
                AntibodyEntry::from_json(&row["input"])
            };
            res.map(|record| {
                assert_eq!(json!(record.input().occurrences), row["expected"]["ok"]["occurrences"]);
                record.to_dict()
            })
        }
        "genealogy" => {
            let res = if construct {
                GenealogyEntry::new(serde_json::from_value(row["input"].clone()).unwrap())
            } else {
                GenealogyEntry::from_json(&row["input"])
            };
            res.map(|record| {
                assert_eq!(json!(record.lineage_id()), row["expected"]["ok"]["lineage_id"]);
                assert_eq!(json!(record.input().concrete_fixes), row["expected"]["ok"]["concrete_fixes"]);
                record.to_dict()
            })
        }
        other => panic!("unknown kind {other}"),
    }
}

#[test]
fn frozen_python_metadata_admission_source_identity_and_strict_loaders(
) -> Result<(), Box<dyn std::error::Error>> {
    let fixture: Value = serde_json::from_str(include_str!("fixtures/python_genealogy_v1.json"))?;
    let rows = fixture["vectors"].as_array().ok_or("vectors required")?;
    assert_eq!(rows.len(), 135);
    for (index, row) in rows.iter().enumerate() {
        let kind = row["kind"].as_str().unwrap();
        let actual = match eval_genealogy_vector(kind, row["op"] == "construct", row) {
            Ok(value) => json!({"ok":value}),
            Err(error) => json!({"error":error}),
        };
        assert_eq!(actual, row["expected"], "metadata vector {index}: {kind}");
    }
    Ok(())
}

// Origin: engine/crates_rs/tests/core_adversary/stage/genealogy_parity.rs
// Claim: urn:core:crates_rs:tests:genealogy-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
