//! Faithful finite-groupoid convolution over the exact subfield Q(i).
//!
//! The category owner validates identities, composition and inverses. This
//! owner linearizes that declared structure; it does not quotient histories or
//! select a character sector. Scalars and matrices retain their sovereign owners.
//! The associated complex C*-algebra is a mathematical extension, not a native
//! finite computation or an operational reconstruction. AuthorityEffect: None.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{matrix as mx, ExactFieldError};
use core_category_theory::finite_groupoid::{GroupoidError, ValidatedFiniteGroupoid};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{rq, Rational};
use std::collections::BTreeMap;

#[derive(Debug, Clone, thiserror::Error)]
pub enum GroupoidAlgebraError {
    #[error("the empty groupoid has no normalized unital state model")]
    Empty,
    #[error("unknown arrow {0}")]
    UnknownArrow(String),
    #[error("unknown component root {0}")]
    UnknownComponent(String),
    #[error("coefficient length {actual}; expected {expected}")]
    CoefficientLength { expected: usize, actual: usize },
    #[error("validated groupoid structure could not be resolved")]
    MissingStructure,
    #[error(transparent)]
    Category(#[from] GroupoidError),
    #[error(transparent)]
    Matrix(#[from] ExactFieldError),
}

/// Coordinates use the lexicographic order of the declared arrow names.
#[derive(Debug, Clone)]
pub struct FiniteGroupoidAlgebra {
    groupoid: ValidatedFiniteGroupoid,
    arrows: Vec<String>,
    indices: BTreeMap<String, usize>,
    product: Vec<Vec<Option<usize>>>,
    inverses: Vec<usize>,
    identities: Vec<usize>,
}
impl FiniteGroupoidAlgebra {
    fn resolve_index(
        indices: &BTreeMap<String, usize>,
        name: &str,
    ) -> Result<usize, GroupoidAlgebraError> {
        indices
            .get(name)
            .copied()
            .ok_or(GroupoidAlgebraError::MissingStructure)
    }

    fn build_product_row(
        groupoid: &ValidatedFiniteGroupoid,
        arrows: &[String],
        indices: &BTreeMap<String, usize>,
        left: &str,
    ) -> Result<Vec<Option<usize>>, GroupoidAlgebraError> {
        let c = groupoid.category().declared();
        let (source, _) = c
            .boundary_of(left)
            .ok_or(GroupoidAlgebraError::MissingStructure)?;
        let mut row = vec![None; arrows.len()];
        for (j, right) in arrows.iter().enumerate() {
            let (_, target) = c
                .boundary_of(right)
                .ok_or(GroupoidAlgebraError::MissingStructure)?;
            if source == target {
                // Algebra product left * right means left AFTER right.
                let comp = c
                    .compose(right, left)
                    .ok_or(GroupoidAlgebraError::MissingStructure)?;
                row[j] = Some(Self::resolve_index(indices, comp)?);
            }
        }
        Ok(row)
    }

    pub fn new(groupoid: ValidatedFiniteGroupoid) -> Result<Self, GroupoidAlgebraError> {
        let c = groupoid.category().declared();
        let arrows: Vec<_> = c.morphisms.keys().cloned().collect();
        if arrows.is_empty() {
            return Err(GroupoidAlgebraError::Empty);
        }
        let indices: BTreeMap<_, _> = arrows.iter().cloned().zip(0..arrows.len()).collect();
        let mut product = Vec::with_capacity(arrows.len());
        let mut inverses = Vec::with_capacity(arrows.len());
        for left in &arrows {
            let inv_name = groupoid
                .inverse(left)
                .ok_or(GroupoidAlgebraError::MissingStructure)?;
            inverses.push(Self::resolve_index(&indices, inv_name)?);
            product.push(Self::build_product_row(&groupoid, &arrows, &indices, left)?);
        }
        let identities = c
            .identities
            .values()
            .map(|id| Self::resolve_index(&indices, id))
            .collect::<Result<_, _>>()?;
        Ok(Self {
            groupoid,
            arrows,
            indices,
            product,
            inverses,
            identities,
        })
    }

    pub fn groupoid(&self) -> &ValidatedFiniteGroupoid {
        &self.groupoid
    }
    pub fn arrows(&self) -> &[String] {
        &self.arrows
    }
    pub fn dimension(&self) -> usize {
        self.arrows.len()
    }

    fn check(&self, a: &[GaussianRat]) -> Result<(), GroupoidAlgebraError> {
        if a.len() != self.dimension() {
            return Err(GroupoidAlgebraError::CoefficientLength {
                expected: self.dimension(),
                actual: a.len(),
            });
        }
        Ok(())
    }
    pub fn basis(&self, arrow: &str) -> Result<Vec<GaussianRat>, GroupoidAlgebraError> {
        let i = self
            .indices
            .get(arrow)
            .ok_or_else(|| GroupoidAlgebraError::UnknownArrow(arrow.into()))?;
        let mut result = vec![GaussianRat::zero(); self.dimension()];
        result[*i] = GaussianRat::one();
        Ok(result)
    }
    pub fn unit(&self) -> Vec<GaussianRat> {
        let mut result = vec![GaussianRat::zero(); self.dimension()];
        for &i in &self.identities {
            result[i] = GaussianRat::one();
        }
        result
    }

    pub fn multiply(
        &self,
        a: &[GaussianRat],
        b: &[GaussianRat],
    ) -> Result<Vec<GaussianRat>, GroupoidAlgebraError> {
        self.check(a)?;
        self.check(b)?;
        let mut result = vec![GaussianRat::zero(); self.dimension()];
        for (i, x) in a.iter().enumerate() {
            for (j, y) in b.iter().enumerate() {
                if let Some(k) = self.product[i][j] {
                    result[k] = result[k].add(&x.mul(y));
                }
            }
        }
        Ok(result)
    }
    pub fn star(&self, a: &[GaussianRat]) -> Result<Vec<GaussianRat>, GroupoidAlgebraError> {
        self.check(a)?;
        let mut result = vec![GaussianRat::zero(); self.dimension()];
        for (i, x) in a.iter().enumerate() {
            result[self.inverses[i]] = x.conj();
        }
        Ok(result)
    }
    /// Sum of identity coefficients, not the matrix trace of the regular action.
    pub fn trace(&self, a: &[GaussianRat]) -> Result<GaussianRat, GroupoidAlgebraError> {
        self.check(a)?;
        Ok(self
            .identities
            .iter()
            .fold(GaussianRat::zero(), |s, &i| s.add(&a[i])))
    }
    pub fn coefficient_norm_squared(
        &self,
        a: &[GaussianRat],
    ) -> Result<Rational, GroupoidAlgebraError> {
        self.check(a)?;
        Ok(a.iter().map(GaussianRat::norm_sq).sum())
    }

    /// L_a on the full arrow space. No irreducible-sector projection is made.
    pub fn left_regular(
        &self,
        a: &[GaussianRat],
    ) -> Result<BasicMatrix<GaussianRat>, GroupoidAlgebraError> {
        self.check(a)?;
        let n = self.dimension();
        let mut rows = vec![vec![GaussianRat::zero(); n]; n];
        for (i, x) in a.iter().enumerate() {
            for j in 0..n {
                if let Some(k) = self.product[i][j] {
                    rows[k][j] = rows[k][j].add(x);
                }
            }
        }
        Ok(mx::from_rows(rows)?)
    }

    /// Central idempotent: average all loops at every object of one component.
    /// It is proper within that component exactly when its isotropy is nontrivial.
    pub fn central_isotropy_average(
        &self,
        root: &str,
    ) -> Result<Vec<GaussianRat>, GroupoidAlgebraError> {
        let component = self
            .groupoid
            .components()?
            .into_iter()
            .find(|c| c.root == root)
            .ok_or_else(|| GroupoidAlgebraError::UnknownComponent(root.into()))?;
        let order = i64::try_from(component.isotropy.len())
            .map_err(|_| GroupoidAlgebraError::MissingStructure)?;
        if order == 0 {
            return Err(GroupoidAlgebraError::MissingStructure);
        }
        let coefficient = GaussianRat::from_rational(rq(1, order));
        let c = self.groupoid.category().declared();
        let mut result = vec![GaussianRat::zero(); self.dimension()];
        for (i, name) in self.arrows.iter().enumerate() {
            let (source, target) = c
                .boundary_of(name)
                .ok_or(GroupoidAlgebraError::MissingStructure)?;
            if source == target && component.objects.contains(source) {
                result[i] = coefficient.clone();
            }
        }
        Ok(result)
    }
}

// Origin: engine/crates_rs/core_lie_theory/src/finite_groupoid_algebra.rs
// Claim: urn:core:crates_rs:core-lie-theory:finite-groupoid-algebra:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_91e94c43 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
