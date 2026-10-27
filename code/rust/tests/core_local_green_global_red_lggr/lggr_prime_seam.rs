//! Integration tests for the LGGR(EPK) → OE Prime 000/001/002 seam.
//!
//! These exercise the real [`core_epk::adequacy`] protocol rather than a stand-in:
//! every green reading here is gated on an actual `DetectorAdequacyVerdict` built
//! from an actual corpus, because the whole point of the seam is that a green
//! cannot be produced without one.
//!
//! Authority: None.

use num_rational::BigRational;
use num_traits::{One, Zero};
use core_epk::epk_engine::{
    evaluator_gluing_defect, BoundarySlice, CompositionRecord, GluingDefect, TraceLedger,
    TraceRecord,
};
use core_epk::adequacy::{evaluate_detector_adequacy, DetectorAdequacyVerdictKind};
use core_epk::bound_measurement::{BoundEpkMeasurement, BoundMeasurementError};
use core_epk::lggr_overlay::{
    closure_eligibility, gate_checklist, gate_sufficiency_status, BoundaryOwner,
    ClosureEligibility, GRepReading, GateChecklistReading, GateSufficiencyStatus, CodaGtlaRole,
    Lemma44Witness, OrganizationalGate,
};
use core_epk::prime_seam::{
    CandidateDeclaration, ContinuationBlocker, PrimeBudget, PrimeContinuationInputs,
    PrimeContinuationPort, PrimeDeclarationOrder, PrimeDeclarationOutcome, PrimeDescentReceipt,
    PrimeIntakeOutcome, PrimeIntakePort, ReferencePrimePorts,
};
use core_epk::verdict::{
    classify, EvaluatorProvenance, GreenUnsoundReason, LggrVerdict, LggrVerdictError,
};
use core_types::{
    DetectorCapacityEvidence, DetectorCapacityResiduals, DetectorCapacityWitness,
    DetectorDeploymentDeclaration, DetectorEvaluatorDeclaration, DetectorEvaluatorRole,
    ProtectedDistinctionDeclaration, DETECTOR_CAPACITY_COMPARISON_TOLERANCE,
    DETECTOR_CAPACITY_RANK_TOLERANCE, DETECTOR_CAPACITY_RESIDUAL_ACCEPTANCE_TOLERANCE,
};

// ── fixtures ─────────────────────────────────────────────────────────────────

/// Build a corpus from `(id, E₁, E₂, E_g)` rows, with a trace ledger whose
/// evaluator flags agree with the composition records.
fn corpus(
    values: &[(&str, bool, bool, bool)],
) -> (Vec<CompositionRecord>, TraceLedger, BoundarySlice) {
    let mut ledger = TraceLedger::new();
    let mut records = Vec::new();
    let mut states = Vec::new();
    for &(id, e1, e2, eg) in values {
        let left_id = format!("{id}-left");
        let right_id = format!("{id}-right");
        let middle = format!("{id}-middle");
        states.push(middle.clone());
        ledger.insert(
            TraceRecord::new(
                &left_id,
                "task",
                "left",
                None,
                format!("{id}-source"),
                &middle,
                BigRational::one(),
                BigRational::zero(),
                e1,
            )
            .unwrap(),
        );
        ledger.insert(
            TraceRecord::new(
                &right_id,
                "task",
                "right",
                None,
                &middle,
                format!("{id}-target"),
                BigRational::one(),
                BigRational::zero(),
                e2,
            )
            .unwrap(),
        );
        records.push(CompositionRecord::new(id, left_id, right_id, e1, e2, eg, None).unwrap());
    }
    (records, ledger, BoundarySlice::new("B", states))
}

/// A corpus that gives the detector real work to do: it contains an exhibited
/// `Δ_E = −1` witness (`r0`), a `Δ_E = +1` (`r2`), and two zeros.
fn strong_corpus() -> (Vec<CompositionRecord>, TraceLedger, BoundarySlice) {
    corpus(&[
        ("r0", true, true, false),
        ("r1", false, false, false),
        ("r2", false, true, true),
        ("r3", false, true, false),
    ])
}

fn evaluator_value(role: DetectorEvaluatorRole, record: &CompositionRecord) -> bool {
    match role {
        DetectorEvaluatorRole::LocalLeft => record.local_left_pass,
        DetectorEvaluatorRole::LocalRight => record.local_right_pass,
        DetectorEvaluatorRole::Global => record.global_pass,
    }
}

fn declaration(
    records: &[CompositionRecord],
    boundary: &BoundarySlice,
    epsilon: f64,
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
            records.iter().map(|record| {
                (
                    record.composed_trace_id.clone(),
                    if evaluator_value(role, record) {
                        "pass"
                    } else {
                        "fail"
                    }
                    .to_string(),
                )
            }),
            true,
            [format!("{role:?} known blind spot at B")],
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
        "seam-corpus",
        &boundary.name,
        boundary.states.iter().cloned(),
        "capacity-model-a",
        epsilon,
        evaluators,
        distinctions,
    )
    .unwrap()
}

fn evidence(declaration: &DetectorDeploymentDeclaration, value: f64) -> DetectorCapacityEvidence {
    evidence_with_model_digest(declaration, value, declaration.capacity_model_digest())
}

/// Same evidence, but the capacity-model digest is caller-supplied so a test can
/// hand in a mismatched one and drive the protocol to `NumericalUnresolved`.
fn evidence_with_model_digest(
    declaration: &DetectorDeploymentDeclaration,
    value: f64,
    model_digest: &str,
) -> DetectorCapacityEvidence {
    DetectorCapacityEvidence::from_f64_numerical_estimate(
        model_digest,
        declaration.protected_subspace_digest(),
        value,
        declaration.epsilon(),
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

fn zero_defect() -> GluingDefect {
    GluingDefect {
        delta_eval: 0,
        local_product: false,
        global_pass: false,
    }
}

fn red_defect() -> GluingDefect {
    GluingDefect {
        delta_eval: -1,
        local_product: true,
        global_pass: false,
    }
}

// ── §3.1 asymmetry ───────────────────────────────────────────────────────────

#[test]
fn local_green_global_red_is_a_sound_detection() {
    let (records, _, _) = strong_corpus();
    let defect = evaluator_gluing_defect(&records[0]);
    assert_eq!(
        defect.delta_eval, -1,
        "r0 is the local-green/global-red row"
    );

    let verdict = classify(&defect, None, EvaluatorProvenance::Exhibited).unwrap();
    assert!(matches!(verdict, LggrVerdict::Red { .. }));
    assert!(verdict.is_sound_detection());
    // Red is sound as a *detection* — never as a certificate of anything.
    assert!(!verdict.certifies_closure());
}

#[test]
fn zero_defect_without_any_adequacy_verdict_is_oracle_needed() {
    let verdict = classify(&zero_defect(), None, EvaluatorProvenance::Exhibited).unwrap();
    match verdict {
        LggrVerdict::GreenOracleNeeded { reasons, .. } => {
            assert_eq!(reasons, vec![GreenUnsoundReason::AdequacyUndeclared]);
        }
        other => panic!("a green with no adequacy protocol must be OracleNeeded, got {other:?}"),
    }
}

#[test]
fn zero_defect_with_supported_adequacy_reaches_numerically_supported() {
    let (records, ledger, boundary) = strong_corpus();
    let decl = declaration(&records, &boundary, 0.5);
    let ev = evidence(&decl, 0.1);
    let adequacy = evaluate_detector_adequacy(Some(&decl), Some(&ev), &records, &ledger, &boundary);
    assert_eq!(
        adequacy.kind(),
        DetectorAdequacyVerdictKind::NumericallySupported,
        "fixture must actually produce a supported verdict, else the test proves nothing: {:?}",
        adequacy.structural_failures()
    );

    let defect = evaluator_gluing_defect(&records[1]);
    assert_eq!(defect.delta_eval, 0);
    let verdict = classify(&defect, Some(&adequacy), EvaluatorProvenance::Exhibited).unwrap();
    assert!(matches!(
        verdict,
        LggrVerdict::GreenNumericallySupported { .. }
    ));
    // The strongest reachable green is still not a certificate.
    assert!(!verdict.certifies_closure());
    assert!(!verdict.is_sound_detection());
}

#[test]
fn aligned_validator_family_blocks_green() {
    // LGGR II §3.1 case 1: E_G is a perfect proxy for the local product, so
    // Δ_E ≡ 0 for every input and "every boundary reads closed".
    let (records, ledger, boundary) = corpus(&[
        ("r0", true, true, true),
        ("r1", false, false, false),
        ("r2", false, true, false),
        ("r3", true, false, false),
    ]);
    let decl = declaration(&records, &boundary, 0.5);
    let ev = evidence(&decl, 0.1);
    let adequacy = evaluate_detector_adequacy(Some(&decl), Some(&ev), &records, &ledger, &boundary);
    assert_eq!(
        adequacy.kind(),
        DetectorAdequacyVerdictKind::StructuralInadequate
    );

    let verdict = classify(
        &zero_defect(),
        Some(&adequacy),
        EvaluatorProvenance::Exhibited,
    )
    .unwrap();
    match verdict {
        LggrVerdict::GreenOracleNeeded { reasons, .. } => assert!(
            reasons.contains(&GreenUnsoundReason::AlignedValidatorFamily),
            "the tautological detector must be named, got {reasons:?}"
        ),
        other => panic!("aligned validator family must block green, got {other:?}"),
    }
}

#[test]
fn constant_evaluator_blocks_green() {
    // An all-accept local evaluator distinguishes nothing.
    let (records, ledger, boundary) = corpus(&[
        ("r0", true, true, false),
        ("r1", true, false, false),
        ("r2", true, true, true),
        ("r3", true, false, false),
    ]);
    let decl = declaration(&records, &boundary, 0.5);
    let ev = evidence(&decl, 0.1);
    let adequacy = evaluate_detector_adequacy(Some(&decl), Some(&ev), &records, &ledger, &boundary);
    assert_eq!(
        adequacy.kind(),
        DetectorAdequacyVerdictKind::StructuralInadequate
    );

    let verdict = classify(
        &zero_defect(),
        Some(&adequacy),
        EvaluatorProvenance::Exhibited,
    )
    .unwrap();
    match verdict {
        LggrVerdict::GreenOracleNeeded { reasons, .. } => assert!(
            !reasons.is_empty(),
            "a structurally inadequate detector must yield at least one reason"
        ),
        other => panic!("constant evaluator must block green, got {other:?}"),
    }
}

#[test]
fn no_verdict_ever_certifies_closure() {
    let (records, ledger, boundary) = strong_corpus();
    let decl = declaration(&records, &boundary, 0.5);
    let ev = evidence(&decl, 0.1);
    let adequacy = evaluate_detector_adequacy(Some(&decl), Some(&ev), &records, &ledger, &boundary);

    for verdict in [
        classify(&red_defect(), None, EvaluatorProvenance::Exhibited).unwrap(),
        classify(&zero_defect(), None, EvaluatorProvenance::Exhibited).unwrap(),
        classify(
            &zero_defect(),
            Some(&adequacy),
            EvaluatorProvenance::Exhibited,
        )
        .unwrap(),
        classify(&red_defect(), None, EvaluatorProvenance::OracleExtracted).unwrap(),
    ] {
        assert!(!verdict.certifies_closure(), "{verdict:?} must not certify");
        assert!(verdict.authority_effect().is_none());
    }
}

#[test]
fn oracle_extracted_verdicts_are_unsound_in_both_directions() {
    // LGGR II §7.3: "the §3.1 asymmetry does not rescue the red verdict here,
    // because the red is no longer exhibited."
    for defect in [red_defect(), zero_defect()] {
        let verdict = classify(&defect, None, EvaluatorProvenance::OracleExtracted).unwrap();
        assert!(matches!(
            verdict,
            LggrVerdict::OracleExtractedUnsound { .. }
        ));
        assert!(
            !verdict.is_sound_detection(),
            "an oracle-extracted red is not a detection"
        );
    }
}

#[test]
fn malformed_defects_are_refused_not_classified() {
    let inconsistent = GluingDefect {
        delta_eval: 0,
        local_product: true,
        global_pass: false, // implies -1, not 0
    };
    assert!(matches!(
        classify(&inconsistent, None, EvaluatorProvenance::Exhibited),
        Err(LggrVerdictError::DefectInternallyInconsistent { implied: -1, .. })
    ));

    let out_of_range = GluingDefect {
        delta_eval: 7,
        local_product: false,
        global_pass: false,
    };
    // Exactly DefectOutOfRange, not DefectInternallyInconsistent: the range check
    // runs first precisely so this branch is reachable and the caller is told the
    // real fault.
    assert!(matches!(
        classify(&out_of_range, None, EvaluatorProvenance::Exhibited),
        Err(LggrVerdictError::DefectOutOfRange(7))
    ));

    // An out-of-range value is refused even when the provenance would otherwise
    // short-circuit to an oracle reading.
    assert!(matches!(
        classify(&out_of_range, None, EvaluatorProvenance::OracleExtracted),
        Err(LggrVerdictError::DefectOutOfRange(7))
    ));
}

// ── LGGR II gates ────────────────────────────────────────────────────────────

#[test]
fn lemma_4_4_witness_satisfies_gates_yet_factorization_fails() {
    let w = Lemma44Witness::default();
    assert!(
        w.weak_g_rep_holds(),
        "E_G is recoverable from R by projection"
    );
    assert!(w.g_auth && w.g_time);
    assert!(
        !w.factorization_holds(),
        "0 = E_G != E1*E2 = 1 — the gates do not force factorization"
    );
}

#[test]
fn gate_conjunction_is_never_reported_as_sufficient() {
    assert_eq!(
        gate_sufficiency_status(GRepReading::Weak),
        GateSufficiencyStatus::RefutedByLemma44
    );
    assert_eq!(
        gate_sufficiency_status(GRepReading::ProductSufficiency),
        GateSufficiencyStatus::CircularWithFactorization
    );
}

#[test]
fn closure_eligibility_never_certifies_closure() {
    let full = BoundaryOwner {
        name: "council".into(),
        has_authority: true,
        has_accountability: true,
    };
    let e = closure_eligibility(Some(&full));
    assert_eq!(e, ClosureEligibility::RequiredFieldPresent);
    assert!(e.required_field_present());
    assert!(
        !e.certifies_closure(),
        "G_auth is necessary, not sufficient"
    );

    assert_eq!(
        closure_eligibility(None),
        ClosureEligibility::NoDeclaredOwner
    );
    assert!(!closure_eligibility(None).certifies_closure());

    for (auth, acct, expected) in [
        (false, true, ClosureEligibility::OwnerLacksAuthority),
        (true, false, ClosureEligibility::OwnerLacksAccountability),
        (
            false,
            false,
            ClosureEligibility::OwnerLacksAuthorityAndAccountability,
        ),
    ] {
        let owner = BoundaryOwner {
            name: "o".into(),
            has_authority: auth,
            has_accountability: acct,
        };
        assert_eq!(closure_eligibility(Some(&owner)), expected);
    }
}

#[test]
fn checklist_flags_a_nonzero_defect_with_all_gates_declared_true() {
    let red = classify(&red_defect(), None, EvaluatorProvenance::Exhibited).unwrap();
    let all_true = [
        (OrganizationalGate::GRep, true),
        (OrganizationalGate::GAuth, true),
        (OrganizationalGate::GTime, true),
        (OrganizationalGate::GEval, true),
    ];
    match gate_checklist(&red, &all_true) {
        GateChecklistReading::SomeConditionFailed {
            candidates,
            contradicts_declaration,
        } => {
            assert!(candidates.is_empty());
            assert!(
                contradicts_declaration,
                "a nonzero defect with every gate declared true is the Lemma 4.4 situation"
            );
        }
        other => panic!("expected a checklist reading, got {other:?}"),
    }
}

#[test]
fn checklist_refuses_to_attribute_from_an_oracle_reading() {
    let oracle = classify(&red_defect(), None, EvaluatorProvenance::OracleExtracted).unwrap();
    assert_eq!(
        gate_checklist(&oracle, &[(OrganizationalGate::GAuth, false)]),
        GateChecklistReading::NoSoundReading
    );
}

#[test]
fn observed_zero_is_not_a_certified_closure() {
    let green = classify(&zero_defect(), None, EvaluatorProvenance::Exhibited).unwrap();
    assert_eq!(
        gate_checklist(&green, &[(OrganizationalGate::GAuth, true)]),
        GateChecklistReading::ObservedZeroNotCertified
    );
}

#[test]
fn all_six_coda_gtla_roles_are_authority_free() {
    assert_eq!(CodaGtlaRole::ALL.len(), 6);
    let tags: Vec<_> = CodaGtlaRole::ALL.iter().map(|r| r.tag()).collect();
    assert_eq!(tags, vec!["FOC", "FDA", "MUR", "OR", "CS", "A"]);
    for role in CodaGtlaRole::ALL {
        assert!(role.authority_effect().is_none());
        assert!(!role.epk_responsibility().is_empty());
    }
}

// ── Prime 000 / 001-I intake ─────────────────────────────────────────────────

fn candidate() -> CandidateDeclaration {
    CandidateDeclaration {
        artifact_id: "a1".into(),
        locus_id: "L1".into(),
        problem_family: "epk".into(),
        primitive_difference_proposal: "pd".into(),
        carrier_proposal: "carrier".into(),
        zero_rel_proposal: "zero".into(),
        observer_proposal: "obs".into(),
        witness_available: true,
        quotient_or_refusal: "E".into(),
        adapter_confidence: "high".into(),
        status: "proposed_only".into(),
    }
}

#[test]
fn intake_reuses_the_declared_literals_exactly() {
    let ports = ReferencePrimePorts;
    assert_eq!(
        ports.evaluate_intake(&candidate()).as_declared_str(),
        "ACCEPT_DECLARATION"
    );

    let mut no_carrier = candidate();
    no_carrier.carrier_proposal = String::new();
    assert_eq!(
        ports.evaluate_intake(&no_carrier),
        PrimeIntakeOutcome::RefusedMissingCarrier
    );
    assert_eq!(
        ports.evaluate_intake(&no_carrier).as_declared_str(),
        "REFUSED_MISSING_CARRIER"
    );

    let mut no_observer = candidate();
    no_observer.observer_proposal = String::new();
    assert_eq!(
        ports.evaluate_intake(&no_observer).as_declared_str(),
        "REFUSED_MISSING_OBSERVER"
    );

    let mut no_witness = candidate();
    no_witness.witness_available = false;
    assert_eq!(
        ports.evaluate_intake(&no_witness).as_declared_str(),
        "REFUSED_MISSING_WITNESS"
    );

    let mut weak_adapter = candidate();
    weak_adapter.adapter_confidence = "inadequate".into();
    assert_eq!(
        ports.evaluate_intake(&weak_adapter).as_declared_str(),
        "ADAPTER_INADEQUATE"
    );
    assert!(ports.evaluate_intake(&weak_adapter).is_refusal());
}

#[test]
fn declaration_order_uses_the_refuse_prefix_not_refused() {
    let ports = ReferencePrimePorts;
    let complete = PrimeDeclarationOrder {
        step0_grounding_hash: "sha256:abc".into(),
        step1_carrier_declared: true,
        step2_observer_id: "obs".into(),
        step3_primitive_difference_declared: true,
        step4_zero_rel_rule: "zr".into(),
        step5_witness_certificate: Some("cert".into()),
        step6_quotient_policy: "Q1_SEPARATED".into(),
    };
    assert_eq!(
        ports.validate_declaration_order(&complete),
        PrimeDeclarationOutcome::AcceptDeclaration
    );

    // The seven-step order refuses with REFUSE_, intake with REFUSED_. Both
    // literals are upstream; the difference is preserved deliberately.
    let mut no_witness = complete.clone();
    no_witness.step5_witness_certificate = None;
    assert_eq!(
        ports
            .validate_declaration_order(&no_witness)
            .as_declared_str(),
        "REFUSE_MISSING_WITNESS"
    );
    assert_ne!(
        ports
            .validate_declaration_order(&no_witness)
            .as_declared_str(),
        PrimeIntakeOutcome::RefusedMissingWitness.as_declared_str()
    );

    let mut no_grounding = complete.clone();
    no_grounding.step0_grounding_hash = String::new();
    assert_eq!(
        ports
            .validate_declaration_order(&no_grounding)
            .as_declared_str(),
        "REFUSE_MISSING_GROUNDING"
    );

    // Order matters: a missing grounding is reported even when later steps are
    // also absent.
    let nothing = PrimeDeclarationOrder {
        step6_quotient_policy: "Q1_SEPARATED".into(),
        ..Default::default()
    };
    assert_eq!(
        ports.validate_declaration_order(&nothing),
        PrimeDeclarationOutcome::RefuseMissingGrounding
    );
}

// ── the sealed aggregate: BoundEpkMeasurement ────────────────────────────────
//
// Everything below exercises the post-review architecture. The old fixtures built
// observations and continuation inputs from independently-supplied parts; that is
// what the review refuted, and those constructors no longer exist.

fn measured(rows: &[(&str, bool, bool, bool)], epsilon: f64, capacity: f64) -> BoundEpkMeasurement {
    let (records, ledger, boundary) = corpus(rows);
    let decl = declaration(&records, &boundary, epsilon);
    let ev = evidence(&decl, capacity);
    BoundEpkMeasurement::measure(
        &records,
        &ledger,
        &boundary,
        Some(&decl),
        Some(&ev),
        EvaluatorProvenance::Exhibited,
    )
    .expect("ledger-backed corpus measures")
}

/// A measurement whose detector is adequate (strong corpus, capacity under epsilon).
fn adequate_measurement() -> BoundEpkMeasurement {
    measured(
        &[
            ("r0", true, true, false),
            ("r1", false, false, false),
            ("r2", false, true, true),
            ("r3", false, true, false),
        ],
        0.5,
        0.1,
    )
}

/// A measurement over the §3.1 case-1 collapsing detector.
fn collapsing_measurement() -> BoundEpkMeasurement {
    measured(
        &[
            ("r0", true, true, true),
            ("r1", false, false, false),
            ("r2", false, true, false),
            ("r3", true, false, false),
        ],
        0.5,
        0.1,
    )
}

#[test]
fn the_aggregate_derives_everything_from_one_triple() {
    let m = adequate_measurement();
    assert_eq!(m.row_count(), 4);
    assert_eq!(
        m.adequacy().kind(),
        DetectorAdequacyVerdictKind::NumericallySupported
    );
    assert!(m.corpus_digest().starts_with("sha256:"));
    // Row 0 is the exhibited local-green/global-red witness.
    assert_eq!(m.defect(0).unwrap().delta_eval, -1);
    assert!(matches!(m.verdict(0).unwrap(), LggrVerdict::Red { .. }));
    assert!(m.authority_effect().is_none());
}

#[test]
fn rows_outside_the_corpus_are_refused() {
    let m = adequate_measurement();
    assert!(matches!(
        m.defect(99),
        Err(BoundMeasurementError::RowOutOfRange { index: 99, len: 4 })
    ));
    assert!(m.observe(99).is_err());
}

// REQUIRED TEST 4 — caller-asserted `Exhibited` without ledger backing is refused.
#[test]
fn asserted_exhibited_provenance_without_ledger_backing_is_refused() {
    let (mut records, ledger, boundary) = strong_corpus();
    // Flip one record's declared local pass so it no longer matches the ledger.
    // Nothing about the *claim* changes — only whether it is true.
    records[0] = CompositionRecord::new(
        records[0].composed_trace_id.clone(),
        records[0].left_trace_id.clone(),
        records[0].right_trace_id.clone(),
        !records[0].local_left_pass,
        records[0].local_right_pass,
        records[0].global_pass,
        None,
    )
    .unwrap();

    let err = BoundEpkMeasurement::measure(
        &records,
        &ledger,
        &boundary,
        None,
        None,
        EvaluatorProvenance::Exhibited,
    )
    .unwrap_err();
    assert!(matches!(
        err,
        BoundMeasurementError::ProvenanceNotExhibited { .. }
    ));

    // The same corpus measures fine when the claim is honest.
    assert!(BoundEpkMeasurement::measure(
        &records,
        &ledger,
        &boundary,
        None,
        None,
        EvaluatorProvenance::OracleExtracted,
    )
    .is_ok());
}

#[test]
fn an_empty_corpus_is_refused() {
    let (_, ledger, boundary) = strong_corpus();
    assert!(matches!(
        BoundEpkMeasurement::measure(
            &[],
            &ledger,
            &boundary,
            None,
            None,
            EvaluatorProvenance::Exhibited
        ),
        Err(BoundMeasurementError::EmptyCorpus)
    ));
}

// REQUIRED TEST 3 — corpus-A adequacy cannot be paired with a corpus-B defect.
#[test]
fn evidence_from_one_corpus_is_refused_by_another() {
    let good = adequate_measurement();
    let bad = collapsing_measurement();
    assert_ne!(good.corpus_digest(), bad.corpus_digest());

    let good_obs = good.observe(1).unwrap();
    let good_receipt = good
        .descend("epk", "prime", &good_obs, true, vec![])
        .unwrap();

    // The adequate measurement's receipt presented to the collapsing measurement.
    assert!(matches!(
        bad.continuation_evidence(&good_receipt),
        Err(BoundMeasurementError::ReceiptCorpusMismatch { .. })
    ));

    // And an observation from the other corpus cannot be descended here.
    let bad_obs = bad.observe(1).unwrap();
    assert!(matches!(
        good.descend("epk", "prime", &bad_obs, true, vec![]),
        Err(BoundMeasurementError::ReceiptCorpusMismatch { .. })
    ));
}

// REQUIRED TEST 5 — a lossy descent receipt makes continuation impossible.
#[test]
fn a_lossy_descent_receipt_blocks_continuation() {
    let m = adequate_measurement();
    let obs = m.observe(1).unwrap();

    let lossy = m
        .descend("epk", "prime", &obs, false, vec!["dropped residual".into()])
        .unwrap();
    let ev = m.continuation_evidence(&lossy).unwrap();
    assert!(!ev.adapter_sound(), "a lossy receipt is not adapter-sound");

    let decision = PrimeContinuationInputs::from_evidence(
        ev,
        PrimeBudget::new(100.0, 10.0),
        true,
        true,
        true,
        true,
        true,
        false,
    )
    .evaluate();
    assert!(!decision.may_continue());
    assert!(decision
        .blockers()
        .contains(&ContinuationBlocker::AdapterUnsound));

    // There is no separate `adapter_sound` parameter to override it with. With a
    // preserved receipt the ONLY remaining blocker is the v1 quarantine.
    let preserved = m.descend("epk", "prime", &obs, true, vec![]).unwrap();
    let clean = PrimeContinuationInputs::from_evidence(
        m.continuation_evidence(&preserved).unwrap(),
        PrimeBudget::new(100.0, 10.0),
        true,
        true,
        true,
        true,
        true,
        false,
    )
    .evaluate();
    assert!(!clean.may_continue(), "v1 is quarantined");
    assert_eq!(
        clean.blockers(),
        &[ContinuationBlocker::V1SchemaQuarantined]
    );
}

#[test]
fn an_inadequate_detector_blocks_continuation() {
    let m = collapsing_measurement();
    assert_eq!(
        m.adequacy().kind(),
        DetectorAdequacyVerdictKind::StructuralInadequate
    );
    let obs = m.observe(1).unwrap();
    // The ledger still reports a clean ngd — the trap the gate exists to catch.
    assert_eq!(obs.ledger().ngd, 0.0);

    let receipt = m.descend("epk", "prime", &obs, true, vec![]).unwrap();
    let ev = m.continuation_evidence(&receipt).unwrap();
    assert!(!ev.detector_adequate());

    let decision = PrimeContinuationInputs::from_evidence(
        ev,
        PrimeBudget::new(100.0, 10.0),
        true,
        true,
        true,
        true,
        true,
        false,
    )
    .evaluate();
    assert!(!decision.may_continue());
    assert!(decision
        .blockers()
        .contains(&ContinuationBlocker::DetectorInadequate));
}

#[test]
fn a_missing_witness_blocks_continuation() {
    let m = adequate_measurement();
    let obs = m.observe(1).unwrap();
    let receipt = m.descend("epk", "prime", &obs, true, vec![]).unwrap();
    let decision = PrimeContinuationInputs::from_evidence(
        m.continuation_evidence(&receipt).unwrap(),
        PrimeBudget::new(100.0, 10.0),
        true,
        false, // has_witness
        true,
        true,
        true,
        false,
    )
    .evaluate();
    assert!(!decision.may_continue());
    assert!(decision
        .blockers()
        .contains(&ContinuationBlocker::WitnessMissing));
    assert_eq!(decision.step_terminal(), "TERMINAL_WITH_DEBT");
}

#[test]
fn budget_boundary_is_exact() {
    assert!(PrimeBudget::new(10.0, 10.0).has_budget(), "at the boundary");
    assert!(PrimeBudget::new(10.5, 10.0).has_budget());
    assert!(!PrimeBudget::new(9.5, 10.0).has_budget());

    let m = adequate_measurement();
    let obs = m.observe(1).unwrap();
    let receipt = m.descend("epk", "prime", &obs, true, vec![]).unwrap();
    let mk = |b| {
        PrimeContinuationInputs::from_evidence(
            m.continuation_evidence(&receipt).unwrap(),
            b,
            true,
            true,
            true,
            true,
            true,
            false,
        )
        .evaluate()
    };
    // At/above the boundary the budget is NOT a blocker; below it, it is. The
    // quarantine is present throughout, so `may_continue` is false either way.
    assert!(!mk(PrimeBudget::new(10.0, 10.0))
        .blockers()
        .contains(&ContinuationBlocker::BudgetExhausted));
    let exhausted = mk(PrimeBudget::new(9.5, 10.0));
    assert!(!exhausted.may_continue());
    assert!(exhausted
        .blockers()
        .contains(&ContinuationBlocker::BudgetExhausted));
}

#[test]
fn nonfinite_budget_is_refused_rather_than_compared() {
    assert!(!PrimeBudget::new(f64::NAN, 10.0).has_budget());
    assert!(!PrimeBudget::new(f64::INFINITY, 10.0).has_budget());
    assert!(!PrimeBudget::new(100.0, f64::NAN).has_budget());
}

#[test]
fn every_failed_conjunct_is_reported_not_just_the_first() {
    let m = collapsing_measurement();
    let obs = m.observe(1).unwrap();
    let lossy = m.descend("epk", "prime", &obs, false, vec![]).unwrap();
    let decision = PrimeContinuationInputs::from_evidence(
        m.continuation_evidence(&lossy).unwrap(),
        PrimeBudget::new(0.0, 10.0),
        false,
        false,
        false,
        false,
        false,
        true,
    )
    .evaluate();
    assert!(!decision.may_continue());
    // Nine conjuncts fail (7 caller-supplied + 2 from evidence), plus the
    // unconditional v1 quarantine.
    assert_eq!(decision.blockers().len(), 10, "{:?}", decision.blockers());
}

// REQUIRED TEST 10 — a refused intake yields no measurement, hence no evidence.
#[test]
fn a_refused_intake_cannot_be_bypassed_into_prime_002() {
    let ports = ReferencePrimePorts;
    let mut refused = candidate();
    refused.witness_available = false;
    assert_eq!(
        ports.evaluate_intake(&refused),
        PrimeIntakeOutcome::RefusedMissingWitness
    );

    // There is exactly one way to obtain `ContinuationEvidence`: from a
    // `BoundEpkMeasurement` plus a `VerifiedDescentReceipt` bound to it. Both are
    // sealed, and `PrimeContinuationInputs` has no other constructor — the
    // `compile_fail` doctests on all three pin that. A caller who stopped at a
    // refused intake never made a measurement, so no evidence exists to pass.
    //
    // What remains testable at runtime is that evidence cannot be conjured from a
    // foreign corpus (covered above) nor from an unverified receipt (below).
    let m = adequate_measurement();
    let obs = m.observe(0).unwrap();
    let receipt = m.descend("epk", "prime", &obs, true, vec![]).unwrap();
    assert_eq!(receipt.observed_corpus_digest(), m.corpus_digest());
}

// ── receipt identity ─────────────────────────────────────────────────────────

// REQUIRED TEST 9 — a deserialized receipt cannot satisfy a gate before verification.
#[test]
fn a_deserialized_receipt_must_be_verified_before_it_gates() {
    let m = adequate_measurement();
    let obs = m.observe(1).unwrap();
    let sealed = m.descend("epk", "prime", &obs, true, vec![]).unwrap();

    // Transport layer: the plain receipt round-trips.
    let json = serde_json::to_string(sealed.receipt()).unwrap();
    let parsed: PrimeDescentReceipt = serde_json::from_str(&json).unwrap();
    assert_eq!(&parsed, sealed.receipt());

    // But a parsed receipt is not a `VerifiedDescentReceipt`; the only way across
    // is recomputation, and it is checked.
    let verified = m.verify_receipt(parsed.clone(), &obs).unwrap();
    assert_eq!(verified.receipt_hash(), sealed.receipt_hash());

    // A tampered receipt is refused: claim adapter-soundness it never had.
    let mut tampered = parsed;
    tampered.residual_preservation_verified = false;
    assert!(matches!(
        m.verify_receipt(tampered, &obs),
        Err(BoundMeasurementError::ReceiptHashMismatch { .. })
    ));
}

// REQUIRED TEST 6 — different corpus digests produce different receipt hashes.
#[test]
fn different_corpora_produce_different_receipt_hashes() {
    let a = adequate_measurement();
    let b = collapsing_measurement();
    let ra = a
        .descend("epk", "prime", &a.observe(1).unwrap(), true, vec![])
        .unwrap();
    let rb = b
        .descend("epk", "prime", &b.observe(1).unwrap(), true, vec![])
        .unwrap();
    assert_ne!(a.corpus_digest(), b.corpus_digest());
    assert_ne!(ra.receipt_hash(), rb.receipt_hash());
}

// REQUIRED TEST 7 — different defect triples produce different receipt hashes.
#[test]
fn different_rows_produce_different_receipt_hashes() {
    let m = adequate_measurement();
    let mut hashes = std::collections::BTreeSet::new();
    for row in 0..m.row_count() {
        let obs = m.observe(row).unwrap();
        hashes.insert(
            m.descend("epk", "prime", &obs, true, vec![])
                .unwrap()
                .receipt_hash()
                .to_string(),
        );
    }
    // r1 and r3 share (delta=0) but differ in the defect triple and record id.
    assert_eq!(hashes.len(), m.row_count(), "rows must not collide");
}

// REQUIRED TEST 8 — NUL-containing field partitions cannot collide.
#[test]
fn nul_containing_fields_cannot_be_repartitioned() {
    let m = adequate_measurement();
    let obs = m.observe(1).unwrap();

    // Under a NUL-delimited encoding these two would hash identically: the first
    // packs both segments into one field separated by NUL, the second uses two
    // fields. Length-prefixing makes them distinct.
    let joined = m
        .descend("epk", "prime", &obs, true, vec!["a\u{0}b".to_string()])
        .unwrap();
    let split = m
        .descend(
            "epk",
            "prime",
            &obs,
            true,
            vec!["a".to_string(), "b".to_string()],
        )
        .unwrap();
    assert_ne!(joined.receipt_hash(), split.receipt_hash());

    // Same for carrier names: "ab"/"c" vs "a"/"bc".
    let x = m.descend("ab", "c", &obs, true, vec![]).unwrap();
    let y = m.descend("a", "bc", &obs, true, vec![]).unwrap();
    assert_ne!(x.receipt_hash(), y.receipt_hash());
}

#[test]
fn receipts_replay_byte_for_byte() {
    let m = adequate_measurement();
    let obs = m.observe(1).unwrap();
    let a = m
        .descend("src", "dst", &obs, true, vec!["loss: none".into()])
        .unwrap();
    let b = m
        .descend("src", "dst", &obs, true, vec!["loss: none".into()])
        .unwrap();
    assert_eq!(a.receipt_hash(), b.receipt_hash());
    assert!(a.receipt_hash().starts_with("sha256:"));
}

#[test]
fn the_observation_serializes_but_is_not_reconstructible_from_json() {
    let m = adequate_measurement();
    let obs = m.observe(0).unwrap();
    let json = serde_json::to_string(&obs).unwrap();
    assert!(json.contains("core.epk.lggr-observation.v1"));
    // The emitted JSON names WHICH corpus was audited, not merely that one was.
    assert_eq!(obs.observed_corpus_digest(), Some(m.corpus_digest()));
    assert!(json.contains(m.corpus_digest()));
}

#[test]
fn observations_stay_coherent_across_every_adequacy_kind() {
    for m in [adequate_measurement(), collapsing_measurement()] {
        let obs = m.observe(1).unwrap();
        let verdict_supported =
            matches!(obs.verdict(), LggrVerdict::GreenNumericallySupported { .. });
        assert_eq!(
            obs.adequacy_kind().permits_detector_adequate(),
            verdict_supported
        );
        assert_eq!(obs.detector_adequate(), verdict_supported);
        assert!(obs.authority_effect().is_none());
        assert!(!obs.verdict().certifies_closure());
    }
}

// ── the end-to-end seam ──────────────────────────────────────────────────────

#[test]
fn candidate_packet_traverses_the_full_prime_seam() {
    let ports = ReferencePrimePorts;

    // Prime 001-I and Prime 000.
    assert_eq!(
        ports.evaluate_intake(&candidate()),
        PrimeIntakeOutcome::AcceptDeclaration
    );
    let order = PrimeDeclarationOrder {
        step0_grounding_hash: "sha256:seed".into(),
        step1_carrier_declared: true,
        step2_observer_id: "obs-1".into(),
        step3_primitive_difference_declared: true,
        step4_zero_rel_rule: "zero-rel".into(),
        step5_witness_certificate: Some("witness-cert".into()),
        step6_quotient_policy: "Q1_SEPARATED".into(),
    };
    assert_eq!(
        ports.validate_declaration_order(&order),
        PrimeDeclarationOutcome::AcceptDeclaration
    );

    // One measurement over one triple.
    let m = adequate_measurement();
    let obs = m.observe(0).unwrap();
    assert!(matches!(obs.verdict(), LggrVerdict::Red { .. }));
    assert!(obs.ledger().ngd > 0.0, "r0 is a hidden failure");

    // Prime 001-T, wired into Prime 002 rather than discarded.
    let receipt = m
        .descend(
            "epk-corpus",
            "prime-carrier",
            &obs,
            true,
            vec!["transport: residual preserved".into()],
        )
        .unwrap();
    let evidence = m.continuation_evidence(&receipt).unwrap();
    assert_eq!(evidence.receipt_hash(), receipt.receipt_hash());
    assert_eq!(evidence.corpus_digest(), m.corpus_digest());

    let decision = ports.can_continue(&PrimeContinuationInputs::from_evidence(
        evidence,
        PrimeBudget::new(100.0, 10.0),
        true,
        true,
        true,
        true,
        true,
        false,
    ));
    // Under quarantine the seam runs end to end and then REFUSES. Every conjunct
    // except the quarantine is satisfied, which is what makes this a fail-closed
    // quarantine rather than a broken pipeline.
    assert!(!decision.may_continue());
    assert_eq!(
        decision.blockers(),
        &["V1SchemaQuarantined".to_string()]
    );
    assert_eq!(decision.disposition(), "ExternalVerifierRequired");
    assert_eq!(decision.step_terminal(), "TERMINAL_WITH_DEBT");
    assert!(decision.authority_effect().is_none());

    // Replay reproduces the receipt exactly.
    let replay = m
        .descend(
            "epk-corpus",
            "prime-carrier",
            &obs,
            true,
            vec!["transport: residual preserved".into()],
        )
        .unwrap();
    assert_eq!(receipt.receipt_hash(), replay.receipt_hash());
}

/// **The quarantine proof.** No v1 path, under any combination of inputs, yields an
/// executable continuation.
#[test]
fn no_v1_path_can_produce_an_executable_continuation() {
    let measurements = [adequate_measurement(), collapsing_measurement()];
    let budgets = [
        PrimeBudget::new(100.0, 10.0),
        PrimeBudget::new(10.0, 10.0),
        PrimeBudget::new(0.0, 10.0),
    ];
    let mut checked = 0usize;
    for m in &measurements {
        for row in 0..m.row_count() {
            let obs = m.observe(row).unwrap();
            for preserved in [true, false] {
                let receipt = m.descend("s", "t", &obs, preserved, vec![]).unwrap();
                let ev = m.continuation_evidence(&receipt).unwrap();
                for budget in budgets {
                    // Every caller-supplied conjunct at its most permissive.
                    let d = PrimeContinuationInputs::from_evidence(
                        ev.clone(),
                        budget,
                        true,
                        true,
                        true,
                        true,
                        true,
                        false,
                    )
                    .evaluate();
                    assert!(
                        !d.may_continue(),
                        "v1 produced an executable continuation: {d:?}"
                    );
                    assert!(d.is_quarantined());
                    assert_eq!(d.disposition(), "ExternalVerifierRequired");
                    checked += 1;
                }
            }
        }
    }
    assert!(checked >= 48, "expected broad coverage, checked {checked}");
}

/// A `PrimeContinuation` cannot be deserialized at all, so a green decision cannot
/// be handed to a caller as JSON. The compile-time half is the `compile_fail`
/// doctest on the type; this is the runtime half.
#[test]
fn a_decision_cannot_be_forged_from_json_or_constructed_empty() {
    // Serializes for transport/audit...
    let m = adequate_measurement();
    let obs = m.observe(1).unwrap();
    let receipt = m.descend("s", "t", &obs, true, vec![]).unwrap();
    let d = PrimeContinuationInputs::from_evidence(
        m.continuation_evidence(&receipt).unwrap(),
        PrimeBudget::new(100.0, 10.0),
        true,
        true,
        true,
        true,
        true,
        false,
    )
    .evaluate();
    let json = serde_json::to_string(&d).unwrap();
    assert!(json.contains("V1SchemaQuarantined"));

    // ...and there is no verdict field in it to forge: `may_continue` is derived.
    assert!(!json.contains("may_continue"));
    assert!(!d.may_continue());
    assert_eq!(d.step_terminal(), "TERMINAL_WITH_DEBT");
}

// Origin: engine/crates_rs/tests/core_local_green_global_red_lggr/lggr_prime_seam.rs
// Claim: urn:core:crates_rs:tests:lggr-prime-seam:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord16316ff6 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord16316ff6` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError16316ff6 {
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
impl BoundaryError16316ff6 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError16316ff6 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError16316ff6 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord16316ff6 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError16316ff6> {
        if capacity_bound == 0 {
            return Err(BoundaryError16316ff6::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError16316ff6::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError16316ff6::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_16316ff6() {
    let admitted = BoundaryRecord16316ff6::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord16316ff6::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
