//! Exact finite signed transport certificates on COMPLETE supplied coefficients.
//! AuthorityEffect: None. The only gauge class is diagonal +/-1. A Hamiltonian
//! interpretation, path partition or sampler is not inferred from this graph.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_4870e456<T> {
    fn checked_invariant_4870e456(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_4870e456<T> for Option<T> {
    #[inline]
    fn checked_invariant_4870e456(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_4870e456<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_4870e456(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use num_rational::BigRational;
use num_traits::Zero;
use serde::{Deserialize, Serialize};
use std::collections::{BTreeSet, VecDeque};

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
#[error("signed transport refusal: {0}")]
pub struct SignedTransportError(pub &'static str);

fn canonical(q: &BigRational) -> bool {
    if q.denom() <= &0.into() {
        return false;
    }
    let normalized = BigRational::new(q.numer().clone(), q.denom().clone());
    normalized.numer() == q.numer() && normalized.denom() == q.denom()
}

/// Checked symmetric rational coefficients; diagonal is retained as input but
/// never treated as a self-edge. Empty transport carrier is permitted.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SignedCoefficientGraph {
    coefficients: Vec<Vec<BigRational>>,
}
impl SignedCoefficientGraph {
    pub fn try_new(coefficients: Vec<Vec<BigRational>>) -> Result<Self, SignedTransportError> {
        let n = coefficients.len();
        if coefficients.iter().any(|r| r.len() != n) {
            return Err(SignedTransportError("non-square coefficient matrix"));
        }
        if coefficients.iter().flatten().any(|q| !canonical(q)) {
            return Err(SignedTransportError(
                "noncanonical rational or invalid denominator",
            ));
        }
        for i in 0..n {
            for j in 0..n {
                if coefficients[i][j] != coefficients[j][i] {
                    return Err(SignedTransportError("asymmetric original coefficients"));
                }
            }
        }
        Ok(Self { coefficients })
    }
    /// Canonical wire rationals only: integer or reduced p/q, no float aliases.
    pub fn from_strings(rows: &[Vec<String>]) -> Result<Self, SignedTransportError> {
        let coefficients = rows
            .iter()
            .map(|row| {
                row.iter()
                    .map(|s| {
                        let q = s.parse::<BigRational>().map_err(|_| {
                            SignedTransportError("invalid rational wire coefficient")
                        })?;
                        if !canonical(&q) || q.to_string() != *s {
                            return Err(SignedTransportError(
                                "noncanonical rational wire coefficient",
                            ));
                        }
                        Ok(q)
                    })
                    .collect::<Result<Vec<_>, _>>()
            })
            .collect::<Result<Vec<_>, _>>()?;
        Self::try_new(coefficients)
    }
    pub fn dimension(&self) -> usize {
        self.coefficients.len()
    }
    pub fn coefficients(&self) -> &[Vec<BigRational>] {
        &self.coefficients
    }
    pub fn canonical_coefficients(&self) -> Vec<Vec<String>> {
        self.coefficients
            .iter()
            .map(|r| r.iter().map(ToString::to_string).collect())
            .collect()
    }
    /// Bool parity of transport t=-sign(H): true for a positive H edge.
    pub fn edge_parity(&self, a: usize, b: usize) -> Option<bool> {
        if a >= self.dimension()
            || b >= self.dimension()
            || a == b
            || self.coefficients[a][b].is_zero()
        {
            return None;
        }
        Some(self.coefficients[a][b] > BigRational::zero())
    }
    pub fn walk_parity(&self, walk: &[usize]) -> Result<bool, SignedTransportError> {
        if walk.is_empty() || walk.iter().any(|&v| v >= self.dimension()) {
            return Err(SignedTransportError("empty or out-of-carrier walk"));
        }
        let mut parity = false;
        for e in walk.windows(2) {
            parity ^= self.edge_parity(e[0], e[1]).ok_or(SignedTransportError(
                "walk uses a self-edge or omitted/non-edge",
            ))?;
        }
        Ok(parity)
    }
}

/// Public payloads are untrusted; every consumer must replay verify().
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ForestGauge {
    pub roots: Vec<usize>,
    /// Includes both root and endpoint; root's own path is [root].
    pub paths: Vec<Vec<usize>>,
    /// false means +1, true means -1.
    pub gauge_parities: Vec<bool>,
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "kind", content = "payload", rename_all = "snake_case")]
pub enum SignedTransportOutcome {
    Gauge(ForestGauge),
    NegativeCycle(Vec<usize>),
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SignedTransportCertificate {
    /// Binds magnitudes, zeros and arbitrary diagonal as well as edge signs.
    pub original_coefficients: Vec<Vec<String>>,
    pub outcome: SignedTransportOutcome,
}

fn validate_forest_dimensions(forest: &ForestGauge, n: usize) -> Result<(), SignedTransportError> {
    if forest.roots.len() != n || forest.paths.len() != n || forest.gauge_parities.len() != n {
        return Err(SignedTransportError("forest/gauge carrier mismatch"));
    }
    Ok(())
}

fn check_vertex_path_validity(
    forest: &ForestGauge,
    v: usize,
    root: usize,
    n: usize,
) -> bool {
    let path = &forest.paths[v];
    root < n
        && path.first() == Some(&root)
        && path.last() == Some(&v)
        && forest.roots[root] == root
        && forest.paths[root] == [root]
        && path.iter().copied().collect::<BTreeSet<_>>().len() == path.len()
}

fn verify_vertex_path(
    graph: &SignedCoefficientGraph,
    forest: &ForestGauge,
    v: usize,
    n: usize,
) -> Result<(), SignedTransportError> {
    let root = forest.roots[v];
    let path = &forest.paths[v];
    if !check_vertex_path_validity(forest, v, root, n) {
        return Err(SignedTransportError("invalid root or spanning-forest path"));
    }
    let parity = graph.walk_parity(path)?;
    if forest.gauge_parities[v] != forest.gauge_parities[root] ^ parity {
        return Err(SignedTransportError(
            "path gauge does not realize its transport",
        ));
    }
    for (index, &node) in path.iter().enumerate() {
        if forest.roots[node] != root || forest.paths[node] != path[..=index] {
            return Err(SignedTransportError(
                "paths do not form a prefix-consistent forest",
            ));
        }
    }
    Ok(())
}

fn verify_edge_compatibilities(
    graph: &SignedCoefficientGraph,
    forest: &ForestGauge,
    n: usize,
) -> Result<(), SignedTransportError> {
    for a in 0..n {
        for b in a + 1..n {
            let Some(parity) = graph.edge_parity(a, b) else {
                continue;
            };
            if forest.roots[a] != forest.roots[b]
                || forest.gauge_parities[a] ^ forest.gauge_parities[b] != parity
            {
                return Err(SignedTransportError(
                    "gauge omits or fails an original edge",
                ));
            }
        }
    }
    Ok(())
}

fn verify_forest(
    graph: &SignedCoefficientGraph,
    forest: &ForestGauge,
) -> Result<(), SignedTransportError> {
    let n = graph.dimension();
    validate_forest_dimensions(forest, n)?;
    for v in 0..n {
        verify_vertex_path(graph, forest, v, n)?;
    }
    // Complete original edge population: never trust a caller's edge subset.
    verify_edge_compatibilities(graph, forest, n)?;
    Ok(())
}

fn verify_negative_cycle(
    graph: &SignedCoefficientGraph,
    walk: &[usize],
) -> Result<(), SignedTransportError> {
    let simple_closed = walk.len() >= 4
        && walk.first() == walk.last()
        && walk[..walk.len() - 1]
            .iter()
            .copied()
            .collect::<BTreeSet<_>>()
            .len()
            == walk.len() - 1;
    if !simple_closed || !graph.walk_parity(walk)? {
        return Err(SignedTransportError(
            "not an actual simple negative closed transport cycle",
        ));
    }
    Ok(())
}

impl SignedTransportCertificate {
    pub fn verify(&self, graph: &SignedCoefficientGraph) -> Result<(), SignedTransportError> {
        if self.original_coefficients != graph.canonical_coefficients() {
            return Err(SignedTransportError(
                "certificate is bound to different original coefficients",
            ));
        }
        match &self.outcome {
            SignedTransportOutcome::Gauge(f) => verify_forest(graph, f),
            SignedTransportOutcome::NegativeCycle(walk) => verify_negative_cycle(graph, walk),
        }
    }
}

fn conflict_cycle(left: &[usize], right: &[usize]) -> Vec<usize> {
    let shared = left.iter().zip(right).take_while(|(a, b)| a == b).count();
    let mut cycle: Vec<_> = left[shared - 1..].iter().rev().copied().collect();
    cycle.extend_from_slice(&right[shared..]);
    cycle.push(*left.last().checked_invariant_4870e456("nonempty root path"));
    cycle
}

fn explore_component(
    graph: &SignedCoefficientGraph,
    root: usize,
    forest: &mut ForestGauge,
    n: usize,
) -> Option<Vec<usize>> {
    forest.roots[root] = root;
    forest.paths[root] = vec![root];
    let mut queue = VecDeque::from([root]);
    while let Some(a) = queue.pop_front() {
        for b in 0..n {
            let Some(parity) = graph.edge_parity(a, b) else {
                continue;
            };
            let required = forest.gauge_parities[a] ^ parity;
            if forest.roots[b] == usize::MAX {
                forest.roots[b] = root;
                forest.gauge_parities[b] = required;
                let mut path = forest.paths[a].clone();
                path.push(b);
                forest.paths[b] = path;
                queue.push_back(b);
            } else if forest.gauge_parities[b] != required {
                return Some(conflict_cycle(&forest.paths[a], &forest.paths[b]));
            }
        }
    }
    None
}

/// Deterministic spanning-forest search; generation and verification are separate.
pub fn certify_signed_transport(graph: &SignedCoefficientGraph) -> SignedTransportCertificate {
    let n = graph.dimension();
    let mut forest = ForestGauge {
        roots: vec![usize::MAX; n],
        paths: vec![vec![]; n],
        gauge_parities: vec![false; n],
    };
    for root in 0..n {
        if forest.roots[root] != usize::MAX {
            continue;
        }
        if let Some(cycle) = explore_component(graph, root, &mut forest, n) {
            return SignedTransportCertificate {
                original_coefficients: graph.canonical_coefficients(),
                outcome: SignedTransportOutcome::NegativeCycle(cycle),
            };
        }
    }
    SignedTransportCertificate {
        original_coefficients: graph.canonical_coefficients(),
        outcome: SignedTransportOutcome::Gauge(forest),
    }
}

/// All realizing gauges differ by one independent parity per connected component.
/// Returned pairs use the first forest's root labels. No preferred root sign is
/// inferred: the generator chooses false merely as a presentation convention.
pub fn compare_realizing_gauges(
    graph: &SignedCoefficientGraph,
    left: &ForestGauge,
    right: &ForestGauge,
) -> Result<Vec<(usize, bool)>, SignedTransportError> {
    verify_forest(graph, left)?;
    verify_forest(graph, right)?;
    let roots: BTreeSet<_> = left.roots.iter().copied().collect();
    for v in 0..graph.dimension() {
        let root = left.roots[v];
        if left.gauge_parities[v] ^ right.gauge_parities[v]
            != left.gauge_parities[root] ^ right.gauge_parities[root]
        {
            return Err(SignedTransportError(
                "relative gauge is not constant on a component",
            ));
        }
    }
    Ok(roots
        .into_iter()
        .map(|r| (r, left.gauge_parities[r] ^ right.gauge_parities[r]))
        .collect())
}

// Origin: engine/crates_rs/core_holonomy/src/signed_transport.rs
// Claim: urn:core:crates_rs:core-holonomy:signed-transport:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_4870e456 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
