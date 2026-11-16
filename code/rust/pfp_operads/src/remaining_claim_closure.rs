//! Finite checks that accompany `lean4/RemainingClaimClosure.lean`.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:remaining-claim-closure:v1
//!
//! What this module supports: exact counts, leaf-span agreement, and the
//! shipped graph operations exercised by the tests below.
//! What it does not support: a physical or fault-tolerance reading, a live
//! model campaign, or an archive row this file does not read.
//! Narrowest claim: each public function returns the value of the arithmetic
//! or JSON check written in its body.
//! Negative control: `inspect_workflow_dag` keeps every non-implemented node
//! whose `source_pilots` list is empty.

use std::collections::BTreeSet;
use std::fs;
use std::path::Path;

use num_bigint::BigInt;
use num_traits::{Signed, Zero};
use serde::Deserialize;

use crate::exact::Rational;
use crate::graph::{walk_sum, Forest, Graph};

/// `|sum| ≤ Σ|v|` for a finite integer list.
pub fn l1_ge_abs_sum(values: &[i128]) -> bool {
    let sum: i128 = values.iter().copied().sum();
    let l1: i128 = values.iter().map(|value| value.abs()).sum();
    l1 >= sum.abs()
}

/// One edge carrying the whole sum. Its L1 norm equals the absolute sum.
pub fn one_edge_carrier(sum: i128) -> Vec<i128> {
    vec![sum]
}

/// `b^n = (b^n - (b-a)^n) + (b-a)^n` when `a ≤ b`.
pub fn admit_split(a: &BigInt, b: &BigInt, n: u32) -> Option<bool> {
    if a > b {
        return None;
    }
    let denominator = b.pow(n);
    let failure = (b - a).pow(n);
    let admitted = &denominator - &failure;
    Some(admitted + failure == denominator)
}

/// `max(tree, chords) ≤ tree + 2 * chords`.
pub fn staged_max_le(tree: u64, chords: u64) -> bool {
    tree.max(chords) <= tree.saturating_add(chords.saturating_mul(2))
}

/// The five named graphs in ATL-P017-008: tree edges, `2 b_1`, unstaged, staged.
pub fn named_arity_rows() -> [(u64, u64, u64, u64); 5] {
    [
        (5, 8, 13, 5),
        (7, 10, 17, 7),
        (4, 12, 16, 6),
        (9, 12, 21, 9),
        (7, 14, 21, 7),
    ]
}

/// A leaf list is faithful when every stored span equals its slice.
pub fn leaf_faithful(leaves: &[(&[u8], &[u8])]) -> bool {
    leaves.iter().all(|(stored, slice)| stored == slice)
}

/// Concatenation is faithful exactly when both parts are.
pub fn faithful_append(left: &[(&[u8], &[u8])], right: &[(&[u8], &[u8])]) -> bool {
    let mut both = left.to_vec();
    both.extend_from_slice(right);
    leaf_faithful(&both) == (leaf_faithful(left) && leaf_faithful(right))
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct WorkflowDagReport {
    pub node_count: usize,
    pub earlier_dependency_failures: Vec<(String, String)>,
    pub duplicate_ids: Vec<String>,
    pub non_implemented_empty_source_pilots: Vec<String>,
}

#[derive(Debug, Deserialize)]
struct WorkflowNode {
    id: String,
    status: String,
    depends_on: Vec<String>,
    #[serde(default)]
    source_pilots: Vec<serde_json::Value>,
}

#[derive(Debug, Deserialize)]
struct WorkflowFile {
    nodes: Vec<WorkflowNode>,
}

/// Read a workflow DAG. A dependency is earlier only when its id has already appeared.
pub fn inspect_workflow_dag(text: &str) -> Result<WorkflowDagReport, String> {
    let file: WorkflowFile = serde_json::from_str(text).map_err(|err| err.to_string())?;
    let mut seen = BTreeSet::new();
    let mut earlier_dependency_failures = Vec::new();
    let mut duplicate_ids = Vec::new();
    let mut non_implemented_empty_source_pilots = Vec::new();
    for node in &file.nodes {
        if seen.contains(&node.id) {
            duplicate_ids.push(node.id.clone());
        }
        for dep in &node.depends_on {
            if !seen.contains(dep) {
                earlier_dependency_failures.push((node.id.clone(), dep.clone()));
            }
        }
        seen.insert(node.id.clone());
        if node.status != "implemented" && node.source_pilots.is_empty() {
            non_implemented_empty_source_pilots.push(node.id.clone());
        }
    }
    Ok(WorkflowDagReport {
        node_count: file.nodes.len(),
        earlier_dependency_failures,
        duplicate_ids,
        non_implemented_empty_source_pilots,
    })
}

pub fn inspect_workflow_dag_file(path: &Path) -> Result<WorkflowDagReport, String> {
    let text = fs::read_to_string(path).map_err(|err| err.to_string())?;
    inspect_workflow_dag(&text)
}

fn rat(value: i64) -> Rational {
    Rational::from_integer(BigInt::from(value))
}

#[cfg(test)]
fn graph_of(edges: &[(i64, i64)]) -> (Vec<(BigInt, BigInt)>, Graph) {
    let owned: Vec<(BigInt, BigInt)> = edges
        .iter()
        .map(|(from, to)| (BigInt::from(*from), BigInt::from(*to)))
        .collect();
    let graph = Graph::of(owned.iter().map(|(from, to)| (from, to)));
    (owned, graph)
}

fn along(values: &[Rational], edge: usize, sign: i8) -> Rational {
    let value = values.get(edge).cloned().unwrap_or_else(Rational::zero);
    if sign == 1 {
        value
    } else {
        -value
    }
}

/// The shipped potential agrees with the parent-link recurrence on every vertex.
pub fn potential_follows_forest(graph: &Graph, values: &[Rational]) -> bool {
    let forest = graph.forest();
    let potential = graph.potential(values);
    forest
        .order
        .iter()
        .all(|&vertex| match forest.parent[vertex] {
            None => potential[vertex] == Rational::zero(),
            Some((above, edge, sign)) => {
                potential[vertex] == &potential[above] + along(values, edge, sign)
            }
        })
}

fn crosses(forest: &Forest, vertex: usize, edge: usize) -> bool {
    let mut current = vertex;
    while let Some((above, parent_edge, _)) = forest.parent[current] {
        if parent_edge == edge {
            return true;
        }
        current = above;
    }
    false
}

/// Adding 1 to a stored tree-edge value shifts exactly the vertices whose parent chain uses it.
pub fn tree_edge_shift_matches(graph: &Graph, values: &[Rational], child: usize) -> bool {
    let forest = graph.forest();
    let Some((_, edge, sign)) = forest.parent[child] else {
        return false;
    };
    let before = graph.potential(values);
    let mut bumped = values.to_vec();
    if edge >= bumped.len() {
        bumped.resize(edge + 1, Rational::zero());
    }
    bumped[edge] += rat(1);
    let after = graph.potential(&bumped);
    let step = if sign == 1 { rat(1) } else { -rat(1) };
    (0..graph.names().len()).all(|vertex| {
        let delta = &after[vertex] - &before[vertex];
        let expected = if crosses(&forest, vertex, edge) {
            step.clone()
        } else {
            Rational::zero()
        };
        delta == expected
    })
}

/// Each fundamental cycle meets the chord set in exactly its own chord.
pub fn chord_support_is_identity(graph: &Graph) -> bool {
    let forest = graph.forest();
    let cycles = graph.fundamental_cycles();
    if cycles.len() != forest.chords.len() {
        return false;
    }
    cycles
        .iter()
        .zip(forest.chords.iter())
        .all(|(cycle, &chord)| {
            let hits: Vec<usize> = cycle
                .iter()
                .filter(|(edge, _)| forest.chords.contains(edge))
                .map(|(edge, _)| *edge)
                .collect();
            hits == vec![chord]
                && walk_sum(cycle, &vec![Rational::zero(); graph.edges().len()]) == Rational::zero()
        })
}

/// A coboundary has defect zero. Adding `delta` on one chord leaves that residual and no tree residual.
pub fn chord_error_residual(graph: &Graph, potential: &[Rational], delta: i64) -> Option<Rational> {
    let forest = graph.forest();
    let chord = *forest.chords.first()?;
    let mut values = graph.coboundary(potential);
    if chord >= values.len() {
        return None;
    }
    values[chord] += rat(delta);
    let explained = graph.potential(&values);
    let residual = graph.residual(&values, &explained);
    let tree_clear = residual
        .iter()
        .enumerate()
        .all(|(edge, value)| forest.chords.contains(&edge) || value.is_zero());
    let other_chords_clear = forest
        .chords
        .iter()
        .skip(1)
        .all(|&edge| residual[edge].is_zero());
    if tree_clear && other_chords_clear && residual[chord] == rat(delta) {
        Some(graph.defect(&values))
    } else {
        None
    }
}

#[cfg(test)]
mod tests {
    use num_traits::{Signed, Zero};

    use super::*;

    #[test]
    fn l1_bound_and_one_edge_attainment() {
        for values in [vec![], vec![0], vec![4, -1, -1], vec![-3, 1, 1, 1]] {
            assert!(l1_ge_abs_sum(&values));
        }
        let carrier = one_edge_carrier(-7);
        assert!(l1_ge_abs_sum(&carrier));
        assert_eq!(carrier.iter().map(|v| v.abs()).sum::<i128>(), 7);
    }

    #[test]
    fn admit_split_identity_and_named_arities() {
        let a = BigInt::from(1);
        let b = BigInt::from(4);
        assert_eq!(admit_split(&a, &b, 5), Some(true));
        assert_eq!(admit_split(&b, &a, 1), None);
        for (tree, twice, unstaged, staged) in named_arity_rows() {
            assert_eq!(tree + twice, unstaged);
            assert_eq!(tree.max(twice / 2), staged);
            assert!(staged_max_le(tree, twice / 2));
        }
    }

    #[test]
    fn nonfaithful_leaf_side_stays_nonfaithful() {
        let good = [(b"aa".as_slice(), b"aa".as_slice())];
        let bad = [(b"aa".as_slice(), b"bb".as_slice())];
        assert!(faithful_append(&good, &good));
        assert!(faithful_append(&bad, &good));
        assert!(!leaf_faithful(&bad));
        assert!(!leaf_faithful(&[bad[0], good[0]]));
    }

    #[test]
    fn workflow_dag_earlier_order_and_empty_pilot_counterexamples() {
        let path =
            Path::new(env!("CARGO_MANIFEST_DIR")).join("../../../workflows/dag/workflow_dag.json");
        let report = inspect_workflow_dag_file(&path).expect("workflow dag");
        assert_eq!(report.node_count, 56);
        assert!(report.earlier_dependency_failures.is_empty());
        assert!(report.duplicate_ids.is_empty());
        assert_eq!(report.non_implemented_empty_source_pilots.len(), 32);
        assert_eq!(report.non_implemented_empty_source_pilots[0], "WF24");
    }

    #[test]
    fn path_chord_and_star_use_the_shipped_graph() {
        let (_owned, path) = graph_of(&[(0, 1), (1, 2), (0, 2)]);
        let potentials = vec![rat(0), rat(3), rat(10)];
        let coboundary = path.coboundary(&potentials);
        assert!(path.defect(&coboundary).is_zero());
        assert!(potential_follows_forest(&path, &coboundary));
        assert_eq!(
            chord_error_residual(&path, &potentials, 4),
            Some(rat(4).abs())
        );
        let child = path
            .forest()
            .parent
            .iter()
            .position(|link| link.is_some())
            .expect("path has a child");
        assert!(tree_edge_shift_matches(&path, &coboundary, child));
        assert!(chord_support_is_identity(&path));

        let (_star_owned, star) = graph_of(&[(0, 1), (0, 2), (0, 3), (1, 2), (1, 3)]);
        let star_potential = vec![rat(0), rat(1), rat(2), rat(4)];
        let star_values = star.coboundary(&star_potential);
        assert!(star.defect(&star_values).is_zero());
        assert_eq!(star.forest().chords.len(), 2);
        assert!(potential_follows_forest(&star, &star_values));
        assert!(chord_support_is_identity(&star));
        assert_eq!(
            chord_error_residual(&star, &star_potential, 5),
            Some(rat(5))
        );
        for cycle in star.fundamental_cycles() {
            assert!(walk_sum(&cycle, &star_values).is_zero());
        }
    }
}
