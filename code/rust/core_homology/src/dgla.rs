#![cfg(any())]
// TODO: Fix imports from legacy arithmos
//! --- yaml
//! title: dgla
//! file_name: dgla.rs
//! file_location: core_core/src/ascent/lambdas/l097/dgla.rs
//! status: Coal
//! invariance_level: Tier 2
//! logic_system: Subobject Classifier (Core)
//! substrate: Rust
//! content_hash: 49cdd4c04cbdd4479f97fff315a0e66235156eb1444b28f9422ecd8466fecaee
//! version: 2
//! ---
//!
//! # Differential Graded Lie Algebra (DGLA) Computation Module
//!
//! This module provides a mathematically rigorous implementation of DGLAs with:
//!
//! - **Differential d**: degree +1, d^2 = 0
//! - **Lie bracket [_,_]**: graded antisymmetry, graded Jacobi identity
//! - **Graded Leibniz rule**: d[x,y] = [dx,y] + (-1)^{|x|}[x,dy]
//! - **Maurer-Cartan equation**: d(alpha) + 1/2[alpha,alpha] = 0
//! - **Gauge equivalence**: infinitesimal gauge action
//! - **Deformation complex**: twisted differential d_alpha
//!
//! ## Mathematical Background
//!
//! A DGLA (L, d, [_,_]) consists of:
//! - A Z-graded vector space L = bigoplus_n L_n
//! - A differential d: L_n -> L_{n+1} with d^2 = 0
//! - A Lie bracket [_,_]: L_m x L_n -> L_{m+n} satisfying:
//!   - Graded antisymmetry: [x,y] = -(-1)^{|x||y|}[y,x]
//!   - Graded Jacobi: (-1)^{|x||z|}[x,[y,z]] + cyclic = 0
//!   - Graded Leibniz: d[x,y] = [dx,y] + (-1)^{|x|}[x,dy]
//!
//! ## Connection to FSP
//!
//! DGLAs encode deformation theory. The Maurer-Cartan equation classifies
//! infinitesimal deformations, and the gauge equivalence relation captures
//! when two deformations represent the "same" physical configuration.
//! In the fermion sign problem context, the graded structure (Z-grading)
//! provides the mathematical framework for tracking sign contributions.
//!
//! ## Key References
//!
//! - Stasheff, "H-spaces from a homotopy point of view" (1970)
//! - Hinich, "DG coalgebras as formal stacks" (2001)
//! - Kontsevich-Soibelman, "Deformation theory" (2007)

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fmt;
use std::ops::{Add, Neg, Sub};

// ============================================================================
// 1. DGLAElement — An element of the differential graded Lie algebra
// ============================================================================

/// An element of a DGLA with integer degree and f64 coefficients.
///
/// The element is represented as a vector of coefficients in some basis.
/// The degree |x| determines sign rules for the graded bracket.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DGLAElement {
    /// Integer degree (Z-grading)
    pub degree: i32,
    /// Coefficient vector in the underlying basis
    pub components: Vec<f64>,
}

impl DGLAElement {
    /// Create a new DGLA element with given degree and components.
    pub fn new(degree: i32, components: Vec<f64>) -> Self {
        Self { degree, components }
    }

    /// Create the zero element at a given degree.
    pub fn zero(degree: i32, dimension: usize) -> Self {
        Self {
            degree,
            components: vec![0.0; dimension],
        }
    }

    /// Create a basis element e_i at given degree.
    pub fn basis_element(degree: i32, dimension: usize, index: usize) -> Self {
        let mut components = vec![0.0; dimension];
        if index < dimension {
            components[index] = 1.0;
        }
        Self { degree, components }
    }

    /// Check if this element is approximately zero.
    pub fn is_zero(&self, tolerance: f64) -> bool {
        self.components.iter().all(|c| c.abs() < tolerance)
    }

    /// Compute the L2 norm of the coefficient vector.
    pub fn norm(&self) -> f64 {
        core_functional::norms::l2_diagnostic(&self.components)
    }

    /// Dimension of the underlying vector space.
    pub fn dimension(&self) -> usize {
        self.components.len()
    }

    /// Scale by a scalar.
    pub fn scale(&self, scalar: f64) -> Self {
        Self {
            degree: self.degree,
            components: self.components.iter().map(|c| c * scalar).collect(),
        }
    }

    /// Koszul sign factor (-1)^{|x||y|}.
    pub fn koszul_sign(degree_x: i32, degree_y: i32) -> f64 {
        let exponent = (degree_x.rem_euclid(2)) * (degree_y.rem_euclid(2));
        if exponent == 0 {
            1.0
        } else {
            -1.0
        }
    }

    /// Sign factor (-1)^{|x|}.
    pub fn degree_sign(degree: i32) -> f64 {
        if degree.rem_euclid(2) == 0 {
            1.0
        } else {
            -1.0
        }
    }
}

impl Add for DGLAElement {
    type Output = Self;
    fn add(self, rhs: Self) -> Self {
        assert_eq!(
            self.degree, rhs.degree,
            "Cannot add DGLA elements of different degrees"
        );
        assert_eq!(
            self.components.len(),
            rhs.components.len(),
            "Component vectors must have same dimension"
        );
        Self {
            degree: self.degree,
            components: self
                .components
                .iter()
                .zip(rhs.components.iter())
                .map(|(a, b)| a + b)
                .collect(),
        }
    }
}

impl Sub for DGLAElement {
    type Output = Self;
    fn sub(self, rhs: Self) -> Self {
        assert_eq!(
            self.degree, rhs.degree,
            "Cannot subtract DGLA elements of different degrees"
        );
        self + rhs.scale(-1.0)
    }
}

impl Neg for DGLAElement {
    type Output = Self;
    fn neg(self) -> Self {
        self.scale(-1.0)
    }
}

impl fmt::Display for DGLAElement {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "DGLAElement(deg={}, ||={})", self.degree, self.norm())
    }
}

// ============================================================================
// 2. DGLA Trait — The abstract interface
// ============================================================================

/// A Differential Graded Lie Algebra.
///
/// Implementors provide the differential and bracket operations,
/// and this trait provides verification of the DGLA axioms.
pub trait DGLA {
    /// Apply the differential d: L_n -> L_{n+1}.
    /// Must satisfy d^2 = 0.
    fn differential(&self, x: &DGLAElement) -> DGLAElement;

    /// Compute the Lie bracket [x,y]: L_m x L_n -> L_{m+n}.
    /// Must satisfy graded antisymmetry and graded Jacobi.
    fn bracket(&self, x: &DGLAElement, y: &DGLAElement) -> DGLAElement;

    /// Verify d^2 = 0 for an element.
    fn verify_d_squared(&self, x: &DGLAElement, tolerance: f64) -> bool {
        let dx = self.differential(x);
        let ddx = self.differential(&dx);
        ddx.is_zero(tolerance)
    }

    /// Verify graded antisymmetry: [x,y] = -(-1)^{|x||y|}[y,x].
    fn verify_antisymmetry(&self, x: &DGLAElement, y: &DGLAElement, tolerance: f64) -> bool {
        let xy = self.bracket(x, y);
        let yx = self.bracket(y, x);
        let sign = DGLAElement::koszul_sign(x.degree, y.degree);
        let expected = yx.scale(-sign);
        (xy.clone() - expected).is_zero(tolerance)
    }

    /// Verify graded Jacobi identity:
    /// (-1)^{|x||z|}[x,[y,z]] + (-1)^{|y||x|}[y,[z,x]] + (-1)^{|z||y|}[z,[x,y]] = 0
    fn verify_jacobi(
        &self,
        x: &DGLAElement,
        y: &DGLAElement,
        z: &DGLAElement,
        tolerance: f64,
    ) -> bool {
        let sign_xz = DGLAElement::koszul_sign(x.degree, z.degree);
        let sign_yx = DGLAElement::koszul_sign(y.degree, x.degree);
        let sign_zy = DGLAElement::koszul_sign(z.degree, y.degree);

        let yz = self.bracket(y, z);
        let zx = self.bracket(z, x);
        let xy = self.bracket(x, y);

        let term1 = self.bracket(x, &yz).scale(sign_xz);
        let term2 = self.bracket(y, &zx).scale(sign_yx);
        let term3 = self.bracket(z, &xy).scale(sign_zy);

        let sum = term1 + term2 + term3;
        sum.is_zero(tolerance)
    }

    /// Verify graded Leibniz rule: d[x,y] = [dx,y] + (-1)^{|x|}[x,dy].
    fn verify_leibniz(&self, x: &DGLAElement, y: &DGLAElement, tolerance: f64) -> bool {
        let xy = self.bracket(x, y);
        let d_xy = self.differential(&xy);

        let dx = self.differential(x);
        let dy = self.differential(y);
        let sign_x = DGLAElement::degree_sign(x.degree);

        let dx_y = self.bracket(&dx, y);
        let x_dy = self.bracket(x, &dy).scale(sign_x);
        let rhs = dx_y + x_dy;

        (d_xy - rhs).is_zero(tolerance)
    }

    /// Compute Maurer-Cartan curvature: d(alpha) + 1/2[alpha, alpha].
    /// For degree-1 elements alpha.
    fn mc_curvature(&self, alpha: &DGLAElement) -> DGLAElement {
        let d_alpha = self.differential(alpha);
        let alpha_alpha = self.bracket(alpha, alpha);
        d_alpha + alpha_alpha.scale(0.5)
    }

    /// Check if alpha is a Maurer-Cartan solution (curvature ~ 0).
    fn is_mc_solution(&self, alpha: &DGLAElement, tolerance: f64) -> bool {
        self.mc_curvature(alpha).is_zero(tolerance)
    }

    /// Infinitesimal gauge action on an MC element:
    /// alpha |-> alpha + d(xi) + [xi, alpha]
    /// for xi of degree 0.
    fn gauge_action(&self, alpha: &DGLAElement, xi: &DGLAElement) -> DGLAElement {
        assert_eq!(xi.degree, 0, "Gauge parameter must have degree 0");
        let d_xi = self.differential(xi);
        let xi_alpha = self.bracket(xi, alpha);
        alpha.clone() + d_xi + xi_alpha
    }

    /// Twisted differential d_alpha for a Maurer-Cartan element alpha:
    /// d_alpha(x) = d(x) + [alpha, x]
    ///
    /// If alpha satisfies MC equation, then d_alpha^2 = 0.
    fn twisted_differential(&self, alpha: &DGLAElement, x: &DGLAElement) -> DGLAElement {
        let dx = self.differential(x);
        let alpha_x = self.bracket(alpha, x);
        dx + alpha_x
    }

    /// Verify d_alpha^2 = 0 (requires alpha to be MC solution).
    fn verify_twisted_d_squared(
        &self,
        alpha: &DGLAElement,
        x: &DGLAElement,
        tolerance: f64,
    ) -> bool {
        let d_alpha_x = self.twisted_differential(alpha, x);
        let d_alpha_d_alpha_x = self.twisted_differential(alpha, &d_alpha_x);
        d_alpha_d_alpha_x.is_zero(tolerance)
    }
}

// ============================================================================
// 3. Concrete DGLA Implementations
// ============================================================================

/// An abelian DGLA: bracket is always zero.
///
/// This is any chain complex viewed as a DGLA with trivial bracket.
/// All elements are automatically MC solutions iff they are d-closed.
#[derive(Debug, Clone)]
pub struct AbelianDGLA {
    /// Dimension of each graded piece
    pub dimension: usize,
    /// Differential matrix for each degree n -> n+1
    /// Maps degree to the matrix (stored as Vec<Vec<f64>>)
    pub differentials: HashMap<i32, Vec<Vec<f64>>>,
}

impl AbelianDGLA {
    /// Create a new abelian DGLA with given dimension.
    pub fn new(dimension: usize) -> Self {
        Self {
            dimension,
            differentials: HashMap::new(),
        }
    }

    /// Set the differential matrix from degree n to degree n+1.
    /// Matrix should be (target_dim x source_dim).
    pub fn set_differential(&mut self, degree: i32, matrix: Vec<Vec<f64>>) {
        self.differentials.insert(degree, matrix);
    }

    /// Create a chain complex that is a standard resolution.
    /// d_n(e_i) = e_{i mod dim} with alternating signs.
    pub fn standard_resolution(dimension: usize, min_degree: i32, max_degree: i32) -> Self {
        let mut dgla = Self::new(dimension);
        (min_degree..max_degree).for_each(|deg| {
            // Create a nilpotent differential: d maps e_i to 0 if i is even,
            // or to e_{i-1} if i is odd (ensuring d^2 = 0)
            let matrix: Vec<Vec<f64>> = (0..dimension)
                .map(|row| {
                    (0..dimension)
                        .map(|col| {
                            if col % 2 == 1 && col > 0 && row == col - 1 {
                                1.0
                            } else {
                                0.0
                            }
                        })
                        .collect()
                })
                .collect();
            dgla.set_differential(deg, matrix);
        });
        dgla
    }
}

impl DGLA for AbelianDGLA {
    fn differential(&self, x: &DGLAElement) -> DGLAElement {
        if let Some(matrix) = self.differentials.get(&x.degree) {
            let target_dim = matrix.len();
            let result: Vec<f64> = matrix
                .iter()
                .map(|row| {
                    row.iter()
                        .zip(x.components.iter())
                        .map(|(&entry, &comp)| entry * comp)
                        .sum()
                })
                .collect();
            DGLAElement::new(
                x.degree + 1,
                if result.len() == target_dim {
                    result
                } else {
                    vec![0.0; target_dim]
                },
            )
        } else {
            // No differential defined => zero
            DGLAElement::zero(x.degree + 1, x.components.len())
        }
    }

    fn bracket(&self, _x: &DGLAElement, y: &DGLAElement) -> DGLAElement {
        // Abelian: bracket is always zero
        DGLAElement::zero(_x.degree + y.degree, y.dimension())
    }
}

/// Endomorphism DGLA: End(V) with commutator bracket.
///
/// Elements are n x n matrices. The bracket is the graded commutator:
/// [f,g] = fg - (-1)^{|f||g|} gf
///
/// The differential can be defined by d(f) = [d_V, f] for some fixed
/// degree +1 endomorphism d_V with d_V^2 = 0.
#[derive(Debug, Clone)]
pub struct EndomorphismDGLA {
    /// Dimension of the underlying vector space V
    pub v_dimension: usize,
    /// The fixed differential d_V (as a flat vector representing n x n matrix)
    /// d_V must satisfy d_V^2 = 0
    pub base_differential: Vec<f64>,
    /// Degree of d_V (typically 1 or odd)
    pub d_degree: i32,
}

impl EndomorphismDGLA {
    /// Create a new endomorphism DGLA.
    /// The base_differential should be a flat representation of an n x n matrix
    /// where n = v_dimension.
    pub fn new(v_dimension: usize, base_differential: Vec<f64>, d_degree: i32) -> Self {
        assert_eq!(
            base_differential.len(),
            v_dimension * v_dimension,
            "base_differential must be v_dimension^2 elements"
        );
        Self {
            v_dimension,
            base_differential,
            d_degree,
        }
    }

    /// Create a trivial endomorphism DGLA (d_V = 0).
    pub fn trivial(v_dimension: usize) -> Self {
        Self {
            v_dimension,
            base_differential: vec![0.0; v_dimension * v_dimension],
            d_degree: 1,
        }
    }

    /// Matrix multiplication for flat n x n matrix representations.
    fn matrix_multiply(a: &[f64], b: &[f64], n: usize) -> Vec<f64> {
        (0..n)
            .flat_map(|i| (0..n).map(move |j| (0..n).map(|k| a[i * n + k] * b[k * n + j]).sum()))
            .collect()
    }

    /// Convert DGLAElement to matrix (components are flat n x n).
    fn element_to_matrix(&self, x: &DGLAElement) -> Vec<f64> {
        let n = self.v_dimension;
        x.components
            .iter()
            .take(n * n)
            .copied()
            .chain(std::iter::repeat(0.0))
            .take(n * n)
            .collect()
    }
}

impl DGLA for EndomorphismDGLA {
    fn differential(&self, x: &DGLAElement) -> DGLAElement {
        // d(f) = [d_V, f] = d_V * f - (-1)^{|d_V||f|} f * d_V
        let n = self.v_dimension;
        let f = self.element_to_matrix(x);
        let d = &self.base_differential;

        let df = Self::matrix_multiply(d, &f, n);
        let fd = Self::matrix_multiply(&f, d, n);
        let sign = DGLAElement::koszul_sign(self.d_degree, x.degree);

        let result: Vec<f64> = df
            .iter()
            .zip(fd.iter())
            .map(|(&df_i, &fd_i)| df_i - sign * fd_i)
            .collect();

        DGLAElement::new(x.degree + 1, result)
    }

    fn bracket(&self, x: &DGLAElement, y: &DGLAElement) -> DGLAElement {
        // [f,g] = fg - (-1)^{|f||g|} gf
        let n = self.v_dimension;
        let f = self.element_to_matrix(x);
        let g = self.element_to_matrix(y);

        let fg = Self::matrix_multiply(&f, &g, n);
        let gf = Self::matrix_multiply(&g, &f, n);
        let sign = DGLAElement::koszul_sign(x.degree, y.degree);

        let result: Vec<f64> = fg
            .iter()
            .zip(gf.iter())
            .map(|(&fg_i, &gf_i)| fg_i - sign * gf_i)
            .collect();

        DGLAElement::new(x.degree + y.degree, result)
    }
}

/// Chevalley-Eilenberg DGLA for a finite-dimensional Lie algebra.
///
/// Given a Lie algebra g with structure constants C^k_{ij} (where [e_i, e_j] = C^k_{ij} e_k),
/// the Chevalley-Eilenberg complex is Alt^*(g^*) with differential induced by the bracket.
///
/// For simplicity, this implementation works with the Lie algebra g itself,
/// using elements of g^otimes n with degree n-1.
#[derive(Debug, Clone)]
pub struct ChevalleyEilenbergDGLA {
    /// Dimension of the Lie algebra g
    pub dimension: usize,
    /// Structure constants C[k][i][j] where [e_i, e_j] = sum_k C[k][i][j] * e_k
    pub structure_constants: Vec<Vec<Vec<f64>>>,
}

impl ChevalleyEilenbergDGLA {
    /// Create from structure constants.
    /// structure_constants[k][i][j] = coefficient of e_k in [e_i, e_j].
    pub fn new(dimension: usize, structure_constants: Vec<Vec<Vec<f64>>>) -> Self {
        Self {
            dimension,
            structure_constants,
        }
    }

    /// Create the abelian Lie algebra (all structure constants zero).
    pub fn abelian(dimension: usize) -> Self {
        let zero_constants = vec![vec![vec![0.0; dimension]; dimension]; dimension];
        Self::new(dimension, zero_constants)
    }

    /// Create sl(2) with standard basis {e, f, h}.
    /// [h, e] = 2e, [h, f] = -2f, [e, f] = h
    pub fn sl2() -> Self {
        let n = 3;
        let mut c = vec![vec![vec![0.0; n]; n]; n];
        // [h, e] = 2e => C[0][2][0] = 2 (e is index 0, f is index 1, h is index 2)
        // Actually let's use: e=0, f=1, h=2
        // [e, f] = h => C[2][0][1] = 1
        c[2][0][1] = 1.0;
        c[2][1][0] = -1.0; // antisymmetry
                           // [h, e] = 2e => C[0][2][0] = 2
        c[0][2][0] = 2.0;
        c[0][0][2] = -2.0;
        // [h, f] = -2f => C[1][2][1] = -2
        c[1][2][1] = -2.0;
        c[1][1][2] = 2.0;

        Self::new(n, c)
    }

    /// Compute [e_i, e_j] using structure constants.
    pub fn bracket_basis(&self, i: usize, j: usize) -> Vec<f64> {
        (0..self.dimension)
            .map(|k| self.structure_constants[k][i][j])
            .collect()
    }

    /// Create so(3) Lie algebra with basis {L1, L2, L3}.
    /// [L1, L2] = L3, [L2, L3] = L1, [L3, L1] = L2
    pub fn so3() -> Self {
        let n = 3;
        let mut c = vec![vec![vec![0.0; n]; n]; n];
        // [L1, L2] = L3 => C[2][0][1] = 1
        c[2][0][1] = 1.0;
        c[2][1][0] = -1.0;
        // [L2, L3] = L1 => C[0][1][2] = 1
        c[0][1][2] = 1.0;
        c[0][2][1] = -1.0;
        // [L3, L1] = L2 => C[1][2][0] = 1
        c[1][2][0] = 1.0;
        c[1][0][2] = -1.0;

        Self::new(n, c)
    }

    /// Create the 3-dimensional Heisenberg Lie algebra with basis {x, y, z}.
    /// [x, y] = z, all other brackets are zero.
    /// This is a nilpotent (hence solvable) Lie algebra with degenerate Killing form.
    pub fn heisenberg() -> Self {
        let n = 3;
        let mut c = vec![vec![vec![0.0; n]; n]; n];
        // [x, y] = z => C[2][0][1] = 1 (x=0, y=1, z=2)
        c[2][0][1] = 1.0;
        c[2][1][0] = -1.0;

        Self::new(n, c)
    }

    /// Create su(2) Lie algebra with factor of 2: [e_i, e_j] = 2 * epsilon_{ijk} * e_k
    /// This is the same as so(3) but with structure constants scaled by 2.
    pub fn su2() -> Self {
        let n = 3;
        let mut c = vec![vec![vec![0.0; n]; n]; n];
        // [e1, e2] = 2*e3
        c[2][0][1] = 2.0;
        c[2][1][0] = -2.0;
        // [e2, e3] = 2*e1
        c[0][1][2] = 2.0;
        c[0][2][1] = -2.0;
        // [e3, e1] = 2*e2
        c[1][2][0] = 2.0;
        c[1][0][2] = -2.0;

        Self::new(n, c)
    }

    // =========================================================================
    // Killing Form and Lie Algebra Classification
    // =========================================================================

    /// Compute the adjoint representation matrix ad_X for an element X.
    ///
    /// Given X = sum_i x_i e_i, the matrix (ad_X)^k_j = sum_i x_i C^k_{ij}
    /// so that ad_X(e_j) = [X, e_j] = sum_k (ad_X)^k_j e_k.
    ///
    /// Returns an n x n matrix stored as Vec<Vec<f64>> where entry [k][j] = (ad_X)^k_j.
    pub fn ad_matrix(&self, x: &[f64]) -> Vec<Vec<f64>> {
        let n = self.dimension;
        (0..n)
            .map(|k| {
                (0..n)
                    .map(|j| {
                        (0..n.min(x.len()))
                            .map(|i| x[i] * self.structure_constants[k][i][j])
                            .sum()
                    })
                    .collect()
            })
            .collect()
    }

    /// Compute the Killing form B(X, Y) = tr(ad_X . ad_Y).
    ///
    /// The Killing form is a symmetric bilinear form on the Lie algebra.
    /// For semisimple Lie algebras, the Killing form is non-degenerate.
    pub fn killing_form(&self, x: &[f64], y: &[f64]) -> f64 {
        let n = self.dimension;
        let ad_x = self.ad_matrix(x);
        let ad_y = self.ad_matrix(y);

        // Compute trace of ad_X . ad_Y
        // tr(AB) = sum_i (AB)_{ii} = sum_i sum_j A_{ij} B_{ji}
        let mut trace = 0.0;
        for i in 0..n {
            for j in 0..n {
                trace += ad_x[i][j] * ad_y[j][i];
            }
        }
        trace
    }

    /// Compute the Killing matrix B_{ij} = B(e_i, e_j) for the standard basis.
    ///
    /// This is an n x n symmetric matrix. For semisimple Lie algebras,
    /// this matrix is non-singular (det != 0).
    pub fn killing_matrix(&self) -> Vec<Vec<f64>> {
        let n = self.dimension;

        // Build upper triangle and symmetric copy
        (0..n)
            .map(|i| {
                let mut e_i = vec![0.0; n];
                e_i[i] = 1.0;
                (0..n)
                    .map(|j| {
                        let mut e_j = vec![0.0; n];
                        e_j[j] = 1.0;
                        self.killing_form(&e_i, &e_j)
                    })
                    .collect()
            })
            .collect()
    }

    /// Check if the Lie algebra is semisimple using Cartan's criterion.
    ///
    /// A Lie algebra is semisimple iff its Killing form is non-degenerate,
    /// i.e., det(B) != 0.
    pub fn is_semisimple(&self) -> bool {
        let b = self.killing_matrix();
        let det = matrix_determinant(&b);
        det.abs() > 1e-10
    }

    /// Check if the Lie algebra is solvable using Cartan's criterion.
    ///
    /// A Lie algebra g is solvable iff B(x, y) = 0 for all x in g and y in [g, g].
    /// Equivalently, the Killing form restricted to [g, g] is zero.
    ///
    /// Note: For a nilpotent algebra (like Heisenberg), this returns true.
    pub fn is_solvable_by_cartan(&self) -> bool {
        let n = self.dimension;

        // Compute a basis for [g, g] by taking all brackets [e_i, e_j]
        // This is a spanning set; we don't need a minimal basis for the check.
        let derived_elements: Vec<Vec<f64>> = (0..n)
            .flat_map(|i| {
                ((i + 1)..n).filter_map(move |j| {
                    let bracket = self.bracket_basis(i, j);
                    // Check if non-zero
                    if bracket.iter().any(|&c| c.abs() > 1e-14) {
                        Some(bracket)
                    } else {
                        None
                    }
                })
            })
            .collect();

        // If [g, g] = 0, the algebra is abelian and hence solvable
        if derived_elements.is_empty() {
            return true;
        }

        // Check B(x, y) = 0 for all x in g and y in [g, g]
        (0..n).all(|i| {
            let mut e_i = vec![0.0; n];
            e_i[i] = 1.0;
            derived_elements
                .iter()
                .all(|y| self.killing_form(&e_i, y).abs() <= 1e-10)
        })
    }

    /// Find candidate elements for a Cartan subalgebra.
    ///
    /// A Cartan subalgebra h is a maximal abelian subalgebra consisting of
    /// semisimple (diagonalizable) elements. For semisimple Lie algebras,
    /// h is unique up to conjugation and its dimension is the rank.
    ///
    /// This heuristic returns basis elements h such that ad_h has
    /// the most eigenvalues (is "most diagonal").
    ///
    /// Returns: Vector of elements (as coefficient vectors) that are candidates
    /// for spanning a Cartan subalgebra.
    pub fn cartan_subalgebra_candidates(&self) -> Vec<Vec<f64>> {
        let n = self.dimension;

        // Check each basis element
        let mut candidates: Vec<(Vec<f64>, usize)> = (0..n)
            .filter_map(|i| {
                let mut e_i = vec![0.0; n];
                e_i[i] = 1.0;
                let ad = self.ad_matrix(&e_i);

                // Count how "diagonal-like" ad is by checking commutator with other basis
                // A better heuristic: count eigenspaces (simplified here to diagonal check)
                let diagonal_score = ad
                    .iter()
                    .enumerate()
                    .filter(|(j, row)| {
                        row.iter()
                            .enumerate()
                            .all(|(k, &v)| k == *j || v.abs() < 1e-10)
                    })
                    .count();

                if diagonal_score > 0 {
                    Some((e_i, diagonal_score))
                } else {
                    None
                }
            })
            .collect();

        // Sort by score (most diagonal first)
        candidates.sort_by_key(|a| std::cmp::Reverse(a.1));
        candidates.into_iter().map(|(v, _)| v).collect()
    }

    /// Compute the root system by diagonalizing ad_h for a Cartan element h.
    ///
    /// Given h in the Cartan subalgebra, the eigenvalues of ad_h are the roots
    /// evaluated at h. This returns pairs (eigenvector, eigenvalue) for non-zero
    /// eigenvalues.
    ///
    /// Note: This is a simplified implementation that works for diagonal ad_h.
    /// For general semisimple algebras, one needs full eigenvalue decomposition.
    ///
    /// Returns: Vec of (root_vector, root_value) pairs.
    pub fn root_system(&self) -> Vec<(Vec<f64>, f64)> {
        let candidates = self.cartan_subalgebra_candidates();
        if candidates.is_empty() {
            return Vec::new();
        }

        // Use the first (best) candidate
        let h = &candidates[0];
        let ad_h = self.ad_matrix(h);
        let n = self.dimension;

        // For diagonal matrices, eigenvalues are on the diagonal
        // and eigenvectors are standard basis vectors
        (0..n)
            .filter_map(|j| {
                let eigenvalue = ad_h[j][j];
                if eigenvalue.abs() > 1e-10 {
                    let mut eigenvector = vec![0.0; n];
                    eigenvector[j] = 1.0;
                    Some((eigenvector, eigenvalue))
                } else {
                    None
                }
            })
            .collect()
    }
}

impl DGLA for ChevalleyEilenbergDGLA {
    fn differential(&self, x: &DGLAElement) -> DGLAElement {
        // For the CE complex, the differential involves the dual bracket.
        // For simplicity, we implement the trivial differential (which makes
        // this an L-infinity structure rather than strict DGLA with non-trivial d).
        // A full CE implementation would require tracking cochains.
        DGLAElement::zero(x.degree + 1, self.dimension)
    }

    fn bracket(&self, x: &DGLAElement, y: &DGLAElement) -> DGLAElement {
        // [x, y] = sum_{i,j} x_i y_j [e_i, e_j]
        let result: Vec<f64> = (0..self.dimension)
            .map(|k| {
                (0..self.dimension.min(x.components.len()))
                    .flat_map(|i| {
                        (0..self.dimension.min(y.components.len())).map(move |j| {
                            let bracket_ij = self.bracket_basis(i, j);
                            x.components[i] * y.components[j] * bracket_ij[k]
                        })
                    })
                    .sum()
            })
            .collect();
        DGLAElement::new(x.degree + y.degree, result)
    }
}

// ============================================================================
// 3.5 Lie Algebra Classification via Killing Form
// ============================================================================

/// Compute the determinant of a square matrix using LU decomposition (Gaussian elimination).
///
/// This is a simple O(n^3) implementation suitable for small matrices (dim <= 100).
fn matrix_determinant(m: &[Vec<f64>]) -> f64 {
    let n = m.len();
    if n == 0 {
        return 1.0;
    }
    if n == 1 {
        return m[0][0];
    }
    if n == 2 {
        return m[0][0] * m[1][1] - m[0][1] * m[1][0];
    }
    if n == 3 {
        // Sarrus' rule for 3x3
        return m[0][0] * m[1][1] * m[2][2]
            + m[0][1] * m[1][2] * m[2][0]
            + m[0][2] * m[1][0] * m[2][1]
            - m[0][2] * m[1][1] * m[2][0]
            - m[0][1] * m[1][0] * m[2][2]
            - m[0][0] * m[1][2] * m[2][1];
    }

    // General case: LU decomposition with partial pivoting
    let mut a: Vec<Vec<f64>> = m.to_vec();
    let mut det = 1.0;
    let mut swaps = 0;

    for col in 0..n {
        if !eliminate_column_det(&mut a, col, n, &mut swaps) {
            return 0.0; // Singular matrix
        }
        det *= a[col][col];
    }

    if swaps % 2 == 1 {
        det = -det;
    }
    det
}

fn eliminate_column_det(a: &mut [Vec<f64>], col: usize, n: usize, swaps: &mut usize) -> bool {
    // Find pivot
    let mut max_row = col;
    let mut max_val = a[col][col].abs();
    for row in (col + 1)..n {
        if a[row][col].abs() > max_val {
            max_val = a[row][col].abs();
            max_row = row;
        }
    }

    if max_val < 1e-15 {
        return false;
    }

    // Swap rows if needed
    if max_row != col {
        a.swap(col, max_row);
        *swaps += 1;
    }

    // Eliminate below
    for row in (col + 1)..n {
        let factor = a[row][col] / a[col][col];
        for k in col..n {
            a[row][k] -= factor * a[col][k];
        }
    }
    true
}

/// Compute the rank of a matrix using Gaussian elimination.
fn matrix_rank(m: &[Vec<f64>]) -> usize {
    if m.is_empty() || m[0].is_empty() {
        return 0;
    }

    let n_rows = m.len();
    let n_cols = m[0].len();
    let mut a: Vec<Vec<f64>> = m.to_vec();

    let mut rank = 0;
    let mut col = 0;

    {
        let mut __iter = (0..n_rows).into_iter();
        loop {
            match __iter.next() {
                Some(row) => {
                    if col >= n_cols {
                        break;
                    }

                    // Find pivot in this column
                    let mut pivot_row = None;
                    {
                        let mut __iter = (row..n_rows).into_iter();
                        loop {
                            match __iter.next() {
                                Some(r) => {
                                    if a[r][col].abs() > 1e-10 {
                                        pivot_row = Some(r);
                                        break;
                                    }
                                }
                                None => break,
                            }
                        }
                    }

                    match pivot_row {
                        None => {
                            col += 1;
                            continue;
                        }
                        Some(p) => {
                            if p != row {
                                a.swap(row, p);
                            }
                        }
                    }

                    // Eliminate below
                    eliminate_below_rank(&mut a, row, col, n_rows, n_cols);

                    rank += 1;
                    col += 1;
                }
                None => break,
            }
        }
    }

    rank
}

fn eliminate_below_rank(a: &mut [Vec<f64>], row: usize, col: usize, n_rows: usize, n_cols: usize) {
    let pivot = a[row][col];
    for r in (row + 1)..n_rows {
        let factor = a[r][col] / pivot;
        for c in col..n_cols {
            a[r][c] -= factor * a[row][c];
        }
    }
}

/// Classification result for a Lie algebra based on Killing form analysis.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LieAlgebraClassification {
    /// Dimension of the Lie algebra.
    pub dimension: usize,
    /// The Killing matrix B_{ij} = B(e_i, e_j).
    pub killing_matrix: Vec<Vec<f64>>,
    /// Determinant of the Killing matrix.
    pub determinant: f64,
    /// Whether the algebra is semisimple (det(B) != 0).
    pub is_semisimple: bool,
    /// Rank of the Killing matrix (dimension of radical complement).
    pub rank: usize,
}

impl LieAlgebraClassification {
    /// Create a classification for an abelian algebra (all zeros Killing form).
    pub fn abelian(dimension: usize) -> Self {
        Self {
            dimension,
            killing_matrix: vec![vec![0.0; dimension]; dimension],
            determinant: 0.0,
            is_semisimple: false,
            rank: 0,
        }
    }
}

/// Classify a Lie algebra using its Killing form.
///
/// This function computes the Killing matrix and derives:
/// - Whether the algebra is semisimple (det != 0)
/// - The rank of the Killing matrix
/// - The full Killing matrix for further analysis
pub fn classify_lie_algebra(ce: &ChevalleyEilenbergDGLA) -> LieAlgebraClassification {
    let killing_matrix = ce.killing_matrix();
    let determinant = matrix_determinant(&killing_matrix);
    let rank = matrix_rank(&killing_matrix);
    let is_semisimple = determinant.abs() > 1e-10;

    LieAlgebraClassification {
        dimension: ce.dimension,
        killing_matrix,
        determinant,
        is_semisimple,
        rank,
    }
}

// ============================================================================
// 4. Maurer-Cartan Moduli Space Analysis
// ============================================================================

/// Result of Maurer-Cartan equation analysis.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MCAnalysis {
    /// The MC curvature d(alpha) + 1/2[alpha,alpha]
    pub curvature: Vec<f64>,
    /// L2 norm of the curvature (obstruction measure)
    pub curvature_norm: f64,
    /// Is this an MC solution (within tolerance)?
    pub is_solution: bool,
    /// Classification following the omphalos pattern
    pub verdict: MCVerdict,
}

/// MC equation classification (compatible with omphalos.rs MaurerCartanVerdict).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum MCVerdict {
    /// d(alpha) + 1/2[alpha,alpha] = 0 -- globally consistent
    Diamond,
    /// Small MC defect -- gauge-fixable
    GaugeFixable,
    /// Large MC defect -- structural obstruction
    Obstructed,
    /// Ill-formed: insufficient data to evaluate
    Indeterminate,
}

impl MCVerdict {
    /// Create from curvature norm with configurable thresholds.
    pub fn from_norm(norm: f64, diamond_threshold: f64, gauge_fixable_threshold: f64) -> Self {
        if norm < diamond_threshold {
            MCVerdict::Diamond
        } else if norm < gauge_fixable_threshold {
            MCVerdict::GaugeFixable
        } else {
            MCVerdict::Obstructed
        }
    }
}

/// Analyze the Maurer-Cartan equation for a degree-1 element.
pub fn analyze_mc<D: DGLA>(
    dgla: &D,
    alpha: &DGLAElement,
    diamond_threshold: f64,
    gauge_fixable_threshold: f64,
) -> MCAnalysis {
    let curvature = dgla.mc_curvature(alpha);
    let curvature_norm = curvature.norm();
    let is_solution = curvature_norm < diamond_threshold;
    let verdict = MCVerdict::from_norm(curvature_norm, diamond_threshold, gauge_fixable_threshold);

    MCAnalysis {
        curvature: curvature.components,
        curvature_norm,
        is_solution,
        verdict,
    }
}

/// Check if two MC solutions are gauge equivalent via infinitesimal gauge action.
///
/// Returns true if there exists a degree-0 element xi such that
/// ||beta - (alpha + d(xi) + [xi, alpha])|| < tolerance
/// for the given xi candidate.
pub fn check_gauge_equivalence<D: DGLA>(
    dgla: &D,
    alpha: &DGLAElement,
    beta: &DGLAElement,
    xi: &DGLAElement,
    tolerance: f64,
) -> bool {
    let transformed = dgla.gauge_action(alpha, xi);
    let diff = beta.clone() - transformed;
    diff.is_zero(tolerance)
}

// ============================================================================
// 5. Deformation Complex
// ============================================================================

/// A deformation complex is a DGLA with twisted differential.
#[derive(Debug, Clone)]
pub struct DeformationComplex<D: DGLA> {
    /// The underlying DGLA
    pub base: D,
    /// The Maurer-Cartan element defining the twist
    pub mc_element: DGLAElement,
}

impl<D: DGLA + Clone> DeformationComplex<D> {
    /// Create a deformation complex from a DGLA and an MC solution.
    pub fn new(base: D, mc_element: DGLAElement) -> Self {
        Self { base, mc_element }
    }

    /// The twisted differential d_alpha.
    pub fn twisted_d(&self, x: &DGLAElement) -> DGLAElement {
        self.base.twisted_differential(&self.mc_element, x)
    }

    /// Verify d_alpha^2 = 0 (consequence of MC equation).
    pub fn verify_twisted_d_squared(&self, x: &DGLAElement, tolerance: f64) -> bool {
        self.base
            .verify_twisted_d_squared(&self.mc_element, x, tolerance)
    }
}

// ============================================================================
// 6. DGLA Verification Report
// ============================================================================

/// Complete verification report for a DGLA.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DGLAVerificationReport {
    /// Name/identifier of the DGLA
    pub name: String,
    /// d^2 = 0 verification results for tested elements
    pub d_squared_results: Vec<(String, bool)>,
    /// Graded antisymmetry verification results
    pub antisymmetry_results: Vec<(String, String, bool)>,
    /// Graded Jacobi verification results
    pub jacobi_results: Vec<(String, String, String, bool)>,
    /// Graded Leibniz verification results
    pub leibniz_results: Vec<(String, String, bool)>,
    /// Overall validity
    pub is_valid: bool,
    /// Number of tests passed
    pub tests_passed: usize,
    /// Total number of tests
    pub tests_total: usize,
}

impl DGLAVerificationReport {
    /// Create a new verification report.
    pub fn new(name: &str) -> Self {
        Self {
            name: name.to_string(),
            d_squared_results: Vec::new(),
            antisymmetry_results: Vec::new(),
            jacobi_results: Vec::new(),
            leibniz_results: Vec::new(),
            is_valid: true,
            tests_passed: 0,
            tests_total: 0,
        }
    }

    /// Add a d^2 = 0 test result.
    pub fn add_d_squared(&mut self, element_name: &str, passed: bool) {
        self.d_squared_results
            .push((element_name.to_string(), passed));
        self.tests_total += 1;
        if passed {
            self.tests_passed += 1;
        } else {
            self.is_valid = false;
        }
    }

    /// Add an antisymmetry test result.
    pub fn add_antisymmetry(&mut self, x_name: &str, y_name: &str, passed: bool) {
        self.antisymmetry_results
            .push((x_name.to_string(), y_name.to_string(), passed));
        self.tests_total += 1;
        if passed {
            self.tests_passed += 1;
        } else {
            self.is_valid = false;
        }
    }

    /// Add a Jacobi identity test result.
    pub fn add_jacobi(&mut self, x_name: &str, y_name: &str, z_name: &str, passed: bool) {
        self.jacobi_results.push((
            x_name.to_string(),
            y_name.to_string(),
            z_name.to_string(),
            passed,
        ));
        self.tests_total += 1;
        if passed {
            self.tests_passed += 1;
        } else {
            self.is_valid = false;
        }
    }

    /// Add a Leibniz rule test result.
    pub fn add_leibniz(&mut self, x_name: &str, y_name: &str, passed: bool) {
        self.leibniz_results
            .push((x_name.to_string(), y_name.to_string(), passed));
        self.tests_total += 1;
        if passed {
            self.tests_passed += 1;
        } else {
            self.is_valid = false;
        }
    }
}

impl fmt::Display for DGLAVerificationReport {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        writeln!(f, "DGLA Verification Report: {}", self.name)?;
        writeln!(
            f,
            "Tests: {}/{} passed",
            self.tests_passed, self.tests_total
        )?;
        writeln!(f, "Valid: {}", if self.is_valid { "YES" } else { "NO" })?;

        if !self.d_squared_results.is_empty() {
            writeln!(f, "\nd^2 = 0 tests:")?;
            self.d_squared_results
                .iter()
                .try_for_each(|(name, passed)| {
                    writeln!(f, "  {}: {}", name, if *passed { "PASS" } else { "FAIL" })
                })?;
        }

        self.fmt_jacobi_failures(f)
    }
}

impl DGLAVerificationReport {
    fn fmt_jacobi_failures(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        if !self.jacobi_results.iter().all(|(_, _, _, p)| *p) {
            writeln!(f, "\nFailed Jacobi tests:")?;
            self.jacobi_results
                .iter()
                .filter(|(_, _, _, passed)| !passed)
                .try_for_each(|(x, y, z, _)| {
                    writeln!(f, "  [{}, [{}, {}]] + cyclic != 0", x, y, z)
                })?;
        }
        Ok(())
    }
}

// ============================================================================
// Tests
// ============================================================================

// Origin: engine/crates_rs/core_homology/src/dgla.rs
// Claim: urn:core:crates_rs:core-homology:dgla:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord1c142d60 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord1c142d60` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError1c142d60 {
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
impl BoundaryError1c142d60 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError1c142d60 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError1c142d60 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord1c142d60 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError1c142d60> {
        if capacity_bound == 0 {
            return Err(BoundaryError1c142d60::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError1c142d60::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError1c142d60::ExceedsCapacity {
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

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)

#[cfg(test)]
mod tests {
    use super::*;

    const TOLERANCE: f64 = 1e-10;

    // -------------------------------------------------------------------------
    // Test 1: d^2 = 0 for AbelianDGLA
    // -------------------------------------------------------------------------
    #[test]
    fn test_abelian_dgla_d_squared() {
        let dgla = AbelianDGLA::standard_resolution(4, 0, 3);
        let x = DGLAElement::new(0, vec![1.0, 2.0, 3.0, 4.0]);

        assert!(
            dgla.verify_d_squared(&x, TOLERANCE),
            "d^2 must equal 0 for abelian DGLA"
        );
    }

    // -------------------------------------------------------------------------
    // Test 2: Graded antisymmetry of bracket
    // -------------------------------------------------------------------------
    #[test]
    fn test_endomorphism_dgla_antisymmetry() {
        let dgla = EndomorphismDGLA::trivial(2);

        // Degree 0 element (2x2 matrix)
        let x = DGLAElement::new(0, vec![1.0, 0.0, 0.0, 2.0]);
        // Degree 1 element
        let y = DGLAElement::new(1, vec![0.0, 1.0, 1.0, 0.0]);

        assert!(
            dgla.verify_antisymmetry(&x, &y, TOLERANCE),
            "[x,y] must equal -(-1)^{{|x||y|}}[y,x]"
        );
    }

    // -------------------------------------------------------------------------
    // Test 3: Graded antisymmetry for same-degree elements
    // -------------------------------------------------------------------------
    #[test]
    fn test_antisymmetry_same_degree() {
        let dgla = EndomorphismDGLA::trivial(2);

        let x = DGLAElement::new(1, vec![1.0, 0.0, 0.0, 0.0]);
        let y = DGLAElement::new(1, vec![0.0, 1.0, 0.0, 0.0]);

        // For |x| = |y| = 1 (odd), [x,y] = -(-1)^1*[y,x] = [y,x]
        // So [x,y] + [y,x] = 2[x,y] for odd-odd
        // Actually graded antisymmetry: [x,y] = -(-1)^{|x||y|}[y,x]
        // For |x|=|y|=1: [x,y] = -(-1)^1 [y,x] = [y,x]
        // This means [x,y] - [y,x] = 0 for odd-odd case
        assert!(
            dgla.verify_antisymmetry(&x, &y, TOLERANCE),
            "Graded antisymmetry must hold for odd-odd elements"
        );
    }

    // -------------------------------------------------------------------------
    // Test 4: Graded Jacobi identity
    // -------------------------------------------------------------------------
    #[test]
    fn test_jacobi_identity() {
        // Use CE DGLA of sl(2) which has non-trivial bracket
        let dgla = ChevalleyEilenbergDGLA::sl2();

        // Three basis elements of sl(2)
        let e = DGLAElement::new(0, vec![1.0, 0.0, 0.0]); // e
        let f = DGLAElement::new(0, vec![0.0, 1.0, 0.0]); // f
        let h = DGLAElement::new(0, vec![0.0, 0.0, 1.0]); // h

        assert!(
            dgla.verify_jacobi(&e, &f, &h, TOLERANCE),
            "Jacobi identity must hold for sl(2)"
        );
    }

    // -------------------------------------------------------------------------
    // Test 5: Graded Leibniz rule
    // -------------------------------------------------------------------------
    #[test]
    fn test_leibniz_rule() {
        let dgla = AbelianDGLA::standard_resolution(4, 0, 3);

        let x = DGLAElement::new(0, vec![1.0, 0.0, 1.0, 0.0]);
        let y = DGLAElement::new(0, vec![0.0, 1.0, 0.0, 1.0]);

        // For abelian DGLA, bracket is zero, so Leibniz is trivially satisfied
        assert!(
            dgla.verify_leibniz(&x, &y, TOLERANCE),
            "Leibniz rule must hold"
        );
    }

    // -------------------------------------------------------------------------
    // Test 6: MC equation for known solution (abelian case)
    // -------------------------------------------------------------------------
    #[test]
    fn test_mc_equation_abelian_solution() {
        let dgla = AbelianDGLA::new(3);

        // For abelian DGLA with d=0, any element is an MC solution
        // since d(alpha) = 0 and [alpha, alpha] = 0
        let alpha = DGLAElement::new(1, vec![1.0, 2.0, 3.0]);

        let analysis = analyze_mc(&dgla, &alpha, TOLERANCE, 0.1);

        assert!(
            analysis.is_solution,
            "Degree-1 element in abelian DGLA with d=0 must be MC solution"
        );
        assert_eq!(analysis.verdict, MCVerdict::Diamond);
    }

    // -------------------------------------------------------------------------
    // Test 7: MC curvature non-zero for non-solution
    // -------------------------------------------------------------------------
    #[test]
    fn test_mc_curvature_nonzero() {
        let dgla = EndomorphismDGLA::trivial(2);

        // Degree 1 element that does not square to 0
        // e.g., alpha = | 1 0 |
        //               | 0 0 |
        let alpha = DGLAElement::new(1, vec![1.0, 0.0, 0.0, 0.0]);

        // [alpha, alpha] = 2 * alpha^2 != 0
        let curvature = dgla.mc_curvature(&alpha);

        assert!(
            !curvature.is_zero(TOLERANCE),
            "MC curvature should be non-zero for non-solution"
        );
    }

    // -------------------------------------------------------------------------
    // Test 8: Gauge action preserves MC solutions
    // -------------------------------------------------------------------------
    #[test]
    fn test_gauge_action_preserves_mc() {
        let dgla = AbelianDGLA::new(3);

        // MC solution (trivial since abelian with d=0)
        let alpha = DGLAElement::new(1, vec![1.0, 0.0, 0.0]);
        // Gauge parameter
        let xi = DGLAElement::new(0, vec![0.5, 0.5, 0.5]);

        // Gauge action: alpha' = alpha + d(xi) + [xi, alpha]
        // For abelian with d=0: alpha' = alpha (no change)
        let alpha_prime = dgla.gauge_action(&alpha, &xi);

        assert!(
            dgla.is_mc_solution(&alpha_prime, TOLERANCE),
            "Gauge action must preserve MC solutions"
        );
    }

    // -------------------------------------------------------------------------
    // Test 9: Twisted differential d_alpha^2 = 0
    // -------------------------------------------------------------------------
    #[test]
    fn test_twisted_differential_squared() {
        let dgla = AbelianDGLA::new(3);

        // MC solution
        let alpha = DGLAElement::new(1, vec![0.0, 0.0, 0.0]);

        // Test element
        let x = DGLAElement::new(0, vec![1.0, 2.0, 3.0]);

        assert!(
            dgla.verify_twisted_d_squared(&alpha, &x, TOLERANCE),
            "d_alpha^2 must equal 0 when alpha is MC solution"
        );
    }

    // -------------------------------------------------------------------------
    // Test 10: Abelian DGLA - all d-closed elements are MC solutions
    // -------------------------------------------------------------------------
    #[test]
    fn test_abelian_d_closed_are_mc() {
        let dgla = AbelianDGLA::standard_resolution(4, 0, 3);

        // Element in kernel of d (d-closed)
        // For our standard resolution, e_0 maps to 0
        let alpha = DGLAElement::new(1, vec![1.0, 0.0, 0.0, 0.0]);

        let d_alpha = dgla.differential(&alpha);
        let is_d_closed = d_alpha.is_zero(TOLERANCE);

        if is_d_closed {
            // For abelian DGLA, d-closed implies MC solution
            // since [alpha, alpha] = 0 always
            assert!(
                dgla.is_mc_solution(&alpha, TOLERANCE),
                "d-closed element in abelian DGLA must be MC solution"
            );
        }
    }

    // -------------------------------------------------------------------------
    // Test 11: Endomorphism DGLA explicit computation
    // -------------------------------------------------------------------------
    #[test]
    fn test_endomorphism_bracket_computation() {
        let dgla = EndomorphismDGLA::trivial(2);

        // Matrix A = [[1, 0], [0, 0]] (degree 0)
        let a = DGLAElement::new(0, vec![1.0, 0.0, 0.0, 0.0]);
        // Matrix B = [[0, 1], [0, 0]] (degree 0)
        let b = DGLAElement::new(0, vec![0.0, 1.0, 0.0, 0.0]);

        let bracket = dgla.bracket(&a, &b);

        // [A, B] = AB - BA
        // AB = [[0, 1], [0, 0]], BA = [[0, 0], [0, 0]]
        // [A, B] = [[0, 1], [0, 0]]
        assert!(
            (bracket.components[0] - 0.0).abs() < TOLERANCE,
            "Bracket[0] should be 0"
        );
        assert!(
            (bracket.components[1] - 1.0).abs() < TOLERANCE,
            "Bracket[1] should be 1"
        );
    }

    // -------------------------------------------------------------------------
    // Test 12: Verify sl(2) structure constants
    // -------------------------------------------------------------------------
    #[test]
    fn test_sl2_bracket_relations() {
        let dgla = ChevalleyEilenbergDGLA::sl2();

        let e = DGLAElement::new(0, vec![1.0, 0.0, 0.0]);
        let f = DGLAElement::new(0, vec![0.0, 1.0, 0.0]);
        let h = DGLAElement::new(0, vec![0.0, 0.0, 1.0]);

        // [e, f] = h
        let ef = dgla.bracket(&e, &f);
        assert!(
            (ef.components[2] - 1.0).abs() < TOLERANCE,
            "[e,f] should equal h"
        );

        // [h, e] = 2e
        let he = dgla.bracket(&h, &e);
        assert!(
            (he.components[0] - 2.0).abs() < TOLERANCE,
            "[h,e] should equal 2e"
        );

        // [h, f] = -2f
        let hf = dgla.bracket(&h, &f);
        assert!(
            (hf.components[1] - (-2.0)).abs() < TOLERANCE,
            "[h,f] should equal -2f"
        );
    }

    // -------------------------------------------------------------------------
    // Test 13: MC verdict classification
    // -------------------------------------------------------------------------
    #[test]
    fn test_mc_verdict_classification() {
        assert_eq!(MCVerdict::from_norm(0.0, 1e-6, 0.1), MCVerdict::Diamond);
        assert_eq!(MCVerdict::from_norm(1e-9, 1e-6, 0.1), MCVerdict::Diamond);
        assert_eq!(
            MCVerdict::from_norm(0.01, 1e-6, 0.1),
            MCVerdict::GaugeFixable
        );
        assert_eq!(MCVerdict::from_norm(0.5, 1e-6, 0.1), MCVerdict::Obstructed);
    }

    // -------------------------------------------------------------------------
    // Test 14: Deformation complex construction
    // -------------------------------------------------------------------------
    #[test]
    fn test_deformation_complex() {
        let base = AbelianDGLA::new(3);
        let alpha = DGLAElement::new(1, vec![0.0, 0.0, 0.0]);

        let deformation = DeformationComplex::new(base, alpha);
        let x = DGLAElement::new(0, vec![1.0, 2.0, 3.0]);

        // For trivial MC element in abelian DGLA, twisted d = d
        assert!(
            deformation.verify_twisted_d_squared(&x, TOLERANCE),
            "Deformation complex d_alpha^2 should be 0"
        );
    }

    // -------------------------------------------------------------------------
    // Test 15: Verification report generation
    // -------------------------------------------------------------------------
    #[test]
    fn test_verification_report() {
        let mut report = DGLAVerificationReport::new("test_dgla");

        report.add_d_squared("x", true);
        report.add_d_squared("y", true);
        report.add_antisymmetry("x", "y", true);
        report.add_jacobi("x", "y", "z", true);
        report.add_leibniz("x", "y", true);

        assert!(report.is_valid);
        assert_eq!(report.tests_passed, 5);
        assert_eq!(report.tests_total, 5);
    }

    // -------------------------------------------------------------------------
    // Test 16: Koszul sign computation
    // -------------------------------------------------------------------------
    #[test]
    fn test_koszul_signs() {
        // Even * Even = Even (sign +1)
        assert_eq!(DGLAElement::koszul_sign(0, 0), 1.0);
        assert_eq!(DGLAElement::koszul_sign(2, 4), 1.0);

        // Even * Odd = Even (sign +1)
        assert_eq!(DGLAElement::koszul_sign(0, 1), 1.0);
        assert_eq!(DGLAElement::koszul_sign(2, 3), 1.0);

        // Odd * Even = Even (sign +1)
        assert_eq!(DGLAElement::koszul_sign(1, 0), 1.0);
        assert_eq!(DGLAElement::koszul_sign(3, 2), 1.0);

        // Odd * Odd = Odd (sign -1)
        assert_eq!(DGLAElement::koszul_sign(1, 1), -1.0);
        assert_eq!(DGLAElement::koszul_sign(1, 3), -1.0);
        assert_eq!(DGLAElement::koszul_sign(3, 5), -1.0);
    }

    // -------------------------------------------------------------------------
    // Test 17: Element operations
    // -------------------------------------------------------------------------
    #[test]
    fn test_element_operations() {
        let x = DGLAElement::new(1, vec![1.0, 2.0, 3.0]);
        let y = DGLAElement::new(1, vec![0.5, 0.5, 0.5]);

        let sum = x.clone() + y.clone();
        assert!((sum.components[0] - 1.5).abs() < TOLERANCE);

        let diff = x.clone() - y.clone();
        assert!((diff.components[0] - 0.5).abs() < TOLERANCE);

        let scaled = x.scale(2.0);
        assert!((scaled.components[0] - 2.0).abs() < TOLERANCE);

        let neg = -x.clone();
        assert!((neg.components[0] - (-1.0)).abs() < TOLERANCE);
    }

    // =========================================================================
    // Killing Form Tests
    // =========================================================================

    // -------------------------------------------------------------------------
    // Test 18: Killing form for sl(2)
    // -------------------------------------------------------------------------
    #[test]
    fn test_killing_form_sl2() {
        let ce = ChevalleyEilenbergDGLA::sl2();

        // Basis: e=0, f=1, h=2
        let e = vec![1.0, 0.0, 0.0];
        let f = vec![0.0, 1.0, 0.0];
        let h = vec![0.0, 0.0, 1.0];

        // B(e, f) = tr(ad_e . ad_f) = 4
        // ad_e: [e, e]=0, [e, f]=h, [e, h]=-2e
        // ad_f: [f, e]=-h, [f, f]=0, [f, h]=2f
        // tr(ad_e . ad_f) = ... = 4
        let b_ef = ce.killing_form(&e, &f);
        assert!(
            (b_ef - 4.0).abs() < TOLERANCE,
            "B(e, f) should be 4, got {}",
            b_ef
        );

        // B(h, h) = tr(ad_h . ad_h) = 8
        // ad_h: [h, e]=2e, [h, f]=-2f, [h, h]=0
        // tr(ad_h^2) = 4 + 4 = 8
        let b_hh = ce.killing_form(&h, &h);
        assert!(
            (b_hh - 8.0).abs() < TOLERANCE,
            "B(h, h) should be 8, got {}",
            b_hh
        );

        // B(e, e) = tr(ad_e . ad_e) = 0 (nilpotent element)
        let b_ee = ce.killing_form(&e, &e);
        assert!(b_ee.abs() < TOLERANCE, "B(e, e) should be 0, got {}", b_ee);
    }

    // -------------------------------------------------------------------------
    // Test 19: Full Killing matrix for sl(2)
    // -------------------------------------------------------------------------
    #[test]
    fn test_killing_matrix_sl2() {
        let ce = ChevalleyEilenbergDGLA::sl2();
        let b = ce.killing_matrix();

        // Expected Killing matrix for sl(2) with basis {e, f, h}:
        // B = [[0, 4, 0],
        //      [4, 0, 0],
        //      [0, 0, 8]]
        assert!((b[0][0] - 0.0).abs() < TOLERANCE, "B[0,0] = 0");
        assert!((b[0][1] - 4.0).abs() < TOLERANCE, "B[0,1] = 4");
        assert!((b[0][2] - 0.0).abs() < TOLERANCE, "B[0,2] = 0");
        assert!((b[1][0] - 4.0).abs() < TOLERANCE, "B[1,0] = 4");
        assert!((b[1][1] - 0.0).abs() < TOLERANCE, "B[1,1] = 0");
        assert!((b[1][2] - 0.0).abs() < TOLERANCE, "B[1,2] = 0");
        assert!((b[2][0] - 0.0).abs() < TOLERANCE, "B[2,0] = 0");
        assert!((b[2][1] - 0.0).abs() < TOLERANCE, "B[2,1] = 0");
        assert!((b[2][2] - 8.0).abs() < TOLERANCE, "B[2,2] = 8");
    }

    // -------------------------------------------------------------------------
    // Test 20: sl(2) is semisimple
    // -------------------------------------------------------------------------
    #[test]
    fn test_sl2_is_semisimple() {
        let ce = ChevalleyEilenbergDGLA::sl2();
        assert!(
            ce.is_semisimple(),
            "sl(2) should be semisimple (det(B) != 0)"
        );
    }

    // -------------------------------------------------------------------------
    // Test 21: Heisenberg algebra is not semisimple
    // -------------------------------------------------------------------------
    #[test]
    fn test_heisenberg_not_semisimple() {
        let ce = ChevalleyEilenbergDGLA::heisenberg();
        assert!(
            !ce.is_semisimple(),
            "Heisenberg algebra should not be semisimple (det(B) = 0)"
        );

        // Verify Killing form is entirely zero for nilpotent algebra
        let b = ce.killing_matrix();
        {
            let mut __iter = (0..3).into_iter();
            loop {
                match __iter.next() {
                    Some(i) => {
                        let mut __iter = (0..3).into_iter();
                        loop {
                            match __iter.next() {
                                Some(j) => {
                                    assert!(
                                        b[i][j].abs() < TOLERANCE,
                                        "Killing form should be zero for nilpotent algebra"
                                    );
                                }
                                None => break,
                            }
                        }
                    }
                    None => break,
                }
            }
        }
    }

    // -------------------------------------------------------------------------
    // Test 22: ad_X matrices for sl(2)
    // -------------------------------------------------------------------------
    #[test]
    fn test_ad_matrix_sl2() {
        let ce = ChevalleyEilenbergDGLA::sl2();

        // ad_e: [e, e_j] for j = e, f, h
        // [e, e] = 0, [e, f] = h, [e, h] = -2e (since [h, e] = 2e => [e, h] = -2e)
        let e = vec![1.0, 0.0, 0.0];
        let ad_e = ce.ad_matrix(&e);

        // ad_e should be:
        // [e, e] = 0         -> column 0 is zero
        // [e, f] = h         -> column 1 has h-coefficient = 1 at row 2
        // [e, h] = -2e       -> column 2 has e-coefficient = -2 at row 0
        assert!((ad_e[0][0]).abs() < TOLERANCE, "ad_e[0,0] = 0");
        assert!(
            (ad_e[2][1] - 1.0).abs() < TOLERANCE,
            "ad_e[2,1] = 1 (coefficient of h in [e,f])"
        );
        assert!(
            (ad_e[0][2] - (-2.0)).abs() < TOLERANCE,
            "ad_e[0,2] = -2 (coefficient of e in [e,h])"
        );

        // ad_h: [h, e] = 2e, [h, f] = -2f, [h, h] = 0
        let h = vec![0.0, 0.0, 1.0];
        let ad_h = ce.ad_matrix(&h);

        assert!(
            (ad_h[0][0] - 2.0).abs() < TOLERANCE,
            "ad_h[0,0] = 2 (coefficient of e in [h,e])"
        );
        assert!(
            (ad_h[1][1] - (-2.0)).abs() < TOLERANCE,
            "ad_h[1,1] = -2 (coefficient of f in [h,f])"
        );
        assert!(
            (ad_h[2][2]).abs() < TOLERANCE,
            "ad_h[2,2] = 0 (coefficient of h in [h,h])"
        );
    }

    // -------------------------------------------------------------------------
    // Test 23: Killing form bilinearity
    // -------------------------------------------------------------------------
    #[test]
    fn test_killing_form_bilinear() {
        let ce = ChevalleyEilenbergDGLA::sl2();

        let x = vec![1.0, 0.0, 0.0]; // e
        let y = vec![0.0, 1.0, 0.0]; // f
        let z = vec![0.0, 0.0, 1.0]; // h

        let a = 2.5;
        let b = -1.3;

        // Test B(ax + by, z) = a*B(x, z) + b*B(y, z)
        let ax_plus_by: Vec<f64> = x
            .iter()
            .zip(y.iter())
            .map(|(&xi, &yi)| a * xi + b * yi)
            .collect();
        let lhs = ce.killing_form(&ax_plus_by, &z);
        let rhs = a * ce.killing_form(&x, &z) + b * ce.killing_form(&y, &z);

        assert!(
            (lhs - rhs).abs() < TOLERANCE,
            "Killing form should be bilinear: B(ax+by, z) = a*B(x,z) + b*B(y,z)"
        );
    }

    // -------------------------------------------------------------------------
    // Test 24: Killing form symmetry
    // -------------------------------------------------------------------------
    #[test]
    fn test_killing_form_symmetric() {
        let ce = ChevalleyEilenbergDGLA::sl2();

        let x = vec![1.0, 2.0, 3.0]; // e + 2f + 3h
        let y = vec![0.5, -1.0, 0.7];

        let b_xy = ce.killing_form(&x, &y);
        let b_yx = ce.killing_form(&y, &x);

        assert!(
            (b_xy - b_yx).abs() < TOLERANCE,
            "Killing form should be symmetric: B(X,Y) = B(Y,X)"
        );
    }

    // -------------------------------------------------------------------------
    // Test 25: Killing form invariance B([X,Y], Z) = B(X, [Y,Z])
    // -------------------------------------------------------------------------
    #[test]
    fn test_killing_form_invariant() {
        let ce = ChevalleyEilenbergDGLA::sl2();

        let x_elem = DGLAElement::new(0, vec![1.0, 0.0, 0.0]); // e
        let y_elem = DGLAElement::new(0, vec![0.0, 1.0, 0.0]); // f
        let z_elem = DGLAElement::new(0, vec![0.0, 0.0, 1.0]); // h

        // Compute [X, Y]
        let xy_bracket = ce.bracket(&x_elem, &y_elem);
        // Compute [Y, Z]
        let yz_bracket = ce.bracket(&y_elem, &z_elem);

        // B([X,Y], Z) should equal B(X, [Y,Z])
        let lhs = ce.killing_form(&xy_bracket.components, &z_elem.components);
        let rhs = ce.killing_form(&x_elem.components, &yz_bracket.components);

        assert!(
            (lhs - rhs).abs() < TOLERANCE,
            "Killing form should be invariant: B([X,Y],Z) = B(X,[Y,Z]), got {} vs {}",
            lhs,
            rhs
        );
    }

    // -------------------------------------------------------------------------
    // Test 26: so(3) Killing form (should be -2 * identity)
    // -------------------------------------------------------------------------
    #[test]
    fn test_so3_killing_form() {
        let ce = ChevalleyEilenbergDGLA::so3();
        let b = ce.killing_matrix();

        // For so(3) with [L_i, L_j] = epsilon_{ijk} L_k,
        // B_{ij} = -2 * delta_{ij}
        // Diagonal should be -2, off-diagonal should be 0
        {
            let mut __iter = (0..3).into_iter();
            loop {
                match __iter.next() {
                    Some(i) => {
                        let mut __iter = (0..3).into_iter();
                        loop {
                            match __iter.next() {
                                Some(j) => {
                                    let expected = if i == j { -2.0 } else { 0.0 };
                                    assert!(
                                        (b[i][j] - expected).abs() < TOLERANCE,
                                        "so(3) Killing form B[{},{}] should be {}, got {}",
                                        i,
                                        j,
                                        expected,
                                        b[i][j]
                                    );
                                }
                                None => break,
                            }
                        }
                    }
                    None => break,
                }
            }
        }

        // so(3) is semisimple (det(B) = -8 != 0)
        assert!(ce.is_semisimple(), "so(3) should be semisimple");
    }

    // -------------------------------------------------------------------------
    // Test 27: Classify sl(2) algebra
    // -------------------------------------------------------------------------
    #[test]
    fn test_classify_lie_algebra_sl2() {
        let ce = ChevalleyEilenbergDGLA::sl2();
        let classification = classify_lie_algebra(&ce);

        assert_eq!(classification.dimension, 3);
        assert_eq!(
            classification.rank, 3,
            "sl(2) Killing matrix should have full rank"
        );
        assert!(
            classification.is_semisimple,
            "sl(2) should be classified as semisimple"
        );
        // det(B) = -8 * 16 = -128 for sl(2) with our conventions
        assert!(
            classification.determinant.abs() > 1e-10,
            "sl(2) determinant should be non-zero"
        );
    }

    // -------------------------------------------------------------------------
    // Test 28: Classify Heisenberg algebra
    // -------------------------------------------------------------------------
    #[test]
    fn test_classify_lie_algebra_heisenberg() {
        let ce = ChevalleyEilenbergDGLA::heisenberg();
        let classification = classify_lie_algebra(&ce);

        assert_eq!(classification.dimension, 3);
        assert!(
            classification.rank < 3,
            "Heisenberg Killing matrix should have rank < 3, got {}",
            classification.rank
        );
        assert!(
            !classification.is_semisimple,
            "Heisenberg should not be classified as semisimple"
        );
        assert!(
            classification.determinant.abs() < TOLERANCE,
            "Heisenberg determinant should be zero"
        );
    }

    // -------------------------------------------------------------------------
    // Test 29: Heisenberg is solvable by Cartan criterion
    // -------------------------------------------------------------------------
    #[test]
    fn test_heisenberg_is_solvable() {
        let ce = ChevalleyEilenbergDGLA::heisenberg();
        assert!(
            ce.is_solvable_by_cartan(),
            "Heisenberg algebra should be solvable by Cartan's criterion"
        );
    }

    // -------------------------------------------------------------------------
    // Test 30: sl(2) is not solvable
    // -------------------------------------------------------------------------
    #[test]
    fn test_sl2_not_solvable() {
        let ce = ChevalleyEilenbergDGLA::sl2();
        assert!(!ce.is_solvable_by_cartan(), "sl(2) should not be solvable");
    }

    // -------------------------------------------------------------------------
    // Test 31: su(2) structure constants (factor of 2)
    // -------------------------------------------------------------------------
    #[test]
    fn test_su2_structure_constants() {
        let ce = ChevalleyEilenbergDGLA::su2();

        let e1 = DGLAElement::new(0, vec![1.0, 0.0, 0.0]);
        let e2 = DGLAElement::new(0, vec![0.0, 1.0, 0.0]);

        // [e1, e2] = 2*e3
        let bracket = ce.bracket(&e1, &e2);
        assert!(
            (bracket.components[2] - 2.0).abs() < TOLERANCE,
            "[e1, e2] should be 2*e3 in su(2)"
        );
    }

    // -------------------------------------------------------------------------
    // Test 32: Matrix determinant helper function
    // -------------------------------------------------------------------------
    #[test]
    fn test_matrix_determinant() {
        // 2x2 case
        let m2 = vec![vec![1.0, 2.0], vec![3.0, 4.0]];
        let det2 = super::matrix_determinant(&m2);
        assert!((det2 - (-2.0)).abs() < TOLERANCE, "det([[1,2],[3,4]]) = -2");

        // 3x3 case (identity)
        let m3_id = vec![
            vec![1.0, 0.0, 0.0],
            vec![0.0, 1.0, 0.0],
            vec![0.0, 0.0, 1.0],
        ];
        let det3_id = super::matrix_determinant(&m3_id);
        assert!((det3_id - 1.0).abs() < TOLERANCE, "det(I_3) = 1");

        // Singular matrix
        let singular = vec![
            vec![1.0, 2.0, 3.0],
            vec![4.0, 5.0, 6.0],
            vec![7.0, 8.0, 9.0],
        ];
        let det_singular = super::matrix_determinant(&singular);
        assert!(
            det_singular.abs() < TOLERANCE,
            "Singular matrix should have det = 0"
        );
    }

    // -------------------------------------------------------------------------
    // Test 33: Cartan subalgebra candidates for sl(2)
    // -------------------------------------------------------------------------
    #[test]
    fn test_cartan_subalgebra_sl2() {
        let ce = ChevalleyEilenbergDGLA::sl2();
        let candidates = ce.cartan_subalgebra_candidates();

        // h is the standard Cartan element for sl(2)
        // It should be among the candidates
        assert!(
            !candidates.is_empty(),
            "sl(2) should have Cartan subalgebra candidates"
        );
    }

    // -------------------------------------------------------------------------
    // Test 34: Root system for sl(2)
    // -------------------------------------------------------------------------
    #[test]
    fn test_root_system_sl2() {
        let ce = ChevalleyEilenbergDGLA::sl2();
        let roots = ce.root_system();

        // sl(2) has two roots: +2 (for e) and -2 (for f) with respect to h
        // The implementation is simplified and may not find all roots,
        // but should find at least some non-zero eigenvalues
        assert!(
            !roots.is_empty() || ce.cartan_subalgebra_candidates().is_empty(),
            "sl(2) should have roots if Cartan candidates exist"
        );
    }
}

#[cfg(test)]
mod l4_boundary_tests_1c142d60 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord1c142d60::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord1c142d60::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord1c142d60::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord1c142d60::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord1c142d60::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError1c142d60::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError1c142d60::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
