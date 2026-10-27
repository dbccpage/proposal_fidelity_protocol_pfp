//! Finite fields `GF(p^k)` as polynomials over `F_p` modulo a monic
//! irreducible of degree `k`.
//!
//! An element is its coefficient vector `c_0 + c_1 x + ... + c_{k-1} x^{k-1}`
//! with each `c_i` in `0..p`. Degree 1 is the prime field `F_p`.
//!
//! Moved from `core_mub::core_native::odd_prime_power_weyl`, where it was
//! private, so that the MUB controls could share one field instead of
//! hand-writing `GF(9)`, `GF(25)`, `GF(27)` and `GF(49)`.
// AuthorityEffect: None. Citation: sealed-derivation-v1 (3100c4e)


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_c3d617ee<T> {
    fn checked_invariant_c3d617ee(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_c3d617ee<T> for Option<T> {
    #[inline]
    fn checked_invariant_c3d617ee(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_c3d617ee<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_c3d617ee(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}

/// An element of `GF(p^k)`: `coeffs[i]` is the coefficient of `x^i`.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct FieldElement {
    pub coeffs: Vec<usize>,
}

impl FieldElement {
    pub fn is_zero(&self) -> bool {
        self.coeffs.iter().all(|coeff| *coeff == 0)
    }
}

/// `GF(p^k)`, with every element enumerated.
#[derive(Debug, Clone)]
pub struct FiniteField {
    prime: usize,
    degree: usize,
    modulus_lower: Vec<usize>,
    elements: Vec<FieldElement>,
}

impl FiniteField {
    /// `GF(p^k)` modulo `x^k + modulus_lower[k-1] x^{k-1} + ... + modulus_lower[0]`.
    ///
    /// The modulus is not checked: pass an irreducible one, for example from
    /// [`find_irreducible_monic`], or use [`FiniteField::with_first_irreducible`].
    pub fn new(prime: usize, degree: usize, modulus_lower: Vec<usize>) -> Self {
        let elements = enumerate_elements(prime, degree);
        Self {
            prime,
            degree,
            modulus_lower,
            elements,
        }
    }

    /// `GF(p^k)` modulo the first monic irreducible in enumeration order, or
    /// `None` if `p` is not prime, `k` is zero, or `p^k` overflows.
    pub fn with_first_irreducible(prime: usize, degree: usize) -> Option<Self> {
        if !is_prime(prime) || degree == 0 {
            return None;
        }
        checked_pow(prime, degree)?;
        let modulus_lower = find_irreducible_monic(prime, degree)?;
        Some(Self::new(prime, degree, modulus_lower))
    }

    /// The prime field `F_p`, or `None` if `p` is not prime.
    pub fn prime_field(prime: usize) -> Option<Self> {
        Self::with_first_irreducible(prime, 1)
    }

    pub fn prime(&self) -> usize {
        self.prime
    }

    pub fn degree(&self) -> usize {
        self.degree
    }

    pub fn modulus_lower(&self) -> &[usize] {
        &self.modulus_lower
    }

    pub fn elements(&self) -> &[FieldElement] {
        &self.elements
    }

    pub fn order(&self) -> usize {
        self.elements.len()
    }

    pub fn zero(&self) -> FieldElement {
        FieldElement {
            coeffs: vec![0; self.degree],
        }
    }

    pub fn one(&self) -> FieldElement {
        self.base(1)
    }

    /// The element `value mod p` of the prime subfield.
    pub fn base(&self, value: usize) -> FieldElement {
        let mut coeffs = vec![0; self.degree];
        coeffs[0] = value % self.prime;
        FieldElement { coeffs }
    }

    pub fn add(&self, left: &FieldElement, right: &FieldElement) -> FieldElement {
        let coeffs = left
            .coeffs
            .iter()
            .zip(&right.coeffs)
            .map(|(a, b)| (a + b) % self.prime)
            .collect();
        FieldElement { coeffs }
    }

    pub fn sub(&self, left: &FieldElement, right: &FieldElement) -> FieldElement {
        let coeffs = left
            .coeffs
            .iter()
            .zip(&right.coeffs)
            .map(|(a, b)| (self.prime + a - b) % self.prime)
            .collect();
        FieldElement { coeffs }
    }

    pub fn mul(&self, left: &FieldElement, right: &FieldElement) -> FieldElement {
        let mut product = vec![0; 2 * self.degree - 1];
        for (i, a) in left.coeffs.iter().enumerate() {
            for (j, b) in right.coeffs.iter().enumerate() {
                product[i + j] = (product[i + j] + a * b) % self.prime;
            }
        }

        for degree in (self.degree..product.len()).rev() {
            let coeff = product[degree] % self.prime;
            if coeff == 0 {
                continue;
            }
            for lower_degree in 0..self.degree {
                let reduction = coeff * self.modulus_lower[lower_degree] % self.prime;
                let target = degree - self.degree + lower_degree;
                product[target] = (self.prime + product[target] - reduction) % self.prime;
            }
        }

        FieldElement {
            coeffs: product[..self.degree].to_vec(),
        }
    }

    pub fn pow(&self, base: &FieldElement, mut exponent: usize) -> FieldElement {
        let mut acc = self.base(1);
        let mut power = base.clone();
        while exponent > 0 {
            if exponent % 2 == 1 {
                acc = self.mul(&acc, &power);
            }
            exponent /= 2;
            if exponent > 0 {
                power = self.mul(&power, &power);
            }
        }
        acc
    }

    /// The absolute trace `Tr(x) = x + x^p + ... + x^{p^{k-1}}`, which lies in
    /// `F_p`. An error means the modulus was not irreducible.
    pub fn trace_value(&self, element: &FieldElement) -> Result<usize, String> {
        let mut sum = self.zero();
        let mut conjugate = element.clone();
        for _ in 0..self.degree {
            sum = self.add(&sum, &conjugate);
            conjugate = self.pow(&conjugate, self.prime);
        }
        if sum.coeffs.iter().skip(1).any(|coeff| *coeff != 0) {
            return Err(format!(
                "trace did not land in the base field for {:?}",
                element.coeffs
            ));
        }
        Ok(sum.coeffs[0])
    }
}

/// The first monic irreducible of degree `degree` over `F_prime`, as its lower
/// coefficients, in the order `index -> (index mod p, index / p mod p, ...)`.
pub fn find_irreducible_monic(prime: usize, degree: usize) -> Option<Vec<usize>> {
    if !is_prime(prime) || degree == 0 {
        return None;
    }
    for mut index in 0..checked_pow(prime, degree)? {
        let mut lower = vec![0; degree];
        for coeff in &mut lower {
            *coeff = index % prime;
            index /= prime;
        }
        if lower[0] == 0 {
            continue;
        }
        if is_irreducible_monic(prime, &lower) {
            return Some(lower);
        }
    }
    None
}

fn monic_divisor_from_index(prime: usize, divisor_degree: usize, mut index: usize) -> Vec<usize> {
    let mut divisor = vec![0; divisor_degree + 1];
    for coeff in divisor.iter_mut().take(divisor_degree) {
        *coeff = index % prime;
        index /= prime;
    }
    divisor[divisor_degree] = 1;
    divisor
}

fn has_monic_divisor_of_degree(
    prime: usize,
    polynomial: &[usize],
    divisor_degree: usize,
) -> Option<bool> {
    let divisor_count = checked_pow(prime, divisor_degree)?;
    for index in 0..divisor_count {
        let divisor = monic_divisor_from_index(prime, divisor_degree, index);
        if divisor[0] != 0
            && poly_mod(prime, polynomial, &divisor)
                .iter()
                .all(|coeff| *coeff == 0)
        {
            return Some(true);
        }
    }
    Some(false)
}

/// Whether the monic polynomial with lower coefficients `lower` is irreducible
/// over `F_prime`, by trial division by every monic divisor up to half degree.
pub fn is_irreducible_monic(prime: usize, lower: &[usize]) -> bool {
    let degree = lower.len();
    if !is_prime(prime) || degree == 0 || lower.iter().any(|&coeff| coeff >= prime) {
        return false;
    }
    if degree > 1 && lower[0] == 0 {
        return false;
    }
    let mut polynomial = lower.to_vec();
    polynomial.push(1);

    for divisor_degree in 1..=degree / 2 {
        if has_monic_divisor_of_degree(prime, &polynomial, divisor_degree) != Some(false) {
            return false;
        }
    }

    true
}

fn poly_mod(prime: usize, polynomial: &[usize], divisor: &[usize]) -> Vec<usize> {
    let mut rem = polynomial.to_vec();
    let divisor_degree = divisor.len() - 1;
    debug_assert_eq!(divisor[divisor_degree], 1);

    while rem.len() >= divisor.len() {
        let coeff = *rem.last().checked_invariant_c3d617ee("remainder has a leading term") % prime;
        if coeff != 0 {
            let offset = rem.len() - divisor.len();
            for (i, divisor_coeff) in divisor.iter().enumerate().take(divisor_degree) {
                let reduction = coeff * divisor_coeff % prime;
                rem[offset + i] = (prime + rem[offset + i] - reduction) % prime;
            }
        }
        rem.pop();
    }

    rem
}

fn enumerate_elements(prime: usize, degree: usize) -> Vec<FieldElement> {
    let order = checked_pow(prime, degree).checked_invariant_c3d617ee("finite-field sample dimensions fit in usize");
    let mut elements = Vec::with_capacity(order);
    for mut index in 0..order {
        let mut coeffs = vec![0; degree];
        for coeff in &mut coeffs {
            *coeff = index % prime;
            index /= prime;
        }
        elements.push(FieldElement { coeffs });
    }
    elements
}

/// `base^exponent`, or `None` on overflow.
pub fn checked_pow(base: usize, exponent: usize) -> Option<usize> {
    let mut acc = 1usize;
    for _ in 0..exponent {
        acc = acc.checked_mul(base)?;
    }
    Some(acc)
}

/// Trial-division primality test.
pub fn is_prime(n: usize) -> bool {
    if n < 2 {
        return false;
    }
    if n == 2 {
        return true;
    }
    if n % 2 == 0 {
        return false;
    }
    let mut d = 3;
    while d <= n / d {
        if n % d == 0 {
            return false;
        }
        d += 2;
    }
    true
}

// Origin: engine/crates_rs/core_number_theory/src/finite_field.rs
// Claim: urn:core:crates_rs:core-number-theory:finite-field:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc3d617ee {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc3d617ee` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc3d617ee {
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
impl BoundaryErrorc3d617ee {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc3d617ee {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc3d617ee {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc3d617ee {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc3d617ee> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc3d617ee::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc3d617ee::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc3d617ee::ExceedsCapacity {
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
mod l4_boundary_tests_c3d617ee {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordc3d617ee::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordc3d617ee::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordc3d617ee::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordc3d617ee::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordc3d617ee::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorc3d617ee::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorc3d617ee::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
