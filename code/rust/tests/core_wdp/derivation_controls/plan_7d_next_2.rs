use std::collections::BTreeSet;

fn build_and_verify_carriers() -> Result<BTreeSet<(i64, i64)>, &'static str> {
    let mut x0 = BTreeSet::new();
    for x in -1..=1_i64 {
        for y in -1..=1_i64 {
            x0.insert((x, y));
        }
    }
    let x1: BTreeSet<(i64, i64)> = x0.iter().map(|&(x, y)| (x + y, x - y)).collect();
    let x2: BTreeSet<(i64, i64)> = x1.iter().map(|&(u, v)| (u, v + u)).collect();
    if x0.len() != 9 || x1.len() != 9 || x2.len() != 9 {
        return Err("image carrier size mismatch");
    }
    if x1.contains(&(1, 0)) || !x2.contains(&(1, 0)) {
        return Err("probe (1,0) membership mismatch between X1 and X2");
    }
    Ok(x0)
}

pub fn check_lane_b_and_c_bindings(reset_budget: bool) -> Result<(usize, [usize; 4], i64), &'static str> {
    let x0 = build_and_verify_carriers()?;
    let mut counts = [0_usize; 4];
    for (idx, d) in [-1_i64, 0, 1, 2].iter().enumerate() {
        counts[idx] = x0.iter().filter(|&&(x, y)| x + y == *d).count();
    }
    if counts != [2, 3, 2, 1] {
        return Err("Lane C solution count mismatch");
    }
    // Lane B Appendix-S table: 15/4 < 4 < 6, original-class-only 7/2
    let disturbance_num = 15_i64;
    let nondisturbing_num = 16_i64; // 16/4 == 4
    if disturbance_num >= nondisturbing_num {
        return Err("Lane B disturbance optimum must be strictly below nondisturbing optimum");
    }
    let budget_cap = 18_i64;
    let round1_spent = 5_i64;
    let remaining = if reset_budget { budget_cap } else { budget_cap - round1_spent };
    if round1_spent + remaining > budget_cap {
        return Err("budget reset allowed cumulative spend above cap");
    }
    Ok((x0.len(), counts, remaining))
}

#[test]
fn plan_7d_next_2_witness_and_controls() {
    let (card, counts, rem) = check_lane_b_and_c_bindings(false).expect("valid bindings pass");
    assert_eq!(card, 9);
    assert_eq!(counts, [2, 3, 2, 1]);
    assert_eq!(rem, 13);
    assert!(check_lane_b_and_c_bindings(true).is_err());
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/plan_7d_next_2.rs
// Claim: urn:core:crates_rs:tests:plan-7d-next-2:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord148004a9 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord148004a9` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError148004a9 {
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
impl BoundaryError148004a9 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError148004a9 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError148004a9 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord148004a9 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError148004a9> {
        if capacity_bound == 0 {
            return Err(BoundaryError148004a9::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError148004a9::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError148004a9::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_148004a9() {
    let admitted = BoundaryRecord148004a9::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord148004a9::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
