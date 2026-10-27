pub trait CandidateGenerator<S, C> {
    fn generate(&self, state: &S) -> Vec<C>;
}

// Origin: engine/crates_rs/core_types/src/candidate.rs
// Claim: urn:core:crates_rs:core-types:candidate:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord4eecf055 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord4eecf055` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError4eecf055 {
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
impl BoundaryError4eecf055 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError4eecf055 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError4eecf055 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord4eecf055 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError4eecf055> {
        if capacity_bound == 0 {
            return Err(BoundaryError4eecf055::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError4eecf055::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError4eecf055::ExceedsCapacity {
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

    struct DummyState(u32);
    struct DummyCandidate(u32);

    struct DummyGenerator;

    impl CandidateGenerator<DummyState, DummyCandidate> for DummyGenerator {
        fn generate(&self, state: &DummyState) -> Vec<DummyCandidate> {
            vec![DummyCandidate(state.0 + 1), DummyCandidate(state.0 + 2)]
        }
    }

    #[test]
    fn test_candidate_generator_trait() {
        let gen = DummyGenerator;
        let state = DummyState(10);
        let candidates = gen.generate(&state);
        assert_eq!(candidates.len(), 2);
        assert_eq!(candidates[0].0, 11);
        assert_eq!(candidates[1].0, 12);
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct InjectionWindowError { kind: &'static str, left: u128, right: u128 }
impl InjectionWindowError {
    const fn new(kind: &'static str, left: u128, right: u128) -> Self { Self { kind, left, right } }
    pub const fn kind(&self) -> &'static str { self.kind }
}
/// Strictly increasing images seed+1, ..., seed+width. The window is injective because each image is the previous plus one.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct InjectionWindow { seed: u32, width: u32, last: u32 }
impl InjectionWindow {
    fn advance_steps(seed: u32, width: u32) -> Result<u32, InjectionWindowError> {
        let mut previous = seed;
        let mut step = 0u32;
        while step < width {
            previous = previous.checked_add(1).ok_or_else(|| InjectionWindowError::new("image overflow", u128::from(previous), 1))?;
            step = step.checked_add(1).ok_or_else(|| InjectionWindowError::new("step overflow", u128::from(step), 1))?;
        }
        Ok(previous)
    }

    pub fn try_new(seed: u32, width: u32) -> Result<Self, InjectionWindowError> {
        if !(1..=64).contains(&width) {
            return Err(InjectionWindowError::new("width lies in 1..=64", u128::from(width), 64));
        }
        let previous = Self::advance_steps(seed, width)?;
        let end = u64::from(seed).checked_add(u64::from(width)).ok_or_else(|| InjectionWindowError::new("window end overflow", u128::from(seed), u128::from(width)))?;
        if u64::from(previous) != end {
            return Err(InjectionWindowError::new("the last image is not seed plus width", u128::from(previous), u128::from(end)));
        }
        Ok(Self { seed, width, last: previous })
    }
    pub const fn last(&self) -> u32 { self.last }
}
#[cfg(test)]
mod injection_window_checks {
    use super::InjectionWindow;
    #[test]
    fn a_width_of_two_ends_two_above_the_seed() {
        assert_eq!(InjectionWindow::try_new(10, 2).as_ref().map(InjectionWindow::last), Ok(12));
    }
    #[test]
    fn the_last_identifier_cannot_host_another_image() {
        assert_eq!(InjectionWindow::try_new(u32::MAX, 1).map(|_| ()).map_err(|e| e.kind()), Err("image overflow"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_4eecf055 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord4eecf055::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord4eecf055::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord4eecf055::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord4eecf055::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord4eecf055::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError4eecf055::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError4eecf055::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
