use core_types::python_unicode::{repr_string, unicode_version};
use serde_json::Value;
use sha2::{Digest, Sha256};

#[test]
fn frozen_python_repr_vectors_and_exhaustive_scalar_fingerprint(
) -> Result<(), Box<dyn std::error::Error>> {
    let fixture: Value = serde_json::from_str(include_str!("fixtures/python_repr_v1.json"))?;
    assert_eq!(unicode_version(), fixture["unicode_version"]);
    let rows = fixture["vectors"].as_array().ok_or("vectors")?;
    assert_eq!(rows.len(), 19);
    for (index, row) in rows.iter().enumerate() {
        assert_eq!(
            repr_string(row["text"].as_str().ok_or("text")?),
            row["repr"],
            "repr vector {index}"
        );
    }
    let mut fingerprint = Sha256::new();
    for code in 0..=0x10ffffu32 {
        let Some(character) = char::from_u32(code) else {
            continue;
        };
        let encoded = repr_string(&character.to_string());
        fingerprint.update(code.to_be_bytes());
        fingerprint.update(u32::try_from(encoded.len())?.to_be_bytes());
        fingerprint.update(encoded.as_bytes());
    }
    assert_eq!(
        format!("{:x}", fingerprint.finalize()),
        fixture["scalar_repr_sha256"]
    );
    Ok(())
}

// Origin: engine/crates_rs/tests/core_types/python_repr_parity.rs
// Claim: urn:core:crates_rs:tests:python-repr-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
