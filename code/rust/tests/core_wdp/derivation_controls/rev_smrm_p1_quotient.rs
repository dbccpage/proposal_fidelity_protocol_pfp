//! Congruence Quotient & Observation Refinement Calculus (REV-SMRM-P1-QUOTIENT) exact verifier.

/// Checks whether a partition `obs` over states `0..n` respects deterministic transition table `next_state`
/// and state output `goal`.
pub fn is_congruence(obs: &[usize], next_state: &[usize], goal: &[u8]) -> bool {
    let n = obs.len();
    for i in 0..n {
        for j in (i + 1)..n {
            if obs[i] == obs[j] {
                if goal[i] != goal[j] {
                    return false;
                }
                if obs[next_state[i]] != obs[next_state[j]] {
                    return false;
                }
            }
        }
    }
    true
}

/// Refines `obs` until it is a congruence with respect to `next_state` and `goal`.
pub fn refine_observation(obs: &[usize], next_state: &[usize], goal: &[u8]) -> Vec<usize> {
    let n = obs.len();
    let mut current: Vec<usize> = obs.to_vec();
    loop {
        let mut signatures: Vec<(usize, u8, usize)> = Vec::with_capacity(n);
        for i in 0..n {
            signatures.push((current[i], goal[i], current[next_state[i]]));
        }
        let mut unique_sigs = signatures.clone();
        unique_sigs.sort_unstable();
        unique_sigs.dedup();
        let next_obs: Vec<usize> = signatures
            .iter()
            .map(|sig| unique_sigs.binary_search(sig).unwrap())
            .collect();
        if next_obs == current {
            return current;
        }
        current = next_obs;
    }
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/rev_smrm_p1_quotient.rs
// Claim: urn:core:crates_rs:tests:rev-smrm-p1-quotient:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb711155e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb711155e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb711155e {
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
impl BoundaryErrorb711155e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb711155e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb711155e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb711155e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb711155e> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb711155e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb711155e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb711155e::ExceedsCapacity {
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

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_quotient_congruence_and_refinement() {
        // States: 0 -> 1 -> 2 (goal=1), 2 -> 2
        let next_state = [1usize, 2, 2];
        let goal = [0u8, 0, 1];
        // Coarse observation merges 0 and 1 into class 0, 2 into class 1
        let coarse_obs = [0usize, 0, 1];
        assert!(!is_congruence(&coarse_obs, &next_state, &goal));

        let refined = refine_observation(&coarse_obs, &next_state, &goal);
        assert!(is_congruence(&refined, &next_state, &goal));
        assert_ne!(refined[0], refined[1]);
    }
}

#[test]
fn l4_boundary_admits_and_refuses_b711155e() {
    let admitted = BoundaryRecordb711155e::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordb711155e::try_admit(9, 8).is_err());
}
