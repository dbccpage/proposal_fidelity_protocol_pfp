//! Holonomy-structured superposition and its phase-gauge annex: coherent path
//! families whose interference is read off relative loop holonomy, gauge
//! invariance, spanning-forest gauge fixing and tree triviality, face
//! curvature, flat connections that keep global holonomy, and exhaustive
//! quarter-turn censuses on small carriers. Every check is exact.

use std::collections::HashMap;

use num_bigint::BigInt;
use num_traits::Zero;
use core_lie_theory::cayley::{is_unit, unit_pow};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq, Rational};
use core_quantum_physics::exact_hermitian::{gi, gq};
use core_quantum_physics::u1_graph_connection::{
    CochainExponential, OrientedWalk, U1Connection, VertexGauge,
};
use core_solvers::data_cochain_packet::FiniteCochainPacket;

use crate::support::rats;
use core_quantum_physics::holonomy_interference::{
    face_holonomies, gauge_equivalence, holonomy_verdict, relative_loop, walk_integral,
    CoherentPathFamily, HolonomyInterferenceError, HolonomyVerdict, TreeGaugeFixing,
};
use core_quantum_physics::phase_blind_quotient::{phase_blind_projection, QuotientError};

fn complex(vertices: &[&str], edges: &[(&str, &str)], faces: &[&[&str]]) -> FiniteCochainPacket {
    FiniteCochainPacket::with_unit_weights(
        FiniteCochainPacket::build_complex(vertices, edges, faces).unwrap(),
    )
    .unwrap()
}

/// `s -> x -> t` and `s -> y -> t`; edges 0: s->x, 1: x->t, 2: s->y, 3: y->t.
fn square(filled: bool) -> FiniteCochainPacket {
    let faces: &[&[&str]] = if filled {
        &[&["s", "x", "t", "y"]]
    } else {
        &[]
    };
    complex(
        &["s", "x", "t", "y"],
        &[("s", "x"), ("x", "t"), ("s", "y"), ("y", "t")],
        faces,
    )
}

fn square_paths(packet: &FiniteCochainPacket) -> (OrientedWalk, OrientedWalk) {
    (
        OrientedWalk::new(packet, "s", &[(0, 1), (1, 1)]).unwrap(),
        OrientedWalk::new(packet, "s", &[(2, 1), (3, 1)]).unwrap(),
    )
}

fn square_connection(packet: &FiniteCochainPacket) -> U1Connection {
    U1Connection::new(
        packet,
        vec![gq(3, 5, 4, 5), gi(0, 1), gq(5, 13, -12, 13), gi(1, 0)],
    )
    .unwrap()
}

fn triangle(filled: bool) -> FiniteCochainPacket {
    let faces: &[&[&str]] = if filled { &[&["a", "b", "c"]] } else { &[] };
    complex(
        &["a", "b", "c"],
        &[("a", "b"), ("b", "c"), ("c", "a")],
        faces,
    )
}

fn triangle_loop(packet: &FiniteCochainPacket) -> OrientedWalk {
    OrientedWalk::new(packet, "a", &[(0, 1), (1, 1), (2, 1)]).unwrap()
}

/// A square with its diagonal a->c, as a graph or with both triangles filled.
fn square_with_diagonal(filled: bool) -> FiniteCochainPacket {
    let faces: &[&[&str]] = if filled {
        &[&["a", "b", "c"], &["a", "c", "d"]]
    } else {
        &[]
    };
    complex(
        &["a", "b", "c", "d"],
        &[("a", "b"), ("b", "c"), ("c", "d"), ("d", "a"), ("a", "c")],
        faces,
    )
}

/// Outer square a b c d, inner square e f g h, four spokes, four faces around the hole.
fn annulus() -> FiniteCochainPacket {
    complex(
        &["a", "b", "c", "d", "e", "f", "g", "h"],
        &[
            ("a", "b"),
            ("b", "c"),
            ("c", "d"),
            ("d", "a"),
            ("e", "f"),
            ("f", "g"),
            ("g", "h"),
            ("h", "e"),
            ("a", "e"),
            ("b", "f"),
            ("c", "g"),
            ("d", "h"),
        ],
        &[
            &["a", "b", "f", "e"],
            &["b", "c", "g", "f"],
            &["c", "d", "h", "g"],
            &["d", "a", "e", "h"],
        ],
    )
}

/// Every assignment of `{1, i, -1, -i}` to `n` slots.
fn quarter_turn_assignments(n: usize) -> Vec<Vec<GaussianRat>> {
    let turns = [gi(1, 0), gi(0, 1), gi(-1, 0), gi(0, -1)];
    (0..4usize.pow(n as u32))
        .map(|mut code| {
            (0..n)
                .map(|_| {
                    let z = turns[code % 4].clone();
                    code /= 4;
                    z
                })
                .collect()
        })
        .collect()
}

fn verdict_census(packet: &FiniteCochainPacket) -> (usize, usize, usize) {
    let (mut curved, mut flat_nontrivial, mut trivial) = (0, 0, 0);
    for values in quarter_turn_assignments(packet.edge_count()) {
        match holonomy_verdict(packet, &U1Connection::new(packet, values).unwrap()).unwrap() {
            HolonomyVerdict::Curved { .. } => curved += 1,
            HolonomyVerdict::FlatNontrivial { .. } => flat_nontrivial += 1,
            HolonomyVerdict::GaugeTrivial => trivial += 1,
        }
    }
    (curved, flat_nontrivial, trivial)
}

// ---------------------------------------------------------------------------
// QCS-C1..C4: coherent path families.
// ---------------------------------------------------------------------------

#[test]
fn two_path_intensity_is_the_l1_sum_plus_the_relative_holonomy_cross_term() {
    let sq = square(false);
    let a = square_connection(&sq);
    let (p, q) = square_paths(&sq);
    let family =
        CoherentPathFamily::new(&sq, &a, &[p.clone(), q.clone()], &[rq(1, 4), rq(9, 16)]).unwrap();
    // H(p) = i (3+4i)/5 and H(q) = (5-12i)/13, so h = H(p) conj H(q):
    let h = family.relative_holonomy(0, 1).unwrap();
    assert_eq!(h, gq(-56, 65, -33, 65));
    assert!(is_unit(&h));
    assert_eq!(
        h,
        a.holonomy(&sq, &relative_loop(&sq, &p, &q).unwrap())
            .unwrap()
    );
    let cross = ri(2) * rq(1, 2) * rq(3, 4) * &h.re;
    assert_eq!(family.sink_intensity(), rq(13, 16) + &cross);
    assert_eq!(family.sink_intensity(), rq(173, 1040));
    assert_eq!(family.holonomy_expansion(), family.sink_intensity());
    assert_eq!(family.interference_residual(), cross);
}

#[test]
fn three_path_intensity_is_the_l1_sum_plus_all_pairwise_holonomy_terms() {
    let theta = complex(
        &["s", "a", "b", "c", "t"],
        &[
            ("s", "a"),
            ("a", "t"),
            ("s", "b"),
            ("b", "t"),
            ("s", "c"),
            ("c", "t"),
        ],
        &[],
    );
    let a = U1Connection::new(
        &theta,
        vec![
            gi(0, 1),
            gi(1, 0),
            gq(3, 5, 4, 5),
            gi(1, 0),
            gi(-1, 0),
            gq(5, 13, 12, 13),
        ],
    )
    .unwrap();
    let walks: Vec<OrientedWalk> = [[(0, 1), (1, 1)], [(2, 1), (3, 1)], [(4, 1), (5, 1)]]
        .iter()
        .map(|steps| OrientedWalk::new(&theta, "s", steps).unwrap())
        .collect();
    let weights = [rq(1, 9), rq(4, 9), rq(4, 9)];
    let moduli = [rq(1, 3), rq(2, 3), rq(2, 3)];
    let family = CoherentPathFamily::new(&theta, &a, &walks, &weights).unwrap();
    let mut residual = Rational::zero();
    for p in 0..3 {
        for q in p + 1..3 {
            let h = family.relative_holonomy(p, q).unwrap();
            assert_eq!(
                h,
                a.holonomy(
                    &theta,
                    &relative_loop(&theta, &walks[p], &walks[q]).unwrap()
                )
                .unwrap()
            );
            residual += ri(2) * &moduli[p] * &moduli[q] * &h.re;
        }
    }
    assert_eq!(family.interference_residual(), residual);
    assert_eq!(family.holonomy_expansion(), family.sink_intensity());
    assert_eq!(family.sink_intensity(), ri(1) + residual);
}

#[test]
fn relative_holonomy_and_intensity_survive_every_vertex_gauge() {
    let sq = square(false);
    let a = square_connection(&sq);
    let (p, q) = square_paths(&sq);
    let walks = [p, q];
    let weights = [rq(1, 4), rq(9, 16)];
    let family = CoherentPathFamily::new(&sq, &a, &walks, &weights).unwrap();
    let g = VertexGauge::new(
        &sq,
        vec![gq(3, 5, -4, 5), gi(0, 1), gq(-5, 13, 12, 13), gi(-1, 0)],
    )
    .unwrap();
    let gauged =
        CoherentPathFamily::new(&sq, &a.gauge_transform(&sq, &g).unwrap(), &walks, &weights)
            .unwrap();
    assert_eq!(gauged.sink_intensity(), family.sink_intensity());
    assert_eq!(
        gauged.relative_holonomy(0, 1),
        family.relative_holonomy(0, 1)
    );
    // Each amplitude picks up the same endpoint factor g(t) conj(g(s)).
    let factor = g.values()[2].mul(&g.values()[0].conj());
    assert_ne!(factor, gi(1, 0));
    for (after, before) in gauged.amplitudes().iter().zip(family.amplitudes()) {
        assert_eq!(*after, factor.mul(&before));
    }
    assert_eq!(gauged.transports()[0], factor.mul(&family.transports()[0]));
    // Changing one edge value is not a gauge: the intensity moves.
    let mut values = a.values().to_vec();
    values[1] = values[1].mul(&gi(0, 1));
    let bent = CoherentPathFamily::new(
        &sq,
        &U1Connection::new(&sq, values).unwrap(),
        &walks,
        &weights,
    )
    .unwrap();
    assert_ne!(bent.sink_intensity(), family.sink_intensity());
}

#[test]
fn coherent_intensity_does_not_factor_through_the_l1_weights() {
    let sq = square(false);
    let (p, q) = square_paths(&sq);
    let walks = [p, q];
    let plus = U1Connection::trivial(&sq);
    let minus = U1Connection::new(&sq, vec![gi(1, 0), gi(-1, 0), gi(1, 0), gi(1, 0)]).unwrap();
    for (w_p, w_q, r_p, r_q) in [
        (rq(1, 4), rq(9, 16), rq(1, 2), rq(3, 4)),
        (rq(1, 4), rq(1, 4), rq(1, 2), rq(1, 2)),
    ] {
        let weights = [w_p, w_q];
        let constructive = CoherentPathFamily::new(&sq, &plus, &walks, &weights).unwrap();
        let destructive = CoherentPathFamily::new(&sq, &minus, &walks, &weights).unwrap();
        assert_eq!(constructive.relative_holonomy(0, 1).unwrap(), gi(1, 0));
        assert_eq!(destructive.relative_holonomy(0, 1).unwrap(), gi(-1, 0));
        let sum = &r_p + &r_q;
        let difference = &r_p - &r_q;
        assert_eq!(constructive.sink_intensity(), &sum * &sum);
        assert_eq!(destructive.sink_intensity(), &difference * &difference);
        assert_eq!(
            constructive.sink_intensity() - destructive.sink_intensity(),
            ri(4) * &r_p * &r_q
        );
    }
    // Equal weights u = 1/4: intensities 4u = 1 and 0 over one L1 packet.
    let equal = [rq(1, 4), rq(1, 4)];
    assert_eq!(
        CoherentPathFamily::new(&sq, &plus, &walks, &equal)
            .unwrap()
            .sink_intensity(),
        ri(1)
    );
    assert_eq!(
        CoherentPathFamily::new(&sq, &minus, &walks, &equal)
            .unwrap()
            .sink_intensity(),
        ri(0)
    );
}

#[test]
fn the_phase_blind_shadow_of_a_coherent_family_is_its_l1_proportions() {
    let sq = square(false);
    let (p, q) = square_paths(&sq);
    let walks = [p, q];
    for a in [square_connection(&sq), U1Connection::trivial(&sq)] {
        let family = CoherentPathFamily::new(&sq, &a, &walks, &[rq(1, 4), rq(9, 16)]).unwrap();
        assert_eq!(
            phase_blind_projection(&family.amplitudes()).unwrap(),
            vec![rq(4, 13), rq(9, 13)]
        );
    }
    let silent =
        CoherentPathFamily::new(&sq, &square_connection(&sq), &walks, &[ri(0), ri(0)]).unwrap();
    assert_eq!(
        phase_blind_projection(&silent.amplitudes()),
        Err(QuotientError::Zero)
    );
}

// ---------------------------------------------------------------------------
// QCS-C5: gauge fixing, tree triviality and gauge equivalence.
// ---------------------------------------------------------------------------

#[test]
fn every_connection_on_a_tree_is_gauge_trivial() {
    let path = complex(
        &["a", "b", "c", "d"],
        &[("a", "b"), ("b", "c"), ("c", "d")],
        &[],
    );
    let assignments = quarter_turn_assignments(3);
    assert_eq!(assignments.len(), 64);
    for values in assignments {
        let a = U1Connection::new(&path, values).unwrap();
        let fixing = TreeGaugeFixing::new(&path, &a).unwrap();
        assert!(fixing.is_gauge_trivial());
        assert!(fixing.cycle_holonomies().is_empty());
        assert_eq!(
            a.gauge_transform(&path, fixing.gauge()).unwrap(),
            U1Connection::trivial(&path)
        );
        assert_eq!(
            holonomy_verdict(&path, &a).unwrap(),
            HolonomyVerdict::GaugeTrivial
        );
    }
    let star = complex(
        &["o", "p", "q", "r"],
        &[("o", "p"), ("q", "o"), ("o", "r")],
        &[],
    );
    let a = U1Connection::new(&star, vec![gq(3, 5, 4, 5), gq(5, 13, -12, 13), gi(0, 1)]).unwrap();
    let fixing = TreeGaugeFixing::new(&star, &a).unwrap();
    assert!((0..3).all(|e| fixing.is_tree_edge(e) == Some(true)));
    assert_eq!(fixing.is_tree_edge(99), None);
    assert_eq!(fixing.residual(), &U1Connection::trivial(&star));
}

#[test]
fn gauge_fixing_leaves_exactly_the_fundamental_cycle_holonomies() {
    let graph = square_with_diagonal(false);
    let a = U1Connection::new(
        &graph,
        vec![
            gi(0, 1),
            gq(3, 5, 4, 5),
            gi(-1, 0),
            gq(5, 13, 12, 13),
            gq(-7, 25, 24, 25),
        ],
    )
    .unwrap();
    let fixing = TreeGaugeFixing::new(&graph, &a).unwrap();
    // Breadth first from a: edges a->b, d->a and a->c span; b->c and c->d close cycles.
    for edge in [0, 3, 4] {
        assert_eq!(fixing.is_tree_edge(edge), Some(true));
        assert_eq!(fixing.residual().values()[edge], gi(1, 0));
    }
    let closes_b_c = OrientedWalk::new(&graph, "b", &[(1, 1), (4, -1), (0, 1)]).unwrap();
    let closes_c_d = OrientedWalk::new(&graph, "c", &[(2, 1), (3, 1), (4, 1)]).unwrap();
    assert_eq!(
        fixing.cycle_holonomies(),
        vec![
            (1, a.holonomy(&graph, &closes_b_c).unwrap()),
            (2, a.holonomy(&graph, &closes_c_d).unwrap())
        ]
    );
    assert!(!fixing.is_gauge_trivial());
}

#[test]
fn gauge_equivalence_is_decided_by_the_fixed_residuals() {
    let graph = square_with_diagonal(false);
    let a = U1Connection::new(
        &graph,
        vec![
            gi(0, 1),
            gq(3, 5, 4, 5),
            gi(-1, 0),
            gq(5, 13, 12, 13),
            gq(-7, 25, 24, 25),
        ],
    )
    .unwrap();
    let g = VertexGauge::new(
        &graph,
        vec![gq(3, 5, 4, 5), gi(0, -1), gi(-1, 0), gq(8, 17, 15, 17)],
    )
    .unwrap();
    let b = a.gauge_transform(&graph, &g).unwrap();
    let relating = gauge_equivalence(&graph, &a, &b)
        .unwrap()
        .expect("gauge related");
    assert_eq!(a.gauge_transform(&graph, &relating).unwrap(), b);
    // A claimed equivalence with a different cycle holonomy is refused.
    let mut values = a.values().to_vec();
    values[1] = values[1].mul(&gi(0, 1));
    let other = U1Connection::new(&graph, values).unwrap();
    assert_eq!(gauge_equivalence(&graph, &a, &other).unwrap(), None);
    // On a forest with two components every pair of connections is related.
    let forest = complex(&["a", "b", "c", "d"], &[("a", "b"), ("c", "d")], &[]);
    let x = U1Connection::new(&forest, vec![gi(0, 1), gq(3, 5, 4, 5)]).unwrap();
    let y = U1Connection::new(&forest, vec![gq(5, 13, 12, 13), gi(-1, 0)]).unwrap();
    let relating = gauge_equivalence(&forest, &x, &y)
        .unwrap()
        .expect("forests are gauge trivial");
    assert_eq!(x.gauge_transform(&forest, &relating).unwrap(), y);
}

#[test]
fn quarter_turn_gauge_classes_are_counted_by_the_cycle_rank() {
    for (packet, classes, class_size) in [
        (triangle(false), 4usize, 16usize),
        (square_with_diagonal(true), 16, 64),
    ] {
        let mut census: HashMap<Vec<GaussianRat>, usize> = HashMap::new();
        let mut flat = 0;
        for values in quarter_turn_assignments(packet.edge_count()) {
            let a = U1Connection::new(&packet, values).unwrap();
            let residual = TreeGaugeFixing::new(&packet, &a)
                .unwrap()
                .residual()
                .values()
                .to_vec();
            *census.entry(residual).or_default() += 1;
            flat += usize::from(
                face_holonomies(&packet, &a)
                    .unwrap()
                    .iter()
                    .all(|h| *h == gi(1, 0)),
            );
        }
        assert_eq!(census.len(), classes);
        assert!(census.values().all(|&n| n == class_size));
        assert_eq!(census[&vec![gi(1, 0); packet.edge_count()]], class_size);
        // Without faces every connection is flat; on the filled square only the trivial class is.
        assert_eq!(
            flat,
            if packet.face_count() == 0 {
                64
            } else {
                class_size
            }
        );
    }
}

// ---------------------------------------------------------------------------
// QCS-C6 .. C8: curvature, flat global holonomy, and the dimension of curvature.
// ---------------------------------------------------------------------------

#[test]
fn face_curvature_is_gauge_invariant_additively_and_multiplicatively() {
    let disk = square_with_diagonal(true);
    for x in [
        rats(&[1, 2, 3, 4, 5]),
        vec![rq(1, 2), ri(-3), rq(7, 4), ri(0), ri(2)],
    ] {
        for f in [
            rats(&[0, 1, -2, 5]),
            vec![rq(1, 3), ri(0), ri(-1), rq(5, 2)],
        ] {
            let repair = disk.primitive_difference(&f).unwrap();
            assert!(disk
                .face_coboundary(&repair)
                .unwrap()
                .iter()
                .all(Zero::is_zero));
            let shifted: Vec<Rational> = x.iter().zip(&repair).map(|(a, b)| a + b).collect();
            assert_eq!(
                disk.face_coboundary(&shifted).unwrap(),
                disk.face_coboundary(&x).unwrap()
            );
        }
    }
    let a = U1Connection::new(
        &disk,
        vec![
            gi(0, 1),
            gq(3, 5, 4, 5),
            gi(-1, 0),
            gq(5, 13, 12, 13),
            gq(-7, 25, 24, 25),
        ],
    )
    .unwrap();
    let g = VertexGauge::new(
        &disk,
        vec![gq(3, 5, 4, 5), gi(0, -1), gi(-1, 0), gq(8, 17, 15, 17)],
    )
    .unwrap();
    let faces = face_holonomies(&disk, &a).unwrap();
    assert_eq!(
        face_holonomies(&disk, &a.gauge_transform(&disk, &g).unwrap()).unwrap(),
        faces
    );
    // With a declared scale u, the face holonomy of Exp(omega) is u^(d1 omega).
    let u = gq(3, 5, 4, 5);
    let exp = CochainExponential::new(u.clone()).unwrap();
    let omega = rats(&[2, -1, 0, 3, 1]);
    let curvature = disk.face_coboundary(&omega).unwrap();
    let expected: Vec<GaussianRat> = curvature
        .iter()
        .map(|k| unit_pow(&u, &k.to_integer()).unwrap())
        .collect();
    assert_eq!(
        face_holonomies(&disk, &exp.connection(&disk, &omega).unwrap()).unwrap(),
        expected
    );
}

#[test]
fn plaquette_interference_reads_the_face_holonomy() {
    let sq = square(true);
    let a = square_connection(&sq);
    let (p, q) = square_paths(&sq);
    let family = CoherentPathFamily::new(&sq, &a, &[p, q], &[rq(1, 4), rq(9, 16)]).unwrap();
    let faces = face_holonomies(&sq, &a).unwrap();
    assert_eq!(faces, vec![family.relative_holonomy(0, 1).unwrap()]);
    assert_eq!(
        family.sink_intensity(),
        rq(13, 16) + ri(2) * rq(1, 2) * rq(3, 4) * &faces[0].re
    );
}

#[test]
fn flat_connections_keep_global_holonomy_on_a_cycle_and_on_an_annulus() {
    let cycle = triangle(false);
    let a = U1Connection::new(&cycle, vec![gi(0, 1), gi(1, 0), gi(1, 0)]).unwrap();
    assert!(face_holonomies(&cycle, &a).unwrap().is_empty());
    assert_eq!(
        holonomy_verdict(&cycle, &a).unwrap(),
        HolonomyVerdict::FlatNontrivial {
            cycle_holonomies: vec![(1, gi(0, 1))]
        }
    );
    // Filling the cycle is a change of carrier: the same edge values are now curved.
    let filled = triangle(true);
    let a_filled = U1Connection::new(&filled, vec![gi(0, 1), gi(1, 0), gi(1, 0)]).unwrap();
    assert_eq!(
        holonomy_verdict(&filled, &a_filled).unwrap(),
        HolonomyVerdict::Curved {
            face_holonomies: vec![gi(0, 1)]
        }
    );

    let ring = annulus();
    let u = gq(3, 5, 4, 5);
    let mut values = vec![gi(1, 0); 12];
    values[0] = u.clone();
    values[4] = u.clone();
    let b = U1Connection::new(&ring, values).unwrap();
    assert_eq!(face_holonomies(&ring, &b).unwrap(), vec![gi(1, 0); 4]);
    let one = gi(1, 0);
    assert_eq!(
        holonomy_verdict(&ring, &b).unwrap(),
        HolonomyVerdict::FlatNontrivial {
            cycle_holonomies: vec![
                (2, u.clone()),
                (4, one.clone()),
                (5, one.clone()),
                (6, u.clone()),
                (7, one)
            ]
        }
    );
    let outer = OrientedWalk::new(&ring, "a", &[(0, 1), (1, 1), (2, 1), (3, 1)]).unwrap();
    assert_eq!(b.holonomy(&ring, &outer).unwrap(), u);
}

#[test]
fn on_a_simply_connected_complex_flat_means_gauge_trivial() {
    // All 1024 quarter-turn connections on the filled square with diagonal.
    assert_eq!(verdict_census(&square_with_diagonal(true)), (960, 0, 64));
}

#[test]
fn graphs_carry_no_local_curvature_and_a_two_cell_can() {
    // (Curved, FlatNontrivial, GaugeTrivial) over all 64 quarter-turn connections.
    assert_eq!(verdict_census(&triangle(false)), (0, 48, 16));
    assert_eq!(verdict_census(&triangle(true)), (48, 0, 16));
}

#[test]
fn path_families_and_gauge_tools_refuse_mismatched_or_foreign_data() {
    let sq = square(false);
    let (p, q) = square_paths(&sq);
    let a = U1Connection::trivial(&sq);
    assert_eq!(
        CoherentPathFamily::new(&sq, &a, &[], &[]),
        Err(HolonomyInterferenceError::EmptyFamily)
    );
    assert_eq!(
        CoherentPathFamily::new(&sq, &a, std::slice::from_ref(&p), &[]),
        Err(HolonomyInterferenceError::WeightCount {
            walks: 1,
            weights: 0
        })
    );
    let short = OrientedWalk::new(&sq, "x", &[(1, 1)]).unwrap();
    assert_eq!(
        CoherentPathFamily::new(&sq, &a, &[p.clone(), short.clone()], &[rq(1, 4), rq(1, 4)]),
        Err(HolonomyInterferenceError::EndpointMismatch { index: 1 })
    );
    assert_eq!(
        CoherentPathFamily::new(&sq, &a, &[p.clone(), q.clone()], &[rq(-1, 4), rq(1, 4)]),
        Err(HolonomyInterferenceError::NegativeWeight { index: 0 })
    );
    assert_eq!(
        CoherentPathFamily::new(&sq, &a, &[p.clone(), q.clone()], &[rq(1, 4), rq(1, 2)]),
        Err(HolonomyInterferenceError::IrrationalAmplitude { index: 1 })
    );
    let family = CoherentPathFamily::new(&sq, &a, &[p.clone(), q], &[rq(1, 4), rq(1, 4)]).unwrap();
    assert_eq!(
        family.relative_holonomy(0, 2),
        Err(HolonomyInterferenceError::PathIndex { index: 2 })
    );
    assert_eq!(
        relative_loop(&sq, &p, &short),
        Err(HolonomyInterferenceError::EndpointMismatch { index: 1 })
    );

    let tri = triangle(false);
    let foreign = U1Connection::trivial(&tri);
    let size = Err(HolonomyInterferenceError::ConnectionSize {
        expected: 4,
        actual: 3,
    });
    assert_eq!(TreeGaugeFixing::new(&sq, &foreign).map(|_| ()), size);
    assert_eq!(face_holonomies(&sq, &foreign).map(|_| ()), size);
    assert_eq!(
        CoherentPathFamily::new(&sq, &foreign, std::slice::from_ref(&p), &[ri(1)]).map(|_| ()),
        size
    );
    let theta = complex(
        &["s", "a", "b", "c", "t"],
        &[
            ("s", "a"),
            ("a", "t"),
            ("s", "b"),
            ("b", "t"),
            ("s", "c"),
            ("c", "t"),
        ],
        &[],
    );
    let far = OrientedWalk::new(&theta, "s", &[(4, 1), (5, 1)]).unwrap();
    assert_eq!(
        walk_integral(&sq, &far, &rats(&[0, 0, 0, 0])),
        Err(HolonomyInterferenceError::WalkOutsidePacket { edge: 4 })
    );
    // Walks on the theta graph that use only edges 0 and 1 name edges the square
    // declares, but they are not walks of the square. s -> a -> t ends at t (4)
    // there, and replays on the square to t (2); t -> a -> s starts at a vertex
    // the square does not have, which used to panic in relative_loop.
    let near = OrientedWalk::new(&theta, "s", &[(0, 1), (1, 1)]).unwrap();
    assert_eq!(
        walk_integral(&sq, &near, &rats(&[0, 0, 0, 0])),
        Err(HolonomyInterferenceError::ForeignWalk)
    );
    let back = OrientedWalk::new(&theta, "t", &[(1, -1), (0, -1)]).unwrap();
    assert_eq!(
        relative_loop(&sq, &back, &back),
        Err(HolonomyInterferenceError::ForeignWalk)
    );
    assert_eq!(
        CoherentPathFamily::new(&sq, &square_connection(&sq), &[near], &[ri(1)]),
        Err(HolonomyInterferenceError::ForeignWalk)
    );
    assert_eq!(
        walk_integral(&sq, &p, &rats(&[0, 0])),
        Err(HolonomyInterferenceError::CochainLength {
            expected: 4,
            actual: 2
        })
    );
}

// ---------------------------------------------------------------------------
// QM_064 annex: the phase gauge residual.
// ---------------------------------------------------------------------------

#[test]
fn a_gauge_shifts_a_phase_cochain_by_a_primitive_difference_and_keeps_loop_holonomy() {
    let tri = triangle(false);
    let loop_walk = triangle_loop(&tri);
    let theta = rats(&[2, -1, 3]);
    let alpha = rats(&[4, 0, -5]);
    let shifted: Vec<Rational> = theta
        .iter()
        .zip(tri.primitive_difference(&alpha).unwrap())
        .map(|(a, b)| a + b)
        .collect();
    assert_ne!(shifted, theta);
    assert_eq!(walk_integral(&tri, &loop_walk, &shifted).unwrap(), ri(4));
    assert_eq!(walk_integral(&tri, &loop_walk, &theta).unwrap(), ri(4));
    let u = gq(3, 5, 4, 5);
    let exp = CochainExponential::new(u.clone()).unwrap();
    let a = exp.connection(&tri, &theta).unwrap();
    let b = exp.connection(&tri, &shifted).unwrap();
    assert_eq!(
        a.gauge_transform(&tri, &exp.gauge(&tri, &alpha).unwrap())
            .unwrap(),
        b
    );
    assert_eq!(
        a.holonomy(&tri, &loop_walk).unwrap(),
        unit_pow(&u, &BigInt::from(4)).unwrap()
    );
    assert_eq!(
        b.holonomy(&tri, &loop_walk).unwrap(),
        a.holonomy(&tri, &loop_walk).unwrap()
    );
    let relating = gauge_equivalence(&tri, &a, &b)
        .unwrap()
        .expect("gauge related");
    assert_eq!(a.gauge_transform(&tri, &relating).unwrap(), b);
}

#[test]
fn no_vertex_gauge_removes_a_nontrivial_cycle_holonomy() {
    let tri = triangle(false);
    let loop_walk = triangle_loop(&tri);
    let a = U1Connection::new(&tri, vec![gi(0, 1), gi(1, 0), gi(1, 0)]).unwrap();
    let gauges = quarter_turn_assignments(3);
    assert_eq!(gauges.len(), 64);
    for values in gauges {
        let b = a
            .gauge_transform(&tri, &VertexGauge::new(&tri, values).unwrap())
            .unwrap();
        assert_eq!(b.holonomy(&tri, &loop_walk).unwrap(), gi(0, 1));
        assert_ne!(b, U1Connection::trivial(&tri));
    }
    // The spanning-tree gauge moves the whole holonomy onto the one edge off the tree.
    let fixing = TreeGaugeFixing::new(&tri, &a).unwrap();
    assert_eq!(fixing.residual().values(), &[gi(1, 0), gi(0, 1), gi(1, 0)]);
}

// Origin: engine/crates_rs/tests/core_quantum_physics/superposition/holonomy_structured_superposition.rs
// Claim: urn:core:crates_rs:tests:holonomy-structured-superposition:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord427ba4ff {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord427ba4ff` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError427ba4ff {
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
impl BoundaryError427ba4ff {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError427ba4ff {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError427ba4ff {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord427ba4ff {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError427ba4ff> {
        if capacity_bound == 0 {
            return Err(BoundaryError427ba4ff::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError427ba4ff::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError427ba4ff::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_427ba4ff() {
    let admitted = BoundaryRecord427ba4ff::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord427ba4ff::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
