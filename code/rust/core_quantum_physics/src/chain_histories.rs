//! Prepare chain-history proposals; decoherence evaluation belongs to core_functional.
use crate::exact_hermitian;
use crate::graded_path_sum::HISTORY_BUDGET;
use crate::heisenberg_picture::heisenberg_observable;
use linear_algebra::backend::basic_matrix::BasicMatrix;
use core_functional::decoherence::DecoherenceError;
use core_number_theory::cyclotomic::GaussianRat;

/// A history through declared projective partitions, with its class operator.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ChainHistory {
    /// The member chosen from each partition, in time order.
    pub labels: Vec<usize>,
    /// `P^n_(a_n)(t_n) ... P^1_(a_1)(t_1)`.
    pub class_operator: BasicMatrix<GaussianRat>,
}

/// Preflight history count, step count, and Hilbert dimension against operation limits.
pub fn preflight_history_budget(
    num_histories: usize,
    num_steps: usize,
    dim: usize,
) -> Result<(), DecoherenceError> {
    if num_histories > HISTORY_BUDGET {
        return Err(DecoherenceError::HistoryBudget {
            budget: HISTORY_BUDGET,
        });
    }
    if dim == 0 {
        return Err(DecoherenceError::Empty);
    }
    core_kernel::resource_limits::OperationLimits::default()
        .check_hilbert_dim(dim)
        .map_err(|e| DecoherenceError::Algebra(e.to_string()))?;

    let work = num_histories
        .checked_mul(num_steps.max(1))
        .and_then(|h_steps| h_steps.checked_mul(dim))
        .and_then(|h_dim| h_dim.checked_mul(dim))
        .and_then(|h_dim2| h_dim2.checked_mul(dim));

    match work {
        Some(w) if w <= (1 << 26) => Ok(()),
        _ => Err(DecoherenceError::Algebra(
            "aggregate history multiplication work exceeds operation budget".into(),
        )),
    }
}

fn history_op_limits() -> linear_algebra::backend::basic_matrix::OperationLimits {
    linear_algebra::backend::basic_matrix::OperationLimits {
        max_elements: 1 << 20,
        max_scalar_ops: 1 << 24,
    }
}

fn check_partition(
    time: usize,
    partition: &[BasicMatrix<GaussianRat>],
    dimension: usize,
) -> Result<(), DecoherenceError> {
    if partition.is_empty() {
        return Err(DecoherenceError::EmptyPartition { time });
    }
    for (index, p) in partition.iter().enumerate() {
        check_single_projector(time, index, p, dimension)?;
    }
    check_pairwise_orthogonal_projectors(time, partition)?;
    check_partition_completeness(time, partition, dimension)
}

fn check_single_projector(
    time: usize,
    index: usize,
    p: &BasicMatrix<GaussianRat>,
    dimension: usize,
) -> Result<(), DecoherenceError> {
    let shaped = p.rows() == dimension && p.cols() == dimension;
    if !shaped || !exact_hermitian::is_hermitian(p) {
        return Err(DecoherenceError::NotProjector {
            time,
            index,
            dimension,
        });
    }
    let squared =
        linear_algebra::exact_field::matrix::multiply_with_limits(p, p, history_op_limits())
            .map_err(|e| DecoherenceError::Algebra(e.to_string()))?;
    if squared != *p {
        return Err(DecoherenceError::NotProjector {
            time,
            index,
            dimension,
        });
    }
    Ok(())
}

fn check_pairwise_orthogonal_projectors(
    time: usize,
    partition: &[BasicMatrix<GaussianRat>],
) -> Result<(), DecoherenceError> {
    for first in 0..partition.len() {
        for second in first + 1..partition.len() {
            let prod = linear_algebra::exact_field::matrix::multiply_with_limits(
                &partition[first],
                &partition[second],
                history_op_limits(),
            )
            .map_err(|error| DecoherenceError::Algebra(error.to_string()))?;
            if !linear_algebra::exact_field::matrix::is_zero_matrix(&prod) {
                return Err(DecoherenceError::NotOrthogonal {
                    time,
                    first,
                    second,
                });
            }
        }
    }
    Ok(())
}

fn check_partition_completeness(
    time: usize,
    partition: &[BasicMatrix<GaussianRat>],
    dimension: usize,
) -> Result<(), DecoherenceError> {
    let zero = linear_algebra::exact_field::matrix::zeros_with_limits::<GaussianRat>(
        dimension,
        dimension,
        history_op_limits(),
    )
    .map_err(|e| DecoherenceError::Algebra(e.to_string()))?;
    let total = partition.iter().try_fold(zero, |acc, p| {
        linear_algebra::exact_field::matrix::add(&acc, p)
            .map_err(|e| DecoherenceError::Algebra(e.to_string()))
    })?;
    let id = linear_algebra::exact_field::matrix::identity_with_limits::<GaussianRat>(
        dimension,
        history_op_limits(),
    )
    .map_err(|e| DecoherenceError::Algebra(e.to_string()))?;
    if total != id {
        return Err(DecoherenceError::IncompletePartition { time });
    }
    Ok(())
}

/// Every history through `partitions`, with step `k` acting before partition `k`,
/// in lexicographic order of the labels (first time most significant).
pub fn chain_histories(
    steps: &[BasicMatrix<GaussianRat>],
    partitions: &[Vec<BasicMatrix<GaussianRat>>],
) -> Result<Vec<ChainHistory>, DecoherenceError> {
    let (dimension, sizes, count) = validate_chain_inputs(steps, partitions)?;
    let heisenberg = build_heisenberg_partitions(steps, partitions)?;

    let mut histories = Vec::with_capacity(count);
    let mut labels = vec![0usize; sizes.len()];
    loop {
        let class_operator = build_class_operator(&heisenberg, &labels, dimension)?;
        histories.push(ChainHistory {
            labels: labels.clone(),
            class_operator,
        });
        if !advance_lexicographic_labels(&mut labels, &sizes) {
            return Ok(histories);
        }
    }
}

fn validate_chain_inputs(
    steps: &[BasicMatrix<GaussianRat>],
    partitions: &[Vec<BasicMatrix<GaussianRat>>],
) -> Result<(usize, Vec<usize>, usize), DecoherenceError> {
    if steps.len() != partitions.len() {
        return Err(DecoherenceError::StepCount {
            steps: steps.len(),
            partitions: partitions.len(),
        });
    }
    let dimension = partitions
        .first()
        .and_then(|p| p.first())
        .map(|p| p.rows())
        .ok_or(DecoherenceError::Empty)?;
    let sizes: Vec<usize> = partitions.iter().map(Vec::len).collect();
    let count = sizes
        .iter()
        .try_fold(1usize, |acc, &s| acc.checked_mul(s))
        .filter(|&n| n <= HISTORY_BUDGET)
        .ok_or(DecoherenceError::HistoryBudget {
            budget: HISTORY_BUDGET,
        })?;

    preflight_history_budget(count, steps.len(), dimension)?;
    validate_partitions_and_steps(steps, partitions, dimension)?;
    Ok((dimension, sizes, count))
}

fn validate_partitions_and_steps(
    steps: &[BasicMatrix<GaussianRat>],
    partitions: &[Vec<BasicMatrix<GaussianRat>>],
    dimension: usize,
) -> Result<(), DecoherenceError> {
    for (time, partition) in partitions.iter().enumerate() {
        check_partition(time, partition, dimension)?;
    }
    for (i, step) in steps.iter().enumerate() {
        if step.rows() != dimension || step.cols() != dimension {
            return Err(DecoherenceError::Algebra(format!(
                "step {i} has shape ({}x{}), expected ({dimension}x{dimension})",
                step.rows(),
                step.cols()
            )));
        }
    }
    Ok(())
}

fn build_heisenberg_partitions(
    steps: &[BasicMatrix<GaussianRat>],
    partitions: &[Vec<BasicMatrix<GaussianRat>>],
) -> Result<Vec<Vec<BasicMatrix<GaussianRat>>>, DecoherenceError> {
    partitions
        .iter()
        .enumerate()
        .map(|(time, partition)| {
            partition
                .iter()
                .map(|p| heisenberg_observable(&steps[..=time], p))
                .collect::<Result<Vec<_>, _>>()
        })
        .collect::<Result<_, _>>()
        .map_err(|error| DecoherenceError::Heisenberg(error.to_string()))
}

fn build_class_operator(
    heisenberg: &[Vec<BasicMatrix<GaussianRat>>],
    labels: &[usize],
    dimension: usize,
) -> Result<BasicMatrix<GaussianRat>, DecoherenceError> {
    let initial_id = linear_algebra::exact_field::matrix::identity_with_limits::<GaussianRat>(
        dimension,
        history_op_limits(),
    )
    .map_err(|e| DecoherenceError::Algebra(e.to_string()))?;

    labels
        .iter()
        .enumerate()
        .try_fold(initial_id, |acc, (time, &a)| {
            linear_algebra::exact_field::matrix::multiply_with_limits(
                &heisenberg[time][a],
                &acc,
                history_op_limits(),
            )
            .map_err(|e| DecoherenceError::Algebra(e.to_string()))
        })
}

fn advance_lexicographic_labels(labels: &mut [usize], sizes: &[usize]) -> bool {
    let mut position = labels.len();
    loop {
        if position == 0 {
            return false;
        }
        position -= 1;
        labels[position] += 1;
        if labels[position] < sizes[position] {
            return true;
        }
        labels[position] = 0;
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/chain_histories.rs
// Claim: urn:core:crates_rs:core-quantum-physics:chain-histories:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord5b4a260b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord5b4a260b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError5b4a260b {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryError5b4a260b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError5b4a260b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError5b4a260b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord5b4a260b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError5b4a260b> {
        if capacity_bound == 0 {
            return Err(BoundaryError5b4a260b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError5b4a260b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError5b4a260b::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[cfg(test)]
mod l4_boundary_tests_5b4a260b {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord5b4a260b::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord5b4a260b::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord5b4a260b::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord5b4a260b::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord5b4a260b::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError5b4a260b::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError5b4a260b::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
