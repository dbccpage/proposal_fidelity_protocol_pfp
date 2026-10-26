//! §§2.3, 3 — the graph retraction `Π(x, y, z) = (x, y, x²)` with one skew
//! generator: the projected generator in the `(x, y)` chart is `(x², 0)`,
//! its derivative `[[2x, 0], [0, 0]]` is not constant (Theorem 3.1's
//! nonlinearity, on one hypothesis-valid instance), and the projected
//! family `S_t = Π ∘ exp(tA)` is not a semigroup: `S_π ≠ S_{π/2} S_{π/2}`
//! on `(1, 0, 1)`, defect `(−2, 0, 0)`.
//!
//! Replicates `retraction_geometry.py`.  Ledger B3/C1.
//!
//! The symbolic part uses bivariate polynomials over the rationals
//! (`Poly2`), which is all the chart computation needs.  The trigonometric
//! part is exact at multiples of `π/2` only — the instance uses `π/2` and
//! `π`, where `cos` and `sin` are `0, ±1` — and refuses every other angle:
//! `rotation` takes a number of quarter turns, not a real.

use std::collections::BTreeMap;
use std::fmt;

use super::matrix::Matrix;
use super::rational::{q, Rational};

/// A polynomial in `x` and `y` with rational coefficients.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Poly2 {
    /// `(deg x, deg y) → coefficient`, zeros removed.
    pub terms: BTreeMap<(u32, u32), Rational>,
}

impl Poly2 {
    /// Zero.
    pub fn zero() -> Poly2 {
        Poly2 { terms: BTreeMap::new() }
    }

    /// A constant.
    pub fn constant(c: Rational) -> Poly2 {
        let mut p = Poly2::zero();
        if !c.is_zero() {
            p.terms.insert((0, 0), c);
        }
        p
    }

    /// `x`.
    pub fn x() -> Poly2 {
        Poly2 { terms: BTreeMap::from([((1, 0), Rational::ONE)]) }
    }

    /// `y`.
    pub fn y() -> Poly2 {
        Poly2 { terms: BTreeMap::from([((0, 1), Rational::ONE)]) }
    }

    /// Is zero.
    pub fn is_zero(&self) -> bool {
        self.terms.is_empty()
    }

    /// Sum.
    pub fn add(&self, o: &Poly2) -> Poly2 {
        let mut terms = self.terms.clone();
        for (k, c) in &o.terms {
            let v = terms.get(k).copied().unwrap_or(Rational::ZERO) + *c;
            if v.is_zero() {
                terms.remove(k);
            } else {
                terms.insert(*k, v);
            }
        }
        Poly2 { terms }
    }

    /// Difference.
    pub fn sub(&self, o: &Poly2) -> Poly2 {
        self.add(&o.scale(q(-1)))
    }

    /// Scalar multiple.
    pub fn scale(&self, c: Rational) -> Poly2 {
        if c.is_zero() {
            return Poly2::zero();
        }
        Poly2 { terms: self.terms.iter().map(|(k, v)| (*k, *v * c)).collect() }
    }

    /// Product.
    pub fn mul(&self, o: &Poly2) -> Poly2 {
        let mut out = Poly2::zero();
        for ((ax, ay), ac) in &self.terms {
            for ((bx, by), bc) in &o.terms {
                let mut t = Poly2::zero();
                t.terms.insert((ax + bx, ay + by), *ac * *bc);
                out = out.add(&t);
            }
        }
        out
    }

    /// Partial derivative: `0` for `x`, `1` for `y`.
    pub fn diff(&self, var: usize) -> Poly2 {
        let mut out = Poly2::zero();
        for (&(dx, dy), &c) in &self.terms {
            let t = match var {
                0 if dx > 0 => Some(((dx - 1, dy), c * q(dx as i128))),
                1 if dy > 0 => Some(((dx, dy - 1), c * q(dy as i128))),
                _ => None,
            };
            if let Some((k, v)) = t {
                let mut m = Poly2::zero();
                m.terms.insert(k, v);
                out = out.add(&m);
            }
        }
        out
    }

    /// Evaluate at a rational point.
    pub fn eval(&self, x: Rational, y: Rational) -> Rational {
        self.terms.iter().fold(Rational::ZERO, |a, (&(dx, dy), &c)| a + c * x.pow(dx) * y.pow(dy))
    }
}

impl fmt::Display for Poly2 {
    /// The Python engine's text: `x**2`, `2*x`, `0`, `x*y`.
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        if self.is_zero() {
            return write!(f, "0");
        }
        let mut parts = Vec::new();
        for (&(dx, dy), &c) in &self.terms {
            let mut mono = Vec::new();
            for (name, d) in [("x", dx), ("y", dy)] {
                match d {
                    0 => {}
                    1 => mono.push(name.to_string()),
                    _ => mono.push(format!("{name}**{d}")),
                }
            }
            let m = mono.join("*");
            parts.push(if m.is_empty() {
                c.to_string()
            } else if c == Rational::ONE {
                m
            } else if c == -Rational::ONE {
                format!("-{m}")
            } else {
                format!("{c}*{m}")
            });
        }
        let mut out = String::new();
        for (i, p) in parts.iter().enumerate() {
            if i == 0 {
                out.push_str(p);
            } else if let Some(rest) = p.strip_prefix('-') {
                out.push_str(" - ");
                out.push_str(rest);
            } else {
                out.push_str(" + ");
                out.push_str(p);
            }
        }
        write!(f, "{out}")
    }
}

/// A dense matrix of bivariate polynomials.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PMatrix {
    /// Rows.
    pub rows: usize,
    /// Columns.
    pub cols: usize,
    /// Entries, row-major.
    pub data: Vec<Poly2>,
}

impl PMatrix {
    /// A column.
    pub fn column(entries: Vec<Poly2>) -> PMatrix {
        PMatrix { rows: entries.len(), cols: 1, data: entries }
    }

    /// From a rational matrix.
    pub fn from_matrix(m: &Matrix) -> PMatrix {
        PMatrix { rows: m.rows, cols: m.cols, data: m.data.iter().map(|c| Poly2::constant(*c)).collect() }
    }

    /// Entry.
    pub fn get(&self, i: usize, j: usize) -> &Poly2 {
        &self.data[i * self.cols + j]
    }

    /// Product.
    pub fn mul(&self, o: &PMatrix) -> PMatrix {
        assert_eq!(self.cols, o.rows, "shape mismatch");
        let mut data = Vec::with_capacity(self.rows * o.cols);
        for i in 0..self.rows {
            for j in 0..o.cols {
                let mut s = Poly2::zero();
                for k in 0..self.cols {
                    s = s.add(&self.get(i, k).mul(o.get(k, j)));
                }
                data.push(s);
            }
        }
        PMatrix { rows: self.rows, cols: o.cols, data }
    }

    /// Evaluate every entry.
    pub fn eval(&self, x: Rational, y: Rational) -> Matrix {
        Matrix { rows: self.rows, cols: self.cols, data: self.data.iter().map(|p| p.eval(x, y)).collect() }
    }
}

impl fmt::Display for PMatrix {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let rows: Vec<String> = (0..self.rows)
            .map(|i| {
                let cells: Vec<String> = (0..self.cols).map(|j| format!("'{}'", self.get(i, j))).collect();
                format!("[{}]", cells.join(", "))
            })
            .collect();
        write!(f, "[{}]", rows.join(", "))
    }
}

/// The polynomial retraction onto `M = {(x, y, z) : z = x²}`.
pub struct GraphRetraction;

impl GraphRetraction {
    /// `(x, y) ↦ (x, y, x²)`.
    pub fn lift(x: Rational, y: Rational) -> Matrix {
        Matrix::column(&[x, y, x * x])
    }

    /// `Π(x, y, z) = (x, y, x²)`.
    pub fn retract(p: &Matrix) -> Matrix {
        Self::require_ambient(p);
        Matrix::column(&[p.get(0, 0), p.get(1, 0), p.get(0, 0) * p.get(0, 0)])
    }

    /// The chart of a point on `M`.
    pub fn chart(p: &Matrix) -> Result<Matrix, String> {
        if !Self::is_on_manifold(p) {
            return Err("chart is defined only on M".into());
        }
        Ok(Matrix::column(&[p.get(0, 0), p.get(1, 0)]))
    }

    /// `z = x²`.
    pub fn is_on_manifold(p: &Matrix) -> bool {
        Self::require_ambient(p);
        p.get(2, 0) == p.get(0, 0) * p.get(0, 0)
    }

    /// `DΠ` at a rational point.
    pub fn jacobian(p: &Matrix) -> Matrix {
        Self::require_ambient(p);
        let x = p.get(0, 0);
        Matrix::from_rows(&[vec![q(1), q(0), q(0)], vec![q(0), q(1), q(0)], vec![q(2) * x, q(0), q(0)]])
    }

    /// `DΠ` at the symbolic point `(x, y, x²)`.
    pub fn jacobian_symbolic() -> PMatrix {
        let (z, o) = (Poly2::zero(), Poly2::constant(Rational::ONE));
        PMatrix { rows: 3, cols: 3, data: vec![o.clone(), z.clone(), z.clone(), z.clone(), o, z.clone(), Poly2::x().scale(q(2)), z.clone(), z] }
    }

    fn require_ambient(p: &Matrix) {
        assert_eq!(p.shape(), (3, 1), "expected a 3x1 ambient point");
    }
}

/// The exact skew generator `A` of the theorem-aligned fixture.
pub fn contraction_generator() -> Matrix {
    Matrix::from_i128(&[&[0, 0, 1], &[0, 0, 0], &[-1, 0, 0]])
}

/// `exp(tA)` for `t = k·π/2`: a rotation in the `(x, z)` plane by `k`
/// quarter turns, exact.
pub fn rotation(quarter_turns: i64) -> Matrix {
    let (c, s) = match quarter_turns.rem_euclid(4) {
        0 => (q(1), q(0)),
        1 => (q(0), q(1)),
        2 => (q(-1), q(0)),
        _ => (q(0), q(-1)),
    };
    Matrix::from_rows(&[vec![c, q(0), s], vec![q(0), q(1), q(0)], vec![-s, q(0), c]])
}

/// `DΠ(p) A p` on `M`, symbolically at `(x, y, x²)`.
pub fn projected_generator_symbolic() -> PMatrix {
    let point = PMatrix::column(vec![Poly2::x(), Poly2::y(), Poly2::x().mul(&Poly2::x())]);
    GraphRetraction::jacobian_symbolic().mul(&PMatrix::from_matrix(&contraction_generator())).mul(&point)
}

/// The chart representation of the projected generator: the first two
/// components.
pub fn projected_generator_chart() -> PMatrix {
    let a = projected_generator_symbolic();
    PMatrix::column(vec![a.get(0, 0).clone(), a.get(1, 0).clone()])
}

/// Exact witness for nonconstant `DB` in one declared affine chart.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct AffineNonlinearityInstance {
    /// `Aᵀ + A = 0`.
    pub generator_is_skew: bool,
    /// `Π ∘ Π = Π` on the instance.
    pub retraction_is_idempotent: bool,
    /// `DΠ(m₀)² = DΠ(m₀)`.
    pub tangent_projection_is_idempotent: bool,
    /// `B(x, y) = (x², 0)`.
    pub chart_vector_field: PMatrix,
    /// `DB = [[2x, 0], [0, 0]]`.
    pub chart_derivative: PMatrix,
    /// `DB` at `(0, 0)`.
    pub derivative_at_x0: Matrix,
    /// `DB` at `(1, 0)`.
    pub derivative_at_x1: Matrix,
    /// The two differ.
    pub derivative_is_nonconstant: bool,
    /// `B(midpoint) − average of B at the endpoints`.
    pub midpoint_nonaffinity_defect: Matrix,
    /// The lifted chart midpoint lies on `M`.
    pub midpoint_is_on_manifold: bool,
}

/// Construct the exact nonconstant-derivative witness for Theorem 3.1.
pub fn affine_nonlinearity_instance() -> AffineNonlinearityInstance {
    let generator = contraction_generator();
    let field = projected_generator_chart();
    let derivative = PMatrix {
        rows: 2,
        cols: 2,
        data: vec![field.get(0, 0).diff(0), field.get(0, 0).diff(1), field.get(1, 0).diff(0), field.get(1, 0).diff(1)],
    };
    let at_x0 = derivative.eval(q(0), q(0));
    let at_x1 = derivative.eval(q(1), q(0));
    let m0 = GraphRetraction::lift(q(0), q(0));
    let m1 = GraphRetraction::lift(q(1), q(0));
    let half = Rational::new(1, 2);
    let lifted_midpoint = GraphRetraction::lift(half, q(0));
    let field_midpoint = field.eval(half, q(0));
    let affine_average = field.eval(q(0), q(0)).add(&field.eval(q(1), q(0))).scale(half);
    let p0 = GraphRetraction::jacobian(&m0);
    AffineNonlinearityInstance {
        generator_is_skew: generator.transpose().add(&generator).is_zero(),
        retraction_is_idempotent: GraphRetraction::retract(&GraphRetraction::retract(&m1)) == GraphRetraction::retract(&m1),
        tangent_projection_is_idempotent: p0.mul(&p0) == p0,
        chart_vector_field: field,
        chart_derivative: derivative,
        derivative_is_nonconstant: at_x0 != at_x1,
        derivative_at_x0: at_x0,
        derivative_at_x1: at_x1,
        midpoint_nonaffinity_defect: field_midpoint.sub(&affine_average),
        midpoint_is_on_manifold: GraphRetraction::is_on_manifold(&lifted_midpoint),
    }
}

/// `S_t(p) = Π(exp(tA) p)` at `t = k·π/2`, on `M`.
pub fn projected_family(p: &Matrix, quarter_turns: i64) -> Result<Matrix, String> {
    if !GraphRetraction::is_on_manifold(p) {
        return Err("S_t is defined here on M".into());
    }
    Ok(GraphRetraction::retract(&rotation(quarter_turns).mul(p)))
}

/// Exact witness that `S_{t+s}` need not equal `S_t S_s`.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct SemigroupDefectInstance {
    /// `t`, in quarter turns.
    pub t_quarter_turns: i64,
    /// `s`, in quarter turns.
    pub s_quarter_turns: i64,
    /// The start point.
    pub start: Matrix,
    /// `S_{t+s}(start)`.
    pub direct: Matrix,
    /// `S_t(S_s(start))`.
    pub stepped: Matrix,
    /// `direct − stepped`.
    pub defect: Matrix,
    /// The defect is nonzero.
    pub is_nonzero: bool,
}

/// `S_π ≠ S_{π/2} S_{π/2}` on `(1, 0, 1)`.
pub fn semigroup_defect_instance() -> SemigroupDefectInstance {
    let start = GraphRetraction::lift(q(1), q(0));
    let direct = projected_family(&start, 2).expect("start is on M");
    let stepped = projected_family(&projected_family(&start, 1).expect("on M"), 1).expect("on M");
    let defect = direct.sub(&stepped);
    let is_nonzero = !defect.is_zero();
    SemigroupDefectInstance { t_quarter_turns: 1, s_quarter_turns: 1, start, direct, stepped, defect, is_nonzero }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// B3: `[['x**2'], ['0']]`, `[['2*x', '0'], ['0', '0']]`, nonconstant.
    #[test]
    fn the_chart_derivative_is_nonconstant() {
        let g = affine_nonlinearity_instance();
        assert!(g.generator_is_skew && g.retraction_is_idempotent && g.tangent_projection_is_idempotent);
        assert_eq!(g.chart_vector_field.to_string(), "[['x**2'], ['0']]");
        assert_eq!(g.chart_derivative.to_string(), "[['2*x', '0'], ['0', '0']]");
        assert_eq!(g.derivative_at_x0, Matrix::zeros(2, 2));
        assert_eq!(g.derivative_at_x1, Matrix::from_i128(&[&[2, 0], &[0, 0]]));
        assert!(g.derivative_is_nonconstant && g.midpoint_is_on_manifold);
        assert_eq!(g.midpoint_nonaffinity_defect, Matrix::column(&[Rational::new(-1, 4), q(0)]));
    }

    /// C1: `[['-2'], ['0'], ['0']]`.
    #[test]
    fn the_projected_family_is_not_a_semigroup() {
        let s = semigroup_defect_instance();
        assert!(s.is_nonzero);
        assert_eq!(s.defect.to_string(), "[['-2'], ['0'], ['0']]");
        assert_eq!(s.direct, Matrix::column_i128(&[-1, 0, 1]));
        assert_eq!(s.stepped, Matrix::column_i128(&[1, 0, 1]));
        assert!(projected_family(&Matrix::column_i128(&[1, 0, 5]), 1).is_err());
        assert_eq!(rotation(4), Matrix::eye(3));
        assert_eq!(rotation(-1), rotation(3));
    }

    #[test]
    fn bivariate_polynomials_print_like_the_python_engine() {
        let xy = Poly2::x().mul(&Poly2::y());
        assert_eq!(xy.to_string(), "x*y");
        assert_eq!(xy.diff(1).to_string(), "x");
        assert_eq!(Poly2::x().mul(&Poly2::x()).scale(q(-1)).add(&Poly2::constant(q(3))).to_string(), "3 - x**2");
        assert_eq!(GraphRetraction::chart(&GraphRetraction::lift(q(2), q(5))).unwrap(), Matrix::column_i128(&[2, 5]));
    }
}
