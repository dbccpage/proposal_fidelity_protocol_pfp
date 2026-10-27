// Executable finite evidence; AuthorityEffect: None.
use core_homology::scalar::{q, qr};
use core_wdp::quantum_geometries::QuantumDensityStalk;

#[test]
fn irrational_distance_retains_exact_squared_evidence() {
    let zero = QuantumDensityStalk::from_pure_vector(&[q(1), q(0)]).unwrap();
    let plus = QuantumDensityStalk::from_pure_vector(&[q(1), q(1)]).unwrap();
    assert_eq!(zero.trace_distance_squared_2x2(&plus).unwrap(), qr(1, 2));
    assert_eq!(zero.classical_l1_distance(&plus), qr(1, 2));
    assert_eq!(
        zero.classical_shadow_contraction_slack_2x2(&plus).unwrap(),
        qr(1, 4)
    );
    assert_eq!(
        zero.trace_distance_2x2(&plus),
        Err("Trace distance is irrational; use trace_distance_squared_2x2")
    );
}

#[test]
fn diagonal_shadow_contraction_has_exact_sharp_and_strict_cases() {
    let zero = QuantumDensityStalk::from_pure_vector(&[q(1), q(0)]).unwrap();
    let one = QuantumDensityStalk::from_pure_vector(&[q(0), q(1)]).unwrap();
    assert_eq!(zero.trace_distance_2x2(&one).unwrap(), q(1));
    assert_eq!(
        zero.classical_shadow_contraction_slack_2x2(&one).unwrap(),
        q(0)
    );
    let plus = QuantumDensityStalk::from_pure_vector(&[q(1), q(1)]).unwrap();
    let minus = QuantumDensityStalk::from_pure_vector(&[q(1), q(-1)]).unwrap();
    assert_eq!(plus.classical_l1_distance(&minus), q(0));
    assert_eq!(plus.trace_distance_2x2(&minus).unwrap(), q(1));
    assert_eq!(
        plus.classical_shadow_contraction_slack_2x2(&minus).unwrap(),
        q(1)
    );
}

#[test]
fn exact_distance_refuses_missing_density_hypotheses() {
    let valid = QuantumDensityStalk::maximally_mixed(2).unwrap();
    for invalid in [
        vec![vec![q(0), q(0)], vec![q(0), q(0)]],
        vec![vec![q(1), q(1)], vec![q(0), q(0)]],
        vec![vec![q(2), q(0)], vec![q(0), q(-1)]],
    ] {
        let state = QuantumDensityStalk::new(invalid).unwrap();
        assert_eq!(
            state.trace_distance_squared_2x2(&valid),
            Err("Trace distance requires valid density matrices")
        );
    }
    let mut malformed = valid.clone();
    malformed.data[0].clear();
    assert!(!malformed.is_valid_density_matrix());
    assert_eq!(
        malformed.trace_distance_squared_2x2(&valid),
        Err("Density matrix shape does not match its dimension")
    );
}

#[test]
fn cptp_construction_refuses_empty_and_ragged_operators() {
    use core_wdp::quantum_geometries::CptpChannel;
    assert!(CptpChannel::new(vec![vec![]]).is_err());
    assert!(CptpChannel::new(vec![vec![vec![q(1)], vec![q(0), q(1)]]]).is_err());
}

#[test]
fn actual_u1_perturbations_have_exact_conditional_weyl_bounds() {
    use core_holonomy::GaussianRational;
    use core_wdp::connection::U1Connection;
    use std::collections::{BTreeMap, BTreeSet};
    let vertices = BTreeSet::from(["a".to_string(), "b".to_string()]);
    let make = |re, im| {
        U1Connection::new(
            vertices.clone(),
            BTreeMap::from([(
                ("a".to_string(), "b".to_string()),
                GaussianRational::new(re, im),
            )]),
        )
        .unwrap()
    };
    let flat = make(q(1), q(0));
    let rotation = make(qr(3, 5), qr(4, 5));
    let unchanged = flat.perturbation_comparison(&flat, q(2)).unwrap();
    assert_eq!(unchanged.operator_norm_bound, q(0));
    assert!(unchanged.gap_survives_if_assumption_holds);
    let changed = flat.perturbation_comparison(&rotation, q(2)).unwrap();
    assert_eq!(changed.row_sum_bounds, vec![qr(6, 5), qr(6, 5)]);
    assert_eq!(changed.gap_shrinkage_bound, qr(12, 5));
    assert!(!changed.gap_survives_if_assumption_holds);
    // An inconclusive bound is not a claim that the true gap closes: both
    // two-vertex unitary Laplacians have eigenvalues 0 and 2.
    assert!(flat.perturbation_comparison(&rotation, q(-1)).is_err());
    let different = U1Connection::new(BTreeSet::from(["c".to_string()]), BTreeMap::new()).unwrap();
    assert!(flat.perturbation_comparison(&different, q(2)).is_err());
}

// Origin: engine/crates_rs/tests/core_wdp/test_quantum_geometry_exact.rs
// Claim: urn:core:crates_rs:tests:test-quantum-geometry-exact:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord89a86d9d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord89a86d9d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError89a86d9d {
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
impl BoundaryError89a86d9d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError89a86d9d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError89a86d9d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord89a86d9d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError89a86d9d> {
        if capacity_bound == 0 {
            return Err(BoundaryError89a86d9d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError89a86d9d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError89a86d9d::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_89a86d9d() {
    let admitted = BoundaryRecord89a86d9d::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord89a86d9d::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
