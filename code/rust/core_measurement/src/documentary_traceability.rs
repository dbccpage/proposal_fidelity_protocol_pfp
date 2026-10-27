//! Finite documentary calibration graphs and exact declared additive bounds.
//!
//! This validates supplied graph data: named documents, nonnegative rational
//! contributions in one declared result unit, rooted connectivity, acyclicity,
//! and termination of every branch at the declared reference. It never verifies
//! the documents, laboratory standards, instruments, signatures, or physical
//! uncertainty claims. An additive total is conditional on the caller's stated
//! error decomposition; graph shape alone is not a metrological certificate.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_2fe2acf0<T> {
    fn checked_invariant_2fe2acf0(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_2fe2acf0<T> for Option<T> {
    #[inline]
    fn checked_invariant_2fe2acf0(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_2fe2acf0<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_2fe2acf0(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::collections::{BTreeMap, BTreeSet, VecDeque};
use std::fmt;

use num_rational::BigRational;
use num_traits::Zero;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DocumentaryCalibrationLink {
    pub source_id: String,
    pub target_id: String,
    pub document_id: String,
    /// Every contribution is already expressed in this declared result unit.
    pub unit: String,
    pub uncertainty_contribution: BigRational,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DocumentaryTraceabilityGraph {
    pub origin_id: String,
    pub terminal_reference_id: String,
    pub terminal_reference_kind: String,
    pub result_unit: String,
    pub links: Vec<DocumentaryCalibrationLink>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DocumentaryTraceabilityError {
    EmptyIdentity { field: &'static str },
    EmptyGraph,
    InvalidContribution { link: usize },
    NegativeContribution { link: usize },
    UnitMismatch { link: usize },
    DuplicateLink { link: usize },
    MissingOrigin,
    MissingTerminal,
    Disconnected,
    Cycle,
    WrongTerminal,
}

impl fmt::Display for DocumentaryTraceabilityError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "documentary traceability graph refusal: {self:?}")
    }
}
impl std::error::Error for DocumentaryTraceabilityError {}

/// Checked structural/documentary graph data only; no physical-authenticity bit.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct DocumentaryTraceabilityReport {
    graph: DocumentaryTraceabilityGraph,
    additive_bound: BigRational,
}

impl DocumentaryTraceabilityReport {
    pub fn graph(&self) -> &DocumentaryTraceabilityGraph {
        &self.graph
    }
    pub fn additive_bound(&self) -> &BigRational {
        &self.additive_bound
    }
}

fn identity(value: &str, field: &'static str) -> Result<(), DocumentaryTraceabilityError> {
    if value.trim().is_empty() {
        return Err(DocumentaryTraceabilityError::EmptyIdentity { field });
    }
    Ok(())
}

fn validate_and_normalize_link(
    index: usize,
    link: &mut DocumentaryCalibrationLink,
    result_unit: &str,
    edges: &mut BTreeSet<(String, String, String)>,
) -> Result<(), DocumentaryTraceabilityError> {
    for (value, field) in [
        (&link.source_id, "source_id"),
        (&link.target_id, "target_id"),
        (&link.document_id, "document_id"),
        (&link.unit, "unit"),
    ] {
        identity(value, field)?;
    }
    if link.unit != result_unit {
        return Err(DocumentaryTraceabilityError::UnitMismatch { link: index });
    }
    if link.uncertainty_contribution.denom().is_zero() {
        return Err(DocumentaryTraceabilityError::InvalidContribution { link: index });
    }
    link.uncertainty_contribution = link.uncertainty_contribution.reduced();
    if link.uncertainty_contribution < BigRational::zero() {
        return Err(DocumentaryTraceabilityError::NegativeContribution { link: index });
    }
    if !edges.insert((
        link.source_id.clone(),
        link.target_id.clone(),
        link.document_id.clone(),
    )) {
        return Err(DocumentaryTraceabilityError::DuplicateLink { link: index });
    }
    Ok(())
}

fn check_reachability(
    origin_id: &str,
    terminal_id: &str,
    nodes: &BTreeSet<String>,
    adjacency: &BTreeMap<String, Vec<String>>,
) -> Result<(), DocumentaryTraceabilityError> {
    if !nodes.contains(origin_id) {
        return Err(DocumentaryTraceabilityError::MissingOrigin);
    }
    if !nodes.contains(terminal_id) {
        return Err(DocumentaryTraceabilityError::MissingTerminal);
    }
    let mut reachable = BTreeSet::new();
    let mut pending = vec![origin_id.to_owned()];
    while let Some(node) = pending.pop() {
        if reachable.insert(node.clone()) {
            pending.extend(adjacency.get(&node).into_iter().flatten().cloned());
        }
    }
    if reachable != *nodes {
        return Err(DocumentaryTraceabilityError::Disconnected);
    }
    Ok(())
}

fn check_acyclic_and_terminal(
    graph: &DocumentaryTraceabilityGraph,
    nodes: &BTreeSet<String>,
    adjacency: &BTreeMap<String, Vec<String>>,
    indegrees: &mut BTreeMap<String, usize>,
) -> Result<(), DocumentaryTraceabilityError> {
    let mut ready: VecDeque<String> = indegrees
        .iter()
        .filter(|(_, degree)| **degree == 0)
        .map(|(node, _)| node.clone())
        .collect();
    let mut removed = 0;
    while let Some(node) = ready.pop_front() {
        removed += 1;
        for target in adjacency.get(&node).into_iter().flatten() {
            let degree = indegrees
                .get_mut(target)
                .checked_invariant_2fe2acf0("each target has an indegree");
            *degree -= 1;
            if *degree == 0 {
                ready.push_back(target.clone());
            }
        }
    }
    if removed != nodes.len() {
        return Err(DocumentaryTraceabilityError::Cycle);
    }
    let unique_sink = nodes
        .iter()
        .all(|node| adjacency.contains_key(node) || node == &graph.terminal_reference_id);
    if graph.origin_id == graph.terminal_reference_id
        || adjacency.contains_key(&graph.terminal_reference_id)
        || !unique_sink
    {
        return Err(DocumentaryTraceabilityError::WrongTerminal);
    }
    Ok(())
}

pub fn validate_documentary_traceability(
    graph: &DocumentaryTraceabilityGraph,
) -> Result<DocumentaryTraceabilityReport, DocumentaryTraceabilityError> {
    for (value, field) in [
        (&graph.origin_id, "origin_id"),
        (&graph.terminal_reference_id, "terminal_reference_id"),
        (&graph.terminal_reference_kind, "terminal_reference_kind"),
        (&graph.result_unit, "result_unit"),
    ] {
        identity(value, field)?;
    }
    if graph.links.is_empty() {
        return Err(DocumentaryTraceabilityError::EmptyGraph);
    }
    let mut normalized = graph.clone();
    let mut nodes = BTreeSet::new();
    let mut edges = BTreeSet::new();
    let mut adjacency: BTreeMap<String, Vec<String>> = BTreeMap::new();
    let mut indegrees: BTreeMap<String, usize> = BTreeMap::new();
    let mut additive_bound = BigRational::zero();
    for (index, link) in normalized.links.iter_mut().enumerate() {
        validate_and_normalize_link(index, link, &graph.result_unit, &mut edges)?;
        nodes.insert(link.source_id.clone());
        nodes.insert(link.target_id.clone());
        adjacency
            .entry(link.source_id.clone())
            .or_default()
            .push(link.target_id.clone());
        indegrees.entry(link.source_id.clone()).or_default();
        *indegrees.entry(link.target_id.clone()).or_default() += 1;
        additive_bound += &link.uncertainty_contribution;
    }
    check_reachability(
        &graph.origin_id,
        &graph.terminal_reference_id,
        &nodes,
        &adjacency,
    )?;
    check_acyclic_and_terminal(graph, &nodes, &adjacency, &mut indegrees)?;
    Ok(DocumentaryTraceabilityReport {
        graph: normalized,
        additive_bound,
    })
}

/// Replay against the caller's independently supplied graph. Self-consistent
/// candidate graph data cannot replace the actual bound problem.
pub fn verify_documentary_traceability(
    actual_graph: &DocumentaryTraceabilityGraph,
    candidate: &DocumentaryTraceabilityReport,
) -> Result<bool, DocumentaryTraceabilityError> {
    Ok(&validate_documentary_traceability(actual_graph)? == candidate)
}

// Origin: engine/crates_rs/core_measurement/src/documentary_traceability.rs
// Claim: urn:core:crates_rs:core-measurement:documentary-traceability:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use num_bigint::BigInt;
    fn q(n: i64, d: i64) -> BigRational {
        BigRational::new(BigInt::from(n), BigInt::from(d))
    }
    fn link(source: &str, target: &str, document: &str) -> DocumentaryCalibrationLink {
        DocumentaryCalibrationLink {
            source_id: source.into(),
            target_id: target.into(),
            document_id: document.into(),
            unit: "V".into(),
            uncertainty_contribution: q(1, 10),
        }
    }
    fn graph() -> DocumentaryTraceabilityGraph {
        DocumentaryTraceabilityGraph {
            origin_id: "calibration".into(),
            terminal_reference_id: "reference".into(),
            terminal_reference_kind: "declared-laboratory-standard".into(),
            result_unit: "V".into(),
            links: vec![
                link("calibration", "transfer", "doc-a"),
                link("transfer", "reference", "doc-b"),
            ],
        }
    }
    #[test]
    fn connected_hierarchy_and_diamond_bind_documents_and_exact_total() {
        let mut actual = graph();
        let report = validate_documentary_traceability(&actual).unwrap();
        assert_eq!(report.additive_bound(), &q(1, 5));
        assert!(verify_documentary_traceability(&actual, &report).unwrap());
        actual.links[0].document_id = "different-document".into();
        assert!(!verify_documentary_traceability(&actual, &report).unwrap());
        actual.links.push(link("calibration", "parallel", "doc-c"));
        actual.links.push(link("parallel", "reference", "doc-d"));
        assert_eq!(
            validate_documentary_traceability(&actual)
                .unwrap()
                .additive_bound(),
            &q(2, 5)
        );
    }
    #[test]
    fn broken_cyclic_or_unit_confused_graphs_are_refused() {
        let mut actual = graph();
        actual.links[1].source_id = "unconnected".into();
        assert_eq!(
            validate_documentary_traceability(&actual),
            Err(DocumentaryTraceabilityError::Disconnected)
        );
        let mut actual = graph();
        actual.links.push(link("transfer", "calibration", "cycle"));
        assert_eq!(
            validate_documentary_traceability(&actual),
            Err(DocumentaryTraceabilityError::Cycle)
        );
        let mut actual = graph();
        actual
            .links
            .push(link("calibration", "orphan-leaf", "leaf"));
        assert_eq!(
            validate_documentary_traceability(&actual),
            Err(DocumentaryTraceabilityError::WrongTerminal)
        );
        let mut actual = graph();
        actual.links[0].unit = "m".into();
        assert_eq!(
            validate_documentary_traceability(&actual),
            Err(DocumentaryTraceabilityError::UnitMismatch { link: 0 })
        );
    }
    #[test]
    fn missing_documents_negative_invalid_or_duplicate_contributions_are_refused() {
        let mut actual = graph();
        actual.links[0].document_id.clear();
        assert!(matches!(
            validate_documentary_traceability(&actual),
            Err(DocumentaryTraceabilityError::EmptyIdentity { .. })
        ));
        let mut actual = graph();
        actual.links[0].uncertainty_contribution = q(-1, 1);
        assert_eq!(
            validate_documentary_traceability(&actual),
            Err(DocumentaryTraceabilityError::NegativeContribution { link: 0 })
        );
        let mut actual = graph();
        actual.links[0].uncertainty_contribution =
            BigRational::new_raw(BigInt::from(1), BigInt::from(0));
        assert_eq!(
            validate_documentary_traceability(&actual),
            Err(DocumentaryTraceabilityError::InvalidContribution { link: 0 })
        );
        let mut actual = graph();
        actual.links.push(actual.links[0].clone());
        assert_eq!(
            validate_documentary_traceability(&actual),
            Err(DocumentaryTraceabilityError::DuplicateLink { link: 2 })
        );
    }
}
