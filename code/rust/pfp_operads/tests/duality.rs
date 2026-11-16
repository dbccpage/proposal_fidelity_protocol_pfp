//! The weighted-digraph duality grader that WF18 and WF35 share: feasible potentials, negative
//! cycles, and the pin of the grader's own source.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-duality-tests:v1

use pfp_operads::datum::Datum;
use pfp_operads::families::duality::{grade, pin, Grade, Item};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn item(value: &Value) -> Item {
    let datum = Datum::parse(&value.to_string()).expect("a datum");
    Item::read(&datum).expect("an item")
}

fn bad_item(value: &Value) -> String {
    let datum = Datum::parse(&value.to_string()).expect("a datum");
    Item::read(&datum).expect_err("a refused item")
}

fn graded(item: &Item, reply: &Value) -> Grade {
    grade(item, &reply.to_string())
}

fn feasible() -> Item {
    item(&json!({"n": 3, "edges": [[0, 1, 2], [1, 2, -1], [0, 2, 3], [2, 0, 1]]}))
}

fn negative() -> Item {
    item(&json!({"n": 3, "edges": [[0, 1, 1], [1, 2, -3], [2, 0, 1]]}))
}

#[test]
fn a_potential_that_holds_on_every_edge_is_certified() {
    let item = feasible();
    assert_eq!(
        graded(&item, &json!({"potential": [0, 2, 1]})),
        Grade::Certified
    );
    assert_eq!(
        graded(&item, &json!({"potential": [5, 7, 6]})),
        Grade::Certified
    );
}

#[test]
fn a_potential_that_breaks_one_edge_is_refused() {
    let item = feasible();
    assert_eq!(
        graded(&item, &json!({"potential": [0, 0, 0]})),
        Grade::Refused
    );
    assert_eq!(
        graded(&item, &json!({"potential": [0, 3, 1]})),
        Grade::Refused
    );
    assert_eq!(
        graded(&item, &json!({"potential": [0, 2, 2]})),
        Grade::Refused
    );
    assert_eq!(
        graded(&item, &json!({"potential": [0, 2, 3]})),
        Grade::Refused
    );
}

#[test]
fn an_edge_that_holds_with_equality_holds() {
    let item = item(&json!({"n": 2, "edges": [[0, 1, 4]]}));
    assert_eq!(
        graded(&item, &json!({"potential": [0, 4]})),
        Grade::Certified
    );
    assert_eq!(graded(&item, &json!({"potential": [0, 5]})), Grade::Refused);
    assert_eq!(
        graded(&item, &json!({"potential": [1, 5]})),
        Grade::Certified
    );
}

#[test]
fn the_edge_runs_from_its_first_end_to_its_second() {
    let item = item(&json!({"n": 2, "edges": [[0, 1, -4]]}));
    assert_eq!(
        graded(&item, &json!({"potential": [0, -4]})),
        Grade::Certified
    );
    assert_eq!(
        graded(&item, &json!({"potential": [-4, 0]})),
        Grade::Refused
    );
}

#[test]
fn a_negative_closed_walk_is_a_typed_refusal() {
    let item = negative();
    assert_eq!(
        graded(&item, &json!({"negative_cycle": [0, 1, 2]})),
        Grade::TypedRefusal
    );
    assert_eq!(
        graded(&item, &json!({"negative_cycle": [1, 2, 0]})),
        Grade::TypedRefusal
    );
    assert_eq!(
        graded(&item, &json!({"negative_cycle": [2, 0, 1]})),
        Grade::TypedRefusal
    );
}

#[test]
fn a_closed_walk_that_does_not_add_up_to_less_than_zero_is_refused() {
    let zero = item(&json!({"n": 2, "edges": [[0, 1, 2], [1, 0, -2]]}));
    assert_eq!(
        graded(&zero, &json!({"negative_cycle": [0, 1]})),
        Grade::Refused
    );
    let positive = item(&json!({"n": 2, "edges": [[0, 1, 1], [1, 0, 1]]}));
    assert_eq!(
        graded(&positive, &json!({"negative_cycle": [0, 1]})),
        Grade::Refused
    );
}

#[test]
fn a_walk_must_follow_edges_and_close() {
    let item = negative();
    assert_eq!(
        graded(&item, &json!({"negative_cycle": [0, 1]})),
        Grade::Refused
    );
    assert_eq!(
        graded(&item, &json!({"negative_cycle": [0, 2, 1]})),
        Grade::Refused
    );
    assert_eq!(
        graded(&item, &json!({"negative_cycle": [0, 0]})),
        Grade::Refused
    );
    assert_eq!(
        graded(&item, &json!({"negative_cycle": [0, 1, 2, 0]})),
        Grade::Refused
    );
    assert_eq!(
        graded(&item, &json!({"negative_cycle": [7, 8]})),
        Grade::Refused
    );
}

#[test]
fn a_walk_goes_round_the_cycle_more_than_once() {
    let item = negative();
    let twice = json!({"negative_cycle": [0, 1, 2, 0, 1, 2]});
    assert_eq!(graded(&item, &twice), Grade::TypedRefusal);
}

#[test]
fn a_walk_of_one_vertex_or_a_walk_that_is_not_integers_is_refused() {
    let item = negative();
    for reply in [
        json!({"negative_cycle": []}),
        json!({"negative_cycle": [0]}),
        json!({"negative_cycle": [0, 1, 2.0]}),
        json!({"negative_cycle": [0, 1, "2"]}),
        json!({"negative_cycle": [0, 1, true]}),
        json!({"negative_cycle": [0, 1, null]}),
        json!({"negative_cycle": "0 1 2"}),
        json!({"negative_cycle": {"0": 1}}),
    ] {
        assert_eq!(graded(&item, &reply), Grade::Refused, "{reply}");
    }
}

#[test]
fn a_walk_of_one_vertex_is_refused_even_on_a_negative_self_loop() {
    let item = item(&json!({"n": 1, "edges": [[0, 0, -1]]}));
    let twice = json!({"negative_cycle": [0, 0]});
    assert_eq!(graded(&item, &twice), Grade::TypedRefusal);
    let once = json!({"negative_cycle": [0]});
    assert_eq!(graded(&item, &once), Grade::Refused);
}

#[test]
fn a_walk_with_one_entry_that_is_not_an_integer_is_refused_whole() {
    let item = negative();
    for stray in [json!(null), json!(true), json!("x"), json!(1.5), json!([1])] {
        let walk = json!({"negative_cycle": [0, stray, 1, 2]});
        assert_eq!(graded(&item, &walk), Grade::Refused, "{walk}");
    }
}

#[test]
fn a_walk_takes_the_lightest_of_parallel_edges() {
    let item = item(&json!({"n": 2, "edges": [[0, 1, 5], [0, 1, -10], [0, 1, 7], [1, 0, 3]]}));
    assert_eq!(
        graded(&item, &json!({"negative_cycle": [0, 1]})),
        Grade::TypedRefusal
    );
    let heavy = self::item(&json!({"n": 2, "edges": [[0, 1, 5], [0, 1, 7], [1, 0, 3]]}));
    assert_eq!(
        graded(&heavy, &json!({"negative_cycle": [0, 1]})),
        Grade::Refused
    );
}

#[test]
fn a_potential_must_hold_on_every_one_of_parallel_edges() {
    let item = item(&json!({"n": 2, "edges": [[0, 1, -10], [0, 1, 5]]}));
    assert_eq!(graded(&item, &json!({"potential": [0, 5]})), Grade::Refused);
    assert_eq!(
        graded(&item, &json!({"potential": [0, -10]})),
        Grade::Certified
    );
    let later = self::item(&json!({"n": 2, "edges": [[0, 1, 5], [0, 1, -10]]}));
    assert_eq!(
        graded(&later, &json!({"potential": [0, 5]})),
        Grade::Refused
    );
}

#[test]
fn a_potential_of_another_length_is_read_as_a_walk_would_be() {
    let item = negative();
    let both = json!({"potential": [0], "negative_cycle": [0, 1, 2]});
    assert_eq!(graded(&item, &both), Grade::TypedRefusal);
    let none = json!({"potential": [0, 0, 0, 0]});
    assert_eq!(graded(&item, &none), Grade::Refused);
}

#[test]
fn a_potential_of_the_right_length_is_graded_even_when_a_walk_comes_with_it() {
    let item = negative();
    let both = json!({"potential": [0, 0, 0], "negative_cycle": [0, 1, 2]});
    assert_eq!(graded(&item, &both), Grade::Refused);
    let fine = feasible();
    let both = json!({"potential": [0, 2, 1], "negative_cycle": [0, 1, 2]});
    assert_eq!(graded(&fine, &both), Grade::Certified);
}

#[test]
fn a_potential_entry_that_is_not_an_exact_rational_refuses_the_reply() {
    let item = feasible();
    for reply in [
        json!({"potential": [0, 2.0, 1]}),
        json!({"potential": [0, "2.0", 1]}),
        json!({"potential": [0, "1e1", 1]}),
        json!({"potential": [0, "+2", 1]}),
        json!({"potential": [0, " 2", 1]}),
        json!({"potential": [0, "2/0", 1]}),
        json!({"potential": [0, true, 1]}),
        json!({"potential": [0, null, 1]}),
        json!({"potential": [0, [2], 1]}),
    ] {
        assert_eq!(graded(&item, &reply), Grade::Refused, "{reply}");
    }
    let walk = json!({"potential": [0, 2.0, 1], "negative_cycle": [0, 1, 2]});
    assert_eq!(graded(&negative(), &walk), Grade::Refused);
}

#[test]
fn rationals_are_written_as_integers_or_as_p_over_q() {
    let item = item(&json!({"n": 2, "edges": [[0, 1, "1/2"]]}));
    assert_eq!(
        graded(&item, &json!({"potential": [0, "1/2"]})),
        Grade::Certified
    );
    assert_eq!(
        graded(&item, &json!({"potential": ["0", "2/4"]})),
        Grade::Certified
    );
    assert_eq!(
        graded(&item, &json!({"potential": [0, "3/4"]})),
        Grade::Refused
    );
    assert_eq!(
        graded(&item, &json!({"potential": ["-1/3", "1/6"]})),
        Grade::Certified
    );
    assert_eq!(
        graded(&item, &json!({"potential": ["-1/3", "1/5"]})),
        Grade::Refused
    );
}

#[test]
fn a_walk_adds_up_rational_weights() {
    let item = item(&json!({"n": 2, "edges": [[0, 1, "1/3"], [1, 0, "-1/2"]]}));
    assert_eq!(
        graded(&item, &json!({"negative_cycle": [0, 1]})),
        Grade::TypedRefusal
    );
    let tied = self::item(&json!({"n": 2, "edges": [[0, 1, "1/2"], [1, 0, "-1/2"]]}));
    assert_eq!(
        graded(&tied, &json!({"negative_cycle": [0, 1]})),
        Grade::Refused
    );
}

#[test]
fn an_edge_end_that_is_not_a_vertex_refuses_the_potential() {
    let high = item(&json!({"n": 2, "edges": [[0, 5, 1]]}));
    assert_eq!(graded(&high, &json!({"potential": [0, 0]})), Grade::Refused);
    let low = item(&json!({"n": 2, "edges": [[-1, 0, 5]]}));
    assert_eq!(graded(&low, &json!({"potential": [0, 0]})), Grade::Refused);
    let edge = item(&json!({"n": 2, "edges": [[0, 1, 1], [2, 0, 5]]}));
    assert_eq!(graded(&edge, &json!({"potential": [0, 0]})), Grade::Refused);
    let top = item(&json!({"n": 2, "edges": [[1, 1, 0]]}));
    assert_eq!(
        graded(&top, &json!({"potential": [0, 0]})),
        Grade::Certified
    );
}

#[test]
fn a_graph_with_no_vertices_and_no_edges_has_the_empty_potential() {
    let empty = item(&json!({"n": 0, "edges": []}));
    assert_eq!(graded(&empty, &json!({"potential": []})), Grade::Certified);
    assert_eq!(graded(&empty, &json!({"potential": [0]})), Grade::Refused);
    let edgeless = item(&json!({"n": 2, "edges": []}));
    assert_eq!(
        graded(&edgeless, &json!({"potential": [3, 9]})),
        Grade::Certified
    );
}

#[test]
fn the_number_of_vertices_may_be_of_any_size() {
    let read = |text: &str| Item::read(&Datum::parse(text).expect("a datum")).expect("an item");
    let huge = read("{\"n\": 100000000000000000000000000000, \"edges\": []}");
    assert_eq!(graded(&huge, &json!({"potential": []})), Grade::Refused);
    let negative = read("{\"n\": -1, \"edges\": []}");
    assert_eq!(graded(&negative, &json!({"potential": []})), Grade::Refused);
    let big = read("{\"n\": 2, \"edges\": [[0, 1, 100000000000000000000000000000]]}");
    assert_eq!(
        grade(&big, "{\"potential\": [0, 100000000000000000000000000000]}"),
        Grade::Certified
    );
    assert_eq!(
        grade(&big, "{\"potential\": [0, 100000000000000000000000000001]}"),
        Grade::Refused
    );
}

#[test]
fn text_that_is_not_one_json_object_is_refused() {
    let item = feasible();
    for raw in [
        "",
        "not json",
        "[0, 2, 1]",
        "\"potential\"",
        "3",
        "null",
        "{\"potential\": [0, 2, 1]",
        "{\"potential\": [0, 2, 1], \"potential\": [0, 0, 0]}",
        "{\"potential\": [0, 2, 1], \"note\": NaN}",
    ] {
        assert_eq!(grade(&item, raw), Grade::Refused, "{raw}");
    }
    assert_eq!(grade(&item, "{\"potential\": [0, 2, 1]}"), Grade::Certified);
    assert_eq!(
        grade(&item, " {\"potential\": [0, 2, 1], \"note\": \"x\"} "),
        Grade::Certified
    );
}

#[test]
fn an_object_with_neither_answer_is_refused() {
    let item = feasible();
    assert_eq!(graded(&item, &json!({})), Grade::Refused);
    assert_eq!(graded(&item, &json!({"answer": [0, 2, 1]})), Grade::Refused);
    assert_eq!(
        graded(&item, &json!({"potential": "0 2 1"})),
        Grade::Refused
    );
}

#[test]
fn an_item_states_an_integer_n_and_a_list_of_edges() {
    let cases = [
        (json!({"edges": []}), "n must be an exact integer"),
        (json!({"n": 2.0, "edges": []}), "n must be an exact integer"),
        (json!({"n": "2", "edges": []}), "n must be an exact integer"),
        (
            json!({"n": true, "edges": []}),
            "n must be an exact integer",
        ),
        (json!({"n": 2}), "edges must be a list"),
        (json!({"n": 2, "edges": "none"}), "edges must be a list"),
        (json!([1, 2]), "n must be an exact integer"),
    ];
    for (value, reason) in cases {
        assert_eq!(bad_item(&value), reason, "{value}");
    }
}

#[test]
fn an_edge_is_two_integer_ends_and_an_exact_rational_weight() {
    let reason = "an edge is two integer ends and an exact rational weight";
    for edge in [
        json!([0, 1]),
        json!([0, 1, 2, 3]),
        json!([0.0, 1, 2]),
        json!(["0", 1, 2]),
        json!([0, true, 2]),
        json!([0, 1, 2.5]),
        json!([0, 1, "2.5"]),
        json!([0, 1, null]),
        json!({"from": 0}),
        json!("0 1 2"),
    ] {
        let value = json!({"n": 2, "edges": [[0, 1, 1], edge]});
        assert_eq!(bad_item(&value), reason, "{edge}");
    }
}

#[test]
fn the_grades_are_named_as_the_stored_dossiers_name_them() {
    assert_eq!(Grade::Certified.name(), "HOST_CERTIFIED");
    assert_eq!(Grade::TypedRefusal.name(), "TYPED_REFUSAL");
    assert_eq!(Grade::Refused.name(), "REFUSED");
    assert!(Grade::Certified.stands());
    assert!(Grade::TypedRefusal.stands());
    assert!(!Grade::Refused.stands());
}

#[test]
fn the_pin_is_the_digest_of_the_graders_source_with_unix_line_endings() {
    let path = concat!(env!("CARGO_MANIFEST_DIR"), "/src/families/duality.rs");
    let text = std::fs::read_to_string(path).expect("the grader's source");
    let unix = text.replace("\r\n", "\n").replace('\r', "\n");
    assert_eq!(pin(), hex::encode(Sha256::digest(unix.as_bytes())));
    assert_eq!(pin().len(), 64);
    assert!(pin().bytes().all(|byte| byte.is_ascii_hexdigit()));
    assert!(text.contains("urn:pfp-operads:families-duality:v1"));
}
