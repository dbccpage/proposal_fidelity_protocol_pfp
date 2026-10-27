//! Trace-artifact vocabulary — the shared abstraction for execution traces.
//!
//! These traits are **law**: abstract contracts about what a trace *is*, not
//! verification machinery that produces or replays one. They live in the
//! foundation crate `core_types` so that the governance layer
//! (`core_contracts`) and the verification layer (`core_replay`) can both
//! depend on the vocabulary **without the law depending on the runtime process
//! it constrains**.
//!
//! This relocation discharges **SG-LAYER-001 / PO-LAYER**: before it,
//! `core_contracts` imported `core_replay::trace::{TraceArtifact, VoidTrace}`,
//! inverting the layer order (law → machinery). The `TraceArtifact` family is a
//! serialization-marker abstraction shared by both layers; its honest home is
//! the foundation, below both. Concrete trace *containers* (`StepTrace`,
//! `LayeredTrace`) remain in `core_replay` and implement these traits.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_f70c77af;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_f70c77af<T> = std::result::Result<T, BoundaryError_f70c77af>;
use serde::{Deserialize, Serialize};

/// A trace artifact: clonable, serializable evidence of execution.
///
/// `IMMUTABLE_AFTER_EMIT` declares the law that a trace, once emitted, is not
/// rewritten — the basis on which replay can treat it as a fixed witness.
pub trait TraceArtifact: Clone + Serialize + for<'de> Deserialize<'de> {
    /// A trace is immutable once emitted (the default; replay relies on it).
    const IMMUTABLE_AFTER_EMIT: bool = true;
}

/// Marker: a [`TraceArtifact`] that is additionally guaranteed immutable.
pub trait ImmutableTrace: TraceArtifact {}

/// Marker: an analysis-stage artifact.
pub trait AnalysisArtifact {}
/// Marker: a validation-stage artifact.
pub trait ValidationArtifact {}
/// Marker: a decision-stage artifact.
pub trait DecisionArtifact {}
/// Marker: an action-result-stage artifact.
pub trait ActionResultArtifact {}

/// Sentinel trace for engine/pipeline stages that produce no trace output.
///
/// Used as the default `type Trace` in the contract enforcement macros, which
/// is why the sentinel — like the trait it implements — must live below the
/// governance layer rather than in the replay crate.
#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct VoidTrace;

impl TraceArtifact for VoidTrace {}
impl ImmutableTrace for VoidTrace {}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn void_trace_round_trips() {
        let trace = VoidTrace;
        let json = serde_json::to_string(&trace).expect("VoidTrace serializes");
        let _: VoidTrace = serde_json::from_str(&json).expect("VoidTrace deserializes");
    }

    #[test]
    fn void_trace_is_an_immutable_trace_artifact() {
        // Compile-time witness that VoidTrace satisfies the foundation-level
        // trace vocabulary that core_contracts depends on.
        fn assert_immutable<T: ImmutableTrace>() {}
        assert_immutable::<VoidTrace>();
        const { assert!(VoidTrace::IMMUTABLE_AFTER_EMIT) };
    }
}

// Exact invariant envelope.
// Origin: engine/crates_rs/core_types/src/trace_artifact.rs
// Claim: urn:core:types:trace-replay-admission:v1
// AuthorityEffect: None

const STAGE_ANALYSIS: u8 = 1;
const STAGE_VALIDATION: u8 = 2;
const STAGE_DECISION: u8 = 4;
const STAGE_ACTION: u8 = 8;
const STAGE_MASK: u8 = STAGE_ANALYSIS | STAGE_VALIDATION | STAGE_DECISION | STAGE_ACTION;

struct ReplayAdmission {
    stages: u8,
    count: u8,
}

#[derive(Debug, Clone, PartialEq, Eq)]
enum ReplayAdmitError {
    Mutable,
    Undeclared { stages: u8 },
    Count { stages: u8, claimed: u8, actual: u8 },
}

// Origin: engine/crates_rs/core_types/src/trace_artifact.rs
// Claim: urn:core:crates_rs:core-types:trace-artifact:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ReplayAdmitError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ReplayAdmitError {}

fn try_replay_admission<T: TraceArtifact>(
    stages: u8,
    claimed_count: u8,
) -> Result<ReplayAdmission, ReplayAdmitError> {
    if !T::IMMUTABLE_AFTER_EMIT {
        return Err(ReplayAdmitError::Mutable);
    }
    if stages & !STAGE_MASK != 0 {
        return Err(ReplayAdmitError::Undeclared { stages });
    }
    let actual = u8::try_from(stages.count_ones()).map_err(|_| ReplayAdmitError::Count {
        stages,
        claimed: claimed_count,
        actual: 0,
    })?;
    if actual != claimed_count {
        return Err(ReplayAdmitError::Count {
            stages,
            claimed: claimed_count,
            actual,
        });
    }
    Ok(ReplayAdmission {
        stages,
        count: actual,
    })
}

impl VoidTrace {
    pub fn admits_replay(stages: u8, claimed_count: u8) -> bool {
        match try_replay_admission::<VoidTrace>(stages, claimed_count) {
            Ok(admission) => admission.stages == stages && admission.count == claimed_count,
            Err(_) => false,
        }
    }
}

#[cfg(test)]
mod replay_admission_tests {
    use super::{
        try_replay_admission, ReplayAdmission, ReplayAdmitError, TraceArtifact, VoidTrace,
        STAGE_ANALYSIS, STAGE_DECISION,
    };
    use serde::{Deserialize, Serialize};

    #[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
    struct MutableTrace;

    impl TraceArtifact for MutableTrace {
        const IMMUTABLE_AFTER_EMIT: bool = false;
    }

    #[test]
    fn void_trace_admits_an_empty_stage_mask() {
        let admission = try_replay_admission::<VoidTrace>(0, 0);
        assert!(matches!(
            admission,
            Ok(ReplayAdmission { stages: 0, count: 0 })
        ));
        assert!(VoidTrace::admits_replay(0, 0));
        assert!(!VoidTrace::admits_replay(0b10000, 1));
    }

    #[test]
    fn analysis_and_decision_count_two_declared_stages() {
        let stages = STAGE_ANALYSIS | STAGE_DECISION;
        let admission = try_replay_admission::<VoidTrace>(stages, 2);
        assert!(matches!(
            admission,
            Ok(ReplayAdmission { stages: 5, count: 2 })
        ));
        assert!(matches!(
            try_replay_admission::<VoidTrace>(stages, 1),
            Err(ReplayAdmitError::Count {
                claimed: 1,
                actual: 2,
                ..
            })
        ));
    }

    #[test]
    fn a_mutable_trace_or_an_undeclared_bit_is_refused() {
        assert!(matches!(
            try_replay_admission::<MutableTrace>(STAGE_ANALYSIS, 1),
            Err(ReplayAdmitError::Mutable)
        ));
        assert!(matches!(
            try_replay_admission::<VoidTrace>(0b10000, 1),
            Err(ReplayAdmitError::Undeclared { stages: 16 })
        ));
    }
}
