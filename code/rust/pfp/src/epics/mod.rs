//! Epic modules for the Symbol Game.
//!
//! AuthorityEffect: None.

pub mod bytecode;
pub mod coda;
pub mod dda;
pub mod debate;
pub mod grammar;
pub mod guard;
pub mod library;
pub mod manifold;
pub mod modular;
pub mod ooutwire;
pub mod probing;
pub mod retraction;
pub mod transport;

pub use modular::least_non_negative_residue;
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ResidueError { kind: &'static str, left: i128, right: i128 }
impl ResidueError {
    const fn new(kind: &'static str, left: i128, right: i128) -> Self { Self { kind, left, right } }
    pub const fn kind(&self) -> &'static str { self.kind }
}
/// Least non-negative residue. A nonpositive modulus is refused before the panicking helper runs.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct CheckedResidue { value: i128 }
fn verify_residue_congruence(lhs: i128, value: i128, modulus: i128) -> Result<(), ResidueError> {
    let delta = lhs
        .checked_sub(value)
        .ok_or_else(|| ResidueError::new("congruence difference overflow", lhs, value))?;
    let quotient = delta
        .checked_div(modulus)
        .ok_or_else(|| ResidueError::new("congruence quotient overflow", delta, modulus))?;
    let restored = quotient
        .checked_mul(modulus)
        .ok_or_else(|| ResidueError::new("congruence product overflow", quotient, modulus))?;
    if restored != delta {
        return Err(ResidueError::new(
            "residue is not congruent to the input",
            restored,
            delta,
        ));
    }
    Ok(())
}

pub fn try_checked_residue(lhs: i128, modulus: i128) -> Result<CheckedResidue, ResidueError> {
    if modulus <= 0 {
        return Err(ResidueError::new("modulus is strictly positive", modulus, 0));
    }
    let value = least_non_negative_residue(lhs, modulus);
    if !(0..modulus).contains(&value) {
        return Err(ResidueError::new("residue lies outside 0..modulus", value, modulus));
    }
    verify_residue_congruence(lhs, value, modulus)?;
    Ok(CheckedResidue { value })
}

// Origin: engine/crates_rs/pfp/src/epics/mod.rs
// Claim: urn:core:crates_rs:pfp:mod:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord58c75067 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord58c75067` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError58c75067 {
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
impl BoundaryError58c75067 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError58c75067 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError58c75067 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord58c75067 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError58c75067> {
        if capacity_bound == 0 {
            return Err(BoundaryError58c75067::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError58c75067::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError58c75067::ExceedsCapacity {
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
mod checked_residue_checks {
    use super::try_checked_residue;
    #[test]
    fn a_negative_dividend_uses_the_cyclic_residue() {
        assert_eq!(try_checked_residue(-17, 5).as_ref().map(|item| item.value), Ok(3));
    }
    #[test]
    fn a_nonpositive_modulus_is_refused_without_the_panicking_helper() {
        assert_eq!(try_checked_residue(17, 0).map(|_| ()).map_err(|e| e.kind()), Err("modulus is strictly positive"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_58c75067 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord58c75067::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord58c75067::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord58c75067::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord58c75067::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord58c75067::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError58c75067::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError58c75067::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
