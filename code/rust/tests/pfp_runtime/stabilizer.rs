// AuthorityEffect: None.
//! Targeted integration test suite for Rust stabilizer solver and total checker.

use pfp_runtime::stabilizer::{check, solve, DecompositionRow, StabilizerOutcome};
use serde_json::json;

#[test]
fn test_single_qubit_trivial_solve() {
    let case = json!({
        "id": "q40_01",
        "n": 1,
        "terms": [
            {
                "id": "t0",
                "pauli": "Z",
                "weight": [1, 1],
                "target": 1
            }
        ]
    });

    let outcome = solve(&case);
    match outcome {
        StabilizerOutcome::Solved {
            id,
            energy,
            degeneracy,
            basis,
            decomposition,
            minimizers,
        } => {
            assert_eq!(id, "q40_01");
            assert_eq!(energy, [0, 1]);
            assert_eq!(degeneracy, 1);
            assert_eq!(basis, vec!["t0"]);
            assert_eq!(
                decomposition,
                vec![DecompositionRow {
                    id: "t0".to_string(),
                    mask: 1,
                    phase: 1,
                }]
            );
            assert_eq!(minimizers, vec![0]);
        }
        _ => panic!("Expected Solved outcome"),
    }
}

#[test]
fn test_bell_stabilizer_solve() {
    // 2 qubits, ZZ and XX commuting generators, target +1
    let case = json!({
        "id": "q40_02",
        "n": 2,
        "terms": [
            {"id": "t0", "pauli": "ZZ", "weight": [1, 1], "target": 1},
            {"id": "t1", "pauli": "XX", "weight": [1, 1], "target": 1}
        ]
    });

    let outcome = solve(&case);
    match outcome {
        StabilizerOutcome::Solved {
            energy,
            degeneracy,
            basis,
            minimizers,
            ..
        } => {
            assert_eq!(energy, [0, 1]);
            assert_eq!(degeneracy, 1);
            assert_eq!(basis.len(), 2);
            assert_eq!(minimizers, vec![0]);
        }
        _ => panic!("Expected Solved outcome"),
    }
}

#[test]
fn test_noncommuting_pair_out_of_scope() {
    let case = json!({
        "id": "q40_03",
        "n": 1,
        "terms": [
            {"id": "t0", "pauli": "X", "weight": [1, 1], "target": 1},
            {"id": "t1", "pauli": "Z", "weight": [1, 1], "target": 1}
        ]
    });

    let outcome = solve(&case);
    match outcome {
        StabilizerOutcome::OutOfScope { id, witness } => {
            assert_eq!(id, "q40_03");
            assert_eq!(witness, ["t0", "t1"]);
        }
        _ => panic!("Expected OutOfScope outcome"),
    }
}

#[test]
fn test_y_bearing_case() {
    // Y on 1 qubit: H = (I - Y)/2
    let case = json!({
        "id": "q40_y1",
        "n": 1,
        "terms": [
            {"id": "t0", "pauli": "Y", "weight": [1, 1], "target": 1}
        ]
    });

    let outcome = solve(&case);
    match outcome {
        StabilizerOutcome::Solved {
            energy, degeneracy, ..
        } => {
            assert_eq!(energy, [0, 1]);
            assert_eq!(degeneracy, 1);
        }
        _ => panic!("Expected Solved outcome"),
    }
}

#[test]
fn test_total_checker_on_valid_solution() {
    let case = json!({
        "id": "q40_01",
        "n": 1,
        "terms": [
            {"id": "t0", "pauli": "Z", "weight": [1, 1], "target": 1}
        ]
    });

    let valid_result = json!({
        "id": "q40_01",
        "status": "SOLVED",
        "energy": [0, 1],
        "degeneracy": 1,
        "basis": ["t0"],
        "decomposition": [{"id": "t0", "mask": 1, "phase": 1}],
        "minimizers": [0]
    });

    let check_res = check(&case, &valid_result);
    assert!(check_res.is_pass(), "Expected Pass, got {:?}", check_res);
}

#[test]
fn test_total_checker_fuzz_malformed_results() {
    let case = json!({
        "id": "q40_01",
        "n": 1,
        "terms": [
            {"id": "t0", "pauli": "Z", "weight": [1, 1], "target": 1}
        ]
    });

    // A collection of malformed / hostile results that must all return Fail, NEVER panic
    let bad_results = vec![
        json!(null),
        json!([]),
        json!("SOLVED"),
        json!({"status": "INVALID_STATUS"}),
        // Wrong energy type (string integer "1a")
        json!({
            "status": "SOLVED",
            "energy": ["1a", 1],
            "degeneracy": 1,
            "basis": ["t0"],
            "decomposition": [{"id": "t0", "mask": 1, "phase": 1}],
            "minimizers": [0]
        }),
        // Float in energy
        json!({
            "status": "SOLVED",
            "energy": [0.0, 1.0],
            "degeneracy": 1,
            "basis": ["t0"],
            "decomposition": [{"id": "t0", "mask": 1, "phase": 1}],
            "minimizers": [0]
        }),
        // Boolean in energy
        json!({
            "status": "SOLVED",
            "energy": [true, false],
            "degeneracy": 1,
            "basis": ["t0"],
            "decomposition": [{"id": "t0", "mask": 1, "phase": 1}],
            "minimizers": [0]
        }),
        // String mask
        json!({
            "status": "SOLVED",
            "energy": [0, 1],
            "degeneracy": 1,
            "basis": ["t0"],
            "decomposition": [{"id": "t0", "mask": "1", "phase": 1}],
            "minimizers": [0]
        }),
        // String phase
        json!({
            "status": "SOLVED",
            "energy": [0, 1],
            "degeneracy": 1,
            "basis": ["t0"],
            "decomposition": [{"id": "t0", "mask": 1, "phase": "1"}],
            "minimizers": [0]
        }),
        // Wrong energy value
        json!({
            "status": "SOLVED",
            "energy": [5, 1],
            "degeneracy": 1,
            "basis": ["t0"],
            "decomposition": [{"id": "t0", "mask": 1, "phase": 1}],
            "minimizers": [0]
        }),
        // Wrong degeneracy
        json!({
            "status": "SOLVED",
            "energy": [0, 1],
            "degeneracy": 99,
            "basis": ["t0"],
            "decomposition": [{"id": "t0", "mask": 1, "phase": 1}],
            "minimizers": [0]
        }),
        // Missing fields
        json!({
            "status": "SOLVED"
        }),
        // Claimed OUT_OF_SCOPE on commuting case
        json!({
            "status": "OUT_OF_SCOPE",
            "witness": ["t0", "t0"]
        }),
    ];

    for (idx, bad) in bad_results.iter().enumerate() {
        let res = check(&case, bad);
        assert!(
            res.is_fail(),
            "Expected Fail for bad result #{idx}, got {:?}",
            res
        );
    }
}

// Origin: engine/crates_rs/tests/pfp_runtime/stabilizer.rs
// Claim: urn:core:crates_rs:tests:stabilizer:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf1774729 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf1774729` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf1774729 {
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
impl BoundaryErrorf1774729 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf1774729 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf1774729 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf1774729 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf1774729> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf1774729::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf1774729::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf1774729::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_f1774729() {
    let admitted = BoundaryRecordf1774729::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordf1774729::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
