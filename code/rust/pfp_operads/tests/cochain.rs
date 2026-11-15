//! Edge cochains on a task graph: reading the task, edge lists and chains, the boundary of a
//! chain, walks, potentials by vertex name, and exactness on part of the graph.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-cochain-tests:v1

use std::collections::BTreeMap;

use num_bigint::BigInt;
use pfp_operads::datum::Datum;
use pfp_operads::exact::Rational;
use pfp_operads::families::cochain::{self, Cochain};

fn datum(json: &str) -> Datum {
    Datum::parse(json).expect("JSON")
}

fn q(top: i64, bottom: i64) -> Rational {
    Rational::new(BigInt::from(top), BigInt::from(bottom))
}

/// A triangle 0-1-2 whose edges first name the vertices in the order 2, 0, 1, and a tail 1-3.
const EDGES: &str = "[[2, 0], [0, 1], [1, 2], [1, 3]]";

fn task(labels: &str) -> Cochain {
    cochain::read(&datum(&format!(
        r#"{{"edges": {EDGES}, "labels": {labels}}}"#
    )))
    .expect("a cochain")
}

fn graph_error(edges: &str) -> String {
    cochain::graph(&datum(&format!(r#"{{"edges": {edges}}}"#))).expect_err("no graph")
}

fn label_error(labels: &str) -> String {
    cochain::read(&datum(&format!(
        r#"{{"edges": {EDGES}, "labels": {labels}}}"#
    )))
    .expect_err("no cochain")
}

#[test]
fn a_task_graph_keeps_the_order_its_edges_name_the_vertices() {
    let read = task("[1, 2, 3, 4]");
    let names: Vec<String> = read
        .named
        .graph
        .names()
        .iter()
        .map(BigInt::to_string)
        .collect();
    assert_eq!(names, ["2", "0", "1", "3"]);
    assert_eq!(read.named.graph.edges(), [(0, 1), (1, 2), (2, 0), (2, 3)]);
    assert_eq!(read.values, [q(1, 1), q(2, 1), q(3, 1), q(4, 1)]);
}

#[test]
fn a_vertex_is_found_by_its_name() {
    let named = task("[0, 0, 0, 0]").named;
    assert_eq!(named.vertex(&datum("2")), Some(0));
    assert_eq!(named.vertex(&datum("0")), Some(1));
    assert_eq!(named.vertex(&datum("1")), Some(2));
    assert_eq!(named.vertex(&datum("3")), Some(3));
    assert_eq!(named.vertex(&datum("4")), None);
    assert_eq!(named.vertex(&datum("-1")), None);
    assert_eq!(named.vertex(&datum("\"1\"")), None);
    assert_eq!(named.vertex(&datum("1.0")), None);
}

#[test]
fn a_task_needs_at_least_one_edge_of_two_exact_integers() {
    let wanted = "edges must be a nonempty list of pairs of exact integers";
    assert_eq!(graph_error("[]"), wanted);
    assert_eq!(graph_error("[[0, 1, 2]]"), wanted);
    assert_eq!(graph_error("[[0, 1.5]]"), wanted);
    assert_eq!(graph_error("{}"), wanted);
    assert_eq!(cochain::graph(&datum("{}")).expect_err("no graph"), wanted);
    assert!(cochain::graph(&datum(r#"{"edges": [[0, 0]]}"#)).is_ok());
}

#[test]
fn the_vertices_of_a_task_are_named_zero_up_to_their_count() {
    assert_eq!(graph_error("[[0, 2]]"), "vertices must be 0..n-1");
    assert_eq!(graph_error("[[1, 2], [2, 3]]"), "vertices must be 0..n-1");
    assert_eq!(graph_error("[[-1, 0]]"), "vertices must be 0..n-1");
    assert!(cochain::graph(&datum(r#"{"edges": [[1, 0]]}"#)).is_ok());
}

#[test]
fn a_task_carries_one_exact_rational_per_edge() {
    let wanted = "labels must be one exact rational per edge";
    assert_eq!(label_error("[1, 2, 3]"), wanted);
    assert_eq!(label_error("[1, 2, 3, 4, 5]"), wanted);
    assert_eq!(label_error("[1, 2, 3, 0.5]"), wanted);
    assert_eq!(label_error("[1, 2, 3, \"x\"]"), wanted);
    assert_eq!(label_error("7"), wanted);
    let missing = cochain::read(&datum(&format!(r#"{{"edges": {EDGES}}}"#)));
    assert_eq!(missing.expect_err("no labels"), wanted);
    assert_eq!(
        task("[1, \"-1/2\", \"6/4\", 0]").values[1..3],
        [q(-1, 2), q(3, 2)]
    );
}

#[test]
fn a_graph_error_comes_before_a_label_error() {
    let both = cochain::read(&datum(r#"{"edges": [[0, 2]], "labels": []}"#));
    assert_eq!(both.expect_err("no cochain"), "vertices must be 0..n-1");
}

#[test]
fn an_edge_list_holds_indices_below_the_edge_count() {
    assert_eq!(
        cochain::indices(&datum("[3, 0, 0]"), 4),
        Some(vec![3, 0, 0])
    );
    assert_eq!(cochain::indices(&datum("[]"), 4), Some(vec![]));
    assert_eq!(cochain::indices(&datum("[4]"), 4), None);
    assert_eq!(cochain::indices(&datum("[0, -1]"), 4), None);
    assert_eq!(cochain::indices(&datum("[0, \"1\"]"), 4), None);
    assert_eq!(cochain::indices(&datum("[1.0]"), 4), None);
    assert_eq!(cochain::indices(&datum("2"), 4), None);
    assert_eq!(cochain::indices(&datum("{}"), 4), None);
}

#[test]
fn a_chain_is_read_step_by_step() {
    assert_eq!(
        cochain::chain(&datum("[[0, 1], [3, -1], [0, 1]]"), 4),
        Ok(vec![(0, 1), (3, -1), (0, 1)])
    );
}

#[test]
fn a_chain_needs_at_least_one_step() {
    let wanted = Err("a chain must be a nonempty list of steps".to_owned());
    assert_eq!(cochain::chain(&datum("[]"), 4), wanted);
    assert_eq!(cochain::chain(&datum("{}"), 4), wanted);
    assert_eq!(cochain::chain(&datum("null"), 4), wanted);
}

#[test]
fn a_step_is_an_edge_in_range_and_a_sign() {
    let wanted =
        Err("a chain step is [edge, sign] with the edge in range and sign 1 or -1".to_owned());
    for steps in [
        "[[4, 1]]",
        "[[-1, 1]]",
        "[[0, 0]]",
        "[[0, 2]]",
        "[[0, -2]]",
        "[[0]]",
        "[[0, 1, 1]]",
        "[0]",
        "[[0, \"1\"]]",
        "[[0, 1.0]]",
        "[[\"0\", 1]]",
        "[[0, 1], [0, 3]]",
    ] {
        assert_eq!(cochain::chain(&datum(steps), 4), wanted, "{steps}");
    }
}

#[test]
fn the_boundary_counts_arrivals_less_departures() {
    let graph = task("[0, 0, 0, 0]").named.graph;
    // Edge 0 runs from vertex number 0 to number 1, edge 3 from number 2 to number 3.
    assert_eq!(
        cochain::boundary(&graph, &[(0, 1)]),
        BTreeMap::from([(0, -1), (1, 1)])
    );
    assert_eq!(
        cochain::boundary(&graph, &[(0, -1)]),
        BTreeMap::from([(0, 1), (1, -1)])
    );
    assert_eq!(
        cochain::boundary(&graph, &[(0, 1), (0, 1), (3, -1)]),
        BTreeMap::from([(0, -2), (1, 2), (2, 1), (3, -1)])
    );
}

#[test]
fn a_closed_chain_has_an_empty_boundary() {
    let graph = task("[0, 0, 0, 0]").named.graph;
    assert!(cochain::boundary(&graph, &[(0, 1), (1, 1), (2, 1)]).is_empty());
    assert!(cochain::boundary(&graph, &[(2, -1), (1, -1), (0, -1)]).is_empty());
    assert!(cochain::boundary(&graph, &[(3, 1), (3, -1)]).is_empty());
    // The steps of a closed chain need not follow one another.
    assert!(cochain::boundary(&graph, &[(1, 1), (0, 1), (2, 1)]).is_empty());
    assert!(cochain::boundary(&graph, &[]).is_empty());
    // Two of the three sides leave the ends of the third.
    assert_eq!(
        cochain::boundary(&graph, &[(0, 1), (1, 1)]),
        BTreeMap::from([(0, -1), (2, 1)])
    );
}

#[test]
fn a_loop_and_an_edge_out_of_range_add_nothing_to_a_boundary() {
    let looped = cochain::graph(&datum(r#"{"edges": [[0, 0], [0, 1]]}"#)).expect("a graph");
    assert!(cochain::boundary(&looped.graph, &[(0, 1)]).is_empty());
    assert_eq!(
        cochain::boundary(&looped.graph, &[(0, 1), (7, 1), (1, 1)]),
        BTreeMap::from([(0, -1), (1, 1)])
    );
}

#[test]
fn a_walk_ends_where_its_last_step_arrives() {
    let graph = task("[0, 0, 0, 0]").named.graph;
    assert_eq!(cochain::walk_end(&graph, 0, &[(0, 1)]), Some(1));
    assert_eq!(cochain::walk_end(&graph, 1, &[(0, -1)]), Some(0));
    assert_eq!(
        cochain::walk_end(&graph, 0, &[(0, 1), (1, 1), (3, 1)]),
        Some(3)
    );
    assert_eq!(
        cochain::walk_end(&graph, 3, &[(3, -1), (2, 1), (0, 1)]),
        Some(1)
    );
    assert_eq!(cochain::walk_end(&graph, 2, &[]), Some(2));
}

#[test]
fn a_step_that_does_not_start_where_the_walk_stands_ends_it() {
    let graph = task("[0, 0, 0, 0]").named.graph;
    // Edge 0 leaves vertex number 0, not number 1.
    assert_eq!(cochain::walk_end(&graph, 1, &[(0, 1)]), None);
    assert_eq!(cochain::walk_end(&graph, 0, &[(0, -1)]), None);
    assert_eq!(cochain::walk_end(&graph, 0, &[(0, 1), (3, 1)]), None);
    assert_eq!(
        cochain::walk_end(&graph, 0, &[(0, 1), (1, 1), (0, -1)]),
        None
    );
    assert_eq!(cochain::walk_end(&graph, 0, &[(4, 1)]), None);
}

#[test]
fn a_potential_is_listed_by_vertex_name() {
    let named = task("[0, 0, 0, 0]").named;
    // Names 0, 1, 2, 3 are the graph's vertices number 1, 2, 0, 3.
    assert_eq!(
        named.potential(&datum("[10, \"1/2\", 30, -4]")),
        Ok(vec![q(30, 1), q(10, 1), q(1, 2), q(-4, 1)])
    );
}

#[test]
fn a_potential_has_one_exact_rational_per_vertex() {
    let named = task("[0, 0, 0, 0]").named;
    let wanted = Err("potential must be one exact rational per vertex".to_owned());
    assert_eq!(named.potential(&datum("[1, 2, 3]")), wanted);
    assert_eq!(named.potential(&datum("[1, 2, 3, 4, 5]")), wanted);
    assert_eq!(named.potential(&datum("[1, 2, 3, 0.5]")), wanted);
    assert_eq!(named.potential(&datum("{}")), wanted);
}

#[test]
fn a_potential_by_name_explains_the_values_it_was_made_for() {
    let read = task("[-20, \"-19/2\", \"59/2\", \"-9/2\"]");
    let potential = read
        .named
        .potential(&datum("[10, \"1/2\", 30, -4]"))
        .expect("a potential");
    let left = read.named.graph.residual(&read.values, &potential);
    assert_eq!(left, vec![q(0, 1); 4]);
}

#[test]
fn values_are_exact_on_edges_that_close_no_odd_cycle() {
    // Round the triangle the values sum to 6.
    let read = task("[1, 2, 3, 4]");
    assert!(read.exact_on(&[0, 1]));
    assert!(read.exact_on(&[1, 2, 3]));
    assert!(read.exact_on(&[3]));
    assert!(read.exact_on(&[]));
    assert!(!read.exact_on(&[0, 1, 2]));
    assert!(!read.exact_on(&[0, 1, 2, 3]));
    assert!(!read.exact_on(&[2, 1, 0]));
}

#[test]
fn exactness_on_a_patch_uses_only_that_patchs_values() {
    let balanced = task("[1, 2, -3, 4]");
    assert!(balanced.exact_on(&[0, 1, 2]));
    assert!(balanced.exact_on(&[0, 1, 2, 3]));
    // The same edge twice is a two-edge cycle: its two values agree, so it sums to zero.
    assert!(balanced.exact_on(&[3, 3]));
    // An edge the graph does not have is left out.
    assert!(balanced.exact_on(&[0, 1, 2, 9]));
    let unbalanced = task("[1, 2, 3, 4]");
    assert!(!unbalanced.exact_on(&[0, 1, 2, 9]));
}
