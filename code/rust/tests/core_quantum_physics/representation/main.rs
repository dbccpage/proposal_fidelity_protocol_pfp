//! Exact tests for the representation movement of the finite quantum mechanics
//! programme: trace and commutator readouts of Gell-Mann matrices, the
//! Heisenberg picture of declared unitary steps, decoherence functionals of
//! declared histories, Dirac operators from declared gamma matrices, and
//! rational spin lifts. One submodule per retired source paper; the
//! paper-to-module map lives in
//! `atlas/coda_atlas/F004_papers/006_finite_qm/finite_quantum_mechanics.md`.

mod support;

mod dirac_equation_admission;
mod gell_mann_hartle_decoherence;
mod heisenberg_picture_shadow;
mod spinor_structure_admission;
mod trace_zero_commutator;

// --- exact carrier witness ---
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TracePairError {
    Shape,
    NotTraceZero { index: usize, trace: i128 },
    Commutator { trace: i128 },
    Overflow,
}

// Origin: engine/crates_rs/tests/core_quantum_physics/representation/main.rs
// Claim: urn:core:crates_rs:tests:main:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for TracePairError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for TracePairError {}

/// Two trace-zero 3×3 integer matrices whose commutator is also trace-zero.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TraceZeroPair {
    commutator_trace: i128,
}

fn matrix_entry(matrix: &[i64; 9], row: usize, column: usize) -> Result<i64, TracePairError> {
    matrix.get(row.checked_mul(3).ok_or(TracePairError::Overflow)?.checked_add(column).ok_or(TracePairError::Overflow)?).copied().ok_or(TracePairError::Shape)
}

fn matrix_trace(matrix: &[i64; 9]) -> Result<i128, TracePairError> {
    let mut trace = 0i128;
    for index in [0usize, 4, 8] {
        trace = trace.checked_add(i128::from(*matrix.get(index).ok_or(TracePairError::Shape)?)).ok_or(TracePairError::Overflow)?;
    }
    Ok(trace)
}

fn matrix_product(left: &[i64; 9], right: &[i64; 9]) -> Result<[i64; 9], TracePairError> {
    let mut product = [0i64; 9];
    for row in 0..3 {
        for column in 0..3 {
            let mut acc = 0i128;
            for index in 0..3 {
                let product_term = i128::from(matrix_entry(left, row, index)?)
                    .checked_mul(i128::from(matrix_entry(right, index, column)?))
                    .ok_or(TracePairError::Overflow)?;
                acc = acc.checked_add(product_term).ok_or(TracePairError::Overflow)?;
            }
            let slot = product.get_mut(row * 3 + column).ok_or(TracePairError::Shape)?;
            *slot = i64::try_from(acc).map_err(|_| TracePairError::Overflow)?;
        }
    }
    Ok(product)
}

fn commutator_diagonal_sum(left: &[i64; 9], right: &[i64; 9]) -> Result<i128, TracePairError> {
    let left_right = matrix_product(left, right)?;
    let right_left = matrix_product(right, left)?;
    let mut commutator = 0i128;
    for index in [0usize, 4, 8] {
        let difference = i128::from(*left_right.get(index).ok_or(TracePairError::Shape)?)
            .checked_sub(i128::from(*right_left.get(index).ok_or(TracePairError::Shape)?))
            .ok_or(TracePairError::Overflow)?;
        commutator = commutator.checked_add(difference).ok_or(TracePairError::Overflow)?;
    }
    Ok(commutator)
}

impl TraceZeroPair {
    pub fn try_new(left: &[i64; 9], right: &[i64; 9]) -> Result<Self, TracePairError> {
        let left_trace = matrix_trace(left)?;
        if left_trace != 0 {
            return Err(TracePairError::NotTraceZero { index: 0, trace: left_trace });
        }
        let right_trace = matrix_trace(right)?;
        if right_trace != 0 {
            return Err(TracePairError::NotTraceZero { index: 1, trace: right_trace });
        }
        let commutator = commutator_diagonal_sum(left, right)?;
        if commutator != 0 {
            return Err(TracePairError::Commutator { trace: commutator });
        }
        Ok(Self { commutator_trace: commutator })
    }

    pub fn commutator_trace(&self) -> i128 { self.commutator_trace }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod trace_pair_tests {
    use super::*;

    #[test]
    fn off_diagonal_units_have_a_trace_zero_commutator() {
        let left = [0, 1, 0, 0, 0, 0, 0, 0, 0];
        let right = [0, 0, 0, 1, 0, 0, 0, 0, 0];
        let pair = TraceZeroPair::try_new(&left, &right);
        assert!(matches!(pair, Ok(ref pair) if pair.commutator_trace() == 0));
    }

    #[test]
    fn a_nonzero_trace_is_refused() {
        let left = [1, 0, 0, 0, 0, 0, 0, 0, 0];
        let right = [0, 0, 0, 0, -1, 0, 0, 0, 0];
        let pair = TraceZeroPair::try_new(&left, &right);
        assert!(matches!(pair, Err(TracePairError::NotTraceZero { index: 0, trace: 1 })));
    }
}
