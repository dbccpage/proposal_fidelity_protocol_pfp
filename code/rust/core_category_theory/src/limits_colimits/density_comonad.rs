//! density_comonad shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_620b9d2e;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_620b9d2e<T> = std::result::Result<T, BoundaryError_620b9d2e>;
use serde::{Deserialize, Serialize};

/// Best-effort shell for the density comonad Lan_K K (or denseness data for K).
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct DensityComonad {
    pub label: String,
    /// Functor K whose density comonad is formed (typically Lan_K K).
    pub functor_k: String,
    /// Domain category of K.
    pub domain_category_ref: String,
    /// Codomain category of K.
    pub codomain_category_ref: String,
    /// Comonad / extension functor reference when claimed.
    pub comonad_ref: String,
    /// Optional left Kan extension shell label (diagnostic linkage).
    pub lan_ref: String,
    pub notes: Vec<String>,
}

impl DensityComonad {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            functor_k: String::new(),
            domain_category_ref: String::new(),
            codomain_category_ref: String::new(),
            comonad_ref: String::new(),
            lan_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn of_functor(
        label: impl Into<String>,
        functor_k: impl Into<String>,
        domain_category_ref: impl Into<String>,
        codomain_category_ref: impl Into<String>,
        comonad_ref: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            functor_k: functor_k.into(),
            domain_category_ref: domain_category_ref.into(),
            codomain_category_ref: codomain_category_ref.into(),
            comonad_ref: comonad_ref.into(),
            lan_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.functor_k.is_empty() {
            return Err("empty functor_k".into());
        }
        if self.domain_category_ref.is_empty() {
            return Err("empty domain_category_ref".into());
        }
        if self.codomain_category_ref.is_empty() {
            return Err("empty codomain_category_ref".into());
        }
        if self.comonad_ref.is_empty() {
            return Err("empty comonad_ref".into());
        }
        Ok(())
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        let d = DensityComonad::of_functor("dens", "K", "C", "D", "Lan_K K");
        assert!(d.validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(DensityComonad::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_missing_functor() {
        assert!(DensityComonad::new("d").validate_shell().is_err());
    }
}

// --- exact carrier witness ---
use std::collections::BTreeSet;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DensityLawError {
    Shell,
    Shape,
    Reflexive { object: usize },
    Transitive { left: usize, right: usize },
    Overflow,
}

// Origin: engine/crates_rs/core_category_theory/src/limits_colimits/density_comonad.rs
// Claim: urn:core:crates_rs:core-category-theory:density-comonad:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for DensityLawError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for DensityLawError {}

/// Comma counts of a full subcategory inside a finite preorder.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DensityCommaWitness {
    counts: Vec<u32>,
}

impl DensityCommaWitness {
    fn build_preorder(
        objects: usize,
        related: &[(usize, usize)],
    ) -> Result<BTreeSet<(usize, usize)>, DensityLawError> {
        let mut relation = BTreeSet::new();
        for &(left, right) in related {
            if left >= objects || right >= objects {
                return Err(DensityLawError::Shape);
            }
            relation.insert((left, right));
        }
        for object in 0..objects {
            if !relation.contains(&(object, object)) {
                return Err(DensityLawError::Reflexive { object });
            }
        }
        for &(left, middle) in &relation {
            for &(other, right) in &relation {
                if middle == other && !relation.contains(&(left, right)) {
                    return Err(DensityLawError::Transitive { left, right });
                }
            }
        }
        Ok(relation)
    }

    fn count_below_target(
        relation: &BTreeSet<(usize, usize)>,
        in_subcategory: &[bool],
        target: usize,
    ) -> Result<u32, DensityLawError> {
        let mut count = 0u32;
        for (source, &inside) in in_subcategory.iter().enumerate() {
            if inside && relation.contains(&(source, target)) {
                count = count.checked_add(1).ok_or(DensityLawError::Overflow)?;
            }
        }
        Ok(count)
    }

    pub fn try_new(shell: &DensityComonad, related: &[(usize, usize)], in_subcategory: &[bool]) -> Result<Self, DensityLawError> {
        if shell.validate_shell().is_err() {
            return Err(DensityLawError::Shell);
        }
        let objects = in_subcategory.len();
        if objects == 0 || objects > 8 {
            return Err(DensityLawError::Shape);
        }
        let relation = Self::build_preorder(objects, related)?;
        let mut counts = Vec::with_capacity(objects);
        for target in 0..objects {
            counts.push(Self::count_below_target(&relation, in_subcategory, target)?);
        }
        Ok(Self { counts })
    }

    pub fn counts(&self) -> &[u32] { &self.counts }
}

#[cfg(test)]
mod density_law_tests {
    use super::*;

    #[test]
    fn a_chain_counts_the_subcategory_below_each_object() {
        let shell = DensityComonad::of_functor("dens", "K", "C", "D", "Lan_K K");
        let witness = DensityCommaWitness::try_new(&shell, &[(0, 0), (1, 1), (0, 1)], &[true, false]);
        assert!(matches!(witness, Ok(ref witness) if witness.counts() == [1, 1]));
    }

    #[test]
    fn a_missing_composite_is_refused() {
        let shell = DensityComonad::of_functor("dens", "K", "C", "D", "Lan_K K");
        let related = [(0, 0), (1, 1), (2, 2), (0, 1), (1, 2)];
        let witness = DensityCommaWitness::try_new(&shell, &related, &[true, false, false]);
        assert!(matches!(witness, Err(DensityLawError::Transitive { left: 0, right: 2 })));
    }
}
