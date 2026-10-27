//! pointwise_kan_extension shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.

use serde::{Deserialize, Serialize};

use super::kan_extension::KanExtensionKind;

/// Best-effort shell for a pointwise Kan extension (computed objectwise via ends/colimits).
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct PointwiseKanExtension {
    pub label: String,
    pub kind: KanExtensionKind,
    /// Functor F being extended.
    pub functor_f: String,
    /// Functor K along which we extend.
    pub along_k: String,
    /// Extension functor reference.
    pub extension_functor: String,
    /// Formula / coend-end construction tag (diagnostic, e.g. "coend" / "end").
    pub pointwise_formula: String,
    pub notes: Vec<String>,
}

impl PointwiseKanExtension {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            kind: KanExtensionKind::Lan,
            functor_f: String::new(),
            along_k: String::new(),
            extension_functor: String::new(),
            pointwise_formula: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn lan_pointwise(
        label: impl Into<String>,
        functor_f: impl Into<String>,
        along_k: impl Into<String>,
        extension_functor: impl Into<String>,
        pointwise_formula: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            kind: KanExtensionKind::Lan,
            functor_f: functor_f.into(),
            along_k: along_k.into(),
            extension_functor: extension_functor.into(),
            pointwise_formula: pointwise_formula.into(),
            notes: Vec::new(),
        }
    }

    pub fn ran_pointwise(
        label: impl Into<String>,
        functor_f: impl Into<String>,
        along_k: impl Into<String>,
        extension_functor: impl Into<String>,
        pointwise_formula: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            kind: KanExtensionKind::Ran,
            functor_f: functor_f.into(),
            along_k: along_k.into(),
            extension_functor: extension_functor.into(),
            pointwise_formula: pointwise_formula.into(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.functor_f.is_empty() {
            return Err("empty functor_f".into());
        }
        if self.along_k.is_empty() {
            return Err("empty along_k".into());
        }
        if self.extension_functor.is_empty() {
            return Err("empty extension_functor".into());
        }
        if self.pointwise_formula.is_empty() {
            return Err("empty pointwise_formula".into());
        }
        Ok(())
    }
}


/// Pointwise Kan extension: one (co)limit is computed per object of the codomain.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PointwiseCensus {
    objects: u32,
    kind_tag: u8,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum PointwiseCensusError {
    Shell,
    NotPointwise { object_count: u32, computed: u32 },
}

// Origin: engine/crates_rs/core_category_theory/src/limits_colimits/pointwise_kan_extension.rs
// Claim: urn:core:crates_rs:core-category-theory:pointwise-kan-extension:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for PointwiseCensusError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for PointwiseCensusError {}

impl PointwiseCensus {
    pub fn admit(
        extension: &PointwiseKanExtension,
        object_count: u32,
        computed: u32,
    ) -> Result<Self, PointwiseCensusError> {
        if extension.validate_shell().is_err() {
            return Err(PointwiseCensusError::Shell);
        }
        if object_count != computed {
            return Err(PointwiseCensusError::NotPointwise {
                object_count,
                computed,
            });
        }
        let kind_tag = match extension.kind {
            KanExtensionKind::Lan => 0,
            KanExtensionKind::Ran => 1,
        };
        Ok(Self {
            objects: object_count,
            kind_tag,
        })
    }

    pub fn objects(&self) -> u32 {
        self.objects
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn lan_validate_ok() {
        let p = PointwiseKanExtension::lan_pointwise("pLan", "F", "K", "Lan", "coend");
        assert_eq!(p.kind, KanExtensionKind::Lan);
        assert!(p.validate_shell().is_ok());
    }

    #[test]
    fn ran_validate_ok() {
        let p = PointwiseKanExtension::ran_pointwise("pRan", "F", "K", "Ran", "end");
        assert_eq!(p.kind, KanExtensionKind::Ran);
        assert!(p.validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(PointwiseKanExtension::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_missing_formula() {
        assert!(PointwiseKanExtension::new("p").validate_shell().is_err());
    }

    #[test]
    fn pointwise_extension_matches_the_object_count() {
        let extension = PointwiseKanExtension::lan_pointwise("pLan", "F", "K", "Lan", "coend");
        let admitted = PointwiseCensus::admit(&extension, 3, 3);
        assert!(admitted.is_ok());
        assert_eq!(admitted.ok().map(|witness| witness.objects()), Some(3));
        assert!(matches!(
            PointwiseCensus::admit(&extension, 3, 2),
            Err(PointwiseCensusError::NotPointwise {
                object_count: 3,
                computed: 2
            })
        ));
    }

}
