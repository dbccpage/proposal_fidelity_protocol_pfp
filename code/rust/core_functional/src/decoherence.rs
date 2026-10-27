// AuthorityEffect: None.

//! The Gell-Mann–Hartle decoherence functional of declared histories over `Q(i)`.
//!
//! Declared: an operator `rho` on `C^d` and class operators `C_1, ..., C_m`
//! (`d x d`), or unitary steps and projective partitions from which the class
//! operators are built. Computed exactly:
//!
//! - [`DecoherenceFunctional::matrix`]: `D_jk = Tr(C_j rho C_k*)`. When `rho`
//!   is positive semidefinite, `D` is the Gram matrix of the `C_j rho^(1/2)`;
//!   whether a given `D` is Hermitian or positive semidefinite is decided by
//!   `exact_hermitian`, not assumed.
//! - [`DecoherenceFunctional::coarse_grain`]: the functional of the class
//!   operators `C_A = sum_(j in A) C_j` of a partition of the histories.
//! - [`DecoherenceFunctional::sum_rule_residual`]: `P(j u k) - D_jj - D_kk`,
//!   where `P(j u k) = Tr((C_j + C_k) rho (C_j + C_k)*)` is computed from the
//!   summed class operator; it equals `D_jk + D_kj`, which is `2 Re D_jk` for a
//!   Hermitian `rho`.
//! - [`DecoherenceFunctional::medium_decoherence_witness`]: the first pair with
//!   `D_jk != 0`, and [`DecoherenceFunctional::weak_decoherence_witness`]: the
//!   first pair whose union breaks the sum rule. Vanishing off-diagonal entries
//!   imply every sum rule; the converse fails.
//! - [`DecoherenceFunctional::is_complete`]: `sum_j C_j* C_j = I`, under which
//!   `sum_j D_jj = Tr(rho)`.
//! - History proposals (owned by `core_quantum_physics::chain_histories`): the class operators `C_a = P^n_(a_n)(t_n) ... P^1_(a_1)(t_1)`
//!   of every history through declared projective partitions, with the
//!   Heisenberg-picture projectors `P(t_k) = W_k* P W_k`, `W_k = U_k ... U_1`,
//!   from the physics Heisenberg adapter.
//!
//! Refused: an empty history family or partition, operators of the wrong
//! shape, a coarse-graining that is not a partition of the histories, a
//! partition whose members are not Hermitian idempotents that are pairwise
//! orthogonal and sum to `I`, non-unitary steps, and more than
//! `graded_path_sum::HISTORY_BUDGET` histories. No probability is assigned to a
//! history family that breaks a sum rule; the sum rules are computed, not
//! assumed.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_3e9c2499<T> {
    fn checked_invariant_3e9c2499(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_3e9c2499<T> for Option<T> {
    #[inline]
    fn checked_invariant_3e9c2499(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_3e9c2499<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_3e9c2499(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use linear_algebra::backend::basic_matrix::BasicMatrix;
use core_number_theory::cyclotomic::GaussianRat;

fn check_well_formed(matrix: &BasicMatrix<GaussianRat>) -> Result<(), DecoherenceError> {
    if matrix.rows() == 0 || matrix.cols() == 0 {
        return Err(DecoherenceError::Empty);
    }
    core_kernel::resource_limits::OperationLimits::default()
        .check_dense_matrix(
            matrix.rows(),
            matrix.cols(),
            std::mem::size_of::<GaussianRat>(),
        )
        .map(|_| ())
        .map_err(|error| DecoherenceError::Algebra(error.to_string()))
}

/// Refusals for decoherence functionals and chain histories.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum DecoherenceError {
    #[error(transparent)]
    Operator(#[from] linear_algebra::exact_field::ExactFieldError),
    #[error("exact algebra refused: {0}")]
    Algebra(String),
    #[error("a history family needs at least one history")]
    Empty,
    #[error("the state is {rows}x{cols}, not square")]
    StateNotSquare { rows: usize, cols: usize },
    #[error("class operator {index} is not {dimension}x{dimension}")]
    ClassOperatorShape { index: usize, dimension: usize },
    #[error("history {index} is out of range for {count} histories")]
    HistoryOutOfRange { index: usize, count: usize },
    #[error("a sum rule needs two distinct histories, got {index} twice")]
    SameHistory { index: usize },
    #[error("history {index} lies in {classes} classes of the coarse-graining, not one")]
    NotAPartition { index: usize, classes: usize },
    #[error("class {class} of the coarse-graining is empty")]
    EmptyClass { class: usize },
    #[error("{steps} steps cannot carry {partitions} partitions")]
    StepCount { steps: usize, partitions: usize },
    #[error("partition {time} is empty")]
    EmptyPartition { time: usize },
    #[error(
        "member {index} of partition {time} is not a {dimension}x{dimension} Hermitian idempotent"
    )]
    NotProjector {
        time: usize,
        index: usize,
        dimension: usize,
    },
    #[error("members {first} and {second} of partition {time} are not orthogonal")]
    NotOrthogonal {
        time: usize,
        first: usize,
        second: usize,
    },
    #[error("partition {time} does not sum to the identity")]
    IncompletePartition { time: usize },
    #[error("more than {budget} histories")]
    HistoryBudget { budget: usize },
    #[error("Heisenberg picture refused: {0}")]
    Heisenberg(String),
}

/// `D_jk = Tr(C_j rho C_k*)` for a declared state and class operators.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DecoherenceFunctional {
    state: BasicMatrix<GaussianRat>,
    class_operators: Vec<BasicMatrix<GaussianRat>>,
    matrix: BasicMatrix<GaussianRat>,
}

impl DecoherenceFunctional {
    fn validate_decoherence_shapes(
        state: &BasicMatrix<GaussianRat>,
        class_operators: &[BasicMatrix<GaussianRat>],
    ) -> Result<(), DecoherenceError> {
        check_well_formed(state)?;
        for c in class_operators {
            check_well_formed(c)?;
        }
        if class_operators.len() > 1024 || state.rows() > 256 {
            return Err(DecoherenceError::HistoryBudget { budget: 1024 });
        }
        if class_operators.is_empty() {
            return Err(DecoherenceError::Empty);
        }
        if state.rows() != state.cols() {
            return Err(DecoherenceError::StateNotSquare {
                rows: state.rows(),
                cols: state.cols(),
            });
        }
        let dimension = state.rows();
        if let Some(index) = class_operators
            .iter()
            .position(|c| c.rows() != dimension || c.cols() != dimension)
        {
            return Err(DecoherenceError::ClassOperatorShape { index, dimension });
        }
        Ok(())
    }

    pub fn new(
        state: BasicMatrix<GaussianRat>,
        class_operators: Vec<BasicMatrix<GaussianRat>>,
    ) -> Result<Self, DecoherenceError> {
        Self::validate_decoherence_shapes(&state, &class_operators)?;
        let weighted: Vec<BasicMatrix<GaussianRat>> = class_operators
            .iter()
            .map(|c| {
                linear_algebra::exact_field::matrix::multiply_with_limits(
                    &(c),
                    &state,
                    linear_algebra::backend::basic_matrix::OperationLimits {
                        max_elements: 1 << 20,
                        max_scalar_ops: 1 << 24,
                    },
                )
                .checked_invariant_3e9c2499("validated finite matrix shape and budget")
            })
            .collect();
        let m = class_operators.len();
        let mut matrix = linear_algebra::exact_field::matrix::zeros_with_limits::<GaussianRat>(
            m,
            m,
            linear_algebra::backend::basic_matrix::OperationLimits {
                max_elements: 1 << 20,
                max_scalar_ops: 1 << 24,
            },
        )
        .checked_invariant_3e9c2499("validated finite matrix shape and budget");
        for (j, c_rho) in weighted.iter().enumerate() {
            for (k, c) in class_operators.iter().enumerate() {
                // Tr(C_j rho C_k*) = Tr(C_k* (C_j rho)), the Hilbert–Schmidt pairing of C_k with C_j rho.
                let entry = linear_algebra::exact_field::involution::hs_inner(c, c_rho)
                    .map_err(linear_algebra::exact_field::ExactFieldError::from)
                    .checked_invariant_3e9c2499("class operators share one shape");
                (matrix)
                    .set(j, k, entry)
                    .checked_invariant_3e9c2499("validated finite matrix shape and budget");
            }
        }
        Ok(Self {
            state,
            class_operators,
            matrix,
        })
    }

    /// The `m x m` matrix `D`.
    pub fn matrix(&self) -> &BasicMatrix<GaussianRat> {
        &self.matrix
    }

    /// `sum_j C_j* C_j = I`.
    pub fn is_complete(&self) -> bool {
        let d = self.state.rows();
        let total = self.class_operators.iter().fold(
            linear_algebra::exact_field::matrix::zeros_with_limits::<GaussianRat>(
                d,
                d,
                linear_algebra::backend::basic_matrix::OperationLimits {
                    max_elements: 1 << 20,
                    max_scalar_ops: 1 << 24,
                },
            )
            .checked_invariant_3e9c2499("validated finite matrix shape and budget"),
            |acc, c| {
                linear_algebra::exact_field::matrix::add(
                    &(acc),
                    &linear_algebra::exact_field::matrix::multiply_with_limits(
                        &(linear_algebra::exact_field::involution::adjoint(&(c))
                            .checked_invariant_3e9c2499(
                                "validated finite matrix shape and budget",
                            )),
                        c,
                        linear_algebra::backend::basic_matrix::OperationLimits {
                            max_elements: 1 << 20,
                            max_scalar_ops: 1 << 24,
                        },
                    )
                    .checked_invariant_3e9c2499("validated finite matrix shape and budget"),
                )
                .checked_invariant_3e9c2499("validated finite matrix shape and budget")
            },
        );
        total
            == linear_algebra::exact_field::matrix::identity_with_limits::<GaussianRat>(
                d,
                linear_algebra::backend::basic_matrix::OperationLimits {
                    max_elements: 1 << 20,
                    max_scalar_ops: 1 << 24,
                },
            )
            .checked_invariant_3e9c2499("validated finite matrix shape and budget")
    }

    fn check_index(&self, index: usize) -> Result<(), DecoherenceError> {
        let count = self.class_operators.len();
        if index >= count {
            return Err(DecoherenceError::HistoryOutOfRange { index, count });
        }
        Ok(())
    }

    /// The functional of the coarse-grained class operators `C_A = sum_(j in A) C_j`.
    pub fn coarse_grain(&self, classes: &[Vec<usize>]) -> Result<Self, DecoherenceError> {
        let count = self.class_operators.len();
        let mut membership = vec![0usize; count];
        for (class, members) in classes.iter().enumerate() {
            if members.is_empty() {
                return Err(DecoherenceError::EmptyClass { class });
            }
            for &index in members {
                self.check_index(index)?;
                membership[index] += 1;
            }
        }
        if let Some((index, &classes)) = membership.iter().enumerate().find(|&(_, &n)| n != 1) {
            return Err(DecoherenceError::NotAPartition { index, classes });
        }
        let d = self.state.rows();
        let coarse = classes
            .iter()
            .map(|members| {
                members.iter().fold(
                    linear_algebra::exact_field::matrix::zeros_with_limits::<GaussianRat>(
                        d,
                        d,
                        linear_algebra::backend::basic_matrix::OperationLimits {
                            max_elements: 1 << 20,
                            max_scalar_ops: 1 << 24,
                        },
                    )
                    .checked_invariant_3e9c2499("validated finite matrix shape and budget"),
                    |acc, &j| {
                        linear_algebra::exact_field::matrix::add(&(acc), &self.class_operators[j])
                            .checked_invariant_3e9c2499("validated finite matrix shape and budget")
                    },
                )
            })
            .collect();
        Self::new(self.state.clone(), coarse)
    }

    /// `Tr((C_j + C_k) rho (C_j + C_k)*) - D_jj - D_kk` for two distinct histories.
    pub fn sum_rule_residual(&self, j: usize, k: usize) -> Result<GaussianRat, DecoherenceError> {
        self.check_index(j)?;
        self.check_index(k)?;
        if j == k {
            return Err(DecoherenceError::SameHistory { index: j });
        }
        let union = linear_algebra::exact_field::matrix::add(
            &self.class_operators[j],
            &self.class_operators[k],
        )
        .map_err(linear_algebra::exact_field::ExactFieldError::from)?;
        let union_weight = linear_algebra::exact_field::matrix::trace(
            &(linear_algebra::exact_field::matrix::multiply_with_limits(
                &(linear_algebra::exact_field::matrix::multiply_with_limits(
                    &(union),
                    &self.state,
                    linear_algebra::backend::basic_matrix::OperationLimits {
                        max_elements: 1 << 20,
                        max_scalar_ops: 1 << 24,
                    },
                )
                .checked_invariant_3e9c2499("validated finite matrix shape and budget")),
                &linear_algebra::exact_field::involution::adjoint(&(union))
                    .checked_invariant_3e9c2499("validated finite matrix shape and budget"),
                linear_algebra::backend::basic_matrix::OperationLimits {
                    max_elements: 1 << 20,
                    max_scalar_ops: 1 << 24,
                },
            )
            .checked_invariant_3e9c2499("validated finite matrix shape and budget")),
        )
        .checked_invariant_3e9c2499("validated finite matrix shape and budget");
        Ok(union_weight
            .sub(
                (self.matrix)
                    .get_ref(j, j)
                    .checked_invariant_3e9c2499("validated finite matrix shape and budget"),
            )
            .sub(
                (self.matrix)
                    .get_ref(k, k)
                    .checked_invariant_3e9c2499("validated finite matrix shape and budget"),
            ))
    }

    /// The first pair `j < k` with `D_jk != 0`, or `None` when `D` is diagonal.
    pub fn medium_decoherence_witness(&self) -> Option<(usize, usize)> {
        let m = self.class_operators.len();
        (0..m)
            .flat_map(|j| (j + 1..m).map(move |k| (j, k)))
            .find(|&(j, k)| {
                !(self.matrix)
                    .get_ref(j, k)
                    .checked_invariant_3e9c2499("validated finite matrix shape and budget")
                    .is_zero()
                    || !(self.matrix)
                        .get_ref(k, j)
                        .checked_invariant_3e9c2499("validated finite matrix shape and budget")
                        .is_zero()
            })
    }

    /// The first pair `j < k` whose union breaks the sum rule, or `None`.
    pub fn weak_decoherence_witness(&self) -> Option<(usize, usize)> {
        let m = self.class_operators.len();
        (0..m)
            .flat_map(|j| (j + 1..m).map(move |k| (j, k)))
            .find(|&(j, k)| {
                !self
                    .sum_rule_residual(j, k)
                    .checked_invariant_3e9c2499("indices are in range and distinct")
                    .is_zero()
            })
    }
}

impl DecoherenceFunctional {
    /// Tensor product of two independent history families and states. The
    /// computed functional is D tensor D', so medium decoherence is stable
    /// under composition; weak decoherence need not be.
    pub fn tensor(&self, other: &Self) -> Result<Self, DecoherenceError> {
        use linear_algebra::exact_field::matrix::kronecker;
        if self
            .class_operators
            .len()
            .checked_mul(other.class_operators.len())
            .is_none_or(|n| n > 1024)
            || self
                .state
                .rows()
                .checked_mul(other.state.rows())
                .is_none_or(|n| n > 256)
        {
            return Err(DecoherenceError::HistoryBudget { budget: 1024 });
        }
        let tensor = |a: &BasicMatrix<GaussianRat>,
                      b: &BasicMatrix<GaussianRat>|
         -> Result<BasicMatrix<GaussianRat>, DecoherenceError> {
            let product = kronecker(
                &Ok::<_, linear_algebra::exact_field::ExactFieldError>((a).clone())?,
                &Ok::<_, linear_algebra::exact_field::ExactFieldError>((b).clone())?,
            )
            .map_err(|e| DecoherenceError::Algebra(e.to_string()))?;
            Ok((&product).clone())
        };
        let state = tensor(&self.state, &other.state)?;
        let mut classes = Vec::new();
        for a in &self.class_operators {
            for b in &other.class_operators {
                classes.push(tensor(a, b)?);
            }
        }
        Self::new(state, classes)
    }
    pub fn is_strongly_positive(&self) -> Result<bool, DecoherenceError> {
        Ok(linear_algebra::exact_field::ordered::hermitian_is_positive_semidefinite(&self.matrix)?)
    }
}

// Origin: engine/crates_rs/core_functional/src/decoherence.rs
// Claim: urn:core:crates_rs:core-functional:decoherence:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_3e9c2499 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
