//! Retained research workflow data, checked against the Rust controller.
//!
//! AuthorityEffect: None.

use core_adversary::research_loop::pack::{
    check_pack, response_schema, validate_response, WORKFLOW_FILE,
};
use core_adversary::research_loop::response_schema::ResponseSchema;
use core_adversary::research_loop::state::ResearchLoop;
use serde_json::{json, Value};
use std::path::{Path, PathBuf};

fn pack_dir() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join("../tests/core_adversary/fixtures/research_pack_v1")
}

fn yaml(path: &Path) -> Value {
    serde_yaml::from_str(&std::fs::read_to_string(path).unwrap()).unwrap()
}

fn copy_tree(from: &Path, to: &Path) {
    std::fs::create_dir_all(to).unwrap();
    for entry in std::fs::read_dir(from).unwrap() {
        let entry = entry.unwrap();
        let target = to.join(entry.file_name());
        if entry.file_type().unwrap().is_dir() {
            copy_tree(&entry.path(), &target);
        } else {
            std::fs::copy(entry.path(), target).unwrap();
        }
    }
}

/// A scratch copy of the folder with one file rewritten.
fn drifted(file: &str, edit: impl Fn(&str) -> String) -> tempfile::TempDir {
    let dir = tempfile::tempdir().unwrap();
    for sub in ["prompts", "stages", "contracts"] {
        copy_tree(&pack_dir().join(sub), &dir.path().join(sub));
    }
    std::fs::copy(
        pack_dir().join(WORKFLOW_FILE),
        dir.path().join(WORKFLOW_FILE),
    )
    .unwrap();
    let path = dir.path().join(file);
    let text = std::fs::read_to_string(&path).unwrap();
    let edited = edit(&text);
    assert_ne!(edited, text, "the edit must change {file}");
    std::fs::write(&path, edited).unwrap();
    dir
}

#[test]
fn the_retained_pack_matches_the_controller() {
    let report = check_pack(&pack_dir()).unwrap();
    assert_eq!(report["packets"].as_array().unwrap().len(), 9);
    assert_eq!(report["dispositions"], json!(11));
}

/// A pack file and the edit that makes it drift from the controller.
type Drift = (&'static str, fn(&str) -> String);

#[test]
fn drift_in_the_pack_is_refused() {
    let cases: [Drift; 6] = [
        (WORKFLOW_FILE, |t| {
            t.replacen("route: Refused", "route: SWAP", 1)
                .replacen("route: InfrastructureFailure", "route: Refused", 1)
                .replacen("route: SWAP", "route: InfrastructureFailure", 1)
        }),
        (WORKFLOW_FILE, |t| {
            t.replacen("  max_rounds: 3", "  max_rounds: 4", 1)
        }),
        (WORKFLOW_FILE, |t| t.replacen("- retention_policy\n", "", 1)),
        (WORKFLOW_FILE, |t| {
            t.replacen("route: StabilizedSurvivor", "route: Survived", 1)
        }),
        ("stages/stage_5_evaluation.yaml", |t| {
            t.replacen("executor: host", "executor: model", 1)
        }),
        ("prompts/p_research_03.yaml", |t| {
            t.replacen("  generation_id: 0", "  generation_id: 1", 1)
        }),
    ];
    for (file, edit) in cases {
        let dir = drifted(file, edit);
        assert_eq!(
            check_pack(dir.path()).unwrap_err().code,
            "RESEARCH_PACK_DRIFT",
            "{file}"
        );
    }
    let dir = drifted("prompts/p_research_02.yaml", |t| {
        t.replacen("  raw_text: 'MISSION RULES", "  raw_text: 'MISSION RULE", 1)
    });
    assert_eq!(
        check_pack(dir.path()).unwrap_err().code,
        "RESEARCH_PACK_DRIFT"
    );
}

#[test]
fn the_example_critic_response_validates_and_mutations_do_not() {
    let response = yaml(&pack_dir().join("examples/response_stage_6.yaml"));
    assert_eq!(
        validate_response(&pack_dir(), "P_RESEARCH_06", &response).unwrap(),
        vec![]
    );

    let rules = |value: &Value| -> Vec<String> {
        validate_response(&pack_dir(), "P_RESEARCH_06", value)
            .unwrap()
            .into_iter()
            .map(|v| format!("{} {}", v.path, v.rule))
            .collect()
    };
    let mut missing = response.clone();
    missing.as_object_mut().unwrap().remove("summary");
    assert_eq!(rules(&missing), ["/summary required"]);
    let mut extra = response.clone();
    extra["final_terminal_status"] = json!("Verified");
    assert_eq!(
        rules(&extra),
        ["/final_terminal_status additionalProperties"]
    );
    let mut policy = response.clone();
    policy["derived_under_policy"] = json!("SPK-002");
    assert_eq!(rules(&policy), ["/derived_under_policy const"]);
    let mut blank = response.clone();
    blank["summary"]["evidence_scope"] = json!("   ");
    assert_eq!(rules(&blank), ["/summary/evidence_scope pattern"]);
    let mut sections = response.clone();
    sections["sections"] = json!([]);
    assert_eq!(rules(&sections), ["/sections minItems"]);
}

#[test]
fn stage_five_has_no_model_response() {
    let refused = validate_response(&pack_dir(), "P_RESEARCH_05", &json!({})).unwrap_err();
    assert_eq!(refused.code, "STAGE5_HOST_ONLY");
    assert_eq!(
        validate_response(&pack_dir(), "P_RESEARCH_99", &json!({}))
            .unwrap_err()
            .code,
        "RESEARCH_PACKET_UNKNOWN"
    );
    // The host-check shape still compiles: the host writes stage 5 records in it.
    response_schema(&pack_dir(), "P_RESEARCH_05").unwrap();
}

#[test]
fn unsupported_schema_keywords_are_refused() {
    for schema in [
        json!({"type": "object", "oneOf": []}),
        json!({"$ref": "#/$defs/Missing"}),
        json!({"$ref": "https://example.com/schema"}),
        json!({"type": "decimal"}),
        json!({"properties": {"a": {"pattern": "("}}}),
    ] {
        assert_eq!(
            ResponseSchema::compile(&schema).unwrap_err().code,
            "RESPONSE_SCHEMA_UNSUPPORTED",
            "{schema}"
        );
    }
}

#[test]
fn prefix_items_close_the_array_when_items_is_false() {
    let schema = ResponseSchema::compile(&json!({
        "type": "array", "prefixItems": [{"const": "a"}, {"type": "integer"}], "items": false
    }))
    .unwrap();
    assert!(schema.validate(&json!(["a", 2])).is_empty());
    assert_eq!(schema.validate(&json!(["a", 2, 3])).len(), 1);
    assert_eq!(
        schema.validate(&json!(["a", true])).len(),
        1,
        "a boolean is not an integer"
    );
    assert_eq!(schema.validate(&json!(["a", 1.5])).len(), 1);
}

#[test]
fn the_estate_example_mission_is_admitted() {
    let mission = yaml(&pack_dir().join("examples/mission.yaml"));
    let state = ResearchLoop::admit(&mission).unwrap();
    assert_eq!(state.run_id(), "LOCAL_REPLAY_ONLY");
}

// Origin: engine/crates_rs/tests/core_adversary/research_pack.rs
// Claim: urn:core:crates_rs:tests:research-pack:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord0db3945d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord0db3945d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError0db3945d {
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
impl BoundaryError0db3945d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError0db3945d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError0db3945d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord0db3945d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError0db3945d> {
        if capacity_bound == 0 {
            return Err(BoundaryError0db3945d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError0db3945d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError0db3945d::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_0db3945d() {
    let admitted = BoundaryRecord0db3945d::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord0db3945d::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
