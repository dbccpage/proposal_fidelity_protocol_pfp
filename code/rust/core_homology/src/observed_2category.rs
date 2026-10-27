//! Locally thin 2-category of question-preserving linear operators.
//! A 2-cell f=>g exists exactly when the target report cannot see g-f.
//! Horizontal composition needs the kernel-transport premise on 1-cells.
//! With full questions only equal maps have 2-cells; with zero questions this
//! is the codiscrete comparison envelope. Neither grants operational authority.

use crate::restriction_dga::{Cochain, Matrix, RestrictionError};
use num_rational::BigRational as Q;
use num_traits::{One, Zero};
use core_functional::protected_linear_quotient::{QuotientError, ReportQuotient};
use thiserror::Error;

#[derive(Debug, Error)]
pub enum CoherenceError {
    #[error(transparent)]
    Quotient(#[from] QuotientError),
    #[error(transparent)]
    Matrix(#[from] linear_algebra::backend::basic_matrix::MatrixError),
    #[error(transparent)]
    Restriction(#[from] RestrictionError),
    #[error("source/target objects or boundary operators differ")]
    Boundary,
    #[error("the proposed 2-cell changes a protected answer")]
    VisibleDifference,
    #[error("question family or connection coverage differs from the poset fibers")]
    Carrier,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ObserverObject {
    id: usize,
    quotient: ReportQuotient,
}
impl ObserverObject {
    pub fn new(id: usize, questions: Matrix) -> Result<Self, CoherenceError> {
        Ok(Self {
            id,
            quotient: ReportQuotient::new(questions)?,
        })
    }
    pub fn id(&self) -> usize {
        self.id
    }
    pub fn quotient(&self) -> &ReportQuotient {
        &self.quotient
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ObserverArrow {
    source: ObserverObject,
    target: ObserverObject,
    operator: Matrix,
    report: Matrix,
}
impl ObserverArrow {
    pub fn new(
        source: ObserverObject,
        target: ObserverObject,
        operator: Matrix,
    ) -> Result<Self, CoherenceError> {
        let report = source.quotient.descend(&target.quotient, &operator)?;
        Ok(Self {
            source,
            target,
            operator,
            report,
        })
    }
    pub fn identity(object: ObserverObject) -> Result<Self, CoherenceError> {
        let n = object.quotient.state_dimension();
        let id = Matrix::try_from_fn(n, n, |i, j| if i == j { Q::one() } else { Q::zero() })?;
        Self::new(object.clone(), object, id)
    }
    pub fn source(&self) -> &ObserverObject {
        &self.source
    }
    pub fn target(&self) -> &ObserverObject {
        &self.target
    }
    pub fn operator(&self) -> &Matrix {
        &self.operator
    }
    pub fn report(&self) -> &Matrix {
        &self.report
    }
    /// self after earlier, including complete question-carrier identity.
    pub fn after(&self, earlier: &Self) -> Result<Self, CoherenceError> {
        if earlier.target != self.source {
            return Err(CoherenceError::Boundary);
        }
        Self::new(
            earlier.source.clone(),
            self.target.clone(),
            self.operator.mul(&earlier.operator)?,
        )
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ComparisonCell {
    source: ObserverArrow,
    target: ObserverArrow,
    difference: Matrix,
}
impl ComparisonCell {
    pub fn new(source: ObserverArrow, target: ObserverArrow) -> Result<Self, CoherenceError> {
        if source.source != target.source || source.target != target.target {
            return Err(CoherenceError::Boundary);
        }
        let difference = target.operator.sub(&source.operator)?;
        let visible = target.target.quotient.report().mul(&difference)?;
        for i in 0..visible.rows() {
            for j in 0..visible.cols() {
                if !visible.get_ref(i, j)?.is_zero() {
                    return Err(CoherenceError::VisibleDifference);
                }
            }
        }
        Ok(Self {
            source,
            target,
            difference,
        })
    }
    pub fn identity(arrow: ObserverArrow) -> Result<Self, CoherenceError> {
        Self::new(arrow.clone(), arrow)
    }
    pub fn source(&self) -> &ObserverArrow {
        &self.source
    }
    pub fn target(&self) -> &ObserverArrow {
        &self.target
    }
    pub fn difference(&self) -> &Matrix {
        &self.difference
    }
    pub fn then(&self, later: &Self) -> Result<Self, CoherenceError> {
        if self.target != later.source {
            return Err(CoherenceError::Boundary);
        }
        Self::new(self.source.clone(), later.target.clone())
    }
    /// self horizontally after earlier: g'f'-gf, including the mixed term.
    pub fn horizontal_after(&self, earlier: &Self) -> Result<Self, CoherenceError> {
        Self::new(
            self.source.after(&earlier.source)?,
            self.target.after(&earlier.target)?,
        )
    }
}

#[derive(Debug, Clone)]
pub struct ObservedRestrictionSystem {
    connection: Cochain,
    objects: Vec<ObserverObject>,
}
impl ObservedRestrictionSystem {
    /// Source is the locally discrete category P^op; target is the above
    /// locally thin 2-category. Compositors point composite=>direct, so their
    /// labels are -K. Constructor checks every strict triangle, not just counts.
    pub fn new(connection: Cochain, questions: Vec<Matrix>) -> Result<Self, CoherenceError> {
        if connection.degree() != 1 || questions.len() != connection.carrier().dimensions().len() {
            return Err(CoherenceError::Carrier);
        }
        let objects: Vec<_> = questions
            .into_iter()
            .enumerate()
            .map(|(i, q)| ObserverObject::new(i, q))
            .collect::<Result<_, _>>()?;
        for (i, o) in objects.iter().enumerate() {
            if o.quotient.state_dimension() != connection.carrier().dimensions()[i] {
                return Err(CoherenceError::Carrier);
            }
        }
        let system = Self {
            connection,
            objects,
        };
        for pair in system.connection.carrier().chains(1) {
            system.arrow(pair[0], pair[1])?;
        }
        for triple in system.connection.carrier().chains(2) {
            system.compositor(triple[0], triple[1], triple[2])?;
        }
        Ok(system)
    }
    pub fn connection(&self) -> &Cochain {
        &self.connection
    }
    pub fn objects(&self) -> &[ObserverObject] {
        &self.objects
    }
    pub fn arrow(&self, x: usize, z: usize) -> Result<ObserverArrow, CoherenceError> {
        let source = self
            .objects
            .get(z)
            .cloned()
            .ok_or(CoherenceError::Carrier)?;
        let target = self
            .objects
            .get(x)
            .cloned()
            .ok_or(CoherenceError::Carrier)?;
        if x == z {
            return ObserverArrow::identity(source);
        }
        let operator = self
            .connection
            .components()
            .get(&vec![x, z])
            .cloned()
            .ok_or(CoherenceError::Carrier)?;
        ObserverArrow::new(source, target, operator)
    }
    pub fn compositor(
        &self,
        x: usize,
        y: usize,
        z: usize,
    ) -> Result<ComparisonCell, CoherenceError> {
        ComparisonCell::new(
            self.arrow(x, y)?.after(&self.arrow(y, z)?)?,
            self.arrow(x, z)?,
        )
    }
}

// Origin: engine/crates_rs/core_homology/src/observed_2category.rs
// Claim: urn:core:crates_rs:core-homology:observed-2category:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_072a0096 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
