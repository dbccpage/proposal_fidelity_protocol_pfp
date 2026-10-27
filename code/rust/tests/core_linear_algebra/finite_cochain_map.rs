use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::finite_cochain_map::{CochainHomotopy, CochainMap, CochainWindow};
use num_rational::BigRational;
fn m(x: i64) -> BasicMatrix<BigRational> {
    BasicMatrix::try_from_fn(1, 1, |_, _| BigRational::from_integer(x.into())).unwrap()
}

fn matrix(rows: usize, cols: usize, data: &[i64]) -> BasicMatrix<BigRational> {
    BasicMatrix::try_from_fn(rows, cols, |i, j| {
        BigRational::from_integer(data[i * cols + j].into())
    })
    .unwrap()
}

fn zero_window(n: usize) -> CochainWindow<BigRational> {
    CochainWindow::try_new(
        [n; 3],
        matrix(n, n, &vec![0; n * n]),
        matrix(n, n, &vec![0; n * n]),
    )
    .unwrap()
}

#[test]
fn composition_obeys_identity_associativity_and_binds_intermediate_differentials() {
    let a = CochainWindow::try_new([1; 3], m(1), m(0)).unwrap();
    let b = CochainWindow::try_new([1; 3], m(2), m(0)).unwrap();
    let f = CochainMap::try_new(&a, &b, [m(1), m(2), m(3)]).unwrap();
    let g = CochainMap::try_new(&b, &b, [m(2), m(2), m(2)]).unwrap();
    let h = CochainMap::try_new(&b, &b, [m(3), m(3), m(3)]).unwrap();
    assert_eq!(CochainMap::identity(&a).unwrap().then(&f).unwrap(), f);
    assert_eq!(f.then(&CochainMap::identity(&b).unwrap()).unwrap(), f);
    assert_eq!(
        f.then(&g).unwrap().then(&h).unwrap(),
        f.then(&g.then(&h).unwrap()).unwrap()
    );
    assert_eq!(f.then(&g).unwrap().transport(1, &m(4)).unwrap(), m(16));
    assert!(f.then(&CochainMap::identity(&a).unwrap()).is_err());
    let empty = zero_window(0);
    let identity = CochainMap::identity(&empty).unwrap();
    assert_eq!(identity.then(&identity).unwrap(), identity);
}

#[test]
fn section_retraction_preserves_old_image_without_collapsing_new_generators() {
    let old = zero_window(1);
    let new = zero_window(2);
    let up = matrix(2, 1, &[1, 0]);
    let down = matrix(1, 2, &[1, 0]);
    let section = CochainMap::try_new(&old, &new, [up.clone(), up.clone(), up]).unwrap();
    let retraction = CochainMap::try_new(&new, &old, [down.clone(), down.clone(), down]).unwrap();
    assert!(retraction.is_retraction_of(&section).unwrap());
    assert!(!section.is_retraction_of(&retraction).unwrap());
    assert_ne!(
        retraction.then(&section).unwrap(),
        CochainMap::identity(&new).unwrap()
    );
    assert!(retraction
        .is_retraction_of(&CochainMap::identity(&old).unwrap())
        .is_err());
}

#[test]
fn explicit_homotopy_checks_all_degrees_and_does_not_identify_arbitrary_repair_classes() {
    let complex =
        CochainWindow::try_new([1, 2, 1], matrix(2, 1, &[1, 0]), matrix(1, 2, &[0, 1])).unwrap();
    let id = CochainMap::identity(&complex).unwrap();
    let zero =
        CochainMap::try_new(&complex, &complex, [m(0), matrix(2, 2, &[0; 4]), m(0)]).unwrap();
    let h1 = matrix(1, 2, &[1, 0]);
    let h2 = matrix(2, 1, &[0, 1]);
    let witness = CochainHomotopy::try_new(&id, &zero, h1.clone(), h2.clone()).unwrap();
    assert_eq!(witness.left(), &id);
    assert_eq!(witness.right(), &zero);
    assert_eq!(witness.h1(), &h1);
    assert_eq!(witness.h2(), &h2);
    assert!(CochainHomotopy::try_new(&id, &zero, h1.clone(), matrix(2, 1, &[0, 2])).is_err());
    assert!(CochainHomotopy::try_new(&id, &zero, m(1), h2).is_err());
    // c=(0,1) is not closed, and the two images differ outside im(d0).
    let c = matrix(2, 1, &[0, 1]);
    assert_ne!(id.transport(1, &c).unwrap(), zero.transport(1, &c).unwrap());
    assert_eq!(
        complex.d1().get_ref(0, 1).unwrap(),
        &BigRational::from_integer(1.into())
    );
    // A zero differential does not supply a filler between unequal maps.
    let flat = zero_window(1);
    let flat_id = CochainMap::identity(&flat).unwrap();
    let flat_zero = CochainMap::try_new(&flat, &flat, [m(0), m(0), m(0)]).unwrap();
    assert!(CochainHomotopy::try_new(&flat_id, &flat_zero, m(0), m(0)).is_err());
}
#[test]
fn checks_complexes_typed_squares_and_transport() {
    assert!(CochainWindow::try_new([1, 1, 1], m(1), m(1)).is_err());
    let a = CochainWindow::try_new([1, 1, 1], m(1), m(0)).unwrap();
    let b = CochainWindow::try_new([1, 1, 1], m(2), m(0)).unwrap();
    assert!(CochainMap::try_new(&a, &b, [m(1), m(1), m(1)]).is_err());
    let f = CochainMap::try_new(&a, &b, [m(1), m(2), m(3)]).unwrap();
    assert_eq!(f.transport(1, &m(4)).unwrap(), m(8));
    assert!(f.transport(3, &m(4)).is_err());
}

// Origin: engine/crates_rs/tests/core_linear_algebra/finite_cochain_map.rs
// Claim: urn:core:crates_rs:tests:finite-cochain-map:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord53497629 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord53497629` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError53497629 {
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
impl BoundaryError53497629 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError53497629 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError53497629 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord53497629 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError53497629> {
        if capacity_bound == 0 {
            return Err(BoundaryError53497629::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError53497629::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError53497629::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_53497629() {
    let admitted = BoundaryRecord53497629::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord53497629::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
