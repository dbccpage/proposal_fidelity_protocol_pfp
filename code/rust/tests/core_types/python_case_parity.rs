use core_types::python_unicode::{lowercase, unicode_version, uppercase};
use serde_json::Value;
use sha2::{Digest, Sha256};

#[test]
fn frozen_python_full_unicode_upper_lower_and_contextual_final_sigma(
) -> Result<(), Box<dyn std::error::Error>> {
    let fixture: Value = serde_json::from_str(include_str!("fixtures/python_case_v1.json"))?;
    assert_eq!(fixture["unicode_version"], unicode_version());
    let rows = fixture["vectors"].as_array().ok_or("vectors")?;
    assert_eq!(rows.len(), 20);
    for row in rows {
        let text = row["text"].as_str().ok_or("text")?;
        assert_eq!(uppercase(text), row["upper"]);
        assert_eq!(lowercase(text), row["lower"]);
    }
    let mut upper = Sha256::new();
    let mut lower = Sha256::new();
    let mut contextual = Sha256::new();
    for point in 0..0x110000u32 {
        let Some(character) = char::from_u32(point) else {
            continue;
        };
        let text = character.to_string();
        upper.update(point.to_be_bytes());
        upper.update(uppercase(&text));
        upper.update([0]);
        lower.update(point.to_be_bytes());
        lower.update(lowercase(&text));
        lower.update([0]);
        contextual.update(point.to_be_bytes());
        for text in [
            format!("AΣ{character}1"),
            format!("AΣ{character}A"),
            format!("A{character}Σ"),
        ] {
            contextual.update(lowercase(&text));
            contextual.update([0]);
        }
    }
    assert_eq!(
        format!("{:x}", upper.finalize()),
        fixture["fingerprints"]["upper"]
    );
    assert_eq!(
        format!("{:x}", lower.finalize()),
        fixture["fingerprints"]["lower"]
    );
    assert_eq!(
        format!("{:x}", contextual.finalize()),
        fixture["contextual_fingerprint"]
    );
    Ok(())
}

// Origin: engine/crates_rs/tests/core_types/python_case_parity.rs
// Claim: urn:core:crates_rs:tests:python-case-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
