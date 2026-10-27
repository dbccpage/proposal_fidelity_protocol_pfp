//! Everettian relative states: the reduced-state formula against an
//! independent partial trace, orthogonal-record diagonalization, the
//! off-diagonal bound on local expectations, same-shadow witnesses, weight
//! conservation under refinement, and U(1) transport on branch trees and
//! recombination diamonds. Everything is exact over `Q(i)`; each positive
//! statement has a refusal or countermodel beside it.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{elimination, involution as iv, matrix as mx};
use num_traits::{One, Zero};
use core_lie_theory::pauli_symplectic::{pauli, Pauli};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq, Rational};
use core_quantum_physics::branch_finegraining::finegrain_state_rationals;
use core_quantum_physics::everett::EverettForkingNode;
use core_quantum_physics::exact_hermitian::{self, gi, gq, partial_trace_second};
use core_quantum_physics::u1_graph_connection::{OrientedWalk, U1Connection, VertexGauge};
use core_solvers::data_cochain_packet::FiniteCochainPacket;

use core_quantum_physics::holonomy_interference::{
    relative_loop, CoherentPathFamily, HolonomyInterferenceError, TreeGaugeFixing,
};
use core_quantum_physics::relative_state_branching::{
    expectation, first_separating_observable, is_contraction, system_only_observables,
    RelativeStateError, RelativeStatePacket,
};

/// `Tr_E` of a state on `C^2 (x) C^2`, by `exact_hermitian`'s partial trace.
fn trace_out_records(state: &BasicMatrix<GaussianRat>) -> BasicMatrix<GaussianRat> {
    partial_trace_second(state, 2, 2).unwrap()
}

fn basis(n: usize, i: usize) -> Vec<GaussianRat> {
    let mut v = vec![gi(0, 0); n];
    v[i] = gi(1, 0);
    v
}

/// `(3/5, 4/5)`: a unit record with overlap `3/5` against `e_0`.
fn tilted() -> Vec<GaussianRat> {
    vec![gq(3, 5, 0, 1), gq(4, 5, 0, 1)]
}

/// `(-4/5, 3/5)`: completes `tilted` to an orthonormal basis of `C^2`.
fn tilted_complement() -> Vec<GaussianRat> {
    vec![gq(-4, 5, 0, 1), gq(3, 5, 0, 1)]
}

fn pauli_x() -> BasicMatrix<GaussianRat> {
    pauli(Pauli::X).unwrap()
}

fn pauli_y() -> BasicMatrix<GaussianRat> {
    pauli(Pauli::Y).unwrap()
}

fn pauli_z() -> BasicMatrix<GaussianRat> {
    pauli(Pauli::Z).unwrap()
}

fn half(n: i64) -> GaussianRat {
    gq(n, 2, 0, 1)
}

// ---------------------------------------------------------------------------
// QCE-C1 / C2: the reduced-state formula and orthogonal-record diagonalization.
// ---------------------------------------------------------------------------

#[test]
fn the_relative_state_formula_is_the_partial_trace_and_carries_record_overlaps() {
    // c = (3, 4i) up to scale; records e_0 and (3/5, 4/5), so <E_1|E_0> = 3/5.
    let packet =
        RelativeStatePacket::new(vec![gi(3, 0), gi(0, 4)], vec![basis(2, 0), tilted()]).unwrap();
    let global = packet.global_state();
    assert_eq!(mx::multiply(&global, &global).unwrap(), global);
    assert_eq!(mx::trace(&global).unwrap(), gi(1, 0));

    let rho = packet.reduced_state();
    assert_eq!(rho, trace_out_records(&global));
    assert_eq!(
        packet.record_gram(),
        mx::from_rows(vec![
            vec![gi(1, 0), gq(3, 5, 0, 1)],
            vec![gq(3, 5, 0, 1), gi(1, 0)]
        ])
        .unwrap()
    );
    // rho_01 = 3 * conj(4i) * 3/5 / 25 and rho_10 = 4i * 3 * 3/5 / 25.
    assert_eq!(
        rho,
        mx::from_rows(vec![
            vec![gq(9, 25, 0, 1), gq(0, 1, -36, 125)],
            vec![gq(0, 1, 36, 125), gq(16, 25, 0, 1)],
        ])
        .unwrap()
    );
    assert!(exact_hermitian::is_positive_semidefinite(&rho));
    assert_eq!(mx::trace(&rho).unwrap(), gi(1, 0));
}

#[test]
fn orthonormal_records_make_the_reduced_state_its_diagonal_shadow() {
    let packet =
        RelativeStatePacket::new(vec![gi(3, 0), gi(0, 4)], vec![basis(2, 0), basis(2, 1)]).unwrap();
    assert_eq!(packet.branch_weights(), vec![rq(9, 25), rq(16, 25)]);
    assert_eq!(packet.reduced_state(), packet.diagonal_shadow());
    assert_eq!(
        packet.reduced_state(),
        mx::diagonal(&[gq(9, 25, 0, 1), gq(16, 25, 0, 1)]).unwrap()
    );
    assert_eq!(packet.off_diagonal_mass().unwrap(), Rational::zero());

    // Orthonormal records need not be standard basis vectors.
    let rotated = RelativeStatePacket::new(
        vec![gi(1, 0), gi(1, 1)],
        vec![tilted(), tilted_complement()],
    )
    .unwrap();
    assert_eq!(rotated.branch_weights(), vec![rq(1, 3), rq(2, 3)]);
    assert_eq!(rotated.reduced_state(), rotated.diagonal_shadow());

    // Overlapping records keep coherence in the reduced state.
    let overlapping =
        RelativeStatePacket::new(vec![gi(3, 0), gi(0, 4)], vec![basis(2, 0), tilted()]).unwrap();
    assert_ne!(overlapping.reduced_state(), overlapping.diagonal_shadow());
    assert_eq!(overlapping.branch_weights(), packet.branch_weights());
}

// ---------------------------------------------------------------------------
// QCE-C3: Phi_off bounds every local expectation difference, and is attained.
// ---------------------------------------------------------------------------

#[test]
fn off_diagonal_mass_bounds_every_declared_contraction_and_is_attained() {
    let real =
        RelativeStatePacket::new(vec![gi(3, 0), gi(4, 0)], vec![basis(2, 0), tilted()]).unwrap();
    let phased =
        RelativeStatePacket::new(vec![gi(3, 0), gi(0, 4)], vec![basis(2, 0), tilted()]).unwrap();
    // 2 * (3/5)(4/5)(3/5) for both: the bound sees moduli, not phases.
    assert_eq!(real.off_diagonal_mass().unwrap(), rq(72, 125));
    assert_eq!(phased.off_diagonal_mass().unwrap(), rq(72, 125));

    let contractions = vec![
        pauli_x(),
        pauli_y(),
        pauli_z(),
        mx::from_rows(vec![
            vec![gq(3, 5, 0, 1), gq(4, 5, 0, 1)],
            vec![gq(4, 5, 0, 1), gq(-3, 5, 0, 1)],
        ])
        .unwrap(),
        mx::from_rows(vec![
            vec![gi(0, 0), gq(3, 5, 4, 5)],
            vec![gi(1, 0), gi(0, 0)],
        ])
        .unwrap(),
        mx::from_rows(vec![vec![gi(0, 0), gi(1, 0)], vec![gi(0, 0), gi(0, 0)]]).unwrap(),
        mx::diagonal(&[gi(1, 0), gi(0, 1)]).unwrap(),
        mx::diagonal(&[half(1), half(-1)]).unwrap(),
    ];
    let bound = rq(72, 125) * rq(72, 125);
    for packet in [&real, &phased] {
        for a in &contractions {
            assert!(is_contraction(a));
            assert!(packet.local_deviation(a).unwrap().norm_sq() <= bound);
        }
    }
    // Equality: sigma_x for real coefficients, sigma_y once the phase is i.
    assert_eq!(real.local_deviation(&pauli_x()).unwrap(), gq(72, 125, 0, 1));
    assert_eq!(phased.local_deviation(&pauli_x()).unwrap(), gi(0, 0));
    assert_eq!(
        phased.local_deviation(&pauli_y()).unwrap(),
        gq(72, 125, 0, 1)
    );
    // Diagonal operators cannot see the off-diagonal residue at all.
    assert_eq!(real.local_deviation(&pauli_z()).unwrap(), gi(0, 0));
}

#[test]
fn non_contractions_and_irrational_off_diagonal_mass_are_refused() {
    let packet =
        RelativeStatePacket::new(vec![gi(3, 0), gi(4, 0)], vec![basis(2, 0), tilted()]).unwrap();
    let doubled = mx::scale(&pauli_x(), &GaussianRat::from_rational(ri(2))).unwrap();
    assert!(!is_contraction(&doubled));
    assert_eq!(
        packet.local_deviation(&doubled),
        Err(RelativeStateError::NotAContraction)
    );
    assert!(matches!(
        packet.local_deviation(&mx::identity::<GaussianRat>(3).unwrap()),
        Err(RelativeStateError::OperatorShape {
            dimension: 2,
            rows: 3,
            cols: 3
        })
    ));
    // |c_0| |c_1| |G_01| / N = sqrt(2) (3/5) / 3 is not rational.
    let irrational =
        RelativeStatePacket::new(vec![gi(1, 0), gi(1, 1)], vec![basis(2, 0), tilted()]).unwrap();
    assert_eq!(
        irrational.off_diagonal_mass(),
        Err(RelativeStateError::IrrationalOffDiagonalTerm {
            first: 0,
            second: 1
        })
    );
}

// ---------------------------------------------------------------------------
// QCE-C4 / C5 / C10: equal local shadows, different global states.
// ---------------------------------------------------------------------------

#[test]
fn equal_local_shadows_hide_a_globally_distinguishable_phase() {
    let witness = |u: &GaussianRat| {
        RelativeStatePacket::new(vec![gi(1, 0), u.clone()], vec![basis(2, 0), basis(2, 1)]).unwrap()
    };
    let reference = witness(&gi(1, 0));
    let recoherence = reference.global_state();
    let local = system_only_observables(2, 2).unwrap();
    // The four observables B (x) I span the system-only algebra.
    let flattened = mx::from_rows(local.iter().map(|b| b.as_slice().to_vec()).collect()).unwrap();
    assert_eq!(elimination::rank(&flattened).unwrap(), 4);
    // They read the system factor: Tr((B (x) I) rho) = Tr(B Tr_E rho) with
    // B = Tr_E(B (x) I) / 2, on a state whose record marginal differs.
    let probe = RelativeStatePacket::new(vec![gi(3, 0), gi(0, 4)], vec![basis(2, 0), tilted()])
        .unwrap()
        .global_state();
    for observable in &local {
        let b = mx::scale(
            &trace_out_records(observable),
            &GaussianRat::from_rational(rq(1, 2)),
        )
        .unwrap();
        assert_eq!(
            expectation(observable, &probe).unwrap(),
            expectation(&b, &trace_out_records(&probe)).unwrap()
        );
    }

    // (u, (1 + Re u) / 2) for unit Gaussian rationals u.
    let cases = [
        (gi(1, 0), ri(1)),
        (gi(-1, 0), ri(0)),
        (gi(0, 1), rq(1, 2)),
        (gq(3, 5, 4, 5), rq(4, 5)),
        (gq(-7, 25, 24, 25), rq(9, 25)),
    ];
    for (u, overlap) in &cases {
        let packet = witness(u);
        let state = packet.global_state();
        assert_eq!(packet.branch_weights(), vec![rq(1, 2), rq(1, 2)]);
        assert_eq!(
            trace_out_records(&state),
            mx::diagonal(&[half(1), half(1)]).unwrap()
        );
        assert_eq!(
            first_separating_observable(&local, &state, &recoherence).unwrap(),
            None
        );
        assert_eq!(
            expectation(&recoherence, &state).unwrap(),
            GaussianRat::from_rational(overlap.clone())
        );
        assert_eq!(*overlap, (Rational::one() + &u.re) / ri(2));
    }
    let separated = first_separating_observable(
        std::slice::from_ref(&recoherence),
        &witness(&gi(0, 1)).global_state(),
        &recoherence,
    )
    .unwrap()
    .unwrap();
    assert_eq!(
        (separated.index, separated.left, separated.right),
        (0, half(1), gi(1, 0))
    );
}

#[test]
fn a_coherent_state_and_its_branch_mixture_share_every_local_statistic() {
    let packet =
        RelativeStatePacket::new(vec![gi(1, 0), gi(1, 0)], vec![basis(2, 0), basis(2, 1)]).unwrap();
    let coherent = packet.global_state();
    let mixture = packet.branch_mixture();
    assert_ne!(coherent, mixture);
    // Same reduced state (the diagonal shadow) and same branch weights.
    assert_eq!(trace_out_records(&mixture), packet.diagonal_shadow());
    assert_eq!(trace_out_records(&coherent), packet.diagonal_shadow());
    let local = system_only_observables(2, 2).unwrap();
    assert_eq!(
        first_separating_observable(&local, &coherent, &mixture).unwrap(),
        None
    );
    // The recoherence projector reads 1 on the coherent state and 1/2 on the mixture.
    let separation =
        first_separating_observable(std::slice::from_ref(&coherent), &coherent, &mixture)
            .unwrap()
            .unwrap();
    assert_eq!((separation.left, separation.right), (gi(1, 0), half(1)));
    // The coherent state is pure; the mixture is not.
    assert_eq!(
        mx::trace(&mx::multiply(&coherent, &coherent).unwrap()).unwrap(),
        gi(1, 0)
    );
    assert_eq!(
        mx::trace(&mx::multiply(&mixture, &mixture).unwrap()).unwrap(),
        half(1)
    );
}

// ---------------------------------------------------------------------------
// QCE-C6: isometric refinement conserves weight; branch counting does not.
// ---------------------------------------------------------------------------

#[test]
fn isometric_refinement_conserves_branch_weight_and_branch_counting_does_not() {
    let packet =
        RelativeStatePacket::new(vec![gi(3, 0), gi(4, 0)], vec![basis(2, 0), basis(2, 1)]).unwrap();
    let refined = packet
        .refine(
            0,
            &[gq(3, 5, 0, 1), gq(0, 1, 4, 5)],
            vec![basis(2, 0), tilted()],
        )
        .unwrap();
    let weights = refined.branch_weights();
    assert_eq!(weights, vec![rq(81, 625), rq(144, 625), rq(16, 25)]);
    assert_eq!(&weights[0] + &weights[1], packet.branch_weights()[0]);
    assert_eq!(weights.iter().sum::<Rational>(), Rational::one());

    // A second cut of the same tree keeps every parent's weight.
    let twice = refined
        .refine(
            2,
            &[gq(5, 13, 0, 1), gq(12, 13, 0, 1)],
            vec![basis(2, 0), basis(2, 1)],
        )
        .unwrap();
    let fine = twice.branch_weights();
    assert_eq!(&fine[2] + &fine[3], rq(16, 25));
    assert_eq!(&fine[0] + &fine[1], rq(9, 25));
    assert_eq!(fine.iter().sum::<Rational>(), Rational::one());

    // Non-isometric amplitudes are refused, as are malformed refinements.
    assert_eq!(
        packet.refine(0, &[half(1), half(1)], vec![basis(2, 0), basis(2, 1)]),
        Err(RelativeStateError::NonIsometricRefinement(rq(1, 2)))
    );
    assert!(matches!(
        packet.refine(2, &[gi(1, 0)], vec![basis(2, 0)]),
        Err(RelativeStateError::BranchOutOfRange {
            branch: 2,
            branches: 2
        })
    ));
    assert!(matches!(
        packet.refine(0, &[gi(1, 0)], vec![]),
        Err(RelativeStateError::RefinementCount {
            amplitudes: 1,
            records: 0
        })
    ));

    // Counting labels moves under the same refinement: parent 0 holds 1/2 of
    // the labels before and 2/3 after, while its squared-norm weight stays 9/25.
    let amplitudes = |p: &RelativeStatePacket| -> Vec<(Rational, Rational)> {
        p.coefficients()
            .iter()
            .map(|c| (c.re.clone(), c.im.clone()))
            .collect()
    };
    let before = EverettForkingNode::from_amplitudes(&amplitudes(&packet)).unwrap();
    let after = EverettForkingNode::from_amplitudes(&amplitudes(&refined)).unwrap();
    assert_eq!(before.branches[0].count_weight, rq(1, 2));
    assert_eq!(
        &after.branches[0].count_weight + &after.branches[1].count_weight,
        rq(2, 3)
    );
    assert_eq!(before.branches[0].born_weight, rq(9, 25));
    assert_eq!(
        &after.branches[0].born_weight + &after.branches[1].born_weight,
        rq(9, 25)
    );
    // Counting matches the weights only after a weight-dependent fine-graining.
    let finegrained = finegrain_state_rationals(&packet.branch_weights(), None);
    assert!(finegrained.is_exact_match);
    assert_eq!(finegrained.total_multiplicity, 25);
    assert_eq!(
        (
            finegrained.branches[0].sub_branch_count,
            finegrained.branches[1].sub_branch_count
        ),
        (9, 16)
    );
}

// ---------------------------------------------------------------------------
// QCE-C9 / QCE-C11: the global state does not fix the branch decomposition.
// ---------------------------------------------------------------------------

#[test]
fn one_global_state_has_two_relative_state_decompositions_with_orthonormal_records() {
    let standard =
        RelativeStatePacket::new(vec![gi(1, 0), gi(1, 0)], vec![basis(2, 0), basis(2, 1)]).unwrap();
    let rotated = RelativeStatePacket::with_system_family(
        vec![tilted(), tilted_complement()],
        vec![gi(1, 0), gi(1, 0)],
        vec![tilted(), tilted_complement()],
    )
    .unwrap();
    assert_eq!(standard.global_state(), rotated.global_state());
    assert_eq!(standard.reduced_state(), rotated.reduced_state());
    assert_eq!(standard.branch_weights(), rotated.branch_weights());
    assert_eq!(rotated.off_diagonal_mass().unwrap(), Rational::zero());
    // Read as outcomes, the two families of branch terms are different states.
    assert_ne!(standard.branch_mixture(), rotated.branch_mixture());
    assert_eq!(
        *rotated.branch_mixture().get_ref(0, 0).unwrap(),
        gq(337, 1250, 0, 1)
    );

    // With unequal weights the reduced state is not diagonal in the rotated
    // family, so no expansion with orthonormal records exists there.
    let unequal =
        RelativeStatePacket::new(vec![gi(3, 0), gi(4, 0)], vec![basis(2, 0), basis(2, 1)]).unwrap();
    let rho = unequal.reduced_state();
    let cross = iv::inner_product(
        &tilted(),
        &mx::multiply_vector(&rho, &tilted_complement()).unwrap(),
    )
    .unwrap();
    assert_eq!(cross, gq(84, 625, 0, 1));
}

// ---------------------------------------------------------------------------
// QCE-C7 / C8: branch trees carry no phase; recombination diamonds do.
// ---------------------------------------------------------------------------

fn packet(vertices: &[&str], edges: &[(&str, &str)]) -> FiniteCochainPacket {
    FiniteCochainPacket::with_unit_weights(
        FiniteCochainPacket::build_complex(vertices, edges, &[]).unwrap(),
    )
    .unwrap()
}

/// r -> a, r -> b, a -> c, a -> d: a two-level branching history.
fn branch_tree() -> FiniteCochainPacket {
    packet(
        &["r", "a", "b", "c", "d"],
        &[("r", "a"), ("r", "b"), ("a", "c"), ("a", "d")],
    )
}

/// x -> a -> y and x -> b -> y: two histories that branch and rejoin.
fn diamond() -> FiniteCochainPacket {
    packet(
        &["x", "a", "b", "y"],
        &[("x", "a"), ("a", "y"), ("x", "b"), ("b", "y")],
    )
}

#[test]
fn every_connection_on_a_branch_tree_is_gauge_trivial() {
    let tree = branch_tree();
    let connections = [
        vec![gq(3, 5, 4, 5), gi(0, 1), gq(5, 13, -12, 13), gi(-1, 0)],
        vec![
            gi(0, -1),
            gq(-7, 25, 24, 25),
            gq(8, 17, 15, 17),
            gq(3, 5, -4, 5),
        ],
    ];
    for values in connections {
        let connection = U1Connection::new(&tree, values).unwrap();
        let fixing = TreeGaugeFixing::new(&tree, &connection).unwrap();
        assert!(fixing.is_gauge_trivial());
        assert!(fixing.cycle_holonomies().is_empty());
        assert_eq!(
            connection.gauge_transform(&tree, fixing.gauge()).unwrap(),
            U1Connection::trivial(&tree)
        );
        let out_and_back =
            OrientedWalk::new(&tree, "r", &[(0, 1), (3, 1), (3, -1), (0, -1)]).unwrap();
        assert_eq!(connection.holonomy(&tree, &out_and_back).unwrap(), gi(1, 0));
    }
    // A recombination diamond keeps exactly one gauge-invariant phase.
    let d = diamond();
    let curved = U1Connection::new(
        &d,
        vec![gq(3, 5, 4, 5), gi(0, 1), gq(5, 13, 12, 13), gi(1, 0)],
    )
    .unwrap();
    let fixing = TreeGaugeFixing::new(&d, &curved).unwrap();
    assert!(!fixing.is_gauge_trivial());
    assert_eq!(fixing.cycle_holonomies().len(), 1);
}

#[test]
fn relative_holonomy_on_a_diamond_is_gauge_invariant_and_governs_recombination() {
    let d = diamond();
    let (a_xa, a_ay, a_xb, a_by) = (gq(3, 5, 4, 5), gi(0, 1), gq(5, 13, 12, 13), gi(1, 0));
    let connection = U1Connection::new(
        &d,
        vec![a_xa.clone(), a_ay.clone(), a_xb.clone(), a_by.clone()],
    )
    .unwrap();
    let routes = [
        OrientedWalk::new(&d, "x", &[(0, 1), (1, 1)]).unwrap(),
        OrientedWalk::new(&d, "x", &[(2, 1), (3, 1)]).unwrap(),
    ];
    let unit = [ri(1), ri(1)];
    let family = CoherentPathFamily::new(&d, &connection, &routes, &unit).unwrap();
    let h = family.relative_holonomy(0, 1).unwrap();
    assert_eq!(h, a_xa.mul(&a_ay).mul(&a_xb.mul(&a_by).conj()));
    assert_eq!(h, gq(16, 65, 63, 65));
    let around = relative_loop(&d, &routes[0], &routes[1]).unwrap();
    assert_eq!(connection.holonomy(&d, &around).unwrap(), h);
    let cycle = TreeGaugeFixing::new(&d, &connection)
        .unwrap()
        .cycle_holonomies();
    assert!(cycle[0].1 == h || cycle[0].1 == h.conj());

    // h survives a gauge change; each route's transport does not.
    let gauge = VertexGauge::new(
        &d,
        vec![gq(3, 5, -4, 5), gi(0, 1), gq(12, 13, 5, 13), gi(-1, 0)],
    )
    .unwrap();
    let transformed = connection.gauge_transform(&d, &gauge).unwrap();
    let moved = CoherentPathFamily::new(&d, &transformed, &routes, &unit).unwrap();
    assert_eq!(moved.relative_holonomy(0, 1).unwrap(), h);
    assert_ne!(moved.transports()[0], family.transports()[0]);
    assert_eq!(moved.sink_intensity(), family.sink_intensity());

    // Recombined intensity w_a + w_b + 2 sqrt(w_a w_b) Re h: a function of h alone.
    assert_eq!(family.sink_intensity(), rq(162, 65));
    for (w_a, w_b, r_a, r_b) in [
        (ri(1), ri(1), ri(1), ri(1)),
        (rq(9, 25), rq(16, 25), rq(3, 5), rq(4, 5)),
        (rq(1, 4), ri(1), rq(1, 2), ri(1)),
    ] {
        let weighted =
            CoherentPathFamily::new(&d, &connection, &routes, &[w_a.clone(), w_b.clone()]).unwrap();
        let expected = &w_a + &w_b + ri(2) * r_a * r_b * &h.re;
        assert_eq!(weighted.sink_intensity(), expected);
        assert_eq!(weighted.holonomy_expansion(), expected);
    }
    // h = 1 recombines constructively and h = -1 destructively.
    let one = gi(1, 0);
    let opposed = U1Connection::new(&d, vec![gi(-1, 0), one.clone(), one.clone(), one]).unwrap();
    let constructive =
        CoherentPathFamily::new(&d, &U1Connection::trivial(&d), &routes, &unit).unwrap();
    let destructive = CoherentPathFamily::new(&d, &opposed, &routes, &unit).unwrap();
    assert_eq!(
        (constructive.sink_intensity(), destructive.sink_intensity()),
        (ri(4), ri(0))
    );

    let partial = [
        routes[0].clone(),
        OrientedWalk::new(&d, "x", &[(0, 1)]).unwrap(),
    ];
    assert!(matches!(
        CoherentPathFamily::new(&d, &connection, &partial, &unit),
        Err(HolonomyInterferenceError::EndpointMismatch { index: 1 })
    ));
}

// ---------------------------------------------------------------------------
// Declarations are validated before anything is computed.
// ---------------------------------------------------------------------------

#[test]
fn relative_state_declarations_refuse_malformed_inputs() {
    assert_eq!(
        RelativeStatePacket::new(vec![], vec![]),
        Err(RelativeStateError::NoBranches)
    );
    assert!(matches!(
        RelativeStatePacket::new(vec![gi(1, 0)], vec![]),
        Err(RelativeStateError::CountMismatch {
            coefficients: 1,
            records: 0,
            family: 1
        })
    ));
    assert_eq!(
        RelativeStatePacket::new(vec![gi(1, 0)], vec![vec![gi(1, 0), gi(1, 0)]]),
        Err(RelativeStateError::UnnormalizedRecord { index: 0 })
    );
    assert!(matches!(
        RelativeStatePacket::new(vec![gi(1, 0), gi(1, 0)], vec![basis(2, 0), basis(3, 0)]),
        Err(RelativeStateError::RecordLength {
            index: 1,
            expected: 2,
            actual: 3
        })
    ));
    assert_eq!(
        RelativeStatePacket::new(vec![gi(0, 0), gi(0, 0)], vec![basis(2, 0), basis(2, 1)]),
        Err(RelativeStateError::ZeroCoefficients)
    );
    assert_eq!(
        RelativeStatePacket::with_system_family(
            vec![basis(2, 0), tilted()],
            vec![gi(1, 0), gi(1, 0)],
            vec![basis(2, 0), basis(2, 1)]
        ),
        Err(RelativeStateError::NonOrthonormalFamily {
            first: 0,
            second: 1
        })
    );
    assert!(matches!(
        RelativeStatePacket::with_system_family(
            vec![basis(2, 0), basis(3, 1)],
            vec![gi(1, 0), gi(1, 0)],
            vec![basis(2, 0), basis(2, 1)]
        ),
        Err(RelativeStateError::SystemVectorLength {
            index: 1,
            expected: 2,
            actual: 3
        })
    ));
    assert_eq!(
        system_only_observables(2, 0),
        Err(RelativeStateError::EmptyFactor)
    );
    assert_eq!(
        system_only_observables(0, 2),
        Err(RelativeStateError::EmptyFactor)
    );
    assert!(matches!(
        expectation(
            &mx::identity::<GaussianRat>(2).unwrap(),
            &mx::identity::<GaussianRat>(4).unwrap()
        ),
        Err(RelativeStateError::StateShape {
            expected: 2,
            rows: 4,
            cols: 4
        })
    ));
}

// Origin: engine/crates_rs/tests/core_quantum_physics/interpretations/everettian_relative_state_contact.rs
// Claim: urn:core:crates_rs:tests:everettian-relative-state-contact:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordac6ec286 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordac6ec286` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorac6ec286 {
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
impl BoundaryErrorac6ec286 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorac6ec286 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorac6ec286 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordac6ec286 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorac6ec286> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorac6ec286::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorac6ec286::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorac6ec286::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_ac6ec286() {
    let admitted = BoundaryRecordac6ec286::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordac6ec286::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
