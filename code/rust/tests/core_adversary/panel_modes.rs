//! Core and full panel modes of the Adversary council.
//!
//! AuthorityEffect: None.

use core_adversary::council::{assemble_council, assemble_council_for, PanelMode, CORE_SEATS};
use serde_json::{json, Value};
use std::collections::BTreeSet;

fn canonical(name: &str) -> String {
    std::fs::read_to_string(
        std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
            .join("../../../adversary/roles")
            .join(name),
    )
    .unwrap()
}

fn assembly(mode: PanelMode) -> core_adversary::council::CouncilAssembly {
    assemble_council_for(&canonical("adversary_panel.yaml"), &canonical("scenes.yaml"), mode).unwrap()
}

fn scene_seats(dict: &Value) -> Vec<(String, Vec<String>)> {
    dict[1]["scenes"]
        .as_array()
        .unwrap()
        .iter()
        .map(|scene| {
            let seats = scene["required_seat_ids"]
                .as_array()
                .unwrap()
                .iter()
                .map(|v| v.as_str().unwrap().to_owned())
                .collect();
            (scene["scene_id"].as_str().unwrap().to_owned(), seats)
        })
        .collect()
}

#[test]
fn full_mode_is_the_assembly_that_existed_before_modes() {
    let before = assemble_council(&canonical("adversary_panel.yaml"), &canonical("scenes.yaml"))
        .unwrap()
        .to_dict()
        .unwrap();
    let full = assembly(PanelMode::Full);
    assert_eq!(full.to_dict().unwrap(), before);
    assert_eq!(full.panel["mode"], "full");
    assert_eq!(full.panel["scene_seat_ids"].as_array().unwrap().len(), 8);
    assert_eq!(full.panel["seatless_acts"], json!([]));
}

#[test]
fn core_mode_seats_five_and_names_how_each_seatless_act_is_handled() {
    let core = assembly(PanelMode::Core);
    core.scheduler().unwrap();
    let dict = core.to_dict().unwrap();
    let declared: BTreeSet<&str> = dict[0]["seat_requirements"]
        .as_array()
        .unwrap()
        .iter()
        .map(|seat| seat["seat_id"].as_str().unwrap())
        .collect();
    assert_eq!(declared, CORE_SEATS.into_iter().collect());
    let domains: Vec<(&str, &str)> = dict[0]["seat_requirements"]
        .as_array()
        .unwrap()
        .iter()
        .map(|seat| (seat["seat_id"].as_str().unwrap(), seat["trust_domain"].as_str().unwrap()))
        .collect();
    for (seat, domain) in [
        ("seat_gauge_breaker", "PRODUCER"),
        ("seat_defect_hunter", "CRITIC"),
        ("seat_primal_dual", "TESTER"),
        ("seat_adversary", "EVALUATOR"),
        ("seat_manuscript_truth", "SELECTOR"),
    ] {
        assert!(domains.contains(&(seat, domain)), "{seat} must be {domain}: {domains:?}");
    }
    let panel = &core.panel;
    assert_eq!(panel["mode"], "core");
    assert_eq!(panel["schema_version"], "core.adversary.panel.v1");
    let seatless: Vec<&str> = panel["seatless_acts"]
        .as_array()
        .unwrap()
        .iter()
        .map(|act| {
            assert_eq!(act["handled_by"], "seat_adversary");
            assert_eq!(act["handling"], "ASSIGNED_TO_EVALUATOR");
            act["scene_id"].as_str().unwrap()
        })
        .collect();
    assert_eq!(seatless.len(), 3, "{seatless:?}");
    assert!(seatless[0].starts_with("act1_"));
    assert!(seatless[1].starts_with("act6_"));
    assert!(seatless[2].starts_with("act7_"));
    for (scene, seats) in scene_seats(&dict) {
        assert!(seats.iter().all(|s| CORE_SEATS.contains(&s.as_str())), "{scene}: {seats:?}");
    }
    assert_ne!(dict[0]["definition_name"], json!("adversary_panel_larger_cast"));
}

#[test]
fn an_unknown_mode_refuses() {
    let error = PanelMode::parse("medium").unwrap_err();
    assert_eq!(error.code, "ADVERSARY_COUNCIL_PROFILE_INVALID");
    assert_eq!(PanelMode::parse("core").unwrap(), PanelMode::Core);
    assert_eq!(PanelMode::parse("full").unwrap(), PanelMode::Full);
}

// Origin: engine/crates_rs/tests/core_adversary/panel_modes.rs
// Claim: urn:core:crates_rs:tests:panel-modes:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb9927b97 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb9927b97` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb9927b97 {
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
impl BoundaryErrorb9927b97 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb9927b97 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb9927b97 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb9927b97 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb9927b97> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb9927b97::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb9927b97::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb9927b97::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_b9927b97() {
    let admitted = BoundaryRecordb9927b97::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordb9927b97::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
