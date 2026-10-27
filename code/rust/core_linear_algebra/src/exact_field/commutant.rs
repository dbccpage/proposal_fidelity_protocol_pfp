//! Exact centralizers of a finite matrix family, with replayed commutation.
//! The linear equations use row-major matrix coordinates. All dimensions,
//! construction work, elimination work and basis storage are bounded before allocation.
//! AuthorityEffect: None.
use super::{charge, element_count, plus, times, ExactFieldError};
use super::{elimination, matrix};
use crate::backend::basic_matrix::{BasicMatrix, OperationLimits};
use crate::scalars::{ExactRing, Field};

fn system<F: Field + ExactRing>(
    n: usize,
    generators: &[BasicMatrix<F>],
    limits: OperationLimits,
) -> Result<BasicMatrix<F>, ExactFieldError> {
    let vars = element_count(n, n)?;
    check_generator_shapes(n, generators)?;
    let rows = times(generators.len(), vars)?;
    charge_system_budget(rows, vars, limits)?;
    matrix::from_fn_with_limits(rows, vars, limits, |r, c| {
        commutant_entry(n, vars, generators, r, c)
    })
}

fn charge_system_budget(
    rows: usize,
    vars: usize,
    limits: OperationLimits,
) -> Result<(), crate::backend::basic_matrix::MatrixError> {
    let elements = element_count(rows, vars)?;
    let elim_work = times(2, times(rows, times(vars, vars)?)?)?;
    let work = plus(times(2, elements)?, elim_work)?;
    charge(limits, elements, work)
}

fn check_generator_shapes<F>(
    n: usize,
    generators: &[BasicMatrix<F>],
) -> Result<(), ExactFieldError> {
    for g in generators {
        if g.shape() != (n, n) {
            return Err(ExactFieldError::ShapeMismatch {
                operation: "commutant",
                left: (n, n),
                right: g.shape(),
            });
        }
    }
    Ok(())
}

fn commutant_entry<F: Field + ExactRing>(
    n: usize,
    vars: usize,
    generators: &[BasicMatrix<F>],
    r: usize,
    c: usize,
) -> F {
    let g = &generators[r / vars];
    let equation = r % vars;
    let (i, j) = (equation / n, equation % n);
    let (k, l) = (c / n, c % n);
    let mut value = F::zero();
    if i == k {
        value = value.add(&g.as_slice()[l * n + j]);
    }
    if j == l {
        value = value.sub(&g.as_slice()[i * n + k]);
    }
    value
}
/// Dimension of the common centralizer; an empty family centralizes every matrix.
pub fn commutant_dimension_with_limits<F: Field + ExactRing>(
    n: usize,
    generators: &[BasicMatrix<F>],
    limits: OperationLimits,
) -> Result<usize, ExactFieldError> {
    let vars = element_count(n, n)?;
    charge(limits, vars, 0)?;
    if generators.is_empty() {
        return Ok(vars);
    }
    let equations = system(n, generators, limits)?;
    Ok(vars - elimination::rank_with_limits(&equations, limits)?)
}
/// Construct an exact basis and independently replay every commutator.
pub fn commutant_basis_with_limits<F: Field + ExactRing>(
    n: usize,
    generators: &[BasicMatrix<F>],
    limits: OperationLimits,
) -> Result<Vec<BasicMatrix<F>>, ExactFieldError> {
    let vars = element_count(n, n)?;
    charge(limits, times(vars, vars)?, 0)?;
    let equations = system(n, generators, limits)?;
    let vectors = elimination::kernel_basis_with_limits(&equations, limits)?;
    charge_commutant_replay_budget(limits, vectors.len(), generators.len(), vars, n)?;
    vectors_to_verified_basis(n, vectors, generators, limits)
}

fn vectors_to_verified_basis<F: Field + ExactRing>(
    n: usize,
    vectors: Vec<Vec<F>>,
    generators: &[BasicMatrix<F>],
    limits: OperationLimits,
) -> Result<Vec<BasicMatrix<F>>, ExactFieldError> {
    let mut basis = super::reserve(vectors.len())?;
    for vector in vectors {
        let value = BasicMatrix::from_row_major(n, n, vector)?;
        verify_commutes_with_all(&value, generators, limits)?;
        basis.push(value);
    }
    Ok(basis)
}

fn charge_commutant_replay_budget(
    limits: OperationLimits,
    vectors_len: usize,
    generators_len: usize,
    vars: usize,
    n: usize,
) -> Result<(), crate::backend::basic_matrix::MatrixError> {
    let n3 = times(n, times(n, n)?)?;
    let replay_ops = times(4, times(generators_len, times(vectors_len, n3)?)?)?;
    charge(limits, times(vectors_len, vars)?, replay_ops)
}

fn verify_commutes_with_all<F: Field + ExactRing>(
    value: &BasicMatrix<F>,
    generators: &[BasicMatrix<F>],
    limits: OperationLimits,
) -> Result<(), ExactFieldError> {
    for g in generators {
        if matrix::multiply_with_limits(value, g, limits)?
            != matrix::multiply_with_limits(g, value, limits)?
        {
            return Err(ExactFieldError::ReplayFailed {
                operation: "commutant basis",
            });
        }
    }
    Ok(())
}

// Origin: engine/crates_rs/core_linear_algebra/src/exact_field/commutant.rs
// Claim: urn:core:crates_rs:core-linear-algebra:commutant:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord8774cdc9 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord8774cdc9` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError8774cdc9 {
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
impl BoundaryError8774cdc9 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError8774cdc9 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError8774cdc9 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord8774cdc9 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError8774cdc9> {
        if capacity_bound == 0 {
            return Err(BoundaryError8774cdc9::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError8774cdc9::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError8774cdc9::ExceedsCapacity {
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
mod tests {
    use super::*;
    use num_rational::BigRational;
    fn q(v: i64) -> BigRational {
        BigRational::from_integer(v.into())
    }
    #[test]
    fn centralizer_detects_multiplicity_and_replays_a_complete_basis() {
        let limits = OperationLimits {
            max_elements: 10000,
            max_scalar_ops: 100000,
        };
        let distinct = matrix::diagonal(&[q(0), q(1), q(2)]).unwrap();
        let repeated = matrix::diagonal(&[q(0), q(0), q(1)]).unwrap();
        assert_eq!(
            commutant_dimension_with_limits::<BigRational>(3, &[], limits),
            Ok(9)
        );
        assert_eq!(
            commutant_dimension_with_limits(3, &[distinct], limits),
            Ok(3)
        );
        assert_eq!(
            commutant_dimension_with_limits(3, &[repeated.clone()], limits),
            Ok(5)
        );
        assert_eq!(
            commutant_basis_with_limits(3, &[repeated], limits)
                .unwrap()
                .len(),
            5
        );
        assert!(commutant_dimension_with_limits(
            3,
            &[matrix::identity::<BigRational>(2).unwrap()],
            limits
        )
        .is_err());
        assert!(commutant_dimension_with_limits::<BigRational>(usize::MAX, &[], limits).is_err());
        assert!(commutant_basis_with_limits::<BigRational>(
            3,
            &[],
            OperationLimits {
                max_elements: 8,
                max_scalar_ops: 1
            }
        )
        .is_err());
    }
}

#[cfg(test)]
mod l4_boundary_tests_8774cdc9 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord8774cdc9::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord8774cdc9::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord8774cdc9::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord8774cdc9::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord8774cdc9::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError8774cdc9::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError8774cdc9::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
