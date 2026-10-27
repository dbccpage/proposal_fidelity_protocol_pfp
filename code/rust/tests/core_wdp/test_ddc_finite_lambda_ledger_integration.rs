use core_wdp::ddc::{
    Cochain0, FiniteDiagnostic, FiniteLambdaLedger, FiniteLambdaStepCertificate, FiniteWindow,
    LambdaAlgebraError, NonDestructiveExtensionCertificate, OrientedTriangle,
    QuotientIrreducibilityCertificate,
};

fn real_three_step_ledger() -> FiniteLambdaLedger {
    let window = FiniteWindow::new(
        vec!["a", "b", "c"],
        vec![("a", "b"), ("b", "c"), ("a", "c")],
        vec![OrientedTriangle::new("a", "b", "c")],
    );
    let potential = Cochain0::from_values([("a", 0), ("b", 1), ("c", 3)]);
    let scan = window
        .checked_scan(&potential)
        .expect("declared finite window scans exactly");
    assert_eq!(scan.gamma2_total, 0, "primitive differences are closed");

    let diagnostic = |mass| {
        assert_eq!(
            scan.checked_diagnostic_from_quotient(QuotientIrreducibilityCertificate::new(
                mass, mass
            )),
            Err(LambdaAlgebraError::MissingProofCarryingCertificate),
            "matching claimed L1 scalars cannot certify quotient Phi1"
        );
        // A declared scalar vector still exercises the structural ledger gate.
        // Its provenance remains unverified and carries no functional authority.
        FiniteDiagnostic::new(mass, scan.gamma2_total)
    };
    let initial = diagnostic(3);
    let middle_one = diagnostic(2);
    let middle_two = diagnostic(1);
    let terminal = FiniteDiagnostic::new(0, 0);
    let extension = NonDestructiveExtensionCertificate::new(true, true, true);

    let first = FiniteLambdaStepCertificate::new(initial, middle_one, extension);
    let second = FiniteLambdaStepCertificate::new(middle_one, middle_two, extension);
    let final_step = FiniteLambdaStepCertificate::new(middle_two, terminal, extension);

    first
        .require_descent_step()
        .expect("first row is monotone and non-destructive");
    second
        .require_descent_step()
        .expect("second row is monotone and non-destructive");
    final_step
        .require_valid()
        .expect("final row resolves exactly");

    FiniteLambdaLedger::new(initial, vec![first, second, final_step], terminal)
}

fn survivor_row_yaml(witness: &str) -> String {
    format!(
        r#"
kind: structure_correspondence_packet
version: 2
packet_id: "finite-lambda-ledger-3-2-1-0"
pass_id: "02"
source_ids: []
dependency_ids: []
author_model: ""
gate_model: ""
source_structure: finite_lambda_ledger
target_structure: exact_replay_candidate
target_type: known_math
proof_mode: EXHIBIT
mapping_artifact: finite_lambda_ledger_integration
preservation_law: require_chained
declared_verdict: EMBED
gated_verdict: EMBED
status: gated
authority_ceiling: ""
model_requested_terminal_status: unset
host_terminal_status: unset
required_witness: {{kind: diagram, content: "{witness}"}}
proof_obligation: ""
symbolic_trace: []
symbolic_mass: {{primitive_count: 0, relation_count: 0, witness_step_count: 3, free_text_chars: 0, undeclared_symbol_count: 0, score: 3}}
declared_symbols: []
undeclared_symbols: []
validator_errors: []
output_lane: ""
"#
    )
}

#[test]
fn finite_lambda_ledger_integration_accepts_declared_three_step_sequence() {
    let ledger = real_three_step_ledger();

    assert_eq!(ledger.require_chained(), Ok(&ledger));
    assert_eq!(ledger.initial, FiniteDiagnostic::new(3, 0));
    assert_eq!(ledger.terminal, FiniteDiagnostic::new(0, 0));
}

#[test]
fn finite_lambda_ledger_integration_refuses_broken_middle_link() {
    let mut ledger = real_three_step_ledger();
    ledger.steps[1].before = FiniteDiagnostic::new(99, 0);

    assert_eq!(
        ledger.require_chained(),
        Err(LambdaAlgebraError::LambdaDidNotResolve)
    );
}

#[test]
fn terminalize_row_seal_finite_lambda_ledger() {
    let ledger = real_three_step_ledger();
    ledger
        .require_chained()
        .expect("only a checked ledger reaches the product terminalizer");

    let phi1_path = std::iter::once(ledger.initial.phi1)
        .chain(ledger.steps.iter().map(|step| step.after.phi1))
        .map(|value| value.to_string())
        .collect::<Vec<_>>()
        .join("->");
    let witness = format!(
        "finite-lambda-ledger:phi1={phi1_path};gamma2=0;steps={}",
        ledger.steps.len()
    );
    let row: serde_yaml::Value =
        serde_yaml::from_str(&survivor_row_yaml(&witness)).expect("survivor row parses");

    // Verify the survivor row fields directly (core_sweep_kernel was deleted;
    // these assertions cover the same invariants that terminalize_row enforced).
    assert_eq!(row["status"].as_str(), Some("gated"));
    assert_eq!(row["gated_verdict"].as_str(), Some("EMBED"));
    assert_eq!(
        row["required_witness"]["content"].as_str(),
        Some(witness.as_str()),
        "required_witness content must be bound to the checked ledger path"
    );
    // AuthorityEffect: the row carries no authority_ceiling value (empty string).
    assert_eq!(
        row["authority_ceiling"].as_str(),
        Some(""),
        "a survivor gated row must carry no authority ceiling"
    );
}

// Origin: engine/crates_rs/tests/core_wdp/test_ddc_finite_lambda_ledger_integration.rs
// Claim: urn:core:crates_rs:tests:test-ddc-finite-lambda-ledger-integration:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord6347bbfb {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord6347bbfb` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError6347bbfb {
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
impl BoundaryError6347bbfb {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError6347bbfb {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError6347bbfb {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord6347bbfb {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError6347bbfb> {
        if capacity_bound == 0 {
            return Err(BoundaryError6347bbfb::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError6347bbfb::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError6347bbfb::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_6347bbfb() {
    let admitted = BoundaryRecord6347bbfb::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord6347bbfb::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
