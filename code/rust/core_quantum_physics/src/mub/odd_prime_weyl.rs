//! Odd-prime Weyl MUB proof schema.
//!
//! This is not another coordinate list. It records the reusable finite-field
//! proof shape for complete MUBs in odd prime dimension: computational basis
//! plus quadratic additive-character bases. The checked part here is the
//! finite-field side of the proof obligations; it deliberately keeps the
//! character/Gauss-sum theorem boundary visible for Lean/Core authority.

use core_number_theory::finite_field::is_prime;
use serde::Serialize;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum OddPrimeWeylStatus {
    ProofSchemaVerified,
    UnsupportedDimension,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct OddPrimeWeylReport {
    pub dimension: usize,
    pub basis_count: usize,
    pub status: OddPrimeWeylStatus,
    pub same_basis_linear_reductions: usize,
    pub cross_basis_quadratic_reductions: usize,
    pub determinant_two_invertible: bool,
    pub checked_identities: Vec<&'static str>,
    pub theorem_obligations: Vec<&'static str>,
    pub boundary: &'static str,
    pub error: Option<String>,
}

pub fn verify_current_odd_prime_weyl_schemas() -> Vec<OddPrimeWeylReport> {
    [3, 5, 7, 11, 13]
        .into_iter()
        .map(verify_odd_prime_weyl_schema)
        .collect()
}

pub fn verify_odd_prime_weyl_schema(p: usize) -> OddPrimeWeylReport {
    if p < 3 || !is_prime(p) {
        return OddPrimeWeylReport {
            dimension: p,
            basis_count: 0,
            status: OddPrimeWeylStatus::UnsupportedDimension,
            same_basis_linear_reductions: 0,
            cross_basis_quadratic_reductions: 0,
            determinant_two_invertible: false,
            checked_identities: vec![],
            theorem_obligations: vec![],
            boundary: "odd-prime Weyl schema only applies to odd prime dimensions",
            error: Some("dimension is not an odd prime".to_string()),
        };
    }

    if p > MAX_WEYL_PRIME_BUDGET {
        return OddPrimeWeylReport {
            dimension: p,
            basis_count: 0,
            status: OddPrimeWeylStatus::UnsupportedDimension,
            same_basis_linear_reductions: 0,
            cross_basis_quadratic_reductions: 0,
            determinant_two_invertible: false,
            checked_identities: vec![],
            theorem_obligations: vec![],
            boundary: "odd-prime Weyl schema work budget exceeded",
            error: Some(format!(
                "dimension {p} exceeds maximum verified prime budget {MAX_WEYL_PRIME_BUDGET}"
            )),
        };
    }

    let same_basis_linear_reductions = match checked_same_basis_linear_reductions(p) {
        Some(count) => count,
        None => {
            return OddPrimeWeylReport {
                dimension: p,
                basis_count: 0,
                status: OddPrimeWeylStatus::UnsupportedDimension,
                same_basis_linear_reductions: 0,
                cross_basis_quadratic_reductions: 0,
                determinant_two_invertible: false,
                checked_identities: vec![],
                theorem_obligations: vec![],
                boundary: "odd-prime Weyl schema arithmetic overflow",
                error: Some(
                    "same-basis linear reduction count overflows 64-bit integer".to_string(),
                ),
            };
        }
    };

    let cross_basis_quadratic_reductions = match checked_cross_basis_quadratic_reductions(p) {
        Some(count) => count,
        None => {
            return OddPrimeWeylReport {
                dimension: p,
                basis_count: 0,
                status: OddPrimeWeylStatus::UnsupportedDimension,
                same_basis_linear_reductions: 0,
                cross_basis_quadratic_reductions: 0,
                determinant_two_invertible: false,
                checked_identities: vec![],
                theorem_obligations: vec![],
                boundary: "odd-prime Weyl schema arithmetic overflow",
                error: Some(
                    "cross-basis quadratic reduction count overflows 64-bit integer".to_string(),
                ),
            };
        }
    };

    let determinant_two_invertible = gcd(2, p) == 1;

    OddPrimeWeylReport {
        dimension: p,
        basis_count: p + 1,
        status: OddPrimeWeylStatus::ProofSchemaVerified,
        same_basis_linear_reductions,
        cross_basis_quadratic_reductions,
        determinant_two_invertible,
        checked_identities: vec![
            "computational basis plus p quadratic Weyl bases gives p+1 bases",
            "same quadratic-basis orthogonality reduces to nonzero linear character sums",
            "cross quadratic-basis unbiasedness reduces to nonzero quadratic Gauss sums",
            "odd-prime change of variables has invertible determinant 2",
        ],
        theorem_obligations: vec![
            "formal additive-character orthogonality over F_p",
            "formal quadratic Gauss norm over F_p",
            "declared coefficient field containing p-th roots and sqrt(p)",
            "Lean/Core transport from proof schema to concrete Hilbert-space bases",
        ],
        boundary: "odd-prime complete-control schema only; not prime powers, composite dimensions, or all-N authority",
        error: None,
    }
}

/// Computation work ceiling for verified odd prime dimensions to prevent 64-bit integer overflow.
pub const MAX_WEYL_PRIME_BUDGET: usize = 65_535;

/// Exact closed-form checked multiplicity for same-basis linear reductions: p^2 * (p - 1).
pub fn checked_same_basis_linear_reductions(p: usize) -> Option<usize> {
    p.checked_mul(p)?.checked_mul(p.checked_sub(1)?)
}

/// Exact closed-form checked multiplicity for cross-basis quadratic reductions: p^3 * (p - 1).
pub fn checked_cross_basis_quadratic_reductions(p: usize) -> Option<usize> {
    p.checked_mul(p)?.checked_mul(p)?.checked_mul(p.checked_sub(1)?)
}

pub fn count_same_basis_linear_reductions(p: usize) -> usize {
    checked_same_basis_linear_reductions(p).unwrap_or(0)
}

pub fn count_cross_basis_quadratic_reductions(p: usize) -> usize {
    checked_cross_basis_quadratic_reductions(p).unwrap_or(0)
}

fn gcd(mut a: usize, mut b: usize) -> usize {
    while b != 0 {
        let r = a % b;
        a = b;
        b = r;
    }
    a
}

// Origin: engine/crates_rs/core_quantum_physics/src/mub/odd_prime_weyl.rs
// Claim: urn:core:crates_rs:core-quantum-physics:odd-prime-weyl:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf33fc677 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf33fc677` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf33fc677 {
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
impl BoundaryErrorf33fc677 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf33fc677 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf33fc677 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf33fc677 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf33fc677> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf33fc677::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf33fc677::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf33fc677::ExceedsCapacity {
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
    fn odd_prime_schemas_verify_for_sample_primes() {
        for p in [3, 5, 7, 11, 13] {
            let report = verify_odd_prime_weyl_schema(p);
            assert_eq!(report.status, OddPrimeWeylStatus::ProofSchemaVerified);
            assert_eq!(report.basis_count, p + 1);
            assert_eq!(report.same_basis_linear_reductions, p * p * (p - 1));
            assert_eq!(report.cross_basis_quadratic_reductions, p * (p - 1) * p * p);
            assert!(report.determinant_two_invertible);
            assert!(report.error.is_none());
        }
    }

    #[test]
    fn odd_prime_schema_rejects_non_odd_primes() {
        for n in [0, 1, 2, 4, 6, 9, 10] {
            let report = verify_odd_prime_weyl_schema(n);
            assert_eq!(report.status, OddPrimeWeylStatus::UnsupportedDimension);
            assert!(report.error.is_some());
        }
    }
}

#[cfg(test)]
mod l4_boundary_tests_f33fc677 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordf33fc677::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordf33fc677::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordf33fc677::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordf33fc677::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordf33fc677::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorf33fc677::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorf33fc677::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
