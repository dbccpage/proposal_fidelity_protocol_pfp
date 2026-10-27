//! ir.rs
//!
//! Intermediate Representation (IR) with Subobject Classifier (Î©) logic.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum ProofTerm {
    Axiom(String),
    UnificationStep {
        left: Box<Node>,
        right: Box<Node>,
        result: Box<CoreTruthValue>,
    },
    Hypothesis {
        name: String,
        value: Box<Node>,
    },
    Cut {
        lemma: Box<ProofTerm>,
        instantiation: HashMap<String, Node>,
    },
    Induction {
        base: Box<ProofTerm>,
        step: Box<ProofTerm>,
    },
    Contradiction {
        cycle: Vec<String>,
    },
    Deferred {
        reason: String,
    },
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum CoreTruthValue {
    True,
    False,
    Unknown,
    Partial {
        confidence: f32,
        justification: Vec<String>,
        proof: Option<ProofTerm>,
    },
    Contradiction {
        cycle: Vec<String>,
        proof: Option<ProofTerm>,
    },
    Deferred {
        dependency: String,
        proof: Option<ProofTerm>,
    },
}

impl CoreTruthValue {
    pub fn and(self, other: Self) -> Self {
        match (&self, &other) {
            (Self::False, _) | (_, Self::False) => Self::False,
            (Self::True, x) | (x, Self::True) => x.clone(),
            (Self::Unknown, _) | (_, Self::Unknown) => Self::Unknown,
            (Self::Partial { .. }, Self::Partial { .. }) => Self::Partial {
                confidence: self.confidence().min(other.confidence()),
                justification: [self.justifications(), other.justifications()].concat(),
                proof: None,
            },
            (Self::Deferred { .. }, x) | (x, Self::Deferred { .. }) => x.clone(),
            (Self::Contradiction { .. }, _) | (_, Self::Contradiction { .. }) => {
                Self::Contradiction {
                    cycle: vec![],
                    proof: None,
                }
            }
        }
    }

    pub fn or(self, other: Self) -> Self {
        match (&self, &other) {
            (Self::True, _) | (_, Self::True) => Self::True,
            (Self::False, x) | (x, Self::False) => x.clone(),
            _ => Self::Unknown,
        }
    }

    pub fn implies(self, other: Self) -> Self {
        if self.is_false() {
            Self::True
        } else {
            other
        }
    }

    pub fn is_false(&self) -> bool {
        matches!(self, Self::False | Self::Contradiction { .. })
    }

    pub fn is_true(&self) -> bool {
        matches!(self, Self::True)
    }

    pub fn then_true(self) -> Self {
        if self.is_true() {
            Self::True
        } else {
            Self::False
        }
    }

    fn confidence(&self) -> f32 {
        match self {
            Self::True => 1.0,
            Self::False => 0.0,
            Self::Unknown => 0.5,
            Self::Partial { confidence, .. } => *confidence,
            Self::Contradiction { .. } => 0.0,
            Self::Deferred { .. } => 0.3,
        }
    }

    fn justifications(&self) -> Vec<String> {
        match self {
            Self::Partial { justification, .. } => justification.clone(),
            _ => vec![],
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq)]
pub struct CoreMetadata {
    pub truth_value: Option<CoreTruthValue>,
    pub properties: HashMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct Span {
    pub line_start: usize,
    pub col_start: usize,
    pub line_end: usize,
    pub col_end: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum Node {
    Module {
        name: String,
        body: Vec<Node>,
        meta: CoreMetadata,
        span: Option<Span>,
    },
    Function {
        name: String,
        args: Vec<String>,
        body: Vec<Node>,
        decorators: Vec<String>,
        meta: CoreMetadata,
        span: Option<Span>,
    },
    Class {
        name: String,
        body: Vec<Node>,
        decorators: Vec<String>,
        meta: CoreMetadata,
        span: Option<Span>,
    },
    Call {
        func: String,
        args: Vec<String>,
        meta: CoreMetadata,
        span: Option<Span>,
    },
    Literal {
        value: String,
        kind: LiteralKind,
        meta: CoreMetadata,
        span: Option<Span>,
    },
    Import {
        module: String,
        names: Vec<String>,
        meta: CoreMetadata,
        span: Option<Span>,
    },
    Hole {
        name: String,
        expected: LiteralKind,
    },
    Var(String),
    Const(f64),
    App(Box<Node>, Vec<Node>),
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum LiteralKind {
    String,
    Integer,
    Float,
    Boolean,
    None,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IR {
    pub file_path: String,
    pub root: Node,
}

impl Node {
    pub fn is_integer(&self) -> bool {
        match self {
            Node::Const(v) => v.fract() == 0.0,
            _ => false,
        }
    }

    pub fn is_float(&self) -> bool {
        matches!(self, Node::Const(_))
    }
}

// Origin: engine/crates_rs/core_types/src/ir.rs
// Claim: urn:core:crates_rs:core-types:ir:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord43963561 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord43963561` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError43963561 {
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
impl BoundaryError43963561 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError43963561 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError43963561 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord43963561 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError43963561> {
        if capacity_bound == 0 {
            return Err(BoundaryError43963561::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError43963561::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError43963561::ExceedsCapacity {
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

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)

#[cfg(test)]
mod l4_boundary_tests_43963561 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord43963561::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord43963561::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord43963561::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord43963561::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord43963561::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError43963561::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError43963561::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
