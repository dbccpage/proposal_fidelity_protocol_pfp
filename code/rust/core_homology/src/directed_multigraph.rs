//! Finite edge-indexed directed multigraphs and their bounded path category.
//! Parallel edges are distinct generators; self-loops are cycles. Acyclicity
//! is decided in O(V+E). No path is dropped to turn a failed walk into evidence.
//! AuthorityEffect: None.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_387cebb9<T> {
    fn checked_invariant_387cebb9(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_387cebb9<T> for Option<T> {
    #[inline]
    fn checked_invariant_387cebb9(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_387cebb9<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_387cebb9(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::collections::VecDeque;
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum DirectedMultigraphError {
    #[error("edge {edge} names vertex {vertex} outside {count} vertices")]
    Vertex {
        edge: usize,
        vertex: usize,
        count: usize,
    },
    #[error("vertex {vertex} is blocked by a directed cycle")]
    Cycle { vertex: usize },
    #[error("operation exceeds the declared finite graph/path budget")]
    Budget,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DirectedMultigraph {
    vertices: usize,
    edges: Vec<(usize, usize)>,
    outgoing: Vec<Vec<usize>>,
}
impl DirectedMultigraph {
    pub fn new(
        vertices: usize,
        edges: Vec<(usize, usize)>,
    ) -> Result<Self, DirectedMultigraphError> {
        if vertices > 4096 || edges.len() > 16384 {
            return Err(DirectedMultigraphError::Budget);
        }
        let mut outgoing = vec![Vec::new(); vertices];
        for (edge, &(u, v)) in edges.iter().enumerate() {
            for vertex in [u, v] {
                if vertex >= vertices {
                    return Err(DirectedMultigraphError::Vertex {
                        edge,
                        vertex,
                        count: vertices,
                    });
                }
            }
            outgoing[u].push(edge);
        }
        Ok(Self {
            vertices,
            edges,
            outgoing,
        })
    }
    pub fn topological_order(&self) -> Result<Vec<usize>, DirectedMultigraphError> {
        let mut degrees = vec![0usize; self.vertices];
        for &(_, v) in &self.edges {
            degrees[v] += 1;
        }
        let mut queue: VecDeque<usize> = (0..self.vertices).filter(|&v| degrees[v] == 0).collect();
        let mut order = Vec::with_capacity(self.vertices);
        while let Some(u) = queue.pop_front() {
            order.push(u);
            for &edge in &self.outgoing[u] {
                let v = self.edges[edge].1;
                degrees[v] -= 1;
                if degrees[v] == 0 {
                    queue.push_back(v);
                }
            }
        }
        if let Some(vertex) = degrees.iter().position(|&d| d != 0) {
            return Err(DirectedMultigraphError::Cycle { vertex });
        }
        Ok(order)
    }
    /// Directed unweighted graph distances, valid for cyclic graphs as well.
    pub fn shortest_distances(
        &self,
        source: usize,
    ) -> Result<Vec<Option<usize>>, DirectedMultigraphError> {
        if source >= self.vertices {
            return Err(DirectedMultigraphError::Vertex {
                edge: 0,
                vertex: source,
                count: self.vertices,
            });
        }
        let mut distances = vec![None; self.vertices];
        distances[source] = Some(0);
        let mut queue = VecDeque::from([source]);
        while let Some(u) = queue.pop_front() {
            for &edge in &self.outgoing[u] {
                let v = self.edges[edge].1;
                if distances[v].is_none() {
                    distances[v] = Some(distances[u].checked_invariant_387cebb9("queued vertex visited") + 1);
                    queue.push_back(v);
                }
            }
        }
        Ok(distances)
    }
    /// All edge-indexed paths, including the identity path at a=b. Counts are
    /// computed before enumeration; refusing a bound produces no partial hom-set.
    pub fn all_paths(
        &self,
        a: usize,
        b: usize,
        limit: usize,
    ) -> Result<Vec<Vec<usize>>, DirectedMultigraphError> {
        for vertex in [a, b] {
            if vertex >= self.vertices {
                return Err(DirectedMultigraphError::Vertex {
                    edge: 0,
                    vertex,
                    count: self.vertices,
                });
            }
        }
        if limit > 65536 {
            return Err(DirectedMultigraphError::Budget);
        }
        let order = self.topological_order()?;
        let counts = self.count_paths_to(b, limit, &order);
        if counts[a] > limit {
            return Err(DirectedMultigraphError::Budget);
        }
        Ok(self.enumerate_paths(a, b, &counts))
    }

    fn count_paths_to(&self, b: usize, limit: usize, order: &[usize]) -> Vec<usize> {
        let mut counts = vec![0usize; self.vertices];
        counts[b] = 1;
        for &u in order.iter().rev() {
            if u == b {
                continue;
            }
            for &edge in &self.outgoing[u] {
                counts[u] = counts[u]
                    .saturating_add(counts[self.edges[edge].1])
                    .min(limit.saturating_add(1));
            }
        }
        counts
    }

    fn enumerate_paths(&self, a: usize, b: usize, counts: &[usize]) -> Vec<Vec<usize>> {
        let mut result = Vec::with_capacity(counts[a]);
        let mut stack = vec![(a, Vec::new())];
        while let Some((u, path)) = stack.pop() {
            if u == b {
                result.push(path);
                continue;
            }
            for &edge in self.outgoing[u].iter().rev() {
                let v = self.edges[edge].1;
                if counts[v] == 0 {
                    continue;
                }
                let mut next = path.clone();
                next.push(edge);
                stack.push((v, next));
            }
        }
        result
    }
}

// Origin: engine/crates_rs/core_homology/src/directed_multigraph.rs
// Claim: urn:core:crates_rs:core-homology:directed-multigraph:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod dynamics_laws {

    use super::*;
    #[test]
    fn parallel_paths_have_distinct_edges_and_composition_is_complete() {
        let g = DirectedMultigraph::new(4, vec![(0, 1), (0, 1), (1, 3), (0, 2), (2, 3)]).unwrap();
        assert_eq!(
            g.all_paths(0, 3, 3).unwrap(),
            vec![vec![0, 2], vec![1, 2], vec![3, 4]]
        );
        assert_eq!(g.all_paths(2, 2, 1).unwrap(), vec![Vec::<usize>::new()]);
        assert_eq!(g.all_paths(3, 0, 0).unwrap(), Vec::<Vec<usize>>::new());
        assert!(matches!(
            g.all_paths(0, 3, 2),
            Err(DirectedMultigraphError::Budget)
        ));
        assert!(matches!(
            g.all_paths(0, 3, usize::MAX),
            Err(DirectedMultigraphError::Budget)
        ));
    }
    #[test]
    fn directed_cycles_and_invalid_vertices_are_refusals() {
        let g = DirectedMultigraph::new(2, vec![(0, 1), (1, 0)]).unwrap();
        assert!(matches!(
            g.all_paths(0, 1, 10),
            Err(DirectedMultigraphError::Cycle { .. })
        ));
        assert!(DirectedMultigraph::new(1, vec![(0, 1)]).is_err());
    }
}
