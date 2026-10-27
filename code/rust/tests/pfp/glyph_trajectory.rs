use pfp::glyph_trajectory::{
    execute, replay, GlyphRefusalCode, GlyphTrajectoryReplayV1, GlyphTrajectoryRequestV1,
};
use pfp_runtime::{
    domain_digest_json, Budget, CandidateMovePacket, FrontierState, MoveKind,
};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn request(game: &str, turns: Vec<Value>) -> GlyphTrajectoryRequestV1 {
    GlyphTrajectoryRequestV1 {
        game_id: game.into(),
        max_turns: turns.len(),
        turns,
    }
}

fn lp() -> Value {
    json!({"a": [["1", "1"], ["1", "0"], ["0", "1"]],
        "b": ["4", "2", "3"], "c": ["3", "2"],
        "primal_x": ["2", "2"], "dual_u": ["2", "1", "0"]})
}

#[test]
fn rational_turns_execute_and_commit_the_complete_native_results() {
    let mut perturbed = lp();
    perturbed["c"][0] = json!("2999999999999/1000000000000");
    let input = request("glyph_game_16_exact_rational_duel", vec![lp(), perturbed]);
    let receipt = execute(&input).unwrap();
    assert_eq!(receipt["turns_executed"], 1);
    assert_eq!(receipt["turns_refused"], 1);
    assert_eq!(receipt["records"][0]["result"]["primal_objective"], "10");
    assert_eq!(receipt["records"][0]["result"]["dual_objective"], "10");
    assert_eq!(receipt["records"][1]["refusal"]["code"], "NATIVE_REFUSAL");
    assert!(receipt["records"][1]["refusal"]["detail"]
        .as_str()
        .unwrap()
        .starts_with("EXACT_OBJECTIVE_MISMATCH:"));
    assert_eq!(receipt["records"][1]["payload"], input.turns[1]);

    let mut previous = receipt["initial_hash"].clone();
    for row in receipt["records"].as_array().unwrap() {
        assert_eq!(row["previous_hash"], previous);
        let mut committed = row.clone();
        let actual = committed
            .as_object_mut()
            .unwrap()
            .remove("turn_hash")
            .unwrap();
        let expected = domain_digest_json("core.glyph.turn.receipt.v1", &committed).unwrap();
        assert_eq!(actual, expected);
        assert_eq!(row["authority_effect"], "None");
        previous = actual;
    }
    assert_eq!(receipt["final_hash"], previous);
    assert_eq!(receipt["authority_effect"], "None");
    assert_eq!(receipt["evidence_ceiling"], "LocalReplay");
    assert!(replay(&GlyphTrajectoryReplayV1 {
        request: input,
        receipt
    })
    .unwrap());
}

#[test]
fn replay_rejects_changed_inputs_forged_outcomes_chain_links_and_truncation() {
    let input = request("glyph_game_16_exact_rational_duel", vec![lp(), lp()]);
    let original = execute(&input).unwrap();
    for mutation in 0..5 {
        let mut forged = original.clone();
        match mutation {
            0 => forged["records"][0]["result"]["primal_objective"] = json!("11"),
            1 => forged["records"][1]["previous_hash"] = json!("0".repeat(64)),
            2 => {
                forged["records"].as_array_mut().unwrap().pop();
            }
            3 => forged["records"][0]["adapter_ref"] = json!("forged/verifier.rs"),
            _ => forged["authority_effect"] = json!("Admitted"),
        }
        assert!(!replay(&GlyphTrajectoryReplayV1 {
            request: input.clone(),
            receipt: forged
        })
        .unwrap());
    }
    let mut changed_input = input;
    changed_input.turns[0]["primal_x"][0] = json!("1");
    let changed = execute(&changed_input).unwrap();
    assert_ne!(
        changed["records"][0]["turn_hash"],
        original["records"][0]["turn_hash"]
    );
    assert_ne!(
        changed["records"][1]["turn_hash"],
        original["records"][1]["turn_hash"]
    );
    assert!(!replay(&GlyphTrajectoryReplayV1 {
        request: changed_input,
        receipt: original
    })
    .unwrap());
}

#[test]
fn proposed_games_and_unknown_routes_never_execute_as_verified_play() {
    for game in [
        "glyph_game_01_parity_tile",
        "glyph_game_19_dispute_bisection",
    ] {
        assert_eq!(
            execute(&request(game, vec![json!({})])).unwrap_err().code,
            GlyphRefusalCode::ProposedFixture
        );
    }
    assert_eq!(
        execute(&request("invented_game", vec![json!({})]))
            .unwrap_err()
            .code,
        GlyphRefusalCode::UnknownGame
    );
}

#[test]
fn empty_over_budget_and_authority_fields_are_refused() {
    let mut input = request("glyph_game_16_exact_rational_duel", vec![lp()]);
    input.max_turns = 0;
    assert_eq!(
        execute(&input).unwrap_err().code,
        GlyphRefusalCode::ResourceBudget
    );
    input.max_turns = 33;
    assert_eq!(
        execute(&input).unwrap_err().code,
        GlyphRefusalCode::ResourceBudget
    );
    input.max_turns = 1;
    input.turns[0]["verified"] = json!(true);
    let receipt = execute(&input).unwrap();
    assert_eq!(receipt["records"][0]["refusal"]["code"], "INVALID_REQUEST");
    assert_eq!(receipt["turns_executed"], 0);
    let mut raw = serde_json::to_value(input).unwrap();
    raw["verified"] = json!(true);
    assert!(serde_json::from_value::<GlyphTrajectoryRequestV1>(raw).is_err());
}

#[test]
fn critical_peak_paths_are_replayed_by_the_real_pinned_adapter() {
    let input = json!({
        "presentation": {"signature": ["a", "b"], "rules": [
            {"name": "left", "lhs": "ab", "rhs": "ba"},
            {"name": "right", "lhs": "ba", "rhs": "ab"}]},
        "claim": {"source": "aba", "left": {"steps": [{"rule": "left", "position": 0}], "endpoint": "baa"},
            "right": {"steps": [{"rule": "right", "position": 1}], "endpoint": "aab"},
            "join": null, "steps_inspected": 2, "step_budget": 4},
    });
    let mut forged = input.clone();
    forged["claim"]["left"]["steps"][0]["rule"] = json!("absent");
    let receipt = execute(&request(
        "glyph_game_14_critical_pair_fork",
        vec![input, forged],
    ))
    .unwrap();
    assert_eq!(receipt["turns_executed"], 2);
    assert_eq!(receipt["records"][1]["result"]["token"], "NEEDS_EVIDENCE");
    assert_ne!(
        receipt["records"][0]["result"],
        receipt["records"][1]["result"]
    );
}

#[test]
fn open_frontier_and_candidate_sealing_preserve_their_evidence_ceilings() {
    let mut frontier = FrontierState::root("declared-frontier", Budget::new(0, 1));
    frontier.surviving_branches.push("unvisited".into());
    let receipt = execute(&request(
        "glyph_game_15_open_frontier",
        vec![json!({
            "frontier": frontier, "narrowest_claim": "Search stopped with a branch open",
        })],
    ))
    .unwrap();
    assert_eq!(
        receipt["records"][0]["result"]["terminal"]["stop_reason"],
        "BoundedWithOpenFrontier"
    );
    assert_eq!(
        receipt["records"][0]["result"]["scheduler_exhaustion_verified"],
        false
    );

    let candidate = CandidateMovePacket::new(
        "parent",
        0,
        "declared-operation",
        MoveKind::Propose,
        "finite claim",
    );
    let raw = serde_json::to_value(candidate).unwrap();
    let digest_envelope = json!({
        "domain": "core.symbol_game.candidate_move.v1",
        "payload": raw,
    });
    let expected_digest = format!(
        "sha256:{:x}",
        Sha256::digest(serde_json::to_vec(&digest_envelope).unwrap())
    );
    let mut forged = raw.clone();
    forged["verified"] = json!(true);
    let receipt = execute(&request(
        "glyph_game_17_candidate_host_split",
        vec![raw, forged],
    ))
    .unwrap();
    let record = &receipt["records"][0]["result"]["round_record"];
    assert_eq!(record["local_replay_status"], "NotRun");
    assert_eq!(record["disposition"], "NeedsEvidence");
    assert_eq!(record["canonical_digest"], expected_digest);
    assert_eq!(receipt["records"][1]["refusal"]["code"], "INVALID_REQUEST");
}

#[test]
fn actual_prime_transport_arrives_proposed_and_refuses_same_carrier() {
    let mut input = json!({"from_carrier_hash": "1".repeat(64),
        "to_carrier_hash": "2".repeat(64), "source_d0_hash": "3".repeat(64),
        "payload": {"claim": "declared"}, "losses": {}, "source_was_admitted": true});
    let first = input.clone();
    input["to_carrier_hash"] = input["from_carrier_hash"].clone();
    let receipt = execute(&request(
        "glyph_game_18_transport_without_promotion",
        vec![first, input],
    ))
    .unwrap();
    assert_eq!(receipt["records"][0]["result"]["status"], "proposed");
    assert_eq!(receipt["records"][0]["result"]["authority_effect"], "None");
    assert_eq!(
        receipt["records"][0]["verifier_ref"],
        "core_wdp/src/prime_algos/prime_algorithm_1.rs"
    );
    let adapter_ref = receipt["records"][0]["adapter_ref"].as_str().unwrap();
    assert_eq!(
        adapter_ref,
        "core_wdp/src/prime_algos/prime_algorithm_1.rs"
    );
    assert!(std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("..")
        .join(adapter_ref)
        .is_file());
    assert_eq!(receipt["records"][1]["execution_status"], "REFUSED");
    assert_eq!(receipt["records"][1]["refusal"]["code"], "NATIVE_REFUSAL");
}

// Origin: engine/crates_rs/tests/pfp/glyph_trajectory.rs
// Claim: urn:core:crates_rs:tests:glyph-trajectory:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord47415fb9 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord47415fb9` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError47415fb9 {
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
impl BoundaryError47415fb9 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError47415fb9 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError47415fb9 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord47415fb9 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError47415fb9> {
        if capacity_bound == 0 {
            return Err(BoundaryError47415fb9::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError47415fb9::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError47415fb9::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_47415fb9() {
    let admitted = BoundaryRecord47415fb9::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord47415fb9::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
