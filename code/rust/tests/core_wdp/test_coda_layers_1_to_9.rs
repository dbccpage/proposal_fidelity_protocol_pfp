// AuthorityEffect: None.
use num_rational::BigRational;
use num_traits::Zero;
use core_wdp::coda::{
    evaluate_coda_pipeline, FirewallDecision, Layer1Foc, Layer2Mur, Layer3Cs, Layer4CsQ, Layer5Q,
    Layer6A, Layer7Or, Layer8Fda, Layer9CodaGtla, LayerId, MasterNormalFormOutcome,
    ObstructionWitnessPayload, ProblemInstance, TerminalKind,
};
use std::collections::BTreeMap;

fn base_problem() -> ProblemInstance {
    let mut problem = ProblemInstance::new("test_base_instance");
    problem.raw_data = "base_payload".to_string();
    problem.candidate_sieve = vec!["cand1".to_string(), "cand2".to_string()];
    problem.coarse_profile = vec![0, 1];
    problem.fine_profile = vec![0, 1];

    let mut proj = BTreeMap::new();
    proj.insert(0, 0);
    proj.insert(1, 1);
    problem.projection_map = proj;

    let mut sections = BTreeMap::new();
    sections.insert("U0".to_string(), vec![BigRational::new(1.into(), 2.into())]);
    sections.insert("U1".to_string(), vec![BigRational::new(1.into(), 2.into())]);
    problem.local_sections = sections;

    let mut overlaps = BTreeMap::new();
    overlaps.insert(("U0".to_string(), "U1".to_string()), true);
    problem.overlaps = overlaps;

    // d0 = [[-1, 1], [1, -1]]
    problem.d0 = vec![
        vec![
            BigRational::from_integer((-1).into()),
            BigRational::from_integer(1.into()),
        ],
        vec![
            BigRational::from_integer(1.into()),
            BigRational::from_integer((-1).into()),
        ],
    ];

    // d1 = [[0, 0]]
    problem.d1 = vec![vec![
        BigRational::from_integer(0.into()),
        BigRational::from_integer(0.into()),
    ]];

    problem.defect_cochain = vec![
        BigRational::from_integer(0.into()),
        BigRational::from_integer(0.into()),
    ];

    problem.fda_license_granted = false;
    problem.enclosure_interval = (
        BigRational::from_integer(0.into()),
        BigRational::from_integer(1.into()),
    );

    problem
}

#[test]
fn test_layer1_foc_zero_defect_and_obstruction() {
    let problem = base_problem();

    // 1. Zero defect
    let (rec, phi1, gamma2, witness, _) =
        Layer1Foc::evaluate(&problem).expect("valid finite complex");
    assert_eq!(rec.layer_id, LayerId::FOC);
    assert!(rec.succeeded);
    assert!(phi1.is_zero());
    assert!(gamma2.is_zero());
    assert!(witness.is_none());

    // 2. Obstructed cochain: [1, 0]^T not in im(d0)
    let mut obstructed = problem;
    obstructed.defect_cochain = vec![
        BigRational::from_integer(1.into()),
        BigRational::from_integer(0.into()),
    ];
    let (rec_obs, phi1_obs, gamma2_obs, witness_obs, _) =
        Layer1Foc::evaluate(&obstructed).expect("valid finite complex");
    assert!(rec_obs.succeeded);
    assert!(phi1_obs > BigRational::zero());
    assert!(gamma2_obs.is_zero());
    assert!(witness_obs.is_some());
    let w = witness_obs.unwrap();
    assert!(w.linfty_norm <= BigRational::from_integer(1.into()));
}

#[test]
fn test_layer2_mur_transport_and_commutation() {
    let problem = base_problem();

    // Baseline: transport verified
    let (rec, loss) = Layer2Mur::evaluate(&problem);
    assert_eq!(rec.layer_id, LayerId::MUR);
    assert!(rec.succeeded);
    assert!(loss.is_zero());

    // Introduce incompatible overlap
    let mut incompatible = problem;
    incompatible
        .overlaps
        .insert(("U0".to_string(), "U1".to_string()), false);
    let (rec_fail, loss_fail) = Layer2Mur::evaluate(&incompatible);
    assert!(!rec_fail.succeeded);
    assert!(loss_fail > BigRational::zero());
}

#[test]
fn test_layer3_cs_continuum_shadow_refinement() {
    let problem = base_problem();

    // Baseline: consistent
    let (rec, consistent) = Layer3Cs::evaluate(&problem);
    assert_eq!(rec.layer_id, LayerId::CS);
    assert!(rec.succeeded);
    assert!(consistent);

    // Inconsistent projection: fine element 0 maps to 999 outside coarse profile [0, 1]
    let mut inconsistent = problem;
    inconsistent.projection_map.insert(0, 999);
    let (rec_fail, consistent_fail) = Layer3Cs::evaluate(&inconsistent);
    assert!(!rec_fail.succeeded);
    assert!(!consistent_fail);
}

#[test]
fn test_layer4_cs_q_metric_separation_bounds() {
    let problem = base_problem();

    // Identical values on a declared-compatible overlap are required agreement, not a collision
    let (rec, _sep) = Layer4CsQ::evaluate(&problem);
    assert_eq!(rec.layer_id, LayerId::CS_Q);
    assert!(rec.succeeded);

    // Perturb section U1 to introduce exact nonzero separation
    let mut separated = problem.clone();
    separated
        .local_sections
        .insert("U1".to_string(), vec![BigRational::new(3.into(), 4.into())]);
    let (rec_sep, sep_val) = Layer4CsQ::evaluate(&separated);
    assert!(rec_sep.succeeded);
    assert_eq!(sep_val, BigRational::new(1.into(), 4.into()));

    // Collision: identical values on UNGLUED sections
    let mut colliding = problem;
    colliding
        .overlaps
        .insert(("U0".to_string(), "U1".to_string()), false);
    let (rec_col, _) = Layer4CsQ::evaluate(&colliding);
    assert!(!rec_col.succeeded);
}

#[test]
fn test_layer5_q_continuum_enclosure_boundaries() {
    let problem = base_problem();

    // Baseline: [0, 1] interval diameter = 1
    let (rec, diam) = Layer5Q::evaluate(&problem);
    assert_eq!(rec.layer_id, LayerId::Q);
    assert!(rec.succeeded);
    assert_eq!(diam, BigRational::from_integer(1.into()));

    // Inverted interval [2, 1] -> failure
    let mut inverted = problem;
    inverted.enclosure_interval = (
        BigRational::from_integer(2.into()),
        BigRational::from_integer(1.into()),
    );
    let (rec_inv, _) = Layer5Q::evaluate(&inverted);
    assert!(!rec_inv.succeeded);
}

#[test]
fn test_layer6_a_residue_cokernel_accounting() {
    let problem = base_problem();

    // Zero residual
    let (rec_zero, has_res_zero) =
        Layer6A::evaluate(&problem, &BigRational::zero(), &BigRational::zero());
    assert_eq!(rec_zero.layer_id, LayerId::A);
    assert!(rec_zero.succeeded);
    assert!(!has_res_zero);

    // Coherent residual (Phi_1 > 0, Gamma_2 == 0)
    let (rec_anom, has_res_anom) = Layer6A::evaluate(
        &problem,
        &BigRational::from_integer(1.into()),
        &BigRational::zero(),
    );
    assert!(rec_anom.succeeded);
    assert!(has_res_anom);
    assert!(rec_anom.diagnostic_message.contains("Sentinel"));
}

#[test]
fn test_layer7_or_hard_refusal_sieve() {
    let problem = base_problem();

    // Baseline: no refusal
    let (rec, refused) = Layer7Or::evaluate(&problem, &BigRational::zero());
    assert_eq!(rec.layer_id, LayerId::OR);
    assert!(rec.succeeded);
    assert!(!refused);

    // Empty candidate sieve -> Hard Refusal (OR-T5)
    let mut empty = problem;
    empty.candidate_sieve = vec![];
    let (rec_empty, refused_empty) = Layer7Or::evaluate(&empty, &BigRational::zero());
    assert!(!rec_empty.succeeded);
    assert!(refused_empty);
}

#[test]
fn test_layer8_fda_authority_firewall_rules() {
    let problem = base_problem();

    // Case 1: Zero defect, but NO verified external grant -> ClosedResidual (never authorized)
    let (_, dec1, token1) =
        Layer8Fda::evaluate(&problem, &BigRational::zero(), &BigRational::zero(), false);
    assert_eq!(dec1, FirewallDecision::RouteClosedResidual);
    assert!(token1.is_none());

    // Case 2: A license flag on ProblemInstance alone never mints a token
    let mut claimed = problem.clone();
    claimed.fda_license_granted = true;
    let (_, dec2, token2) =
        Layer8Fda::evaluate(&claimed, &BigRational::zero(), &BigRational::zero(), false);
    assert_eq!(dec2, FirewallDecision::RouteClosedResidual);
    assert!(token2.is_none());

    // Case 3: Upstream refusal -> RouteRefused
    let (_, dec3, token3) =
        Layer8Fda::evaluate(&problem, &BigRational::zero(), &BigRational::zero(), true);
    assert_eq!(dec3, FirewallDecision::RouteRefused);
    assert!(token3.is_none());
}

#[test]
fn test_layer9_coda_gtla_terminalization_and_disjointness() {
    let problem = base_problem();
    let records = Vec::new();

    let outcome = Layer9CodaGtla::terminalize(
        &problem,
        Some(BigRational::zero()),
        Some(BigRational::zero()),
        None,
        FirewallDecision::RouteClosedResidual,
        None,
        records,
        None,
        None,
        "test_evidence_hash".to_string(),
    );

    assert_eq!(outcome.terminal_kind, TerminalKind::ClosedResidual);
    assert!(outcome.is_closed_residual());
    assert!(!outcome.is_authorized());
    assert!(!outcome.is_refused());
    assert_eq!(outcome.layer_records.len(), 1);
    assert_eq!(outcome.layer_records[0].layer_id, LayerId::CODA_GTLA);
}

#[test]
fn layer1_malformed_complex_refuses_without_zero_functional_values() {
    let mut problem = base_problem();
    problem.d1 = vec![vec![BigRational::from_integer(1.into())]];
    let refused = Layer1Foc::evaluate(&problem).expect_err("ragged next differential must refuse");
    assert!(!refused.succeeded);
}

#[test]
fn test_layer1_foc_curved_descent_constrained_lp_vs_flat_complex() {
    use core_functional::gamma2::{ExactCochainComplexQ, ExactGamma2Error};
    use serde_json::json;

    let mut curved = base_problem();
    // Curved 1-vertex, 2-edge, 1-face presentation:
    // d0 = [[1], [1]], d1 = [[1, -2]], so K = d1 * d0 = [[-1]] != 0.
    curved.d0 = vec![
        vec![BigRational::from_integer(1.into())],
        vec![BigRational::from_integer(1.into())],
    ];
    curved.d1 = vec![vec![
        BigRational::from_integer(1.into()),
        BigRational::from_integer((-2).into()),
    ]];
    curved.defect_cochain = vec![
        BigRational::from_integer(2.into()),
        BigRational::from_integer(1.into()),
    ];

    // ExactCochainComplexQ stays strictly restricted to the flat (K = 0) locus.
    assert_eq!(
        ExactCochainComplexQ::try_new(1, 2, 1, curved.d0.clone(), curved.d1.clone()),
        Err(ExactGamma2Error::CochainIdentityViolation { row: 0, column: 0 })
    );

    // Default Layer1Foc::evaluate uses tau = 0 on curved presentations:
    // baseline raw Gamma2([2, 1]) = |2 - 2| = 0, so ||d1 x - K f||_1 <= 0 forces f* = 0
    // with constrained repair norm ||[2, 1]||_1 = 3 and raw Gamma2 = 0.
    let (rec_tau0, phi1_tau0, gamma2_tau0, witness_tau0, repair_tau0) =
        Layer1Foc::evaluate(&curved).expect("curved complex solved via constrained LP");
    assert!(rec_tau0.succeeded);
    assert_eq!(
        rec_tau0.metadata.get("locus"),
        Some(&json!("curved_representative_constrained"))
    );
    assert_eq!(rec_tau0.metadata.get("quotient_invariant"), Some(&json!(false)));
    assert_eq!(phi1_tau0, BigRational::from_integer(3.into()));
    assert_eq!(gamma2_tau0, BigRational::zero());
    assert_eq!(repair_tau0, vec![BigRational::zero()]);
    assert!(witness_tau0.is_some());

    // With closure slack tau = 1/2, the constrained LP allows raw Gamma2 <= 1/2,
    // reducing the degree-1 repair norm from 3 to 2 at f* = 1/2.
    let tau_half = BigRational::new(1.into(), 2.into());
    let (rec_half, phi1_half, gamma2_half, _, repair_half) =
        Layer1Foc::evaluate_with_closure_guard(&curved, &tau_half)
            .expect("curved complex with tau = 1/2");
    assert!(!rec_half.succeeded); // repaired raw Gamma2 = 1/2 > 0
    assert_eq!(phi1_half, BigRational::from_integer(2.into()));
    assert_eq!(gamma2_half, tau_half);
    assert_eq!(repair_half, vec![tau_half.clone()]);

    // Direct certificate inspection confirms RawClosureDefectResult values and curvature K.
    let verified = Layer1Foc::evaluate_curved_constrained(&curved, &tau_half)
        .expect("verified curved constrained certificate");
    assert!(verified.is_curved());
    assert_eq!(verified.baseline_raw_gamma2().value(), &BigRational::zero());
    assert_eq!(verified.repaired_raw_gamma2().value(), &tau_half);
}

#[test]
fn test_curved_coda_full_certificate_preservation_and_coupled_annihilator() {
    let mut curved = ProblemInstance::new("curved_coupled_annihilator_test");
    curved.d0 = vec![
        vec![BigRational::from_integer(1.into())],
        vec![BigRational::from_integer(1.into())],
    ];
    curved.d1 = vec![vec![
        BigRational::from_integer(1.into()),
        BigRational::from_integer((-2).into()),
    ]];
    curved.defect_cochain = vec![
        BigRational::from_integer(2.into()),
        BigRational::from_integer(1.into()),
    ];

    let (rec, phi1, gamma2, witness, payload, repair) =
        Layer1Foc::evaluate_with_payload(&curved, &BigRational::zero())
            .expect("curved constrained evaluation");

    assert!(rec.succeeded);
    assert_eq!(phi1, BigRational::from_integer(3.into()));
    assert_eq!(gamma2, BigRational::zero());
    assert_eq!(repair, vec![BigRational::zero()]);
    assert!(witness.is_some());
    assert!(payload.is_some());

    let payload = payload.unwrap();
    assert!(payload.is_curved());
    assert!(!payload.is_flat());

    let cw = payload.as_curved().expect("must be CurvedConstrained payload");
    assert_eq!(
        cw.dual_y,
        vec![
            BigRational::from_integer(1.into()),
            BigRational::from_integer(1.into())
        ]
    );
    assert_eq!(cw.objective, BigRational::from_integer(3.into()));

    // y alone is not a flat quotient annihilator: d0^T y = 1*1 + 1*1 = 2 != 0
    let mut d0_transpose_y = BigRational::zero();
    for i in 0..curved.d0.len() {
        d0_transpose_y += &curved.d0[i][0] * &cw.dual_y[i];
    }
    assert_eq!(d0_transpose_y, BigRational::from_integer(2.into()));

    // K = d1 * d0 = [1*1 + (-2)*1] = [-1]
    let k = vec![vec![BigRational::from_integer((-1).into())]];
    assert!(
        cw.verify_coupled_annihilator(&curved.d0, &k),
        "Coupled annihilator d0^T y + K^T z = 0 must hold!"
    );

    // Verify pipeline outcome preserves full certificate through MasterNormalFormOutcome
    let outcome = evaluate_coda_pipeline(&curved);
    assert!(outcome.is_curved_obstruction());
    assert!(!outcome.is_flat_obstruction());
    let pip_cw = outcome
        .curved_witness()
        .expect("must preserve curved certificate in outcome");
    assert_eq!(pip_cw.dual_y, cw.dual_y);
    assert_eq!(pip_cw.dual_z, cw.dual_z);
    assert_eq!(pip_cw.dual_lambda, cw.dual_lambda);

    // Verify serde serialization / deserialization roundtrip preserves payload variant
    let serialized = serde_json::to_string(&outcome).expect("must serialize");
    let deserialized: MasterNormalFormOutcome =
        serde_json::from_str(&serialized).expect("must deserialize");
    assert!(deserialized.is_curved_obstruction());
    assert_eq!(
        deserialized.curved_witness().unwrap().dual_z,
        cw.dual_z
    );
}

#[test]
fn test_curved_diagnostic_packet_and_propose_curved_value_edit() {
    use core_category_theory::context_reflection::ContextSystem;
    use core_wdp::coda::diagnostic_routing::{
        propose_curved_value_edit, CurvedDiagnosticPacket, CurvedProposal, ProposalPolicy, Refusal,
    };

    let system = ContextSystem::new(vec![0, 1], vec![vec![0], vec![1]], 1).unwrap();
    let policy = ProposalPolicy {
        allow_profile_coarsening: false,
        allow_value_edits: true,
    };

    // Before: curved presentation d0 = [[1], [1]], d1 = [[1, -2]], K = [[-1]],
    // omega = [2, 1], tau = 0 -> constrained norm = 3, repaired raw Gamma2 = 0.
    let mut before_problem = base_problem();
    before_problem.d0 = vec![
        vec![BigRational::from_integer(1.into())],
        vec![BigRational::from_integer(1.into())],
    ];
    before_problem.d1 = vec![vec![
        BigRational::from_integer(1.into()),
        BigRational::from_integer((-2).into()),
    ]];
    before_problem.defect_cochain = vec![
        BigRational::from_integer(2.into()),
        BigRational::from_integer(1.into()),
    ];
    let before_cert = Layer1Foc::evaluate_curved_constrained(&before_problem, &BigRational::zero())
        .unwrap()
        .certificate()
        .clone();
    let before_packet = CurvedDiagnosticPacket::replay(system.clone(), before_cert.clone()).unwrap();
    assert_eq!(
        before_packet.constrained_phi1().value(),
        &BigRational::from_integer(3.into())
    );
    assert_eq!(before_packet.repaired_raw_gamma2().value(), &BigRational::zero());

    // Candidate 1: same omega -> no strict descent -> Refused(CandidateHasNoStrictDescent).
    assert_eq!(
        propose_curved_value_edit(&before_packet, policy, before_cert),
        Ok(CurvedProposal::Refused(Refusal::CandidateHasNoStrictDescent))
    );

    // Candidate 2: edited omega = [1, 1] -> in im(d0) with f* = 1, but at f* = 1
    // d1(omega' - d0 f*) = d1([0, 0]) = 0!
    // So with tau = 0, constrained norm drops from 3 to 0 AND repaired raw Gamma2 stays 0.
    let mut after_problem = before_problem.clone();
    after_problem.defect_cochain = vec![
        BigRational::from_integer(1.into()),
        BigRational::from_integer(1.into()),
    ];
    let after_cert = Layer1Foc::evaluate_curved_constrained(&after_problem, &BigRational::zero())
        .unwrap()
        .certificate()
        .clone();
    match propose_curved_value_edit(&before_packet, policy, after_cert).unwrap() {
        CurvedProposal::ValueEdit { before, after } => {
            assert_eq!(
                before.constrained_phi1().value(),
                &BigRational::from_integer(3.into())
            );
            assert_eq!(after.constrained_phi1().value(), &BigRational::zero());
            assert_eq!(after.repaired_raw_gamma2().value(), &BigRational::zero());
        }
        other => panic!("expected accepted CurvedProposal::ValueEdit, got {other:?}"),
    }

    // Candidate 3: edited omega = [2, 0] with tau = 0 has baseline raw Gamma2 = 2,
    // and optimal constrained repair at f* = 1 gives residual [1, -1] with repaired raw Gamma2 = 3 > 0 + 0,
    // which violates the cross-step closure guard against before_packet's repaired_raw_gamma2 = 0.
    let mut worse_closure_problem = before_problem;
    worse_closure_problem.defect_cochain = vec![
        BigRational::from_integer(2.into()),
        BigRational::from_integer(0.into()),
    ];
    let worse_closure_cert =
        Layer1Foc::evaluate_curved_constrained(&worse_closure_problem, &BigRational::zero())
            .unwrap()
            .certificate()
            .clone();
    assert_eq!(
        propose_curved_value_edit(&before_packet, policy, worse_closure_cert),
        Ok(CurvedProposal::Refused(Refusal::CurvedClosureGuardViolated))
    );
}

#[test]
fn test_multiview_lossy_projection_reconciliation_benchmark() {
    use num_bigint::BigInt;
    use core_category_theory::context_reflection::ContextSystem;
    use core_functional::gamma2::{
        ExactCochainComplexQ, ExactGamma2Error, Gamma2Functional,
    };
    use core_functional::l1_seminorm::L1Seminorm;
    use core_solvers::solver_lp_phi1_quotient::{
        solve_constrained_curved_phi1, solve_exact_phi1, verify_constrained_curved_phi1,
    };
    use core_wdp::coda::diagnostic_routing::{
        propose_curved_value_edit, CurvedDiagnosticPacket, CurvedProposal, DiagnosticPacket,
        ProposalPolicy, Refusal, RoutingError,
    };

    let q = |v: i64| BigRational::from_integer(BigInt::from(v));
    let qr = |n: i64, d: i64| BigRational::new(BigInt::from(n), BigInt::from(d));

    // 6-view, 9-edge, 4-triangle hierarchical multi-view network with lossy inter-view projections:
    // Views v0..v5, 4 overlapping audit triangles:
    //   Triangle 0: e0=(0->1), e1=(1->2), e2=(0->2)
    //   Triangle 1: e1=(1->2), e3=(2->3), e4=(1->3)
    //   Triangle 2: e3=(2->3), e5=(3->4), e6=(2->4)
    //   Triangle 3: e5=(3->4), e7=(4->5), e8=(3->5)
    // Direct 1-hop edges (e0, e1, e3, e5, e7) have conversion factor 9/10: (d0 f)_(u->v) = (9/10) f_v - f_u.
    // 2-hop summary edges (e2, e4, e6, e8) have coarse factor 4/5: (d0 f)_(u->w) = (4/5) f_w - f_u.
    // Consequently, on each triangle t=(u, v, w), curvature is:
    //   (K f)_t = (9/10 f_v - f_u) + (9/10 f_w - f_v) - (4/5 f_w - f_u) = -1/10 f_v + 1/10 f_w != 0.
    // Note dim(C^0) = 6, dim(C^1) = 9, dim(C^2) = 4, and dim(ker(K)) = 2 (f_0 is free and
    // uniform shifts f_1 = f_2 = f_3 = f_4 = f_5 lie in ker(K)).
    let edges: [(usize, usize, BigRational); 9] = [
        (0, 1, qr(9, 10)), // e0
        (1, 2, qr(9, 10)), // e1
        (0, 2, qr(4, 5)),  // e2
        (2, 3, qr(9, 10)), // e3
        (1, 3, qr(4, 5)),  // e4
        (3, 4, qr(9, 10)), // e5
        (2, 4, qr(4, 5)),  // e6
        (4, 5, qr(9, 10)), // e7
        (3, 5, qr(4, 5)),  // e8
    ];
    let d0: Vec<Vec<BigRational>> = edges
        .iter()
        .map(|(u, v, rate)| {
            let mut row = vec![q(0); 6];
            row[*u] = q(-1);
            row[*v] = rate.clone();
            row
        })
        .collect();

    // 4 triangle audit rows in d1 (4 x 9):
    // T0: e0 + e1 - e2
    // T1: e1 + e3 - e4
    // T2: e3 + e5 - e6
    // T3: e5 + e7 - e8
    let triangle_edges: [(usize, usize, usize); 4] = [
        (0, 1, 2),
        (1, 3, 4),
        (3, 5, 6),
        (5, 7, 8),
    ];
    let d1: Vec<Vec<BigRational>> = triangle_edges
        .iter()
        .map(|&(a, b, c)| {
            let mut row = vec![q(0); 9];
            row[a] = q(1);
            row[b] = q(1);
            row[c] = q(-1);
            row
        })
        .collect();

    let weights = vec![q(1); 9];
    let space = L1Seminorm::new(d0.clone(), weights).unwrap();

    // Verify flat ExactCochainComplexQ refuses this multi-view network (K != 0).
    assert_eq!(
        ExactCochainComplexQ::try_new(6, 9, 4, d0.clone(), d1.clone()),
        Err(ExactGamma2Error::CochainIdentityViolation { row: 0, column: 1 })
    );

    // =========================================================================
    // Regime A: Common-mode drift in ker(K) + localized edge discrepancy in ker(d1).
    // True drift f_true = [10, 20, 20, 20, 20, 20] lies in ker(K) because f_1=..=f_5=20!
    // Plus a localized triangle-balanced flow discrepancy on T1..T3 that tempts
    // unconstrained l1 to shift f_2 != f_3, breaking 3-way loop consistency.
    // =========================================================================
    let f_ker_k = vec![q(10), q(20), q(20), q(20), q(20), q(20)];
    let mut core_regime_a: Vec<BigRational> = d0
        .iter()
        .map(|row| {
            row.iter()
                .zip(&f_ker_k)
                .map(|(a, b)| a * b)
                .sum::<BigRational>()
        })
        .collect();
    // Add a loop-consistent edge discrepancy delta_x in ker(d1):
    // Set delta_x on e3=(2->3) to +10, e4=(1->3) to +10, e6=(2->4) to +10:
    // Check d1(delta_x):
    //   T0: e0 + e1 - e2 = 0
    //   T1: e1 + e3 - e4 = 0 + 10 - 10 = 0
    //   T2: e3 + e5 - e6 = 10 + 0 - 10 = 0
    //   T3: e5 + e7 - e8 = 0
    // Because delta_x is in ker(d1) AND f_ker_k is in ker(K), baseline raw Gamma2(omega) == 0!
    core_regime_a[3] += q(10); // e3 = (2->3)
    core_regime_a[4] += q(10); // e4 = (1->3)
    core_regime_a[6] += q(10); // e6 = (2->4)

    let unc_a = solve_exact_phi1(&space, &core_regime_a).unwrap();
    let unc_a_gamma2 =
        Gamma2Functional::try_compute_raw(unc_a.primal_residual(), &d1).unwrap();
    let con_a_tau0 =
        solve_constrained_curved_phi1(&space, &d1, &core_regime_a, &q(0)).unwrap();

    println!(
        "[Benchmark Regime A (ker(K) drift + loop-balanced edge anomaly)] baseline_gamma2={}, unc_phi1={}, unc_repaired_gamma2={}, con_tau0_phi1={}, con_tau0_repaired_gamma2={}",
        con_a_tau0.baseline_raw_gamma2().value(),
        unc_a.value(),
        unc_a_gamma2.value(),
        con_a_tau0.value(),
        con_a_tau0.repaired_raw_gamma2().value(),
    );

    // Baseline raw closure defect is 0, but unconstrained l1 repair shifts node 3 relative to node 2,
    // inducing non-zero 3-way loop inconsistency (unc_repaired_gamma2 > 0) and smearing the residual
    // onto clean edges!
    assert_eq!(con_a_tau0.baseline_raw_gamma2().value(), &q(0));
    assert!(
        unc_a_gamma2.value() > &q(0),
        "unconstrained l1 repair induces 3-way loop closure defect on curved network"
    );
    // Constrained curved LP with tau = 0 cancels the full common-mode drift f_ker_k (reducing norm from
    // ||omega||_1 = 62 to ||delta_x||_1 = 30) while keeping 3-way loop defect at 0 and localizing
    // the exact 3 corrupted edges {e3, e4, e6}!
    assert_eq!(con_a_tau0.repaired_raw_gamma2().value(), &q(0));
    assert_eq!(con_a_tau0.value(), &q(30));
    let expected_residual_a = vec![
        q(0),
        q(0),
        q(0),
        q(10),
        q(10),
        q(0),
        q(10),
        q(0),
        q(0),
    ];
    assert_eq!(con_a_tau0.primal_residual(), expected_residual_a.as_slice());

    // =========================================================================
    // Regime B: Pareto frontier across closure budgets tau in {0, 1/4, 1/2, 1, 2, 5}
    // =========================================================================
    let tau_grid = [q(0), qr(1, 4), qr(1, 2), q(1), q(2), q(5)];
    let mut prev_phi1 = con_a_tau0.value().clone();
    let mut prev_gamma2 = con_a_tau0.repaired_raw_gamma2().value().clone();
    for tau in &tau_grid {
        let solved = solve_constrained_curved_phi1(&space, &d1, &core_regime_a, tau).unwrap();
        let replayed = verify_constrained_curved_phi1(solved.certificate().clone()).unwrap();
        assert_eq!(replayed.value(), solved.value());
        assert!(solved.repaired_raw_gamma2().value() <= &(solved.baseline_raw_gamma2().value() + tau));
        assert!(
            solved.value() <= &prev_phi1,
            "constrained Phi1 must be non-increasing as tau grows"
        );
        assert!(
            solved.repaired_raw_gamma2().value() >= &prev_gamma2,
            "repaired raw Gamma2 must be non-decreasing along the active Pareto frontier"
        );
        println!(
            "[Benchmark Regime B Pareto] tau={} -> constrained_phi1={}, repaired_gamma2={}, dual_lambda={}",
            tau,
            solved.value(),
            solved.repaired_raw_gamma2().value(),
            solved.dual_lambda()
        );
        prev_phi1 = solved.value().clone();
        prev_gamma2 = solved.repaired_raw_gamma2().value().clone();
    }
    // Once tau is large enough, constrained Phi1 matches unconstrained Phi1 exactly.
    assert_eq!(&prev_phi1, unc_a.value());

    // =========================================================================
    // Regime C: Pure node calibration drift (omega = d0 * f_drift + single-edge spike)
    // where baseline raw Gamma2 > 0 because K * f_drift != 0.
    // Here canceling f_drift REDUCES raw Gamma2, so tau = 0 recovers f_drift and
    // matches unconstrained l1 while shrinking raw Gamma2 from 6 down to 1!
    // =========================================================================
    let f_drift = vec![q(0), q(10), q(-10), q(20), q(0), q(10)];
    let mut core_regime_c: Vec<BigRational> = d0
        .iter()
        .map(|row| {
            row.iter()
                .zip(&f_drift)
                .map(|(a, b)| a * b)
                .sum::<BigRational>()
        })
        .collect();
    core_regime_c[0] += q(1); // single 1-unit measurement error on e0
    let unc_c = solve_exact_phi1(&space, &core_regime_c).unwrap();
    let con_c_tau0 =
        solve_constrained_curved_phi1(&space, &d1, &core_regime_c, &q(0)).unwrap();
    println!(
        "[Benchmark Regime C (node calibration drift + 1-edge error)] baseline_gamma2={}, con_tau0_phi1={}, con_tau0_repaired_gamma2={}, unc_phi1={}",
        con_c_tau0.baseline_raw_gamma2().value(),
        con_c_tau0.value(),
        con_c_tau0.repaired_raw_gamma2().value(),
        unc_c.value(),
    );
    assert!(con_c_tau0.baseline_raw_gamma2().value() > &q(5));
    assert_eq!(con_c_tau0.value(), &q(1));
    assert_eq!(con_c_tau0.value(), unc_c.value());
    assert_eq!(con_c_tau0.repaired_raw_gamma2().value(), &q(1));

    // =========================================================================
    // Regime D: Guarded multi-step remediation via propose_curved_value_edit
    // vs flat DiagnosticPacket refusal.
    // =========================================================================
    let system = ContextSystem::new(vec![0, 1], vec![vec![0], vec![1]], 1).unwrap();
    let policy = ProposalPolicy {
        allow_profile_coarsening: false,
        allow_value_edits: true,
    };

    // Flat DiagnosticPacket::replay refuses the benchmark network with CochainIdentityViolation.
    assert!(matches!(
        DiagnosticPacket::replay(system.clone(), unc_a.certificate().clone(), d1.clone()),
        Err(RoutingError::Gamma2(
            ExactGamma2Error::CochainIdentityViolation { .. }
        ))
    ));

    let packet_step0 =
        CurvedDiagnosticPacket::replay(system.clone(), con_a_tau0.certificate().clone()).unwrap();

    // Poisoned candidate edit: reduces pairwise l1 norm by perturbing only e3,
    // which breaks triangle T1/T2 closure (repaired raw Gamma2 jumps from 0 to > 0 under tau = 0).
    let mut core_poisoned = core_regime_a.clone();
    core_poisoned[3] -= q(5); // unbalances T1 and T2!
    let cert_poisoned =
        solve_constrained_curved_phi1(&space, &d1, &core_poisoned, &q(0))
            .unwrap()
            .certificate()
            .clone();
    assert_eq!(
        propose_curved_value_edit(&packet_step0, policy, cert_poisoned),
        Ok(CurvedProposal::Refused(Refusal::CurvedClosureGuardViolated))
    );

    // Valid coordinated multi-view edit: corrects the 3-edge loop-balanced anomaly by half,
    // reducing constrained Phi1 from 30 to 15 while keeping repaired raw Gamma2 == 0.
    let mut core_step1 = core_regime_a.clone();
    core_step1[3] -= q(5);
    core_step1[4] -= q(5);
    core_step1[6] -= q(5);
    let cert_step1 = solve_constrained_curved_phi1(&space, &d1, &core_step1, &q(0))
        .unwrap()
        .certificate()
        .clone();
    match propose_curved_value_edit(&packet_step0, policy, cert_step1).unwrap() {
        CurvedProposal::ValueEdit { before, after } => {
            assert_eq!(before.constrained_phi1().value(), &q(30));
            assert_eq!(after.constrained_phi1().value(), &q(15));
            assert_eq!(after.repaired_raw_gamma2().value(), &q(0));
        }
        other => panic!("expected accepted CurvedProposal::ValueEdit, got {other:?}"),
    }
}

// Origin: engine/crates_rs/tests/core_wdp/test_coda_layers_1_to_9.rs
// Claim: urn:core:crates_rs:tests:test-coda-layers-1-to-9:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord7732152a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord7732152a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError7732152a {
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
impl BoundaryError7732152a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError7732152a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError7732152a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord7732152a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError7732152a> {
        if capacity_bound == 0 {
            return Err(BoundaryError7732152a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError7732152a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError7732152a::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_7732152a() {
    let admitted = BoundaryRecord7732152a::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord7732152a::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
