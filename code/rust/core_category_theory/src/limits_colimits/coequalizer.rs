//! coequalizer shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_4972ef65;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_4972ef65<T> = std::result::Result<T, BoundaryError_4972ef65>;
use serde::{Deserialize, Serialize};

/// Best-effort shell for a coequalizer of a parallel pair.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct Coequalizer {
    pub label: String,
    pub coequalizer_object: String,
    pub source: String,
    pub target: String,
    pub morphism_f: String,
    pub morphism_g: String,
    /// Coequalizer morphism q : target → Q with q∘f = q∘g.
    pub coequalizer_morphism: String,
    pub notes: Vec<String>,
}

impl Coequalizer {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            coequalizer_object: String::new(),
            source: String::new(),
            target: String::new(),
            morphism_f: String::new(),
            morphism_g: String::new(),
            coequalizer_morphism: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn of_pair(
        label: impl Into<String>,
        coequalizer_object: impl Into<String>,
        source: impl Into<String>,
        target: impl Into<String>,
        morphism_f: impl Into<String>,
        morphism_g: impl Into<String>,
        coequalizer_morphism: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            coequalizer_object: coequalizer_object.into(),
            source: source.into(),
            target: target.into(),
            morphism_f: morphism_f.into(),
            morphism_g: morphism_g.into(),
            coequalizer_morphism: coequalizer_morphism.into(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.coequalizer_object.is_empty() {
            return Err("empty coequalizer_object".into());
        }
        if self.source.is_empty() {
            return Err("empty source".into());
        }
        if self.target.is_empty() {
            return Err("empty target".into());
        }
        if self.morphism_f.is_empty() {
            return Err("empty morphism_f".into());
        }
        if self.morphism_g.is_empty() {
            return Err("empty morphism_g".into());
        }
        if self.coequalizer_morphism.is_empty() {
            return Err("empty coequalizer_morphism".into());
        }
        Ok(())
    }
}

// Origin: engine/crates_rs/core_category_theory/src/limits_colimits/coequalizer.rs
// Claim: urn:core:crates_rs:core-category-theory:coequalizer:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        let c = Coequalizer::of_pair("coeq", "Q", "A", "B", "f", "g", "q");
        assert!(c.validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(Coequalizer::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_missing_morphism() {
        assert!(Coequalizer::new("coeq").validate_shell().is_err());
    }
}

/// Coequalizer of a parallel pair of endofunctions, counted by union-find.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct EndoCoequalizer {
    points: usize,
    classes: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CoeqError {
    Bound,
    Image,
}

impl std::fmt::Display for CoeqError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            CoeqError::Bound => write!(formatter, "the carrier must lie in 1..=16"),
            CoeqError::Image => write!(formatter, "an endofunction leaves the carrier"),
        }
    }
}

impl std::error::Error for CoeqError {}

impl EndoCoequalizer {
    fn check_in_bounds(left: &[usize], right: &[usize], points: usize) -> Result<(), CoeqError> {
        for &image in left.iter().chain(right.iter()) {
            if image >= points {
                return Err(CoeqError::Image);
            }
        }
        Ok(())
    }

    fn merge_at(
        parent: &mut [usize],
        classes: &mut usize,
        left: &[usize],
        right: &[usize],
        index: usize,
    ) -> Result<(), CoeqError> {
        let left_image = *left.get(index).ok_or(CoeqError::Image)?;
        let right_image = *right.get(index).ok_or(CoeqError::Image)?;
        let left_root = find(parent, left_image)?;
        let right_root = find(parent, right_image)?;
        if left_root != right_root {
            if let Some(slot) = parent.get_mut(right_root) {
                *slot = left_root;
            }
            *classes -= 1;
        }
        Ok(())
    }

    pub fn classes(left: &[usize], right: &[usize]) -> Result<Self, CoeqError> {
        if left.is_empty() || left.len() > 16 || left.len() != right.len() {
            return Err(CoeqError::Bound);
        }
        let points = left.len();
        Self::check_in_bounds(left, right, points)?;
        let mut parent: Vec<usize> = (0..points).collect();
        let mut classes = points;
        for index in 0..points {
            Self::merge_at(&mut parent, &mut classes, left, right, index)?;
        }
        Ok(Self { points, classes })
    }

    pub fn classes_count(&self) -> usize {
        self.classes
    }
}

fn find(parent: &mut [usize], mut point: usize) -> Result<usize, CoeqError> {
    let mut root = point;
    for _step in 0..=parent.len() {
        let next = *parent.get(root).ok_or(CoeqError::Image)?;
        if next == root {
            break;
        }
        root = next;
    }
    if parent.get(root).copied() != Some(root) {
        return Err(CoeqError::Image);
    }
    for _step in 0..=parent.len() {
        let next = *parent.get(point).ok_or(CoeqError::Image)?;
        if next == root {
            break;
        }
        if let Some(slot) = parent.get_mut(point) {
            *slot = root;
        }
        point = next;
    }
    Ok(root)
}

#[cfg(test)]
mod coequalizer_tests {
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
    fn a_three_cycle_paired_with_the_identity_has_one_class() {
        let quotient = taken(EndoCoequalizer::classes(&[1, 2, 0], &[0, 1, 2]));
        assert_eq!(quotient.classes_count(), 1);
        assert!(EndoCoequalizer::classes(&[1, 2, 3], &[0, 1, 2]).is_err());
    }
}
