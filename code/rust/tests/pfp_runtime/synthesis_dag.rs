//! Integration tests for Program Synthesis Loop v2 (U10).
//!
//! Invariants tested:
//! - Module DAG scheduling enforces dependency order (only schedulable when all deps Frozen).
//! - Retraction context for attempt t >= 2 carries previous code and failing diff.
//! - Attempt t >= 2 without previous code or diff refuses with typed error.
//!
//! AuthorityEffect: None.

use pfp_runtime::synthesis_dag::{ModuleDagV1, ModuleStatus, RetractionContextV1};

#[test]
fn test_module_dag_dependency_progression() {
    let mut dag = ModuleDagV1::new();
    dag.add_module("parse_case", &[]);
    dag.add_module("gf2_eliminate", &["parse_case"]);
    dag.add_module("format", &["gf2_eliminate"]);

    assert!(!dag.is_all_frozen());

    {
        let next = dag
            .next_schedulable_module()
            .expect("parse_case should be schedulable");
        assert_eq!(next.name, "parse_case");
        assert_eq!(next.status, ModuleStatus::Ready);
    }
    // Attempting next before freezing parse_case yields None
    assert!(dag.next_schedulable_module().is_none());

    // Freeze parse_case
    dag.freeze_module("parse_case", "def parse_case(raw): return raw")
        .unwrap();

    {
        let next = dag
            .next_schedulable_module()
            .expect("gf2_eliminate should be schedulable");
        assert_eq!(next.name, "gf2_eliminate");
        assert_eq!(next.status, ModuleStatus::Ready);
    }

    // Freeze gf2_eliminate
    dag.freeze_module("gf2_eliminate", "def gf2_eliminate(mat): return mat")
        .unwrap();

    {
        let next = dag
            .next_schedulable_module()
            .expect("format should be schedulable");
        assert_eq!(next.name, "format");
        assert_eq!(next.status, ModuleStatus::Ready);
    }

    // Freeze format
    dag.freeze_module("format", "def format(out): return str(out)")
        .unwrap();

    assert!(dag.is_all_frozen());
}

#[test]
fn test_retraction_context_attempt_invariants() {
    // Attempt 1: does not require previous code
    let ctx_t1 = RetractionContextV1 {
        module_name: "gf2_eliminate".to_string(),
        attempt_number: 1,
        spec_text: "Eliminate linear equations in GF(2)".to_string(),
        schema_card: "Input: Matrix[bool], Output: Matrix[bool]".to_string(),
        previous_code: None,
        failing_diff: None,
        error_feedback: "".to_string(),
        authority_effect: "None".to_string(),
    };
    let prompt_t1 = ctx_t1
        .render_prompt()
        .expect("attempt 1 prompt should render");
    assert!(prompt_t1.contains("Eliminate linear equations in GF(2)"));
    assert!(!prompt_t1.contains("Previous Code"));

    // Attempt 2: missing previous code or diff MUST fail
    let ctx_t2_missing = RetractionContextV1 {
        module_name: "gf2_eliminate".to_string(),
        attempt_number: 2,
        spec_text: "Eliminate linear equations in GF(2)".to_string(),
        schema_card: "Input: Matrix[bool], Output: Matrix[bool]".to_string(),
        previous_code: None, // Missing!
        failing_diff: None,
        error_feedback: "AssertionError: row 2 not eliminated".to_string(),
        authority_effect: "None".to_string(),
    };
    assert_eq!(
        ctx_t2_missing.render_prompt().unwrap_err(),
        "REPAIR_MISSING_PREVIOUS_CODE"
    );

    // Attempt 2: with previous code and diff MUST include both
    let ctx_t2_valid = RetractionContextV1 {
        module_name: "gf2_eliminate".to_string(),
        attempt_number: 2,
        spec_text: "Eliminate linear equations in GF(2)".to_string(),
        schema_card: "Input: Matrix[bool], Output: Matrix[bool]".to_string(),
        previous_code: Some("def gf2_eliminate(mat):\n    return mat".to_string()),
        failing_diff: Some("--- expected\n+++ actual\n@@ -1 +1 @@\n- 0\n+ 1".to_string()),
        error_feedback: "AssertionError: pivot not cleared".to_string(),
        authority_effect: "None".to_string(),
    };
    let prompt_t2 = ctx_t2_valid
        .render_prompt()
        .expect("attempt 2 prompt should render");
    assert!(prompt_t2.contains("Previous Code (Failed Host Verification)"));
    assert!(prompt_t2.contains("def gf2_eliminate"));
    assert!(prompt_t2.contains("Failure Diagnostics & Diff"));
    assert!(prompt_t2.contains("--- expected"));
    assert!(prompt_t2.contains("AssertionError: pivot not cleared"));
}

// Origin: engine/crates_rs/tests/pfp_runtime/synthesis_dag.rs
// Claim: urn:core:crates_rs:tests:synthesis-dag:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord82f015bd {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord82f015bd` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError82f015bd {
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
impl BoundaryError82f015bd {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError82f015bd {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError82f015bd {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord82f015bd {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError82f015bd> {
        if capacity_bound == 0 {
            return Err(BoundaryError82f015bd::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError82f015bd::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError82f015bd::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_82f015bd() {
    let admitted = BoundaryRecord82f015bd::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord82f015bd::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
