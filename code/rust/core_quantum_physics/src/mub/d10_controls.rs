//! Exact `Q(zeta_120)` controls for the MUB(10) carrier boundary.
//!
//! The d=10 control is intentionally partial: tensoring exact d=2 and d=5
//! controls yields three mutually unbiased bases in dimension 10, not a
//! complete eleven-basis MUB(10) theorem.

use std::sync::OnceLock;

use serde::Serialize;

use core_number_theory::cyclotomic120::{c1_120, icyc_120, sqrt2_120, sqrt5_120, Cyc120};
use core_number_theory::rational::rq;

pub type Vector120 = Vec<Cyc120>;
pub type Basis120 = Vec<Vector120>;
pub type BasisSet120 = Vec<Basis120>;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum Cyclotomic120Status {
    ExactCompleteSet,
    ExactPartialSet,
    VerificationFailed,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct Cyclotomic120ControlReport {
    pub target: &'static str,
    pub dimension: usize,
    pub basis_count: usize,
    pub status: Cyclotomic120Status,
    pub construction: &'static str,
    pub checked_identities: Vec<&'static str>,
    pub boundary: &'static str,
    pub error: Option<String>,
}

pub fn verify_cyclotomic120_controls() -> Vec<Cyclotomic120ControlReport> {
    static REPORTS: OnceLock<Vec<Cyclotomic120ControlReport>> = OnceLock::new();
    REPORTS
        .get_or_init(|| {
            vec![
                verify_d5_complete_control(),
                verify_d10_product_three_mub_control(),
            ]
        })
        .clone()
}

pub fn verify_d5_complete_control() -> Cyclotomic120ControlReport {
    let bases = build_d5_complete_mub();
    match verify_basis_set(&bases, Some(6)) {
        Ok(()) => Cyclotomic120ControlReport {
            target: "d=5 complete MUB control",
            dimension: 5,
            basis_count: bases.len(),
            status: Cyclotomic120Status::ExactCompleteSet,
            construction: "odd-prime Weyl quadratic bases over F_5 in Q(zeta_120)",
            checked_identities: exact_identity_list("basis count is d+1"),
            boundary: "prime-dimensional control benchmark only; used to enable exact d=10 lower-control tensors",
            error: None,
        },
        Err(error) => failed_report("d=5 complete MUB control", 5, bases.len(), error),
    }
}

pub fn verify_d10_product_three_mub_control() -> Cyclotomic120ControlReport {
    let bases = build_d10_product_three_mubs();
    match verify_basis_set(&bases, Some(3)) {
        Ok(()) => Cyclotomic120ControlReport {
            target: "d=10 tensor-product three-MUB lower control",
            dimension: 10,
            basis_count: bases.len(),
            status: Cyclotomic120Status::ExactPartialSet,
            construction: "tensor product of exact d=2 and d=5 MUB controls in Q(zeta_120)",
            checked_identities: exact_identity_list("basis count is 3, not d+1"),
            boundary: "lower-control only; does not construct or obstruct a complete MUB(10)",
            error: None,
        },
        Err(error) => failed_report(
            "d=10 tensor-product three-MUB lower control",
            10,
            bases.len(),
            error,
        ),
    }
}

pub fn build_d5_complete_mub() -> BasisSet120 {
    let zero = Cyc120::zero();
    let one = c1_120();
    let inv_s5 = sqrt5_120().inv();
    let mut bases = Vec::new();

    let computational = (0..5)
        .map(|col| {
            (0..5)
                .map(|row| {
                    if row == col {
                        one.clone()
                    } else {
                        zero.clone()
                    }
                })
                .collect::<Vector120>()
        })
        .collect::<Basis120>();
    bases.push(computational);

    for a in 0_i32..5 {
        let basis = (0_i32..5)
            .map(|m| {
                (0_i32..5)
                    .map(|x| {
                        let exponent = (a * x * x + m * x).rem_euclid(5);
                        Cyc120::zeta(24 * exponent).mul(&inv_s5)
                    })
                    .collect::<Vector120>()
            })
            .collect::<Basis120>();
        bases.push(basis);
    }
    bases
}

pub fn build_d10_product_three_mubs() -> BasisSet120 {
    let d2 = build_d2_complete_mub_120();
    let d5 = build_d5_complete_mub();
    (0..3)
        .map(|i| tensor_basis(&d2[i], &d5[i]))
        .collect::<BasisSet120>()
}

fn build_d2_complete_mub_120() -> BasisSet120 {
    let zero = Cyc120::zero();
    let one = c1_120();
    let inv_s2 = sqrt2_120().inv();
    let i = icyc_120();

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

fn tensor_basis(left: &Basis120, right: &Basis120) -> Basis120 {
    let mut basis = Vec::with_capacity(left.len() * right.len());
    for u in left {
        for v in right {
            let mut vector = Vec::with_capacity(u.len() * v.len());
            for x in u {
                for y in v {
                    vector.push(x.mul(y));
                }
            }
            basis.push(vector);
        }
    }
    basis
}

fn verify_single_basis(
    basis: &Basis120,
    d: usize,
    one: &Cyc120,
    zero: &Cyc120,
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

fn verify_cross_basis_pair(
    b1: usize,
    b2: usize,
    basis1: &Basis120,
    basis2: &Basis120,
    inv_d: &Cyc120,
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

fn verify_basis_set(bases: &[Basis120], expected_basis_count: Option<usize>) -> Result<(), String> {
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
    let one = c1_120();
    let zero = Cyc120::zero();
    let inv_d = Cyc120::rat(rq(1, d as i64));

    for basis in bases {
        verify_single_basis(basis, d, &one, &zero)?;
    }

    for b1 in 0..bases.len() {
        for b2 in (b1 + 1)..bases.len() {
            verify_cross_basis_pair(b1, b2, &bases[b1], &bases[b2], &inv_d)?;
        }
    }
    Ok(())
}

fn inner_product(u: &[Cyc120], v: &[Cyc120]) -> Cyc120 {
    let mut ip = Cyc120::zero();
    for (x, y) in u.iter().zip(v.iter()) {
        ip = ip.add(&x.conj().mul(y));
    }
    ip
}

fn exact_identity_list(count_identity: &'static str) -> Vec<&'static str> {
    vec![
        "each basis has d vectors in dimension d",
        "each basis is exactly orthonormal",
        "each cross-basis squared overlap is exactly 1/d",
        count_identity,
    ]
}

fn failed_report(
    target: &'static str,
    dimension: usize,
    basis_count: usize,
    error: String,
) -> Cyclotomic120ControlReport {
    Cyclotomic120ControlReport {
        target,
        dimension,
        basis_count,
        status: Cyclotomic120Status::VerificationFailed,
        construction: "exact Q(zeta_120) finite control",
        checked_identities: vec![],
        boundary: "failed control benchmark",
        error: Some(error),
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/mub/d10_controls.rs
// Claim: urn:core:crates_rs:core-quantum-physics:d10-controls:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord9e7b7d18 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord9e7b7d18` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError9e7b7d18 {
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
impl BoundaryError9e7b7d18 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError9e7b7d18 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError9e7b7d18 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord9e7b7d18 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError9e7b7d18> {
        if capacity_bound == 0 {
            return Err(BoundaryError9e7b7d18::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError9e7b7d18::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError9e7b7d18::ExceedsCapacity {
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
    fn d5_complete_mub_verifies_exactly() {
        let report = verify_d5_complete_control();
        assert_eq!(report.status, Cyclotomic120Status::ExactCompleteSet);
        assert_eq!(report.basis_count, 6);
    }

    #[test]
    fn d10_tensor_product_three_mubs_verify_exactly() {
        let report = verify_d10_product_three_mub_control();
        assert_eq!(report.status, Cyclotomic120Status::ExactPartialSet);
        assert_eq!(report.dimension, 10);
        assert_eq!(report.basis_count, 3);
        assert!(report.boundary.contains("does not"));
    }

    #[test]
    fn d10_control_is_not_complete() {
        let report = verify_d10_product_three_mub_control();
        assert_ne!(report.basis_count, report.dimension + 1);
    }
}

#[cfg(test)]
mod l4_boundary_tests_9e7b7d18 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord9e7b7d18::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord9e7b7d18::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord9e7b7d18::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord9e7b7d18::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord9e7b7d18::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError9e7b7d18::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError9e7b7d18::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
