//! Finite graphs with oriented edges, and rational values on their edges, for the workflow hosts.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:graph:v1
//!
//! A graph is a list of edges `[u, v]` between vertices named by exact integers. Vertices are
//! numbered in the order the edges first name them, and every function here speaks in those
//! numbers. An edge runs from its first vertex to its second.
//!
//! [`Graph::forest`] is the breadth-first spanning forest that takes roots in vertex order and
//! neighbours in edge order. An edge outside it is a chord, and each chord closes one
//! fundamental cycle. A value on every edge is the coboundary of a value on every vertex exactly
//! when its sum round every fundamental cycle is zero.
//!
//! A list of values shorter than the edges or vertices it is read against is read as ending in
//! zeros.

use std::collections::{BTreeSet, VecDeque};

use num_bigint::BigInt;
use num_traits::{Signed, Zero};

use crate::datum::Datum;
use crate::exact::Rational;

/// One step of a walk: the edge, and whether it is taken forwards (`1`) or backwards (`-1`).
pub type Step = (usize, i8);

/// How a vertex hangs in the spanning forest: its parent, the edge between them, and `1` when
/// that edge runs from the parent to the vertex, `-1` when it runs the other way.
pub type Link = (usize, usize, i8);

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Graph {
    names: Vec<BigInt>,
    edges: Vec<(usize, usize)>,
}

/// The breadth-first spanning forest of a graph.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Forest {
    /// The link of each vertex to its parent; nothing for a root.
    pub parent: Vec<Option<Link>>,
    /// The edges outside the forest, in edge order.
    pub chords: Vec<usize>,
    /// The vertices in the order the search reached them, so a parent comes before its children.
    pub order: Vec<usize>,
}

fn pair(edge: &Datum) -> Option<(&BigInt, &BigInt)> {
    match edge.as_list()? {
        [from, to] => Some((from.as_int()?, to.as_int()?)),
        _ => None,
    }
}

impl Graph {
    /// The graph a value denotes: a list of `[u, v]` pairs of exact integers. The list may be
    /// empty.
    pub fn read(edges: &Datum) -> Option<Self> {
        let mut graph = Graph {
            names: Vec::new(),
            edges: Vec::new(),
        };
        for edge in edges.as_list()? {
            let (from, to) = pair(edge)?;
            let from = graph.number(from);
            let to = graph.number(to);
            graph.edges.push((from, to));
        }
        Some(graph)
    }

    fn number(&mut self, name: &BigInt) -> usize {
        self.names
            .iter()
            .position(|known| known == name)
            .unwrap_or_else(|| {
                self.names.push(name.clone());
                self.names.len() - 1
            })
    }

    /// The edges as pairs of vertex numbers.
    pub fn edges(&self) -> &[(usize, usize)] {
        &self.edges
    }

    /// The names of the vertices, in the order the edges first name them.
    pub fn names(&self) -> &[BigInt] {
        &self.names
    }

    /// Whether the vertices are named `0, 1, ..., n - 1`, in any order.
    pub fn is_numbered(&self) -> bool {
        let names: BTreeSet<&BigInt> = self.names.iter().collect();
        (0..self.names.len()).all(|number| names.contains(&BigInt::from(number)))
    }

    /// The vertex a name denotes, if an edge names it.
    pub fn vertex(&self, name: &BigInt) -> Option<usize> {
        self.names.iter().position(|known| known == name)
    }

    pub fn forest(&self) -> Forest {
        let mut neighbours: Vec<Vec<Link>> = vec![Vec::new(); self.names.len()];
        for (edge, &(from, to)) in self.edges.iter().enumerate() {
            neighbours[from].push((to, edge, 1));
            neighbours[to].push((from, edge, -1));
        }
        let mut parent: Vec<Option<Link>> = vec![None; self.names.len()];
        let mut reached = vec![false; self.names.len()];
        let mut in_forest = vec![false; self.edges.len()];
        let mut order = Vec::new();
        for root in 0..self.names.len() {
            if reached[root] {
                continue;
            }
            reached[root] = true;
            let mut queue = VecDeque::from([root]);
            while let Some(at) = queue.pop_front() {
                order.push(at);
                for &(next, edge, sign) in &neighbours[at] {
                    if !reached[next] {
                        reached[next] = true;
                        parent[next] = Some((at, edge, sign));
                        in_forest[edge] = true;
                        queue.push_back(next);
                    }
                }
            }
        }
        let chords = (0..self.edges.len())
            .filter(|&edge| !in_forest[edge])
            .collect();
        Forest {
            parent,
            chords,
            order,
        }
    }

    /// One cycle per chord, in chord order, as signed edges: the chord forwards, the forest edges
    /// from its head up to where the two paths to the root meet, each against the way the forest
    /// climbs it, and the forest edges from its tail up to that point, each the way it climbs.
    pub fn fundamental_cycles(&self) -> Vec<Vec<Step>> {
        let forest = self.forest();
        let to_root = |mut vertex: usize| {
            let mut path = Vec::new();
            while let Some((above, edge, sign)) = forest.parent[vertex] {
                path.push((edge, sign));
                vertex = above;
            }
            path
        };
        forest
            .chords
            .iter()
            .map(|&chord| {
                let (tail, head) = self.edges[chord];
                let (from_tail, from_head) = (to_root(tail), to_root(head));
                let shared = |edge: usize, other: &[Step]| other.iter().any(|step| step.0 == edge);
                let down = from_head
                    .iter()
                    .filter(|step| !shared(step.0, &from_tail))
                    .map(|&(edge, sign)| (edge, -sign));
                let up = from_tail
                    .iter()
                    .filter(|step| !shared(step.0, &from_head))
                    .copied();
                [(chord, 1)].into_iter().chain(down).chain(up).collect()
            })
            .collect()
    }

    /// The coboundary of a value on every vertex: on an edge, the value at its head less the
    /// value at its tail.
    pub fn coboundary(&self, potential: &[Rational]) -> Vec<Rational> {
        self.edges
            .iter()
            .map(|&(from, to)| at(potential, to) - at(potential, from))
            .collect()
    }

    /// The value on every vertex that is zero at each root and matches `values` along the forest.
    pub fn potential(&self, values: &[Rational]) -> Vec<Rational> {
        let forest = self.forest();
        let mut potential = vec![Rational::zero(); self.names.len()];
        for &vertex in &forest.order {
            if let Some((above, edge, sign)) = forest.parent[vertex] {
                potential[vertex] = &potential[above] + signed(values, edge, sign);
            }
        }
        potential
    }

    /// What is left of `values` once the coboundary of `potential` is taken away.
    pub fn residual(&self, values: &[Rational], potential: &[Rational]) -> Vec<Rational> {
        self.coboundary(potential)
            .into_iter()
            .enumerate()
            .map(|(edge, explained)| at(values, edge) - explained)
            .collect()
    }

    /// The sum of the sizes of what the forest potential leaves unexplained. It is zero exactly
    /// when `values` is a coboundary.
    pub fn defect(&self, values: &[Rational]) -> Rational {
        self.residual(values, &self.potential(values))
            .iter()
            .map(Signed::abs)
            .sum()
    }
}

/// The entry at `index`, or zero when the list is shorter.
fn at(values: &[Rational], index: usize) -> Rational {
    values.get(index).cloned().unwrap_or_else(Rational::zero)
}

/// The value on an edge as a step takes it: itself forwards, its negative backwards.
fn signed(values: &[Rational], edge: usize, sign: i8) -> Rational {
    if sign == 1 {
        at(values, edge)
    } else {
        -at(values, edge)
    }
}

/// The sum of `values` along a walk, each edge counted with its sign.
pub fn walk_sum(walk: &[Step], values: &[Rational]) -> Rational {
    walk.iter()
        .map(|&(edge, sign)| signed(values, edge, sign))
        .sum()
}
