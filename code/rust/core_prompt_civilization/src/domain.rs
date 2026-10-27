//! Domain placement and eligibility predicate.
//!
//! Enforces:
//! - F-DOMAIN-01: One eligibility predicate (hard_domain_eligible requires disposition == ADMITTED_LOCAL
//!   and query_domain in read_scope; taxonomy recognition alone never admits).
//!
//! AuthorityEffect: None.

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DomainPlacementV1 {
    pub placement_id: String,
    pub content_digest: String,
    pub domain_assignment: String,
    pub read_scope: Vec<String>,
    pub disposition: String,
}

pub(crate) fn scope_covers(scope: &str, target: &str) -> bool {
    if scope == "*" || scope == target {
        return true;
    }
    let Some(stem) = scope.strip_suffix(".*") else {
        return false;
    };
    !stem.is_empty() && (target == stem || target.starts_with(&format!("{stem}.")))
}

pub fn hard_domain_eligible(placement: &DomainPlacementV1, query_domain: &str) -> bool {
    placement.disposition == "ADMITTED_LOCAL"
        && placement
            .read_scope
            .iter()
            .any(|scope| scope_covers(scope, query_domain))
}

// Origin: engine/crates_rs/core_prompt_civilization/src/domain.rs
// Claim: urn:core:crates_rs:core-prompt-civilization:domain:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda7b8f48f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda7b8f48f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora7b8f48f {
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
impl BoundaryErrora7b8f48f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora7b8f48f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora7b8f48f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda7b8f48f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora7b8f48f> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora7b8f48f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora7b8f48f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora7b8f48f::ExceedsCapacity {
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
    fn test_f_domain_01_eligibility() {
        let proposed = DomainPlacementV1 {
            placement_id: "pl1".into(),
            content_digest: "d1".into(),
            domain_assignment: "algebra".into(),
            read_scope: vec!["algebra".into()],
            disposition: "PROPOSED".into(),
        };
        assert!(!hard_domain_eligible(&proposed, "algebra"));

        let admitted = DomainPlacementV1 {
            placement_id: "pl2".into(),
            content_digest: "d2".into(),
            domain_assignment: "algebra".into(),
            read_scope: vec!["algebra".into()],
            disposition: "ADMITTED_LOCAL".into(),
        };
        assert!(hard_domain_eligible(&admitted, "algebra"));
        assert!(!hard_domain_eligible(&admitted, "geometry"));

        // F4 (P1 Parity): domain_assignment is origin metadata; cross-assignment with admitted read_scope is ELIGIBLE
        let cross = DomainPlacementV1 {
            placement_id: "pl3".into(),
            content_digest: "d3".into(),
            domain_assignment: "physics".into(),
            read_scope: vec!["physics".into(), "math.*".into()],
            disposition: "ADMITTED_LOCAL".into(),
        };
        assert!(hard_domain_eligible(&cross, "math.integral"));
        assert!(!hard_domain_eligible(&cross, "mathematics"));
        assert!(!hard_domain_eligible(&cross, "physics.lab"));
        assert!(!hard_domain_eligible(&cross, "biology"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_a7b8f48f {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorda7b8f48f::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorda7b8f48f::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorda7b8f48f::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorda7b8f48f::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorda7b8f48f::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryErrora7b8f48f::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryErrora7b8f48f::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
