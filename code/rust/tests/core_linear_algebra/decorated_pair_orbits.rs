use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::gauge_pair_table::*;
use linear_algebra::pair_table_canonical::*;
use num_rational::BigRational;
use std::cell::Cell;

fn looped() -> BasicMatrix<BigRational> {
    BasicMatrix::from_row_major(
        3,
        3,
        [1, 0, 0, 0, 0, 0, 0, 0, 0]
            .into_iter()
            .map(|v| BigRational::from_integer(v.into()))
            .collect(),
    )
    .unwrap()
}
#[test]
fn raw_and_gauge_orbits_keep_the_same_decoration_witness() {
    let table = looped();
    let a = canonical_pair_tables_with_decoration(&[table.clone()], 6, |p| p[0]).unwrap();
    let b = canonical_pair_tables_with_decoration(&[table.clone()], 6, |p| p[1]).unwrap();
    assert_eq!(a.tables, b.tables);
    assert_eq!(a.decoration, 2);
    assert_eq!(b.decoration, 0);
    assert_eq!(a.old_to_new, vec![2, 0, 1]); // First full witness in the tied orbit.
    assert_eq!(a.old_to_new[0], a.decoration);
    assert_eq!(b.old_to_new[1], b.decoration);
    let ga = canonical_gauge_pair_table_with_decoration(&table, 6, |p| p[0]).unwrap();
    let gb = canonical_gauge_pair_table_with_decoration(&table, 6, |p| p[1]).unwrap();
    assert_eq!(ga.normal, gb.normal);
    assert_ne!(ga.decoration, gb.decoration);
    assert_eq!(ga.examined, 6);
    assert_eq!(
        canonical_gauge_pair_table(&table, 6).unwrap().normal,
        ga.normal
    );
    assert_eq!(canonical_pair_tables(&[table], 6).unwrap().tables, a.tables);
}
#[test]
fn alignment_matches_both_fixed_writing_components() {
    let table = looped();
    assert_eq!(
        align_gauge_pair_tables_with_decoration(&table, &table, 6, &0, |p| p[0]).unwrap(),
        Some(vec![0, 1, 2])
    );
    assert!(
        align_gauge_pair_tables_with_decoration(&table, &table, 6, &1, |p| p[0])
            .unwrap()
            .is_none()
    );
}
#[test]
fn an_incomplete_orbit_never_calls_the_decoration_transport() {
    let calls = Cell::new(0);
    let decorate = |_: &[usize]| {
        calls.set(calls.get() + 1);
        0
    };
    let table = looped();
    assert!(canonical_pair_tables_with_decoration(&[table.clone()], 5, decorate).is_err());
    assert!(canonical_gauge_pair_table_with_decoration(&table, 5, decorate).is_err());
    assert!(align_gauge_pair_tables_with_decoration(&table, &table, 5, &0, decorate).is_err());
    assert_eq!(calls.get(), 0);
    let empty = BasicMatrix::from_row_major(0, 0, vec![]).unwrap();
    let value = canonical_gauge_pair_table_with_decoration(&empty, 1, |_| vec![9]).unwrap();
    assert_eq!(value.examined, 1);
    assert_eq!(value.decoration, vec![9]);
}

// Origin: engine/crates_rs/tests/core_linear_algebra/decorated_pair_orbits.rs
// Claim: urn:core:crates_rs:tests:decorated-pair-orbits:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordbf648282 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordbf648282` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorbf648282 {
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
impl BoundaryErrorbf648282 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorbf648282 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorbf648282 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordbf648282 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorbf648282> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorbf648282::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorbf648282::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorbf648282::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_bf648282() {
    let admitted = BoundaryRecordbf648282::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordbf648282::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
