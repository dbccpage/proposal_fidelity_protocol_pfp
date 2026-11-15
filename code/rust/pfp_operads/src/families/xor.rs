//! The XOR repair domain: flip the fewest edge labels so every cycle of a graph has an even sum.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-xor:v1
//!
//! Each edge carries a label, 0 or 1. The labels come from a 0/1 value on the vertices exactly
//! when the labels round every cycle sum to an even number, and it is enough to look at the
//! fundamental cycles. A repair is a set of edges whose labels are flipped. The host accepts it
//! when no fundamental cycle is left odd and no smaller set would do; it finds the smallest size
//! by trying every set of edges, which is why a task has at most [`MAX_EDGES`] of them.
//!
//! Task: `edges`, a list of `[u, v]` pairs of exact integers, and `labels`, one exact integer 0
//! or 1 per edge. Reply: `{"flip": [edge index, ...]}`.

use std::collections::BTreeSet;

use crate::datum::Datum;
use crate::graph::Graph;

use super::attempts::Assessment;

/// The most edges a task may have.
pub const MAX_EDGES: usize = 20;

/// A graph with a 0/1 label on every edge.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Labelled {
    pub graph: Graph,
    labels: Vec<bool>,
    /// For each edge, the set of fundamental cycles it lies on, as bits.
    cycles_through: Vec<u32>,
    cycles: usize,
}

fn label(value: &Datum) -> Option<bool> {
    match value.as_count()? {
        0 => Some(false),
        1 => Some(true),
        _ => None,
    }
}

/// The labelled graph of a task.
pub fn read(task: &Datum) -> Result<Labelled, String> {
    let (Some(edges), Some(labels)) = (
        task.get("edges").and_then(Datum::as_list),
        task.get("labels").and_then(Datum::as_list),
    ) else {
        return Err("edges and labels must be lists".to_owned());
    };
    if edges.len() != labels.len() {
        return Err("one label per edge".to_owned());
    }
    if edges.len() > MAX_EDGES {
        return Err(format!("at most {MAX_EDGES} edges"));
    }
    let graph = task
        .get("edges")
        .and_then(Graph::read)
        .ok_or("each edge is a pair of exact integers")?;
    let labels: Vec<bool> = labels
        .iter()
        .map(label)
        .collect::<Option<_>>()
        .ok_or("every label must be the exact integer 0 or 1")?;
    let cycles = graph.fundamental_cycles();
    let mut cycles_through = vec![0u32; labels.len()];
    for (cycle, walk) in cycles.iter().enumerate() {
        for &(edge, _) in walk {
            cycles_through[edge] ^= 1 << cycle;
        }
    }
    Ok(Labelled {
        graph,
        labels,
        cycles_through,
        cycles: cycles.len(),
    })
}

/// The set of edges a value lists: exact integers, each the index of one of `edges` edges.
pub fn flips(value: Option<&Datum>, edges: usize) -> Result<BTreeSet<usize>, String> {
    let listed = value.and_then(Datum::as_list).ok_or("flip list required")?;
    if !listed.iter().all(|index| index.as_int().is_some()) {
        return Err("flip must be an exact int".to_owned());
    }
    listed
        .iter()
        .map(|index| index.as_count().filter(|&index| index < edges))
        .collect::<Option<_>>()
        .ok_or_else(|| "flip index out of range".to_owned())
}

impl Labelled {
    /// The fundamental cycles left odd once the labels of `flips` are flipped, as bits.
    fn odd(&self, flips: &BTreeSet<usize>) -> u32 {
        self.cycles_through
            .iter()
            .zip(&self.labels)
            .enumerate()
            .filter(|(edge, (_, &label))| label != flips.contains(edge))
            .fold(0, |odd, (_, (through, _))| odd ^ through)
    }

    /// The numbers of the fundamental cycles left odd once the labels of `flips` are flipped.
    pub fn odd_cycles(&self, flips: &BTreeSet<usize>) -> Vec<usize> {
        let odd = self.odd(flips);
        (0..self.cycles)
            .filter(|cycle| odd & (1 << cycle) != 0)
            .collect()
    }

    /// The size of the smallest set of flips that leaves no cycle odd, found by trying every set
    /// of edges.
    pub fn least_repair(&self) -> usize {
        let target = self.odd(&BTreeSet::new());
        let mut least = self.labels.len();
        let mut reached = 0u32;
        for step in 0u32..(1 << self.labels.len()) {
            // Sets are visited in Gray-code order, so each differs from the last by one edge.
            if let Some(through) = self.cycles_through.get(step.trailing_zeros() as usize) {
                reached ^= through;
            }
            let size = (step ^ (step >> 1)).count_ones() as usize;
            if reached == target && size < least {
                least = size;
            }
        }
        least
    }

    /// The finding on one reply. The residual names the cycles still odd and the number of
    /// flips, never an edge to flip.
    pub fn assess(&self, reply: &Datum) -> Result<Assessment, String> {
        let flips = flips(reply.get("flip"), self.labels.len())?;
        let odd = self.odd_cycles(&flips);
        let accepted = odd.is_empty() && flips.len() == self.least_repair();
        Ok(Assessment {
            accepted,
            measure: Datum::from(odd.len()),
            residual: Datum::map([
                ("flip_count", Datum::from(flips.len())),
                ("minimal_known", Datum::Bool(odd.is_empty())),
                ("odd_cycles", Datum::from(odd)),
            ]),
        })
    }
}
