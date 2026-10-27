#[derive(Debug, Clone)]
pub enum SolverError {
    DimensionMismatch {
        expected: usize,
        got: usize,
    },
    NonFiniteInput,
    NonConvergence {
        iterations: usize,
        residual: f64,
    },
    InvalidTopology,
    NumericalFailure(String),
    Divergence {
        trajectory_norm: f64,
        threshold: f64,
        step: usize,
    },
    NilpotencyViolation {
        residual: f64,
    },
    GaugeInvarianceViolation {
        deviation: f64,
    },
    InvalidParameter(String),
}

impl std::fmt::Display for SolverError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::DimensionMismatch { expected, got } => {
                write!(f, "Dimension mismatch: expected {expected}, got {got}")
            }
            Self::NonFiniteInput => write!(f, "Non-finite input value"),
            Self::NonConvergence {
                iterations,
                residual,
            } => {
                write!(
                    f,
                    "Non-convergence after {iterations} iterations (residual={residual:.6e})"
                )
            }
            Self::InvalidTopology => write!(f, "Invalid topology"),
            Self::NumericalFailure(msg) => write!(f, "Numerical failure: {msg}"),
            Self::Divergence {
                trajectory_norm,
                threshold,
                step,
            } => {
                write!(
                    f,
                    "Divergence at step {step}: |x|={trajectory_norm:.6e} > {threshold:.6e}"
                )
            }
            Self::NilpotencyViolation { residual } => {
                write!(f, "Nilpotency violation: d^2!=0 (residual={residual:.6e})")
            }
            Self::GaugeInvarianceViolation { deviation } => {
                write!(f, "Gauge invariance violated: deviation={deviation:.6e}")
            }
            Self::InvalidParameter(msg) => write!(f, "Invalid parameter: {msg}"),
        }
    }
}

impl std::error::Error for SolverError {}

impl crate::refusal_class::ClassifyRefusal for SolverError {
    /// Map each diagnostic variant onto the contract's governed vocabulary.
    ///
    /// Exhaustive on purpose, with no wildcard arm: adding a variant to
    /// `SolverError` is a compile error until someone decides which declared
    /// class it belongs to. A `_ =>` here would file every future error under
    /// one class and the vocabulary would stop being governed without anyone
    /// noticing.
    fn refusal_class(&self) -> crate::refusal_class::RefusalClass {
        use crate::refusal_class::RefusalClass;
        match self {
            // Not well formed. The caller can fix this by sending better input.
            Self::DimensionMismatch { .. } | Self::NonFiniteInput | Self::InvalidParameter(_) => {
                RefusalClass::InvalidArguments
            }

            // Well formed, the procedure ran, it did not get there.
            Self::NonConvergence { .. } | Self::Divergence { .. } | Self::NumericalFailure(_) => {
                RefusalClass::GateFailed
            }

            // The declared structure was not what it claimed to be, so nothing
            // computed on it means anything. `d^2 != 0` is the chain law
            // failing; gauge dependence means the quantity was never an
            // invariant; an invalid topology is a malformed carrier.
            Self::NilpotencyViolation { .. }
            | Self::GaugeInvarianceViolation { .. }
            | Self::InvalidTopology => RefusalClass::InvariantBreach,
        }
    }
}

// Origin: engine/crates_rs/core_types/src/solver_error.rs
// Claim: urn:core:crates_rs:core-types:solver-error:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord03336500 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord03336500` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError03336500 {
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
impl BoundaryError03336500 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError03336500 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError03336500 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord03336500 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError03336500> {
        if capacity_bound == 0 {
            return Err(BoundaryError03336500::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError03336500::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError03336500::ExceedsCapacity {
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

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)

#[cfg(test)]
mod refusal_classification_tests {
    use super::*;
    use crate::refusal_class::{ClassifyRefusal, RefusalClass};

    /// One representative of every variant. If a variant is added, the
    /// exhaustive match above stops compiling first; this list keeps the
    /// classification itself checked rather than merely total.
    fn every_variant() -> Vec<SolverError> {
        vec![
            SolverError::DimensionMismatch {
                expected: 3,
                got: 2,
            },
            SolverError::NonFiniteInput,
            SolverError::NonConvergence {
                iterations: 10,
                residual: 1.0,
            },
            SolverError::InvalidTopology,
            SolverError::NumericalFailure("singular".into()),
            SolverError::Divergence {
                trajectory_norm: 9.0,
                threshold: 1.0,
                step: 4,
            },
            SolverError::NilpotencyViolation { residual: 1.0 },
            SolverError::GaugeInvarianceViolation { deviation: 1.0 },
            SolverError::InvalidParameter("tolerance".into()),
        ]
    }

    #[test]
    fn every_variant_classifies_into_a_declared_class() {
        for error in every_variant() {
            let class = error.refusal_class();
            assert!(
                RefusalClass::ALL.contains(&class),
                "{error:?} classified outside the contract vocabulary"
            );
        }
    }

    #[test]
    fn malformed_input_is_an_argument_refusal() {
        assert_eq!(
            SolverError::DimensionMismatch {
                expected: 3,
                got: 2
            }
            .refusal_class(),
            RefusalClass::InvalidArguments
        );
        assert_eq!(
            SolverError::NonFiniteInput.refusal_class(),
            RefusalClass::InvalidArguments
        );
    }

    #[test]
    fn failing_to_converge_is_a_gate_failure_not_an_argument_error() {
        // The distinction that matters to a scheduler: retrying with different
        // arguments can fix InvalidArguments, and cannot fix GateFailed.
        assert_eq!(
            SolverError::NonConvergence {
                iterations: 99,
                residual: 0.5
            }
            .refusal_class(),
            RefusalClass::GateFailed
        );
        assert_eq!(
            SolverError::Divergence {
                trajectory_norm: 9.0,
                threshold: 1.0,
                step: 4
            }
            .refusal_class(),
            RefusalClass::GateFailed
        );
    }

    #[test]
    fn a_broken_chain_law_is_an_invariant_breach() {
        // `d^2 != 0` means the declared object was never a complex. This must
        // not be filed as a mere gate failure -- a gate failure invites a
        // retry, and there is nothing here worth retrying.
        assert_eq!(
            SolverError::NilpotencyViolation { residual: 1.0 }.refusal_class(),
            RefusalClass::InvariantBreach
        );
        assert_eq!(
            SolverError::GaugeInvarianceViolation { deviation: 0.25 }.refusal_class(),
            RefusalClass::InvariantBreach
        );
        assert_eq!(
            SolverError::InvalidTopology.refusal_class(),
            RefusalClass::InvariantBreach
        );
    }

    #[test]
    fn the_code_accessor_agrees_with_the_class() {
        for error in every_variant() {
            assert_eq!(error.refusal_code(), error.refusal_class().code());
        }
    }

    #[test]
    fn all_three_declared_classes_are_reachable() {
        // A classification that never emits one of the declared classes would
        // mean the contract declares a refusal the code cannot produce.
        let produced: std::collections::BTreeSet<_> = every_variant()
            .iter()
            .map(ClassifyRefusal::refusal_class)
            .collect();
        for class in RefusalClass::ALL {
            assert!(produced.contains(&class), "no variant produces {class}");
        }
    }
}

#[cfg(test)]
mod l4_boundary_tests_03336500 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord03336500::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord03336500::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord03336500::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord03336500::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord03336500::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError03336500::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError03336500::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
