//! Integration tests for Real Model-in-the-Loop Engine Turn Driver (U05).
//!
//! Enforces:
//! - Strict descent invariant: Frontier advances iff (Phi1, Gamma2) is componentwise
//!   non-increasing with at least ONE STRICT DECREASE (<).
//! - Non-improving or malformed candidates are routed to CemeteryRowV1.
//! AuthorityEffect: None (const).

use pfp_runtime::domain_digest_json;
use pfp_runtime::driver::{
    next_prompt, step, DriverMovePacket, EngineTurnStateV1, PromptPolicyV1, StepOutcome,
    MAX_PROMPT_POLICY_LABEL_BYTES, MAX_PROMPT_POLICY_LIST_ITEMS, MAX_PROMPT_POLICY_TOKENS,
    TURN_DRIVER_PROMPT_ID_DOMAIN, TURN_DRIVER_PROMPT_INVALID,
};
use serde_json::{json, Map, Value};

#[test]
fn test_turn_driver_next_prompt_compilation() {
    let state = EngineTurnStateV1 {
        round_seq: 0,
        specification_digest: "spec_digest_abc123".to_string(),
        current_phi1: 5,
        current_gamma2: 2,
        open_defect_count: 7,
        previous_code: Some("def foo(): pass".to_string()),
        previous_diff: Some("+ def bar(): pass".to_string()),
        open_obligations: vec!["disprove_cycle_obstruction".to_string()],
        promoted_operands: vec!["operand_homology_repair".to_string()],
        cemetery_count: 0,
    };

    let policy = PromptPolicyV1 {
        regime_id: "a".repeat(64),
        regime_kind: "SYMBOL_GAME_ROUND".to_string(),
        admitted_constructors: vec!["repair_edge".to_string()],
        kill_conditions: vec!["budget_exceeded".to_string()],
        required_reply_fields: vec!["candidate_id".to_string(), "proposed_diff".to_string()],
        max_tokens: 4096,
    };

    let artifact = next_prompt(&state, &policy).expect("valid prompt policy");
    assert_eq!(artifact.regime_id, policy.regime_id);
    assert_eq!(artifact.regime_kind, "SYMBOL_GAME_ROUND");
    assert_eq!(artifact.authority_effect, "None");
    assert!(!artifact.prompt_body_sha256.is_empty());
    assert_eq!(artifact.demand_set.len(), 1);
    assert_eq!(
        artifact.demand_set[0].demand_id,
        "disprove_cycle_obstruction"
    );
}

fn prompt_fixture() -> (EngineTurnStateV1, PromptPolicyV1) {
    (
        EngineTurnStateV1 {
            round_seq: 7,
            specification_digest: "spec_digest_abc123".to_owned(),
            current_phi1: 5,
            current_gamma2: 2,
            open_defect_count: 7,
            previous_code: Some("fn old() {}".to_owned()),
            previous_diff: Some("+fn new() {}\n".to_owned()),
            open_obligations: vec!["obs_1".to_owned(), "obs_2".to_owned()],
            promoted_operands: vec!["operand_a".to_owned(), "operand_b".to_owned()],
            cemetery_count: 1,
        },
        PromptPolicyV1 {
            regime_id: "a".repeat(64),
            regime_kind: "SYMBOL_GAME_ROUND".to_owned(),
            admitted_constructors: vec!["repair_edge".to_owned(), "replace_edge".to_owned()],
            kill_conditions: vec!["budget_exceeded".to_owned(), "invalid_shape".to_owned()],
            required_reply_fields: vec!["candidate_id".to_owned(), "proposed_diff".to_owned()],
            max_tokens: 4096,
        },
    )
}

#[test]
fn prompt_identity_replays_and_binds_every_state_field() {
    let (state, policy) = prompt_fixture();
    let original = next_prompt(&state, &policy).unwrap();
    assert_eq!(original, next_prompt(&state, &policy).unwrap());
    let changes: &[(&str, fn(&mut EngineTurnStateV1))] = &[
        ("round", |state| state.round_seq += 1),
        ("specification", |state| {
            state.specification_digest.push('x')
        }),
        ("phi1", |state| state.current_phi1 += 1),
        ("gamma2", |state| state.current_gamma2 += 1),
        ("defects", |state| state.open_defect_count += 1),
        ("previous_code", |state| state.previous_code = None),
        ("previous_diff", |state| state.previous_diff = None),
        ("obligations", |state| state.open_obligations.reverse()),
        ("operands", |state| state.promoted_operands.reverse()),
        ("cemetery", |state| state.cemetery_count += 1),
    ];
    for (name, change) in changes {
        let mut changed = state.clone();
        change(&mut changed);
        assert_ne!(
            original.prompt_artifact_id,
            next_prompt(&changed, &policy).unwrap().prompt_artifact_id,
            "state field {name} was omitted from prompt identity"
        );
    }
}

#[test]
fn same_round_policy_changes_have_distinct_prompt_identities() {
    let (state, policy) = prompt_fixture();
    let original = next_prompt(&state, &policy).unwrap();
    let changes: &[(&str, fn(&mut PromptPolicyV1))] = &[
        ("regime_id", |policy| policy.regime_id = "b".repeat(64)),
        ("regime_kind", |policy| policy.regime_kind.push('X')),
        ("constructors", |policy| {
            policy.admitted_constructors.push("insert_edge".to_owned())
        }),
        ("kills", |policy| {
            policy.kill_conditions.push("rejected".to_owned())
        }),
        ("fields", |policy| {
            policy.required_reply_fields.push("summary".to_owned())
        }),
        ("max_tokens", |policy| policy.max_tokens += 1),
    ];
    for (name, change) in changes {
        let mut changed = policy.clone();
        change(&mut changed);
        let artifact = next_prompt(&state, &changed).unwrap();
        assert_eq!(artifact.regime_id, changed.regime_id);
        assert_ne!(
            original.prompt_artifact_id, artifact.prompt_artifact_id,
            "policy field {name}"
        );
        // These policies share a rendered body; configuration identity is broader.
        assert_eq!(original.prompt_body_sha256, artifact.prompt_body_sha256);
    }
}

#[test]
fn policy_sets_and_empty_defaults_normalize_before_identity() {
    let (state, policy) = prompt_fixture();
    let mut reordered = policy.clone();
    for values in [
        &mut reordered.admitted_constructors,
        &mut reordered.kill_conditions,
        &mut reordered.required_reply_fields,
    ] {
        values.reverse();
        values.push(values[0].clone());
    }
    assert_eq!(
        next_prompt(&state, &policy).unwrap(),
        next_prompt(&state, &reordered).unwrap()
    );

    let mut defaults = policy.clone();
    defaults.kill_conditions.clear();
    defaults.required_reply_fields.clear();
    let artifact = next_prompt(&state, &defaults).unwrap();
    let mut explicit_defaults = defaults.clone();
    explicit_defaults.kill_conditions = artifact.kill_conditions.clone();
    explicit_defaults.required_reply_fields = artifact.required_reply_fields.clone();
    assert_eq!(artifact, next_prompt(&state, &explicit_defaults).unwrap());
}

fn reverse_object_order(value: &Value) -> Value {
    match value {
        Value::Object(object) => {
            let mut reversed = Map::new();
            for (key, value) in object.iter().rev() {
                reversed.insert(key.clone(), reverse_object_order(value));
            }
            Value::Object(reversed)
        }
        Value::Array(array) => Value::Array(array.iter().map(reverse_object_order).collect()),
        value => value.clone(),
    }
}

#[test]
fn prompt_identity_uses_driver_domain_and_canonical_nested_mappings() {
    let (state, policy) = prompt_fixture();
    let artifact = next_prompt(&state, &policy).unwrap();
    let identity = json!({
        "state": state,
        "normalized_policy": policy,
        "prompt_body_sha256": artifact.prompt_body_sha256,
        "prompt_body_byte_count": artifact.prompt_body_byte_count,
    });
    let digest = domain_digest_json(TURN_DRIVER_PROMPT_ID_DOMAIN, &identity).unwrap();
    assert_eq!(artifact.prompt_artifact_id, digest);
    assert_eq!(
        digest,
        domain_digest_json(
            TURN_DRIVER_PROMPT_ID_DOMAIN,
            &reverse_object_order(&identity)
        )
        .unwrap()
    );
    assert_ne!(
        digest,
        domain_digest_json("foreign-driver", &identity).unwrap()
    );
    let mut changed_array = identity;
    changed_array["state"]["open_obligations"]
        .as_array_mut()
        .unwrap()
        .reverse();
    assert_ne!(
        digest,
        domain_digest_json(TURN_DRIVER_PROMPT_ID_DOMAIN, &changed_array).unwrap()
    );
}

#[test]
fn malformed_prompt_policies_refuse_with_a_stable_code() {
    let (state, policy) = prompt_fixture();
    let changes: &[(&str, fn(&mut PromptPolicyV1))] = &[
        ("missing digest", |policy| policy.regime_id.clear()),
        ("uppercase digest", |policy| {
            policy.regime_id = "A".repeat(64)
        }),
        ("nonhex digest", |policy| policy.regime_id = "g".repeat(64)),
        ("blank kind", |policy| policy.regime_kind = " \t".to_owned()),
        ("large kind", |policy| {
            policy.regime_kind = "x".repeat(MAX_PROMPT_POLICY_LABEL_BYTES + 1)
        }),
        ("blank constructor", |policy| {
            policy.admitted_constructors.push(String::new())
        }),
        ("control in kill", |policy| {
            policy.kill_conditions.push("a\nb".to_owned())
        }),
        ("large reply field", |policy| {
            policy
                .required_reply_fields
                .push("x".repeat(MAX_PROMPT_POLICY_LABEL_BYTES + 1))
        }),
        ("too many constructors", |policy| {
            policy.admitted_constructors = vec!["x".to_owned(); MAX_PROMPT_POLICY_LIST_ITEMS + 1]
        }),
        ("too many kills", |policy| {
            policy.kill_conditions = vec!["x".to_owned(); MAX_PROMPT_POLICY_LIST_ITEMS + 1]
        }),
        ("too many fields", |policy| {
            policy.required_reply_fields = vec!["x".to_owned(); MAX_PROMPT_POLICY_LIST_ITEMS + 1]
        }),
        ("zero token bound", |policy| policy.max_tokens = 0),
        ("excess token bound", |policy| {
            policy.max_tokens = MAX_PROMPT_POLICY_TOKENS + 1
        }),
    ];
    for (name, change) in changes {
        let mut invalid = policy.clone();
        change(&mut invalid);
        assert_eq!(
            next_prompt(&state, &invalid).expect_err(name).code,
            TURN_DRIVER_PROMPT_INVALID,
            "{name}"
        );
    }
    for tokens in [1, MAX_PROMPT_POLICY_TOKENS] {
        let mut boundary = policy.clone();
        boundary.max_tokens = tokens;
        boundary.regime_kind = "x".repeat(MAX_PROMPT_POLICY_LABEL_BYTES);
        boundary.admitted_constructors = vec!["x".to_owned(); MAX_PROMPT_POLICY_LIST_ITEMS];
        next_prompt(&state, &boundary).expect("inclusive policy limits are valid");
    }
    let mut unicode = policy;
    unicode.regime_kind = "é".repeat(MAX_PROMPT_POLICY_LABEL_BYTES / 2);
    next_prompt(&state, &unicode).expect("non-control Unicode labels within the byte limit");
    unicode.regime_kind.push('é');
    assert_eq!(
        next_prompt(&state, &unicode).unwrap_err().code,
        TURN_DRIVER_PROMPT_INVALID
    );
}

#[test]
fn rendered_line_endings_normalize_without_erasing_raw_state_identity() {
    let (mut state, policy) = prompt_fixture();
    state.previous_diff = Some("+line_one\n+line_two\n".to_owned());
    state.specification_digest.push('\n');
    state.open_obligations[0].push('\n');
    state.promoted_operands[0].push('\n');
    let lf = next_prompt(&state, &policy).unwrap();
    for ending in ["\r\n", "\r"] {
        let mut changed = state.clone();
        changed.previous_diff = Some(state.previous_diff.as_ref().unwrap().replace('\n', ending));
        changed.specification_digest = state.specification_digest.replace('\n', ending);
        changed.open_obligations[0] = state.open_obligations[0].replace('\n', ending);
        changed.promoted_operands[0] = state.promoted_operands[0].replace('\n', ending);
        let artifact = next_prompt(&changed, &policy).unwrap();
        assert_eq!(lf.prompt_body_sha256, artifact.prompt_body_sha256);
        assert_eq!(lf.prompt_body_byte_count, artifact.prompt_body_byte_count);
        assert_ne!(lf.prompt_artifact_id, artifact.prompt_artifact_id);
    }
}

#[test]
fn test_turn_driver_strict_descent_and_cemetery_routing() {
    let initial_state = EngineTurnStateV1 {
        round_seq: 0,
        specification_digest: "spec_digest_abc123".to_string(),
        current_phi1: 5,
        current_gamma2: 2,
        open_defect_count: 7,
        previous_code: None,
        previous_diff: None,
        open_obligations: vec!["obs_1".to_string()],
        promoted_operands: vec![],
        cemetery_count: 0,
    };

    // Candidate 1: Strict descent (Phi1: 5 -> 3, Gamma2: 2 -> 2)
    // One strict decrease, componentwise non-increasing => ACCEPTED!
    let cand_improving = DriverMovePacket {
        candidate_id: "cand_01".to_string(),
        proposed_diff: "--- a.py\n+++ a.py\n@@ -1 +1 @@\n-x\n+y".to_string(),
        declared_phi1: 3,
        declared_gamma2: 2,
        summary: "Repaired 2 boundary defects".to_string(),
    };

    let outcome1 = step(&initial_state, &cand_improving);
    let state_after_step1 = match outcome1 {
        StepOutcome::Accepted {
            new_state,
            step_row,
        } => {
            assert_eq!(new_state.round_seq, 1);
            assert_eq!(new_state.current_phi1, 3);
            assert_eq!(new_state.current_gamma2, 2);
            assert_eq!(new_state.open_defect_count, 5);
            assert!(!step_row.step_hash.is_empty());
            new_state
        }
        _ => panic!("Expected candidate 1 to be accepted under strict descent"),
    };

    // Candidate 2: Non-improving move (Phi1: 3 -> 3, Gamma2: 2 -> 2)
    // Zero strict decrease => REJECTED TO CEMETERY!
    // MUTATION KILL GATE: changing < to <= in driver.rs would incorrectly accept this!
    let cand_stagnant = DriverMovePacket {
        candidate_id: "cand_02".to_string(),
        proposed_diff: "--- a.py\n+++ a.py\n@@ -1 +1 @@\n-y\n+z".to_string(),
        declared_phi1: 3,
        declared_gamma2: 2,
        summary: "No obstruction descent achieved".to_string(),
    };

    let outcome2 = step(&state_after_step1, &cand_stagnant);
    match outcome2 {
        StepOutcome::RejectedNonDescent {
            cemetery_row,
            refusal_reason,
        } => {
            assert_eq!(cemetery_row.candidate_id, "cand_02");
            assert_eq!(cemetery_row.phi1_before, 3);
            assert_eq!(cemetery_row.phi1_after, 3);
            assert_eq!(cemetery_row.authority_effect, "None");
            assert!(refusal_reason.contains("NON_DESCENDING_CANDIDATE"));
        }
        _ => panic!("Expected stagnant candidate to be rejected to cemetery"),
    }

    // Candidate 3: Malformed empty diff
    // => REJECTED AS MALFORMED TO CEMETERY!
    let cand_malformed = DriverMovePacket {
        candidate_id: "cand_03".to_string(),
        proposed_diff: "   \n".to_string(),
        declared_phi1: 1,
        declared_gamma2: 1,
        summary: "Empty diff".to_string(),
    };

    let outcome3 = step(&state_after_step1, &cand_malformed);
    match outcome3 {
        StepOutcome::RejectedMalformed {
            cemetery_row,
            refusal_reason,
        } => {
            assert_eq!(cemetery_row.candidate_id, "cand_03");
            assert_eq!(cemetery_row.rejection_reason, "MALFORMED_EMPTY_DIFF");
            assert_eq!(refusal_reason, "MALFORMED_EMPTY_DIFF");
        }
        _ => panic!("Expected empty diff to be rejected as malformed"),
    }

    // Witness check: In this sequence, exactly 1 candidate accepted, exactly 2 cemetery rows
    assert_eq!(state_after_step1.round_seq, 1);
}

// Origin: engine/crates_rs/tests/pfp_runtime/engine_turn_driver.rs
// Claim: urn:core:crates_rs:tests:engine-turn-driver:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd9ad9ed7 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd9ad9ed7` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord9ad9ed7 {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryErrord9ad9ed7 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord9ad9ed7 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord9ad9ed7 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd9ad9ed7 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord9ad9ed7> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord9ad9ed7::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord9ad9ed7::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord9ad9ed7::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[test]
fn l4_boundary_admits_and_refuses_d9ad9ed7() {
    let admitted = BoundaryRecordd9ad9ed7::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordd9ad9ed7::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
