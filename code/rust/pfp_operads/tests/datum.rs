//! Exact JSON: what is read, what is refused, and the one text each value has.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:datum-tests:v1

use num_bigint::BigInt;
use pfp_operads::datum::{Datum, MAX_DEPTH};
use pfp_operads::Refusal;
use serde_json::json;

fn parse(text: &str) -> Datum {
    Datum::parse(text).expect("the text is JSON")
}

fn refusal(text: &str) -> Refusal {
    Datum::parse(text).expect_err("the text is refused")
}

fn int(digits: &str) -> Datum {
    Datum::Int(digits.parse::<BigInt>().expect("digits"))
}

fn nested(depth: usize) -> String {
    format!("{}{}", "[".repeat(depth), "]".repeat(depth))
}

#[test]
fn scalars_are_read_as_what_they_are() {
    assert_eq!(parse("null"), Datum::Null);
    assert_eq!(parse("true"), Datum::Bool(true));
    assert_eq!(parse("false"), Datum::Bool(false));
    assert_eq!(
        parse("\"a\\u00e9\\n\""),
        Datum::Text("a\u{e9}\n".to_owned())
    );
    assert_eq!(parse(" 7 "), int("7"));
    assert_eq!(parse("-7"), int("-7"));
    assert_eq!(parse("-0"), int("0"));
}

#[test]
fn an_integer_is_read_from_its_digits_at_any_size() {
    let digits = "123456789012345678901234567890123456789012345678901234567890";
    assert_eq!(parse(digits), int(digits));
    assert_eq!(parse(digits).canonical(), digits);
    assert_eq!(
        parse(&format!("-{digits}")).canonical(),
        format!("-{digits}")
    );
}

#[test]
fn a_number_with_a_fraction_or_an_exponent_is_kept_as_written_and_is_no_integer() {
    for written in ["1.0", "1e3", "-2.5E-3", "0.5"] {
        let value = parse(written);
        assert_eq!(value, Datum::Decimal(written.to_owned()));
        assert_eq!(value.as_int(), None);
        assert_eq!(value.as_count(), None);
        assert_eq!(value.canonical(), written);
    }
}

#[test]
fn lists_and_objects_are_read_in_full() {
    let value = parse(r#"{"b": [1, "x", null, {"c": false}], "a": 2}"#);
    assert_eq!(
        value,
        Datum::map([
            ("a", int("2")),
            (
                "b",
                Datum::List(vec![
                    int("1"),
                    Datum::text("x"),
                    Datum::Null,
                    Datum::map([("c", Datum::Bool(false))]),
                ])
            ),
        ])
    );
}

#[test]
fn a_key_that_appears_twice_is_refused_by_name() {
    assert_eq!(
        refusal(r#"{"a": 1, "b": 2, "a": 3}"#),
        Refusal::new("BAD_JSON", "the key a appears twice in one object")
    );
    assert_eq!(
        refusal(r#"[{"k": {"z": 1, "z": 1}}]"#).message,
        "the key z appears twice in one object"
    );
}

#[test]
fn nesting_is_read_to_the_limit_and_refused_one_past_it() {
    assert_eq!(MAX_DEPTH, 64);
    assert!(Datum::parse(&nested(MAX_DEPTH + 1)).is_ok());
    assert_eq!(
        refusal(&nested(MAX_DEPTH + 2)),
        Refusal::new("BAD_JSON", "nesting deeper than 64")
    );
    let objects = format!("{}1{}", "{\"k\":".repeat(MAX_DEPTH), "}".repeat(MAX_DEPTH));
    assert!(Datum::parse(&objects).is_ok());
    let deeper = format!(
        "{}1{}",
        "{\"k\":".repeat(MAX_DEPTH + 1),
        "}".repeat(MAX_DEPTH + 1)
    );
    assert_eq!(refusal(&deeper).message, "nesting deeper than 64");
}

#[test]
fn text_that_is_not_one_json_value_is_refused() {
    for text in [
        "", "{", "[1,]", "1 2", "nul", "NaN", "Infinity", "{\"a\":}", "01", "'a'",
    ] {
        assert_eq!(refusal(text).code, "BAD_JSON", "{text}");
    }
    assert!(refusal("[1,]").message.contains("line 1 column 4"));
}

#[test]
fn the_canonical_text_sorts_keys_by_code_point_and_has_no_spaces() {
    let value = parse(r#"{ "b" : [ 1 , 2 ] , "a" : { "z" : null , "B" : true } , "é" : "x" }"#);
    assert_eq!(
        value.canonical(),
        "{\"a\":{\"B\":true,\"z\":null},\"b\":[1,2],\"\u{e9}\":\"x\"}"
    );
    assert_eq!(parse("[]").canonical(), "[]");
    assert_eq!(parse("{}").canonical(), "{}");
    assert_eq!(parse("[false]").canonical(), "[false]");
}

#[test]
fn the_canonical_text_escapes_only_what_json_requires() {
    let text = Datum::text("q\" b\\ n\n r\r t\t b\u{8} f\u{c} u\u{1} v\u{1f} d\u{7f} e\u{e9} s/");
    assert_eq!(
        text.canonical(),
        "\"q\\\" b\\\\ n\\n r\\r t\\t b\\b f\\f u\\u0001 v\\u001f d\u{7f} e\u{e9} s/\""
    );
    assert_eq!(Datum::text(" ").canonical(), "\" \"");
    let key = Datum::map([("a\"b", Datum::Null)]);
    assert_eq!(key.canonical(), "{\"a\\\"b\":null}");
}

#[test]
fn the_canonical_text_reads_back_as_the_same_value() {
    let value = parse(r#"{"k": ["a\u0001\"\\", -12, 1.50, true, null, {"x": []}]}"#);
    assert_eq!(parse(&value.canonical()), value);
}

#[test]
fn accessors_answer_only_for_their_own_kind() {
    let value = parse(r#"{"list": [1], "int": 5, "text": "t", "neg": -1}"#);
    assert!(value.is_map());
    assert!(!parse("[]").is_map());
    assert_eq!(value.get("int"), Some(&int("5")));
    assert_eq!(value.get("absent"), None);
    assert_eq!(parse("[1]").get("0"), None);
    assert_eq!(
        value.get("list").and_then(Datum::as_list),
        Some(&[int("1")][..])
    );
    assert_eq!(value.get("int").and_then(Datum::as_list), None);
    assert_eq!(value.get("text").and_then(Datum::as_text), Some("t"));
    assert_eq!(value.get("int").and_then(Datum::as_text), None);
    assert_eq!(
        value.get("int").and_then(Datum::as_int),
        Some(&BigInt::from(5))
    );
    assert_eq!(value.get("text").and_then(Datum::as_int), None);
}

#[test]
fn a_count_is_an_integer_from_zero_to_the_machine_limit() {
    assert_eq!(parse("0").as_count(), Some(0));
    assert_eq!(parse("17").as_count(), Some(17));
    assert_eq!(parse("-1").as_count(), None);
    assert_eq!(parse("\"3\"").as_count(), None);
    assert_eq!(parse("true").as_count(), None);
    assert_eq!(
        parse("340282366920938463463374607431768211456").as_count(),
        None
    );
}

#[test]
fn an_outcome_value_keeps_every_integer_exact() {
    let value = parse(
        r#"{"small": -9223372036854775808, "big": 18446744073709551615,
            "over": 18446744073709551616, "under": -9223372036854775809,
            "decimal": 2.50, "rest": [null, true, "t", {"k": 1}]}"#,
    );
    assert_eq!(
        value.to_json(),
        json!({
            "small": i64::MIN,
            "big": u64::MAX,
            "over": "18446744073709551616",
            "under": "-9223372036854775809",
            "decimal": "2.50",
            "rest": [null, true, "t", {"k": 1}],
        })
    );
}

#[test]
fn values_are_built_from_plain_rust_values() {
    assert_eq!(Datum::from(3usize), int("3"));
    assert_eq!(Datum::from(-3i64), int("-3"));
    assert_eq!(Datum::from(BigInt::from(9)), int("9"));
    assert_eq!(Datum::from("t"), Datum::Text("t".to_owned()));
    assert_eq!(Datum::text(String::from("t")), Datum::Text("t".to_owned()));
    assert_eq!(
        Datum::from(vec![1usize, 2]),
        Datum::List(vec![int("1"), int("2")])
    );
    assert_eq!(Datum::from(vec!["a"]).canonical(), "[\"a\"]");
}

#[test]
fn a_later_entry_replaces_an_earlier_one_when_a_map_is_built() {
    let map = Datum::map([("k", int("1")), ("j", int("2")), ("k", int("3"))]);
    assert_eq!(map.canonical(), "{\"j\":2,\"k\":3}");
    assert_eq!(Datum::map([]).canonical(), "{}");
}
