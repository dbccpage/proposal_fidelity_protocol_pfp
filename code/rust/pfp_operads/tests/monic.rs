//! The monic-polynomial domain: the expected coefficients, canonical writing, and the kind of
//! mistake a reply makes.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-monic-tests:v1

use num_bigint::BigInt;
use pfp_operads::datum::Datum;
use pfp_operads::exact::Rational;
use pfp_operads::families::monic::{classify, expand, roots, CLEAN, EPITOPES};

fn q(top: i64, bottom: i64) -> Rational {
    Rational::new(BigInt::from(top), BigInt::from(bottom))
}

fn whole(values: &[i64]) -> Vec<Rational> {
    values.iter().map(|&value| q(value, 1)).collect()
}

fn task(text: &str) -> Result<Vec<Rational>, String> {
    roots(&Datum::parse(text).expect("JSON"))
}

/// (x - 1)(x - 2)(x - 3).
fn cubic() -> Vec<Rational> {
    whole(&[1, -6, 11, -6])
}

/// The kind of a reply whose coefficient list is this JSON.
fn kind(coefficients: &str, expected: &[Rational]) -> &'static str {
    classify(&format!(r#"{{"coefficients": {coefficients}}}"#), expected)
}

#[test]
fn the_names_are_the_ones_the_workflows_use() {
    assert_eq!(CLEAN, "CLEAN");
    assert_eq!(
        EPITOPES,
        [
            "MALFORMED_JSON",
            "RATIONAL_NONCANONICAL",
            "NONMONIC_LEADING_COEFFICIENT",
            "SIGN_MISMATCH",
            "WRONG_VALUE"
        ]
    );
}

#[test]
fn roots_are_a_nonempty_list_of_exact_rationals() {
    assert_eq!(
        task(r#"{"roots": [1, "-3/2", 0]}"#),
        Ok(vec![q(1, 1), q(-3, 2), q(0, 1)])
    );
    let required = Err("roots required".to_owned());
    assert_eq!(task("{}"), required);
    assert_eq!(task(r#"{"roots": []}"#), required);
    assert_eq!(task(r#"{"roots": 3}"#), required);
    assert_eq!(task(r#"{"roots": "1"}"#), required);
    let inexact = Err("every root must be an exact rational".to_owned());
    assert_eq!(task(r#"{"roots": [1.5]}"#), inexact);
    assert_eq!(task(r#"{"roots": [1, "x"]}"#), inexact);
    assert_eq!(task(r#"{"roots": [null]}"#), inexact);
    assert_eq!(task(r#"{"roots": [true]}"#), inexact);
    assert_eq!(task(r#"{"roots": ["1/0"]}"#), inexact);
}

#[test]
fn the_expected_polynomial_is_the_expanded_product_highest_degree_first() {
    assert_eq!(expand(&whole(&[1, 2, 3])), cubic());
    assert_eq!(expand(&whole(&[2])), whole(&[1, -2]));
    assert_eq!(expand(&whole(&[2, -2])), whole(&[1, 0, -4]));
    assert_eq!(expand(&whole(&[0, 0])), whole(&[1, 0, 0]));
    assert_eq!(expand(&whole(&[3, 1, 0])), whole(&[1, -4, 3, 0]));
    assert_eq!(expand(&[q(1, 2)]), [q(1, 1), q(-1, 2)]);
    assert_eq!(expand(&[q(1, 2), q(-3, 2)]), [q(1, 1), q(1, 1), q(-3, 4)]);
    assert_eq!(expand(&[]), whole(&[1]));
    assert_eq!(expand(&whole(&[-1, -1, -1])), whole(&[1, 3, 3, 1]));
}

#[test]
fn the_expected_polynomial_written_canonically_is_clean() {
    assert_eq!(kind("[1, -6, 11, -6]", &cubic()), CLEAN);
    assert_eq!(kind(r#"[1, "-1/2"]"#, &[q(1, 1), q(-1, 2)]), CLEAN);
    assert_eq!(
        kind(r#"[1, 1, "-3/4"]"#, &[q(1, 1), q(1, 1), q(-3, 4)]),
        CLEAN
    );
    assert_eq!(kind(r#"[1, "7/3"]"#, &[q(1, 1), q(7, 3)]), CLEAN);
    assert_eq!(
        classify(" {\"coefficients\": [1, -2]}\n", &whole(&[1, -2])),
        CLEAN
    );
    assert_eq!(
        classify(
            r#"{"note": "x", "coefficients": [1, -2]}"#,
            &whole(&[1, -2])
        ),
        CLEAN
    );
}

#[test]
fn a_reply_that_is_not_the_coefficient_object_is_malformed() {
    let malformed = "MALFORMED_JSON";
    for text in [
        "",
        "coefficients: 1, -6, 11, -6",
        "[1, -6, 11, -6]",
        "{}",
        r#"{"coefficient": [1]}"#,
        r#"{"coefficients": []}"#,
        r#"{"coefficients": 1}"#,
        r#"{"coefficients": "1,-6,11,-6"}"#,
        r#"{"coefficients": {"0": 1}}"#,
        r#"{"coefficients": [1, -6, 11, -6]"#,
        r#"{"coefficients": [1], "coefficients": [1]}"#,
        "null",
        "7",
    ] {
        assert_eq!(classify(text, &cubic()), malformed, "{text}");
    }
}

#[test]
fn a_coefficient_that_is_no_number_in_any_notation_is_malformed() {
    for coefficients in [
        "[1.5]",
        "[1, -6.0, 11, -6]",
        "[1e2]",
        "[true]",
        "[null]",
        "[[1]]",
        "[{}]",
        r#"["x"]"#,
        r#"[""]"#,
        r#"["1/0"]"#,
        r#"["1/00"]"#,
        r#"["0/0"]"#,
        r#"["1/-2"]"#,
        r#"["--1"]"#,
        r#"["1/2/3"]"#,
        r#"["1 /2"]"#,
        r#"["1/ 2"]"#,
        r#"["1/2e3"]"#,
        r#"["."]"#,
        r#"["e5"]"#,
        r#"["1e"]"#,
        r#"["0x10"]"#,
        r#"["1,5"]"#,
        r#"["one"]"#,
        r#"["+"]"#,
        r#"["1/2x"]"#,
        r#"["x1/2"]"#,
    ] {
        assert_eq!(
            kind(coefficients, &cubic()),
            "MALFORMED_JSON",
            "{coefficients}"
        );
    }
    // One unreadable coefficient is enough, wherever it stands.
    assert_eq!(kind(r#"[1, -6, 11, "x"]"#, &cubic()), "MALFORMED_JSON");
    assert_eq!(kind(r#"["2/4", "x"]"#, &cubic()), "MALFORMED_JSON");
}

#[test]
fn a_number_written_in_another_notation_is_noncanonical() {
    for coefficients in [
        r#"["1"]"#,
        r#"["-6"]"#,
        r#"["2/4"]"#,
        r#"["-2/4"]"#,
        r#"["3/1"]"#,
        r#"["6/3"]"#,
        r#"["0/5"]"#,
        r#"["01/2"]"#,
        r#"["1/02"]"#,
        r#"["+1/2"]"#,
        r#"[" 1/2"]"#,
        r#"["1/2 "]"#,
        r#"["\t1/2\n"]"#,
        r#"["1.5"]"#,
        r#"["-1.5"]"#,
        r#"["1e2"]"#,
        r#"["1E+2"]"#,
        r#"["1.5e-3"]"#,
        r#"[".5"]"#,
        r#"["5."]"#,
        r#"["-0"]"#,
        r#"["+7"]"#,
        r#"["0.0"]"#,
    ] {
        assert_eq!(
            kind(coefficients, &cubic()),
            "RATIONAL_NONCANONICAL",
            "{coefficients}"
        );
    }
}

#[test]
fn noncanonical_writing_is_reported_before_any_value_is_compared() {
    // The values are the right ones; one is an integer written as text.
    assert_eq!(
        kind(r#"[1, "-6", 11, -6]"#, &cubic()),
        "RATIONAL_NONCANONICAL"
    );
    // Wrong leading coefficient and noncanonical writing: the writing is named.
    assert_eq!(
        kind(r#"[2, "2/4"]"#, &[q(1, 1), q(-1, 2)]),
        "RATIONAL_NONCANONICAL"
    );
    assert_eq!(
        kind(r#"[1, "-2/4"]"#, &[q(1, 1), q(-1, 2)]),
        "RATIONAL_NONCANONICAL"
    );
    assert_eq!(
        kind(r#"["1/2", 5, "+1"]"#, &cubic()),
        "RATIONAL_NONCANONICAL"
    );
}

#[test]
fn a_first_coefficient_other_than_one_is_nonmonic() {
    let nonmonic = "NONMONIC_LEADING_COEFFICIENT";
    assert_eq!(kind("[2, -12, 22, -12]", &cubic()), nonmonic);
    assert_eq!(kind("[-1, 6, -11, 6]", &cubic()), nonmonic);
    assert_eq!(kind("[0, -6, 11, -6]", &cubic()), nonmonic);
    assert_eq!(kind(r#"["1/2", -6, 11, -6]"#, &cubic()), nonmonic);
    assert_eq!(kind("[-6, 11, -6]", &cubic()), nonmonic);
    // Sizes right and signs wrong, but the lead is -1: that is named first.
    assert_eq!(kind("[-1, -6, 11, -6]", &cubic()), nonmonic);
}

#[test]
fn right_sizes_with_a_wrong_sign_is_a_sign_mismatch() {
    assert_eq!(kind("[1, 6, 11, 6]", &cubic()), "SIGN_MISMATCH");
    assert_eq!(kind("[1, -6, -11, -6]", &cubic()), "SIGN_MISMATCH");
    assert_eq!(kind("[1, -6, 11, 6]", &cubic()), "SIGN_MISMATCH");
    assert_eq!(kind(r#"[1, "1/2"]"#, &[q(1, 1), q(-1, 2)]), "SIGN_MISMATCH");
}

#[test]
fn anything_else_is_a_wrong_value() {
    let wrong = "WRONG_VALUE";
    assert_eq!(kind("[1, -6, 11, -5]", &cubic()), wrong);
    assert_eq!(kind("[1, -6, 12, -6]", &cubic()), wrong);
    assert_eq!(kind("[1, 6, 11, 5]", &cubic()), wrong);
    // Right sizes as far as it goes, but a coefficient short or long.
    assert_eq!(kind("[1, -6, 11]", &cubic()), wrong);
    assert_eq!(kind("[1, 6, 11]", &cubic()), wrong);
    assert_eq!(kind("[1, -6, 11, -6, 0]", &cubic()), wrong);
    assert_eq!(kind("[1]", &cubic()), wrong);
    assert_eq!(kind(r#"[1, "-1/3"]"#, &[q(1, 1), q(-1, 2)]), wrong);
}

#[test]
fn a_canonical_fraction_is_lowest_terms_with_a_denominator_above_one() {
    let half = [q(1, 1), q(1, 2)];
    assert_eq!(kind(r#"[1, "1/2"]"#, &half), CLEAN);
    assert_eq!(kind(r#"[1, "2/4"]"#, &half), "RATIONAL_NONCANONICAL");
    let whole_two = whole(&[1, 2]);
    assert_eq!(kind("[1, 2]", &whole_two), CLEAN);
    assert_eq!(kind(r#"[1, "2"]"#, &whole_two), "RATIONAL_NONCANONICAL");
    assert_eq!(kind(r#"[1, "2/1"]"#, &whole_two), "RATIONAL_NONCANONICAL");
    assert_eq!(kind(r#"[1, "4/2"]"#, &whole_two), "RATIONAL_NONCANONICAL");
}

#[test]
fn an_integer_of_any_size_is_read_exactly() {
    let big: BigInt = "123456789012345678901234567890".parse().expect("digits");
    let expected = [q(1, 1), Rational::from_integer(big)];
    assert_eq!(
        kind("[1, 123456789012345678901234567890]", &expected),
        CLEAN
    );
    assert_eq!(
        kind("[1, 123456789012345678901234567891]", &expected),
        "WRONG_VALUE"
    );
    assert_eq!(
        kind("[1, -123456789012345678901234567890]", &expected),
        "SIGN_MISMATCH"
    );
}
