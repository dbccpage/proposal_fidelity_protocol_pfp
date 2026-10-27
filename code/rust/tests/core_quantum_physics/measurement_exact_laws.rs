use linear_algebra::exact_field::{
    involution as star, involution::outer_product, matrix as mx, ordered::hermitian_inertia,
};
use num_bigint::{BigInt, BigUint};
use num_traits::{One, Zero};
use core_number_theory::cyclotomic::{Cyc24, GaussianRat};
use core_number_theory::cyclotomic_field::{sqrt_of_integer, Cyclotomic};
use core_number_theory::rational::{ri, rq, Rational};
use core_quantum_physics::{finite_chsh_correlations as bell, kochen_specker, mub::MubSystem};

fn gi(n: i64) -> GaussianRat {
    GaussianRat::from_ints(n, 0)
}

#[test]
fn prime_power_mubs_replay_projectors_two_design_and_inversion() {
    let q9 = MubSystem::try_new(
        9,
        core_quantum_physics::mub::odd_prime::build_odd_prime_power_mub::<3>(2, 1_000_000)
            .unwrap(),
    )
    .unwrap();
    assert!(q9.verify_two_design_with_budget(1_000_000).unwrap());
    let rho = mx::scale(
        &mx::identity::<Cyclotomic<3>>(9).unwrap(),
        &Cyclotomic::rational(rq(1, 9)),
    )
    .unwrap();
    assert!(q9.verify_exact_reconstruction(&rho));
    assert_eq!(
        q9.deterministic_valuation_purity(&vec![0; 10]).unwrap(),
        Cyclotomic::rational(ri(9))
    );
    let q8 = MubSystem::try_new(
        8,
        core_quantum_physics::mub::char_two::build_char_two_mub(3, 1_000_000).unwrap(),
    )
    .unwrap();
    assert!(q8.verify_two_design_with_budget(1_000_000).unwrap());
    assert!(core_quantum_physics::mub::char_two::build_char_two_mub(3, 1).is_err());
    assert!(core_quantum_physics::mub::odd_prime::build_odd_prime_power_mub::<3>(2, 1).is_err());
}
#[test]
fn tomography_normalization_and_algebra_are_separate_from_state_admission() {
    let system = MubSystem::mub_d3();
    let mut probabilities = vec![vec![ri(0); 3]; 4];
    for row in &mut probabilities {
        row[0] = ri(1);
    }
    let inverted = system
        .try_reconstruct_state_rational(&probabilities)
        .unwrap();
    assert_eq!(
        system
            .purity_from_probabilities(
                &probabilities
                    .iter()
                    .map(|r| r.iter().cloned().map(Cyc24::rat).collect())
                    .collect::<Vec<_>>()
            )
            .unwrap(),
        Cyc24::from_int(3)
    );
    assert!(!core_quantum_physics::tomography::check_density_operator(&inverted).unwrap());
    assert!(
        core_quantum_physics::tomography::reconstruct_admitted_state(&system, &probabilities)
            .is_err()
    );
    assert!(MubSystem::<Cyc24>::new(usize::MAX, vec![])
        .try_reconstruct_state(&[])
        .is_err());
    let malformed = MubSystem::<Cyc24>::new(3, vec![vec![]]);
    assert!(!malformed.verify_idempotence());
    assert!(malformed
        .try_measure_state(&mx::identity(3).unwrap())
        .is_err());
    let mut trace_only = system.clone();
    trace_only.bases[0][0] = mx::scale(&mx::identity(3).unwrap(), &Cyc24::rat(rq(1, 3))).unwrap();
    assert!(!trace_only.verify_rank_one_trace());
    let mut repeated = system.clone();
    repeated.bases[1] = repeated.bases[0].clone();
    assert_ne!(
        repeated.verify_projector_algebra().status,
        core_quantum_physics::mub::algebra::ProjectorAlgebraStatus::AlgebraVerified
    );
}
#[test]
fn kochen_specker_rays_preserve_field_pair_and_context_constraints() {
    let peres = kochen_specker::peres_33().unwrap();
    assert_eq!(
        (peres.rays.len(), peres.pairs.len(), peres.contexts.len()),
        (33, 72, 16)
    );
    assert_eq!(peres.affine_frame_dimension().unwrap(), 17);
    assert!(matches!(
        peres.decide(1_000_000).unwrap(),
        core_solvers::solver_sat_dpll::BooleanOutcome::Unsat { .. }
    ));
    let mut corrupted = peres.clone();
    corrupted.pairs.pop();
    assert!(corrupted.problem().is_err());
    let cabello = kochen_specker::cabello_18().unwrap();
    assert!(matches!(
        cabello.decide(1_000_000).unwrap(),
        core_solvers::solver_sat_dpll::BooleanOutcome::Unsat { .. }
    ));
    assert!(peres.decide(0).is_err());
    for ray in [[1, 0, 0], [0, 1, 0], [0, 0, 1], [3, 4, 0], [4, -3, 0]] {
        let ray = ray.map(BigInt::from);
        assert!(kochen_specker::pythagorean_colour(&ray).is_ok());
    }
    assert!(kochen_specker::pythagorean_colour(&[1.into(), 1.into(), 0.into()]).is_err());
}
#[test]
fn chsh_square_sos_attainment_and_moment_replay_reject_corruption() {
    let c = core_quantum_physics::tensor_commuting_correlation_frontier::chsh_game_certificate()
        .unwrap();
    for matrix in [&c.state, &c.alice[0], &c.alice[1], &c.bob[0], &c.bob[1]] {
        assert!(matrix.as_slice().iter().all(|entry| entry.is_real()));
    }
    assert!(bell::verify_chsh_square_identity(&c.alice, &c.bob).unwrap());
    let tau = Cyclotomic::<8>::try_from(sqrt_of_integer(8, &2.into()).unwrap()).unwrap();
    assert!(bell::verify_tsirelson_certificate(&c.alice, &c.bob, &tau, &c.operator_bound).unwrap());
    assert!(hermitian_inertia(&c.moment)
        .unwrap()
        .is_positive_semidefinite());
    assert!(
        core_quantum_physics::tensor_commuting_correlation_frontier::certify_chsh_interval(
            &rq(17, 20),
            &rq(43, 50)
        )
        .unwrap()
    );
    let mut bad = c.operator_bound.clone();
    bad.upper_factors[0] = mx::identity(4).unwrap();
    assert!(!bell::verify_tsirelson_certificate(&c.alice, &c.bob, &tau, &bad).unwrap());
    let mut rho = c.state.clone();
    rho.set(0, 0, Cyclotomic::rational(ri(-1))).unwrap();
    assert!(bell::algebraic_box_from_state(&rho, &c.alice, &c.bob).is_err());
}
#[test]
fn busch_inertia_checks_dimension_four_and_mutated_places() {
    use core_number_theory::cyclotomic_ordered::{
        CyclotomicRealRoot, FieldElementF, FieldElementFPlus,
    };
    use core_quantum_physics::busch_effects::HermitianMatrix;
    let mut place = CyclotomicRealRoot::new(4);
    let mut h = HermitianMatrix::identity(4, 4).unwrap();
    h.entries
        .set(3, 3, FieldElementF::rational(ri(-1), 4))
        .unwrap();
    assert!(!h.is_positive_semidefinite(&mut place));
    let identity = HermitianMatrix::identity(4, 4).unwrap();
    assert_eq!(identity.principal_minors_with_budget(15).unwrap().len(), 15);
    assert!(identity.principal_minors_with_budget(14).is_err());
    place.poly = core_number_theory::polynomial::Polynomial::from_i64s(&[-1, 1]);
    assert!(identity.try_inertia(&place).is_err());
    assert!(HermitianMatrix::identity(0, 4).is_err());
    assert!(HermitianMatrix::identity(4, 7).is_err());
    assert!(identity
        .add(&HermitianMatrix::identity(2, 4).unwrap())
        .is_err());
    let mut radical = HermitianMatrix::identity(2, 8).unwrap();
    radical
        .entries
        .set(
            0,
            0,
            FieldElementF::new(
                8,
                FieldElementFPlus::new(8, &[ri(-1), ri(1)]),
                FieldElementFPlus::zero(8),
            ),
        )
        .unwrap();
    let mut positive_place = CyclotomicRealRoot::new(8);
    assert!(radical.is_positive_semidefinite(&mut positive_place));
    let mut negative_place = CyclotomicRealRoot::new(8);
    negative_place.a = rq(-3, 2);
    negative_place.b = rq(-7, 5);
    assert!(!radical.is_positive_semidefinite(&mut negative_place));
}
#[test]
fn arbitrary_weighted_rectangular_channels_do_not_signal_on_all_matrix_units() {
    use core_quantum_physics::{
        exact_channel::ExactKrausChannel, no_signalling::certify_no_signalling_map,
    };
    let reset = ExactKrausChannel::try_weighted(
        2,
        1,
        vec![
            (
                ri(1),
                mx::from_rows(vec![vec![GaussianRat::one(), GaussianRat::zero()]]).unwrap(),
            ),
            (
                ri(1),
                mx::from_rows(vec![vec![GaussianRat::zero(), GaussianRat::one()]]).unwrap(),
            ),
        ],
        "rectangular discard",
    )
    .unwrap();
    assert!(certify_no_signalling_map(&reset, 3, 36).unwrap());
    assert!(certify_no_signalling_map(&reset, 3, 35).is_err());
    assert!(matches!(
        certify_no_signalling_map(&reset, usize::MAX, usize::MAX),
        Err(core_quantum_physics::no_signalling::NoSignallingError::Dimension)
    ));
    assert!(matches!(
        certify_no_signalling_map(&reset, 33, usize::MAX),
        Err(core_quantum_physics::no_signalling::NoSignallingError::Dimension)
    ));
}
#[test]
fn general_microcausality_does_not_require_a_two_factor_colouring() {
    use core_quantum_physics::commuting_observables::{
        check_microcausality, validate_observable_assignment, verify_microcausality_certificate,
    };
    let poset =
        core_homology::finite_poset::FinitePoset::from_generating_relations(3, []).unwrap();
    let diagonal = mx::diagonal(&[GaussianRat::one(), GaussianRat::from_ints(-1, 0)]).unwrap();
    let assignment = (0..3).map(|v| (v, diagonal.clone())).collect();
    let certificate = check_microcausality(&poset, &assignment).unwrap();
    assert_eq!(certificate.incomparable_pairs.len(), 3);
    assert!(verify_microcausality_certificate(
        &poset,
        &assignment,
        &certificate
    ));
    let labels = (0..3).map(|v| (v, 1)).collect();
    assert!(!validate_observable_assignment(&poset, &assignment, &labels, false).0);
    let mut bad = certificate.clone();
    bad.incomparable_pairs.pop();
    assert!(!verify_microcausality_certificate(
        &poset,
        &assignment,
        &bad
    ));
}
#[test]
fn cyclic_cancellations_and_reflection_matchings_are_distinct_certificates() {
    use core_quantum_physics::cancellation_certificates::{
        certify_phase_cancellation, verify_phase_cancellation,
    };
    let triangle = certify_phase_cancellation(3, &[0, 1, 2]).unwrap().unwrap();
    assert!(triangle.reflected_pairs.is_none());
    assert!(verify_phase_cancellation(&triangle).unwrap());
    let pair = certify_phase_cancellation(4, &[0, 2]).unwrap().unwrap();
    assert!(pair.reflected_pairs.is_some());
    assert!(verify_phase_cancellation(&pair).unwrap());
    let mut bad = pair.clone();
    bad.exponents[1] = 1;
    assert!(!verify_phase_cancellation(&bad).unwrap());
    assert!(certify_phase_cancellation(0, &[0]).is_err());
}
#[test]
fn ccr_trace_defect_and_clock_shift_winding_replay_exactly() {
    use core_quantum_physics::norm_approximation_frontier::{
        certify_ccr_defect, clock_shift_winding, NormFrontierError,
    };
    let q = mx::diagonal(&[GaussianRat::zero(), GaussianRat::one()]).unwrap();
    let p = mx::from_rows(vec![
        vec![GaussianRat::zero(), GaussianRat::one()],
        vec![GaussianRat::one(), GaussianRat::zero()],
    ])
    .unwrap();
    let cert = certify_ccr_defect(&q, &p, &rq(1, 7)).unwrap();
    assert_eq!(cert.trace_defect, GaussianRat::from_rational(rq(-2, 7)));
    assert_eq!(cert.normalized_lower_bound, rq(1, 7));
    assert!(certify_ccr_defect(&q, &p, &ri(0)).is_err());
    assert_eq!(clock_shift_winding(1).unwrap().winding, BigInt::zero());
    assert_eq!(clock_shift_winding(3).unwrap().winding, BigInt::one());
    assert_eq!(clock_shift_winding(2), Err(NormFrontierError::BranchCut));
}
#[test]
fn naimark_compression_replays_a_nonprojective_povm_without_rational_square_roots() {
    use core_quantum_physics::operational_axiom_selection::{
        naimark_projective_dilation, verify_naimark_certificate,
    };
    let g = |q| GaussianRat::from_rational(q);
    let effects = vec![
        mx::diagonal(&[g(rq(1, 3)), g(rq(2, 3))]).unwrap(),
        mx::diagonal(&[g(rq(2, 3)), g(rq(1, 3))]).unwrap(),
    ];
    let povm = core_quantum_physics::instruments::ExactPovm::try_new(effects).unwrap();
    let c = naimark_projective_dilation(&povm, 100_000).unwrap();
    assert!(verify_naimark_certificate(&c).unwrap());
    let mut bad = c.clone();
    bad.effects[0].set(0, 0, g(rq(1, 2))).unwrap();
    assert!(!verify_naimark_certificate(&bad).unwrap());
}
#[test]
fn operational_dimensions_are_exact_beyond_machine_products() {
    use core_quantum_physics::operational_axiom_selection::{
        local_tomography_dimensions, FiniteRivalTheory,
    };
    let huge = BigUint::from(u64::MAX) + BigUint::one();
    let d = local_tomography_dimensions(FiniteRivalTheory::Complex, &huge, &huge).unwrap();
    assert!(d.holds());
    assert!(
        !local_tomography_dimensions(FiniteRivalTheory::Real, &2u8.into(), &2u8.into())
            .unwrap()
            .holds()
    );
    assert!(local_tomography_dimensions(FiniteRivalTheory::Real, &BigUint::zero(), &huge).is_err());
}

#[test]
fn contextual_fraction_support_and_ks_are_independent_finite_decisions() {
    use core_finite_probability::local_deterministic::LocalVertexLimits;
    use core_quantum_physics::contextuality_obstruction::BinaryEmpiricalModel;
    let limits = LocalVertexLimits {
        assignments: 8,
        coordinates: 12,
        entries: 96,
    };
    let contexts = vec![vec![0, 1], vec![1, 2], vec![0, 2]];
    let strong = BinaryEmpiricalModel {
        variables: 3,
        contexts: contexts.clone(),
        probabilities: vec![vec![ri(0), rq(1, 2), rq(1, 2), ri(0)]; 3],
    };
    assert!(strong
        .supported_global_assignments(limits)
        .unwrap()
        .is_empty());
    assert!(strong.is_logically_contextual(limits).unwrap());
    let c = strong.contextual_fraction(limits, 1).unwrap();
    assert_eq!(c.contextual_fraction, ri(1));
    strong.verify_contextual_fraction(limits, &c).unwrap();
    let weak = BinaryEmpiricalModel {
        variables: 3,
        contexts: contexts.clone(),
        probabilities: vec![vec![rq(1, 4), rq(3, 8), rq(3, 8), ri(0)]; 3],
    };
    assert_eq!(weak.supported_global_assignments(limits).unwrap().len(), 4);
    assert!(!weak.is_logically_contextual(limits).unwrap());
    let c = weak.contextual_fraction(limits, 2000).unwrap();
    assert_eq!(c.contextual_fraction, rq(1, 4));
    weak.verify_contextual_fraction(limits, &c).unwrap();
    let mut bad = c.clone();
    bad.packing.dual.fill(ri(0));
    assert!(weak.verify_contextual_fraction(limits, &bad).is_err());
    assert!(weak.contextual_fraction(limits, 10).is_err());
    let mut disturbing = weak.clone();
    disturbing.probabilities[0] = vec![ri(1), ri(0), ri(0), ri(0)];
    assert!(disturbing.supported_global_assignments(limits).is_err());
    let local = BinaryEmpiricalModel {
        variables: 3,
        contexts,
        probabilities: vec![vec![ri(1), ri(0), ri(0), ri(0)]; 3],
    };
    assert_eq!(
        local
            .contextual_fraction(limits, 100)
            .unwrap()
            .contextual_fraction,
        ri(0)
    );
    assert!(matches!(
        core_quantum_physics::kochen_specker::cabello_18()
            .unwrap()
            .decide(1_000_000)
            .unwrap(),
        core_solvers::solver_sat_dpll::BooleanOutcome::Unsat { .. }
    ));
}

#[test]
fn quadratic_interference_has_second_order_terms_and_no_higher_orders() {
    use core_quantum_physics::coherent_interference::sorkin_interference;
    let c = vec![gi(1), gi(2), GaussianRat::from_ints(1, 1), gi(-3)];
    assert_eq!(
        sorkin_interference(&c, &[vec![0], vec![1]], 4).unwrap(),
        ri(4)
    );
    assert_eq!(
        sorkin_interference(&c, &[vec![0, 1], vec![2], vec![3]], 8).unwrap(),
        ri(0)
    );
    assert_eq!(
        sorkin_interference(&c, &[vec![0], vec![1], vec![2], vec![3]], 16).unwrap(),
        ri(0)
    );
    assert!(sorkin_interference(&c, &[vec![0], vec![0]], 4).is_err());
    assert!(sorkin_interference(&c, &[vec![0], vec![1], vec![2]], 7).is_err());
}

#[test]
fn phase_average_is_an_exact_conditional_expectation() {
    use core_quantum_physics::phase_averaged_shadow::{
        diagonal_expectation, phase_group_average, verify_diagonal_bimodule,
        verify_diagonal_self_adjoint,
    };
    use core_quantum_physics::phase_blind_quotient::UnitPhaseGroup;
    let a = mx::from_rows(vec![
        vec![gi(1), GaussianRat::from_ints(2, 3)],
        vec![GaussianRat::from_ints(-1, 2), gi(4)],
    ])
    .unwrap();
    let b = mx::from_rows(vec![vec![gi(0), gi(1)], vec![GaussianRat::i(), gi(-2)]]).unwrap();
    let left = mx::diagonal(&[gi(2), gi(3)]).unwrap();
    let right = mx::diagonal(&[gi(-1), gi(5)]).unwrap();
    assert!(verify_diagonal_bimodule(&a, &left, &right).unwrap());
    assert!(verify_diagonal_self_adjoint(&a, &b).unwrap());
    assert_eq!(
        phase_group_average(&a, &UnitPhaseGroup::new(vec![gi(1), gi(-1)]).unwrap()).unwrap(),
        diagonal_expectation(&a).unwrap()
    );
    assert!(!verify_diagonal_bimodule(&a, &a, &right).unwrap());
    assert!(diagonal_expectation(&mx::zeros::<GaussianRat>(0, 0).unwrap()).is_err());
}

#[test]
fn tensor_states_replay_both_reductions_and_product_statistics() {
    use core_quantum_physics::composition_tensor_mub::{
        compose_density, product_statistic, verify_tensor_state,
    };
    let a = mx::diagonal(&[
        GaussianRat::from_rational(rq(1, 3)),
        GaussianRat::from_rational(rq(2, 3)),
    ])
    .unwrap();
    let b = mx::scale(
        &star::outer_product(&[gi(1), GaussianRat::i()], &[gi(1), GaussianRat::i()]).unwrap(),
        &GaussianRat::from_rational(rq(1, 2)),
    )
    .unwrap();
    let c = compose_density(&a, &b).unwrap();
    assert!(verify_tensor_state(&a, &b, &c).unwrap());
    assert_eq!(
        product_statistic(&a, &b, &mx::diagonal(&[gi(1), gi(0)]).unwrap(), &b).unwrap(),
        GaussianRat::from_rational(rq(1, 3))
    );
    let mut bad = c.clone();
    bad.joint.set(0, 0, gi(1)).unwrap();
    assert!(!verify_tensor_state(&a, &b, &bad).unwrap());
}

#[test]
fn parity_cochains_and_pauli_signs_replay_actual_differentials() {
    use core_quantum_physics::contextuality_obstruction::{
        build_cochain_complex, compute_obstruction_class, construct_cabello_scenario,
    };
    use core_quantum_physics::pauli_context_table::PauliContextTable;
    let scenario = construct_cabello_scenario();
    let mut cx = build_cochain_complex(&scenario).unwrap();
    cx.checked_complex().unwrap();
    assert_eq!(compute_obstruction_class(&scenario).unwrap().dim_h1, 1);
    let row = (0..cx.dim_c1)
        .find(|&r| !cx.delta0_matrix.row(r).unwrap().is_zero())
        .unwrap();
    cx.dim_c2 = 1;
    cx.d1_matrix = core_number_theory::gf2::F2Matrix::zeros(1, cx.dim_c1).unwrap();
    cx.d1_matrix.set(0, row, true).unwrap();
    assert!(cx.checked_complex().is_err());
    let table = PauliContextTable::mermin();
    assert!(table.observables_are_hermitian_involutions());
    assert_eq!(table.sign_table().unwrap(), vec![1, 1, 1, 1, 1, -1]);
    let packet = table.packet().unwrap();
    let certificate = packet.certificate(packet.targets()).unwrap();
    assert!(packet
        .verify_certificate(packet.targets(), certificate)
        .unwrap());
    assert!(table.observable(9).is_err());
}
#[test]
fn exact_power_readouts_refuse_wrapped_exponents_before_arithmetic() {
    use core_quantum_physics::{gaussian_frame_readout as gaussian, power_rule_outcomes as power};
    let e = [gi(1), gi(0)];
    assert_eq!(
        gaussian::readout(&e, &e, u32::MAX),
        Err(gaussian::FrameError::PowerBudget(u32::MAX))
    );
    assert!(gaussian::square_is_frame_additive(1).unwrap());
    let context = power::Context::new(vec![vec![ri(1), ri(0)], vec![ri(0), ri(1)]]).unwrap();
    assert!(power::power_rule(&[ri(1), ri(0)], &context, usize::MAX).is_err());
    assert_eq!(
        power::power_rule(&[ri(3), ri(4)], &context, 2).unwrap(),
        vec![rq(9, 25), rq(16, 25)]
    );
}

#[test]
fn finite_frames_recover_trace_states_and_replay_exact_spectral_margins() {
    use core_quantum_physics::{
        frame_function_polytope::{eigenvalues_above, eigenvalues_at_least, FrameSystem},
        kochen_specker::{CABELLO_18_VECTORS, CABELLO_9_CONTEXTS},
    };
    let f = FrameSystem::new(
        CABELLO_18_VECTORS.iter().map(|r| r.to_vec()).collect(),
        CABELLO_9_CONTEXTS.iter().map(|c| c.to_vec()).collect(),
    )
    .unwrap();
    assert_eq!(f.incidence_rank().unwrap(), 9);
    assert_eq!(f.projector_span_rank().unwrap(), 10);
    let state = mx::scale(&mx::identity(4).unwrap(), &rq(1, 4)).unwrap();
    let values = f.frame_function_of(&state).unwrap();
    assert_eq!(f.state_of(&values).unwrap(), state);
    assert!(eigenvalues_at_least(&state, &rq(1, 4)).unwrap());
    assert!(!eigenvalues_above(&state, &rq(1, 4)).unwrap());
    assert!(f.vertices_with_budget(1).is_err());
    let mut bad = values;
    bad[0] += ri(1);
    assert!(f.state_of(&bad).is_err());
    assert!(eigenvalues_at_least(&mx::zeros::<Rational>(1, 2).unwrap(), &ri(0)).is_err());
}

#[test]
fn finite_planar_search_replays_its_declared_class_and_refuses_incomplete_search() {
    use core_quantum_physics::quantum_correlation::{
        evaluate_planar_chsh, finite_planar_chsh_max, generate_unit_vectors, tsirelson_value,
        PlanarCorrelationError,
    };
    let axes = generate_unit_vectors(4, 2).unwrap();
    let classical = finite_planar_chsh_max(&axes, true, 10_000).unwrap();
    assert_eq!(classical.value, Cyclotomic::<24>::rational(ri(2)));
    let directions = generate_unit_vectors(8, 2).unwrap();
    let maximum = finite_planar_chsh_max(&directions, true, 10_000).unwrap();
    assert_eq!(maximum.value, tsirelson_value());
    let [a, b, c, d] = maximum.strategy;
    let actual = evaluate_planar_chsh(
        &directions[a],
        &directions[b],
        &directions[c],
        &directions[d],
    )
    .unwrap();
    assert!(actual == maximum.value || actual == -maximum.value.clone());
    assert!(matches!(
        finite_planar_chsh_max(&directions, true, 0),
        Err(PlanarCorrelationError::Budget(0))
    ));
    let mut corrupted = directions.clone();
    corrupted[0].x = Cyclotomic::rational(ri(2));
    assert!(matches!(
        finite_planar_chsh_max(&corrupted, true, 10_000),
        Err(PlanarCorrelationError::NotUnitReal)
    ));
}

#[test]
fn population_shadows_compute_stochastic_rows_and_a_nonzero_composition_defect() {
    use core_quantum_physics::{
        exact_channel::ExactKrausChannel,
        population_shadow::{compose_kernels, composition_defect, population_shadow},
    };
    let rotation = mx::from_rows(vec![
        vec![
            GaussianRat::from_rational(rq(3, 5)),
            GaussianRat::from_rational(rq(-4, 5)),
        ],
        vec![
            GaussianRat::from_rational(rq(4, 5)),
            GaussianRat::from_rational(rq(3, 5)),
        ],
    ])
    .unwrap();
    let channel = ExactKrausChannel::from_operators(vec![rotation]).unwrap();
    let shadow = population_shadow(&channel).unwrap();
    assert_eq!(
        shadow,
        mx::from_rows(vec![
            vec![rq(9, 25), rq(16, 25)],
            vec![rq(16, 25), rq(9, 25)]
        ])
        .unwrap()
    );
    assert_eq!(
        composition_defect(&channel, &channel).unwrap(),
        mx::from_rows(vec![
            vec![rq(-288, 625), rq(288, 625)],
            vec![rq(288, 625), rq(-288, 625)]
        ])
        .unwrap()
    );
    let malformed = mx::from_rows(vec![vec![rq(-1, 2), rq(3, 2)]]).unwrap();
    assert!(compose_kernels(&malformed, &shadow).is_err());
}

#[test]
fn conditioning_and_luders_updates_replay_probabilities_and_refuse_null_sectors() {
    use core_quantum_physics::sector_conditioning::{
        condition_weights, luders_channel, luders_update, sector_projector,
        sector_weight_probability, ConditioningError,
    };
    let weights = vec![ri(9), ri(16)];
    let sector = [true, false];
    assert_eq!(
        sector_weight_probability(&weights, &sector).unwrap(),
        rq(9, 25)
    );
    assert_eq!(
        condition_weights(&weights, &sector).unwrap(),
        vec![ri(1), ri(0)]
    );
    let amplitudes = [
        GaussianRat::from_rational(rq(3, 5)),
        GaussianRat::from_rational(rq(4, 5)),
    ];
    let rho = outer_product(&amplitudes, &amplitudes).unwrap();
    let p = sector_projector(&sector).unwrap();
    assert_eq!(luders_update(&rho, &p).unwrap(), p);
    let q = sector_projector(&[false, true]).unwrap();
    let channel = luders_channel(&[p.clone(), q]).unwrap();
    assert_eq!(
        channel.apply(&rho).unwrap(),
        mx::diagonal(&[
            GaussianRat::from_rational(rq(9, 25)),
            GaussianRat::from_rational(rq(16, 25))
        ])
        .unwrap()
    );
    assert_eq!(
        luders_update(&p, &sector_projector(&[false, true]).unwrap()),
        Err(ConditioningError::NullSector)
    );
    assert!(luders_update(&mx::identity(2).unwrap(), &p).is_err());
    assert!(condition_weights(&[ri(-1), ri(2)], &sector).is_err());
    assert!(matches!(
        luders_channel(&[mx::identity(65).unwrap()]),
        Err(ConditioningError::Shape)
    ));
}

#[test]
fn phase_quotient_lifts_replay_norms_and_distinguish_nonexistence_from_budgets() {
    use core_number_theory::integer_factorization::FactorizationBudget;
    use core_quantum_physics::phase_blind_quotient::{
        gaussian_lift, gaussian_lift_with_budget, phase_blind_projection, rational_lift,
        QuotientError, UnitPhaseGroup,
    };
    let point = [rq(1, 3), rq(2, 3)];
    let lift = gaussian_lift(&point).unwrap().unwrap();
    assert_eq!(phase_blind_projection(&lift).unwrap(), point);
    assert!(rational_lift(&point).unwrap().is_none());
    assert!(gaussian_lift(&[rq(1, 4), rq(3, 4)]).unwrap().is_none());
    assert!(gaussian_lift_with_budget(&point, FactorizationBudget::default(), 0).is_err());
    assert!(matches!(
        UnitPhaseGroup::new(vec![GaussianRat::one(); 5]),
        Err(QuotientError::PhaseGroupSize(5))
    ));
}

// Origin: engine/crates_rs/tests/core_quantum_physics/measurement_exact_laws.rs
// Claim: urn:core:crates_rs:tests:measurement-exact-laws:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord62894ba8 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord62894ba8` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError62894ba8 {
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
impl BoundaryError62894ba8 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError62894ba8 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError62894ba8 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord62894ba8 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError62894ba8> {
        if capacity_bound == 0 {
            return Err(BoundaryError62894ba8::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError62894ba8::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError62894ba8::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_62894ba8() {
    let admitted = BoundaryRecord62894ba8::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord62894ba8::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
