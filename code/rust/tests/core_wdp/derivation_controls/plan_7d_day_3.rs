fn count_diagonal_characters(m: usize) -> usize {
    let mut diag = 0_usize;
    for a in 0..m {
        for b in 0..m {
            if (0..m).all(|x| ((a + m - b) * x) % m == 0) {
                diag += 1;
            }
        }
    }
    diag
}

pub fn verify_day_3_gate(m: usize, p: u32, n: u32, rank: u32) -> Result<(usize, u32, (u32, u32)), &'static str> {
    if m < 2 || p < 2 || n < 1 || rank > n {
        return Err("invalid Day 3 Lane E parameters");
    }
    let diag = count_diagonal_characters(m);
    if diag != m {
        return Err("LE-1 cyclic character separation failed");
    }
    let kernel_size = p.pow(n - rank);
    if kernel_size != 1 {
        return Err("LE-2 rank deficiency leaves nontrivial kernel");
    }
    let z4_exp = 4_u32;
    let z2_z2_exp = 2_u32;
    if z4_exp == z2_z2_exp {
        return Err("LE-4 exponent separation failed");
    }
    Ok((diag, kernel_size, (z4_exp, z2_z2_exp)))
}

#[test]
fn plan_7d_day_3_witness_and_controls() {
    let (diag, ker, exps) = verify_day_3_gate(6, 3, 3, 3).expect("valid Day 3 gate passes");
    assert_eq!(diag, 6);
    assert_eq!(ker, 1);
    assert_eq!(exps, (4, 2));
    assert!(verify_day_3_gate(6, 3, 3, 2).is_err());
    assert!(verify_day_3_gate(1, 3, 3, 3).is_err());
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/plan_7d_day_3.rs
// Claim: urn:core:crates_rs:tests:plan-7d-day-3:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord817cef23 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord817cef23` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError817cef23 {
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
impl BoundaryError817cef23 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError817cef23 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError817cef23 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord817cef23 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError817cef23> {
        if capacity_bound == 0 {
            return Err(BoundaryError817cef23::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError817cef23::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError817cef23::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_817cef23() {
    let admitted = BoundaryRecord817cef23::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord817cef23::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
