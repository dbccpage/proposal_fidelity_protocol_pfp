//! The sealed-value guard: which sealed values count, and where in a prompt they are a leak.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-sealed-tests:v1

use pfp_operads::datum::Datum;
use pfp_operads::families::sealed::{Guard, ANSWER_KEYS, SUBSTRING_LENGTH};

fn guard(sealed: &str) -> Guard {
    Guard::new(&Datum::parse(sealed).expect("sealed JSON"))
}

fn leaks(sealed: &str, prompt: &str) -> bool {
    guard(sealed).leaks(prompt)
}

#[test]
fn a_sealed_value_of_four_or_more_characters_is_a_leak_anywhere() {
    assert_eq!(SUBSTRING_LENGTH, 4);
    assert!(leaks(r#"{"note": 98765}"#, "the code is 98765."));
    assert!(leaks(r#"{"note": 98765}"#, "x9876543"));
    assert!(leaks(r#"{"note": "abcd"}"#, "xxabcdxx"));
    assert!(leaks(r#"{"note": -123}"#, "value-123"));
    assert!(!leaks(r#"{"note": 98765}"#, "the code is 9876."));
    assert!(!leaks(r#"{"note": "abcd"}"#, "ab cd"));
}

#[test]
fn a_shorter_sealed_value_outside_an_answer_key_is_not_guarded() {
    assert!(!leaks(r#"{"note": 987}"#, "the code is 987"));
    assert!(!leaks(r#"{"note": "abc"}"#, "abc"));
    assert!(!leaks(r#"{"note": -12}"#, "-12"));
}

#[test]
fn length_is_counted_in_characters() {
    assert!(!leaks(r#"{"note": "ééé"}"#, "ééé"));
    assert!(leaks(r#"{"note": "éééé"}"#, "xééééx"));
}

#[test]
fn a_value_under_an_answer_key_is_a_leak_as_a_whole_word_at_any_length() {
    assert!(leaks(r#"{"answer": 42}"#, "the answer is 42"));
    assert!(leaks(r#"{"answer": 42}"#, "42"));
    assert!(leaks(r#"{"answer": "x"}"#, "pick x now"));
    assert!(!leaks(r#"{"answer": 42}"#, "the answer is 421"));
    assert!(!leaks(r#"{"answer": 42}"#, "1420"));
    assert!(!leaks(r#"{"answer": 42}"#, "a42"));
}

#[test]
fn every_break_character_and_white_space_ends_a_word() {
    for edge in [
        ",", ":", ";", "[", "]", "{", "}", "(", ")", "\"", "'", " ", "\n", "\t",
    ] {
        assert!(
            leaks(r#"{"answer": 42}"#, &format!("a{edge}42{edge}b")),
            "{edge:?}"
        );
    }
    for edge in [".", "-", "=", "/", "_", "!"] {
        assert!(
            !leaks(r#"{"answer": 42}"#, &format!("a{edge}42{edge}b")),
            "{edge:?}"
        );
    }
}

#[test]
fn each_answer_key_is_recognised_in_any_case() {
    assert_eq!(
        ANSWER_KEYS,
        [
            "answer",
            "answers",
            "expected",
            "expected_answer",
            "solution",
            "key",
            "answer_key"
        ]
    );
    for key in ANSWER_KEYS {
        let sealed = format!(r#"{{"{key}": 7}}"#);
        assert!(leaks(&sealed, "is it 7 ?"), "{key}");
        let upper = format!(r#"{{"{}": 7}}"#, key.to_uppercase());
        assert!(leaks(&upper, "is it 7 ?"), "{key}");
    }
    assert!(!leaks(r#"{"answered": 7}"#, "is it 7 ?"));
    assert!(!leaks(r#"{"the_answer": 7}"#, "is it 7 ?"));
}

#[test]
fn everything_inside_an_answer_key_is_an_answer() {
    assert!(leaks(r#"{"answer": [1, {"deep": [9]}]}"#, "try 9"));
    assert!(leaks(r#"{"answer": [1, {"deep": [9]}]}"#, "try 1"));
    assert!(leaks(r#"{"outer": {"solution": {"x": 5}}}"#, "x is 5"));
    assert!(leaks(r#"{"list": [{"key": 3}]}"#, "3"));
    assert!(!leaks(
        r#"{"outer": {"solution": {"x": 5}}, "y": 6}"#,
        "y is 6"
    ));
    assert!(!leaks(r#"{"list": [{"key": 3}, 8]}"#, "8"));
}

#[test]
fn a_long_value_is_guarded_both_ways_under_an_answer_key() {
    assert!(leaks(r#"{"answer": 12345}"#, "x12345x"));
    assert!(leaks(r#"{"list": [12345]}"#, "x12345x"));
    assert!(leaks(r#"{"deep": {"er": ["wxyz"]}}"#, "awxyzb"));
}

#[test]
fn booleans_null_and_empty_text_are_not_guarded() {
    assert!(!leaks(r#"{"answer": true}"#, "true"));
    assert!(!leaks(r#"{"answer": false, "note": false}"#, "false false"));
    assert!(!leaks(r#"{"answer": null, "note": null}"#, "null"));
    assert!(!leaks(r#"{"answer": ""}"#, "a  b"));
    assert!(!leaks(r#"{"answer": ""}"#, ""));
}

#[test]
fn text_is_guarded_as_written_in_json_without_its_outer_quotes() {
    assert!(leaks(r#"{"answer": "yes"}"#, "say yes"));
    assert!(!leaks(r#"{"answer": "yes"}"#, "say yesterday"));
    assert!(leaks(r#"{"note": "a\"bcd"}"#, r#"x a\"bcd y"#));
    assert!(!leaks(r#"{"note": "a\"bcd"}"#, r#"x a"bcd y"#));
}

#[test]
fn a_decimal_is_guarded_as_written() {
    assert!(leaks(r#"{"answer": 1.5}"#, "about 1.5 units"));
    assert!(!leaks(r#"{"note": 1.5}"#, "about 1.5 units"));
    assert!(leaks(r#"{"note": 1.25}"#, "about 1.25 units"));
}

#[test]
fn an_empty_sealed_part_guards_nothing() {
    assert!(!leaks("{}", "anything at all 12345"));
    assert!(!leaks("[]", "anything"));
    assert!(!Guard::default().leaks("anything"));
}

#[test]
fn a_mark_that_closes_a_sentence_is_not_part_of_the_word() {
    assert!(leaks(r#"{"answer": 42}"#, "The total is 42."));
    assert!(leaks(r#"{"answer": 42}"#, "Is it 42?"));
    assert!(leaks(r#"{"answer": 42}"#, "It is 42!"));
    assert!(leaks(r#"{"answer": 42}"#, "It is 42?!.."));
    assert!(leaks(r#"{"answer": "a."}"#, "choose a."));
    assert!(leaks(r#"{"answer": "a."}"#, "choose a.?"));
    assert!(!leaks(r#"{"answer": "a."}"#, "choose a"));
    assert!(leaks(r#"{"answer": "a.!"}"#, "choose a.!?"));
    assert!(!leaks(r#"{"answer": "a.!"}"#, "choose a."));
    assert!(leaks(r#"{"answer": 1.5}"#, "It is 1.5."));
    assert!(!leaks(r#"{"answer": 42}"#, "p = .42"));
    assert!(!leaks(r#"{"answer": 42}"#, "see 42.5"));
    assert!(!leaks(r#"{"answer": 42}"#, "see 42-"));
    assert!(!leaks(r#"{"note": 42}"#, "The total is 42."));
}
