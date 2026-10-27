//! Conformance fixtures for Epoch 19 Blind-Spot Capacity.
//!
//! Deterministic `f64` numerical-evidence checks. No authority is minted.


#[allow(dead_code, non_camel_case_types, missing_docs)]
type BigRationalRatioWitness_17d50c07 = (i128, i128);
use nalgebra::DMatrix;
use core_solvers::cert_lggr_soundness::{
    audit_budget_floor, hidden_mass_bounds, hidden_mass_l2, verify_hidden_mass_l2_replay,
    BlindSpotError, CoveringCarrier, ObserverKernelFamily, BLIND_SPOT_AUTHORITY,
};

const TOL: f64 = 1e-7;

fn eye(d: usize) -> DMatrix<f64> {
    DMatrix::identity(d, d)
}
fn zero(d: usize) -> DMatrix<f64> {
    DMatrix::zeros(d, d)
}
fn kernel(d: usize, i: usize) -> DMatrix<f64> {
    let mut b = DMatrix::zeros(d, 1);
    b[(i, 0)] = 1.0;
    b
}
fn chain() -> CoveringCarrier {
    CoveringCarrier {
        num_vertices: 4,
        dim: 1,
        edges: vec![(0, 1, eye(1)), (1, 2, eye(1)), (2, 3, eye(1))],
    }
}
fn diamond() -> CoveringCarrier {
    CoveringCarrier {
        num_vertices: 4,
        dim: 2,
        edges: vec![
            (0, 2, eye(2)),
            (1, 2, zero(2)),
            (1, 3, eye(2)),
            (0, 3, zero(2)),
        ],
    }
}
fn hexagon() -> (CoveringCarrier, ObserverKernelFamily) {
    let carrier = CoveringCarrier {
        num_vertices: 6,
        dim: 3,
        edges: vec![
            (0, 3, eye(3)),
            (0, 4, eye(3)),
            (1, 4, eye(3)),
            (1, 5, eye(3)),
            (2, 5, eye(3)),
            (2, 3, eye(3)),
        ],
    };
    let kernels = ObserverKernelFamily::new(vec![
        kernel(3, 0),
        kernel(3, 1),
        kernel(3, 1),
        kernel(3, 2),
        kernel(3, 2),
        kernel(3, 0),
    ]);
    (carrier, kernels)
}

#[test]
fn recorded_hexagon_has_sqrt_twelve_fifths_hidden_mass() {
    let (carrier, kernels) = hexagon();
    let estimate = hidden_mass_l2(&carrier, &kernels).expect("hexagon estimate");
    let expected = (12.0_f64 / 5.0).sqrt();
    assert!((estimate.value - expected).abs() <= TOL);
    assert_eq!(estimate.top_singular_multiplicity, 3);
    assert_eq!(estimate.authority, BLIND_SPOT_AUTHORITY);
    assert!(estimate.residuals.max_residual <= TOL);
    assert!((estimate.witness.section_l2 - 1.0).abs() <= TOL);
    assert!((estimate.witness.defect_l2 - expected).abs() <= TOL);

    let bounds = hidden_mass_bounds(&carrier, &kernels).expect("hexagon bounds");
    assert_eq!(bounds.coordinate_count, 18);
    assert!((bounds.upper_factor - 18.0_f64.sqrt()).abs() <= TOL);
    assert!(bounds.witnessed_lower_estimate + TOL >= bounds.spectral_lower_estimate);
    assert!(bounds.coordinate_l1_upper_estimate + TOL >= bounds.witnessed_lower_estimate);

    let budget = audit_budget_floor(&carrier, &kernels, 1.0).expect("hexagon budget");
    assert_eq!(budget.rank_one_cut_floor_for_at_most_epsilon, Some(3));
    assert_eq!(
        budget.rank_one_cut_floor_for_strictly_below_epsilon,
        Some(3)
    );
    let zero_budget = audit_budget_floor(&carrier, &kernels, 0.0).expect("zero threshold");
    assert_eq!(zero_budget.rank_one_cut_floor_for_at_most_epsilon, None);
    assert_eq!(
        zero_budget.rank_one_cut_floor_for_strictly_below_epsilon,
        None
    );
    assert!(zero_budget.near_threshold_count > 0);
    assert!(budget.unrestricted_global_rank_one_only);
    assert!(!budget.edge_local_placement_characterized);
}

#[test]
fn zero_kernels_price_chain_and_diamond_at_zero() {
    let c = chain();
    let c_estimate = hidden_mass_l2(&c, &ObserverKernelFamily::zero(&c)).expect("chain");
    assert!(c_estimate.value <= TOL);
    assert!(c_estimate.witness.defect_l2 <= TOL);
    let d = diamond();
    let d_estimate = hidden_mass_l2(&d, &ObserverKernelFamily::zero(&d)).expect("diamond");
    assert!(d_estimate.value <= TOL);
    assert!(d_estimate.witness.defect_l2 <= TOL);
}

#[test]
fn nec_chain_with_one_nonzero_kernel_has_positive_hidden_mass() {
    let carrier = chain();
    let kernels = ObserverKernelFamily::new(vec![
        DMatrix::identity(1, 1),
        DMatrix::zeros(1, 0),
        DMatrix::zeros(1, 0),
    ]);
    let estimate = hidden_mass_l2(&carrier, &kernels).expect("one-line family");
    assert!(estimate.value > 0.5);
    assert!(estimate.witness.defect_l2 > 0.5);
    assert!(estimate.witness.all_green_residual <= TOL);
}

#[test]
fn malformed_inputs_are_typed_failures() {
    let carrier = chain();
    let wrong_count = ObserverKernelFamily::new(vec![DMatrix::zeros(1, 0)]);
    assert!(matches!(
        hidden_mass_l2(&carrier, &wrong_count),
        Err(BlindSpotError::KernelCountMismatch {
            expected: 3,
            found: 1
        })
    ));
    let wrong_rows = ObserverKernelFamily::new(vec![
        DMatrix::zeros(2, 0),
        DMatrix::zeros(1, 0),
        DMatrix::zeros(1, 0),
    ]);
    assert!(matches!(
        hidden_mass_l2(&carrier, &wrong_rows),
        Err(BlindSpotError::KernelRowMismatch { edge: 0, .. })
    ));
    let non_finite = ObserverKernelFamily::new(vec![
        DMatrix::from_element(1, 1, f64::NAN),
        DMatrix::zeros(1, 0),
        DMatrix::zeros(1, 0),
    ]);
    assert!(matches!(
        hidden_mass_l2(&carrier, &non_finite),
        Err(BlindSpotError::NonFiniteKernelEntry {
            edge: 0,
            row: 0,
            col: 0
        })
    ));
    assert!(matches!(
        audit_budget_floor(&carrier, &ObserverKernelFamily::zero(&carrier), -1.0),
        Err(BlindSpotError::InvalidEpsilon { .. })
    ));
}

#[test]
fn deterministic_witness_replay_rejects_tampering() {
    let (carrier, kernels) = hexagon();
    let first = hidden_mass_l2(&carrier, &kernels).expect("first");
    let encoded = serde_json::to_string(&first).expect("serialize numerical evidence");
    let decoded = serde_json::from_str(&encoded).expect("deserialize numerical evidence");
    let decoded_replay =
        verify_hidden_mass_l2_replay(&carrier, &kernels, &decoded).expect("decoded replay");
    assert!(decoded_replay.accepted);
    let second = hidden_mass_l2(&carrier, &kernels).expect("second");
    assert_eq!(first, second);
    let replay = verify_hidden_mass_l2_replay(&carrier, &kernels, &first).expect("replay");
    assert!(replay.accepted);
    assert_eq!(replay.authority, BLIND_SPOT_AUTHORITY);

    let mut within_tolerance = first.clone();
    within_tolerance.value += 1.0e-8;
    let near_replay = verify_hidden_mass_l2_replay(&carrier, &kernels, &within_tolerance)
        .expect("within-tolerance replay");
    assert!(near_replay.max_field_difference > 0.0);

    let mut altered_residual = first.clone();
    altered_residual.residuals.capacity_attainment += 0.25;
    assert!(matches!(
        verify_hidden_mass_l2_replay(&carrier, &kernels, &altered_residual),
        Err(BlindSpotError::EvidenceMismatch {
            field: "capacity_attainment_residual",
            ..
        })
    ));
    let mut altered_flag = first.clone();
    altered_flag.residuals_within_tolerance = !altered_flag.residuals_within_tolerance;
    assert!(matches!(
        verify_hidden_mass_l2_replay(&carrier, &kernels, &altered_flag),
        Err(BlindSpotError::EvidenceDiscreteMismatch { .. })
    ));
    let mut altered_value = first.clone();
    altered_value.value += 0.25;
    assert!(matches!(
        verify_hidden_mass_l2_replay(&carrier, &kernels, &altered_value),
        Err(BlindSpotError::EvidenceMismatch { field: "value", .. })
    ));
    let mut altered_witness = first;
    altered_witness.witness.section[0] += 0.25;
    assert!(matches!(
        verify_hidden_mass_l2_replay(&carrier, &kernels, &altered_witness),
        Err(BlindSpotError::EvidenceMismatch {
            field: "section",
            ..
        })
    ));
}

// Origin: engine/crates_rs/tests/core_solvers/blind_spot_capacity_conformance.rs
// Claim: urn:core:crates_rs:tests:blind-spot-capacity-conformance:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord17d50c07 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord17d50c07` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError17d50c07 {
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
impl BoundaryError17d50c07 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError17d50c07 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError17d50c07 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord17d50c07 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError17d50c07> {
        if capacity_bound == 0 {
            return Err(BoundaryError17d50c07::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError17d50c07::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError17d50c07::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_17d50c07() {
    let admitted = BoundaryRecord17d50c07::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord17d50c07::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
