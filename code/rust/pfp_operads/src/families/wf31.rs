//! WF31, multi-agent tournament with held-out cross-validation: several proposers fit a public
//! training share, and the host scores each on a sealed held-out share.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf31:v1
//!
//! Each proposer returns the exact coefficients of a polynomial, constant term first. Its score
//! is the number of held-out points the polynomial hits exactly; a reply that cannot be read
//! scores -1. The winner is the highest score, the earlier name on a tie, and it is certified
//! only if it strictly beats the task's declared baseline polynomial on the same points. The run
//! is refused before any proposer is asked when a training id is also a held-out id.
//!
//! Task: `train`, a nonempty list of points with an integer `id`; `proposers`, 1 to 64; optional
//! `baseline_coefficients` (default `[0]`). Sealed: `held_out`, points with `id`, `x` and `y`.
//! Reply of each proposer: `{"coefficients": [c0, c1, ...]}`.

use std::collections::{BTreeMap, BTreeSet};

use num_bigint::BigInt;

use crate::datum::Datum;
use crate::exact::{polynomial, rational, rationals, Rational};

use super::{refused, Checks, Family, Run, Stop, Verdict};

pub const MAX_PROPOSERS: usize = 64;

pub const FAMILY: Family = Family {
    workflow: "WF31",
    name: "Multi-agent tournament with held-out cross-validation",
    host_check: "exact_held_out_referee",
    validate,
    walk,
};

struct Point {
    id: BigInt,
    x: Rational,
    y: Rational,
}

struct Task {
    train_ids: BTreeSet<BigInt>,
    proposers: usize,
    baseline: Vec<Rational>,
    held_out: Vec<Point>,
}

fn id(point: &Datum) -> Option<BigInt> {
    point.get("id").and_then(Datum::as_int).cloned()
}

fn held_out_point(point: &Datum) -> Option<Point> {
    Some(Point {
        id: id(point)?,
        x: rational(point.get("x")?)?,
        y: rational(point.get("y")?)?,
    })
}

fn task(public: &Datum, sealed: &Datum) -> Result<Task, String> {
    let train_ids = public
        .get("train")
        .and_then(Datum::as_list)
        .filter(|points| !points.is_empty())
        .ok_or("train must be a nonempty list of points")?
        .iter()
        .map(id)
        .collect::<Option<_>>()
        .ok_or("every training point needs an exact integer id")?;
    let proposers = public
        .get("proposers")
        .and_then(Datum::as_count)
        .filter(|count| (1..=MAX_PROPOSERS).contains(count))
        .ok_or(format!(
            "proposers must be an exact integer from 1 to {MAX_PROPOSERS}"
        ))?;
    let baseline = match public.get("baseline_coefficients") {
        None => vec![Rational::from_integer(BigInt::from(0))],
        Some(list) => {
            rationals(list).ok_or("baseline_coefficients must be a list of exact rationals")?
        }
    };
    let held_out = match sealed.get("held_out") {
        None => Vec::new(),
        Some(list) => list
            .as_list()
            .ok_or("held_out must be a list of points")?
            .iter()
            .map(held_out_point)
            .collect::<Option<_>>()
            .ok_or("every held-out point needs an integer id and exact rational x and y")?,
    };
    Ok(Task {
        train_ids,
        proposers,
        baseline,
        held_out,
    })
}

fn validate(public: &Datum, sealed: &Datum) -> Result<(), String> {
    task(public, sealed).map(|_| ())
}

/// The number of points the polynomial hits exactly.
fn hits(coefficients: &[Rational], points: &[Point]) -> usize {
    points
        .iter()
        .filter(|point| polynomial(coefficients, &point.x) == point.y)
        .count()
}

/// The highest score, and on a tie the name that sorts first.
fn winner(scores: &BTreeMap<String, i64>) -> Option<(&String, i64)> {
    let mut best: Option<(&String, i64)> = None;
    for (name, &score) in scores {
        if best.is_none_or(|(_, top)| score > top) {
            best = Some((name, score));
        }
    }
    best
}

fn walk(run: &mut Run, checks: &mut Checks) -> Result<Verdict, Stop> {
    let task = task(run.task, run.sealed).map_err(Stop::Malformed)?;
    let overlap: Vec<BigInt> = task
        .held_out
        .iter()
        .map(|point| &point.id)
        .filter(|id| task.train_ids.contains(id))
        .collect::<BTreeSet<_>>()
        .into_iter()
        .cloned()
        .collect();
    let overlap = Datum::from(overlap);
    if !checks.record(
        "splits_disjoint",
        overlap == Datum::List(Vec::new()),
        &overlap,
    ) {
        return Ok(refused("SPLIT_OVERLAP", Datum::map([("overlap", overlap)])));
    }
    let mut scores: BTreeMap<String, i64> = BTreeMap::new();
    for proposer in 0..task.proposers {
        let stage = format!("proposer:{proposer}");
        let Some(reply) = run.ask(&stage, run.prompt())? else {
            continue;
        };
        let score = match reply.get("coefficients").and_then(rationals) {
            Some(coefficients) => {
                i64::try_from(hits(&coefficients, &task.held_out)).unwrap_or(i64::MAX)
            }
            None => -1,
        };
        scores.insert(stage, score);
    }
    let Some((name, top)) = winner(&scores) else {
        return Ok(super::no_reply());
    };
    let baseline = i64::try_from(hits(&task.baseline, &task.held_out)).unwrap_or(i64::MAX);
    let table = Datum::Map(
        scores
            .iter()
            .map(|(name, &score)| (name.clone(), Datum::from(score)))
            .collect(),
    );
    checks.record(
        "winner_beats_baseline",
        top > baseline,
        &Datum::map([
            ("scores", table.clone()),
            ("baseline", Datum::from(baseline)),
        ]),
    );
    Ok(checks.judge(
        "WINNER_SELECTED",
        Datum::map([
            ("winner", Datum::text(name.clone())),
            ("scores", table),
            ("baseline", Datum::from(baseline)),
            ("held_out", Datum::from(task.held_out.len())),
        ]),
    ))
}
