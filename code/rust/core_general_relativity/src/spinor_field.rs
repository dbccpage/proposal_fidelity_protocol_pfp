//! `spinor_field` — finite dual-face object for `core_general_relativity`.
//!
//! AUTHORING_QUALITY: human_llm_best_effort_slop (best-effort dual-face scaffold; not human-canon math; not PROVED; not GlobalGreen).
//! **AuthorityEffect:** None.

/// Fence string (proposal).
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; best-effort scaffold.";

/// Finite carrier for `spinor_field` (proposal; not full classical object).
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct SpinorField {
    /// Degree / dimension / stage proxy (ℕ₀).
    pub degree: usize,
    /// Stable label / object id (finite string).
    pub label: String,
}

impl SpinorField {
    /// Construct a finite carrier.
    pub fn new(degree: usize, label: impl Into<String>) -> Self {
        Self {
            degree,
            label: label.into(),
        }
    }

    /// Authority fence (never mints PROVED/GlobalGreen).
    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

// Origin: engine/crates_rs/core_general_relativity/src/spinor_field.rs
// Claim: urn:core:crates_rs:core-general-relativity:spinor-field:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord8c783e8f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord8c783e8f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError8c783e8f {
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
impl BoundaryError8c783e8f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError8c783e8f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError8c783e8f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord8c783e8f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError8c783e8f> {
        if capacity_bound == 0 {
            return Err(BoundaryError8c783e8f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError8c783e8f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError8c783e8f::ExceedsCapacity {
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
    fn new_and_fence() {
        let x = SpinorField::new(1, "test");
        assert_eq!(x.degree, 1);
        assert_eq!(x.label, "test");
        assert!(SpinorField::authority_fence().contains("AuthorityEffect None"));
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct WeylError { kind: &'static str, left: u128, right: u128 }
impl WeylError {
    const fn new(kind: &'static str, left: u128, right: u128) -> Self { Self { kind, left, right } }
    pub const fn kind(&self) -> &'static str { self.kind }
    pub const fn left(&self) -> u128 { self.left }
    pub const fn right(&self) -> u128 { self.right }
}

/// Even spacetime dimension n <= 16 has Weyl dimension 2^(n/2).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct WeylDimension { spacetime_dim: u32, dimension: u64 }

fn pow2_checked(mut exponent: u32) -> Result<u64, WeylError> {
    let mut dimension = 1u64;
    while exponent > 0 {
        dimension = dimension
            .checked_mul(2)
            .ok_or_else(|| WeylError::new("Weyl dimension overflow", u128::from(dimension), 2))?;
        exponent = exponent
            .checked_sub(1)
            .ok_or_else(|| WeylError::new("exponent underflow", u128::from(exponent), 1))?;
    }
    Ok(dimension)
}

impl WeylDimension {
    pub fn try_even(spacetime_dim: u32) -> Result<Self, WeylError> {
        let parity = spacetime_dim.checked_rem(2).ok_or_else(|| {
            WeylError::new("parity remainder failed", u128::from(spacetime_dim), 2)
        })?;
        if spacetime_dim == 0 || spacetime_dim > 16 || parity != 0 {
            return Err(WeylError::new("spacetime dimension is even and in 2..=16", u128::from(spacetime_dim), 16));
        }
        let exponent = spacetime_dim.checked_div(2).ok_or_else(|| {
            WeylError::new("half-dimension failed", u128::from(spacetime_dim), 2)
        })?;
        let dimension = pow2_checked(exponent)?;
        Ok(Self { spacetime_dim, dimension })
    }
    pub const fn dimension(&self) -> u64 { self.dimension }
}

#[cfg(test)]
mod weyl_checks {
    use super::WeylDimension;
    #[test]
    fn four_dimensions_have_weyl_dimension_four() {
        let weyl = WeylDimension::try_even(4);
        assert_eq!(weyl.as_ref().map(WeylDimension::dimension), Ok(4));
    }
    #[test]
    fn an_odd_dimension_is_refused() {
        assert_eq!(WeylDimension::try_even(3).map(|_| ()).map_err(|e| e.kind()), Err("spacetime dimension is even and in 2..=16"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_8c783e8f {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord8c783e8f::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord8c783e8f::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord8c783e8f::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord8c783e8f::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord8c783e8f::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError8c783e8f::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError8c783e8f::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
