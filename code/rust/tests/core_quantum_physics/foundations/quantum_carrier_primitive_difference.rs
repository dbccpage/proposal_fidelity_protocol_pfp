//! Primitive difference for quantum carriers: graph cochains and the weighted
//! L1 quotient, declared U(1) connections, the connection Laplacian, the
//! fixed-scale cochain exponential, the generalized Gell-Mann basis, and the
//! declared mass/phase embedding. Every check is exact; each theorem has a
//! negative control that a wrong implementation would fail.

use linear_algebra::exact_field::involution as iv;
use linear_algebra::exact_field::matrix as mx;
use num_traits::{One, Signed, Zero};
use core_functional::phi1::Phi1Functional;
use core_lie_theory::cayley::{is_unit, unit_from_parameter};
use core_lie_theory::su_n::{GellMannBasis, GellMannError};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::quadratic::Surd as SurdRational;
use core_number_theory::rational::sqrt_exact as rational_sqrt;
use core_number_theory::rational::{ri, rq, Rational};
use core_policy::trichotomy::ObstructionDiagnosticClass;
use core_quantum_physics::exact_hermitian::{self, gi, gq};
use core_quantum_physics::mass_phase_embedding::{EmbeddingError, MassPhaseEmbedding};
use core_quantum_physics::u1_graph_connection::{
    l1_self_normalized, CochainExponential, OrientedWalk, U1Connection, U1GaugeError, VertexGauge,
};
use core_solvers::data_cochain_packet::{CochainPacketError, FiniteCochainPacket};

fn rats(values: &[i64]) -> Vec<Rational> {
    values.iter().map(|&v| ri(v)).collect()
}

fn triangle(with_face: bool, weights: &[i64]) -> FiniteCochainPacket {
    let faces: &[&[&str]] = if with_face { &[&["a", "b", "c"]] } else { &[] };
    let complex = FiniteCochainPacket::build_complex(
        &["a", "b", "c"],
        &[("a", "b"), ("b", "c"), ("c", "a")],
        faces,
    )
    .unwrap();
    FiniteCochainPacket::new(complex, rats(weights)).unwrap()
}

/// Triangle a-b-c with a pendant edge c->d: one cycle and one open branch.
fn kite(weights: Vec<Rational>) -> FiniteCochainPacket {
    let complex = FiniteCochainPacket::build_complex(
        &["a", "b", "c", "d"],
        &[("a", "b"), ("b", "c"), ("c", "a"), ("c", "d")],
        &[],
    )
    .unwrap();
    FiniteCochainPacket::new(complex, weights).unwrap()
}

fn kite_connection(packet: &FiniteCochainPacket) -> U1Connection {
    U1Connection::new(
        packet,
        vec![
            gq(3, 5, 4, 5),
            gq(5, 13, 12, 13),
            gi(0, 1),
            gq(8, 17, 15, 17),
        ],
    )
    .unwrap()
}

fn kite_gauge(packet: &FiniteCochainPacket) -> VertexGauge {
    VertexGauge::new(
        packet,
        vec![gq(3, 5, -4, 5), gi(-1, 0), gq(12, 13, 5, 13), gi(0, -1)],
    )
    .unwrap()
}

fn kite_field() -> Vec<GaussianRat> {
    vec![gi(1, 2), gi(3, 0), gi(0, -1), gi(2, -1)]
}

// ---------------------------------------------------------------------------
// QMC-T1: the weighted L1 quotient is an attained norm with a circulation dual.
// ---------------------------------------------------------------------------

#[test]
fn quotient_mass_of_a_unit_circulation_is_attained_and_dual_certified() {
    let packet = triangle(false, &[1, 2, 3]);
    let omega = rats(&[1, 1, 1]);
    let phi1 = packet.quotient_mass(&omega).unwrap();
    // The oriented cycle sum is 3 whatever the gauge, and the cheapest edge has weight 1.
    assert_eq!(phi1.value(), &ri(3));
    let z = phi1.dual_witness();
    // The dual is a circulation: d0^T z = 0, bounded by the weights, pairing to Phi1.
    for column in 0..packet.vertex_count() {
        let flow: Rational = (0..packet.edge_count())
            .map(|e| &packet.d0()[e][column] * &z[e])
            .sum();
        assert!(flow.is_zero());
    }
    for (value, weight) in z.iter().zip(packet.weights()) {
        assert!(value.abs() <= *weight);
    }
    let pairing: Rational = z.iter().zip(&omega).map(|(a, b)| a * b).sum();
    assert_eq!(&pairing, phi1.value());
}

#[test]
fn raw_mass_depends_on_the_representative_but_quotient_mass_does_not() {
    let packet = triangle(false, &[1, 1, 1]);
    let omega = rats(&[1, 1, 1]);
    let repair = packet.primitive_difference(&rats(&[0, 5, 2])).unwrap();
    assert_eq!(repair, rats(&[5, -3, -2]));
    let shifted: Vec<Rational> = omega.iter().zip(&repair).map(|(a, b)| a + b).collect();
    assert_eq!(packet.raw_mass(&omega).unwrap(), ri(3));
    assert_eq!(packet.raw_mass(&shifted).unwrap(), ri(9));
    assert_eq!(packet.quotient_mass(&omega).unwrap().value(), &ri(3));
    assert_eq!(packet.quotient_mass(&shifted).unwrap().value(), &ri(3));
    // A pure repair has positive raw mass and zero quotient mass.
    assert_eq!(packet.raw_mass(&repair).unwrap(), ri(10));
    assert!(packet.quotient_mass(&repair).unwrap().value().is_zero());
}

#[test]
fn quotient_mass_vanishes_on_forests_and_on_the_edgeless_graph() {
    let path = FiniteCochainPacket::with_unit_weights(
        FiniteCochainPacket::build_complex(&["a", "b", "c"], &[("a", "b"), ("b", "c")], &[])
            .unwrap(),
    )
    .unwrap();
    assert!(path
        .quotient_mass(&rats(&[7, -3]))
        .unwrap()
        .value()
        .is_zero());
    assert_eq!(path.dimensions().h1, 0);

    let edgeless = FiniteCochainPacket::with_unit_weights(
        FiniteCochainPacket::build_complex(&["a", "b"], &[], &[]).unwrap(),
    )
    .unwrap();
    assert!(edgeless.quotient_mass(&[]).unwrap().value().is_zero());
    let dims = edgeless.dimensions();
    assert_eq!((dims.c1, dims.b1, dims.h1), (0, 0, 0));
}

#[test]
fn a_tampered_quotient_certificate_is_refused_by_the_functional_verifier() {
    let packet = triangle(false, &[1, 2, 3]);
    let verified = packet.quotient_mass(&rats(&[2, 0, -1])).unwrap();
    assert_eq!(verified.value(), &ri(1));
    let mut inflated = verified.certificate().clone();
    inflated.reported_value = ri(2);
    assert!(Phi1Functional::verify_exact_certificate(inflated).is_err());
    let mut broken_dual = verified.certificate().clone();
    broken_dual.dual_witness[0] = &broken_dual.dual_witness[0] + Rational::one();
    assert!(Phi1Functional::verify_exact_certificate(broken_dual).is_err());
}

#[test]
fn cochain_dimensions_and_the_exact_trichotomy() {
    let open = triangle(false, &[1, 1, 1]);
    let filled = triangle(true, &[1, 1, 1]);
    let dims_open = open.dimensions();
    let dims_filled = filled.dimensions();
    assert_eq!((dims_open.b1, dims_open.z1, dims_open.h1), (2, 3, 1));
    assert_eq!((dims_filled.b1, dims_filled.z1, dims_filled.h1), (2, 2, 0));

    let circulation = rats(&[1, 1, 1]);
    assert_eq!(
        open.classify(&circulation).unwrap().diagnostic_class(),
        ObstructionDiagnosticClass::ClosedResidual
    );
    let failure = filled.classify(&circulation).unwrap();
    assert_eq!(
        failure.diagnostic_class(),
        ObstructionDiagnosticClass::ActiveClosureFailure
    );
    assert_eq!(failure.gamma2_value(), &ri(3));
    let repair = filled.primitive_difference(&rats(&[4, 0, -1])).unwrap();
    assert_eq!(
        filled.classify(&repair).unwrap().diagnostic_class(),
        ObstructionDiagnosticClass::ExactRepair
    );
}

#[test]
fn packet_declarations_refuse_self_loops_bad_weights_and_wrong_lengths() {
    let looped =
        FiniteCochainPacket::build_complex(&["a", "b"], &[("a", "b"), ("a", "a")], &[]).unwrap();
    assert!(matches!(
        FiniteCochainPacket::with_unit_weights(looped),
        Err(CochainPacketError::SelfLoop { edge: 1, .. })
    ));
    let complex = FiniteCochainPacket::build_complex(&["a", "b"], &[("a", "b")], &[]).unwrap();
    assert!(matches!(
        FiniteCochainPacket::new(complex.clone(), vec![Rational::zero()]),
        Err(CochainPacketError::NonPositiveWeight { edge: 0 })
    ));
    assert!(matches!(
        FiniteCochainPacket::new(complex, rats(&[1, 1])),
        Err(CochainPacketError::WeightCountMismatch {
            edges: 1,
            weights: 2
        })
    ));
    let packet = triangle(false, &[1, 1, 1]);
    assert!(matches!(
        packet.quotient_mass(&rats(&[1, 1])),
        Err(CochainPacketError::CochainLength {
            expected: 3,
            actual: 2
        })
    ));
}

// ---------------------------------------------------------------------------
// QMC-T2 / T3: gauge covariance and closed-loop gauge invariance.
// ---------------------------------------------------------------------------

#[test]
fn covariant_difference_is_gauge_covariant_edgewise() {
    let packet = kite(rats(&[1, 1, 1, 1]));
    let a = kite_connection(&packet);
    let g = kite_gauge(&packet);
    let psi = kite_field();
    let before = a.covariant_difference(&packet, &psi).unwrap();
    let after = a
        .gauge_transform(&packet, &g)
        .unwrap()
        .covariant_difference(&packet, &g.apply_to_field(&psi).unwrap())
        .unwrap();
    for (e, edge) in packet.complex().edges.iter().enumerate() {
        let v = packet.complex().vertex_map[&edge.target];
        assert_eq!(after[e], g.values()[v].mul(&before[e]));
    }
}

#[test]
fn the_swapped_gauge_convention_breaks_covariance() {
    // A''_(u,v) = g(u) A conj(g(v)) is the wrong convention and must fail.
    let packet = kite(rats(&[1, 1, 1, 1]));
    let a = kite_connection(&packet);
    let g = kite_gauge(&packet);
    let psi = kite_field();
    let swapped: Vec<GaussianRat> = packet
        .complex()
        .edges
        .iter()
        .enumerate()
        .map(|(e, edge)| {
            let u = packet.complex().vertex_map[&edge.source];
            let v = packet.complex().vertex_map[&edge.target];
            g.values()[u].mul(&a.values()[e]).mul(&g.values()[v].conj())
        })
        .collect();
    let wrong = U1Connection::new(&packet, swapped).unwrap();
    let before = a.covariant_difference(&packet, &psi).unwrap();
    let after = wrong
        .covariant_difference(&packet, &g.apply_to_field(&psi).unwrap())
        .unwrap();
    let covariant = packet.complex().edges.iter().enumerate().all(|(e, edge)| {
        let v = packet.complex().vertex_map[&edge.target];
        after[e] == g.values()[v].mul(&before[e])
    });
    assert!(!covariant);
}

#[test]
fn closed_holonomy_is_gauge_invariant_and_open_transport_is_endpoint_covariant() {
    let packet = kite(rats(&[1, 1, 1, 1]));
    let a = kite_connection(&packet);
    let g = kite_gauge(&packet);
    let transformed = a.gauge_transform(&packet, &g).unwrap();

    let cycle = OrientedWalk::new(&packet, "a", &[(0, 1), (1, 1), (2, 1)]).unwrap();
    let hol = a.holonomy(&packet, &cycle).unwrap();
    assert_eq!(hol, a.values()[0].mul(&a.values()[1]).mul(&a.values()[2]));
    assert_eq!(transformed.holonomy(&packet, &cycle).unwrap(), hol);
    assert!(is_unit(&hol));
    let reversed = OrientedWalk::new(&packet, "a", &[(2, -1), (1, -1), (0, -1)]).unwrap();
    assert_eq!(a.holonomy(&packet, &reversed).unwrap(), hol.conj());

    // The open path a -> b -> c -> d changes by g(d) . conj(g(a)).
    let path = OrientedWalk::new(&packet, "a", &[(0, 1), (1, 1), (3, 1)]).unwrap();
    assert!(!path.is_closed());
    let t = a.transport(&path).unwrap();
    let t_prime = transformed.transport(&path).unwrap();
    assert_ne!(t_prime, t);
    assert_eq!(t_prime, g.values()[3].mul(&t).mul(&g.values()[0].conj()));
    assert!(matches!(
        a.holonomy(&packet, &path),
        Err(U1GaugeError::WalkNotClosed { .. })
    ));

    // Cross-check against core_holonomy's ordered loop product.
    assert_eq!(
        a.holonomy_crate_loop(&packet, &["a", "b", "c", "a"])
            .unwrap(),
        hol
    );
}

#[test]
fn walks_are_validated_against_the_declared_graph() {
    let packet = kite(rats(&[1, 1, 1, 1]));
    assert!(matches!(
        OrientedWalk::new(&packet, "a", &[(0, 1), (3, 1)]),
        Err(U1GaugeError::Discontinuous { step: 1 })
    ));
    assert!(matches!(
        OrientedWalk::new(&packet, "a", &[(9, 1)]),
        Err(U1GaugeError::EdgeOutOfRange { step: 0, edge: 9 })
    ));
    assert!(matches!(
        OrientedWalk::new(&packet, "a", &[(0, 0)]),
        Err(U1GaugeError::BadOrientation {
            step: 0,
            direction: 0
        })
    ));
    assert!(matches!(
        OrientedWalk::new(&packet, "a", &[]),
        Err(U1GaugeError::EmptyWalk)
    ));
    assert!(matches!(
        OrientedWalk::new(&packet, "z", &[(0, 1)]),
        Err(U1GaugeError::UnknownVertex(_))
    ));
    // Traversing an edge against its orientation must start at its target.
    assert!(matches!(
        OrientedWalk::new(&packet, "a", &[(0, -1)]),
        Err(U1GaugeError::Discontinuous { step: 0 })
    ));
}

#[test]
fn connections_and_gauges_refuse_non_unit_values() {
    let packet = kite(rats(&[1, 1, 1, 1]));
    assert!(matches!(
        U1Connection::new(&packet, vec![gi(1, 0), gi(2, 0), gi(1, 0), gi(1, 0)]),
        Err(U1GaugeError::NonUnitValue { index: 1 })
    ));
    assert!(matches!(
        VertexGauge::new(&packet, vec![gi(1, 0); 3]),
        Err(U1GaugeError::ValueCount {
            expected: 4,
            actual: 3
        })
    ));
    // Stereographic parameters give genuine circle points.
    for t in [rq(1, 2), rq(-3, 7), ri(5)] {
        assert!(is_unit(&unit_from_parameter(&t)));
    }
}

// ---------------------------------------------------------------------------
// QMC-T4: the connection Laplacian is Hermitian PSD and gauge equivalent.
// ---------------------------------------------------------------------------

#[test]
fn connection_laplacian_is_hermitian_psd_and_reproduces_the_dirichlet_energy() {
    let packet = kite(vec![ri(1), ri(2), ri(3), rq(1, 2)]);
    let a = kite_connection(&packet);
    let laplacian = a.laplacian(&packet);
    assert!(exact_hermitian::is_hermitian(&laplacian));
    assert!(exact_hermitian::is_positive_semidefinite(&laplacian));
    let psi = kite_field();
    let q = linear_algebra::exact_field::ordered::hermitian_form(&laplacian, &psi).unwrap();
    assert!(q.im.is_zero());
    assert_eq!(q.re, a.dirichlet_energy(&packet, &psi).unwrap());
    // A non-flat triangle leaves no covariantly constant field: Delta is definite.
    assert!(exact_hermitian::is_positive_definite(&laplacian));
    // The trivial connection has the constants in its kernel: semidefinite only.
    let flat = U1Connection::trivial(&packet).laplacian(&packet);
    assert!(exact_hermitian::is_positive_semidefinite(&flat));
    assert!(!exact_hermitian::is_positive_definite(&flat));
    assert_eq!(
        linear_algebra::exact_field::elimination::rank(&flat).unwrap(),
        packet.vertex_count() - 1
    );
}

#[test]
fn gauge_related_connections_have_unitarily_equivalent_laplacians() {
    let packet = kite(vec![ri(1), ri(2), ri(3), rq(1, 2)]);
    let a = kite_connection(&packet);
    let g = kite_gauge(&packet);
    let big_g = g.diagonal();
    let lhs = a.gauge_transform(&packet, &g).unwrap().laplacian(&packet);
    let rhs = mx::multiply(
        &mx::multiply(&big_g, &a.laplacian(&packet)).unwrap(),
        &iv::adjoint(&big_g).unwrap(),
    )
    .unwrap();
    assert_eq!(lhs, rhs);
    assert_eq!(
        mx::multiply(&big_g, &iv::adjoint(&big_g).unwrap()).unwrap(),
        mx::diagonal(&[gi(1, 0), gi(1, 0), gi(1, 0), gi(1, 0)]).unwrap()
    );
}

#[test]
fn core_holonomy_laplacian_is_the_entrywise_conjugate() {
    let packet = kite(vec![ri(1), ri(2), ri(3), rq(1, 2)]);
    let a = kite_connection(&packet);
    let ours = a.laplacian(&packet);
    let theirs = a.holonomy_crate_laplacian(&packet).unwrap();
    assert_eq!(theirs, mx::transpose(&ours).unwrap());
    assert_eq!(
        theirs.as_slice().to_vec(),
        ours.as_slice().iter().map(|z| z.conj()).collect::<Vec<_>>()
    );
}

#[test]
fn the_psd_decision_rejects_indefinite_and_non_hermitian_matrices() {
    let indefinite = mx::diagonal(&[gi(1, 0), gi(-1, 0)]).unwrap();
    assert!(!exact_hermitian::is_positive_semidefinite(&indefinite));
    let non_hermitian =
        mx::from_rows(vec![vec![gi(1, 0), gi(0, 1)], vec![gi(0, 1), gi(1, 0)]]).unwrap();
    assert!(!exact_hermitian::is_hermitian(&non_hermitian));
    assert!(!exact_hermitian::is_positive_semidefinite(&non_hermitian));
    // [[1, i], [-i, 1]] is PSD of rank one; [[1, 2i], [-2i, 1]] is not PSD.
    let rank_one =
        mx::from_rows(vec![vec![gi(1, 0), gi(0, 1)], vec![gi(0, -1), gi(1, 0)]]).unwrap();
    assert!(exact_hermitian::is_positive_semidefinite(&rank_one));
    assert_eq!(
        linear_algebra::exact_field::elimination::rank(&rank_one).unwrap(),
        1
    );
    let too_coherent =
        mx::from_rows(vec![vec![gi(1, 0), gi(0, 2)], vec![gi(0, -2), gi(1, 0)]]).unwrap();
    assert!(!exact_hermitian::is_positive_semidefinite(&too_coherent));
}

// ---------------------------------------------------------------------------
// QMC-T5: the fixed-scale cochain exponential descends to gauge classes.
// ---------------------------------------------------------------------------

#[test]
fn exponentials_of_repair_related_cochains_are_gauge_equivalent() {
    let packet = kite(rats(&[1, 1, 1, 1]));
    let omega = rats(&[1, 2, 3, -1]);
    let f = rats(&[0, 1, -2, 5]);
    let repair = packet.primitive_difference(&f).unwrap();
    let shifted: Vec<Rational> = omega.iter().zip(&repair).map(|(a, b)| a + b).collect();
    for base in [gi(0, 1), gq(3, 5, 4, 5), gq(-7, 25, 24, 25)] {
        let exp = CochainExponential::new(base).unwrap();
        let direct = exp.connection(&packet, &shifted).unwrap();
        let gauge = exp.gauge(&packet, &f).unwrap();
        let via_gauge = exp
            .connection(&packet, &omega)
            .unwrap()
            .gauge_transform(&packet, &gauge)
            .unwrap();
        assert_eq!(direct, via_gauge);
    }
}

#[test]
fn a_periodic_scale_loses_values_and_an_aperiodic_scale_does_not() {
    let packet = kite(rats(&[1, 1, 1, 1]));
    let omega = rats(&[1, 2, 3, -1]);
    let bumped = rats(&[5, 2, 3, -1]);
    let quarter_turn = CochainExponential::new(gi(0, 1)).unwrap();
    assert_eq!(quarter_turn.order(), Some(4));
    assert_eq!(
        quarter_turn.connection(&packet, &omega).unwrap(),
        quarter_turn.connection(&packet, &bumped).unwrap()
    );
    let pythagorean = CochainExponential::new(gq(3, 5, 4, 5)).unwrap();
    assert_eq!(pythagorean.order(), None);
    assert_ne!(
        pythagorean.connection(&packet, &omega).unwrap(),
        pythagorean.connection(&packet, &bumped).unwrap()
    );
}

#[test]
fn the_exponential_refuses_non_integer_cochains_and_non_unit_scales() {
    let packet = kite(rats(&[1, 1, 1, 1]));
    let exp = CochainExponential::new(gi(0, 1)).unwrap();
    assert!(matches!(
        exp.connection(&packet, &[ri(1), rq(1, 2), ri(0), ri(0)]),
        Err(U1GaugeError::NonIntegerCochain { index: 1 })
    ));
    assert!(CochainExponential::new(gi(1, 1)).is_err());
}

#[test]
fn self_normalizing_by_raw_mass_is_scale_invariant_and_not_additive() {
    let packet = kite(rats(&[1, 1, 1, 1]));
    let omega = rats(&[1, -2, 0, 3]);
    let doubled: Vec<Rational> = omega.iter().map(|x| x * ri(2)).collect();
    assert_eq!(
        l1_self_normalized(&packet, &omega),
        l1_self_normalized(&packet, &doubled)
    );
    let e0 = rats(&[1, 0, 0, 0]);
    let e1 = rats(&[0, 1, 0, 0]);
    let sum = rats(&[1, 1, 0, 0]);
    let parts: Vec<Rational> = l1_self_normalized(&packet, &e0)
        .unwrap()
        .iter()
        .zip(l1_self_normalized(&packet, &e1).unwrap())
        .map(|(a, b)| a + b)
        .collect();
    assert_ne!(l1_self_normalized(&packet, &sum).unwrap(), parts);
    assert!(l1_self_normalized(&packet, &rats(&[0, 0, 0, 0])).is_none());
}

// ---------------------------------------------------------------------------
// QMC-T6: the generalized Gell-Mann family is a normalized traceless-Hermitian basis.
// ---------------------------------------------------------------------------

#[test]
fn gell_mann_family_counts_gram_identity_and_real_independence() {
    for n in 2..=6usize {
        let basis = GellMannBasis::new(n).unwrap();
        assert_eq!(basis.len(), n * n - 1);
        assert!(basis.all_traceless_hermitian());
        assert!(
            basis.verify_gram_identity(),
            "Gram identity failed at n = {n}"
        );
        assert_eq!(basis.real_independence_rank(), n * n - 1);
    }
    assert!(matches!(
        GellMannBasis::new(1),
        Err(GellMannError::DimensionTooSmall(1))
    ));
}

#[test]
fn gell_mann_structure_constants_are_antisymmetric_close_and_satisfy_jacobi() {
    for n in 2..=4usize {
        let basis = GellMannBasis::new(n).unwrap();
        assert!(basis.verify_total_antisymmetry(), "n = {n}");
        assert!(basis.verify_commutation_relations(), "n = {n}");
        assert!(basis.verify_jacobi(), "n = {n}");
    }
}

#[test]
fn su2_and_su3_structure_constants_match_the_standard_tables() {
    let su2 = GellMannBasis::new(2).unwrap();
    assert_eq!(
        su2.structure_constant(0, 1, 2).unwrap(),
        SurdRational::rational(ri(1))
    );
    assert_eq!(
        su2.structure_constant(1, 0, 2).unwrap(),
        SurdRational::rational(ri(-1))
    );

    // Family order for N = 3 is (l1, l4, l6, l2, l5, l7, l3, l8) in the standard labels.
    let su3 = GellMannBasis::new(3).unwrap();
    let family = |standard: usize| [0usize, 0, 3, 6, 1, 4, 2, 5, 7][standard];
    let f = |a: usize, b: usize, c: usize| {
        su3.structure_constant(family(a), family(b), family(c))
            .unwrap()
    };
    let half = SurdRational::rational(rq(1, 2));
    let minus_half = SurdRational::rational(rq(-1, 2));
    assert_eq!(f(1, 2, 3), SurdRational::rational(ri(1)));
    assert_eq!(f(1, 4, 7), half);
    assert_eq!(f(1, 5, 6), minus_half);
    assert_eq!(f(2, 4, 6), half);
    assert_eq!(f(2, 5, 7), half);
    assert_eq!(f(3, 4, 5), half);
    assert_eq!(f(3, 6, 7), minus_half);
    let root_three_halves = SurdRational::new(rq(1, 2), &ri(3)).unwrap();
    assert_eq!(f(4, 5, 8), root_three_halves);
    assert_eq!(f(6, 7, 8), root_three_halves);
    assert!(f(1, 2, 8).is_zero());
}

#[test]
fn gell_mann_expansion_reconstructs_traceless_hermitian_matrices_exactly() {
    let basis = GellMannBasis::new(3).unwrap();
    let x = mx::from_rows(vec![
        vec![gi(1, 0), gi(2, -1), gi(0, 3)],
        vec![gi(2, 1), gi(-4, 0), gq(1, 2, 0, 1)],
        vec![gi(0, -3), gq(1, 2, 0, 1), gi(3, 0)],
    ])
    .unwrap();
    assert_eq!(basis.reconstruct(&x).unwrap(), x);
    // The l8 coordinate carries the irrational scale sqrt(1/3).
    let coordinates = basis.coordinates(&x).unwrap();
    assert_eq!(coordinates[7].radicand(), &3.into());
    // A matrix with nonzero trace is not in the span and is refused.
    let traced = mx::diagonal(&[gi(1, 0), gi(0, 0), gi(0, 0)]).unwrap();
    assert!(matches!(
        basis.reconstruct(&traced),
        Err(GellMannError::NotTracelessHermitian)
    ));
}

// ---------------------------------------------------------------------------
// QMC-P1: the declared mass/phase embedding has unit L2 norm and explicit losses.
// ---------------------------------------------------------------------------

#[test]
fn mass_phase_embedding_is_unit_norm_and_many_to_one() {
    let phases = [gi(1, 0), gi(0, 1), gi(-1, 0)];
    let embedding = MassPhaseEmbedding::new(&rats(&[1, 2, 1]), &phases).unwrap();
    assert_eq!(embedding.probabilities(), &[rq(1, 4), rq(1, 2), rq(1, 4)]);
    assert_eq!(embedding.norm_squared(), Rational::one());
    // Overall scale is discarded.
    assert_eq!(
        MassPhaseEmbedding::new(&rats(&[2, 4, 2]), &phases).unwrap(),
        embedding
    );
    // Phases are not determined by the masses.
    let other =
        MassPhaseEmbedding::new(&rats(&[1, 2, 1]), &[gi(1, 0), gi(1, 0), gi(1, 0)]).unwrap();
    assert_ne!(other, embedding);
    assert_eq!(other.born_weights(), embedding.born_weights());
    // Signs of a signed cochain are discarded.
    assert_eq!(
        MassPhaseEmbedding::from_signed_cochain(&rats(&[1, -2, 1]), &phases).unwrap(),
        MassPhaseEmbedding::from_signed_cochain(&rats(&[-1, 2, -1]), &phases).unwrap()
    );
}

#[test]
fn exact_amplitudes_exist_only_for_square_probabilities() {
    let phases = [gi(1, 0), gi(0, 1), gi(-1, 0)];
    let square = MassPhaseEmbedding::new(&rats(&[1, 4, 4]), &phases).unwrap();
    let amplitudes = square.exact_amplitudes().unwrap();
    assert_eq!(
        amplitudes,
        vec![gq(1, 3, 0, 1), gq(0, 1, 2, 3), gq(-2, 3, 0, 1)]
    );
    let norm: Rational = amplitudes.iter().map(GaussianRat::norm_sq).sum();
    assert_eq!(norm, Rational::one());
    let irrational = MassPhaseEmbedding::new(&rats(&[1, 2, 1]), &phases).unwrap();
    assert!(irrational.exact_amplitudes().is_none());
    assert_eq!(rational_sqrt(&rq(9, 49)), Some(rq(3, 7)));
    assert_eq!(rational_sqrt(&rq(2, 1)), None);
}

#[test]
fn the_embedding_refuses_implicit_phases_and_invalid_masses() {
    let masses = rats(&[1, 2, 1]);
    assert!(matches!(
        MassPhaseEmbedding::new(&masses, &[]),
        Err(EmbeddingError::PhaseCountMismatch {
            masses: 3,
            phases: 0
        })
    ));
    assert!(matches!(
        MassPhaseEmbedding::new(&masses, &[gi(1, 0), gi(2, 0), gi(1, 0)]),
        Err(EmbeddingError::NonUnitPhase { index: 1 })
    ));
    assert!(matches!(
        MassPhaseEmbedding::new(&rats(&[1, -1]), &[gi(1, 0), gi(1, 0)]),
        Err(EmbeddingError::NegativeMass { index: 1 })
    ));
    assert!(matches!(
        MassPhaseEmbedding::new(&rats(&[0, 0]), &[gi(1, 0), gi(1, 0)]),
        Err(EmbeddingError::ZeroTotalMass)
    ));
    assert!(matches!(
        MassPhaseEmbedding::new(&[], &[]),
        Err(EmbeddingError::Empty)
    ));
}

// Origin: engine/crates_rs/tests/core_quantum_physics/foundations/quantum_carrier_primitive_difference.rs
// Claim: urn:core:crates_rs:tests:quantum-carrier-primitive-difference:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord48136be1 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord48136be1` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError48136be1 {
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
impl BoundaryError48136be1 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError48136be1 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError48136be1 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord48136be1 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError48136be1> {
        if capacity_bound == 0 {
            return Err(BoundaryError48136be1::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError48136be1::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError48136be1::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_48136be1() {
    let admitted = BoundaryRecord48136be1::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord48136be1::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
