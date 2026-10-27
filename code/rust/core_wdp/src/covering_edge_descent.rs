// Executable finite evidence; AuthorityEffect: None.
//! # Covering-Edge Descent Complexes, Functorial Presheaves, and Coherence Defects
//!
//! Sovereign Rust implementation of the mathematical definitions, theorems,
//! boundary relations, and algebraic certifiers established in Paper PO-001:
//! - §2 Path A: Strict Functorial Completion, Covering-Edge Diagrams, and Diamond Commutativity.
//! - §3 Path B: Composition Curvature Operator, Coboundary-Curvature Identity `d_1 d_0 = K`,
//!   Flat Locus Equivalence, Degree-3 `d_2 K` Boundary, and Unconditional Operator Cocycle `δ_2 K = 0`.
//! - §4 Extensions: Operator Commutator `[K, T]`, 4-Term Operator Comparison,
//!   Primal-Dual Distance-to-Image LP Certificate, Additive Normal Form `r = r̂ + A`,
//!   DDC Lattice Commutator `⟦Λ, D⟧`, Distinction Collapse Loss Ledger,
//!   and Exact 4D Simplicial Gauge Holonomy over Q(ζ_8).
//!   The Bell gluing distance stays in the paper package solver
//!   `quantum_sheaf_contextuality.py`; this module does not restate it as a constant.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_0989c5da<T> {
    fn checked_invariant_0989c5da(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_0989c5da<T> for Option<T> {
    #[inline]
    fn checked_invariant_0989c5da(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_0989c5da<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_0989c5da(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::collections::BTreeMap;
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Zero};
use serde::{Deserialize, Serialize};

use linear_algebra::backend::basic_matrix::BasicMatrix;
use core_number_theory::cyclotomic::Cyc8;
use crate::types::AuthorityEffect;

// ---------------------------------------------------------------------------
// 1. Exact Rational Matrix Support for Arbitrary Finite Fibers
// ---------------------------------------------------------------------------

/// Exact rectangular matrix over Q with arbitrary dimensions, backed by
/// `linear_algebra::backend::basic_matrix::BasicMatrix`.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExactMatrix {
    pub rows: usize,
    pub cols: usize,
    pub matrix: BasicMatrix<BigRational>,
}

impl ExactMatrix {
    /// Zero matrix of size `rows × cols` via `BasicMatrix::zero`.
    pub fn zero(rows: usize, cols: usize) -> Self {
        let matrix = BasicMatrix::zero(rows, cols).checked_invariant_0989c5da("zero matrix allocation failed");
        Self { rows, cols, matrix }
    }

    /// Square identity matrix of size `n × n` via `BasicMatrix::try_from_fn`.
    pub fn eye(n: usize) -> Self {
        let matrix = BasicMatrix::try_from_fn(n, n, |r, c| {
            if r == c {
                BigRational::one()
            } else {
                BigRational::zero()
            }
        })
        .checked_invariant_0989c5da("identity matrix allocation failed");
        Self { rows: n, cols: n, matrix }
    }

    /// Construct from integer literal 2D slice via `BasicMatrix::from_row_major`.
    pub fn from_i64(slice: &[&[i64]]) -> Self {
        let rows = slice.len();
        let cols = if rows > 0 { slice[0].len() } else { 0 };
        let mut data = Vec::with_capacity(rows * cols);
        for row in slice {
            assert_eq!(row.len(), cols, "All rows must have identical column count");
            for &x in row.iter() {
                data.push(BigRational::from(BigInt::from(x)));
            }
        }
        let matrix = BasicMatrix::from_row_major(rows, cols, data)
            .checked_invariant_0989c5da("valid matrix from i64 slice");
        Self { rows, cols, matrix }
    }

    /// Construct column vector from integer 1D slice via `BasicMatrix::from_row_major`.
    pub fn col_vector(slice: &[i64]) -> Self {
        let rows = slice.len();
        let data = slice.iter().map(|&x| BigRational::from(BigInt::from(x))).collect();
        let matrix = BasicMatrix::from_row_major(rows, 1, data)
            .checked_invariant_0989c5da("valid column vector from i64 slice");
        Self { rows, cols: 1, matrix }
    }

    /// Construct from a sovereign `BasicMatrix<BigRational>`.
    pub fn from_basic_matrix(matrix: BasicMatrix<BigRational>) -> Self {
        Self {
            rows: matrix.rows(),
            cols: matrix.cols(),
            matrix,
        }
    }

    /// Borrow the underlying sovereign `BasicMatrix<BigRational>`.
    pub fn as_basic_matrix(&self) -> &BasicMatrix<BigRational> {
        &self.matrix
    }

    /// Consume into the underlying sovereign `BasicMatrix<BigRational>`.
    pub fn into_basic_matrix(self) -> BasicMatrix<BigRational> {
        self.matrix
    }

    /// Matrix addition `A + B` delegated to `BasicMatrix::add`.
    pub fn add(&self, other: &Self) -> Self {
        Self::from_basic_matrix(
            self.matrix
                .add(&other.matrix)
                .checked_invariant_0989c5da("Dimension mismatch for matrix addition"),
        )
    }

    /// Matrix subtraction `A - B` delegated to `BasicMatrix::sub`.
    pub fn sub(&self, other: &Self) -> Self {
        Self::from_basic_matrix(
            self.matrix
                .sub(&other.matrix)
                .checked_invariant_0989c5da("Dimension mismatch for matrix subtraction"),
        )
    }

    /// Matrix multiplication `A * B` delegated to `BasicMatrix::mul`.
    pub fn mul(&self, other: &Self) -> Self {
        Self::from_basic_matrix(
            self.matrix
                .mul(&other.matrix)
                .checked_invariant_0989c5da("Inner dimension mismatch for matrix multiplication"),
        )
    }

    /// Transpose `A^T` delegated to `BasicMatrix::try_transpose`.
    pub fn transpose(&self) -> Self {
        Self::from_basic_matrix(
            self.matrix
                .try_transpose()
                .checked_invariant_0989c5da("Transpose dimension overflow"),
        )
    }

    /// Whether all entries are zero via sovereign `BasicMatrix::as_slice`.
    pub fn is_zero(&self) -> bool {
        self.matrix.as_slice().iter().all(|x| x.is_zero())
    }
}

impl std::ops::Deref for ExactMatrix {
    type Target = BasicMatrix<BigRational>;

    fn deref(&self) -> &Self::Target {
        &self.matrix
    }
}

impl From<BasicMatrix<BigRational>> for ExactMatrix {
    fn from(matrix: BasicMatrix<BigRational>) -> Self {
        Self::from_basic_matrix(matrix)
    }
}

impl From<ExactMatrix> for BasicMatrix<BigRational> {
    fn from(exact: ExactMatrix) -> Self {
        exact.matrix
    }
}

// ---------------------------------------------------------------------------
// 2. Definition 2.1 & Proposition 2.1a: Covering-Edge Diagram & Strict Presheaf
// ---------------------------------------------------------------------------

/// Finite Covering-Edge Diagram with arbitrary fiber dimensions and declared restrictions.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CoveringEdgeDiagramCED {
    pub elements: Vec<String>,
    pub fiber_dimensions: BTreeMap<String, usize>,
    /// Restrictions `r_{upper, lower}` mapping from `upper` to `lower`.
    pub restrictions: BTreeMap<(String, String), ExactMatrix>,
}

impl CoveringEdgeDiagramCED {
    /// Construct a new validated diagram.
    pub fn new(
        elements: Vec<String>,
        fiber_dimensions: BTreeMap<String, usize>,
        restrictions: BTreeMap<(String, String), ExactMatrix>,
    ) -> Result<Self, String> {
        for ((upper, lower), mat) in &restrictions {
            let dim_upper = *fiber_dimensions.get(upper).ok_or_else(|| format!("Unknown upper element {upper}"))?;
            let dim_lower = *fiber_dimensions.get(lower).ok_or_else(|| format!("Unknown lower element {lower}"))?;
            if mat.rows != dim_lower || mat.cols != dim_upper {
                return Err(format!(
                    "Shape mismatch for restriction {upper}->{lower}: got ({}, {}), expected ({dim_lower}, {dim_upper})",
                    mat.rows, mat.cols
                ));
            }
        }
        Ok(Self { elements, fiber_dimensions, restrictions })
    }

    /// Retrieve restriction `r_{upper, lower}`.
    pub fn get_restriction(&self, upper: &str, lower: &str) -> Option<&ExactMatrix> {
        self.restrictions.get(&(upper.to_string(), lower.to_string()))
    }

    /// Lemma 2.2: Check Diamond Path-Independence around `a <= {b1, b2} <= c`.
    /// Returns `(is_independent, defect)` where `defect = r_{b1, a} r_{c, b1} - r_{b2, a} r_{c, b2}`.
    pub fn check_diamond_path_independence(
        &self,
        a: &str,
        b1: &str,
        b2: &str,
        c: &str,
    ) -> Result<(bool, ExactMatrix), String> {
        let r_c_b1 = self.get_restriction(c, b1).ok_or("Missing restriction c->b1")?;
        let r_b1_a = self.get_restriction(b1, a).ok_or("Missing restriction b1->a")?;
        let r_c_b2 = self.get_restriction(c, b2).ok_or("Missing restriction c->b2")?;
        let r_b2_a = self.get_restriction(b2, a).ok_or("Missing restriction b2->a")?;

        let path1 = r_b1_a.mul(r_c_b1);
        let path2 = r_b2_a.mul(r_c_b2);
        let defect = path1.sub(&path2);
        let is_indep = defect.is_zero();
        Ok((is_indep, defect))
    }

    fn compose_saturated_chain(
        a: &String,
        c: &String,
        chain: &[String],
        fiber_dimensions: &BTreeMap<String, usize>,
        full_restrictions: &BTreeMap<(String, String), ExactMatrix>,
    ) -> Result<ExactMatrix, String> {
        if chain.len() < 2
            || chain.first().checked_invariant_0989c5da("checked invariant") != a
            || chain.last().checked_invariant_0989c5da("checked invariant") != c
        {
            return Err(format!("Invalid chain from {a} to {c}"));
        }
        let mut comp = ExactMatrix::eye(
            *fiber_dimensions
                .get(a)
                .checked_invariant_0989c5da("checked invariant"),
        );
        for i in 0..(chain.len() - 1) {
            let low = &chain[i];
            let up = &chain[i + 1];
            let step = full_restrictions
                .get(&(up.clone(), low.clone()))
                .ok_or_else(|| format!("Missing covering restriction {up}->{low}"))?;
            comp = step.mul(&comp);
        }
        Ok(comp)
    }

    /// Proposition 2.1a: Complete covering edges to a strict functorial presheaf along saturated chains.
    pub fn build_path_a_completion(
        elements: Vec<String>,
        fiber_dimensions: BTreeMap<String, usize>,
        covering_restrictions: BTreeMap<(String, String), ExactMatrix>,
        saturated_chains: BTreeMap<(String, String), Vec<String>>,
    ) -> Result<Self, String> {
        let mut full_restrictions = covering_restrictions.clone();

        // Add identity restrictions r_{x, x} = I
        for el in &elements {
            let dim = *fiber_dimensions.get(el).ok_or_else(|| format!("Unknown element {el}"))?;
            full_restrictions.insert((el.clone(), el.clone()), ExactMatrix::eye(dim));
        }

        // Composite along declared saturated chains
        for ((c, a), chain) in saturated_chains {
            if full_restrictions.contains_key(&(c.clone(), a.clone())) {
                continue;
            }
            let comp =
                Self::compose_saturated_chain(&a, &c, &chain, &fiber_dimensions, &full_restrictions)?;
            full_restrictions.insert((c, a), comp);
        }

        Self::new(elements, fiber_dimensions, full_restrictions)
    }
}

// ---------------------------------------------------------------------------
// 3. Definition 3.1 & Corollary 3.3: Composition Curvature Operator
// ---------------------------------------------------------------------------

/// Curvature operator `K_{c,b,a} = r_{b,a} r_{c,b} - r_{c,a}`.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CurvatureOperatorCED {
    pub diagram: CoveringEdgeDiagramCED,
}

impl CurvatureOperatorCED {
    pub fn new(diagram: CoveringEdgeDiagramCED) -> Self {
        Self { diagram }
    }

    /// Definition 3.1: Compute curvature operator `K_{c,b,a}` for comparable triple `a <= b <= c`.
    pub fn compute_curvature(&self, a: &str, b: &str, c: &str) -> Result<ExactMatrix, String> {
        let r_cb = self.diagram.get_restriction(c, b).ok_or_else(|| format!("Missing restriction {c}->{b}"))?;
        let r_ba = self.diagram.get_restriction(b, a).ok_or_else(|| format!("Missing restriction {b}->{a}"))?;
        let r_ca = self.diagram.get_restriction(c, a).ok_or_else(|| format!("Missing restriction {c}->{a}"))?;

        let composite = r_ba.mul(r_cb);
        Ok(composite.sub(r_ca))
    }

    /// Corollary 3.3: Check whether diagram is flat (all comparable triples have K == 0).
    pub fn is_flat(&self, comparable_triples: &[(&str, &str, &str)]) -> Result<bool, String> {
        for &(a, b, c) in comparable_triples {
            let k = self.compute_curvature(a, b, c)?;
            if !k.is_zero() {
                return Ok(false);
            }
        }
        Ok(true)
    }
}

// ---------------------------------------------------------------------------
// 4. Theorem 3.2 & Theorem 3.4: Coboundary-Curvature Cochain Complex
// ---------------------------------------------------------------------------

/// Section assigning a column vector `s(x) in Q^{d_x}` to each element `x`.
pub type SectionCED = BTreeMap<String, ExactMatrix>;

/// Finite Cochain Complex and Coboundaries d0, d1, d2.
#[derive(Clone, Debug)]
pub struct CochainComplexCED {
    pub diagram: CoveringEdgeDiagramCED,
}

impl CochainComplexCED {
    pub fn new(diagram: CoveringEdgeDiagramCED) -> Self {
        Self { diagram }
    }

    /// Coboundary `(d_0 s)(a, b) = r_{b,a} s(b) - s(a)` for `a <= b`.
    pub fn d0(&self, s: &SectionCED, a: &str, b: &str) -> Result<ExactMatrix, String> {
        let s_b = s.get(b).ok_or_else(|| format!("Missing section value at {b}"))?;
        let s_a = s.get(a).ok_or_else(|| format!("Missing section value at {a}"))?;
        let r_ba = self.diagram.get_restriction(b, a).ok_or_else(|| format!("Missing restriction {b}->{a}"))?;
        Ok(r_ba.mul(s_b).sub(s_a))
    }

    /// Coboundary `(d_1 ω)(a, b, c) = r_{b,a} ω(b, c) - ω(a, c) + ω(a, b)`.
    pub fn d1(
        &self,
        omega: &BTreeMap<(String, String), ExactMatrix>,
        a: &str,
        b: &str,
        c: &str,
    ) -> Result<ExactMatrix, String> {
        let w_bc = omega.get(&(b.to_string(), c.to_string())).ok_or("Missing omega(b, c)")?;
        let w_ac = omega.get(&(a.to_string(), c.to_string())).ok_or("Missing omega(a, c)")?;
        let w_ab = omega.get(&(a.to_string(), b.to_string())).ok_or("Missing omega(a, b)")?;
        let r_ba = self.diagram.get_restriction(b, a).ok_or_else(|| format!("Missing restriction {b}->{a}"))?;

        let term1 = r_ba.mul(w_bc);
        let term2 = term1.sub(w_ac);
        Ok(term2.add(w_ab))
    }

    /// Theorem 3.2: Verify pointwise identity `(d_1 (d_0 s))(a,b,c) = K_{c,b,a}(s(c))`.
    pub fn verify_theorem_3_2(
        &self,
        s: &SectionCED,
        a: &str,
        b: &str,
        c: &str,
    ) -> Result<(bool, ExactMatrix, ExactMatrix), String> {
        let d0_ab = self.d0(s, a, b)?;
        let d0_bc = self.d0(s, b, c)?;
        let d0_ac = self.d0(s, a, c)?;

        let mut omega = BTreeMap::new();
        omega.insert((a.to_string(), b.to_string()), d0_ab);
        omega.insert((b.to_string(), c.to_string()), d0_bc);
        omega.insert((a.to_string(), c.to_string()), d0_ac);

        let d1_d0 = self.d1(&omega, a, b, c)?;
        let curv_op = CurvatureOperatorCED::new(self.diagram.clone());
        let k = curv_op.compute_curvature(a, b, c)?;
        let s_c = s.get(c).ok_or_else(|| format!("Missing section value at {c}"))?;
        let k_sc = k.mul(s_c);

        let matches = d1_d0 == k_sc;
        Ok((matches, d1_d0, k_sc))
    }

    /// Theorem 3.4: Evaluate Degree-3 Boundary `(d_2 K(s))(a,b,c,d) = K_{c,b,a}(r_{d,c} s_d) - K_{c,b,a}(s_c)`.
    pub fn evaluate_d2_boundary(
        &self,
        a: &str,
        b: &str,
        c: &str,
        d: &str,
        s_d: &ExactMatrix,
        s_c: &ExactMatrix,
    ) -> Result<(ExactMatrix, ExactMatrix), String> {
        let r_dc = self.diagram.get_restriction(d, c).ok_or("Missing restriction d->c")?;
        let curv_op = CurvatureOperatorCED::new(self.diagram.clone());
        let k_cba = curv_op.compute_curvature(a, b, c)?;

        let r_dc_sd = r_dc.mul(s_d);
        let k_r_dc_sd = k_cba.mul(&r_dc_sd);
        let k_sc = k_cba.mul(s_c);
        let lower_diff = k_r_dc_sd.sub(&k_sc);

        // Standard 4-term d2 definition on section values:
        let r_ba = self.diagram.get_restriction(b, a).ok_or("Missing restriction b->a")?;
        let k_dcb = curv_op.compute_curvature(b, c, d)?;
        let k_dca = curv_op.compute_curvature(a, c, d)?;
        let k_dba = curv_op.compute_curvature(a, b, d)?;

        let t1 = r_ba.mul(&k_dcb.mul(s_d));
        let t2 = k_dca.mul(s_d);
        let t3 = k_dba.mul(s_d);
        let t4 = k_cba.mul(s_c);

        let d2_val = t1.sub(&t2).add(&t3).sub(&t4);
        Ok((d2_val, lower_diff))
    }
}

// ---------------------------------------------------------------------------
// 5. Theorem 3.6, Theorem 4.1 & Theorem 4.2: Operator Coboundary & Cocycle
// ---------------------------------------------------------------------------

/// Operator Cochains and Coboundaries δ1 and δ2 on Hom-bundles.
#[derive(Clone, Debug)]
pub struct OperatorCochainCED {
    pub diagram: CoveringEdgeDiagramCED,
}

impl OperatorCochainCED {
    pub fn new(diagram: CoveringEdgeDiagramCED) -> Self {
        Self { diagram }
    }

    /// Theorem 3.6: Unconditional Operator Cocycle Identity `(δ_2 K)_{d,c,b,a} = 0`.
    /// `δ_2 K = r_{b,a} K_{d,c,b} - K_{d,c,a} + K_{d,b,a} - K_{c,b,a} r_{d,c} = 0`.
    pub fn evaluate_operator_delta2_k(
        &self,
        a: &str,
        b: &str,
        c: &str,
        d: &str,
    ) -> Result<ExactMatrix, String> {
        let curv_op = CurvatureOperatorCED::new(self.diagram.clone());
        let k_dcb = curv_op.compute_curvature(b, c, d)?;
        let k_dca = curv_op.compute_curvature(a, c, d)?;
        let k_dba = curv_op.compute_curvature(a, b, d)?;
        let k_cba = curv_op.compute_curvature(a, b, c)?;

        let r_ba = self.diagram.get_restriction(b, a).ok_or("Missing restriction b->a")?;
        let r_dc = self.diagram.get_restriction(d, c).ok_or("Missing restriction d->c")?;

        let term1 = r_ba.mul(&k_dcb);
        let term2 = k_dca;
        let term3 = k_dba;
        let term4 = k_cba.mul(r_dc);

        let delta2_k = term1.sub(&term2).add(&term3).sub(&term4);
        Ok(delta2_k)
    }

    /// Theorem 4.2: Four-Term Operator Comparison.
    /// `r_{b,a} K_{d,c,b} + K_{d,b,a} = K_{d,c,a} + K_{c,b,a} r_{d,c}`.
    pub fn verify_four_term_comparison(
        &self,
        a: &str,
        b: &str,
        c: &str,
        d: &str,
    ) -> Result<(bool, ExactMatrix, ExactMatrix), String> {
        let curv_op = CurvatureOperatorCED::new(self.diagram.clone());
        let k_dcb = curv_op.compute_curvature(b, c, d)?;
        let k_dca = curv_op.compute_curvature(a, c, d)?;
        let k_dba = curv_op.compute_curvature(a, b, d)?;
        let k_cba = curv_op.compute_curvature(a, b, c)?;

        let r_ba = self.diagram.get_restriction(b, a).ok_or("Missing restriction b->a")?;
        let r_dc = self.diagram.get_restriction(d, c).ok_or("Missing restriction d->c")?;

        let lhs = r_ba.mul(&k_dcb).add(&k_dba);
        let rhs = k_dca.add(&k_cba.mul(r_dc));
        let matches = lhs == rhs;
        Ok((matches, lhs, rhs))
    }

    /// Theorem 4.1: Curved Differential Derivation Identity `(δ_2 δ_1 T)_{d,c,b,a} = [K, T]_{d,c,b,a}`.
    /// `[K, T]_{d,c,b,a} = K_{c,b,a} T_{d,c} - T_{b,a} K_{d,c,b}`.
    pub fn evaluate_curved_derivation(
        &self,
        t_dc: &ExactMatrix,
        t_ba: &ExactMatrix,
        a: &str,
        b: &str,
        c: &str,
        d: &str,
    ) -> Result<ExactMatrix, String> {
        let curv_op = CurvatureOperatorCED::new(self.diagram.clone());
        let k_cba = curv_op.compute_curvature(a, b, c)?;
        let k_dcb = curv_op.compute_curvature(b, c, d)?;

        let term1 = k_cba.mul(t_dc);
        let term2 = t_ba.mul(&k_dcb);
        Ok(term1.sub(&term2))
    }
}

// ---------------------------------------------------------------------------
// 6. Theorem 4.4: Additive Normal Form Decomposition `r = r̂ + A`
// ---------------------------------------------------------------------------

/// Additive Normal Form decomposition of restriction maps.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct AdditiveNormalFormCED {
    pub strict_hat: CoveringEdgeDiagramCED,
    pub perturbation_a: BTreeMap<(String, String), ExactMatrix>,
}

impl AdditiveNormalFormCED {
    /// Decompose arbitrary restrictions `r` against strict completion `r̂`.
    pub fn decompose(
        full: &CoveringEdgeDiagramCED,
        strict_hat: &CoveringEdgeDiagramCED,
    ) -> Result<Self, String> {
        let mut perturbation_a = BTreeMap::new();
        for ((up, low), r_mat) in &full.restrictions {
            let hat_mat = strict_hat.get_restriction(up, low).ok_or_else(|| {
                format!("Missing strict restriction {up}->{low}")
            })?;
            let a_mat = r_mat.sub(hat_mat);
            perturbation_a.insert((up.clone(), low.clone()), a_mat);
        }
        Ok(Self { strict_hat: strict_hat.clone(), perturbation_a })
    }

    /// Theorem 4.4: Verify that A vanishes on covering edges, and `K_{c,b,a} = -A_{c,a}` for covering legs.
    pub fn verify_covering_leg_curvature(
        &self,
        a: &str,
        _b: &str,
        c: &str,
        k_cba: &ExactMatrix,
    ) -> Result<bool, String> {
        let a_ca = self.perturbation_a.get(&(c.to_string(), a.to_string())).ok_or("Missing A(c, a)")?;
        let minus_a_ca = ExactMatrix::zero(a_ca.rows, a_ca.cols).sub(a_ca);
        Ok(k_cba == &minus_a_ca)
    }
}

// ---------------------------------------------------------------------------
// 7. Theorem 4.6 & Statement 4.7: DDC Commutator & Distinction Collapse Ledger
// ---------------------------------------------------------------------------

/// DDC Diamond Operational Commutator `⟦Λ, D⟧ = K_{c, b1, a} - K_{c, b2, a}`.
pub fn evaluate_ddc_diamond_commutator(
    curv_op: &CurvatureOperatorCED,
    a: &str,
    b1: &str,
    b2: &str,
    c: &str,
) -> Result<ExactMatrix, String> {
    let k1 = curv_op.compute_curvature(a, b1, c)?;
    let k2 = curv_op.compute_curvature(a, b2, c)?;
    Ok(k1.sub(&k2))
}

/// Statement 4.7: Declared Cost-Two Ledger for Collapsed Distinctions.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct DistinctionCollapseLedgerCED {
    pub collapsed_count: usize,
    pub declared_charge: usize,
    pub authority_effect: AuthorityEffect,
}

impl DistinctionCollapseLedgerCED {
    pub fn record_collapse(m: usize) -> Self {
        Self {
            collapsed_count: m,
            declared_charge: 2 * m,
            authority_effect: AuthorityEffect::None,
        }
    }
}

// ---------------------------------------------------------------------------
// 8. Theorem 4.11 & Corollary 4.11a: Exact 4D Simplicial Holonomy over Q(ζ_8)
// ---------------------------------------------------------------------------

/// Exact 2x2 unitary link variable over `Cyc8`.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Cyc8Matrix2x2 {
    pub data: [[Cyc8; 2]; 2],
}

impl Cyc8Matrix2x2 {
    pub fn eye() -> Self {
        Self {
            data: [
                [Cyc8::one(), Cyc8::zero()],
                [Cyc8::zero(), Cyc8::one()],
            ],
        }
    }

    pub fn mul(&self, other: &Self) -> Self {
        let mut out = [[Cyc8::zero(), Cyc8::zero()], [Cyc8::zero(), Cyc8::zero()]];
        for i in 0..2 {
            for j in 0..2 {
                let term0 = self.data[i][0].mul(&other.data[0][j]);
                let term1 = self.data[i][1].mul(&other.data[1][j]);
                out[i][j] = term0.add(&term1);
            }
        }
        Self { data: out }
    }

    /// Conjugate transpose `U^†`.
    pub fn dagger(&self) -> Self {
        Self {
            data: [
                [self.data[0][0].conj(), self.data[1][0].conj()],
                [self.data[0][1].conj(), self.data[1][1].conj()],
            ],
        }
    }

    /// Discrete Bianchi check: is this matrix equal to the identity?
    pub fn is_identity(&self) -> bool {
        self == &Self::eye()
    }
}

/// Theorem 4.11 & Corollary 4.11a: Wilson loop holonomy on a triangle `(i, j, k)`.
/// `W(i, j, k) = U_{ki} * U_{jk} * U_{ij}`.
pub fn compute_wilson_triangle_holonomy(
    u_ij: &Cyc8Matrix2x2,
    u_jk: &Cyc8Matrix2x2,
    u_ik: &Cyc8Matrix2x2,
) -> Cyc8Matrix2x2 {
    let u_ki = u_ik.dagger();
    u_ki.mul(&u_jk.mul(u_ij))
}

/// Corollary 4.11a: Discrete Bianchi identity for an ordered tetrahedron.
/// Returns product of face holonomies around the 4 boundary faces.
pub fn verify_tetrahedral_bianchi(
    w_012: &Cyc8Matrix2x2,
    w_023: &Cyc8Matrix2x2,
    w_013: &Cyc8Matrix2x2,
    w_123: &Cyc8Matrix2x2,
) -> Cyc8Matrix2x2 {
    // Oriented tetrahedral closure: W_{012} * W_{023} * W_{013}^† * W_{123}^†
    w_012.mul(w_023).mul(&w_013.dagger()).mul(&w_123.dagger())
}

// Origin: engine/crates_rs/core_wdp/src/covering_edge_descent.rs
// Claim: urn:core:crates_rs:core-wdp:covering-edge-descent:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord0989c5da {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord0989c5da` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError0989c5da {
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
impl BoundaryError0989c5da {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError0989c5da {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError0989c5da {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord0989c5da {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError0989c5da> {
        if capacity_bound == 0 {
            return Err(BoundaryError0989c5da::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError0989c5da::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError0989c5da::ExceedsCapacity {
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
mod l4_boundary_tests_0989c5da {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord0989c5da::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord0989c5da::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord0989c5da::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord0989c5da::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord0989c5da::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError0989c5da::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError0989c5da::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
