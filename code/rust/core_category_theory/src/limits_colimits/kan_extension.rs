//! kan_extension shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_33f946bc;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_33f946bc<T> = std::result::Result<T, BoundaryError_33f946bc>;
use serde::{Deserialize, Serialize};

/// Left or right Kan extension kind.
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum KanExtensionKind {
    /// Left Kan extension Lan_K F.
    #[default]
    Lan,
    /// Right Kan extension Ran_K F.
    Ran,
}

/// Best-effort shell for a (global) Kan extension along a functor.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct KanExtension {
    pub label: String,
    /// Extension kind: left (Lan) or right (Ran).
    pub kind: KanExtensionKind,
    /// Functor F being extended.
    pub functor_f: String,
    /// Functor K along which we extend (Lan_K F / Ran_K F).
    pub along_k: String,
    /// Extension functor (Lan_K F or Ran_K F) reference when claimed.
    pub extension_functor: String,
    /// Unit/counit natural transformation label (diagnostic).
    pub unit_counit_ref: String,
    pub notes: Vec<String>,
}

impl KanExtension {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            kind: KanExtensionKind::Lan,
            functor_f: String::new(),
            along_k: String::new(),
            extension_functor: String::new(),
            unit_counit_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn lan(
        label: impl Into<String>,
        functor_f: impl Into<String>,
        along_k: impl Into<String>,
        extension_functor: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            kind: KanExtensionKind::Lan,
            functor_f: functor_f.into(),
            along_k: along_k.into(),
            extension_functor: extension_functor.into(),
            unit_counit_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn ran(
        label: impl Into<String>,
        functor_f: impl Into<String>,
        along_k: impl Into<String>,
        extension_functor: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            kind: KanExtensionKind::Ran,
            functor_f: functor_f.into(),
            along_k: along_k.into(),
            extension_functor: extension_functor.into(),
            unit_counit_ref: String::new(),
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
        Ok(())
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn lan_validate_ok() {
        let k = KanExtension::lan("Lan_K F", "F", "K", "Lan");
        assert_eq!(k.kind, KanExtensionKind::Lan);
        assert!(k.validate_shell().is_ok());
    }

    #[test]
    fn ran_validate_ok() {
        let k = KanExtension::ran("Ran_K F", "F", "K", "Ran");
        assert_eq!(k.kind, KanExtensionKind::Ran);
        assert!(k.validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(KanExtension::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_missing_functors() {
        assert!(KanExtension::new("k").validate_shell().is_err());
    }

    #[test]
    fn kind_default_is_lan() {
        assert_eq!(KanExtensionKind::default(), KanExtensionKind::Lan);
    }
}

// Exact invariant envelope.
// Origin: engine/crates_rs/core_category_theory/src/limits_colimits/kan_extension.rs
// Claim: urn:core:category:kan:pointwise-fiber:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PointwiseKan {
    kind: KanExtensionKind,
    fibers: usize,
    value: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum PointwiseKanError {
    ShellRefused { reason: String },
    Overflow { index: usize },
    ClaimMismatch { computed: u64, claimed: u64 },
}

// Origin: engine/crates_rs/core_category_theory/src/limits_colimits/kan_extension.rs
// Claim: urn:core:crates_rs:core-category-theory:kan-extension:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for PointwiseKanError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for PointwiseKanError {}

impl PointwiseKan {
    pub fn try_on(shell: &KanExtension, fibers: &[u64], claimed: u64) -> Result<Self, PointwiseKanError> {
        shell
            .validate_shell()
            .map_err(|reason| PointwiseKanError::ShellRefused { reason })?;
        let value = match shell.kind {
            KanExtensionKind::Lan => {
                let mut total = 0u64;
                for (index, fiber) in fibers.iter().enumerate() {
                    total = total.checked_add(*fiber).ok_or(PointwiseKanError::Overflow { index })?;
                }
                total
            }
            KanExtensionKind::Ran => {
                let mut product = 1u64;
                for (index, fiber) in fibers.iter().enumerate() {
                    product = product.checked_mul(*fiber).ok_or(PointwiseKanError::Overflow { index })?;
                }
                product
            }
        };
        if value != claimed {
            return Err(PointwiseKanError::ClaimMismatch { computed: value, claimed });
        }
        Ok(Self {
            kind: shell.kind,
            fibers: fibers.len(),
            value,
        })
    }

    pub fn value(&self) -> u64 {
        self.value
    }

    pub fn kind(&self) -> KanExtensionKind {
        self.kind
    }
}

#[cfg(test)]
mod pointwise_kan_tests {
    use super::*;

    #[test]
    fn lan_sums_and_ran_multiplies() {
        let lan = KanExtension::lan("Lan", "F", "K", "LanF");
        let summed = PointwiseKan::try_on(&lan, &[2, 3], 5);
        assert!(matches!(summed, Ok(ref w) if w.kind() == KanExtensionKind::Lan && w.value() == 5));
        let ran = KanExtension::ran("Ran", "F", "K", "RanF");
        let multiplied = PointwiseKan::try_on(&ran, &[2, 3, 4], 24);
        assert!(matches!(multiplied, Ok(ref w) if w.value() == 24));
        let empty = PointwiseKan::try_on(&ran, &[], 1);
        assert!(matches!(empty, Ok(ref w) if w.value() == 1));
    }

    #[test]
    fn refuses_a_sum_claimed_as_a_product() {
        let lan = KanExtension::lan("Lan", "F", "K", "LanF");
        let wrong = PointwiseKan::try_on(&lan, &[2, 3], 6);
        assert!(matches!(
            wrong,
            Err(PointwiseKanError::ClaimMismatch { computed: 5, claimed: 6 })
        ));
    }
}
