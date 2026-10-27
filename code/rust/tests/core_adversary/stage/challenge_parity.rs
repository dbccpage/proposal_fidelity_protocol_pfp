use core_adversary::stage::packets::Challenge;
use serde_json::{json, Value};

#[test]
fn frozen_python_challenge_admission_and_canonical_identity(
) -> Result<(), Box<dyn std::error::Error>> {
    let fixture: Value = serde_json::from_str(include_str!("fixtures/python_challenges_v1.json"))?;
    let rows = fixture["vectors"].as_array().ok_or("vectors required")?;
    assert_eq!(rows.len(), 42);
    for (index, row) in rows.iter().enumerate() {
        let raw = serde_json::to_vec(&row["input"])?;
        let actual = match serde_json::from_slice::<Challenge>(&raw) {
            Ok(value) => {
                assert_eq!(json!(value.candidate_id()), row["input"]["candidate_id"]);
                assert_eq!(
                    json!(value.critic_agent_id()),
                    row["input"]["critic_agent_id"]
                );
                assert_eq!(json!(value.trust_domain()), row["input"]["trust_domain"]);
                assert_eq!(
                    json!(value.challenge_kind()),
                    row["input"]["challenge_kind"]
                );
                assert_eq!(json!(value.statement()), row["input"]["statement"]);
                assert_eq!(json!(value.evidence_refs()), row["input"]["evidence_refs"]);
                assert_eq!(json!(value.blocking()), row["input"]["blocking"]);
                assert_eq!(
                    json!(value.authority_effect()),
                    row["input"]["authority_effect"]
                );
                assert_eq!(
                    json!(value.schema_version()),
                    row["input"]["schema_version"]
                );
                assert_eq!(
                    json!(value.challenge_id()),
                    row["expected"]["ok"]["challenge_id"]
                );
                json!({"ok":value})
            }
            Err(error) => {
                let text = error.to_string();
                let message = text
                    .rsplit_once(" at line ")
                    .map_or(text.as_str(), |(message, _)| message);
                json!({"error":message})
            }
        };
        assert_eq!(actual, row["expected"], "challenge vector {index}");
    }
    Ok(())
}

// Origin: engine/crates_rs/tests/core_adversary/stage/challenge_parity.rs
// Claim: urn:core:crates_rs:tests:challenge-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
