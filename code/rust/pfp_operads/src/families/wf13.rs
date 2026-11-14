//! WF13, exact-domain capsule battery: every capsule is judged by the checker of its own domain.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf13:v1
//!
//! A capsule is one small exact question in a named domain (see [`super::domains`]). Before any
//! capsule is put to the model the host checks that it has a checker for every domain named; a
//! battery with an unknown domain is refused whole. Each capsule is then asked on its own and
//! its reply judged by its domain's checker.
//!
//! The battery is certified only when every capsule passes. A capsule with no reply, or with a
//! reply the checker cannot read, counts as failed, so the denominator is always the number of
//! capsules declared. Results are reported per domain; no average across domains is formed.
//!
//! Task: `capsules`, a nonempty list of `{"id", "domain", "data"}` with distinct text ids. Reply
//! to each capsule: what its domain's checker reads.

use std::collections::{BTreeMap, BTreeSet};

use crate::datum::Datum;

use super::domains::checker;
use super::{refused, Checks, Family, Run, Stop, Verdict};

pub const FAMILY: Family = Family {
    workflow: "WF13",
    name: "Exact-domain capsule battery",
    host_check: "per_domain_registered_checker",
    validate,
    walk,
};

struct Capsule<'a> {
    id: &'a str,
    domain: &'a str,
    data: &'a Datum,
    whole: &'a Datum,
}

fn capsule(whole: &Datum) -> Option<Capsule<'_>> {
    Some(Capsule {
        id: whole.get("id")?.as_text()?,
        domain: whole.get("domain")?.as_text()?,
        data: whole.get("data").filter(|data| data.is_map())?,
        whole,
    })
}

fn capsules(task: &Datum) -> Result<Vec<Capsule<'_>>, String> {
    let capsules: Vec<Capsule> = task
        .get("capsules")
        .and_then(Datum::as_list)
        .filter(|list| !list.is_empty())
        .ok_or("capsules must be a nonempty list")?
        .iter()
        .map(capsule)
        .collect::<Option<_>>()
        .ok_or("every capsule needs a text id, a text domain and a data object")?;
    let ids: BTreeSet<&str> = capsules.iter().map(|capsule| capsule.id).collect();
    if ids.len() != capsules.len() {
        return Err("capsule ids must be unique".to_owned());
    }
    Ok(capsules)
}

fn validate(task: &Datum, _sealed: &Datum) -> Result<(), String> {
    capsules(task).map(|_| ())
}

/// What the model is shown for one capsule: the capsule under the task's statement.
fn shown(capsule: &Datum, task: &Datum) -> Datum {
    let mut shown = match capsule {
        Datum::Map(map) => map.clone(),
        _ => BTreeMap::new(),
    };
    shown.remove("statement");
    if let Some(statement) = task.get("statement") {
        shown.insert("statement".to_owned(), statement.clone());
    }
    Datum::Map(shown)
}

fn walk(run: &mut Run, checks: &mut Checks) -> Result<Verdict, Stop> {
    let capsules = capsules(run.task).map_err(Stop::Malformed)?;
    let unregistered: BTreeSet<&str> = capsules
        .iter()
        .map(|capsule| capsule.domain)
        .filter(|domain| checker(domain).is_none())
        .collect();
    let unregistered = Datum::from(unregistered.into_iter().collect::<Vec<_>>());
    if !checks.record(
        "checkers_registered_before_dispatch",
        unregistered == Datum::List(Vec::new()),
        &unregistered,
    ) {
        return Ok(refused(
            "UNREGISTERED_DOMAIN",
            Datum::map([("unregistered", unregistered)]),
        ));
    }
    let mut tallies: BTreeMap<&str, (usize, usize)> = BTreeMap::new();
    for capsule in &capsules {
        let stage = format!("capsule:{}", capsule.id);
        let prompt = run.prompt_for(&shown(capsule.whole, run.task));
        let (passed, witness) = match (run.ask(&stage, prompt)?, checker(capsule.domain)) {
            (Some(reply), Some(check)) => check(capsule.data, reply)
                .unwrap_or_else(|reason| (false, Datum::map([("malformed", Datum::text(reason))]))),
            _ => (false, Datum::map([("reply", Datum::Null)])),
        };
        let tally = tallies.entry(capsule.domain).or_default();
        tally.0 += usize::from(passed);
        tally.1 += 1;
        checks.record(&stage, passed, &witness);
    }
    let per_domain = Datum::Map(
        tallies
            .into_iter()
            .map(|(domain, (passed, total))| {
                let tally = Datum::map([
                    ("passed", Datum::from(passed)),
                    ("total", Datum::from(total)),
                ]);
                (domain.to_owned(), tally)
            })
            .collect(),
    );
    Ok(checks.judge(
        "BATTERY_PASSED",
        Datum::map([
            ("per_domain", per_domain),
            ("denominator", Datum::from(capsules.len())),
        ]),
    ))
}
