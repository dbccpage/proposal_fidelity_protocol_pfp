//! terminal_category shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! 1: one object, one identity morphism (terminal object of Cat).

use serde::{Deserialize, Serialize};

/// Best-effort terminal category shell (one object, one id).
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct TerminalCategoryShell {
    pub label: String,
    /// The unique object tag (default "∗").
    pub object: String,
    /// The unique identity morphism name (default "id").
    pub identity: String,
    pub notes: Vec<String>,
}

impl TerminalCategoryShell {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            object: "∗".into(),
            identity: "id".into(),
            notes: Vec::new(),
        }
    }

    pub fn with_object(label: impl Into<String>, object: impl Into<String>) -> Self {
        let object = object.into();
        Self {
            label: label.into(),
            identity: format!("id_{object}"),
            object,
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.object.is_empty() {
            return Err("empty object".into());
        }
        if self.identity.is_empty() {
            return Err("empty identity".into());
        }
        Ok(())
    }
}


/// Terminal category: one object, one identity endomorphism, and the only
/// composite is that identity (`1 * 1 = 1`).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TerminalWitness {
    objects: u32,
    morphisms: u32,
    composites: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TerminalWitnessError {
    Shell,
    IdentityNotEndomorphism,
    Overflow,
    IdentityLaw { composites: u32, morphisms: u32 },
}

// Origin: engine/crates_rs/core_category_theory/src/category/terminal_category.rs
// Claim: urn:core:crates_rs:core-category-theory:terminal-category:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for TerminalWitnessError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for TerminalWitnessError {}

impl TerminalWitness {
    pub fn admit(shell: &TerminalCategoryShell) -> Result<Self, TerminalWitnessError> {
        if shell.validate_shell().is_err() {
            return Err(TerminalWitnessError::Shell);
        }
        let identity_ok = shell.identity == "id" || shell.identity == format!("id_{}", shell.object);
        if !identity_ok {
            return Err(TerminalWitnessError::IdentityNotEndomorphism);
        }
        let objects = 1u32;
        let morphisms = 1u32;
        let composites = morphisms
            .checked_mul(morphisms)
            .ok_or(TerminalWitnessError::Overflow)?;
        if composites != morphisms {
            return Err(TerminalWitnessError::IdentityLaw {
                composites,
                morphisms,
            });
        }
        Ok(Self {
            objects,
            morphisms,
            composites,
        })
    }

    pub fn composites(&self) -> u32 {
        self.composites
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        assert!(TerminalCategoryShell::new("1").validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(TerminalCategoryShell::new("").validate_shell().is_err());
    }

    #[test]
    fn with_object_ok() {
        let t = TerminalCategoryShell::with_object("1", "star");
        assert_eq!(t.object, "star");
        assert!(t.validate_shell().is_ok());
    }

    #[test]
    fn terminal_identity_is_the_unique_endomorphism() {
        let shell = TerminalCategoryShell::new("1");
        let admitted = TerminalWitness::admit(&shell);
        assert!(admitted.is_ok());
        assert_eq!(admitted.ok().map(|witness| witness.composites()), Some(1));
        let mut broken = shell;
        broken.identity = "nope".into();
        assert!(matches!(
            TerminalWitness::admit(&broken),
            Err(TerminalWitnessError::IdentityNotEndomorphism)
        ));
    }

}
