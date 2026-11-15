//! WF46, boundary sufficiency and gluing diagnostic: do the values two patch agents share on
//! their boundary decide whether their answers glue?
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf46:v1
//!
//! The task is a rational edge cochain on a graph whose edges are split into two patches, and
//! a packet: vertices that lie on both patches. Each run's reply is one potential per patch, a
//! list of `[vertex, value]`. A run is locally accepted when each potential covers exactly the
//! vertices of its patch and explains the values on every edge of it.
//!
//! For a locally accepted run the host shifts the second potential to agree with the first at
//! the first packet vertex. The packet passes when the two then agree at every packet vertex.
//! The glued trace is the first potential, and the shifted second where the first says
//! nothing; it passes when it explains the values on every edge of the graph.
//!
//! `ngd` is the share of locally accepted runs whose glued trace fails. It is undefined with
//! no accepted run (`NGD_UNDEFINED`). The run is certified as `BOUNDARY_SUFFICIENT` when the
//! packet and the glued trace agree on every accepted run, and refused as
//! `BOUNDARY_INSUFFICIENT` otherwise.
//!
//! Task: the cochain task of [`super::cochain`]; `patches`, two lists of edge indices that
//! together hold every edge once; `packet`, a nonempty list of vertices on both patches; and
//! `runs`, 1 to 64.

use std::collections::{BTreeMap, BTreeSet};

use num_bigint::BigInt;

use crate::datum::Datum;
use crate::exact::{rational, show, Rational};

use super::cochain::{self, Cochain};
use super::{refused, Checks, Family, Run, Stop, Verdict};

/// The most runs a task may ask for.
pub const MAX_RUNS: usize = 64;

pub const FAMILY: Family = Family {
    workflow: "WF46",
    name: "Boundary sufficiency and gluing diagnostic",
    host_check: "glued_trace_global_evaluator",
    validate,
    walk,
};

/// A value on some vertices, by vertex name.
type Potential = BTreeMap<BigInt, Rational>;

struct Cover {
    cochain: Cochain,
    patches: [Vec<usize>; 2],
    packet: Vec<BigInt>,
    runs: usize,
}

impl Cover {
    /// The names of the two ends of an edge.
    fn ends(&self, edge: usize) -> Option<(&BigInt, &BigInt)> {
        let graph = &self.cochain.named.graph;
        let &(from, to) = graph.edges().get(edge)?;
        Some((graph.names().get(from)?, graph.names().get(to)?))
    }

    /// The names of the vertices a patch touches.
    fn vertices(&self, patch: &[usize]) -> BTreeSet<&BigInt> {
        let ends = patch.iter().filter_map(|&edge| self.ends(edge));
        ends.flat_map(|(from, to)| [from, to]).collect()
    }

    /// Whether a potential explains the value on every one of these edges.
    fn explains(&self, potential: &Potential, edges: &[usize]) -> bool {
        edges.iter().all(|&edge| {
            let found = || {
                let (from, to) = self.ends(edge)?;
                let step = potential.get(to)? - potential.get(from)?;
                Some(step == *self.cochain.values.get(edge)?)
            };
            found().unwrap_or(false)
        })
    }

    /// Whether a potential covers exactly a patch's vertices and explains its edges.
    fn local(&self, potential: &Potential, patch: &[usize]) -> bool {
        let covered: BTreeSet<&BigInt> = potential.keys().collect();
        covered == self.vertices(patch) && self.explains(potential, patch)
    }

    /// Whether the packet passes and whether the glued trace does, for two local potentials.
    fn glue(&self, first: &Potential, second: &Potential) -> Option<(bool, bool)> {
        let gap = |vertex: &BigInt| Some(first.get(vertex)? - second.get(vertex)?);
        let shift = gap(self.packet.first()?)?;
        let packet = self
            .packet
            .iter()
            .all(|vertex| gap(vertex) == Some(shift.clone()));
        let mut glued: Potential = second
            .iter()
            .map(|(vertex, value)| (vertex.clone(), value + &shift))
            .collect();
        glued.extend(
            first
                .iter()
                .map(|(vertex, value)| (vertex.clone(), value.clone())),
        );
        let every: Vec<usize> = (0..self.cochain.values.len()).collect();
        Some((packet, self.explains(&glued, &every)))
    }
}

fn cover(task: &Datum) -> Result<Cover, String> {
    let cochain = cochain::read(task)?;
    let edges = cochain.values.len();
    let patch = |listed: &Datum| cochain::indices(listed, edges);
    let patches = match task.get("patches").and_then(Datum::as_list) {
        Some([first, second]) => patch(first).zip(patch(second)),
        _ => None,
    };
    let (first, second) = patches.ok_or("patches must be two lists of edge indices")?;
    let mut held: Vec<usize> = first.iter().chain(&second).copied().collect();
    held.sort_unstable();
    if held != (0..edges).collect::<Vec<_>>() {
        return Err("patches must hold every edge exactly once".to_owned());
    }
    let packet: Vec<BigInt> = task
        .get("packet")
        .and_then(Datum::as_list)
        .filter(|packet| !packet.is_empty())
        .and_then(|packet| packet.iter().map(|v| v.as_int().cloned()).collect())
        .ok_or("packet must be a nonempty list of exact integers")?;
    let runs = task
        .get("runs")
        .and_then(Datum::as_count)
        .filter(|runs| (1..=MAX_RUNS).contains(runs))
        .ok_or(format!(
            "runs must be an exact integer from 1 to {MAX_RUNS}"
        ))?;
    let cover = Cover {
        cochain,
        patches: [first, second],
        packet,
        runs,
    };
    let shared = |vertex: &BigInt| {
        let on = |patch: &[usize]| cover.vertices(patch).contains(vertex);
        cover.patches.iter().all(|patch| on(patch))
    };
    if !cover.packet.iter().all(shared) {
        return Err("packet vertices must lie on both patches".to_owned());
    }
    Ok(cover)
}

fn validate(task: &Datum, _sealed: &Datum) -> Result<(), String> {
    cover(task).map(|_| ())
}

/// The potential a reply lists for one patch. A vertex listed twice keeps its last value.
fn potential(listed: &Datum) -> Result<Potential, String> {
    let entry = |entry: &Datum| match entry.as_list() {
        Some([vertex, value]) => Some((vertex.as_int()?.clone(), rational(value)?)),
        _ => None,
    };
    listed
        .as_list()
        .and_then(|entries| entries.iter().map(entry).collect())
        .ok_or_else(|| {
            "a patch potential is a list of [vertex, value] with exact entries".to_owned()
        })
}

/// One run's row in the verdict, and its packet and glued-trace findings when it is locally
/// accepted.
fn assess(
    cover: &Cover,
    number: usize,
    reply: &Datum,
) -> Result<(Datum, Option<(bool, bool)>), String> {
    let Some([first, second]) = reply.as_list() else {
        return Err("one potential per patch".to_owned());
    };
    let (first, second) = (potential(first)?, potential(second)?);
    let [one, two] = &cover.patches;
    let found = (cover.local(&first, one) && cover.local(&second, two))
        .then(|| cover.glue(&first, &second))
        .flatten();
    let mut row = vec![
        ("run", Datum::from(number)),
        ("local", Datum::Bool(found.is_some())),
    ];
    if let Some((packet, global)) = found {
        row.push(("packet", Datum::Bool(packet)));
        row.push(("global", Datum::Bool(global)));
    }
    let row = row.into_iter().map(|(key, value)| (key.to_owned(), value));
    Ok((Datum::Map(row.collect()), found))
}

fn walk(run: &mut Run, checks: &mut Checks) -> Result<Verdict, Stop> {
    let cover = cover(run.task).map_err(Stop::Malformed)?;
    let (mut rows, mut accepted, mut replied) = (Vec::new(), Vec::new(), 0usize);
    for number in 0..cover.runs {
        let Some(reply) = run.ask(&format!("run:{number}"), run.prompt())? else {
            continue;
        };
        replied += 1;
        let (row, found) = assess(&cover, number, reply).map_err(Stop::Malformed)?;
        rows.push(row);
        accepted.extend(found);
    }
    let rows = Datum::List(rows);
    let mut detail = vec![
        (
            "completed",
            Datum::text(format!("{replied}/{}", cover.runs)),
        ),
        ("backlog", Datum::from(cover.runs - replied)),
        ("runs", rows.clone()),
    ];
    let finish = |detail: Vec<(&str, Datum)>| {
        let entries = detail
            .into_iter()
            .map(|(key, value)| (key.to_owned(), value));
        Datum::Map(entries.collect())
    };
    if !checks.record("ngd_defined", !accepted.is_empty(), &rows) {
        detail.push(("ngd", Datum::Null));
        return Ok(refused("NGD_UNDEFINED", finish(detail)));
    }
    let failed = accepted.iter().filter(|(_, global)| !global).count();
    let hidden = accepted
        .iter()
        .filter(|(packet, global)| *packet && !global)
        .count();
    let ngd = Rational::new(BigInt::from(failed), BigInt::from(accepted.len()));
    detail.push(("ngd", Datum::text(show(&ngd))));
    let decides = accepted.iter().all(|(packet, global)| packet == global);
    if !checks.record("packet_decides_global", decides, &Datum::from(hidden)) {
        detail.push(("hidden_failures", Datum::from(hidden)));
        return Ok(refused("BOUNDARY_INSUFFICIENT", finish(detail)));
    }
    Ok(checks.judge("BOUNDARY_SUFFICIENT", finish(detail)))
}
