use core_types::python_unicode::{casefold, data_shape, is_printable, unicode_version};
use serde_json::Value;
use sha2::{Digest, Sha256};

#[test]
fn frozen_python_unicode_scalar_fingerprints() -> Result<(), Box<dyn std::error::Error>> {
    let fixture: Value = serde_json::from_str(include_str!("fixtures/python_unicode_v1.json"))?;
    assert_eq!(unicode_version(), fixture["version"]);
    let (fold_entries, nonprintable_ranges) = data_shape();
    assert_eq!(
        fold_entries as u64,
        fixture["fold_entries"].as_u64().ok_or("fold entries")?
    );
    assert_eq!(
        nonprintable_ranges as u64,
        fixture["nonprintable_ranges"]
            .as_u64()
            .ok_or("printability ranges")?
    );
    let (mut fold_hash, mut print_hash) = (Sha256::new(), Sha256::new());
    for point in 0_u32..=0x10ffff {
        let Some(character) = char::from_u32(point) else {
            continue;
        };
        let folded = casefold(&character.to_string());
        fold_hash.update(point.to_be_bytes());
        fold_hash.update(u32::try_from(folded.len())?.to_be_bytes());
        fold_hash.update(folded.as_bytes());
        print_hash.update(point.to_be_bytes());
        print_hash.update([u8::from(is_printable(character))]);
    }
    assert_eq!(
        format!("{:x}", fold_hash.finalize()),
        fixture["casefold_sha256"]
    );
    assert_eq!(
        format!("{:x}", print_hash.finalize()),
        fixture["printability_sha256"]
    );
    Ok(())
}

// Origin: engine/crates_rs/tests/core_types/python_unicode_parity.rs
// Claim: urn:core:crates_rs:tests:python-unicode-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
