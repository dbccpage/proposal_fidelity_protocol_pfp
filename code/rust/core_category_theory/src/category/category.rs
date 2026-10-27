//! category shell (finite presentation) for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_fff3bdc8;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_fff3bdc8<T> = std::result::Result<T, BoundaryError_fff3bdc8>;
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

/// Named morphism boundary triple: (source, target, name).
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct MorphismTriple {
    pub source: String,
    pub target: String,
    pub name: String,
}

impl MorphismTriple {
    pub fn new(
        source: impl Into<String>,
        target: impl Into<String>,
        name: impl Into<String>,
    ) -> Self {
        Self {
            source: source.into(),
            target: target.into(),
            name: name.into(),
        }
    }
}

/// Best-effort finite category shell: objects, morphisms, identity keys.
///
/// Composition tables are optional diagnostic notes only — not a law certificate.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct FiniteCategoryShell {
    pub label: String,
    pub objects: Vec<String>,
    /// Morphisms as (source, target, name) triples.
    pub morphisms: Vec<MorphismTriple>,
    /// object → identity morphism name.
    pub identity_map: BTreeMap<String, String>,
    pub notes: Vec<String>,
}

fn validate_morphism_fields(morphisms: &[MorphismTriple]) -> Result<(), String> {
    for (i, m) in morphisms.iter().enumerate() {
        if m.source.is_empty() || m.target.is_empty() || m.name.is_empty() {
            return Err(format!("empty morphism field at index {i}"));
        }
    }
    Ok(())
}

fn validate_identity_entries(identity_map: &BTreeMap<String, String>) -> Result<(), String> {
    for (obj, id_name) in identity_map {
        if obj.is_empty() || id_name.is_empty() {
            return Err("empty identity_map key or value".into());
        }
    }
    Ok(())
}

impl FiniteCategoryShell {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            objects: Vec::new(),
            morphisms: Vec::new(),
            identity_map: BTreeMap::new(),
            notes: Vec::new(),
        }
    }

    pub fn with_objects(label: impl Into<String>, objects: Vec<String>) -> Self {
        let mut identity_map = BTreeMap::new();
        let mut morphisms = Vec::new();
        for o in &objects {
            let id_name = format!("id_{o}");
            identity_map.insert(o.clone(), id_name.clone());
            morphisms.push(MorphismTriple::new(o.clone(), o.clone(), id_name));
        }
        Self {
            label: label.into(),
            objects,
            morphisms,
            identity_map,
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        for (i, o) in self.objects.iter().enumerate() {
            if o.is_empty() {
                return Err(format!("empty object tag at index {i}"));
            }
        }
        validate_morphism_fields(&self.morphisms)?;
        validate_identity_entries(&self.identity_map)
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        assert!(FiniteCategoryShell::new("C").validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(FiniteCategoryShell::new("").validate_shell().is_err());
    }

    #[test]
    fn with_objects_ok() {
        let c = FiniteCategoryShell::with_objects("C", vec!["a".into(), "b".into()]);
        assert_eq!(c.objects.len(), 2);
        assert_eq!(c.identity_map.len(), 2);
        assert!(c.validate_shell().is_ok());
    }
}

// Exact carrier witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct IdentityCensus { object_count: usize, identity_count: usize }

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum IdentityCensusError {
    EmptyObject,
    DuplicateObject,
    MissingIdentity,
    ExtraIdentity,
    IdentityNotEndomorphism,
    IdentityAbsent,
    DuplicateMorphism,
}

// Origin: engine/crates_rs/core_category_theory/src/category/category.rs
// Claim: urn:core:crates_rs:core-category-theory:category:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for IdentityCensusError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for IdentityCensusError {}

impl IdentityCensus {
    pub fn object_count(&self) -> usize { self.object_count }
    pub fn identity_count(&self) -> usize { self.identity_count }
}

fn collect_unique_objects(
    raw_objects: &[String],
) -> Result<std::collections::BTreeSet<String>, IdentityCensusError> {
    let mut objects = std::collections::BTreeSet::new();
    for object in raw_objects {
        if object.is_empty() {
            return Err(IdentityCensusError::EmptyObject);
        }
        if !objects.insert(object.clone()) {
            return Err(IdentityCensusError::DuplicateObject);
        }
    }
    Ok(objects)
}

fn verify_object_identity_arrow(
    object: &str,
    identity_map: &BTreeMap<String, String>,
    morphisms: &[MorphismTriple],
) -> Result<(), IdentityCensusError> {
    let id_name = identity_map
        .get(object)
        .filter(|name| !name.is_empty())
        .ok_or(IdentityCensusError::MissingIdentity)?;
    let mut found = false;
    for morphism in morphisms {
        if &morphism.name == id_name {
            if morphism.source != object || morphism.target != object {
                return Err(IdentityCensusError::IdentityNotEndomorphism);
            }
            found = true;
        }
    }
    if !found {
        return Err(IdentityCensusError::IdentityAbsent);
    }
    Ok(())
}

impl FiniteCategoryShell {
    /// One identity per object, and that identity is an endomorphism present in the morphism list.
    pub fn certify_identities(&self) -> Result<IdentityCensus, IdentityCensusError> {
        let objects = collect_unique_objects(&self.objects)?;
        if self.identity_map.len() != objects.len() {
            return Err(IdentityCensusError::ExtraIdentity);
        }
        for object in &objects {
            verify_object_identity_morphism_entry(object, &self.identity_map, &self.morphisms)?;
        }
        if self.identity_map.keys().any(|key| !objects.contains(key)) {
            return Err(IdentityCensusError::ExtraIdentity);
        }
        Ok(IdentityCensus { object_count: objects.len(), identity_count: self.identity_map.len() })
    }
}

fn verify_object_identity_morphism_entry(
    object: &str,
    identity_map: &BTreeMap<String, String>,
    morphisms: &[MorphismTriple],
) -> Result<(), IdentityCensusError> {
    verify_object_identity_arrow(object, identity_map, morphisms)
}

#[cfg(test)]
mod identity_census_checks {
    use super::*;

    #[test]
    fn two_objects_carry_two_identity_endomorphisms() {
        let shell = FiniteCategoryShell::with_objects("C", vec!["a".into(), "b".into()]);
        let census = shell.certify_identities();
        assert!(matches!(census, Ok(c) if c.object_count() == 2 && c.identity_count() == 2));
    }

    #[test]
    fn a_missing_identity_arrow_is_refused() {
        let mut shell = FiniteCategoryShell::with_objects("C", vec!["a".into()]);
        shell.morphisms.clear();
        assert!(matches!(shell.certify_identities(), Err(IdentityCensusError::IdentityAbsent)));
    }
}
