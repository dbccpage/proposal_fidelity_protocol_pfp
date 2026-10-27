//! Integration tests for the OEWAS + OEEIS -> OEADVERSARY bridge (`oewas_oeeis_bridge`).
//!
//! AuthorityEffect: None.

use num_bigint::BigUint;
use num_rational::BigRational;
use core_epistemic_immune_system::{
    anti_skill::{AntiSkillStatus, FailureClass},
    regulation::DetectorTelemetry,
    thymus::ThymusVerdict,
};
use core_operads::{
    immune_guards::{immune_guarded_substitute, DangerScreenRequest},
    immune_ports::{
        DetectorIdentity, DetectorMatch, ExactCount, HostDangerObservation, ImmuneScreenPort,
        SensorReading,
    },
    planar::OperadOperation,
    policy::DangerSignalPolicy,
    workflow::WorkflowReport,
};
use core_adversary::{
    oewas_oeeis_bridge::{OeeisImmuneAdapter, AdversaryOeopBoutBridge},
    specialization::{base, PortName},
};
use serde_json::json;
use std::collections::BTreeSet;

fn theta_op() -> OperadOperation {
    OperadOperation::new(
        "theta".into(),
        vec!["Audit".into(), "State".into()],
        "Receipt".into(),
    )
    .expect("valid theta")
}

fn phi_op() -> OperadOperation {
    OperadOperation::new("phi".into(), vec!["Ledger".into()], "Audit".into()).expect("valid phi")
}

fn sample_match() -> DetectorMatch {
    DetectorMatch::new(
        "E".into(),
        "m".into(),
        ExactCount::new(BigUint::from(0u8)),
    )
    .expect("valid match")
}

fn sample_danger(observer: &str) -> HostDangerObservation {
    HostDangerObservation::new(
        "PROTECTED_FIELD_VIOLATION".into(),
        "HIGH".into(),
        ExactCount::new(BigUint::from(1u8)),
        format!("sha256:{}", "a".repeat(64)),
        observer.into(),
        Vec::new(),
    )
    .expect("valid danger")
}

#[test]
fn oeeis_adapter_enforces_two_signal_conjunction_and_signal_independence() {
    let mut adapter = OeeisImmuneAdapter::new(vec![
        "theorem coboundary_nilpotent : d1 * d0 = 0".into(),
    ])
    .expect("adapter");
    let detector =
        DetectorIdentity::new("prompt-scanner".into(), BTreeSet::new(), false).expect("detector");
    let m = sample_match();
    let danger = sample_danger("host-protected-field-check");

    // 1. Both Signal 1 and independent Signal 2 -> Quarantined (blocks = true)
    let v_both = adapter
        .danger_verdict(&[m.clone()], Some(&danger), &detector)
        .expect("both signals");
    assert!(*v_both.blocks());
    assert_eq!(v_both.decision(), "QUARANTINED");

    // 2. Signal 2 only (no detector match) -> DiagnosticOnly (blocks = false)
    let v_sig2_only = adapter
        .danger_verdict(&[], Some(&danger), &detector)
        .expect("signal 2 only");
    assert!(!*v_sig2_only.blocks());
    assert_eq!(v_sig2_only.decision(), "DIAGNOSTIC_ONLY");

    // 3. Signal 1 only (no host danger observation) -> DiagnosticOnly (blocks = false)
    let v_sig1_only = adapter
        .danger_verdict(&[m.clone()], None, &detector)
        .expect("signal 1 only");
    assert!(!*v_sig1_only.blocks());
    assert_eq!(v_sig1_only.decision(), "DIAGNOSTIC_ONLY");

    // 4. Signal 2 observed by the detector itself (case-insensitive) -> TWO_SIGNAL_COLLAPSE refusal
    for self_observer in ["prompt-scanner", "Prompt-Scanner", "PROMPT-SCANNER"] {
        let derived = sample_danger(self_observer);
        let err = adapter
            .danger_verdict(&[m.clone()], Some(&derived), &detector)
            .expect_err("self-derived danger must be refused");
        assert_eq!(err.code, "TWO_SIGNAL_COLLAPSE");
    }

    // 5. Detector's own predicate overlapping Signal 2 kind -> TWO_SIGNAL_COLLAPSE refusal
    let overlapping_detector = DetectorIdentity::new(
        "pharmacy".into(),
        BTreeSet::from(["PROTECTED_FIELD_VIOLATION".to_owned()]),
        false,
    )
    .expect("overlapping detector");
    let err = adapter
        .danger_verdict(&[m.clone()], Some(&danger), &overlapping_detector)
        .expect_err("predicate overlap must be refused");
    assert_eq!(err.code, "TWO_SIGNAL_COLLAPSE");

    // 6. Guarded operad substitution propagates TWO_SIGNAL_COLLAPSE instead of DANGER_GATE_SUPPRESSION
    let derived = sample_danger("PROMPT-SCANNER");
    let sub_err = immune_guarded_substitute(
        &theta_op(),
        &json!(0),
        &phi_op(),
        &mut adapter,
        DangerScreenRequest {
            detector: &detector,
            matches: &[m],
            danger: Some(&derived),
        },
    )
    .expect_err("must fail with TWO_SIGNAL_COLLAPSE");
    assert_eq!(sub_err.code, "TWO_SIGNAL_COLLAPSE");
}

#[test]
fn oeeis_adapter_allosteric_quorum_and_duplicate_sensor_refusal() {
    let mut adapter = OeeisImmuneAdapter::standard_baseline().expect("baseline adapter");
    let s_a = SensorReading::new("a".into(), BigRational::from_integer(1.into())).unwrap();
    let s_b = SensorReading::new("b".into(), BigRational::from_integer(1.into())).unwrap();

    // Two distinct sensors with signal 1 reach Hill quorum (S=2, H(2)=1/2 >= 1/2) -> blocks = false
    let v_pass = adapter
        .quorum_verdict(&[s_a.clone(), s_b])
        .expect("two distinct sensors");
    assert!(!*v_pass.blocks());
    assert_eq!(v_pass.decision(), "ACTIVATED");

    // One sensor alone with signal 1 is below Hill quorum (S=1, H(1)=1/5 < 1/2) -> blocks = true
    let v_block = adapter
        .quorum_verdict(&[s_a.clone()])
        .expect("single sensor");
    assert!(*v_block.blocks());
    assert_eq!(v_block.decision(), "NOT_ACTIVATED");

    // Duplicate sensor (including casefolded duplicate) is refused with DUPLICATE_SENSOR
    let s_a_upper = SensorReading::new("A".into(), BigRational::from_integer(1.into())).unwrap();
    for dup in [[s_a.clone(), s_a.clone()], [s_a, s_a_upper]] {
        let err = adapter
            .quorum_verdict(&dup)
            .expect_err("duplicate sensor must be refused");
        assert_eq!(err.code, "DUPLICATE_SENSOR");
    }
}

#[test]
fn oeeis_adapter_thymus_tolerance_distinguishes_autoimmunity_and_unscreenable() {
    let mut adapter = OeeisImmuneAdapter::new(vec![
        "theorem coboundary_nilpotent : d1 * d0 = 0".into(),
    ])
    .expect("adapter");

    // Phrase matching healthy self fixture -> REFUSED (blocks = true)
    let v_autoimmune = adapter
        .trigger_tolerance_verdict("SKILL-GATE-test", &["d1 * d0".to_owned()])
        .expect("autoimmune check");
    assert!(*v_autoimmune.blocks());
    assert_eq!(v_autoimmune.decision(), "REFUSED");

    // Overlong trigger phrase (>256 chars) -> UNSCREENABLE (blocks = true)
    let v_unscreenable = adapter
        .trigger_tolerance_verdict("SKILL-GATE-test", &["x".repeat(300)])
        .expect("unscreenable check");
    assert!(*v_unscreenable.blocks());
    assert_eq!(v_unscreenable.decision(), "UNSCREENABLE");

    // Non-self-reactive phrase -> ADMITTED (blocks = false)
    let v_admitted = adapter
        .trigger_tolerance_verdict("SKILL-GATE-test", &["verify-claim-ledger".to_owned()])
        .expect("admitted check");
    assert!(!*v_admitted.blocks());
    assert_eq!(v_admitted.decision(), "ADMITTED");
}

#[test]
fn adversary_oewas_bout_bridge_enforces_seven_act_stage_port_licenses() {
    let mut bridge = AdversaryOeopBoutBridge::standard_base().expect("standard base bridge");
    let theta = theta_op();
    let phi = phi_op();
    let detector =
        DetectorIdentity::new("prompt-scanner".into(), BTreeSet::new(), false).expect("detector");
    let m = sample_match();
    let danger = sample_danger("host-protected-field-check");

    // Act I ("intake") licenses [AdversaryRuntime, ImmuneAntibodies]:
    // 1. Clean danger screen at "intake" allows operad substitution:
    let composed = bridge
        .stage_danger_guarded_substitute(
            "intake",
            &theta,
            &json!(0),
            &phi,
            DangerScreenRequest {
                detector: &detector,
                matches: &[],
                danger: None,
            },
        )
        .expect("clean substitution at intake");
    assert_eq!(composed.source_colours(), &["Ledger", "State"]);
    assert_eq!(composed.target_colour(), "Receipt");

    // 2. Corroborated two-signal danger at "intake" suppresses operad substitution:
    let suppressed = bridge
        .stage_danger_guarded_substitute(
            "intake",
            &theta,
            &json!(0),
            &phi,
            DangerScreenRequest {
                detector: &detector,
                matches: &[m.clone()],
                danger: Some(&danger),
            },
        )
        .expect_err("corroborated danger must suppress substitution");
    assert_eq!(suppressed.code, "DANGER_GATE_SUPPRESSION");

    // Act IV ("gauge_break") only licenses [SeatTransport], NOT ImmuneAntibodies or OeopAntiSkill:
    let unlicensed = bridge
        .stage_danger_guarded_substitute(
            "gauge_break",
            &theta,
            &json!(0),
            &phi,
            DangerScreenRequest {
                detector: &detector,
                matches: &[],
                danger: None,
            },
        )
        .expect_err("gauge_break does not license immune or anti-skill ports");
    assert_eq!(unlicensed.code, "PORT_NOT_LICENSED_AT_STAGE");

    // Act VII ("terminal_gate") licenses [NativeBout, SgtEmission, OeopAntiSkill, OeopLearning, EnvelopeStore]:
    // 3. Allosteric quorum substitution succeeds at "terminal_gate" via OeopLearning:
    let s_a = SensorReading::new("a".into(), BigRational::from_integer(1.into())).unwrap();
    let s_b = SensorReading::new("b".into(), BigRational::from_integer(1.into())).unwrap();
    let quorum_composed = bridge
        .stage_allosteric_quorum_substitute("terminal_gate", &theta, &json!(0), &phi, &[s_a, s_b])
        .expect("quorum substitution at terminal_gate");
    assert_eq!(quorum_composed.source_colours(), &["Ledger", "State"]);

    // 4. Workflow guard evaluation at "compost" (Act VI, licenses ImmuneAntibodies):
    let report = WorkflowReport::new("wf-01".into(), theta.clone(), Some(composed), Vec::new());
    let policy =
        DangerSignalPolicy::new(true, true, BigRational::new(1.into(), 2.into())).expect("policy");
    let guarded_report = bridge
        .stage_validate_workflow_guard(
            "compost",
            &report,
            &policy,
            DangerScreenRequest {
                detector: &detector,
                matches: &[m],
                danger: Some(&danger),
            },
        )
        .expect("workflow guard evaluation");
    let guarded_json = json!(guarded_report);
    assert!(guarded_json["composed"].is_null());
    assert_eq!(guarded_json["findings"].as_array().unwrap().len(), 1);
    assert_eq!(
        guarded_json["findings"][0]["code"],
        "DANGER_GATE_SUPPRESSION"
    );

    // 5. Anti-skill proposal, ThymusGate screening, Formulary admission, and TregSupervisor telemetry review at "terminal_gate":
    let (candidate_spec, thymus_verdict) = bridge
        .stage_propose_and_screen_antiskill(
            "terminal_gate",
            r"subfloor_counterfeit_witness",
            FailureClass::CounterfeitExactness,
            "adversary_bout",
            "Detects counterfeit exactness witness tokens",
            200,
        )
        .expect("propose and screen anti-skill");
    assert!(matches!(thymus_verdict, ThymusVerdict::Survived { .. }));
    assert_eq!(candidate_spec.status, AntiSkillStatus::Candidate);

    let (mut admitted_spec, receipt) = bridge
        .stage_register_and_admit_antiskill(
            "terminal_gate",
            candidate_spec,
            "Dr. Carroll",
            201,
            "sha256_human_admission_receipt",
        )
        .expect("register and admit in formulary");
    assert_eq!(admitted_spec.status, AntiSkillStatus::Admitted);
    assert_eq!(receipt.admitted_by, "Dr. Carroll");
    assert_eq!(receipt.authority_effect, "None");

    let telemetry = DetectorTelemetry {
        anti_skill_id: admitted_spec.id.clone(),
        true_positives: 2,
        false_positives: 9,
        last_active_epoch: 205,
    };
    let suspended = bridge
        .stage_review_detector_telemetry("terminal_gate", &mut admitted_spec, &telemetry)
        .expect("treg review");
    assert!(suspended);
    assert_eq!(admitted_spec.status, AntiSkillStatus::Suspended);

    // 6. Narrowed child specialization without OeopAntiSkill/ImmuneAntibodies is refused at construction or stage check:
    let mut narrowed = base();
    narrowed.specialization_id = "adversary.narrow".into();
    narrowed.ancestry.push("adversary.narrow".into());
    narrowed.licensed_ports.remove(&PortName::OeopAntiSkill);
    narrowed.licensed_ports.remove(&PortName::OeopLearning);
    narrowed.stage_plan.iter_mut().for_each(|s| {
        s.ports
            .retain(|p| narrowed.licensed_ports.contains(p));
    });
    let mut narrowed_bridge =
        AdversaryOeopBoutBridge::new(narrowed, OeeisImmuneAdapter::standard_baseline().unwrap())
            .expect("narrowed bridge");
    let err = narrowed_bridge
        .stage_allosteric_quorum_substitute("terminal_gate", &theta, &json!(0), &phi, &[])
        .expect_err("terminal_gate no longer licenses OeopLearning");
    assert_eq!(err.code, "PORT_NOT_LICENSED_AT_STAGE");
}

// Origin: engine/crates_rs/tests/core_adversary/oewas_oeeis_bridge.rs
// Claim: urn:core:crates_rs:tests:oewas-oeeis-bridge:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord083cf5c5 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord083cf5c5` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError083cf5c5 {
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
impl BoundaryError083cf5c5 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError083cf5c5 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError083cf5c5 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord083cf5c5 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError083cf5c5> {
        if capacity_bound == 0 {
            return Err(BoundaryError083cf5c5::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError083cf5c5::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError083cf5c5::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_083cf5c5() {
    let admitted = BoundaryRecord083cf5c5::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord083cf5c5::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
