use core_adversary::carrier::parse_carrier_json;
use serde_json::{json, Value};

fn verify_carrier_row(index: usize, row: &Value) -> Result<(), Box<dyn std::error::Error>> {
    let result = parse_carrier_json(Some(row["carrier_json"].as_str().unwrap()));
    let actual = match result {
        Ok(value) => {
            let network = value.network();
            assert_eq!(json!(network.nodes()), row["expected"]["ok"]["network"]["nodes"]);
            assert_eq!(json!(network.edges()), row["expected"]["ok"]["network"]["edges"]);
            assert_eq!(json!(network.faces()), row["expected"]["ok"]["network"]["faces"]);
            assert_eq!(json!(network.tetrahedra()), row["expected"]["ok"]["network"]["tetrahedra"]);
            assert_eq!(json!(network.four_simplices()), row["expected"]["ok"]["network"]["four_simplices"]);
            assert_eq!(value.declared(), value.carrier_status() == "DECLARED");
            assert_eq!(json!(value.implicit_zero_edges()), row["expected"]["ok"]["implicit_zero_edges"]);
            for (edge, rational) in value.cochain().entries() {
                assert_eq!(value.cochain().value(edge), Some(rational));
            }
            json!({"ok":value.to_dict()?})
        }
        Err(error) => json!({"error":error}),
    };
    assert_eq!(actual, row["expected"], "carrier vector {index}");
    Ok(())
}

#[test]
fn frozen_python_carrier_shape_orientation_labels_cells_and_ordered_exact_cochain(
) -> Result<(), Box<dyn std::error::Error>> {
    let fixture: Value = serde_json::from_str(include_str!("fixtures/python_carrier_v1.json"))?;
    let rows = fixture["vectors"].as_array().ok_or("vectors")?;
    assert_eq!(rows.len(), 104);
    let later: Value =
        serde_json::from_str(include_str!("fixtures/python_carrier_acceptance_v1.json"))?;
    let accepted = later["vectors"].as_array().ok_or("acceptance rows")?;
    assert_eq!(accepted.len(), 48);
    for (index, row) in rows.iter().chain(accepted).enumerate() {
        verify_carrier_row(index, row)?;
    }
    let empty = parse_carrier_json(None)?;
    assert!(!empty.declared());
    Ok(())
}

// Origin: engine/crates_rs/tests/core_adversary/carrier_parity.rs
// Claim: urn:core:crates_rs:tests:carrier-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
