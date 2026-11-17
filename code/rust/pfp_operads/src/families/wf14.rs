//! WF14, immune failure classification: sort refused replies into epitopes, and admit detector
//! rules only when two independent signals hold them.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf14:v1
//!
//! The domain is the monic polynomial with stated rational roots (see [`super::monic`]). The
//! task is `failures`, a nonempty list of `{text, roots}` (and an optional `id` and
//! `provenance` with the text keys `model`, `scaffold`, `precedent` and `lineage`), and
//! `self_panel_sha256`. The sealed part is `self_panel`, a list of the same, clean replies. The
//! reply is `rules`, a nonempty list of `{rule_id, target_epitope, pattern}` with a known
//! `target_epitope` and a pattern in the dialect of [`super::pattern`].
//!
//! The host records, in this order:
//!
//! * `self_panel_sealed`: the digest of the sealed panel is `self_panel_sha256`. Otherwise the
//!   run ends there, refused as `SELF_PANEL_SEAL_BROKEN`.
//! * `self_panel_clean`: the host classifies every panel text as `CLEAN`.
//! * `no_autoimmune_rule`: no rule is killed by the thymus, that is, refused as a pattern or
//!   matching a panel text.
//! * `every_rule_two_signal_admitted`: every rule is `ADMITTED`.
//!
//! A surviving rule is `ADMITTED` when it matches at least one failure and, on every failure it
//! matches in order, the failure is not `CLEAN` (the observer `host.contract_check` reports a
//! `MALFORMED_PAYLOAD` danger for it), the two signals are independent, and the failure's
//! epitope is the rule's `target_epitope`. The first failure that is not so ends the rule's
//! check with its status: `DIAGNOSTIC_ONLY` (matched a clean failure), the refusal code of the
//! decision, `NOT_HELD`, or `EPITOPE_MISMATCH`. A rule that matches no failure is `UNMATCHED`.
//!
//! The run is certified as `RULES_ADMITTED` with `rules` (each rule's status), `epitopes` (how
//! many failures fall under each epitope) and `antibodies` (the custody of each epitope
//! observed: `Provisional` only with three observations that share no model, scaffold,
//! precedent or lineage). When the task names a `ledger_path`, the detail also has
//! `ledger_failures`, the entries the caller writes to that ledger: a `thymus_kill:ID` entry
//! for each killed rule and a `rule_rejected:ID` entry for each other rule that is not
//! admitted.
//!
//! Differences from the Python this replaces: roots must be exact rationals (an integer or text
//! `p/q`); a `rule_id` is text or an integer; an `id` or a provenance value is text; and JSON
//! with a repeated key in a failure text is `MALFORMED_JSON`. A rule pattern that uses syntax
//! the host does not read stops the run as malformed.

use std::collections::BTreeMap;

use crate::datum::Datum;
use crate::exact::{rationals, Rational};

use super::immune::{self, Danger, Fate, Observation, Rule, HOST_OBSERVERS};
use super::monic::{classify, expand, CLEAN, EPITOPES};
use super::pattern::{is_space, Pattern};
use super::reading::object;
use super::{no_reply, refused, sha256_hex, Checks, Family, Run, Stop, Verdict};

pub const FAMILY: Family = Family {
    workflow: "WF14",
    name: "Immune failure classification",
    host_check: "thymus_two_signal_admission",
    validate,
    walk,
};

/// The host check that reports the danger of a failure.
pub const OBSERVER: &str = "host.contract_check";

/// The danger kind the observer reports.
pub const DANGER: &str = "MALFORMED_PAYLOAD";

/// The status of a rule that passed every test.
const ADMITTED: &str = "ADMITTED";

/// The status of a rule the thymus killed.
const KILLED: &str = "KILLED_BY_THYMUS";

/// A reply text and the polynomial it should be.
struct Case<'t> {
    text: &'t str,
    expected: Vec<Rational>,
}

/// A failure: a case and what the antibody registry keeps of it.
struct Failure<'t> {
    case: Case<'t>,
    id: String,
    keys: [String; 4],
}

fn case(entry: &Datum) -> Result<Case<'_>, String> {
    let text = entry
        .get("text")
        .and_then(Datum::as_text)
        .ok_or("each entry needs its text")?;
    let expected = entry
        .get("roots")
        .and_then(rationals)
        .ok_or("roots must be a list of exact rationals")?;
    Ok(Case {
        text,
        expected: expand(&expected),
    })
}

/// A provenance key: its text, or empty when absent.
fn key(provenance: Option<&Datum>, name: &str) -> Result<String, String> {
    match provenance.and_then(|from| from.get(name)) {
        None => Ok(String::new()),
        Some(Datum::Text(text)) => Ok(text.clone()),
        Some(_) => Err(format!("provenance {name} must be text")),
    }
}

fn failure(place: usize, entry: &Datum) -> Result<Failure<'_>, String> {
    let id = match entry.get("id") {
        None => place.to_string(),
        Some(Datum::Text(text)) => text.clone(),
        Some(_) => return Err("a failure id must be text".to_owned()),
    };
    let provenance = entry.get("provenance");
    if provenance.is_some_and(|from| !from.is_map()) {
        return Err("provenance must be an object".to_owned());
    }
    Ok(Failure {
        case: case(entry)?,
        id,
        keys: [
            key(provenance, "model")?,
            key(provenance, "scaffold")?,
            key(provenance, "precedent")?,
            key(provenance, "lineage")?,
        ],
    })
}

fn failures(task: &Datum) -> Result<Vec<Failure<'_>>, String> {
    task.get("failures")
        .and_then(Datum::as_list)
        .filter(|listed| !listed.is_empty())
        .ok_or("failures must be a nonempty list")?
        .iter()
        .enumerate()
        .map(|(place, entry)| failure(place, entry))
        .collect()
}

fn seal(task: &Datum) -> Result<&str, String> {
    task.get("self_panel_sha256")
        .and_then(Datum::as_text)
        .ok_or_else(|| "self panel seal required".to_owned())
}

fn validate(task: &Datum, _sealed: &Datum) -> Result<(), String> {
    failures(task)?;
    seal(task).map(|_| ())
}

fn panel(sealed: &Datum) -> Result<(&Datum, Vec<Case<'_>>), String> {
    let listed = sealed
        .get("self_panel")
        .filter(|listed| listed.as_list().is_some_and(|entries| !entries.is_empty()))
        .ok_or("self_panel must be a nonempty list")?;
    let cases: Result<Vec<Case>, String> = listed
        .as_list()
        .unwrap_or_default()
        .iter()
        .map(case)
        .collect();
    Ok((listed, cases?))
}

/// The id of a rule: text or an integer.
fn rule_id(spec: &Datum) -> Option<String> {
    match spec.get("rule_id") {
        Some(Datum::Text(text)) if !text.chars().all(is_space) => Some(text.clone()),
        Some(Datum::Int(number)) => Some(number.to_string()),
        _ => None,
    }
}

fn rule(spec: &Datum) -> Result<Rule, String> {
    let epitope = spec
        .get("target_epitope")
        .and_then(Datum::as_text)
        .filter(|epitope| EPITOPES.contains(epitope))
        .ok_or("rule needs a known target_epitope")?;
    let id = rule_id(spec).ok_or("bad rule: rule_id must be a nonempty string")?;
    let pattern = spec
        .get("pattern")
        .and_then(Datum::as_text)
        .filter(|pattern| !pattern.chars().all(is_space))
        .ok_or("bad rule: match_pattern must be a nonempty string")?;
    Ok(Rule {
        id,
        epitope: epitope.to_owned(),
        pattern: pattern.to_owned(),
    })
}

fn rules(reply: &Datum) -> Result<Vec<Rule>, String> {
    let listed = reply
        .get("rules")
        .and_then(Datum::as_list)
        .filter(|listed| !listed.is_empty())
        .ok_or("rules must be a nonempty list")?;
    let rules: Vec<Rule> = listed.iter().map(rule).collect::<Result<_, _>>()?;
    let mut ids: Vec<&str> = rules.iter().map(|one| one.id.as_str()).collect();
    ids.sort_unstable();
    ids.dedup();
    if ids.len() != rules.len() {
        return Err("rule ids must be unique".to_owned());
    }
    Ok(rules)
}

/// The status of one surviving rule over the failures it matches, in order.
fn status(
    rule: &Rule,
    compiled: &Pattern,
    failures: &[Failure],
    epitopes: &[&str],
) -> &'static str {
    let mut hits = 0;
    for (one, epitope) in failures.iter().zip(epitopes) {
        let Some(found) = immune::signal1(one.case.text, rule, compiled) else {
            continue;
        };
        hits += 1;
        let danger = (*epitope != CLEAN).then(|| Danger::observed(DANGER, OBSERVER, one.case.text));
        let decision = immune::decide(&[found], danger.as_ref(), &HOST_OBSERVERS);
        let refused = if danger.is_none() {
            Some("DIAGNOSTIC_ONLY")
        } else if decision.code.is_some() {
            decision.code
        } else if *epitope != rule.epitope {
            Some("EPITOPE_MISMATCH")
        } else {
            None
        };
        if let Some(code) = refused {
            return code;
        }
    }
    if hits > 0 {
        ADMITTED
    } else {
        "UNMATCHED"
    }
}

/// The custody of each epitope the failures show.
fn antibodies(failures: &[Failure], epitopes: &[&str]) -> BTreeMap<String, Datum> {
    let mut seen: BTreeMap<&str, Vec<Observation>> = BTreeMap::new();
    for (one, epitope) in failures.iter().zip(epitopes) {
        if *epitope != CLEAN {
            seen.entry(*epitope).or_default().push(Observation {
                occurrence: one.id.clone(),
                keys: one.keys.clone(),
            });
        }
    }
    seen.into_iter()
        .map(|(epitope, observations)| {
            (
                epitope.to_owned(),
                Datum::from(immune::custody(&observations)),
            )
        })
        .collect()
}

fn entry(id: String, class: &str, evidence: String) -> Datum {
    Datum::map([
        ("failure_id", Datum::text(id)),
        ("failure_class", Datum::from(class)),
        ("ddc_trace", Datum::from("CRM")),
        ("evidence_sha256", Datum::text(sha256_hex(&evidence))),
    ])
}

/// The ledger entries for the rules that were not admitted, in rule id order.
fn ledger(statuses: &BTreeMap<String, &str>) -> Datum {
    Datum::List(
        statuses
            .iter()
            .filter(|(_, status)| **status != ADMITTED)
            .map(|(id, status)| {
                let (kind, class) = if *status == KILLED {
                    ("thymus_kill", "BoundaryLeakage")
                } else {
                    ("rule_rejected", "StructuralNonFit")
                };
                entry(format!("{kind}:{id}"), class, format!("{status}:{id}"))
            })
            .collect(),
    )
}

fn walk(run: &mut Run, checks: &mut Checks) -> Result<Verdict, Stop> {
    let failures = failures(run.task).map_err(Stop::Malformed)?;
    let wanted = seal(run.task).map_err(Stop::Malformed)?;
    let (listed, clean) = panel(run.sealed).map_err(Stop::Malformed)?;
    let Some(reply) = run.ask("rules", run.prompt())? else {
        return Ok(no_reply());
    };
    let reply = object(reply, "rules")?;
    let digest = sha256_hex(&listed.canonical());
    if !checks.record("self_panel_sealed", digest == wanted, &Datum::text(digest)) {
        return Ok(refused("SELF_PANEL_SEAL_BROKEN", Datum::map([])));
    }
    let all_clean = clean
        .iter()
        .all(|one| classify(one.text, &one.expected) == CLEAN);
    checks.record("self_panel_clean", all_clean, &Datum::from(clean.len()));
    let rules = rules(reply).map_err(Stop::Malformed)?;
    let texts: Vec<&str> = clean.iter().map(|one| one.text).collect();
    let fates = immune::screen(&rules, &texts).map_err(Stop::Malformed)?;
    let epitopes: Vec<&str> = failures
        .iter()
        .map(|one| classify(one.case.text, &one.case.expected))
        .collect();
    let statuses: BTreeMap<String, &str> = rules
        .iter()
        .zip(&fates)
        .map(|(one, fate)| match fate {
            Fate::Admitted(compiled) => {
                (one.id.clone(), status(one, compiled, &failures, &epitopes))
            }
            Fate::Killed => (one.id.clone(), KILLED),
        })
        .collect();
    let shown = Datum::Map(
        statuses
            .iter()
            .map(|(id, status)| (id.clone(), Datum::from(*status)))
            .collect(),
    );
    let killed = statuses
        .values()
        .filter(|status| **status == KILLED)
        .count();
    checks.record("no_autoimmune_rule", killed == 0, &shown);
    let every = statuses.values().all(|status| *status == ADMITTED);
    checks.record("every_rule_two_signal_admitted", every, &shown);
    let mut counts: BTreeMap<String, usize> = BTreeMap::new();
    for epitope in &epitopes {
        *counts.entry((*epitope).to_owned()).or_default() += 1;
    }
    let mut detail = BTreeMap::from([
        ("rules".to_owned(), shown),
        (
            "epitopes".to_owned(),
            Datum::Map(
                counts
                    .into_iter()
                    .map(|(name, count)| (name, Datum::from(count)))
                    .collect(),
            ),
        ),
        (
            "antibodies".to_owned(),
            Datum::Map(antibodies(&failures, &epitopes)),
        ),
    ]);
    if run
        .task
        .get("ledger_path")
        .and_then(Datum::as_text)
        .is_some_and(|path| !path.is_empty())
    {
        detail.insert("ledger_failures".to_owned(), ledger(&statuses));
    }
    Ok(checks.judge("RULES_ADMITTED", Datum::Map(detail)))
}
