//! WF30, constraint-forcing anti-recitation: a sorting network under constraints that a
//! memorised network breaks.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf30:v1
//!
//! The task forces the first comparators and forbids some others. The host checks the forced
//! prefix, the forbidden set, the size bound, and that the network sorts. Sorting is decided by
//! the 0-1 principle: a comparator network sorts every input exactly when it sorts all `2^n`
//! inputs of zeros and ones, and the host runs all of them.
//!
//! Task: `n` wires, 2 to 10; optional `forced_prefix` and `forbidden`, lists of comparators; and
//! optional `max_comparators`. Reply: `{"network": [[i, j], ...]}` with `0 <= i < j < n`.

use std::collections::BTreeSet;

use crate::datum::Datum;

use super::{no_reply, Checks, Family, Run, Stop, Verdict};

pub const MIN_WIRES: usize = 2;
pub const MAX_WIRES: usize = 10;

pub const FAMILY: Family = Family {
    workflow: "WF30",
    name: "Constraint-forcing anti-recitation",
    host_check: "comparator_network_zero_one_principle",
    validate,
    walk,
};

type Comparator = (usize, usize);

fn comparator(pair: &Datum, wires: usize) -> Result<Comparator, String> {
    let Some([low, high]) = pair.as_list() else {
        return Err("a comparator is a pair [i, j]".to_owned());
    };
    match (low.as_count(), high.as_count()) {
        (Some(low), Some(high)) if low < high && high < wires => Ok((low, high)),
        _ => Err("a comparator must satisfy 0 <= i < j < n".to_owned()),
    }
}

/// The comparators under `key`, or none when the key is absent.
fn comparators(holder: &Datum, key: &str, wires: usize) -> Result<Vec<Comparator>, String> {
    match holder.get(key) {
        None => Ok(Vec::new()),
        Some(list) => list
            .as_list()
            .ok_or(format!("{key} must be a list of comparators"))?
            .iter()
            .map(|pair| comparator(pair, wires))
            .collect(),
    }
}

struct Task {
    wires: usize,
    prefix: Vec<Comparator>,
    forbidden: BTreeSet<Comparator>,
    bound: Option<usize>,
}

fn task(task: &Datum) -> Result<Task, String> {
    let wires = task
        .get("n")
        .and_then(Datum::as_count)
        .filter(|wires| (MIN_WIRES..=MAX_WIRES).contains(wires))
        .ok_or(format!(
            "n must be an exact integer from {MIN_WIRES} to {MAX_WIRES}"
        ))?;
    let bound = match task.get("max_comparators") {
        None => None,
        Some(bound) => Some(
            bound
                .as_count()
                .ok_or("max_comparators must be an exact integer, zero or more")?,
        ),
    };
    Ok(Task {
        wires,
        prefix: comparators(task, "forced_prefix", wires)?,
        forbidden: comparators(task, "forbidden", wires)?.into_iter().collect(),
        bound,
    })
}

fn validate(public: &Datum, _sealed: &Datum) -> Result<(), String> {
    task(public).map(|_| ())
}

/// The wires after the network has run on them. A comparator that names a wire the input does
/// not have does nothing.
pub fn apply(network: &[Comparator], input: &[u8]) -> Vec<u8> {
    let mut wires = input.to_vec();
    for &(low, high) in network {
        if let (Some(&first), Some(&second)) = (wires.get(low), wires.get(high)) {
            if first > second {
                wires.swap(low, high);
            }
        }
    }
    wires
}

/// Input number `index` of the `2^wires` inputs of zeros and ones, first wire most significant.
fn binary_input(index: usize, wires: usize) -> Vec<u8> {
    (0..wires)
        .map(|wire| u8::from(index >> (wires - 1 - wire) & 1 == 1))
        .collect()
}

/// Every input of zeros and ones the network leaves unsorted, in counting order.
pub fn unsorted_inputs(network: &[Comparator], wires: usize) -> Vec<Vec<u8>> {
    (0..1usize << wires)
        .map(|index| binary_input(index, wires))
        .filter(|input| {
            let mut sorted = input.clone();
            sorted.sort_unstable();
            apply(network, input) != sorted
        })
        .collect()
}

fn pairs(network: &[Comparator]) -> Datum {
    Datum::List(
        network
            .iter()
            .map(|&(low, high)| Datum::from(vec![low, high]))
            .collect(),
    )
}

fn walk(run: &mut Run, checks: &mut Checks) -> Result<Verdict, Stop> {
    let task = task(run.task).map_err(Stop::Malformed)?;
    let Some(reply) = run.ask("solve", run.prompt())? else {
        return Ok(no_reply());
    };
    if reply.get("network").and_then(Datum::as_list).is_none() {
        return Err(Stop::Malformed(
            "the reply must be an object with a network list".to_owned(),
        ));
    }
    let network = comparators(reply, "network", task.wires).map_err(Stop::Malformed)?;
    let written = pairs(&network);
    checks.record(
        "forced_prefix_kept",
        network.starts_with(&task.prefix),
        &written,
    );
    checks.record(
        "no_forbidden_comparator",
        !network.iter().any(|pair| task.forbidden.contains(pair)),
        &written,
    );
    checks.record(
        "within_size_bound",
        task.bound.is_none_or(|bound| network.len() <= bound),
        &Datum::from(network.len()),
    );
    let failures = unsorted_inputs(&network, task.wires);
    let first: Vec<Datum> = failures
        .first()
        .map(|input| {
            input
                .iter()
                .map(|&bit| Datum::from(usize::from(bit)))
                .collect()
        })
        .unwrap_or_default();
    checks.record(
        "sorts_all_binary_inputs",
        failures.is_empty(),
        &Datum::List(first),
    );
    Ok(checks.judge(
        super::CERTIFIED_CODE,
        Datum::map([
            ("comparators", Datum::from(network.len())),
            ("binary_failures", Datum::from(failures.len())),
        ]),
    ))
}
