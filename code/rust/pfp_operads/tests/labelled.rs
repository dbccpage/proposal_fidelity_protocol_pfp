//! Task graphs with text vertex names: reading the edges, and reading a value on the vertices
//! from an object keyed by name.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-labelled-tests:v1

use num_bigint::BigInt;
use pfp_operads::datum::Datum;
use pfp_operads::exact::Rational;
use pfp_operads::families::labelled::{read, Labelled};

fn datum(text: &str) -> Datum {
    Datum::parse(text).expect("a datum")
}

fn graph(text: &str) -> Labelled {
    read(&datum(text)).expect("a graph")
}

fn ratio(top: i64, bottom: i64) -> Rational {
    Rational::new(BigInt::from(top), BigInt::from(bottom))
}

/// Three vertices first named in the order b, a, c.
fn triangle() -> Labelled {
    graph(r#"[["b","a"],["a","c"],["b","c"]]"#)
}

#[test]
fn vertices_are_numbered_in_the_order_the_edges_first_name_them() {
    let triangle = triangle();
    assert_eq!(triangle.names(), ["b", "a", "c"]);
    assert_eq!(triangle.graph.edges(), [(0, 1), (1, 2), (0, 2)]);
}

#[test]
fn loops_and_repeated_edges_are_kept_as_written() {
    let doubled = graph(r#"[["a","a"],["a","b"],["a","b"],["b","a"]]"#);
    assert_eq!(doubled.names(), ["a", "b"]);
    assert_eq!(doubled.graph.edges(), [(0, 0), (0, 1), (0, 1), (1, 0)]);
}

#[test]
fn an_empty_list_is_the_graph_with_no_vertices() {
    let empty = graph("[]");
    assert!(empty.names().is_empty());
    assert!(empty.graph.edges().is_empty());
    assert!(empty.covers(&datum("{}")));
    assert_eq!(empty.potential(&datum("{}")), Some(Vec::new()));
}

#[test]
fn edges_that_are_not_pairs_of_text_are_not_a_graph() {
    for written in [
        r#"{"a":"b"}"#,
        r#""ab""#,
        "null",
        r#"[["a"]]"#,
        r#"[["a","b","c"]]"#,
        r#"[["a","b"],"ab"]"#,
        r#"[["a",1]]"#,
        r#"[[0,"b"]]"#,
        r#"[["a",null]]"#,
        "[[0,1]]",
    ] {
        assert_eq!(read(&datum(written)), None, "{written}");
    }
}

#[test]
fn a_value_covers_the_graph_when_its_keys_are_exactly_the_vertex_names() {
    let triangle = triangle();
    assert!(triangle.covers(&datum(r#"{"a":1,"b":"x","c":null}"#)));
    for written in [
        r#"{"a":1,"b":2}"#,
        r#"{"a":1,"b":2,"c":3,"d":4}"#,
        r#"{"a":1,"b":2,"d":3}"#,
        r#"["b","a","c"]"#,
        r#""bac""#,
        "null",
        "{}",
    ] {
        assert!(!triangle.covers(&datum(written)), "{written}");
    }
}

#[test]
fn a_potential_is_read_by_name_into_vertex_order() {
    let triangle = triangle();
    assert_eq!(
        triangle.potential(&datum(r#"{"a":"1/2","b":-3,"c":"4/6"}"#)),
        Some(vec![ratio(-3, 1), ratio(1, 2), ratio(2, 3)])
    );
    // Entries under other keys are not looked at.
    assert_eq!(
        triangle.potential(&datum(r#"{"a":1,"b":2,"c":3,"zz":"x"}"#)),
        Some(vec![ratio(2, 1), ratio(1, 1), ratio(3, 1)])
    );
}

#[test]
fn a_potential_with_a_missing_or_unreadable_entry_is_nothing() {
    let triangle = triangle();
    for written in [
        r#"{"a":1,"b":2}"#,
        r#"{"a":1,"b":2,"c":"x"}"#,
        r#"{"a":1,"b":2,"c":1.5}"#,
        r#"{"a":1,"b":2,"c":null}"#,
        "[1,2,3]",
        "null",
    ] {
        assert_eq!(triangle.potential(&datum(written)), None, "{written}");
    }
}

#[test]
fn any_reading_of_the_entries_comes_back_in_vertex_order() {
    let triangle = triangle();
    let listed = datum(r#"{"a":"x","b":"y","c":"z","d":"w"}"#);
    let text = |entry: &Datum| entry.as_text().map(str::to_owned);
    assert_eq!(
        triangle.by_name(&listed, text),
        Some(vec!["y".to_owned(), "x".to_owned(), "z".to_owned()])
    );
    let mixed = datum(r#"{"a":"x","b":2,"c":"z"}"#);
    assert_eq!(triangle.by_name(&mixed, text), None);
    let count = |entry: &Datum| entry.as_count();
    assert_eq!(triangle.by_name(&mixed, count), None);
    assert_eq!(
        triangle.by_name(&datum(r#"{"a":4,"b":2,"c":0}"#), count),
        Some(vec![2, 4, 0])
    );
}
