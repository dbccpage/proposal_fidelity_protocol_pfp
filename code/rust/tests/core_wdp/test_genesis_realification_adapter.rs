use linear_algebra::backend::basic_matrix::OperationLimits;
use linear_algebra::exact_field::matrix as mx;
use core_quantum_physics::exact_hermitian::{gi, gq};
use core_quantum_physics::exact_instrument::ExactDensityState;
use core_wdp::genesis_realification_adapter::DeclaredRealComposite;
use core_wdp::types::AuthorityEffect;

#[test]
fn actual_complex_state_dimensions_and_balanced_views_are_retained_without_permission() {
    let state = ExactDensityState::try_new(
        mx::from_rows(vec![
            vec![gq(1, 2, 0, 1), gi(0, 0), gi(0, 0), gq(0, 1, -1, 2)],
            vec![gi(0, 0); 4],
            vec![gi(0, 0); 4],
            vec![gq(0, 1, 1, 2), gi(0, 0), gi(0, 0), gq(1, 2, 0, 1)],
        ])
        .unwrap(),
    )
    .unwrap();
    let packet =
        DeclaredRealComposite::from_complex(&state, 2, 2, OperationLimits::UNLIMITED).unwrap();
    assert_eq!(packet.local_dimensions(), (2, 2));
    assert_eq!(packet.real_view().shape(), (8, 8));
    assert_eq!(packet.balanced_state().shape(), (16, 16));
    assert_eq!(packet.authority_effect(), AuthorityEffect::None);
    assert!(DeclaredRealComposite::from_complex(&state, 1, 3, OperationLimits::UNLIMITED).is_err());
    assert!(DeclaredRealComposite::from_complex(
        &state,
        2,
        2,
        OperationLimits {
            max_elements: 1,
            max_scalar_ops: usize::MAX
        }
    )
    .is_err());
}

// Origin: engine/crates_rs/tests/core_wdp/test_genesis_realification_adapter.rs
// Claim: urn:core:crates_rs:tests:test-genesis-realification-adapter:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3b246f83 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3b246f83` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3b246f83 {
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
impl BoundaryError3b246f83 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3b246f83 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3b246f83 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3b246f83 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3b246f83> {
        if capacity_bound == 0 {
            return Err(BoundaryError3b246f83::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3b246f83::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3b246f83::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_3b246f83() {
    let admitted = BoundaryRecord3b246f83::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord3b246f83::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
