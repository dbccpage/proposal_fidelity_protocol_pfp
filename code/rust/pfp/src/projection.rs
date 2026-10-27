//! Prompt-bound declared finite carrier projection. No semantic inference.
//! AuthorityEffect: None.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_b2a68b6a<T> {
    fn checked_invariant_b2a68b6a(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_b2a68b6a<T> for Option<T> {
    #[inline]
    fn checked_invariant_b2a68b6a(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_b2a68b6a<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_b2a68b6a(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::functional::{evaluate_functional, FunctionalReceiptV1};
use crate::protocol::canonical_json;
use core_functional::normal_projection::measure_normal_projection;
use core_homology::simplicial::{Simplex, SimplicialComplex};
use core_kernel::{parse_exact, to_canonical_string, Exact};
use pfp_runtime::framed_sha256;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::BTreeSet;

pub const PROJECTION_REQUEST_DOMAIN: &str = "core.symbol-game.projection-evaluate-request.v1";
pub const PROJECTION_RECEIPT_SCHEMA: &str = "core.symbol-game.projection-receipt.v1";

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct ProjectionRequest {
    carrier: Carrier,
    retraction: Retraction,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct Carrier {
    prompt_digest: String,
    prompt_bytes: usize,
    max_prompt_bytes: usize,
    nodes: Vec<String>,
    edges: Vec<[String; 2]>,
    faces: Vec<[String; 3]>,
    source_spans: Vec<SourceSpan>,
    carrier_degree: usize,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct SourceSpan {
    edge_index: usize,
    start: usize,
    end: usize,
    interpretation: String,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct Retraction {
    projection_id: String,
    projectors: Vec<Vec<Vec<String>>>,
    rates: Vec<Vec<String>>,
    observers: Vec<Vec<String>>,
    epsilon_proj: String,
    precision_boundaries: Vec<String>,
    continuum_approximations: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct NormalResidualWire {
    pub edge_index: usize,
    pub vector: Vec<String>,
    pub l1_norm: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ProjectionReceiptV1 {
    pub schema_version: String,
    pub input_digest: String,
    pub projected_cochain: Vec<String>,
    pub normal_residuals: Vec<NormalResidualWire>,
    pub functional_receipt: FunctionalReceiptV1,
    pub authority_effect: String,
}

pub fn projection_input_digest(payload: &Value) -> String {
    framed_sha256(PROJECTION_REQUEST_DOMAIN, &canonical_json(payload))
}

fn parse_vector(values: &[String]) -> Result<Vec<Exact>, String> {
    values
        .iter()
        .map(|text| parse_exact(text).map_err(|e| format!("PROJECTION_NOT_EXACT: {e}")))
        .collect()
}

fn validate_carrier_bounds(c: &Carrier) -> Result<(), String> {
    let topology_invalid = c.carrier_degree != 1
        || !(2..=32).contains(&c.nodes.len())
        || c.edges.is_empty()
        || c.edges.len() > 64
        || c.faces.len() > 64;
    let prompt_invalid =
        c.prompt_bytes == 0 || c.prompt_bytes > c.max_prompt_bytes || c.max_prompt_bytes > 1048576;
    if topology_invalid || prompt_invalid {
        return Err("PROJECTION_BOUNDS_REFUSED".into());
    }
    Ok(())
}

fn validate_prompt_digest(digest: &str) -> Result<(), String> {
    let valid_hex = digest
        .strip_prefix("sha256:")
        .is_some_and(|hex| hex.len() == 64 && hex.bytes().all(|ch| matches!(ch, b'0'..=b'9' | b'a'..=b'f')));
    if !valid_hex {
        return Err("PROJECTION_PROMPT_DIGEST_INVALID".into());
    }
    Ok(())
}

fn validate_declarations(c: &Carrier, r: &Retraction) -> Result<(), String> {
    let nodes_invalid = c.nodes.iter().any(|node| node.is_empty())
        || c.nodes.iter().collect::<BTreeSet<_>>().len() != c.nodes.len();
    let retraction_invalid = r.projection_id.trim().is_empty()
        || r.precision_boundaries
            .iter()
            .chain(&r.continuum_approximations)
            .any(|s| s.trim().is_empty());
    if nodes_invalid || retraction_invalid {
        return Err("PROJECTION_DECLARATION_INVALID".into());
    }
    Ok(())
}

fn lookup_node_index(nodes: &[String], node: &str) -> Result<usize, String> {
    nodes
        .iter()
        .position(|n| n == node)
        .ok_or_else(|| "PROJECTION_UNKNOWN_VERTEX".to_string())
}

fn validate_canonical_basis(basis: &[Vec<usize>]) -> Result<(), String> {
    let noncanonical_order = basis.windows(2).any(|pair| pair[0] >= pair[1]);
    let noncanonical_simplex = basis
        .iter()
        .any(|simplex| simplex.windows(2).any(|pair| pair[0] >= pair[1]));
    if noncanonical_order || noncanonical_simplex {
        return Err("PROJECTION_NONCANONICAL_CARRIER".into());
    }
    Ok(())
}

fn resolve_carrier_simplices(c: &Carrier) -> Result<(Vec<Vec<usize>>, Vec<Vec<usize>>), String> {
    let edges: Vec<Vec<usize>> = c
        .edges
        .iter()
        .map(|e| Ok(vec![lookup_node_index(&c.nodes, &e[0])?, lookup_node_index(&c.nodes, &e[1])?]))
        .collect::<Result<_, String>>()?;
    let faces: Vec<Vec<usize>> = c
        .faces
        .iter()
        .map(|f| {
            Ok(vec![
                lookup_node_index(&c.nodes, &f[0])?,
                lookup_node_index(&c.nodes, &f[1])?,
                lookup_node_index(&c.nodes, &f[2])?,
            ])
        })
        .collect::<Result<_, String>>()?;
    validate_canonical_basis(&edges)?;
    validate_canonical_basis(&faces)?;
    Ok((edges, faces))
}

fn is_valid_span(span: &SourceSpan, edge_count: usize, previous: usize, prompt_bytes: usize) -> bool {
    span.edge_index < edge_count
        && span.start >= previous
        && span.end > span.start
        && span.end <= prompt_bytes
        && !span.interpretation.trim().is_empty()
}

fn validate_source_spans(c: &Carrier, edge_count: usize, r: &Retraction) -> Result<(), String> {
    let mut previous = 0;
    let mut covered = BTreeSet::new();
    for span in &c.source_spans {
        if !is_valid_span(span, edge_count, previous, c.prompt_bytes) {
            return Err("PROJECTION_SOURCE_SPAN_INVALID".into());
        }
        previous = span.end;
        covered.insert(span.edge_index);
    }
    if [covered.len(), r.rates.len(), r.projectors.len(), r.observers.len()]
        .into_iter()
        .any(|len| len != edge_count)
    {
        return Err("PROJECTION_EDGE_COVERAGE_MISMATCH".into());
    }
    Ok(())
}

fn validate_epsilon(epsilon_proj: &str) -> Result<(), String> {
    let epsilon = parse_exact(epsilon_proj).map_err(|e| format!("PROJECTION_NOT_EXACT: {e}"))?;
    if epsilon < Exact::from_integer(0.into()) {
        return Err("PROJECTION_NEGATIVE_TOLERANCE".into());
    }
    Ok(())
}

fn build_simplicial_complex(
    node_count: usize,
    edges: &[Vec<usize>],
    faces: &[Vec<usize>],
) -> Result<SimplicialComplex, String> {
    let mut simplices: Vec<_> = (0..node_count)
        .map(|v| Simplex::new(vec![v]).checked_invariant_b2a68b6a("a singleton is canonical"))
        .collect();
    for vertices in edges.iter().chain(faces) {
        simplices.push(
            Simplex::new(vertices.clone())
                .map_err(|e| format!("PROJECTION_INVALID_SIMPLEX: {e}"))?,
        );
    }
    let complex = SimplicialComplex::from_simplices(simplices)
        .map_err(|e| format!("PROJECTION_COMPLEX_REFUSED: {e}"))?;
    if complex.count(1) != edges.len() || complex.count(2) != faces.len() {
        return Err("MISSING_FACE_BOUNDARY: automatic carrier expansion is forbidden".into());
    }
    Ok(complex)
}

fn measure_single_edge(
    e: usize,
    r: &Retraction,
) -> Result<(String, NormalResidualWire), String> {
    let rate = parse_vector(&r.rates[e])?;
    if rate.is_empty() || rate.len() > 16 {
        return Err("PROJECTION_RATE_BOUND_EXCEEDED".into());
    }
    let p = r.projectors[e]
        .iter()
        .map(|row| parse_vector(row))
        .collect::<Result<Vec<_>, _>>()?;
    let observer = parse_vector(&r.observers[e])?;
    let measured = measure_normal_projection(&p, &rate, &observer).map_err(|e| e.to_string())?;
    let retained = to_canonical_string(&measured.retained_observation);
    let wire = NormalResidualWire {
        edge_index: e,
        vector: measured
            .normal_residual
            .iter()
            .map(to_canonical_string)
            .collect(),
        l1_norm: to_canonical_string(&measured.normal_l1),
    };
    Ok((retained, wire))
}

fn measure_edge_projections(
    edge_count: usize,
    r: &Retraction,
) -> Result<(Vec<String>, Vec<NormalResidualWire>), String> {
    let mut projected_cochain = Vec::with_capacity(edge_count);
    let mut normal_residuals = Vec::with_capacity(edge_count);
    for e in 0..edge_count {
        let (retained, residual) = measure_single_edge(e, r)?;
        projected_cochain.push(retained);
        normal_residuals.push(residual);
    }
    Ok((projected_cochain, normal_residuals))
}

fn wire_coboundary_matrix(complex: &SimplicialComplex, degree: usize) -> Result<Value, String> {
    let matrix = complex
        .coboundary_matrix(degree)
        .map_err(|e| format!("PROJECTION_BOUNDARY_REFUSED: {e}"))?;
    let rows: Vec<Vec<String>> = (0..matrix.rows())
        .map(|i| {
            (0..matrix.cols())
                .map(|j| {
                    matrix
                        .get(i, j)
                        .map(|value| to_canonical_string(&value))
                        .map_err(|e| e.to_string())
                })
                .collect()
        })
        .collect::<Result<_, _>>()?;
    Ok(json!({"rows": rows}))
}

/// Caller-declared simplices must already be closed; closure adds no new edge.
pub fn evaluate_projection(payload: &Value) -> Result<ProjectionReceiptV1, String> {
    let request: ProjectionRequest = serde_json::from_value(payload.clone())
        .map_err(|e| format!("INVALID_PROJECTION_REQUEST: {e}"))?;
    let c = request.carrier;
    let r = request.retraction;
    validate_carrier_bounds(&c)?;
    validate_prompt_digest(&c.prompt_digest)?;
    validate_declarations(&c, &r)?;
    let (edges, faces) = resolve_carrier_simplices(&c)?;
    validate_source_spans(&c, edges.len(), &r)?;
    validate_epsilon(&r.epsilon_proj)?;
    let complex = build_simplicial_complex(c.nodes.len(), &edges, &faces)?;
    let (projected_cochain, normal_residuals) = measure_edge_projections(edges.len(), &r)?;
    let d0 = wire_coboundary_matrix(&complex, 0)?;
    let d1 = wire_coboundary_matrix(&complex, 1)?;
    let functional_payload = json!({"d0": d0, "d1": d1, "residual": projected_cochain});
    let functional_receipt = evaluate_functional(&functional_payload).map_err(|e| e.wire())?;
    Ok(ProjectionReceiptV1 {
        schema_version: PROJECTION_RECEIPT_SCHEMA.into(),
        input_digest: projection_input_digest(payload),
        projected_cochain,
        normal_residuals,
        functional_receipt,
        authority_effect: "None".into(),
    })
}

pub fn verify_projection(payload: &Value) -> Result<Value, String> {
    #[derive(Deserialize)]
    #[serde(deny_unknown_fields)]
    struct Verify {
        request: Value,
        receipt: ProjectionReceiptV1,
    }
    let verify: Verify = serde_json::from_value(payload.clone())
        .map_err(|e| format!("INVALID_PROJECTION_REQUEST: {e}"))?;
    let recomputed = evaluate_projection(&verify.request)?;
    Ok(
        json!({"accepted": recomputed == verify.receipt, "input_digest": recomputed.input_digest, "authority_effect": "None"}),
    )
}

// Origin: engine/crates_rs/pfp/src/projection.rs
// Claim: urn:core:crates_rs:pfp:projection:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb2a68b6a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb2a68b6a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb2a68b6a {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryErrorb2a68b6a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb2a68b6a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb2a68b6a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb2a68b6a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb2a68b6a> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb2a68b6a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb2a68b6a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb2a68b6a::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn fixture() -> Value {
        json!({
            "carrier": {"prompt_digest": format!("sha256:{}", "a".repeat(64)), "prompt_bytes": 8, "max_prompt_bytes": 32,
                "nodes": ["a", "b", "c"], "edges": [["a", "b"], ["a", "c"], ["b", "c"]], "faces": [["a", "b", "c"]],
                "source_spans": [{"edge_index": 0, "start": 0, "end": 2, "interpretation": "ab"}, {"edge_index": 2, "start": 3, "end": 5, "interpretation": "bc"}, {"edge_index": 1, "start": 6, "end": 8, "interpretation": "ac"}], "carrier_degree": 1},
            "retraction": {"projection_id": "declared-exact-rate-v1", "projectors": [[["1", "0"], ["0", "0"]], [["1", "0"], ["0", "0"]], [["1", "0"], ["0", "0"]]],
                "rates": [["1", "1/2"], ["0", "1/2"], ["1", "1/2"]], "observers": [["1", "0"], ["1", "0"], ["1", "0"]],
                "epsilon_proj": "1/2", "precision_boundaries": [], "continuum_approximations": []}
        })
    }

    #[test]
    fn measures_exact_triangle_with_separate_projection_loss() {
        let receipt = evaluate_projection(&fixture()).unwrap();
        assert_eq!(receipt.projected_cochain, ["1", "0", "1"]);
        assert_eq!(receipt.functional_receipt.phi1, "2");
        assert_eq!(receipt.functional_receipt.gamma2, "2");
        assert!(receipt
            .normal_residuals
            .iter()
            .all(|r| r.vector == ["0", "1/2"] && r.l1_norm == "1/2"));
        assert_eq!(receipt.functional_receipt.second_stage_repairs, "none");
    }

    #[test]
    fn rejects_unlicensed_implicit_face_edges_and_false_projectors() {
        let mut payload = fixture();
        payload["carrier"]["edges"]
            .as_array_mut()
            .unwrap()
            .remove(1);
        payload["carrier"]["source_spans"] = json!([{"edge_index": 0, "start": 0, "end": 2, "interpretation": "ab"}, {"edge_index": 1, "start": 3, "end": 5, "interpretation": "bc"}]);
        for field in ["projectors", "rates", "observers"] {
            payload["retraction"][field]
                .as_array_mut()
                .unwrap()
                .remove(1);
        }
        assert!(evaluate_projection(&payload)
            .unwrap_err()
            .starts_with("MISSING_FACE_BOUNDARY"));
        let mut payload = fixture();
        payload["retraction"]["projectors"][0][0][0] = json!("2");
        assert_eq!(
            evaluate_projection(&payload).unwrap_err(),
            "PROJECTOR_NOT_IDEMPOTENT"
        );
    }

    #[test]
    fn native_receipt_replay_binds_source_spans_rates_and_norms() {
        let request = fixture();
        let receipt = evaluate_projection(&request).unwrap();
        assert_eq!(
            verify_projection(&json!({"request": request, "receipt": receipt})).unwrap()
                ["accepted"],
            true
        );
        let mut mutated = fixture();
        mutated["carrier"]["source_spans"][0]["interpretation"] = json!("another declared meaning");
        assert_eq!(
            verify_projection(&json!({"request": mutated, "receipt": receipt})).unwrap()
                ["accepted"],
            false
        );
        let mut forged = receipt;
        forged.normal_residuals[0].l1_norm = "0".into();
        assert_eq!(
            verify_projection(&json!({"request": fixture(), "receipt": forged})).unwrap()
                ["accepted"],
            false
        );
    }

    #[test]
    fn rejects_float_bool_and_malformed_source_data_at_native_boundary() {
        for value in [json!(0.5), json!(true), json!("0.5"), json!("1/1")] {
            let mut payload = fixture();
            payload["retraction"]["rates"][0][0] = value;
            assert!(evaluate_projection(&payload).is_err());
        }
        let mut payload = fixture();
        payload["carrier"]["source_spans"][0]["start"] = json!(true);
        assert!(evaluate_projection(&payload).is_err());
    }
}

#[cfg(test)]
mod l4_boundary_tests_b2a68b6a {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordb2a68b6a::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordb2a68b6a::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordb2a68b6a::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordb2a68b6a::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordb2a68b6a::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorb2a68b6a::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorb2a68b6a::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
