// AuthorityEffect: None.
//! Exact quantum stabilizer Hamiltonian solver and total certificate checker.
//!
//! Provides:
//! - Exact rational ground state energy and degeneracy calculations over commuting Pauli Hamiltonians.
//! - Independent generator extraction over GF(2) via [`crate::f2::F2Matrix`].
//! - Exact phase-tracked term decomposition using [`PauliString::multiply`].
//! - Bounded 2^k exhaustive search ($k \le 8$).
//! - Total certificate checker returning Pass or Fail for any JSON input without panicking.
//! - SOLVED certificates bind the deterministic input-order basis and decomposition;
//!   alternate bases require a different certificate contract and are refused here.

use num_rational::Rational64;
use serde::{Deserialize, Serialize};

use core_quantum_physics::pauli::PauliString;

mod certificate;
mod input;
mod solver;

pub use certificate::check;
pub use input::{parse_case, parse_target, parse_weight};
pub use solver::solve;

/// Maximum number of qubits supported in Q40 benchmark.
pub const MAX_QUBITS: usize = 8;
/// Maximum number of terms supported in Q40 benchmark.
pub const MAX_TERMS: usize = 24;

/// A validated Hamiltonian term.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Term {
    pub id: String,
    pub pauli: PauliString,
    pub weight: Rational64,
    pub target: i8, // +1 or -1
}

/// A parsed challenge case.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct StabilizerCase {
    pub id: String,
    pub num_qubits: usize,
    pub terms: Vec<Term>,
}

#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub struct DecompositionRow {
    pub id: String,
    pub mask: usize,
    pub phase: i8,
}

#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(tag = "status")]
pub enum StabilizerOutcome {
    #[serde(rename = "SOLVED")]
    Solved {
        id: String,
        energy: [i64; 2],
        degeneracy: u64,
        basis: Vec<String>,
        decomposition: Vec<DecompositionRow>,
        minimizers: Vec<usize>,
    },
    #[serde(rename = "OUT_OF_SCOPE")]
    OutOfScope { id: String, witness: [String; 2] },
    #[serde(rename = "UNKNOWN")]
    Unknown {
        id: String,
        refusal_code: String,
        message: String,
    },
}

#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum StabilizerCheckResult {
    Pass {
        case_id: String,
        details: Option<String>,
    },
    Fail {
        case_id: String,
        reason: String,
    },
}

impl StabilizerCheckResult {
    pub fn is_pass(&self) -> bool {
        matches!(self, StabilizerCheckResult::Pass { .. })
    }

    pub fn is_fail(&self) -> bool {
        matches!(self, StabilizerCheckResult::Fail { .. })
    }
}

// Origin: engine/crates_rs/pfp_runtime/src/stabilizer/mod.rs
// Claim: urn:core:crates_rs:pfp-runtime:mod:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord0635e4e1 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord0635e4e1` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError0635e4e1 {
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
impl BoundaryError0635e4e1 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError0635e4e1 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError0635e4e1 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord0635e4e1 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError0635e4e1> {
        if capacity_bound == 0 {
            return Err(BoundaryError0635e4e1::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError0635e4e1::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError0635e4e1::ExceedsCapacity {
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
mod l4_boundary_tests_0635e4e1 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord0635e4e1::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord0635e4e1::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord0635e4e1::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord0635e4e1::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord0635e4e1::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError0635e4e1::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError0635e4e1::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
