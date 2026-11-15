//! WF24, pinned-token scratchpad: the holonomy of a loop, with every partial product shown.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf24:v1
//!
//! The task gives a permutation of `n` points for each link and a loop of tokens: `eK+` is the
//! permutation of link `eK` and `eK-` its inverse. The reply echoes the tokens, lists the
//! partial product after each token, and gives the holonomy and whether it is the identity.
//!
//! The host folds the loop twice, by composing permutations and by multiplying permutation
//! matrices, and records that the two agree. The reply is certified only when its tokens are
//! the loop's, every partial product is right, and its holonomy and flatness are the host's.
//!
//! Task: `n`, 1 to 64; `links`, an object of permutations of `n` points; `loop`, 1 to 4096
//! tokens on declared links. Reply: `{"tokens", "scratchpad", "holonomy", "flat"}`.

use std::collections::BTreeMap;

use crate::datum::Datum;
use crate::perm::{self, Perm};

use super::domains::permutation;
use super::{no_reply, Checks, Family, Run, Stop, Verdict};

pub const MAX_POINTS: usize = 64;
pub const MAX_LOOP: usize = 4096;

pub const FAMILY: Family = Family {
    workflow: "WF24",
    name: "Pinned-token operational scratchpad",
    host_check: "dual_holonomy_checkers",
    validate,
    walk,
};

struct Task {
    points: usize,
    /// The permutation each token of the loop stands for, in loop order.
    steps: Vec<Perm>,
}

/// The permutation a token stands for: `eK+` is link `eK`, `eK-` its inverse.
fn step(token: &Datum, links: &BTreeMap<String, Perm>) -> Option<Perm> {
    let token = token.as_text()?;
    let (name, forward) = match (token.strip_suffix('+'), token.strip_suffix('-')) {
        (Some(name), _) => (name, true),
        (_, Some(name)) => (name, false),
        _ => return None,
    };
    let number = name.strip_prefix('e')?;
    if number.is_empty() || !number.bytes().all(|byte| byte.is_ascii_digit()) {
        return None;
    }
    let link = links.get(name)?;
    Some(if forward {
        link.clone()
    } else {
        perm::inverse(link)
    })
}

fn task(task: &Datum) -> Result<Task, String> {
    let points = task
        .get("n")
        .and_then(Datum::as_count)
        .filter(|points| (1..=MAX_POINTS).contains(points))
        .ok_or(format!("n must be an exact integer from 1 to {MAX_POINTS}"))?;
    let Some(Datum::Map(declared)) = task.get("links") else {
        return Err("links must be an object".to_owned());
    };
    let links: BTreeMap<String, Perm> = declared
        .iter()
        .map(|(name, link)| Some((name.clone(), perm::read(link, points)?)))
        .collect::<Option<_>>()
        .ok_or(format!(
            "every link must be a permutation of {points} points"
        ))?;
    let steps = task
        .get("loop")
        .and_then(Datum::as_list)
        .filter(|tokens| (1..=MAX_LOOP).contains(&tokens.len()))
        .ok_or(format!("loop must be a list of 1 to {MAX_LOOP} tokens"))?
        .iter()
        .map(|token| step(token, &links))
        .collect::<Option<_>>()
        .ok_or("loop tokens must be pinned eK+ / eK- on declared links")?;
    Ok(Task { points, steps })
}

fn validate(public: &Datum, _sealed: &Datum) -> Result<(), String> {
    task(public).map(|_| ())
}

/// The first step at which the reply's scratchpad differs from the true partial products: the
/// first unequal pair, or the length of the shorter list when one is a prefix of the other.
fn first_bad_step(written: &[Perm], chain: &[Perm]) -> Option<usize> {
    written
        .iter()
        .zip(chain)
        .position(|(given, truth)| given != truth)
        .or_else(|| (written.len() != chain.len()).then(|| written.len().min(chain.len())))
}

fn walk(run: &mut Run, checks: &mut Checks) -> Result<Verdict, Stop> {
    let task = task(run.task).map_err(Stop::Malformed)?;
    let Some(reply) = run.ask("solve", run.prompt())? else {
        return Ok(no_reply());
    };
    let (Some(tokens), Some(scratchpad)) = (
        reply
            .get("tokens")
            .filter(|tokens| tokens.as_list().is_some()),
        reply.get("scratchpad").and_then(Datum::as_list),
    ) else {
        return Err(Stop::Malformed("tokens and scratchpad required".to_owned()));
    };
    let Some(Datum::Bool(flat)) = reply.get("flat") else {
        return Err(Stop::Malformed("flat must be a bool".to_owned()));
    };
    let written: Vec<Perm> = scratchpad
        .iter()
        .map(|entry| perm::read(entry, task.points))
        .collect::<Option<_>>()
        .ok_or_else(|| {
            Stop::Malformed(format!(
                "every scratchpad entry must be a permutation of {} points",
                task.points
            ))
        })?;
    let claimed = permutation(reply, "holonomy", task.points).map_err(Stop::Malformed)?;

    let identity = perm::identity(task.points);
    let mut chain: Vec<Perm> = Vec::new();
    let mut holonomy = identity.clone();
    let mut matrices = perm::matrix(&identity);
    for step in &task.steps {
        holonomy = perm::compose(&holonomy, step);
        chain.push(holonomy.clone());
        matrices = perm::product(&matrices, &perm::matrix(step));
    }
    let second = perm::of_matrix(&matrices);
    let bad = first_bad_step(&written, &chain);
    let is_flat = holonomy == identity;
    let truth = Datum::from(holonomy.clone());

    checks.record(
        "tokens_pinned",
        Some(tokens) == run.task.get("loop"),
        tokens,
    );
    checks.record(
        "scratchpad_steps_exact",
        bad.is_none(),
        &bad.map_or(Datum::Null, Datum::from),
    );
    checks.record(
        "dual_checkers_agree",
        second.as_ref() == Some(&holonomy),
        &Datum::map([
            ("composed", truth.clone()),
            ("matrices", second.map_or(Datum::Null, Datum::from)),
        ]),
    );
    checks.record("holonomy_matches", claimed == holonomy, &truth);
    checks.record("flatness_matches", *flat == is_flat, &Datum::Bool(is_flat));
    Ok(checks.judge(
        super::CERTIFIED_CODE,
        Datum::map([
            ("holonomy", truth),
            ("flat", Datum::Bool(is_flat)),
            ("first_bad_step", bad.map_or(Datum::Null, Datum::from)),
        ]),
    ))
}
