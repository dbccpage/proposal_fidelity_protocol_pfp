//! Exact rationals, row reduction, the rank test on a linear system, and polynomial values.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:exact-tests:v1

use num_bigint::BigInt;
use pfp_operads::datum::Datum;
use pfp_operads::exact::{
    classify_linear, polynomial, rank, rational, rationals, rref, show, Rational, Solvability,
};

fn q(top: i64, bottom: i64) -> Rational {
    Rational::new(BigInt::from(top), BigInt::from(bottom))
}

fn whole(value: i64) -> Rational {
    q(value, 1)
}

fn row(values: &[i64]) -> Vec<Rational> {
    values.iter().map(|&value| whole(value)).collect()
}

fn matrix(rows: &[&[i64]]) -> Vec<Vec<Rational>> {
    rows.iter().map(|values| row(values)).collect()
}

fn text(written: &str) -> Option<Rational> {
    rational(&Datum::text(written))
}

#[test]
fn an_integer_and_the_form_p_over_q_are_rationals() {
    assert_eq!(rational(&Datum::from(5i64)), Some(whole(5)));
    assert_eq!(rational(&Datum::from(-5i64)), Some(whole(-5)));
    assert_eq!(text("3/4"), Some(q(3, 4)));
    assert_eq!(text("-3/4"), Some(q(-3, 4)));
    assert_eq!(text("6/8"), Some(q(3, 4)));
    assert_eq!(text("7"), Some(whole(7)));
    assert_eq!(text("-7"), Some(whole(-7)));
    assert_eq!(text("0/5"), Some(whole(0)));
    assert_eq!(text("-0"), Some(whole(0)));
    assert_eq!(text("007/2"), Some(q(7, 2)));
}

#[test]
fn a_rational_is_read_at_any_size() {
    let big = "1000000000000000000000000000000000000001";
    let read = text(&format!("{big}/3")).expect("a rational");
    assert_eq!(read.numer(), &big.parse::<BigInt>().expect("digits"));
    assert_eq!(read.denom(), &BigInt::from(3));
}

#[test]
fn any_other_text_is_not_a_rational() {
    for written in [
        "",
        "-",
        "/",
        "/2",
        "1/",
        "1/0",
        "-1/0",
        "1.5",
        "1e3",
        "+1",
        " 1",
        "1 ",
        "1/-2",
        "--1",
        "1//2",
        "1/2/3",
        "x",
        "1/x",
        "x/1",
        "\u{ff11}",
        "1/\u{ff12}",
        "0x10",
        "1_0",
    ] {
        assert_eq!(text(written), None, "{written:?}");
    }
}

#[test]
fn no_other_kind_of_value_is_a_rational() {
    for value in [
        Datum::Null,
        Datum::Bool(true),
        Datum::Decimal("1.0".to_owned()),
        Datum::List(vec![Datum::from(1i64)]),
        Datum::map([("p", Datum::from(1i64))]),
    ] {
        assert_eq!(rational(&value), None);
    }
}

#[test]
fn a_list_is_read_whole_or_not_at_all() {
    let list = Datum::List(vec![Datum::from(1i64), Datum::text("1/2")]);
    assert_eq!(rationals(&list), Some(vec![whole(1), q(1, 2)]));
    assert_eq!(rationals(&Datum::List(Vec::new())), Some(Vec::new()));
    let broken = Datum::List(vec![Datum::from(1i64), Datum::text("0.5")]);
    assert_eq!(rationals(&broken), None);
    assert_eq!(rationals(&Datum::from(1i64)), None);
    assert_eq!(rationals(&Datum::text("12")), None);
}

#[test]
fn a_rational_is_written_in_lowest_terms_with_its_denominator() {
    assert_eq!(show(&whole(3)), "3/1");
    assert_eq!(show(&q(-2, 4)), "-1/2");
    assert_eq!(show(&whole(0)), "0/1");
}

#[test]
fn row_reduction_gives_the_reduced_form_and_the_pivot_columns() {
    let (reduced, pivots) = rref(&matrix(&[&[2, 4, 2], &[1, 3, 0]]));
    assert_eq!(reduced, matrix(&[&[1, 0, 3], &[0, 1, -1]]));
    assert_eq!(pivots, vec![0, 1]);
}

#[test]
fn row_reduction_swaps_rows_and_skips_a_column_with_no_pivot() {
    let (reduced, pivots) = rref(&matrix(&[&[0, 0, 2], &[0, 3, 6], &[0, 1, 2]]));
    assert_eq!(reduced, matrix(&[&[0, 1, 0], &[0, 0, 1], &[0, 0, 0]]));
    assert_eq!(pivots, vec![1, 2]);
}

#[test]
fn row_reduction_clears_the_rows_above_a_pivot_and_leaves_fractions_exact() {
    let (reduced, pivots) = rref(&matrix(&[&[2, 1], &[4, 5]]));
    assert_eq!(reduced, matrix(&[&[1, 0], &[0, 1]]));
    assert_eq!(pivots, vec![0, 1]);
    let (reduced, pivots) = rref(&matrix(&[&[3, 1, 1], &[6, 2, 5]]));
    assert_eq!(
        reduced,
        vec![vec![whole(1), q(1, 3), whole(0)], row(&[0, 0, 1])]
    );
    assert_eq!(pivots, vec![0, 2]);
}

#[test]
fn row_reduction_stops_when_every_row_has_a_pivot() {
    let (reduced, pivots) = rref(&matrix(&[&[1, 2, 3, 4]]));
    assert_eq!(reduced, matrix(&[&[1, 2, 3, 4]]));
    assert_eq!(pivots, vec![0]);
    let (reduced, pivots) = rref(&matrix(&[&[0, 2, 4, 6]]));
    assert_eq!(reduced, matrix(&[&[0, 1, 2, 3]]));
    assert_eq!(pivots, vec![1]);
}

#[test]
fn an_empty_or_zero_matrix_has_no_pivot() {
    assert_eq!(rref(&[]), (Vec::new(), Vec::new()));
    assert_eq!(rank(&[]), 0);
    let zero = matrix(&[&[0, 0], &[0, 0]]);
    assert_eq!(rref(&zero), (zero.clone(), Vec::new()));
    assert_eq!(rank(&zero), 0);
}

#[test]
fn a_short_row_is_read_as_ending_in_zeros() {
    let ragged = vec![row(&[0, 1]), row(&[2, 0, 4]), Vec::new()];
    let (reduced, pivots) = rref(&ragged);
    assert_eq!(reduced, matrix(&[&[1, 0, 2], &[0, 1, 0], &[0, 0, 0]]));
    assert_eq!(pivots, vec![0, 1]);
    assert_eq!(rank(&[row(&[1]), row(&[1, 1])]), 2);
    assert_eq!(
        rref(&[Vec::new(), Vec::new()]),
        (vec![Vec::new(), Vec::new()], Vec::new())
    );
}

#[test]
fn rank_counts_the_independent_rows() {
    assert_eq!(rank(&matrix(&[&[1, 2], &[2, 4]])), 1);
    assert_eq!(rank(&matrix(&[&[1, 2], &[3, 4]])), 2);
    assert_eq!(rank(&matrix(&[&[1, 0, 0], &[0, 1, 0], &[1, 1, 0]])), 2);
    assert_eq!(rank(&matrix(&[&[1], &[2], &[3]])), 1);
    assert_eq!(rank(&[vec![q(1, 2), q(1, 3)], vec![q(3, 2), whole(1)]]), 1);
}

#[test]
fn a_system_with_one_solution_is_unique_and_the_solution_is_exact() {
    let status = classify_linear(&matrix(&[&[1, 1], &[1, -1]]), &row(&[3, 1]));
    assert_eq!(status.solvability, Solvability::Unique(row(&[2, 1])));
    assert_eq!((status.rank_a, status.rank_ab), (2, 2));
    assert_eq!(status.solvability.name(), "unique");
    let status = classify_linear(&matrix(&[&[2, 0], &[0, 3]]), &row(&[1, 1]));
    assert_eq!(
        status.solvability,
        Solvability::Unique(vec![q(1, 2), q(1, 3)])
    );
}

#[test]
fn more_equations_than_unknowns_can_still_have_one_solution() {
    let status = classify_linear(&matrix(&[&[0, 1], &[1, 0], &[1, 1]]), &row(&[5, 7, 12]));
    assert_eq!(status.solvability, Solvability::Unique(row(&[7, 5])));
    assert_eq!((status.rank_a, status.rank_ab), (2, 2));
}

#[test]
fn a_system_whose_ranks_differ_is_inconsistent() {
    let status = classify_linear(&matrix(&[&[1, 1], &[2, 2]]), &row(&[3, 7]));
    assert_eq!(status.solvability, Solvability::Inconsistent);
    assert_eq!((status.rank_a, status.rank_ab), (1, 2));
    assert_eq!(status.solvability.name(), "inconsistent");
}

#[test]
fn a_consistent_system_with_too_little_rank_is_underdetermined() {
    let status = classify_linear(&matrix(&[&[1, 1], &[2, 2]]), &row(&[3, 6]));
    assert_eq!(status.solvability, Solvability::Underdetermined);
    assert_eq!((status.rank_a, status.rank_ab), (1, 1));
    assert_eq!(status.solvability.name(), "underdetermined");
    let wide = classify_linear(&matrix(&[&[1, 2, 3]]), &row(&[6]));
    assert_eq!(wide.solvability, Solvability::Underdetermined);
    assert_eq!((wide.rank_a, wide.rank_ab), (1, 1));
}

#[test]
fn a_polynomial_is_evaluated_exactly_with_the_constant_term_first() {
    assert_eq!(polynomial(&row(&[1, 0, 2]), &whole(3)), whole(19));
    assert_eq!(polynomial(&row(&[1, 2]), &whole(5)), whole(11));
    assert_eq!(polynomial(&row(&[5]), &whole(100)), whole(5));
    assert_eq!(polynomial(&[], &whole(4)), whole(0));
    assert_eq!(polynomial(&[q(1, 2), whole(1)], &q(1, 3)), q(5, 6));
    assert_eq!(polynomial(&row(&[0, 0, 1]), &whole(-4)), whole(16));
}
