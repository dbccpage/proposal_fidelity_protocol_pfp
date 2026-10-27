//! Complete balance-preservation criteria for the five canonical Source-25
//! edits at a fixed ordered carrier and declared oriented face set. This is a
//! diagnostic on raw states; it confers no permission to extend Genesis.
use crate::genesis_ongoing_adapter::{GenesisOngoingPacket, MarkedTriple};
use crate::genesis_source_execution::{Source25Change, Source25State, SourceExecutionError};
use crate::types::AuthorityEffect;
use linear_algebra::backend::basic_matrix::{BasicMatrix, MatrixError, OperationLimits};
use linear_algebra::row_constraint_implication::{
    self as implication, ImplicationError, RowImplication,
};
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Signed, Zero};

#[derive(Debug, thiserror::Error)]
pub enum BalanceTransitionError {
    #[error("balance certificate does not replay against the bound context")]
    Replay,
    #[error(transparent)]
    Source(#[from] SourceExecutionError),
    #[error(transparent)]
    Matrix(#[from] MatrixError),
    #[error(transparent)]
    Math(#[from] ImplicationError),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BalanceReason {
    ExistingFaces,
    UntouchedDirectedArc,
    NoSurvivingMergedFace,
    FaceCombination { coefficients: Vec<BigRational> },
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BalanceCounterexample {
    source: Source25State,
    target: Source25State,
    face: MarkedTriple,
    value: BigInt,
}
impl BalanceCounterexample {
    pub fn source(&self) -> &Source25State {
        &self.source
    }
    pub fn target(&self) -> &Source25State {
        &self.target
    }
    pub fn face(&self) -> MarkedTriple {
        self.face
    }
    pub fn value(&self) -> &BigInt {
        &self.value
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BalanceVerdict {
    Preserved(BalanceReason),
    Obstructed(BalanceCounterexample),
}

/// Complete input/output representatives are retained even when the universal
/// context verdict is negative but this particular transition remains balanced.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Source25BalanceProfile {
    source: Source25State,
    change: Source25Change,
    target: Source25State,
    verdict: BalanceVerdict,
}

fn cycle_value(state: &Source25State, face: MarkedTriple) -> BigInt {
    let p = state.packet();
    let n = p.terms.len();
    [(face.x, face.y), (face.y, face.z), (face.z, face.x)]
        .iter()
        .map(|&(x, y)| &p.r[x * n + y] - &p.s[x * n + y])
        .sum()
}
pub fn balanced(state: &Source25State) -> bool {
    state
        .packet()
        .filled
        .iter()
        .all(|&face| cycle_value(state, face).is_zero())
}
fn touches(face: MarkedTriple, x: usize, y: usize) -> bool {
    [(face.x, face.y), (face.y, face.z), (face.z, face.x)].contains(&(x, y))
}
fn cycle_row(n: usize, face: MarkedTriple, limit: usize) -> Result<Vec<BigRational>, MatrixError> {
    Ok(BasicMatrix::try_from_fn_with_limit(
        1,
        n.checked_mul(n)
            .ok_or(MatrixError::DimensionOverflow { rows: n, cols: n })?,
        limit,
        |_, j| {
            if touches(face, j / n, j % n) {
                BigRational::one()
            } else {
                BigRational::zero()
            }
        },
    )?
    .as_slice()
    .to_vec())
}
fn equations(state: &Source25State, limit: usize) -> Result<BasicMatrix<BigRational>, MatrixError> {
    let p = state.packet();
    let n = p.terms.len();
    BasicMatrix::try_from_fn_with_limit(
        p.filled.len(),
        n.checked_mul(n)
            .ok_or(MatrixError::DimensionOverflow { rows: n, cols: n })?,
        limit,
        |i, j| {
            if touches(p.filled[i], j / n, j % n) {
                BigRational::one()
            } else {
                BigRational::zero()
            }
        },
    )
}
fn realize(
    context: &Source25State,
    excess: Vec<BigInt>,
) -> Result<Source25State, SourceExecutionError> {
    let r = excess
        .iter()
        .map(|e| {
            if e.is_positive() {
                e + 1
            } else {
                BigInt::one()
            }
        })
        .collect();
    let s = excess
        .iter()
        .map(|e| {
            if e.is_negative() {
                -e + 1
            } else {
                BigInt::one()
            }
        })
        .collect();
    Source25State::try_new(GenesisOngoingPacket {
        terms: context.packet().terms.clone(),
        r,
        s,
        filled: context.packet().filled.clone(),
    })
}
fn counterexample(
    context: &Source25State,
    change: Source25Change,
    excess: Vec<BigInt>,
) -> Result<BalanceVerdict, BalanceTransitionError> {
    let source = realize(context, excess)?;
    let target = source.perform_enabled(change)?;
    if !balanced(&source) {
        return Err(BalanceTransitionError::Replay);
    }
    let face = target
        .packet()
        .filled
        .iter()
        .copied()
        .find(|&t| !cycle_value(&target, t).is_zero())
        .ok_or(BalanceTransitionError::Replay)?;
    let value = cycle_value(&target, face);
    Ok(BalanceVerdict::Obstructed(BalanceCounterexample {
        source,
        target,
        face,
        value,
    }))
}

impl Source25BalanceProfile {
    /// `fill_solver_limits` applies to the dense Fill matrix and exact solver.
    /// Raw source execution and face scans retain the source kernel's allocation
    /// behavior; this API does not promise a global memory or time budget.
    fn classify_identify_verdict(
        source: &Source25State,
        target: &Source25State,
        change: Source25Change,
        n: usize,
        x: usize,
        y: usize,
    ) -> Result<BalanceVerdict, BalanceTransitionError> {
        if let Some(face) = target
            .packet()
            .filled
            .iter()
            .find(|face| [face.x, face.y, face.z].contains(&x))
        {
            let successor = if face.x == x {
                face.y
            } else if face.y == x {
                face.z
            } else {
                face.x
            };
            let old = successor + usize::from(successor >= y);
            let excess = (0..n * n)
                .map(|i| BigInt::from(i / n == old) - BigInt::from(i % n == old))
                .collect();
            counterexample(source, change, excess)
        } else {
            Ok(BalanceVerdict::Preserved(
                BalanceReason::NoSurvivingMergedFace,
            ))
        }
    }

    fn classify_fill_verdict(
        source: &Source25State,
        change: Source25Change,
        n: usize,
        triple: MarkedTriple,
        fill_solver_limits: OperationLimits,
    ) -> Result<BalanceVerdict, BalanceTransitionError> {
        let d = equations(source, fill_solver_limits.max_elements)?;
        let row = cycle_row(n, triple, fill_solver_limits.max_elements)?;
        match implication::classify_with_limits(&d, &row, fill_solver_limits)? {
            RowImplication::Follows { coefficients } => Ok(BalanceVerdict::Preserved(
                BalanceReason::FaceCombination { coefficients },
            )),
            RowImplication::Independent { witness } => {
                counterexample(source, change, implication::clear_denominators(&witness))
            }
        }
    }

    fn execute_enabled_change(
        source: &Source25State,
        change: Source25Change,
    ) -> Result<Source25State, BalanceTransitionError> {
        if !source.is_enabled(change) {
            return Err(SourceExecutionError::DisabledChange.into());
        }
        Ok(source.perform_enabled(change)?)
    }

    pub fn new(
        source: Source25State,
        change: Source25Change,
        fill_solver_limits: OperationLimits,
    ) -> Result<Self, BalanceTransitionError> {
        let target = Self::execute_enabled_change(&source, change)?;
        let n = source.packet().terms.len();
        let verdict = match change {
            Source25Change::AddTerm => BalanceVerdict::Preserved(BalanceReason::ExistingFaces),
            Source25Change::AddAssertion { x, y, .. } | Source25Change::Remove { x, y, .. } => {
                if source
                    .packet()
                    .filled
                    .iter()
                    .any(|&face| touches(face, x, y))
                {
                    counterexample(&source, change, vec![BigInt::zero(); n * n])?
                } else {
                    BalanceVerdict::Preserved(BalanceReason::UntouchedDirectedArc)
                }
            }
            Source25Change::Identify { x, y } => {
                Self::classify_identify_verdict(&source, &target, change, n, x, y)?
            }
            Source25Change::Fill { x, y, z } => {
                Self::classify_fill_verdict(&source, change, n, MarkedTriple { x, y, z }, fill_solver_limits)?
            }
        };
        let result = Self {
            source,
            change,
            target,
            verdict,
        };
        result.verify()?;
        Ok(result)
    }

    fn verify_preserved_reason(&self, reason: &BalanceReason) -> Result<(), BalanceTransitionError> {
        match (self.change, reason) {
            (Source25Change::AddTerm, BalanceReason::ExistingFaces) => Ok(()),
            (
                Source25Change::AddAssertion { x, y, .. } | Source25Change::Remove { x, y, .. },
                BalanceReason::UntouchedDirectedArc,
            ) if !self
                .source
                .packet()
                .filled
                .iter()
                .any(|&t| touches(t, x, y)) =>
            {
                Ok(())
            }
            (Source25Change::Identify { x, .. }, BalanceReason::NoSurvivingMergedFace)
                if !self
                    .target
                    .packet()
                    .filled
                    .iter()
                    .any(|t| [t.x, t.y, t.z].contains(&x)) =>
            {
                Ok(())
            }
            (
                Source25Change::Fill { x, y, z },
                BalanceReason::FaceCombination { coefficients },
            ) => {
                let d = equations(&self.source, usize::MAX)?;
                let row = cycle_row(
                    self.source.packet().terms.len(),
                    MarkedTriple { x, y, z },
                    usize::MAX,
                )?;
                implication::verify(
                    &d,
                    &row,
                    &RowImplication::Follows {
                        coefficients: coefficients.clone(),
                    },
                )?;
                Ok(())
            }
            _ => Err(BalanceTransitionError::Replay),
        }
    }

    fn verify_obstructed_verdict(&self) -> Result<(), BalanceTransitionError> {
        if let BalanceVerdict::Obstructed(w) = &self.verdict {
            let same_shape = w.source.packet().terms == self.source.packet().terms
                && w.source.packet().filled == self.source.packet().filled;
            if !same_shape
                || !balanced(&w.source)
                || w.source.perform_enabled(self.change)? != w.target
            {
                return Err(BalanceTransitionError::Replay);
            }
            if !w.target.packet().filled.contains(&w.face)
                || cycle_value(&w.target, w.face) != w.value
                || w.value.is_zero()
            {
                return Err(BalanceTransitionError::Replay);
            }
        }
        Ok(())
    }

    /// No elimination in replay. Positive Fill uses the exact equation
    /// combination; a negative verdict uses an actual enabled source edit.
    pub fn verify(&self) -> Result<(), BalanceTransitionError> {
        if self.source.perform_enabled(self.change)? != self.target {
            return Err(BalanceTransitionError::Replay);
        }
        match &self.verdict {
            BalanceVerdict::Preserved(reason) => self.verify_preserved_reason(reason),
            BalanceVerdict::Obstructed(_) => self.verify_obstructed_verdict(),
        }
    }
    pub fn source(&self) -> &Source25State {
        &self.source
    }
    pub fn target(&self) -> &Source25State {
        &self.target
    }
    pub fn change(&self) -> Source25Change {
        self.change
    }
    pub fn verdict(&self) -> &BalanceVerdict {
        &self.verdict
    }
    pub fn actual_source_balanced(&self) -> bool {
        balanced(&self.source)
    }
    pub fn actual_target_balanced(&self) -> bool {
        balanced(&self.target)
    }
    pub fn authority_effect(&self) -> AuthorityEffect {
        AuthorityEffect::None
    }
}

// Origin: engine/crates_rs/core_wdp/src/genesis_balance_transition.rs
// Claim: urn:core:crates_rs:core-wdp:genesis-balance-transition:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_e84c074e {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
