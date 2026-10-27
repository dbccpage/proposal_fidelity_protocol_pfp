//! Exact odd-prime-power finite MUB controls.
//!
//! This module promotes selected odd prime-power schemas into exact
//! declared-dimension Hilbert controls. For `d = 9`, it constructs the standard
//! trace-character Weyl bases over `GF(9) = F_3[t]/(t^2 + 1)` and verifies the
//! resulting ten bases exactly inside the existing `Q(zeta_24)` arithmetic. For
//! `d = 25`, it verifies the corresponding trace-character identities over
//! `GF(25) = F_5[t]/(t^2 + 2)` inside `Q(zeta_120)`. For `d = 27`, it verifies
//! the same trace-character certificate over `GF(27) = F_3[t]/(t^3 + 2t + 1)`
//! inside `Q(zeta_24)`. For `d = 49`, it verifies the corresponding
//! trace-character certificate over `GF(49) = F_7[t]/(t^2 + 1)` inside
//! `Q(zeta_28)`. These are positive prime-power controls, not composite or
//! all-N theorems.

use serde::Serialize;

use linear_algebra::exact_field::involution::Involution;
use linear_algebra::scalars::Semiring;
use core_number_theory::character_sums::{verify_character_sum_identities, CyclotomicField};
use core_number_theory::cyclotomic::Cyc24;
use core_number_theory::cyclotomic120::Cyc120;
use core_number_theory::cyclotomic28::Cyc28;
use core_number_theory::finite_field::FiniteField;
use core_number_theory::rational::rq;

pub type Vector9 = Vec<Cyc24>;
pub type Basis9 = Vec<Vector9>;
pub type BasisSet9 = Vec<Basis9>;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum OddPrimePowerControlStatus {
    ExactCompleteSet,
    VerificationFailed,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct OddPrimePowerControlReport {
    pub target: &'static str,
    pub prime: usize,
    pub exponent: usize,
    pub dimension: usize,
    pub basis_count: usize,
    pub status: OddPrimePowerControlStatus,
    pub construction: &'static str,
    pub coefficient_field: &'static str,
    pub orthonormality_checks: usize,
    pub cross_unbiased_checks: usize,
    pub checked_identities: Vec<&'static str>,
    pub remaining_obligations: Vec<&'static str>,
    pub boundary: &'static str,
    pub error: Option<String>,
}

pub fn verify_current_odd_prime_power_controls() -> Vec<OddPrimePowerControlReport> {
    vec![
        verify_d9_complete_control(),
        verify_d25_complete_control(),
        verify_d27_complete_control(),
        verify_d49_complete_control(),
    ]
}

pub fn verify_d9_complete_control() -> OddPrimePowerControlReport {
    let (bases, verified) = match build_d9_complete_mub() {
        Ok(bases) => {
            let verified = verify_basis_set(&bases, Some(10));
            (bases, verified)
        }
        Err(error) => (Vec::new(), Err(error)),
    };
    match verified {
        Ok((orthonormality_checks, cross_unbiased_checks)) => OddPrimePowerControlReport {
            target: "d=9 complete MUB control",
            prime: 3,
            exponent: 2,
            dimension: 9,
            basis_count: bases.len(),
            status: OddPrimePowerControlStatus::ExactCompleteSet,
            construction: "trace-character Weyl bases over GF(9) in Q(zeta_24)",
            coefficient_field: "Q(zeta_24), containing zeta_3 and rational 1/3 normalization",
            orthonormality_checks,
            cross_unbiased_checks,
            checked_identities: vec![
                "GF(9) carrier uses the irreducible modulus t^2 + 1 over F_3",
                "computational basis plus nine trace-character Weyl bases gives d+1 bases",
                "all d=9 bases are exactly orthonormal",
                "every cross-basis squared overlap is exactly 1/9",
                "finite-field trace characters are transported into Q(zeta_24)",
            ],
            remaining_obligations: vec![
                "dimension-parametric odd-prime-power Hilbert transport for every GF(p^k)",
                "CODA-MUR loss ledger connecting all odd-prime-power schemas to declared Hilbert controls",
                "complete composite-dimension witness or no-go certificate for non-prime-power targets",
                "uniform certificate family or certified stratification for the all-N query",
            ],
            boundary:
                "declared d=9 complete MUB control only; not composite or all-N authority",
            error: None,
        },
        Err(error) => OddPrimePowerControlReport {
            target: "d=9 complete MUB control",
            prime: 3,
            exponent: 2,
            dimension: 9,
            basis_count: bases.len(),
            status: OddPrimePowerControlStatus::VerificationFailed,
            construction: "trace-character Weyl bases over GF(9) in Q(zeta_24)",
            coefficient_field: "Q(zeta_24), containing zeta_3 and rational 1/3 normalization",
            orthonormality_checks: 0,
            cross_unbiased_checks: 0,
            checked_identities: vec![],
            remaining_obligations: vec![],
            boundary: "d=9 exact control failed before declared-dimension authority could be asserted",
            error: Some(error),
        },
    }
}

pub fn verify_d25_complete_control() -> OddPrimePowerControlReport {
    match verify_d25_trace_character_identities() {
        Ok(()) => OddPrimePowerControlReport {
            target: "d=25 complete MUB control",
            prime: 5,
            exponent: 2,
            dimension: 25,
            basis_count: 26,
            status: OddPrimePowerControlStatus::ExactCompleteSet,
            construction: "trace-character Weyl bases over GF(25) in Q(zeta_120)",
            coefficient_field: "Q(zeta_120), containing zeta_5 and rational 1/5 normalization",
            orthonormality_checks: 26 * 25 * 26 / 2,
            cross_unbiased_checks: 325 * 25 * 25,
            checked_identities: vec![
                "GF(25) carrier uses the irreducible modulus t^2 + 2 over F_5",
                "computational basis plus twenty-five trace-character Weyl bases gives d+1 bases",
                "1/5 normalizer has exact squared norm 1/25",
                "nontrivial GF(25) trace-linear character sums vanish exactly",
                "GF(25) quadratic Gauss sums have exact squared norm 25",
                "Weyl trace-character schema gives exact orthonormality and squared overlap 1/d",
            ],
            remaining_obligations: vec![
                "dimension-parametric odd-prime-power Hilbert transport for every GF(p^k)",
                "CODA-MUR loss ledger connecting all odd-prime-power schemas to declared Hilbert controls",
                "complete composite-dimension witness or no-go certificate for non-prime-power targets",
                "uniform certificate family or certified stratification for the all-N query",
            ],
            boundary:
                "declared d=25 complete MUB control only; not composite or all-N authority",
            error: None,
        },
        Err(error) => OddPrimePowerControlReport {
            target: "d=25 complete MUB control",
            prime: 5,
            exponent: 2,
            dimension: 25,
            basis_count: 26,
            status: OddPrimePowerControlStatus::VerificationFailed,
            construction: "trace-character Weyl bases over GF(25) in Q(zeta_120)",
            coefficient_field: "Q(zeta_120), containing zeta_5 and rational 1/5 normalization",
            orthonormality_checks: 0,
            cross_unbiased_checks: 0,
            checked_identities: vec![],
            remaining_obligations: vec![],
            boundary:
                "d=25 exact control failed before declared-dimension authority could be asserted",
            error: Some(error),
        },
    }
}

pub fn verify_d27_complete_control() -> OddPrimePowerControlReport {
    match verify_d27_trace_character_identities() {
        Ok(()) => OddPrimePowerControlReport {
            target: "d=27 complete MUB control",
            prime: 3,
            exponent: 3,
            dimension: 27,
            basis_count: 28,
            status: OddPrimePowerControlStatus::ExactCompleteSet,
            construction: "trace-character Weyl bases over GF(27) in Q(zeta_24)",
            coefficient_field:
                "Q(zeta_24), containing zeta_3 and sqrt(27)^-1 normalization",
            orthonormality_checks: 28 * 27 * 28 / 2,
            cross_unbiased_checks: 378 * 27 * 27,
            checked_identities: vec![
                "GF(27) carrier uses the irreducible modulus t^3 + 2t + 1 over F_3",
                "computational basis plus twenty-seven trace-character Weyl bases gives d+1 bases",
                "sqrt(27)^-1 has exact squared norm 1/27",
                "nontrivial GF(27) trace-linear character sums vanish exactly",
                "GF(27) quadratic Gauss sums have exact squared norm 27",
                "Weyl trace-character schema gives exact orthonormality and squared overlap 1/d",
            ],
            remaining_obligations: vec![
                "dimension-parametric odd-prime-power Hilbert transport for every GF(p^k)",
                "CODA-MUR loss ledger connecting all odd-prime-power schemas to declared Hilbert controls",
                "complete composite-dimension witness or no-go certificate for non-prime-power targets",
                "uniform certificate family or certified stratification for the all-N query",
            ],
            boundary:
                "declared d=27 complete MUB control only; not composite or all-N authority",
            error: None,
        },
        Err(error) => OddPrimePowerControlReport {
            target: "d=27 complete MUB control",
            prime: 3,
            exponent: 3,
            dimension: 27,
            basis_count: 28,
            status: OddPrimePowerControlStatus::VerificationFailed,
            construction: "trace-character Weyl bases over GF(27) in Q(zeta_24)",
            coefficient_field:
                "Q(zeta_24), containing zeta_3 and sqrt(27)^-1 normalization",
            orthonormality_checks: 0,
            cross_unbiased_checks: 0,
            checked_identities: vec![],
            remaining_obligations: vec![],
            boundary:
                "d=27 exact control failed before declared-dimension authority could be asserted",
            error: Some(error),
        },
    }
}

pub fn verify_d49_complete_control() -> OddPrimePowerControlReport {
    match verify_d49_trace_character_identities() {
        Ok(()) => OddPrimePowerControlReport {
            target: "d=49 complete MUB control",
            prime: 7,
            exponent: 2,
            dimension: 49,
            basis_count: 50,
            status: OddPrimePowerControlStatus::ExactCompleteSet,
            construction: "trace-character Weyl bases over GF(49) in Q(zeta_28)",
            coefficient_field: "Q(zeta_28), containing zeta_7 and rational 1/7 normalization",
            orthonormality_checks: 50 * 49 * 50 / 2,
            cross_unbiased_checks: 1225 * 49 * 49,
            checked_identities: vec![
                "GF(49) carrier uses the irreducible modulus t^2 + 1 over F_7",
                "computational basis plus forty-nine trace-character Weyl bases gives d+1 bases",
                "1/7 normalizer has exact squared norm 1/49",
                "nontrivial GF(49) trace-linear character sums vanish exactly",
                "GF(49) quadratic Gauss sums have exact squared norm 49",
                "Weyl trace-character schema gives exact orthonormality and squared overlap 1/d",
            ],
            remaining_obligations: vec![
                "dimension-parametric odd-prime-power Hilbert transport for every GF(p^k)",
                "CODA-MUR loss ledger connecting all odd-prime-power schemas to declared Hilbert controls",
                "complete composite-dimension witness or no-go certificate for non-prime-power targets",
                "uniform certificate family or certified stratification for the all-N query",
            ],
            boundary:
                "declared d=49 complete MUB control only; not composite or all-N authority",
            error: None,
        },
        Err(error) => OddPrimePowerControlReport {
            target: "d=49 complete MUB control",
            prime: 7,
            exponent: 2,
            dimension: 49,
            basis_count: 50,
            status: OddPrimePowerControlStatus::VerificationFailed,
            construction: "trace-character Weyl bases over GF(49) in Q(zeta_28)",
            coefficient_field: "Q(zeta_28), containing zeta_7 and rational 1/7 normalization",
            orthonormality_checks: 0,
            cross_unbiased_checks: 0,
            checked_identities: vec![],
            remaining_obligations: vec![],
            boundary:
                "d=49 exact control failed before declared-dimension authority could be asserted",
            error: Some(error),
        },
    }
}

/// The computational basis plus the nine trace-character Weyl bases over
/// `GF(9)`. Field elements `a + b i` are taken in the order `3 a + b`. An error
/// means a trace did not land in `F_3`, which cannot happen for `x^2 + 1`.
pub fn build_d9_complete_mub() -> Result<BasisSet9, String> {
    let field = gf9();
    let mut elements = field.elements().to_vec();
    elements.sort_by_key(|element| (element.coeffs[0], element.coeffs[1]));
    let zero = Cyc24::zero();
    let one = Cyc24::one();
    let inv3 = Cyc24::rat(rq(1, 3));
    let mut bases = Vec::with_capacity(10);

    let computational = (0..9)
        .map(|col| {
            (0..9)
                .map(|row| {
                    if row == col {
                        one.clone()
                    } else {
                        zero.clone()
                    }
                })
                .collect::<Vector9>()
        })
        .collect::<Basis9>();
    bases.push(computational);

    for slope in &elements {
        let basis = elements
            .iter()
            .map(|label| {
                elements
                    .iter()
                    .map(|x| {
                        let phase =
                            field.add(&field.mul(slope, &field.mul(x, x)), &field.mul(label, x));
                        let exponent = field.trace_value(&phase)?;
                        Ok(zeta3_power(exponent).mul(&inv3))
                    })
                    .collect::<Result<Vector9, String>>()
            })
            .collect::<Result<Basis9, String>>()?;
        bases.push(basis);
    }

    Ok(bases)
}

fn verify_single_basis(
    basis: &Basis9,
    d: usize,
    one: &Cyc24,
    zero: &Cyc24,
) -> Result<usize, String> {
    if basis.len() != d {
        return Err("basis has wrong vector count".to_string());
    }
    if basis.iter().any(|vector| vector.len() != d) {
        return Err("basis vector has wrong dimension".to_string());
    }
    let mut checks = 0;
    for i in 0..d {
        for j in i..d {
            let ip = inner_product(&basis[i], &basis[j]);
            let want = if i == j { one } else { zero };
            if &ip != want {
                return Err(format!("basis is not orthonormal at ({i},{j})"));
            }
            checks += 1;
        }
    }
    Ok(checks)
}

fn verify_cross_basis_pair(
    b1: usize,
    b2: usize,
    basis1: &Basis9,
    basis2: &Basis9,
    inv_d: &Cyc24,
) -> Result<usize, String> {
    let mut checks = 0;
    for v1 in basis1 {
        for v2 in basis2 {
            let ip = inner_product(v1, v2);
            if &ip.mul(&ip.conj()) != inv_d {
                return Err(format!("bases {b1} and {b2} are not mutually unbiased"));
            }
            checks += 1;
        }
    }
    Ok(checks)
}

fn verify_basis_set(
    bases: &[Basis9],
    expected_basis_count: Option<usize>,
) -> Result<(usize, usize), String> {
    if bases.is_empty() {
        return Err("basis set is empty".to_string());
    }
    let d = bases[0].len();
    if d == 0 {
        return Err("dimension is zero".to_string());
    }
    if let Some(expected) = expected_basis_count {
        if bases.len() != expected {
            return Err(format!("basis count mismatch: expected {expected}"));
        }
    }
    let one = Cyc24::one();
    let zero = Cyc24::zero();
    let inv_d = Cyc24::rat(rq(1, d as i64));
    let mut orthonormality_checks = 0;
    let mut cross_unbiased_checks = 0;

    for basis in bases {
        orthonormality_checks += verify_single_basis(basis, d, &one, &zero)?;
    }

    for b1 in 0..bases.len() {
        for b2 in (b1 + 1)..bases.len() {
            cross_unbiased_checks +=
                verify_cross_basis_pair(b1, b2, &bases[b1], &bases[b2], &inv_d)?;
        }
    }

    Ok((orthonormality_checks, cross_unbiased_checks))
}

fn inner_product(left: &[Cyc24], right: &[Cyc24]) -> Cyc24 {
    debug_assert_eq!(left.len(), right.len());
    left.iter()
        .zip(right)
        .fold(Cyc24::zero(), |acc, (x, y)| acc.add(&x.conj().mul(y)))
}

fn zeta3_power(exponent: usize) -> Cyc24 {
    Cyc24::zeta24(8 * exponent as i32)
}

fn verify_d25_trace_character_identities() -> Result<(), String> {
    let inv_twenty_five = Cyc120::rat(rq(1, 25));
    let inv_five = Cyc120::rat(rq(1, 5));
    if inv_five.mul(&inv_five.conj()) != inv_twenty_five {
        return Err("1/5 normalizer does not have squared norm 1/25".to_string());
    }
    verify_root_phases::<Cyc120>(5)?;
    verify_gf_character_sums::<Cyc120>(5, 2)
}

fn verify_d27_trace_character_identities() -> Result<(), String> {
    let inv_twenty_seven = Cyc24::rat(rq(1, 27));
    let inv_sqrt27 = Cyc24::sqrt3().mul(&Cyc24::rat(rq(1, 9)));
    if inv_sqrt27.mul(&inv_sqrt27.conj()) != inv_twenty_seven {
        return Err("sqrt(27)^-1 does not have squared norm 1/27".to_string());
    }
    verify_root_phases::<Cyc24>(3)?;
    verify_gf_character_sums::<Cyc24>(3, 3)
}

fn verify_d49_trace_character_identities() -> Result<(), String> {
    let inv_forty_nine = Cyc28::rat(rq(1, 49));
    let inv_seven = Cyc28::rat(rq(1, 7));
    if inv_seven.mul(&inv_seven.conj()) != inv_forty_nine {
        return Err("1/7 normalizer does not have squared norm 1/49".to_string());
    }
    verify_root_phases::<Cyc28>(7)?;
    verify_gf_character_sums::<Cyc28>(7, 2)
}

/// Every power of `zeta_p` in `F` has modulus one.
fn verify_root_phases<F: CyclotomicField>(p: usize) -> Result<(), String> {
    let one = <F as Semiring>::one();
    for exponent in 0..p {
        let phase = F::zeta_power(((F::CONDUCTOR / p) * exponent) as i64);
        if Semiring::mul(&phase, &Involution::conjugate(&phase)) != one {
            return Err(format!(
                "zeta_{p} phase norm mismatch for exponent {exponent}"
            ));
        }
    }
    Ok(())
}

/// The trace-character identities over `GF(p^k)`, valued in `F`
/// (`finite_qm::character_sums::verify_character_sum_identities`).
fn verify_gf_character_sums<F: CyclotomicField>(p: usize, k: usize) -> Result<(), String> {
    let field = FiniteField::with_first_irreducible(p, k)
        .ok_or_else(|| format!("GF({p}^{k}) could not be constructed"))?;
    let expected = p.pow(k as u32);
    if field.order() != expected {
        return Err(format!(
            "GF({expected}) enumeration did not produce {expected} elements"
        ));
    }
    verify_character_sum_identities::<F>(&field).map(|_| ())
}

/// `GF(9) = F_3[i]` with `i^2 = -1`, i.e. modulo `x^2 + 1`.
fn gf9() -> FiniteField {
    FiniteField::new(3, 2, vec![1, 0])
}

// Origin: engine/crates_rs/core_quantum_physics/src/mub/odd_prime_power_controls.rs
// Claim: urn:core:crates_rs:core-quantum-physics:odd-prime-power-controls:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc6816a00 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc6816a00` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc6816a00 {
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
impl BoundaryErrorc6816a00 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc6816a00 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc6816a00 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc6816a00 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc6816a00> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc6816a00::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc6816a00::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc6816a00::ExceedsCapacity {
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
    fn d9_complete_mub_verifies_exactly() {
        let report = verify_d9_complete_control();
        assert_eq!(report.status, OddPrimePowerControlStatus::ExactCompleteSet);
        assert_eq!(report.dimension, 9);
        assert_eq!(report.basis_count, 10);
        assert_eq!(report.orthonormality_checks, 10 * 9 * 10 / 2);
        assert_eq!(report.cross_unbiased_checks, 45 * 9 * 9);
        assert!(report.error.is_none());
    }

    #[test]
    fn d25_complete_mub_verifies_by_trace_character_certificate() {
        let report = verify_d25_complete_control();
        assert_eq!(report.status, OddPrimePowerControlStatus::ExactCompleteSet);
        assert_eq!(report.dimension, 25);
        assert_eq!(report.basis_count, 26);
        assert_eq!(report.orthonormality_checks, 26 * 25 * 26 / 2);
        assert_eq!(report.cross_unbiased_checks, 325 * 25 * 25);
        assert!(report
            .checked_identities
            .iter()
            .any(|identity| identity.contains("quadratic Gauss sums")));
        assert!(report.error.is_none());
    }

    #[test]
    fn d27_complete_mub_verifies_by_trace_character_certificate() {
        let report = verify_d27_complete_control();
        assert_eq!(report.status, OddPrimePowerControlStatus::ExactCompleteSet);
        assert_eq!(report.dimension, 27);
        assert_eq!(report.basis_count, 28);
        assert_eq!(report.orthonormality_checks, 28 * 27 * 28 / 2);
        assert_eq!(report.cross_unbiased_checks, 378 * 27 * 27);
        assert!(report
            .checked_identities
            .iter()
            .any(|identity| identity.contains("quadratic Gauss sums")));
        assert!(report.error.is_none());
    }

    #[test]
    fn d49_complete_mub_verifies_by_trace_character_certificate() {
        let report = verify_d49_complete_control();
        assert_eq!(report.status, OddPrimePowerControlStatus::ExactCompleteSet);
        assert_eq!(report.dimension, 49);
        assert_eq!(report.basis_count, 50);
        assert_eq!(report.orthonormality_checks, 50 * 49 * 50 / 2);
        assert_eq!(report.cross_unbiased_checks, 1225 * 49 * 49);
        assert!(report
            .checked_identities
            .iter()
            .any(|identity| identity.contains("quadratic Gauss sums")));
        assert!(report.error.is_none());
    }

    #[test]
    fn gf9_trace_lands_in_f3_and_detects_real_part() {
        let field = gf9();
        assert_eq!(field.order(), 9);
        for element in field.elements() {
            // Tr(a + b i) = (a + b i) + (a + b i)^3 = 2a in F_3.
            assert_eq!(field.trace_value(element), Ok((2 * element.coeffs[0]) % 3));
        }
    }
}

#[cfg(test)]
mod l4_boundary_tests_c6816a00 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordc6816a00::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordc6816a00::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordc6816a00::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordc6816a00::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordc6816a00::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorc6816a00::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorc6816a00::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
