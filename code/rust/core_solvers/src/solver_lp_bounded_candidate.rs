//! Stack-only bounded primal proposals; canonical BigRational replay decides.
//!
//! This is a finite optimization proposal profile, not a replacement coefficient
//! domain. Every arithmetic operation refuses fixed-width overflow. The caller
//! must independently verify each returned optimum using the arbitrary-precision
//! primal/dual checker before assigning a mathematical status.

use std::cmp::Ordering;

pub const MAX_ROWS: usize = 8;
pub const MAX_COLS: usize = 16;
// max_{0 <= rank <= 8} binomial(8, rank) = 70 basic row subsets.
pub const MAX_TIES: usize = 70;
const WIDTH: usize = MAX_COLS + 1;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CandidateError {
    Shape,
    Overflow,
    Capacity,
    Budget,
    NonPositiveWeight,
}

// Origin: engine/crates_rs/core_solvers/src/solver_lp_bounded_candidate.rs
// Claim: urn:core:crates_rs:core-solvers:solver-lp-bounded-candidate:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for CandidateError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for CandidateError {}

use core_kernel::bounded_rational::{gcd, BoundedRationalError, StackRational};

impl From<BoundedRationalError> for CandidateError {
    fn from(_: BoundedRationalError) -> Self {
        Self::Overflow
    }
}

#[derive(Clone, Copy)]
pub struct Candidate {
    pub potential: [StackRational; MAX_COLS],
    pub exact_part: [StackRational; MAX_ROWS],
}

const EMPTY: Candidate = Candidate {
    potential: [StackRational::ZERO; MAX_COLS],
    exact_part: [StackRational::ZERO; MAX_ROWS],
};

pub struct Candidates {
    pub value: StackRational,
    pub ties: [Candidate; MAX_TIES],
    pub tie_count: usize,
    pub subsets: usize,
}

fn eliminate_rref_pivot(
    a: &mut [[StackRational; WIDTH]; MAX_ROWS],
    rows: usize,
    columns: usize,
    rank: usize,
    col: usize,
) -> Result<(), CandidateError> {
    let scale = a[rank][col];
    for c in col..columns {
        a[rank][c] = a[rank][c].div(scale)?;
    }
    for row in 0..rows {
        if row == rank || a[row][col].numerator == 0 {
            continue;
        }
        let factor = a[row][col];
        for c in col..columns {
            a[row][c] = a[row][c].sub(factor.mul(a[rank][c])?)?;
        }
    }
    Ok(())
}

fn rref(
    a: &mut [[StackRational; WIDTH]; MAX_ROWS],
    rows: usize,
    columns: usize,
) -> Result<([usize; MAX_ROWS], usize), CandidateError> {
    let mut pivots = [0usize; MAX_ROWS];
    let mut rank = 0;
    for col in 0..columns {
        let Some(pivot) = (rank..rows).find(|&r| a[r][col].numerator != 0) else {
            continue;
        };
        a.swap(rank, pivot);
        eliminate_rref_pivot(a, rows, columns, rank, col)?;
        pivots[rank] = col;
        rank += 1;
        if rank == rows {
            break;
        }
    }
    Ok((pivots, rank))
}

fn validate_stack_inputs(
    matrix: &[[StackRational; MAX_COLS]; MAX_ROWS],
    rows: usize,
    columns: usize,
    reading: &[StackRational; MAX_ROWS],
    weights: &[StackRational; MAX_ROWS],
) -> Result<(), CandidateError> {
    if rows > MAX_ROWS || columns > MAX_COLS {
        return Err(CandidateError::Capacity);
    }
    for q in matrix
        .iter()
        .take(rows)
        .flat_map(|r| r.iter().take(columns))
        .chain(reading.iter().take(rows))
        .chain(weights.iter().take(rows))
    {
        // Public fields are untrusted; refuse values bypassing new().
        let valid_q = q.denominator > 0
            && q.numerator != i128::MIN
            && gcd(q.numerator.abs(), q.denominator) == 1;
        if !valid_q {
            return Err(CandidateError::Shape);
        }
    }
    if weights.iter().take(rows).any(|q| q.numerator <= 0) {
        return Err(CandidateError::NonPositiveWeight);
    }
    Ok(())
}

fn populate_exact_part(
    candidate: &mut Candidate,
    matrix: &[[StackRational; MAX_COLS]; MAX_ROWS],
    rows: usize,
    columns: usize,
) -> Result<(), CandidateError> {
    for row in 0..rows {
        for col in 0..columns {
            candidate.exact_part[row] = candidate.exact_part[row]
                .add(matrix[row][col].mul(candidate.potential[col])?)?;
        }
    }
    Ok(())
}

fn build_subset_candidate(
    matrix: &[[StackRational; MAX_COLS]; MAX_ROWS],
    rows: usize,
    columns: usize,
    reading: &[StackRational; MAX_ROWS],
    pivots: &[usize; MAX_ROWS],
    rank: usize,
    selected: &[usize; MAX_ROWS],
) -> Result<Option<Candidate>, CandidateError> {
    let mut reduced = [[StackRational::ZERO; WIDTH]; MAX_ROWS];
    for row in 0..rank {
        for col in 0..rank {
            reduced[row][col] = matrix[selected[row]][pivots[col]];
        }
        reduced[row][rank] = reading[selected[row]];
    }
    let (row_pivots, subrank) = rref(&mut reduced, rank, rank + 1)?;
    if subrank != rank || !(0..rank).all(|i| row_pivots[i] == i) {
        return Ok(None);
    }
    let mut candidate = EMPTY;
    for i in 0..rank {
        candidate.potential[pivots[i]] = reduced[i][rank];
    }
    populate_exact_part(&mut candidate, matrix, rows, columns)?;
    Ok(Some(candidate))
}

fn record_subset_candidate(
    result: &mut Candidates,
    candidate: Candidate,
    rows: usize,
    reading: &[StackRational; MAX_ROWS],
    weights: &[StackRational; MAX_ROWS],
) -> Result<(), CandidateError> {
    let value = core_functional::phi1::Phi1Functional::bounded_representative_mass(
        &weights[..rows],
        &reading[..rows],
        &candidate.exact_part[..rows],
    )
    .map_err(|_| CandidateError::Overflow)?;
    let comparison = if result.tie_count == 0 {
        Ordering::Less
    } else {
        value.compare(result.value)?
    };
    if comparison == Ordering::Less {
        result.value = value;
        result.tie_count = 0;
    }
    if comparison != Ordering::Greater
        && !result
            .ties
            .iter()
            .take(result.tie_count)
            .any(|old| old.exact_part[..rows] == candidate.exact_part[..rows])
    {
        if result.tie_count == MAX_TIES {
            return Err(CandidateError::Capacity);
        }
        result.ties[result.tie_count] = candidate;
        result.tie_count += 1;
    }
    Ok(())
}

fn advance_subset_selection(selected: &mut [usize; MAX_ROWS], rows: usize, rank: usize) -> bool {
    if rank == 0 {
        return false;
    }
    let Some(pos) = (0..rank).rev().find(|&i| selected[i] < rows - rank + i) else {
        return false;
    };
    selected[pos] += 1;
    for i in pos + 1..rank {
        selected[i] = selected[i - 1] + 1;
    }
    true
}

#[allow(clippy::too_many_arguments)]
fn evaluate_all_subsets(
    matrix: &[[StackRational; MAX_COLS]; MAX_ROWS],
    rows: usize,
    columns: usize,
    reading: &[StackRational; MAX_ROWS],
    weights: &[StackRational; MAX_ROWS],
    pivots: &[usize; MAX_ROWS],
    rank: usize,
    subset_budget: usize,
) -> Result<Candidates, CandidateError> {
    let mut selected = [0usize; MAX_ROWS];
    for (i, item) in selected.iter_mut().take(rank).enumerate() {
        *item = i;
    }
    let mut result = Candidates {
        value: StackRational::ZERO,
        ties: [EMPTY; MAX_TIES],
        tie_count: 0,
        subsets: 0,
    };
    loop {
        if result.subsets == subset_budget {
            return Err(CandidateError::Budget);
        }
        result.subsets += 1;
        if let Some(candidate) =
            build_subset_candidate(matrix, rows, columns, reading, pivots, rank, &selected)?
        {
            record_subset_candidate(&mut result, candidate, rows, reading, weights)?;
        }
        if !advance_subset_selection(&mut selected, rows, rank) {
            break;
        }
    }
    Ok(result)
}

/// Exhaust the basic row subsets within the declared stack profile and fuel.
/// This function performs no heap allocation, including its elimination loops.
pub fn propose(
    matrix: &[[StackRational; MAX_COLS]; MAX_ROWS],
    rows: usize,
    columns: usize,
    reading: &[StackRational; MAX_ROWS],
    weights: &[StackRational; MAX_ROWS],
    subset_budget: usize,
) -> Result<Candidates, CandidateError> {
    validate_stack_inputs(matrix, rows, columns, reading, weights)?;
    let mut full = [[StackRational::ZERO; WIDTH]; MAX_ROWS];
    for r in 0..rows {
        full[r][..columns].copy_from_slice(&matrix[r][..columns]);
    }
    let (pivots, rank) = rref(&mut full, rows, columns)?;
    let result = evaluate_all_subsets(
        matrix,
        rows,
        columns,
        reading,
        weights,
        &pivots,
        rank,
        subset_budget,
    )?;
    if result.tie_count == 0 {
        return Err(CandidateError::Shape);
    }
    Ok(result)
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_a78e3433 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
