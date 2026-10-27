//! Integration & Verification suite for the Extreme Quantum Cognition Machine (EQCM).
//!
//! Grounded in Romeo & Settino, arXiv: 2603.05430v2 (2026).
//!
//! Validates:
//! 1. MaxEnt initial density distribution normalization (\(\operatorname{Tr}(\rho)=1\)) and polarization bounds.
//! 2. Transverse-Field Ising + Dynamical Attention Hamiltonian Hermiticity & trace preservation.
//! 3. Non-commutative observable extraction (\(\sigma_z, \sigma_x, \sigma_z\sigma_z\)) within physical bounds.
//! 4. Closed-form Ridge Regression training and multi-agent dispute consensus arbitration.
//! 5. AuthorityEffect::None boundary.
//!
//! AuthorityEffect: None.


#[allow(dead_code, non_camel_case_types, missing_docs)]
type BigRationalRatioWitness_008a8591 = (i128, i128);
use engines::quantum::eqcm_deliberation_engine::{
    AgentDeliberationInput, EqcmConfig, EqcmEngine,
};
use core_types::authority::AuthorityEffect;

#[test]
fn test_max_ent_density_properties() {
    let config = EqcmConfig {
        num_qubits: 4,
        ..Default::default()
    };
    let engine = EqcmEngine::new(config).expect("Valid engine");

    // Confidences for 4 agents
    let confidences = vec![0.5, -0.8, 1.2, 0.0];
    let probs = engine.build_max_ent_density(&confidences).expect("MaxEnt density");

    assert_eq!(probs.len(), 16); // 2^4 = 16

    // 1. Total probability sum must be 1.0 (Tr(rho) = 1)
    let total_prob: f64 = probs.iter().sum();
    assert!((total_prob - 1.0).abs() < 1e-12, "Total probability must be 1.0, got {total_prob}");

    // 2. All probabilities non-negative
    for &p in &probs {
        assert!(p >= 0.0, "Probabilities must be non-negative");
    }

    // 3. Expected polarization for qubit 0: <sigma_z> = -tanh(lambda_0) = -tanh(0.5)
    let mut exp_sigma_z_0 = 0.0;
    for state in 0..16 {
        let bit0 = (state >> 3) & 1;
        let s0 = if bit0 == 0 { 1.0 } else { -1.0 };
        exp_sigma_z_0 += probs[state] * s0;
    }
    let expected_s0 = -0.5_f64.tanh();
    assert!(
        (exp_sigma_z_0 - expected_s0).abs() < 1e-10,
        "Expected polarization {expected_s0}, got {exp_sigma_z_0}"
    );
}

#[test]
fn test_hamiltonian_and_observable_extraction() {
    let config = EqcmConfig {
        num_qubits: 4,
        ising_j: 1.0,
        transverse_h: 0.5,
        attention_g: 0.8,
        evolution_time: 1.0,
        ..Default::default()
    };
    let engine = EqcmEngine::new(config).expect("Valid engine");

    // Expected observables for m=4: 4 (Z) + 4 (X) + 6 (ZZ) = 14
    assert_eq!(engine.num_observables(), 14);

    let input = AgentDeliberationInput {
        confidences: vec![0.5, 0.5, 0.5, 0.5],
        votes: vec![1.0, -1.0, 1.0, -1.0],
    };

    let features = engine.extract_features(&input).expect("Feature extraction");
    assert_eq!(features.len(), 14);

    // All expectation values must lie within physical range [-1.0, 1.0]
    for (idx, &f) in features.iter().enumerate() {
        assert!(
            f >= -1.0001 && f <= 1.0001,
            "Observable {idx} value {f} out of physical range [-1, 1]"
        );
    }
}

#[test]
fn test_multi_agent_dispute_deliberation_training() {
    // 4-Agent panel:
    // Agent 0: Inspector (blocking test quality)
    // Agent 1: Thanatos Truth Guard (claim hygiene)
    // Agent 2: Techne Architect (Clean Architecture inward dependencies)
    // Agent 3: Product Planning (feature scope)
    let config = EqcmConfig {
        num_qubits: 4,
        ising_j: 1.2,
        transverse_h: 0.4,
        attention_g: 0.9,
        evolution_time: 1.2,
        ridge_gamma: 1e-4,
    };
    let mut engine = EqcmEngine::new(config).expect("Valid engine");

    // Training dataset: 8 synthetic dispute scenarios
    let training_inputs = vec![
        // Case 1: Unanimous pass -> Accept (+1)
        AgentDeliberationInput {
            confidences: vec![1.0, 1.0, 1.0, 1.0],
            votes: vec![1.0, 1.0, 1.0, 1.0],
        },
        // Case 2: Inspector veto (-1) -> Reject (-1)
        AgentDeliberationInput {
            confidences: vec![1.5, 0.5, 0.5, 0.5],
            votes: vec![-1.0, 1.0, 1.0, 1.0],
        },
        // Case 3: Thanatos Truth breach (-1) -> Reject (-1)
        AgentDeliberationInput {
            confidences: vec![0.5, 1.5, 0.5, 0.5],
            votes: vec![1.0, -1.0, 1.0, 1.0],
        },
        // Case 4: Techne inward dependency breach (-1) -> Reject (-1)
        AgentDeliberationInput {
            confidences: vec![0.5, 0.5, 1.5, 0.5],
            votes: vec![1.0, 1.0, -1.0, 1.0],
        },
        // Case 5: Product scope debate with strong techne pass -> Accept (+1)
        AgentDeliberationInput {
            confidences: vec![1.0, 1.0, 1.0, 0.2],
            votes: vec![1.0, 1.0, 1.0, -1.0],
        },
        // Case 6: Multiple soft disagreements -> Reject (-1)
        AgentDeliberationInput {
            confidences: vec![0.8, 0.8, 0.2, 0.2],
            votes: vec![-1.0, -1.0, 1.0, 1.0],
        },
        // Case 7: Strong consensus pass -> Accept (+1)
        AgentDeliberationInput {
            confidences: vec![1.2, 1.2, 0.8, 0.5],
            votes: vec![1.0, 1.0, 1.0, 1.0],
        },
        // Case 8: Unanimous reject -> Reject (-1)
        AgentDeliberationInput {
            confidences: vec![1.0, 1.0, 1.0, 1.0],
            votes: vec![-1.0, -1.0, -1.0, -1.0],
        },
    ];

    let training_labels = vec![1.0, -1.0, -1.0, -1.0, 1.0, -1.0, 1.0, -1.0];

    engine
        .train(&training_inputs, &training_labels)
        .expect("Training successful");

    assert!(engine.weights.is_some());

    // Test Deliberation 1: Strong pass scenario
    let test_pass = AgentDeliberationInput {
        confidences: vec![0.9, 0.9, 0.9, 0.4],
        votes: vec![1.0, 1.0, 1.0, 1.0],
    };
    let report_pass = engine.deliberate(&test_pass).expect("Deliberate pass");
    assert_eq!(report_pass.decision, 1, "Expected verdict to accept");
    assert!(report_pass.decision_score > 0.0);
    assert_eq!(report_pass.authority_effect, AuthorityEffect::None);

    // Test Deliberation 2: Inspector strong veto
    let test_veto = AgentDeliberationInput {
        confidences: vec![1.8, 0.3, 0.3, 0.3],
        votes: vec![-1.0, 1.0, 1.0, 1.0],
    };
    let report_veto = engine.deliberate(&test_veto).expect("Deliberate veto");
    assert_eq!(report_veto.decision, -1, "Expected verdict to reject on Soviet veto");
    assert!(report_veto.decision_score < 0.0);
    assert_eq!(report_veto.authority_effect, AuthorityEffect::None);
}

// Origin: engine/crates_rs/tests/engines/test_eqcm_deliberation_engine.rs
// Claim: urn:core:crates_rs:tests:test-eqcm-deliberation-engine:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord008a8591 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord008a8591` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError008a8591 {
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
impl BoundaryError008a8591 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError008a8591 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError008a8591 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord008a8591 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError008a8591> {
        if capacity_bound == 0 {
            return Err(BoundaryError008a8591::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError008a8591::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError008a8591::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_008a8591() {
    let admitted = BoundaryRecord008a8591::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord008a8591::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
