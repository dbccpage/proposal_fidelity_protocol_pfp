//! The numerical rail's arithmetic: complex `f64` matrices, Kronecker
//! products, partial traces over a multi-site tensor factorisation,
//! embedding of a local operator on arbitrary (possibly non-adjacent)
//! sites, and a Hermitian eigendecomposition by cyclic Jacobi rotations,
//! from which come `exp(−iHt)`, the trace norm, and the operator norm.
//!
//! This replaces NumPy's `eigh`, `svd`, `kron`, `trace`, `reshape` and
//! `transpose` for the finite quantum replays of §§5–6.  Its scope is
//! narrower than NumPy's on purpose: the norms are computed for Hermitian
//! inputs only — every matrix the paper's replays take a norm of is
//! Hermitian (reduced derivatives, projected tangents, defect operators,
//! density matrices, Hamiltonian terms) — and a non-Hermitian input is
//! refused rather than handled by a general SVD.
//!
//! Everything here is floating point.  It is a *numerical replay*, the
//! paper's own evidence kind for these claims, and no `Certificate` is
//! ever built from a float: the tolerances are printed next to the values.

use std::fmt;
use std::ops::{Add, Mul, Neg, Sub};

/// A complex number.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct C {
    /// Real part.
    pub re: f64,
    /// Imaginary part.
    pub im: f64,
}

impl C {
    /// Zero.
    pub const ZERO: C = C { re: 0.0, im: 0.0 };
    /// One.
    pub const ONE: C = C { re: 1.0, im: 0.0 };
    /// `i`.
    pub const I: C = C { re: 0.0, im: 1.0 };

    /// `re + i·im`.
    pub const fn new(re: f64, im: f64) -> C {
        C { re, im }
    }

    /// A real number.
    pub const fn real(re: f64) -> C {
        C { re, im: 0.0 }
    }

    /// Complex conjugate.
    pub fn conj(self) -> C {
        C { re: self.re, im: -self.im }
    }

    /// `|z|²`.
    pub fn abs2(self) -> f64 {
        self.re * self.re + self.im * self.im
    }

    /// `|z|`.
    pub fn abs(self) -> f64 {
        self.abs2().sqrt()
    }

    /// `e^{iθ}`.
    pub fn cis(theta: f64) -> C {
        C { re: theta.cos(), im: theta.sin() }
    }

    /// Scale by a real.
    pub fn scale(self, s: f64) -> C {
        C { re: self.re * s, im: self.im * s }
    }
}

impl Add for C {
    type Output = C;
    fn add(self, o: C) -> C {
        C { re: self.re + o.re, im: self.im + o.im }
    }
}

impl Sub for C {
    type Output = C;
    fn sub(self, o: C) -> C {
        C { re: self.re - o.re, im: self.im - o.im }
    }
}

impl Neg for C {
    type Output = C;
    fn neg(self) -> C {
        C { re: -self.re, im: -self.im }
    }
}

impl Mul for C {
    type Output = C;
    fn mul(self, o: C) -> C {
        C { re: self.re * o.re - self.im * o.im, im: self.re * o.im + self.im * o.re }
    }
}

impl fmt::Display for C {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "({:.6}{:+.6}i)", self.re, self.im)
    }
}

/// A dense complex matrix, row-major.
#[derive(Clone, Debug, PartialEq)]
pub struct CMatrix {
    /// Rows.
    pub rows: usize,
    /// Columns.
    pub cols: usize,
    /// Entries.
    pub data: Vec<C>,
}

impl CMatrix {
    /// Zeros.
    pub fn zeros(rows: usize, cols: usize) -> CMatrix {
        CMatrix { rows, cols, data: vec![C::ZERO; rows * cols] }
    }

    /// Identity.
    pub fn eye(n: usize) -> CMatrix {
        let mut m = CMatrix::zeros(n, n);
        for i in 0..n {
            m.set(i, i, C::ONE);
        }
        m
    }

    /// From rows of complex entries.
    pub fn from_rows(rows: &[&[C]]) -> CMatrix {
        let r = rows.len();
        let c = rows.first().map_or(0, |x| x.len());
        let mut data = Vec::with_capacity(r * c);
        for row in rows {
            assert_eq!(row.len(), c, "ragged matrix");
            data.extend_from_slice(row);
        }
        CMatrix { rows: r, cols: c, data }
    }

    /// From rows of real entries.
    pub fn from_real_rows(rows: &[&[f64]]) -> CMatrix {
        let r = rows.len();
        let c = rows.first().map_or(0, |x| x.len());
        let mut data = Vec::with_capacity(r * c);
        for row in rows {
            assert_eq!(row.len(), c, "ragged matrix");
            data.extend(row.iter().map(|&x| C::real(x)));
        }
        CMatrix { rows: r, cols: c, data }
    }

    /// The density matrix `|v⟩⟨v|` of a column vector.
    pub fn density(v: &[C]) -> CMatrix {
        let n = v.len();
        let mut m = CMatrix::zeros(n, n);
        for i in 0..n {
            for j in 0..n {
                m.set(i, j, v[i] * v[j].conj());
            }
        }
        m
    }

    /// Shape.
    pub fn shape(&self) -> (usize, usize) {
        (self.rows, self.cols)
    }

    /// Entry.
    pub fn get(&self, i: usize, j: usize) -> C {
        self.data[i * self.cols + j]
    }

    /// Set an entry.
    pub fn set(&mut self, i: usize, j: usize, v: C) {
        self.data[i * self.cols + j] = v;
    }

    /// Product.
    pub fn mul(&self, o: &CMatrix) -> CMatrix {
        assert_eq!(self.cols, o.rows, "shape mismatch in product");
        let mut out = CMatrix::zeros(self.rows, o.cols);
        for i in 0..self.rows {
            for k in 0..self.cols {
                let a = self.get(i, k);
                if a == C::ZERO {
                    continue;
                }
                for j in 0..o.cols {
                    let v = out.get(i, j) + a * o.get(k, j);
                    out.set(i, j, v);
                }
            }
        }
        out
    }

    /// Sum.
    pub fn add(&self, o: &CMatrix) -> CMatrix {
        assert_eq!(self.shape(), o.shape());
        CMatrix { rows: self.rows, cols: self.cols, data: self.data.iter().zip(&o.data).map(|(a, b)| *a + *b).collect() }
    }

    /// Difference.
    pub fn sub(&self, o: &CMatrix) -> CMatrix {
        assert_eq!(self.shape(), o.shape());
        CMatrix { rows: self.rows, cols: self.cols, data: self.data.iter().zip(&o.data).map(|(a, b)| *a - *b).collect() }
    }

    /// Scalar multiple.
    pub fn scale(&self, s: C) -> CMatrix {
        CMatrix { rows: self.rows, cols: self.cols, data: self.data.iter().map(|a| *a * s).collect() }
    }

    /// Real scalar multiple.
    pub fn scale_real(&self, s: f64) -> CMatrix {
        self.scale(C::real(s))
    }

    /// Conjugate transpose.
    pub fn adjoint(&self) -> CMatrix {
        let mut out = CMatrix::zeros(self.cols, self.rows);
        for i in 0..self.rows {
            for j in 0..self.cols {
                out.set(j, i, self.get(i, j).conj());
            }
        }
        out
    }

    /// Kronecker product, `self ⊗ o`.
    pub fn kron(&self, o: &CMatrix) -> CMatrix {
        let mut out = CMatrix::zeros(self.rows * o.rows, self.cols * o.cols);
        for i in 0..self.rows {
            for j in 0..self.cols {
                let a = self.get(i, j);
                for k in 0..o.rows {
                    for l in 0..o.cols {
                        out.set(i * o.rows + k, j * o.cols + l, a * o.get(k, l));
                    }
                }
            }
        }
        out
    }

    /// Trace.
    pub fn trace(&self) -> C {
        (0..self.rows.min(self.cols)).fold(C::ZERO, |a, i| a + self.get(i, i))
    }

    /// Frobenius norm.
    pub fn frobenius(&self) -> f64 {
        self.data.iter().map(|z| z.abs2()).sum::<f64>().sqrt()
    }

    /// `‖A − A†‖_F`.
    pub fn hermiticity_defect(&self) -> f64 {
        self.sub(&self.adjoint()).frobenius()
    }

    /// Whether `‖A − A†‖_F ≤ atol` entrywise-in-aggregate.
    pub fn is_hermitian(&self, atol: f64) -> bool {
        self.rows == self.cols && self.hermiticity_defect() <= atol
    }
}

/// The multi-index of a tensor index, most significant factor first.
pub fn decompose(mut index: usize, dims: &[usize]) -> Vec<usize> {
    let mut out = vec![0; dims.len()];
    for k in (0..dims.len()).rev() {
        out[k] = index % dims[k];
        index /= dims[k];
    }
    out
}

/// The tensor index of a multi-index.
pub fn compose(multi: &[usize], dims: &[usize]) -> usize {
    multi.iter().zip(dims).fold(0, |a, (&m, &d)| a * d + m)
}

/// Trace out every factor not in `keep`, returning the factors in the
/// order `keep` lists them.
pub fn partial_trace(m: &CMatrix, dims: &[usize], keep: &[usize]) -> CMatrix {
    let total: usize = dims.iter().product();
    assert_eq!(m.shape(), (total, total), "partial_trace: shape");
    let kept_dims: Vec<usize> = keep.iter().map(|&k| dims[k]).collect();
    let kept_total: usize = kept_dims.iter().product();
    let traced: Vec<usize> = (0..dims.len()).filter(|k| !keep.contains(k)).collect();
    let mut out = CMatrix::zeros(kept_total, kept_total);
    for i in 0..total {
        let mi = decompose(i, dims);
        for j in 0..total {
            let mj = decompose(j, dims);
            if traced.iter().any(|&k| mi[k] != mj[k]) {
                continue;
            }
            let a = compose(&keep.iter().map(|&k| mi[k]).collect::<Vec<_>>(), &kept_dims);
            let b = compose(&keep.iter().map(|&k| mj[k]).collect::<Vec<_>>(), &kept_dims);
            let v = out.get(a, b) + m.get(i, j);
            out.set(a, b, v);
        }
    }
    out
}

/// Embed an operator on the factors `support` (in that order) as
/// `op ⊗ identity` on the complement, in the global factor order.
pub fn embed(op: &CMatrix, support: &[usize], dims: &[usize]) -> CMatrix {
    let total: usize = dims.iter().product();
    let support_dims: Vec<usize> = support.iter().map(|&k| dims[k]).collect();
    let local: usize = support_dims.iter().product();
    assert_eq!(op.shape(), (local, local), "embed: operator shape");
    let complement: Vec<usize> = (0..dims.len()).filter(|k| !support.contains(k)).collect();
    let mut out = CMatrix::zeros(total, total);
    for i in 0..total {
        let mi = decompose(i, dims);
        for j in 0..total {
            let mj = decompose(j, dims);
            if complement.iter().any(|&k| mi[k] != mj[k]) {
                continue;
            }
            let a = compose(&support.iter().map(|&k| mi[k]).collect::<Vec<_>>(), &support_dims);
            let b = compose(&support.iter().map(|&k| mj[k]).collect::<Vec<_>>(), &support_dims);
            out.set(i, j, op.get(a, b));
        }
    }
    out
}

/// The result of a Hermitian eigendecomposition `A = V Λ V†`.
#[derive(Clone, Debug, PartialEq)]
pub struct HermitianEigen {
    /// Eigenvalues, in the order the Jacobi sweep left them.
    pub values: Vec<f64>,
    /// Eigenvectors as columns.
    pub vectors: CMatrix,
    /// `‖A V − V Λ‖_F`.
    pub residual: f64,
}

/// Cyclic Jacobi for a Hermitian matrix.  Refuses a non-Hermitian input.
pub fn hermitian_eigen(a0: &CMatrix, atol: f64) -> Result<HermitianEigen, String> {
    if a0.rows == 0 || a0.rows != a0.cols || a0.rows.checked_mul(a0.cols) != Some(a0.data.len())
        || !atol.is_finite() || atol < 0.0
        || a0.data.iter().any(|z| !z.re.is_finite() || !z.im.is_finite()) {
        return Err("eigensolver needs a nonempty finite square matrix and finite nonnegative tolerance".into());
    }
    if !a0.is_hermitian(atol) {
        return Err(format!("input is not Hermitian; Frobenius defect={}", a0.hermiticity_defect()));
    }
    let n = a0.rows;
    let mut a = a0.clone();
    let mut v = CMatrix::eye(n);
    let scale = 1.0 + a.frobenius();
    if !scale.is_finite() { return Err("eigensolver scale overflow".into()); }
    for _sweep in 0..200 {
        let mut off = 0.0;
        for p in 0..n {
            for q in p + 1..n {
                off += a.get(p, q).abs2();
            }
        }
        if off.sqrt() <= 1e-15 * scale {
            break;
        }
        for p in 0..n {
            for q in p + 1..n {
                let apq = a.get(p, q);
                let r = apq.abs();
                if r <= 1e-300 {
                    continue;
                }
                let phase = apq.scale(1.0 / r);
                let app = a.get(p, p).re;
                let aqq = a.get(q, q).re;
                let theta = (aqq - app) / (2.0 * r);
                let t = if theta >= 0.0 { 1.0 / (theta + (theta * theta + 1.0).sqrt()) } else { -1.0 / (-theta + (theta * theta + 1.0).sqrt()) };
                let c = 1.0 / (t * t + 1.0).sqrt();
                let s = t * c;
                // G = D·P on the (p, q) block: D = diag(1, e^{-iφ}), P = [[c, s], [-s, c]].
                let mut g = CMatrix::eye(n);
                g.set(p, p, C::real(c));
                g.set(p, q, C::real(s));
                g.set(q, p, C::real(-s) * phase.conj());
                g.set(q, q, C::real(c) * phase.conj());
                a = g.adjoint().mul(&a).mul(&g);
                v = v.mul(&g);
                // Keep the diagonal exactly real and the pivot exactly zero.
                a.set(p, q, C::ZERO);
                a.set(q, p, C::ZERO);
                let dp = a.get(p, p);
                a.set(p, p, C::real(dp.re));
                let dq = a.get(q, q);
                a.set(q, q, C::real(dq.re));
            }
        }
    }
    let values: Vec<f64> = (0..n).map(|i| a.get(i, i).re).collect();
    let mut lam = CMatrix::zeros(n, n);
    for (i, &val) in values.iter().enumerate() {
        lam.set(i, i, C::real(val));
    }
    let residual = a0.mul(&v).sub(&v.mul(&lam)).frobenius();
    if !residual.is_finite() || residual > atol.max(1e-14) * scale * (n as f64 + 1.0)
        || values.iter().any(|x| !x.is_finite()) {
        return Err("eigensolver failed its residual bound".into());
    }
    Ok(HermitianEigen { values, vectors: v, residual })
}

/// `Σ|λ|` of a Hermitian matrix — its trace norm.
pub fn trace_norm_hermitian(a: &CMatrix, atol: f64) -> Result<f64, String> {
    Ok(hermitian_eigen(a, atol)?.values.iter().map(|x| x.abs()).sum())
}

/// `max|λ|` of a Hermitian matrix — its operator norm.
pub fn operator_norm_hermitian(a: &CMatrix, atol: f64) -> Result<f64, String> {
    Ok(hermitian_eigen(a, atol)?.values.iter().fold(0.0, |m, x| m.max(x.abs())))
}

/// The smallest eigenvalue of a Hermitian matrix.
pub fn min_eigenvalue_hermitian(a: &CMatrix, atol: f64) -> Result<f64, String> {
    Ok(hermitian_eigen(a, atol)?.values.iter().fold(f64::INFINITY, |m, x| m.min(*x)))
}

/// `exp(−iHt)` for Hermitian `H`, through its eigendecomposition; also
/// returns the eigendecomposition residual and the unitarity error.
pub fn evolution_operator(h: &CMatrix, t: f64, atol: f64) -> Result<(CMatrix, f64, f64), String> {
    if !t.is_finite() { return Err("time must be finite".into()); }
    let e = hermitian_eigen(h, atol)?;
    let n = h.rows;
    let mut phases = CMatrix::zeros(n, n);
    for i in 0..n {
        phases.set(i, i, C::cis(-e.values[i] * t));
    }
    let u = e.vectors.mul(&phases).mul(&e.vectors.adjoint());
    let unitarity = u.adjoint().mul(&u).sub(&CMatrix::eye(n)).frobenius();
    Ok((u, e.residual, unitarity))
}

/// The Pauli matrices `(X, Y, Z)`.
pub fn paulis() -> (CMatrix, CMatrix, CMatrix) {
    let x = CMatrix::from_real_rows(&[&[0.0, 1.0], &[1.0, 0.0]]);
    let y = CMatrix::from_rows(&[&[C::ZERO, C::new(0.0, -1.0)], &[C::new(0.0, 1.0), C::ZERO]]);
    let z = CMatrix::from_real_rows(&[&[1.0, 0.0], &[0.0, -1.0]]);
    (x, y, z)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn jacobi_diagonalises_a_hermitian_matrix() {
        let (x, y, z) = paulis();
        let h = x.scale_real(0.5).add(&y.scale_real(0.25)).add(&z.scale_real(2.0));
        let e = hermitian_eigen(&h, 1e-12).unwrap();
        assert!(e.residual < 1e-13);
        let expected = (0.25f64 + 0.0625 + 4.0).sqrt();
        let mut vals = e.values.clone();
        vals.sort_by(|a, b| a.partial_cmp(b).unwrap());
        assert!((vals[0] + expected).abs() < 1e-13 && (vals[1] - expected).abs() < 1e-13);
        assert!((trace_norm_hermitian(&h, 1e-12).unwrap() - 2.0 * expected).abs() < 1e-13);
        assert!((operator_norm_hermitian(&h, 1e-12).unwrap() - expected).abs() < 1e-13);
        assert!(hermitian_eigen(&CMatrix::from_real_rows(&[&[0.0, 1.0], &[0.0, 0.0]]), 1e-12).is_err());
    }

    #[test]
    fn the_evolution_operator_is_unitary_and_correct_on_a_pauli() {
        let (x, _, _) = paulis();
        let t = 0.7;
        let (u, res, unit) = evolution_operator(&x, t, 1e-12).unwrap();
        assert!(res < 1e-14 && unit < 1e-14);
        // exp(-i t X) = cos t · I − i sin t · X
        let expected = CMatrix::eye(2).scale_real(t.cos()).add(&x.scale(C::new(0.0, -t.sin())));
        assert!(u.sub(&expected).frobenius() < 1e-14);
    }

    #[test]
    fn partial_trace_and_embedding_respect_the_factor_order() {
        let (x, _, z) = paulis();
        let dims = [2, 2, 2];
        // Z on site 0 and X on site 2, embedded from support (2, 0): op = X ⊗ Z in that order.
        let op = x.kron(&z);
        let embedded = embed(&op, &[2, 0], &dims);
        let direct = z.kron(&CMatrix::eye(2)).kron(&x);
        assert!(embedded.sub(&direct).frobenius() < 1e-15);
        // Tracing a product state back to a factor.
        let zero = CMatrix::density(&[C::ONE, C::ZERO]);
        let plus = CMatrix::density(&[C::real(std::f64::consts::FRAC_1_SQRT_2), C::real(std::f64::consts::FRAC_1_SQRT_2)]);
        let rho = zero.kron(&plus).kron(&zero);
        assert!(partial_trace(&rho, &dims, &[1]).sub(&plus).frobenius() < 1e-15);
        assert!(partial_trace(&rho, &dims, &[2, 1]).sub(&zero.kron(&plus)).frobenius() < 1e-15);
        assert_eq!(compose(&decompose(5, &dims), &dims), 5);
    }
}
