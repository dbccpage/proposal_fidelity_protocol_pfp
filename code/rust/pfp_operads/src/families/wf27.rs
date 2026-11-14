//! WF27, hinted retraction: the WF9 repair loop with a structural hint after each rejection and
//! a stop when the proposer is going round in circles.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf27:v1
//!
//! The domain is the XOR repair of [`super::xor`]. After a rejected attempt the next prompt
//! carries the host's residual and a hint built only from that residual and the public graph:
//! the vertices of each fundamental cycle that is still odd. The hint never names an edge to
//! flip.
//!
//! If the residual of an attempt equals the residual three attempts earlier, the run stops and
//! is refused as `STATIONARY_LOOP`. A reply the host cannot read is never taken as that signal.
//! Reaching the attempt limit, or a missing reply, is refused as `TURN_CAP_EXHAUSTED`.
//!
//! Task: the XOR task, and optionally `max_attempts`, 1 to 8 (default 3).

use std::collections::BTreeSet;

use num_bigint::BigInt;

use crate::datum::Datum;

use super::attempts::{limit, row, unread, with_residual};
use super::wf09::{DEFAULT_ATTEMPTS, MAX_ATTEMPTS};
use super::xor::{self, Labelled};
use super::{certified, refused, Checks, Family, Run, Stop, Verdict};

/// How many attempts back the host looks for the same residual.
pub const PERIOD: usize = 3;

pub const FAMILY: Family = Family {
    workflow: "WF27",
    name: "Hinted retraction with a stationary-loop detector",
    host_check: "xor_residual_gate_stationary_loop",
    validate,
    walk,
};

fn validate(task: &Datum, _sealed: &Datum) -> Result<(), String> {
    xor::read(task)?;
    limit(task, DEFAULT_ATTEMPTS, MAX_ATTEMPTS).map(|_| ())
}

/// The odd cycles a residual names, and the vertices of each in ascending order.
fn hint(labelled: &Labelled, residual: &Datum) -> Datum {
    let cycles = labelled.graph.fundamental_cycles();
    let odd: Vec<usize> = residual
        .get("odd_cycles")
        .and_then(Datum::as_list)
        .unwrap_or_default()
        .iter()
        .filter_map(Datum::as_count)
        .filter(|&cycle| cycle < cycles.len())
        .collect();
    let vertices = |cycle: &usize| {
        let on_cycle: BTreeSet<&BigInt> = cycles[*cycle]
            .iter()
            .filter_map(|&(edge, _)| labelled.graph.edges().get(edge))
            .flat_map(|&(from, to)| [from, to])
            .filter_map(|vertex| labelled.graph.names().get(vertex))
            .collect();
        Datum::List(on_cycle.into_iter().cloned().map(Datum::Int).collect())
    };
    Datum::map([
        (
            "cycle_vertices",
            Datum::List(odd.iter().map(vertices).collect()),
        ),
        ("odd_cycles", Datum::from(odd)),
    ])
}

fn walk(run: &mut Run, checks: &mut Checks) -> Result<Verdict, Stop> {
    let labelled = xor::read(run.task).map_err(Stop::Malformed)?;
    let limit = limit(run.task, DEFAULT_ATTEMPTS, MAX_ATTEMPTS).map_err(Stop::Malformed)?;
    let mut prompt = run.prompt();
    let mut trail: Vec<Datum> = Vec::new();
    let mut residuals: Vec<Datum> = Vec::new();
    for attempt in 0..limit {
        let Some(reply) = run.ask(&format!("attempt:{attempt}"), prompt)? else {
            break;
        };
        let finding = labelled.assess(reply).unwrap_or_else(unread);
        trail.push(row(attempt, &finding));
        if finding.accepted {
            checks.record("accepted_within_limit", true, &Datum::List(trail.clone()));
            let code = if attempt == 0 {
                "ACCEPTED_FIRST_TRY"
            } else {
                "REPAIRED"
            };
            let detail = Datum::map([
                ("attempts", Datum::from(attempt + 1)),
                ("trail", Datum::List(trail)),
            ]);
            return Ok(certified(code, detail));
        }
        let read = finding.residual.get("malformed").is_none();
        let earlier = attempt.checked_sub(PERIOD).and_then(|at| residuals.get(at));
        if read && earlier == Some(&finding.residual) {
            checks.record("residual_not_stationary", false, &Datum::List(trail));
            let detail = Datum::map([
                ("turn", Datum::from(attempt)),
                ("repeats_turn", Datum::from(attempt - PERIOD)),
                ("hint", hint(&labelled, &finding.residual)),
                ("residual", finding.residual),
            ]);
            return Ok(refused("STATIONARY_LOOP", detail));
        }
        prompt = format!(
            "{}\nStructural hint: {}",
            with_residual(&run.prompt(), &finding.residual),
            hint(&labelled, &finding.residual).canonical()
        );
        residuals.push(finding.residual);
    }
    checks.record("accepted_within_limit", false, &Datum::List(trail.clone()));
    let detail = Datum::map([
        ("attempts", Datum::from(trail.len())),
        ("trail", Datum::List(trail)),
    ]);
    Ok(refused("TURN_CAP_EXHAUSTED", detail))
}
