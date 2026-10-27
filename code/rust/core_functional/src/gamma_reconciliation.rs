// AuthorityEffect: None.

//! Raw versus second-repair quotient `Gamma`: certificate checkers.
//!
//! The data are a defect map `D : Q^n -> Q^m`, a second-repair map
//! `A : Q^k -> Q^m` (both row-wise) and strictly positive weights `w` on
//! `Q^m`. For `x` in `Q^n`:
//!
//! - `Gamma_raw(x) = sum_i w_i |(D x)_i|`;
//! - `Gamma_quot(x) = min_u ||D x + A u||_{1,w}`.
//!
//! Taking `u = 0` shows `Gamma_quot <= Gamma_raw`. The two agree at every `x`
//! exactly when the capacity-bounded annihilator condition holds:
//! `D^T K_w = D^T B_w`, `B_w = {z : |z_i| <= w_i}`, `K_w = B_w ∩ ker A^T`.
//! Since `D^T B_w` is the convex hull of the `2^m` points `D^T (w ⊙ σ)`,
//! `σ` in `{-1, 1}^m`, the condition is the finite vertex condition: for every
//! sign vector `σ` some `z_σ` has `A^T z_σ = 0`, `|z_σ| <= w` and
//! `D^T z_σ = D^T (w ⊙ σ)`.
//!
//! This module checks, without trusting a producer:
//!
//! - a dual certificate of one value of `Gamma_quot` ([`RepairQuotientProblem::verify_quotient_certificate`]);
//! - a complete vertex table, which gives agreement at every `x`
//!   ([`RepairQuotientProblem::verify_vertex_table`]);
//! - a Farkas certificate that one vertex fails, from which it builds an `x`
//!   and a `u` with `Gamma_quot(x) < Gamma_raw(x)`
//!   ([`RepairQuotientProblem::verify_vertex_farkas`]);
//! - a direct value gap and a zero-test gap;
//! - the two descent conditions for a declared first repair `d0 : Q^c -> Q^n`.
//!
//! The zero tests `Gamma_raw(x) = 0` and `Gamma_quot(x) = 0` agree for all `x`
//! exactly when `im D ∩ im A = {0}`; that condition is weaker than value
//! agreement. All carriers here are rational vector spaces with the weighted
//! `l1` norm; a binary carrier with Hamming weight is a different problem and
//! is not accepted by these types.

use num_rational::BigRational as Q;
use num_traits::{Signed, Zero};
use std::collections::BTreeMap;
use thiserror::Error;

/// The largest number of rows for which a full vertex table is checked.
pub const MAX_VERTEX_ROWS: usize = 16;

/// Refusals and negative findings of the reconciliation contract.
#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum GammaReconciliationError {
    #[error("{what}: expected {expected} entries, found {actual}")]
    DimensionMismatch {
        what: &'static str,
        expected: usize,
        actual: usize,
    },
    #[error("a rational entry has a non-positive denominator")]
    InvalidRational,
    #[error("weight {index} is not strictly positive")]
    NonPositiveWeight { index: usize },
    #[error("{rows} rows exceed the vertex-table limit {limit}")]
    CarrierTooLarge { rows: usize, limit: usize },
    #[error("the claimed residual differs from D x + A u")]
    ResidualMismatch,
    #[error("the claimed value differs from the weighted l1 norm of the residual")]
    ValueMismatch,
    #[error("dual entry {index} lies outside the weight box")]
    DualOutOfBox { index: usize },
    #[error("the dual does not annihilate column {column} of A")]
    DualNotAnnihilating { column: usize },
    #[error("the dual pairing with D x differs from the value")]
    DualPairingMismatch,
    #[error("sign vector {sign:?} is not a sign vector of length m")]
    BadSign { sign: Vec<i8> },
    #[error("the vertex table has no entry for sign vector {sign:?}")]
    MissingVertex { sign: Vec<i8> },
    #[error("the vertex table repeats sign vector {sign:?}")]
    DuplicateVertex { sign: Vec<i8> },
    #[error("the extension for {sign:?} fails at {reason}")]
    VertexDefect { sign: Vec<i8>, reason: &'static str },
    #[error("Farkas multiplier {index} is negative")]
    NegativeMultiplier { index: usize },
    #[error("the Farkas combination is nonzero at row {row}")]
    FarkasCombinationNonzero { row: usize },
    #[error("the Farkas bound is not negative")]
    FarkasBoundNotNegative,
    #[error("the residual norm is not below Gamma_raw(x)")]
    NoValueGap,
    #[error("the pair does not separate the zero tests")]
    NoZeroTestGap,
    #[error("D d0 is nonzero at ({row}, {column})")]
    NotRawDescent { row: usize, column: usize },
    #[error("D d0 differs from A G at ({row}, {column})")]
    NotQuotientDescent { row: usize, column: usize },
}

type Result<T> = std::result::Result<T, GammaReconciliationError>;

fn valid(x: &Q) -> bool {
    x.denom().is_positive()
}

fn check_matrix(what: &'static str, rows: &[Vec<Q>], m: usize, cols: usize) -> Result<()> {
    if rows.len() != m {
        return Err(GammaReconciliationError::DimensionMismatch {
            what,
            expected: m,
            actual: rows.len(),
        });
    }
    for row in rows {
        if row.len() != cols {
            return Err(GammaReconciliationError::DimensionMismatch {
                what,
                expected: cols,
                actual: row.len(),
            });
        }
        if row.iter().any(|x| !valid(x)) {
            return Err(GammaReconciliationError::InvalidRational);
        }
    }
    Ok(())
}

fn check_vector(what: &'static str, v: &[Q], len: usize) -> Result<()> {
    if v.len() != len {
        return Err(GammaReconciliationError::DimensionMismatch {
            what,
            expected: len,
            actual: v.len(),
        });
    }
    if v.iter().any(|x| !valid(x)) {
        return Err(GammaReconciliationError::InvalidRational);
    }
    Ok(())
}

fn apply(rows: &[Vec<Q>], v: &[Q]) -> Vec<Q> {
    rows.iter()
        .map(|row| row.iter().zip(v).map(|(a, b)| a * b).sum())
        .collect()
}

fn apply_transpose(rows: &[Vec<Q>], z: &[Q], cols: usize) -> Vec<Q> {
    (0..cols)
        .map(|j| rows.iter().zip(z).map(|(row, zi)| &row[j] * zi).sum())
        .collect()
}

fn dot(a: &[Q], b: &[Q]) -> Q {
    a.iter().zip(b).map(|(x, y)| x * y).sum()
}

/// A dual-certified value of `Gamma_quot(x)`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct QuotientGammaCertificate {
    pub x: Vec<Q>,
    pub u: Vec<Q>,
    pub residual: Vec<Q>,
    pub dual: Vec<Q>,
    pub value: Q,
}

/// Multipliers that certify one vertex system infeasible:
/// `upper, lower >= 0` and `upper - lower + A annihilator + D restriction = 0`
/// with `w . (upper + lower) + restriction . D^T (w ⊙ sign) < 0`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VertexFarkasCertificate {
    pub sign: Vec<i8>,
    pub upper: Vec<Q>,
    pub lower: Vec<Q>,
    pub annihilator: Vec<Q>,
    pub restriction: Vec<Q>,
}

/// `x` and `u` with `||D x + A u||_{1,w} < Gamma_raw(x)`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ValueGapWitness {
    pub x: Vec<Q>,
    pub u: Vec<Q>,
}

/// A complete table of vertex extensions, one per sign vector.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VertexExtensionTable {
    entries: BTreeMap<Vec<i8>, Vec<Q>>,
}

impl VertexExtensionTable {
    /// Refuses a repeated sign vector instead of keeping either entry.
    pub fn try_from_entries(entries: Vec<(Vec<i8>, Vec<Q>)>) -> Result<Self> {
        let mut map = BTreeMap::new();
        for (sign, z) in entries {
            if map.contains_key(&sign) {
                return Err(GammaReconciliationError::DuplicateVertex { sign });
            }
            map.insert(sign, z);
        }
        Ok(Self { entries: map })
    }

    pub fn entries(&self) -> &BTreeMap<Vec<i8>, Vec<Q>> {
        &self.entries
    }
}

/// All `2^m` sign vectors in lexicographic order of `{-1, 1}^m`.
pub fn all_sign_vectors(m: usize) -> Result<Vec<Vec<i8>>> {
    if m > MAX_VERTEX_ROWS {
        return Err(GammaReconciliationError::CarrierTooLarge {
            rows: m,
            limit: MAX_VERTEX_ROWS,
        });
    }
    let mut out = Vec::with_capacity(1usize << m);
    for mask in 0..(1usize << m) {
        out.push(
            (0..m)
                .map(|i| if mask >> (m - 1 - i) & 1 == 1 { 1 } else { -1 })
                .collect(),
        );
    }
    Ok(out)
}

/// The finite data `(D, A, w)` of the comparison.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RepairQuotientProblem {
    n: usize,
    k: usize,
    d: Vec<Vec<Q>>,
    a: Vec<Vec<Q>>,
    weights: Vec<Q>,
}

impl RepairQuotientProblem {
    /// `d` is `m x n`, `a` is `m x k`, `m = weights.len()`.
    pub fn try_new(
        n: usize,
        k: usize,
        d: Vec<Vec<Q>>,
        a: Vec<Vec<Q>>,
        weights: Vec<Q>,
    ) -> Result<Self> {
        let m = weights.len();
        check_vector("weights", &weights, m)?;
        if let Some(index) = weights.iter().position(|w| !w.is_positive()) {
            return Err(GammaReconciliationError::NonPositiveWeight { index });
        }
        check_matrix("D", &d, m, n)?;
        check_matrix("A", &a, m, k)?;
        Ok(Self {
            n,
            k,
            d,
            a,
            weights,
        })
    }

    pub fn rows(&self) -> usize {
        self.weights.len()
    }
    pub fn defect_dimension(&self) -> usize {
        self.n
    }
    pub fn repair_dimension(&self) -> usize {
        self.k
    }
    pub fn d(&self) -> &[Vec<Q>] {
        &self.d
    }
    pub fn a(&self) -> &[Vec<Q>] {
        &self.a
    }
    pub fn weights(&self) -> &[Q] {
        &self.weights
    }

    /// `||v||_{1,w}` for `v` in `Q^m`.
    pub fn weighted_norm(&self, v: &[Q]) -> Result<Q> {
        check_vector("vector in Q^m", v, self.rows())?;
        Ok(self.weights.iter().zip(v).map(|(w, x)| w * x.abs()).sum())
    }

    /// `D x`.
    pub fn defect(&self, x: &[Q]) -> Result<Vec<Q>> {
        check_vector("x", x, self.n)?;
        Ok(apply(&self.d, x))
    }

    /// `Gamma_raw(x)`.
    pub fn raw_gamma(&self, x: &[Q]) -> Result<Q> {
        let dx = self.defect(x)?;
        self.weighted_norm(&dx)
    }

    /// `||D x + A u||_{1,w}`, an upper bound for `Gamma_quot(x)`.
    pub fn residual_norm(&self, x: &[Q], u: &[Q]) -> Result<Q> {
        let dx = self.defect(x)?;
        check_vector("u", u, self.k)?;
        let au = apply(&self.a, u);
        let r: Vec<Q> = dx.iter().zip(&au).map(|(p, q)| p + q).collect();
        self.weighted_norm(&r)
    }

    fn check_dual(&self, z: &[Q]) -> Result<()> {
        check_vector("dual", z, self.rows())?;
        if let Some(index) = z
            .iter()
            .zip(&self.weights)
            .position(|(zi, wi)| &zi.abs() > wi)
        {
            return Err(GammaReconciliationError::DualOutOfBox { index });
        }
        let az = apply_transpose(&self.a, z, self.k);
        if let Some(column) = az.iter().position(|v| !v.is_zero()) {
            return Err(GammaReconciliationError::DualNotAnnihilating { column });
        }
        Ok(())
    }

    /// Checks residual, value and dual. A dual `z` in `K_w` gives, for every
    /// `u'`, `||D x + A u'||_{1,w} >= z . (D x + A u') = z . D x`, so a value
    /// equal to `z . D x` is the minimum.
    pub fn verify_quotient_certificate(&self, cert: &QuotientGammaCertificate) -> Result<Q> {
        let dx = self.defect(&cert.x)?;
        check_vector("u", &cert.u, self.k)?;
        check_vector("residual", &cert.residual, self.rows())?;
        let au = apply(&self.a, &cert.u);
        let expected: Vec<Q> = dx.iter().zip(&au).map(|(p, q)| p + q).collect();
        if expected != cert.residual {
            return Err(GammaReconciliationError::ResidualMismatch);
        }
        if !valid(&cert.value) || self.weighted_norm(&cert.residual)? != cert.value {
            return Err(GammaReconciliationError::ValueMismatch);
        }
        self.check_dual(&cert.dual)?;
        if dot(&cert.dual, &dx) != cert.value {
            return Err(GammaReconciliationError::DualPairingMismatch);
        }
        Ok(cert.value.clone())
    }

    fn check_sign(&self, sign: &[i8]) -> Result<()> {
        if sign.len() != self.rows() || sign.iter().any(|s| *s != 1 && *s != -1) {
            return Err(GammaReconciliationError::BadSign {
                sign: sign.to_vec(),
            });
        }
        Ok(())
    }

    /// `D^T (w ⊙ sign)`.
    pub fn vertex_target(&self, sign: &[i8]) -> Result<Vec<Q>> {
        self.check_sign(sign)?;
        let ws: Vec<Q> = self
            .weights
            .iter()
            .zip(sign)
            .map(|(w, s)| if *s == 1 { w.clone() } else { -w })
            .collect();
        Ok(apply_transpose(&self.d, &ws, self.n))
    }

    /// Checks one vertex extension `z` for `sign`.
    pub fn verify_vertex_extension(&self, sign: &[i8], z: &[Q]) -> Result<()> {
        let target = self.vertex_target(sign)?;
        let defect = |reason| GammaReconciliationError::VertexDefect {
            sign: sign.to_vec(),
            reason,
        };
        if z.len() != self.rows() || z.iter().any(|x| !valid(x)) {
            return Err(defect("length or rational form"));
        }
        if z.iter().zip(&self.weights).any(|(zi, wi)| &zi.abs() > wi) {
            return Err(defect("weight box"));
        }
        if apply_transpose(&self.a, z, self.k)
            .iter()
            .any(|v| !v.is_zero())
        {
            return Err(defect("annihilation of A"));
        }
        if apply_transpose(&self.d, z, self.n) != target {
            return Err(defect("restriction to D"));
        }
        Ok(())
    }

    /// Checks that the table has exactly the `2^m` sign vectors and that every
    /// entry is an extension. Success gives `Gamma_quot = Gamma_raw` at every
    /// `x`: with `σ` a sign vector of `D x`, `Gamma_raw(x) = z_σ . D x`, and
    /// `z_σ` in `K_w` bounds `Gamma_quot(x)` from below by the same number.
    pub fn verify_vertex_table(&self, table: &VertexExtensionTable) -> Result<()> {
        let signs = all_sign_vectors(self.rows())?;
        for sign in &signs {
            let z = table
                .entries
                .get(sign)
                .ok_or_else(|| GammaReconciliationError::MissingVertex { sign: sign.clone() })?;
            self.verify_vertex_extension(sign, z)?;
        }
        if table.entries.len() != signs.len() {
            let extra = table
                .entries
                .keys()
                .find(|s| self.check_sign(s).is_err())
                .cloned()
                .unwrap_or_default();
            return Err(GammaReconciliationError::BadSign { sign: extra });
        }
        Ok(())
    }

    fn verify_farkas_combination(&self, cert: &VertexFarkasCertificate, m: usize) -> Result<()> {
        let a_lambda = apply(&self.a, &cert.annihilator);
        let d_mu = apply(&self.d, &cert.restriction);
        for row in 0..m {
            let combined = &cert.upper[row] - &cert.lower[row] + &a_lambda[row] + &d_mu[row];
            if !combined.is_zero() {
                return Err(GammaReconciliationError::FarkasCombinationNonzero { row });
            }
        }
        Ok(())
    }

    /// Checks a Farkas certificate for one vertex and returns the separating
    /// pair `x = -restriction`, `u = -annihilator`. Then
    /// `D x = upper - lower + A annihilator`, so `D x + A u = upper - lower` and
    /// `||D x + A u||_{1,w} <= w . (upper + lower) < -restriction . target
    /// = x . target <= Gamma_raw(x)`. The gap is replayed before returning.
    pub fn verify_vertex_farkas(&self, cert: &VertexFarkasCertificate) -> Result<ValueGapWitness> {
        let target = self.vertex_target(&cert.sign)?;
        let m = self.rows();
        check_vector("upper multipliers", &cert.upper, m)?;
        check_vector("lower multipliers", &cert.lower, m)?;
        check_vector("annihilator multipliers", &cert.annihilator, self.k)?;
        check_vector("restriction multipliers", &cert.restriction, self.n)?;
        if let Some(index) = cert
            .upper
            .iter()
            .chain(&cert.lower)
            .position(|x| x.is_negative())
        {
            return Err(GammaReconciliationError::NegativeMultiplier { index });
        }
        self.verify_farkas_combination(cert, m)?;
        let capacity: Q = self
            .weights
            .iter()
            .zip(cert.upper.iter().zip(&cert.lower))
            .map(|(w, (p, q))| w * (p + q))
            .sum();
        if !(capacity + dot(&cert.restriction, &target)).is_negative() {
            return Err(GammaReconciliationError::FarkasBoundNotNegative);
        }
        let witness = ValueGapWitness {
            x: cert.restriction.iter().map(|v| -v).collect(),
            u: cert.annihilator.iter().map(|v| -v).collect(),
        };
        self.verify_value_gap(&witness)?;
        Ok(witness)
    }

    /// Checks `||D x + A u||_{1,w} < Gamma_raw(x)`; returns `(raw, upper bound)`.
    pub fn verify_value_gap(&self, witness: &ValueGapWitness) -> Result<(Q, Q)> {
        let raw = self.raw_gamma(&witness.x)?;
        let bound = self.residual_norm(&witness.x, &witness.u)?;
        if bound < raw {
            Ok((raw, bound))
        } else {
            Err(GammaReconciliationError::NoValueGap)
        }
    }

    /// Checks `D x + A u = 0` with `D x != 0`: `Gamma_quot(x) = 0 < Gamma_raw(x)`.
    pub fn verify_zero_test_gap(&self, witness: &ValueGapWitness) -> Result<Q> {
        let dx = self.defect(&witness.x)?;
        check_vector("u", &witness.u, self.k)?;
        let au = apply(&self.a, &witness.u);
        if dx.iter().all(Zero::is_zero) || dx.iter().zip(&au).any(|(p, q)| !(p + q).is_zero()) {
            return Err(GammaReconciliationError::NoZeroTestGap);
        }
        self.weighted_norm(&dx)
    }

    /// `D d0 = 0` (`d0` is `n x c`, row-wise): `Gamma_raw(x + d0 y) = Gamma_raw(x)`.
    pub fn verify_raw_descent(&self, d0: &[Vec<Q>], c: usize) -> Result<()> {
        check_matrix("d0", d0, self.n, c)?;
        for (row, d_row) in self.d.iter().enumerate() {
            for column in 0..c {
                let entry: Q = d_row.iter().zip(d0).map(|(a, b)| a * &b[column]).sum();
                if !entry.is_zero() {
                    return Err(GammaReconciliationError::NotRawDescent { row, column });
                }
            }
        }
        Ok(())
    }

    /// `D d0 = A g` (`g` is `k x c`): `D (x + d0 y) + A u = D x + A (u + g y)`,
    /// so `Gamma_quot(x + d0 y) = Gamma_quot(x)`.
    pub fn verify_quotient_descent(&self, d0: &[Vec<Q>], g: &[Vec<Q>], c: usize) -> Result<()> {
        check_matrix("d0", d0, self.n, c)?;
        check_matrix("G", g, self.k, c)?;
        for row in 0..self.rows() {
            for column in 0..c {
                let lhs: Q = self.d[row]
                    .iter()
                    .zip(d0)
                    .map(|(a, b)| a * &b[column])
                    .sum();
                let rhs: Q = self.a[row].iter().zip(g).map(|(a, b)| a * &b[column]).sum();
                if lhs != rhs {
                    return Err(GammaReconciliationError::NotQuotientDescent { row, column });
                }
            }
        }
        Ok(())
    }
}

// Origin: engine/crates_rs/core_functional/src/gamma_reconciliation.rs
// Claim: urn:core:crates_rs:core-functional:gamma-reconciliation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use num_bigint::BigInt;

    fn q(n: i64) -> Q {
        Q::from_integer(BigInt::from(n))
    }
    fn col(v: &[i64]) -> Vec<Vec<Q>> {
        v.iter().map(|x| vec![q(*x)]).collect()
    }

    /// D x = (x, x), A u = (u, 0), unit weights.
    fn duplicated() -> RepairQuotientProblem {
        RepairQuotientProblem::try_new(1, 1, col(&[1, 1]), col(&[1, 0]), vec![q(1), q(1)]).unwrap()
    }

    #[test]
    fn raw_two_quotient_one_with_dual_certificate() {
        let p = duplicated();
        assert_eq!(p.raw_gamma(&[q(1)]).unwrap(), q(2));
        let cert = QuotientGammaCertificate {
            x: vec![q(1)],
            u: vec![q(-1)],
            residual: vec![q(0), q(1)],
            dual: vec![q(0), q(1)],
            value: q(1),
        };
        assert_eq!(p.verify_quotient_certificate(&cert).unwrap(), q(1));
        // Tamper: a dual that does not annihilate A.
        let mut bad = cert.clone();
        bad.dual = vec![q(1), q(1)];
        assert_eq!(
            p.verify_quotient_certificate(&bad),
            Err(GammaReconciliationError::DualNotAnnihilating { column: 0 })
        );
        // Tamper: an understated value.
        let mut bad = cert.clone();
        bad.value = q(0);
        assert_eq!(
            p.verify_quotient_certificate(&bad),
            Err(GammaReconciliationError::ValueMismatch)
        );
        let mut bad = cert;
        bad.residual = vec![q(1), q(1)];
        assert_eq!(
            p.verify_quotient_certificate(&bad),
            Err(GammaReconciliationError::ResidualMismatch)
        );
    }

    #[test]
    fn weighted_variant_raw_five_quotient_three() {
        let p = RepairQuotientProblem::try_new(1, 1, col(&[1, 1]), col(&[1, 0]), vec![q(2), q(3)])
            .unwrap();
        assert_eq!(p.raw_gamma(&[q(1)]).unwrap(), q(5));
        let cert = QuotientGammaCertificate {
            x: vec![q(1)],
            u: vec![q(-1)],
            residual: vec![q(0), q(1)],
            dual: vec![q(0), q(3)],
            value: q(3),
        };
        assert_eq!(p.verify_quotient_certificate(&cert).unwrap(), q(3));
    }

    #[test]
    fn farkas_certificate_for_failed_vertex_builds_the_gap() {
        // Vertex (1, 1): z in K_w is (0, z2) with |z2| <= 1, and D^T z = z2
        // cannot reach 2. Multipliers: (0, 1) - 0 + A (1) + D (-1) = 0 and
        // w . (0, 1) + (-1) * 2 = -1 < 0.
        let p = duplicated();
        let cert = VertexFarkasCertificate {
            sign: vec![1, 1],
            upper: vec![q(0), q(1)],
            lower: vec![q(0), q(0)],
            annihilator: vec![q(1)],
            restriction: vec![q(-1)],
        };
        let gap = p.verify_vertex_farkas(&cert).unwrap();
        assert_eq!(gap.x, vec![q(1)]);
        assert_eq!(p.verify_value_gap(&gap).unwrap(), (q(2), q(1)));
        let mut bad = cert.clone();
        bad.upper = vec![q(0), q(2)];
        assert!(matches!(
            p.verify_vertex_farkas(&bad),
            Err(GammaReconciliationError::FarkasCombinationNonzero { .. })
        ));
        let mut bad = cert.clone();
        bad.lower = vec![q(-1), q(0)];
        assert!(matches!(
            p.verify_vertex_farkas(&bad),
            Err(GammaReconciliationError::NegativeMultiplier { .. })
        ));
        // The vertex (1, -1) has target 0 and z = 0 extends it; no
        // certificate for it can pass.
        let mut bad = cert;
        bad.sign = vec![1, -1];
        assert_eq!(
            p.verify_vertex_farkas(&bad),
            Err(GammaReconciliationError::FarkasBoundNotNegative)
        );
    }

    #[test]
    fn opposite_repair_has_complete_vertex_table() {
        // A u = (u, -u): K_w = {(t, t) : |t| <= 1}, D^T z = 2 t covers [-2, 2].
        let p = RepairQuotientProblem::try_new(1, 1, col(&[1, 1]), col(&[1, -1]), vec![q(1), q(1)])
            .unwrap();
        let entries = vec![
            (vec![-1, -1], vec![q(-1), q(-1)]),
            (vec![-1, 1], vec![q(0), q(0)]),
            (vec![1, -1], vec![q(0), q(0)]),
            (vec![1, 1], vec![q(1), q(1)]),
        ];
        let table = VertexExtensionTable::try_from_entries(entries.clone()).unwrap();
        assert!(p.verify_vertex_table(&table).is_ok());
        // Missing vertex.
        let partial = VertexExtensionTable::try_from_entries(entries[..3].to_vec()).unwrap();
        assert_eq!(
            p.verify_vertex_table(&partial),
            Err(GammaReconciliationError::MissingVertex { sign: vec![1, 1] })
        );
        // Tampered entry.
        let mut tampered = entries.clone();
        tampered[3].1 = vec![q(1), q(0)];
        let table = VertexExtensionTable::try_from_entries(tampered).unwrap();
        assert!(matches!(
            p.verify_vertex_table(&table),
            Err(GammaReconciliationError::VertexDefect { .. })
        ));
        // Duplicate and stray signs.
        let mut dup = entries.clone();
        dup.push((vec![1, 1], vec![q(1), q(1)]));
        assert!(matches!(
            VertexExtensionTable::try_from_entries(dup),
            Err(GammaReconciliationError::DuplicateVertex { .. })
        ));
        let mut stray = entries;
        stray.push((vec![0, 1], vec![q(0), q(0)]));
        let table = VertexExtensionTable::try_from_entries(stray).unwrap();
        assert!(matches!(
            p.verify_vertex_table(&table),
            Err(GammaReconciliationError::BadSign { .. })
        ));
    }

    #[test]
    fn zero_test_gap_and_descent_conditions() {
        // D = A = identity on Q^1: zero tests disagree at x = 1.
        let p = RepairQuotientProblem::try_new(1, 1, col(&[1]), col(&[1]), vec![q(1)]).unwrap();
        let w = ValueGapWitness {
            x: vec![q(1)],
            u: vec![q(-1)],
        };
        assert_eq!(p.verify_zero_test_gap(&w).unwrap(), q(1));
        let bad = ValueGapWitness {
            x: vec![q(0)],
            u: vec![q(0)],
        };
        assert_eq!(
            p.verify_zero_test_gap(&bad),
            Err(GammaReconciliationError::NoZeroTestGap)
        );
        // Descent: d0 = (1) is quotient descent with G = (1), not raw descent.
        assert!(p.verify_quotient_descent(&col(&[1]), &col(&[1]), 1).is_ok());
        assert_eq!(
            p.verify_raw_descent(&col(&[1]), 1),
            Err(GammaReconciliationError::NotRawDescent { row: 0, column: 0 })
        );
        assert!(p.verify_raw_descent(&col(&[0]), 1).is_ok());
        assert!(matches!(
            p.verify_quotient_descent(&col(&[1]), &col(&[2]), 1),
            Err(GammaReconciliationError::NotQuotientDescent { .. })
        ));
    }

    #[test]
    fn refusals_are_typed() {
        assert!(matches!(
            RepairQuotientProblem::try_new(1, 1, col(&[1, 1]), col(&[1, 0]), vec![q(1), q(0)]),
            Err(GammaReconciliationError::NonPositiveWeight { index: 1 })
        ));
        assert!(matches!(
            RepairQuotientProblem::try_new(2, 1, col(&[1, 1]), col(&[1, 0]), vec![q(1), q(1)]),
            Err(GammaReconciliationError::DimensionMismatch { .. })
        ));
        assert!(matches!(
            all_sign_vectors(MAX_VERTEX_ROWS + 1),
            Err(GammaReconciliationError::CarrierTooLarge { .. })
        ));
        assert_eq!(all_sign_vectors(0).unwrap(), vec![Vec::<i8>::new()]);
        let p = duplicated();
        assert!(matches!(
            p.raw_gamma(&[]),
            Err(GammaReconciliationError::DimensionMismatch { .. })
        ));
    }
}
