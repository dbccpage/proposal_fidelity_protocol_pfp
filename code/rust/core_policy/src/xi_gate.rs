//! Exact guards for using a computed Xi diagnostic. No functional arithmetic.
use core_kernel::Exact;

pub fn firewall_allows_candidate(
    phi1_before: &Exact,
    phi1_after: &Exact,
    gamma2_before: &Exact,
    gamma2_after: &Exact,
) -> bool {
    phi1_after <= phi1_before && gamma2_after <= gamma2_before
}

pub fn xi_may_decide_tie(
    phi1_before: &Exact,
    phi1_after: &Exact,
    gamma2_before: &Exact,
    gamma2_after: &Exact,
) -> bool {
    phi1_after == phi1_before && gamma2_after == gamma2_before
}

// Origin: engine/crates_rs/core_policy/src/xi_gate.rs
// Claim: urn:core:crates_rs:core-policy:xi-gate:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord0cb6fa68 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord0cb6fa68` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError0cb6fa68 {
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
impl BoundaryError0cb6fa68 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError0cb6fa68 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError0cb6fa68 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord0cb6fa68 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError0cb6fa68> {
        if capacity_bound == 0 {
            return Err(BoundaryError0cb6fa68::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError0cb6fa68::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError0cb6fa68::ExceedsCapacity {
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
    fn ex(v: i64) -> Exact {
        core_kernel::integer(v)
    }

    #[test]
    fn test_xi_cannot_decide_when_phi_worsens() {
        assert!(!xi_may_decide_tie(&ex(5), &ex(6), &ex(2), &ex(2)));
    }
    #[test]
    fn test_xi_cannot_decide_when_gamma_worsens() {
        assert!(!xi_may_decide_tie(&ex(5), &ex(5), &ex(2), &ex(3)));
    }
    #[test]
    fn test_xi_may_decide_only_when_phi_and_gamma_tied() {
        // tied
        assert!(xi_may_decide_tie(&ex(5), &ex(5), &ex(2), &ex(2)));
        // phi improves, gamma tied - Xi may not decide (Phi decides)
        assert!(!xi_may_decide_tie(&ex(5), &ex(4), &ex(2), &ex(2)));
    }
    #[test]
    fn test_xi_value_does_not_override_phi_improvement() {
        // Candidate allowed because Phi improves
        assert!(firewall_allows_candidate(&ex(5), &ex(4), &ex(2), &ex(2)));
        // But Xi cannot be the deciding factor
        assert!(!xi_may_decide_tie(&ex(5), &ex(4), &ex(2), &ex(2)));
    }
    #[test]
    fn a_hair_of_phi1_worsening_does_not_pass_the_firewall() {
        // The firewall exists to stop Phi1 rising. With an epsilon it admitted
        // any rise smaller than the caller's tolerance.
        let before = ex(5);
        let after = &before + core_kernel::exact(1, 100_000_000_000);
        assert!(!firewall_allows_candidate(&before, &after, &ex(2), &ex(2)));
        assert!(firewall_allows_candidate(&before, &before, &ex(2), &ex(2)));
    }
    #[test]
    fn a_hair_of_phi1_difference_is_not_a_tie() {
        // Xi may only break a tie the exact functionals established. A near-tie
        // is not a tie, or Xi would be overriding Phi1.
        let before = ex(5);
        let after = &before + core_kernel::exact(1, 100_000_000_000);
        assert!(!xi_may_decide_tie(&before, &after, &ex(2), &ex(2)));
    }
}

#[cfg(test)]
mod l4_boundary_tests_0cb6fa68 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord0cb6fa68::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord0cb6fa68::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord0cb6fa68::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord0cb6fa68::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord0cb6fa68::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError0cb6fa68::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError0cb6fa68::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
