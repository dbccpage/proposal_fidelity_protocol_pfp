use core_adversary::providers::request::{build_openrouter_body, CandidateRequest, ChatMessage};
use serde_json::{json, Value};

#[test]
fn frozen_python_message_construction_and_native_request_ingress(
) -> Result<(), Box<dyn std::error::Error>> {
    let rows: Vec<Value> = serde_json::from_str(include_str!("fixtures/python_message_v1.json"))?;
    assert_eq!(rows.len(), 14);
    for (index, row) in rows.iter().enumerate() {
        let raw = serde_json::to_vec(&row["input"])?;
        let message = serde_json::from_slice::<ChatMessage>(&raw);
        let actual = match message {
            Ok(message) => {
                let request = CandidateRequest {
                    messages: vec![message.clone()],
                    ..Default::default()
                };
                let body =
                    build_openrouter_body(&request, "a/x", 64).map_err(|error| error.message)?;
                assert_eq!(
                    body["messages"],
                    json!([row["input"]]),
                    "request preserves message {index}"
                );
                json!({"ok": {"role": message.role(), "content": message.content()}})
            }
            Err(error) => {
                let error = error.to_string();
                let message = error
                    .rsplit_once(" at line ")
                    .map_or(error.as_str(), |(message, _)| message);
                json!({"error": message})
            }
        };
        assert_eq!(actual, row["expected"], "JSON message boundary {index}");
        if let (Some(role), Some(content)) = (
            row["input"]["role"].as_str(),
            row["input"]["content"].as_str(),
        ) {
            let actual = match ChatMessage::new(role.into(), content.into()) {
                Ok(message) => json!({"ok": message}),
                Err(error) => {
                    assert_eq!(error.code, "PROVIDER_CONFIG_INVALID");
                    json!({"error": error.message})
                }
            };
            assert_eq!(actual, row["expected"], "typed message constructor {index}");
        }
        if row["expected"].get("error").is_some() {
            let request = json!({"messages":[row["input"]]});
            assert!(
                serde_json::from_slice::<CandidateRequest>(&serde_json::to_vec(&request)?).is_err(),
                "invalid message must refuse during request admission {index}"
            );
        }
    }
    Ok(())
}

// Origin: engine/crates_rs/tests/core_adversary/providers/message_parity.rs
// Claim: urn:core:crates_rs:tests:message-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
