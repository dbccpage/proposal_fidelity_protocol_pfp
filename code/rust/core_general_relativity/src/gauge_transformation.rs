//! `gauge_transformation` — finite dual-face object for `core_general_relativity`.
//!
//! AUTHORING_QUALITY: human_llm_best_effort_slop (best-effort dual-face scaffold; not human-canon math; not PROVED; not GlobalGreen).
//! **AuthorityEffect:** None.

/// Fence string (proposal).
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; best-effort scaffold.";

/// Finite carrier for `gauge_transformation` (proposal; not full classical object).
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct GaugeTransformation {
    /// Degree / dimension / stage proxy (ℕ₀).
    pub degree: usize,
    /// Stable label / object id (finite string).
    pub label: String,
}

impl GaugeTransformation {
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

// Origin: engine/crates_rs/core_general_relativity/src/gauge_transformation.rs
// Claim: urn:core:crates_rs:core-general-relativity:gauge-transformation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord0da49ee1 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord0da49ee1` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError0da49ee1 {
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
impl BoundaryError0da49ee1 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError0da49ee1 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError0da49ee1 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord0da49ee1 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError0da49ee1> {
        if capacity_bound == 0 {
            return Err(BoundaryError0da49ee1::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError0da49ee1::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError0da49ee1::ExceedsCapacity {
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
        let x = GaugeTransformation::new(1, "test");
        assert_eq!(x.degree, 1);
        assert_eq!(x.label, "test");
        assert!(GaugeTransformation::authority_fence().contains("AuthorityEffect None"));
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct WindingError { kind: &'static str, left: i128, right: i128 }
impl WindingError {
    const fn new(kind: &'static str, left: i128, right: i128) -> Self { Self { kind, left, right } }
    pub const fn kind(&self) -> &'static str { self.kind }
    pub const fn left(&self) -> i128 { self.left }
    pub const fn right(&self) -> i128 { self.right }
}

/// Integer winding in 0..order. Composition adds windings modulo the order.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct WindingClass { order: i128, charge: i128 }

fn normalize_winding_charge(total: i128, order: i128) -> Result<i128, WindingError> {
    let mut charge = total
        .checked_rem(order)
        .ok_or_else(|| WindingError::new("winding remainder failed", total, order))?;
    if charge < 0 {
        charge = charge
            .checked_add(order)
            .ok_or_else(|| WindingError::new("winding normalization overflow", charge, order))?;
    }
    if !(0..order).contains(&charge) {
        return Err(WindingError::new(
            "winding left the fundamental domain",
            charge,
            order,
        ));
    }
    Ok(charge)
}

impl WindingClass {
    pub fn try_from_steps(order: i64, steps: &[i64]) -> Result<Self, WindingError> {
        if order <= 0 {
            return Err(WindingError::new("winding order is positive", i128::from(order), 0));
        }
        let mut total = 0i128;
        for step in steps {
            total = total.checked_add(i128::from(*step)).ok_or_else(|| WindingError::new("winding sum overflow", total, i128::from(*step)))?;
        }
        let order = i128::from(order);
        let charge = normalize_winding_charge(total, order)?;
        Ok(Self { order, charge })
    }

    pub fn try_compose(&self, other: &Self) -> Result<Self, WindingError> {
        if self.order != other.order {
            return Err(WindingError::new("winding orders differ", self.order, other.order));
        }
        let sum = self.charge.checked_add(other.charge).ok_or_else(|| WindingError::new("composed winding overflow", self.charge, other.charge))?;
        let mut charge = sum.checked_rem(self.order).ok_or_else(|| WindingError::new("composed remainder failed", sum, self.order))?;
        if charge < 0 {
            charge = charge.checked_add(self.order).ok_or_else(|| WindingError::new("composed normalization overflow", charge, self.order))?;
        }
        Ok(Self { order: self.order, charge })
    }

    pub const fn charge(&self) -> i128 { self.charge }
    pub const fn order(&self) -> i128 { self.order }
}

#[cfg(test)]
mod winding_checks {
    use super::WindingClass;
    #[test]
    fn steps_reduce_and_compose_modulo_the_order() {
        let left = WindingClass::try_from_steps(5, &[3, 4]);
        assert_eq!(left.as_ref().map(WindingClass::charge), Ok(2));
        let right = WindingClass::try_from_steps(5, &[4]);
        let composed = left.and_then(|left| right.and_then(|right| left.try_compose(&right)));
        assert_eq!(composed.as_ref().map(WindingClass::charge), Ok(1));
    }
    #[test]
    fn a_nonpositive_order_is_refused() {
        assert_eq!(WindingClass::try_from_steps(0, &[1]).map(|_| ()).map_err(|e| e.kind()), Err("winding order is positive"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_0da49ee1 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord0da49ee1::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord0da49ee1::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord0da49ee1::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord0da49ee1::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord0da49ee1::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError0da49ee1::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError0da49ee1::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
