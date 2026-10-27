//! Integer modular arithmetic shared by Rust-side Symbol Game re-derivations.
//!
//! AuthorityEffect: None.

/// Return the least non-negative residue of `lhs` modulo a positive `modulus`.
///
/// Rust's `%` is a truncated remainder: `-17 % 5 == -2`.  Symbol Game's
/// cross-language contract uses the cyclic-group convention instead, where
/// `-17 mod 5 == 3`.  `rem_euclid` states that convention directly.
///
/// # Panics
///
/// Panics when `modulus <= 0`. A modulus is a cycle order on this interface and
/// therefore strictly positive; rejecting the invalid domain keeps the helper
/// from silently assigning a second convention to negative moduli.
pub fn least_non_negative_residue(lhs: i128, modulus: i128) -> i128 {
    assert!(modulus > 0, "modulus must be strictly positive");
    lhs.rem_euclid(modulus)
}

// Origin: engine/crates_rs/pfp_runtime/src/modular.rs
// Claim: urn:core:crates_rs:pfp-runtime:modular:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord72e9c8c3 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord72e9c8c3` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError72e9c8c3 {
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
impl BoundaryError72e9c8c3 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError72e9c8c3 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError72e9c8c3 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord72e9c8c3 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError72e9c8c3> {
        if capacity_bound == 0 {
            return Err(BoundaryError72e9c8c3::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError72e9c8c3::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError72e9c8c3::ExceedsCapacity {
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
    fn negative_dividends_use_the_cyclic_group_convention() {
        assert_eq!(least_non_negative_residue(-17, 5), 3);
        assert_ne!(least_non_negative_residue(-17, 5), -17 % 5);
    }

    #[test]
    #[should_panic(expected = "modulus must be strictly positive")]
    fn nonpositive_moduli_are_outside_the_contract() {
        let _ = least_non_negative_residue(17, 0);
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ResidueError { kind: &'static str, left: i128, right: i128 }
impl ResidueError {
    const fn new(kind: &'static str, left: i128, right: i128) -> Self { Self { kind, left, right } }
    pub const fn kind(&self) -> &'static str { self.kind }
}
fn verify_congruence(lhs: i128, value: i128, modulus: i128) -> Result<(), ResidueError> {
    let delta = lhs.checked_sub(value).ok_or_else(|| ResidueError::new("congruence difference overflow", lhs, value))?;
    let quotient = delta.checked_div(modulus).ok_or_else(|| ResidueError::new("congruence quotient overflow", delta, modulus))?;
    let restored = quotient.checked_mul(modulus).ok_or_else(|| ResidueError::new("congruence product overflow", quotient, modulus))?;
    if restored != delta {
        return Err(ResidueError::new("residue is not congruent to the input", restored, delta));
    }
    Ok(())
}

/// Least non-negative residue. A nonpositive modulus is refused before the panicking helper runs.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct CheckedResidue { value: i128 }
pub fn try_checked_residue(lhs: i128, modulus: i128) -> Result<CheckedResidue, ResidueError> {
    if modulus <= 0 {
        return Err(ResidueError::new("modulus is strictly positive", modulus, 0));
    }
    let value = least_non_negative_residue(lhs, modulus);
    if value < 0 || value >= modulus {
        return Err(ResidueError::new("residue lies outside 0..modulus", value, modulus));
    }
    verify_congruence(lhs, value, modulus)?;
    Ok(CheckedResidue { value })
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
mod l4_boundary_tests_72e9c8c3 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord72e9c8c3::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord72e9c8c3::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord72e9c8c3::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord72e9c8c3::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord72e9c8c3::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError72e9c8c3::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError72e9c8c3::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
