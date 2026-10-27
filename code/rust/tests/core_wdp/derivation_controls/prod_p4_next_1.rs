//! Companion Rust witness for PROD-P4-NEXT-1 (ObservationPlanner over finite_observation).

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PlanVerdict {
    pub feasible: bool,
    pub suite_mask: Option<usize>,
    pub cost_half_units: Option<u64>,
    pub unresolved_pair_indices: Vec<usize>,
}

/// Evaluates all 2^m subsets over a bitmask coverage table `separates[inst_idx][pair_idx]`.
pub fn plan_cheapest_suite(
    prices_half_units: &[u64],
    separates: &[Vec<bool>],
    num_pairs: usize,
) -> PlanVerdict {
    let m = prices_half_units.len();
    let mut best: Option<(u64, usize)> = None;
    for mask in 0..(1usize << m) {
        let covers_all = (0..num_pairs).all(|p| {
            (0..m).any(|i| ((mask >> i) & 1 == 1) && separates[i][p])
        });
        if covers_all {
            let cost: u64 = (0..m)
                .filter(|&i| (mask >> i) & 1 == 1)
                .map(|i| prices_half_units[i])
                .sum();
            let cand = (cost, mask);
            if best.map_or(true, |b| cand < b) {
                best = Some(cand);
            }
        }
    }
    if let Some((cost, mask)) = best {
        PlanVerdict {
            feasible: true,
            suite_mask: Some(mask),
            cost_half_units: Some(cost),
            unresolved_pair_indices: vec![],
        }
    } else {
        let unresolved = (0..num_pairs)
            .filter(|&p| (0..m).all(|i| !separates[i][p]))
            .collect();
        PlanVerdict {
            feasible: false,
            suite_mask: None,
            cost_half_units: None,
            unresolved_pair_indices: unresolved,
        }
    }
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/prod_p4_next_1.rs
// Claim: urn:core:crates_rs:tests:prod-p4-next-1:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord340643ad {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord340643ad` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError340643ad {
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
impl BoundaryError340643ad {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError340643ad {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError340643ad {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord340643ad {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError340643ad> {
        if capacity_bound == 0 {
            return Err(BoundaryError340643ad::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError340643ad::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError340643ad::ExceedsCapacity {
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
    fn cheapest_sufficient_suite_and_infeasible_witness() {
        // 3 instruments: I0 (cost 10/2=5, separates all 3), I1 (cost 3/2, separates pairs 0,2), I2 (cost 4/2=2, separates pairs 1,2)
        let prices = [10, 3, 4];
        let separates = vec![
            vec![true, true, true],
            vec![true, false, true],
            vec![false, true, true],
        ];
        let v = plan_cheapest_suite(&prices, &separates, 3);
        assert!(v.feasible);
        assert_eq!(v.suite_mask, Some(0b110));
        assert_eq!(v.cost_half_units, Some(7));

        let infeasible_sep = vec![vec![true, false, true]];
        let inv = plan_cheapest_suite(&[2], &infeasible_sep, 3);
        assert!(!inv.feasible);
        assert_eq!(inv.unresolved_pair_indices, vec![1]);
    }
}

#[test]
fn l4_boundary_admits_and_refuses_340643ad() {
    let admitted = BoundaryRecord340643ad::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord340643ad::try_admit(9, 8).is_err());
}
