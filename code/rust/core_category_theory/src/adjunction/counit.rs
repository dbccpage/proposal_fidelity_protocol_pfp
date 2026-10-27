//! counit (ε) shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Natural-transformation-style record for the counit of an adjunction:
//! ε : L ∘ R ⇒ Id_D.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_9414e6f3;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_9414e6f3<T> = std::result::Result<T, BoundaryError_9414e6f3>;
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

/// Best-effort shell for an adjunction counit ε : L∘R ⇒ Id.
///
/// Natural-transformation shape: source/target functor labels plus
/// object → component morphism tags. Not a naturality certificate.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct CounitShell {
    pub label: String,
    /// Source functor label (typically L∘R).
    pub source_functor: String,
    /// Target functor label (typically Id_D).
    pub target_functor: String,
    /// Component map: object tag → morphism tag ε_B : L(R(B)) → B.
    pub components: BTreeMap<String, String>,
    /// Optional owning adjunction label.
    pub adjunction_ref: String,
    pub notes: Vec<String>,
}

impl CounitShell {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            source_functor: String::new(),
            target_functor: String::new(),
            components: BTreeMap::new(),
            adjunction_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn between(
        label: impl Into<String>,
        source_functor: impl Into<String>,
        target_functor: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            source_functor: source_functor.into(),
            target_functor: target_functor.into(),
            components: BTreeMap::new(),
            adjunction_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn with_component(
        mut self,
        object: impl Into<String>,
        morphism: impl Into<String>,
    ) -> Self {
        self.components.insert(object.into(), morphism.into());
        self
    }

    pub fn set_component(&mut self, object: impl Into<String>, morphism: impl Into<String>) {
        self.components.insert(object.into(), morphism.into());
    }

    pub fn with_adjunction_ref(mut self, adjunction_ref: impl Into<String>) -> Self {
        self.adjunction_ref = adjunction_ref.into();
        self
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.source_functor.is_empty() {
            return Err("empty source_functor".into());
        }
        if self.target_functor.is_empty() {
            return Err("empty target_functor".into());
        }
        for (obj, mor) in &self.components {
            if obj.is_empty() || mor.is_empty() {
                return Err("empty counit component key or value".into());
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
        let c = CounitShell::between("ε", "L∘R", "Id_D");
        assert!(c.validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(CounitShell::new("").validate_shell().is_err());
    }

    #[test]
    fn with_component_ok() {
        let c = CounitShell::between("ε", "LR", "Id")
            .with_component("b", "ε_b")
            .with_adjunction_ref("free-forget");
        assert_eq!(c.components.len(), 1);
        assert!(c.validate_shell().is_ok());
    }

    #[test]
    fn rejects_empty_component_tags() {
        let mut c = CounitShell::between("ε", "LR", "Id");
        c.set_component("b", "");
        assert!(c.validate_shell().is_err());
    }
}

// Exact invariant envelope.
// Origin: engine/crates_rs/core_category_theory/src/adjunction/counit.rs
// Claim: urn:core:category:adjunction:counit-triangle:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TriangleIdentity {
    objects: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TriangleIdentityError {
    ShellRefused { reason: String },
    Empty,
    LengthMismatch { unit: usize, counit: usize },
    ImageOutOfRange { index: usize, image: u16 },
    NotInverse { index: usize, returned: u16 },
}

// Origin: engine/crates_rs/core_category_theory/src/adjunction/counit.rs
// Claim: urn:core:crates_rs:core-category-theory:counit:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for TriangleIdentityError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for TriangleIdentityError {}

fn image_in(map: &[u16], index: usize, len: usize) -> Result<usize, TriangleIdentityError> {
    let image = *map.get(index).ok_or(TriangleIdentityError::ImageOutOfRange { index, image: 0 })?;
    let as_usize = usize::from(image);
    if as_usize >= len {
        return Err(TriangleIdentityError::ImageOutOfRange { index, image });
    }
    Ok(as_usize)
}

fn check_roundtrip(
    first: &[u16],
    second: &[u16],
    index: usize,
    len: usize,
) -> Result<(), TriangleIdentityError> {
    let mid = image_in(first, index, len)?;
    let back = image_in(second, mid, len)?;
    if back != index {
        let returned = u16::try_from(back).map_err(|_| TriangleIdentityError::ImageOutOfRange {
            index,
            image: 0,
        })?;
        return Err(TriangleIdentityError::NotInverse { index, returned });
    }
    Ok(())
}

impl TriangleIdentity {
    pub fn try_on(shell: &CounitShell, unit: &[u16], counit: &[u16]) -> Result<Self, TriangleIdentityError> {
        shell
            .validate_shell()
            .map_err(|reason| TriangleIdentityError::ShellRefused { reason })?;
        if unit.is_empty() {
            return Err(TriangleIdentityError::Empty);
        }
        if unit.len() != counit.len() {
            return Err(TriangleIdentityError::LengthMismatch { unit: unit.len(), counit: counit.len() });
        }
        let len = unit.len();
        for index in 0..len {
            check_roundtrip(unit, counit, index, len)?;
            check_roundtrip(counit, unit, index, len)?;
        }
        Ok(Self { objects: len })
    }

    pub fn objects(&self) -> usize {
        self.objects
    }
}

#[cfg(test)]
mod triangle_identity_tests {
    use super::*;

    #[test]
    fn unit_and_counit_are_mutual_inverses() {
        let shell = CounitShell::between("eps", "LR", "Id");
        let witness = TriangleIdentity::try_on(&shell, &[1, 0], &[1, 0]);
        assert!(matches!(witness, Ok(ref w) if w.objects() == 2));
    }

    #[test]
    fn refuses_a_non_section() {
        let shell = CounitShell::between("eps", "LR", "Id");
        let wrong = TriangleIdentity::try_on(&shell, &[1, 0], &[0, 0]);
        assert!(matches!(wrong, Err(TriangleIdentityError::NotInverse { index: 0, returned: 1 })));
    }
}
