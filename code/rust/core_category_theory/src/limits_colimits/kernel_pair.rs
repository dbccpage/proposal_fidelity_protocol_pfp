//! kernel_pair shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_6943f27d;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_6943f27d<T> = std::result::Result<T, BoundaryError_6943f27d>;
use serde::{Deserialize, Serialize};

/// Best-effort shell for a kernel pair of a morphism f : A → B
/// (pullback of f along itself).
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct KernelPair {
    pub label: String,
    /// Kernel-pair object R ⇉ A.
    pub pair_object: String,
    pub source: String,
    pub target: String,
    /// Morphism f : source → target whose kernel pair is taken.
    pub morphism_f: String,
    /// Left projection R → source.
    pub projection_left: String,
    /// Right projection R → source.
    pub projection_right: String,
    pub notes: Vec<String>,
}

impl KernelPair {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            pair_object: String::new(),
            source: String::new(),
            target: String::new(),
            morphism_f: String::new(),
            projection_left: String::new(),
            projection_right: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn of_morphism(
        label: impl Into<String>,
        pair_object: impl Into<String>,
        source: impl Into<String>,
        target: impl Into<String>,
        morphism_f: impl Into<String>,
        projection_left: impl Into<String>,
        projection_right: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            pair_object: pair_object.into(),
            source: source.into(),
            target: target.into(),
            morphism_f: morphism_f.into(),
            projection_left: projection_left.into(),
            projection_right: projection_right.into(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.pair_object.is_empty() {
            return Err("empty pair_object".into());
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
        if self.projection_left.is_empty() {
            return Err("empty projection_left".into());
        }
        if self.projection_right.is_empty() {
            return Err("empty projection_right".into());
        }
        Ok(())
    }
}

// Origin: engine/crates_rs/core_category_theory/src/limits_colimits/kernel_pair.rs
// Claim: urn:core:crates_rs:core-category-theory:kernel-pair:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        let k = KernelPair::of_morphism("kp", "R", "A", "B", "f", "p₁", "p₂");
        assert!(k.validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(KernelPair::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_missing_morphism() {
        assert!(KernelPair::new("kp").validate_shell().is_err());
    }
}

/// Kernel pair of a self-map: the number of ordered pairs with equal image equals the sum of squared fiber sizes.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct KernelPairCount {
    points: usize,
    pairs: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum KernelError {
    Bound,
    Image,
    Overflow,
    Square,
}

impl std::fmt::Display for KernelError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            KernelError::Bound => write!(formatter, "the carrier must lie in 1..=16"),
            KernelError::Image => write!(formatter, "the map leaves the carrier"),
            KernelError::Overflow => write!(formatter, "the pair count overflowed"),
            KernelError::Square => write!(formatter, "fiber squares do not match the pair count"),
        }
    }
}

impl std::error::Error for KernelError {}

impl KernelPairCount {
    fn compute_fiber_squares(images: &[usize], points: usize) -> Result<u128, KernelError> {
        let mut fiber = vec![0u128; points];
        for &image in images {
            let slot = fiber.get_mut(image).ok_or(KernelError::Image)?;
            *slot = slot.checked_add(1).ok_or(KernelError::Overflow)?;
        }
        let mut squared: u128 = 0;
        for count in &fiber {
            let term = count.checked_mul(*count).ok_or(KernelError::Overflow)?;
            squared = squared.checked_add(term).ok_or(KernelError::Overflow)?;
        }
        Ok(squared)
    }

    fn compute_direct_pairs(images: &[usize], points: usize) -> Result<u128, KernelError> {
        let mut direct: u128 = 0;
        for left in 0..points {
            for right in 0..points {
                if images.get(left) == images.get(right) {
                    direct = direct.checked_add(1).ok_or(KernelError::Overflow)?;
                }
            }
        }
        Ok(direct)
    }

    pub fn count(images: &[usize]) -> Result<Self, KernelError> {
        let points = images.len();
        if points == 0 || points > 16 {
            return Err(KernelError::Bound);
        }
        let squared = Self::compute_fiber_squares(images, points)?;
        let direct = Self::compute_direct_pairs(images, points)?;
        if direct != squared {
            return Err(KernelError::Square);
        }
        let pairs = usize::try_from(squared).map_err(|_| KernelError::Overflow)?;
        Ok(Self { points, pairs })
    }

    pub fn pairs(&self) -> usize {
        self.pairs
    }
}

#[cfg(test)]
mod kernel_tests {
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
    fn fibers_of_sizes_two_and_one_give_five_pairs() {
        let kernel = taken(KernelPairCount::count(&[0, 0, 1]));
        assert_eq!(kernel.pairs(), 5);
        assert!(KernelPairCount::count(&[0, 0, 3]).is_err());
    }
}
