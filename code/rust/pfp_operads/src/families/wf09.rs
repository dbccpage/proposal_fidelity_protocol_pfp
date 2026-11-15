//! WF9, bounded check-and-repair: check a reply, hand back only what is still wrong, and stop
//! after a fixed number of attempts.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf09:v1
//!
//! The domain is the XOR repair of [`super::xor`]. Each attempt is assessed by the host. A
//! rejected attempt is followed by the same prompt with the host's residual under it: which
//! fundamental cycles are still odd and how many edges were flipped. The run is certified when
//! an attempt is accepted within the limit, and refused when the limit is reached or a reply is
//! missing. A reply the host cannot read uses up an attempt.
//!
//! Task: the XOR task, and optionally `max_attempts`, 1 to 8 (default 3).
//!
//! [`bounded`] is the loop itself, for any domain that can assess a reply.

use crate::datum::Datum;

use super::attempts::{limit, row, unread, with_residual, Assessment};
use super::{certified, refused, xor, Checks, Family, Run, Stop, Verdict};

pub const DEFAULT_ATTEMPTS: usize = 3;
pub const MAX_ATTEMPTS: usize = 8;

pub const FAMILY: Family = Family {
    workflow: "WF9",
    name: "Bounded check-and-repair",
    host_check: "xor_cycle_minimal_repair",
    validate,
    walk,
};

fn validate(task: &Datum, _sealed: &Datum) -> Result<(), String> {
    xor::read(task)?;
    limit(task, DEFAULT_ATTEMPTS, MAX_ATTEMPTS).map(|_| ())
}

/// Ask up to `limit` times, assessing each reply and carrying its residual into the next prompt.
/// Certified on the first accepted attempt; refused when the attempts run out or a reply is
/// missing.
pub fn bounded(
    run: &mut Run,
    checks: &mut Checks,
    limit: usize,
    assess: &mut dyn FnMut(&Datum) -> Result<Assessment, String>,
) -> Result<Verdict, Stop> {
    let mut prompt = run.prompt();
    let mut trail = Vec::new();
    for attempt in 0..limit {
        let Some(reply) = run.ask(&format!("attempt:{attempt}"), prompt)? else {
            break;
        };
        let finding = assess(reply).unwrap_or_else(unread);
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
        prompt = with_residual(&run.prompt(), &finding.residual);
    }
    checks.record("accepted_within_limit", false, &Datum::List(trail.clone()));
    let detail = Datum::map([
        ("attempts", Datum::from(trail.len())),
        ("trail", Datum::List(trail)),
    ]);
    Ok(refused("REPAIR_LIMIT_EXHAUSTED", detail))
}

fn walk(run: &mut Run, checks: &mut Checks) -> Result<Verdict, Stop> {
    let labelled = xor::read(run.task).map_err(Stop::Malformed)?;
    let limit = limit(run.task, DEFAULT_ATTEMPTS, MAX_ATTEMPTS).map_err(Stop::Malformed)?;
    bounded(run, checks, limit, &mut |reply| labelled.assess(reply))
}
