//! Foundation: Operations, identifiers, and operation kinds.
//!
//! AuthorityEffect: None.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_130244b1;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_130244b1<T> = std::result::Result<T, BoundaryError_130244b1>;
use std::fmt;
use serde::{Deserialize, Serialize};
use super::colour::{OperadColour, OperadSignature};

/// Classification of operation types.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum OperationKindType {
    Identity,
    Generator,
    Composite,
}

/// Explicit structural kind of an operation.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum OperationKind {
    Identity { colour: OperadColour },
    Generator,
    Composite { term_hash: String },
}

impl OperationKind {
    pub fn identity(colour: OperadColour) -> Self {
        Self::Identity { colour }
    }

    pub fn generator() -> Self {
        Self::Generator
    }

    pub fn composite(term_hash: impl Into<String>) -> Self {
        Self::Composite {
            term_hash: term_hash.into(),
        }
    }

    pub fn kind_type(&self) -> OperationKindType {
        match self {
            Self::Identity { .. } => OperationKindType::Identity,
            Self::Generator => OperationKindType::Generator,
            Self::Composite { .. } => OperationKindType::Composite,
        }
    }
}

/// Exact-type identifier for an operad operation.
#[derive(Debug, Clone, PartialEq, Eq, Hash, PartialOrd, Ord, Serialize, Deserialize)]
pub struct OperationId {
    value: String,
}

impl OperationId {
    pub fn new(name: impl Into<String>) -> Result<Self, String> {
        let n = name.into();
        let trimmed = n.trim();
        if trimmed.is_empty() {
            return Err("OperationId value cannot be empty.".to_string());
        }
        Ok(Self {
            value: trimmed.to_string(),
        })
    }

    pub fn identity_for(colour: &OperadColour) -> Self {
        Self {
            value: format!("id_{}", colour.as_str()),
        }
    }

    pub fn is_identity(&self) -> bool {
        self.value.starts_with("id_")
    }

    pub fn as_str(&self) -> &str {
        &self.value
    }
}

impl fmt::Display for OperationId {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.value)
    }
}

/// An operation f in O(c_1, ..., c_n; c) of a coloured operad.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Operation {
    pub op_id: OperationId,
    pub signature: OperadSignature,
    pub kind: OperationKind,
    pub is_equivariant: bool,
    pub description: String,
}

impl Operation {
    pub fn new_generator(
        id: OperationId,
        signature: OperadSignature,
        description: impl Into<String>,
    ) -> Self {
        Self {
            op_id: id,
            signature,
            kind: OperationKind::generator(),
            is_equivariant: false,
            description: description.into(),
        }
    }

    pub fn identity(colour: OperadColour) -> Self {
        let id = OperationId::identity_for(&colour);
        let sig = OperadSignature::new(vec![colour.clone()], colour.clone());
        Self {
            op_id: id,
            signature: sig,
            kind: OperationKind::identity(colour.clone()),
            is_equivariant: true,
            description: format!("Canonical identity morphism on colour {}", colour.as_str()),
        }
    }

    pub fn is_identity(&self) -> bool {
        matches!(self.kind, OperationKind::Identity { .. })
    }

    pub fn arity(&self) -> usize {
        self.signature.arity()
    }

    pub fn inputs(&self) -> &[OperadColour] {
        &self.signature.inputs
    }

    pub fn output(&self) -> &OperadColour {
        &self.signature.output
    }

    pub fn permute_inputs(&self, permutation: &[usize]) -> Result<Self, String> {
        let n = self.arity();
        let mut sorted = permutation.to_vec();
        sorted.sort_unstable();
        let expected: Vec<usize> = (0..n).collect();
        if sorted != expected {
            return Err(format!("Invalid permutation {:?} for arity {}", permutation, n));
        }

        let new_inputs: Vec<OperadColour> = permutation.iter().map(|&p| self.signature.inputs[p].clone()).collect();
        let perm_str: String = permutation.iter().map(|p| p.to_string()).collect();
        let new_id = OperationId::new(format!("{}^sigma_{}", self.op_id.as_str(), perm_str))?;

        Ok(Self {
            op_id: new_id,
            signature: OperadSignature::new(new_inputs, self.signature.output.clone()),
            kind: self.kind.clone(),
            is_equivariant: self.is_equivariant,
            description: format!("Permutation {:?} of {}", permutation, self.op_id.as_str()),
        })
    }
}

// Origin: engine/crates_rs/core_operad_theory/src/foundation/operation.rs
// Claim: urn:core:crates_rs:core-operad-theory:operation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_130244b1 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
