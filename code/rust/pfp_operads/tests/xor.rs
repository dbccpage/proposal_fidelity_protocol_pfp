//! The XOR repair domain: reading a labelled graph, the cycles a set of flips leaves odd, the
//! smallest repair, and the finding on a reply.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-xor-tests:v1

use std::collections::BTreeSet;

use pfp_operads::datum::Datum;
use pfp_operads::families::xor::{flips, read, Labelled, MAX_EDGES};

fn datum(text: &str) -> Datum {
    Datum::parse(text).expect("JSON")
}

fn labelled(edges: &str, labels: &str) -> Labelled {
    read(&datum(&format!(
        r#"{{"edges": {edges}, "labels": {labels}}}"#
    )))
    .expect("a task")
}

fn refused(task: &str) -> String {
    read(&datum(task)).expect_err("a refusal")
}

fn set(edges: &[usize]) -> BTreeSet<usize> {
    edges.iter().copied().collect()
}

/// Two triangles that share the edge 2. Their fundamental cycles are the edges {1, 2, 0} and
/// {3, 4, 2}.
const KITE: &str = "[[0, 1], [1, 2], [2, 0], [2, 3], [3, 0]]";

fn kite(labels: &str) -> Labelled {
    labelled(KITE, labels)
}

#[test]
fn a_task_is_its_edges_with_one_binary_label_each() {
    let read = kite("[1, 0, 0, 0, 0]");
    assert_eq!(read.graph.edges().len(), 5);
    assert_eq!(read.graph.names().len(), 4);
    assert_eq!(labelled("[]", "[]").graph.edges().len(), 0);
}

#[test]
fn a_task_without_two_lists_of_one_length_is_refused() {
    let lists = "edges and labels must be lists";
    assert_eq!(refused("{}"), lists);
    assert_eq!(refused(r#"{"edges": [[0, 1]]}"#), lists);
    assert_eq!(refused(r#"{"labels": [0]}"#), lists);
    assert_eq!(refused(r#"{"edges": "x", "labels": [0]}"#), lists);
    assert_eq!(refused(r#"{"edges": [[0, 1]], "labels": 0}"#), lists);
    assert_eq!(refused("[]"), lists);
    let count = "one label per edge";
    assert_eq!(refused(r#"{"edges": [[0, 1]], "labels": []}"#), count);
    assert_eq!(refused(r#"{"edges": [[0, 1]], "labels": [0, 1]}"#), count);
    assert_eq!(refused(r#"{"edges": [], "labels": [0]}"#), count);
}

#[test]
fn an_edge_that_is_not_a_pair_of_integers_is_refused() {
    let pair = "each edge is a pair of exact integers";
    assert_eq!(
        refused(r#"{"edges": [[0, 1], [1, 2, 0]], "labels": [0, 0]}"#),
        pair
    );
    assert_eq!(refused(r#"{"edges": ["ab"], "labels": [0]}"#), pair);
    assert_eq!(refused(r#"{"edges": [["a", "b"]], "labels": [0]}"#), pair);
    assert_eq!(refused(r#"{"edges": [[0, 1.0]], "labels": [0]}"#), pair);
}

#[test]
fn a_label_other_than_the_integer_zero_or_one_is_refused() {
    let binary = "every label must be the exact integer 0 or 1";
    for label in [
        "2", "-1", "0.0", "1.0", "0.9", r#""0""#, r#""1""#, "true", "false", "null", "[1]",
    ] {
        let task = format!(r#"{{"edges": [[0, 1], [1, 2]], "labels": [0, {label}]}}"#);
        assert_eq!(refused(&task), binary, "{label}");
    }
}

#[test]
fn a_task_has_at_most_twenty_edges() {
    assert_eq!(MAX_EDGES, 20);
    let path = |edges: usize| {
        let pairs: Vec<String> = (0..edges).map(|at| format!("[{at}, {}]", at + 1)).collect();
        let labels = vec!["1"; edges].join(", ");
        format!(
            r#"{{"edges": [{}], "labels": [{labels}]}}"#,
            pairs.join(", ")
        )
    };
    assert!(read(&datum(&path(20))).is_ok());
    assert_eq!(refused(&path(21)), "at most 20 edges");
    // The count is checked before the edges are read.
    let wide = format!(
        r#"{{"edges": [{}], "labels": [{}]}}"#,
        vec!["7"; 21].join(", "),
        vec!["0"; 21].join(", ")
    );
    assert_eq!(refused(&wide), "at most 20 edges");
}

#[test]
fn a_flip_list_is_a_set_of_edge_indices() {
    assert_eq!(flips(Some(&datum("[2, 0]")), 3), Ok(set(&[0, 2])));
    assert_eq!(flips(Some(&datum("[1, 1, 1]")), 3), Ok(set(&[1])));
    assert_eq!(flips(Some(&datum("[]")), 0), Ok(set(&[])));
    assert_eq!(flips(Some(&datum("[2]")), 3), Ok(set(&[2])));
}

#[test]
fn a_flip_list_that_cannot_be_read_says_why() {
    let required = Err("flip list required".to_owned());
    assert_eq!(flips(None, 3), required);
    assert_eq!(flips(Some(&datum(r#""x""#)), 3), required);
    assert_eq!(flips(Some(&datum("{}")), 3), required);
    assert_eq!(flips(Some(&datum("1")), 3), required);
    let inexact = Err("flip must be an exact int".to_owned());
    assert_eq!(flips(Some(&datum(r#"["1"]"#)), 3), inexact);
    assert_eq!(flips(Some(&datum("[1.0]")), 3), inexact);
    assert_eq!(flips(Some(&datum("[true]")), 3), inexact);
    assert_eq!(flips(Some(&datum("[0, null]")), 3), inexact);
    // An entry that is no integer is reported before one that is out of range.
    assert_eq!(flips(Some(&datum(r#"[99, "x"]"#)), 3), inexact);
    let range = Err("flip index out of range".to_owned());
    assert_eq!(flips(Some(&datum("[3]")), 3), range);
    assert_eq!(flips(Some(&datum("[0, -1]")), 3), range);
    assert_eq!(flips(Some(&datum("[0]")), 0), range);
    assert_eq!(
        flips(Some(&datum("[123456789012345678901234567890]")), 3),
        range
    );
}

#[test]
fn a_cycle_is_odd_when_its_labels_after_the_flips_sum_to_an_odd_number() {
    let read = kite("[1, 0, 0, 0, 0]");
    assert_eq!(read.odd_cycles(&set(&[])), [0]);
    assert_eq!(read.odd_cycles(&set(&[0])), Vec::<usize>::new());
    assert_eq!(read.odd_cycles(&set(&[1])), Vec::<usize>::new());
    // The shared edge moves the fault to the other triangle.
    assert_eq!(read.odd_cycles(&set(&[2])), [1]);
    assert_eq!(read.odd_cycles(&set(&[3])), [0, 1]);
    assert_eq!(read.odd_cycles(&set(&[3, 4])), [0]);
    assert_eq!(read.odd_cycles(&set(&[0, 3, 4])), Vec::<usize>::new());
    assert_eq!(kite("[1, 0, 0, 1, 0]").odd_cycles(&set(&[])), [0, 1]);
    assert_eq!(
        kite("[1, 1, 0, 1, 1]").odd_cycles(&set(&[])),
        Vec::<usize>::new()
    );
    assert_eq!(kite("[0, 0, 0, 0, 1]").odd_cycles(&set(&[])), [1]);
}

#[test]
fn an_edge_on_no_cycle_never_makes_one_odd() {
    let tailed = labelled("[[0, 1], [1, 2], [2, 0], [2, 3]]", "[0, 0, 0, 1]");
    assert_eq!(tailed.odd_cycles(&set(&[])), Vec::<usize>::new());
    assert_eq!(tailed.odd_cycles(&set(&[3])), Vec::<usize>::new());
    assert_eq!(tailed.least_repair(), 0);
    let path = labelled("[[0, 1], [1, 2]]", "[1, 1]");
    assert_eq!(path.odd_cycles(&set(&[0])), Vec::<usize>::new());
    assert_eq!(path.least_repair(), 0);
}

#[test]
fn the_least_repair_is_the_size_of_the_smallest_set_that_leaves_no_cycle_odd() {
    assert_eq!(kite("[0, 0, 0, 0, 0]").least_repair(), 0);
    assert_eq!(kite("[1, 0, 0, 0, 0]").least_repair(), 1);
    assert_eq!(kite("[0, 0, 1, 0, 0]").least_repair(), 1);
    // Both triangles odd: the one shared edge mends both.
    assert_eq!(kite("[1, 0, 0, 1, 0]").least_repair(), 1);
    assert_eq!(kite("[1, 1, 1, 1, 1]").least_repair(), 1);
    assert_eq!(kite("[1, 1, 0, 1, 1]").least_repair(), 0);
    assert_eq!(labelled("[]", "[]").least_repair(), 0);
}

#[test]
fn the_least_repair_may_be_the_last_edge_alone() {
    // Both triangles are odd and share the last edge. Flipping it mends both; without it the
    // repair takes one flip in each triangle.
    let shared_last = labelled(
        "[[0, 1], [1, 2], [2, 3], [3, 0], [2, 0]]",
        "[0, 0, 0, 0, 1]",
    );
    assert_eq!(shared_last.odd_cycles(&set(&[])), [0, 1]);
    assert_eq!(shared_last.odd_cycles(&set(&[4])), Vec::<usize>::new());
    assert_eq!(shared_last.least_repair(), 1);
}

#[test]
fn cycles_that_share_no_edge_each_need_their_own_flip() {
    let apart = labelled(
        "[[0, 1], [1, 2], [2, 0], [3, 4], [4, 5], [5, 3]]",
        "[1, 0, 0, 0, 1, 0]",
    );
    assert_eq!(apart.odd_cycles(&set(&[])), [0, 1]);
    assert_eq!(apart.least_repair(), 2);
    let bowtie = labelled(
        "[[0, 1], [1, 2], [2, 0], [0, 3], [3, 4], [4, 0]]",
        "[1, 1, 1, 0, 0, 1]",
    );
    assert_eq!(bowtie.least_repair(), 2);
    let three = labelled("[[0, 0], [1, 1], [2, 2], [0, 1]]", "[1, 1, 1, 1]");
    assert_eq!(three.odd_cycles(&set(&[])), [0, 1, 2]);
    assert_eq!(three.least_repair(), 3);
}

#[test]
fn a_loop_and_a_doubled_edge_are_cycles_of_their_own() {
    let looped = labelled("[[0, 0]]", "[1]");
    assert_eq!(looped.odd_cycles(&set(&[])), [0]);
    assert_eq!(looped.odd_cycles(&set(&[0])), Vec::<usize>::new());
    assert_eq!(looped.least_repair(), 1);
    let doubled = labelled("[[0, 1], [0, 1]]", "[1, 0]");
    assert_eq!(doubled.odd_cycles(&set(&[])), [0]);
    assert_eq!(doubled.odd_cycles(&set(&[0, 1])), [0]);
    assert_eq!(doubled.least_repair(), 1);
    assert_eq!(labelled("[[0, 1], [0, 1]]", "[1, 1]").least_repair(), 0);
}

#[test]
fn the_least_repair_is_found_on_the_largest_task() {
    // Ten doubled edges in a row, every pair odd: one flip per pair.
    let pairs: Vec<String> = (0..10)
        .flat_map(|at| [format!("[{at}, {}]", at + 1), format!("[{at}, {}]", at + 1)])
        .collect();
    let labels: Vec<&str> = (0..20)
        .map(|at| if at % 2 == 0 { "1" } else { "0" })
        .collect();
    let chain = labelled(
        &format!("[{}]", pairs.join(", ")),
        &format!("[{}]", labels.join(", ")),
    );
    assert_eq!(chain.odd_cycles(&set(&[])).len(), 10);
    assert_eq!(chain.least_repair(), 10);
    assert_eq!(chain.odd_cycles(&set(&[19])), [0, 1, 2, 3, 4, 5, 6, 7, 8]);
}

#[test]
fn a_reply_is_accepted_only_when_no_cycle_is_odd_and_no_smaller_repair_exists() {
    let read = kite("[1, 0, 0, 0, 0]");
    let finding = |reply: &str| read.assess(&datum(reply)).expect("a finding");
    let good = finding(r#"{"flip": [0]}"#);
    assert!(good.accepted);
    assert_eq!(good.measure, datum("0"));
    assert_eq!(
        good.residual.canonical(),
        r#"{"flip_count":1,"minimal_known":true,"odd_cycles":[]}"#
    );
    assert!(finding(r#"{"flip": [1]}"#).accepted);
    assert!(finding(r#"{"flip": [1, 1]}"#).accepted);
    let moved = finding(r#"{"flip": [2]}"#);
    assert!(!moved.accepted);
    assert_eq!(moved.measure, datum("1"));
    assert_eq!(
        moved.residual.canonical(),
        r#"{"flip_count":1,"minimal_known":false,"odd_cycles":[1]}"#
    );
    // Every cycle even, with three flips where one would do.
    let wasteful = finding(r#"{"flip": [0, 3, 4]}"#);
    assert!(!wasteful.accepted);
    assert_eq!(wasteful.measure, datum("0"));
    assert_eq!(
        wasteful.residual.canonical(),
        r#"{"flip_count":3,"minimal_known":true,"odd_cycles":[]}"#
    );
    let nothing = finding(r#"{"flip": []}"#);
    assert!(!nothing.accepted);
    assert_eq!(
        nothing.residual.canonical(),
        r#"{"flip_count":0,"minimal_known":false,"odd_cycles":[0]}"#
    );
    let worse = finding(r#"{"flip": [3]}"#);
    assert_eq!(worse.measure, datum("2"));
}

#[test]
fn the_empty_repair_is_accepted_only_when_nothing_is_odd() {
    let even = kite("[1, 1, 0, 1, 1]");
    assert!(
        even.assess(&datum(r#"{"flip": []}"#))
            .expect("finding")
            .accepted
    );
    // Two flips that keep every cycle even are not the least repair of an even graph.
    assert!(
        !even
            .assess(&datum(r#"{"flip": [0, 1]}"#))
            .expect("finding")
            .accepted
    );
    let empty = labelled("[]", "[]");
    assert!(
        empty
            .assess(&datum(r#"{"flip": []}"#))
            .expect("finding")
            .accepted
    );
}

#[test]
fn a_reply_without_a_readable_flip_list_is_an_error_with_the_reason() {
    let read = kite("[1, 0, 0, 0, 0]");
    let error = |reply: &str| read.assess(&datum(reply)).expect_err("an error");
    assert_eq!(error("{}"), "flip list required");
    assert_eq!(error(r#""flip""#), "flip list required");
    assert_eq!(error("[0]"), "flip list required");
    assert_eq!(error("null"), "flip list required");
    assert_eq!(error(r#"{"flip": ["0"]}"#), "flip must be an exact int");
    assert_eq!(error(r#"{"flip": [5]}"#), "flip index out of range");
    assert!(read.assess(&datum(r#"{"flip": [4]}"#)).is_ok());
}
