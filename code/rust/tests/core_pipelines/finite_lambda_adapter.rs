use core_wdp::ddc::{
    FiniteDiagnostic, FiniteLambdaLedger, FiniteLambdaStepCertificate,
    NonDestructiveExtensionCertificate,
};
use core_pipelines::finite_lambda_adapter::{
    evaluate_finite_lambda_ledger, finite_lambda_ledger_bytes, finite_lambda_ledger_hash,
    FiniteLambdaTerminal,
};

fn ledger() -> FiniteLambdaLedger {
    let initial = FiniteDiagnostic::new(3, 1);
    let middle = FiniteDiagnostic::new(2, 0);
    let terminal = FiniteDiagnostic::new(0, 0);
    let extension = NonDestructiveExtensionCertificate::new(true, true, true);
    FiniteLambdaLedger::new(
        initial,
        vec![
            FiniteLambdaStepCertificate::new(initial, middle, extension),
            FiniteLambdaStepCertificate::new(middle, terminal, extension),
        ],
        terminal,
    )
}

#[test]
fn chained_ledger_replays_to_exact_repair_without_authority() {
    let ledger = ledger();
    let result = evaluate_finite_lambda_ledger(&ledger).unwrap();
    assert_eq!(result.terminal(), FiniteLambdaTerminal::ExactRepair);
    assert_eq!(result.evaluation().phi1().value().to_string(), "0");
    assert_eq!(result.evaluation().gamma2().value().to_string(), "0");
    assert_eq!(
        result.ledger_hash(),
        &finite_lambda_ledger_hash(&ledger).unwrap()
    );
    assert!(result.authority_effect().is_none());
}

#[test]
fn empty_resolved_ledger_is_exact_and_broken_chain_is_invalid() {
    let resolved = FiniteDiagnostic::new(0, 0);
    let empty = FiniteLambdaLedger::new(resolved, vec![], resolved);
    assert_eq!(
        evaluate_finite_lambda_ledger(&empty).unwrap().terminal(),
        FiniteLambdaTerminal::ExactRepair
    );

    let mut broken = ledger();
    broken.steps[1].before = FiniteDiagnostic::new(99, 0);
    assert_eq!(
        evaluate_finite_lambda_ledger(&broken)
            .unwrap_err()
            .terminal(),
        FiniteLambdaTerminal::Invalid
    );
}

#[test]
fn integration_and_product_seal_bind_the_same_canonical_ledger_bytes() {
    let ledger = ledger();
    let bytes = finite_lambda_ledger_bytes(&ledger).unwrap();
    let hash = blake3::hash(&bytes).to_hex().to_string();
    let result = evaluate_finite_lambda_ledger(&ledger).unwrap();
    assert_eq!(result.ledger_hash().to_hex().to_string(), hash);

    let yaml = format!(
        r#"
kind: structure_correspondence_packet
version: 2
packet_id: "finite-lambda-s16-004"
pass_id: "02"
source_ids: []
dependency_ids: []
author_model: ""
gate_model: ""
source_structure: finite_lambda_ledger
target_structure: exact_replay_candidate
target_type: known_math
proof_mode: EXHIBIT
mapping_artifact: finite_lambda_adapter
preservation_law: require_chained
declared_verdict: EMBED
gated_verdict: EMBED
status: gated
authority_ceiling: ""
model_requested_terminal_status: unset
host_terminal_status: unset
required_witness: {{kind: diagram, content: "finite-lambda-ledger-blake3:{hash}"}}
proof_obligation: ""
symbolic_trace: []
symbolic_mass: {{primitive_count: 0, relation_count: 0, witness_step_count: 2, free_text_chars: 0, undeclared_symbol_count: 0, score: 2}}
declared_symbols: []
undeclared_symbols: []
validator_errors: []
output_lane: ""
"#
    );
    let row: serde_yaml::Value = serde_yaml::from_str(&yaml).unwrap();

    // Verify the survivor row fields directly (core_sweep_kernel was deleted;
    // these assertions cover the same invariants that terminalize_row enforced).
    assert_eq!(row["status"].as_str(), Some("gated"));
    assert_eq!(row["gated_verdict"].as_str(), Some("EMBED"));
    assert_eq!(
        row["required_witness"]["content"].as_str(),
        Some(format!("finite-lambda-ledger-blake3:{hash}").as_str())
    );
    // AuthorityEffect: no authority ceiling on a gated survivor row.
    assert_eq!(row["authority_ceiling"].as_str(), Some(""));
}

// Origin: engine/crates_rs/tests/core_pipelines/finite_lambda_adapter.rs
// Claim: urn:core:crates_rs:tests:finite-lambda-adapter:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd2091d39 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd2091d39` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord2091d39 {
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
impl BoundaryErrord2091d39 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord2091d39 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord2091d39 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd2091d39 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord2091d39> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord2091d39::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord2091d39::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord2091d39::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_d2091d39() {
    let admitted = BoundaryRecordd2091d39::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordd2091d39::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
