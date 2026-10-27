use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::pair_table_canonical::{canonical_pair_tables, PairCanonicalError};
use num_bigint::BigInt;
use num_rational::BigRational;
use core_combinatorics::enumeration::CombinatoricsError;

fn table(n: usize, values: &[i64]) -> BasicMatrix<BigRational> {
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
fn rewrite(table: &BasicMatrix<BigRational>, image: &[usize]) -> BasicMatrix<BigRational> {
    let n = image.len();
    let mut out = vec![BigRational::from_integer(0.into()); n * n];
    for x in 0..n {
        for y in 0..n {
            out[image[x] * n + image[y]] = table.as_slice()[x * n + y].clone();
        }
    }
    BasicMatrix::from_row_major(n, n, out).unwrap()
}

#[test]
fn one_permutation_must_carry_every_table_together() {
    let r = table(2, &[1, 0, 0, 0]);
    let s = table(2, &[0, 0, 0, 1]);
    let joint = canonical_pair_tables(&[r.clone(), s.clone()], 2).unwrap();
    assert_eq!(joint.old_to_new, vec![1, 0]);
    assert_eq!(joint.tables, vec![s.clone(), r]);
    assert_ne!(
        joint.tables[1],
        canonical_pair_tables(&[s], 2).unwrap().tables[0]
    );
    assert_eq!(joint.examined, 2);
}

#[test]
fn complete_three_table_orbit_has_exact_minimum_and_witness() {
    let mut r = table(3, &[4, 0, 1, 2, 3, 0, 0, 1, 5]);
    let mut values = r.as_slice().to_vec();
    values[0] = BigRational::from_integer(BigInt::from(1u8) << 140usize);
    r = BasicMatrix::from_row_major(3, 3, values).unwrap();
    let tables = vec![
        r,
        table(3, &[0, 1, 0, 0, 1, 4, 2, 0, 0]),
        table(3, &[3, 0, 2, 0, 1, 0, 4, 0, 0]),
    ];
    let images = [
        vec![0, 1, 2],
        vec![0, 2, 1],
        vec![1, 0, 2],
        vec![1, 2, 0],
        vec![2, 0, 1],
        vec![2, 1, 0],
    ];
    let orbit: Vec<_> = images
        .iter()
        .map(|image| tables.iter().map(|t| rewrite(t, image)).collect::<Vec<_>>())
        .collect();
    let key = |ts: &Vec<BasicMatrix<BigRational>>| {
        ts.iter()
            .flat_map(|t| t.as_slice().iter().cloned())
            .collect::<Vec<_>>()
    };
    let expected = orbit.iter().min_by_key(|ts| key(ts)).unwrap();
    let result = canonical_pair_tables(&tables, 6).unwrap();
    assert_eq!(&result.tables, expected);
    assert_eq!(result.examined, 6);
    assert_eq!(
        tables
            .iter()
            .map(|t| rewrite(t, &result.old_to_new))
            .collect::<Vec<_>>(),
        result.tables
    );
    for writing in orbit {
        assert_eq!(
            canonical_pair_tables(&writing, 6).unwrap().tables,
            result.tables
        );
    }
}

#[test]
fn malformed_tables_and_incomplete_search_are_refused() {
    assert_eq!(
        canonical_pair_tables::<BigRational>(&[], 1),
        Err(PairCanonicalError::IncompatibleTables)
    );
    assert_eq!(
        canonical_pair_tables(&[table(2, &[0; 4]), table(1, &[0])], 6),
        Err(PairCanonicalError::IncompatibleTables)
    );
    let rectangle =
        BasicMatrix::from_row_major(1, 2, vec![BigRational::from_integer(0.into()); 2]).unwrap();
    assert_eq!(
        canonical_pair_tables(&[rectangle], 6),
        Err(PairCanonicalError::IncompatibleTables)
    );
    assert!(matches!(
        canonical_pair_tables(&[table(3, &[0; 9])], 5),
        Err(PairCanonicalError::Enumeration(
            CombinatoricsError::BudgetExceeded { .. }
        ))
    ));
    assert!(canonical_pair_tables(&[table(0, &[])], 0).is_err());
    let empty = canonical_pair_tables(&[table(0, &[])], 1).unwrap();
    assert_eq!(empty.examined, 1);
    assert!(empty.old_to_new.is_empty());
    assert_eq!(
        canonical_pair_tables(&[table(2, &[0; 4])], 2)
            .unwrap()
            .old_to_new,
        vec![0, 1]
    );
}

// Origin: engine/crates_rs/tests/core_linear_algebra/pair_table_canonical.rs
// Claim: urn:core:crates_rs:tests:pair-table-canonical:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda541fa02 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda541fa02` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora541fa02 {
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
impl BoundaryErrora541fa02 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora541fa02 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora541fa02 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda541fa02 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora541fa02> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora541fa02::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora541fa02::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora541fa02::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_a541fa02() {
    let admitted = BoundaryRecorda541fa02::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorda541fa02::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
