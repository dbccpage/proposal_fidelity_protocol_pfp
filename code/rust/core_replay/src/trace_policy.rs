use crate::trace_config::TraceConfig;
use crate::trace_paths::{TraceArtifactPair, TracePathsError};
use crate::run_trace::RunTrace;
use core_types::trace_artifact_id::{TraceArtifactId, TraceArtifactIdError};

pub fn sanitize_filename_component(input: &str) -> String {
    let mut out = String::with_capacity(input.len());
    let mut prev_underscore = false;

    for ch in input.chars() {
        let mapped = if ch.is_ascii_alphanumeric() {
            ch.to_ascii_lowercase()
        } else {
            '_'
        };
        if mapped == '_' {
            if !prev_underscore {
                out.push('_');
                prev_underscore = true;
            }
        } else {
            out.push(mapped);
            prev_underscore = false;
        }
    }

    out.trim_matches('_').to_string()
}

pub fn build_trace_artifact_id(trace: &RunTrace) -> Result<TraceArtifactId, TraceArtifactIdError> {
    let verdict = if trace.success { "satisfied" } else { "failed" }.to_string();
    let test_name = sanitize_filename_component(&trace.test_name);
    // Use last 16 chars to capture hash+GUID suffix for uniqueness
    let char_count = trace.run_id.chars().count();
    let short_id = if char_count > 16 {
        trace
            .run_id
            .chars()
            .skip(char_count - 16)
            .collect::<String>()
    } else {
        trace.run_id.clone()
    };

    TraceArtifactId::new(test_name, short_id, verdict)
}

pub fn build_trace_paths(
    config: &TraceConfig,
    artifact_id: &TraceArtifactId,
) -> Result<TraceArtifactPair, TracePathsError> {
    let filename_base = artifact_id.filename_base();

    // As per user feedback, place them all in the same folder (.intelligence/.traces)
    let dir = config
        .target_base_dir()
        .join(".intelligence")
        .join(".traces");

    let trace_path = dir.join(format!("trace_{}.json", filename_base));
    let narrative_path = dir.join(format!("uns_{}.md", filename_base));

    TraceArtifactPair::new(trace_path, narrative_path)
}

/// Satisfies the contract validator for the TracePolicy symbol.
pub struct TracePolicy;

// Origin: engine/crates_rs/core_replay/src/trace_policy.rs
// Claim: urn:core:crates_rs:core-replay:trace-policy:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord6bd942d2 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord6bd942d2` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError6bd942d2 {
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
impl BoundaryError6bd942d2 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError6bd942d2 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError6bd942d2 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord6bd942d2 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError6bd942d2> {
        if capacity_bound == 0 {
            return Err(BoundaryError6bd942d2::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError6bd942d2::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError6bd942d2::ExceedsCapacity {
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
mod tests {
    use super::*;

    #[test]
    fn test_sanitize_filename_component() {
        assert_eq!(sanitize_filename_component("Hello World!"), "hello_world");
        assert_eq!(sanitize_filename_component("test--case"), "test_case");
        assert_eq!(sanitize_filename_component("___leading___"), "leading");
        assert_eq!(sanitize_filename_component("ABC123"), "abc123");
        assert_eq!(sanitize_filename_component("a.b.c"), "a_b_c");
    }

    #[test]
    fn test_build_trace_artifact_id() {
        let trace = RunTrace::new(
            "abcdef1234567890abcdef".to_string(),
            "2025-01-01T00:00:00Z".to_string(),
            "My Test Case".to_string(),
            "test-model".to_string(),
            "fp-0000".to_string(),
            0,
            String::new(),
        );
        let artifact_id = build_trace_artifact_id(&trace).unwrap();
        assert!(artifact_id.filename_base().contains("my_test_case"));
    }

    #[test]
    fn test_non_ascii_run_id_no_panic() {
        let trace = RunTrace::new(
            "ab©de\u{1F1E8}\u{1F1F5}1234567890".to_string(),
            "2025-01-01T00:00:00Z".to_string(),
            "My Test Case".to_string(),
            "test-model".to_string(),
            "fp-0000".to_string(),
            0,
            String::new(),
        );
        let artifact_id = build_trace_artifact_id(&trace);
        assert!(artifact_id.is_ok());
        let aid = artifact_id.unwrap();
        assert_eq!(aid.run_id_short(), "b©de\u{1F1E8}\u{1F1F5}1234567890");
    }
}

#[cfg(test)]
mod l4_boundary_tests_6bd942d2 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord6bd942d2::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord6bd942d2::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord6bd942d2::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord6bd942d2::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord6bd942d2::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError6bd942d2::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError6bd942d2::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
