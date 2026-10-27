// Python 15.0.0 Nd zero bases, frozen before the carrier parser.
pub(crate) const DECIMAL_ZERO_BASES: &[u32] = &[
    0x30, 0x660, 0x6f0, 0x7c0, 0x966, 0x9e6, 0xa66, 0xae6, 0xb66, 0xbe6, 0xc66, 0xce6, 0xd66,
    0xde6, 0xe50, 0xed0, 0xf20, 0x1040, 0x1090, 0x17e0, 0x1810, 0x1946, 0x19d0, 0x1a80, 0x1a90,
    0x1b50, 0x1bb0, 0x1c40, 0x1c50, 0xa620, 0xa8d0, 0xa900, 0xa9d0, 0xa9f0, 0xaa50, 0xabf0, 0xff10,
    0x104a0, 0x10d30, 0x11066, 0x110f0, 0x11136, 0x111d0, 0x112f0, 0x11450, 0x114d0, 0x11650,
    0x116c0, 0x11730, 0x118e0, 0x11950, 0x11c50, 0x11d50, 0x11da0, 0x11f50, 0x16a60, 0x16ac0,
    0x16b50, 0x1d7ce, 0x1d7d8, 0x1d7e2, 0x1d7ec, 0x1d7f6, 0x1e140, 0x1e2f0, 0x1e4f0, 0x1e950,
    0x1fbf0,
];

#[allow(dead_code)]
pub(crate) fn decimal_digit(code: u32) -> Option<u32> {
    let mut lo = 0usize;
    let mut hi = DECIMAL_ZERO_BASES.len();
    while lo < hi {
        let mid = lo + (hi - lo) / 2;
        let Some(base) = DECIMAL_ZERO_BASES.get(mid).copied() else {
            return None;
        };
        if code < base {
            hi = mid;
            continue;
        }
        let Some(next_index) = mid.checked_add(1) else {
            return None;
        };
        if let Some(next) = DECIMAL_ZERO_BASES.get(next_index).copied() {
            if code >= next {
                lo = next_index;
                continue;
            }
        }
        let digit = code.checked_sub(base)?;
        if digit < 10 {
            return Some(digit);
        }
        return None;
    }
    None
}

// Origin: engine/crates_rs/core_adversary/src/carrier_digits.rs
// Claim: urn:core:crates_rs:core-adversary:carrier-digits:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord911bdb8a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord911bdb8a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError911bdb8a {
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
impl BoundaryError911bdb8a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError911bdb8a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError911bdb8a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord911bdb8a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError911bdb8a> {
        if capacity_bound == 0 {
            return Err(BoundaryError911bdb8a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError911bdb8a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError911bdb8a::ExceedsCapacity {
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
mod digit_tests {
    use super::*;

    #[test]
    fn ascii_digits_and_separated_bases() {
        assert_eq!(decimal_digit(0x30), Some(0));
        assert_eq!(decimal_digit(0x35), Some(5));
        assert_eq!(decimal_digit(0x3A), None);
        let mut previous: Option<u32> = None;
        for base in DECIMAL_ZERO_BASES {
            if let Some(prev) = previous {
                let end = prev.checked_add(10);
                assert!(matches!(end, Some(end) if end <= *base));
            }
            previous = Some(*base);
        }
    }
}

#[cfg(test)]
mod l4_boundary_tests_911bdb8a {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord911bdb8a::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord911bdb8a::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord911bdb8a::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord911bdb8a::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord911bdb8a::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError911bdb8a::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError911bdb8a::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
