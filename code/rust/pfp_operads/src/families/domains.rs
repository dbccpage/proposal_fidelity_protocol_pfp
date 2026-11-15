//! Exact-domain checkers: small closed questions the host can answer itself.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-domains:v1
//!
//! Each checker takes the data of one item and the reply to it. It works out the true answer
//! from the data alone, says whether the reply gives it, and returns the true answer as the
//! witness. Data or a reply it cannot read is an error with the reason.
//!
//! * `stabilizer_commutation`: which pairs of Pauli strings anticommute (symplectic product 1
//!   mod 2). Reply `{"anticommuting": [[i, j], ...]}`.
//! * `u1_anomaly`: the sum of the charges and the sum of their cubes, and whether both vanish.
//!   Reply `{"linear": s1, "cubic": s3, "anomaly_free": bool}`.
//! * `group_commutator`: `g^-1 h^-1 g h` in the symmetric group on `n` points, 1 to 8, products
//!   in reading order. Reply `{"commutator": [...]}`.
//! * `linear_refusal`: WF7's check on `A x = b`: the one solution, or a refusal with the code
//!   the rank test gives.

use num_bigint::BigInt;
use num_traits::Zero;

use crate::datum::Datum;
use crate::exact::{rational, rationals, Rational};
use crate::perm;

use super::{settle, wf07, Checks, REFUSED};

/// The largest number of points a commutator item may permute.
pub const MAX_POINTS: usize = 8;

/// Whether the reply gives the true answer, and the true answer; or why one of them is unreadable.
pub type Checker = fn(data: &Datum, answer: &Datum) -> Result<(bool, Datum), String>;

/// Every domain this host checks, by name.
pub const DOMAINS: &[(&str, Checker)] = &[
    ("group_commutator", commutator),
    ("linear_refusal", linear_refusal),
    ("stabilizer_commutation", stabilizer),
    ("u1_anomaly", anomaly),
];

/// The checker of a domain, if the host has one.
pub fn checker(domain: &str) -> Option<Checker> {
    DOMAINS
        .iter()
        .find(|(name, _)| *name == domain)
        .map(|&(_, checker)| checker)
}

/// One Pauli letter as its (x, z) bits.
fn pauli(letter: char) -> Option<(bool, bool)> {
    match letter {
        'I' => Some((false, false)),
        'X' => Some((true, false)),
        'Z' => Some((false, true)),
        'Y' => Some((true, true)),
        _ => None,
    }
}

fn pauli_string(datum: &Datum) -> Option<Vec<(bool, bool)>> {
    datum.as_text()?.chars().map(pauli).collect()
}

/// Whether two Pauli strings of one length anticommute: their symplectic product is 1 mod 2.
fn anticommute(a: &[(bool, bool)], b: &[(bool, bool)]) -> bool {
    a.iter()
        .zip(b)
        .filter(|((ax, az), (bx, bz))| (*ax && *bz) != (*az && *bx))
        .count()
        % 2
        == 1
}

fn pair(datum: &Datum) -> Result<Vec<BigInt>, String> {
    let Some([first, second]) = datum.as_list() else {
        return Err("pairs are [i, j]".to_owned());
    };
    let mut pair = vec![
        first.as_int().ok_or("pair must be an exact int")?.clone(),
        second.as_int().ok_or("pair must be an exact int")?.clone(),
    ];
    pair.sort();
    Ok(pair)
}

fn stabilizer(data: &Datum, answer: &Datum) -> Result<(bool, Datum), String> {
    let generators: Vec<Vec<(bool, bool)>> = data
        .get("generators")
        .and_then(Datum::as_list)
        .filter(|list| !list.is_empty())
        .and_then(|list| list.iter().map(pauli_string).collect())
        .filter(|strings: &Vec<Vec<(bool, bool)>>| {
            let length = strings.first().map(Vec::len);
            strings.iter().all(|one| Some(one.len()) == length)
        })
        .ok_or("generators must be Pauli strings of one length")?;
    let mut truth: Vec<Vec<BigInt>> = Vec::new();
    for (i, first) in generators.iter().enumerate() {
        for (j, second) in generators.iter().enumerate().skip(i + 1) {
            if anticommute(first, second) {
                truth.push(vec![BigInt::from(i), BigInt::from(j)]);
            }
        }
    }
    let mut claimed: Vec<Vec<BigInt>> = answer
        .get("anticommuting")
        .and_then(Datum::as_list)
        .ok_or("anticommuting list required")?
        .iter()
        .map(pair)
        .collect::<Result<_, _>>()?;
    claimed.sort();
    let witness = Datum::map([("anticommuting", Datum::from(truth.clone()))]);
    Ok((claimed == truth, witness))
}

/// A rational as text: `p` when it is an integer, `p/q` otherwise.
fn plain(value: &Rational) -> String {
    if value.is_integer() {
        value.numer().to_string()
    } else {
        format!("{}/{}", value.numer(), value.denom())
    }
}

fn anomaly(data: &Datum, answer: &Datum) -> Result<(bool, Datum), String> {
    let charges = data
        .get("charges")
        .filter(|charges| charges.as_list().is_some_and(|list| !list.is_empty()))
        .ok_or("charges required")?;
    let charges = rationals(charges).ok_or("charge must be an exact rational")?;
    let linear: Rational = charges.iter().sum();
    let cubic: Rational = charges.iter().map(|charge| charge * charge * charge).sum();
    let Some(Datum::Bool(free)) = answer.get("anomaly_free") else {
        return Err("anomaly_free bool required".to_owned());
    };
    let given_linear = answer
        .get("linear")
        .and_then(rational)
        .ok_or("linear must be an exact rational")?;
    let given_cubic = answer
        .get("cubic")
        .and_then(rational)
        .ok_or("cubic must be an exact rational")?;
    let passed = given_linear == linear
        && given_cubic == cubic
        && *free == (linear.is_zero() && cubic.is_zero());
    let witness = Datum::map([
        ("linear", Datum::text(plain(&linear))),
        ("cubic", Datum::text(plain(&cubic))),
    ]);
    Ok((passed, witness))
}

/// The permutation of `n` points under `key`, or the reason there is none.
pub fn permutation(holder: &Datum, key: &str, n: usize) -> Result<perm::Perm, String> {
    holder
        .get(key)
        .and_then(|value| perm::read(value, n))
        .ok_or(format!("{key} must be a permutation of {n} points"))
}

fn commutator(data: &Datum, answer: &Datum) -> Result<(bool, Datum), String> {
    let n = data
        .get("n")
        .and_then(Datum::as_count)
        .filter(|n| (1..=MAX_POINTS).contains(n))
        .ok_or(format!("n must be an exact integer from 1 to {MAX_POINTS}"))?;
    let g = permutation(data, "g", n)?;
    let h = permutation(data, "h", n)?;
    let inverses = perm::compose(&perm::inverse(&g), &perm::inverse(&h));
    let truth = perm::compose(&perm::compose(&inverses, &g), &h);
    let claimed = permutation(answer, "commutator", n)?;
    let witness = Datum::map([("commutator", Datum::from(truth.clone()))]);
    Ok((claimed == truth, witness))
}

fn linear_refusal(data: &Datum, answer: &Datum) -> Result<(bool, Datum), String> {
    let mut checks = Checks::default();
    let verdict = settle(wf07::grade(data, answer, &mut checks)?, &checks);
    let mut witness = match verdict.detail.get("witness") {
        Some(Datum::Map(map)) => map.clone(),
        _ => Default::default(),
    };
    witness.insert("code".to_owned(), Datum::text(verdict.code));
    Ok((verdict.verdict != REFUSED, Datum::Map(witness)))
}
