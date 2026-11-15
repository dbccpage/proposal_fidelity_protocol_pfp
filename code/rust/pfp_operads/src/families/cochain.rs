//! Rational values on the edges of a task graph whose vertices are named `0..n-1`, and signed
//! chains of its edges, for the families that glue, decimate and repair such values.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-cochain:v1
//!
//! Task: `edges`, a nonempty list of `[u, v]` pairs whose vertices are named `0..n-1`, and
//! `labels`, one exact rational per edge. A reply names a vertex by its name and an edge by its
//! index in `edges`.
//!
//! A chain is a nonempty list of `[edge, sign]` steps, sign `1` for the edge taken forwards and
//! `-1` for backwards. Its boundary is the net count of arrivals less departures at each vertex,
//! and a chain with an empty boundary is closed. A chain is a walk when every step starts where
//! the one before it ended.

use std::collections::BTreeMap;

use num_bigint::BigInt;
use num_traits::Zero;

use crate::datum::Datum;
use crate::exact::{rationals, Rational};
use crate::graph::{Graph, Step};

/// A task graph: at least one edge, and vertices named `0..n-1`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Named {
    pub graph: Graph,
    /// The graph's number for the vertex of each name.
    numbered: Vec<usize>,
}

/// A task graph with a rational value on every edge.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Cochain {
    pub named: Named,
    pub values: Vec<Rational>,
}

/// The graph of a task.
pub fn graph(task: &Datum) -> Result<Named, String> {
    let graph = task
        .get("edges")
        .and_then(Graph::read)
        .filter(|graph| !graph.edges().is_empty())
        .ok_or("edges must be a nonempty list of pairs of exact integers")?;
    if !graph.is_numbered() {
        return Err("vertices must be 0..n-1".to_owned());
    }
    let numbered = (0..graph.names().len())
        .filter_map(|name| graph.vertex(&BigInt::from(name)))
        .collect();
    Ok(Named { graph, numbered })
}

/// The graph and edge values of a task.
pub fn read(task: &Datum) -> Result<Cochain, String> {
    let named = graph(task)?;
    let values = task
        .get("labels")
        .and_then(rationals)
        .filter(|values| values.len() == named.graph.edges().len())
        .ok_or("labels must be one exact rational per edge")?;
    Ok(Cochain { named, values })
}

/// The edges a value lists: exact integers, each the index of one of `edges` edges.
pub fn indices(listed: &Datum, edges: usize) -> Option<Vec<usize>> {
    let index = |entry: &Datum| entry.as_count().filter(|&index| index < edges);
    listed.as_list()?.iter().map(index).collect()
}

fn step(entry: &Datum, edges: usize) -> Option<Step> {
    let [edge, sign] = entry.as_list()? else {
        return None;
    };
    let edge = edge.as_count().filter(|&edge| edge < edges)?;
    let sign = match sign.as_int()? {
        sign if *sign == BigInt::from(1) => 1,
        sign if *sign == BigInt::from(-1) => -1,
        _ => return None,
    };
    Some((edge, sign))
}

/// The chain a value lists, on a graph of `edges` edges.
pub fn chain(listed: &Datum, edges: usize) -> Result<Vec<Step>, String> {
    let steps = listed
        .as_list()
        .filter(|steps| !steps.is_empty())
        .ok_or("a chain must be a nonempty list of steps")?;
    let read: Option<Vec<Step>> = steps.iter().map(|entry| step(entry, edges)).collect();
    read.ok_or_else(|| {
        "a chain step is [edge, sign] with the edge in range and sign 1 or -1".to_owned()
    })
}

/// The boundary of a chain: for each vertex where it is not zero, the number of steps that
/// arrive less the number that leave.
pub fn boundary(graph: &Graph, chain: &[Step]) -> BTreeMap<usize, i64> {
    let mut net: BTreeMap<usize, i64> = BTreeMap::new();
    for &(edge, sign) in chain {
        if let Some(&(from, to)) = graph.edges().get(edge) {
            *net.entry(from).or_default() -= i64::from(sign);
            *net.entry(to).or_default() += i64::from(sign);
        }
    }
    net.retain(|_, count| *count != 0);
    net
}

/// The vertex a chain ends at when walked from `start`. Nothing when a step does not start
/// where the one before it ended.
pub fn walk_end(graph: &Graph, start: usize, chain: &[Step]) -> Option<usize> {
    chain.iter().try_fold(start, |at, &(edge, sign)| {
        let &(from, to) = graph.edges().get(edge)?;
        let (leaves, arrives) = if sign == 1 { (from, to) } else { (to, from) };
        (at == leaves).then_some(arrives)
    })
}

impl Named {
    /// The graph's number for the vertex a value names.
    pub fn vertex(&self, name: &Datum) -> Option<usize> {
        self.numbered.get(name.as_count()?).copied()
    }

    /// One rational per vertex, listed by vertex name, in the graph's vertex order.
    pub fn potential(&self, listed: &Datum) -> Result<Vec<Rational>, String> {
        let by_name = rationals(listed)
            .filter(|values| values.len() == self.numbered.len())
            .ok_or("potential must be one exact rational per vertex")?;
        let mut potential = vec![Rational::zero(); by_name.len()];
        for (value, &vertex) in by_name.into_iter().zip(&self.numbered) {
            potential[vertex] = value;
        }
        Ok(potential)
    }
}

impl Cochain {
    /// Whether the values on these edges are a coboundary on the graph of these edges alone.
    pub fn exact_on(&self, edges: &[usize]) -> bool {
        let names = self.named.graph.names();
        let picked: Vec<(&BigInt, &BigInt)> = edges
            .iter()
            .filter_map(|&edge| self.named.graph.edges().get(edge))
            .filter_map(|&(from, to)| Some((names.get(from)?, names.get(to)?)))
            .collect();
        let values: Vec<Rational> = edges
            .iter()
            .filter_map(|&edge| self.values.get(edge).cloned())
            .collect();
        Graph::of(picked).defect(&values).is_zero()
    }
}
