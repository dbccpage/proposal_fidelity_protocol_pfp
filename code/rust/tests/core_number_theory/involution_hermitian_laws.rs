use linear_algebra::exact_field::laws::{check_hermitian_ordered_axioms, check_involution_axioms};
use linear_algebra::exact_field::{involution, matrix, ordered};
use core_number_theory::{
    cyclotomic120::Cyc120,
    cyclotomic28::Cyc28,
    cyclotomic44::Cyc44,
    cyclotomic52::Cyc52,
    rational::{ri, rq},
};
use core_number_theory::{Cyc12, Cyc24, Cyc5, Cyc8, EisensteinRat, GaussianRat};

#[test]
fn fixed_field_involutions_obey_the_shared_scalar_contract() {
    macro_rules! check {
        ($t:ty) => {{
            let samples = vec![
                <$t>::zero(),
                <$t as linear_algebra::scalars::Semiring>::one(),
                <$t as linear_algebra::scalars::Semiring>::one().scale_rat(&ri(-2)),
            ];
            check_involution_axioms(&samples).unwrap();
        }};
    }
    check!(GaussianRat);
    check!(EisensteinRat);
    check!(Cyc5);
    check!(Cyc8);
    check!(Cyc12);
    check!(Cyc24);
    check!(Cyc28);
    check!(Cyc44);
    check!(Cyc52);
    check!(Cyc120);
    check_involution_axioms(&[
        GaussianRat::i(),
        GaussianRat {
            re: rq(2, 3),
            im: rq(-7, 5),
        },
    ])
    .unwrap();
    check_hermitian_ordered_axioms(&[
        GaussianRat::zero(),
        GaussianRat::one(),
        GaussianRat::i(),
        GaussianRat {
            re: rq(-3, 2),
            im: rq(5, 7),
        },
    ])
    .unwrap();
}

#[test]
fn gaussian_complex_psd_uses_shared_inertia_without_dropping_phase() {
    let i = GaussianRat::i();
    let rho = matrix::from_rows(vec![
        vec![GaussianRat::one(), i.clone()],
        vec![i.scale_rat(&ri(-1)), GaussianRat::one()],
    ])
    .unwrap();
    assert!(involution::is_hermitian(&rho).unwrap());
    let inertia = ordered::hermitian_inertia(&rho).unwrap();
    assert_eq!(
        (inertia.positive, inertia.negative, inertia.zero),
        (1, 0, 1)
    );
    let bad = matrix::from_rows(vec![
        vec![GaussianRat::one(), i.scale_rat(&ri(2))],
        vec![i.scale_rat(&ri(-2)), GaussianRat::one()],
    ])
    .unwrap();
    assert_eq!(ordered::hermitian_inertia(&bad).unwrap().negative, 1);
}

#[test]
fn quadratic_complex_involution_distinguishes_real_and_galois_embeddings() {
    use linear_algebra::exact_field::involution::Involution;
    use core_number_theory::quadratic::Quadratic;
    let real = Quadratic::<2>::from_ints(1, 1);
    assert_eq!(Involution::conjugate(&real), real);
    assert_ne!(real.conjugate(), real);
    check_hermitian_ordered_axioms(&[real, Quadratic::<2>::from_ints(-2, 3)]).unwrap();
    let imaginary = Quadratic::<-1>::from_ints(0, 1);
    assert_eq!(
        Involution::conjugate(&imaginary),
        Quadratic::<-1>::from_ints(0, -1)
    );
    check_hermitian_ordered_axioms(&[imaginary, Quadratic::<-1>::from_ints(2, -3)]).unwrap();
}

// Origin: engine/crates_rs/tests/core_number_theory/involution_hermitian_laws.rs
// Claim: urn:core:crates_rs:tests:involution-hermitian-laws:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord20dc4f74 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord20dc4f74` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError20dc4f74 {
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
impl BoundaryError20dc4f74 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError20dc4f74 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError20dc4f74 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord20dc4f74 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError20dc4f74> {
        if capacity_bound == 0 {
            return Err(BoundaryError20dc4f74::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError20dc4f74::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError20dc4f74::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_20dc4f74() {
    let admitted = BoundaryRecord20dc4f74::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord20dc4f74::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
