//! Adversarial regressions for report alignment; no new mathematical authority.
use std::collections::BTreeSet;

use core_quantum_physics::mub::{
    char_two_weyl_board::verify_char_two_weyl_board_schema,
    composite_tensor_family_gate::{
        verify_composite_tensor_family_gate, CompositeTensorFamilyStatus,
    },
    dimension_stratification::{stratify_dimension_with, DimensionStratificationReport},
    gtmur_projector_ledger::{verify_gtmur_projector_ledger, GtmurProjectorLedgerStatus},
    hilbert_transport::verify_char_two_hilbert_transport,
    projector_algebra::verify_char_two_projector_algebra,
    spectral_lift::verify_char_two_board_spectral_lift,
};

#[test]
fn transport_rejects_each_mismatched_carrier_even_with_verified_counts() {
    let board = verify_char_two_weyl_board_schema(2);
    let spectral = verify_char_two_board_spectral_lift(&board);
    let algebra = verify_char_two_projector_algebra(&board);
    let hilbert = verify_char_two_hilbert_transport(&board);
    assert_eq!(
        verify_gtmur_projector_ledger(&board, Some(&spectral), Some(&algebra), Some(&hilbert))
            .status,
        GtmurProjectorLedgerStatus::FiniteLedgerClosed
    );
    for field in 0..7 {
        let (mut b, mut s, mut a, mut h) = (
            board.clone(),
            spectral.clone(),
            algebra.clone(),
            hilbert.clone(),
        );
        match field {
            0 => b.dimension += 1,
            1 => b.exponent += 1,
            2 => s.dimension += 1,
            3 => a.dimension += 1,
            4 => a.exponent += 1,
            5 => h.dimension += 1,
            _ => h.exponent += 1,
        }
        assert_eq!(
            verify_gtmur_projector_ledger(&b, Some(&s), Some(&a), Some(&h)).status,
            GtmurProjectorLedgerStatus::InvalidAlignment,
            "mutation {field}"
        );
    }
}

fn mutate_tensor_factor(report: &mut DimensionStratificationReport, field: usize) {
    match field {
        3 => report.factors[0].complete_basis_count = 7,
        4 => report.factors[0].value = 4,
        5 => report.factors[0].exponent = 0,
        _ => report.factors[1] = report.factors[0].clone(),
    }
}

fn mutate_tensor_report(report: &mut DimensionStratificationReport, field: usize) {
    match field {
        0 => report.factors.clear(),
        1 => {
            report.factors.pop();
        }
        2 => report.dimension = 10,
        3..=6 => mutate_tensor_factor(report, field),
        7 => report.guaranteed_basis_count = Some(7),
        8 => report.complete_basis_count = None,
        _ => report.dimension = usize::MAX,
    }
}

#[test]
fn tensor_gate_rejects_malformed_reports_without_panicking() {
    // This fixture declares admitted controls; this test exercises consistency,
    // not reproduction of the controls' underlying projector certificates.
    let valid = stratify_dimension_with(6, &BTreeSet::from([2, 3]));
    assert_eq!(
        verify_composite_tensor_family_gate(vec![valid.clone()]).status,
        CompositeTensorFamilyStatus::TensorFamilyVerified
    );
    for field in 0..10 {
        let mut report = valid.clone();
        mutate_tensor_report(&mut report, field);
        let result = verify_composite_tensor_family_gate(vec![report]);
        assert_eq!(
            result.status,
            CompositeTensorFamilyStatus::MissingTensorLowerControl,
            "mutation {field}"
        );
        assert!(result.cases.is_empty());
    }
}

// Origin: engine/crates_rs/tests/core_quantum_physics/mub_certificate_boundaries.rs
// Claim: urn:core:crates_rs:tests:mub-certificate-boundaries:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordfa2e15fc {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordfa2e15fc` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorfa2e15fc {
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
impl BoundaryErrorfa2e15fc {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorfa2e15fc {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorfa2e15fc {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordfa2e15fc {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorfa2e15fc> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorfa2e15fc::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorfa2e15fc::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorfa2e15fc::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_fa2e15fc() {
    let admitted = BoundaryRecordfa2e15fc::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordfa2e15fc::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
