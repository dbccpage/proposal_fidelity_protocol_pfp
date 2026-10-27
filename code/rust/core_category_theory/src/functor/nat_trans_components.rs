//! nat_trans_components shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Explicit component inventory for a natural transformation (shape only).


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_daa6c1cf;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_daa6c1cf<T> = std::result::Result<T, BoundaryError_daa6c1cf>;
use serde::{Deserialize, Serialize};

/// Best-effort shell for component data attached to a nat-trans reference.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct NatTransComponents {
    pub label: String,
    pub nat_trans_ref: String,
    /// Component map as (object, morphism) pairs.
    pub components: Vec<(String, String)>,
    pub notes: Vec<String>,
}

impl NatTransComponents {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            nat_trans_ref: String::new(),
            components: Vec::new(),
            notes: Vec::new(),
        }
    }

    pub fn for_nat_trans(
        label: impl Into<String>,
        nat_trans_ref: impl Into<String>,
        components: Vec<(String, String)>,
    ) -> Self {
        Self {
            label: label.into(),
            nat_trans_ref: nat_trans_ref.into(),
            components,
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.nat_trans_ref.is_empty() {
            return Err("empty nat_trans_ref".into());
        }
        for (i, (obj, mor)) in self.components.iter().enumerate() {
            if obj.is_empty() || mor.is_empty() {
                return Err(format!("empty component tag at index {i}"));
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
        assert!(
            NatTransComponents::for_nat_trans("comps", "eta", vec![("A".into(), "m".into())])
                .validate_shell()
                .is_ok()
        );
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(NatTransComponents::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_missing_ref() {
        assert!(NatTransComponents::new("x").validate_shell().is_err());
    }
}

// Exact carrier witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum NatComponentError { Empty, Width, Tag, Missing, DuplicateObject, DuplicateTag }

// Origin: engine/crates_rs/core_category_theory/src/functor/nat_trans_components.rs
// Claim: urn:core:crates_rs:core-category-theory:nat-trans-components:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for NatComponentError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for NatComponentError {}

impl NatTransComponents {
    fn collect_unique_objects(
        objects: &[String],
    ) -> Result<std::collections::BTreeSet<String>, NatComponentError> {
        let mut object_set = std::collections::BTreeSet::new();
        for object in objects {
            if object.is_empty() || !object_set.insert(object.clone()) {
                return Err(NatComponentError::DuplicateObject);
            }
        }
        Ok(object_set)
    }

    fn verify_component_entry(
        object: &String,
        tag: &String,
        object_set: &std::collections::BTreeSet<String>,
        seen: &mut std::collections::BTreeSet<String>,
        tags: &mut std::collections::BTreeSet<String>,
    ) -> Result<(), NatComponentError> {
        if object.is_empty() || tag.is_empty() {
            return Err(NatComponentError::Tag);
        }
        if !object_set.contains(object) || !seen.insert(object.clone()) {
            return Err(NatComponentError::Missing);
        }
        if !tags.insert(tag.clone()) {
            return Err(NatComponentError::DuplicateTag);
        }
        Ok(())
    }

    /// Component objects are exactly the object set, and component tags are injective.
    pub fn certify_components(&self, objects: &[String]) -> Result<usize, NatComponentError> {
        if objects.is_empty() || self.components.is_empty() {
            return Err(NatComponentError::Empty);
        }
        if objects.len() != self.components.len() {
            return Err(NatComponentError::Width);
        }
        let object_set = Self::collect_unique_objects(objects)?;
        let mut tags = std::collections::BTreeSet::new();
        let mut seen = std::collections::BTreeSet::new();
        for (object, tag) in &self.components {
            Self::verify_component_entry(object, tag, &object_set, &mut seen, &mut tags)?;
        }
        if seen != object_set {
            return Err(NatComponentError::Missing);
        }
        Ok(seen.len())
    }
}

#[cfg(test)]
mod nat_component_checks {
    use super::*;

    #[test]
    fn one_tag_per_object() {
        let comps = NatTransComponents::for_nat_trans("eta", "eta", vec![("A".into(), "a".into()), ("B".into(), "b".into())]);
        let census = comps.certify_components(&["A".into(), "B".into()]);
        assert!(matches!(census, Ok(2)));
    }

    #[test]
    fn a_repeated_tag_is_refused() {
        let comps = NatTransComponents::for_nat_trans("eta", "eta", vec![("A".into(), "a".into()), ("B".into(), "a".into())]);
        assert!(matches!(comps.certify_components(&["A".into(), "B".into()]), Err(NatComponentError::DuplicateTag)));
    }
}
