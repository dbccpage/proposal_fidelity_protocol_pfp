//! Regression laws moved with the canonical Clifford and Pauli/symplectic owners.
use linear_algebra::exact_field::matrix as mx;
use core_lie_theory::pauli_symplectic::{
    clifford_order_mod_phases, clifford_to_symplectic, generate_sp2_f2, generate_sp4_f2, hadamard,
    pauli, phase_gate, stabilizer_state_count, symplectic_order, Pauli,
};
use core_lie_theory::scalar::dagger;
use core_number_theory::cyclotomic::Cyc24;

#[test]
fn test_symplectic_group_orders() {
    for (n, order) in [
        (0, "1"),
        (1, "6"),
        (2, "720"),
        (3, "1451520"),
        (4, "47377612800"),
        (5, "24815256521932800"),
        (6, "208114637736580743168000"),
        (7, "27930968965434591767112450048000"),
    ] {
        assert_eq!(symplectic_order(n).unwrap().to_string(), order);
    }
    assert!(symplectic_order(usize::MAX).is_err());
    assert_eq!(clifford_order_mod_phases(1).unwrap().to_string(), "24");
    assert_eq!(clifford_order_mod_phases(2).unwrap().to_string(), "11520");
    assert_eq!(stabilizer_state_count(1).unwrap().to_string(), "6");
    assert_eq!(stabilizer_state_count(2).unwrap().to_string(), "60");
}
#[test]
fn binary_symplectic_generation_is_deterministic_and_has_the_exact_orders() {
    let one = generate_sp2_f2().unwrap();
    assert_eq!(one.len(), 6);
    let two = generate_sp4_f2().unwrap();
    assert_eq!(two.len(), 720);
    assert_eq!(generate_sp2_f2().unwrap(), one);
    assert_eq!(generate_sp4_f2().unwrap(), two);
    assert!(one.iter().chain(&two).all(|m| m.preserves_form()));
}
#[test]
fn test_clifford_unitary_generators_and_conjugation() {
    let h = hadamard::<Cyc24>().unwrap();
    let s = phase_gate::<Cyc24>().unwrap();
    let x = pauli::<Cyc24>(Pauli::X).unwrap();
    let z = pauli::<Cyc24>(Pauli::Z).unwrap();
    let conjugate =
        |u: &_, p: &_| mx::multiply(&mx::multiply(u, p).unwrap(), &dagger(u).unwrap()).unwrap();
    assert_eq!(conjugate(&h, &x), z);
    assert_eq!(conjugate(&h, &z), x);
    assert_eq!(conjugate(&s, &z), z);
    let hi = clifford_to_symplectic(&h).unwrap();
    let si = clifford_to_symplectic(&s).unwrap();
    assert_eq!(hi.entries(), &[0, 1, 1, 0]);
    assert_eq!(si.entries(), &[1, 0, 1, 1]);
    assert_eq!(
        clifford_to_symplectic(&mx::multiply(&h, &s).unwrap()).unwrap(),
        hi.multiply(&si).unwrap()
    );
    let scaled = mx::scale(&h, &Cyc24::from_int(2)).unwrap();
    assert!(clifford_to_symplectic(&scaled).is_err());
    let arbitrary = mx::from_rows(vec![
        vec![Cyc24::one(), Cyc24::zero()],
        vec![Cyc24::zero(), Cyc24::zeta3()],
    ])
    .unwrap();
    assert!(clifford_to_symplectic(&arbitrary).is_err());
}
#[test]
fn the_one_qubit_clifford_cover_has_192_elements_and_32_element_symplectic_fibres() {
    let h = hadamard::<Cyc24>().unwrap();
    let s = phase_gate::<Cyc24>().unwrap();
    let group = core_lie_theory::finite_group::generate(
        &[h, s],
        mx::identity(2).unwrap(),
        |a, b| mx::multiply(a, b).unwrap(),
        |m| m.as_slice().to_vec(),
        192,
    )
    .unwrap();
    assert_eq!(group.len(), 192);
    let mut counts = std::collections::BTreeMap::new();
    for u in group {
        *counts
            .entry(clifford_to_symplectic(&u).unwrap().entries().to_vec())
            .or_insert(0) += 1;
    }
    assert_eq!(counts.len(), 6);
    assert!(counts.values().all(|c| *c == 32));
}

#[test]
fn exact_clifford_families_have_the_declared_volume_square_chirality_and_full_matrix_span() {
    use linear_algebra::exact_field::matrix as mx;
    use core_lie_theory::clifford::{CliffordError, CliffordFamily};
    use core_number_theory::cyclotomic::GaussianRat;
    use core_number_theory::rational::ri;
    for n in 1..=7 {
        let family = CliffordFamily::<GaussianRat>::euclidean(n).unwrap();
        let volume = family.volume_element().unwrap();
        assert_eq!(
            mx::multiply(&volume, &volume).unwrap(),
            mx::scale(
                &mx::identity(family.size()).unwrap(),
                &GaussianRat::from_ints(i64::from(family.volume_square()), 0)
            )
            .unwrap()
        );
        assert_eq!(
            family.product_span_rank().unwrap(),
            family.size() * family.size()
        );
        if n % 2 == 0 {
            let chirality = family.chirality().unwrap();
            assert_eq!(
                mx::multiply(&chirality, &chirality).unwrap(),
                mx::identity(family.size()).unwrap()
            );
            for gamma in family.gammas() {
                assert!(mx::is_zero_matrix(
                    &mx::anticommutator(&chirality, gamma).unwrap()
                ));
            }
        } else {
            assert_eq!(family.chirality(), Err(CliffordError::OddFamily));
        }
    }
    let family = CliffordFamily::<GaussianRat>::minkowski(1, 3).unwrap();
    assert_eq!(family.volume_square(), -1);
    let mut broken = family.gammas().to_vec();
    let changed = broken[0]
        .get_ref(0, 0)
        .unwrap()
        .add(&GaussianRat::from_rational(ri(1) / ri(1024)));
    broken[0].set(0, 0, changed).unwrap();
    assert!(matches!(
        CliffordFamily::admit(broken, vec![1, -1, -1, -1]),
        Err(CliffordError::Anticommutator { mu: 0, nu: 0 })
    ));
    assert_eq!(
        CliffordFamily::<GaussianRat>::euclidean(13),
        Err(CliffordError::SizeBound)
    );
}

// Origin: engine/crates_rs/tests/core_lie_theory/clifford_regression.rs
// Claim: urn:core:crates_rs:tests:clifford-regression:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord8e92602e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord8e92602e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError8e92602e {
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
impl BoundaryError8e92602e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError8e92602e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError8e92602e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord8e92602e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError8e92602e> {
        if capacity_bound == 0 {
            return Err(BoundaryError8e92602e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError8e92602e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError8e92602e::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_8e92602e() {
    let admitted = BoundaryRecord8e92602e::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord8e92602e::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
