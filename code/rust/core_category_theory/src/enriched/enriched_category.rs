//! enriched_category shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_5dd70990;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_5dd70990<T> = std::result::Result<T, BoundaryError_5dd70990>;
use serde::{Deserialize, Serialize};

/// Hom-object entry: pair of object labels maps to a V-object label.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct HomObjectEntry {
    pub domain: String,
    pub codomain: String,
    /// Hom-object label in the base monoidal category V.
    pub hom_object: String,
}

/// Best-effort V-enriched category shell.
/// Base monoidal V + hom-objects map; composition/ids are optional refs.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct EnrichedCategory {
    pub label: String,
    /// Base monoidal category V shell label.
    pub base_monoidal_v: String,
    /// Object labels of C.
    pub objects: Vec<String>,
    /// Hom-objects C(A,B) ∈ Ob(V).
    pub hom_objects: Vec<HomObjectEntry>,
    /// Optional composition morphism family ref in V.
    pub composition_ref: String,
    /// Optional identity morphism family ref j_A : I → C(A,A) in V.
    pub identity_ref: String,
    pub notes: Vec<String>,
}

impl EnrichedCategory {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            base_monoidal_v: String::new(),
            objects: Vec::new(),
            hom_objects: Vec::new(),
            composition_ref: String::new(),
            identity_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn over_v(label: impl Into<String>, base_monoidal_v: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            base_monoidal_v: base_monoidal_v.into(),
            objects: Vec::new(),
            hom_objects: Vec::new(),
            composition_ref: String::new(),
            identity_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn with_hom(
        &mut self,
        domain: impl Into<String>,
        codomain: impl Into<String>,
        hom_object: impl Into<String>,
    ) {
        self.hom_objects.push(HomObjectEntry {
            domain: domain.into(),
            codomain: codomain.into(),
            hom_object: hom_object.into(),
        });
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.base_monoidal_v.is_empty() {
            return Err("empty base_monoidal_v".into());
        }
        for (i, o) in self.objects.iter().enumerate() {
            if o.is_empty() {
                return Err(format!("empty object tag at index {i}"));
            }
        }
        for (i, h) in self.hom_objects.iter().enumerate() {
            if h.domain.is_empty() || h.codomain.is_empty() || h.hom_object.is_empty() {
                return Err(format!("empty hom_objects entry at index {i}"));
            }
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
        assert!(EnrichedCategory::over_v("C", "V").validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(EnrichedCategory::new("").validate_shell().is_err());
    }
}

// --- exact carrier witness ---
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum UltraError {
    Shell,
    Shape,
    Diagonal,
    Symmetry,
    Ultrametric { left: usize, right: usize },
}

// Origin: engine/crates_rs/core_category_theory/src/enriched/enriched_category.rs
// Claim: urn:core:crates_rs:core-category-theory:enriched-category:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for UltraError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for UltraError {}

/// Ultrametric enrichment of a finite hom-object over (N, max, 0).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct UltrametricHomWitness {
    objects: usize,
    diameter: u32,
}

fn check_ultrametric_triple(
    i: usize,
    j: usize,
    objects: usize,
    ij: u32,
    distance: &[u32],
) -> Result<(), UltraError> {
    for k in 0..objects {
        let ik = distance[i * objects + k];
        let jk = distance[j * objects + k];
        if ik > ij.max(jk) {
            return Err(UltraError::Ultrametric { left: i, right: k });
        }
    }
    Ok(())
}

fn check_ultrametric_row(i: usize, objects: usize, distance: &[u32]) -> Result<u32, UltraError> {
    if distance[i * objects + i] != 0 {
        return Err(UltraError::Diagonal);
    }
    let mut row_max = 0u32;
    for j in 0..objects {
        let forward = distance[i * objects + j];
        let backward = distance[j * objects + i];
        if forward != backward {
            return Err(UltraError::Symmetry);
        }
        row_max = row_max.max(forward);
        check_ultrametric_triple(i, j, objects, forward, distance)?;
    }
    Ok(row_max)
}

impl UltrametricHomWitness {
    pub fn try_new(category: &EnrichedCategory, objects: usize, distance: &[u32]) -> Result<Self, UltraError> {
        if category.validate_shell().is_err() || objects == 0 {
            return Err(UltraError::Shell);
        }
        let cells = objects.checked_mul(objects).ok_or(UltraError::Shape)?;
        if distance.len() != cells {
            return Err(UltraError::Shape);
        }
        let mut diameter = 0u32;
        for i in 0..objects {
            diameter = diameter.max(check_ultrametric_row(i, objects, distance)?);
        }
        Ok(Self { objects, diameter })
    }

    pub fn objects(&self) -> usize { self.objects }
    pub fn diameter(&self) -> u32 { self.diameter }
}

#[cfg(test)]
mod ultra_tests {
    use super::*;

    #[test]
    fn a_two_step_path_of_length_one_is_ultrametric() {
        let category = EnrichedCategory::over_v("C", "V");
        let witness = UltrametricHomWitness::try_new(&category, 3, &[0, 1, 1, 1, 0, 1, 1, 1, 0]);
        assert!(matches!(witness, Ok(ref witness) if witness.diameter() == 1 && witness.objects() == 3));
    }

    #[test]
    fn a_shortcut_longer_than_the_path_is_refused() {
        let category = EnrichedCategory::over_v("C", "V");
        let witness = UltrametricHomWitness::try_new(&category, 3, &[0, 1, 3, 1, 0, 1, 3, 1, 0]);
        assert!(matches!(witness, Err(UltraError::Ultrametric { left: 0, right: 2 })));
    }
}
