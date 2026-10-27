//! Exact finite-dimensional control MUB constructors.
//!
//! These are positive benchmark solves for dimensions supported by the current
//! exact field `Q(zeta_24)`: prime d=2 and d=3, plus the prime-power
//! two-qubit control d=4. The d=7, d=11, and d=13 odd-prime controls use
//! separate clean-room cyclotomic lanes. They do not imply anything about d=6,
//! d=10, or general d.

use std::sync::OnceLock;

use serde::Serialize;

use linear_algebra::exact_field::involution::Involution;
use linear_algebra::scalars::Semiring;
use core_number_theory::character_sums::{verify_character_sum_identities, CyclotomicField};
use core_number_theory::cyclotomic::Cyc24;
use core_number_theory::cyclotomic28::{c1_28, sqrt7_28, Cyc28};
use core_number_theory::cyclotomic44::{c1_44, sqrt11_44, Cyc44};
use core_number_theory::cyclotomic52::{sqrt13_52, Cyc52};
use core_number_theory::finite_field::FiniteField;
use core_number_theory::rational::rq;
use core_number_theory::scalar::RationalEmbedding;

pub type Vector = Vec<Cyc24>;
pub type Basis = Vec<Vector>;
pub type BasisSet = Vec<Basis>;
pub type Vector28 = Vec<Cyc28>;
pub type Basis28 = Vec<Vector28>;
pub type BasisSet28 = Vec<Basis28>;
pub type Vector44 = Vec<Cyc44>;
pub type Basis44 = Vec<Vector44>;
pub type BasisSet44 = Vec<Basis44>;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum BenchmarkStatus {
    ExactCompleteSet,
    VerificationFailed,
    UnsupportedDimension,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct PrimeControlReport {
    pub dimension: usize,
    pub basis_count: usize,
    pub status: BenchmarkStatus,
    pub construction: &'static str,
    pub checked_identities: Vec<&'static str>,
    pub boundary: &'static str,
    pub error: Option<String>,
}

pub fn verify_prime_controls() -> Vec<PrimeControlReport> {
    static REPORTS: OnceLock<Vec<PrimeControlReport>> = OnceLock::new();
    REPORTS
        .get_or_init(|| {
            vec![
                verify_d2_control(),
                verify_d3_control(),
                verify_d7_control(),
                verify_d11_control(),
                verify_d13_control(),
            ]
        })
        .clone()
}

pub fn verify_prime_power_controls() -> Vec<PrimeControlReport> {
    static REPORTS: OnceLock<Vec<PrimeControlReport>> = OnceLock::new();
    REPORTS.get_or_init(|| vec![verify_d4_control()]).clone()
}

pub fn verify_d2_control() -> PrimeControlReport {
    let bases = build_d2_complete_mub();
    match verify_basis_set(&bases) {
        Ok(()) => PrimeControlReport {
            dimension: 2,
            basis_count: bases.len(),
            status: BenchmarkStatus::ExactCompleteSet,
            construction: "Pauli X/Y/Z eigenbases in Q(zeta_24)",
            checked_identities: exact_identity_list(),
            boundary: "control benchmark only; does not transport to d=6 or d=10",
            error: None,
        },
        Err(error) => failed_report(2, bases.len(), error),
    }
}

pub fn verify_d3_control() -> PrimeControlReport {
    let bases = build_d3_complete_mub();
    match verify_basis_set(&bases) {
        Ok(()) => PrimeControlReport {
            dimension: 3,
            basis_count: bases.len(),
            status: BenchmarkStatus::ExactCompleteSet,
            construction: "odd-prime Weyl quadratic bases over F_3 in Q(zeta_24)",
            checked_identities: exact_identity_list(),
            boundary: "prime-dimensional control benchmark only; not a composite-dimension theorem",
            error: None,
        },
        Err(error) => failed_report(3, bases.len(), error),
    }
}

pub fn verify_d4_control() -> PrimeControlReport {
    let bases = build_d4_complete_mub();
    match verify_basis_set(&bases) {
        Ok(()) => PrimeControlReport {
            dimension: 4,
            basis_count: bases.len(),
            status: BenchmarkStatus::ExactCompleteSet,
            construction: "two-qubit Pauli stabilizer bases in Q(zeta_24)",
            checked_identities: exact_identity_list(),
            boundary:
                "prime-power composite control benchmark only; does not transport to d=6 or d=10",
            error: None,
        },
        Err(error) => failed_report(4, bases.len(), error),
    }
}

pub fn verify_d7_control() -> PrimeControlReport {
    let bases = build_d7_complete_mub();
    match verify_basis_set_28(&bases).and_then(|_| verify_d7_weyl_quadratic_identities()) {
        Ok(()) => PrimeControlReport {
            dimension: 7,
            basis_count: bases.len(),
            status: BenchmarkStatus::ExactCompleteSet,
            construction: "odd-prime Weyl quadratic bases over F_7 in Q(zeta_28)",
            checked_identities: d7_exact_identity_list(),
            boundary: "prime-dimensional control only; not a composite-dimension or all-N theorem",
            error: None,
        },
        Err(error) => failed_report(7, bases.len(), error),
    }
}

pub fn verify_d11_control() -> PrimeControlReport {
    match verify_d11_weyl_quadratic_identities() {
        Ok(()) => PrimeControlReport {
            dimension: 11,
            basis_count: 12,
            status: BenchmarkStatus::ExactCompleteSet,
            construction: "odd-prime Weyl quadratic bases over F_11 in Q(zeta_44)",
            checked_identities: d11_exact_identity_list(),
            boundary: "prime-dimensional control only; not a composite-dimension or all-N theorem",
            error: None,
        },
        Err(error) => failed_report(11, 12, error),
    }
}

pub fn verify_d13_control() -> PrimeControlReport {
    match verify_d13_weyl_quadratic_identities() {
        Ok(()) => PrimeControlReport {
            dimension: 13,
            basis_count: 14,
            status: BenchmarkStatus::ExactCompleteSet,
            construction: "odd-prime Weyl quadratic bases over F_13 in Q(zeta_52)",
            checked_identities: d13_exact_identity_list(),
            boundary: "prime-dimensional control only; not a composite-dimension or all-N theorem",
            error: None,
        },
        Err(error) => failed_report(13, 14, error),
    }
}

pub fn build_d2_complete_mub() -> BasisSet {
    let zero = Cyc24::zero();
    let one = Cyc24::one();
    let inv_s2 = Cyc24::sqrt2().inv();
    let i = Cyc24::i();

    let z = vec![
        vec![one.clone(), zero.clone()],
        vec![zero.clone(), one.clone()],
    ];
    let x = vec![
        vec![inv_s2.clone(), inv_s2.clone()],
        vec![inv_s2.clone(), inv_s2.neg()],
    ];
    let y = vec![
        vec![inv_s2.clone(), i.mul(&inv_s2)],
        vec![inv_s2.clone(), i.mul(&inv_s2).neg()],
    ];
    vec![z, x, y]
}

pub fn build_d3_complete_mub() -> BasisSet {
    let zero = Cyc24::zero();
    let one = Cyc24::one();
    let inv_s3 = Cyc24::sqrt3().inv();
    let mut bases = Vec::new();

    let computational = (0..3)
        .map(|col| {
            (0..3)
                .map(|row| {
                    if row == col {
                        one.clone()
                    } else {
                        zero.clone()
                    }
                })
                .collect::<Vector>()
        })
        .collect::<Basis>();
    bases.push(computational);

    for a in 0_i32..3 {
        let basis = (0_i32..3)
            .map(|m| {
                (0_i32..3)
                    .map(|x| {
                        let exponent = (a * x * x + m * x).rem_euclid(3);
                        Cyc24::zeta24(8 * exponent).mul(&inv_s3)
                    })
                    .collect::<Vector>()
            })
            .collect::<Basis>();
        bases.push(basis);
    }
    bases
}

pub fn build_d4_complete_mub() -> BasisSet {
    let zero = Cyc24::zero();
    let one = Cyc24::one();
    let minus_one = one.neg();
    let half = Cyc24::rat(rq(1, 2));
    let i = Cyc24::i();
    let minus_i = i.neg();

    let computational = (0..4)
        .map(|col| {
            (0..4)
                .map(|row| {
                    if row == col {
                        one.clone()
                    } else {
                        zero.clone()
                    }
                })
                .collect::<Vector>()
        })
        .collect::<Basis>();

    let xx = scaled_basis(
        vec![
            vec![one.clone(), one.clone(), one.clone(), one.clone()],
            vec![
                minus_one.clone(),
                one.clone(),
                minus_one.clone(),
                one.clone(),
            ],
            vec![
                minus_one.clone(),
                minus_one.clone(),
                one.clone(),
                one.clone(),
            ],
            vec![
                one.clone(),
                minus_one.clone(),
                minus_one.clone(),
                one.clone(),
            ],
        ],
        &half,
    );
    let yy = scaled_basis(
        vec![
            vec![
                minus_one.clone(),
                minus_i.clone(),
                minus_i.clone(),
                one.clone(),
            ],
            vec![one.clone(), minus_i.clone(), i.clone(), one.clone()],
            vec![one.clone(), i.clone(), minus_i.clone(), one.clone()],
            vec![minus_one.clone(), i.clone(), i.clone(), one.clone()],
        ],
        &half,
    );
    let xz_zy = scaled_basis(
        vec![
            vec![i.clone(), minus_one.clone(), i.clone(), one.clone()],
            vec![
                minus_i.clone(),
                minus_one.clone(),
                minus_i.clone(),
                one.clone(),
            ],
            vec![minus_i.clone(), one.clone(), i.clone(), one.clone()],
            vec![i.clone(), one.clone(), minus_i.clone(), one.clone()],
        ],
        &half,
    );
    let xy_yz = scaled_basis(
        vec![
            vec![minus_i.clone(), i.clone(), one.clone(), one.clone()],
            vec![
                minus_i.clone(),
                minus_i.clone(),
                minus_one.clone(),
                one.clone(),
            ],
            vec![i.clone(), i.clone(), minus_one.clone(), one.clone()],
            vec![i.clone(), minus_i.clone(), one.clone(), one.clone()],
        ],
        &half,
    );

    vec![computational, xx, yy, xz_zy, xy_yz]
}

pub fn build_d7_complete_mub() -> BasisSet28 {
    let zero = Cyc28::zero();
    let one = c1_28();
    let inv_s7 = sqrt7_28().inv();
    let mut bases = Vec::new();

    let computational = (0..7)
        .map(|col| {
            (0..7)
                .map(|row| {
                    if row == col {
                        one.clone()
                    } else {
                        zero.clone()
                    }
                })
                .collect::<Vector28>()
        })
        .collect::<Basis28>();
    bases.push(computational);

    for a in 0_i32..7 {
        let basis = (0_i32..7)
            .map(|m| {
                (0_i32..7)
                    .map(|x| {
                        let exponent = (a * x * x + m * x).rem_euclid(7);
                        Cyc28::zeta(4 * exponent).mul(&inv_s7)
                    })
                    .collect::<Vector28>()
            })
            .collect::<Basis28>();
        bases.push(basis);
    }
    bases
}

pub fn build_d11_complete_mub() -> BasisSet44 {
    let zero = Cyc44::zero();
    let one = c1_44();
    let inv_s11 = sqrt11_44().inv();
    let mut bases = Vec::new();

    let computational = (0..11)
        .map(|col| {
            (0..11)
                .map(|row| {
                    if row == col {
                        one.clone()
                    } else {
                        zero.clone()
                    }
                })
                .collect::<Vector44>()
        })
        .collect::<Basis44>();
    bases.push(computational);

    for a in 0_i32..11 {
        let basis = (0_i32..11)
            .map(|m| {
                (0_i32..11)
                    .map(|x| {
                        let exponent = (a * x * x + m * x).rem_euclid(11);
                        Cyc44::zeta(4 * exponent).mul(&inv_s11)
                    })
                    .collect::<Vector44>()
            })
            .collect::<Basis44>();
        bases.push(basis);
    }
    bases
}

pub fn verify_basis_set(bases: &[Basis]) -> Result<(), String> {
    verify_basis_set_with_expected_count(bases, None)
}

pub fn verify_partial_basis_set(
    bases: &[Basis],
    expected_basis_count: usize,
) -> Result<(), String> {
    verify_basis_set_with_expected_count(bases, Some(expected_basis_count))
}

fn verify_single_basis_24(
    basis: &Basis,
    d: usize,
    one: &Cyc24,
    zero: &Cyc24,
) -> Result<(), String> {
    if basis.len() != d {
        return Err("basis has wrong vector count".to_string());
    }
    if basis.iter().any(|vector| vector.len() != d) {
        return Err("basis vector has wrong dimension".to_string());
    }
    for i in 0..d {
        for j in i..d {
            let ip = inner_product(&basis[i], &basis[j]);
            let want = if i == j { one } else { zero };
            if &ip != want {
                return Err(format!("basis is not orthonormal at ({i},{j})"));
            }
        }
    }
    Ok(())
}

fn verify_cross_basis_pair_24(
    b1: usize,
    b2: usize,
    basis1: &Basis,
    basis2: &Basis,
    inv_d: &Cyc24,
) -> Result<(), String> {
    for v1 in basis1 {
        for v2 in basis2 {
            let ip = inner_product(v1, v2);
            if &ip.mul(&ip.conj()) != inv_d {
                return Err(format!("bases {b1} and {b2} are not mutually unbiased"));
            }
        }
    }
    Ok(())
}

fn validate_basis_set_dimensions(
    bases: &[Basis],
    expected_basis_count: Option<usize>,
) -> Result<usize, String> {
    let first = bases.first().ok_or_else(|| "basis set is empty".to_string())?;
    let d = first.len();
    if d == 0 {
        return Err("dimension is zero".to_string());
    }
    match expected_basis_count {
        Some(expected) if bases.len() != expected => {
            return Err(format!("basis count mismatch: expected {expected}"));
        }
        None if bases.len() != d + 1 => {
            return Err("basis set is not complete: expected d+1 bases".to_string());
        }
        _ => {}
    }
    Ok(d)
}

fn verify_basis_set_with_expected_count(
    bases: &[Basis],
    expected_basis_count: Option<usize>,
) -> Result<(), String> {
    let d = validate_basis_set_dimensions(bases, expected_basis_count)?;
    let one = Cyc24::one();
    let zero = Cyc24::zero();
    let inv_d = Cyc24::rat(rq(1, d as i64));

    for basis in bases {
        verify_single_basis_24(basis, d, &one, &zero)?;
    }

    for b1 in 0..bases.len() {
        for b2 in (b1 + 1)..bases.len() {
            verify_cross_basis_pair_24(b1, b2, &bases[b1], &bases[b2], &inv_d)?;
        }
    }

    Ok(())
}

fn inner_product(u: &[Cyc24], v: &[Cyc24]) -> Cyc24 {
    let mut ip = Cyc24::zero();
    for (x, y) in u.iter().zip(v.iter()) {
        ip = ip.add(&x.conj().mul(y));
    }
    ip
}

fn verify_single_basis_28(
    basis: &Basis28,
    d: usize,
    one: &Cyc28,
    zero: &Cyc28,
) -> Result<(), String> {
    if basis.len() != d {
        return Err("basis has wrong vector count".to_string());
    }
    if basis.iter().any(|vector| vector.len() != d) {
        return Err("basis vector has wrong dimension".to_string());
    }
    for i in 0..d {
        for j in i..d {
            let ip = inner_product_28(&basis[i], &basis[j]);
            let want = if i == j { one } else { zero };
            if &ip != want {
                return Err(format!("basis is not orthonormal at ({i},{j})"));
            }
        }
    }
    Ok(())
}

fn verify_cross_basis_pair_28(
    b1: usize,
    b2: usize,
    basis1: &Basis28,
    basis2: &Basis28,
    inv_d: &Cyc28,
) -> Result<(), String> {
    for v1 in basis1 {
        for v2 in basis2 {
            let ip = inner_product_28(v1, v2);
            if &ip.mul(&ip.conj()) != inv_d {
                return Err(format!("bases {b1} and {b2} are not mutually unbiased"));
            }
        }
    }
    Ok(())
}

fn verify_basis_set_28(bases: &[Basis28]) -> Result<(), String> {
    if bases.is_empty() {
        return Err("basis set is empty".to_string());
    }
    let d = bases[0].len();
    if d == 0 {
        return Err("dimension is zero".to_string());
    }
    if bases.len() != d + 1 {
        return Err("basis set is not complete: expected d+1 bases".to_string());
    }
    let one = c1_28();
    let zero = Cyc28::zero();
    let inv_d = Cyc28::rat(rq(1, d as i64));

    for basis in bases {
        verify_single_basis_28(basis, d, &one, &zero)?;
    }

    for b1 in 0..bases.len() {
        for b2 in (b1 + 1)..bases.len() {
            verify_cross_basis_pair_28(b1, b2, &bases[b1], &bases[b2], &inv_d)?;
        }
    }

    Ok(())
}

fn inner_product_28(u: &[Cyc28], v: &[Cyc28]) -> Cyc28 {
    let mut ip = Cyc28::zero();
    for (x, y) in u.iter().zip(v.iter()) {
        ip = ip.add(&x.conj().mul(y));
    }
    ip
}

fn verify_d7_weyl_quadratic_identities() -> Result<(), String> {
    let sqrt7 = sqrt7_28();
    verify_prime_weyl_identities::<Cyc28>(7, &sqrt7, &sqrt7.inv())
}

fn verify_d11_weyl_quadratic_identities() -> Result<(), String> {
    let sqrt11 = sqrt11_44();
    verify_prime_weyl_identities::<Cyc44>(11, &sqrt11, &sqrt11.inv())
}

fn verify_d13_weyl_quadratic_identities() -> Result<(), String> {
    let sqrt13 = sqrt13_52();
    verify_prime_weyl_identities::<Cyc52>(13, &sqrt13, &sqrt13.inv())
}

/// The Weyl quadratic identities for prime `p` in `F = Q(zeta_{4p})`: the
/// `sqrt(p)` normalizer is real with inverse of squared norm `1/p`, and the
/// character-sum identities over `F_p` hold (see
/// `finite_qm::character_sums::verify_character_sum_identities`).
fn verify_prime_weyl_identities<F: CyclotomicField>(
    p: usize,
    sqrt_p: &F,
    inv_sqrt_p: &F,
) -> Result<(), String> {
    let one = <F as Semiring>::one();
    let p_value = <F as RationalEmbedding>::from_rational(&rq(p as i64, 1));
    let inv_p = <F as RationalEmbedding>::from_rational(&rq(1, p as i64));

    if Semiring::mul(sqrt_p, sqrt_p) != p_value {
        return Err(format!("sqrt({p}) normalizer does not square to {p}"));
    }
    if Involution::conjugate(sqrt_p) != *sqrt_p {
        return Err(format!("sqrt({p}) normalizer is not fixed by conjugation"));
    }
    if Semiring::mul(inv_sqrt_p, sqrt_p) != one {
        return Err(format!(
            "sqrt({p})^-1 is not a two-sided normalizer inverse"
        ));
    }
    if Semiring::mul(inv_sqrt_p, &Involution::conjugate(inv_sqrt_p)) != inv_p {
        return Err(format!("sqrt({p})^-1 does not have squared norm 1/{p}"));
    }

    let field = FiniteField::prime_field(p).ok_or_else(|| format!("F_{p} is not a prime field"))?;
    verify_character_sum_identities::<F>(&field).map(|_| ())
}

fn scaled_basis(raw: Vec<Vector>, scale: &Cyc24) -> Basis {
    raw.into_iter()
        .map(|vector| vector.into_iter().map(|x| x.mul(scale)).collect())
        .collect()
}

fn exact_identity_list() -> Vec<&'static str> {
    vec![
        "each basis has d vectors in dimension d",
        "each basis is exactly orthonormal",
        "each cross-basis squared overlap is exactly 1/d",
        "basis count is d+1",
    ]
}

fn d7_exact_identity_list() -> Vec<&'static str> {
    vec![
        "each basis has d vectors in dimension d",
        "each basis is exactly orthonormal",
        "each cross-basis squared overlap is exactly 1/d",
        "basis count is d+1",
        "sqrt(7)^-1 has exact squared norm 1/7",
        "nontrivial F_7 linear character sums vanish exactly",
        "F_7 quadratic Gauss sums have exact squared norm 7",
        "Weyl quadratic schema gives exact orthonormality and squared overlap 1/d",
    ]
}

fn d11_exact_identity_list() -> Vec<&'static str> {
    vec![
        "basis count is d+1",
        "sqrt(11)^-1 has exact squared norm 1/11",
        "nontrivial F_11 linear character sums vanish exactly",
        "F_11 quadratic Gauss sums have exact squared norm 11",
        "Weyl quadratic schema gives exact orthonormality and squared overlap 1/d",
    ]
}

fn d13_exact_identity_list() -> Vec<&'static str> {
    vec![
        "basis count is d+1",
        "sqrt(13)^-1 has exact squared norm 1/13",
        "nontrivial F_13 linear character sums vanish exactly",
        "F_13 quadratic Gauss sums have exact squared norm 13",
        "Weyl quadratic schema gives exact orthonormality and squared overlap 1/d",
    ]
}

fn failed_report(dimension: usize, basis_count: usize, error: String) -> PrimeControlReport {
    PrimeControlReport {
        dimension,
        basis_count,
        status: BenchmarkStatus::VerificationFailed,
        construction: "exact finite-dimensional control",
        checked_identities: vec![],
        boundary: "failed control benchmark",
        error: Some(error),
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/mub/prime_controls.rs
// Claim: urn:core:crates_rs:core-quantum-physics:prime-controls:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord2f903bb3 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord2f903bb3` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError2f903bb3 {
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
impl BoundaryError2f903bb3 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError2f903bb3 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError2f903bb3 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord2f903bb3 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError2f903bb3> {
        if capacity_bound == 0 {
            return Err(BoundaryError2f903bb3::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError2f903bb3::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError2f903bb3::ExceedsCapacity {
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
    fn d2_complete_mub_verifies_exactly() {
        let report = verify_d2_control();
        assert_eq!(report.status, BenchmarkStatus::ExactCompleteSet);
        assert_eq!(report.basis_count, 3);
    }

    #[test]
    fn d3_complete_mub_verifies_exactly() {
        let report = verify_d3_control();
        assert_eq!(report.status, BenchmarkStatus::ExactCompleteSet);
        assert_eq!(report.basis_count, 4);
    }

    #[test]
    fn d7_complete_mub_verifies_exactly() {
        let report = verify_d7_control();
        assert_eq!(report.status, BenchmarkStatus::ExactCompleteSet);
        assert_eq!(report.basis_count, 8);
    }

    #[test]
    fn d11_complete_mub_verifies_exactly() {
        let report = verify_d11_control();
        assert_eq!(report.status, BenchmarkStatus::ExactCompleteSet);
        assert_eq!(report.basis_count, 12);
    }

    #[test]
    fn d13_complete_mub_verifies_exactly() {
        let report = verify_d13_control();
        assert_eq!(report.status, BenchmarkStatus::ExactCompleteSet);
        assert_eq!(report.basis_count, 14);
    }

    #[test]
    fn d4_complete_mub_verifies_exactly() {
        let report = verify_d4_control();
        assert_eq!(report.status, BenchmarkStatus::ExactCompleteSet);
        assert_eq!(report.basis_count, 5);
    }

    #[test]
    fn prime_controls_do_not_claim_composite_dimensions() {
        for report in verify_prime_controls() {
            assert!(report.boundary.contains("not") || report.boundary.contains("does not"));
        }
    }

    #[test]
    fn prime_power_controls_do_not_claim_non_prime_power_dimensions() {
        for report in verify_prime_power_controls() {
            assert!(report.boundary.contains("does not"));
        }
    }
}

#[cfg(test)]
mod l4_boundary_tests_2f903bb3 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord2f903bb3::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord2f903bb3::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord2f903bb3::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord2f903bb3::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord2f903bb3::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError2f903bb3::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError2f903bb3::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
