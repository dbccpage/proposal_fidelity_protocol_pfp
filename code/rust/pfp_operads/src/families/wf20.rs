//! WF20, derivation loop with lift grants: the WF9 repair loop, with a structural grant when
//! the repair stops improving.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf20:v1
//!
//! The domain is the XOR repair of [`super::xor`]. When an attempt's measure is not strictly
//! below the last measure the host could read, the host adds a grant to every later prompt: the
//! graph's fundamental cycles, or its chords if the reply asked for `chords`. The function that
//! builds a grant is given the graph and nothing else, so a grant cannot depend on the labels or
//! on any repair.
//!
//! A reply may name the grant it wants in `lift_request`. A request for anything other than
//! `fundamental_cycles` or `chords` ends the run as `LIFT_SCOPE_VIOLATION`. Otherwise the run is
//! certified as `DERIVED` on an accepted attempt, and refused as `HALTED_ON_LIMIT` when the
//! attempts run out or `HALTED_ON_BUDGET` when a reply is missing.
//!
//! Task: the XOR task, and optionally `max_attempts`, 1 to 5 (default 5).
//!
//! [`derive`] is the loop itself, for any domain that can assess a reply. WF33 and WF40 run it
//! on parts of their own tasks.

use crate::datum::Datum;
use crate::exact::rational;
use crate::graph::Graph;

use super::attempts::{limit, row, unread, with_residual, Assessment, Fuel};
use super::{refused, xor, Checks, Family, Run, Stop, Verdict};

/// The most attempts a derivation loop makes.
pub const LOOP_LIMIT: usize = 5;

/// The grants a reply may ask for. The first is given when a stalled reply asks for none.
pub const LIFTS: [&str; 2] = ["fundamental_cycles", "chords"];

pub const FAMILY: Family = Family {
    workflow: "WF20",
    name: "Derivation loop with lift grants",
    host_check: "structural_lift_grant_loop",
    validate,
    walk,
};

/// Why a derivation loop ended.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Halt {
    /// An attempt was accepted.
    Certificate,
    /// A reply was missing.
    Budget,
    /// The shared fuel ran out before an attempt could be asked for.
    Fuel,
    /// Every attempt was used.
    Limit,
    /// A reply asked for a grant outside [`LIFTS`].
    Scope,
}

impl Halt {
    pub fn name(self) -> &'static str {
        match self {
            Halt::Certificate => "certificate",
            Halt::Budget => "budget",
            Halt::Fuel => "fuel",
            Halt::Limit => "limit",
            Halt::Scope => "scope",
        }
    }
}

/// One derivation loop to run: the task put to the model, the graph grants are built from, the
/// text before each stage name, and the number of attempts.
pub struct Loop<'t> {
    pub task: &'t Datum,
    pub graph: &'t Graph,
    pub prefix: &'t str,
    pub limit: usize,
}

/// How a derivation loop ended.
pub struct Derivation<'a> {
    pub halt: Halt,
    pub trail: Vec<Datum>,
    /// The attempt and kind of each grant given, without its data.
    pub grants: Vec<Datum>,
    /// The accepted reply, when the loop ended on one.
    pub accepted: Option<&'a Datum>,
}

/// The data of one grant, from the graph alone.
pub fn grant(graph: &Graph, kind: &str) -> Datum {
    if kind == "chords" {
        return Datum::map([("chords", Datum::from(graph.forest().chords))]);
    }
    let cycles = graph.fundamental_cycles().into_iter().map(|cycle| {
        let steps = cycle
            .into_iter()
            .map(|(edge, sign)| Datum::List(vec![Datum::from(edge), Datum::from(i64::from(sign))]));
        Datum::List(steps.collect())
    });
    Datum::map([("fundamental_cycles", Datum::List(cycles.collect()))])
}

/// The grant a reply asks for: nothing, one of [`LIFTS`], or the request it may not make.
fn request(reply: &Datum) -> Result<Option<&'static str>, String> {
    match reply.get("lift_request") {
        None | Some(Datum::Null) => Ok(None),
        Some(asked) => LIFTS
            .iter()
            .find(|kind| asked.as_text() == Some(kind))
            .map(|kind| Some(*kind))
            .ok_or_else(|| {
                asked
                    .as_text()
                    .map_or_else(|| asked.canonical(), str::to_owned)
            }),
    }
}

/// Run one derivation loop. Each attempt draws one unit of `fuel` first, when there is any to
/// share.
pub fn derive<'a>(
    run: &mut Run<'a>,
    turn: &Loop,
    mut fuel: Option<&mut Fuel>,
    assess: &dyn Fn(&Datum) -> Result<Assessment, String>,
) -> Result<Derivation<'a>, Stop> {
    let base = run.prompt_for(turn.task);
    let mut out = Derivation {
        halt: Halt::Limit,
        trail: Vec::new(),
        grants: Vec::new(),
        accepted: None,
    };
    let (mut prompt, mut granted, mut previous) = (base.clone(), String::new(), None);
    for attempt in 0..turn.limit {
        if fuel.as_mut().is_some_and(|fuel| !fuel.draw()) {
            out.halt = Halt::Fuel;
            return Ok(out);
        }
        let stage = format!("{}attempt:{attempt}", turn.prefix);
        let Some(reply) = run.ask(&stage, prompt)? else {
            out.halt = Halt::Budget;
            return Ok(out);
        };
        let asked = match request(reply) {
            Ok(asked) => asked,
            Err(outside) => {
                out.halt = Halt::Scope;
                out.trail.push(Datum::map([
                    ("attempt", Datum::from(attempt)),
                    ("lift_request", Datum::text(outside)),
                ]));
                return Ok(out);
            }
        };
        let finding = assess(reply).unwrap_or_else(unread);
        out.trail.push(row(attempt, &finding));
        if finding.accepted {
            out.halt = Halt::Certificate;
            out.accepted = Some(reply);
            return Ok(out);
        }
        let measure = rational(&finding.measure);
        let stalled = previous
            .as_ref()
            .is_some_and(|before| measure.as_ref().is_none_or(|now| now >= before));
        if stalled {
            let kind = asked.unwrap_or(LIFTS[0]);
            out.grants.push(Datum::map([
                ("attempt", Datum::from(attempt)),
                ("kind", Datum::from(kind)),
            ]));
            granted.push_str("\nLIFT_REQUEST grant: ");
            granted.push_str(&grant(turn.graph, kind).canonical());
        }
        previous = measure.or(previous);
        prompt = with_residual(&base, &finding.residual) + &granted;
    }
    Ok(out)
}

fn validate(task: &Datum, _sealed: &Datum) -> Result<(), String> {
    xor::read(task)?;
    limit(task, LOOP_LIMIT, LOOP_LIMIT).map(|_| ())
}

fn walk(run: &mut Run, checks: &mut Checks) -> Result<Verdict, Stop> {
    let labelled = xor::read(run.task).map_err(Stop::Malformed)?;
    let turn = Loop {
        task: run.task,
        graph: &labelled.graph,
        prefix: "",
        limit: limit(run.task, LOOP_LIMIT, LOOP_LIMIT).map_err(Stop::Malformed)?,
    };
    let derivation = derive(run, &turn, None, &|reply| labelled.assess(reply))?;
    if derivation.halt == Halt::Scope {
        let last = derivation.trail.last().cloned().unwrap_or(Datum::Null);
        checks.record("lift_request_structural", false, &last);
        let detail = Datum::map([("trail", Datum::List(derivation.trail))]);
        return Ok(refused("LIFT_SCOPE_VIOLATION", detail));
    }
    let halt = derivation.halt.name();
    let detail = Datum::map([
        ("attempts", Datum::from(derivation.trail.len())),
        ("grants", Datum::List(derivation.grants)),
    ]);
    if !checks.record(
        "certificate_within_loop_limit",
        derivation.halt == Halt::Certificate,
        &Datum::from(halt),
    ) {
        return Ok(refused(
            &format!("HALTED_ON_{}", halt.to_uppercase()),
            detail,
        ));
    }
    Ok(checks.judge("DERIVED", detail))
}
