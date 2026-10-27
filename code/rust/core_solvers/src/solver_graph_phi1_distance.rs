//! Exact finite graph quotient distance for the Python governor adapter.
//!
//! The graph is small and explicit. We enumerate every spanning forest gauge,
//! submit residuals to Phi1Functional, and return a deterministic minimizer
//! only after canonical primal-dual replay.
//! A bounded search refuses instead of returning an unproved partial minimum.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_39052190<T> {
    fn checked_invariant_39052190(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_39052190<T> for Option<T> {
    #[inline]
    fn checked_invariant_39052190(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_39052190<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_39052190(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use num_rational::BigRational;
use num_traits::Zero;
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};
use std::str::FromStr;

const MAX_FORESTS: usize = 100_000;

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct GraphPhi1Edge {
    pub u: String,
    pub v: String,
    pub weight: String,
    pub claim: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct GraphPhi1Request {
    pub vertices: Vec<String>,
    pub edges: Vec<GraphPhi1Edge>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct GraphPhi1Result {
    pub phi1: String,
    pub gauge: BTreeMap<String, String>,
    pub forests_checked: usize,
}

#[derive(Debug, thiserror::Error, PartialEq, Eq)]
pub enum GraphPhi1Error {
    #[error("duplicate vertex")]
    DuplicateVertex,
    #[error("edge endpoint absent from declared carrier")]
    UnknownEndpoint,
    #[error("self edge")]
    SelfEdge,
    #[error("invalid rational")]
    InvalidRational,
    #[error("weight must be positive")]
    NonPositiveWeight,
    #[error("spanning forest enumeration limit exceeded")]
    EnumerationLimit,
    #[error("canonical Phi1 evaluation refused: {0}")]
    FunctionalRefusal(String),
}

struct Edge {
    u: usize,
    v: usize,
    weight: BigRational,
    claim: BigRational,
}

pub fn solve_graph_phi1(input: GraphPhi1Request) -> Result<GraphPhi1Result, GraphPhi1Error> {
    solve_graph_phi1_with_limit(input, MAX_FORESTS)
}

fn parse_graph_edges(
    vertices: &[String],
    raw_edges: Vec<GraphPhi1Edge>,
) -> Result<Vec<Edge>, GraphPhi1Error> {
    let mut names = BTreeMap::new();
    for (index, name) in vertices.iter().enumerate() {
        if names.insert(name.clone(), index).is_some() {
            return Err(GraphPhi1Error::DuplicateVertex);
        }
    }
    let mut edges = Vec::with_capacity(raw_edges.len());
    for edge in raw_edges {
        let u = *names.get(&edge.u).ok_or(GraphPhi1Error::UnknownEndpoint)?;
        let v = *names.get(&edge.v).ok_or(GraphPhi1Error::UnknownEndpoint)?;
        if u == v {
            return Err(GraphPhi1Error::SelfEdge);
        }
        let weight =
            BigRational::from_str(&edge.weight).map_err(|_| GraphPhi1Error::InvalidRational)?;
        let claim =
            BigRational::from_str(&edge.claim).map_err(|_| GraphPhi1Error::InvalidRational)?;
        if weight <= BigRational::zero() {
            return Err(GraphPhi1Error::NonPositiveWeight);
        }
        edges.push(Edge {
            u,
            v,
            weight,
            claim,
        });
    }
    Ok(edges)
}

fn certify_graph_phi1(
    edges: &[Edge],
    n: usize,
    best_gauge: &[BigRational],
) -> Result<String, GraphPhi1Error> {
    // Enumeration proposes a minimizer. Independently replay it against a
    // feasible optimal dual; only core_functional supplies the reported Phi1.
    let (d0, claims, weights) = presentation(edges, n);
    let space = core_functional::l1_seminorm::L1Seminorm::new(d0.clone(), weights.clone())
        .map_err(|e| GraphPhi1Error::FunctionalRefusal(e.to_string()))?;
    let dual = crate::solver_lp_phi1_quotient::solve_exact_phi1(&space, &claims)
        .map_err(|e| GraphPhi1Error::FunctionalRefusal(e.to_string()))?;
    let evaluated = core_functional::phi1::Phi1Functional::evaluate_exact_witness(
        &claims,
        &d0,
        &weights,
        best_gauge,
        dual.dual_witness(),
    )
    .map_err(|e| GraphPhi1Error::FunctionalRefusal(e.to_string()))?;
    Ok(evaluated.value().to_string())
}

/// Enumerate all spanning forest proposals, refusing an exhausted declared budget.
pub fn solve_graph_phi1_with_limit(
    input: GraphPhi1Request,
    limit: usize,
) -> Result<GraphPhi1Result, GraphPhi1Error> {
    let edges = parse_graph_edges(&input.vertices, input.edges)?;
    let n = input.vertices.len();
    let mut all_parent: Vec<usize> = (0..n).collect();
    for edge in &edges {
        union(&mut all_parent, edge.u, edge.v);
    }
    let components = (0..n)
        .map(|i| root(&all_parent, i))
        .collect::<BTreeSet<_>>()
        .len();
    let target = n - components;
    let mut best_gauge = vec![BigRational::zero(); n];
    let mut best = weighted_residual(&edges, &best_gauge);
    let mut checked = 0usize;
    let mut chosen = Vec::with_capacity(target);
    enumerate(
        0,
        target,
        &edges,
        &(0..n).collect::<Vec<_>>(),
        &mut chosen,
        &mut checked,
        limit,
        &mut best,
        &mut best_gauge,
    )?;
    let phi1 = certify_graph_phi1(&edges, n, &best_gauge)?;
    let gauge = input
        .vertices
        .into_iter()
        .zip(best_gauge)
        .map(|(name, value)| (name, value.to_string()))
        .collect();
    Ok(GraphPhi1Result {
        phi1,
        gauge,
        forests_checked: checked,
    })
}

fn root(parent: &[usize], mut i: usize) -> usize {
    while parent[i] != i {
        i = parent[i];
    }
    i
}

fn union(parent: &mut [usize], a: usize, b: usize) -> bool {
    let a = root(parent, a);
    let b = root(parent, b);
    if a == b {
        false
    } else {
        parent[a] = b;
        true
    }
}

fn presentation(
    edges: &[Edge],
    vertices: usize,
) -> (Vec<Vec<BigRational>>, Vec<BigRational>, Vec<BigRational>) {
    let d0 = edges
        .iter()
        .map(|edge| {
            let mut row = vec![BigRational::zero(); vertices];
            row[edge.u] = BigRational::from_integer((-1).into());
            row[edge.v] = BigRational::from_integer(1.into());
            row
        })
        .collect();
    (
        d0,
        edges.iter().map(|e| e.claim.clone()).collect(),
        edges.iter().map(|e| e.weight.clone()).collect(),
    )
}

fn weighted_residual(edges: &[Edge], gauge: &[BigRational]) -> BigRational {
    let (d0, claims, weights) = presentation(edges, gauge.len());
    core_functional::phi1::Phi1Functional::evaluate_representative(&claims, &d0, &weights, gauge)
        .checked_invariant_39052190("validated graph dimensions and exact rational coefficients")
        .1
}

fn build_forest_gauge(n: usize, edges: &[Edge], chosen: &[usize]) -> Vec<BigRational> {
    let mut gauge = vec![BigRational::zero(); n];
    let mut adjacency = vec![Vec::<(usize, BigRational)>::new(); n];
    for &index in chosen {
        let edge = &edges[index];
        adjacency[edge.u].push((edge.v, edge.claim.clone()));
        adjacency[edge.v].push((edge.u, -edge.claim.clone()));
    }
    let mut seen = vec![false; n];
    for start in 0..n {
        if seen[start] {
            continue;
        }
        seen[start] = true;
        let mut stack = vec![start];
        while let Some(u) = stack.pop() {
            for (v, delta) in &adjacency[u] {
                if !seen[*v] {
                    seen[*v] = true;
                    gauge[*v] = &gauge[u] + delta;
                    stack.push(*v);
                }
            }
        }
    }
    gauge
}

#[allow(clippy::too_many_arguments)]
fn enumerate(
    next: usize,
    target: usize,
    edges: &[Edge],
    parent: &[usize],
    chosen: &mut Vec<usize>,
    checked: &mut usize,
    limit: usize,
    best: &mut BigRational,
    best_gauge: &mut Vec<BigRational>,
) -> Result<(), GraphPhi1Error> {
    if chosen.len() == target {
        if *checked == limit {
            return Err(GraphPhi1Error::EnumerationLimit);
        }
        *checked += 1;
        let gauge = build_forest_gauge(parent.len(), edges, chosen);
        let cost = weighted_residual(edges, &gauge);
        if cost < *best {
            *best = cost;
            *best_gauge = gauge;
        }
        return Ok(());
    }
    if next >= edges.len() || chosen.len() + edges.len() - next < target {
        return Ok(());
    }
    let edge = &edges[next];
    let mut included_parent = parent.to_vec();
    if union(&mut included_parent, edge.u, edge.v) {
        chosen.push(next);
        enumerate(
            next + 1,
            target,
            edges,
            &included_parent,
            chosen,
            checked,
            limit,
            best,
            best_gauge,
        )?;
        chosen.pop();
    }
    enumerate(
        next + 1,
        target,
        edges,
        parent,
        chosen,
        checked,
        limit,
        best,
        best_gauge,
    )
}

// Origin: engine/crates_rs/core_solvers/src/solver_graph_phi1_distance.rs
// Claim: urn:core:crates_rs:core-solvers:solver-graph-phi1-distance:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    fn edge(u: &str, v: &str, claim: &str) -> GraphPhi1Edge {
        GraphPhi1Edge {
            u: u.into(),
            v: v.into(),
            weight: "1".into(),
            claim: claim.into(),
        }
    }
    #[test]
    fn exact_and_inconsistent_triangles() {
        let vertices = vec!["a".into(), "b".into(), "c".into()];
        let exact = solve_graph_phi1(GraphPhi1Request {
            vertices: vertices.clone(),
            edges: vec![
                edge("a", "b", "1"),
                edge("b", "c", "1"),
                edge("a", "c", "2"),
            ],
        })
        .unwrap();
        assert_eq!(exact.phi1, "0");
        let inconsistent = solve_graph_phi1(GraphPhi1Request {
            vertices,
            edges: vec![
                edge("a", "b", "1"),
                edge("b", "c", "1"),
                edge("a", "c", "3"),
            ],
        })
        .unwrap();
        assert_eq!(inconsistent.phi1, "1");
    }
    #[test]
    fn rejects_nonpositive_weight() {
        let mut bad = edge("a", "b", "1");
        bad.weight = "0".into();
        assert_eq!(
            solve_graph_phi1(GraphPhi1Request {
                vertices: vec!["a".into(), "b".into()],
                edges: vec![bad]
            })
            .unwrap_err(),
            GraphPhi1Error::NonPositiveWeight
        );
    }
    #[test]
    fn rational_triangle_uses_exact_weighted_minimum() {
        let mut closing = edge("a", "c", "3/2");
        closing.weight = "2".into();
        let result = solve_graph_phi1(GraphPhi1Request {
            vertices: vec!["a".into(), "b".into(), "c".into()],
            edges: vec![edge("a", "b", "1/2"), edge("b", "c", "1/2"), closing],
        })
        .unwrap();
        assert_eq!(result.phi1, "1/2");
    }

    #[test]
    fn planar_triangular_multi_cycle_b1_2() {
        // 4 vertices, 5 edges: 2 triangles sharing edge (v1, v2).
        // First Betti number b1 = 5 - 4 + 1 = 2.
        let vertices = vec!["v0".into(), "v1".into(), "v2".into(), "v3".into()];
        let edges = vec![
            edge("v0", "v1", "1"),
            edge("v1", "v2", "1"),
            edge("v2", "v0", "1"),
            edge("v1", "v3", "1"),
            edge("v3", "v2", "1"),
        ];
        let result = solve_graph_phi1(GraphPhi1Request { vertices, edges }).unwrap();
        assert_eq!(result.phi1, "4");
        assert_eq!(result.forests_checked, 8);
    }

    #[test]
    fn kagome_trimer_multi_cycle_b1_4() {
        // 6 vertices, 9 edges: 3 corner-sharing triangles in a trimer ring.
        // First Betti number b1 = 9 - 6 + 1 = 4.
        let vertices = vec![
            "v0".into(),
            "v1".into(),
            "v2".into(),
            "v3".into(),
            "v4".into(),
            "v5".into(),
        ];
        let edges = vec![
            // Triangle 0: (v0, v1, v2)
            edge("v0", "v1", "1"),
            edge("v1", "v2", "1"),
            edge("v2", "v0", "1"),
            // Triangle 1: (v2, v3, v4) sharing v2
            edge("v2", "v3", "1"),
            edge("v3", "v4", "1"),
            edge("v4", "v2", "1"),
            // Triangle 2: (v4, v5, v0) sharing v4 and v0
            edge("v4", "v5", "1"),
            edge("v5", "v0", "1"),
            edge("v0", "v4", "1"),
        ];
        let result = solve_graph_phi1(GraphPhi1Request { vertices, edges }).unwrap();
        assert_eq!(result.phi1, "9");
        assert_eq!(result.forests_checked, 54);
    }
}

#[cfg(test)]
mod paper_conformance {
    use super::*;
    fn edge(u: &str, v: &str, claim: &str) -> GraphPhi1Edge {
        GraphPhi1Edge {
            u: u.into(),
            v: v.into(),
            weight: "1".into(),
            claim: claim.into(),
        }
    }
    #[test]
    fn exact_and_inconsistent_triangles() {
        let vertices = vec!["a".into(), "b".into(), "c".into()];
        let exact = solve_graph_phi1(GraphPhi1Request {
            vertices: vertices.clone(),
            edges: vec![
                edge("a", "b", "1"),
                edge("b", "c", "1"),
                edge("a", "c", "2"),
            ],
        })
        .unwrap();
        assert_eq!(exact.phi1, "0");
        let inconsistent = solve_graph_phi1(GraphPhi1Request {
            vertices,
            edges: vec![
                edge("a", "b", "1"),
                edge("b", "c", "1"),
                edge("a", "c", "3"),
            ],
        })
        .unwrap();
        assert_eq!(inconsistent.phi1, "1");
    }
    #[test]
    fn rejects_nonpositive_weight() {
        let mut bad = edge("a", "b", "1");
        bad.weight = "0".into();
        assert_eq!(
            solve_graph_phi1(GraphPhi1Request {
                vertices: vec!["a".into(), "b".into()],
                edges: vec![bad]
            })
            .unwrap_err(),
            GraphPhi1Error::NonPositiveWeight
        );
    }
    #[test]
    fn rational_triangle_uses_exact_weighted_minimum() {
        let mut closing = edge("a", "c", "3/2");
        closing.weight = "2".into();
        let result = solve_graph_phi1(GraphPhi1Request {
            vertices: vec!["a".into(), "b".into(), "c".into()],
            edges: vec![edge("a", "b", "1/2"), edge("b", "c", "1/2"), closing],
        })
        .unwrap();
        assert_eq!(result.phi1, "1/2");
    }

    #[test]
    fn planar_triangular_multi_cycle_b1_2() {
        // 4 vertices, 5 edges: 2 triangles sharing edge (v1, v2).
        // First Betti number b1 = 5 - 4 + 1 = 2.
        let vertices = vec!["v0".into(), "v1".into(), "v2".into(), "v3".into()];
        let edges = vec![
            edge("v0", "v1", "1"),
            edge("v1", "v2", "1"),
            edge("v2", "v0", "1"),
            edge("v1", "v3", "1"),
            edge("v3", "v2", "1"),
        ];
        let result = solve_graph_phi1(GraphPhi1Request { vertices, edges }).unwrap();
        assert_eq!(result.phi1, "4");
        assert_eq!(result.forests_checked, 8);
    }

    #[test]
    fn kagome_trimer_multi_cycle_b1_4() {
        // 6 vertices, 9 edges: 3 corner-sharing triangles in a trimer ring.
        // First Betti number b1 = 9 - 6 + 1 = 4.
        let vertices = vec![
            "v0".into(),
            "v1".into(),
            "v2".into(),
            "v3".into(),
            "v4".into(),
            "v5".into(),
        ];
        let edges = vec![
            // Triangle 0: (v0, v1, v2)
            edge("v0", "v1", "1"),
            edge("v1", "v2", "1"),
            edge("v2", "v0", "1"),
            // Triangle 1: (v2, v3, v4) sharing v2
            edge("v2", "v3", "1"),
            edge("v3", "v4", "1"),
            edge("v4", "v2", "1"),
            // Triangle 2: (v4, v5, v0) sharing v4 and v0
            edge("v4", "v5", "1"),
            edge("v5", "v0", "1"),
            edge("v0", "v4", "1"),
        ];
        let result = solve_graph_phi1(GraphPhi1Request { vertices, edges }).unwrap();
        assert_eq!(result.phi1, "9");
        assert_eq!(result.forests_checked, 54);
    }

    fn kagome_request() -> GraphPhi1Request {
        let vertices = (0..6).map(|i| format!("v{i}")).collect();
        let pairs = [
            (0, 1),
            (1, 2),
            (2, 0),
            (2, 3),
            (3, 4),
            (4, 2),
            (4, 5),
            (5, 0),
            (0, 4),
        ];
        let edges = pairs
            .iter()
            .map(|(u, v)| edge(&format!("v{u}"), &format!("v{v}"), "1"))
            .collect();
        GraphPhi1Request { vertices, edges }
    }

    #[test]
    fn enumeration_limit_refuses_instead_of_returning_partial_minimum() {
        // The kagome fixture has exactly 54 spanning trees.
        assert_eq!(
            solve_graph_phi1_with_limit(kagome_request(), 54)
                .unwrap()
                .forests_checked,
            54
        );
        assert_eq!(
            solve_graph_phi1_with_limit(kagome_request(), 53).unwrap_err(),
            GraphPhi1Error::EnumerationLimit
        );
    }

    #[test]
    fn manuscript_triangle_minimum_is_three() {
        // Reports (1,1,1) on a->b, b->c, c->a with penalties (1,2,3).
        let weighted = |u: &str, v: &str, w: &str| GraphPhi1Edge {
            u: u.into(),
            v: v.into(),
            weight: w.into(),
            claim: "1".into(),
        };
        let result = solve_graph_phi1(GraphPhi1Request {
            vertices: vec!["a".into(), "b".into(), "c".into()],
            edges: vec![
                weighted("a", "b", "1"),
                weighted("b", "c", "2"),
                weighted("c", "a", "3"),
            ],
        })
        .unwrap();
        assert_eq!(result.phi1, "3");
        let s = |name: &str| BigRational::from_str(&result.gauge[name]).unwrap();
        // The returned potential attains the minimum: only a->b carries residual 3.
        assert_eq!(
            BigRational::from_integer(1.into()) - (s("b") - s("a")),
            BigRational::from_integer(3.into())
        );
    }

    #[test]
    fn rejects_unknown_endpoint_self_edge_and_bad_rational() {
        let two = || vec!["a".to_string(), "b".to_string()];
        let unknown = GraphPhi1Request {
            vertices: two(),
            edges: vec![edge("a", "x", "1")],
        };
        assert_eq!(
            solve_graph_phi1(unknown).unwrap_err(),
            GraphPhi1Error::UnknownEndpoint
        );
        let looped = GraphPhi1Request {
            vertices: two(),
            edges: vec![edge("a", "a", "1")],
        };
        assert_eq!(
            solve_graph_phi1(looped).unwrap_err(),
            GraphPhi1Error::SelfEdge
        );
        let decimal = GraphPhi1Request {
            vertices: two(),
            edges: vec![edge("a", "b", "0.5")],
        };
        assert_eq!(
            solve_graph_phi1(decimal).unwrap_err(),
            GraphPhi1Error::InvalidRational
        );
        let zero_denominator = GraphPhi1Request {
            vertices: two(),
            edges: vec![edge("a", "b", "1/0")],
        };
        assert_eq!(
            solve_graph_phi1(zero_denominator).unwrap_err(),
            GraphPhi1Error::InvalidRational
        );
    }
}
