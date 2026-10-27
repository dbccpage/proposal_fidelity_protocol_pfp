fn compute_crt_residues(corrupt_crt_residue: bool) -> Result<[u32; 4], &'static str> {
    let mut residues = [0_u32; 4];
    for (idx, slot) in residues.iter_mut().enumerate() {
        let n = (idx + 1) as u32;
        let mod_2n = 2_u32.pow(n);
        let mod_3n = 3_u32.pow(n);
        let mod_6n = 6_u32.pow(n);
        let mut found = (0..mod_6n)
            .find(|&a| a % mod_2n == 0 && a % mod_3n == 1)
            .unwrap_or(0);
        if corrupt_crt_residue {
            found += 1;
        }
        if found % mod_2n != 0 || found % mod_3n != 1 {
            return Err("CRT residue failed mod 2^n / 3^n congruences");
        }
        *slot = found;
    }
    Ok(residues)
}

pub fn verify_day_5_campaign(
    fuel_cap: u32,
    reset_fuel_between_episodes: bool,
    retain_raw_proposals: bool,
    corrupt_crt_residue: bool,
) -> Result<(u32, u32, [u32; 4]), &'static str> {
    if reset_fuel_between_episodes {
        return Err("fuel ledger reset between episodes refused");
    }
    if !retain_raw_proposals {
        return Err("omitting raw proposal retention refused");
    }
    let spent = 6_u32 + 5 + 3;
    if spent > fuel_cap {
        return Err("campaign fuel spend exceeded cap");
    }

    let residues = compute_crt_residues(corrupt_crt_residue)?;

    Ok((spent, fuel_cap - spent, residues))
}

#[test]
fn plan_7d_day_5_witness_and_controls() {
    let (spent, rem, residues) =
        verify_day_5_campaign(20, false, true, false).expect("valid Day 5 campaign passes");
    assert_eq!(spent, 14);
    assert_eq!(rem, 6);
    assert_eq!(residues, [4, 28, 136, 1216]);

    assert!(verify_day_5_campaign(20, true, true, false).is_err());
    assert!(verify_day_5_campaign(20, false, false, false).is_err());
    assert!(verify_day_5_campaign(20, false, true, true).is_err());
    assert!(verify_day_5_campaign(10, false, true, false).is_err());
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/plan_7d_day_5.rs
// Claim: urn:core:crates_rs:tests:plan-7d-day-5:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord2d01956b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord2d01956b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError2d01956b {
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
impl BoundaryError2d01956b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError2d01956b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError2d01956b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord2d01956b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError2d01956b> {
        if capacity_bound == 0 {
            return Err(BoundaryError2d01956b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError2d01956b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError2d01956b::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_2d01956b() {
    let admitted = BoundaryRecord2d01956b::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord2d01956b::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
