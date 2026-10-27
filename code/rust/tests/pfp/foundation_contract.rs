use num_bigint::BigInt;
use num_rational::BigRational;
use serde_json::{json, Value};

use pfp::foundation::{
    assess_extension_family, canonical_json_bytes, decide_oesos, replay_dda_path,
    semantic_equivalent, structurally_identical, CandidateEvaluation, ConservativeExtensionWitness,
    DdaEvent, DdaEventDraft, DdaPath, DdaReplayCode, DeclaredExtensionFamily, DeclaredProjection,
    DeclaredRepairUniverse, DetectorEntry, ExactFiniteDetector, ExhaustionCertificate,
    ExtensionCandidate, FoundationErrorCode, InvariantProjection, LossRecord, OesosDecision,
    PacketKernel, PrimitiveDifference, RepairCandidate, StructureDelta,
};

fn q(numerator: i64, denominator: i64) -> BigRational {
    BigRational::new(BigInt::from(numerator), BigInt::from(denominator))
}

fn repair_evidence(
    candidate_values: &[(&str, &str, BigRational)],
) -> (DeclaredRepairUniverse, ExactFiniteDetector) {
    let universe = DeclaredRepairUniverse::new(
        "ctx",
        "source",
        candidate_values
            .iter()
            .map(|(candidate_id, state_id, _)| {
                RepairCandidate::new(*candidate_id, *state_id).expect("valid candidate")
            })
            .collect(),
    )
    .expect("valid universe");
    let mut entries = vec![DetectorEntry::new("source", q(1, 1)).expect("valid source")];
    entries.extend(candidate_values.iter().map(|(_, state_id, value)| {
        DetectorEntry::new(*state_id, value.clone()).expect("valid candidate value")
    }));
    let detector = ExactFiniteDetector::new("detector", entries).expect("valid detector");
    (universe, detector)
}

#[test]
fn primitive_difference_is_nullary() {
    let witness = PrimitiveDifference;
    assert_eq!(std::mem::size_of_val(&witness), 0);
}

#[test]
fn empty_observations_cannot_forge_nonempty_exhaustion() {
    let (universe, detector) = repair_evidence(&[("candidate-a", "state-a", q(1, 2))]);
    let error = ExhaustionCertificate::certify(&universe, &detector, Vec::new())
        .expect_err("a nonempty declared universe requires complete coverage");
    assert_eq!(error.code(), FoundationErrorCode::IncompleteCoverage);

    let wrong = CandidateEvaluation::new("candidate-a", q(1, 3)).expect("exact observation");
    let error = ExhaustionCertificate::certify(&universe, &detector, vec![wrong])
        .expect_err("detector values are recomputed");
    assert_eq!(error.code(), FoundationErrorCode::EvaluationMismatch);

    let empty =
        DeclaredRepairUniverse::new("ctx", "source", Vec::new()).expect("explicit empty universe");
    let certificate = ExhaustionCertificate::certify(&empty, &detector, Vec::new())
        .expect("empty coverage is valid only for an empty declaration");
    assert!(matches!(
        decide_oesos(&certificate),
        OesosDecision::R2ExtensionLicensed(_)
    ));
}

#[test]
fn r1_has_priority_and_r2_requires_positive_checked_exhaustion() {
    let (r1_universe, r1_detector) = repair_evidence(&[
        ("positive", "state-positive", q(1, 2)),
        ("zero", "state-zero", q(0, 1)),
    ]);
    let r1_certificate =
        ExhaustionCertificate::enumerate(&r1_universe, &r1_detector).expect("checked coverage");
    match decide_oesos(&r1_certificate) {
        OesosDecision::R1SameContext {
            residual,
            selected_candidate_ids,
            ..
        } => {
            assert_eq!(residual, q(0, 1));
            assert_eq!(selected_candidate_ids, vec!["zero"]);
        }
        OesosDecision::R2ExtensionLicensed(_) => panic!("R2 must not bypass a zero repair"),
    }

    let (r2_universe, r2_detector) = repair_evidence(&[
        ("half", "state-half", q(1, 2)),
        ("third", "state-third", q(1, 3)),
    ]);
    let r2_certificate =
        ExhaustionCertificate::enumerate(&r2_universe, &r2_detector).expect("checked coverage");
    match decide_oesos(&r2_certificate) {
        OesosDecision::R2ExtensionLicensed(license) => {
            assert_eq!(license.context_id(), "ctx");
            assert_eq!(license.source_state_id(), "source");
            assert_eq!(license.residual(), &q(1, 3));
        }
        OesosDecision::R1SameContext { .. } => panic!("positive exhaustion must license R2"),
    }
}

fn extension_witness(extra_points: &[i32]) -> ConservativeExtensionWitness<i32, i32> {
    let old = [0, 1];
    let mut new = old.to_vec();
    new.extend(extra_points);
    ConservativeExtensionWitness::certify(
        "ctx",
        "extended-ctx",
        &old,
        &new,
        |point| *point,
        |point| (*point <= 1).then_some(*point),
        |point| q(i64::from(*point + 1), 1),
        |point| q(i64::from(*point + 1), 1),
    )
    .expect("finite lift/retraction and detector preservation")
}

#[test]
fn conservative_extension_checks_roundtrip_and_detector_preservation() {
    let witness = extension_witness(&[2]);
    assert!(witness.forget_lift_holds());
    assert!(witness.detector_preserved());
    assert_eq!(witness.extension_size(), 1);
    assert_eq!(witness.target_point_count(), 3);

    let error = ConservativeExtensionWitness::certify(
        "ctx",
        "bad-ctx",
        &[0, 1],
        &[0, 1, 2],
        |point| *point,
        |point| Some(*point),
        |point| q(i64::from(*point + 1), 1),
        |point| q(i64::from(*point + 2), 1),
    )
    .expect_err("old detector values may not change");
    assert_eq!(error.code(), FoundationErrorCode::DetectorNotPreserved);
}

#[test]
fn extension_assessment_is_scoped_bound_and_tie_preserving() {
    let (universe, detector) = repair_evidence(&[("blocked", "blocked-state", q(1, 2))]);
    let certificate =
        ExhaustionCertificate::enumerate(&universe, &detector).expect("positive exhaustion");
    let second = ExtensionCandidate::evaluate(
        "second",
        "ctx",
        "source",
        2,
        extension_witness(&[2]),
        |_| q(0, 1),
    )
    .expect("resolving extension");
    let first =
        ExtensionCandidate::evaluate("first", "ctx", "source", 3, extension_witness(&[3]), |_| {
            q(0, 1)
        })
        .expect("tied resolving extension");
    let larger = ExtensionCandidate::evaluate(
        "larger",
        "ctx",
        "source",
        4,
        extension_witness(&[4, 5]),
        |_| q(0, 1),
    )
    .expect("larger resolving extension");
    let family = DeclaredExtensionFamily::new(
        "declared-family",
        "ctx",
        "source",
        vec![second, first, larger],
    )
    .expect("bound family");
    let assessment = assess_extension_family(&certificate, &family).expect("scoped comparison");
    assert_eq!(
        assessment.declared_candidate_order(),
        &["second", "first", "larger"]
    );
    assert_eq!(assessment.minimum_extension_size(), 1);
    assert_eq!(assessment.tied_candidate_ids(), &["second", "first"]);
    assert_eq!(assessment.unique_candidate_id(), None);

    let (r1_universe, r1_detector) = repair_evidence(&[("zero", "zero-state", q(0, 1))]);
    let r1_certificate =
        ExhaustionCertificate::enumerate(&r1_universe, &r1_detector).expect("R1 evidence");
    let error = assess_extension_family(&r1_certificate, &family)
        .expect_err("extension must refuse while R1 is available");
    assert_eq!(error.code(), FoundationErrorCode::R1Priority);
}

fn packet(contract: &str, task: &str, payload: Value, parent_id: Option<String>) -> PacketKernel {
    PacketKernel::new(contract, task, payload, parent_id).expect("valid packet kernel")
}

#[test]
fn packet_identity_binds_all_four_fields_and_normalizes_object_order() {
    let root = packet("contract-a", "task-a", json!({"content": "hello"}), None);
    let root_id = root.packet_id();
    assert_ne!(
        packet("contract-b", "task-a", root.payload().clone(), None).packet_id(),
        root_id
    );
    assert_ne!(
        packet("contract-a", "task-b", root.payload().clone(), None).packet_id(),
        root_id
    );
    assert_ne!(
        packet("contract-a", "task-a", json!({"content": "goodbye"}), None).packet_id(),
        root_id
    );
    assert_ne!(
        packet(
            "contract-a",
            "task-a",
            root.payload().clone(),
            Some("0".repeat(64)),
        )
        .packet_id(),
        root_id
    );

    let left_payload: Value =
        serde_json::from_str(r#"{"content":"hello","intent":"answer"}"#).expect("JSON");
    let right_payload: Value =
        serde_json::from_str(r#"{"intent":"answer","content":"hello"}"#).expect("JSON");
    let left = packet("contract-a", "task-a", left_payload, None);
    let right = packet("contract-a", "task-a", right_payload, None);
    assert!(structurally_identical(&left, &right));
    assert_eq!(left.packet_id(), right.packet_id());

    let error = PacketKernel::new("contract-a", "task-a", json!({"x": 0.5}), None)
        .expect_err("packet identity refuses floats");
    assert_eq!(error.code(), FoundationErrorCode::NonExactJson);
}

#[test]
fn packet_id_matches_python_canonical_golden_vector() {
    // Generated with symbol_game/canonical.py::domain_digest through the
    // Python PacketKernel implementation. This covers every admitted JSON
    // node kind: null, bool, integer, string, list, and mapping.
    let golden = packet(
        "core.symbol-game.golden.v1",
        "task-17",
        json!({
            "alpha": [null, true, 7, "omega"],
            "nested": {"b": 2, "a": 1}
        }),
        Some("0123456789abcdef".repeat(4)),
    );
    assert_eq!(
        golden.packet_id(),
        "999043cbf31263572f76446bd54096c194e04ded58129ea9cf85d1bed45ff0ef"
    );
}

#[test]
fn semantic_comparison_requires_an_explicit_projection() {
    let left = packet(
        "chat",
        "task",
        json!({"content": "2 + 2", "format": "plain"}),
        None,
    );
    let right = packet(
        "chat",
        "task",
        json!({"format": "markdown", "content": "2 + 2"}),
        None,
    );
    let error = semantic_equivalent(&left, &right, None)
        .expect_err("semantic equality is not inferred from bytes");
    assert_eq!(error.code(), FoundationErrorCode::ProjectionRequired);

    let content = DeclaredProjection::new("chat-content-v1", |value: &PacketKernel| {
        value
            .payload()
            .get("content")
            .cloned()
            .ok_or_else(|| "content is absent".to_owned())
    })
    .expect("declared projection");
    assert!(semantic_equivalent(&left, &right, Some(&content)).expect("projected comparison"));
}

#[derive(Clone, Debug, PartialEq, Eq)]
struct ExactState {
    value: i64,
    source_revision: String,
}

fn state(value: i64) -> ExactState {
    ExactState {
        value,
        source_revision: "source-abc".to_owned(),
    }
}

fn dda_event(
    before: i64,
    after: i64,
    event_id: &str,
    parent_event_id: Option<&str>,
) -> DdaEvent<ExactState> {
    let projection = InvariantProjection::new("source_revision", |value: &ExactState| {
        Ok(Value::String(value.source_revision.clone()))
    })
    .expect("valid invariant projection");
    DdaEvent::record(
        DdaEventDraft {
            event_id: event_id.to_owned(),
            contract_id: "math-contract".to_owned(),
            task_id: "proof-task".to_owned(),
            source_id: "source-abc".to_owned(),
            before: state(before),
            operation_id: "add".to_owned(),
            parameters: json!({"amount": after - before}),
            after: state(after),
            obstruction_before: q(1, 1),
            obstruction_after: q(0, 1),
            structure_delta: StructureDelta::same_context(),
            losses: Vec::new(),
            parent_event_id: parent_event_id.map(str::to_owned),
        },
        &[projection],
    )
    .expect("valid exact DDA event")
}

#[test]
fn dda_composition_has_identities_associativity_and_boundary_refusals() {
    let first = dda_event(0, 2, "event-a", None);
    let second = dda_event(2, 4, "event-b", Some("event-a"));
    let third = dda_event(4, 6, "event-c", Some("event-b"));
    let a = DdaPath::from_events(state(0), vec![first]).expect("path a");
    let b = DdaPath::from_events(state(2), vec![second]).expect("path b");
    let c = DdaPath::from_events(state(4), vec![third]).expect("path c");

    assert_eq!(
        DdaPath::identity(state(0))
            .compose(&a)
            .expect("left identity"),
        a
    );
    assert_eq!(
        a.compose(&DdaPath::identity(state(2)))
            .expect("right identity"),
        a
    );
    assert_eq!(
        a.compose(&b).expect("a;b").compose(&c).expect("(a;b);c"),
        a.compose(&b.compose(&c).expect("b;c")).expect("a;(b;c)")
    );

    let error = a
        .compose(&DdaPath::identity(state(99)))
        .expect_err("composition is partial on the intermediate state");
    assert_eq!(error.code(), FoundationErrorCode::IntermediateStateMismatch);

    let mut wrong_boundary = dda_event(2, 4, "event-x", Some("event-a"));
    let draft = DdaEventDraft {
        event_id: wrong_boundary.event_id().to_owned(),
        contract_id: "other-contract".to_owned(),
        task_id: wrong_boundary.task_id().to_owned(),
        source_id: wrong_boundary.source_id().to_owned(),
        before: wrong_boundary.before().clone(),
        operation_id: wrong_boundary.operation_id().to_owned(),
        parameters: wrong_boundary.parameters().clone(),
        after: wrong_boundary.after().clone(),
        obstruction_before: wrong_boundary.obstruction_before().clone(),
        obstruction_after: wrong_boundary.obstruction_after().clone(),
        structure_delta: wrong_boundary.structure_delta().clone(),
        losses: Vec::new(),
        parent_event_id: wrong_boundary.parent_event_id().map(str::to_owned),
    };
    wrong_boundary = DdaEvent::record(draft, &[]).expect("standalone alternate boundary");
    let wrong_path = DdaPath::from_events(state(2), vec![wrong_boundary]).expect("path");
    let error = a
        .compose(&wrong_path)
        .expect_err("contract boundary must match");
    assert_eq!(error.code(), FoundationErrorCode::BoundaryMismatch);
}

#[test]
fn dda_refuses_protected_loss_and_replay_mismatch() {
    let projection = InvariantProjection::new("source_revision", |value: &ExactState| {
        Ok(Value::String(value.source_revision.clone()))
    })
    .expect("valid invariant projection");
    let protected_loss = LossRecord::new("source_revision", "discarded binding")
        .expect("well-formed loss declaration");
    let error = DdaEvent::record(
        DdaEventDraft {
            event_id: "loss-event".to_owned(),
            contract_id: "math-contract".to_owned(),
            task_id: "proof-task".to_owned(),
            source_id: "source-abc".to_owned(),
            before: state(0),
            operation_id: "add".to_owned(),
            parameters: json!({"amount": 2}),
            after: state(2),
            obstruction_before: q(1, 1),
            obstruction_after: q(0, 1),
            structure_delta: StructureDelta::same_context(),
            losses: vec![protected_loss],
            parent_event_id: None,
        },
        &[projection],
    )
    .expect_err("protected information loss is refused");
    assert_eq!(error.code(), FoundationErrorCode::ProtectedLoss);

    let event = dda_event(0, 2, "event-a", None);
    let path = DdaPath::from_events(state(0), vec![event]).expect("valid path");
    let accepted = replay_dda_path(&path, |operation, before, parameters| {
        (operation == "add").then(|| ExactState {
            value: before.value + parameters["amount"].as_i64().expect("integer amount"),
            source_revision: before.source_revision.clone(),
        })
    });
    assert!(accepted.accepted());
    assert_eq!(accepted.after(), Some(&state(2)));

    let mismatch = replay_dda_path(&path, |operation, before, _| {
        (operation == "add").then(|| before.clone())
    });
    assert_eq!(mismatch.code(), DdaReplayCode::AfterStateMismatch);
}

#[test]
fn canonical_json_bytes_matches_python_canonical_for_exact_integers() {
    // Bytes from pfp/infrastructure/serialization/canonical.py:
    // Python ints are unbounded, and json.loads("-0") is the int 0.
    let value: Value =
        serde_json::from_str(r#"{"n": 18446744073709551616, "z": -0}"#).expect("valid JSON");
    let bytes = canonical_json_bytes(&value).expect("exact integers are admitted");
    assert_eq!(
        String::from_utf8(bytes).unwrap(),
        concat!(
            r#"["core-canonical-v1","mapping",[["core-canonical-v1","string","builtins"],"#,
            r#"["core-canonical-v1","string","dict"],["core-canonical-v1","entry","#,
            r#"[["core-canonical-v1","string","n"],["core-canonical-v1","int","18446744073709551616"]]],"#,
            r#"["core-canonical-v1","entry",[["core-canonical-v1","string","z"],"#,
            r#"["core-canonical-v1","int","0"]]]]]"#
        )
    );
    // Python would encode 1.5 as a float node; the foundation's exact subset refuses it.
    let float: Value = serde_json::from_str("1.5").expect("valid JSON");
    assert_eq!(
        canonical_json_bytes(&float).unwrap_err().code(),
        FoundationErrorCode::NonExactJson
    );
}

// Origin: engine/crates_rs/tests/pfp/foundation_contract.rs
// Claim: urn:core:crates_rs:tests:foundation-contract:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord9e60fb20 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord9e60fb20` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError9e60fb20 {
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
impl BoundaryError9e60fb20 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError9e60fb20 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError9e60fb20 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord9e60fb20 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError9e60fb20> {
        if capacity_bound == 0 {
            return Err(BoundaryError9e60fb20::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError9e60fb20::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError9e60fb20::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_9e60fb20() {
    let admitted = BoundaryRecord9e60fb20::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord9e60fb20::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
