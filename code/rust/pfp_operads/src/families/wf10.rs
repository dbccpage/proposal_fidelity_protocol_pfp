//! WF10, local-to-global obstruction certificate: glue an edge cochain into one vertex
//! potential, or show the cycle that forbids it.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf10:v1
//!
//! The task is a rational value on every edge of a graph, and optionally `patches`, lists of
//! edge indices. The reply takes one of two forms, and prose takes neither:
//!
//! * `potential`: one rational per vertex. Certified as `GLUED` when the edge values are exactly
//!   its coboundary.
//! * `obstruction`: a chain. It stands as the typed refusal `GLOBAL_OBSTRUCTION` when the chain
//!   is closed and the edge values sum to something other than zero round it.
//!
//! The verdict also says, for each patch, whether the values on that patch alone are a
//! coboundary. That is reported and never decides the verdict.

use num_traits::Zero;

use crate::datum::Datum;
use crate::exact::show;
use crate::graph::walk_sum;

use super::cochain::{self, Cochain};
use super::{no_reply, refused, typed_refusal, Checks, Family, Run, Stop, Verdict};

pub const FAMILY: Family = Family {
    workflow: "WF10",
    name: "Local-to-global obstruction certificate",
    host_check: "cochain_gluing_or_cycle_obstruction",
    validate,
    walk,
};

fn patches(task: &Datum, edges: usize) -> Result<Vec<Vec<usize>>, String> {
    let Some(listed) = task.get("patches") else {
        return Ok(Vec::new());
    };
    let patches = |listed: &Datum| -> Option<Vec<Vec<usize>>> {
        let listed = listed.as_list()?.iter();
        listed.map(|patch| cochain::indices(patch, edges)).collect()
    };
    patches(listed).ok_or_else(|| "patches must be lists of edge indices".to_owned())
}

fn validate(task: &Datum, _sealed: &Datum) -> Result<(), String> {
    let cochain = cochain::read(task)?;
    patches(task, cochain.values.len()).map(|_| ())
}

fn glue(
    cochain: &Cochain,
    listed: &Datum,
    checks: &mut Checks,
    local: Datum,
) -> Result<Verdict, String> {
    let potential = cochain.named.potential(listed)?;
    let left = cochain.named.graph.residual(&cochain.values, &potential);
    let support: Vec<usize> = (0..left.len())
        .filter(|&edge| left.get(edge).is_some_and(|value| !value.is_zero()))
        .collect();
    let exact = support.is_empty();
    let support = Datum::from(support);
    checks.record("zero_residual_on_every_edge", exact, &support);
    let detail = Datum::map([("residual_support", support), ("local_sections", local)]);
    Ok(checks.judge("GLUED", detail))
}

fn obstruct(
    cochain: &Cochain,
    listed: &Datum,
    checks: &mut Checks,
    local: Datum,
) -> Result<Verdict, String> {
    let graph = &cochain.named.graph;
    let chain = cochain::chain(listed, cochain.values.len())?;
    let open = cochain::boundary(graph, &chain);
    let closed = open.is_empty();
    let named = open
        .into_iter()
        .filter_map(|(vertex, count)| Some((graph.names().get(vertex)?.to_string(), count)));
    let boundary = Datum::Map(named.map(|(name, count)| (name, count.into())).collect());
    if !checks.record("witness_is_closed_cycle", closed, &boundary) {
        let detail = Datum::map([("boundary", boundary), ("local_sections", local)]);
        return Ok(refused("OPEN_CYCLE_WITNESS", detail));
    }
    let holonomy = walk_sum(&chain, &cochain.values);
    let shown = Datum::text(show(&holonomy));
    if !checks.record("nonzero_holonomy", !holonomy.is_zero(), &shown) {
        let detail = Datum::map([("local_sections", local)]);
        return Ok(refused("ZERO_HOLONOMY_WITNESS", detail));
    }
    let steps = chain
        .iter()
        .map(|&(edge, sign)| Datum::List(vec![Datum::from(edge), Datum::from(i64::from(sign))]));
    let detail = Datum::map([
        ("holonomy", shown),
        ("cycle", Datum::List(steps.collect())),
        ("local_sections", local),
    ]);
    Ok(typed_refusal("GLOBAL_OBSTRUCTION", detail))
}

fn walk(run: &mut Run, checks: &mut Checks) -> Result<Verdict, Stop> {
    let cochain = cochain::read(run.task).map_err(Stop::Malformed)?;
    let patches = patches(run.task, cochain.values.len()).map_err(Stop::Malformed)?;
    let Some(reply) = run.ask("solve", run.prompt())? else {
        return Ok(no_reply());
    };
    if !reply.is_map() {
        return Err(Stop::Malformed("reply must be an object".to_owned()));
    }
    let sections = patches.iter().map(|patch| cochain.exact_on(patch));
    let local = Datum::List(sections.map(Datum::Bool).collect());
    if let Some(potential) = reply.get("potential") {
        return glue(&cochain, potential, checks, local).map_err(Stop::Malformed);
    }
    if let Some(cycle) = reply.get("obstruction") {
        return obstruct(&cochain, cycle, checks, local).map_err(Stop::Malformed);
    }
    Err(Stop::Malformed(
        "reply must carry a potential or an obstruction cycle, not a claim".to_owned(),
    ))
}
