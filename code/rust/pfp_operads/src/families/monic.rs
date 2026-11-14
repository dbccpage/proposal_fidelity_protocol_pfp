//! The monic-polynomial domain: the reply must be the polynomial with the stated roots, and a
//! wrong reply is sorted by what kind of mistake it is.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-monic:v1
//!
//! The expected answer is the expanded product of `(x - r)` over the roots, coefficients
//! highest degree first. A reply is text holding one JSON object `{"coefficients": [...]}`.
//! A coefficient is written canonically as a JSON integer, or as text `p/q` in lowest terms
//! with `q` above 1 and no sign but a leading minus.
//!
//! [`classify`] gives the first of these that applies:
//!
//! * `MALFORMED_JSON`: not JSON, not that object, an empty list, or a coefficient that is not a
//!   number in any notation.
//! * `RATIONAL_NONCANONICAL`: every coefficient is a number, but one is text in another
//!   notation: an integer as text, a fraction not in lowest terms, a sign, spaces, a decimal
//!   point or an exponent.
//! * `NONMONIC_LEADING_COEFFICIENT`: the first coefficient is not 1.
//! * `CLEAN`: the coefficients are the expected ones.
//! * `SIGN_MISMATCH`: right sizes, wrong signs.
//! * `WRONG_VALUE`: anything else.

use std::sync::LazyLock;

use num_traits::{One, Signed, Zero};
use regex::Regex;

use crate::datum::Datum;
use crate::exact::{rational, show, Rational};

pub const CLEAN: &str = "CLEAN";

/// The mistakes a reply can be sorted into, in the order they are looked for.
pub const EPITOPES: [&str; 5] = [
    "MALFORMED_JSON",
    "RATIONAL_NONCANONICAL",
    "NONMONIC_LEADING_COEFFICIENT",
    "SIGN_MISMATCH",
    "WRONG_VALUE",
];

/// A number as text in some notation the host does not take as canonical: a fraction of digit
/// strings, or digits with an optional point and exponent, with an optional sign and spaces
/// round it.
static LOOSE: LazyLock<Option<Regex>> = LazyLock::new(|| {
    Regex::new(concat!(
        r"^[ \t\n\r]*[-+]?(?:[0-9]+/0*[1-9][0-9]*",
        r"|(?:[0-9]+\.?[0-9]*|\.[0-9]+)(?:[eE][-+]?[0-9]+)?)[ \t\n\r]*$"
    ))
    .ok()
});

/// The roots a task states: a nonempty list of exact rationals.
pub fn roots(task: &Datum) -> Result<Vec<Rational>, String> {
    task.get("roots")
        .and_then(Datum::as_list)
        .filter(|roots| !roots.is_empty())
        .ok_or("roots required")?
        .iter()
        .map(rational)
        .collect::<Option<_>>()
        .ok_or_else(|| "every root must be an exact rational".to_owned())
}

/// The coefficients of the product of `(x - r)` over the roots, highest degree first.
pub fn expand(roots: &[Rational]) -> Vec<Rational> {
    let mut coefficients = vec![Rational::one()];
    for root in roots {
        let mut next = coefficients.clone();
        next.push(Rational::zero());
        for (place, coefficient) in coefficients.iter().enumerate() {
            next[place + 1] -= root * coefficient;
        }
        coefficients = next;
    }
    coefficients
}

/// One coefficient as written: its value when the writing is canonical, nothing when it is a
/// number in another notation. An error when it is no number at all.
fn coefficient(written: &Datum) -> Result<Option<Rational>, ()> {
    match written {
        Datum::Int(_) => Ok(rational(written)),
        Datum::Text(text) => {
            let canonical =
                rational(written).filter(|value| !value.is_integer() && *text == show(value));
            let numeric = LOOSE.as_ref().is_some_and(|loose| loose.is_match(text));
            if canonical.is_some() || numeric {
                Ok(canonical)
            } else {
                Err(())
            }
        }
        _ => Err(()),
    }
}

fn coefficients(text: &str) -> Option<Vec<Option<Rational>>> {
    let reply = Datum::parse(text).ok()?;
    reply
        .get("coefficients")?
        .as_list()
        .filter(|written| !written.is_empty())?
        .iter()
        .map(|written| coefficient(written).ok())
        .collect()
}

/// `CLEAN` when the reply text is the expected polynomial written canonically, else the
/// mistake it makes.
pub fn classify(text: &str, expected: &[Rational]) -> &'static str {
    let Some(written) = coefficients(text) else {
        return "MALFORMED_JSON";
    };
    let Some(values) = written.into_iter().collect::<Option<Vec<Rational>>>() else {
        return "RATIONAL_NONCANONICAL";
    };
    let same_sizes = values.len() == expected.len()
        && values
            .iter()
            .zip(expected)
            .all(|(given, wanted)| given.abs() == wanted.abs());
    if values.first() != Some(&Rational::one()) {
        "NONMONIC_LEADING_COEFFICIENT"
    } else if values == expected {
        CLEAN
    } else if same_sizes {
        "SIGN_MISMATCH"
    } else {
        "WRONG_VALUE"
    }
}
