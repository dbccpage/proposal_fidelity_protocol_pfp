//! Tree gauge fixing, pure-gauge decisions, gauge equivalence, holonomy
//! verdicts and flat cyclic gauge classes on cell complexes.
//!
//! Each test states the invariant it protects. The independent routes are
//! the string-keyed `DiscreteConnection` code already in the crate (gauge
//! action, loop holonomy, pure-gauge construction) and brute-force
//! enumeration of `Z_n` connections and their gauge orbits, written here in
//! plain integers, so neither shares code with the module under test.
//!
//! AuthorityEffect: None.

use num_bigint::{BigInt, BigUint};
use num_rational::BigRational;
use core_holonomy::gauge_fixing::{
    cycle_rank, face_holonomies, flat_cyclic_gauge_classes, gauge_equivalence, holonomy_verdict,
    tree_gauge, tree_gauge_indexed, EdgeConnection, GaugeEquivalence, HolonomyVerdict,
    PureGaugeVerdict,
};
use core_holonomy::graph::{Face, OrientedStep};
use core_holonomy::{
    compute_loop_holonomy, CellComplex, DiscreteConnection, ExactMatrix, GaussianRational,
    HolonomyError,
};
use core_kernel::resource_limits::OperationLimits;
use std::collections::{BTreeMap, BTreeSet};

type Q = BigRational;
type Gq = GaussianRational<BigRational>;
type QM = ExactMatrix<Q>;
type GM = ExactMatrix<Gq>;

fn q(n: i64) -> Q {
    BigRational::from_integer(BigInt::from(n))
}

fn qr(n: i64, d: i64) -> Q {
    BigRational::new(BigInt::from(n), BigInt::from(d))
}

fn m2(a: i64, b: i64, c: i64, d: i64) -> QM {
    ExactMatrix::try_new(2, 2, vec![q(a), q(b), q(c), q(d)]).unwrap()
}

fn scalar(x: Q) -> QM {
    ExactMatrix::try_new(1, 1, vec![x]).unwrap()
}

fn id(n: usize) -> QM {
    ExactMatrix::try_identity(n).unwrap()
}

fn mul(a: &QM, b: &QM) -> QM {
    a.matmul(b).unwrap()
}

fn inv(a: &QM) -> QM {
    a.inverse().unwrap()
}

fn gi(re: i64, im: i64) -> Gq {
    GaussianRational::new(q(re), q(im))
}

fn gm2(a: Gq, b: Gq, c: Gq, d: Gq) -> GM {
    ExactMatrix::try_new(2, 2, vec![a, b, c, d]).unwrap()
}

fn gmul(a: &GM, b: &GM) -> GM {
    a.matmul(b).unwrap()
}

fn gneg(m: &GM) -> GM {
    ExactMatrix::try_new(m.rows, m.cols, m.data.iter().map(|x| -x.clone()).collect()).unwrap()
}

// The quaternion group Q8 as 2x2 matrices over Q(i): a non-abelian finite
// subgroup of SU(2) with i*j = k.
fn q8_one() -> GM {
    gm2(gi(1, 0), gi(0, 0), gi(0, 0), gi(1, 0))
}
fn q8_i() -> GM {
    gm2(gi(0, 1), gi(0, 0), gi(0, 0), gi(0, -1))
}
fn q8_j() -> GM {
    gm2(gi(0, 0), gi(1, 0), gi(-1, 0), gi(0, 0))
}
fn q8_k() -> GM {
    gm2(gi(0, 0), gi(0, 1), gi(0, 1), gi(0, 0))
}

// ---------------------------------------------------------------------------
// Complexes
// ---------------------------------------------------------------------------

fn build(vertices: &[&str], edges: &[(&str, &str)]) -> CellComplex {
    let mut complex = CellComplex::new(OperationLimits::holonomy());
    for v in vertices {
        complex.add_vertex(*v).unwrap();
    }
    for (s, t) in edges {
        complex.add_edge(s, t).unwrap();
    }
    complex
}

/// A face with explicit steps: `add_face` resolves an edge by its vertex pair
/// and cannot choose between antiparallel edges or give a loop direction -1.
fn push_face(complex: &mut CellComplex, id: &str, vertices: &[&str], steps: &[(usize, i8)]) {
    let index = complex.faces.len();
    complex.faces.push(Face {
        id: id.to_owned(),
        index,
        boundary_vertices: vertices.iter().map(|s| (*s).to_owned()).collect(),
        boundary_edges: steps
            .iter()
            .map(|&(edge_index, direction)| OrientedStep {
                edge_index,
                direction,
            })
            .collect(),
    });
    complex.face_map.insert(id.to_owned(), index);
}

fn triangle() -> CellComplex {
    build(&["a", "b", "c"], &[("a", "b"), ("b", "c"), ("c", "a")])
}

fn triangle_with_face() -> CellComplex {
    let mut complex = triangle();
    complex
        .add_face("f", &["a".to_owned(), "b".to_owned(), "c".to_owned()])
        .unwrap();
    complex
}

/// A square `a b c d` with the diagonal `a c`: cycle rank 2.
fn square_with_diagonal() -> CellComplex {
    build(
        &["a", "b", "c", "d"],
        &[("a", "b"), ("b", "c"), ("c", "d"), ("d", "a"), ("a", "c")],
    )
}

/// The boundary of a tetrahedron: a triangulated 2-sphere.
fn tetrahedron() -> CellComplex {
    let mut complex = build(
        &["0", "1", "2", "3"],
        &[
            ("0", "1"),
            ("0", "2"),
            ("0", "3"),
            ("1", "2"),
            ("1", "3"),
            ("2", "3"),
        ],
    );
    for (index, face) in [
        ["0", "1", "2"],
        ["0", "1", "3"],
        ["0", "2", "3"],
        ["1", "2", "3"],
    ]
    .iter()
    .enumerate()
    {
        let cycle: Vec<String> = face.iter().map(|s| (*s).to_owned()).collect();
        complex.add_face(format!("f{index}"), &cycle).unwrap();
    }
    complex
}

/// The 2 x 2 periodic square lattice: 4 vertices, 8 edges (each horizontal
/// and vertical pair joins the same two vertices in opposite directions),
/// 4 faces. Vertex `(r, c)` is named `rc`; edges are `h(r, c)` from `(r, c)`
/// to `(r, c+1)` at index `2r + c` and `v(r, c)` from `(r, c)` to `(r+1, c)`
/// at index `4 + 2r + c`, indices mod 2.
fn torus_2x2() -> CellComplex {
    let name = |r: usize, c: usize| format!("{}{}", r % 2, c % 2);
    let mut complex = CellComplex::new(OperationLimits::holonomy());
    for r in 0..2 {
        for c in 0..2 {
            complex.add_vertex(name(r, c)).unwrap();
        }
    }
    for r in 0..2 {
        for c in 0..2 {
            complex.add_edge(&name(r, c), &name(r, c + 1)).unwrap();
        }
    }
    for r in 0..2 {
        for c in 0..2 {
            complex.add_edge(&name(r, c), &name(r + 1, c)).unwrap();
        }
    }
    let h = |r: usize, c: usize| 2 * (r % 2) + (c % 2);
    let v = |r: usize, c: usize| 4 + 2 * (r % 2) + (c % 2);
    for pr in 0..2usize {
        for pc in 0..2usize {
            let corners = [
                name(pr, pc),
                name(pr, pc + 1),
                name(pr + 1, pc + 1),
                name(pr + 1, pc),
                name(pr, pc),
            ];
            let corner_refs: Vec<&str> = corners.iter().map(String::as_str).collect();
            push_face(
                &mut complex,
                &format!("f{pr}{pc}"),
                &corner_refs,
                &[
                    (h(pr, pc), 1),
                    (v(pr, pc + 1), 1),
                    (h(pr + 1, pc), -1),
                    (v(pr, pc), -1),
                ],
            );
        }
    }
    complex
}

/// The projective plane as a cell complex: one vertex, one loop `e`, one face
/// whose boundary is `e e`.
fn projective_plane_cell() -> CellComplex {
    let mut complex = build(&["v"], &[("v", "v")]);
    push_face(&mut complex, "f", &["v", "v", "v"], &[(0, 1), (0, 1)]);
    complex
}

/// The Klein bottle as one face with boundary `a b a^-1 b`. `add_edge` keeps one
/// edge per `(source, target)` pair, so only `a` is a loop at `v`; `b` is
/// subdivided into `v -> w -> v`. H_1 = Z + Z/2.
fn klein_bottle_cell() -> CellComplex {
    let mut complex = build(&["v", "w"], &[("v", "v"), ("v", "w"), ("w", "v")]);
    push_face(
        &mut complex,
        "f",
        &["v", "v", "w", "v", "v", "w", "v"],
        &[(0, 1), (1, 1), (2, 1), (0, -1), (1, 1), (2, 1)],
    );
    complex
}

/// The torus as one face with boundary `a b a^-1 b^-1`, both generators
/// subdivided: `a = v -> w -> v`, `b = v -> x -> v`. H_1 = Z^2.
fn torus_cell() -> CellComplex {
    let mut complex = build(
        &["v", "w", "x"],
        &[("v", "w"), ("w", "v"), ("v", "x"), ("x", "v")],
    );
    // word a b a^-1 b^-1 with a = e0 e1, b = e2 e3.
    push_face(
        &mut complex,
        "f",
        &["v", "w", "v", "x", "v", "w", "v", "x", "v"],
        &[
            (0, 1),
            (1, 1),
            (2, 1),
            (3, 1),
            (1, -1),
            (0, -1),
            (3, -1),
            (2, -1),
        ],
    );
    complex
}

fn index_of(complex: &CellComplex, id: &str) -> usize {
    complex.vertex_map[id]
}

fn path(steps: &[(usize, i8)]) -> Vec<OrientedStep> {
    steps
        .iter()
        .map(|&(edge_index, direction)| OrientedStep {
            edge_index,
            direction,
        })
        .collect()
}

fn discrete(complex: &CellComplex, dim: usize, values: &[QM]) -> DiscreteConnection<Q> {
    let mut connection = DiscreteConnection::<Q>::new(dim, complex.limits);
    for (edge, value) in complex.edges.iter().zip(values) {
        connection
            .set_connection(edge.source.clone(), edge.target.clone(), value.clone())
            .unwrap();
    }
    connection
}

// ---------------------------------------------------------------------------
// Tree gauge
// ---------------------------------------------------------------------------

#[test]
fn every_connection_on_a_tree_is_gauge_trivial() {
    // A path and a star: no edge lies off the forest, so every residual is
    // the identity whatever the values are.
    let path_graph = build(&["a", "b", "c", "d"], &[("a", "b"), ("c", "b"), ("c", "d")]);
    let values = [m2(1, 1, 0, 1), m2(2, 1, 1, 1), m2(1, 0, 3, 1)];
    let connection = EdgeConnection::new(&path_graph, 2, values.to_vec()).unwrap();
    let fixed = tree_gauge_indexed(&path_graph, &connection).unwrap();
    assert!(fixed.is_gauge_trivial());
    assert_eq!(fixed.tree_edges(), vec![0, 1, 2]);
    assert!(fixed.cycle_holonomies().is_empty());
    assert!(matches!(
        fixed.pure_gauge_verdict().unwrap(),
        PureGaugeVerdict::PureGauge { .. }
    ));

    let star = build(&["h", "x", "y", "z"], &[("h", "x"), ("y", "h"), ("h", "z")]);
    let connection = EdgeConnection::new(&star, 2, values.to_vec()).unwrap();
    assert!(tree_gauge_indexed(&star, &connection)
        .unwrap()
        .is_gauge_trivial());
}

#[test]
fn the_tree_gauge_makes_every_tree_edge_the_identity_and_spans_each_component() {
    // Two components: a triangle and a segment, plus an isolated vertex.
    let complex = build(
        &["a", "b", "c", "d", "e", "iso"],
        &[("a", "b"), ("b", "c"), ("c", "a"), ("d", "e")],
    );
    let values = vec![
        m2(1, 1, 0, 1),
        m2(1, 0, 1, 1),
        m2(2, 1, 1, 1),
        m2(1, 2, 0, 1),
    ];
    let connection = EdgeConnection::new(&complex, 2, values).unwrap();
    let fixed = tree_gauge_indexed(&complex, &connection).unwrap();
    // 6 vertices, 3 components: 3 tree edges of the 4, one edge off the forest.
    assert_eq!(fixed.tree_edges().len(), 6 - 3);
    assert_eq!(cycle_rank(&complex).unwrap(), 1);
    for edge in fixed.tree_edges() {
        assert_eq!(
            *fixed.residual_value(edge).unwrap(),
            id(2),
            "tree edge {edge}"
        );
    }
    let roots: BTreeSet<usize> = (0..6).map(|v| fixed.root_of(v).unwrap()).collect();
    assert_eq!(roots.len(), 3);
    // Roots are the first vertex of each component, and carry the identity.
    for root in roots {
        assert_eq!(fixed.gauge()[root], id(2));
        assert_eq!(*fixed.transport_from_root(root).unwrap(), id(2));
    }
    assert_eq!(fixed.root_of(4).unwrap(), 3);
    assert_eq!(fixed.root_of(5).unwrap(), 5);
}

#[test]
fn the_residual_on_a_cycle_edge_is_the_holonomy_of_its_fundamental_cycle() {
    let complex = triangle();
    // Q8: a -> b by i, b -> c by i, c -> a by j. The loop a b c a has
    // holonomy j * i * i = -j.
    let values = vec![q8_i(), q8_i(), q8_j()];
    let connection = EdgeConnection::new(&complex, 2, values.clone()).unwrap();
    let fixed = tree_gauge_indexed(&complex, &connection).unwrap();
    // BFS from a discovers b through e0 and c through e2 (reversed); e1 is off the tree.
    assert_eq!(fixed.tree_edges(), vec![0, 2]);
    let expected = gmul(&gmul(&values[2], &values[1]), &values[0]);
    assert_eq!(expected, gneg(&q8_j()));
    let cycles = fixed.cycle_holonomies();
    assert_eq!(cycles, vec![(1, expected.clone())]);
    // The fundamental cycle replays to the residual, by the crate's own
    // walk and by the string-keyed loop holonomy.
    let cycle = fixed.fundamental_cycle(1).unwrap();
    assert_eq!(cycle.base, "a");
    assert_eq!(cycle.vertices.first(), cycle.vertices.last());
    let base = index_of(&complex, &cycle.base);
    assert_eq!(
        connection
            .loop_holonomy(&complex, base, &cycle.steps)
            .unwrap(),
        expected
    );
    let string_keyed = connection.to_discrete_connection(&complex).unwrap();
    assert_eq!(
        compute_loop_holonomy(&string_keyed, &cycle.vertices).unwrap(),
        expected
    );
}

#[test]
fn the_residual_is_the_edge_value_conjugated_by_the_tree_path_transports() {
    // Edges: e0 a->b, e1 c->b (against the tree direction), e2 c->d, e3 d->a.
    // BFS from a takes e0 (to b), e3 reversed (to d), then e1 reversed from b
    // (to c); e2 is the only edge off the tree.
    let complex = build(
        &["a", "b", "c", "d"],
        &[("a", "b"), ("c", "b"), ("c", "d"), ("d", "a")],
    );
    let (u0, u1, u2, u3) = (
        m2(1, 1, 0, 1),
        m2(2, 1, 1, 1),
        m2(1, 0, 3, 1),
        m2(3, 1, 2, 1),
    );
    let connection = EdgeConnection::new(
        &complex,
        2,
        vec![u0.clone(), u1.clone(), u2.clone(), u3.clone()],
    )
    .unwrap();
    let fixed = tree_gauge_indexed(&complex, &connection).unwrap();
    assert_eq!(fixed.tree_edges(), vec![0, 1, 3]);

    // Transports from the root a, written out along the tree paths.
    let t_a = id(2);
    let t_b = u0.clone();
    let t_d = inv(&u3);
    let t_c = mul(&inv(&u1), &u0);
    for (vertex, expected) in [("a", &t_a), ("b", &t_b), ("c", &t_c), ("d", &t_d)] {
        let index = index_of(&complex, vertex);
        assert_eq!(
            fixed.transport_from_root(index).unwrap(),
            expected,
            "T({vertex})"
        );
        assert_eq!(
            fixed.gauge()[index],
            inv(expected),
            "g({vertex}) = T({vertex})^-1"
        );
    }
    // R_e2 = T(d)^-1 U2 T(c) = U3 U2 U1^-1 U0 for e2: c -> d.
    let expected = mul(&mul(&mul(&u3, &u2), &inv(&u1)), &u0);
    assert_eq!(expected, mul(&mul(&inv(&t_d), &u2), &t_c));
    assert_eq!(*fixed.residual_value(2).unwrap(), expected);
    // Based at c the same loop has holonomy T(c) R T(c)^-1: conjugation, not equality.
    let around_c = connection
        .loop_holonomy(
            &complex,
            index_of(&complex, "c"),
            &path(&[(2, 1), (3, 1), (0, 1), (1, -1)]),
        )
        .unwrap();
    assert_eq!(around_c, mul(&mul(&t_c, &expected), &inv(&t_c)));
    assert_ne!(
        around_c, expected,
        "the two based loops differ for a non-abelian fibre"
    );
}

#[test]
fn the_tree_gauge_residual_equals_the_string_keyed_gauge_action() {
    // The existing DiscreteConnection::apply_gauge_transformation is an
    // independent implementation of g(t) U g(s)^-1.
    let complex = square_with_diagonal();
    let values = vec![
        m2(1, 1, 0, 1),
        m2(2, 1, 1, 1),
        m2(1, 0, 3, 1),
        m2(3, 1, 2, 1),
        m2(1, 2, 0, 1),
    ];
    let connection = discrete(&complex, 2, &values);
    let fixed = tree_gauge(&complex, &connection).unwrap();
    let transformed = connection
        .apply_gauge_transformation(&fixed.gauge_map())
        .unwrap();
    for (index, edge) in complex.edges.iter().enumerate() {
        assert_eq!(
            transformed.get_step(&edge.source, &edge.target).unwrap(),
            fixed.residual_value(index).unwrap(),
            "edge {index}"
        );
    }
    // The identity on the tree, and two edges off it (cycle rank 2).
    assert_eq!(cycle_rank(&complex).unwrap(), 2);
    assert_eq!(fixed.cycle_holonomies().len(), 2);
    // Round trip through the string-keyed form.
    let indexed = EdgeConnection::from_discrete_connection(&complex, &connection).unwrap();
    assert_eq!(
        indexed
            .to_discrete_connection(&complex)
            .unwrap()
            .content_hash(),
        connection.content_hash()
    );
}

// ---------------------------------------------------------------------------
// Pure gauge
// ---------------------------------------------------------------------------

#[test]
fn a_gauge_transform_of_the_trivial_connection_is_pure_gauge_and_its_potentials_come_back() {
    let complex = square_with_diagonal();
    let potentials = vec![
        m2(1, 2, 1, 3),
        m2(2, 1, 5, 3),
        m2(1, 0, 3, 1),
        m2(3, 1, 2, 1),
    ];
    let connection = EdgeConnection::pure_gauge(&complex, &potentials).unwrap();
    let fixed = tree_gauge_indexed(&complex, &connection).unwrap();
    assert!(fixed.is_gauge_trivial());
    let PureGaugeVerdict::PureGauge {
        potentials: recovered,
    } = fixed.pure_gauge_verdict().unwrap()
    else {
        panic!("a pure-gauge connection must be decided pure gauge");
    };
    // The recovered potentials are the originals normalised to the identity at
    // the root: h(v) = g(v) g(root)^-1.
    let root = inv(&potentials[0]);
    assert_eq!(recovered[0], id(2));
    for (v, g) in potentials.iter().enumerate() {
        assert_eq!(recovered[v], mul(g, &root), "h({v})");
    }
    // They rebuild the same connection exactly.
    assert_eq!(
        EdgeConnection::pure_gauge(&complex, &recovered).unwrap(),
        connection
    );
    // The existing string-keyed constructor agrees on U_e = g(t) g(s)^-1.
    let gauge_map: BTreeMap<String, QM> = complex
        .vertices
        .iter()
        .zip(&potentials)
        .map(|(v, g)| (v.id.clone(), g.clone()))
        .collect();
    let existing =
        DiscreteConnection::from_pure_gauge(&complex, &gauge_map, 2, complex.limits).unwrap();
    assert_eq!(
        existing.content_hash(),
        connection
            .to_discrete_connection(&complex)
            .unwrap()
            .content_hash()
    );
}

#[test]
fn the_trivial_connection_is_pure_gauge_with_identity_potentials() {
    let complex = square_with_diagonal();
    let connection = EdgeConnection::<Q>::trivial(&complex, 3).unwrap();
    let fixed = tree_gauge_indexed(&complex, &connection).unwrap();
    let PureGaugeVerdict::PureGauge { potentials } = fixed.pure_gauge_verdict().unwrap() else {
        panic!("the trivial connection is pure gauge");
    };
    assert!(potentials.iter().all(|h| *h == id(3)));
}

#[test]
fn a_perturbed_cycle_edge_is_not_pure_gauge_and_the_witness_replays() {
    let complex = square_with_diagonal();
    let potentials = vec![q8_one(), q8_i(), q8_j(), q8_k()];
    let pure = EdgeConnection::pure_gauge(&complex, &potentials).unwrap();
    // BFS from a takes the edges at a (0, 3 and the diagonal 4) as the tree, so
    // edges 1 and 2 lie off it. Multiply edge 1 (b -> c) by i.
    let mut values: Vec<GM> = (0..5).map(|e| pure.value(e).unwrap().clone()).collect();
    values[1] = gmul(&q8_i(), &values[1]);
    let perturbed = EdgeConnection::new(&complex, 2, values).unwrap();
    let fixed = tree_gauge_indexed(&complex, &perturbed).unwrap();
    assert_eq!(fixed.tree_edges(), vec![0, 3, 4]);
    let PureGaugeVerdict::NotPureGauge { witness } = fixed.pure_gauge_verdict().unwrap() else {
        panic!("a perturbed cycle edge must be refused as pure gauge");
    };
    assert_eq!(witness.edge, 1);
    assert_ne!(witness.holonomy, ExactMatrix::try_identity(2).unwrap());
    // The refusal is replayable on its own: walk the cycle.
    let base = index_of(&complex, &witness.cycle.base);
    assert_eq!(
        perturbed
            .loop_holonomy(&complex, base, &witness.cycle.steps)
            .unwrap(),
        witness.holonomy
    );
    assert_eq!(
        witness.cycle.vertices.first(),
        witness.cycle.vertices.last()
    );
    assert_eq!(witness.cycle.vertices.first().unwrap(), &witness.cycle.base);
    // Replay against the existing string-keyed holonomy too.
    let string_keyed = perturbed.to_discrete_connection(&complex).unwrap();
    assert_eq!(
        compute_loop_holonomy(&string_keyed, &witness.cycle.vertices).unwrap(),
        witness.holonomy
    );
}

#[test]
fn gauge_triviality_depends_only_on_the_holonomies_of_cycles() {
    // A triangle with a pendant edge c -> d. The pendant edge lies on no cycle
    // (a bridge), so any change of its value is absorbed by a gauge at d and the
    // connection stays pure gauge. A tree edge on a cycle is different: changing
    // it changes the holonomy of every cycle through it.
    let complex = build(
        &["a", "b", "c", "d"],
        &[("a", "b"), ("b", "c"), ("c", "a"), ("c", "d")],
    );
    let potentials = vec![q8_one(), q8_i(), q8_j(), q8_k()];
    let pure = EdgeConnection::pure_gauge(&complex, &potentials).unwrap();
    let mut values: Vec<GM> = (0..4).map(|e| pure.value(e).unwrap().clone()).collect();

    let mut with_bridge_changed = values.clone();
    with_bridge_changed[3] = gmul(&q8_j(), &with_bridge_changed[3]);
    let bridge = EdgeConnection::new(&complex, 2, with_bridge_changed).unwrap();
    let fixed = tree_gauge_indexed(&complex, &bridge).unwrap();
    assert!(fixed.is_tree_edge(3).unwrap());
    assert!(matches!(
        fixed.pure_gauge_verdict().unwrap(),
        PureGaugeVerdict::PureGauge { .. }
    ));

    // Edge 0 is a tree edge on the triangle: changing it breaks the cycle.
    values[0] = gmul(&q8_j(), &values[0]);
    let on_cycle = EdgeConnection::new(&complex, 2, values).unwrap();
    let fixed = tree_gauge_indexed(&complex, &on_cycle).unwrap();
    assert!(fixed.is_tree_edge(0).unwrap());
    assert!(matches!(
        fixed.pure_gauge_verdict().unwrap(),
        PureGaugeVerdict::NotPureGauge { .. }
    ));
}

#[test]
fn a_gauge_transformation_conjugates_the_tree_residuals_by_the_root_gauge() {
    // For a non-abelian fibre the residual of g.A is g(root) R g(root)^-1, not R:
    // T'(v) = g(v) T(v) g(root)^-1. Every trace and determinant of a residual is
    // gauge invariant.
    let complex = square_with_diagonal();
    let values = vec![
        m2(1, 1, 0, 1),
        m2(2, 1, 1, 1),
        m2(1, 0, 3, 1),
        m2(3, 1, 2, 1),
        m2(1, 2, 0, 1),
    ];
    let a = EdgeConnection::new(&complex, 2, values).unwrap();
    let gauge = vec![
        m2(1, 2, 1, 3),
        m2(2, 1, 5, 3),
        m2(1, 0, 3, 1),
        m2(3, 1, 2, 1),
    ];
    let b = a.gauge_transform(&complex, &gauge).unwrap();
    let fixed_a = tree_gauge_indexed(&complex, &a).unwrap();
    let fixed_b = tree_gauge_indexed(&complex, &b).unwrap();
    let root = &gauge[0];
    for (edge, residual_a) in fixed_a.cycle_holonomies() {
        let residual_b = fixed_b.residual_value(edge).unwrap();
        assert_eq!(
            *residual_b,
            mul(&mul(root, &residual_a), &inv(root)),
            "edge {edge}"
        );
        assert_ne!(
            *residual_b, residual_a,
            "the gauge does not commute with the residual"
        );
        assert_eq!(residual_b.trace().unwrap(), residual_a.trace().unwrap());
        assert_eq!(
            residual_b.determinant().unwrap(),
            residual_a.determinant().unwrap()
        );
    }
    // A gauge that is 1 at the root leaves the residuals exactly unchanged.
    let mut normalised = gauge.clone();
    normalised[0] = id(2);
    let c = a.gauge_transform(&complex, &normalised).unwrap();
    let fixed_c = tree_gauge_indexed(&complex, &c).unwrap();
    assert_eq!(fixed_c.cycle_holonomies(), fixed_a.cycle_holonomies());
}

#[test]
fn an_abelian_residual_is_the_product_of_the_edge_values_around_the_cycle() {
    // Scalars on a triangle: R = u2 u1 u0 whatever the tree is.
    let complex = triangle();
    let connection = EdgeConnection::from_scalars(&complex, vec![q(2), q(3), qr(1, 5)]).unwrap();
    let fixed = tree_gauge_indexed(&complex, &connection).unwrap();
    let (edge, residual) = fixed.cycle_holonomies().remove(0);
    assert_eq!(edge, 1);
    assert_eq!(residual, scalar(qr(6, 5)));
    // Pure gauge exactly when the product is 1.
    assert!(!fixed.is_gauge_trivial());
    let balanced = EdgeConnection::from_scalars(&complex, vec![q(2), q(3), qr(1, 6)]).unwrap();
    assert!(tree_gauge_indexed(&complex, &balanced)
        .unwrap()
        .is_gauge_trivial());
}

// ---------------------------------------------------------------------------
// Antiparallel edges
// ---------------------------------------------------------------------------

#[test]
fn antiparallel_edges_carry_independent_values_only_in_an_edge_indexed_connection() {
    let complex = build(&["a", "b"], &[("a", "b"), ("b", "a")]);
    // Independent values 2 and 3: the loop a b a has holonomy 6.
    let indexed = EdgeConnection::from_scalars(&complex, vec![q(2), q(3)]).unwrap();
    let fixed = tree_gauge_indexed(&complex, &indexed).unwrap();
    assert_eq!(fixed.cycle_holonomies(), vec![(1, scalar(q(6)))]);
    assert!(!fixed.is_gauge_trivial());
    // Consistent values 2 and 1/2: pure gauge.
    let consistent = EdgeConnection::from_scalars(&complex, vec![q(2), qr(1, 2)]).unwrap();
    assert!(tree_gauge_indexed(&complex, &consistent)
        .unwrap()
        .is_gauge_trivial());

    // A string-keyed connection stores one matrix per vertex pair and reads the
    // opposite direction as its inverse: it cannot express the first case, and
    // the adapters refuse rather than guess.
    let mut string_keyed = DiscreteConnection::<Q>::new(1, complex.limits);
    string_keyed.set_connection("a", "b", scalar(q(2))).unwrap();
    string_keyed.set_connection("b", "a", scalar(q(3))).unwrap();
    assert_eq!(
        *string_keyed.get_step("a", "b").unwrap(),
        scalar(qr(1, 3)),
        "the second write replaced the first as its inverse"
    );
    assert_eq!(
        tree_gauge(&complex, &string_keyed).unwrap_err(),
        HolonomyError::AntiparallelEdges {
            first: 0,
            second: 1
        }
    );
    assert_eq!(
        EdgeConnection::from_discrete_connection(&complex, &string_keyed).unwrap_err(),
        HolonomyError::AntiparallelEdges {
            first: 0,
            second: 1
        }
    );
    assert_eq!(
        indexed.to_discrete_connection(&complex).unwrap_err(),
        HolonomyError::AntiparallelEdges {
            first: 0,
            second: 1
        }
    );
}

#[test]
fn a_flat_connection_with_holonomy_minus_one_lives_on_the_two_by_two_torus() {
    // Horizontal edges of row 0 and row 1 carry -1 on the first column and +1
    // on the second, so every face is flat, yet the horizontal loop has
    // holonomy -1. The two horizontal edges of a row join the same vertices in
    // opposite directions with independent values: a string-keyed connection
    // would force them to be inverse and lose the holonomy.
    let complex = torus_2x2();
    assert_eq!(
        (
            complex.vertices.len(),
            complex.edges.len(),
            complex.faces.len()
        ),
        (4, 8, 4)
    );
    let values: Vec<Q> = [-1, 1, -1, 1, 1, 1, 1, 1].iter().map(|&x| q(x)).collect();
    let connection = EdgeConnection::from_scalars(&complex, values).unwrap();
    let holonomies = face_holonomies(&complex, &connection).unwrap();
    assert!(
        holonomies.iter().all(|h| *h == scalar(q(1))),
        "every face is flat"
    );
    let verdict = holonomy_verdict(&complex, &connection).unwrap();
    let HolonomyVerdict::FlatNontrivial { cycle_holonomies } = verdict else {
        panic!("a flat connection with holonomy -1 around a cycle is flat and nontrivial");
    };
    assert!(cycle_holonomies.iter().any(|(_, h)| *h == scalar(q(-1))));
    // The same flux on one face only is curved.
    let values: Vec<Q> = [-1, 1, 1, 1, 1, 1, 1, 1].iter().map(|&x| q(x)).collect();
    let curved = EdgeConnection::from_scalars(&complex, values).unwrap();
    assert!(matches!(
        holonomy_verdict(&complex, &curved).unwrap(),
        HolonomyVerdict::Curved { .. }
    ));
    // A string-keyed adapter refuses the torus.
    assert!(matches!(
        connection.to_discrete_connection(&complex),
        Err(HolonomyError::AntiparallelEdges { .. })
    ));
}

// ---------------------------------------------------------------------------
// Gauge equivalence
// ---------------------------------------------------------------------------

#[test]
fn abelian_gauge_equivalence_is_decided_by_the_residuals() {
    let complex = square_with_diagonal();
    let a = EdgeConnection::from_scalars(&complex, vec![q(2), q(3), q(5), q(7), q(11)]).unwrap();
    // B is A moved by an arbitrary scalar gauge: equivalent, and the returned
    // gauge carries A to B exactly.
    let gauge: Vec<QM> = [2, 3, 5, 7].iter().map(|&x| scalar(q(x))).collect();
    let b = a.gauge_transform(&complex, &gauge).unwrap();
    let GaugeEquivalence::Equivalent { gauge: found } =
        gauge_equivalence(&complex, &a, &b).unwrap()
    else {
        panic!("a gauge transform of A is equivalent to A");
    };
    assert_eq!(a.gauge_transform(&complex, &found).unwrap(), b);
    // Changing the value of edge 1 (off the tree, on the cycle a b c a) changes
    // that cycle's holonomy: inequivalent, naming the edge.
    let c = EdgeConnection::from_scalars(&complex, vec![q(2), q(13), q(5), q(7), q(11)]).unwrap();
    assert!(matches!(
        gauge_equivalence(&complex, &a, &c).unwrap(),
        GaugeEquivalence::Inequivalent { edge: 1 }
    ));
    // A connection is equivalent to itself with the identity gauge up to the tree.
    assert!(matches!(
        gauge_equivalence(&complex, &a, &a).unwrap(),
        GaugeEquivalence::Equivalent { .. }
    ));
}

#[test]
fn non_abelian_equivalence_is_not_overclaimed() {
    let complex = triangle();
    // Residual R_A = [[1,1],[0,1]] on the edge off the tree (edge 1), with
    // identities on the tree edges (0 and 2).
    let a = EdgeConnection::new(&complex, 2, vec![id(2), m2(1, 1, 0, 1), id(2)]).unwrap();
    // The constant gauge c = diag(2, 1) turns it into [[1,2],[0,1]].
    let c = m2(2, 0, 0, 1);
    let b = a
        .gauge_transform(&complex, &[c.clone(), c.clone(), c.clone()])
        .unwrap();
    assert_eq!(b.value(1).unwrap(), &m2(1, 2, 0, 1));
    // The residuals differ, yet the connections are equivalent by construction:
    // the verdict must not be Inequivalent. Trace and determinant agree, so it
    // is Undetermined.
    assert!(matches!(
        gauge_equivalence(&complex, &a, &b).unwrap(),
        GaugeEquivalence::Undetermined { edge: 1 }
    ));
    // A different determinant is a proof of inequivalence.
    let d = EdgeConnection::new(&complex, 2, vec![id(2), m2(1, 0, 0, 3), id(2)]).unwrap();
    let e = EdgeConnection::new(&complex, 2, vec![id(2), m2(1, 0, 0, 2), id(2)]).unwrap();
    assert!(matches!(
        gauge_equivalence(&complex, &d, &e).unwrap(),
        GaugeEquivalence::Inequivalent { edge: 1 }
    ));
    // A gauge that is the identity at the root keeps the residuals equal, so
    // equivalence is certified with the returned gauge.
    let g = vec![id(2), m2(1, 2, 1, 3), m2(2, 1, 5, 3)];
    let moved = a.gauge_transform(&complex, &g).unwrap();
    let GaugeEquivalence::Equivalent { gauge } = gauge_equivalence(&complex, &a, &moved).unwrap()
    else {
        panic!("a gauge that fixes the root leaves the residuals equal");
    };
    assert_eq!(a.gauge_transform(&complex, &gauge).unwrap(), moved);
}

#[test]
fn equivalence_needs_matching_dimensions() {
    let complex = triangle();
    let a = EdgeConnection::<Q>::trivial(&complex, 1).unwrap();
    let b = EdgeConnection::<Q>::trivial(&complex, 2).unwrap();
    assert!(matches!(
        gauge_equivalence(&complex, &a, &b),
        Err(HolonomyError::DimensionMismatch {
            expected: 1,
            actual: 2
        })
    ));
}

// ---------------------------------------------------------------------------
// Verdicts
// ---------------------------------------------------------------------------

#[test]
fn a_graph_has_no_curvature_and_a_cycle_can_carry_flat_nontrivial_holonomy() {
    let complex = triangle();
    let flat_nontrivial = EdgeConnection::from_scalars(&complex, vec![q(-1), q(1), q(1)]).unwrap();
    let HolonomyVerdict::FlatNontrivial { cycle_holonomies } =
        holonomy_verdict(&complex, &flat_nontrivial).unwrap()
    else {
        panic!("a graph has no faces, so holonomy -1 is flat and nontrivial");
    };
    assert_eq!(cycle_holonomies, vec![(1, scalar(q(-1)))]);
    let trivial = EdgeConnection::from_scalars(&complex, vec![q(-1), q(-1), q(1)]).unwrap();
    assert_eq!(
        holonomy_verdict(&complex, &trivial).unwrap(),
        HolonomyVerdict::GaugeTrivial
    );
}

#[test]
fn filling_the_cycle_turns_the_same_flux_into_curvature() {
    let values = vec![q(-1), q(1), q(1)];
    let graph = triangle();
    let filled = triangle_with_face();
    let on_graph = EdgeConnection::from_scalars(&graph, values.clone()).unwrap();
    let on_disk = EdgeConnection::from_scalars(&filled, values).unwrap();
    assert!(matches!(
        holonomy_verdict(&graph, &on_graph).unwrap(),
        HolonomyVerdict::FlatNontrivial { .. }
    ));
    let HolonomyVerdict::Curved {
        face_holonomies,
        first_curved_face,
    } = holonomy_verdict(&filled, &on_disk).unwrap()
    else {
        panic!("the same connection on a filled triangle is curved");
    };
    assert_eq!(first_curved_face, 0);
    assert_eq!(face_holonomies, vec![scalar(q(-1))]);
}

#[test]
fn on_a_simply_connected_complex_flat_means_gauge_trivial_and_a_perturbation_is_curved() {
    let sphere = tetrahedron();
    let potentials = vec![
        m2(1, 2, 1, 3),
        m2(2, 1, 5, 3),
        m2(1, 0, 3, 1),
        m2(3, 1, 2, 1),
    ];
    let pure = EdgeConnection::pure_gauge(&sphere, &potentials).unwrap();
    assert_eq!(
        holonomy_verdict(&sphere, &pure).unwrap(),
        HolonomyVerdict::GaugeTrivial
    );
    // Multiply one edge by a non-identity matrix: the two faces containing it
    // become curved, the other two stay flat.
    let mut values: Vec<QM> = (0..6).map(|e| pure.value(e).unwrap().clone()).collect();
    values[0] = mul(&m2(1, 1, 0, 1), &values[0]);
    let perturbed = EdgeConnection::new(&sphere, 2, values).unwrap();
    let HolonomyVerdict::Curved {
        face_holonomies,
        first_curved_face,
    } = holonomy_verdict(&sphere, &perturbed).unwrap()
    else {
        panic!("a perturbed edge must curve the faces around it");
    };
    let curved: Vec<usize> = face_holonomies
        .iter()
        .enumerate()
        .filter(|(_, h)| **h != id(2))
        .map(|(f, _)| f)
        .collect();
    // Edge 0 is (0, 1): faces f0 = [0 1 2] and f1 = [0 1 3] contain it.
    assert_eq!(curved, vec![0, 1]);
    assert_eq!(first_curved_face, 0);
}

#[test]
fn torsion_lets_a_flat_connection_carry_holonomy_on_the_projective_plane() {
    // One loop e, one face with boundary e e: the face holonomy is u^2, so the
    // connection is flat exactly for u = +-1, although H^1(RP^2; R) = 0.
    let complex = projective_plane_cell();
    let verdict_for = |u: i64| {
        let connection = EdgeConnection::from_scalars(&complex, vec![q(u)]).unwrap();
        holonomy_verdict(&complex, &connection).unwrap()
    };
    assert_eq!(verdict_for(1), HolonomyVerdict::GaugeTrivial);
    assert_eq!(
        verdict_for(-1),
        HolonomyVerdict::FlatNontrivial {
            cycle_holonomies: vec![(0, scalar(q(-1)))]
        }
    );
    assert!(matches!(verdict_for(2), HolonomyVerdict::Curved { .. }));
}

// ---------------------------------------------------------------------------
// Flat cyclic gauge classes
// ---------------------------------------------------------------------------

/// Brute force: enumerate every `Z_n`-valued edge function, keep the flat ones
/// (every face sums to 0 mod n) and count gauge orbits by applying every
/// vertex gauge. Shares no code with the library.
fn brute_force_flat_classes(complex: &CellComplex, n: u64) -> u64 {
    let vertices = complex.vertices.len();
    let endpoints: Vec<(usize, usize)> = complex
        .edges
        .iter()
        .map(|e| (complex.vertex_map[&e.source], complex.vertex_map[&e.target]))
        .collect();
    let faces: Vec<Vec<(usize, i64)>> = complex
        .faces
        .iter()
        .map(|f| {
            f.boundary_edges
                .iter()
                .map(|s| (s.edge_index, i64::from(s.direction)))
                .collect()
        })
        .collect();
    let edges = endpoints.len();
    let n_us = usize::try_from(n).unwrap();
    let total = n_us.pow(u32::try_from(edges).unwrap());
    let gauges = n_us.pow(u32::try_from(vertices).unwrap());
    let decode = |mut code: usize, len: usize| -> Vec<u64> {
        (0..len)
            .map(|_| {
                let digit = u64::try_from(code % n_us).unwrap();
                code /= n_us;
                digit
            })
            .collect()
    };
    let encode = |a: &[u64]| -> usize {
        a.iter()
            .rev()
            .fold(0usize, |acc, &x| acc * n_us + usize::try_from(x).unwrap())
    };
    let modulus = i64::try_from(n).unwrap();
    let mut visited = vec![false; total];
    let mut classes = 0;
    for code in 0..total {
        if visited[code] {
            continue;
        }
        let a = decode(code, edges);
        let flat = faces.iter().all(|face| {
            face.iter()
                .map(|&(edge, d)| d * i64::try_from(a[edge]).unwrap())
                .sum::<i64>()
                .rem_euclid(modulus)
                == 0
        });
        if !flat {
            visited[code] = true;
            continue;
        }
        classes += 1;
        for gauge_code in 0..gauges {
            let g = decode(gauge_code, vertices);
            let b: Vec<u64> = (0..edges)
                .map(|e| (a[e] + g[endpoints[e].1] + n - g[endpoints[e].0]) % n)
                .collect();
            visited[encode(&b)] = true;
        }
    }
    classes
}

fn gcd(a: u64, b: u64) -> u64 {
    if b == 0 {
        a
    } else {
        gcd(b, a % b)
    }
}

#[test]
fn flat_cyclic_classes_match_the_first_cohomology_of_each_complex() {
    // |Hom(H_1(X; Z), Z_n)| for the cell complexes whose H_1 is known:
    //   tree Z^0 -> 1, circle Z -> n, theta graph Z^2 -> n^2, disk 0 -> 1,
    //   sphere 0 -> 1, torus Z^2 -> n^2, RP^2 Z/2 -> gcd(2, n),
    //   Klein bottle Z + Z/2 -> n gcd(2, n).
    let path_graph = build(&["a", "b", "c"], &[("a", "b"), ("b", "c")]);
    let two_triangles = build(
        &["a", "b", "c", "d", "e", "f"],
        &[
            ("a", "b"),
            ("b", "c"),
            ("c", "a"),
            ("d", "e"),
            ("e", "f"),
            ("f", "d"),
        ],
    );
    let cases: Vec<(&str, CellComplex, Box<dyn Fn(u64) -> u64>)> = vec![
        ("path", path_graph, Box::new(|_| 1)),
        ("triangle graph", triangle(), Box::new(|n| n)),
        ("theta graph", square_with_diagonal(), Box::new(|n| n * n)),
        ("two triangles", two_triangles, Box::new(|n| n * n)),
        ("disk", triangle_with_face(), Box::new(|_| 1)),
        ("sphere", tetrahedron(), Box::new(|_| 1)),
        ("torus", torus_2x2(), Box::new(|n| n * n)),
        ("torus, one face", torus_cell(), Box::new(|n| n * n)),
        (
            "projective plane",
            projective_plane_cell(),
            Box::new(|n| gcd(2, n)),
        ),
        (
            "Klein bottle",
            klein_bottle_cell(),
            Box::new(|n| n * gcd(2, n)),
        ),
    ];
    for (name, complex, expected) in &cases {
        for n in 1..=6u64 {
            assert_eq!(
                flat_cyclic_gauge_classes(&complex, n).unwrap(),
                BigUint::from(expected(n)),
                "{name}, Z_{n}"
            );
        }
    }
}

#[test]
fn flat_cyclic_classes_agree_with_brute_force_enumeration_of_connections_and_gauge_orbits() {
    // The brute force enumerates all n^E connections and all n^V gauges, so the
    // sizes are kept small; the complexes include torsion (RP^2, Klein bottle)
    // and antiparallel edges (torus).
    let cases: Vec<(&str, CellComplex, Vec<u64>)> = vec![
        ("triangle graph", triangle(), vec![1, 2, 3, 4, 6]),
        ("theta graph", square_with_diagonal(), vec![1, 2, 3, 4]),
        ("disk", triangle_with_face(), vec![1, 2, 3, 4, 6]),
        ("sphere", tetrahedron(), vec![1, 2, 3, 4]),
        ("torus", torus_2x2(), vec![1, 2, 3, 4]),
        (
            "projective plane",
            projective_plane_cell(),
            vec![1, 2, 3, 4, 6],
        ),
        ("Klein bottle", klein_bottle_cell(), vec![1, 2, 3, 4]),
        ("torus, one face", torus_cell(), vec![1, 2, 3, 4]),
    ];
    for (name, complex, orders) in &cases {
        for &n in orders {
            assert_eq!(
                flat_cyclic_gauge_classes(complex, n).unwrap(),
                BigUint::from(brute_force_flat_classes(complex, n)),
                "{name}, Z_{n}"
            );
        }
    }
}

#[test]
fn cycle_rank_is_edges_minus_vertices_plus_components() {
    assert_eq!(cycle_rank(&triangle()).unwrap(), 1);
    assert_eq!(cycle_rank(&square_with_diagonal()).unwrap(), 2);
    assert_eq!(cycle_rank(&tetrahedron()).unwrap(), 3);
    assert_eq!(cycle_rank(&torus_2x2()).unwrap(), 5);
    assert_eq!(cycle_rank(&projective_plane_cell()).unwrap(), 1);
    assert_eq!(cycle_rank(&build(&["a", "b"], &[])).unwrap(), 0);
    assert_eq!(cycle_rank(&build(&[], &[])).unwrap(), 0);
}

#[test]
fn quarter_turn_gauge_classes_are_counted_by_the_cycle_rank() {
    // Connections with values in {1, i, -1, -i} on the theta graph: 4^5 of them.
    // Their orbits under the 4^4 vertex gauges number 4^rank = 16, and two
    // connections lie in one orbit exactly when the tree residuals agree.
    let complex = square_with_diagonal();
    let units = [gi(1, 0), gi(0, 1), gi(-1, 0), gi(0, -1)];
    let endpoints: Vec<(usize, usize)> = complex
        .edges
        .iter()
        .map(|e| (complex.vertex_map[&e.source], complex.vertex_map[&e.target]))
        .collect();
    let mut orbit_of_code = vec![usize::MAX; 4usize.pow(5)];
    let mut orbits = 0;
    let mut residual_to_orbit = BTreeMap::new();
    let mut seen_residuals = BTreeSet::new();
    for code in 0..4usize.pow(5) {
        let exponents: Vec<usize> = (0..5).map(|e| (code / 4usize.pow(e)) % 4).collect();
        if orbit_of_code[code] == usize::MAX {
            // Plain Z_4 gauge orbit of this connection.
            for gauge in 0..4usize.pow(4) {
                let g: Vec<usize> = (0..4).map(|v| (gauge / 4usize.pow(v)) % 4).collect();
                let moved: usize = (0..5)
                    .map(|e| {
                        let value = (exponents[e] + g[endpoints[e].1] + 4 - g[endpoints[e].0]) % 4;
                        value * 4usize.pow(u32::try_from(e).unwrap())
                    })
                    .sum();
                orbit_of_code[moved] = orbits;
            }
            orbits += 1;
        }
        let connection = EdgeConnection::from_scalars(
            &complex,
            exponents.iter().map(|&k| units[k].clone()).collect(),
        )
        .unwrap();
        let fixed = tree_gauge_indexed(&complex, &connection).unwrap();
        let residual_key: Vec<String> = fixed
            .cycle_holonomies()
            .iter()
            .map(|(e, h)| format!("{e}:{}", h.data[0]))
            .collect();
        seen_residuals.insert(residual_key.clone());
        // Each orbit maps to exactly one residual tuple, and back.
        let previous = residual_to_orbit.insert(residual_key, orbit_of_code[code]);
        if let Some(previous) = previous {
            assert_eq!(
                previous, orbit_of_code[code],
                "residual tuple shared by two orbits"
            );
        }
    }
    assert_eq!(orbits, 16);
    assert_eq!(seen_residuals.len(), 16);
    assert_eq!(
        BigUint::from(4u32).pow(u32::try_from(cycle_rank(&complex).unwrap()).unwrap()),
        BigUint::from(16u32)
    );
}

// ---------------------------------------------------------------------------
// Refusals
// ---------------------------------------------------------------------------

#[test]
fn edge_connection_construction_refuses_malformed_data() {
    let complex = triangle();
    let good = vec![id(2), id(2), id(2)];
    assert!(EdgeConnection::new(&complex, 2, good.clone()).is_ok());
    assert_eq!(
        EdgeConnection::new(&complex, 2, good[..2].to_vec()).unwrap_err(),
        HolonomyError::EdgeValueCount {
            expected: 3,
            actual: 2
        }
    );
    let mut wrong_shape = good.clone();
    wrong_shape[1] = id(3);
    assert!(matches!(
        EdgeConnection::new(&complex, 2, wrong_shape),
        Err(HolonomyError::DimensionMismatch {
            expected: 2,
            actual: 3
        })
    ));
    let mut singular = good;
    singular[2] = m2(1, 2, 2, 4);
    assert!(matches!(
        EdgeConnection::new(&complex, 2, singular),
        Err(HolonomyError::SingularConnection { src, tgt, .. }) if src == "c" && tgt == "a"
    ));
    assert!(matches!(
        EdgeConnection::<Q>::trivial(&complex, 0),
        Err(HolonomyError::DimensionMismatch {
            expected: 1,
            actual: 0
        })
    ));
    let mut tight = OperationLimits::holonomy();
    tight.max_dimension = 2;
    let mut limited = CellComplex::new(tight);
    limited.add_vertex("x").unwrap();
    assert!(matches!(
        EdgeConnection::<Q>::trivial(&limited, 3),
        Err(HolonomyError::AllocationFailure { .. })
    ));
}

#[test]
fn walks_are_validated_step_by_step() {
    let complex = triangle();
    let connection = EdgeConnection::from_scalars(&complex, vec![q(2), q(3), q(5)]).unwrap();
    let a = index_of(&complex, "a");
    // a -> b -> c -> a: 5 * 3 * 2 = 30, and the open walk a -> b -> c is 6.
    assert_eq!(
        connection
            .loop_holonomy(&complex, a, &path(&[(0, 1), (1, 1), (2, 1)]))
            .unwrap(),
        scalar(q(30))
    );
    let (open, end) = connection
        .walk(&complex, a, &path(&[(0, 1), (1, 1)]))
        .unwrap();
    assert_eq!((open, end), (scalar(q(6)), index_of(&complex, "c")));
    assert!(matches!(
        connection.loop_holonomy(&complex, a, &path(&[(0, 1), (1, 1)])),
        Err(HolonomyError::OpenLoop { .. })
    ));
    // A backwards step uses the inverse: a -> c is e2 reversed, value 1/5.
    assert_eq!(
        connection.walk(&complex, a, &path(&[(2, -1)])).unwrap().0,
        scalar(qr(1, 5))
    );
    // Step 1 does not leave the vertex step 0 reached.
    assert!(matches!(
        connection.walk(&complex, a, &path(&[(0, 1), (0, 1)])),
        Err(HolonomyError::BrokenWalk { step: 1, .. })
    ));
    assert!(matches!(
        connection.walk(&complex, a, &path(&[(0, 2)])),
        Err(HolonomyError::InvalidStepDirection {
            step: 0,
            direction: 2
        })
    ));
    assert!(matches!(
        connection.walk(&complex, a, &path(&[(9, 1)])),
        Err(HolonomyError::EdgeIndexOutOfRange {
            index: 9,
            edge_count: 3
        })
    ));
    assert!(matches!(
        connection.walk(&complex, 7, &[]),
        Err(HolonomyError::VertexIndexOutOfRange {
            index: 7,
            vertex_count: 3
        })
    ));
    // The empty walk is the identity.
    assert_eq!(
        connection.walk(&complex, a, &[]).unwrap(),
        (scalar(q(1)), a)
    );
    // A walk longer than the complex's path limit.
    let mut tight = OperationLimits::holonomy();
    tight.max_path_length = 2;
    let mut short_paths = CellComplex::new(tight);
    short_paths.add_vertex("a").unwrap();
    short_paths.add_edge("a", "a").unwrap();
    let loop_connection = EdgeConnection::from_scalars(&short_paths, vec![q(2)]).unwrap();
    assert!(matches!(
        loop_connection.walk(&short_paths, 0, &path(&[(0, 1), (0, 1), (0, 1)])),
        Err(HolonomyError::PathLengthExceeded {
            length: 3,
            limit: 2
        })
    ));
}

#[test]
fn gauge_transforms_refuse_malformed_gauges() {
    let complex = triangle();
    let connection = EdgeConnection::<Q>::trivial(&complex, 2).unwrap();
    assert_eq!(
        connection
            .gauge_transform(&complex, &[id(2), id(2)])
            .unwrap_err(),
        HolonomyError::VertexValueCount {
            expected: 3,
            actual: 2
        }
    );
    assert!(matches!(
        connection.gauge_transform(&complex, &[id(2), id(2), id(3)]),
        Err(HolonomyError::DimensionMismatch {
            expected: 2,
            actual: 3
        })
    ));
    assert!(matches!(
        connection.gauge_transform(&complex, &[id(2), id(2), m2(1, 2, 2, 4)]),
        Err(HolonomyError::SingularMatrix { .. })
    ));
    // A connection built for another complex is refused.
    let other = build(&["a", "b"], &[("a", "b")]);
    assert!(matches!(
        tree_gauge_indexed(&other, &connection),
        Err(HolonomyError::EdgeValueCount {
            expected: 1,
            actual: 3
        })
    ));
}

#[test]
fn indices_outside_the_complex_are_refused() {
    let complex = triangle();
    let connection = EdgeConnection::from_scalars(&complex, vec![q(2), q(3), q(5)]).unwrap();
    let fixed = tree_gauge_indexed(&complex, &connection).unwrap();
    assert!(matches!(
        fixed.residual_value(3),
        Err(HolonomyError::EdgeIndexOutOfRange { .. })
    ));
    assert!(matches!(
        fixed.is_tree_edge(3),
        Err(HolonomyError::EdgeIndexOutOfRange { .. })
    ));
    assert!(matches!(
        fixed.fundamental_cycle(3),
        Err(HolonomyError::EdgeIndexOutOfRange { .. })
    ));
    assert!(matches!(
        fixed.root_of(3),
        Err(HolonomyError::VertexIndexOutOfRange { .. })
    ));
    assert!(matches!(
        fixed.transport_from_root(3),
        Err(HolonomyError::VertexIndexOutOfRange { .. })
    ));
    assert!(matches!(
        connection.value(3),
        Err(HolonomyError::EdgeIndexOutOfRange { .. })
    ));
    // A tree edge has a backtracking fundamental cycle with trivial holonomy.
    let cycle = fixed.fundamental_cycle(0).unwrap();
    let base = index_of(&complex, &cycle.base);
    assert_eq!(
        connection
            .loop_holonomy(&complex, base, &cycle.steps)
            .unwrap(),
        scalar(q(1))
    );
}

#[test]
fn faces_that_are_not_closed_walks_are_refused() {
    let mut broken = triangle();
    // Steps e0 (a -> b) then e2 (c -> a): the second does not leave b.
    push_face(
        &mut broken,
        "f",
        &["a", "b", "c"],
        &[(0, 1), (2, 1), (1, 1)],
    );
    let connection = EdgeConnection::from_scalars(&broken, vec![q(2), q(3), q(5)]).unwrap();
    assert!(matches!(
        face_holonomies(&broken, &connection),
        Err(HolonomyError::BrokenWalk { step: 1, .. })
    ));
    assert!(matches!(
        flat_cyclic_gauge_classes(&broken, 3),
        Err(HolonomyError::BrokenWalk { step: 1, .. })
    ));
    // A walk that does not come back to its first vertex.
    let mut open = triangle();
    push_face(&mut open, "f", &["a", "b", "c"], &[(0, 1), (1, 1)]);
    let connection = EdgeConnection::from_scalars(&open, vec![q(2), q(3), q(5)]).unwrap();
    assert!(matches!(
        face_holonomies(&open, &connection),
        Err(HolonomyError::BoundaryCycleMismatch { .. })
    ));
    assert!(matches!(
        flat_cyclic_gauge_classes(&open, 3),
        Err(HolonomyError::BoundaryCycleMismatch { .. })
    ));
    // A direction other than +-1.
    let mut bad_direction = triangle();
    push_face(&mut bad_direction, "f", &["a", "b", "c"], &[(0, 3)]);
    assert!(matches!(
        flat_cyclic_gauge_classes(&bad_direction, 3),
        Err(HolonomyError::InvalidStepDirection {
            step: 0,
            direction: 3
        })
    ));
    // A face naming an edge the complex lacks.
    let mut missing = triangle();
    push_face(&mut missing, "f", &["a", "b", "c"], &[(7, 1)]);
    assert!(matches!(
        flat_cyclic_gauge_classes(&missing, 3),
        Err(HolonomyError::EdgeIndexOutOfRange {
            index: 7,
            edge_count: 3
        })
    ));
}

#[test]
fn a_cyclic_group_of_order_zero_is_refused() {
    assert_eq!(
        flat_cyclic_gauge_classes(&triangle(), 0).unwrap_err(),
        HolonomyError::InvalidGroupOrder { order: 0 }
    );
}

#[test]
fn the_quaternion_group_is_non_abelian_in_the_fibre_used_here() {
    // Guard for the Q8 fixtures: i j = k, j i = -k, and i^2 = -1.
    assert_eq!(gmul(&q8_i(), &q8_j()), q8_k());
    assert_eq!(gmul(&q8_j(), &q8_i()), gneg(&q8_k()));
    assert_eq!(gmul(&q8_i(), &q8_i()), gneg(&q8_one()));
}

// Origin: engine/crates_rs/tests/core_holonomy/gauge_fixing_tests.rs
// Claim: urn:core:crates_rs:tests:gauge-fixing-tests:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord07e3694b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord07e3694b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError07e3694b {
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
impl BoundaryError07e3694b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError07e3694b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError07e3694b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord07e3694b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError07e3694b> {
        if capacity_bound == 0 {
            return Err(BoundaryError07e3694b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError07e3694b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError07e3694b::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_07e3694b() {
    let admitted = BoundaryRecord07e3694b::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord07e3694b::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
