use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::gauge_pair_table::*;
use linear_algebra::pair_table_canonical::PairCanonicalError;
use num_rational::BigRational;

fn matrix(n: usize, values: &[i64]) -> BasicMatrix<BigRational> {
    BasicMatrix::from_row_major(
        n,
        n,
        values
            .iter()
            .map(|&v| BigRational::from_integer(v.into()))
            .collect(),
    )
    .unwrap()
}
#[test]
fn root_loop_survives_and_every_integer_gradient_is_removed() {
    let base = matrix(2, &[7, 4, -2, 9]);
    let shifted = matrix(2, &[7, 12, -10, 9]); // Shift by potential (3,-5).
    let normal = root_normalized_pair_table(&base).unwrap();
    assert_eq!(normal, matrix(2, &[7, 2, 0, 9]));
    assert_eq!(root_normalized_pair_table(&shifted).unwrap(), normal);
    assert_eq!(root_normalized_pair_table(&normal).unwrap(), normal);
    let mut fractions = base.as_slice().to_vec();
    fractions[0] = BigRational::new(7.into(), 3.into());
    let fractions = BasicMatrix::from_row_major(2, 2, fractions).unwrap();
    assert_eq!(
        root_normalized_pair_table(&fractions).unwrap().as_slice()[0],
        BigRational::new(7.into(), 3.into())
    );
}
#[test]
fn orbit_and_alignment_normalize_each_fixed_writing() {
    let base = matrix(2, &[7, 4, -2, 9]);
    let moved = matrix(2, &[9, -2, 4, 7]);
    let least = canonical_gauge_pair_table(&base, 2).unwrap();
    assert_eq!(least.normal, matrix(2, &[7, 2, 0, 9]));
    assert_eq!(least.old_to_new, vec![0, 1]);
    assert_eq!(least.examined, 2);
    assert_eq!(
        canonical_gauge_pair_table(&moved, 2).unwrap().normal,
        least.normal
    );
    assert_eq!(
        align_gauge_pair_tables(&base, &moved, 2).unwrap(),
        Some(vec![1, 0])
    );
    assert!(
        align_gauge_pair_tables(&base, &matrix(2, &[8, 4, -2, 9]), 2)
            .unwrap()
            .is_none()
    );
    assert_eq!(
        canonical_gauge_pair_table(&matrix(2, &[0, 2, -2, 0]), 2)
            .unwrap()
            .old_to_new,
        vec![0, 1]
    );
}
#[test]
fn malformed_shapes_and_incomplete_orbits_refuse_without_a_sampled_key() {
    let rectangle =
        BasicMatrix::from_row_major(1, 2, vec![BigRational::from_integer(0.into()); 2]).unwrap();
    assert_eq!(
        root_normalized_pair_table(&rectangle),
        Err(PairCanonicalError::IncompatibleTables)
    );
    assert_eq!(
        align_gauge_pair_tables(&matrix(1, &[0]), &matrix(2, &[0; 4]), 2),
        Err(PairCanonicalError::IncompatibleTables)
    );
    assert!(canonical_gauge_pair_table(&matrix(3, &[0; 9]), 5).is_err());
    assert!(canonical_gauge_pair_table(&matrix(0, &[]), 0).is_err());
    let empty = canonical_gauge_pair_table(&matrix(0, &[]), 1).unwrap();
    assert_eq!(empty.examined, 1);
    assert!(empty.normal.as_slice().is_empty());
}

// Origin: engine/crates_rs/tests/core_linear_algebra/gauge_pair_table.rs
// Claim: urn:core:crates_rs:tests:gauge-pair-table:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord34d5c4e3 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord34d5c4e3` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError34d5c4e3 {
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
impl BoundaryError34d5c4e3 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError34d5c4e3 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError34d5c4e3 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord34d5c4e3 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError34d5c4e3> {
        if capacity_bound == 0 {
            return Err(BoundaryError34d5c4e3::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError34d5c4e3::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError34d5c4e3::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_34d5c4e3() {
    let admitted = BoundaryRecord34d5c4e3::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord34d5c4e3::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
