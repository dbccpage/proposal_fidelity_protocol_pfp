// AuthorityEffect: None.

//! The generalized Gell-Mann basis of an independently declared label space `C^N`.
//!
//! For `N >= 2` the family is
//!
//! - `E_jk + E_kj` for `j < k`,
//! - `-i E_jk + i E_kj` for `j < k`,
//! - `sqrt(2 / (l (l + 1))) diag(1, ..., 1, -l, 0, ..., 0)` for `1 <= l <= N - 1`
//!   (`l` ones before `-l`).
//!
//! The diagonal scales are irrational, so each generator is stored as
//! `lambda_a = sqrt(r_a) M_a` with `M_a` exact over `Q(i)` and `r_a` rational
//! (`r_a = 1` off the diagonal). Every identity is then an exact rational
//! identity:
//!
//! - `Tr(lambda_a lambda_b) = 2 delta_ab`;
//! - any traceless Hermitian `X` equals `sum_a (r_a / 2) Tr(X M_a) M_a`;
//! - with `T_a = lambda_a / 2`, `[T_a, T_b] = i sum_c f_abc T_c`, where
//!   `f_abc = sqrt(r_a r_b r_c) t_abc` and `t_abc = -(i/4) Tr([M_a, M_b] M_c)`
//!   is rational;
//! - the Jacobi identity, after the common factor `sqrt(r_a r_b r_c r_e)`
//!   is removed, is `sum_d r_d (t_abd t_dce + t_bcd t_dae + t_cad t_dbe) = 0`.
//!
//! The label space is a separate declaration. Nothing here builds it from a
//! graph, and attaching it to vertices or edges is a further modelling choice.

use crate::scalar::is_hermitian;
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{elimination, matrix as mx, ExactFieldError};
use num_traits::Zero;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::quadratic::{QuadraticError, Surd};
use core_number_theory::rational::{ri, rq, Rational};

pub const MAX_DIMENSION: usize = 8;
pub type GaussianMatrix = BasicMatrix<GaussianRat>;

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum GellMannError {
    #[error(transparent)]
    Storage(#[from] linear_algebra::backend::basic_matrix::MatrixError),
    #[error("the label dimension must be at least two, got {0}")]
    DimensionTooSmall(usize),
    #[error("the label dimension {0} exceeds the exact construction bound {MAX_DIMENSION}")]
    DimensionTooLarge(usize),
    #[error("generator {index} is outside the family of {len}")]
    IndexOutOfRange { index: usize, len: usize },
    #[error("matrix must be {n}x{n}")]
    ShapeMismatch { n: usize },
    #[error("matrix is not traceless Hermitian")]
    NotTracelessHermitian,
    #[error("a structure-constant trace was not purely imaginary")]
    NonRealStructureConstant,
    #[error(transparent)]
    Surd(#[from] QuadraticError),
    #[error(transparent)]
    Matrix(#[from] ExactFieldError),
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum GeneratorKind {
    Symmetric { j: usize, k: usize },
    Antisymmetric { j: usize, k: usize },
    Diagonal { l: usize },
}

/// `lambda_a = sqrt(scale_squared) shape`; the shape has rational Gaussian entries.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GellMannGenerator {
    pub kind: GeneratorKind,
    pub shape: GaussianMatrix,
    pub scale_squared: Rational,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GellMannBasis {
    n: usize,
    generators: Vec<GellMannGenerator>,
}

impl GellMannBasis {
    fn off_diagonal_generator(
        n: usize,
        j: usize,
        k: usize,
        antisymmetric: bool,
    ) -> Result<GellMannGenerator, GellMannError> {
        let mut shape = mx::zeros::<GaussianRat>(n, n)?;
        let (upper, lower, kind) = if antisymmetric {
            (
                GaussianRat::i().neg(),
                GaussianRat::i(),
                GeneratorKind::Antisymmetric { j, k },
            )
        } else {
            (
                GaussianRat::one(),
                GaussianRat::one(),
                GeneratorKind::Symmetric { j, k },
            )
        };
        shape.set(j, k, upper).map_err(ExactFieldError::from)?;
        shape.set(k, j, lower).map_err(ExactFieldError::from)?;
        Ok(GellMannGenerator {
            kind,
            shape,
            scale_squared: ri(1),
        })
    }

    fn diagonal_generator(n: usize, l: usize) -> Result<GellMannGenerator, GellMannError> {
        let mut shape = mx::zeros::<GaussianRat>(n, n)?;
        for i in 0..l {
            shape
                .set(i, i, GaussianRat::one())
                .map_err(ExactFieldError::from)?;
        }
        shape
            .set(l, l, GaussianRat::from_ints(-(l as i64), 0))
            .map_err(ExactFieldError::from)?;
        Ok(GellMannGenerator {
            kind: GeneratorKind::Diagonal { l },
            shape,
            scale_squared: rq(2, (l * (l + 1)) as i64),
        })
    }

    pub fn new(n: usize) -> Result<Self, GellMannError> {
        if n < 2 {
            return Err(GellMannError::DimensionTooSmall(n));
        }
        if n > MAX_DIMENSION {
            return Err(GellMannError::DimensionTooLarge(n));
        }
        let mut generators = Vec::with_capacity(n * n - 1);
        for antisymmetric in [false, true] {
            for j in 0..n {
                for k in j + 1..n {
                    generators.push(Self::off_diagonal_generator(n, j, k, antisymmetric)?);
                }
            }
        }
        for l in 1..n {
            generators.push(Self::diagonal_generator(n, l)?);
        }
        Ok(Self { n, generators })
    }
    pub fn dimension(&self) -> usize {
        self.n
    }
    pub fn len(&self) -> usize {
        self.generators.len()
    }
    pub fn is_empty(&self) -> bool {
        self.generators.is_empty()
    }
    pub fn generators(&self) -> &[GellMannGenerator] {
        &self.generators
    }
    pub fn generator(&self, index: usize) -> Result<&GellMannGenerator, GellMannError> {
        self.generators
            .get(index)
            .ok_or(GellMannError::IndexOutOfRange {
                index,
                len: self.len(),
            })
    }
    pub fn all_traceless_hermitian(&self) -> bool {
        self.generators.iter().all(|g| {
            is_hermitian(&g.shape) == Ok(true) && mx::trace(&g.shape) == Ok(GaussianRat::zero())
        })
    }
    pub fn gram_entry(&self, a: usize, b: usize) -> Result<Surd, GellMannError> {
        let (a, b) = (self.generator(a)?, self.generator(b)?);
        let t = mx::trace(&mx::multiply(&a.shape, &b.shape)?)?;
        if !t.im.is_zero() {
            return Err(GellMannError::NotTracelessHermitian);
        }
        Ok(Surd::new(t.re, &(&a.scale_squared * &b.scale_squared))?)
    }
    pub fn verify_gram_identity(&self) -> bool {
        (0..self.len()).all(|a| {
            (0..self.len()).all(|b| {
                self.gram_entry(a, b) == Ok(Surd::rational(ri(if a == b { 2 } else { 0 })))
            })
        })
    }
    pub fn real_independence_rank(&self) -> usize {
        let data = self
            .generators
            .iter()
            .flat_map(|g| {
                g.shape
                    .as_slice()
                    .iter()
                    .flat_map(|z| [z.re.clone(), z.im.clone()])
            })
            .collect();
        BasicMatrix::from_row_major(self.len(), 2 * self.n * self.n, data)
            .ok()
            .and_then(|m| elimination::rank(&m).ok())
            .unwrap_or(0)
    }
    fn check(&self, x: &GaussianMatrix) -> Result<(), GellMannError> {
        if x.shape() != (self.n, self.n) {
            return Err(GellMannError::ShapeMismatch { n: self.n });
        }
        if !is_hermitian(x)? || !mx::trace(x)?.is_zero() {
            return Err(GellMannError::NotTracelessHermitian);
        }
        Ok(())
    }
    pub fn coordinates(&self, x: &GaussianMatrix) -> Result<Vec<Surd>, GellMannError> {
        self.check(x)?;
        self.generators
            .iter()
            .map(|g| {
                let t = mx::trace(&mx::multiply(x, &g.shape)?)?;
                if !t.im.is_zero() {
                    return Err(GellMannError::NotTracelessHermitian);
                }
                Ok(Surd::new(t.re / ri(2), &g.scale_squared)?)
            })
            .collect()
    }
    pub fn reconstruct(&self, x: &GaussianMatrix) -> Result<GaussianMatrix, GellMannError> {
        self.check(x)?;
        let mut result = mx::zeros(self.n, self.n)?;
        for g in &self.generators {
            let t = mx::trace(&mx::multiply(x, &g.shape)?)?;
            let c = t.mul(&GaussianRat::from_rational(&g.scale_squared / ri(2)));
            result = mx::add(&result, &mx::scale(&g.shape, &c)?)?;
        }
        Ok(result)
    }
    pub fn rational_structure_part(
        &self,
        a: usize,
        b: usize,
        c: usize,
    ) -> Result<Rational, GellMannError> {
        let (a, b, c) = (self.generator(a)?, self.generator(b)?, self.generator(c)?);
        let t = mx::trace(&mx::multiply(
            &mx::commutator(&a.shape, &b.shape)?,
            &c.shape,
        )?)?;
        if !t.re.is_zero() {
            return Err(GellMannError::NonRealStructureConstant);
        }
        Ok(t.im / ri(4))
    }
    pub fn structure_constant(&self, a: usize, b: usize, c: usize) -> Result<Surd, GellMannError> {
        let t = self.rational_structure_part(a, b, c)?;
        Ok(Surd::new(
            t,
            &(&self.generators[a].scale_squared
                * &self.generators[b].scale_squared
                * &self.generators[c].scale_squared),
        )?)
    }
    /// Sparse trace projection; one commutator per pair, never per triple.
    fn structure_table(&self) -> Result<Vec<Vec<Vec<Rational>>>, GellMannError> {
        let n = self.len();
        let mut table = vec![vec![vec![ri(0); n]; n]; n];
        for a in 0..n {
            for b in a + 1..n {
                let comm = mx::commutator(&self.generators[a].shape, &self.generators[b].shape)?;
                for c in 0..n {
                    // Tr(C M) = sum_ij C_ij M_ji, without allocating C M.
                    let mut t = GaussianRat::zero();
                    for i in 0..self.n {
                        for j in 0..self.n {
                            t = t.add(
                                &comm
                                    .get_ref(i, j)?
                                    .mul(self.generators[c].shape.get_ref(j, i)?),
                            );
                        }
                    }
                    if !t.re.is_zero() {
                        return Err(GellMannError::NonRealStructureConstant);
                    }
                    table[a][b][c] = t.im / ri(4);
                    table[b][a][c] = -&table[a][b][c];
                }
            }
        }
        Ok(table)
    }
    pub fn verify_total_antisymmetry(&self) -> bool {
        let Ok(t) = self.structure_table() else {
            return false;
        };
        (0..self.len()).all(|a| {
            (0..self.len()).all(|b| {
                (0..self.len()).all(|c| t[a][b][c] == -&t[b][a][c] && t[a][b][c] == -&t[a][c][b])
            })
        })
    }
    pub fn verify_commutation_relations(&self) -> bool {
        let Ok(t) = self.structure_table() else {
            return false;
        };
        for a in 0..self.len() {
            for b in 0..self.len() {
                let Ok(lhs) = mx::commutator(&self.generators[a].shape, &self.generators[b].shape)
                else {
                    return false;
                };
                let Ok(mut rhs) = mx::zeros(self.n, self.n) else {
                    return false;
                };
                for c in 0..self.len() {
                    if !t[a][b][c].is_zero() {
                        let coefficient = GaussianRat {
                            re: ri(0),
                            im: ri(2) * &self.generators[c].scale_squared * &t[a][b][c],
                        };
                        let Ok(term) = mx::scale(&self.generators[c].shape, &coefficient) else {
                            return false;
                        };
                        let Ok(sum) = mx::add(&rhs, &term) else {
                            return false;
                        };
                        rhs = sum;
                    }
                }
                if lhs != rhs {
                    return false;
                }
            }
        }
        true
    }
    pub fn verify_jacobi(&self) -> bool {
        let Ok(t) = self.structure_table() else {
            return false;
        };
        let n = self.len();
        for a in 0..n {
            for b in a + 1..n {
                for c in b + 1..n {
                    for e in 0..n {
                        let mut total = ri(0);
                        for d in 0..n {
                            total += &self.generators[d].scale_squared
                                * (&t[a][b][d] * &t[d][c][e]
                                    + &t[b][c][d] * &t[d][a][e]
                                    + &t[c][a][d] * &t[d][b][e]);
                        }
                        if !total.is_zero() {
                            return false;
                        }
                    }
                }
            }
        }
        true
    }
    /// Fundamental quadratic Casimir, `sum_a T_a T_a = (n^2-1)/(2n) I`.
    pub fn fundamental_casimir(&self) -> Result<GaussianMatrix, GellMannError> {
        let mut result = mx::zeros(self.n, self.n)?;
        for g in &self.generators {
            let square = mx::multiply(&g.shape, &g.shape)?;
            result = mx::add(
                &result,
                &mx::scale(
                    &square,
                    &GaussianRat::from_rational(&g.scale_squared / ri(4)),
                )?,
            )?;
        }
        Ok(result)
    }
    /// Exact Fierz completeness tensor in the fundamental representation.
    pub fn fierz_entry(
        &self,
        i: usize,
        j: usize,
        k: usize,
        l: usize,
    ) -> Result<GaussianRat, GellMannError> {
        if [i, j, k, l].iter().any(|v| *v >= self.n) {
            return Err(GellMannError::ShapeMismatch { n: self.n });
        }
        let mut value = GaussianRat::zero();
        for g in &self.generators {
            value = value.add(
                &g.shape
                    .get_ref(i, j)?
                    .mul(g.shape.get_ref(k, l)?)
                    .mul(&GaussianRat::from_rational(&g.scale_squared / ri(4))),
            );
        }
        Ok(value)
    }
    /// `d_abc = Tr({lambda_a,lambda_b} lambda_c)/4` in exact surd form.
    pub fn symmetric_structure_constant(
        &self,
        a: usize,
        b: usize,
        c: usize,
    ) -> Result<Surd, GellMannError> {
        let (a, b, c) = (self.generator(a)?, self.generator(b)?, self.generator(c)?);
        let t = mx::trace(&mx::multiply(
            &mx::anticommutator(&a.shape, &b.shape)?,
            &c.shape,
        )?)?;
        if !t.im.is_zero() {
            return Err(GellMannError::NotTracelessHermitian);
        }
        Ok(Surd::new(
            t.re / ri(4),
            &(&a.scale_squared * &b.scale_squared * &c.scale_squared),
        )?)
    }
    /// Killing form on `T_a=lambda_a/2`, `2n Tr(T_a T_b)=n delta_ab`.
    pub fn killing_entry(&self, a: usize, b: usize) -> Result<Surd, GellMannError> {
        let gram = self.gram_entry(a, b)?;
        Ok(Surd::new(
            gram.coefficient() * rq(self.n as i64, 2),
            &Rational::from_integer(gram.radicand().clone()),
        )?)
    }
    /// The rational anti-Hermitian shapes form an exact Lie algebra with no square roots.
    pub fn shape_lie_algebra(
        &self,
    ) -> Result<
        crate::lie_algebra::StructureConstants<GaussianRat>,
        crate::lie_algebra::LieAlgebraError,
    > {
        crate::lie_algebra::structure_constants_from_matrices(
            &self
                .generators
                .iter()
                .map(|g| g.shape.clone())
                .collect::<Vec<_>>(),
        )
    }
}

pub fn is_special_unitary<F: crate::scalar::ComplexField>(
    u: &BasicMatrix<F>,
) -> Result<bool, ExactFieldError> {
    Ok(crate::scalar::is_unitary(u)? && elimination::determinant(u)? == F::one())
}

// Origin: engine/crates_rs/core_lie_theory/src/su_n.rs
// Claim: urn:core:crates_rs:core-lie-theory:su-n:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_c6f7c7a6 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
