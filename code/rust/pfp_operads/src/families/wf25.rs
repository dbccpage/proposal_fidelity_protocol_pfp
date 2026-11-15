//! WF25, hierarchical decimation: remove the tree and degree-2 parts of a cochain graph without
//! changing what any cycle sums to.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf25:v1
//!
//! The reply is a smaller graph on some of the task's vertices. Each of its edges stands for a
//! walk in the task's graph and carries the sum of the task's values along that walk. The host
//! checks that
//!
//! * every path is a walk from its edge's tail to its head,
//! * every label is the sum along its path,
//! * the reduced graph has as many independent cycles as the task's,
//! * the reduced graph's fundamental cycles, written out as chains of task edges, have that
//!   same rank, so every cycle of the task is still there, and
//! * the reduced graph has fewer edges and no vertex of degree 1. A loop counts twice toward
//!   the degree of its vertex.
//!
//! Task: the cochain task of [`super::cochain`]. Reply: `edges`, `labels` and `paths`, three
//! lists of one nonzero length.

use std::collections::BTreeMap;

use num_bigint::BigInt;
use num_traits::Zero;

use crate::datum::Datum;
use crate::exact::{rank, rationals, show, Rational};
use crate::graph::{walk_sum, Graph, Step};

use super::cochain::{self, Cochain};
use super::{no_reply, Checks, Family, Run, Stop, Verdict};

pub const FAMILY: Family = Family {
    workflow: "WF25",
    name: "Hierarchical decimation",
    host_check: "cycle_residual_preserving_decimation",
    validate,
    walk,
};

fn validate(task: &Datum, _sealed: &Datum) -> Result<(), String> {
    cochain::read(task).map(|_| ())
}

/// The reduced graph of a reply, as the host reads it.
struct Reduced {
    /// Each edge by the names of its two vertices.
    ends: Vec<(BigInt, BigInt)>,
    labels: Vec<Rational>,
    /// The walk of task edges each reduced edge stands for.
    paths: Vec<Vec<Step>>,
}

fn pair(entry: &Datum) -> Option<(BigInt, BigInt)> {
    match entry.as_list()? {
        [from, to] => Some((from.as_int()?.clone(), to.as_int()?.clone())),
        _ => None,
    }
}

fn reduced(reply: &Datum, cochain: &Cochain) -> Result<Reduced, String> {
    let (Some(edges), Some(labels), Some(paths)) = (
        reply.get("edges").and_then(Datum::as_list),
        reply.get("labels").and_then(Datum::as_list),
        reply.get("paths").and_then(Datum::as_list),
    ) else {
        return Err("edges, labels and paths must be lists".to_owned());
    };
    if edges.is_empty() || edges.len() != labels.len() || edges.len() != paths.len() {
        return Err("one label and one path per reduced edge, and at least one edge".to_owned());
    }
    let ends: Vec<(BigInt, BigInt)> = edges
        .iter()
        .map(pair)
        .collect::<Option<_>>()
        .ok_or("reduced edges must be pairs of exact integers")?;
    let known = |name: &BigInt| cochain.named.graph.vertex(name).is_some();
    if !ends.iter().all(|(from, to)| known(from) && known(to)) {
        return Err("reduced vertices must be vertices of the task".to_owned());
    }
    let labels = reply
        .get("labels")
        .and_then(rationals)
        .ok_or("reduced labels must be exact rationals")?;
    let paths = paths
        .iter()
        .map(|path| cochain::chain(path, cochain.values.len()))
        .collect::<Result<_, _>>()?;
    Ok(Reduced {
        ends,
        labels,
        paths,
    })
}

/// The degree of each vertex that has one. A loop counts twice.
fn degrees(ends: &[(BigInt, BigInt)]) -> BTreeMap<&BigInt, usize> {
    let mut degree = BTreeMap::new();
    for (from, to) in ends {
        *degree.entry(from).or_default() += 1;
        *degree.entry(to).or_default() += 1;
    }
    degree
}

fn written(values: &[Rational]) -> Datum {
    Datum::List(values.iter().map(|v| Datum::text(show(v))).collect())
}

fn walk(run: &mut Run, checks: &mut Checks) -> Result<Verdict, Stop> {
    let cochain = cochain::read(run.task).map_err(Stop::Malformed)?;
    let Some(reply) = run.ask("solve", run.prompt())? else {
        return Ok(no_reply());
    };
    if !reply.is_map() {
        return Err(Stop::Malformed("reply must be an object".to_owned()));
    }
    let reduced = reduced(reply, &cochain).map_err(Stop::Malformed)?;
    let graph = &cochain.named.graph;
    let small = Graph::of(reduced.ends.iter().map(|(from, to)| (from, to)));

    let walks = reduced.ends.iter().zip(&reduced.paths).all(|(ends, path)| {
        let (Some(from), Some(to)) = (graph.vertex(&ends.0), graph.vertex(&ends.1)) else {
            return false;
        };
        cochain::walk_end(graph, from, path) == Some(to)
    });
    let paths = reply.get("paths").cloned().unwrap_or(Datum::Null);
    checks.record("paths_are_walks", walks, &paths);

    let sums: Vec<Rational> = reduced
        .paths
        .iter()
        .map(|path| walk_sum(path, &cochain.values))
        .collect();
    checks.record(
        "labels_are_path_sums",
        reduced.labels == sums,
        &Datum::List(vec![written(&reduced.labels), written(&sums)]),
    );

    let cycles = small.fundamental_cycles();
    let betti = graph.forest().chords.len();
    checks.record(
        "cycle_rank_preserved",
        cycles.len() == betti,
        &Datum::from(vec![cycles.len(), betti]),
    );

    // Each cycle of the reduced graph as a chain of task edges: one coefficient per task edge.
    let lifted: Vec<Vec<Rational>> = cycles
        .iter()
        .map(|cycle| {
            let mut coefficients = vec![Rational::zero(); cochain.values.len()];
            let steps = cycle
                .iter()
                .filter_map(|&(edge, sign)| Some((reduced.paths.get(edge)?, sign)));
            for (path, sign) in steps {
                for &(edge, turn) in path {
                    if let Some(coefficient) = coefficients.get_mut(edge) {
                        *coefficient += Rational::from_integer(BigInt::from(sign * turn));
                    }
                }
            }
            coefficients
        })
        .collect();
    checks.record(
        "lifted_cycles_span_h1",
        rank(&lifted) == betti,
        &Datum::List(lifted.iter().map(|row| written(row)).collect()),
    );

    let degree = degrees(&reduced.ends);
    let no_leaf = degree.values().all(|&count| count > 1);
    let listed = degree
        .iter()
        .map(|(name, &count)| Datum::List(vec![Datum::Int((*name).clone()), Datum::from(count)]));
    checks.record(
        "strictly_smaller_without_leaves",
        reduced.ends.len() < cochain.values.len() && no_leaf,
        &Datum::List(listed.collect()),
    );

    let residuals = cycles
        .iter()
        .map(|cycle| Datum::text(show(&walk_sum(cycle, &reduced.labels))));
    let detail = Datum::map([
        ("edges", Datum::from(reduced.ends.len())),
        ("b1", Datum::from(betti)),
        ("cycle_residuals", Datum::List(residuals.collect())),
    ]);
    Ok(checks.judge("DECIMATED", detail))
}
