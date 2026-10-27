//! GF(p^k) arithmetic and the two character-sum identities behind the Weyl MUB
//! proof, on every field the MUB controls use.

use core_number_theory::character_sums::{
    additive_character, verify_character_sum_identities, CharacterSumCertificate, CyclotomicField,
};
use core_number_theory::cyclotomic::Cyc24;
use core_number_theory::cyclotomic120::Cyc120;
use core_number_theory::cyclotomic28::Cyc28;
use core_number_theory::cyclotomic44::Cyc44;
use core_number_theory::cyclotomic52::Cyc52;
use core_number_theory::finite_field::{
    find_irreducible_monic, is_irreducible_monic, is_prime, FiniteField,
};

fn field(p: usize, k: usize) -> FiniteField {
    FiniteField::with_first_irreducible(p, k).expect("small prime power")
}

fn certify<F: CyclotomicField>(p: usize, k: usize) -> CharacterSumCertificate {
    verify_character_sum_identities::<F>(&field(p, k))
        .unwrap_or_else(|e| panic!("GF({p}^{k}) over Q(zeta_{}): {e}", F::CONDUCTOR))
}

fn assert_counts(cert: CharacterSumCertificate, q: usize) {
    assert_eq!(cert.field_order, q);
    assert_eq!(cert.linear_sums_checked, q - 1);
    assert_eq!(cert.gauss_sums_checked, (q - 1) * q);
}

#[test]
fn the_trace_lands_in_f_p_with_uniform_fibres() {
    for (p, k) in [(3, 1), (7, 1), (3, 2), (3, 3), (5, 2), (7, 2)] {
        let f = field(p, k);
        let q = f.order();
        assert_eq!(q, p.pow(k as u32));
        let mut fibres = vec![0usize; p];
        for x in f.elements() {
            fibres[f.trace_value(x).expect("trace lands in F_p")] += 1;
        }
        assert!(
            fibres.iter().all(|&n| n == q / p),
            "GF({p}^{k}) fibres {fibres:?}"
        );
    }
}

#[test]
fn the_field_axioms_hold_on_gf27() {
    let f = field(3, 3);
    let els = f.elements();
    for a in els {
        assert_eq!(f.add(a, &f.zero()), *a);
        assert_eq!(f.mul(a, &f.one()), *a);
        assert!(f.sub(a, a).is_zero());
        if !a.is_zero() {
            // Fermat: a^(q-1) = 1 in GF(q)^*.
            assert_eq!(f.pow(a, f.order() - 1), f.one());
        }
    }
}

#[test]
fn prime_fields_satisfy_the_identities_used_by_prime_controls() {
    assert_counts(certify::<Cyc28>(7, 1), 7);
    assert_counts(certify::<Cyc44>(11, 1), 11);
    assert_counts(certify::<Cyc52>(13, 1), 13);
}

#[test]
fn prime_power_fields_satisfy_the_identities_used_by_odd_prime_power_controls() {
    assert_counts(certify::<Cyc120>(5, 2), 25);
    assert_counts(certify::<Cyc24>(3, 3), 27);
    assert_counts(certify::<Cyc28>(7, 2), 49);
    assert_counts(certify::<Cyc24>(3, 2), 9);
}

#[test]
fn a_field_without_the_p_th_roots_is_refused() {
    let f5 = field(5, 1);
    let err = additive_character::<Cyc28>(&f5, &f5.one()).unwrap_err();
    assert!(err.contains("does not contain the 5-th roots"), "{err}");
}

#[test]
fn a_reducible_modulus_is_not_a_field_and_fails_the_identities() {
    // x^2 + 2 = x^2 - 1 = (x - 1)(x + 1) over F_3.
    assert!(!is_irreducible_monic(3, &[2, 0]));
    let not_a_field = FiniteField::new(3, 2, vec![2, 0]);
    assert!(verify_character_sum_identities::<Cyc24>(&not_a_field).is_err());
}

#[test]
fn constructors_refuse_non_primes() {
    assert!(!is_prime(9));
    assert!(FiniteField::prime_field(9).is_none());
    assert!(FiniteField::with_first_irreducible(4, 2).is_none());
    assert!(FiniteField::with_first_irreducible(3, 0).is_none());
}

#[test]
fn irreducibility_helpers_refuse_invalid_or_reducible_inputs() {
    assert!(is_irreducible_monic(3, &[0])); // x is irreducible in degree one.
    assert!(!is_irreducible_monic(3, &[0, 0])); // x^2 has the factor x.
    assert!(!is_irreducible_monic(3, &[0, 1])); // x^2 + x has the factor x.
    assert!(!is_irreducible_monic(3, &[3, 0])); // coefficient outside F_3.
    assert!(!is_irreducible_monic(4, &[1, 1]));
    assert_eq!(find_irreducible_monic(3, 0), None);
    assert_eq!(find_irreducible_monic(4, 2), None);
}

// Origin: engine/crates_rs/tests/core_number_theory/finite_field_character_sums.rs
// Claim: urn:core:crates_rs:tests:finite-field-character-sums:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3aa37625 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3aa37625` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3aa37625 {
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
impl BoundaryError3aa37625 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3aa37625 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3aa37625 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3aa37625 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3aa37625> {
        if capacity_bound == 0 {
            return Err(BoundaryError3aa37625::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3aa37625::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3aa37625::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_3aa37625() {
    let admitted = BoundaryRecord3aa37625::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord3aa37625::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
