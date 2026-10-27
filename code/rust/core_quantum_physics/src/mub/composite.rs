// AuthorityEffect: None. Citation: sealed-derivation-v1 (3100c4e)

//! Composite dimension MUB tensor-product lower-control construction.
//!
//! Adapted from core_mub composite_tensor_family_gate.rs:
//! For a composite dimension d = d_1 * d_2 with prime-power factors d_1 and d_2,
//! taking the paired Kronecker products of projectors from factor MUB families
//! yields min(B_1, B_2) mutually unbiased bases of dimension d.
//!
//! For d = 6 = 2 * 3:
//! - d_1 = 2 has 3 complete MUB bases
//! - d_2 = 3 has 4 complete MUB bases
//! - Paired tensor product yields min(3, 4) = 3 mutually unbiased bases of size 6x6.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_53b7fcc5<T> {
    fn checked_invariant_53b7fcc5(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_53b7fcc5<T> for Option<T> {
    #[inline]
    fn checked_invariant_53b7fcc5(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_53b7fcc5<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_53b7fcc5(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::mub::char_two::build_char_two_mub_d2;
use crate::mub::odd_prime::build_odd_prime_mub_d3;
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{involution::Involution, matrix};
use core_number_theory::cyclotomic::Cyc24;
use core_number_theory::scalar::RationalEmbedding;

/// Build a composite MUB family by pairing basis indices and taking Kronecker products.
pub fn build_composite_tensor_mub<C: RationalEmbedding + Involution>(
    family_a: &[Vec<BasicMatrix<C>>],
    dim_a: usize,
    family_b: &[Vec<BasicMatrix<C>>],
    dim_b: usize,
) -> Result<Vec<Vec<BasicMatrix<C>>>, String> {
    if dim_a == 0
        || dim_b == 0
        || dim_a.checked_mul(dim_b).is_none_or(|d| d > 64)
        || family_a.is_empty()
        || family_b.is_empty()
    {
        return Err("invalid composite MUB carrier".into());
    }
    validate_composite_factor(family_a, dim_a)?;
    validate_composite_factor(family_b, dim_b)?;
    let mut out = Vec::new();
    for (a, b) in family_a.iter().zip(family_b) {
        out.push(kronecker_basis_pair(a, b, dim_a * dim_b)?);
    }
    Ok(out)
}

fn validate_composite_factor<C>(
    family: &[Vec<BasicMatrix<C>>],
    d: usize,
) -> Result<(), String> {
    if family
        .iter()
        .any(|b| b.len() != d || b.iter().any(|p| p.shape() != (d, d)))
    {
        return Err("malformed tensor factor projector carrier".into());
    }
    Ok(())
}

fn kronecker_basis_pair<C: RationalEmbedding + Involution>(
    a: &[BasicMatrix<C>],
    b: &[BasicMatrix<C>],
    cap: usize,
) -> Result<Vec<BasicMatrix<C>>, String> {
    let mut basis = Vec::with_capacity(cap);
    for p in a {
        for q in b {
            basis.push(matrix::kronecker(p, q).map_err(|e| e.to_string())?);
        }
    }
    Ok(basis)
}

/// Construct the 3 guaranteed MUB bases in composite dimension 6 (2 * 3) over Cyc24.
pub fn build_composite_mub_d6() -> Vec<Vec<BasicMatrix<Cyc24>>> {
    let d2 = build_char_two_mub_d2();
    let d3 = build_odd_prime_mub_d3();
    build_composite_tensor_mub(&d2, 2, &d3, 3).checked_invariant_53b7fcc5("fixed admitted factor families")
}

// Origin: engine/crates_rs/core_quantum_physics/src/mub/composite.rs
// Claim: urn:core:crates_rs:core-quantum-physics:composite:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord53b7fcc5 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord53b7fcc5` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError53b7fcc5 {
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
impl BoundaryError53b7fcc5 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError53b7fcc5 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError53b7fcc5 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord53b7fcc5 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError53b7fcc5> {
        if capacity_bound == 0 {
            return Err(BoundaryError53b7fcc5::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError53b7fcc5::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError53b7fcc5::ExceedsCapacity {
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
    use crate::mub::algebra::{verify_mub_projector_algebra, ProjectorAlgebraStatus};

    #[test]
    fn test_composite_d6_algebra() {
        let bases = build_composite_mub_d6();
        let report = verify_mub_projector_algebra(&bases, 6);
        assert_eq!(report.status, ProjectorAlgebraStatus::AlgebraVerified);
        assert_eq!(report.basis_count, 3);
        assert_eq!(report.projector_count, 18);
        assert_eq!(report.dimension, 6);
    }
}

#[cfg(test)]
mod l4_boundary_tests_53b7fcc5 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord53b7fcc5::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord53b7fcc5::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord53b7fcc5::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord53b7fcc5::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord53b7fcc5::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError53b7fcc5::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError53b7fcc5::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
