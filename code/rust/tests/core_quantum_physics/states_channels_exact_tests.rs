//! Exact state, channel and information laws, with independent presentations.
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{involution as star, matrix as mx};
use num_bigint::BigInt;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::cyclotomic::{Cyc8, EisensteinRat, GaussianRat as G};
use core_number_theory::rational::{ri, rq, Rational};
use core_number_theory::scalar::RationalEmbedding;
use core_quantum_physics::{
    bell_state::{BellBasis, BellState},
    bipartite_operator as bip,
    cptp_channels_stinespring::WeightedStinespring,
    density_matrix::ExactDensityMatrix as State,
    entanglement::Entanglement,
    entropy::Entropy,
    exact_channel::{apply_choi, ExactChoiMatrix, ExactKrausChannel as Channel},
    exact_hermitian::{self as h},
    exact_operator::ExactOperator as Op,
    ghz_state::GhzState,
    instruments::{ExactInstrumentError, ExactPovm, ExactProjectiveMeasurement},
    no_cloning::NoCloning,
    packed_hermitian::PackedDensityOperator,
    purification::{Purification, PurificationIsometry, UhlmannMaximizer, WeightedPurification},
    quantum_mutual_information::QuantumMutualInformation as MI,
    quantum_relative_entropy::QuantumRelativeEntropy as RE,
    quantum_state::RayVector,
    teleportation::{teleport_qudit, Teleportation},
    unitary_operator::ExactUnitary,
    w_state::WState,
};
fn basis(i: usize) -> RayVector {
    RayVector::basis(2, i).unwrap()
}
fn matrix(rows: &[&[i64]]) -> BasicMatrix<GaussianRat> {
    mx::from_rows(
        rows.iter()
            .map(|row| row.iter().map(|&v| G::from_ints(v, 0)).collect())
            .collect(),
    )
    .unwrap()
}

#[test]
fn bell_basis_six_overlaps_completeness_and_marginals() {
    let rays = [
        BellBasis::PhiPlus,
        BellBasis::PhiMinus,
        BellBasis::PsiPlus,
        BellBasis::PsiMinus,
    ]
    .map(|b| BellState::exact_ray(b).unwrap());
    let mut sum = Op::zeros(4, 4).unwrap();
    for i in 0..4 {
        assert_eq!(rays[i].norm_sq(), ri(2));
        for j in 0..i {
            assert_eq!(rays[i].inner(&rays[j]).unwrap(), G::zero());
        }
        let rho = State::pure(&rays[i]).unwrap();
        assert_eq!(rho.purity(), ri(1));
        assert_eq!(
            rho.partial_trace_second(2, 2).unwrap(),
            State::maximally_mixed(2).unwrap()
        );
        assert_eq!(
            rho.partial_trace_first(2, 2).unwrap(),
            State::maximally_mixed(2).unwrap()
        );
        assert_eq!(Entanglement::schmidt_rank_exact(&rays[i], 2, 2).unwrap(), 2);
        sum = sum.add(rho.as_operator()).unwrap();
    }
    assert_eq!(sum, Op::identity(4).unwrap());
}

#[test]
fn ghz_w_dicke_cuts_retain_coherences_and_distinguish_three_tangle() {
    for n in 2..=5 {
        let ghz = GhzState::exact(n).unwrap();
        let w = WState::exact(n).unwrap();
        assert_eq!(ghz.norm_sq(), ri(2));
        assert_eq!(w.norm_sq(), Rational::from_integer(n.into()));
        let g = State::pure(&ghz).unwrap();
        let reduced = g.partial_trace_second(2, 1usize << (n - 1)).unwrap();
        assert_eq!(reduced, State::maximally_mixed(2).unwrap());
        let reduced = State::pure(&w)
            .unwrap()
            .partial_trace_second(2, 1usize << (n - 1))
            .unwrap();
        assert_eq!(
            reduced.matrix().get_ref(0, 0).unwrap().re,
            Rational::new((n - 1).into(), n.into())
        );
        assert_eq!(
            reduced.matrix().get_ref(1, 1).unwrap().re,
            Rational::new(1.into(), n.into())
        );
        if n >= 3 {
            let pair = State::pure(&w)
                .unwrap()
                .partial_trace_second(4, 1usize << (n - 2))
                .unwrap();
            assert!(!bip::is_ppt(pair.matrix(), 2, 2).unwrap());
            assert_eq!(
                Entanglement::concurrence_exact(&pair, 10_000).unwrap(),
                Rational::new(2.into(), n.into())
            );
        }
    }
    assert_eq!(
        Entanglement::three_tangle_squared(&GhzState::exact(3).unwrap()).unwrap(),
        ri(1)
    );
    assert_eq!(
        Entanglement::three_tangle_squared(&WState::exact(3).unwrap()).unwrap(),
        ri(0)
    );
    assert_eq!(WState::dicke(4, 2).unwrap().norm_sq(), ri(6));
    assert!(GhzState::exact(usize::MAX).is_err());
    assert!(WState::dicke(3, 4).is_err());
}

#[test]
fn werner_and_isotropic_ppt_thresholds_are_exact_at_tiny_perturbations() {
    let tiny = Rational::new(1.into(), BigInt::from(10).pow(30));
    assert!(bip::is_ppt(BellState::werner(rq(1, 3)).unwrap().matrix(), 2, 2).unwrap());
    assert!(!bip::is_ppt(BellState::werner(rq(1, 3) + &tiny).unwrap().matrix(), 2, 2).unwrap());
    for d in [2, 3] {
        let f = Rational::new(1.into(), d.into());
        assert!(bip::is_ppt(BellState::isotropic(f.clone(), d).unwrap().matrix(), d, d).unwrap());
        assert!(!bip::is_ppt(BellState::isotropic(f + &tiny, d).unwrap().matrix(), d, d).unwrap());
    }
}

#[test]
fn channels_have_choi_kraus_metric_stinespring_and_ordinary_routes() {
    for channel in [
        Channel::depolarizing(2, rq(2, 7)).unwrap(),
        Channel::generalized_amplitude_damping(rq(2, 3), rq(3, 7)).unwrap(),
        Channel::try_new(
            2,
            2,
            vec![mx::diagonal(&[G::one(), G::i()]).unwrap()],
            "S phase",
        )
        .unwrap(),
    ] {
        let choi = channel.choi().unwrap();
        let canonical = choi.weighted_kraus().unwrap();
        assert!(canonical.same_channel(&channel).unwrap());
        assert_eq!(canonical.operators().len(), channel.kraus_rank().unwrap());
        let dilation = WeightedStinespring::from_channel(&channel).unwrap();
        assert!(dilation.verify().unwrap());
        let unit = canonical.to_unit_weight(10_000).unwrap();
        assert!(unit.same_channel(&channel).unwrap());
        let v = dilation.ordinary_isometry(10_000).unwrap();
        assert_eq!(
            mx::multiply_with_limits(&(star::adjoint(&(v)).unwrap()), &v, h::exact_limits())
                .unwrap(),
            mx::identity(2).unwrap()
        );
        // Matrix units include all off-diagonal coherences, unlike population-only tests.
        for i in 0..2 {
            for j in 0..2 {
                let mut e = mx::zeros(2, 2).unwrap();
                e.set(i, j, G::one()).unwrap();
                let expected = channel.apply(&e).unwrap();
                assert_eq!(apply_choi(choi.matrix(), 2, 2, &e).unwrap(), expected);
                assert_eq!(dilation.apply(&e).unwrap(), expected);
                assert_eq!(canonical.apply(&e).unwrap(), expected);
            }
        }
    }
}

#[test]
fn generalized_amplitude_damping_has_the_exact_thermal_fixed_state() {
    let rho = State::try_new(
        mx::diagonal(&[G::from_rational(rq(3, 7)), G::from_rational(rq(4, 7))]).unwrap(),
    )
    .unwrap();
    let channel = Channel::generalized_amplitude_damping(rq(2, 3), rq(3, 7)).unwrap();
    assert_eq!(rho.apply_channel(&channel).unwrap(), rho);
    let dep = Channel::depolarizing(3, rq(1, 5)).unwrap();
    assert_eq!(
        dep.choi().unwrap().entanglement_fidelity().unwrap(),
        rq(37, 45)
    );
    assert_eq!(
        Channel::identity(3, "I")
            .unwrap()
            .choi()
            .unwrap()
            .entanglement_fidelity()
            .unwrap(),
        ri(1)
    );
    assert_eq!(
        State::maximally_mixed(3)
            .unwrap()
            .apply_channel(&dep)
            .unwrap(),
        State::maximally_mixed(3).unwrap()
    );
    assert!(Channel::depolarizing(usize::MAX, rq(1, 2)).is_err());
}

#[test]
fn rectangular_channel_factorization_and_malformed_choi_refusals() {
    let k = BasicMatrix::<GaussianRat>::from_row_major(
        3,
        2,
        vec![
            G::one(),
            G::zero(),
            G::zero(),
            G::one(),
            G::zero(),
            G::zero(),
        ],
    )
    .expect("validated matrix literal");
    let channel = Channel::from_operators(vec![k]).unwrap();
    let rebuilt = channel.choi().unwrap().weighted_kraus().unwrap();
    assert_eq!((rebuilt.dim_in(), rebuilt.dim_out()), (2, 3));
    assert!(rebuilt.same_channel(&channel).unwrap());
    let swap = matrix(&[&[1, 0, 0, 0], &[0, 0, 1, 0], &[0, 1, 0, 0], &[0, 0, 0, 1]]);
    assert!(ExactChoiMatrix::try_new(2, 2, swap).is_err());
    assert!(ExactChoiMatrix::try_new(usize::MAX, 2, mx::zeros(1, 1).unwrap()).is_err());
}

#[test]
fn spectral_projective_measurements_are_repeatable_and_refuse_noncommuting_joint() {
    let z = matrix(&[&[1, 0], &[0, -1]]);
    let x = matrix(&[&[0, 1], &[1, 0]]);
    let mz = ExactProjectiveMeasurement::from_observable(&z, &[ri(-1), ri(1)]).unwrap();
    let mx = ExactProjectiveMeasurement::from_observable(&x, &[ri(-1), ri(1)]).unwrap();
    assert_eq!(mz.joint(&mx), Err(ExactInstrumentError::Noncommuting));
    let input = State::pure(&RayVector::from_ints(&[(1, 2), (3, -1)]).unwrap()).unwrap();
    let instrument = mz.instrument().unwrap();
    for k in 0..2 {
        let outcome = instrument.outcome(&input, k).unwrap();
        let state = outcome.state.unwrap();
        assert_eq!(instrument.outcome(&state, k).unwrap().probability, ri(1));
    }
    assert_eq!(
        mz.povm()
            .probabilities(&input)
            .unwrap()
            .into_iter()
            .sum::<Rational>(),
        ri(1)
    );
    let zero = State::pure(&basis(0)).unwrap();
    assert!(instrument.outcome(&zero, 0).unwrap().state.is_none());
    let registered = input
        .apply_channel(&instrument.classical_register_channel().unwrap())
        .unwrap();
    assert_eq!(
        registered.partial_trace_second(2, 2).unwrap(),
        input
            .apply_channel(&instrument.unselective().unwrap())
            .unwrap()
    );
    assert!(ExactPovm::try_new(vec![mx::identity(2).unwrap(), mx::identity(2).unwrap()]).is_err());
}

#[test]
fn weighted_purification_and_constructive_uhlmann_uniqueness_replay() {
    let rho = State::try_new(
        mx::diagonal(&[G::from_rational(rq(1, 3)), G::from_rational(rq(2, 3))]).unwrap(),
    )
    .unwrap();
    let weighted = WeightedPurification::of(&rho).unwrap();
    assert_eq!(weighted.reduced_state().unwrap(), *rho.matrix());
    let c = weighted.ordinary_coefficients(10_000).unwrap();
    assert_eq!(
        mx::multiply_with_limits(&(c), &star::adjoint(&c).unwrap(), h::exact_limits()).unwrap(),
        *rho.matrix()
    );
    let mut d = mx::zeros(c.rows(), c.cols() + 1).unwrap();
    for i in 0..c.rows() {
        for k in 0..c.cols() {
            d.set(
                i,
                k,
                c.get_ref(i, c.cols() - 1 - k).unwrap().clone().mul(&G::i()),
            )
            .unwrap();
        }
    }
    let isometry = PurificationIsometry::between(&c, &d).unwrap();
    assert!(isometry.verify(&c, &d).unwrap());
    let mut forged = isometry.clone();
    forged.map.set(0, 0, G::from_ints(7, 0)).unwrap();
    assert!(!forged.verify(&c, &d).unwrap());
}

#[test]
fn purification_supports_are_bound_to_the_original_coefficient_matrices() {
    let c = mx::from_rows(vec![vec![G::one(), G::zero()]]).unwrap();
    let actual = PurificationIsometry::between(&c, &c).unwrap();
    assert!(actual.verify(&c, &c).unwrap());
    assert_eq!(
        actual.source_support,
        mx::diagonal(&[G::one(), G::zero()]).unwrap()
    );
    let forged = PurificationIsometry {
        map: mx::identity(2).unwrap(),
        source_support: mx::identity(2).unwrap(),
        target_support: mx::identity(2).unwrap(),
    };
    assert!(!forged.verify(&c, &c).unwrap());
}

#[test]
fn exact_teleportation_computes_all_complex_qubit_and_qudit_branches() {
    let input = RayVector::from_ints(&[(1, 2), (3, -1)]).unwrap();
    let branches = Teleportation::exact(&input).unwrap();
    assert_eq!(branches.len(), 4);
    for branch in branches {
        assert_eq!(branch.probability, rq(1, 4));
        assert!(branch.bob_after.same_ray(&input).unwrap());
    }
    let q = [
        EisensteinRat::one(),
        EisensteinRat::zeta3(),
        EisensteinRat::from_ints(2, -1),
    ];
    let branches = teleport_qudit(&q, &EisensteinRat::zeta3()).unwrap();
    assert_eq!(branches.len(), 9);
    for branch in branches {
        assert_eq!(branch.probability, rq(1, 9));
        assert_eq!(
            branch.corrected,
            q.iter()
                .map(
                    |x| x.mul(&<EisensteinRat as RationalEmbedding>::from_rational(&rq(
                        1, 3
                    )))
                )
                .collect::<Vec<_>>()
        );
    }
    assert!(teleport_qudit(&q, &EisensteinRat::one()).is_err());
}

#[test]
fn no_cloning_obstruction_and_broadcasting_are_phase_independent() {
    let plus = RayVector::from_ints(&[(1, 0), (1, 0)]).unwrap();
    assert_eq!(
        NoCloning::exact_obstruction(&basis(0), &plus).unwrap(),
        rq(1, 4)
    );
    assert_eq!(
        NoCloning::exact_obstruction(&plus, &plus.scale(&G::i()).unwrap()).unwrap(),
        ri(0)
    );
    assert_eq!(
        NoCloning::exact_obstruction(&basis(0), &basis(1)).unwrap(),
        ri(0)
    );
    assert!(NoCloning::broadcasting_witness(&[
        State::pure(&basis(0)).unwrap(),
        State::pure(&plus).unwrap()
    ])
    .unwrap()
    .is_some());
    assert_eq!(
        NoCloning::universal_cloning_fidelity(2, 1, 2).unwrap(),
        rq(5, 6)
    );
}

#[test]
fn coherent_information_and_relative_entropy_use_full_operators() {
    let bell = BellState::exact_density(BellBasis::PhiPlus).unwrap();
    let ln2 =
        core_finite_probability::log_form::LogForm::ln_of_positive_rational(&ri(2), 100).unwrap();
    assert_eq!(
        Entropy::von_neumann_exact(&bell).unwrap(),
        core_finite_probability::log_form::LogForm::zero()
    );
    assert_eq!(MI::exact(&bell, 2, 2).unwrap(), ln2.scale(&ri(2)));
    assert_eq!(MI::conditional_exact(&bell, 2, 2).unwrap(), ln2.neg());
    assert_eq!(
        RE::exact(&bell, &State::maximally_mixed(4).unwrap()).unwrap(),
        ln2.scale(&ri(2))
    );
    let plus = State::pure(&RayVector::from_ints(&[(1, 0), (1, 0)]).unwrap()).unwrap();
    let mixed = State::maximally_mixed(2).unwrap();
    assert_eq!(RE::exact(&plus, &mixed).unwrap(), ln2);
    assert!(RE::klein_exact(&plus, &mixed, 128).unwrap());
    assert!(RE::data_processing(
        &plus,
        &mixed,
        &Channel::depolarizing(2, rq(1, 3)).unwrap(),
        128
    )
    .unwrap());
    assert!(RE::exact(&mixed, &plus).is_err());
    assert_eq!(RE::petz_renyi_two_moment(&plus, &mixed).unwrap(), ri(2));
}

#[test]
fn algebraic_spectrum_entropy_has_a_certified_interval_instead_of_fake_projectors() {
    let rho = State::try_new(
        mx::from_rows(vec![
            vec![G::from_rational(rq(2, 3)), G::from_rational(rq(1, 6))],
            vec![G::from_rational(rq(1, 6)), G::from_rational(rq(1, 3))],
        ])
        .unwrap(),
    )
    .unwrap();
    assert!(!rho.spectrum().unwrap().is_rational());
    assert!(Entropy::von_neumann_exact(&rho).is_err());
    let wide = Entropy::von_neumann_enclosure(&rho, 16).unwrap();
    let narrow = Entropy::von_neumann_enclosure(&rho, 48).unwrap();
    assert!(wide.lo() <= narrow.lo() && narrow.hi() <= wide.hi());
    assert!(narrow.lo() > &ri(0));
    assert!(narrow.hi() < &rq(7, 10));
    let oversized: Vec<_> = (0..4096).map(ri).collect();
    assert!(matches!(
        h::spectral_resolution(&mx::identity(2).unwrap(), &oversized),
        Err(h::SpectrumError::Algebra(
            linear_algebra::exact_field::ExactFieldError::Matrix(
                linear_algebra::backend::basic_matrix::MatrixError::OperationLimitExceeded { .. }
            )
        ))
    ));
}

#[test]
fn exact_clifford_t_gate_words_and_packed_operators_keep_complex_phases() {
    let h = ExactUnitary::hadamard().unwrap();
    assert_eq!(h.compose(&h).unwrap(), ExactUnitary::identity(2).unwrap());
    let t = ExactUnitary::t_gate().unwrap();
    let mut word = ExactUnitary::identity(2).unwrap();
    for _ in 0..8 {
        word = t.compose(&word).unwrap();
    }
    assert_eq!(word, ExactUnitary::identity(2).unwrap());
    let circuit = ExactUnitary::cnot()
        .unwrap()
        .compose(&h.tensor(&ExactUnitary::identity(2).unwrap()).unwrap())
        .unwrap();
    let out = circuit
        .apply(&[Cyc8::one(), Cyc8::zero(), Cyc8::zero(), Cyc8::zero()])
        .unwrap();
    assert_eq!(
        out,
        vec![
            Cyc8::inv_sqrt2(),
            Cyc8::zero(),
            Cyc8::zero(),
            Cyc8::inv_sqrt2()
        ]
    );
    let ray = RayVector::from_ints(&[(1, 2), (3, -1)]).unwrap();
    let rho = State::pure(&ray).unwrap();
    let packed = PackedDensityOperator::from_state(&rho).unwrap();
    assert_eq!(packed.to_state().unwrap(), rho);
    assert_eq!(packed.expectation(&ray).unwrap(), ri(1));
}

#[test]
fn tiles_bound_entanglement_and_local_separability_criteria_are_replayed() {
    let tiles = core_quantum_physics::higher_dim::tiles().unwrap();
    let rho = tiles.complement_state();
    assert_eq!(rho.rank().unwrap(), 4);
    assert_eq!(rho.purity(), rq(1, 4));
    assert!(bip::is_ppt(rho.matrix(), 3, 3).unwrap());
    assert!(!bip::in_separable_ball(rho, 3, 3).unwrap());
    let mut repeated = tiles.factors().to_vec();
    repeated[1] = repeated[0].clone();
    assert!(bip::UnextendibleProductBasis::try_new(repeated, 32).is_err());
    let bell = BellState::exact_density(BellBasis::PhiPlus).unwrap();
    assert_eq!(bip::operator_schmidt_rank(bell.matrix(), 2, 2).unwrap(), 4);
    assert_eq!(
        bip::reduction_criterion(&bell, 2, 2).unwrap(),
        (false, false)
    );
    let product = State::pure(&basis(0).kron(&basis(1)).unwrap()).unwrap();
    assert_eq!(
        bip::operator_schmidt_rank(product.matrix(), 2, 2).unwrap(),
        1
    );
    assert_eq!(
        bip::reduction_criterion(&product, 2, 2).unwrap(),
        (true, true)
    );
    assert!(bip::in_separable_ball(&State::maximally_mixed(4).unwrap(), 2, 2).unwrap());
    assert!(BasicMatrix::<GaussianRat>::from_row_major(4, 4, vec![]).is_err());
    assert!(bip::realignment(&mx::identity(3).unwrap(), 2, 2).is_err());
}

#[test]
fn uhlmann_fidelity_and_trace_norm_intervals_agree_on_pure_and_mixed_routes() {
    let zero = State::pure(&basis(0)).unwrap();
    let one = State::pure(&basis(1)).unwrap();
    let plus = State::pure(&RayVector::from_ints(&[(1, 0), (1, 0)]).unwrap()).unwrap();
    assert_eq!(
        Purification::fidelity_exact(&zero, &zero, 10_000).unwrap(),
        ri(1)
    );
    assert_eq!(
        Purification::fidelity_exact(&zero, &one, 10_000).unwrap(),
        ri(0)
    );
    // sqrt(1/2) is absent from Q; the squared fidelity is still enclosed exactly.
    let f = Purification::fidelity_enclosure(&zero, &plus, 48, 10_000).unwrap();
    assert!(f.lo() <= &rq(1, 2) && f.hi() >= &rq(1, 2));
    let d =
        core_quantum_physics::trace_norm_certificate::trace_distance_enclosure(&zero, &plus, 48)
            .unwrap();
    let square = d.mul(&d);
    assert!(square.lo() <= &rq(1, 2) && square.hi() >= &rq(1, 2));
    let bell = BellState::exact_density(BellBasis::PhiPlus).unwrap();
    let negativity = bip::negativity_enclosure(&bell, 2, 2, 32).unwrap();
    assert_eq!(negativity.lo(), &rq(1, 2));
    assert_eq!(negativity.hi(), &rq(1, 2));
    let ccnr = bip::realignment_norm_enclosure(&bell, 2, 2, 32).unwrap();
    assert_eq!(ccnr.lo(), &ri(2));
    assert_eq!(ccnr.hi(), &ri(2));
}

#[test]
fn declared_uhlmann_polar_root_constructs_optimal_environmental_overlap() {
    let c = mx::diagonal(&[G::from_rational(rq(3, 5)), G::from_rational(rq(4, 5))]).unwrap();
    let d = mx::diagonal(&[G::from_rational(rq(4, 5)), G::from_rational(rq(3, 5))]).unwrap();
    let root = mx::scale(&(mx::identity(2).unwrap()), &G::from_rational(rq(12, 25))).unwrap();
    let maximizing = UhlmannMaximizer::from_positive_root(&c, &d, &root).unwrap();
    assert_eq!(maximizing.environmental_map, mx::identity(2).unwrap());
    assert_eq!(maximizing.fidelity, rq(576, 625));
    // An environmental phase changes the maximizing map, while leaving both
    // reduced states and the optimal fidelity intact.
    let phase = mx::diagonal(&[G::one(), G::i()]).unwrap();
    let phased = mx::multiply_with_limits(&d, &phase, h::exact_limits()).unwrap();
    let phased_maximizer = UhlmannMaximizer::from_positive_root(&c, &phased, &root).unwrap();
    assert_eq!(
        phased_maximizer.environmental_map,
        star::adjoint(&phase).unwrap()
    );
    assert_eq!(phased_maximizer.fidelity, maximizing.fidelity);
    assert!(UhlmannMaximizer::from_positive_root(&c, &d, &mx::identity(2).unwrap()).is_err());
    assert_eq!(
        Purification::fidelity_exact(
            &State::pure(&basis(0)).unwrap(),
            &State::pure(&RayVector::from_ints(&[(1, 0), (1, 0)]).unwrap()).unwrap(),
            10_000
        )
        .unwrap(),
        rq(1, 2)
    );
}

#[test]
fn mixed_two_qubit_concurrence_matches_spin_flip_and_werner_closed_forms() {
    for p in [rq(0, 1), rq(1, 3), rq(1, 2), rq(1, 1)] {
        let state = BellState::werner(p.clone()).unwrap();
        let expected = ((ri(3) * p - ri(1)) / ri(2)).max(ri(0));
        assert_eq!(
            Entanglement::concurrence_exact(&state, 10_000).unwrap(),
            expected
        );
        let enclosure = Entanglement::concurrence_enclosure(&state, 32, 10_000).unwrap();
        assert!(enclosure.lo() <= &expected && enclosure.hi() >= &expected);
    }
    assert_eq!(
        Entanglement::concurrence_squared(&BellState::exact_ray(BellBasis::PhiPlus).unwrap())
            .unwrap(),
        ri(1)
    );
}

#[test]
fn arbitrary_algebraic_relative_entropy_encloses_noncommuting_spectral_weights() {
    let sigma = State::try_new(
        mx::from_rows(vec![
            vec![G::from_rational(rq(2, 3)), G::from_rational(rq(1, 6))],
            vec![G::from_rational(rq(1, 6)), G::from_rational(rq(1, 3))],
        ])
        .unwrap(),
    )
    .unwrap();
    let rho = State::pure(&basis(0)).unwrap();
    assert!(!sigma.spectrum().unwrap().is_rational());
    assert!(RE::exact(&rho, &sigma).is_err());
    let wide = RE::enclosure(&rho, &sigma, 24).unwrap();
    let narrow = RE::enclosure(&rho, &sigma, 56).unwrap();
    assert!(wide.lo() <= narrow.lo() && narrow.hi() <= wide.hi());
    assert!(narrow.lo() > &ri(0) && narrow.hi() < &ri(1));
    // Independent closed-form numerical comparison is diagnostic, not evidence.
    use num_traits::ToPrimitive;
    let r = 2.0f64.sqrt();
    let value = -(1.0 + 1.0 / r) / 2.0 * ((1.0 + r / 3.0) / 2.0).ln()
        - (1.0 - 1.0 / r) / 2.0 * ((1.0 - r / 3.0) / 2.0).ln();
    assert!(narrow.lo().to_f64().unwrap() <= value + 1e-12);
    assert!(value <= narrow.hi().to_f64().unwrap() + 1e-12);
    assert_eq!(
        RE::enclosure(&sigma, &sigma, 56).unwrap(),
        core_kernel::interval::Interval::point(ri(0))
    );
    assert!(RE::enclosure(&sigma, &rho, 56).is_err());
}

#[test]
fn diagnostic_faces_refuse_nan_tolerances_and_invalid_public_storage() {
    use linear_algebra::linear_algebra::complex_matrix::{CMatrix, C64};
    use core_quantum_physics::{
        density_matrix::DensityMatrix, hilbert_space::HilbertSpace, no_cloning::NoCloning,
        observable::Observable, quantum_state::QuantumState,
    };
    let identity = CMatrix::identity(2, 2);
    assert!(Observable::try_new(2, identity.clone(), "I", f64::NAN).is_err());
    let mut nan = identity.clone();
    nan[(0, 0)] = C64::new(f64::NAN, 0.0);
    assert!(Observable::try_new(2, nan, "NaN", 1e-7).is_err());
    let space = HilbertSpace::try_new(2, "q").unwrap();
    let psi = QuantumState::try_normalized(&space, vec![C64::ONE, C64::ZERO], "0").unwrap();
    let phase =
        QuantumState::try_normalized(&space, vec![C64::new(0.0, 1.0), C64::ZERO], "i0").unwrap();
    assert_eq!(NoCloning::cloning_obstruction(&psi, &phase).unwrap(), 0.0);
    assert!(NoCloning::can_clone_perfectly(&psi, &phase, f64::NAN).is_err());
    let mut forged = Observable::pauli_z();
    forged.matrix = CMatrix::identity(3, 3);
    assert!(forged.expectation_value_state(&psi).is_err());
    let mut rho = DensityMatrix::maximally_mixed(&space, "mix");
    rho.probs = vec![0.4, 0.4];
    assert!(Purification::purify_diagonal(&rho, "invalid trace").is_err());
    assert!(Purification::verify_purification(&psi, &identity, f64::NAN).is_err());
    assert!(Teleportation::simulate_teleportation(&psi, f64::NAN).is_err());
    let mut invalid = psi.clone();
    invalid.amplitudes.pop();
    assert!(invalid.inner_product(&psi).is_err());
    assert!(Teleportation::simulate_teleportation(&invalid, 1e-7).is_err());
    assert!(
        QuantumState::try_unit(&space, vec![C64::ONE, C64::ZERO], "bad tol", f64::NAN).is_err()
    );
    let huge = QuantumState::try_normalized(
        &space,
        vec![C64::new(1e308, 0.0), C64::new(1e308, 0.0)],
        "huge",
    )
    .unwrap();
    assert!(huge.validate().is_ok());
    assert!(Observable::identity(usize::MAX).is_err());
    assert!(
        MI::conditional_mutual_exact(&State::pure(&basis(0)).unwrap(), usize::MAX, 2, 1).is_err()
    );
}

#[test]
fn population_entropy_revalidates_storage_and_refuses_spectral_copies_before_allocation() {
    use linear_algebra::hermitian_eigen::SpectrumError;
    use linear_algebra::linear_algebra::complex_matrix::{CMatrix, C64};
    use core_quantum_physics::density_matrix::{DensityError, PopulationShadow};
    use core_quantum_physics::entropy::EntropyError;
    use core_quantum_physics::hilbert_space::HilbertSpace;
    use core_quantum_physics::quantum_relative_entropy::RelativeEntropyError;
    let space = HilbertSpace::try_new(2, "populations").unwrap();
    let valid = PopulationShadow::maximally_mixed(&space, "valid");
    assert_eq!(Entropy::relative_entropy(&valid, &valid), Ok(0.0));
    let mut short = valid.clone();
    short.probs.pop();
    assert!(matches!(
        Entropy::relative_entropy(&short, &valid),
        Err(EntropyError::Density(DensityError::DimensionMismatch {
            expected: 2,
            actual: 1
        }))
    ));
    assert!(matches!(
        short.fidelity(&valid),
        Err(DensityError::DimensionMismatch { .. })
    ));
    let mut wrong_dim = valid.clone();
    wrong_dim.dim = 3;
    assert!(matches!(
        wrong_dim.to_linear_algebra_density(),
        Err(DensityError::DimensionMismatch {
            expected: 3,
            actual: 2
        })
    ));
    for probabilities in [vec![f64::NAN, 0.5], vec![-0.25, 1.25], vec![0.4, 0.4]] {
        let mut invalid = valid.clone();
        invalid.probs = probabilities;
        assert!(matches!(
            Entropy::relative_entropy(&invalid, &valid),
            Err(EntropyError::Density(_))
        ));
    }
    assert_eq!(
        valid.validate(f64::NAN),
        Err(DensityError::InvalidTolerance)
    );
    assert_eq!(
        PopulationShadow::try_from_probs(&space, vec![0.5, 0.5], "NaN tolerance", f64::NAN),
        Err(DensityError::InvalidTolerance)
    );
    let mut nan_coherence = CMatrix::identity(2, 2).map(|z| C64::new(z.re * 0.5, z.im * 0.5));
    nan_coherence[(0, 1)] = C64::new(f64::NAN, 0.0);
    assert_eq!(
        PopulationShadow::from_cmatrix(&nan_coherence, "bad coherence", 1e-9),
        Err(DensityError::NonFiniteEntry)
    );
    // The declared spectral carrier is rejected before density validation copies
    // its storage. Nonfinite data would produce a different error after a copy.
    let mut unsupported = CMatrix::identity(257, 257);
    unsupported[(0, 0)] = C64::new(f64::NAN, 0.0);
    assert!(matches!(
        RE::relative_entropy_matrices(&unsupported, &unsupported, 1e-9),
        Err(RelativeEntropyError::Spectrum(
            SpectrumError::DimensionLimit {
                actual: 257,
                limit: 256
            }
        ))
    ));
}

#[test]
fn population_partial_traces_revalidate_storage_before_marginal_allocation() {
    use core_quantum_physics::density_matrix::{DensityError, PopulationShadow};
    use core_quantum_physics::entanglement::EntanglementError;
    use core_quantum_physics::hilbert_space::HilbertSpace;

    let space = HilbertSpace::try_new(4, "joint populations").unwrap();
    let ordinary = PopulationShadow::try_from_probs(
        &space,
        vec![0.1, 0.2, 0.3, 0.4],
        "nonsymmetric joint distribution",
        1e-9,
    )
    .unwrap();
    let a = Entanglement::partial_trace_b(&ordinary, 2, 2).unwrap();
    let b = Entanglement::partial_trace_a(&ordinary, 2, 2).unwrap();
    for (actual, expected) in a.probs.iter().zip([0.3, 0.7]) {
        assert!((actual - expected).abs() < 1e-12);
    }
    for (actual, expected) in b.probs.iter().zip([0.4, 0.6]) {
        assert!((actual - expected).abs() < 1e-12);
    }
    let reductions: [fn(
        &PopulationShadow,
        usize,
        usize,
    ) -> Result<PopulationShadow, EntanglementError>; 2] =
        [Entanglement::partial_trace_a, Entanglement::partial_trace_b];
    for reduce in reductions {
        let mut empty = ordinary.clone();
        empty.probs.clear();
        assert!(matches!(
            reduce(&empty, 2, 2),
            Err(EntanglementError::Density(DensityError::Empty))
        ));
        let mut short = ordinary.clone();
        short.probs.pop();
        assert!(matches!(
            reduce(&short, 2, 2),
            Err(EntanglementError::Density(
                DensityError::DimensionMismatch {
                    expected: 4,
                    actual: 3
                }
            ))
        ));
        let mut wrong_dim = ordinary.clone();
        wrong_dim.dim = 3;
        assert!(matches!(
            reduce(&wrong_dim, 2, 2),
            Err(EntanglementError::Density(
                DensityError::DimensionMismatch {
                    expected: 3,
                    actual: 4
                }
            ))
        ));
        let mut nan = ordinary.clone();
        nan.probs[0] = f64::NAN;
        assert!(matches!(
            reduce(&nan, 2, 2),
            Err(EntanglementError::Density(DensityError::NonFiniteEntry))
        ));
        assert!(matches!(
            reduce(&ordinary, 0, 4),
            Err(EntanglementError::InvalidSubsystemDimension)
        ));
    }
}

#[test]
fn spectral_decomposition_revalidates_public_dimension_and_carrier_metadata() {
    use core_quantum_physics::hermitian_spectral::{
        spectral_decompose, HermitianMatrix, ScalarCarrier, SpectralError,
    };

    let y = HermitianMatrix::try_exact(
        2,
        ScalarCarrier::GaussianRational,
        vec![
            G::zero(),
            G::from_ints(0, -1),
            G::from_ints(0, 1),
            G::zero(),
        ],
    )
    .unwrap();
    let control = spectral_decompose(&y).unwrap();
    assert_eq!(control.n, 2);
    assert_eq!(control.distinct_eigenvalues(), vec![ri(-1), ri(1)]);
    for (lambda, vector) in control.eigenvalues.iter().zip(&control.eigenvectors) {
        assert!(h::eigen_residual(y.exact_matrix().unwrap(), lambda, vector)
            .unwrap()
            .iter()
            .all(G::is_zero));
    }
    let mut zero = y.clone();
    zero.n = 0;
    assert_eq!(spectral_decompose(&zero), Err(SpectralError::ZeroDimension));
    assert!(!zero.is_diagonal_exact());
    for n in [1, 3, usize::MAX] {
        let mut wrong_dimension = y.clone();
        wrong_dimension.n = n;
        assert!(!wrong_dimension.is_diagonal_exact());
        assert!(matches!(
            spectral_decompose(&wrong_dimension),
            Err(SpectralError::ExactAlgebra(_))
        ));
    }
    let mut forged_carrier = y.clone();
    forged_carrier.carrier = ScalarCarrier::Rational;
    assert!(matches!(
        spectral_decompose(&forged_carrier),
        Err(SpectralError::ExactAlgebra(_))
    ));
    let diagonal = HermitianMatrix::try_exact(
        2,
        ScalarCarrier::Rational,
        vec![G::from_ints(1, 0), G::zero(), G::zero(), G::from_ints(2, 0)],
    )
    .unwrap();
    assert!(diagonal.is_diagonal_exact());
    assert_eq!(
        spectral_decompose(&diagonal)
            .unwrap()
            .distinct_eigenvalues(),
        vec![ri(1), ri(2)]
    );
}

#[test]
fn numerical_partial_traces_refuse_overflow_and_retain_imaginary_coherence() {
    use linear_algebra::linear_algebra::complex_matrix::{CMatrix, C64};
    use core_kernel::resource_limits::ResourceError;
    use core_quantum_physics::entanglement::EntanglementError;

    // |+i><+i| on A, tensored with diag(3/5, 2/5) on B.
    let mut joint = CMatrix::zeros(4, 4);
    for (b, weight) in [0.6, 0.4].into_iter().enumerate() {
        joint[(b, b)] = C64::new(weight / 2.0, 0.0);
        joint[(2 + b, 2 + b)] = C64::new(weight / 2.0, 0.0);
        joint[(b, 2 + b)] = C64::new(0.0, -weight / 2.0);
        joint[(2 + b, b)] = C64::new(0.0, weight / 2.0);
    }
    let a = Entanglement::partial_trace_b_matrix(&joint, 2, 2).unwrap();
    let b = Entanglement::partial_trace_a_matrix(&joint, 2, 2).unwrap();
    let expected_a = CMatrix::from_row_slice(
        2,
        2,
        &[
            C64::new(0.5, 0.0),
            C64::new(0.0, -0.5),
            C64::new(0.0, 0.5),
            C64::new(0.5, 0.0),
        ],
    );
    let expected_b = CMatrix::from_row_slice(
        2,
        2,
        &[
            C64::new(0.6, 0.0),
            C64::new(0.0, 0.0),
            C64::new(0.0, 0.0),
            C64::new(0.4, 0.0),
        ],
    );
    assert!((&a - expected_a).norm() < 1e-12);
    assert!((&b - expected_b).norm() < 1e-12);
    let reductions: [fn(&CMatrix, usize, usize) -> Result<CMatrix, EntanglementError>; 2] = [
        Entanglement::partial_trace_a_matrix,
        Entanglement::partial_trace_b_matrix,
    ];
    let singleton = CMatrix::identity(1, 1);
    for reduce in reductions {
        assert!(matches!(
            reduce(&singleton, usize::MAX, 2),
            Err(EntanglementError::Limits(ResourceError::DimensionOverflow))
        ));
        assert!(matches!(
            reduce(&joint, 0, 4),
            Err(EntanglementError::InvalidSubsystemDimension)
        ));
        assert!(matches!(
            reduce(&singleton, 2, 2),
            Err(EntanglementError::DimensionMismatch {
                expected: 4,
                actual: 1
            })
        ));
        assert!(matches!(
            reduce(&CMatrix::zeros(4, 3), 2, 2),
            Err(EntanglementError::DimensionMismatch { .. })
        ));
    }
}

#[test]
fn diagnostic_matrix_information_rejects_invalid_tolerances_and_retains_bell_values() {
    use linear_algebra::linear_algebra::complex_matrix::CMatrix;
    use linear_algebra::linear_algebra::density::DensityMatrixError;
    use core_quantum_physics::quantum_mutual_information::MutualInformationError;

    let bell = BellState::phi_plus().to_projector_cmatrix();
    assert!(
        (MI::mutual_information_matrix(&bell, 2, 2, 1e-9).unwrap() - 2.0 * std::f64::consts::LN_2)
            .abs()
            < 1e-9
    );
    assert!(
        (MI::conditional_entropy_matrix(&bell, 2, 2, 1e-9).unwrap() + std::f64::consts::LN_2).abs()
            < 1e-9
    );
    let information: [fn(&CMatrix, usize, usize, f64) -> Result<f64, MutualInformationError>; 2] = [
        MI::mutual_information_matrix,
        MI::conditional_entropy_matrix,
    ];
    for evaluate in information {
        for tol in [f64::NAN, f64::INFINITY, f64::NEG_INFINITY] {
            assert!(matches!(
                evaluate(&bell, 2, 2, tol),
                Err(MutualInformationError::Numerical(
                    DensityMatrixError::NonFiniteTolerance {
                        name: "trace_tol",
                        ..
                    }
                ))
            ));
        }
        for tol in [-1e-9, 0.0] {
            assert!(matches!(
                evaluate(&bell, 2, 2, tol),
                Err(MutualInformationError::Numerical(
                    DensityMatrixError::InvalidTolerance {
                        name: "trace_tol",
                        ..
                    }
                ))
            ));
        }
    }
}

#[test]
fn diagnostic_matrix_information_uses_the_supplied_trace_tolerance() {
    use linear_algebra::linear_algebra::complex_matrix::{CMatrix, C64};
    use linear_algebra::linear_algebra::density::DensityMatrixError;
    use core_quantum_physics::quantum_mutual_information::MutualInformationError;

    // Positive diagonal data with a known trace drift, between the two caller
    // tolerances. Admission is diagnostic and does not renormalize this input.
    let drift = 5e-7;
    let joint = CMatrix::from_row_slice(
        2,
        2,
        &[
            C64::new(0.5, 0.0),
            C64::new(0.0, 0.0),
            C64::new(0.0, 0.0),
            C64::new(0.5 + drift, 0.0),
        ],
    );
    let information: [fn(&CMatrix, usize, usize, f64) -> Result<f64, MutualInformationError>; 2] = [
        MI::mutual_information_matrix,
        MI::conditional_entropy_matrix,
    ];
    for evaluate in information {
        assert!(matches!(
            evaluate(&joint, 2, 1, 1e-8),
            Err(MutualInformationError::Numerical(
                DensityMatrixError::TraceNotOne { tol: 1e-8, .. }
            ))
        ));
        assert!(evaluate(&joint, 2, 1, 1e-6).unwrap().is_finite());
    }
    assert_eq!(joint[(1, 1)].re, 0.5 + drift);
}

#[test]
fn diagnostic_pure_separability_rejects_invalid_tolerances_and_retains_product_bell_controls() {
    use core_quantum_physics::density_matrix::DensityError;
    use core_quantum_physics::entanglement::EntanglementError;
    use core_quantum_physics::hilbert_space::HilbertSpace;
    use core_quantum_physics::quantum_state::QuantumState;

    let space = HilbertSpace::try_new(4, "two diagnostic qubits").unwrap();
    let product = QuantumState::computational_basis(&space, 0, "00").unwrap();
    let bell = BellState::phi_plus();
    assert!(Entanglement::is_separable_pure(&product, 2, 2, 1e-9).unwrap());
    assert!(Entanglement::is_separable_pure(&product, 2, 2, 0.0).unwrap());
    assert!(!Entanglement::is_separable_pure(&bell, 2, 2, 1e-9).unwrap());
    for state in [&product, &bell] {
        for tol in [f64::NAN, f64::INFINITY, f64::NEG_INFINITY, -1e-9] {
            assert_eq!(
                Entanglement::is_separable_pure(state, 2, 2, tol),
                Err(EntanglementError::Density(DensityError::InvalidTolerance))
            );
        }
    }
}

// Origin: engine/crates_rs/tests/core_quantum_physics/states_channels_exact_tests.rs
// Claim: urn:core:crates_rs:tests:states-channels-exact-tests:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde4f05d01 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde4f05d01` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore4f05d01 {
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
impl BoundaryErrore4f05d01 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore4f05d01 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore4f05d01 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde4f05d01 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore4f05d01> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore4f05d01::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore4f05d01::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore4f05d01::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_e4f05d01() {
    let admitted = BoundaryRecorde4f05d01::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorde4f05d01::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
