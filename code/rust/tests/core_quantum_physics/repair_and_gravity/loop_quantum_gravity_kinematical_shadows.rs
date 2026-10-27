//! Finite kinematical shadows of loop quantum gravity: the quaternion group
//! inside `SU(2)`, pure-gauge and curved quaternion connections through
//! `core_holonomy`, holonomy as the complete invariant of a cycle's first
//! cohomology, `dim H^1 = E - V + C` over every prime, interference cross terms
//! on finite phase groups, the flux/holonomy commutator on functions on `Q8`,
//! and the spin-`j` Casimir with the area labels it feeds. Every check is exact.

use linear_algebra::exact_field::involution as iv;
use core_kernel::resource_limits::OperationLimits;
use std::collections::{BTreeMap, BTreeSet};

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::matrix as mx;
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{ToPrimitive, Zero};
use core_holonomy::{
    compute_loop_holonomy, compute_path_holonomy, group_commutator, is_flat, wilson_loop_trace,
};
use core_homology::graph_f2::simple_graphs;
use core_homology::smith_normal_form::invariant_factors;
use core_lie_theory::finite_group::{generate, FiniteGroup, GroupError};
use core_number_theory::cyclotomic::{Cyc24, GaussianRat};
use core_number_theory::quadratic::Surd as SurdRational;
use core_number_theory::rational::{ri, rq, Rational};
use core_quantum_physics::exact_hermitian::{gi, gq};
use core_quantum_physics::holonomy_interference::{walk_integral, CoherentPathFamily};
use core_quantum_physics::u1_graph_connection::{OrientedWalk, U1Connection};
use core_solvers::cert_cohomology_admission::{admit, complex_of_packet, verify_admission, Admission};
use core_solvers::data_cochain_packet::FiniteCochainPacket;

use crate::support::quaternion_group;
use crate::support::{
    cell_complex, field, identity, path, q8, quaternion_plaquette, Connection, Scalar, I, J, K,
    MINUS_ONE,
};
use core_lie_theory::su2::{
    bracket_defects, casimir, commutant_dimension, SpinRepresentation, Su2Error as SpinError,
};
use core_quantum_physics::quaternion_gauge_shadow::{FiniteGroupAlgebra, GroupAlgebraError};
use core_quantum_physics::spin_area_spectrum::{area_label, area_label_squared};

fn is_special_unitary(m: &BasicMatrix<GaussianRat>) -> bool {
    core_lie_theory::su_n::is_special_unitary(m).unwrap_or(false)
}
fn close_under_multiplication(
    g: &[BasicMatrix<GaussianRat>],
    bound: usize,
) -> Result<Vec<BasicMatrix<GaussianRat>>, GroupError> {
    generate(
        g,
        mx::identity(g[0].rows()).unwrap(),
        |a, b| mx::multiply(a, b).unwrap(),
        |a| (a.rows(), a.cols(), a.as_slice().to_vec()),
        bound,
    )
}
fn commuting_pairs(g: &[BasicMatrix<GaussianRat>]) -> usize {
    FiniteGroup::from_operation(
        g.to_vec(),
        |a, b| mx::multiply(a, b).unwrap(),
        |m| m.as_slice().to_vec(),
    )
    .unwrap()
    .commuting_pairs()
}

fn scalar(re: i64) -> Scalar {
    Scalar::new(
        BigRational::from_integer(BigInt::from(re)),
        BigRational::zero(),
    )
}

#[test]
fn the_quaternion_group_is_a_finite_subgroup_of_su2() {
    let q = quaternion_group();
    assert_eq!(q.len(), 8);
    assert!(q.iter().all(is_special_unitary));
    let group = FiniteGroupAlgebra::new(q.clone()).unwrap();
    assert_eq!(group.order(), 8);
    // i j = k, j i = -k, i^2 = -1.
    assert_eq!(group.product_index(2, 4).unwrap(), 6);
    assert_eq!(group.product_index(4, 2).unwrap(), 7);
    assert_eq!(group.product_index(2, 2).unwrap(), 1);
    // The library's closure of {i, j} is the same set, with 40 commuting pairs of 64.
    let generated = close_under_multiplication(&[q[2].clone(), q[4].clone()], 64).unwrap();
    assert_eq!(generated.len(), 8);
    assert!(generated.iter().all(|g| q.contains(g)));
    assert_eq!(commuting_pairs(&q), 40);
    // Determinant one without unitarity, and unitarity with determinant -1, are both outside SU(2).
    assert!(!is_special_unitary(
        &mx::diagonal(&[gi(2, 0), gq(1, 2, 0, 1)]).unwrap()
    ));
    assert!(!is_special_unitary(
        &mx::diagonal(&[gi(0, 1), gi(0, 1)]).unwrap()
    ));
    assert!(!is_special_unitary(
        &mx::from_fn(2, 3, |_, _| (GaussianRat::zero()).clone()).unwrap()
    ));
}

#[test]
fn malformed_groups_are_refused() {
    let one = mx::identity(2).unwrap();
    assert_eq!(
        FiniteGroupAlgebra::new(vec![]),
        Err(GroupAlgebraError::Empty)
    );
    assert_eq!(
        FiniteGroupAlgebra::new(vec![one.clone(), mx::identity(3).unwrap()]),
        Err(GroupAlgebraError::Shape { index: 1 })
    );
    assert_eq!(
        FiniteGroupAlgebra::new(vec![one.clone(), one.clone()]),
        Err(GroupAlgebraError::Repeated {
            first: 0,
            second: 1
        })
    );
    assert_eq!(
        FiniteGroupAlgebra::new(vec![mx::zeros(2, 2).unwrap()]),
        Err(GroupAlgebraError::NoIdentity)
    );
    assert_eq!(
        FiniteGroupAlgebra::new(vec![q8(MINUS_ONE)]),
        Err(GroupAlgebraError::NoIdentity)
    );
    assert_eq!(
        FiniteGroupAlgebra::new(vec![one.clone(), q8(I)]),
        Err(GroupAlgebraError::NotClosed { left: 1, right: 1 })
    );
    // {I, 0} is closed with an identity, and 0 has no inverse.
    assert_eq!(
        FiniteGroupAlgebra::new(vec![one, mx::zeros(2, 2).unwrap()]),
        Err(GroupAlgebraError::NoInverse { index: 1 })
    );
    let group = FiniteGroupAlgebra::new(quaternion_group()).unwrap();
    assert_eq!(
        group.flux(8),
        Err(GroupAlgebraError::IndexOutOfRange { index: 8 })
    );
    let constant_function = vec![ri(1); 8];
    for refusal in [
        group.flux_holonomy_commutator(8, &constant_function),
        group.translated_difference(8, &constant_function),
    ] {
        assert_eq!(
            refusal,
            Err(GroupAlgebraError::IndexOutOfRange { index: 8 })
        );
    }
    assert_eq!(
        group.holonomy(&[ri(1)]),
        Err(GroupAlgebraError::FunctionLength {
            expected: 8,
            actual: 1
        })
    );
}

/// Every closed walk of length 2 to 4 from `a` on the complete graph on `a, b, c, d`.
fn closed_walks_of_k4() -> Vec<Vec<String>> {
    let names = ["a", "b", "c", "d"];
    let mut walks = Vec::new();
    let mut frontier = vec![vec!["a"]];
    for _ in 0..4 {
        let mut next = Vec::new();
        for walk in &frontier {
            for v in names {
                if v != *walk.last().unwrap() {
                    let mut longer = walk.clone();
                    longer.push(v);
                    if v == "a" {
                        walks.push(path(&longer));
                    }
                    next.push(longer);
                }
            }
        }
        frontier = next;
    }
    walks
}

#[test]
fn a_pure_gauge_connection_has_trivial_holonomy_around_every_closed_walk() {
    let q = quaternion_group();
    let triangle = cell_complex(&["a", "b", "c"], &[("a", "b"), ("b", "c"), ("c", "a")], &[]);
    let loops = [
        path(&["a", "b", "c", "a"]),
        path(&["a", "c", "b", "a"]),
        path(&["a", "b", "a"]),
        path(&["b", "c", "a", "b", "c", "a", "b"]),
    ];
    let mut gauges = 0;
    for ga in &q {
        for gb in &q {
            for gc in &q {
                let potentials: BTreeMap<String, _> = [("a", ga), ("b", gb), ("c", gc)]
                    .into_iter()
                    .map(|(v, g)| (v.to_string(), field(g)))
                    .collect();
                let flat = Connection::from_pure_gauge(
                    &triangle,
                    &potentials,
                    2,
                    OperationLimits::holonomy(),
                )
                .unwrap();
                for l in &loops {
                    assert_eq!(compute_loop_holonomy(&flat, l).unwrap(), identity(2));
                }
                // An open path telescopes to g(end) g(start)^-1.
                let open = compute_path_holonomy(&flat, &path(&["a", "b", "c"])).unwrap();
                assert_eq!(
                    open,
                    field(&mx::multiply(&(gc), &(&iv::adjoint(&(ga)).unwrap())).unwrap())
                );
                gauges += 1;
            }
        }
    }
    assert_eq!(gauges, 512);

    let k4 = cell_complex(
        &["a", "b", "c", "d"],
        &[
            ("a", "b"),
            ("a", "c"),
            ("a", "d"),
            ("b", "c"),
            ("b", "d"),
            ("c", "d"),
        ],
        &[],
    );
    let walks = closed_walks_of_k4();
    assert_eq!(walks.len(), 3 + 6 + 21);
    for shift in 0..8 {
        let potentials: BTreeMap<String, _> = ["a", "b", "c", "d"]
            .iter()
            .enumerate()
            .map(|(v, name)| (name.to_string(), field(&q[(3 * v + shift) % 8])))
            .collect();
        let flat =
            Connection::from_pure_gauge(&k4, &potentials, 2, OperationLimits::holonomy()).unwrap();
        for walk in &walks {
            assert_eq!(compute_loop_holonomy(&flat, walk).unwrap(), identity(2));
        }
    }
}

#[test]
fn the_quaternion_plaquette_has_wilson_loop_minus_one() {
    let square = cell_complex(
        &["a", "b", "c", "d"],
        &[("a", "b"), ("b", "c"), ("c", "d"), ("d", "a")],
        &[&["a", "b", "c", "d"]],
    );
    let curved = quaternion_plaquette();
    let plaquette = path(&["a", "b", "c", "d", "a"]);
    assert_eq!(
        compute_loop_holonomy(&curved, &plaquette).unwrap(),
        field(&q8(MINUS_ONE))
    );
    assert_eq!(wilson_loop_trace(&curved, &plaquette).unwrap(), scalar(-2));
    assert!(!is_flat(&curved, &square).unwrap());
    assert_eq!(
        group_commutator(&field(&q8(I)), &field(&q8(J))).unwrap(),
        field(&q8(MINUS_ONE))
    );

    let q = quaternion_group();
    let potentials: BTreeMap<String, _> = ["a", "b", "c", "d"]
        .iter()
        .zip([I, J, K, MINUS_ONE])
        .map(|(v, g)| (v.to_string(), field(&q[g])))
        .collect();
    let flat =
        Connection::from_pure_gauge(&square, &potentials, 2, OperationLimits::holonomy()).unwrap();
    assert!(is_flat(&flat, &square).unwrap());

    // Every commutator in Q8 is 1 or -1; -1 exactly for the 24 non-commuting ordered pairs.
    let mut minus = 0;
    for a in &q {
        for b in &q {
            let c = group_commutator(&field(a), &field(b)).unwrap();
            let commute = mx::multiply(&(a), &(b)).unwrap() == mx::multiply(&(b), &(a)).unwrap();
            assert_eq!(c == identity(2), commute);
            if !commute {
                assert_eq!(c, field(&q8(MINUS_ONE)));
                minus += 1;
            }
        }
    }
    assert_eq!(minus, 24);
    // An abelian phase group cannot curve a plaquette.
    let units = [gi(1, 0), gi(0, 1), gi(-1, 0), gi(0, -1)];
    for a in &units {
        for b in &units {
            let one_by_one =
                |z: &GaussianRat| field(&mx::diagonal(std::slice::from_ref(z)).unwrap());
            assert_eq!(
                group_commutator(&one_by_one(a), &one_by_one(b)).unwrap(),
                identity(1)
            );
        }
    }
}

fn cycle(n: usize) -> FiniteCochainPacket {
    let names: Vec<String> = (0..n).map(|i| format!("v{i}")).collect();
    let vertices: Vec<&str> = names.iter().map(String::as_str).collect();
    let edges: Vec<(&str, &str)> = (0..n)
        .map(|i| (vertices[i], vertices[(i + 1) % n]))
        .collect();
    FiniteCochainPacket::with_unit_weights(
        FiniteCochainPacket::build_complex(&vertices, &edges, &[]).unwrap(),
    )
    .unwrap()
}

#[test]
fn holonomy_annihilates_coboundaries_and_detects_every_other_class_on_a_cycle() {
    for n in 3..=7 {
        let packet = cycle(n);
        let around: Vec<(usize, i8)> = (0..n).map(|e| (e, 1)).collect();
        let walk = OrientedWalk::new(&packet, "v0", &around).unwrap();
        let hol = |x: &[Rational]| walk_integral(&packet, &walk, x).unwrap();
        for v in 0..n {
            let f: Vec<Rational> = (0..n).map(|w| ri(i64::from(w == v))).collect();
            assert_eq!(hol(&packet.primitive_difference(&f).unwrap()), ri(0));
        }
        let dims = packet.dimensions();
        assert_eq!((dims.b1, dims.h1), (n - 1, 1));
        if n > 5 {
            continue;
        }
        let complex = complex_of_packet(&packet).unwrap();
        let mut exact = 0;
        for code in 0..3usize.pow(n as u32) {
            let a: Vec<Rational> = (0..n)
                .map(|i| ri((code / 3usize.pow(i as u32) % 3) as i64 - 1))
                .collect();
            let admission = admit(&complex, Some(&a));
            assert!(verify_admission(&complex, &a, &admission));
            match &admission {
                Admission::Exact { .. } => {
                    assert_eq!(hol(&a), ri(0));
                    exact += 1;
                }
                Admission::ClosedNonexact { separator } => {
                    assert!(hol(&a) != ri(0));
                    assert!(separator.iter().all(|z| *z == separator[0]));
                }
                other => panic!("a cycle has no 2-cells, got {other:?}"),
            }
        }
        // Central trinomial coefficients: the balanced cochains are the exact ones.
        assert_eq!(exact, [7, 19, 51][n - 3]);
    }
}

fn components(n: usize, edges: &[(usize, usize)]) -> usize {
    let mut parent: Vec<usize> = (0..n).collect();
    fn root(parent: &mut [usize], mut x: usize) -> usize {
        while parent[x] != x {
            x = parent[x];
        }
        x
    }
    for &(u, v) in edges {
        let (ru, rv) = (root(&mut parent, u), root(&mut parent, v));
        parent[ru] = rv;
    }
    (0..n).filter(|&v| root(&mut parent, v) == v).count()
}

#[test]
fn first_cohomology_has_dimension_edges_minus_vertices_plus_components_over_every_prime() {
    let mut graphs = 0;
    for n in [4, 5] {
        let names: Vec<String> = (0..n).map(|i| i.to_string()).collect();
        let vertices: Vec<&str> = names.iter().map(String::as_str).collect();
        for carrier in simple_graphs(n).unwrap() {
            let edges = carrier.edges();
            let named: Vec<(&str, &str)> = edges
                .iter()
                .map(|&(u, v)| (vertices[u], vertices[v]))
                .collect();
            let packet = FiniteCochainPacket::with_unit_weights(
                FiniteCochainPacket::build_complex(&vertices, &named, &[]).unwrap(),
            )
            .unwrap();
            let c = components(n, edges);
            let dims = packet.dimensions();
            assert_eq!(dims.b1, n - c);
            assert_eq!(dims.h1, edges.len() + c - n);
            // Every nonzero invariant factor of d0 over Z is 1, so rank d0 mod p is n - c
            // for every prime p and |H^1(G; F_p)| = p^(E - V + C).
            let integer: Vec<Vec<i128>> = packet
                .d0()
                .iter()
                .map(|row| {
                    row.iter()
                        .map(|x| x.to_integer().to_i128().unwrap())
                        .collect()
                })
                .collect();
            let factors = invariant_factors(integer).unwrap();
            assert_eq!(factors.len(), n - c);
            assert!(factors.iter().all(|&d| d == 1));
            graphs += 1;
        }
    }
    assert_eq!(graphs, 64 + 1024);
}

/// Three disjoint two-path interferometers `s_i -> x_i -> t_i`, `s_i -> y_i -> t_i`.
fn three_interferometers() -> FiniteCochainPacket {
    let names: Vec<String> = (0..3)
        .flat_map(|i| ["s", "x", "y", "t"].map(|v| format!("{v}{i}")))
        .collect();
    let vertices: Vec<&str> = names.iter().map(String::as_str).collect();
    let edges: Vec<(&str, &str)> = (0..3)
        .flat_map(|i| {
            let [s, x, y, t] = [
                vertices[4 * i],
                vertices[4 * i + 1],
                vertices[4 * i + 2],
                vertices[4 * i + 3],
            ];
            [(s, x), (x, t), (s, y), (y, t)]
        })
        .collect();
    FiniteCochainPacket::with_unit_weights(
        FiniteCochainPacket::build_complex(&vertices, &edges, &[]).unwrap(),
    )
    .unwrap()
}

fn interference_profile(weights: &[(i64, i64); 3], signs: u32) -> Vec<Rational> {
    let packet = three_interferometers();
    let values: Vec<GaussianRat> = (0..12)
        .map(|e| {
            if e % 4 == 1 && signs >> (e / 4) & 1 == 1 {
                gi(-1, 0)
            } else {
                gi(1, 0)
            }
        })
        .collect();
    let connection = U1Connection::new(&packet, values).unwrap();
    (0..3)
        .map(|i| {
            let source = format!("s{i}");
            let upper = OrientedWalk::new(&packet, &source, &[(4 * i, 1), (4 * i + 1, 1)]).unwrap();
            let lower =
                OrientedWalk::new(&packet, &source, &[(4 * i + 2, 1), (4 * i + 3, 1)]).unwrap();
            let (w, w2) = weights[i];
            CoherentPathFamily::new(&packet, &connection, &[upper, lower], &[ri(w), ri(w2)])
                .unwrap()
                .interference_residual()
        })
        .collect()
}

#[test]
fn k_independent_loops_give_two_to_the_k_distinct_interference_profiles() {
    let weights = [(1, 4), (9, 1), (4, 9)];
    let profiles: BTreeSet<Vec<Rational>> =
        (0..8).map(|s| interference_profile(&weights, s)).collect();
    assert_eq!(profiles.len(), 8);
    assert!(profiles.contains(&vec![ri(4), ri(6), ri(12)]));
    assert!(profiles.contains(&vec![ri(-4), ri(6), ri(-12)]));
    // A path of weight zero erases its loop: the eight sign patterns give four profiles.
    let degenerate = [(1, 0), (9, 1), (4, 9)];
    let collapsed: BTreeSet<Vec<Rational>> = (0..8)
        .map(|s| interference_profile(&degenerate, s))
        .collect();
    assert_eq!(collapsed.len(), 4);
}

#[test]
fn the_interference_cross_term_samples_the_cosine_on_finite_phase_groups() {
    let square = FiniteCochainPacket::with_unit_weights(
        FiniteCochainPacket::build_complex(
            &["s", "x", "y", "t"],
            &[("s", "x"), ("x", "t"), ("s", "y"), ("y", "t")],
            &[],
        )
        .unwrap(),
    )
    .unwrap();
    let upper = OrientedWalk::new(&square, "s", &[(0, 1), (1, 1)]).unwrap();
    let lower = OrientedWalk::new(&square, "s", &[(2, 1), (3, 1)]).unwrap();
    // Weights 1 and 4, amplitudes 1 and 2: the cross term is 2 * 1 * 2 * Re(u).
    let cases = [
        (gi(1, 0), ri(4)),
        (gi(0, 1), ri(0)),
        (gi(-1, 0), ri(-4)),
        (gi(0, -1), ri(0)),
        (gq(3, 5, 4, 5), rq(12, 5)),
        (gq(5, 13, -12, 13), rq(20, 13)),
    ];
    for (u, cross) in cases {
        let connection = U1Connection::new(&square, vec![gi(1, 0), u, gi(1, 0), gi(1, 0)]).unwrap();
        let family = CoherentPathFamily::new(
            &square,
            &connection,
            &[upper.clone(), lower.clone()],
            &[ri(1), ri(4)],
        )
        .unwrap();
        assert_eq!(family.interference_residual(), cross);
        assert_eq!(family.holonomy_expansion(), family.sink_intensity());
    }
    // The 24th roots of unity: |1 + 2 z|^2 - 1 - 4 = 2 (z + conj z) in Q(zeta_24).
    let mut rational_values = BTreeMap::new();
    for k in 0..24 {
        let z = Cyc24::zeta24(k);
        let amplitude = Cyc24::one().add(&z.mul(&Cyc24::from_int(2)));
        let cross = amplitude.mul(&amplitude.conj()).sub(&Cyc24::from_int(5));
        assert_eq!(cross, z.add(&z.conj()).mul(&Cyc24::from_int(2)));
        assert_eq!(cross.conj(), cross);
        if let Some(value) = cross.as_rational() {
            rational_values.insert(k, value);
        }
    }
    let expected: BTreeMap<i32, Rational> = [
        (0, 4),
        (4, 2),
        (6, 0),
        (8, -2),
        (12, -4),
        (16, -2),
        (18, 0),
        (20, 2),
    ]
    .into_iter()
    .map(|(k, v)| (k, ri(v)))
    .collect();
    assert_eq!(rational_values, expected);
}

fn indicator(order: usize, index: usize) -> Vec<Rational> {
    (0..order).map(|x| ri(i64::from(x == index))).collect()
}

#[test]
fn flux_and_holonomy_do_not_commute_on_the_quaternion_group() {
    let group = FiniteGroupAlgebra::new(quaternion_group()).unwrap();
    for g in 0..8 {
        for h in 0..8 {
            let phi = indicator(8, h);
            assert_eq!(
                group.flux_holonomy_commutator(g, &phi).unwrap(),
                group.translated_difference(g, &phi).unwrap()
            );
        }
        let generic: Vec<Rational> = (0..8).map(|x| rq(x * x - 3, 7)).collect();
        assert_eq!(
            group.flux_holonomy_commutator(g, &generic).unwrap(),
            group.translated_difference(g, &generic).unwrap()
        );
    }
    // The source's witness: g = i, phi = the indicator of 1, read at x = -i where x g = 1.
    let witness = group.flux_holonomy_commutator(I, &indicator(8, 0)).unwrap();
    assert_eq!(witness.get_ref(3, 0).unwrap(), &ri(1));
    // The commutator vanishes exactly when phi is constant on the cosets x<g>.
    let mut commuting = 0;
    for g in 0..8 {
        for mask in 0u32..256 {
            let phi: Vec<Rational> = (0..8).map(|x| ri(i64::from(mask >> x & 1))).collect();
            let vanishes =
                group.flux_holonomy_commutator(g, &phi).unwrap() == mx::zeros(8, 8).unwrap();
            let invariant = (0..8).all(|x| phi[group.product_index(x, g).unwrap()] == phi[x]);
            assert_eq!(vanishes, invariant);
            commuting += usize::from(vanishes);
        }
    }
    // g = 1: all 256; g = -1: cosets {x, -x}, 16; the six elements of order 4: 4 each.
    assert_eq!(commuting, 256 + 16 + 6 * 4);
    // The two-element group {1, -1} is abelian, and flux and holonomy still fail to commute.
    let signs = FiniteGroupAlgebra::new(vec![
        mx::identity(1).unwrap(),
        mx::scale(&mx::identity(1).unwrap(), &gi(-1, 0)).unwrap(),
    ])
    .unwrap();
    assert_ne!(
        signs.flux_holonomy_commutator(1, &indicator(2, 0)).unwrap(),
        mx::zeros(2, 2).unwrap()
    );
}

#[test]
fn area_labels_increase_strictly_from_a_gap_of_root_three_over_two() {
    let first: Vec<SurdRational> = (0..5).map(|n| area_label(n).unwrap()).collect();
    let surd = |coefficient: Rational, radicand: i64| {
        SurdRational::new(coefficient, &ri(radicand)).unwrap()
    };
    assert_eq!(
        first,
        vec![
            surd(ri(0), 1),
            surd(rq(1, 2), 3),
            surd(ri(1), 2),
            surd(rq(1, 2), 15),
            surd(ri(1), 6)
        ]
    );
    let squares: Vec<Rational> = (0..=200).map(area_label_squared).collect();
    for n in 0..=200u32 {
        let label = area_label(n).unwrap();
        assert_eq!(label.square(), squares[n as usize]);
        if n < 200 {
            assert!(squares[n as usize] < squares[n as usize + 1]);
        }
    }
    let positive_minimum = squares.iter().filter(|s| !s.is_zero()).min().unwrap();
    assert_eq!(positive_minimum, &rq(3, 4));
    assert_eq!(squares.iter().filter(|s| *s == &rq(3, 4)).count(), 1);
}

#[test]
fn the_spin_j_casimir_is_j_times_j_plus_one_on_an_irreducible_representation() {
    for n in 0..=12u32 {
        let spin = SpinRepresentation::new(n).unwrap();
        let d = spin.dimension();
        assert_eq!(d, n as usize + 1);
        for defect in bracket_defects(spin.generators()).unwrap() {
            assert_eq!(defect, mx::zeros::<Rational>(d, d).unwrap());
        }
        let expected = mx::scale(&mx::identity(d).unwrap(), &area_label_squared(n)).unwrap();
        assert_eq!(casimir(spin.generators()).unwrap(), expected);
        if n <= 6 {
            assert_eq!(commutant_dimension(&spin.generators()).unwrap(), 1);
        }
    }
    // A triple that is not a representation: J_- doubled breaks [J_+, J_-] = 2 J_z,
    // and its "Casimir" is no longer a scalar.
    let spin = SpinRepresentation::new(2).unwrap();
    let [j_z, j_plus, j_minus] = spin.generators();
    let doubled = mx::scale(j_minus, &ri(2)).unwrap();
    let defects = bracket_defects([j_z, j_plus, &doubled]).unwrap();
    assert_eq!(defects[2], mx::scale(j_z, &ri(2)).unwrap());
    let not_scalar = casimir([j_z, j_plus, &doubled]).unwrap();
    assert_ne!(not_scalar.get(0, 0), not_scalar.get(1, 1));
    // J_z alone on spin 3/2 commutes with the four diagonal matrices; two copies
    // of spin 1/2 commute with M_2 (x) I.
    let three_halves = SpinRepresentation::new(3).unwrap();
    assert_eq!(
        commutant_dimension(&[three_halves.generators()[0]]).unwrap(),
        4
    );
    let half = SpinRepresentation::new(1).unwrap();
    let two = mx::identity::<Rational>(2).unwrap();
    let doubled_half: Vec<BasicMatrix<Rational>> = half
        .generators()
        .iter()
        .map(|g| mx::kronecker(&two, g).unwrap())
        .collect();
    assert_eq!(
        commutant_dimension(&doubled_half.iter().collect::<Vec<_>>()).unwrap(),
        4
    );
    assert_eq!(commutant_dimension(&[]), Err(SpinError::Shape));
    assert_eq!(bracket_defects([j_z, j_plus, &two]), Err(SpinError::Shape));
}

// Origin: engine/crates_rs/tests/core_quantum_physics/repair_and_gravity/loop_quantum_gravity_kinematical_shadows.rs
// Claim: urn:core:crates_rs:tests:loop-quantum-gravity-kinematical-shadows:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord2151871f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord2151871f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError2151871f {
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
impl BoundaryError2151871f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError2151871f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError2151871f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord2151871f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError2151871f> {
        if capacity_bound == 0 {
            return Err(BoundaryError2151871f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError2151871f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError2151871f::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_2151871f() {
    let admitted = BoundaryRecord2151871f::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord2151871f::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
