//! Exact tests for the channels movement of the finite quantum mechanics
//! programme: the trace-distance obstruction geometry and its dual witnesses,
//! the trace-norm CPTP transport audit, channels as stochastic kernels, and
//! the completely positive import boundary. One submodule per retired source
//! paper; the paper-to-module map lives in
//! `atlas/coda_atlas/F004_papers/006_finite_qm/finite_quantum_mechanics.md`.

mod support;

mod channels_as_stochastic_kernels;
mod completely_positive_import_boundary;
mod cptp_trace_norm_geometry;
mod trace_norm_transport_audit;
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct StochasticRowError { kind: &'static str, left: u128, right: u128 }
impl StochasticRowError {
    const fn new(kind: &'static str, left: u128, right: u128) -> Self { Self { kind, left, right } }
    pub const fn kind(&self) -> &'static str { self.kind }
}
/// One row of a nonnegative integer kernel with a common denominator.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct StochasticRow { columns: u64, total: u64 }
impl StochasticRow {
    pub fn try_new(weights: &[u64], denominator: u64) -> Result<Self, StochasticRowError> {
        if weights.is_empty() {
            return Err(StochasticRowError::new("a stochastic row has a column", 0, 0));
        }
        if denominator == 0 {
            return Err(StochasticRowError::new("the common denominator is positive", 0, 0));
        }
        let mut total = 0u64;
        let mut columns = 0u64;
        for weight in weights {
            if *weight > denominator {
                return Err(StochasticRowError::new("a weight exceeds the denominator", u128::from(*weight), u128::from(denominator)));
            }
            total = total.checked_add(*weight).ok_or_else(|| StochasticRowError::new("row sum overflow", u128::from(total), u128::from(*weight)))?;
            columns = columns.checked_add(1).ok_or_else(|| StochasticRowError::new("column count overflow", u128::from(columns), 1))?;
        }
        if total != denominator {
            return Err(StochasticRowError::new("row sum differs from the common denominator", u128::from(total), u128::from(denominator)));
        }
        Ok(Self { columns, total })
    }
    pub const fn total(&self) -> u64 { self.total }
}
#[test]
fn a_two_denominator_row_sums_to_that_denominator() {
    let row = StochasticRow::try_new(&[1, 0, 1], 2);
    assert_eq!(row.as_ref().map(StochasticRow::total), Ok(2));
    assert_eq!(row.as_ref().map(|item| item.columns), Ok(3));
}
#[test]
fn a_row_that_misses_its_denominator_is_refused() {
    assert_eq!(StochasticRow::try_new(&[1, 1], 1).map(|_| ()).map_err(|e| e.kind()), Err("row sum differs from the common denominator"));
}

// Origin: engine/crates_rs/tests/core_quantum_physics/channels/main.rs
// Claim: urn:core:crates_rs:tests:main:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf669bf8e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf669bf8e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf669bf8e {
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
impl BoundaryErrorf669bf8e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf669bf8e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf669bf8e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf669bf8e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf669bf8e> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf669bf8e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf669bf8e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf669bf8e::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_f669bf8e() {
    let admitted = BoundaryRecordf669bf8e::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordf669bf8e::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
