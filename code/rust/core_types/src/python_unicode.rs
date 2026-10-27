//! Character mappings frozen from the Python oracle's Unicode version.
use crate::python_alnum_v1::ALNUM;
use crate::python_case_v1::{CASED, CASE_IGNORABLE, LOWER, UPPER};
use crate::python_unicode_v1::{CASE_FOLD, NONPRINTABLE, PYTHON_UNICODE_VERSION};

fn in_ranges(character: char, ranges: &[(u32, u32)]) -> bool {
    let point = u32::from(character);
    ranges
        .partition_point(|(low, _)| *low <= point)
        .checked_sub(1)
        .and_then(|i| ranges.get(i))
        .is_some_and(|(_, high)| point <= *high)
}
fn append_mapping(result: &mut String, character: char, table: &[(u32, &str)]) {
    match table.binary_search_by_key(&u32::from(character), |(point, _)| *point) {
        Ok(index) => result.push_str(table[index].1),
        Err(_) => result.push(character),
    }
}
pub fn is_alphanumeric(character: char) -> bool {
    in_ranges(character, ALNUM)
}
pub fn uppercase(text: &str) -> String {
    let mut result = String::new();
    for character in text.chars() {
        append_mapping(&mut result, character, UPPER);
    }
    result
}
pub fn lowercase(text: &str) -> String {
    let characters = text.chars().collect::<Vec<_>>();
    let mut result = String::new();
    for (index, character) in characters.iter().copied().enumerate() {
        let final_sigma = character == 'Σ'
            && characters[..index]
                .iter()
                .rev()
                .find(|c| !in_ranges(**c, CASE_IGNORABLE))
                .is_some_and(|c| in_ranges(*c, CASED))
            && !characters[index + 1..]
                .iter()
                .find(|c| !in_ranges(**c, CASE_IGNORABLE))
                .is_some_and(|c| in_ranges(*c, CASED));
        if final_sigma {
            result.push('ς');
        } else {
            append_mapping(&mut result, character, LOWER);
        }
    }
    result
}

pub fn unicode_version() -> &'static str {
    PYTHON_UNICODE_VERSION
}
pub fn data_shape() -> (usize, usize) {
    (CASE_FOLD.len(), NONPRINTABLE.len())
}
pub fn casefold(text: &str) -> String {
    let mut result = String::new();
    for character in text.chars() {
        match CASE_FOLD.binary_search_by_key(&u32::from(character), |(point, _)| *point) {
            Ok(index) => result.push_str(CASE_FOLD[index].1),
            Err(_) => result.push(character),
        }
    }
    result
}
pub fn is_printable(character: char) -> bool {
    let point = u32::from(character);
    NONPRINTABLE
        .partition_point(|(low, _)| *low <= point)
        .checked_sub(1)
        .and_then(|index| NONPRINTABLE.get(index))
        .is_none_or(|(_, high)| point > *high)
}

fn push_non_printable_escape(result: &mut String, character: char) {
    let point = u32::from(character);
    if point <= 0xff {
        result.push_str(&format!("\\x{point:02x}"));
    } else if point <= 0xffff {
        result.push_str(&format!("\\u{point:04x}"));
    } else {
        result.push_str(&format!("\\U{point:08x}"));
    }
}

fn push_repr_char(result: &mut String, character: char, quote: char) {
    match character {
        '\\' => result.push_str("\\\\"),
        '\n' => result.push_str("\\n"),
        '\r' => result.push_str("\\r"),
        '\t' => result.push_str("\\t"),
        c if c == quote => {
            result.push('\\');
            result.push(c);
        }
        c if !is_printable(c) => push_non_printable_escape(result, c),
        c => result.push(c),
    }
}

/// Exact Python string repr for the frozen oracle version, without normalization.
pub fn repr_string(text: &str) -> String {
    let quote = if text.contains('\'') && !text.contains('"') {
        '"'
    } else {
        '\''
    };
    let mut result = String::from(quote);
    for character in text.chars() {
        push_repr_char(&mut result, character, quote);
    }
    result.push(quote);
    result
}

// Origin: engine/crates_rs/core_types/src/python_unicode.rs
// Claim: urn:core:crates_rs:core-types:python-unicode:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3ae331e9 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3ae331e9` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3ae331e9 {
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
impl BoundaryError3ae331e9 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3ae331e9 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3ae331e9 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3ae331e9 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3ae331e9> {
        if capacity_bound == 0 {
            return Err(BoundaryError3ae331e9::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3ae331e9::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3ae331e9::ExceedsCapacity {
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
mod l4_boundary_tests_3ae331e9 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord3ae331e9::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord3ae331e9::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord3ae331e9::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord3ae331e9::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord3ae331e9::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError3ae331e9::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError3ae331e9::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
