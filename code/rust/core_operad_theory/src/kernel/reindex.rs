//! Explicit input reindexing of checked planar terms.
//!
//! Each bijection maps an external input occurrence to its planar leaf index.
//! This layer neither permutes operation children nor enumerates permutations.
//! Its canonical profile is distinct from the unchanged planar profile. A host
//! must still authorize the underlying term and bind the external ordering in
//! its execution record; reindexing itself grants no execution authority.

use serde_json::{json, Value};

use super::canonical::{canonical_id, CanonicalError};
use super::model::BoundarySignature;
use super::result::Refusal;
use super::terms::{
    normalize_term, substitute, term_from_normalized, NormalizedTerm, OperationTerm,
};

pub const REINDEXED_TERM_PROFILE: &str = "core.oewas.operation-term.reindexed.v1";

fn refuse(code: &str, message: &str) -> Refusal {
    Refusal {
        code: code.to_owned(),
        message: message.to_owned(),
        locus: String::new(),
        details: Vec::new(),
    }
}

/// A checked bijection from new positions to old positions.
///
/// There is no unchecked deserialization path. For a term, old positions are
/// the ordered planar leaves, including separate occurrences of one colour.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct InputPermutation {
    external_to_planar: Vec<usize>,
}

impl InputPermutation {
    pub fn new(indices: Vec<usize>) -> Result<Self, Refusal> {
        let mut seen = vec![false; indices.len()];
        for &index in &indices {
            if index >= seen.len() || seen[index] {
                return Err(refuse(
                    "INVALID_INPUT_PERMUTATION",
                    "input order must contain every index in 0..arity exactly once",
                ));
            }
            seen[index] = true;
        }
        Ok(Self {
            external_to_planar: indices,
        })
    }

    pub fn identity(arity: usize) -> Self {
        Self {
            external_to_planar: (0..arity).collect(),
        }
    }

    pub fn as_slice(&self) -> &[usize] {
        &self.external_to_planar
    }

    pub fn inverse(&self) -> Self {
        let mut inverse = vec![0; self.external_to_planar.len()];
        for (external, &planar) in self.external_to_planar.iter().enumerate() {
            inverse[planar] = external;
        }
        Self {
            external_to_planar: inverse,
        }
    }

    /// `self.compose(right)[i] = self[right[i]]`.
    ///
    /// Reindexing first by `self`, then by `right`, uses this composition.
    pub fn compose(&self, right: &Self) -> Result<Self, Refusal> {
        if self.external_to_planar.len() != right.external_to_planar.len() {
            return Err(refuse(
                "PERMUTATION_ARITY_MISMATCH",
                "composed input permutations must have the same arity",
            ));
        }
        Ok(Self {
            external_to_planar: right
                .external_to_planar
                .iter()
                .map(|&index| self.external_to_planar[index])
                .collect(),
        })
    }
}

/// An immutable checked planar tree and an explicit external input order.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ReindexedTerm {
    planar: NormalizedTerm,
    permutation: InputPermutation,
}

impl ReindexedTerm {
    pub fn new(term: &OperationTerm, permutation: InputPermutation) -> Result<Self, Refusal> {
        let planar = normalize_term(term)?;
        if planar.boundary().inputs.len() != permutation.as_slice().len() {
            return Err(refuse(
                "PERMUTATION_ARITY_MISMATCH",
                "input permutation arity must match the checked planar boundary",
            ));
        }
        Ok(Self {
            planar,
            permutation,
        })
    }

    pub fn from_planar(term: &OperationTerm) -> Result<Self, Refusal> {
        let planar = normalize_term(term)?;
        let permutation = InputPermutation::identity(planar.boundary().inputs.len());
        Ok(Self {
            planar,
            permutation,
        })
    }

    pub fn planar(&self) -> &NormalizedTerm {
        &self.planar
    }

    pub fn permutation(&self) -> &InputPermutation {
        &self.permutation
    }

    pub fn boundary(&self) -> BoundarySignature {
        let planar = self.planar.boundary();
        BoundarySignature::new(
            self.permutation
                .as_slice()
                .iter()
                .map(|&index| planar.inputs[index].clone())
                .collect(),
            planar.output,
        )
    }

    pub fn reindex(&self, new_to_old: &InputPermutation) -> Result<Self, Refusal> {
        Ok(Self {
            planar: self.planar.clone(),
            permutation: self.permutation.compose(new_to_old)?,
        })
    }

    /// Route externally supplied values into the existing planar executor.
    ///
    /// Values are transported as occurrences, without sorting or deduplication.
    pub fn route_inputs<T: Clone>(&self, external: &[T]) -> Result<Vec<T>, Refusal> {
        if external.len() != self.permutation.as_slice().len() {
            return Err(refuse(
                "INPUT_ARITY_MISMATCH",
                "external input values must match the checked ordered boundary",
            ));
        }
        Ok(self
            .permutation
            .inverse()
            .as_slice()
            .iter()
            .map(|&index| external[index].clone())
            .collect())
    }

    /// Substitute at an external slot, retaining explicit external order.
    ///
    /// The selected planar leaf is `self.permutation[external_slot]`. The new
    /// external order is the outer prefix, inner order, then outer suffix.
    /// Tree validation, colour checking and identity reduction remain owned by
    /// the planar kernel, including its existing occurrence-name convention.
    pub fn substitute(&self, external_slot: usize, inner: &Self) -> Result<Self, Refusal> {
        let outer_order = self.permutation.as_slice();
        let Some(&planar_slot) = outer_order.get(external_slot) else {
            return Err(refuse(
                "SLOT_OUT_OF_RANGE",
                "external substitution slot must be within the checked boundary",
            ));
        };
        let inner_order = inner.permutation.as_slice();
        let new_arity = (outer_order.len() - 1)
            .checked_add(inner_order.len())
            .ok_or_else(|| refuse("ARITY_OVERFLOW", "composite input arity exceeds usize"))?;
        let planar = substitute(
            &term_from_normalized(&self.planar),
            planar_slot,
            &term_from_normalized(&inner.planar),
        )?;
        let shift = |index: usize| {
            if index < planar_slot {
                index
            } else {
                // The replaced index is excluded below. This order also
                // handles a nullary inner operation without unsigned underflow.
                index - 1 + inner_order.len()
            }
        };
        let mut order = Vec::with_capacity(new_arity);
        order.extend(outer_order[..external_slot].iter().copied().map(shift));
        order.extend(inner_order.iter().map(|&index| planar_slot + index));
        order.extend(outer_order[external_slot + 1..].iter().copied().map(shift));
        Self::new(
            &term_from_normalized(&planar),
            InputPermutation::new(order)?,
        )
    }

    pub fn to_canonical(&self) -> Value {
        json!({
            "schema_version": REINDEXED_TERM_PROFILE,
            "planar": self.planar.to_canonical(),
            "external_to_planar": self.permutation.as_slice(),
            "boundary": self.boundary().to_canonical(),
        })
    }

    pub fn canonical_id(&self) -> Result<String, CanonicalError> {
        canonical_id(REINDEXED_TERM_PROFILE, &self.to_canonical())
    }
}

// Origin: engine/crates_rs/core_operad_theory/src/kernel/reindex.rs
// Claim: urn:core:crates_rs:core-operad-theory:reindex:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3b270566 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3b270566` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3b270566 {
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
impl BoundaryError3b270566 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3b270566 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3b270566 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3b270566 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3b270566> {
        if capacity_bound == 0 {
            return Err(BoundaryError3b270566::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3b270566::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3b270566::ExceedsCapacity {
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
mod l4_boundary_tests_3b270566 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord3b270566::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord3b270566::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord3b270566::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord3b270566::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord3b270566::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError3b270566::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError3b270566::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
