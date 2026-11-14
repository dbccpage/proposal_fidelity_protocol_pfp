//! What the repair loops share: the attempt limit, a trail row, the residual line of a prompt,
//! and the fuel counter.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-attempts-tests:v1

use num_bigint::BigInt;
use pfp_operads::datum::Datum;
use pfp_operads::families::attempts::{limit, row, unread, with_residual, Assessment, Fuel};

fn datum(text: &str) -> Datum {
    Datum::parse(text).expect("JSON")
}

fn stated(max_attempts: &str) -> Result<usize, String> {
    limit(
        &datum(&format!(r#"{{"max_attempts": {max_attempts}}}"#)),
        3,
        8,
    )
}

#[test]
fn a_task_that_names_no_limit_gets_the_default() {
    assert_eq!(limit(&datum("{}"), 3, 8), Ok(3));
    assert_eq!(limit(&datum(r#"{"edges": []}"#), 5, 5), Ok(5));
    assert_eq!(limit(&datum("[]"), 2, 8), Ok(2));
}

#[test]
fn a_stated_limit_from_one_to_the_ceiling_is_taken() {
    assert_eq!(stated("1"), Ok(1));
    assert_eq!(stated("4"), Ok(4));
    assert_eq!(stated("8"), Ok(8));
    assert_eq!(limit(&datum(r#"{"max_attempts": 5}"#), 5, 5), Ok(5));
}

#[test]
fn a_stated_limit_outside_the_range_is_refused_with_the_range() {
    let outside = Err("max_attempts must be in 1..8".to_owned());
    assert_eq!(stated("0"), outside);
    assert_eq!(stated("9"), outside);
    assert_eq!(stated("-1"), outside);
    assert_eq!(stated("123456789012345678901234567890"), outside);
    assert_eq!(
        limit(&datum(r#"{"max_attempts": 6}"#), 5, 5),
        Err("max_attempts must be in 1..5".to_owned())
    );
}

#[test]
fn a_stated_limit_that_is_not_an_exact_integer_is_refused() {
    let inexact = Err("max_attempts must be an exact int".to_owned());
    assert_eq!(stated(r#""3""#), inexact);
    assert_eq!(stated("3.0"), inexact);
    assert_eq!(stated("null"), inexact);
    assert_eq!(stated("true"), inexact);
    assert_eq!(stated("[3]"), inexact);
}

#[test]
fn an_unread_reply_has_its_reason_as_residual_and_no_measure() {
    assert_eq!(
        unread("flip list required".to_owned()),
        Assessment {
            accepted: false,
            residual: datum(r#"{"malformed": "flip list required"}"#),
            measure: Datum::Null,
        }
    );
}

#[test]
fn a_trail_row_is_the_attempt_its_measure_and_its_residual() {
    let finding = Assessment {
        accepted: true,
        residual: datum(r#"{"odd_cycles": [1]}"#),
        measure: datum("2"),
    };
    assert_eq!(
        row(4, &finding).canonical(),
        r#"{"attempt":4,"measure":2,"residual":{"odd_cycles":[1]}}"#
    );
    assert_eq!(
        row(0, &unread("x".to_owned())).canonical(),
        r#"{"attempt":0,"measure":null,"residual":{"malformed":"x"}}"#
    );
}

#[test]
fn the_residual_goes_under_the_prompt_as_canonical_json() {
    assert_eq!(
        with_residual(
            "Repair it.",
            &datum(r#"{"odd_cycles": [0, 1], "flip_count": 2}"#)
        ),
        "Repair it.\nHost residual: {\"flip_count\":2,\"odd_cycles\":[0,1]}"
    );
}

#[test]
fn fuel_goes_down_by_one_each_draw_and_keeps_its_trace() {
    let mut fuel = Fuel::new(BigInt::from(3));
    assert_eq!(fuel.left(), &BigInt::from(3));
    assert_eq!(fuel.trace().canonical(), "[3]");
    assert!(fuel.draw());
    assert_eq!(fuel.left(), &BigInt::from(2));
    assert!(fuel.draw());
    assert!(fuel.draw());
    assert_eq!(fuel.left(), &BigInt::from(0));
    assert_eq!(fuel.trace().canonical(), "[3,2,1,0]");
}

#[test]
fn spent_fuel_gives_nothing_and_records_nothing() {
    let mut fuel = Fuel::new(BigInt::from(1));
    assert!(fuel.draw());
    assert!(!fuel.draw());
    assert!(!fuel.draw());
    assert_eq!(fuel.left(), &BigInt::from(0));
    assert_eq!(fuel.trace().canonical(), "[1,0]");
    let mut none = Fuel::new(BigInt::from(0));
    assert!(!none.draw());
    assert_eq!(none.trace().canonical(), "[0]");
    let mut owed = Fuel::new(BigInt::from(-2));
    assert!(!owed.draw());
    assert_eq!(owed.left(), &BigInt::from(-2));
}

#[test]
fn fuel_is_not_bounded_by_the_machine_word() {
    let start: BigInt = "123456789012345678901234567890".parse().expect("digits");
    let mut fuel = Fuel::new(start);
    assert!(fuel.draw());
    assert_eq!(
        fuel.trace().canonical(),
        "[123456789012345678901234567890,123456789012345678901234567889]"
    );
}
