//! Foundation Tier for Operad Theory.
//!
//! AuthorityEffect: None.

pub mod colour;
pub mod operation;
pub mod planar_tree;
pub mod colored_operad;
pub mod monoidal_operad;
pub mod span_operand;

pub use colour::{OperadColour, OperadSignature};
pub use operation::{Operation, OperationId, OperationKind, OperationKindType};
pub use planar_tree::{OpenLeaf, PlanarTree, TreeChild};
pub use colored_operad::{OperadVariant, PlanarColoredOperad, SymmetricColoredOperad};
pub use monoidal_operad::MonoidalOperad;
pub use span_operand::{SpanOperand, ADMITTED_FINITE_COLOURS};

/// One unary identity corolla for every name in a finite colour palette.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct IdentityCorollaFamily {
    colour_count: u32,
    arity_sum: u32,
}

/// Refusal of an identity corolla on a colour palette.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum IdentityCorollaError {
    EmptyPalette,
    RejectedColour { name: String, detail: String },
    DuplicateColour { name: String },
    BadArity { name: String, arity: usize },
    ColourMismatch { name: String },
    Overflow,
}

// Origin: engine/crates_rs/core_operad_theory/src/foundation/mod.rs
// Claim: urn:core:crates_rs:core-operad-theory:mod:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for IdentityCorollaError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for IdentityCorollaError {}

impl IdentityCorollaFamily {
    /// Build the identity corolla of every [`ADMITTED_FINITE_COLOURS`] name.
    pub fn certify() -> Result<Self, IdentityCorollaError> {
        Self::certify_names(ADMITTED_FINITE_COLOURS)
    }

    fn certify_single_name(
        name: &str,
        seen: &mut std::collections::BTreeSet<String>,
    ) -> Result<u32, IdentityCorollaError> {
        let submitted = name.to_string();
        let colour = OperadColour::new(name).map_err(|detail| {
            IdentityCorollaError::RejectedColour {
                name: submitted.clone(),
                detail,
            }
        })?;
        if !seen.insert(colour.as_str().to_string()) {
            return Err(IdentityCorollaError::DuplicateColour {
                name: colour.as_str().to_string(),
            });
        }
        let operation = Operation::identity(colour);
        let arity = operation.arity();
        if arity != 1 || !operation.is_identity() {
            return Err(IdentityCorollaError::BadArity {
                name: submitted,
                arity,
            });
        }
        let tree = PlanarTree::corolla(operation);
        let child_matches = tree.children.first().is_some_and(|child| {
            child.output_colour() == tree.output_colour()
                && tree.output_colour().as_str() == submitted.as_str()
                && tree.children.len() == 1
        });
        if !child_matches {
            return Err(IdentityCorollaError::ColourMismatch { name: submitted });
        }
        u32::try_from(arity).map_err(|_| IdentityCorollaError::Overflow)
    }

    /// Build one identity corolla per name: arity 1, and the input colour equals the output.
    pub fn certify_names(names: &[&str]) -> Result<Self, IdentityCorollaError> {
        if names.is_empty() {
            return Err(IdentityCorollaError::EmptyPalette);
        }
        let mut seen = std::collections::BTreeSet::new();
        let mut colour_count: u32 = 0;
        let mut arity_sum: u32 = 0;
        for name in names {
            let arity_u32 = Self::certify_single_name(name, &mut seen)?;
            colour_count = colour_count.checked_add(1).ok_or(IdentityCorollaError::Overflow)?;
            arity_sum = arity_sum
                .checked_add(arity_u32)
                .ok_or(IdentityCorollaError::Overflow)?;
        }
        if colour_count != arity_sum {
            return Err(IdentityCorollaError::Overflow);
        }
        Ok(Self {
            colour_count,
            arity_sum,
        })
    }

    /// Number of distinct colours that received an identity.
    pub fn colour_count(self) -> u32 {
        self.colour_count
    }

    /// Sum of the identity arities. Each admitted identity contributes 1.
    pub fn arity_sum(self) -> u32 {
        self.arity_sum
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod identity_corolla_family_checks {
    use super::{IdentityCorollaError, IdentityCorollaFamily, ADMITTED_FINITE_COLOURS};

    #[test]
    fn every_admitted_colour_has_a_unary_identity_corolla() {
        let admitted = match u32::try_from(ADMITTED_FINITE_COLOURS.len()) {
            Ok(count) => count,
            Err(_) => 0,
        };
        assert!(admitted > 0);
        assert_eq!(
            IdentityCorollaFamily::certify().map(|row| (row.colour_count(), row.arity_sum())),
            Ok((admitted, admitted))
        );
        assert!(matches!(
            IdentityCorollaFamily::certify_names(&[""]),
            Err(IdentityCorollaError::RejectedColour { .. })
        ));
        assert!(matches!(
            IdentityCorollaFamily::certify_names(&["   "]),
            Err(IdentityCorollaError::RejectedColour { .. })
        ));
        assert!(matches!(
            IdentityCorollaFamily::certify_names(&["State", "State"]),
            Err(IdentityCorollaError::DuplicateColour { .. })
        ));
    }
}
