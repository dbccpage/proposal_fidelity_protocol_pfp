// AuthorityEffect: None. Citation: sealed-derivation-v1 (3100c4e)

//! Odd-prime Weyl MUB construction.
//!
//! Adapted from core_mub odd_prime_weyl.rs: implements the exact quadratic
//! additive-character MUB family in odd prime dimensions p.
//! For any odd prime p, constructs the p+1 bases:
//! - Basis 0: Computational basis |k><k|
//! - Bases 1..=p: Quadratic chirp bases with slope s in 0..p:
//!   (Pi_{s, k})_{j, l} = 1/p * zeta_p^( 2^(-1) * s * (j^2 - l^2) + k * (j - l) )

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_05eb2260<T> {
    fn checked_invariant_05eb2260(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_05eb2260<T> for Option<T> {
    #[inline]
    fn checked_invariant_05eb2260(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_05eb2260<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_05eb2260(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::matrix;
use core_number_theory::cyclotomic::{Cyc24, Cyc5};
use core_number_theory::rational::rq;

/// Construct the complete 4 MUB bases of dimension 3 over Cyc24.
pub fn build_odd_prime_mub_d3() -> Vec<Vec<BasicMatrix<Cyc24>>> {
    let mut bases = Vec::with_capacity(4);

    // Basis 0: Computational basis |k><k|
    let mut b0 = Vec::with_capacity(3);
    for k in 0..3 {
        let mut proj =
            matrix::zeros(3, 3).checked_invariant_05eb2260("checked square projector carrier");
        proj.set(k, k, Cyc24::one())
            .checked_invariant_05eb2260("indices lie in the checked projector carrier");
        b0.push(proj);
    }
    bases.push(b0);

    // Bases 1, 2, 3: Slopes s in {0, 1, 2}
    // In F_3, 2^(-1) = 2.
    for s in 0..3i64 {
        let mut b_s = Vec::with_capacity(3);
        for k in 0..3i64 {
            let mut proj =
                matrix::zeros(3, 3).checked_invariant_05eb2260("checked square projector carrier");
            for j in 0..3i64 {
                for l in 0..3i64 {
                    let quad = 2 * s * (j * j - l * l);
                    let lin = k * (j - l);
                    let pow = (quad + lin).rem_euclid(3) as i32;
                    let val = Cyc24::zeta3_pow(pow).mul(&Cyc24::rat(rq(1, 3)));
                    proj.set(j as usize, l as usize, val)
                        .checked_invariant_05eb2260("indices lie in the checked projector carrier");
                }
            }
            b_s.push(proj);
        }
        bases.push(b_s);
    }

    bases
}

/// Construct the complete 6 MUB bases of dimension 5 over Cyc5.
pub fn build_odd_prime_mub_d5() -> Vec<Vec<BasicMatrix<Cyc5>>> {
    let mut bases = Vec::with_capacity(6);

    // Basis 0: Computational basis |k><k|
    let mut b0 = Vec::with_capacity(5);
    for k in 0..5 {
        let mut proj =
            matrix::zeros(5, 5).checked_invariant_05eb2260("checked square projector carrier");
        proj.set(k, k, Cyc5::one())
            .checked_invariant_05eb2260("indices lie in the checked projector carrier");
        b0.push(proj);
    }
    bases.push(b0);

    // Bases 1..=5: Slopes s in 0..5
    // In F_5, 2^(-1) = 3 (since 2 * 3 = 6 = 1 mod 5).
    let fifth = Cyc5::rat(rq(1, 5));
    for s in 0..5i64 {
        let mut b_s = Vec::with_capacity(5);
        for k in 0..5i64 {
            let mut proj =
                matrix::zeros(5, 5).checked_invariant_05eb2260("checked square projector carrier");
            for j in 0..5i64 {
                for l in 0..5i64 {
                    let quad = 3 * s * (j * j - l * l);
                    let lin = k * (j - l);
                    let pow = (quad + lin).rem_euclid(5) as i32;
                    let val = Cyc5::zeta5(pow).mul(&fifth);
                    proj.set(j as usize, l as usize, val)
                        .checked_invariant_05eb2260("indices lie in the checked projector carrier");
                }
            }
            b_s.push(proj);
        }
        bases.push(b_s);
    }

    bases
}

// Origin: engine/crates_rs/core_quantum_physics/src/mub/odd_prime.rs
// Claim: urn:core:crates_rs:core-quantum-physics:odd-prime:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord05eb2260 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord05eb2260` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError05eb2260 {
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
impl BoundaryError05eb2260 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError05eb2260 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError05eb2260 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord05eb2260 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError05eb2260> {
        if capacity_bound == 0 {
            return Err(BoundaryError05eb2260::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError05eb2260::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError05eb2260::ExceedsCapacity {
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
    fn test_odd_prime_d3_algebra() {
        let bases = build_odd_prime_mub_d3();
        let report = verify_mub_projector_algebra(&bases, 3);
        assert_eq!(report.status, ProjectorAlgebraStatus::AlgebraVerified);
        assert_eq!(report.basis_count, 4);
        assert_eq!(report.projector_count, 12);
    }

    #[test]
    fn test_odd_prime_d5_algebra() {
        let bases = build_odd_prime_mub_d5();
        let report = verify_mub_projector_algebra(&bases, 5);
        assert_eq!(report.status, ProjectorAlgebraStatus::AlgebraVerified);
        assert_eq!(report.basis_count, 6);
        assert_eq!(report.projector_count, 30);
    }
}

fn build_computational_projectors<const P: usize>(
    q: usize,
) -> Result<Vec<BasicMatrix<core_number_theory::cyclotomic_field::Cyclotomic<P>>>, String> {
    use core_number_theory::cyclotomic_field::Cyclotomic;
    let mut computational = Vec::with_capacity(q);
    for k in 0..q {
        let mut p = matrix::zeros::<Cyclotomic<P>>(q, q).map_err(|e| e.to_string())?;
        p.set(k, k, Cyclotomic::one()).map_err(|e| e.to_string())?;
        computational.push(p);
    }
    Ok(computational)
}

fn build_slope_frequency_projector<const P: usize>(
    field: &core_number_theory::finite_field::FiniteField,
    q: usize,
    inv_two: &core_number_theory::finite_field::FieldElement,
    slope: &core_number_theory::finite_field::FieldElement,
    frequency: &core_number_theory::finite_field::FieldElement,
    weight: &core_number_theory::rational::Rational,
) -> Result<BasicMatrix<core_number_theory::cyclotomic_field::Cyclotomic<P>>, String> {
    use core_number_theory::cyclotomic_field::Cyclotomic;
    let elements = field.elements();
    let mut projector = matrix::zeros::<Cyclotomic<P>>(q, q).map_err(|e| e.to_string())?;
    for (j, x) in elements.iter().enumerate() {
        for (l, y) in elements.iter().enumerate() {
            let difference = field.sub(x, y);
            let squares = field.sub(&field.mul(x, x), &field.mul(y, y));
            let phase = field.add(
                &field.mul(&field.mul(inv_two, slope), &squares),
                &field.mul(frequency, &difference),
            );
            let exponent = field.trace_value(&phase)?;
            projector
                .set(j, l, Cyclotomic::<P>::zeta(exponent as i64).scale(weight))
                .map_err(|e| e.to_string())?;
        }
    }
    Ok(projector)
}

fn validate_odd_prime_mub_budget<const P: usize>(
    degree: usize,
    entry_budget: usize,
) -> Result<(usize, core_number_theory::finite_field::FiniteField), String> {
    use core_number_theory::finite_field::{checked_pow, is_prime, FiniteField};
    if P == 2 || !is_prime(P) || degree == 0 {
        return Err("an odd prime and positive extension degree are required".into());
    }
    let q = checked_pow(P, degree).ok_or("finite-field order overflow")?;
    let required = q
        .checked_mul(q)
        .and_then(|x| x.checked_mul(q))
        .and_then(|x| x.checked_mul(q + 1))
        .ok_or("entry count overflow")?;
    if required > entry_budget {
        return Err(format!(
            "{required} output entries exceed budget {entry_budget}"
        ));
    }
    let field = FiniteField::with_first_irreducible(P, degree)
        .ok_or("no checked irreducible field polynomial")?;
    Ok((q, field))
}

/// Complete MUBs in an arbitrary declared odd prime-power dimension q=p^r.
/// The scalar field Q(zeta_P) has compile-time prime conductor P; finite-field
/// arithmetic and absolute traces are delegated to core_number_theory.
/// The output-entry budget bounds q^3(q+1), and exhaustion is not nonexistence.
pub fn build_odd_prime_power_mub<const P: usize>(
    degree: usize,
    entry_budget: usize,
) -> Result<Vec<Vec<BasicMatrix<core_number_theory::cyclotomic_field::Cyclotomic<P>>>>, String> {
    let (q, field) = validate_odd_prime_mub_budget::<P>(degree, entry_budget)?;
    let elements = field.elements();
    let inv_two = field.base((P + 1) / 2);
    let mut bases = Vec::with_capacity(q + 1);
    bases.push(build_computational_projectors::<P>(q)?);
    let weight =
        core_number_theory::rational::Rational::new(1.into(), num_bigint::BigInt::from(q));
    for slope in elements {
        let mut basis = Vec::with_capacity(q);
        for frequency in elements {
            basis.push(build_slope_frequency_projector::<P>(
                &field, q, &inv_two, slope, frequency, &weight,
            )?);
        }
        bases.push(basis);
    }
    Ok(bases)
}

#[cfg(test)]
mod l4_boundary_tests_05eb2260 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord05eb2260::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord05eb2260::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord05eb2260::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord05eb2260::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord05eb2260::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError05eb2260::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError05eb2260::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
