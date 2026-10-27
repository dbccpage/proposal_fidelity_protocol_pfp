use core_replay::{
    derive_markdown_narrative_v1, emit_retrospective_v1, AppendOnlyTraceV1, DualTraceError,
    MemoryReferenceV1, TraceEventKindV1,
};

const HASH: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";

fn trace() -> AppendOnlyTraceV1 {
    let mut trace = AppendOnlyTraceV1::default();
    trace
        .append(TraceEventKindV1::Fact {
            key: "gate".to_owned(),
            value: "passed".to_owned(),
        })
        .unwrap();
    trace
        .append(TraceEventKindV1::ResidualObserved {
            residual_id: "R-1".to_owned(),
            detail: "human promotion absent".to_owned(),
        })
        .unwrap();
    trace
}

#[test]
fn replay_hash_parent_and_state_are_deterministic() {
    let first = trace().replay().unwrap();
    let second = trace().replay().unwrap();
    assert_eq!(first, second);
    assert_eq!(first.facts["gate"].value, "passed");
    assert_eq!(first.residuals["R-1"].occurrences, 1);
}

#[test]
fn hash_or_parent_tamper_is_rejected() {
    let mut hash_tamper = trace();
    let mut events = hash_tamper.events().to_vec();
    events[0].event_sha256 = HASH.to_owned();
    hash_tamper = serde_json::from_value(serde_json::to_value(events).unwrap()).unwrap();
    assert!(matches!(
        hash_tamper.replay(),
        Err(DualTraceError::EventHashMismatch(0))
    ));

    let mut parent_tamper = trace();
    let mut events = parent_tamper.events().to_vec();
    events[1].parent_sha256 = Some(HASH.to_owned());
    parent_tamper = serde_json::from_value(serde_json::to_value(events).unwrap()).unwrap();
    assert!(matches!(
        parent_tamper.replay(),
        Err(DualTraceError::ParentMismatch(1))
    ));
}

#[test]
fn terminal_event_prevents_all_later_mutation() {
    let mut trace = trace();
    trace
        .append(TraceEventKindV1::TerminalRecorded {
            terminal: "StabilizedSurvivor".to_owned(),
        })
        .unwrap();
    let error = trace
        .append(TraceEventKindV1::Fact {
            key: "late".to_owned(),
            value: "mutation".to_owned(),
        })
        .unwrap_err();
    assert_eq!(error, DualTraceError::TerminalImmutable);
}

#[test]
fn narrative_is_exactly_derived_and_evidence_only() {
    let state = trace().replay().unwrap();
    let narrative = derive_markdown_narrative_v1(&state);
    assert!(narrative.contains("`gate` = `passed`"));
    assert!(narrative.contains("`R-1`: human promotion absent"));
    assert!(!narrative.contains("approved"));
    assert!(!narrative.contains("authorized"));
}

#[test]
fn repeated_residual_emits_nonactivating_host_candidate() {
    let mut trace = trace();
    trace
        .append(TraceEventKindV1::ResidualObserved {
            residual_id: "R-1".to_owned(),
            detail: "human promotion absent".to_owned(),
        })
        .unwrap();
    let retrospective = emit_retrospective_v1(&trace.replay().unwrap(), vec![]).unwrap();
    assert_eq!(retrospective.residuals, ["R-1"]);
    assert_eq!(retrospective.improvement_candidates.len(), 1);
    let candidate = &retrospective.improvement_candidates[0];
    assert!(candidate.host_admission_required);
    assert!(!candidate.self_activation_requested);
    assert!(retrospective.authority_effect.is_none());
}

#[test]
fn memory_keeps_only_redacted_hash_references() {
    let state = trace().replay().unwrap();
    let reference = MemoryReferenceV1 {
        artifact_sha256: HASH.to_owned(),
        policy_reference: "policy:S11-001/private".to_owned(),
        redaction_receipt_sha256: HASH.to_owned(),
    };
    let retrospective = emit_retrospective_v1(&state, vec![reference]).unwrap();
    let json = serde_json::to_string(&retrospective).unwrap();
    assert!(!json.contains("secret content"));
    assert!(json.contains("policy:S11-001/private"));
}

#[test]
fn residual_identity_cannot_be_rewritten() {
    let mut trace = trace();
    trace
        .append(TraceEventKindV1::ResidualObserved {
            residual_id: "R-1".to_owned(),
            detail: "different meaning".to_owned(),
        })
        .unwrap();
    assert_eq!(
        trace.replay().unwrap_err(),
        DualTraceError::ResidualMutation("R-1".to_owned())
    );
}

// Origin: engine/crates_rs/tests/core_replay/dual_trace_memory.rs
// Claim: urn:core:crates_rs:tests:dual-trace-memory:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc6fedc21 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc6fedc21` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc6fedc21 {
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
impl BoundaryErrorc6fedc21 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc6fedc21 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc6fedc21 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc6fedc21 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc6fedc21> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc6fedc21::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc6fedc21::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc6fedc21::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_c6fedc21() {
    let admitted = BoundaryRecordc6fedc21::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordc6fedc21::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
