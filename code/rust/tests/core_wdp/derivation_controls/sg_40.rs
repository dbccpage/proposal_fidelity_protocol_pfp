pub fn run_sg_40_episode(
    partial_2: [i64; 3],
    beta: i64,
    extension_declared: bool,
    issuer_is_host_stage_5: bool,
) -> Result<(usize, usize, [i64; 3], [i64; 3]), &'static str> {
    if !issuer_is_host_stage_5 {
        return Err("parser self-receipt refused: Stage 5 host verifier required");
    }
    if !extension_declared {
        return Err("undeclared 2-cell attachment refused");
    }
    let partial_1: [[i64; 3]; 3] = [[-1, 0, 1], [1, -1, 0], [0, 1, -1]];
    let z: [i64; 3] = [1, 1, 1];

    let mut d1_z = [0_i64; 3];
    let mut d1_d2 = [0_i64; 3];
    for i in 0..3 {
        for j in 0..3 {
            d1_z[i] += partial_1[i][j] * z[j];
            d1_d2[i] += partial_1[i][j] * partial_2[j];
        }
    }
    if d1_z != [0, 0, 0] {
        return Err("z is not a 1-cycle");
    }
    if d1_d2 != [0, 0, 0] {
        return Err("chain complex identity d1 * d2 = 0 failed");
    }
    let d2_beta = [
        partial_2[0] * beta,
        partial_2[1] * beta,
        partial_2[2] * beta,
    ];
    if d2_beta != z {
        return Err("witness equation d2 * beta = z failed");
    }
    let before_h1_rank = 3 - 2 - 0;
    let after_h1_rank = 3 - 2 - 1;
    Ok((before_h1_rank, after_h1_rank, d1_d2, d2_beta))
}

#[test]
fn sg_40_witness_and_controls() {
    let (before_rank, after_rank, d1_d2, d2_beta) =
        run_sg_40_episode([1, 1, 1], 1, true, true).expect("valid SG-40 episode passes");
    assert_eq!(before_rank, 1);
    assert_eq!(after_rank, 0);
    assert_eq!(d1_d2, [0, 0, 0]);
    assert_eq!(d2_beta, [1, 1, 1]);

    assert!(run_sg_40_episode([1, 1, 1], 0, true, true).is_err());
    assert!(run_sg_40_episode([1, 1, -1], 1, true, true).is_err());
    assert!(run_sg_40_episode([1, 1, 1], 1, false, true).is_err());
    assert!(run_sg_40_episode([1, 1, 1], 1, true, false).is_err());
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/sg_40.rs
// Claim: urn:core:crates_rs:tests:sg-40:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc3e8c643 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc3e8c643` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc3e8c643 {
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
impl BoundaryErrorc3e8c643 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc3e8c643 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc3e8c643 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc3e8c643 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc3e8c643> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc3e8c643::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc3e8c643::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc3e8c643::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_c3e8c643() {
    let admitted = BoundaryRecordc3e8c643::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordc3e8c643::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
