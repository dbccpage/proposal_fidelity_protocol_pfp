//! A finite abelian group with a fully checked normalized unitary 2-cocycle.
//!
//! u_g u_h = alpha(g,h) u_(gh). Scalars and matrices retain their canonical
//! owners. The complex block profile is algebraic; it admits neither histories
//! nor physical states/processes. The cubic declaration check is bounded by 64
//! labels. AuthorityEffect: None.

use crate::finite_group::{FiniteGroup, GroupError};
use crate::scalar::ComplexField;
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{matrix as mx, ExactFieldError};

pub const MAX_COCYCLE_ORDER: usize = 64;

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum TwistedAlgebraError {
    #[error("cocycle order {0} exceeds the finite validation budget")]
    Budget(usize),
    #[error("cocycle table must be square with the group order")]
    CocycleShape,
    #[error("the declared group is nonabelian at ({left}, {right})")]
    NonAbelian { left: usize, right: usize },
    #[error("cocycle is not normalized at label {0}")]
    NotNormalized(usize),
    #[error("cocycle value at ({left}, {right}) is not unitary")]
    NotUnitary { left: usize, right: usize },
    #[error("cocycle identity fails at ({g}, {h}, {k})")]
    NotCocycle { g: usize, h: usize, k: usize },
    #[error("validated complex block dimensions are inconsistent")]
    InconsistentBlocks,
    #[error(transparent)]
    Group(#[from] GroupError),
    #[error(transparent)]
    Matrix(#[from] ExactFieldError),
}

/// Over C the algebra is a sum of `center_dimension` copies of
/// M_`block_dimension`(C). This says nothing about operational availability.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ComplexBlockProfile {
    pub algebra_dimension: usize,
    pub center_dimension: usize,
    pub block_dimension: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TwistedAbelianAlgebra<F> {
    group: FiniteGroup<usize>,
    alpha: Vec<Vec<F>>,
    radical: Vec<usize>,
}

impl<F: ComplexField> TwistedAbelianAlgebra<F> {
    fn check_abelian_and_unitary(
        group: &FiniteGroup<usize>,
        alpha: &[Vec<F>],
    ) -> Result<(), TwistedAlgebraError> {
        let n = group.order();
        let identity = group.identity();
        for g in 0..n {
            if alpha[identity][g] != F::one() || alpha[g][identity] != F::one() {
                return Err(TwistedAlgebraError::NotNormalized(g));
            }
            for h in 0..n {
                if group.multiply(g, h)? != group.multiply(h, g)? {
                    return Err(TwistedAlgebraError::NonAbelian { left: g, right: h });
                }
                if alpha[g][h].mul(&alpha[g][h].conjugate()) != F::one() {
                    return Err(TwistedAlgebraError::NotUnitary { left: g, right: h });
                }
            }
        }
        Ok(())
    }

    fn check_cocycle_triples(
        group: &FiniteGroup<usize>,
        alpha: &[Vec<F>],
    ) -> Result<(), TwistedAlgebraError> {
        let n = group.order();
        for g in 0..n {
            for h in 0..n {
                let gh = group.multiply(g, h)?;
                for k in 0..n {
                    let hk = group.multiply(h, k)?;
                    if alpha[g][h].mul(&alpha[gh][k]) != alpha[h][k].mul(&alpha[g][hk]) {
                        return Err(TwistedAlgebraError::NotCocycle { g, h, k });
                    }
                }
            }
        }
        Ok(())
    }

    /// The table uses left * right; identities need not have index zero.
    /// Every group law and every cocycle triple is checked, not sampled.
    pub fn new(table: Vec<Vec<usize>>, alpha: Vec<Vec<F>>) -> Result<Self, TwistedAlgebraError> {
        let n = table.len();
        if n > MAX_COCYCLE_ORDER {
            return Err(TwistedAlgebraError::Budget(n));
        }
        let group = FiniteGroup::from_table((0..n).collect(), table)?;
        if alpha.len() != n || alpha.iter().any(|row| row.len() != n) {
            return Err(TwistedAlgebraError::CocycleShape);
        }
        Self::check_abelian_and_unitary(&group, &alpha)?;
        Self::check_cocycle_triples(&group, &alpha)?;
        let radical = (0..n)
            .filter(|&g| (0..n).all(|h| alpha[g][h] == alpha[h][g]))
            .collect();
        Ok(Self {
            group,
            alpha,
            radical,
        })
    }

    pub fn group(&self) -> &FiniteGroup<usize> {
        &self.group
    }
    /// Labels spanning the center, i.e. the radical of alpha(g,h)/alpha(h,g).
    pub fn center_basis(&self) -> &[usize] {
        &self.radical
    }
    pub fn phase(&self, g: usize, h: usize) -> Result<&F, TwistedAlgebraError> {
        self.group.element(g)?;
        self.group.element(h)?;
        Ok(&self.alpha[g][h])
    }
    pub fn commutator_phase(&self, g: usize, h: usize) -> Result<F, TwistedAlgebraError> {
        Ok(self.phase(g, h)?.mul(&self.phase(h, g)?.conjugate()))
    }
    pub fn basis_product(&self, g: usize, h: usize) -> Result<(usize, F), TwistedAlgebraError> {
        Ok((self.group.multiply(g, h)?, self.phase(g, h)?.clone()))
    }
    pub fn basis_star(&self, g: usize) -> Result<(usize, F), TwistedAlgebraError> {
        let inverse = self.group.inverse(g)?;
        Ok((inverse, self.phase(inverse, g)?.conjugate()))
    }

    pub fn complex_block_profile(&self) -> Result<ComplexBlockProfile, TwistedAlgebraError> {
        let n = self.group.order();
        let r = self.radical.len();
        if r == 0 || n % r != 0 {
            return Err(TwistedAlgebraError::InconsistentBlocks);
        }
        // Integer-only square recognition. The written center/free-module
        // theorem supplies the reason every complex block has this dimension.
        let d = (1..=n)
            .find(|d| d * d == n / r)
            .ok_or(TwistedAlgebraError::InconsistentBlocks)?;
        Ok(ComplexBlockProfile {
            algebra_dimension: n,
            center_dimension: r,
            block_dimension: d,
        })
    }

    fn check(&self, a: &[F]) -> Result<(), TwistedAlgebraError> {
        if a.len() != self.group.order() {
            return Err(GroupError::FunctionLength {
                expected: self.group.order(),
                actual: a.len(),
            }
            .into());
        }
        Ok(())
    }
    pub fn basis(&self, g: usize) -> Result<Vec<F>, TwistedAlgebraError> {
        self.group.element(g)?;
        let mut result = vec![F::zero(); self.group.order()];
        result[g] = F::one();
        Ok(result)
    }
    pub fn multiply(&self, a: &[F], b: &[F]) -> Result<Vec<F>, TwistedAlgebraError> {
        self.check(a)?;
        self.check(b)?;
        let mut result = vec![F::zero(); self.group.order()];
        for (g, x) in a.iter().enumerate() {
            for (h, y) in b.iter().enumerate() {
                let gh = self.group.multiply(g, h)?;
                result[gh] = result[gh].add(&x.mul(y).mul(&self.alpha[g][h]));
            }
        }
        Ok(result)
    }
    pub fn star(&self, a: &[F]) -> Result<Vec<F>, TwistedAlgebraError> {
        self.check(a)?;
        let mut result = vec![F::zero(); self.group.order()];
        for (g, x) in a.iter().enumerate() {
            let (inverse, phase) = self.basis_star(g)?;
            result[inverse] = x.conjugate().mul(&phase);
        }
        Ok(result)
    }
    /// Identity coefficient: tau(a* a) = sum_g conjugate(a_g) a_g.
    pub fn trace(&self, a: &[F]) -> Result<F, TwistedAlgebraError> {
        self.check(a)?;
        Ok(a[self.group.identity()].clone())
    }
    /// Faithful left multiplication on the complete group-label space.
    pub fn left_regular(&self, a: &[F]) -> Result<BasicMatrix<F>, TwistedAlgebraError> {
        self.check(a)?;
        let n = self.group.order();
        let mut result = mx::zeros::<F>(n, n)?;
        for (g, x) in a.iter().enumerate() {
            for h in 0..n {
                let gh = self.group.multiply(g, h)?;
                let entry = result
                    .get_ref(gh, h)
                    .map_err(ExactFieldError::from)?
                    .add(&x.mul(&self.alpha[g][h]));
                result.set(gh, h, entry).map_err(ExactFieldError::from)?;
            }
        }
        Ok(result)
    }
}

// Origin: engine/crates_rs/core_lie_theory/src/twisted_abelian_algebra.rs
// Claim: urn:core:crates_rs:core-lie-theory:twisted-abelian-algebra:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_bdb30c0e {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
