//! WF35, proposal-channel comparison: arms that propose through different channels answer the
//! same weighted digraphs, one fixed grader judges every reply, and a channel's own claim about
//! its answers counts for nothing.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf35:v1
//!
//! The task is `items`, a nonempty list of weighted digraphs (see [`super::duality`]), and
//! `arms`, a list of at least two objects with different text `channel`s, each with the
//! `checker_pin` of the grader it used and the `budget` it ran under.
//!
//! The host records `arms_share_fixed_checker` (every arm's `checker_pin` is
//! [`super::duality::pin`]) and `arms_share_budget` (every arm's `budget` has the same canonical
//! form; a missing budget is `null`). If either fails the run ends there, refused as
//! `ARMS_NOT_MATCHED`, with nothing asked.
//!
//! Otherwise each arm in turn is asked about each item, in order, under the stage
//! `CHANNEL:K` with `K` the item's position. The prompt is the default prompt for the item with
//! its `channel` added, so it names no statement: the item has none. A reply with no text under `text`, or no reply at all, is graded
//! `REFUSED`. A reply stands when the grader gives `HOST_CERTIFIED` or `TYPED_REFUSAL`.
//!
//! * `accept_set_depends_only_on_bytes`: no reply says `accepted` other than the boolean the
//!   grader gave it. The detail lists the replies that do, as `CHANNEL:K`.
//!
//! All held, the comparison is certified as `CHANNELS_COMPARED` with `accepts`, the number of
//! replies that stood for each channel, and `discordant`, the items the first arm's reply stood
//! for and the second's did not (`first_only`) and the other way round (`second_only`).

use std::collections::BTreeMap;

use crate::datum::Datum;

use super::duality::{self, Item};
use super::{refused, Checks, Family, Run, Stop, Verdict};

pub const FAMILY: Family = Family {
    workflow: "WF35",
    name: "Proposal-channel comparison",
    host_check: "channel_blind_fixed_oracle",
    validate,
    walk,
};

/// One graded item: what to ask, and the graph to grade the reply on.
struct Case<'t> {
    asked: &'t Datum,
    item: Item,
}

fn case(asked: &Datum) -> Result<Case<'_>, String> {
    Item::read(asked).map(|item| Case { asked, item })
}

fn items(task: &Datum) -> Result<Vec<Case<'_>>, String> {
    let listed = task
        .get("items")
        .and_then(Datum::as_list)
        .filter(|listed| !listed.is_empty())
        .ok_or("items must be a nonempty list")?;
    listed.iter().map(case).collect()
}

fn named(arm: &Datum) -> Option<(&str, &Datum)> {
    let channel = arm.get("channel").and_then(Datum::as_text)?;
    Some((channel, arm))
}

fn arms(task: &Datum) -> Result<Vec<(&str, &Datum)>, String> {
    let listed = task
        .get("arms")
        .and_then(Datum::as_list)
        .filter(|listed| listed.len() >= 2)
        .ok_or("arms must be a list of at least two")?;
    let arms: Option<Vec<(&str, &Datum)>> = listed.iter().map(named).collect();
    let arms = arms.ok_or("each arm needs its channel as text")?;
    let mut channels: Vec<&str> = arms.iter().map(|(channel, _)| *channel).collect();
    channels.sort_unstable();
    channels.dedup();
    if channels.len() != arms.len() {
        return Err("each arm needs its own channel".to_owned());
    }
    Ok(arms)
}

fn validate(task: &Datum, _sealed: &Datum) -> Result<(), String> {
    items(task)?;
    arms(task).map(|_| ())
}

/// What the item is asked as, for the channel: the item and the channel.
fn question(item: &Datum, channel: &str) -> Datum {
    let mut asked = match item {
        Datum::Map(entries) => entries.clone(),
        _ => BTreeMap::new(),
    };
    asked.insert("channel".to_owned(), Datum::text(channel));
    Datum::Map(asked)
}

/// Whether the reply stands, and whether it claims an acceptance the grader does not give.
fn read(reply: Option<&Datum>, case: &Case) -> (bool, bool) {
    let raw = reply
        .and_then(|reply| reply.get("text"))
        .and_then(Datum::as_text);
    let stands = raw.is_some_and(|raw| duality::grade(&case.item, raw).stands());
    let claim = reply.and_then(|reply| reply.get("accepted"));
    let honest = claim.is_none_or(|claim| *claim == Datum::Bool(stands));
    (stands, honest)
}

fn count(row: &[bool]) -> usize {
    row.iter().filter(|stood| **stood).count()
}

/// The items the first row stood for and the second did not.
fn only(first: &[bool], second: &[bool]) -> usize {
    first
        .iter()
        .zip(second)
        .filter(|(left, right)| **left && !**right)
        .count()
}

fn walk(run: &mut Run, checks: &mut Checks) -> Result<Verdict, Stop> {
    let cases = items(run.task).map_err(Stop::Malformed)?;
    let arms = arms(run.task).map_err(Stop::Malformed)?;
    let pin = duality::pin();
    let pins: Vec<bool> = arms
        .iter()
        .map(|(_, arm)| arm.get("checker_pin").and_then(Datum::as_text) == Some(pin.as_str()))
        .collect();
    let budgets: Vec<Datum> = arms
        .iter()
        .map(|(_, arm)| arm.get("budget").cloned().unwrap_or(Datum::Null))
        .collect();
    let first = budgets.first().map(Datum::canonical);
    let same_budget = budgets
        .iter()
        .map(|budget| Some(budget.canonical()))
        .all(|one| one == first);
    let fixed = pins.iter().all(|pinned| *pinned);
    let shown = Datum::List(pins.into_iter().map(Datum::Bool).collect());
    checks.record("arms_share_fixed_checker", fixed, &shown);
    checks.record("arms_share_budget", same_budget, &Datum::List(budgets));
    if !(fixed && same_budget) {
        return Ok(refused("ARMS_NOT_MATCHED", Datum::map([])));
    }
    let mut rows: Vec<(&str, Vec<bool>)> = Vec::new();
    let mut leaning: Vec<String> = Vec::new();
    for (channel, _) in &arms {
        let mut row = Vec::new();
        for (place, case) in cases.iter().enumerate() {
            let asked = question(case.asked, channel);
            let reply = run.ask(&format!("{channel}:{place}"), run.prompt_for(&asked))?;
            let (stands, honest) = read(reply, case);
            if !honest {
                leaning.push(format!("{channel}:{place}"));
            }
            row.push(stands);
        }
        rows.push((*channel, row));
    }
    let leaning = Datum::List(leaning.into_iter().map(Datum::text).collect());
    checks.record(
        "accept_set_depends_only_on_bytes",
        leaning.as_list().is_some_and(<[Datum]>::is_empty),
        &leaning,
    );
    let accepts: BTreeMap<String, Datum> = rows
        .iter()
        .map(|(channel, row)| ((*channel).to_owned(), Datum::from(count(row))))
        .collect();
    let (first, second) = match rows.as_slice() {
        [(_, first), (_, second), ..] => (first.as_slice(), second.as_slice()),
        _ => (&[][..], &[][..]),
    };
    let discordant = Datum::map([
        ("first_only", Datum::from(only(first, second))),
        ("second_only", Datum::from(only(second, first))),
    ]);
    Ok(checks.judge(
        "CHANNELS_COMPARED",
        Datum::map([("accepts", Datum::Map(accepts)), ("discordant", discordant)]),
    ))
}
