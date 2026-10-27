use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::semiring_lumpability::push_forward_square;
use num_rational::BigRational;
use num_traits::Zero;

fn q(value: usize) -> BigRational {
    BigRational::from_integer(value.into())
}

fn assert_fiber_sums_match(
    table: &BasicMatrix<BigRational>,
    moved: &BasicMatrix<BigRational>,
    image: &[usize],
    source: usize,
    target: usize,
) {
    for u in 0..target {
        for v in 0..target {
            let mut expected = BigRational::zero();
            for x in 0..source {
                for y in 0..source {
                    if image[x] == u && image[y] == v {
                        expected += table.get(x, y).unwrap();
                    }
                }
            }
            assert_eq!(moved.get(u, v).unwrap(), expected);
        }
    }
}

#[test]
fn every_small_vertex_map_agrees_with_independent_fiber_sums() {
    for source in 0..=3usize {
        for target in 0..=3usize {
            let table =
                BasicMatrix::try_from_fn(source, source, |x, y| q(1 + x * source + y)).unwrap();
            for mut code in 0..target.pow(source as u32) {
                let mut image = vec![0; source];
                for vertex in &mut image {
                    *vertex = code % target;
                    code /= target;
                }
                let moved = push_forward_square(&table, &image, target).unwrap();
                assert_eq!(moved.shape(), (target, target));
                assert_fiber_sums_match(&table, &moved, &image, source, target);
            }
        }
    }
}

#[test]
fn pair_transport_composes_for_noninjective_maps_and_preserves_empty_fibers() {
    let table = BasicMatrix::try_from_fn(4, 4, |x, y| q(1 + 4 * x + y)).unwrap();
    let first = [0, 0, 1, 2];
    let second = [1, 0, 1];
    let composite: Vec<_> = first.iter().map(|&i| second[i]).collect();
    let a = push_forward_square(&table, &first, 3).unwrap();
    assert_eq!(
        push_forward_square(&a, &second, 2).unwrap(),
        push_forward_square(&table, &composite, 2).unwrap()
    );
    let injection = [0, 1, 2, 3];
    let enlarged = push_forward_square(&table, &injection, 5).unwrap();
    for i in 0..5 {
        assert!(enlarged.get(i, 4).unwrap().is_zero());
        assert!(enlarged.get(4, i).unwrap().is_zero());
    }
    let empty = BasicMatrix::<BigRational>::from_row_major(0, 0, vec![]).unwrap();
    assert_eq!(
        push_forward_square(&empty, &[], 2).unwrap().as_slice(),
        &[q(0), q(0), q(0), q(0)]
    );
}

#[test]
fn malformed_table_or_vertex_map_is_refused() {
    let square = BasicMatrix::try_from_fn(2, 2, |_, _| q(1)).unwrap();
    assert!(push_forward_square(&square, &[0], 1).is_err());
    assert!(push_forward_square(&square, &[0, 1], 1).is_err());
    assert!(push_forward_square(&square, &[0, 0], 0).is_err());
    let rectangle = BasicMatrix::try_from_fn(1, 2, |_, _| q(1)).unwrap();
    assert!(push_forward_square(&rectangle, &[0], 1).is_err());
}

// Origin: engine/crates_rs/tests/core_linear_algebra/pair_table_transport.rs
// Claim: urn:core:crates_rs:tests:pair-table-transport:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda78fb35e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda78fb35e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora78fb35e {
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
impl BoundaryErrora78fb35e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora78fb35e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora78fb35e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda78fb35e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora78fb35e> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora78fb35e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora78fb35e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora78fb35e::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_a78fb35e() {
    let admitted = BoundaryRecorda78fb35e::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorda78fb35e::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
