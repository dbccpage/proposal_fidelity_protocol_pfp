//! WF42, reasoning-trace validation: read a claim graph out of a trace and certify it, or
//! certify its obstruction.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf42:v1
//!
//! A trace is a list of steps written `u - v = k`, optionally after a label such as `s1:`. The
//! host reads each step as the edge from `v` to `u` with value `k`, so a step is a value on an
//! edge of a graph whose vertices are the names the steps use. A trace holds at most eight
//! steps.
//!
//! The host finds `Phi`, the largest `z . c` over the vectors `z` of `-1`, `0` and `1` that are
//! circulations on the graph. It is the least total size of a correction that makes the steps
//! a coboundary, and it is zero exactly when they already are one. The reply states `CONSISTENT`
//! or `OBSTRUCTED`, and the host records, in this order:
//!
//! * `status_matches_obstruction`: the status says `OBSTRUCTED` exactly when `Phi` is above
//!   zero. A trace that fails it is refused as `HIDDEN_OBSTRUCTION` when `Phi` is above zero and
//!   as `FALSE_OBSTRUCTION` when it is not; both carry `Phi` and the circulation found.
//! * when `Phi` is above zero, `correction_closes_cycles` (the steps less the reply's
//!   `correction`, one integer per step, are a coboundary) and `primal_equals_dual` (the
//!   correction has total size `Phi`). With both held the trace stands as the typed refusal
//!   `TRACE_OBSTRUCTED`.
//! * when `Phi` is zero, `potential_explains_steps` (the reply's `potential`, an object with an
//!   exact integer for every name in the steps, explains every step),
//!   `conclusion_forced_by_steps` (the `conclusion`, a step of the same form, joins two names
//!   the steps already join) and `conclusion_matches_steps` (and the potential agrees with its
//!   value). All three held, the trace is certified as `TRACE_VALID`.

use std::sync::LazyLock;

use num_bigint::BigInt;
use num_traits::{Signed, Zero};
use regex::Regex;

use crate::datum::Datum;
use crate::exact::Rational;
use crate::graph::{Forest, Graph};

use super::labelled::{self, Labelled};
use super::reading::integers;
use super::{
    no_reply, refused, require, typed_refusal, Checks, Family, Run, Stop, Verdict, CERTIFIED_CODE,
};

pub const FAMILY: Family = Family {
    workflow: "WF42",
    name: "Reasoning-trace validation",
    host_check: "rational_lp_primal_dual_check",
    validate,
    walk,
};

/// The most steps a trace may hold.
pub const LIMIT: usize = 8;

/// A step: an optional label, then two names, then the difference as an integer.
static STEP: LazyLock<Option<Regex>> = LazyLock::new(|| {
    Regex::new(r"^\s*(?:\w+:\s*)?([a-z]\w*)\s*-\s*([a-z]\w*)\s*=\s*(-?[0-9]+)\s*$").ok()
});

/// One step `u - v = k`: the value `k` on the edge from `v` to `u`.
struct Claim {
    tail: String,
    head: String,
    value: BigInt,
}

fn claim(line: Option<&Datum>) -> Result<Claim, Stop> {
    let text = line
        .and_then(Datum::as_text)
        .ok_or_else(|| Stop::Malformed("trace steps must be strings".to_owned()))?;
    let found = STEP.as_ref().and_then(|step| step.captures(text));
    let parsed = found.and_then(|found| {
        let head = found.get(1)?.as_str().to_owned();
        let tail = found.get(2)?.as_str().to_owned();
        let value = found.get(3)?.as_str().parse().ok()?;
        Some(Claim { tail, head, value })
    });
    parsed.ok_or_else(|| Stop::Malformed(format!("extractor cannot parse step {text:?}")))
}

fn validate(_task: &Datum, _sealed: &Datum) -> Result<(), String> {
    Ok(())
}

/// `Phi`, the most `z . c` can be over circulations `z` with entries `-1`, `0` and `1`, and the
/// first circulation that reaches it: the first in the order that counts the first edge's entry
/// slowest, upwards from `-1`.
fn dual(graph: &Graph, values: &[BigInt]) -> Result<(BigInt, Vec<i8>), Stop> {
    let edges = graph.edges();
    require(edges.len() <= LIMIT, "trace graphs are limited to 8 claims")?;
    let mut candidates: Vec<Vec<i8>> = vec![Vec::new()];
    for _ in edges {
        candidates = candidates
            .into_iter()
            .flat_map(|prefix| {
                [-1, 0, 1].map(|step| {
                    let mut next = prefix.clone();
                    next.push(step);
                    next
                })
            })
            .collect();
    }
    let mut best = BigInt::zero();
    let mut found = vec![0; edges.len()];
    for flow in candidates {
        let mut net = vec![0_i64; graph.names().len()];
        for (&(from, to), &step) in edges.iter().zip(&flow) {
            if let Some(slot) = net.get_mut(from) {
                *slot -= i64::from(step);
            }
            if let Some(slot) = net.get_mut(to) {
                *slot += i64::from(step);
            }
        }
        let worth: BigInt = flow
            .iter()
            .zip(values)
            .map(|(&step, value)| BigInt::from(step) * value)
            .sum();
        if net.iter().all(|at| *at == 0) && worth > best {
            best = worth;
            found = flow;
        }
    }
    Ok((best, found))
}

/// The same value on every edge, as exact rationals.
fn rationals_of(values: &[BigInt]) -> Vec<Rational> {
    values.iter().cloned().map(Rational::from_integer).collect()
}

/// The root of the tree the forest hangs a vertex in.
fn root(forest: &Forest, mut vertex: usize) -> usize {
    while let Some(Some((above, _, _))) = forest.parent.get(vertex) {
        vertex = *above;
    }
    vertex
}

fn witness(phi: &BigInt, flow: &[i8]) -> Datum {
    let flow = flow.iter().map(|&step| Datum::Int(BigInt::from(step)));
    Datum::map([
        ("Phi", Datum::Int(phi.clone())),
        ("dual", Datum::List(flow.collect())),
    ])
}

/// The steps are not a coboundary: the correction must close every cycle at total size `Phi`.
fn obstructed(
    reply: &Datum,
    graph: &Graph,
    values: &[BigInt],
    phi: &BigInt,
    witness: Datum,
    checks: &mut Checks,
) -> Result<Verdict, Stop> {
    let correction = reply
        .get("correction")
        .and_then(integers)
        .ok_or_else(|| Stop::Malformed("correction must be a list of exact integers".to_owned()))?;
    require(correction.len() == values.len(), "one correction per step")?;
    let corrected: Vec<BigInt> = values
        .iter()
        .zip(&correction)
        .map(|(value, change)| value - change)
        .collect();
    checks.record(
        "correction_closes_cycles",
        graph.defect(&rationals_of(&corrected)).is_zero(),
        &Datum::from(correction.clone()),
    );
    let size: BigInt = correction.iter().map(Signed::abs).sum();
    checks.record("primal_equals_dual", size == *phi, &witness);
    if checks.certified() {
        Ok(typed_refusal("TRACE_OBSTRUCTED", witness))
    } else {
        Ok(checks.judge(CERTIFIED_CODE, witness))
    }
}

/// The steps are a coboundary: the potential must explain them and the conclusion follow.
fn consistent(
    reply: &Datum,
    named: &Labelled,
    values: &[BigInt],
    witness: Datum,
    checks: &mut Checks,
) -> Result<Verdict, Stop> {
    let given = reply.get("potential").filter(|given| given.is_map());
    let given = given.ok_or_else(|| Stop::Malformed("potential object required".to_owned()))?;
    let potential = named
        .by_name(given, |entry| entry.as_int().cloned())
        .ok_or_else(|| Stop::Malformed("potential must be an exact int".to_owned()))?;
    let residual = named
        .graph
        .residual(&rationals_of(values), &rationals_of(&potential));
    checks.record(
        "potential_explains_steps",
        residual.iter().all(Zero::is_zero),
        &Datum::from(potential.clone()),
    );
    let conclusion = claim(reply.get("conclusion"))?;
    let place = |name: &str| named.names().iter().position(|known| known == name);
    let ends = place(&conclusion.tail).zip(place(&conclusion.head));
    let forest = named.graph.forest();
    let joined = ends.filter(|&(tail, head)| root(&forest, tail) == root(&forest, head));
    let evidence = Datum::List(vec![
        Datum::text(conclusion.head.clone()),
        Datum::text(conclusion.tail.clone()),
    ]);
    checks.record("conclusion_forced_by_steps", joined.is_some(), &evidence);
    let difference =
        joined.and_then(|(tail, head)| Some(potential.get(head)? - potential.get(tail)?));
    let matches = difference.is_some_and(|difference| difference == conclusion.value);
    let said = Datum::List(vec![
        Datum::text(conclusion.head),
        Datum::text(conclusion.tail),
        Datum::Int(conclusion.value),
    ]);
    checks.record("conclusion_matches_steps", matches, &said);
    Ok(checks.judge("TRACE_VALID", witness))
}

fn walk(run: &mut Run, checks: &mut Checks) -> Result<Verdict, Stop> {
    let Some(reply) = run.ask("solve", run.prompt())? else {
        return Ok(no_reply());
    };
    let trace = reply.get("trace").and_then(Datum::as_list);
    let trace = trace.ok_or_else(|| Stop::Malformed("trace list required".to_owned()))?;
    let status = reply.get("status").and_then(Datum::as_text);
    let status = status.filter(|status| matches!(*status, "CONSISTENT" | "OBSTRUCTED"));
    let status = status
        .ok_or_else(|| Stop::Malformed("status must be CONSISTENT or OBSTRUCTED".to_owned()))?;
    let claims: Vec<Claim> = trace
        .iter()
        .map(|line| claim(Some(line)))
        .collect::<Result<_, _>>()?;
    let edges = Datum::List(
        claims
            .iter()
            .map(|step| {
                Datum::List(vec![
                    Datum::text(step.tail.clone()),
                    Datum::text(step.head.clone()),
                ])
            })
            .collect(),
    );
    let named = labelled::read(&edges)
        .ok_or_else(|| Stop::Malformed("trace steps must name a graph".to_owned()))?;
    let values: Vec<BigInt> = claims.into_iter().map(|step| step.value).collect();
    let (phi, flow) = dual(&named.graph, &values)?;
    let witness = witness(&phi, &flow);
    let obstruction = phi.is_positive();
    if !checks.record(
        "status_matches_obstruction",
        (status == "OBSTRUCTED") == obstruction,
        &witness,
    ) {
        let code = if obstruction {
            "HIDDEN_OBSTRUCTION"
        } else {
            "FALSE_OBSTRUCTION"
        };
        return Ok(refused(code, witness));
    }
    if obstruction {
        obstructed(reply, &named.graph, &values, &phi, witness, checks)
    } else {
        consistent(reply, &named, &values, witness, checks)
    }
}
