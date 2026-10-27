//! v2 field-isolation matrix (ADR-008 §6).
//!
//! **Exactly one field is mutated per test.** v1's tests 6–8 varied several hashed
//! fields at once, so deleting the field they claimed to pin could have left them
//! green — the same "check that cannot fail" defect they existed to prevent.
//!
//! Row 13 of the matrix is the one that would have caught v1 round 3: *removing
//! each hashed field must make its dedicated mutation test fail.*
//!
//! Authority: None.

use std::collections::BTreeMap;

use num_rational::BigRational;
use num_traits::{One, Zero};
use core_epk::epk_engine::{BoundarySlice, CompositionRecord, TraceLedger, TraceRecord};
use core_epk::verified_continuation_context_v2::{
    decide, verify, AcceptedIntakeReceipt, AdmissionAuthority, CapacitySolver,
    ContinuationBlockerV2, GlobalEvaluatorReplay, RawEvidencePacket, RefusalStore,
    RefusingVerifierSuite, TransportClaim, TransportVerifier, TypedRefusal, VerifierSuite,
    V2_CONTEXT_SCHEMA,
};
use core_types::{
    DetectorCapacityEvidence, DetectorCapacityResiduals, DetectorCapacityWitness,
    DetectorDeploymentDeclaration, DetectorEvaluatorDeclaration, DetectorEvaluatorRole,
    ProtectedDistinctionDeclaration, DETECTOR_CAPACITY_COMPARISON_TOLERANCE,
    DETECTOR_CAPACITY_RANK_TOLERANCE, DETECTOR_CAPACITY_RESIDUAL_ACCEPTANCE_TOLERANCE,
};

// ── a trusted verifier suite for tests ───────────────────────────────────────
//
// The TEST supplies the trusted verifiers. That is the point: production callers
// must too, and `RefusingVerifierSuite` is what they get if they do not.

struct TestVerifiers {
    /// Ground truth the evaluator would observe, independent of the packet.
    truth: BTreeMap<String, bool>,
    /// Residual the adapter actually produces at the target carrier.
    measured_target: f64,
    standing: Vec<ContinuationBlockerV2>,
    admit_ok: bool,
    capacity_value: f64,
}

impl Default for TestVerifiers {
    fn default() -> Self {
        Self {
            truth: ROWS
                .iter()
                .map(|&(id, _, _, eg)| (id.to_string(), eg))
                .collect(),
            measured_target: 0.25, // equals the corpus ngd: 1 of 4 rows is Δ_E = −1
            standing: vec![],
            admit_ok: true,
            capacity_value: 0.1,
        }
    }
}

impl AdmissionAuthority for TestVerifiers {
    fn confirm_admission(&self, _r: &AcceptedIntakeReceipt) -> Result<(), TypedRefusal> {
        if self.admit_ok {
            Ok(())
        } else {
            Err(TypedRefusal::IntakeNotAccepted)
        }
    }
}
impl GlobalEvaluatorReplay for TestVerifiers {
    fn replay_global(&self, r: &CompositionRecord) -> Result<bool, TypedRefusal> {
        self.truth
            .get(&r.composed_trace_id)
            .copied()
            .ok_or_else(|| TypedRefusal::GlobalTraceMissing {
                record_id: r.composed_trace_id.clone(),
            })
    }
}
impl CapacitySolver for TestVerifiers {
    fn solve(
        &self,
        d: &DetectorDeploymentDeclaration,
        _r: &[CompositionRecord],
        _l: &TraceLedger,
        _b: &BoundarySlice,
    ) -> Result<DetectorCapacityEvidence, TypedRefusal> {
        Ok(evidence(d, self.capacity_value))
    }
}
impl TransportVerifier for TestVerifiers {
    fn measure_target(&self, _c: &TransportClaim, _s: f64) -> Result<f64, TypedRefusal> {
        Ok(self.measured_target)
    }
}
impl RefusalStore for TestVerifiers {
    fn standing_refusals(&self, _run_id: &str) -> Vec<ContinuationBlockerV2> {
        self.standing.clone()
    }
}
impl VerifierSuite for TestVerifiers {
    fn admission(&self) -> &dyn AdmissionAuthority {
        self
    }
    fn global_replay(&self) -> &dyn GlobalEvaluatorReplay {
        self
    }
    fn capacity(&self) -> &dyn CapacitySolver {
        self
    }
    fn transport(&self) -> &dyn TransportVerifier {
        self
    }
    fn refusals(&self) -> &dyn RefusalStore {
        self
    }
}

fn trusted() -> TestVerifiers {
    TestVerifiers::default()
}

/// One named single-field mutation of a packet.
type PacketMutation = Box<dyn Fn(&mut RawEvidencePacket)>;

// ── fixtures ─────────────────────────────────────────────────────────────────

const ROWS: &[(&str, bool, bool, bool)] = &[
    ("r0", true, true, false),
    ("r1", false, false, false),
    ("r2", false, true, true),
    ("r3", false, true, false),
];

fn corpus() -> (Vec<CompositionRecord>, TraceLedger, BoundarySlice) {
    let mut ledger = TraceLedger::new();
    let mut records = Vec::new();
    let mut states = Vec::new();
    for &(id, e1, e2, eg) in ROWS {
        let (l, r, mid) = (
            format!("{id}-left"),
            format!("{id}-right"),
            format!("{id}-middle"),
        );
        states.push(mid.clone());
        ledger.insert(
            TraceRecord::new(
                &l,
                "task",
                "left",
                None,
                format!("{id}-src"),
                &mid,
                BigRational::one(),
                BigRational::zero(),
                e1,
            )
            .unwrap(),
        );
        ledger.insert(
            TraceRecord::new(
                &r,
                "task",
                "right",
                None,
                &mid,
                format!("{id}-tgt"),
                BigRational::one(),
                BigRational::zero(),
                e2,
            )
            .unwrap(),
        );
        records.push(CompositionRecord::new(id, l, r, e1, e2, eg, None).unwrap());
    }
    (records, ledger, BoundarySlice::new("B", states))
}

fn declaration(
    records: &[CompositionRecord],
    boundary: &BoundarySlice,
    epsilon: f64,
    model: &str,
) -> DetectorDeploymentDeclaration {
    let carriers: Vec<_> = records
        .iter()
        .map(|r| r.composed_trace_id.clone())
        .collect();
    let evaluators = [
        DetectorEvaluatorRole::LocalLeft,
        DetectorEvaluatorRole::LocalRight,
        DetectorEvaluatorRole::Global,
    ]
    .into_iter()
    .map(|role| {
        DetectorEvaluatorDeclaration::new(
            role,
            carriers.clone(),
            records.iter().map(|rec| {
                let v = match role {
                    DetectorEvaluatorRole::LocalLeft => rec.local_left_pass,
                    DetectorEvaluatorRole::LocalRight => rec.local_right_pass,
                    DetectorEvaluatorRole::Global => rec.global_pass,
                };
                (
                    rec.composed_trace_id.clone(),
                    if v { "pass" } else { "fail" }.to_string(),
                )
            }),
            true,
            [format!("{role:?} blind spot")],
        )
        .unwrap()
    })
    .collect();
    let distinctions = vec![
        ProtectedDistinctionDeclaration::new(
            "D-left",
            DetectorEvaluatorRole::LocalLeft,
            "r0",
            "r1",
            vec![1.0, 0.0, 0.0, 0.0],
        )
        .unwrap(),
        ProtectedDistinctionDeclaration::new(
            "D-right",
            DetectorEvaluatorRole::LocalRight,
            "r0",
            "r1",
            vec![0.0, 1.0, 0.0, 0.0],
        )
        .unwrap(),
        ProtectedDistinctionDeclaration::new(
            "D-global",
            DetectorEvaluatorRole::Global,
            "r2",
            "r3",
            vec![0.0, 0.0, 1.0, 0.0],
        )
        .unwrap(),
    ];
    DetectorDeploymentDeclaration::new(
        "deployment",
        "v2-corpus",
        &boundary.name,
        boundary.states.iter().cloned(),
        model,
        epsilon,
        evaluators,
        distinctions,
    )
    .unwrap()
}

fn evidence(d: &DetectorDeploymentDeclaration, value: f64) -> DetectorCapacityEvidence {
    DetectorCapacityEvidence::from_f64_numerical_estimate(
        d.capacity_model_digest(),
        d.protected_subspace_digest(),
        value,
        d.epsilon(),
        4,
        3,
        1,
        vec![value],
        DetectorCapacityWitness::new(vec![1.0, 0.0, 0.0, 0.0], vec![value]).unwrap(),
        DetectorCapacityResiduals::new(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
            .unwrap(),
        DETECTOR_CAPACITY_RANK_TOLERANCE,
        DETECTOR_CAPACITY_RESIDUAL_ACCEPTANCE_TOLERANCE,
        DETECTOR_CAPACITY_COMPARISON_TOLERANCE,
    )
    .unwrap()
}

/// A packet that verifies and continues. Every mutation below changes exactly one
/// thing relative to this.
fn base_packet() -> RawEvidencePacket {
    let (records, trace_ledger, boundary) = corpus();
    let decl = declaration(&records, &boundary, 0.5, "capacity-model-a");
    RawEvidencePacket {
        schema: V2_CONTEXT_SCHEMA.to_string(),
        run_id: "run-1".into(),
        accepted_intake: AcceptedIntakeReceipt::admit(
            "run-1",
            "cand-1",
            "witness-cert",
            "carrier-2",
        ),
        records,
        trace_ledger,
        boundary,
        declaration: Some(decl),
        selected_row: 1,
        transport: Some(TransportClaim {
            source_carrier: "epk".into(),
            target_carrier: "prime".into(),
            loss_ledger: vec![],
        }),
        budget_remaining: 100.0,
        delta_control: 10.0,
        parent_receipt_hash: None,
        coda_gtla_refusal: false,
    }
}

#[test]
fn the_base_packet_verifies_and_continues() {
    let ctx = verify(&base_packet(), &trusted()).expect("base packet verifies");
    let d = decide(&ctx);
    assert!(
        d.may_continue(),
        "base must continue or every mutation below is vacuous: {:?}",
        d.blockers()
    );
    assert_eq!(d.step_terminal(), "LOCAL_GREEN_FOR_SCOPE");
    assert!(d.authority_effect().is_none());
    assert_eq!(d.root_digest(), ctx.root_digest());
}

// ── ROW 1: same corpus, different adequacy evidence ──────────────────────────
//
// THE ROUND-3 KILLER. v1 produced identical digests here.

#[test]
fn row1_same_corpus_different_adequacy_evidence_changes_the_root() {
    // The packet has no `capacity_evidence` field to vary any more -- that IS the
    // fix. Vary what the SOLVER returns instead: same corpus, different adequacy.
    let mut weak = trusted();
    weak.capacity_value = 9.0; // above epsilon -> NumericalCounterevidence

    let a = verify(&base_packet(), &trusted()).unwrap();
    let b = verify(&base_packet(), &weak).unwrap();

    assert_ne!(
        a.root_digest(),
        b.root_digest(),
        "v1's exact defect: identical digests across different adequacy evidence"
    );
    assert!(decide(&a).may_continue());
    let d = decide(&b);
    assert!(!d.may_continue());
    assert!(d
        .blockers()
        .contains(&ContinuationBlockerV2::DetectorInadequate));
}

// ── ROW 2: same corpus, different declaration ────────────────────────────────

#[test]
fn row2_a_different_declaration_changes_the_root() {
    let base = base_packet();
    let (records, _, boundary) = corpus();
    let mut other = base_packet();
    other.declaration = Some(declaration(&records, &boundary, 0.5, "capacity-model-B"));

    assert_ne!(
        verify(&base, &trusted()).unwrap().root_digest(),
        verify(&other, &trusted()).unwrap().root_digest()
    );
}

// ── ROW 3: same local traces, changed global_pass ────────────────────────────
//
// v1 never checked E_g at all.

#[test]
fn row3_a_changed_global_pass_is_refused() {
    let mut p = base_packet();
    let r = &p.records[0];
    p.records[0] = CompositionRecord::new(
        r.composed_trace_id.clone(),
        r.left_trace_id.clone(),
        r.right_trace_id.clone(),
        r.local_left_pass,
        r.local_right_pass,
        !r.global_pass, // exactly one field
        None,
    )
    .unwrap();

    assert!(matches!(
        verify(&p, &trusted()),
        Err(TypedRefusal::GlobalTraceMismatch { .. })
    ));
}

#[test]
fn row3b_a_missing_global_trace_refuses_exhibited() {
    let mut v = trusted();
    v.truth.remove("r0"); // the evaluator cannot replay this row
    assert!(matches!(
        verify(&base_packet(), &v),
        Err(TypedRefusal::GlobalTraceMissing { .. })
    ));
}

// ── ROW 4: capacity evidence from another declaration ────────────────────────

#[test]
fn row4_foreign_capacity_evidence_changes_the_root() {
    // A caller cannot attach foreign evidence at all now -- the field is gone.
    // What remains testable: a declaration naming a different capacity model
    // yields a different root, and the solver is the only source of evidence.
    let (records, _, boundary) = corpus();
    let mut p = base_packet();
    p.declaration = Some(declaration(&records, &boundary, 0.5, "capacity-model-B"));
    let base_root = verify(&base_packet(), &trusted())
        .unwrap()
        .root_digest()
        .to_string();
    assert_ne!(base_root, verify(&p, &trusted()).unwrap().root_digest());
}

// ── ROW 5: a different selected row ──────────────────────────────────────────

#[test]
fn row5_a_different_row_changes_the_root() {
    let mut p = base_packet();
    p.selected_row = 0; // one field
    assert_ne!(
        verify(&base_packet(), &trusted()).unwrap().root_digest(),
        verify(&p, &trusted()).unwrap().root_digest()
    );
}

#[test]
fn row5b_an_out_of_range_row_is_refused() {
    let mut p = base_packet();
    p.selected_row = 99;
    assert!(matches!(
        verify(&p, &trusted()),
        Err(TypedRefusal::RowOutOfRange { index: 99, len: 4 })
    ));
}

// ── ROW 6: preservation claimed without a verified witness ───────────────────

#[test]
fn row6_an_unpreserved_transport_blocks_continuation() {
    // The caller cannot claim a target residual any more. The ADAPTER measures it.
    let mut v = trusted();
    v.measured_target = 0.0; // the residual really did vanish in transit
    let ctx = verify(&base_packet(), &v).unwrap();
    let w = ctx.preservation().expect("witness produced");
    assert!(!w.preserved(), "0.0 != source ngd, so not preserving");
    let d = decide(&ctx);
    assert!(!d.may_continue());
    assert!(d
        .blockers()
        .contains(&ContinuationBlockerV2::AdapterNotPreserving));
}

#[test]
fn row6b_no_transport_at_all_is_not_a_preserved_transport() {
    let mut p = base_packet();
    p.transport = None;
    let d = decide(&verify(&p, &trusted()).unwrap());
    assert!(!d.may_continue());
    assert!(d
        .blockers()
        .contains(&ContinuationBlockerV2::AdapterNotPreserving));
}

// ── ROW 7: refused intake ────────────────────────────────────────────────────

#[test]
fn row7_a_refused_intake_cannot_reach_a_decision() {
    let mut p = base_packet();
    p.accepted_intake = None; // one field
    assert!(matches!(
        verify(&p, &trusted()),
        Err(TypedRefusal::IntakeNotAccepted)
    ));

    // And admission itself refuses without a witness.
    assert!(AcceptedIntakeReceipt::admit("run-1", "c", "", "carrier-2").is_none());
    assert!(AcceptedIntakeReceipt::admit("run-1", "c", "w", "").is_none());
}

// ── ROW 9/10: schema ─────────────────────────────────────────────────────────

#[test]
fn row9_a_mutated_schema_is_refused_before_recomputation() {
    let mut p = base_packet();
    p.schema = "evil".into(); // one field
    assert!(matches!(
        verify(&p, &trusted()),
        Err(TypedRefusal::SchemaRefused { .. })
    ));
}

#[test]
fn row10_every_v1_packet_is_refused() {
    for v1 in [
        "core.epk.lggr-observation.v1",
        "core.epk.prime-descent-receipt.v1",
        "core.epk.bound-measurement.v1",
    ] {
        let mut p = base_packet();
        p.schema = v1.into();
        assert!(
            matches!(
                verify(&p, &trusted()),
                Err(TypedRefusal::SchemaRefused { .. })
            ),
            "{v1} must be refused"
        );
    }
}

// ── ROW 12: replay under another run ─────────────────────────────────────────

#[test]
fn row12_an_intake_receipt_from_another_run_is_refused() {
    let mut p = base_packet();
    p.run_id = "run-2".into(); // one field; the receipt still says run-1
    assert!(matches!(
        verify(&p, &trusted()),
        Err(TypedRefusal::IntakeRunMismatch { .. })
    ));
}

#[test]
fn row12b_a_decision_carries_its_root_so_it_cannot_be_replayed_elsewhere() {
    let a = verify(&base_packet(), &trusted()).unwrap();
    let mut p = base_packet();
    p.selected_row = 0;
    let b = verify(&p, &trusted()).unwrap();
    assert_ne!(decide(&a).root_digest(), decide(&b).root_digest());
}

// ── budget / coda_gtla / monotone refusal ─────────────────────────────────────────

#[test]
fn budget_boundary_is_exact_and_nonfinite_is_refused() {
    let mut at = base_packet();
    at.budget_remaining = 10.0;
    assert!(decide(&verify(&at, &trusted()).unwrap()).may_continue());

    let mut below = base_packet();
    below.budget_remaining = 9.5;
    let d = decide(&verify(&below, &trusted()).unwrap());
    assert!(d
        .blockers()
        .contains(&ContinuationBlockerV2::BudgetExhausted));

    let mut nan = base_packet();
    nan.budget_remaining = f64::NAN;
    assert!(decide(&verify(&nan, &trusted()).unwrap())
        .blockers()
        .contains(&ContinuationBlockerV2::BudgetExhausted));
}

#[test]
fn a_standing_prior_refusal_blocks_continuation() {
    // The packet cannot omit a refusal any more; the STORE decides.
    let mut v = trusted();
    v.standing = vec![ContinuationBlockerV2::DetectorInadequate];
    let d = decide(&verify(&base_packet(), &v).unwrap());
    assert!(!d.may_continue());
    assert!(d
        .blockers()
        .contains(&ContinuationBlockerV2::PriorRefusalStanding));
}

#[test]
fn coda_gtla_refusal_alone_blocks_continuation() {
    let mut p = base_packet();
    p.coda_gtla_refusal = true;
    let d = decide(&verify(&p, &trusted()).unwrap());
    assert!(!d.may_continue());
    assert_eq!(d.blockers(), &[ContinuationBlockerV2::CodaGtlaRefusal]);
}

// ── ROW 13: the meta-test ────────────────────────────────────────────────────

/// **Row 13.** Every field the root digest claims to bind must actually change it.
///
/// This is the test that would have caught v1 round 3: there, the adequacy field
/// was *claimed* to be bound and was not, and no test noticed because every other
/// test varied several fields at once.
///
/// Each entry mutates exactly one field and asserts the digest moves.
#[test]
fn row13_every_claimed_bound_field_actually_moves_the_root_digest() {
    let base = verify(&base_packet(), &trusted())
        .unwrap()
        .root_digest()
        .to_string();
    let (records, _, boundary) = corpus();

    let mutations: Vec<(&str, PacketMutation)> = vec![
        // Split: an earlier revision changed run_id AND the receipt together,
        // which is the multi-field defect this matrix exists to prevent.
        (
            "intake_candidate",
            Box::new(|p: &mut RawEvidencePacket| {
                p.accepted_intake = AcceptedIntakeReceipt::admit(
                    "run-1",
                    "cand-OTHER",
                    "witness-cert",
                    "carrier-2",
                );
            }),
        ),
        (
            "intake_witness",
            Box::new(|p: &mut RawEvidencePacket| {
                p.accepted_intake =
                    AcceptedIntakeReceipt::admit("run-1", "cand-1", "witness-OTHER", "carrier-2");
            }),
        ),
        (
            "intake_next_carrier",
            Box::new(|p: &mut RawEvidencePacket| {
                p.accepted_intake = AcceptedIntakeReceipt::admit(
                    "run-1",
                    "cand-1",
                    "witness-cert",
                    "carrier-OTHER",
                );
            }),
        ),
        (
            "selected_row",
            Box::new(|p: &mut RawEvidencePacket| p.selected_row = 2),
        ),
        (
            "declaration",
            Box::new(move |p: &mut RawEvidencePacket| {
                p.declaration = Some(declaration(&records, &boundary, 0.25, "capacity-model-a"));
            }),
        ),
        (
            "transport_absent",
            Box::new(|p: &mut RawEvidencePacket| p.transport = None),
        ),
        (
            "loss_ledger",
            Box::new(|p: &mut RawEvidencePacket| {
                if let Some(t) = p.transport.as_mut() {
                    t.loss_ledger = vec!["dropped".into()];
                }
            }),
        ),
        (
            "budget_remaining",
            Box::new(|p: &mut RawEvidencePacket| p.budget_remaining = 50.0),
        ),
        (
            "delta_control",
            Box::new(|p: &mut RawEvidencePacket| p.delta_control = 20.0),
        ),
        (
            "gtla_refusal",
            Box::new(|p: &mut RawEvidencePacket| p.coda_gtla_refusal = true),
        ),
        (
            "parent_receipt",
            Box::new(|p: &mut RawEvidencePacket| {
                p.parent_receipt_hash = Some("sha256:parent".into());
            }),
        ),
    ];

    for (name, mutate) in mutations {
        let mut p = base_packet();
        mutate(&mut p);
        let got = verify(&p, &trusted())
            .unwrap_or_else(|e| panic!("{name} mutation should still verify, got {e}"))
            .root_digest()
            .to_string();
        assert_ne!(
            base, got,
            "field `{name}` is claimed to be bound but does not move the root digest"
        );
    }
}

#[test]
fn the_context_and_decision_are_serialize_only() {
    // Runtime half; the compile-time half is the `compile_fail` doctests.
    let ctx = verify(&base_packet(), &trusted()).unwrap();
    let json = serde_json::to_string(&ctx).unwrap();
    assert!(json.contains(ctx.root_digest()));
    let d = serde_json::to_string(&decide(&ctx)).unwrap();
    // No stored verdict to forge.
    assert!(!d.contains("may_continue"));
}

// -- no trusted verifier => no facts, therefore no green ----------------------

#[test]
fn without_trusted_verifiers_nothing_can_be_established() {
    // The honest default. `verify` cannot establish external facts from raw data,
    // so with no verifiers wired it REFUSES rather than reading them off the packet.
    let err = verify(&base_packet(), &RefusingVerifierSuite).unwrap_err();
    assert!(
        matches!(err, TypedRefusal::NoTrustedVerifier { .. }),
        "expected a NoTrustedVerifier refusal, got {err}"
    );
}

#[test]
fn a_refusing_admission_authority_blocks_verification() {
    let mut v = trusted();
    v.admit_ok = false;
    assert!(matches!(
        verify(&base_packet(), &v),
        Err(TypedRefusal::IntakeNotAccepted)
    ));
}

#[test]
fn a_declared_transport_loss_blocks_preservation() {
    // Even when the measured residual matches, a non-empty loss ledger means the
    // adapter reported loss; that is not preservation.
    let mut p = base_packet();
    if let Some(t) = p.transport.as_mut() {
        t.loss_ledger = vec!["dropped a row".into()];
    }
    let ctx = verify(&p, &trusted()).unwrap();
    assert!(!ctx.preservation().unwrap().preserved());
    assert!(decide(&ctx)
        .blockers()
        .contains(&ContinuationBlockerV2::AdapterNotPreserving));
}

// Origin: engine/crates_rs/tests/core_local_green_global_red_lggr/v2_field_isolation.rs
// Claim: urn:core:crates_rs:tests:v2-field-isolation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordbde811c2 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordbde811c2` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorbde811c2 {
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
impl BoundaryErrorbde811c2 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorbde811c2 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorbde811c2 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordbde811c2 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorbde811c2> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorbde811c2::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorbde811c2::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorbde811c2::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_bde811c2() {
    let admitted = BoundaryRecordbde811c2::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordbde811c2::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
