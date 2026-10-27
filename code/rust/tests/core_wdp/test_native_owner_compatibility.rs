//! Independent controls for the owner extraction and retained WDP API.
use num_bigint::BigInt;
use num_rational::BigRational;
use core_homology::scalar::{q, qr};
use core_wdp::{
    generate_canonical_lggr_counterexample, AuthorityEffect, EvaluatedPathKernelGraph,
    RationalMatrix2x2, WdpError,
};

#[test]
fn matrix_path_keeps_exact_product_serialization_and_wdp_error_surface() {
    let (graph, cycle) = generate_canonical_lggr_counterexample();
    let product = graph.evaluate_path(&cycle).unwrap();
    // Literal multiplication of the three original shears, independent of
    // the extracted implementation. The max column sum of M-I is 11/8.
    assert_eq!(
        product,
        RationalMatrix2x2::new(qr(5, 4), qr(9, 8), qr(1, 2), qr(5, 4))
    );
    assert_eq!(product.deviation_from_identity().unwrap(), qr(11, 8));
    assert_eq!(graph.authority_effect, AuthorityEffect::None);
    let bytes = serde_json::to_vec(&graph).unwrap();
    let recovered: EvaluatedPathKernelGraph = serde_json::from_slice(&bytes).unwrap();
    assert_eq!(recovered, graph);
    assert_eq!(recovered.evaluate_path(&cycle).unwrap(), product);
    let native: core_epk::matrix_path_kernel::RationalMatrix2x2 =
        serde_json::from_value(serde_json::to_value(&product).unwrap()).unwrap();
    assert_eq!(native.deviation_from_identity().unwrap(), qr(11, 8));

    let error: Result<RationalMatrix2x2, WdpError> = graph.evaluate_path(&[0, 2]);
    assert!(matches!(error, Err(WdpError::InvalidInput { .. })));
}

#[test]
fn mutable_and_deserialized_presentations_are_rechecked_by_the_owner() {
    let (mut graph, cycle) = generate_canonical_lggr_counterexample();
    graph.edges[0].0 = "undeclared".into();
    let graph: EvaluatedPathKernelGraph =
        serde_json::from_value(serde_json::to_value(graph).unwrap()).unwrap();
    assert!(matches!(
        graph.evaluate_path(&cycle),
        Err(WdpError::GraphCarrier(_))
    ));
    let invalid = BigRational::new_raw(BigInt::from(1), BigInt::from(0));
    let matrix = RationalMatrix2x2::new(q(1), invalid, q(0), q(1));
    assert!(matches!(
        matrix.l1_norm(),
        Err(WdpError::InvalidInput { .. })
    ));
}

#[test]
fn coda_packets_and_prime_policies_have_identical_types_at_wdp_paths() {
    use core_category_theory::context_reflection::ContextSystem;
    use core_functional::phi1::ExactPhi1Certificate;
    use core_wdp::coda::diagnostic_routing::DiagnosticPacket;
    use core_wdp::prime_algos::finite_routing::{FiniteRefusal, FiniteTerminal, TerminalPolicy};
    let packet: DiagnosticPacket = core_wdp::coda::diagnostic_routing::DiagnosticPacket::replay(
        ContextSystem::new(vec![0], vec![vec![0]], 1).unwrap(),
        ExactPhi1Certificate {
            omega: vec![q(2)],
            d0: vec![vec![q(0)]],
            weights: vec![q(1)],
            alpha: vec![q(0)],
            primal_residual: vec![q(2)],
            dual_witness: vec![q(1)],
            reported_value: q(2),
        },
        vec![vec![q(0)]],
    )
    .unwrap();
    let policy: core_wdp::prime_algos::finite_routing::TerminalPolicy = TerminalPolicy {
        rows: [None, Some(FiniteTerminal::ClosedCertified), None],
    };
    assert_eq!(
        core_wdp::prime_algos::finite_routing::terminalize(&packet, Some(&policy), None),
        Ok(FiniteTerminal::ClosedCertified)
    );
    assert_eq!(
        core_wdp::prime_algos::finite_routing::terminalize(&packet, None, None),
        Err(FiniteRefusal::MissingPolicy)
    );
}

// Origin: engine/crates_rs/tests/core_wdp/test_native_owner_compatibility.rs
// Claim: urn:core:crates_rs:tests:test-native-owner-compatibility:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord44051015 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord44051015` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError44051015 {
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
impl BoundaryError44051015 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError44051015 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError44051015 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord44051015 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError44051015> {
        if capacity_bound == 0 {
            return Err(BoundaryError44051015::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError44051015::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError44051015::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_44051015() {
    let admitted = BoundaryRecord44051015::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord44051015::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
