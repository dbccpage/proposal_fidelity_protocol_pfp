/// Exact categorization of operator types.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum OperatorKind {
    Constructor,
    Encoder,
    Generator,
    Lambda,
    Reducer,
    Transform,
}

/// Typed failure for operator application.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum OperatorFailure {
    ComputationFailed,
    DomainMismatch,
}

// --- exact carrier witness ---
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TypedOperator {
    kind: OperatorKind,
    domain: u32,
    codomain: u32,
}

impl TypedOperator {
    pub fn try_new(kind: OperatorKind, domain: u32, codomain: u32) -> Result<Self, OperatorFailure> {
        if domain == 0 || codomain == 0 {
            return Err(OperatorFailure::DomainMismatch);
        }
        match kind {
            OperatorKind::Encoder | OperatorKind::Reducer if codomain > domain => {
                return Err(OperatorFailure::DomainMismatch);
            }
            OperatorKind::Generator if domain != codomain => {
                return Err(OperatorFailure::DomainMismatch);
            }
            OperatorKind::Constructor | OperatorKind::Lambda | OperatorKind::Transform | OperatorKind::Encoder | OperatorKind::Reducer | OperatorKind::Generator => {}
        }
        Ok(Self { kind, domain, codomain })
    }

    pub fn compose(first: &Self, second: &Self) -> Result<Self, OperatorFailure> {
        if first.codomain != second.domain {
            return Err(OperatorFailure::DomainMismatch);
        }
        Self::try_new(OperatorKind::Transform, first.domain, second.codomain)
    }

    pub fn domain(&self) -> u32 { self.domain }
    pub fn codomain(&self) -> u32 { self.codomain }
    pub fn kind(&self) -> OperatorKind { self.kind }
}

// Origin: engine/crates_rs/core_types/src/operator.rs
// Claim: urn:core:crates_rs:core-types:operator:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord07bc7f8c {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord07bc7f8c` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError07bc7f8c {
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
impl BoundaryError07bc7f8c {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError07bc7f8c {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError07bc7f8c {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord07bc7f8c {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError07bc7f8c> {
        if capacity_bound == 0 {
            return Err(BoundaryError07bc7f8c::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError07bc7f8c::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError07bc7f8c::ExceedsCapacity {
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
mod typed_operator_tests {
    use super::*;

    #[test]
    fn an_encoder_composes_into_a_matching_transform() {
        let encoder = TypedOperator::try_new(OperatorKind::Encoder, 4, 2);
        let next = TypedOperator::try_new(OperatorKind::Transform, 2, 3);
        let composed = encoder.and_then(|encoder| next.and_then(|next| TypedOperator::compose(&encoder, &next)));
        assert!(matches!(composed, Ok(ref composed) if composed.domain() == 4 && composed.codomain() == 3));
    }

    #[test]
    fn a_reducer_cannot_widen_its_codomain() {
        let reducer = TypedOperator::try_new(OperatorKind::Reducer, 2, 4);
        assert!(matches!(reducer, Err(OperatorFailure::DomainMismatch)));
    }
}

#[cfg(test)]
mod l4_boundary_tests_07bc7f8c {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord07bc7f8c::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord07bc7f8c::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord07bc7f8c::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord07bc7f8c::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord07bc7f8c::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError07bc7f8c::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError07bc7f8c::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
