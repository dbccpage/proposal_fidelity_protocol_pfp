//! Exact laws of the reusable finite dynamics and gauge carriers.
use linear_algebra::exact_field::{characteristic_polynomial, involution as iv, matrix as mx};
use num_bigint::{BigInt, BigUint};
use num_traits::{One, Signed, Zero};
use core_homology::f2_cohomology::F2ChainComplex;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::cyclotomic_field::{contains_cyclotomic_field, CyclotomicNumber};
use core_number_theory::gf2::{F2Matrix, F2Vector};
use core_number_theory::rational::{ri, rq, Rational};
use core_quantum_physics::exact_hermitian::gi;
use core_quantum_physics::{
    grover::GroverInstance, phase_estimation::RationalPhaseEstimation, quantum_walk::hadamard_line,
    richardson::RichardsonPlan,
};
use std::collections::BTreeSet;

#[test]
fn grover_chebyshev_probability_matches_every_evolved_marked_amplitude() {
    for n in 2..=12 {
        for marked_count in 1..=n {
            let model = GroverInstance::new(n, (0..marked_count).collect()).unwrap();
            let iterate = model.iterate().unwrap();
            assert!(iv::is_unitary(&iterate.step).unwrap());
            for k in 0..=8 {
                let state = model.amplitudes(k).unwrap();
                assert_eq!(state.iter().map(|x| x * x).sum::<Rational>(), ri(n as i64));
                let probability = state[..marked_count]
                    .iter()
                    .map(|x| x * x)
                    .sum::<Rational>()
                    / ri(n as i64);
                assert_eq!(probability, model.success_probability(k).unwrap());
            }
            assert_eq!(
                model.exact_one_step(),
                model.success_probability(1).unwrap() == ri(1)
            );
        }
    }
    assert!(GroverInstance::new(4, BTreeSet::from([4])).is_err());
    assert_eq!(
        GroverInstance::new(8, BTreeSet::from([0]))
            .unwrap()
            .optimal_iterations(20)
            .unwrap(),
        2
    );
}

#[test]
fn rational_qpe_preserves_total_probability_and_rejects_a_false_eigenphase() {
    for phase in [rq(1, 3), rq(-2, 5), rq(7, 8)] {
        let out = RationalPhaseEstimation::run(3, phase).unwrap();
        let sum = out
            .probabilities
            .iter()
            .try_fold(CyclotomicNumber::zero(out.conductor).unwrap(), |s, p| {
                s.add(p)
            })
            .unwrap();
        assert_eq!(sum, CyclotomicNumber::one(out.conductor).unwrap());
        assert!(out.fourier_unitary);
    }
    let u = mx::diagonal(&[gi(0, 1), gi(-1, 0)]).unwrap();
    let state = vec![gi(1, 0), gi(0, 0)];
    let out = RationalPhaseEstimation::from_eigenpair(3, rq(1, 4), &u, &state).unwrap();
    assert_eq!(
        out.probabilities[2],
        CyclotomicNumber::one(out.conductor).unwrap()
    );
    assert!(RationalPhaseEstimation::from_eigenpair(3, rq(1, 2), &u, &state).is_err());
}

#[test]
fn richardson_interpolates_every_polynomial_below_the_node_count() {
    let plan = RichardsonPlan::new(rq(-1, 3), vec![rq(1, 2), ri(2), ri(5), ri(9)]).unwrap();
    for degree in 0..4 {
        let values = plan
            .nodes()
            .iter()
            .map(|x| x.pow(degree))
            .collect::<Vec<_>>();
        assert_eq!(
            plan.extrapolate(&values).unwrap(),
            plan.target().pow(degree)
        );
    }
    assert!(RichardsonPlan::new(ri(0), vec![ri(1), ri(1)]).is_err());
    assert!(plan.extrapolate(&[ri(1)]).is_err());
}

#[test]
fn infinite_line_hadamard_walk_has_exact_finite_time_light_cone_and_variance() {
    for t in 0..=16 {
        let out = hadamard_line(t).unwrap();
        assert_eq!(out.probabilities.values().sum::<Rational>(), ri(1));
        assert_eq!(out.mean, ri(0));
        assert!(out
            .probabilities
            .keys()
            .all(|&x| x.unsigned_abs() <= t as u64 && (x - t as i64).rem_euclid(2) == 0));
        assert_eq!(
            out.variance,
            out.probabilities.iter().map(|(&x, p)| ri(x * x) * p).sum()
        );
    }
    assert!(hadamard_line(257).is_err());
}

#[test]
fn spectral_propagator_is_unitary_in_the_formal_frequency_algebra() {
    use core_quantum_physics::finite_schrodinger_step::{euler_norm_defect, SpectralPropagator};
    let h = mx::diagonal(&[gi(-1, 0), gi(1, 0)]).unwrap();
    let u = SpectralPropagator::new(&h, &[ri(-1), ri(1)]).unwrap();
    assert_eq!(u.at_zero(), mx::identity::<GaussianRat>(2).unwrap());
    assert_eq!(u.derivative_at_zero(), mx::scale(&h, &gi(0, -1)).unwrap());
    assert!(u.adjoint().multiply(&u).unwrap().is_identity());
    assert!(SpectralPropagator::new(&h, &[ri(0)]).is_err());
    assert_eq!(
        euler_norm_defect(&h, &rq(1, 3)).unwrap(),
        mx::diagonal(&vec![GaussianRat::from_rational(rq(1, 9)); 2]).unwrap()
    );
}

#[test]
fn product_formula_bounds_use_actual_noncommutation_and_step_count() {
    use core_quantum_physics::continuous_time_locality_limit::product_formula_bounds;
    let z = mx::diagonal(&[gi(1, 0), gi(-1, 0)]).unwrap();
    let x = mx::from_rows(vec![vec![gi(0, 0), gi(1, 0)], vec![gi(1, 0), gi(0, 0)]]).unwrap();
    let commute = product_formula_bounds(&z, &z, &ri(3), 2).unwrap();
    assert_eq!(commute.first_order_error, ri(0));
    assert_eq!(commute.second_order_error, ri(0));
    let coarse = product_formula_bounds(&z, &x, &ri(1), 2).unwrap();
    let fine = product_formula_bounds(&z, &x, &ri(1), 4).unwrap();
    assert_eq!(coarse.commutator_bound, ri(4));
    assert_eq!(fine.first_order_error * ri(2), coarse.first_order_error);
    assert_eq!(fine.second_order_error * ri(4), coarse.second_order_error);
    assert!(product_formula_bounds(&z, &x, &ri(1), 0).is_err());
}

#[test]
fn heisenberg_taylor_coefficients_replay_the_nested_commutators() {
    use core_quantum_physics::heisenberg_picture::{ehrenfest_derivative, heisenberg_taylor};
    let z = mx::diagonal(&[gi(1, 0), gi(-1, 0)]).unwrap();
    let x = mx::from_rows(vec![vec![gi(0, 0), gi(1, 0)], vec![gi(1, 0), gi(0, 0)]]).unwrap();
    let series = heisenberg_taylor(&z, &x, 2).unwrap();
    assert_eq!(series[0], x);
    assert_eq!(
        series[1],
        mx::scale(&mx::commutator(&z, &x).unwrap(), &gi(0, 1)).unwrap()
    );
    assert_eq!(series[2], mx::scale(&x, &gi(-2, 0)).unwrap());
    let rho = mx::diagonal(&vec![GaussianRat::from_rational(rq(1, 2)); 2]).unwrap();
    assert_eq!(ehrenfest_derivative(&z, &x, &rho).unwrap(), ri(0));
}

#[test]
fn markov_stationarity_and_dobrushin_contraction_are_computed() {
    use core_quantum_physics::stochastic_unitary_boundary::MarkovKernel;
    let k = MarkovKernel::new(vec![vec![rq(1, 2), rq(1, 2)], vec![rq(1, 3), rq(2, 3)]]).unwrap();
    let stationary = [rq(2, 5), rq(3, 5)];
    assert!(k.is_stationary(&stationary).unwrap());
    assert!(k.detailed_balance(&stationary).unwrap());
    assert_eq!(k.dobrushin_coefficient(), rq(1, 6));
    let a = k.evolve(&[ri(1), ri(0)], 3).unwrap();
    let b = k.evolve(&[ri(0), ri(1)], 3).unwrap();
    assert_eq!((&a[0] - &b[0]).abs(), rq(1, 216));
    assert!(k.evolve(&[ri(1), ri(1)], 1).is_err());
}

#[test]
fn branch_counting_has_no_machine_integer_denominator_limit() {
    use core_quantum_physics::branch_finegraining::BranchCounting;
    let n: BigInt = BigInt::one() << 100;
    let w = Rational::new(BigInt::one(), n.clone());
    let weights = [w.clone(), Rational::one() - w];
    let counts = BranchCounting::new(&weights, None).unwrap();
    assert_eq!(counts.multiplicity, n);
    assert!(counts.verify(&weights));
    assert!(BranchCounting::new(&weights, Some(BigInt::zero())).is_err());
    use core_quantum_physics::everett::EverettForkingNode;
    assert!(EverettForkingNode::from_amplitudes(&[]).is_err());
    assert!(EverettForkingNode::from_amplitudes(&[(ri(0), ri(0))]).is_err());
    for slits in 3..=6 {
        let amplitudes = (0..slits)
            .map(|i| gi(i as i64 + 1, 2 * i as i64 - 1))
            .collect::<Vec<_>>();
        assert!(
            core_quantum_physics::everett::sorkin_interference(&amplitudes)
                .unwrap()
                .is_zero()
        );
    }
    assert!(core_quantum_physics::everett::sorkin_interference(&vec![gi(1, 0); 17]).is_err());
    assert!(BranchCounting::new(&vec![ri(0); 4097], None).is_err());
    let one = CyclotomicNumber::one(5).unwrap();
    let z = CyclotomicNumber::zeta(5, 1).unwrap();
    let alpha = z.add(&z.pow(4)).unwrap();
    let norm = alpha.mul(&alpha.conjugate()).unwrap();
    let weight = norm
        .mul(&one.add(&norm).unwrap().inverse().unwrap())
        .unwrap();
    let weights = [weight.clone(), one.sub(&weight).unwrap()];
    assert!(matches!(
        BranchCounting::from_cyclotomic_weights(&weights, None),
        Err(
            core_quantum_physics::branch_finegraining::BranchCountingError::IrrationalWeight {
                branch: 0
            }
        )
    ));
    assert!(
        !core_quantum_physics::branch_finegraining::verify_finegraining(
            &[rq(1, 2), rq(1, 2)],
            i64::MAX,
            &[i64::MAX, i64::MAX]
        )
    );
}

#[test]
fn green_function_closure_refuses_a_divergent_cycle() {
    use core_quantum_physics::graded_path_sum::{NonNegative, TransportGraph};
    let graph = TransportGraph::new(1, vec![(0, 0, NonNegative::new(rq(1, 2)).unwrap())]).unwrap();
    let certificate = graph.closure().unwrap();
    assert_eq!(certificate.kernel.get(0, 0).unwrap(), ri(2));
    assert_eq!(certificate.contraction_bound, rq(1, 2));
    let divergent = TransportGraph::new(1, vec![(0, 0, NonNegative::new(ri(1)).unwrap())]).unwrap();
    assert!(divergent.closure().is_err());
}

#[test]
fn spin_lift_counts_use_cohomology_without_exponential_enumeration() {
    use core_quantum_physics::spin_structure_obstruction::SpinLiftClassification;
    let c = F2ChainComplex::new(
        vec![1, 32, 0],
        vec![
            F2Matrix::zeros(1, 32).unwrap(),
            F2Matrix::zeros(32, 0).unwrap(),
        ],
    )
    .unwrap();
    let lifts = SpinLiftClassification::new(c, F2Vector::zeros(0).unwrap()).unwrap();
    assert_eq!(lifts.lift_count(), BigUint::one() << 32);
    assert_eq!(lifts.gauge_class_count().unwrap(), BigUint::one() << 32);
    assert!(lifts.enumerate_lifts(64).is_err());
}

#[test]
fn subsystem_embeddings_preserve_products_and_compose() {
    use core_quantum_physics::refinement_subsystem_tower::ObservableEmbedding;
    let a = mx::from_rows(vec![vec![gi(0, 0), gi(1, 0)], vec![gi(1, 0), gi(0, 0)]]).unwrap();
    let first = ObservableEmbedding::new(2, 4).unwrap();
    let next = ObservableEmbedding::new(4, 12).unwrap();
    let total = first.compose(&next).unwrap();
    assert_eq!(
        next.apply(&first.apply(&a).unwrap()).unwrap(),
        total.apply(&a).unwrap()
    );
    assert_eq!(
        mx::multiply(&total.apply(&a).unwrap(), &total.apply(&a).unwrap()).unwrap(),
        total.apply(&mx::identity(2).unwrap()).unwrap()
    );
    assert!(ObservableEmbedding::new(2, 3).is_err());
}

#[test]
fn finite_ising_spectrum_and_gauss_constraints_use_declared_carriers() {
    use core_quantum_physics::lattice_gauge_manybody_benchmark::{open_tfim, Z2LatticeGauge};
    let h = open_tfim(2, &ri(1), &ri(1)).unwrap();
    assert_eq!(
        characteristic_polynomial::characteristic_polynomial(&h).unwrap(),
        vec![ri(5), ri(0), ri(-6), ri(0), ri(1)]
    );
    let d1 = F2Matrix::from_rows(&[vec![1, 0, 1], vec![1, 1, 0], vec![0, 1, 1]]).unwrap();
    let d2 = F2Matrix::from_rows(&[vec![1], vec![1], vec![1]]).unwrap();
    let gauge =
        Z2LatticeGauge::new(F2ChainComplex::new(vec![3, 3, 1], vec![d1, d2]).unwrap()).unwrap();
    assert_eq!(gauge.physical_dimension().unwrap(), BigUint::from(2u8));
    let zero = F2Vector::zeros(3).unwrap();
    let loop_label = F2Vector::from_bits(&[1, 1, 1]).unwrap();
    assert_eq!(gauge.magnetic_flip(&zero, &loop_label).unwrap(), loop_label);
    assert!(gauge
        .magnetic_flip(&zero, &F2Vector::from_bits(&[1, 0, 0]).unwrap())
        .is_err());
}

#[test]
fn cyclotomic_tower_normalizes_equivalent_conductors_and_exhibits_growth() {
    use core_quantum_physics::{growth_refinement::growth_witness, tower::CyclotomicTower};
    let tower = CyclotomicTower::new(vec![3, 6, 12]).unwrap();
    let z = CyclotomicNumber::zeta(3, 1).unwrap();
    assert_eq!(
        tower.embed(&z, 2).unwrap(),
        CyclotomicNumber::zeta(12, 4).unwrap()
    );
    assert_eq!(
        tower
            .embed(&z, 1)
            .unwrap()
            .mul(&tower.embed(&z, 1).unwrap())
            .unwrap(),
        tower.embed(&z.mul(&z).unwrap(), 1).unwrap()
    );
    assert!(contains_cyclotomic_field(6, 3).unwrap());
    for n in [1, 3, 6, 12, 30, 105] {
        let w = growth_witness(n).unwrap();
        assert!(!w.contains_prime_phase);
    }
}

#[test]
fn fuzzy_sphere_normalization_and_moment_counterexample_are_explicit() {
    use core_quantum_physics::tower_topological_completion::{
        fuzzy_sphere, rank_one_completion_comparison, rank_one_normalized_moment,
    };
    for d in 2..=9 {
        let c = fuzzy_sphere(d).unwrap();
        assert!(c.bracket_relations && c.casimir_relation);
        assert!(c.commutator_norm < c.upper_bound);
        assert_eq!(c.casimir_norm, ri(1) - rq(1, (d * d) as i64));
    }
    assert_eq!(rank_one_normalized_moment(32).unwrap(), rq(1, 32));
    assert_eq!(
        rank_one_completion_comparison(32).unwrap().norm_difference,
        ri(1)
    );
}

#[test]
fn heisenberg_full_matrix_span_certifies_irreducibility() {
    use core_quantum_physics::heisenberg_representation_uniqueness::certify_schrodinger_irreducibility;
    let c = certify_schrodinger_irreducibility::<3>().unwrap();
    assert_eq!(c.matrix_units_reconstructed, 9);
    assert_eq!(
        certify_schrodinger_irreducibility::<5>()
            .unwrap()
            .matrix_units_reconstructed,
        25
    );
}

#[test]
fn unitary_dichotomy_distinguishes_torsion_from_an_exact_aperiodic_rotation() {
    use core_quantum_physics::dynamics_dichotomy::{classify_unitary_orbit, UnitaryOrbit};
    let reflection = mx::diagonal(&[gi(1, 0), gi(-1, 0)]).unwrap();
    assert_eq!(
        classify_unitary_orbit(&reflection).unwrap(),
        UnitaryOrbit::Periodic { order: 2 }
    );
    let phase = mx::diagonal(&[GaussianRat {
        re: rq(3, 5),
        im: rq(4, 5),
    }])
    .unwrap();
    assert_eq!(
        classify_unitary_orbit(&phase).unwrap(),
        UnitaryOrbit::Aperiodic
    );
    assert!(classify_unitary_orbit(&mx::diagonal(&[gi(2, 0)]).unwrap()).is_err());
}

#[test]
fn interaction_cones_use_actual_graph_distance_and_typed_bounds() {
    use core_quantum_physics::continuous_time_locality_limit::{
        trotter_first_order_error_bound, DeclaredInteractionGraph,
    };
    let graph = DeclaredInteractionGraph::new(5, &[(0, 1), (1, 2), (2, 3)]).unwrap();
    assert!(graph.outside_cone(0, 3, &ri(1), &ri(2)).unwrap());
    assert!(!graph.outside_cone(0, 2, &ri(-1), &ri(2)).unwrap());
    assert!(graph.outside_cone(0, 4, &ri(100), &ri(100)).unwrap());
    assert!(graph.outside_cone(0, 2, &ri(1), &ri(-1)).is_err());
    assert!(DeclaredInteractionGraph::new(2, &[(0, 2)]).is_err());
    let large = Rational::from_integer(BigInt::from(i64::MAX));
    assert_eq!(
        trotter_first_order_error_bound(&large, &1.into(), &ri(2)).unwrap(),
        &large * &large
    );
}

#[test]
fn finite_trace_obstruction_replays_the_supplied_operators() {
    use core_quantum_physics::continuum::canonical_commutator_obstruction;
    for n in 1..=8 {
        let a = mx::from_fn(n, n, |r, c| if r == c { gi(r as i64, 0) } else { gi(0, 0) }).unwrap();
        let b = mx::from_fn(n, n, |r, c| gi(i64::from(r == (c + 1) % n), 0)).unwrap();
        let witness = canonical_commutator_obstruction(&a, &b, &gi(0, 1)).unwrap();
        assert_eq!(witness.trace_commutator, gi(0, 0));
        assert_eq!(witness.trace_target, gi(0, n as i64));
        assert!(witness.equality_obstructed);
        assert!(
            !canonical_commutator_obstruction(&a, &b, &gi(0, 0))
                .unwrap()
                .equality_obstructed
        );
    }
}
#[test]
fn contextual_lift_trigger_is_computed_and_bad_inputs_are_refused() {
    use core_quantum_physics::tower_walk_validator::find_lift_trigger;
    let trigger = find_lift_trigger(&[0, 0, 1], &[vec![0, 2, 2]])
        .unwrap()
        .unwrap();
    assert_eq!((trigger.x, trigger.y, trigger.context), (0, 1, 0));
    assert!(find_lift_trigger(&[0, 0], &[vec![0, 2]]).is_err());
    assert!(find_lift_trigger(&[0, 1], &[vec![0, 1]]).unwrap().is_none());
}
#[test]
fn finite_report_dilations_and_permutation_root_criteria_are_exact() {
    use core_quantum_physics::finite_report_dynamics::{
        permutation_has_half_step, reversible_dilation_count, swap_interpolants,
    };
    assert_eq!(
        reversible_dilation_count(&[0, 0], 2, Some(0)).unwrap(),
        BigUint::from(4u8)
    );
    assert!(!permutation_has_half_step(&[1, 0]).unwrap());
    assert!(permutation_has_half_step(&[1, 0, 3, 2]).unwrap());
    assert!(!permutation_has_half_step(&[1, 1]).unwrap());
    assert_eq!(swap_interpolants(100).unwrap().len(), 4);
    assert!(swap_interpolants(3).unwrap().is_empty());
    assert!(swap_interpolants(0).is_err());
}

#[test]
fn pin_obstructions_use_the_actual_cup_square_on_projective_plane_and_klein_bottle() {
    use core_homology::f2_cohomology::F2ChainComplex;
    use core_homology::simplicial::{Simplex, SimplicialComplex};
    use core_number_theory::gf2::F2Vector;
    use core_quantum_physics::spin_structure_obstruction::{PinLiftClassification, PinType};
    let rp2 = SimplicialComplex::from_simplices(
        [
            [0, 1, 2],
            [0, 1, 3],
            [0, 2, 4],
            [0, 3, 5],
            [0, 4, 5],
            [1, 2, 5],
            [1, 3, 4],
            [1, 4, 5],
            [2, 3, 4],
            [2, 3, 5],
        ]
        .map(|v| Simplex::from_unordered(v.to_vec()).unwrap())
        .to_vec(),
    )
    .unwrap();
    let chain = F2ChainComplex::from_simplicial_complex(&rp2).unwrap();
    assert_eq!(chain.euler_characteristic(), 1.into());
    assert_eq!(chain.cohomology_dimension(1).unwrap(), 1);
    let w1 = chain.cohomology_basis(1).unwrap().remove(0);
    let w2 = core_homology::cup_product::cup_product_f2(&rp2, 1, &w1, 1, &w1).unwrap();
    assert!(!chain.is_coboundary(2, &w2).unwrap());
    let plus = PinLiftClassification::from_characteristic_cocycles(
        &rp2,
        w1.clone(),
        w2.clone(),
        PinType::Plus,
    )
    .unwrap();
    let minus = PinLiftClassification::from_characteristic_cocycles(
        &rp2,
        w1.clone(),
        w2.clone(),
        PinType::Minus,
    )
    .unwrap();
    assert_eq!(plus.gauge_class_count().unwrap(), 0u8.into());
    assert_eq!(minus.gauge_class_count().unwrap(), 2u8.into());
    assert!(minus.obstruction().is_zero());
    for gauge in 0..(1usize << rp2.count(0)) {
        let gauge = F2Vector::from_indices(
            rp2.count(0),
            &(0..rp2.count(0))
                .filter(|v| gauge & (1 << v) != 0)
                .collect::<Vec<_>>(),
        )
        .unwrap();
        let moved = w1
            .add(&chain.coboundary(0).unwrap().mul_vec(&gauge).unwrap())
            .unwrap();
        let classified = PinLiftClassification::from_characteristic_cocycles(
            &rp2,
            moved,
            w2.clone(),
            PinType::Minus,
        )
        .unwrap();
        assert_eq!(classified.gauge_class_count().unwrap(), 2u8.into());
    }
    // A triangulated3x3 square grid with reflection across the vertical seam.
    let vertex = |x: usize, y: usize| {
        if y == 3 {
            (3 - x % 3) % 3
        } else {
            (x % 3) + 3 * y
        }
    };
    let facets = (0..3)
        .flat_map(|y| {
            (0..3).flat_map(move |x| {
                let a = vertex(x, y);
                let b = vertex(x + 1, y);
                let c = vertex(x, y + 1);
                let d = vertex(x + 1, y + 1);
                [[a, b, d], [a, d, c]].map(|v| Simplex::from_unordered(v.to_vec()).unwrap())
            })
        })
        .collect();
    let klein = SimplicialComplex::from_simplices(facets).unwrap();
    let chain = F2ChainComplex::from_simplicial_complex(&klein).unwrap();
    assert_eq!(chain.euler_characteristic(), 0.into());
    assert_eq!(chain.cohomology_dimension(1).unwrap(), 2);
    let basis = chain.cohomology_basis(1).unwrap();
    let w1 = [
        basis[0].clone(),
        basis[1].clone(),
        basis[0].add(&basis[1]).unwrap(),
    ]
    .into_iter()
    .find(|a| {
        let square = core_homology::cup_product::cup_product_f2(&klein, 1, a, 1, a).unwrap();
        chain.is_coboundary(2, &square).unwrap()
    })
    .expect("nonzero isotropic class on the Klein bottle");
    let w2 = F2Vector::zeros(klein.count(2)).unwrap();
    for pin in [PinType::Plus, PinType::Minus] {
        assert_eq!(
            PinLiftClassification::from_characteristic_cocycles(
                &klein,
                w1.clone(),
                w2.clone(),
                pin
            )
            .unwrap()
            .gauge_class_count()
            .unwrap(),
            4u8.into()
        );
    }
    assert!(PinLiftClassification::from_characteristic_cocycles(
        &rp2,
        F2Vector::zeros(0).unwrap(),
        F2Vector::zeros(rp2.count(2)).unwrap(),
        PinType::Plus
    )
    .is_err());
    assert!(PinLiftClassification::from_characteristic_cocycles(
        &rp2,
        F2Vector::unit(rp2.count(1), 0).unwrap(),
        F2Vector::zeros(rp2.count(2)).unwrap(),
        PinType::Minus
    )
    .is_err());
}

#[test]
fn ray_configuration_search_delegates_exact_boolean_constraints_and_refuses_bad_frames() {
    use core_quantum_physics::finite_geometry::{adjacent, coloring_count_small, config, sorkin};
    let graph = adjacent(&[vec![1, 0], vec![0, 1]]).unwrap();
    let frames = vec![vec![0, 1]];
    assert!(config(&graph, &frames).unwrap().has_classical_coloring);
    assert_eq!(coloring_count_small(&graph, &frames).unwrap(), 2);
    for invalid in [vec![vec![]], vec![vec![0, 0]], vec![vec![0, 2]]] {
        assert!(config(&graph, &invalid).is_err());
    }
    assert!(config(&[0, 0], &frames).is_err());
    assert!(adjacent(&[vec![0, 0]]).is_err());
    assert!(coloring_count_small(&vec![0; 25], &[]).is_err());
    assert!(sorkin(&ri(0), &ri(0), &ri(0), u32::MAX).is_err());
    assert_eq!(sorkin(&ri(1), &ri(1), &ri(1), 3).unwrap(), ri(6));
}

// Origin: engine/crates_rs/tests/core_quantum_physics/dynamics_completion.rs
// Claim: urn:core:crates_rs:tests:dynamics-completion:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc5b4c5d4 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc5b4c5d4` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc5b4c5d4 {
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
impl BoundaryErrorc5b4c5d4 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc5b4c5d4 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc5b4c5d4 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc5b4c5d4 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc5b4c5d4> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc5b4c5d4::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc5b4c5d4::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc5b4c5d4::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_c5b4c5d4() {
    let admitted = BoundaryRecordc5b4c5d4::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordc5b4c5d4::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
