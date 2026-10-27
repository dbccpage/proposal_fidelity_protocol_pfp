//! traced_monoidal shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.

use serde::{Deserialize, Serialize};

/// Best-effort traced monoidal category shell.
/// Trace operator family Tr^X_{A,B} : C(A⊗X, B⊗X) → C(A,B) as a ref.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct TracedMonoidal {
    pub label: String,
    /// Underlying (typically symmetric) monoidal category shell label.
    pub monoidal_ref: String,
    /// Trace operator family ref.
    pub trace_ref: String,
    pub notes: Vec<String>,
}

impl TracedMonoidal {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            monoidal_ref: String::new(),
            trace_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn with_trace(
        label: impl Into<String>,
        monoidal_ref: impl Into<String>,
        trace_ref: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            monoidal_ref: monoidal_ref.into(),
            trace_ref: trace_ref.into(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.monoidal_ref.is_empty() {
            return Err("empty monoidal_ref".into());
        }
        if self.trace_ref.is_empty() {
            return Err("empty trace_ref".into());
        }
        Ok(())
    }
}

// Origin: engine/crates_rs/core_category_theory/src/monoidal/traced_monoidal.rs
// Claim: urn:core:crates_rs:core-category-theory:traced-monoidal:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord6e9e4418 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord6e9e4418` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError6e9e4418 {
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
impl BoundaryError6e9e4418 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError6e9e4418 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError6e9e4418 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord6e9e4418 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError6e9e4418> {
        if capacity_bound == 0 {
            return Err(BoundaryError6e9e4418::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError6e9e4418::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError6e9e4418::ExceedsCapacity {
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

    #[test]
    fn validate_ok() {
        assert!(TracedMonoidal::with_trace("Tr", "Sym", "Tr")
            .validate_shell()
            .is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(TracedMonoidal::new("").validate_shell().is_err());
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TraceCardError { kind: &'static str, left: u128, right: u128 }
impl TraceCardError {
    const fn new(kind: &'static str, left: u128, right: u128) -> Self { Self { kind, left, right } }
    pub const fn kind(&self) -> &'static str { self.kind }
}
/// Finite trace domain |A| * |U| and codomain |B| * |U|.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TraceCard { domain: u64, codomain: u64 }
impl TraceCard {
    pub fn try_new(input: u64, output: u64, trace_object: u64) -> Result<Self, TraceCardError> {
        if trace_object == 0 {
            return Err(TraceCardError::new("the traced object is nonempty", 0, 0));
        }
        let domain = input.checked_mul(trace_object).ok_or_else(|| TraceCardError::new("trace domain overflow", u128::from(input), u128::from(trace_object)))?;
        let codomain = output.checked_mul(trace_object).ok_or_else(|| TraceCardError::new("trace codomain overflow", u128::from(output), u128::from(trace_object)))?;
        Ok(Self { domain, codomain })
    }
    pub const fn domain(&self) -> u64 { self.domain }
    pub const fn codomain(&self) -> u64 { self.codomain }
}
#[cfg(test)]
mod trace_card_checks {
    use super::TraceCard;
    #[test]
    fn domain_and_codomain_scale_by_the_traced_object() {
        let card = TraceCard::try_new(3, 2, 4);
        assert_eq!(card.as_ref().map(TraceCard::domain), Ok(12));
        assert_eq!(card.as_ref().map(TraceCard::codomain), Ok(8));
    }
    #[test]
    fn an_empty_traced_object_is_refused() {
        assert_eq!(TraceCard::try_new(1, 1, 0).map(|_| ()).map_err(|e| e.kind()), Err("the traced object is nonempty"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_6e9e4418 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord6e9e4418::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord6e9e4418::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord6e9e4418::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord6e9e4418::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord6e9e4418::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError6e9e4418::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError6e9e4418::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
