//! WF45, finite terminal selector: select within a declared finite family, or say why no single
//! selection exists.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf45:v1
//!
//! The family is a set of candidate polynomials with exact coefficients, constant term first.
//! Each observation `(x, y, tol)` keeps the candidates with `|p(x) - y| <= tol`. The survivors
//! fix the terminal: one is `Accepted`, several `Underdetermined`, none `Refuted`, and an empty
//! family or no evidence is `Refused`.
//!
//! The reply must name the whole declared family, the terminal the survivors give and, when
//! accepted, the survivor. The host also adds a twin of the first survivor, a different
//! polynomial that agrees with it at every observed `x`, and records the twin and that the
//! survivor count rises by one: acceptance is relative to the declared family.
//!
//! Task: `family`, an object of coefficient lists, none named `~twin`; `evidence`, a list of
//! `{"x", "y", "tol"}` with exact rationals and `tol` zero or more (default 0). Reply:
//! `{"terminal", "selected", "family_considered"}`.

use std::collections::{BTreeMap, BTreeSet};

use num_traits::{One, Signed, Zero};

use crate::datum::Datum;
use crate::exact::{polynomial, rational, rationals, show, Rational};

use super::wf07::{INCONSISTENT, UNDERDETERMINED};
use super::{no_reply, typed_refusal, Checks, Family, Run, Stop, Verdict};

pub const ACCEPTED: &str = "Accepted";
pub const UNDERDETERMINED_TERMINAL: &str = "Underdetermined";
pub const REFUTED: &str = "Refuted";
pub const REFUSED_TERMINAL: &str = "Refused";
pub const TERMINALS: &[&str] = &[
    ACCEPTED,
    UNDERDETERMINED_TERMINAL,
    REFUTED,
    REFUSED_TERMINAL,
];

/// The name of the candidate the host adds for the plenitude test.
pub const TWIN: &str = "~twin";

pub const FAMILY: Family = Family {
    workflow: "WF45",
    name: "Finite terminal selector and plenitude test",
    host_check: "finite_survivor_set_verifier",
    validate,
    walk,
};

struct Observation {
    x: Rational,
    y: Rational,
    tolerance: Rational,
}

type Candidates = BTreeMap<String, Vec<Rational>>;

struct Task {
    family: Candidates,
    evidence: Vec<Observation>,
}

fn observation(datum: &Datum) -> Option<Observation> {
    let tolerance = match datum.get("tol") {
        None => Rational::zero(),
        Some(tolerance) => rational(tolerance).filter(|tolerance| !tolerance.is_negative())?,
    };
    Some(Observation {
        x: rational(datum.get("x")?)?,
        y: rational(datum.get("y")?)?,
        tolerance,
    })
}

fn task(public: &Datum) -> Result<Task, String> {
    let Some(Datum::Map(declared)) = public.get("family") else {
        return Err("family must be an object".to_owned());
    };
    let family: Candidates = declared
        .iter()
        .map(|(name, coefficients)| Some((name.clone(), rationals(coefficients)?)))
        .collect::<Option<_>>()
        .ok_or("every candidate must be a list of exact rationals")?;
    if family.contains_key(TWIN) {
        return Err(format!("the candidate name {TWIN} is kept for the host"));
    }
    let evidence = public
        .get("evidence")
        .and_then(Datum::as_list)
        .ok_or("evidence must be a list")?
        .iter()
        .map(observation)
        .collect::<Option<_>>()
        .ok_or("every observation needs exact rational x and y, and tol zero or more")?;
    Ok(Task { family, evidence })
}

fn validate(public: &Datum, _sealed: &Datum) -> Result<(), String> {
    task(public).map(|_| ())
}

/// The candidates every observation keeps, in name order.
fn survivors<'a>(family: &'a Candidates, evidence: &[Observation]) -> Vec<&'a str> {
    family
        .iter()
        .filter(|(_, coefficients)| {
            evidence
                .iter()
                .all(|seen| (polynomial(coefficients, &seen.x) - &seen.y).abs() <= seen.tolerance)
        })
        .map(|(name, _)| name.as_str())
        .collect()
}

/// A polynomial that differs from `base` and agrees with it at every observed `x`: `base` plus
/// the product of `(X - x)` over the distinct observed points.
fn twin(base: &[Rational], evidence: &[Observation]) -> Vec<Rational> {
    let points: BTreeSet<&Rational> = evidence.iter().map(|seen| &seen.x).collect();
    let mut vanishing = vec![Rational::one()];
    for point in points {
        vanishing = (0..=vanishing.len())
            .map(|power| {
                let shifted = power
                    .checked_sub(1)
                    .and_then(|below| vanishing.get(below))
                    .cloned()
                    .unwrap_or_else(Rational::zero);
                let scaled = vanishing
                    .get(power)
                    .map_or_else(Rational::zero, |coefficient| coefficient * point);
                shifted - scaled
            })
            .collect();
    }
    let width = base.len().max(vanishing.len());
    (0..width)
        .map(|power| {
            base.get(power).cloned().unwrap_or_else(Rational::zero)
                + vanishing.get(power).cloned().unwrap_or_else(Rational::zero)
        })
        .collect()
}

fn walk(run: &mut Run, checks: &mut Checks) -> Result<Verdict, Stop> {
    let task = task(run.task).map_err(Stop::Malformed)?;
    let Some(reply) = run.ask("solve", run.prompt())? else {
        return Ok(no_reply());
    };
    let alive = survivors(&task.family, &task.evidence);
    let truth = match alive.len() {
        _ if task.family.is_empty() || task.evidence.is_empty() => REFUSED_TERMINAL,
        0 => REFUTED,
        1 => ACCEPTED,
        _ => UNDERDETERMINED_TERMINAL,
    };
    let terminal = reply
        .get("terminal")
        .and_then(Datum::as_text)
        .filter(|terminal| TERMINALS.contains(terminal))
        .ok_or_else(|| {
            Stop::Malformed(format!("terminal must be one of {}", TERMINALS.join(", ")))
        })?;
    let mut considered: Vec<&str> = reply
        .get("family_considered")
        .and_then(Datum::as_list)
        .and_then(|ids| ids.iter().map(Datum::as_text).collect())
        .ok_or_else(|| Stop::Malformed("family_considered must list candidate ids".to_owned()))?;
    considered.sort_unstable();

    let survivors_listed = Datum::from(alive.clone());
    checks.record(
        "declared_family_kept",
        considered == task.family.keys().map(String::as_str).collect::<Vec<_>>(),
        &Datum::from(considered),
    );
    checks.record(
        "terminal_matches_survivor_set",
        terminal == truth,
        &Datum::map([
            ("terminal", Datum::from(truth)),
            ("survivors", survivors_listed.clone()),
        ]),
    );
    if let (ACCEPTED, Some(survivor)) = (truth, alive.first()) {
        checks.record(
            "selection_is_the_survivor",
            reply.get("selected").and_then(Datum::as_text) == Some(survivor),
            &Datum::from(*survivor),
        );
    }
    if let Some(first) = alive.first() {
        let mut grown = task.family.clone();
        let base = task.family.get(*first).map_or(&[][..], Vec::as_slice);
        let twin = twin(base, &task.evidence);
        let written = twin
            .iter()
            .map(|coefficient| Datum::text(show(coefficient)));
        let written = Datum::List(written.collect());
        grown.insert(TWIN.to_owned(), twin);
        let after = survivors(&grown, &task.evidence).len();
        checks.record(
            "plenitude_raises_survivor_count",
            after == alive.len() + 1,
            &Datum::map([
                ("before", Datum::from(alive.len())),
                ("after", Datum::from(after)),
                ("twin", written),
            ]),
        );
    }
    let detail = Datum::map([
        ("survivors", survivors_listed),
        ("terminal", Datum::from(truth)),
    ]);
    if !checks.certified() || truth == ACCEPTED {
        return Ok(checks.judge("ACCEPTED_WITHIN_FAMILY", detail));
    }
    let code = match truth {
        UNDERDETERMINED_TERMINAL => UNDERDETERMINED,
        REFUTED => INCONSISTENT,
        _ => "REFUSED_UNDECLARED_FAMILY",
    };
    Ok(typed_refusal(code, detail))
}
