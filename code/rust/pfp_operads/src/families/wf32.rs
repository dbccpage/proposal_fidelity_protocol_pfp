//! WF32, claim-scoped receipt: each claim is admitted only through its own check, bound to its
//! own evidence.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf32:v1
//!
//! The reply is a list of atomic claims and the ids it says are admitted.
//!
//! * An `exact` claim names an input the task declares, with the domain checker the task chose
//!   for it, and gives a witness. The host runs that checker (see [`super::domains`]). A claim
//!   that brings its own input or checker is not checked and fails.
//! * A `quote` claim names a declared source and a byte span. It holds when the span is not
//!   empty and its bytes are the quoted text.
//! * Any other claim, and the free text on an exact claim, has no check. It is never admitted
//!   and is listed as an open obligation.
//!
//! Each checked claim gets a digest of the claim and the host's witness. The reply is refused
//! when a checked claim fails, when it lists as admitted a claim the host did not admit, when a
//! digest it states is not the host's, or when nothing is admitted.
//!
//! Task: optional `sources`, an object of texts; optional `inputs`, an object of
//! `{"checker", "input"}` with a registered checker. Reply: `{"claims": [...], "admitted": [ids]}`.

use std::collections::{BTreeMap, BTreeSet};

use crate::datum::Datum;

use super::domains::checker;
use super::{certified, no_reply, sha256_hex, Checks, Family, Run, Stop, Verdict};

pub const FAMILY: Family = Family {
    workflow: "WF32",
    name: "Claim-scoped receipt",
    host_check: "per_claim_independent_checkers",
    validate,
    walk,
};

fn validate(task: &Datum, _sealed: &Datum) -> Result<(), String> {
    let texts = |sources: &Datum| match sources {
        Datum::Map(map) => map.values().all(|source| source.as_text().is_some()),
        _ => false,
    };
    if !task.get("sources").is_none_or(texts) {
        return Err("sources must be an object of texts".to_owned());
    }
    let declared = |inputs: &Datum| match inputs {
        Datum::Map(map) => map.values().all(|input| checked_input(input).is_some()),
        _ => false,
    };
    if !task.get("inputs").is_none_or(declared) {
        return Err("declared inputs need a registered checker and an input object".to_owned());
    }
    Ok(())
}

/// A declared input's checker and data.
fn checked_input(declared: &Datum) -> Option<(super::domains::Checker, &Datum)> {
    let check = checker(declared.get("checker")?.as_text()?)?;
    let input = declared.get("input").filter(|input| input.is_map())?;
    Some((check, input))
}

/// The host's finding on an exact claim: its declared input's checker run on the witness, or a
/// failure when the claim names no declared input or brings an input or a checker of its own.
fn exact(task: &Datum, claim: &Datum) -> Result<(bool, Datum), String> {
    let reference = claim.get("input_ref").unwrap_or(&Datum::Null);
    let declared = reference
        .as_text()
        .and_then(|name| task.get("inputs")?.get(name))
        .and_then(checked_input)
        .filter(|_| claim.get("input").is_none() && claim.get("checker").is_none());
    match declared {
        Some((check, input)) => check(input, claim.get("witness").unwrap_or(&Datum::Null)),
        None => Ok((
            false,
            Datum::map([("undeclared_input", Datum::text(reference.canonical()))]),
        )),
    }
}

/// The host's finding on a quote claim, or nothing when it names no declared source or has no
/// span list, in which case the claim stays open.
fn quote(task: &Datum, claim: &Datum) -> Result<Option<(bool, Datum)>, String> {
    let source = claim
        .get("source")
        .and_then(Datum::as_text)
        .and_then(|name| task.get("sources")?.get(name))
        .and_then(Datum::as_text);
    let (Some(source), Some(span)) = (source, claim.get("span").and_then(Datum::as_list)) else {
        return Ok(None);
    };
    let ([start, end], Some(text)) = (span, claim.get("text").and_then(Datum::as_text)) else {
        return Err("quote needs [start, end] and text".to_owned());
    };
    if start.as_int().is_none() || end.as_int().is_none() {
        return Err("span must be exact ints".to_owned());
    }
    let holds = match (start.as_count(), end.as_count()) {
        (Some(start), Some(end)) if start < end => {
            source.as_bytes().get(start..end) == Some(text.as_bytes())
        }
        _ => false,
    };
    let witness = Datum::map([
        (
            "source_sha256",
            Datum::text(sha256_hex(&Datum::text(source).canonical())),
        ),
        ("span", Datum::List(vec![start.clone(), end.clone()])),
    ]);
    Ok(Some((holds, witness)))
}

/// The host's finding on one claim, or nothing when no check covers its kind.
fn finding(task: &Datum, claim: &Datum) -> Result<Option<(bool, Datum)>, String> {
    match claim.get("kind").and_then(Datum::as_text) {
        Some("exact") => exact(task, claim).map(Some),
        Some("quote") => quote(task, claim),
        _ => Ok(None),
    }
}

/// The part of a claim its digest covers: everything but the digest it states, and but its free
/// text unless the claim is a quote.
fn scope(claim: &Datum, is_quote: bool) -> Datum {
    match claim {
        Datum::Map(map) => Datum::Map(
            map.iter()
                .filter(|(key, _)| {
                    key.as_str() != "evidence_sha256" && (is_quote || key.as_str() != "text")
                })
                .map(|(key, value)| (key.clone(), value.clone()))
                .collect(),
        ),
        other => other.clone(),
    }
}

fn names(ids: impl IntoIterator<Item = String>) -> Datum {
    Datum::List(ids.into_iter().map(Datum::Text).collect())
}

/// The reply's claims with their ids: a nonempty list of objects, each with a text id, no id
/// twice.
fn claims(reply: &Datum) -> Result<Vec<(&str, &Datum)>, String> {
    let claims = reply
        .get("claims")
        .and_then(Datum::as_list)
        .filter(|claims| !claims.is_empty())
        .ok_or("claims required")?;
    if !claims.iter().all(Datum::is_map) {
        return Err("claims are objects".to_owned());
    }
    let ids: Vec<&str> = claims
        .iter()
        .map(|claim| claim.get("id").and_then(Datum::as_text))
        .collect::<Option<_>>()
        .filter(|ids: &Vec<&str>| ids.iter().collect::<BTreeSet<_>>().len() == ids.len())
        .ok_or("claims need unique string ids")?;
    Ok(ids.into_iter().zip(claims).collect())
}

/// The ids the reply lists as admitted that the host did not admit. An id that is not text is
/// named by its canonical text.
fn overreach(
    reply: &Datum,
    admitted: &BTreeMap<String, String>,
) -> Result<BTreeSet<String>, String> {
    let listed = match reply.get("admitted") {
        None => &[][..],
        Some(listed) => listed.as_list().ok_or("admitted must be a list")?,
    };
    Ok(listed
        .iter()
        .map(|id| id.as_text().map_or_else(|| id.canonical(), str::to_owned))
        .filter(|id| !admitted.contains_key(id))
        .collect())
}

fn walk(run: &mut Run, checks: &mut Checks) -> Result<Verdict, Stop> {
    let Some(reply) = run.ask("solve", run.prompt())? else {
        return Ok(no_reply());
    };
    let claims = claims(reply).map_err(Stop::Malformed)?;

    let mut admitted: BTreeMap<String, String> = BTreeMap::new();
    let mut open: Vec<String> = Vec::new();
    for (id, claim) in claims {
        let Some((holds, witness)) = finding(run.task, claim).map_err(Stop::Malformed)? else {
            open.push(id.to_owned());
            continue;
        };
        let is_quote = claim.get("kind").and_then(Datum::as_text) == Some("quote");
        if !is_quote && claim.get("text").is_some() {
            open.push(format!("{id}:text"));
        }
        let bound = Datum::map([("claim", scope(claim, is_quote)), ("host", witness.clone())]);
        let bound = sha256_hex(&bound.canonical());
        checks.record(&format!("claim:{id}"), holds, &witness);
        if let Some(stated) = claim.get("evidence_sha256") {
            checks.record(
                &format!("claim:{id}:digest_bound"),
                stated.as_text() == Some(bound.as_str()),
                &Datum::text(bound.clone()),
            );
        }
        if holds {
            admitted.insert(id.to_owned(), bound);
        }
    }

    let overreach = overreach(reply, &admitted).map_err(Stop::Malformed)?;
    let overreach = names(overreach);
    let admitted_ids = names(admitted.keys().cloned());
    checks.record(
        "no_admission_overreach",
        overreach == Datum::List(Vec::new()),
        &overreach,
    );
    checks.record("some_claim_admitted", !admitted.is_empty(), &admitted_ids);
    if !checks.certified() {
        let detail = Datum::map([
            ("overreach", overreach),
            ("admitted", admitted_ids),
            ("unadmitted", names(open.clone())),
        ]);
        return Ok(checks.judge(super::CERTIFIED_CODE, detail).owing(open));
    }
    let code = if open.is_empty() {
        "ALL_CLAIMS_ADMITTED"
    } else {
        "CLAIM_SCOPED"
    };
    let receipt = Datum::Map(
        admitted
            .into_iter()
            .map(|(id, bound)| (id, Datum::Text(bound)))
            .collect(),
    );
    let detail = Datum::map([("admitted", receipt), ("unadmitted", names(open.clone()))]);
    Ok(certified(code, detail).owing(open))
}
