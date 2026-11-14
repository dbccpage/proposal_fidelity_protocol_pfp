//! Graphs with oriented edges: reading, the breadth-first forest, fundamental cycles, and
//! rational values on edges and vertices.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:graph-tests:v1

use num_bigint::BigInt;
use pfp_operads::datum::Datum;
use pfp_operads::exact::Rational;
use pfp_operads::graph::{walk_sum, Graph};

fn graph(edges: &str) -> Graph {
    Graph::read(&Datum::parse(edges).expect("JSON")).expect("a graph")
}

fn unread(edges: &str) -> bool {
    Graph::read(&Datum::parse(edges).expect("JSON")).is_none()
}

fn q(top: i64, bottom: i64) -> Rational {
    Rational::new(BigInt::from(top), BigInt::from(bottom))
}

fn whole(values: &[i64]) -> Vec<Rational> {
    values.iter().map(|&value| q(value, 1)).collect()
}

/// Two triangles that share the edge 2: 0-1-2 and 2-3-0.
const KITE: &str = "[[0, 1], [1, 2], [2, 0], [2, 3], [3, 0]]";

/// A square 0-1-2-3 with the diagonal 0-2 as its last edge.
const SQUARE: &str = "[[0, 1], [1, 2], [2, 3], [3, 0], [0, 2]]";

#[test]
fn vertices_are_numbered_in_the_order_the_edges_name_them() {
    let read = graph("[[5, -2], [7, 5], [-2, 7]]");
    assert_eq!(
        read.names(),
        [BigInt::from(5), BigInt::from(-2), BigInt::from(7)]
    );
    assert_eq!(read.edges(), [(0, 1), (2, 0), (1, 2)]);
    assert_eq!(read.vertex(&BigInt::from(7)), Some(2));
    assert_eq!(read.vertex(&BigInt::from(5)), Some(0));
    assert_eq!(read.vertex(&BigInt::from(6)), None);
}

#[test]
fn an_empty_edge_list_is_a_graph_with_nothing_in_it() {
    let read = graph("[]");
    assert!(read.names().is_empty() && read.edges().is_empty());
    assert!(read.forest().chords.is_empty());
    assert!(read.fundamental_cycles().is_empty());
}

#[test]
fn a_vertex_may_be_any_exact_integer() {
    let read = graph("[[123456789012345678901234567890, 0]]");
    assert_eq!(
        read.names()[0].to_string(),
        "123456789012345678901234567890"
    );
}

#[test]
fn only_a_list_of_pairs_of_exact_integers_is_a_graph() {
    assert!(unread("null"));
    assert!(unread("{}"));
    assert!(unread("[[0, 1, 2]]"));
    assert!(unread("[[0]]"));
    assert!(unread("[[]]"));
    assert!(unread("[0, 1]"));
    assert!(unread(r#"[["a", "b"]]"#));
    assert!(unread(r#"[[0, "1"]]"#));
    assert!(unread("[[0, 1.0]]"));
    assert!(unread("[[1.0, 0]]"));
    assert!(unread("[[true, 0]]"));
    assert!(unread("[[0, 1], [1, null]]"));
    assert!(unread("[[0, 1], 7]"));
}

#[test]
fn a_graph_is_numbered_when_its_names_are_zero_up_to_the_vertex_count() {
    assert!(graph("[]").is_numbered());
    assert!(graph("[[0, 0]]").is_numbered());
    assert!(graph("[[2, 0], [1, 2]]").is_numbered());
    assert!(!graph("[[0, 2]]").is_numbered());
    assert!(!graph("[[1, 2]]").is_numbered());
    assert!(!graph("[[1, 1]]").is_numbered());
    assert!(!graph("[[0, -1]]").is_numbered());
    assert!(!graph("[[0, 1], [1, 3]]").is_numbered());
}

#[test]
fn the_forest_takes_roots_in_vertex_order_and_neighbours_in_edge_order() {
    let forest = graph(KITE).forest();
    assert_eq!(
        forest.parent,
        [None, Some((0, 0, 1)), Some((0, 2, -1)), Some((0, 4, -1))]
    );
    assert_eq!(forest.chords, [1, 3]);
    assert_eq!(forest.order, [0, 1, 2, 3]);
}

#[test]
fn the_forest_is_breadth_first() {
    // 0 reaches 1 and 3 first; 2 is then reached from 1, the earlier of the two.
    let forest = graph("[[0, 1], [1, 2], [2, 3], [3, 0]]").forest();
    assert_eq!(
        forest.parent,
        [None, Some((0, 0, 1)), Some((1, 1, 1)), Some((0, 3, -1))]
    );
    assert_eq!(forest.chords, [2]);
    assert_eq!(forest.order, [0, 1, 3, 2]);
    // Depth first from 0 would hang 3 under 2 and leave the edge 3 as the chord.
    let deep = graph("[[0, 1], [1, 2], [2, 3], [0, 3], [3, 4]]").forest();
    assert_eq!(deep.parent[3], Some((0, 3, 1)));
    assert_eq!(deep.parent[4], Some((3, 4, 1)));
    assert_eq!(deep.chords, [2]);
    assert_eq!(deep.order, [0, 1, 3, 2, 4]);
}

#[test]
fn each_component_gets_its_own_root() {
    let forest = graph("[[0, 1], [2, 3], [3, 2]]").forest();
    assert_eq!(
        forest.parent,
        [None, Some((0, 0, 1)), None, Some((2, 1, 1))]
    );
    assert_eq!(forest.chords, [2]);
    assert_eq!(forest.order, [0, 1, 2, 3]);
}

#[test]
fn a_loop_and_a_second_edge_between_two_vertices_are_chords() {
    let looped = graph("[[0, 0]]");
    assert_eq!(looped.forest().parent, [None]);
    assert_eq!(looped.forest().chords, [0]);
    assert_eq!(looped.fundamental_cycles(), [vec![(0, 1)]]);
    let doubled = graph("[[0, 1], [0, 1], [1, 0]]");
    assert_eq!(doubled.forest().chords, [1, 2]);
    assert_eq!(
        doubled.fundamental_cycles(),
        [vec![(1, 1), (0, -1)], vec![(2, 1), (0, 1)]]
    );
}

#[test]
fn a_fundamental_cycle_is_its_chord_then_the_two_forest_paths() {
    assert_eq!(
        graph(KITE).fundamental_cycles(),
        [vec![(1, 1), (2, 1), (0, 1)], vec![(3, 1), (4, 1), (2, -1)]]
    );
    assert_eq!(
        graph("[[0, 1], [1, 2], [2, 3], [3, 0]]").fundamental_cycles(),
        [vec![(2, 1), (3, 1), (1, 1), (0, 1)]]
    );
}

#[test]
fn a_fundamental_cycle_leaves_out_the_forest_edges_both_paths_share() {
    // Both ends of the chord 3 hang under vertex 1, so the edge 0 is on neither side.
    assert_eq!(
        graph("[[0, 1], [1, 2], [1, 3], [2, 3]]").fundamental_cycles(),
        [vec![(3, 1), (2, -1), (1, 1)]]
    );
}

#[test]
fn every_fundamental_cycle_closes() {
    for edges in [
        KITE,
        SQUARE,
        "[[0, 1], [1, 2], [1, 3], [2, 3], [3, 0], [2, 2]]",
    ] {
        let read = graph(edges);
        for cycle in read.fundamental_cycles() {
            let mut net = vec![0i32; read.names().len()];
            for (edge, sign) in cycle {
                let (from, to) = read.edges()[edge];
                net[to] += i32::from(sign);
                net[from] -= i32::from(sign);
            }
            assert!(net.iter().all(|&at| at == 0), "{edges}");
        }
    }
}

#[test]
fn a_coboundary_is_head_less_tail_on_each_edge() {
    let read = graph(SQUARE);
    assert_eq!(
        read.coboundary(&whole(&[0, 2, 5, 3])),
        whole(&[2, 3, -2, -3, 5])
    );
    // The vertex named 1 is numbered first, so it takes the first value.
    assert_eq!(
        graph("[[1, 0]]").coboundary(&[q(1, 2), q(1, 3)]),
        [q(-1, 6)]
    );
    assert_eq!(graph("[[0, 0]]").coboundary(&whole(&[9])), whole(&[0]));
}

#[test]
fn a_potential_shorter_than_the_vertices_ends_in_zeros() {
    let read = graph("[[0, 1], [1, 2]]");
    assert_eq!(read.coboundary(&whole(&[5])), whole(&[-5, 0]));
    assert_eq!(read.coboundary(&[]), whole(&[0, 0]));
    assert_eq!(read.coboundary(&whole(&[1, 4])), whole(&[3, -4]));
}

#[test]
fn the_forest_potential_is_zero_at_each_root_and_follows_the_forest() {
    let read = graph(SQUARE);
    // 1 hangs on edge 0 forwards, 3 on edge 3 backwards, 2 on the diagonal forwards.
    assert_eq!(
        read.potential(&whole(&[2, 3, -2, -3, 5])),
        whole(&[0, 2, 5, 3])
    );
    assert_eq!(
        read.potential(&whole(&[2, 3, -2, -2, 5])),
        whole(&[0, 2, 5, 2])
    );
    // The second component is rooted at the vertex named 3; 2 and then 4 hang forwards under it.
    let two = graph("[[0, 1], [3, 2], [2, 4]]");
    assert_eq!(
        two.potential(&[q(1, 2), q(7, 1), q(-1, 3)]),
        [q(0, 1), q(1, 2), q(0, 1), q(7, 1), q(20, 3)]
    );
}

#[test]
fn a_potential_follows_a_path_that_runs_deeper_than_one_edge() {
    // 0 - 1 - 2 - 3 with the middle edge written backwards.
    let read = graph("[[0, 1], [2, 1], [2, 3]]");
    assert_eq!(read.potential(&whole(&[4, 1, 10])), whole(&[0, 4, 3, 13]));
}

#[test]
fn the_residual_is_what_the_coboundary_of_a_potential_leaves() {
    let read = graph(SQUARE);
    let values = whole(&[2, 3, -2, -3, 6]);
    assert_eq!(
        read.residual(&values, &whole(&[0, 0, 0, 0])),
        whole(&[2, 3, -2, -3, 6])
    );
    assert_eq!(
        read.residual(&values, &whole(&[0, 2, 5, 3])),
        whole(&[0, 0, 0, 0, 1])
    );
    assert_eq!(
        read.residual(&values, &whole(&[1, 0, 0, 0])),
        whole(&[3, 3, -2, -4, 7])
    );
}

#[test]
fn values_shorter_than_the_edges_end_in_zeros() {
    let read = graph("[[0, 1], [1, 2]]");
    assert_eq!(
        read.residual(&whole(&[7]), &whole(&[0, 1, 3])),
        whole(&[6, -2])
    );
    assert_eq!(read.residual(&[], &whole(&[0, 1, 3])), whole(&[-1, -2]));
    assert_eq!(read.potential(&whole(&[7])), whole(&[0, 7, 7]));
    assert_eq!(walk_sum(&[(0, 1), (3, -1)], &whole(&[4])), q(4, 1));
}

#[test]
fn the_defect_is_zero_exactly_for_a_coboundary() {
    let read = graph(SQUARE);
    assert_eq!(read.defect(&whole(&[2, 3, -2, -3, 5])), q(0, 1));
    // One unit round the square's own cycle.
    assert_eq!(read.defect(&whole(&[2, 3, -2, -2, 5])), q(1, 1));
    // The diagonal off by one: both triangles through it are off.
    assert_eq!(read.defect(&whole(&[2, 3, -2, -3, 6])), q(2, 1));
    assert_eq!(read.defect(&whole(&[2, 3, -2, -5, 5])), q(2, 1));
    assert_eq!(
        read.defect(&[q(2, 1), q(5, 2), q(-2, 1), q(-3, 1), q(5, 1)]),
        q(1, 2)
    );
    assert_eq!(graph("[[0, 1], [1, 2]]").defect(&whole(&[9, -4])), q(0, 1));
    assert_eq!(graph("[[0, 0]]").defect(&whole(&[-3])), q(3, 1));
    assert_eq!(graph("[]").defect(&[]), q(0, 1));
}

#[test]
fn a_walk_sum_counts_each_edge_with_its_sign() {
    let values = [q(3, 1), q(5, 1), q(1, 2)];
    assert_eq!(walk_sum(&[(0, 1), (1, -1)], &values), q(-2, 1));
    assert_eq!(walk_sum(&[(2, -1), (2, -1), (0, 1)], &values), q(2, 1));
    assert_eq!(walk_sum(&[(1, 1)], &values), q(5, 1));
    assert_eq!(walk_sum(&[], &values), q(0, 1));
}

#[test]
fn a_value_is_a_coboundary_exactly_when_every_fundamental_cycle_sums_to_zero() {
    let read = graph(SQUARE);
    let cycles = read.fundamental_cycles();
    assert_eq!(cycles.len(), 2);
    for values in [
        whole(&[2, 3, -2, -3, 5]),
        whole(&[2, 3, -2, -2, 5]),
        whole(&[2, 3, -2, -3, 6]),
        whole(&[0, 0, 0, 0, 0]),
        whole(&[1, 1, 1, 1, 2]),
    ] {
        let flat = cycles
            .iter()
            .all(|cycle| walk_sum(cycle, &values) == q(0, 1));
        assert_eq!(flat, read.defect(&values) == q(0, 1), "{values:?}");
    }
}
