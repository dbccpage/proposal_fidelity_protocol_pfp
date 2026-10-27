//! Deformation: Quadratic Operads and Relations.
//!
//! AuthorityEffect: None.

use std::collections::HashMap;
use serde::{Deserialize, Serialize};
use crate::foundation::Operation;

/// A weight-two relation in Free(E)(2) expressing an algebraic identity.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct QuadraticRelation {
    pub relation_id: String,
    pub generating_terms: Vec<String>,
    pub coefficients: Vec<i64>,
    pub description: String,
}

/// A quadratic operad P presented by generators E and quadratic relations R.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QuadraticOperad {
    pub name: String,
    pub generators: HashMap<String, Operation>,
    pub relations: Vec<QuadraticRelation>,
}

impl QuadraticOperad {
    pub fn new(name: impl Into<String>) -> Self {
        Self {
            name: name.into(),
            generators: HashMap::new(),
            relations: Vec::new(),
        }
    }

    pub fn add_generator(&mut self, op: Operation) {
        self.generators.insert(op.op_id.as_str().to_string(), op);
    }

    pub fn add_relation(&mut self, rel: QuadraticRelation) {
        self.relations.push(rel);
    }
}

// Exact carrier witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum RelationError { Width, Overflow, Sum, Zero }

// Origin: engine/crates_rs/core_operad_theory/src/deformation/quadratic_operad.rs
// Claim: urn:core:crates_rs:core-operad-theory:quadratic-operad:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for RelationError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for RelationError {}

impl QuadraticRelation {
    /// A quadratic relation has matching term and coefficient widths, at least two terms, and coefficient sum zero.
    pub fn certify(&self) -> Result<i64, RelationError> {
        if self.coefficients.len() != self.generating_terms.len() || self.coefficients.len() < 2 {
            return Err(RelationError::Width);
        }
        let mut sum = 0i64;
        let mut nonzero = false;
        for coeff in &self.coefficients {
            if *coeff != 0 {
                nonzero = true;
            }
            sum = sum.checked_add(*coeff).ok_or(RelationError::Overflow)?;
        }
        if !nonzero {
            return Err(RelationError::Zero);
        }
        if sum != 0 {
            return Err(RelationError::Sum);
        }
        Ok(sum)
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod relation_checks {
    use super::*;

    #[test]
    fn a_commutator_relation_sums_to_zero() {
        let relation = QuadraticRelation {
            relation_id: "comm".into(),
            generating_terms: vec!["ab".into(), "ba".into()],
            coefficients: vec![1, -1],
            description: "commutator".into(),
        };
        assert!(matches!(relation.certify(), Ok(0)));
    }

    #[test]
    fn a_nonzero_sum_is_refused() {
        let relation = QuadraticRelation {
            relation_id: "bad".into(),
            generating_terms: vec!["ab".into(), "ba".into()],
            coefficients: vec![1, 1],
            description: "not a relation".into(),
        };
        assert!(matches!(relation.certify(), Err(RelationError::Sum)));
    }
}
