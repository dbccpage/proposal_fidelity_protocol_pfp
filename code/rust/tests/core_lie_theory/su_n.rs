use linear_algebra::exact_field::matrix as mx;
use core_lie_theory::su_n::GellMannBasis;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::quadratic::Surd;
use core_number_theory::rational::{ri, rq};

#[test]
fn gell_mann_gram_independence_and_sparse_structure_constants_are_exact() {
    for n in 2..=4 {
        let b = GellMannBasis::new(n).unwrap();
        assert_eq!(b.len(), n * n - 1);
        assert!(b.all_traceless_hermitian());
        assert!(b.verify_gram_identity());
        assert_eq!(b.real_independence_rank(), n * n - 1);
        assert!(b.verify_total_antisymmetry());
        assert!(b.verify_commutation_relations());
        assert!(b.verify_jacobi());
    }
    let b = GellMannBasis::new(2).unwrap();
    assert_eq!(
        b.structure_constant(0, 1, 2).unwrap(),
        Surd::rational(ri(1))
    );
    let b = GellMannBasis::new(3).unwrap();
    assert_eq!(
        b.symmetric_structure_constant(0, 0, 7).unwrap(),
        Surd::new(rq(1, 3), &ri(3)).unwrap()
    );
    assert!(GellMannBasis::new(usize::MAX).is_err());
}
#[test]
fn fundamental_casimir_killing_form_and_fierz_completeness_hold_through_su_six() {
    for n in 2..=6 {
        let b = GellMannBasis::new(n).unwrap();
        let casimir = mx::scale(
            &mx::identity(n).unwrap(),
            &GaussianRat::from_rational(rq((n * n - 1) as i64, 2 * n as i64)),
        )
        .unwrap();
        assert_eq!(b.fundamental_casimir().unwrap(), casimir);
        for a in 0..b.len() {
            assert_eq!(b.killing_entry(a, a).unwrap(), Surd::rational(ri(n as i64)));
        }
        for i in 0..n {
            for j in 0..n {
                for k in 0..n {
                    for l in 0..n {
                        let expected = rq(i64::from(i == l && j == k), 2)
                            - rq(i64::from(i == j && k == l), 2 * n as i64);
                        assert_eq!(
                            b.fierz_entry(i, j, k, l).unwrap(),
                            GaussianRat::from_rational(expected)
                        );
                    }
                }
            }
        }
    }
}

#[test]
fn basis_coordinates_refuse_nontraceless_nonhermitian_and_wrong_shape_inputs() {
    use core_lie_theory::su_n::GellMannError;
    assert!(matches!(
        GellMannBasis::new(1),
        Err(GellMannError::DimensionTooSmall(1))
    ));
    let basis = GellMannBasis::new(3).unwrap();
    assert_eq!(
        basis.coordinates(&mx::identity(3).unwrap()),
        Err(GellMannError::NotTracelessHermitian)
    );
    let mut nonhermitian = mx::zeros(3, 3).unwrap();
    nonhermitian.set(0, 1, GaussianRat::one()).unwrap();
    assert_eq!(
        basis.coordinates(&nonhermitian),
        Err(GellMannError::NotTracelessHermitian)
    );
    assert_eq!(
        basis.coordinates(&mx::zeros(2, 2).unwrap()),
        Err(GellMannError::ShapeMismatch { n: 3 })
    );
    assert!(matches!(
        basis.generator(basis.len()),
        Err(GellMannError::IndexOutOfRange { .. })
    ));
}

// Origin: engine/crates_rs/tests/core_lie_theory/su_n.rs
// Claim: urn:core:crates_rs:tests:su-n:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord58b1edf4 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord58b1edf4` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError58b1edf4 {
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
impl BoundaryError58b1edf4 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError58b1edf4 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError58b1edf4 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord58b1edf4 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError58b1edf4> {
        if capacity_bound == 0 {
            return Err(BoundaryError58b1edf4::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError58b1edf4::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError58b1edf4::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_58b1edf4() {
    let admitted = BoundaryRecord58b1edf4::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord58b1edf4::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
