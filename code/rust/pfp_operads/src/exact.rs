//! Exact rational arithmetic and linear algebra for the workflow hosts.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:exact:v1
//!
//! Every number is a ratio of unbounded integers, so no step rounds and none overflows. A
//! rational is written on the wire as an integer or as the text `p/q`: an optional minus, digits,
//! and optionally a slash and a nonzero denominator in digits. A decimal point, an exponent, a
//! plus sign and spaces are not part of that form.

use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Zero};

use crate::datum::Datum;

pub type Rational = BigRational;

fn digits(text: &str) -> Option<BigInt> {
    if !text.bytes().all(|byte| byte.is_ascii_digit()) {
        return None;
    }
    text.parse().ok()
}

fn ratio(text: &str) -> Option<Rational> {
    let (negative, body) = match text.strip_prefix('-') {
        Some(rest) => (true, rest),
        None => (false, text),
    };
    let (top, bottom) = match body.split_once('/') {
        Some((top, bottom)) => (digits(top)?, digits(bottom)?),
        None => (digits(body)?, BigInt::one()),
    };
    if bottom.is_zero() {
        return None;
    }
    let value = Rational::new(top, bottom);
    Some(if negative { -value } else { value })
}

/// The rational a value denotes: an integer, or text in the form `p/q`.
pub fn rational(datum: &Datum) -> Option<Rational> {
    match datum {
        Datum::Int(number) => Some(Rational::from_integer(number.clone())),
        Datum::Text(text) => ratio(text),
        _ => None,
    }
}

/// Every item of a list as a rational, or nothing if the value is not a list of rationals.
pub fn rationals(datum: &Datum) -> Option<Vec<Rational>> {
    datum.as_list()?.iter().map(rational).collect()
}

/// A rational as the hosts write it: `p/q` in lowest terms, with `q` written even when it is 1.
pub fn show(value: &Rational) -> String {
    format!("{}/{}", value.numer(), value.denom())
}

/// Reduced row echelon form over the rationals, and the column of each pivot. A row shorter than
/// the widest one is read as ending in zeros.
pub fn rref(rows: &[Vec<Rational>]) -> (Vec<Vec<Rational>>, Vec<usize>) {
    let mut matrix = rows.to_vec();
    let mut pivots = Vec::new();
    let width = matrix.iter().map(Vec::len).max().unwrap_or(0);
    for row in &mut matrix {
        row.resize(width, Rational::zero());
    }
    let mut next = 0;
    for column in 0..width {
        let Some(pivot) = (next..matrix.len()).find(|&row| !matrix[row][column].is_zero()) else {
            continue;
        };
        matrix.swap(next, pivot);
        let lead = matrix[next][column].clone();
        for entry in &mut matrix[next] {
            *entry = &*entry / &lead;
        }
        let pivot_row = matrix[next].clone();
        for (row, entries) in matrix.iter_mut().enumerate() {
            if row == next {
                continue;
            }
            let factor = entries[column].clone();
            for (entry, above) in entries.iter_mut().zip(&pivot_row) {
                *entry = &*entry - &factor * above;
            }
        }
        pivots.push(column);
        next += 1;
    }
    (matrix, pivots)
}

/// The rank of a matrix over the rationals.
pub fn rank(rows: &[Vec<Rational>]) -> usize {
    rref(rows).1.len()
}

/// Whether `A x = b` has exactly one solution, none, or more than one.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Solvability {
    Unique(Vec<Rational>),
    Inconsistent,
    Underdetermined,
}

impl Solvability {
    /// The name the hosts report.
    pub fn name(&self) -> &'static str {
        match self {
            Solvability::Unique(_) => "unique",
            Solvability::Inconsistent => "inconsistent",
            Solvability::Underdetermined => "underdetermined",
        }
    }
}

/// The rank test on `A x = b` and what it found.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LinearStatus {
    pub solvability: Solvability,
    pub rank_a: usize,
    pub rank_ab: usize,
}

/// Answerability of `A x = b` over the rationals by the Rouche-Capelli rank test: one solution
/// exactly when `rank(A) = rank([A|b])` and that rank is the number of unknowns.
///
/// `a` has one row per entry of `b`, and the first row gives the number of unknowns.
pub fn classify_linear(a: &[Vec<Rational>], b: &[Rational]) -> LinearStatus {
    let unknowns = a.first().map_or(0, Vec::len);
    let augmented: Vec<Vec<Rational>> = a
        .iter()
        .zip(b)
        .map(|(row, right)| row.iter().cloned().chain([right.clone()]).collect())
        .collect();
    let rank_a = rank(a);
    let (reduced, pivots) = rref(&augmented);
    let rank_ab = pivots.len();
    let solvability = if rank_a != rank_ab {
        Solvability::Inconsistent
    } else if rank_a < unknowns {
        Solvability::Underdetermined
    } else {
        let mut solution = vec![Rational::zero(); unknowns];
        for (row, &column) in reduced.iter().zip(&pivots) {
            solution[column] = row[unknowns].clone();
        }
        Solvability::Unique(solution)
    };
    LinearStatus {
        solvability,
        rank_a,
        rank_ab,
    }
}

/// The value of the polynomial with these coefficients, constant term first, at `x`.
pub fn polynomial(coefficients: &[Rational], x: &Rational) -> Rational {
    coefficients
        .iter()
        .rev()
        .fold(Rational::zero(), |sum, coefficient| sum * x + coefficient)
}
