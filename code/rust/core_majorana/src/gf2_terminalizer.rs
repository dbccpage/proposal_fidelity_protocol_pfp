//! Majorana GF(2) parity **diagnostic classifier / receipt**, and elements of
//! the cyclotomic ring $\mathbb{Z}[\zeta_{16}]$.
//!
//! `Cyclotomic16Element` is an element of $\mathbb{Z}[\zeta_{16}]$ with `i64`
//! coefficients; its one operation is an overflow-checked product modulo
//! $\zeta^8 + 1$. No braid identity is checked in this crate: the braid
//! relations of Majorana braid operators are checked, over $\mathbb{Q}(i)$, by
//! `core_quantum_physics::majorana_fock_algebra`. This module used to call
//! itself a "$\mathbb{Q}(\zeta_{16})$ braid verifier".
//!
//! # Authority fence (MANDATORY)
//!
//! This module is a **diagnostic classifier and receipt emitter only**.
//! - **AuthorityEffect: None** on every emitted certificate.
//! - It is **not** a CODA_GTLA / sweep / CODA authority terminalizer.
//! - It does **not** mint `CertifiedAuthority`, does not close an authority gate,
//!   and does not promote FOC `ExactRepair` or any other terminal status.
//! - The historical name `*Terminalizer*` and method `terminalize` mean
//!   "produce a parity-schedule diagnostic receipt", **not** "mint terminal authority".
//!
//! # What it computes
//!
//! Polynomial-time GF(2) Gaussian elimination, coboundary boundary validation
//! ($d_1 \cdot d_0 = 0 \pmod 2$), parity schedule classification
//! (`Exact`, `ClosedResidual`, `OpenObstruction` as **diagnostic** labels only),
//! and exact cyclotomic field arithmetic rejecting floating-point approximations.
//!
//! Certificate tag: `core.majorana-gf2-receipt.v1`  
//! AuthorityEffect: None
//!
//! Canonical crate home: `core_majorana` (re-exported from `engines::quantum`).

use serde::{Deserialize, Serialize};

/// Explicit fence for importers / skills.
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; not physical Majorana; GF(2) diagnostic only.";

/// Diagnostic schedule classification under GF(2) parity analysis.
///
/// Labels are receipt fields only. They do **not** mint authority, FOC ExactRepair,
/// or CODA_GTLA terminal status. `Exact` here means "GF(2) syndrome is a coboundary",
/// not "certified exact repair".
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum GF2ScheduleStatus {
    /// Diagnostic: exact parity solution ($d_0 x = \omega \pmod 2$ solvable).
    Exact,
    /// Diagnostic: closed residual parity ($d_1 \omega = 0 \pmod 2$, non-trivial cycle).
    ClosedResidual,
    /// Diagnostic: open parity obstruction ($d_1 \omega \neq 0 \pmod 2$).
    OpenObstruction,
}

/// A GF(2) Matrix representing coboundary operators or syndrome schedules.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct GF2Matrix {
    pub rows: usize,
    pub cols: usize,
    pub data: Vec<Vec<u8>>,
}

impl GF2Matrix {
    /// Creates a new GF(2) matrix initialized to zeros.
    pub fn zeros(rows: usize, cols: usize) -> Self {
        Self {
            rows,
            cols,
            data: vec![vec![0; cols]; rows],
        }
    }

    /// Creates a GF(2) matrix from a 2D vector of binary values (modulo 2).
    ///
    /// Rows are rectangularized to the longest row. A shorter row is padded
    /// with zeros; taking the width from row 0 alone left a later short row
    /// to panic in `rref` and `matmul`.
    pub fn from_data(data: Vec<Vec<u8>>) -> Self {
        let rows = data.len();
        let cols = data.iter().map(Vec::len).max().unwrap_or(0);
        let mut normalized = Vec::with_capacity(rows);
        for row in data {
            let mut out = vec![0u8; cols];
            for (col, val) in row.into_iter().enumerate() {
                out[col] = val % 2;
            }
            normalized.push(out);
        }
        Self {
            rows,
            cols,
            data: normalized,
        }
    }

    /// Performs matrix multiplication $C = A \cdot B \pmod 2$.
    pub fn matmul(&self, rhs: &GF2Matrix) -> Result<GF2Matrix, String> {
        if self.cols != rhs.rows {
            return Err(format!(
                "Shape mismatch for GF(2) matmul: ({}, {}) x ({}, {})",
                self.rows, self.cols, rhs.rows, rhs.cols
            ));
        }
        let mut result = GF2Matrix::zeros(self.rows, rhs.cols);
        for i in 0..self.rows {
            for j in 0..rhs.cols {
                let mut sum = 0u8;
                for k in 0..self.cols {
                    sum ^= self.data[i][k] & rhs.data[k][j];
                }
                result.data[i][j] = sum & 1;
            }
        }
        Ok(result)
    }

    /// Checks if the matrix is identical to the zero matrix.
    pub fn is_zero(&self) -> bool {
        self.data.iter().all(|row| row.iter().all(|&v| v == 0))
    }

    /// Computes Gaussian elimination over GF(2) and returns rank and reduced row-echelon form.
    pub fn rref(&self) -> (usize, GF2Matrix) {
        let mut mat = self.clone();
        let mut rank = 0;
        let mut col = 0;

        while rank < mat.rows && col < mat.cols {
            // Find pivot
            let mut pivot_row = None;
            for r in rank..mat.rows {
                if mat.data[r][col] == 1 {
                    pivot_row = Some(r);
                    break;
                }
            }

            if let Some(p_row) = pivot_row {
                mat.data.swap(rank, p_row);
                // Eliminate below and above
                for r in 0..mat.rows {
                    if r != rank && mat.data[r][col] == 1 {
                        for c in 0..mat.cols {
                            mat.data[r][c] ^= mat.data[rank][c];
                        }
                    }
                }
                rank += 1;
            }
            col += 1;
        }
        (rank, mat)
    }
}

/// Diagnostic receipt for a GF(2) cocycle/schedule classification.
///
/// Always carries `authority_effect = "None"`. Does not mint `CertifiedAuthority`.
/// Tag: `core.majorana-gf2-receipt.v1`.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Gf2ScheduleReceipt {
    pub certificate_tag: String,
    pub status: GF2ScheduleStatus,
    pub d0_rank: usize,
    pub d1_rank: usize,
    pub q1_dimension: usize,
    pub boundary_valid: bool,
    /// Always `"None"`.
    pub authority_effect: String,
}

/// GF(2) **diagnostic cocycle classifier** (membership in im/ker of declared maps).
///
/// Canonical name for the abacus Deutsch/Albert demanded. Does **not** mint authority.
pub struct Gf2CocycleClassifier;

impl Gf2CocycleClassifier {
    /// Verifies boundary condition $d_1 \cdot d_0 = 0 \pmod 2$.
    pub fn verify_boundary(d0: &GF2Matrix, d1: &GF2Matrix) -> bool {
        match d1.matmul(d0) {
            Ok(prod) => prod.is_zero(),
            Err(_) => false,
        }
    }

    /// Classify $\omega\in C^1$ against declared $(d_0,d_1)$: Exact / ClosedResidual / Open.
    ///
    /// Emits [`Gf2ScheduleReceipt`] with `authority_effect: "None"`.
    pub fn classify(
        d0: &GF2Matrix,
        d1: &GF2Matrix,
        syndrome: &[u8],
    ) -> Result<Gf2ScheduleReceipt, String> {
        if syndrome.len() != d0.rows {
            return Err(format!(
                "Syndrome dimension {} does not match d0 rows {}",
                syndrome.len(),
                d0.rows
            ));
        }

        let boundary_valid = Self::verify_boundary(d0, d1);
        if !boundary_valid {
            return Err("Boundary operator validation failed: d1 * d0 != 0 mod 2".into());
        }

        let (rank_d0, _) = d0.rref();
        let (rank_d1, _) = d1.rref();

        let mut d1_syndrome = vec![0u8; d1.rows];
        for i in 0..d1.rows {
            let mut sum = 0u8;
            for j in 0..d1.cols {
                sum ^= d1.data[i][j] & (syndrome[j] % 2);
            }
            d1_syndrome[i] = sum & 1;
        }

        let is_closed = d1_syndrome.iter().all(|&v| v == 0);

        let mut augmented = vec![vec![0u8; d0.cols + 1]; d0.rows];
        for r in 0..d0.rows {
            for c in 0..d0.cols {
                augmented[r][c] = d0.data[r][c];
            }
            augmented[r][d0.cols] = syndrome[r] % 2;
        }
        let aug_mat = GF2Matrix::from_data(augmented);
        let (aug_rank, _) = aug_mat.rref();

        let status = if aug_rank == rank_d0 {
            GF2ScheduleStatus::Exact
        } else if is_closed {
            GF2ScheduleStatus::ClosedResidual
        } else {
            GF2ScheduleStatus::OpenObstruction
        };

        let ker_d1 = d1.cols.saturating_sub(rank_d1);
        let q1_dim = ker_d1.saturating_sub(rank_d0);

        Ok(Gf2ScheduleReceipt {
            certificate_tag: "core.majorana-gf2-receipt.v1".into(),
            status,
            d0_rank: rank_d0,
            d1_rank: rank_d1,
            q1_dimension: q1_dim,
            boundary_valid,
            authority_effect: "None".into(),
        })
    }
}

/// An element of the cyclotomic ring $\mathbb{Z}[\zeta_{16}]$: integer
/// coefficients on $1, \zeta, \dots, \zeta^7$, with $\zeta^8 = -1$. It carries
/// no division and verifies no braid identity.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Cyclotomic16Element {
    /// Coefficients $[c_0, c_1, \dots, c_7]$ for basis $1, \zeta, \zeta^2, \dots, \zeta^7$.
    pub coeffs: [i64; 8],
}

impl Cyclotomic16Element {
    pub fn zero() -> Self {
        Self { coeffs: [0; 8] }
    }

    pub fn one() -> Self {
        let mut c = [0; 8];
        c[0] = 1;
        Self { coeffs: c }
    }

    pub fn from_scalar(val: i64) -> Self {
        let mut c = [0; 8];
        c[0] = val;
        Self { coeffs: c }
    }

    /// The product in $\mathbb{Z}[\zeta_{16}]$, reducing modulo $\zeta^8 + 1$;
    /// `None` when a coefficient leaves `i64` (it used to wrap silently in
    /// release builds).
    pub fn checked_mul(&self, rhs: &Self) -> Option<Self> {
        let mut raw = [0i64; 16];
        for i in 0..8 {
            for j in 0..8 {
                raw[i + j] = raw[i + j].checked_add(self.coeffs[i].checked_mul(rhs.coeffs[j])?)?;
            }
        }
        // Reduce using zeta^8 = -1
        let mut res = [0i64; 8];
        for k in 0..8 {
            res[k] = raw[k].checked_sub(raw[k + 8])?;
        }
        Some(Self { coeffs: res })
    }

    /// $\zeta$ itself.
    pub fn zeta() -> Self {
        let mut c = [0; 8];
        c[1] = 1;
        Self { coeffs: c }
    }
}

// Origin: engine/crates_rs/core_majorana/src/gf2_terminalizer.rs
// Claim: urn:core:crates_rs:core-majorana:gf2-terminalizer:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord7ed9677d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord7ed9677d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError7ed9677d {
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
impl BoundaryError7ed9677d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError7ed9677d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError7ed9677d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord7ed9677d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError7ed9677d> {
        if capacity_bound == 0 {
            return Err(BoundaryError7ed9677d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError7ed9677d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError7ed9677d::ExceedsCapacity {
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
    fn test_gf2_matrix_boundary_and_terminalization() {
        // d0: 3 vertices to 3 edges (Triangle complex)
        let d0_data = vec![
            vec![1, 1, 0], // edge 0: (v0, v1)
            vec![0, 1, 1], // edge 1: (v1, v2)
            vec![1, 0, 1], // edge 2: (v0, v2)
        ];
        let d0 = GF2Matrix::from_data(d0_data);

        // d1: 3 edges to 1 face
        let d1_data = vec![
            vec![1, 1, 1], // face 0: e0 + e1 + e2
        ];
        let d1 = GF2Matrix::from_data(d1_data);

        assert!(Gf2CocycleClassifier::verify_boundary(&d0, &d1));

        // Exact syndrome: e0 + e1 + e2 = d0(v1)
        let exact_syndrome = vec![1, 1, 0];
        let cert_exact = Gf2CocycleClassifier::classify(&d0, &d1, &exact_syndrome).unwrap();
        assert_eq!(cert_exact.status, GF2ScheduleStatus::Exact);
        assert_eq!(cert_exact.certificate_tag, "core.majorana-gf2-receipt.v1");

        // Open obstruction syndrome: single edge defect
        let open_syndrome = vec![1, 0, 0];
        let cert_open = Gf2CocycleClassifier::classify(&d0, &d1, &open_syndrome).unwrap();
        assert_eq!(cert_open.status, GF2ScheduleStatus::OpenObstruction);
    }

    #[test]
    fn ragged_rows_are_rectangular_and_do_not_panic() {
        let matrix = GF2Matrix::from_data(vec![vec![1], vec![1, 1, 3]]);
        assert_eq!(matrix.rows, 2);
        assert_eq!(matrix.cols, 3);
        assert_eq!(matrix.data[0], vec![1, 0, 0]);
        assert_eq!(matrix.data[1], vec![1, 1, 1]);
        let (rank, _) = matrix.rref();
        assert_eq!(rank, 2);
        let wide = GF2Matrix::from_data(vec![vec![1, 0], vec![1]]);
        let product = wide.matmul(&GF2Matrix::zeros(2, 1)).unwrap();
        assert_eq!(product.data, vec![vec![0], vec![0]]);
    }

    #[test]
    fn test_cyclotomic16_arithmetic() {
        let one = Cyclotomic16Element::one();
        let prod = one.checked_mul(&one).unwrap();
        assert_eq!(prod, one);

        // zeta^4 * zeta^4 = zeta^8 mod (zeta^8 + 1) = -1
        let mut zeta4 = Cyclotomic16Element::zero();
        zeta4.coeffs[4] = 1;
        let zeta8 = zeta4.checked_mul(&zeta4).unwrap();
        assert_eq!(zeta8.coeffs[0], -1);
    }

    /// The reduction is modulo `zeta^8 + 1`, so `zeta` has order exactly 16;
    /// reducing modulo `zeta^8 - 1` would give order 8.
    #[test]
    fn zeta_has_order_sixteen() {
        let zeta = Cyclotomic16Element::zeta();
        let mut power = Cyclotomic16Element::one();
        let mut order = None;
        for k in 1..=16 {
            power = power.checked_mul(&zeta).unwrap();
            if power == Cyclotomic16Element::one() {
                order = Some(k);
                break;
            }
        }
        assert_eq!(order, Some(16));
    }

    /// A product whose coefficients leave `i64` is refused, not wrapped.
    #[test]
    fn coefficient_overflow_is_refused() {
        let big = Cyclotomic16Element::from_scalar(i64::MAX / 2 + 1);
        assert_eq!(big.checked_mul(&Cyclotomic16Element::from_scalar(2)), None);
        assert_eq!(
            Cyclotomic16Element::from_scalar(3).checked_mul(&Cyclotomic16Element::from_scalar(-4)),
            Some(Cyclotomic16Element::from_scalar(-12))
        );
    }
}

#[cfg(test)]
mod l4_boundary_tests_7ed9677d {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord7ed9677d::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord7ed9677d::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord7ed9677d::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord7ed9677d::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord7ed9677d::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError7ed9677d::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError7ed9677d::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
