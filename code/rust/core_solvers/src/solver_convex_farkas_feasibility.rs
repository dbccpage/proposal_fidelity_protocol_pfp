// AuthorityEffect: None.

//! Exact rational feasibility of a finite inequality system `M v <= b`.
//!
//! Either a rational point satisfies every row, or a Farkas certificate
//! `eta >= 0`, `eta^T M = 0`, `eta^T b < 0` shows that none does: summing the
//! rows with weights `eta` gives `0 <= eta^T b < 0`. Exactly one of the two
//! exists (Farkas' lemma for inequalities over an ordered field).
//!
//! [`LinearInequalitySystem::decide`] proposes one of them with the existing
//! two-phase simplex of [`crate::solver_lp_standard_form`]; the proposal is then
//! replayed by [`LinearInequalitySystem::is_satisfied_by`] or
//! [`LinearInequalitySystem::verify_farkas`], which use only rational
//! arithmetic on the caller's rows. A spent pivot budget is a typed
//! [`FeasibilityError::BudgetExhausted`], never a verdict.

use crate::solver_lp_standard_form::{StandardLp, StandardLpError};
use num_rational::BigRational as Q;
use num_traits::{One, Signed, Zero};
use thiserror::Error;

/// Refusals of the feasibility contract.
#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum FeasibilityError {
    #[error("row {row} has {actual} entries, expected {expected}")]
    Ragged {
        row: usize,
        expected: usize,
        actual: usize,
    },
    #[error("{rows} rows but {rhs} right-hand sides")]
    RhsCount { rows: usize, rhs: usize },
    #[error("vector has {actual} entries, expected {expected}")]
    Length { expected: usize, actual: usize },
    #[error("a rational entry has a non-positive denominator")]
    InvalidRational,
    #[error("the declared pivot budget was exhausted; feasibility is unknown")]
    BudgetExhausted,
    #[error("the proposed certificate failed independent replay")]
    CertificateMismatch,
}

/// Why a claimed Farkas certificate does not certify infeasibility.
#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum FarkasDefect {
    #[error("{actual} multipliers for {expected} rows")]
    Length { expected: usize, actual: usize },
    #[error("multiplier {row} is negative")]
    NegativeMultiplier { row: usize },
    #[error("the combination is nonzero at column {column}")]
    NonzeroCombination { column: usize },
    #[error("the combined right-hand side is not negative")]
    NonNegativeBound,
}

/// The two exclusive outcomes, each with its replayable witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum FeasibilityVerdict {
    Feasible { point: Vec<Q> },
    Infeasible { multipliers: Vec<Q> },
}

/// `M v <= b` with `columns` unknowns.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LinearInequalitySystem {
    columns: usize,
    rows: Vec<Vec<Q>>,
    rhs: Vec<Q>,
}

fn valid(x: &Q) -> bool {
    x.denom().is_positive()
}

impl LinearInequalitySystem {
    pub fn try_new(
        columns: usize,
        rows: Vec<Vec<Q>>,
        rhs: Vec<Q>,
    ) -> Result<Self, FeasibilityError> {
        if rows.len() != rhs.len() {
            return Err(FeasibilityError::RhsCount {
                rows: rows.len(),
                rhs: rhs.len(),
            });
        }
        for (row, entries) in rows.iter().enumerate() {
            if entries.len() != columns {
                return Err(FeasibilityError::Ragged {
                    row,
                    expected: columns,
                    actual: entries.len(),
                });
            }
        }
        if rows.iter().flatten().chain(&rhs).any(|x| !valid(x)) {
            return Err(FeasibilityError::InvalidRational);
        }
        Ok(Self { columns, rows, rhs })
    }

    /// An empty system in `columns` unknowns.
    pub fn empty(columns: usize) -> Self {
        Self {
            columns,
            rows: Vec::new(),
            rhs: Vec::new(),
        }
    }

    /// Appends `row . v <= bound`.
    pub fn push_le(&mut self, row: Vec<Q>, bound: Q) -> Result<(), FeasibilityError> {
        if row.len() != self.columns {
            return Err(FeasibilityError::Ragged {
                row: self.rows.len(),
                expected: self.columns,
                actual: row.len(),
            });
        }
        if row.iter().chain([&bound]).any(|x| !valid(x)) {
            return Err(FeasibilityError::InvalidRational);
        }
        self.rows.push(row);
        self.rhs.push(bound);
        Ok(())
    }

    /// Appends `row . v = value` as two inequalities.
    pub fn push_eq(&mut self, row: Vec<Q>, value: Q) -> Result<(), FeasibilityError> {
        let negated: Vec<Q> = row.iter().map(|x| -x).collect();
        self.push_le(row, value.clone())?;
        self.push_le(negated, -value)
    }

    pub fn columns(&self) -> usize {
        self.columns
    }
    pub fn rows(&self) -> &[Vec<Q>] {
        &self.rows
    }
    pub fn rhs(&self) -> &[Q] {
        &self.rhs
    }

    /// Whether `point` satisfies every row.
    pub fn is_satisfied_by(&self, point: &[Q]) -> Result<bool, FeasibilityError> {
        if point.len() != self.columns {
            return Err(FeasibilityError::Length {
                expected: self.columns,
                actual: point.len(),
            });
        }
        if point.iter().any(|x| !valid(x)) {
            return Err(FeasibilityError::InvalidRational);
        }
        Ok(self
            .rows
            .iter()
            .zip(&self.rhs)
            .all(|(row, b)| &dot(row, point) <= b))
    }

    /// Replays a Farkas certificate.
    pub fn verify_farkas(&self, multipliers: &[Q]) -> Result<(), FarkasDefect> {
        if multipliers.len() != self.rows.len() {
            return Err(FarkasDefect::Length {
                expected: self.rows.len(),
                actual: multipliers.len(),
            });
        }
        if let Some(row) = multipliers
            .iter()
            .position(|x| !valid(x) || x.is_negative())
        {
            return Err(FarkasDefect::NegativeMultiplier { row });
        }
        for column in 0..self.columns {
            let combined: Q = self
                .rows
                .iter()
                .zip(multipliers)
                .map(|(row, eta)| &row[column] * eta)
                .sum();
            if !combined.is_zero() {
                return Err(FarkasDefect::NonzeroCombination { column });
            }
        }
        if !dot(&self.rhs, multipliers).is_negative() {
            return Err(FarkasDefect::NonNegativeBound);
        }
        Ok(())
    }

    /// Decides feasibility and returns a replayed witness for the answer.
    pub fn decide(&self, max_pivots: usize) -> Result<FeasibilityVerdict, FeasibilityError> {
        let (r, c) = (self.rows.len(), self.columns);
        // v = v_plus - v_minus, slack s >= 0: M v_plus - M v_minus + s = b.
        let mut matrix = Vec::with_capacity(r);
        for (i, row) in self.rows.iter().enumerate() {
            let mut line: Vec<Q> = row.clone();
            line.extend(row.iter().map(|x| -x));
            line.extend((0..r).map(|j| if i == j { Q::one() } else { Q::zero() }));
            matrix.push(line);
        }
        let point_lp = StandardLp::new(vec![Q::zero(); 2 * c + r], matrix, self.rhs.clone())
            .map_err(|_| FeasibilityError::InvalidRational)?;
        match point_lp.solve(max_pivots) {
            Ok(solution) => {
                let point: Vec<Q> = (0..c)
                    .map(|j| &solution.primal[j] - &solution.primal[c + j])
                    .collect();
                if self.is_satisfied_by(&point)? {
                    return Ok(FeasibilityVerdict::Feasible { point });
                }
                Err(FeasibilityError::CertificateMismatch)
            }
            Err(StandardLpError::Infeasible) => self.farkas(max_pivots),
            Err(StandardLpError::BudgetExhausted) => Err(FeasibilityError::BudgetExhausted),
            Err(_) => Err(FeasibilityError::CertificateMismatch),
        }
    }

    fn farkas(&self, max_pivots: usize) -> Result<FeasibilityVerdict, FeasibilityError> {
        let (r, c) = (self.rows.len(), self.columns);
        // eta >= 0, M^T eta = 0, b^T eta = -1.
        let mut matrix: Vec<Vec<Q>> = (0..c)
            .map(|j| self.rows.iter().map(|row| row[j].clone()).collect())
            .collect();
        matrix.push(self.rhs.clone());
        let mut rhs = vec![Q::zero(); c];
        rhs.push(-Q::one());
        let lp = StandardLp::new(vec![Q::zero(); r], matrix, rhs)
            .map_err(|_| FeasibilityError::InvalidRational)?;
        match lp.solve(max_pivots) {
            Ok(solution) => {
                if self.verify_farkas(&solution.primal).is_ok() {
                    Ok(FeasibilityVerdict::Infeasible {
                        multipliers: solution.primal,
                    })
                } else {
                    Err(FeasibilityError::CertificateMismatch)
                }
            }
            Err(StandardLpError::BudgetExhausted) => Err(FeasibilityError::BudgetExhausted),
            Err(_) => Err(FeasibilityError::CertificateMismatch),
        }
    }
}

fn dot(a: &[Q], b: &[Q]) -> Q {
    a.iter().zip(b).map(|(x, y)| x * y).sum()
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use num_bigint::BigInt;

    fn q(n: i64) -> Q {
        Q::from_integer(BigInt::from(n))
    }

    #[test]
    fn feasible_box_returns_a_replayed_point() {
        // 0 <= v0 <= 1, v1 = v0 + 2.
        let mut sys = LinearInequalitySystem::empty(2);
        sys.push_le(vec![q(1), q(0)], q(1)).unwrap();
        sys.push_le(vec![q(-1), q(0)], q(0)).unwrap();
        sys.push_eq(vec![q(-1), q(1)], q(2)).unwrap();
        match sys.decide(200).unwrap() {
            FeasibilityVerdict::Feasible { point } => {
                assert!(sys.is_satisfied_by(&point).unwrap());
                assert_eq!(&point[1] - &point[0], q(2));
            }
            other => panic!("expected feasible, got {other:?}"),
        }
    }

    #[test]
    fn infeasible_pair_returns_a_replayed_farkas_certificate() {
        // v <= 0 and -v <= -1.
        let sys =
            LinearInequalitySystem::try_new(1, vec![vec![q(1)], vec![q(-1)]], vec![q(0), q(-1)])
                .unwrap();
        match sys.decide(200).unwrap() {
            FeasibilityVerdict::Infeasible { multipliers } => {
                assert!(sys.verify_farkas(&multipliers).is_ok());
            }
            other => panic!("expected infeasible, got {other:?}"),
        }
    }

    #[test]
    fn tampered_farkas_certificates_are_rejected() {
        let sys =
            LinearInequalitySystem::try_new(1, vec![vec![q(1)], vec![q(-1)]], vec![q(0), q(-1)])
                .unwrap();
        assert!(sys.verify_farkas(&[q(1), q(1)]).is_ok());
        assert_eq!(
            sys.verify_farkas(&[q(1), q(2)]),
            Err(FarkasDefect::NonzeroCombination { column: 0 })
        );
        assert_eq!(
            sys.verify_farkas(&[q(-1), q(-1)]),
            Err(FarkasDefect::NegativeMultiplier { row: 0 })
        );
        assert_eq!(
            sys.verify_farkas(&[q(0), q(0)]),
            Err(FarkasDefect::NonNegativeBound)
        );
        assert_eq!(
            sys.verify_farkas(&[q(1)]),
            Err(FarkasDefect::Length {
                expected: 2,
                actual: 1
            })
        );
    }

    #[test]
    fn boundary_cases() {
        // No rows: feasible at the origin.
        let sys = LinearInequalitySystem::empty(3);
        assert!(matches!(
            sys.decide(10).unwrap(),
            FeasibilityVerdict::Feasible { .. }
        ));
        // 0 <= -1 with no unknowns: infeasible, multiplier 1.
        let sys = LinearInequalitySystem::try_new(0, vec![vec![]], vec![q(-1)]).unwrap();
        assert_eq!(
            sys.decide(10).unwrap(),
            FeasibilityVerdict::Infeasible {
                multipliers: vec![q(1)]
            }
        );
        // Touching boundary v <= 0, -v <= 0 is feasible.
        let sys =
            LinearInequalitySystem::try_new(1, vec![vec![q(1)], vec![q(-1)]], vec![q(0), q(0)])
                .unwrap();
        assert!(matches!(
            sys.decide(10).unwrap(),
            FeasibilityVerdict::Feasible { .. }
        ));
    }

    #[test]
    fn malformed_input_and_budget_are_typed() {
        assert!(matches!(
            LinearInequalitySystem::try_new(2, vec![vec![q(1)]], vec![q(0)]),
            Err(FeasibilityError::Ragged { .. })
        ));
        assert!(matches!(
            LinearInequalitySystem::try_new(1, vec![vec![q(1)]], vec![]),
            Err(FeasibilityError::RhsCount { .. })
        ));
        let sys = LinearInequalitySystem::try_new(1, vec![vec![q(-1)]], vec![q(-1)]).unwrap();
        assert!(matches!(
            sys.is_satisfied_by(&[q(1), q(2)]),
            Err(FeasibilityError::Length { .. })
        ));
        assert_eq!(sys.decide(0), Err(FeasibilityError::BudgetExhausted));
    }
}
