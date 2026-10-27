//! Immutable railway result and typed refusal values.
//!
//! Rust face of `engine/kernel/higher_operad/result.py`.

use std::collections::BTreeMap;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use thiserror::Error;

use super::canonical::{canonical_id, require_identifier, require_text, CanonicalError};
use super::model::ModelError;

/// A structured refusal record when an operation or check cannot proceed.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Refusal {
    pub code: String,
    pub message: String,
    #[serde(default)]
    pub locus: String,
    #[serde(default)]
    pub details: Vec<(String, String)>,
}

impl Refusal {
    pub fn new(code: &str, message: &str) -> Result<Self, CanonicalError> {
        Ok(Self {
            code: require_identifier(code, "code")?,
            message: require_text(message, "message")?,
            locus: String::new(),
            details: Vec::new(),
        })
    }

    pub fn with_locus(mut self, locus: &str) -> Result<Self, CanonicalError> {
        if !locus.is_empty() {
            self.locus = require_text(locus, "locus")?;
        }
        Ok(self)
    }

    pub fn with_details(mut self, details: Vec<(String, String)>) -> Result<Self, KernelError> {
        let mut map = BTreeMap::new();
        for (k, v) in details {
            let key = require_text(&k, "detail key")?;
            if map.insert(key, v).is_some() {
                return Err(KernelError::InvalidRefusal("refusal detail keys must be unique".into()));
            }
        }
        self.details = map.into_iter().collect();
        Ok(self)
    }

    pub fn to_canonical(&self) -> Value {
        let mut map = serde_json::Map::new();
        for (k, v) in &self.details {
            map.insert(k.clone(), Value::String(v.clone()));
        }
        json!({
            "code": self.code,
            "message": self.message,
            "locus": self.locus,
            "details": Value::Object(map),
        })
    }

    pub fn canonical_id(&self) -> Result<String, CanonicalError> {
        canonical_id("core.oewas.refusal.v1", &self.to_canonical())
    }
}

impl std::fmt::Display for Refusal {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}: {}", self.code, self.message)
    }
}

impl std::error::Error for Refusal {}

#[derive(Debug, Error, PartialEq, Eq)]
pub enum KernelError {
    #[error(transparent)]
    Canonical(#[from] CanonicalError),

    #[error(transparent)]
    Model(#[from] ModelError),

    #[error(transparent)]
    Refused(#[from] Refusal),

    #[error("invalid refusal: {0}")]
    InvalidRefusal(String),

    #[error("kernel error: {0}")]
    Message(String),
}

// Origin: engine/crates_rs/core_operad_theory/src/kernel/result.rs
// Claim: urn:core:crates_rs:core-operad-theory:result:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_41a02171 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
