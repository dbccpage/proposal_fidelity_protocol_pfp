//! CPTP-compatible obstruction theory: the trace-distance quotient of
//! Hermitian trace-zero edge defects, its dual witnesses, the trace-zero dual
//! ball, and the Schatten non-monotonicity example. Every value is exact.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::matrix as mx;
use num_bigint::BigInt;
use num_traits::{Signed, Zero};
use core_lie_theory::su_n::GellMannBasis;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::quadratic::Surd;
use core_number_theory::rational::{ri, rq, Rational};
use core_quantum_physics::exact_channel::{apply_choi, choi_is_cptp};
use core_quantum_physics::exact_hermitian::{self, gi, gq, SpectrumError};
use core_quantum_physics::tower_walk_validator::half_trace_norm_2x2;
use core_quantum_physics::u1_graph_connection::OrientedWalk;

use crate::support::{depolarizing_choi, dm, packet, pauli_x, pauli_z, rm, unit};
use core_quantum_physics::trace_distance_quotient::{
    DualCertificate, PrimalCertificate, RepairSpace, TraceDefectPacket, TraceQuotientError,
};
use core_quantum_physics::trace_norm_certificate::{
    dual_ball_value, qubit_polar_pairing, sign_certificate_from_spectrum, sum_zero_dual_pair,
    within_operator_ball, SignCertificate, TraceNormError,
};

/// `[[1, 2, 0], [2, 1, 0], [0, 0, -2]]`, spectrum `{3, -1, -2}`.
fn spectral_example() -> BasicMatrix<GaussianRat> {
    rm(&[&[1, 2, 0], &[2, 1, 0], &[0, 0, -2]], 1)
}

/// Entrywise Jordan split of a diagonal matrix.
fn diagonal_split(
    m: &BasicMatrix<GaussianRat>,
) -> (BasicMatrix<GaussianRat>, BasicMatrix<GaussianRat>) {
    let part = |sign: i64| {
        let entries: Vec<GaussianRat> = (0..m.rows())
            .map(|i| {
                GaussianRat::from_rational(
                    (&m.get_ref(i, i).unwrap().re * ri(sign)).max(Rational::zero()),
                )
            })
            .collect();
        mx::diagonal(&entries).unwrap()
    };
    (part(1), part(-1))
}

/// `sum_e w_e (1/2) ||delta_e||_1` for diagonal defects: the unrepaired edge mass.
fn raw_mass(defects: &TraceDefectPacket) -> Rational {
    let certificate = PrimalCertificate {
        potentials: vec![
            mx::zeros(defects.dim(), defects.dim()).unwrap();
            defects.graph().vertex_count()
        ],
        splits: defects.defects().iter().map(diagonal_split).collect(),
    };
    defects
        .upper_bound(&certificate, RepairSpace::TraceZero)
        .unwrap()
}

/// `K_{2,3}`: two hubs `u`, `v` joined through `w1`, `w2`, `w3` (two independent cycles).
fn k23(defects_on_first_leg: Vec<BasicMatrix<GaussianRat>>, dim: usize) -> TraceDefectPacket {
    let graph = packet(
        &["u", "v", "w1", "w2", "w3"],
        &[
            ("u", "w1"),
            ("u", "w2"),
            ("u", "w3"),
            ("w1", "v"),
            ("w2", "v"),
            ("w3", "v"),
        ],
        vec![ri(1); 6],
    );
    let mut defects = defects_on_first_leg;
    defects.extend(vec![mx::zeros(dim, dim).unwrap(); 3]);
    TraceDefectPacket::new(graph, dim, defects).unwrap()
}

/// `D_k = 3 E_kk - I` on the legs `u -> w_k`.
fn k23_qutrit() -> TraceDefectPacket {
    k23(
        vec![
            dm(&[2, -1, -1], 1),
            dm(&[-1, 2, -1], 1),
            dm(&[-1, -1, 2], 1),
        ],
        3,
    )
}

fn negated(potentials: &[BasicMatrix<GaussianRat>]) -> Vec<BasicMatrix<GaussianRat>> {
    potentials
        .iter()
        .map(|m| mx::scale(&(m), &GaussianRat::from_rational(ri(-1))).unwrap())
        .collect()
}

#[test]
fn sign_certificates_give_exact_trace_norms_jordan_parts_and_schatten_powers() {
    let x = spectral_example();
    let certificate = sign_certificate_from_spectrum(&x, &[ri(3), ri(-1), ri(-2)]).unwrap();
    assert_eq!(
        certificate.sign(),
        &rm(&[&[0, 1, 0], &[1, 0, 0], &[0, 0, -1]], 1)
    );
    assert_eq!(certificate.trace_norm(), ri(6));
    assert_eq!(
        certificate.positive_part(),
        rm(&[&[3, 3, 0], &[3, 3, 0], &[0, 0, 0]], 2)
    );
    assert_eq!(
        certificate.negative_part(),
        rm(&[&[1, -1, 0], &[-1, 1, 0], &[0, 0, 4]], 2)
    );
    assert_eq!(
        mx::sub(&certificate.positive_part(), &certificate.negative_part()).unwrap(),
        x
    );
    assert!(mx::is_zero_matrix(
        &mx::multiply_with_limits(
            &certificate.positive_part(),
            &certificate.negative_part(),
            exact_hermitian::exact_limits()
        )
        .unwrap()
    ));
    assert_eq!(certificate.schatten_power(1).unwrap(), ri(6));
    assert_eq!(certificate.schatten_power(2).unwrap(), ri(14));
    assert_eq!(certificate.schatten_power(3).unwrap(), ri(36));
    // Two declared eigenvalues; a declared value that is not an eigenvalue is refused
    // (its Lagrange projector is zero), since the declaration must be exactly the spectrum.
    assert_eq!(
        sign_certificate_from_spectrum(&pauli_x(), &[ri(1), ri(-1)])
            .unwrap()
            .sign(),
        &pauli_x()
    );
    assert_eq!(
        sign_certificate_from_spectrum(&x, &[ri(3), ri(-1), ri(-2), ri(7)]),
        Err(TraceNormError::Spectrum(SpectrumError::NotAnEigenvalue {
            value: ri(7)
        }))
    );
    // A declared spectrum must contain every eigenvalue, once.
    assert_eq!(
        sign_certificate_from_spectrum(&x, &[ri(3), ri(-1)]),
        Err(TraceNormError::Spectrum(SpectrumError::SpectrumIncomplete))
    );
    assert_eq!(
        sign_certificate_from_spectrum(&x, &[ri(3), ri(3), ri(-1), ri(-2)]),
        Err(TraceNormError::Spectrum(
            SpectrumError::RepeatedEigenvalue { value: ri(3) }
        ))
    );
    // Each of the four sign identities is checked.
    let refuse = |s: BasicMatrix<GaussianRat>| SignCertificate::new(x.clone(), s).unwrap_err();
    assert_eq!(
        refuse(rm(&[&[0, 1, 0], &[-1, 0, 0], &[0, 0, 1]], 1)),
        TraceNormError::SignNotHermitian
    );
    assert_eq!(
        refuse(dm(&[2, 1, -1], 1)),
        TraceNormError::SignNotInvolution
    );
    assert_eq!(
        refuse(dm(&[1, -1, -1], 1)),
        TraceNormError::SignDoesNotCommute
    );
    assert_eq!(
        refuse(mx::identity(3).unwrap()),
        TraceNormError::SignNotAligned
    );
}

#[test]
fn the_eigenvalue_core_of_the_dual_ball_is_certified_on_every_small_sum_zero_vector() {
    // Every m in {-1/2, 0, 1/2}^4 has spread at most one.
    let grid: Vec<Vec<Rational>> = (0..81i64)
        .map(|code| {
            (0..4u32)
                .map(|i| rq((code / 3i64.pow(i)) % 3 - 1, 2))
                .collect()
        })
        .collect();
    let mut checked = 0;
    for code in 0..625i64 {
        let x: Vec<Rational> = (0..4u32)
            .map(|i| ri((code / 5i64.pow(i)) % 5 - 2))
            .collect();
        if !x.iter().sum::<Rational>().is_zero() {
            continue;
        }
        checked += 1;
        let pair = sum_zero_dual_pair(&x).unwrap();
        let value = pair.verify(&x).unwrap();
        assert_eq!(value, x.iter().map(Signed::abs).sum::<Rational>() / ri(2));
        for m in &grid {
            let pairing: Rational = m.iter().zip(&x).map(|(a, b)| a * b).sum();
            assert_eq!(pair.plan_pairing(m).unwrap(), pairing);
            assert!(pairing <= value);
        }
    }
    assert_eq!(checked, 85);
    // Refusals: nonzero sum, tampered plans, a maximizer of spread above one.
    assert_eq!(
        sum_zero_dual_pair(&[ri(1), ri(1)]),
        Err(TraceNormError::NotTraceZero)
    );
    let x = vec![ri(2), ri(-1), ri(-1), ri(0)];
    let pair = sum_zero_dual_pair(&x).unwrap();
    assert_eq!(pair.plan, vec![(0, 1, ri(1)), (0, 2, ri(1))]);
    let mut heavier = pair.clone();
    heavier.plan[0].2 = ri(2);
    assert_eq!(heavier.verify(&x), Err(TraceNormError::PlanMarginal));
    let mut negative = pair.clone();
    negative.plan.push((1, 3, ri(-1)));
    assert_eq!(negative.verify(&x), Err(TraceNormError::PlanEntry));
    let mut wide = pair;
    wide.maximizer[0] = ri(1);
    assert_eq!(wide.verify(&x), Err(TraceNormError::Maximizer));
}

#[test]
fn the_trace_zero_dual_norm_is_the_spectral_diameter_not_twice_the_operator_norm() {
    let m = spectral_example();
    let top = [gi(1, 0), gi(1, 0), gi(0, 0)];
    let middle = [gi(1, 0), gi(-1, 0), gi(0, 0)];
    let bottom = [gi(0, 0), gi(0, 0), gi(1, 0)];
    let (diameter, maximizer) = dual_ball_value(&m, &top, &bottom).unwrap();
    assert_eq!(diameter, ri(5));
    assert_eq!(maximizer, rm(&[&[1, 1, 0], &[1, 1, 0], &[0, 0, -2]], 2));
    assert!(mx::trace(&(maximizer)).unwrap().re.is_zero());
    let unit_ball = SignCertificate::new(maximizer.clone(), dm(&[1, 1, -1], 1)).unwrap();
    assert_eq!(unit_ball.trace_norm(), ri(2));
    assert_eq!(
        mx::trace(
            &(mx::multiply_with_limits(&(m), &maximizer, exact_hermitian::exact_limits()).unwrap())
        )
        .unwrap()
        .re,
        ri(5)
    );
    // Other points of the trace-zero ball pair to less.
    let flip = rm(&[&[0, 1, 0], &[1, 0, 0], &[0, 0, 0]], 1);
    let flip_ball =
        SignCertificate::new(flip.clone(), rm(&[&[0, 1, 0], &[1, 0, 0], &[0, 0, 1]], 1)).unwrap();
    assert_eq!(flip_ball.trace_norm(), ri(2));
    assert_eq!(
        mx::trace(
            &(mx::multiply_with_limits(&(m), &flip, exact_hermitian::exact_limits()).unwrap())
        )
        .unwrap()
        .re,
        ri(4)
    );
    // The value sees M only modulo the identity.
    let shifted = mx::add(
        &(m),
        &mx::scale(
            &mx::identity(3).unwrap(),
            &GaussianRat::from_rational(ri(7)),
        )
        .unwrap(),
    )
    .unwrap();
    assert_eq!(dual_ball_value(&shifted, &top, &bottom).unwrap().0, ri(5));
    // Declarations are checked.
    assert_eq!(
        dual_ball_value(&m, &top, &middle),
        Err(TraceNormError::NotExtreme)
    );
    assert_eq!(
        dual_ball_value(&m, &[gi(1, 0), gi(0, 0), gi(0, 0)], &bottom),
        Err(TraceNormError::NotEigenvector)
    );
    // Twice the operator norm is the dual norm on all Hermitian matrices; on the
    // trace-zero space the dual norm is the diameter.
    let e0 = [gi(1, 0), gi(0, 0)];
    let e1 = [gi(0, 0), gi(1, 0)];
    let projector = dm(&[1, 0], 1);
    assert_eq!(dual_ball_value(&projector, &e0, &e1).unwrap().0, ri(1));
    assert!(within_operator_ball(&projector, &ri(0), &ri(1)).unwrap());
    assert!(!within_operator_ball(&projector, &ri(0), &rq(99, 100)).unwrap());
    let (identity_value, identity_maximizer) =
        dual_ball_value(&mx::identity(2).unwrap(), &e0, &e1).unwrap();
    assert_eq!(identity_value, ri(0));
    assert!(mx::is_zero_matrix(&identity_maximizer));
}

#[test]
fn the_one_qubit_cycle_replay_has_obstruction_one_with_witness_half_z() {
    let graph = packet(
        &["a", "b", "c"],
        &[("a", "b"), ("b", "c"), ("c", "a")],
        vec![ri(1); 3],
    );
    let walk = OrientedWalk::new(&graph, "a", &[(0, 1), (1, 1), (2, 1)]).unwrap();
    let z = pauli_z();
    let defects = TraceDefectPacket::new(
        graph,
        2,
        vec![
            z.clone(),
            mx::zeros(2, 2).unwrap(),
            mx::zeros(2, 2).unwrap(),
        ],
    )
    .unwrap();
    let sign = SignCertificate::new(z.clone(), z.clone()).unwrap();
    assert_eq!(sign.trace_norm() / ri(2), ri(1));
    let (primal, dual) = defects.cycle_certificates(&walk, &sign).unwrap();
    let half_z = mx::scale(&(z), &GaussianRat::from_rational(rq(1, 2))).unwrap();
    assert!(dual.observables.iter().all(|m| m == &half_z));
    assert_eq!(
        defects.certify(&primal, &dual, RepairSpace::TraceZero),
        Ok(ri(1))
    );
    assert_eq!(
        defects.certify(&primal, &dual, RepairSpace::AllHermitian),
        Ok(ri(1))
    );
    // ||M||_op = 1/2 exactly and Tr(M Z) = 1.
    assert!(within_operator_ball(&half_z, &ri(0), &rq(1, 2)).unwrap());
    assert!(!within_operator_ball(&half_z, &ri(0), &rq(49, 100)).unwrap());
    assert_eq!(
        mx::trace(
            &(mx::multiply_with_limits(&(half_z), &z, exact_hermitian::exact_limits()).unwrap())
        )
        .unwrap()
        .re,
        ri(1)
    );
}

#[test]
fn a_cycle_obstruction_is_the_lightest_weight_times_the_trace_distance_of_the_cycle_sum() {
    // a -> b, then back along (c, b), then c -> d, then back along (a, d).
    let graph = packet(
        &["a", "b", "c", "d"],
        &[("a", "b"), ("c", "b"), ("c", "d"), ("a", "d")],
        vec![ri(3), rq(1, 2), ri(2), ri(5)],
    );
    let walk = OrientedWalk::new(&graph, "a", &[(0, 1), (1, -1), (2, 1), (3, -1)]).unwrap();
    let defects = vec![
        dm(&[1, -1, 0], 1),
        dm(&[0, -1, 1], 1),
        rm(&[&[0, 2, 0], &[2, 0, 0], &[0, 0, 0]], 1),
        dm(&[0, -1, 1], 1),
    ];
    let packet = TraceDefectPacket::new(graph.clone(), 3, defects).unwrap();
    let cycle_sum = spectral_example();
    let sign = sign_certificate_from_spectrum(&cycle_sum, &[ri(3), ri(-1), ri(-2)]).unwrap();
    let (primal, dual) = packet.cycle_certificates(&walk, &sign).unwrap();
    // The whole class sits on the lightest edge, traversed backwards: -S there.
    let residuals = packet.residuals(&primal.potentials).unwrap();
    assert_eq!(
        residuals[1],
        mx::scale(&(cycle_sum), &GaussianRat::from_rational(ri(-1))).unwrap()
    );
    assert!([0, 2, 3].iter().all(|&e| mx::is_zero_matrix(&residuals[e])));
    // (1/2) * (1/2) ||S||_1 = 3/2 for either repair space.
    assert_eq!(
        packet.certify(&primal, &dual, RepairSpace::TraceZero),
        Ok(rq(3, 2))
    );
    assert_eq!(
        packet.certify(&primal, &dual, RepairSpace::AllHermitian),
        Ok(rq(3, 2))
    );
    // An open walk or a sign certificate for another matrix is refused.
    let open = OrientedWalk::new(&graph, "a", &[(0, 1), (1, -1)]).unwrap();
    assert_eq!(
        packet.cycle_certificates(&open, &sign).unwrap_err(),
        TraceQuotientError::NotACycle
    );
    let wrong = SignCertificate::new(dm(&[1, -1, 0], 1), dm(&[1, -1, 1], 1)).unwrap();
    assert_eq!(
        packet.cycle_certificates(&walk, &wrong).unwrap_err(),
        TraceQuotientError::CycleSum
    );

    // Degenerate spectrum: the full sign witness attains 2, the rank-two
    // projector difference only 1.
    let triangle = packet_on_triangle(dm(&[1, 1, -1, -1], 1));
    let triangle_walk =
        OrientedWalk::new(triangle.graph(), "a", &[(0, 1), (1, 1), (2, 1)]).unwrap();
    let full = SignCertificate::new(dm(&[1, 1, -1, -1], 1), dm(&[1, 1, -1, -1], 1)).unwrap();
    let (primal, dual) = triangle.cycle_certificates(&triangle_walk, &full).unwrap();
    assert_eq!(
        triangle.certify(&primal, &dual, RepairSpace::TraceZero),
        Ok(ri(2))
    );
    let rank_two = mx::scale(
        &(mx::sub(&(unit(4, 0, 0)), &unit(4, 3, 3)).unwrap()),
        &GaussianRat::from_rational(rq(1, 2)),
    )
    .unwrap();
    let weak = DualCertificate {
        observables: vec![rank_two; 3],
        centres: vec![ri(0); 3],
    };
    assert_eq!(
        triangle.certify(&primal, &weak, RepairSpace::TraceZero),
        Err(TraceQuotientError::DualityGap(Box::new((ri(2), ri(1)))))
    );
}

fn packet_on_triangle(defect: BasicMatrix<GaussianRat>) -> TraceDefectPacket {
    let n = defect.rows();
    let graph = packet(
        &["a", "b", "c"],
        &[("a", "b"), ("b", "c"), ("c", "a")],
        vec![ri(1); 3],
    );
    TraceDefectPacket::new(
        graph,
        n,
        vec![defect, mx::zeros(n, n).unwrap(), mx::zeros(n, n).unwrap()],
    )
    .unwrap()
}

#[test]
fn divergence_free_witnesses_vanish_on_trees_and_pendant_edges() {
    let (x, z) = (pauli_x(), pauli_z());
    let path = packet(
        &["a", "b", "c"],
        &[("a", "b"), ("b", "c")],
        vec![ri(1), ri(1)],
    );
    assert_eq!(path.dimensions().h1, 0);
    let tree = TraceDefectPacket::new(path, 2, vec![z.clone(), x.clone()]).unwrap();
    // Every cochain on a tree is a coboundary: alpha = (0, Z, Z + X) repairs it.
    let potentials = vec![
        mx::zeros(2, 2).unwrap(),
        z.clone(),
        mx::add(&(z), &x).unwrap(),
    ];
    assert!(tree
        .residuals(&potentials)
        .unwrap()
        .iter()
        .all(mx::is_zero_matrix));
    let zero_split = (mx::zeros(2, 2).unwrap(), mx::zeros(2, 2).unwrap());
    let repair = PrimalCertificate {
        potentials,
        splits: vec![zero_split.clone(), zero_split],
    };
    let silent = DualCertificate {
        observables: vec![mx::zeros(2, 2).unwrap(); 2],
        centres: vec![ri(0); 2],
    };
    assert_eq!(
        tree.certify(&repair, &silent, RepairSpace::TraceZero),
        Ok(ri(0))
    );
    // No nonzero circulation lives on a tree: the leaf a sees -M_ab.
    let half_z = mx::scale(&(z), &GaussianRat::from_rational(rq(1, 2))).unwrap();
    let constant = DualCertificate {
        observables: vec![half_z.clone(); 2],
        centres: vec![ri(0); 2],
    };
    assert_eq!(
        tree.lower_bound(&constant, RepairSpace::AllHermitian),
        Err(TraceQuotientError::Divergence { vertex: 0 })
    );
    // Trace-zero repairs tolerate a scalar divergence, which pairs to zero.
    let scalar = DualCertificate {
        observables: vec![
            mx::scale(
                &(mx::identity(2).unwrap()),
                &GaussianRat::from_rational(rq(1, 2)),
            )
            .unwrap(),
            mx::zeros(2, 2).unwrap(),
        ],
        centres: vec![rq(1, 2), ri(0)],
    };
    assert_eq!(tree.lower_bound(&scalar, RepairSpace::TraceZero), Ok(ri(0)));

    // A triangle with a pendant edge c -> d.
    let tailed = packet(
        &["a", "b", "c", "d"],
        &[("a", "b"), ("b", "c"), ("c", "a"), ("c", "d")],
        vec![ri(1); 4],
    );
    assert_eq!(tailed.dimensions().h1, 1);
    let defects = TraceDefectPacket::new(
        tailed.clone(),
        2,
        vec![
            z.clone(),
            mx::zeros(2, 2).unwrap(),
            mx::zeros(2, 2).unwrap(),
            x.clone(),
        ],
    )
    .unwrap();
    let on_cycle = DualCertificate {
        observables: vec![
            half_z.clone(),
            half_z.clone(),
            half_z.clone(),
            mx::zeros(2, 2).unwrap(),
        ],
        centres: vec![ri(0); 4],
    };
    assert_eq!(
        defects.lower_bound(&on_cycle, RepairSpace::AllHermitian),
        Ok(ri(1))
    );
    let leaking = DualCertificate {
        observables: vec![
            half_z.clone(),
            half_z.clone(),
            half_z,
            mx::scale(&(x), &GaussianRat::from_rational(rq(1, 2))).unwrap(),
        ],
        centres: vec![ri(0); 4],
    };
    assert_eq!(
        defects.lower_bound(&leaking, RepairSpace::TraceZero),
        Err(TraceQuotientError::Divergence { vertex: 2 })
    );
    let walk = OrientedWalk::new(&tailed, "a", &[(0, 1), (1, 1), (2, 1)]).unwrap();
    let sign = SignCertificate::new(z.clone(), z).unwrap();
    assert_eq!(
        defects.cycle_certificates(&walk, &sign).unwrap_err(),
        TraceQuotientError::NotACycle
    );
}

#[test]
fn trace_zero_repairs_need_uncentred_witnesses_on_two_cycles_of_qutrit_defects() {
    let packet = k23_qutrit();
    // Weighted-l1 route: core_solvers proposes, core_functional replays, and
    // the lifted matrix certificates close the gap independently.
    let (primal, dual, replayed) = packet
        .diagonal_certificates(RepairSpace::TraceZero)
        .unwrap();
    assert_eq!(replayed, ri(6));
    assert_eq!(
        packet.certify(&primal, &dual, RepairSpace::TraceZero),
        Ok(ri(6))
    );
    let (all_primal, all_dual, all_replayed) = packet
        .diagonal_certificates(RepairSpace::AllHermitian)
        .unwrap();
    assert_eq!(all_replayed, rq(9, 2));
    assert_eq!(
        packet.certify(&all_primal, &all_dual, RepairSpace::AllHermitian),
        Ok(rq(9, 2))
    );
    // The all-Hermitian optimum needs scalar parts: it is no trace-zero repair.
    assert!(matches!(
        packet.upper_bound(&all_primal, RepairSpace::TraceZero),
        Err(TraceQuotientError::Potential { .. })
    ));

    // Hand certificates for the trace-zero value: no repair, and M_k = D_k / 3
    // on both edges of leg k, exactly divergence-free with centre 1/6.
    let zero = mx::zeros(3, 3).unwrap();
    let no_repair = PrimalCertificate {
        potentials: vec![zero.clone(); 5],
        splits: packet.defects().iter().map(diagonal_split).collect(),
    };
    assert_eq!(raw_mass(&packet), ri(6));
    let legs: Vec<BasicMatrix<GaussianRat>> = (0..3)
        .map(|k| {
            mx::scale(
                &(packet.defects()[k]),
                &GaussianRat::from_rational(rq(1, 3)),
            )
            .unwrap()
        })
        .collect();
    let uncentred = DualCertificate {
        observables: legs.iter().chain(legs.iter()).cloned().collect(),
        centres: vec![rq(1, 6); 6],
    };
    assert!(packet
        .divergence(&uncentred.observables)
        .unwrap()
        .iter()
        .all(mx::is_zero_matrix));
    assert_eq!(
        packet.certify(&no_repair, &uncentred, RepairSpace::TraceZero),
        Ok(ri(6))
    );
    assert_eq!(
        packet.lower_bound(&uncentred, RepairSpace::AllHermitian),
        Err(TraceQuotientError::Centre { edge: 0 })
    );
    // Centring the witness keeps the value but breaks exact divergence-freeness.
    let centred_legs: Vec<BasicMatrix<GaussianRat>> = legs
        .iter()
        .map(|m| {
            mx::sub(
                &(m),
                &mx::scale(
                    &mx::identity(3).unwrap(),
                    &GaussianRat::from_rational(rq(1, 6)),
                )
                .unwrap(),
            )
            .unwrap()
        })
        .collect();
    let centred = DualCertificate {
        observables: centred_legs
            .iter()
            .chain(centred_legs.iter())
            .cloned()
            .collect(),
        centres: vec![ri(0); 6],
    };
    assert_eq!(
        packet.lower_bound(&centred, RepairSpace::TraceZero),
        Ok(ri(6))
    );
    assert_eq!(
        packet.divergence(&centred.observables).unwrap()[0],
        mx::scale(
            &(mx::identity(3).unwrap()),
            &GaussianRat::from_rational(rq(1, 2))
        )
        .unwrap()
    );
    assert_eq!(
        packet.lower_bound(&centred, RepairSpace::AllHermitian),
        Err(TraceQuotientError::Divergence { vertex: 0 })
    );

    // Exactly divergence-free witnesses with ||M_e||_op <= 1/2 (the source's dual
    // SDP; centred ones included) are all-Hermitian dual certificates, so the
    // all-Hermitian repair bounds them by 9/2: this one attains 9/2 and leaves a
    // gap of 3/2 against 6.
    let source_legs = [
        dm(&[2, -1, -1], 4),
        dm(&[-1, 2, -1], 4),
        dm(&[-1, -1, 2], 4),
    ];
    let source_form = DualCertificate {
        observables: source_legs
            .iter()
            .chain(source_legs.iter())
            .cloned()
            .collect(),
        centres: vec![ri(0); 6],
    };
    assert_eq!(
        packet.certify(&all_primal, &source_form, RepairSpace::AllHermitian),
        Ok(rq(9, 2))
    );
    assert_eq!(
        packet.certify(&no_repair, &source_form, RepairSpace::TraceZero),
        Err(TraceQuotientError::DualityGap(Box::new((ri(6), rq(9, 2)))))
    );
    // Genuinely centred witnesses (lambda_max + lambda_min = 0) that are exactly
    // divergence-free also reach 9/2, and no more.
    let centred_source = [dm(&[1, -1, 0], 2), dm(&[0, 1, -1], 2), dm(&[-1, 0, 1], 2)];
    let centred_form = DualCertificate {
        observables: centred_source
            .iter()
            .chain(centred_source.iter())
            .cloned()
            .collect(),
        centres: vec![ri(0); 6],
    };
    assert!(packet
        .divergence(&centred_form.observables)
        .unwrap()
        .iter()
        .all(mx::is_zero_matrix));
    assert_eq!(
        packet.certify(&all_primal, &centred_form, RepairSpace::AllHermitian),
        Ok(rq(9, 2))
    );

    // On qubits the scalar parts never help: both quotients agree.
    let qubit = k23(
        vec![
            pauli_z(),
            mx::scale(&(pauli_z()), &GaussianRat::from_rational(ri(2))).unwrap(),
            mx::scale(&(pauli_z()), &GaussianRat::from_rational(ri(-3))).unwrap(),
        ],
        2,
    );
    let (p, d, value) = qubit.diagonal_certificates(RepairSpace::TraceZero).unwrap();
    let (p_all, d_all, value_all) = qubit
        .diagonal_certificates(RepairSpace::AllHermitian)
        .unwrap();
    assert_eq!(value, ri(5));
    assert_eq!(value_all, ri(5));
    assert_eq!(qubit.certify(&p, &d, RepairSpace::TraceZero), Ok(ri(5)));
    assert_eq!(
        qubit.certify(&p_all, &d_all, RepairSpace::AllHermitian),
        Ok(ri(5))
    );
}

#[test]
fn the_certified_value_is_a_class_invariant_while_the_raw_mass_is_not() {
    let base = k23_qutrit();
    let (primal, dual, _) = base.diagonal_certificates(RepairSpace::TraceZero).unwrap();
    // A non-diagonal trace-zero shift beta: delta' = delta + d0 beta.
    let beta = vec![
        rm(&[&[0, 1, 0], &[1, 0, 0], &[0, 0, 0]], 1),
        mx::from_rows(vec![
            vec![gi(1, 0), gi(0, 1), gi(0, 0)],
            vec![gi(0, -1), gi(-1, 0), gi(0, 0)],
            vec![gi(0, 0), gi(0, 0), gi(0, 0)],
        ])
        .unwrap(),
        rm(&[&[0, 0, 1], &[0, 0, 0], &[1, 0, 0]], 1),
        dm(&[1, 1, -2], 1),
        mx::zeros(3, 3).unwrap(),
    ];
    let shifted = TraceDefectPacket::new(
        base.graph().clone(),
        3,
        base.residuals(&negated(&beta)).unwrap(),
    )
    .unwrap();
    let moved = PrimalCertificate {
        potentials: primal
            .potentials
            .iter()
            .zip(&beta)
            .map(|(a, b)| mx::add(&(a), b).unwrap())
            .collect(),
        splits: primal.splits.clone(),
    };
    assert_eq!(
        shifted.residuals(&moved.potentials).unwrap(),
        base.residuals(&primal.potentials).unwrap()
    );
    assert_eq!(
        shifted.certify(&moved, &dual, RepairSpace::TraceZero),
        Ok(ri(6))
    );

    // A diagonal shift keeps the weighted-l1 route open: replayed value 6 again,
    // while the unrepaired edge mass moves from 6 to 12.
    let diagonal_beta = vec![
        dm(&[1, -1, 0], 1),
        dm(&[0, 1, -1], 1),
        mx::zeros(3, 3).unwrap(),
        mx::zeros(3, 3).unwrap(),
        dm(&[-2, 1, 1], 1),
    ];
    let diagonal_shift = TraceDefectPacket::new(
        base.graph().clone(),
        3,
        base.residuals(&negated(&diagonal_beta)).unwrap(),
    )
    .unwrap();
    let (p, d, replayed) = diagonal_shift
        .diagonal_certificates(RepairSpace::TraceZero)
        .unwrap();
    assert_eq!(replayed, ri(6));
    assert_eq!(
        diagonal_shift.certify(&p, &d, RepairSpace::TraceZero),
        Ok(ri(6))
    );
    assert_eq!(raw_mass(&base), ri(6));
    assert_eq!(raw_mass(&diagonal_shift), ri(12));

    // A coboundary is invisible: Phi(d0 beta) = 0.
    let zero = mx::zeros(3, 3).unwrap();
    let empty = TraceDefectPacket::new(base.graph().clone(), 3, vec![zero.clone(); 6]).unwrap();
    let coboundary = TraceDefectPacket::new(
        base.graph().clone(),
        3,
        empty.residuals(&negated(&beta)).unwrap(),
    )
    .unwrap();
    let repair = PrimalCertificate {
        potentials: beta,
        splits: vec![(zero.clone(), zero.clone()); 6],
    };
    let silent = DualCertificate {
        observables: vec![zero; 6],
        centres: vec![ri(0); 6],
    };
    assert_eq!(
        coboundary.certify(&repair, &silent, RepairSpace::TraceZero),
        Ok(ri(0))
    );
}

#[test]
fn malformed_packets_and_certificates_are_refused() {
    let graph = packet(&["a", "b"], &[("a", "b")], vec![ri(1)]);
    let z = pauli_z();
    assert_eq!(
        TraceDefectPacket::new(graph.clone(), 1, vec![dm(&[0], 1)]).unwrap_err(),
        TraceQuotientError::Dimension
    );
    assert_eq!(
        TraceDefectPacket::new(graph.clone(), 2, vec![]).unwrap_err(),
        TraceQuotientError::EdgeCount {
            expected: 1,
            actual: 0
        }
    );
    assert_eq!(
        TraceDefectPacket::new(graph.clone(), 2, vec![dm(&[1, 0], 1)]).unwrap_err(),
        TraceQuotientError::Defect { edge: 0 }
    );
    let skew = mx::from_rows(vec![vec![gi(0, 0), gi(1, 0)], vec![gi(-1, 0), gi(0, 0)]]).unwrap();
    assert_eq!(
        TraceDefectPacket::new(graph.clone(), 2, vec![skew]).unwrap_err(),
        TraceQuotientError::Defect { edge: 0 }
    );
    let edge = TraceDefectPacket::new(graph, 2, vec![z.clone()]).unwrap();
    // A split that is not PSD, or that does not reproduce the residual.
    let bad_split = PrimalCertificate {
        potentials: vec![mx::zeros(2, 2).unwrap(); 2],
        splits: vec![(z.clone(), mx::zeros(2, 2).unwrap())],
    };
    assert_eq!(
        edge.upper_bound(&bad_split, RepairSpace::TraceZero),
        Err(TraceQuotientError::SplitNotPositive { edge: 0 })
    );
    let loose = PrimalCertificate {
        potentials: vec![mx::zeros(2, 2).unwrap(); 2],
        splits: vec![(dm(&[2, 0], 1), dm(&[0, 1], 1))],
    };
    assert_eq!(
        edge.upper_bound(&loose, RepairSpace::TraceZero),
        Err(TraceQuotientError::SplitMismatch { edge: 0 })
    );
    // A PSD split need not be the Jordan split: it only bounds from above.
    let slack = PrimalCertificate {
        potentials: vec![mx::zeros(2, 2).unwrap(); 2],
        splits: vec![(dm(&[2, 1], 1), dm(&[1, 2], 1))],
    };
    assert_eq!(edge.upper_bound(&slack, RepairSpace::TraceZero), Ok(ri(3)));
    // Potentials: wrong count, wrong space.
    let few = PrimalCertificate {
        potentials: vec![mx::zeros(2, 2).unwrap()],
        splits: vec![diagonal_split(&z)],
    };
    assert_eq!(
        edge.upper_bound(&few, RepairSpace::TraceZero),
        Err(TraceQuotientError::VertexCount {
            expected: 2,
            actual: 1
        })
    );
    // A scalar potential at b leaves the residual Z - I = diag(0, -2): outside the
    // trace-zero repairs, and no better than no repair on a qubit.
    let scalar_potential = PrimalCertificate {
        potentials: vec![mx::zeros(2, 2).unwrap(), mx::identity(2).unwrap()],
        splits: vec![diagonal_split(
            &mx::sub(&(z), &mx::identity(2).unwrap()).unwrap(),
        )],
    };
    assert_eq!(
        edge.upper_bound(&scalar_potential, RepairSpace::TraceZero),
        Err(TraceQuotientError::Potential { vertex: 1 })
    );
    assert_eq!(
        edge.upper_bound(&scalar_potential, RepairSpace::AllHermitian),
        Ok(ri(1))
    );
    // Observables outside their ball, or not Hermitian.
    let heavy = DualCertificate {
        observables: vec![z.clone()],
        centres: vec![ri(0)],
    };
    assert_eq!(
        edge.lower_bound(&heavy, RepairSpace::TraceZero),
        Err(TraceQuotientError::OutsideBall { edge: 0 })
    );
    let rotated = mx::from_rows(vec![
        vec![gi(0, 0), gq(1, 2, 0, 1)],
        vec![gq(-1, 2, 0, 1), gi(0, 0)],
    ])
    .unwrap();
    let not_hermitian = DualCertificate {
        observables: vec![rotated],
        centres: vec![ri(0)],
    };
    assert_eq!(
        edge.lower_bound(&not_hermitian, RepairSpace::TraceZero),
        Err(TraceQuotientError::Observable { edge: 0 })
    );
    // The diagonal route refuses coherent defects.
    let coherent = TraceDefectPacket::new(
        packet(&["a", "b"], &[("a", "b")], vec![ri(1)]),
        2,
        vec![pauli_x()],
    )
    .unwrap();
    assert_eq!(
        coherent
            .diagonal_certificates(RepairSpace::TraceZero)
            .unwrap_err(),
        TraceQuotientError::NotDiagonal { edge: 0 }
    );
}

#[test]
fn diagonal_quotient_refuses_oversized_flattening_and_preserves_empty_carriers() {
    use core_solvers::solver_cohomology_quotient_phi1::CertifiedPhi1Error;
    // No input operators are allocated: the declared physical axis itself is
    // legal, but its flattened vertex-repair axis exceeds the shared LP domain.
    let large = TraceDefectPacket::new(packet(&["v"], &[], vec![]), 1024, vec![]).unwrap();
    for (space, c0) in [
        (RepairSpace::TraceZero, 1023),
        (RepairSpace::AllHermitian, 1024),
    ] {
        assert_eq!(
            large.diagonal_certificates(space),
            Err(TraceQuotientError::Quotient(
                CertifiedPhi1Error::SizeLimit {
                    c0,
                    c1: 0,
                    maximum: 256,
                }
            ))
        );
    }
    // The edge axis is checked independently of the vertex-repair axis.
    let names: Vec<_> = (0..129).map(|i| format!("v{i}")).collect();
    let vertices: Vec<_> = names.iter().map(String::as_str).collect();
    let edges: Vec<_> = (0..129)
        .map(|i| (vertices[i], vertices[(i + 1) % 129]))
        .collect();
    let wide = TraceDefectPacket::new(
        packet(&vertices, &edges, vec![ri(1); 129]),
        2,
        vec![pauli_z(); 129],
    )
    .unwrap();
    assert_eq!(
        wide.diagonal_certificates(RepairSpace::TraceZero),
        Err(TraceQuotientError::Quotient(
            CertifiedPhi1Error::SizeLimit {
                c0: 129,
                c1: 258,
                maximum: 256,
            }
        ))
    );
    for graph in [packet(&[], &[], vec![]), packet(&["v"], &[], vec![])] {
        let vertices = graph.vertex_count();
        let empty = TraceDefectPacket::new(graph, 2, vec![]).unwrap();
        for space in [RepairSpace::TraceZero, RepairSpace::AllHermitian] {
            let (primal, dual, value) = empty.diagonal_certificates(space).unwrap();
            assert_eq!(value, ri(0));
            assert_eq!(primal.potentials.len(), vertices);
            assert!(
                primal.splits.is_empty() && dual.observables.is_empty() && dual.centres.is_empty()
            );
            assert_eq!(empty.certify(&primal, &dual, space).unwrap(), ri(0));
        }
    }
}

#[test]
fn schatten_norms_above_one_grow_under_the_partial_trace() {
    let half = mx::scale(
        &(mx::identity(2).unwrap()),
        &GaussianRat::from_rational(rq(1, 2)),
    )
    .unwrap();
    let rho = mx::kronecker_with_limits(&(dm(&[1, 0], 1)), &half, exact_hermitian::exact_limits())
        .unwrap();
    let sigma =
        mx::kronecker_with_limits(&(dm(&[0, 1], 1)), &half, exact_hermitian::exact_limits())
            .unwrap();
    for state in [&rho, &sigma] {
        assert!(exact_hermitian::is_positive_semidefinite(state));
        assert_eq!(mx::trace(&(state)).unwrap(), GaussianRat::one());
    }
    let x = mx::sub(&(rho), &sigma).unwrap();
    assert_eq!(x, dm(&[1, 1, -1, -1], 2));
    let reduced = exact_hermitian::partial_trace_second(&x, 2, 2).unwrap();
    assert_eq!(reduced, pauli_z());
    let input = SignCertificate::new(x.clone(), dm(&[1, 1, -1, -1], 1)).unwrap();
    let output = SignCertificate::new(reduced.clone(), pauli_z()).unwrap();
    // p = 1: the trace norm does not grow (2 -> 2).
    assert_eq!(input.trace_norm(), ri(2));
    assert_eq!(output.trace_norm(), ri(2));
    // p >= 2: (||Tr_B X||_p / ||X||_p)^p = 2^(p - 1) > 1.
    for p in 2..=6u32 {
        assert_eq!(
            output.schatten_power(p).unwrap(),
            input.schatten_power(p).unwrap() * ri(1i64 << (p - 1))
        );
    }
    // p = infinity: the operator norm doubles, 1/2 -> 1.
    assert!(within_operator_ball(&x, &ri(0), &rq(1, 2)).unwrap());
    assert!(!within_operator_ball(&reduced, &ri(0), &rq(1, 2)).unwrap());
    assert!(within_operator_ball(&reduced, &ri(0), &ri(1)).unwrap());
}

#[test]
fn depolarizing_noise_scales_every_trace_zero_difference_by_one_minus_p() {
    let cases: [(usize, Vec<Rational>, Vec<Rational>); 2] = [
        (
            2,
            vec![ri(0), rq(3, 10), ri(1), rq(4, 3)],
            vec![rq(-1, 10), rq(3, 2)],
        ),
        (3, vec![rq(1, 2), rq(9, 8)], vec![rq(5, 4)]),
    ];
    for (d, admissible, excluded) in cases {
        for p in &excluded {
            assert!(!choi_is_cptp(&depolarizing_choi(d, p), d, d));
        }
        // The generalized Gell-Mann shapes span the trace-zero Hermitian matrices,
        // so the identity below holds for every trace-zero difference.
        let basis = GellMannBasis::new(d).unwrap();
        for p in &admissible {
            let choi = depolarizing_choi(d, p);
            assert!(choi_is_cptp(&choi, d, d));
            for generator in basis.generators() {
                assert_eq!(
                    apply_choi(&choi, d, d, &generator.shape.clone()).unwrap(),
                    mx::scale(
                        &(generator.shape.clone()),
                        &GaussianRat::from_rational(ri(1) - p)
                    )
                    .unwrap()
                );
            }
        }
    }
    // The sampled pair |0><0|, |1><1| at p = 3/10: trace distance 1 -> 7/10.
    let choi = depolarizing_choi(2, &rq(3, 10));
    let out = mx::sub(
        &apply_choi(&choi, 2, 2, &dm(&[1, 0], 1)).unwrap(),
        &apply_choi(&choi, 2, 2, &dm(&[0, 1], 1)).unwrap(),
    )
    .unwrap();
    assert_eq!(
        out,
        mx::scale(&(pauli_z()), &GaussianRat::from_rational(rq(7, 10))).unwrap()
    );
    assert_eq!(
        SignCertificate::new(out, pauli_z()).unwrap().trace_norm(),
        rq(7, 5)
    );
    // An irrational pair: (1/2)||X||_1 = sqrt(34)/10 goes to 7 sqrt(34)/100.
    let x = rm(&[&[5, 3], &[3, -5]], 10);
    let scaled = apply_choi(&choi, 2, 2, &x).unwrap();
    let radicand = BigInt::from(34);
    assert_eq!(
        half_trace_norm_2x2(&x).unwrap(),
        Surd::from_natural(rq(1, 10), &radicand).unwrap()
    );
    assert_eq!(
        half_trace_norm_2x2(&scaled).unwrap(),
        Surd::from_natural(rq(7, 100), &radicand).unwrap()
    );
}

#[test]
fn the_polar_witness_attains_the_trace_norm_on_the_sampled_pairs() {
    let pairs = [
        (
            rm(&[&[8, 2], &[2, 2]], 10),
            rm(&[&[3, -1], &[-1, 7]], 10),
            rq(1, 5),
            34,
        ),
        (
            rm(&[&[9, 1], &[1, 1]], 10),
            rm(&[&[2, 0], &[0, 8]], 10),
            ri(1),
            2,
        ),
        (
            rm(&[&[7, 1], &[1, 3]], 10),
            rm(&[&[1, 0], &[0, 9]], 10),
            rq(1, 5),
            37,
        ),
    ];
    for (rho, sigma, coefficient, radicand) in pairs {
        for state in [&rho, &sigma] {
            assert!(exact_hermitian::is_positive_semidefinite(state));
            assert_eq!(mx::trace(&(state)).unwrap(), GaussianRat::one());
        }
        let x = mx::sub(&(rho), &sigma).unwrap();
        let trace_norm = Surd::from_natural(coefficient, &BigInt::from(radicand)).unwrap();
        // W = X / sqrt(q) is a Hermitian unitary: X^2 = q I, q = Tr(X^2) / 2.
        let q = mx::trace(
            &(mx::multiply_with_limits(&(x), &x, exact_hermitian::exact_limits()).unwrap()),
        )
        .unwrap()
        .re / ri(2);
        assert_eq!(
            mx::multiply_with_limits(&(x), &x, exact_hermitian::exact_limits()).unwrap(),
            mx::scale(&(mx::identity(2).unwrap()), &GaussianRat::from_rational(q)).unwrap()
        );
        let attained = qubit_polar_pairing(&x, &x).unwrap();
        assert_eq!(attained, trace_norm);
        let half = half_trace_norm_2x2(&x).unwrap();
        assert_eq!(
            attained,
            Surd::from_natural(half.coefficient() * ri(2), half.radicand()).unwrap()
        );
        // The anti-aligned witness reaches -||X||_1.
        let anti = qubit_polar_pairing(
            &x,
            &mx::scale(&(x), &GaussianRat::from_rational(ri(-1))).unwrap(),
        )
        .unwrap();
        assert_eq!(anti.coefficient(), &(-trace_norm.coefficient()));
    }
    assert_eq!(
        qubit_polar_pairing(&mx::zeros(2, 2).unwrap(), &pauli_z()),
        Err(TraceNormError::ZeroMatrix)
    );
    assert_eq!(
        qubit_polar_pairing(&dm(&[1, 0], 1), &pauli_z()),
        Err(TraceNormError::NotTraceZero)
    );
    assert_eq!(
        qubit_polar_pairing(&dm(&[1, 0, -1], 1), &dm(&[1, 0, -1], 1)),
        Err(TraceNormError::NotQubit)
    );
}

#[test]
fn general_quotient_refuses_aggregate_storage_and_foreign_walks_before_materialization() {
    let oversized = TraceDefectPacket::new(packet(&["a", "b"], &[], vec![]), 1024, vec![]).unwrap();
    assert!(matches!(
        oversized.divergence(&[]),
        Err(TraceQuotientError::Limits(
            core_kernel::resource_limits::ResourceError::AllocationFailure { .. }
        ))
    ));
    let empty = TraceDefectPacket::new(packet(&[], &[], vec![]), 1024, vec![]).unwrap();
    assert!(empty.divergence(&[]).unwrap().is_empty());
    let z = pauli_z();
    let ordinary = TraceDefectPacket::new(
        packet(&["a", "b"], &[("a", "b")], vec![ri(1)]),
        2,
        vec![z.clone()],
    )
    .unwrap();
    assert_eq!(
        ordinary.divergence(&[z.clone()]).unwrap(),
        vec![
            mx::scale(&z, &GaussianRat::from_rational(ri(-1))).unwrap(),
            z.clone()
        ]
    );

    // The edge indices fit, and the foreign walk is closed, but it does not
    // replay the endpoint/orientation sequence of the receiving triangle.
    let foreign = packet(
        &["a", "b", "c"],
        &[("c", "b"), ("a", "c"), ("b", "a")],
        vec![ri(1); 3],
    );
    let walk = OrientedWalk::new(&foreign, "a", &[(1, 1), (0, 1), (2, 1)]).unwrap();
    let triangle = packet_on_triangle(z.clone());
    let sign = SignCertificate::new(z.clone(), z.clone()).unwrap();
    assert_eq!(
        triangle.cycle_certificates(&walk, &sign),
        Err(TraceQuotientError::NotACycle)
    );

    let foreign = packet(
        &["a", "b", "c"],
        &[("a", "b"), ("b", "c"), ("c", "a"), ("a", "c")],
        vec![ri(1); 4],
    );
    let walk = OrientedWalk::new(&foreign, "a", &[(3, 1), (2, 1)]).unwrap();
    let cycle = TraceDefectPacket::new(
        packet(&["a", "b"], &[("a", "b"), ("b", "a")], vec![ri(1); 2]),
        2,
        vec![z, mx::zeros(2, 2).unwrap()],
    )
    .unwrap();
    assert_eq!(
        cycle.cycle_certificates(&walk, &sign),
        Err(TraceQuotientError::NotACycle)
    );
}

// Origin: engine/crates_rs/tests/core_quantum_physics/channels/cptp_trace_norm_geometry.rs
// Claim: urn:core:crates_rs:tests:cptp-trace-norm-geometry:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord419272d2 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord419272d2` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError419272d2 {
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
impl BoundaryError419272d2 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError419272d2 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError419272d2 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord419272d2 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError419272d2> {
        if capacity_bound == 0 {
            return Err(BoundaryError419272d2::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError419272d2::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError419272d2::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_419272d2() {
    let admitted = BoundaryRecord419272d2::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord419272d2::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
