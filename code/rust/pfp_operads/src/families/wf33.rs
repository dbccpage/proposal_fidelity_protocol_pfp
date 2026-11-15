//! WF33, recursive re-entry with shared fuel: split a repair among child derivations that draw
//! on one fuel counter and are each bound to their parent.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf33:v1
//!
//! The domain is the XOR repair of [`super::xor`]. The first reply is a plan: lists of edge
//! indices, one list per child, which together must hold every edge of the task exactly once.
//! Each child then re-enters: its header reply must carry the parent receipt the host just
//! showed it, the digest of the unchanged task, and the fuel the host has left. The child's
//! edges and labels go through the WF20 loop as a task of their own. The flips each child is
//! accepted with are mapped back to the task's edges, and their union must pass the task's own
//! WF9 check.
//!
//! Every question put to the model takes one unit of fuel first, from one counter, so no child
//! can be asked more than the task's fuel allows, and the fuel a child states must be the
//! host's.
//!
//! Receipts are SHA-256 digests of canonical JSON. The root receipt covers the digest of the
//! task and the plan. After each child the receipt covers the receipt before it, the child's
//! number, its flips as task edges, and the fuel left.
//!
//! Task: the XOR task, `fuel`, an exact integer of at least 1, and optionally `max_attempts`,
//! 1 to 5 (default 5), for each child.

use std::collections::BTreeSet;

use num_bigint::BigInt;
use num_traits::One;

use crate::datum::Datum;

use super::attempts::{limit, Fuel};
use super::wf20::{derive, Halt, Loop, LOOP_LIMIT};
use super::xor::{self, flips};
use super::{no_reply, refused, sha256_hex, Checks, Family, Run, Stop, Verdict};

pub const FAMILY: Family = Family {
    workflow: "WF33",
    name: "Recursive re-entry with shared fuel",
    host_check: "shared_fuel_parent_bound_reentry",
    validate,
    walk,
};

fn fuel(task: &Datum) -> Result<BigInt, String> {
    let fuel = task
        .get("fuel")
        .and_then(Datum::as_int)
        .ok_or("fuel must be an exact int")?;
    if *fuel < BigInt::one() {
        return Err("fuel must be positive".to_owned());
    }
    Ok(fuel.clone())
}

fn validate(task: &Datum, _sealed: &Datum) -> Result<(), String> {
    xor::read(task)?;
    limit(task, LOOP_LIMIT, LOOP_LIMIT)?;
    fuel(task).map(|_| ())
}

fn digest(value: &Datum) -> String {
    sha256_hex(&value.canonical())
}

fn indices(edges: &[usize]) -> Datum {
    Datum::from(edges.to_vec())
}

/// The check of one child's header against what the host holds. The code is the refusal when a
/// binding fails.
fn bind(
    checks: &mut Checks,
    child: usize,
    head: &Datum,
    receipt: &str,
    task: &Datum,
    fuel: &Fuel,
) -> Result<Option<&'static str>, String> {
    let task_digest = digest(task);
    let stated = |key: &str| head.get(key).and_then(Datum::as_text);
    if !checks.record(
        &format!("child{child}:parent_bound"),
        stated("parent_receipt") == Some(receipt),
        &Datum::from(receipt),
    ) {
        return Ok(Some("STALE_PARENT_RECEIPT"));
    }
    if !checks.record(
        &format!("child{child}:task_unchanged"),
        stated("task_digest") == Some(task_digest.as_str()),
        &Datum::text(task_digest.clone()),
    ) {
        return Ok(Some("TASK_CHANGED"));
    }
    let claimed = head
        .get("fuel")
        .and_then(Datum::as_int)
        .ok_or("fuel must be an exact int")?;
    let evidence = Datum::map([
        ("claimed", Datum::Int(claimed.clone())),
        ("left", Datum::Int(fuel.left().clone())),
    ]);
    if !checks.record(
        &format!("child{child}:fuel_not_reset"),
        claimed == fuel.left(),
        &evidence,
    ) {
        return Ok(Some(if claimed > fuel.left() {
            "FUEL_RESET"
        } else {
            "FUEL_MISMATCH"
        }));
    }
    Ok(None)
}

/// The plan a reply gives: one ascending list of distinct edge indices per child.
fn plan(reply: &Datum, edges: usize) -> Result<Vec<Vec<usize>>, String> {
    reply
        .get("children")
        .and_then(Datum::as_list)
        .ok_or("children must be a list")?
        .iter()
        .map(|child| flips(Some(child), edges).map(|child| child.into_iter().collect()))
        .collect()
}

/// A child's part of the task: its edges and labels under the task's statement.
fn part(task: &Datum, child: &[usize], limit: usize) -> Datum {
    let pick = |key: &str| {
        let whole = task.get(key).and_then(Datum::as_list).unwrap_or_default();
        Datum::List(
            child
                .iter()
                .filter_map(|&edge| whole.get(edge))
                .cloned()
                .collect(),
        )
    };
    Datum::map([
        (
            "statement",
            task.get("statement").cloned().unwrap_or(Datum::text("")),
        ),
        ("edges", pick("edges")),
        ("labels", pick("labels")),
        ("max_attempts", Datum::from(limit)),
    ])
}

/// One child of the plan: its number, its edges as task edges, and its attempt limit.
struct Child<'p> {
    number: usize,
    edges: &'p [usize],
    limit: usize,
}

/// How one child's re-entry ended: the task edges it flipped, or the verdict that ends the run.
enum Entry {
    Flipped(Vec<usize>),
    Ended(Verdict),
}

/// Re-enter one child: draw fuel for its header, bind the header to the parent, and run its
/// part of the task through the derivation loop.
fn enter(
    run: &mut Run,
    checks: &mut Checks,
    fuel: &mut Fuel,
    receipt: &str,
    child: &Child,
) -> Result<Entry, Stop> {
    let number = child.number;
    let halted = |code: &str, fuel: &Fuel| {
        let detail = Datum::map([("child", Datum::from(number)), ("fuel_trace", fuel.trace())]);
        Ok(Entry::Ended(refused(code, detail)))
    };
    if !fuel.draw() {
        return halted("FUEL_EXHAUSTED", fuel);
    }
    let listing: Vec<String> = child.edges.iter().map(usize::to_string).collect();
    let prompt = format!(
        "{}\nChild {number} edges: [{}]\nParent receipt: {receipt}\nFuel: {}",
        run.prompt(),
        listing.join(", "),
        fuel.left()
    );
    let head = run
        .ask(&format!("enter:{number}"), prompt)?
        .filter(|head| head.is_map())
        .ok_or_else(|| Stop::Malformed(format!("enter:{number} header must be an object")))?;
    if let Some(code) =
        bind(checks, number, head, receipt, run.task, fuel).map_err(Stop::Malformed)?
    {
        let detail = Datum::map([("child", Datum::from(number))]);
        return Ok(Entry::Ended(refused(code, detail)));
    }
    let part = part(run.task, child.edges, child.limit);
    let labelled = xor::read(&part).map_err(Stop::Malformed)?;
    let turn = Loop {
        task: &part,
        graph: &labelled.graph,
        prefix: &format!("child:{number}:"),
        limit: child.limit,
    };
    let derivation = derive(run, &turn, Some(&mut *fuel), &|reply| {
        labelled.assess(reply)
    })?;
    let halt = derivation.halt.name();
    if !checks.record(
        &format!("child{number}:certified"),
        derivation.halt == Halt::Certificate,
        &Datum::from(halt),
    ) {
        return halted(&format!("CHILD_HALTED_ON_{}", halt.to_uppercase()), fuel);
    }
    let accepted = derivation.accepted.and_then(|reply| reply.get("flip"));
    let flipped = flips(accepted, child.edges.len())
        .map_err(Stop::Malformed)?
        .into_iter()
        .filter_map(|edge| child.edges.get(edge).copied())
        .collect();
    Ok(Entry::Flipped(flipped))
}

/// Whether the plan holds every edge of the task exactly once.
fn partitions(plan: &[Vec<usize>], edges: usize) -> bool {
    let mut covered: Vec<usize> = plan.iter().flatten().copied().collect();
    covered.sort_unstable();
    covered == (0..edges).collect::<Vec<_>>()
}

fn walk(run: &mut Run, checks: &mut Checks) -> Result<Verdict, Stop> {
    let task = run.task;
    let root = xor::read(task).map_err(Stop::Malformed)?;
    let limit = limit(task, LOOP_LIMIT, LOOP_LIMIT).map_err(Stop::Malformed)?;
    let mut fuel = Fuel::new(fuel(task).map_err(Stop::Malformed)?);
    let edges = root.graph.edges().len();
    fuel.draw();
    let Some(reply) = run.ask("plan", format!("{}\nFuel: {}", run.prompt(), fuel.left()))? else {
        return Ok(no_reply());
    };
    let plan = plan(reply, edges).map_err(Stop::Malformed)?;
    let listed = Datum::List(plan.iter().map(|child| indices(child)).collect());
    if !checks.record(
        "forward_coverage_partition",
        partitions(&plan, edges),
        &listed,
    ) {
        return Ok(refused(
            "COVERAGE_NOT_A_PARTITION",
            Datum::map([("plan", listed)]),
        ));
    }
    let mut receipt = digest(&Datum::map([
        ("root", Datum::text(digest(task))),
        ("plan", listed),
    ]));
    let mut combined = BTreeSet::new();
    for (number, edges) in plan.iter().enumerate() {
        let child = Child {
            number,
            edges,
            limit,
        };
        let flipped = match enter(run, checks, &mut fuel, &receipt, &child)? {
            Entry::Flipped(flipped) => flipped,
            Entry::Ended(verdict) => return Ok(verdict),
        };
        receipt = digest(&Datum::map([
            ("parent", Datum::text(receipt)),
            ("child", Datum::from(number)),
            ("flips", indices(&flipped)),
            ("fuel", Datum::Int(fuel.left().clone())),
        ]));
        combined.extend(flipped);
    }
    let flips = Datum::from(combined.iter().copied().collect::<Vec<_>>());
    let whole = root.odd_cycles(&combined).is_empty() && combined.len() == root.least_repair();
    checks.record("backward_solution_map", whole, &flips);
    let detail = Datum::map([
        ("flips", flips),
        ("fuel_trace", fuel.trace()),
        ("receipt", Datum::text(receipt)),
    ]);
    Ok(checks.judge("REENTRY_CERTIFIED", detail))
}
