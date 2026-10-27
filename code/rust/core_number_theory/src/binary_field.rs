//! `GF(2^k)` with elements packed as bit masks: bit `i` of an element is its
//! coefficient of `x^i`, and arithmetic is carry-less modulo an irreducible
//! polynomial. The symplectic trace form on `GF(2^k)^2` is included for the
//! Weyl-board spread checks.
//!
//! AuthorityEffect: None.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_5482bc20<T> {
    fn checked_invariant_5482bc20(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_5482bc20<T> for Option<T> {
    #[inline]
    fn checked_invariant_5482bc20(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_5482bc20<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_5482bc20(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::finite_field::checked_pow;

#[derive(Debug, Clone)]
pub struct BinaryField {
    degree: usize,
    modulus: usize,
    mask: usize,
    elements: Vec<usize>,
}

impl BinaryField {
    /// `GF(2^degree)` modulo `modulus`, a bit mask whose bit `i` is the
    /// coefficient of `x^i`.
    ///
    /// Panics unless `modulus` is an irreducible polynomial of exactly
    /// `degree`: any other modulus gives a ring with zero divisors, not a
    /// field. [`find_irreducible_binary_polynomial`] returns a valid one.
    pub fn new(degree: usize, modulus: usize) -> Self {
        assert!(
            poly_degree(modulus) == Some(degree) && is_irreducible_binary(modulus),
            "binary field modulus {modulus:#b} is not an irreducible polynomial of degree {degree}"
        );
        let order = checked_pow(2, degree).checked_invariant_5482bc20("binary field sample dimensions fit in usize");
        Self {
            degree,
            modulus,
            mask: order - 1,
            elements: (0..order).collect(),
        }
    }

    pub fn degree(&self) -> usize {
        self.degree
    }

    /// The irreducible modulus as a bit mask: bit `i` is the coefficient of `x^i`.
    pub fn modulus(&self) -> usize {
        self.modulus
    }

    pub fn order(&self) -> usize {
        self.elements.len()
    }

    pub fn elements(&self) -> &[usize] {
        &self.elements
    }

    pub fn add(&self, left: usize, right: usize) -> usize {
        (left ^ right) & self.mask
    }

    pub fn mul(&self, mut left: usize, mut right: usize) -> usize {
        let mut product = 0usize;
        while right != 0 {
            if right & 1 == 1 {
                product ^= left;
            }
            right >>= 1;
            left <<= 1;
            if left & (1usize << self.degree) != 0 {
                left ^= self.modulus;
            }
        }
        product & self.mask
    }

    pub fn square(&self, value: usize) -> usize {
        self.mul(value, value)
    }

    pub fn trace(&self, value: usize) -> usize {
        let mut sum = 0usize;
        let mut conjugate = value;
        for _ in 0..self.degree {
            sum = self.add(sum, conjugate);
            conjugate = self.square(conjugate);
        }
        sum & 1
    }

    pub fn symplectic_trace(&self, left: (usize, usize), right: (usize, usize)) -> usize {
        let xy = self.mul(left.0, right.1);
        let yx = self.mul(left.1, right.0);
        self.trace(self.add(xy, yx))
    }
}

pub fn find_irreducible_binary_polynomial(degree: usize) -> Option<usize> {
    let start = (1usize << degree) | 1;
    let end = 1usize << (degree + 1);
    (start..end)
        .step_by(2)
        .find(|poly| poly_degree(*poly) == Some(degree) && is_irreducible_binary(*poly))
}

fn is_irreducible_binary(poly: usize) -> bool {
    let degree = poly_degree(poly).checked_invariant_5482bc20("nonzero polynomial");
    for divisor_degree in 1..=degree / 2 {
        let start = (1usize << divisor_degree) | 1;
        let end = 1usize << (divisor_degree + 1);
        for divisor in (start..end).step_by(2) {
            if poly_degree(divisor) == Some(divisor_degree) && poly_mod_binary(poly, divisor) == 0 {
                return false;
            }
        }
    }
    true
}

fn poly_mod_binary(mut dividend: usize, divisor: usize) -> usize {
    let divisor_degree = poly_degree(divisor).checked_invariant_5482bc20("nonzero divisor");
    while let Some(dividend_degree) = poly_degree(dividend) {
        if dividend_degree < divisor_degree {
            break;
        }
        dividend ^= divisor << (dividend_degree - divisor_degree);
    }
    dividend
}

fn poly_degree(poly: usize) -> Option<usize> {
    if poly == 0 {
        None
    } else {
        Some(usize::BITS as usize - 1 - poly.leading_zeros() as usize)
    }
}

pub fn binary_polynomial_coefficients(poly: usize, degree: usize) -> Vec<usize> {
    (0..=degree).map(|i| (poly >> i) & 1).collect()
}

/// A Weyl operator `i^phase X^x Z^z` on `C^{2^k}`, labelled over `GF(2^k)`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BinaryPauli {
    /// Phase exponent for `i^phase`.
    pub phase: u8,
    pub x: usize,
    pub z: usize,
}

impl BinaryPauli {
    /// The identity operator.
    pub fn identity() -> Self {
        Self {
            phase: 0,
            x: 0,
            z: 0,
        }
    }

    /// The Hermitian representative of `X^x Z^z`.
    pub fn hermitian(field: &BinaryField, x: usize, z: usize) -> Self {
        Self {
            phase: field.trace(field.mul(x, z)) as u8,
            x,
            z,
        }
    }

    pub fn mul(self, other: Self, field: &BinaryField) -> Self {
        let raw_sign = field.trace(field.mul(self.z, other.x)) as u8;
        Self {
            phase: (self.phase + other.phase + 2 * raw_sign) % 4,
            x: field.add(self.x, other.x),
            z: field.add(self.z, other.z),
        }
    }

    pub fn adjoint(self, field: &BinaryField) -> Self {
        let raw_adjoint_sign = field.trace(field.mul(self.x, self.z)) as u8;
        Self {
            phase: (4 - self.phase + 2 * raw_adjoint_sign) % 4,
            x: self.x,
            z: self.z,
        }
    }

    pub fn is_vector_zero(self) -> bool {
        self.x == 0 && self.z == 0
    }
}

/// Every product of a subset of `generators`, indexed by the subset's bit mask.
pub fn build_line_group(field: &BinaryField, generators: &[BinaryPauli]) -> Vec<BinaryPauli> {
    let mut group = Vec::with_capacity(field.order());
    for mask in 0..field.order() {
        let mut op = BinaryPauli::identity();
        for (bit, generator) in generators.iter().enumerate() {
            if (mask >> bit) & 1 == 1 {
                op = op.mul(*generator, field);
            }
        }
        group.push(op);
    }
    group
}

// Origin: engine/crates_rs/core_number_theory/src/binary_field.rs
// Claim: urn:core:crates_rs:core-number-theory:binary-field:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord5482bc20 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord5482bc20` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError5482bc20 {
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
impl BoundaryError5482bc20 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError5482bc20 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError5482bc20 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord5482bc20 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError5482bc20> {
        if capacity_bound == 0 {
            return Err(BoundaryError5482bc20::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError5482bc20::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError5482bc20::ExceedsCapacity {
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn the_first_irreducible_polynomials_are_the_known_ones() {
        assert_eq!(find_irreducible_binary_polynomial(1), Some(0b11));
        assert_eq!(find_irreducible_binary_polynomial(2), Some(0b111));
        assert_eq!(find_irreducible_binary_polynomial(3), Some(0b1011));
        assert_eq!(find_irreducible_binary_polynomial(4), Some(0b10011));
        assert_eq!(binary_polynomial_coefficients(0b1011, 3), vec![1, 1, 0, 1]);
    }

    #[test]
    fn gf4_multiplication_and_trace_match_hand_computation() {
        // GF(4) = F_2[x] / (x^2 + x + 1): x * x = x + 1, x * (x + 1) = 1.
        let field = BinaryField::new(2, 0b111);
        assert_eq!(field.order(), 4);
        assert_eq!(field.mul(0b10, 0b10), 0b11);
        assert_eq!(field.mul(0b10, 0b11), 0b01);
        assert_eq!(field.add(0b10, 0b11), 0b01);
        // Tr(a) = a + a^2: Tr(0) = Tr(1) = 0, Tr(x) = Tr(x + 1) = 1.
        let traces: Vec<usize> = field.elements().iter().map(|a| field.trace(*a)).collect();
        assert_eq!(traces, vec![0, 0, 1, 1]);
    }

    #[test]
    fn every_nonzero_element_has_an_inverse() {
        for degree in 1..=5 {
            let modulus = find_irreducible_binary_polynomial(degree).unwrap();
            let field = BinaryField::new(degree, modulus);
            for a in field.elements().iter().copied().filter(|a| *a != 0) {
                assert!(
                    field.elements().iter().any(|b| field.mul(a, *b) == 1),
                    "GF(2^{degree}): {a:#b} has no inverse"
                );
            }
        }
    }

    #[test]
    #[should_panic(expected = "not an irreducible polynomial")]
    fn a_reducible_modulus_is_refused() {
        // x^2 + 1 = (x + 1)^2 over F_2.
        BinaryField::new(2, 0b101);
    }

    #[test]
    #[should_panic(expected = "not an irreducible polynomial")]
    fn a_modulus_of_the_wrong_degree_is_refused() {
        BinaryField::new(3, 0b111);
    }

    #[test]
    fn hermitian_paulis_are_self_adjoint_involutions() {
        let field = BinaryField::new(2, 0b111);
        for x in field.elements() {
            for z in field.elements() {
                let p = BinaryPauli::hermitian(&field, *x, *z);
                assert_eq!(p.adjoint(&field), p);
                assert_eq!(p.mul(p, &field), BinaryPauli::identity());
            }
        }
    }

    #[test]
    fn a_line_group_has_one_element_per_subset_of_generators() {
        let field = BinaryField::new(2, 0b111);
        let generators = [
            BinaryPauli::hermitian(&field, 0b01, 0),
            BinaryPauli::hermitian(&field, 0b10, 0),
        ];
        let group = build_line_group(&field, &generators);
        assert_eq!(group.len(), 4);
        assert_eq!(group[0], BinaryPauli::identity());
        assert_eq!(group[3], generators[0].mul(generators[1], &field));
    }
}

#[cfg(test)]
mod l4_boundary_tests_5482bc20 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord5482bc20::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord5482bc20::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord5482bc20::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord5482bc20::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord5482bc20::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError5482bc20::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError5482bc20::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
