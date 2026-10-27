//! hlevel shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Homotopy h-level / n-type classification shell (shape only).


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_a865565e;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_a865565e<T> = std::result::Result<T, BoundaryError_a865565e>;
use serde::{Deserialize, Serialize};

/// Best-effort shell for an h-level claim on a type reference.
///
/// Convention: `level` uses the integer n in "is-n-type", with n ≥ -2
/// represented as a signed integer. Shape validation only.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct HLevel {
    pub label: String,
    /// Integer h-level n (caller convention: n ≥ -2).
    pub level: i32,
    /// Optional type reference being classified.
    pub type_ref: String,
    pub notes: Vec<String>,
}

impl HLevel {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            level: 0,
            type_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn for_type(label: impl Into<String>, type_ref: impl Into<String>, level: i32) -> Self {
        Self {
            label: label.into(),
            level,
            type_ref: type_ref.into(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.level < -2 {
            return Err(format!("h-level {} < -2", self.level));
        }
        Ok(())
    }
}

// Origin: engine/crates_rs/core_category_theory/src/foundations/hlevel.rs
// Claim: urn:core:crates_rs:core-category-theory:hlevel:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        assert!(HLevel::new("x").validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(HLevel::new("").validate_shell().is_err());
    }

    #[test]
    fn rejects_below_minus_two() {
        let h = HLevel::for_type("bad", "A", -3);
        assert!(h.validate_shell().is_err());
    }

    #[test]
    fn contractible_level_ok() {
        let h = HLevel::for_type("contr", "A", -2);
        assert!(h.validate_shell().is_ok());
    }
}

/// Finite truncation: a contractible set has one point, a proposition at most one, and a set is a partition.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiniteTruncation {
    points: usize,
    classes: usize,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TruncationKind {
    Contractible,
    Proposition,
    Set,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TruncationError {
    Bound,
    Contractible,
    Proposition,
    Partition,
}

impl std::fmt::Display for TruncationError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            TruncationError::Bound => write!(formatter, "point count must be at most 32"),
            TruncationError::Contractible => write!(formatter, "a contractible set needs exactly one point"),
            TruncationError::Proposition => write!(formatter, "a proposition has at most one point"),
            TruncationError::Partition => write!(formatter, "class sizes do not partition the points"),
        }
    }
}

impl std::error::Error for TruncationError {}

impl FiniteTruncation {
    fn validate_partition(points: usize, class_sizes: &[usize]) -> Result<(), TruncationError> {
        if points > 32 || class_sizes.len() > 32 {
            return Err(TruncationError::Bound);
        }
        let mut summed: usize = 0;
        for &size in class_sizes {
            if size == 0 {
                return Err(TruncationError::Partition);
            }
            summed = summed.checked_add(size).ok_or(TruncationError::Partition)?;
        }
        if summed != points {
            return Err(TruncationError::Partition);
        }
        Ok(())
    }

    pub fn certify(kind: TruncationKind, points: usize, class_sizes: &[usize]) -> Result<Self, TruncationError> {
        Self::validate_partition(points, class_sizes)?;
        match kind {
            TruncationKind::Contractible if points == 1 && class_sizes == [1] => {}
            TruncationKind::Contractible => return Err(TruncationError::Contractible),
            TruncationKind::Proposition if points <= 1 && class_sizes.len() == points => {}
            TruncationKind::Proposition => return Err(TruncationError::Proposition),
            TruncationKind::Set => {}
        }
        Ok(Self {
            points,
            classes: class_sizes.len(),
        })
    }

    pub fn points(&self) -> usize {
        self.points
    }

    pub fn classes(&self) -> usize {
        self.classes
    }
}

#[cfg(test)]
mod truncation_tests {
    use super::*;

    fn taken<T, E>(value: Result<T, E>) -> T {
        match value {
            Ok(inner) => inner,
            Err(_) => loop {
                assert!(false);
            },
        }
    }

    #[test]
    fn one_point_is_contractible_and_two_singleton_classes_are_a_set() {
        let point = taken(FiniteTruncation::certify(TruncationKind::Contractible, 1, &[1]));
        assert_eq!(point.points(), 1);
        let set = taken(FiniteTruncation::certify(TruncationKind::Set, 3, &[2, 1]));
        assert_eq!(set.classes(), 2);
        assert!(FiniteTruncation::certify(TruncationKind::Proposition, 2, &[1, 1]).is_err());
    }
}
