// AuthorityEffect: None.

//! Proposals for the raw-versus-quotient `Gamma` comparison, each replayed by
//! the checkers in `core_functional::gamma_reconciliation`.
//!
//! - [`quotient_gamma`] computes `Gamma_quot(x) = min_u ||D x + A u||_{1,w}`
//!   with the existing exact weighted-`l1` projection solver.
//! - [`decide_value_agreement`] runs the `2^m` vertex systems through the exact
//!   feasibility module: either every vertex extends (a complete table, so the
//!   two values agree at every `x`), or one vertex has a Farkas certificate,
//!   from which an explicit `x` with `Gamma_quot(x) < Gamma_raw(x)` is built.
//! - [`decide_zero_test_agreement`] decides `im D ∩ im A = {0}` from a kernel
//!   basis of `[D | A]`, with a witness `D x + A u = 0`, `D x != 0` otherwise.
//!
//! No proposal is returned before the functional checker accepts it.

use crate::solver_convex_farkas_feasibility::{
    FeasibilityError, FeasibilityVerdict, LinearInequalitySystem,
};
use crate::solver_lp_exact_simplex::{solve_weighted_l1_projection, L1LpError};
use linear_algebra::backend::basic_matrix::{BasicMatrix, MatrixError};
use linear_algebra::exact_field::elimination;
use linear_algebra::exact_field::ExactFieldError;
use num_rational::BigRational as Q;
use num_traits::Zero;
use core_functional::gamma_reconciliation::{
    all_sign_vectors, GammaReconciliationError, QuotientGammaCertificate, RepairQuotientProblem,
    ValueGapWitness, VertexExtensionTable, VertexFarkasCertificate,
};
use thiserror::Error;

/// Refusals of the proposal layer.
#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum GammaSearchError {
    #[error(transparent)]
    Check(#[from] GammaReconciliationError),
    #[error("weighted l1 solver refused: {0}")]
    Solver(#[from] L1LpError),
    #[error("feasibility search refused: {0}")]
    Feasibility(#[from] FeasibilityError),
    #[error(transparent)]
    LinearAlgebra(#[from] ExactFieldError),
    #[error(transparent)]
    Storage(#[from] MatrixError),
    #[error("the quotient value at the separator is not below the raw value")]
    InconsistentSeparator,
}

/// Value agreement, with its replayed witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ValueAgreementVerdict {
    /// Every vertex extends: `Gamma_quot = Gamma_raw` at every `x`.
    Agree { table: VertexExtensionTable },
    /// One vertex fails; `quotient` certifies `Gamma_quot(gap.x)` exactly.
    Disagree {
        certificate: VertexFarkasCertificate,
        gap: ValueGapWitness,
        raw: Q,
        quotient: QuotientGammaCertificate,
    },
}

/// Zero-test agreement, with its witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ZeroTestVerdict {
    /// `rank D + rank A = rank [D | A]`, so `im D ∩ im A = {0}`.
    Agree {
        rank_d: usize,
        rank_a: usize,
        rank_joint: usize,
    },
    /// `D x + A u = 0` with `D x != 0`: `Gamma_quot(x) = 0 < Gamma_raw(x)`.
    Disagree { witness: ValueGapWitness, raw: Q },
}

/// A pivot budget proportional to the size of the weighted-`l1` program.
fn l1_budget(problem: &RepairQuotientProblem) -> usize {
    64 * (problem.rows() + problem.repair_dimension()) + 1024
}

/// `Gamma_quot(x)` with a replayed dual certificate.
pub fn quotient_gamma(
    problem: &RepairQuotientProblem,
    x: &[Q],
) -> Result<QuotientGammaCertificate, GammaSearchError> {
    let dx = problem.defect(x)?;
    let k = problem.repair_dimension();
    let cert = if problem.rows() == 0 {
        QuotientGammaCertificate {
            x: x.to_vec(),
            u: vec![Q::zero(); k],
            residual: Vec::new(),
            dual: Vec::new(),
            value: Q::zero(),
        }
    } else {
        let solution =
            solve_weighted_l1_projection(&dx, problem.weights(), problem.a(), l1_budget(problem))?;
        let u: Vec<Q> = if k == 0 {
            Vec::new()
        } else {
            solution.coefficients.iter().map(|g| -g).collect()
        };
        QuotientGammaCertificate {
            x: x.to_vec(),
            u,
            residual: solution.residual,
            dual: solution.dual,
            value: solution.value,
        }
    };
    problem.verify_quotient_certificate(&cert)?;
    Ok(cert)
}

fn unit(m: usize, i: usize, sign: i64) -> Vec<Q> {
    (0..m)
        .map(|j| {
            if j == i {
                Q::from_integer(sign.into())
            } else {
                Q::zero()
            }
        })
        .collect()
}

/// The vertex system in `z`: `z <= w`, `-z <= w`, `A^T z = 0`,
/// `D^T z = D^T (w ⊙ sign)`, rows in that order, equalities as row pairs.
fn vertex_system(
    problem: &RepairQuotientProblem,
    sign: &[i8],
) -> Result<LinearInequalitySystem, GammaSearchError> {
    let m = problem.rows();
    let target = problem.vertex_target(sign)?;
    let mut system = LinearInequalitySystem::empty(m);
    for (i, w) in problem.weights().iter().enumerate() {
        system.push_le(unit(m, i, 1), w.clone())?;
    }
    for (i, w) in problem.weights().iter().enumerate() {
        system.push_le(unit(m, i, -1), w.clone())?;
    }
    for j in 0..problem.repair_dimension() {
        let column = problem.a().iter().map(|row| row[j].clone()).collect();
        system.push_eq(column, Q::zero())?;
    }
    for (j, g) in target.into_iter().enumerate() {
        let column = problem.d().iter().map(|row| row[j].clone()).collect();
        system.push_eq(column, g)?;
    }
    Ok(system)
}

fn farkas_parts(
    problem: &RepairQuotientProblem,
    sign: &[i8],
    eta: &[Q],
) -> VertexFarkasCertificate {
    let m = problem.rows();
    let k = problem.repair_dimension();
    let pair = |offset: usize, j: usize| &eta[offset + 2 * j] - &eta[offset + 2 * j + 1];
    VertexFarkasCertificate {
        sign: sign.to_vec(),
        upper: eta[..m].to_vec(),
        lower: eta[m..2 * m].to_vec(),
        annihilator: (0..k).map(|j| pair(2 * m, j)).collect(),
        restriction: (0..problem.defect_dimension())
            .map(|j| pair(2 * m + 2 * k, j))
            .collect(),
    }
}

fn certify_vertex_disagreement(
    problem: &RepairQuotientProblem,
    sign: &[i8],
    multipliers: &[Q],
) -> Result<ValueAgreementVerdict, GammaSearchError> {
    let certificate = farkas_parts(problem, sign, multipliers);
    let gap = problem.verify_vertex_farkas(&certificate)?;
    let (raw, _) = problem.verify_value_gap(&gap)?;
    let quotient = quotient_gamma(problem, &gap.x)?;
    if quotient.value >= raw {
        return Err(GammaSearchError::InconsistentSeparator);
    }
    Ok(ValueAgreementVerdict::Disagree {
        certificate,
        gap,
        raw,
        quotient,
    })
}

/// Decides `Gamma_quot = Gamma_raw` at every `x` through the vertex condition.
pub fn decide_value_agreement(
    problem: &RepairQuotientProblem,
    max_pivots: usize,
) -> Result<ValueAgreementVerdict, GammaSearchError> {
    let mut entries = Vec::new();
    for sign in all_sign_vectors(problem.rows())? {
        let system = vertex_system(problem, &sign)?;
        match system.decide(max_pivots)? {
            FeasibilityVerdict::Feasible { point } => entries.push((sign, point)),
            FeasibilityVerdict::Infeasible { multipliers } => {
                return certify_vertex_disagreement(problem, &sign, &multipliers);
            }
        }
    }
    let table = VertexExtensionTable::try_from_entries(entries)?;
    problem.verify_vertex_table(&table)?;
    Ok(ValueAgreementVerdict::Agree { table })
}

fn matrix(rows: &[Vec<Q>], cols: usize) -> Result<BasicMatrix<Q>, MatrixError> {
    BasicMatrix::from_row_major(rows.len(), cols, rows.iter().flatten().cloned().collect())
}

fn find_kernel_zero_test_gap(
    problem: &RepairQuotientProblem,
    joint: &BasicMatrix<Q>,
    n: usize,
) -> Result<Option<ZeroTestVerdict>, GammaSearchError> {
    for vector in elimination::kernel_basis(joint)? {
        let witness = ValueGapWitness {
            x: vector[..n].to_vec(),
            u: vector[n..].to_vec(),
        };
        if problem.defect(&witness.x)?.iter().any(|v| !v.is_zero()) {
            let raw = problem.verify_zero_test_gap(&witness)?;
            return Ok(Some(ZeroTestVerdict::Disagree { witness, raw }));
        }
    }
    Ok(None)
}

/// Decides whether `Gamma_raw(x) = 0` and `Gamma_quot(x) = 0` agree at every `x`.
pub fn decide_zero_test_agreement(
    problem: &RepairQuotientProblem,
) -> Result<ZeroTestVerdict, GammaSearchError> {
    let (n, k) = (problem.defect_dimension(), problem.repair_dimension());
    let joint_rows: Vec<Vec<Q>> = problem
        .d()
        .iter()
        .zip(problem.a())
        .map(|(d, a)| d.iter().chain(a).cloned().collect())
        .collect();
    let joint = matrix(&joint_rows, n + k)?;
    if let Some(disagree) = find_kernel_zero_test_gap(problem, &joint, n)? {
        return Ok(disagree);
    }
    // Every kernel vector has D x = 0, so D x = -A u forces D x = 0.
    let rank_d = elimination::rank(&matrix(problem.d(), n)?)?;
    let rank_a = elimination::rank(&matrix(problem.a(), k)?)?;
    let rank_joint = elimination::rank(&joint)?;
    if rank_d + rank_a != rank_joint {
        return Err(GammaSearchError::InconsistentSeparator);
    }
    Ok(ZeroTestVerdict::Agree {
        rank_d,
        rank_a,
        rank_joint,
    })
}

/// `Gamma_raw(x)` and a replayed certificate of `Gamma_quot(x)`, refusing a
/// quotient value above the raw value (`u = 0` bounds it by the raw value).
pub fn compare_at(
    problem: &RepairQuotientProblem,
    x: &[Q],
) -> Result<(Q, QuotientGammaCertificate), GammaSearchError> {
    let raw = problem.raw_gamma(x)?;
    let quotient = quotient_gamma(problem, x)?;
    if quotient.value > raw {
        return Err(GammaSearchError::InconsistentSeparator);
    }
    Ok((raw, quotient))
}

// Origin: engine/crates_rs/core_solvers/src/solver_graph_reconciliation.rs
// Claim: urn:core:crates_rs:core-solvers:solver-graph-reconciliation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use num_bigint::BigInt;

    fn q(n: i64) -> Q {
        Q::from_integer(BigInt::from(n))
    }
    fn col(v: &[i64]) -> Vec<Vec<Q>> {
        v.iter().map(|x| vec![q(*x)]).collect()
    }
    fn problem(d: &[i64], a: &[i64], w: &[i64]) -> RepairQuotientProblem {
        RepairQuotientProblem::try_new(1, 1, col(d), col(a), w.iter().map(|x| q(*x)).collect())
            .unwrap()
    }

    #[test]
    fn duplicated_defect_disagrees_with_raw_two_quotient_one() {
        let p = problem(&[1, 1], &[1, 0], &[1, 1]);
        let (raw, quotient) = compare_at(&p, &[q(1)]).unwrap();
        assert_eq!((raw, quotient.value), (q(2), q(1)));
        match decide_value_agreement(&p, 500).unwrap() {
            ValueAgreementVerdict::Disagree {
                certificate,
                gap,
                raw,
                quotient,
            } => {
                assert!(p.verify_vertex_farkas(&certificate).is_ok());
                assert!(quotient.value < raw);
                assert!(p.verify_value_gap(&gap).is_ok());
            }
            other => panic!("expected disagreement, got {other:?}"),
        }
        // Zero tests agree here: im D ∩ im A = 0.
        assert_eq!(
            decide_zero_test_agreement(&p).unwrap(),
            ZeroTestVerdict::Agree {
                rank_d: 1,
                rank_a: 1,
                rank_joint: 2
            }
        );
    }

    #[test]
    fn weighted_variant_values() {
        let p = problem(&[1, 1], &[1, 0], &[2, 3]);
        let (raw, quotient) = compare_at(&p, &[q(1)]).unwrap();
        assert_eq!((raw, quotient.value), (q(5), q(3)));
    }

    #[test]
    fn opposite_repair_agrees_everywhere() {
        let p = problem(&[1, 1], &[1, -1], &[1, 1]);
        match decide_value_agreement(&p, 500).unwrap() {
            ValueAgreementVerdict::Agree { table } => {
                assert_eq!(table.entries().len(), 4);
                assert!(p.verify_vertex_table(&table).is_ok());
            }
            other => panic!("expected agreement, got {other:?}"),
        }
        for x in [-3, 0, 2] {
            let (raw, quotient) = compare_at(&p, &[q(x)]).unwrap();
            assert_eq!(raw, quotient.value);
        }
    }

    #[test]
    fn identical_maps_disagree_on_zero_tests() {
        let p = problem(&[1], &[1], &[1]);
        match decide_zero_test_agreement(&p).unwrap() {
            ZeroTestVerdict::Disagree { witness, raw } => {
                assert!(raw > q(0));
                assert!(p.verify_zero_test_gap(&witness).is_ok());
                assert_eq!(quotient_gamma(&p, &witness.x).unwrap().value, q(0));
            }
            other => panic!("expected disagreement, got {other:?}"),
        }
    }

    #[test]
    fn boundary_shapes() {
        // No repair columns: the quotient is the raw value, and every vertex extends.
        let p = RepairQuotientProblem::try_new(
            1,
            0,
            col(&[1, 2]),
            vec![vec![], vec![]],
            vec![q(1), q(1)],
        )
        .unwrap();
        assert!(matches!(
            decide_value_agreement(&p, 500).unwrap(),
            ValueAgreementVerdict::Agree { .. }
        ));
        assert_eq!(compare_at(&p, &[q(1)]).unwrap().1.value, q(3));
        // No rows: both values are zero.
        let p = RepairQuotientProblem::try_new(2, 1, vec![], vec![], vec![]).unwrap();
        assert_eq!(quotient_gamma(&p, &[q(1), q(1)]).unwrap().value, q(0));
        assert!(matches!(
            decide_value_agreement(&p, 10).unwrap(),
            ValueAgreementVerdict::Agree { .. }
        ));
    }

    #[test]
    fn exhausted_budget_is_not_a_verdict() {
        let p = problem(&[1, 1], &[1, 0], &[1, 1]);
        assert!(matches!(
            decide_value_agreement(&p, 0),
            Err(GammaSearchError::Feasibility(
                FeasibilityError::BudgetExhausted
            ))
        ));
    }
}
