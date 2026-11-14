//! WF38, diagnostic-trace proposal selection: rank candidate repairs by the defect the host
//! recomputes, never by what a candidate says of itself.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf38:v1
//!
//! The defect of a rational edge cochain is the sum of the sizes of its fundamental cycle
//! sums; it is zero exactly for a coboundary. Each candidate is a name and a list of
//! `[edge, value]` corrections added to the task's values. The host recomputes the defect after
//! each candidate, keeps those that lower it strictly, and ranks them by defect, then by the
//! total size of the correction, then by name. Any other field of a candidate, such as a score
//! it gives itself, is not read.
//!
//! The run is certified as `SELECTED` with the first of that ranking, and refused as
//! `NO_STRICT_DECREASE` when no candidate lowers the defect.
//!
//! Task: the cochain task of [`super::cochain`]. Reply: `{"candidates": [{"name", "delta"}]}`.

use std::collections::BTreeMap;

use num_traits::{Signed, Zero};

use crate::datum::Datum;
use crate::exact::{rational, show, Rational};

use super::cochain::{self, Cochain};
use super::{no_reply, refused, Checks, Family, Run, Stop, Verdict};

pub const FAMILY: Family = Family {
    workflow: "WF38",
    name: "Diagnostic-trace proposal selection",
    host_check: "host_recomputed_defect_ranking",
    validate,
    walk,
};

fn validate(task: &Datum, _sealed: &Datum) -> Result<(), String> {
    cochain::read(task).map(|_| ())
}

/// One correction of a candidate: the edge and the value added to it.
fn correction(entry: &Datum, edges: usize) -> Result<(usize, Rational), String> {
    let Some([edge, value]) = entry.as_list() else {
        return Err("delta entries are [edge, value]".to_owned());
    };
    let value = rational(value).ok_or("delta value must be an exact rational")?;
    let edge = edge.as_int().ok_or("delta edge must be an exact int")?;
    let edge = usize::try_from(edge).ok().filter(|&edge| edge < edges);
    Ok((edge.ok_or("edge index out of range")?, value))
}

/// The defect a candidate leaves and the total size of its correction.
fn score(cochain: &Cochain, delta: &[Datum]) -> Result<(Rational, Rational), String> {
    let mut values = cochain.values.clone();
    let mut size = Rational::zero();
    for entry in delta {
        let (edge, change) = correction(entry, values.len())?;
        size += change.abs();
        if let Some(value) = values.get_mut(edge) {
            *value += change;
        }
    }
    Ok((cochain.named.graph.defect(&values), size))
}

/// Every candidate's score, by name.
fn table(
    cochain: &Cochain,
    reply: &Datum,
) -> Result<BTreeMap<String, (Rational, Rational)>, String> {
    let candidates = reply
        .get("candidates")
        .and_then(Datum::as_list)
        .ok_or("candidates must be a list")?;
    let mut table = BTreeMap::new();
    for candidate in candidates {
        let name = candidate
            .get("name")
            .and_then(Datum::as_text)
            .ok_or("every candidate needs a text name")?;
        let delta = candidate
            .get("delta")
            .and_then(Datum::as_list)
            .ok_or("every candidate needs a delta list")?;
        if table
            .insert(name.to_owned(), score(cochain, delta)?)
            .is_some()
        {
            return Err("candidate names must be distinct".to_owned());
        }
    }
    Ok(table)
}

fn walk(run: &mut Run, checks: &mut Checks) -> Result<Verdict, Stop> {
    let cochain = cochain::read(run.task).map_err(Stop::Malformed)?;
    let Some(reply) = run.ask("solve", run.prompt())? else {
        return Ok(no_reply());
    };
    let table = table(&cochain, reply).map_err(Stop::Malformed)?;
    let before = cochain.named.graph.defect(&cochain.values);
    let mut admissible: Vec<(&Rational, &Rational, &String)> = table
        .iter()
        .filter(|(_, (defect, _))| *defect < before)
        .map(|(name, (defect, size))| (defect, size, name))
        .collect();
    admissible.sort();
    let shown = |value: &Rational| Datum::text(show(value));
    let scores = Datum::Map(
        table
            .iter()
            .map(|(name, (defect, size))| {
                (name.clone(), Datum::List(vec![shown(defect), shown(size)]))
            })
            .collect(),
    );
    let phi0 = shown(&before);
    let evidence = Datum::List(vec![phi0.clone(), scores.clone()]);
    let found = checks.record(
        "strict_defect_decrease_exists",
        !admissible.is_empty(),
        &evidence,
    );
    let (Some((defect, _, winner)), true) = (admissible.first(), found) else {
        let detail = Datum::map([("phi0", phi0), ("scores", scores)]);
        return Ok(refused("NO_STRICT_DECREASE", detail));
    };
    let ranking: Vec<&str> = admissible.iter().map(|entry| entry.2.as_str()).collect();
    let detail = Datum::map([
        ("winner", Datum::text(winner.as_str())),
        ("phi0", phi0),
        ("phi", shown(defect)),
        ("scores", scores),
        ("ranking", Datum::from(ranking)),
    ]);
    Ok(checks.judge("SELECTED", detail))
}
