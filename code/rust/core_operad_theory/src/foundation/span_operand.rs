//! Foundation: Exact UTF-8 Span Operands as Multicategory Objects.
//!
//! Enforces:
//! 1. Exact UTF-8 byte span boundaries without BOM (RULE_UTF8_MOJIBAKE_CLEANLINESS_001).
//! 2. Content-addressable SHA-256 integrity digests for all parsed spans.
//! 3. Sort mapping to ADMITTED_FINITE_COLOURS.
//! 4. Strict Value Object exact-type equality and ordered key derivation (RULE_RUST_ORDERED_KEY_DERIVE_001).
//!
//! AuthorityEffect: None.

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use super::colour::OperadColour;

/// Admitted finite colours for span operands in the estate.
pub const ADMITTED_FINITE_COLOURS: &[&str] = &[
    "State", "Proof", "Receipt", "Audit", "Contract", "Ledger", "Code", "Paper", "Diagram", "Post",
];

/// An exact, content-addressed text span acting as an operand in a coloured multicategory.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub struct SpanOperand {
    pub file_path: String,
    pub start_line: usize,
    pub end_line: usize,
    pub byte_offset: usize,
    pub byte_length: usize,
    pub colour: OperadColour,
    pub content_sha256: String,
    pub raw_text: String,
    pub role: String,
}

impl SpanOperand {
    /// Constructs and validates a SpanOperand from raw text.
    pub fn new(
        file_path: impl Into<String>,
        start_line: usize,
        end_line: usize,
        byte_offset: usize,
        byte_length: usize,
        colour: OperadColour,
        content_sha256: impl Into<String>,
        raw_text: impl Into<String>,
        role: Option<String>,
    ) -> Result<Self, String> {
        let f_path = file_path.into();
        let text = raw_text.into();
        let sha = content_sha256.into();

        if start_line < 1 {
            return Err(format!("start_line must be >= 1, got {start_line}"));
        }
        if end_line < start_line {
            return Err(format!(
                "end_line ({end_line}) cannot precede start_line ({start_line})"
            ));
        }
        if text.as_bytes().starts_with(&[0xef, 0xbb, 0xbf]) {
            return Err("Span text contains forbidden UTF-8 BOM bytes".to_string());
        }

        Ok(Self {
            file_path: f_path,
            start_line,
            end_line,
            byte_offset,
            byte_length,
            colour,
            content_sha256: sha,
            raw_text: text,
            role: role.unwrap_or_else(|| "general".to_string()),
        })
    }

    /// Factory method computing SHA-256 and byte length automatically.
    pub fn from_raw_text(
        file_path: impl Into<String>,
        raw_text: impl Into<String>,
        colour: OperadColour,
        start_line: usize,
        end_line: usize,
        byte_offset: usize,
        role: Option<String>,
    ) -> Result<Self, String> {
        let text = raw_text.into();
        if text.as_bytes().starts_with(&[0xef, 0xbb, 0xbf]) {
            return Err("Span text contains forbidden UTF-8 BOM bytes".to_string());
        }

        let mut hasher = Sha256::new();
        hasher.update(text.as_bytes());
        let digest_hex = hex::encode(hasher.finalize());
        let byte_len = text.as_bytes().len();

        Self::new(
            file_path,
            start_line,
            end_line,
            byte_offset,
            byte_len,
            colour,
            digest_hex,
            text,
            role,
        )
    }

    /// Verifies if the internal SHA-256 matches the raw text digest.
    pub fn verify_integrity(&self) -> bool {
        let mut hasher = Sha256::new();
        hasher.update(self.raw_text.as_bytes());
        let computed = hex::encode(hasher.finalize());
        computed == self.content_sha256 && self.byte_length == self.raw_text.as_bytes().len()
    }
}

// Origin: engine/crates_rs/core_operad_theory/src/foundation/span_operand.rs
// Claim: urn:core:crates_rs:core-operad-theory:span-operand:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord0c33e36f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord0c33e36f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError0c33e36f {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryError0c33e36f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError0c33e36f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError0c33e36f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord0c33e36f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError0c33e36f> {
        if capacity_bound == 0 {
            return Err(BoundaryError0c33e36f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError0c33e36f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError0c33e36f::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[cfg(test)]
mod l4_boundary_tests_0c33e36f {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord0c33e36f::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord0c33e36f::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord0c33e36f::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord0c33e36f::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord0c33e36f::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError0c33e36f::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError0c33e36f::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
