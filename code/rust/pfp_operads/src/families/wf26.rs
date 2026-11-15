//! WF26, multi-round antibody dialogue: each kind of mistake the host sees becomes a fixed
//! constraint carried into every later round.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf26:v1
//!
//! The domain is the monic polynomial of [`super::monic`], and the loop is WF9's. When the host
//! sorts a reply into a kind of mistake it has not seen in this run, it adds that kind's
//! antibody to the set, and every later prompt carries the whole set as the residual. An
//! antibody is one of the fixed sentences in [`ANTIBODIES`], chosen by the kind of mistake
//! alone; the host has no way to put a coefficient into one.
//!
//! The run is certified when a reply is the expected polynomial within the limit, and refused
//! when the rounds run out. A reply that is not text uses up a round and adds no antibody.
//!
//! Task: `roots`, a nonempty list of exact rationals, and optionally `max_attempts`, 1 to 8
//! (default 3). Reply: text holding `{"coefficients": [...]}`, highest degree first.

use crate::datum::Datum;

use super::attempts::{limit, Assessment};
use super::monic::{classify, expand, roots, CLEAN};
use super::wf09::{bounded, DEFAULT_ATTEMPTS, MAX_ATTEMPTS};
use super::{Checks, Family, Run, Stop, Verdict};

/// The constraint carried forward for each kind of mistake.
pub const ANTIBODIES: [(&str, &str); 5] = [
    (
        "MALFORMED_JSON",
        "Reply with one JSON object of the form {\"coefficients\": [...]} and nothing else.",
    ),
    (
        "RATIONAL_NONCANONICAL",
        "Write integers as integers and other rationals as p/q in lowest terms.",
    ),
    (
        "NONMONIC_LEADING_COEFFICIENT",
        "The leading coefficient must be 1.",
    ),
    (
        "SIGN_MISMATCH",
        "Some coefficient signs are wrong; the sign of each coefficient follows Vieta.",
    ),
    (
        "WRONG_VALUE",
        "The coefficients do not vanish at the stated roots.",
    ),
];

pub const FAMILY: Family = Family {
    workflow: "WF26",
    name: "Multi-round antibody dialogue",
    host_check: "epitope_antibody_exact_oracle",
    validate,
    walk,
};

fn validate(task: &Datum, _sealed: &Datum) -> Result<(), String> {
    roots(task)?;
    limit(task, DEFAULT_ATTEMPTS, MAX_ATTEMPTS).map(|_| ())
}

fn antibody(epitope: &str) -> Option<Datum> {
    let (_, constraint) = ANTIBODIES.iter().find(|(kind, _)| *kind == epitope)?;
    Some(Datum::map([
        ("constraint", Datum::from(*constraint)),
        ("epitope", Datum::from(epitope)),
    ]))
}

fn walk(run: &mut Run, checks: &mut Checks) -> Result<Verdict, Stop> {
    let expected = expand(&roots(run.task).map_err(Stop::Malformed)?);
    let limit = limit(run.task, DEFAULT_ATTEMPTS, MAX_ATTEMPTS).map_err(Stop::Malformed)?;
    let mut antibodies: Vec<Datum> = Vec::new();
    let mut assess = |reply: &Datum| {
        let text = reply.as_text().ok_or("reply must be text")?;
        let epitope = classify(text, &expected);
        if let Some(new) = antibody(epitope).filter(|new| !antibodies.contains(new)) {
            antibodies.push(new);
        }
        Ok(Assessment {
            accepted: epitope == CLEAN,
            measure: Datum::from(epitope),
            residual: Datum::map([("antibodies", Datum::List(antibodies.clone()))]),
        })
    };
    let mut verdict = bounded(run, checks, limit, &mut assess)?;
    if let Datum::Map(detail) = &mut verdict.detail {
        detail.insert("antibodies".to_owned(), Datum::from(antibodies.len()));
    }
    Ok(verdict)
}
