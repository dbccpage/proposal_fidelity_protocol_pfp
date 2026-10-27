//! reflective subcategory shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! A full subcategory i : A ↪ C is reflective when the inclusion admits
//! a left adjoint (reflector) r : C → A, r ⊣ i.

use serde::{Deserialize, Serialize};

/// Best-effort shell for a reflective subcategory declaration.
///
/// Records subcategory and reflector labels only — not a reflectivity proof.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReflectiveSubcategoryShell {
    pub label: String,
    /// Ambient category C.
    pub ambient_category: String,
    /// Subcategory A ⊆ C (full subcategory label).
    pub subcategory: String,
    /// Inclusion i : A → C label.
    pub inclusion: String,
    /// Reflector (left adjoint) r : C → A label.
    pub reflector: String,
    /// Optional unit ref for r ⊣ i.
    pub unit_ref: String,
    /// Optional counit ref for r ⊣ i.
    pub counit_ref: String,
    pub notes: Vec<String>,
}

impl ReflectiveSubcategoryShell {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            ambient_category: String::new(),
            subcategory: String::new(),
            inclusion: String::new(),
            reflector: String::new(),
            unit_ref: String::new(),
            counit_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn with_labels(
        label: impl Into<String>,
        ambient_category: impl Into<String>,
        subcategory: impl Into<String>,
        reflector: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            ambient_category: ambient_category.into(),
            subcategory: subcategory.into(),
            inclusion: String::new(),
            reflector: reflector.into(),
            unit_ref: String::new(),
            counit_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn with_inclusion(mut self, inclusion: impl Into<String>) -> Self {
        self.inclusion = inclusion.into();
        self
    }

    pub fn with_unit_counit(
        mut self,
        unit_ref: impl Into<String>,
        counit_ref: impl Into<String>,
    ) -> Self {
        self.unit_ref = unit_ref.into();
        self.counit_ref = counit_ref.into();
        self
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.ambient_category.is_empty() {
            return Err("empty ambient_category".into());
        }
        if self.subcategory.is_empty() {
            return Err("empty subcategory".into());
        }
        if self.reflector.is_empty() {
            return Err("empty reflector".into());
        }
        Ok(())
    }
}


/// A reflective subcategory includes into its ambient category, so the
/// subcategory cannot have more objects than the ambient category.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ReflectiveCensus {
    ambient_objects: u32,
    sub_objects: u32,
    complement: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ReflectiveCensusError {
    Shell,
    NotSubcategory { ambient_objects: u32, sub_objects: u32 },
    Overflow,
}

// Origin: engine/crates_rs/core_category_theory/src/adjunction/reflective_subcategory.rs
// Claim: urn:core:crates_rs:core-category-theory:reflective-subcategory:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ReflectiveCensusError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ReflectiveCensusError {}

impl ReflectiveCensus {
    pub fn admit(
        shell: &ReflectiveSubcategoryShell,
        ambient_objects: u32,
        sub_objects: u32,
    ) -> Result<Self, ReflectiveCensusError> {
        if shell.validate_shell().is_err() {
            return Err(ReflectiveCensusError::Shell);
        }
        if sub_objects > ambient_objects {
            return Err(ReflectiveCensusError::NotSubcategory {
                ambient_objects,
                sub_objects,
            });
        }
        let complement = ambient_objects
            .checked_sub(sub_objects)
            .ok_or(ReflectiveCensusError::Overflow)?;
        Ok(Self {
            ambient_objects,
            sub_objects,
            complement,
        })
    }

    pub fn complement(&self) -> u32 {
        self.complement
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        let r = ReflectiveSubcategoryShell::with_labels("refl", "C", "A", "r");
        assert!(r.validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(ReflectiveSubcategoryShell::new("")
            .validate_shell()
            .is_err());
    }

    #[test]
    fn with_inclusion_and_unit_ok() {
        let r = ReflectiveSubcategoryShell::with_labels("sheafification", "PSh", "Sh", "a")
            .with_inclusion("i")
            .with_unit_counit("η", "ε");
        assert_eq!(r.inclusion, "i");
        assert!(r.validate_shell().is_ok());
    }

    #[test]
    fn rejects_missing_reflector() {
        let r = ReflectiveSubcategoryShell::new("x").with_inclusion("i");
        // ambient/subcategory/reflector still empty
        let mut r = r;
        r.ambient_category = "C".into();
        r.subcategory = "A".into();
        assert!(r.validate_shell().is_err());
    }

    #[test]
    fn subcategory_cannot_outgrow_the_ambient_category() {
        let shell = ReflectiveSubcategoryShell::with_labels("refl", "C", "A", "r");
        let admitted = ReflectiveCensus::admit(&shell, 4, 1);
        assert!(admitted.is_ok());
        assert_eq!(admitted.ok().map(|witness| witness.complement()), Some(3));
        assert!(matches!(
            ReflectiveCensus::admit(&shell, 1, 4),
            Err(ReflectiveCensusError::NotSubcategory {
                ambient_objects: 1,
                sub_objects: 4
            })
        ));
    }

}
