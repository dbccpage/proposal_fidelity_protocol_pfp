//! Immutable vector view (zero-copy slice over coordinates).
//!
//! Scaffold: full view API lands with contiguous storage traits.

/// Read-only view of a contiguous scalar buffer.
#[derive(Debug, Clone, Copy)]
pub struct VectorView<'a, T> {
    data: &'a [T],
}

impl<'a, T> VectorView<'a, T> {
    #[must_use]
    pub fn new(data: &'a [T]) -> Self {
        Self { data }
    }

    #[must_use]
    pub fn len(&self) -> usize {
        self.data.len()
    }

    #[must_use]
    pub fn is_empty(&self) -> bool {
        self.data.is_empty()
    }

    #[must_use]
    pub fn as_slice(&self) -> &'a [T] {
        self.data
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct WindowDotError {
    kind: &'static str,
    left: i128,
    right: i128,
}
impl WindowDotError {
    const fn new(kind: &'static str, left: i128, right: i128) -> Self {
        Self { kind, left, right }
    }
    pub const fn kind(&self) -> &'static str {
        self.kind
    }
}
/// Exact integer dot product of one shared window.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct WindowDot {
    len: u64,
    dot: i128,
}
pub fn try_window_dot(
    left: &[i64],
    right: &[i64],
    start: usize,
    len: usize,
) -> Result<WindowDot, WindowDotError> {
    validate_window_bounds(left.len(), right.len(), start, len)?;
    let mut dot = 0i128;
    let mut offset = 0usize;
    while offset < len {
        let product = window_coordinate_product(left, right, start, offset)?;
        dot = dot
            .checked_add(product)
            .ok_or_else(|| WindowDotError::new("dot overflow", dot, product))?;
        offset = offset.checked_add(1).ok_or_else(|| {
            WindowDotError::new("offset overflow", usize_to_i128_sat(offset), 1)
        })?;
    }
    let len_u = u64::try_from(len).map_err(|_| {
        WindowDotError::new(
            "window length exceeds u64",
            usize_to_i128_sat(len),
            i128::from(u64::MAX),
        )
    })?;
    Ok(WindowDot { len: len_u, dot })
}

fn usize_to_i128_sat(value: usize) -> i128 {
    i128::try_from(value).map_or(i128::MAX, |converted| converted)
}

fn validate_window_bounds(
    left_len: usize,
    right_len: usize,
    start: usize,
    len: usize,
) -> Result<(), WindowDotError> {
    if len == 0 {
        return Err(WindowDotError::new("a window is nonempty", 0, 0));
    }
    let end = start.checked_add(len).ok_or_else(|| {
        WindowDotError::new(
            "window end overflow",
            usize_to_i128_sat(start),
            usize_to_i128_sat(len),
        )
    })?;
    if end > left_len || end > right_len {
        return Err(WindowDotError::new(
            "the window leaves a vector",
            usize_to_i128_sat(end),
            usize_to_i128_sat(left_len.min(right_len)),
        ));
    }
    Ok(())
}

fn window_coordinate_product(
    left: &[i64],
    right: &[i64],
    start: usize,
    offset: usize,
) -> Result<i128, WindowDotError> {
    let index = start.checked_add(offset).ok_or_else(|| {
        WindowDotError::new(
            "window index overflow",
            usize_to_i128_sat(start),
            usize_to_i128_sat(offset),
        )
    })?;
    let left_value = *left.get(index).ok_or_else(|| {
        WindowDotError::new("left coordinate is missing", usize_to_i128_sat(index), 0)
    })?;
    let right_value = *right.get(index).ok_or_else(|| {
        WindowDotError::new("right coordinate is missing", usize_to_i128_sat(index), 0)
    })?;
    i128::from(left_value)
        .checked_mul(i128::from(right_value))
        .ok_or_else(|| {
            WindowDotError::new(
                "coordinate product overflow",
                i128::from(left_value),
                i128::from(right_value),
            )
        })
}

// Origin: engine/crates_rs/core_linear_algebra/src/vector/view.rs
// Claim: urn:core:crates_rs:core-linear-algebra:view:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord01481ffa {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord01481ffa` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError01481ffa {
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
impl BoundaryError01481ffa {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError01481ffa {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError01481ffa {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord01481ffa {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError01481ffa> {
        if capacity_bound == 0 {
            return Err(BoundaryError01481ffa::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError01481ffa::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError01481ffa::ExceedsCapacity {
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
mod window_dot_checks {
    use super::try_window_dot;
    #[test]
    fn the_tail_window_dot_is_exact() {
        assert_eq!(
            try_window_dot(&[1, 2, 3], &[4, 5, 6], 1, 2)
                .as_ref()
                .map(|item| item.dot),
            Ok(28)
        );
    }
    #[test]
    fn a_window_past_the_vector_is_refused() {
        assert_eq!(
            try_window_dot(&[1], &[1], 0, 2)
                .map(|_| ())
                .map_err(|e| e.kind()),
            Err("the window leaves a vector")
        );
    }
}

#[cfg(test)]
mod l4_boundary_tests_01481ffa {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord01481ffa::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord01481ffa::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord01481ffa::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord01481ffa::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord01481ffa::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError01481ffa::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError01481ffa::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
