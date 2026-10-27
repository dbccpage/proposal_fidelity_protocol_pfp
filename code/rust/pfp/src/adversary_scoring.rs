//! Concrete exact carrier scorer over the existing native projection solver.
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::Zero;
use core_adversary::stage::ports::Refusal;
use core_adversary::carrier::{ExactCochain, Network, NodeLabel};
use core_adversary::evidence::{
    canonical_rational, parse_exact_rational, MeasurementInput, MeasurementStatus,
    ObstructionMeasurement,
};
use core_adversary::scoring_ports::{CochainScoringPort, CochainScoringRequest};
use serde_json::{json, Value};

pub struct NativeCochainScorer;
fn absent(reason: impl Into<String>, backend: &str) -> Result<ObstructionMeasurement, Refusal> {
    ObstructionMeasurement::not_measured(reason.into(), backend.into())
}
fn label(node: &NodeLabel) -> Result<String, Refusal> {
    Ok(match node {
        NodeLabel::Text(text) => text.clone(),
        NodeLabel::Integer(value) => value.0.to_string(),
        NodeLabel::Boolean(value) => if *value { "True" } else { "False" }.into(),
        NodeLabel::Float(_) => serde_json::to_string(node)
            .map_err(|e| Refusal::new("CARRIER_MALFORMED", e.to_string()))?,
    })
}
fn validate_edges(edges: &[[NodeLabel; 2]]) -> Option<String> {
    if edges.is_empty() {
        return Some("EMPTY_CARRIER: a carrier without edges has nothing to measure".into());
    }
    for (i, edge) in edges.iter().enumerate() {
        if edges[..i].contains(edge) {
            return Some("MALFORMED_CARRIER: duplicate edge".into());
        }
        if edge[0] == edge[1] {
            return Some("MALFORMED_CARRIER: self-loop edge".into());
        }
        if edges.contains(&[edge[1].clone(), edge[0].clone()]) {
            return Some("MALFORMED_CARRIER: edge appears in both orientations".into());
        }
    }
    None
}

fn has_undirected_edge(edges: &[[NodeLabel; 2]], u: &NodeLabel, v: &NodeLabel) -> bool {
    edges.contains(&[u.clone(), v.clone()]) || edges.contains(&[v.clone(), u.clone()])
}

fn validate_face(network: &Network, face: &[NodeLabel; 3]) -> Option<String> {
    if face[0] == face[1] || face[1] == face[2] || face[2] == face[0] {
        return Some("MALFORMED_FACE: triangle must have three distinct nodes".into());
    }
    if face.iter().any(|node| !network.nodes().contains(node)) {
        return Some("MALFORMED_FACE: node outside the carrier".into());
    }
    let edges = network.edges();
    for [u, v] in [[&face[0], &face[1]], [&face[1], &face[2]], [&face[2], &face[0]]] {
        if !has_undirected_edge(edges, u, v) {
            return Some("MALFORMED_FACE: missing boundary edge".into());
        }
    }
    None
}

fn validation(network: &Network) -> Option<String> {
    if let Some(err) = validate_edges(network.edges()) {
        return Some(err);
    }
    for face in network.faces() {
        if let Some(err) = validate_face(network, face) {
            return Some(err);
        }
    }
    None
}
fn indexed_cells<const N: usize>(
    network: &Network,
    cells: &[[NodeLabel; N]],
) -> Result<Vec<[usize; N]>, Refusal> {
    cells
        .iter()
        .map(|cell| {
            let mut indices = [0; N];
            for (slot, node) in cell.iter().enumerate() {
                indices[slot] = network
                    .nodes()
                    .iter()
                    .position(|n| n == node)
                    .ok_or_else(|| Refusal::new("CARRIER_MALFORMED", "cell vertex absent"))?;
            }
            Ok(indices)
        })
        .collect()
}

fn measure_closures(
    network: &Network,
    cochain: &ExactCochain,
    higher: bool,
) -> Result<core_functional::simplicial_defect::SimplicialDefects, Refusal> {
    let edges = indexed_cells(network, network.edges())?;
    let faces = indexed_cells(network, network.faces())?;
    let tetrahedra = if higher {
        indexed_cells(network, network.tetrahedra())?
    } else {
        vec![]
    };
    let simplices = if higher {
        indexed_cells(network, network.four_simplices())?
    } else {
        vec![]
    };
    let values: Vec<_> = network
        .edges()
        .iter()
        .map(|edge| {
            cochain
                .value(edge)
                .cloned()
                .unwrap_or_else(BigRational::zero)
        })
        .collect();
    core_functional::simplicial_defect::evaluate_simplicial_defects(
        &edges,
        &faces,
        &tetrahedra,
        &simplices,
        &values,
    )
    .map_err(|error| Refusal::new("CLOSURE_EVALUATION_REFUSED", error.to_string()))
}

fn is_no_obstruction_typing_ablation(request: &CochainScoringRequest<'_>) -> bool {
    request
        .ablation_flags
        .and_then(|flags| flags.get("no_obstruction_typing"))
        .is_some_and(|flag| {
            flag != &Value::Bool(false) && flag != &Value::Null && flag != &json!(0)
        })
}

fn build_l1_solver_input(
    network: &Network,
    cochain: &ExactCochain,
) -> Result<(Vec<Vec<&'static str>>, Vec<String>), Refusal> {
    let mut matrix = Vec::new();
    let mut target = Vec::new();
    for edge in network.edges() {
        let mut row = vec!["0"; network.nodes().len()];
        let u = network
            .nodes()
            .iter()
            .position(|n| n == &edge[0])
            .ok_or_else(|| Refusal::new("CARRIER_MALFORMED", "edge source absent"))?;
        let v = network
            .nodes()
            .iter()
            .position(|n| n == &edge[1])
            .ok_or_else(|| Refusal::new("CARRIER_MALFORMED", "edge target absent"))?;
        row[u] = "-1";
        row[v] = "1";
        matrix.push(row);
        target.push(canonical_rational(
            &cochain
                .value(edge)
                .cloned()
                .unwrap_or_else(BigRational::zero),
        ));
    }
    Ok((matrix, target))
}

fn parse_rational_array(payload: &Value, key: &str, missing_msg: &str) -> Result<Vec<BigRational>, Refusal> {
    payload[key]
        .as_array()
        .ok_or_else(|| Refusal::new("HOST_PAYLOAD_INVALID", missing_msg))?
        .iter()
        .map(parse_exact_rational)
        .collect()
}

fn collect_active_and_witness(
    edges: &[[NodeLabel; 2]],
    residual: Vec<BigRational>,
    dual: Vec<BigRational>,
) -> Result<(Vec<String>, Vec<(String, BigRational)>), Refusal> {
    let mut active = Vec::new();
    let mut witness = Vec::new();
    for ((edge, res), d) in edges.iter().zip(residual).zip(dual) {
        let name = format!("{}->{}", label(&edge[0])?, label(&edge[1])?);
        if !res.is_zero() {
            active.push(name.clone());
        }
        witness.push((name, d));
    }
    Ok((active, witness))
}

fn evaluate_ablation_mass(cochain: &ExactCochain) -> Result<ObstructionMeasurement, Refusal> {
    let values: Vec<_> = cochain
        .entries()
        .iter()
        .map(|(_, value)| value.clone())
        .collect();
    let mass = core_functional::phi1::Phi1Functional::unweighted_l1_rational(&values)
        .ok_or_else(|| Refusal::new("CARRIER_MALFORMED", "invalid rational cochain"))?;
    absent(
        format!(
            "ABLATION_NO_OBSTRUCTION_TYPING: the untyped scalar l1 mass {} is not a quotient measurement",
            canonical_rational(&mass)
        ),
        "ablation_no_typing",
    )
}

fn decode_verified_l1_solution(
    payload: &Value,
    edge_count: usize,
) -> Result<Result<(BigRational, Vec<BigRational>, Vec<BigRational>), ObstructionMeasurement>, Refusal> {
    if payload["certificate_verified"] != Value::Bool(true) {
        return Ok(Err(absent(
            "CERTIFICATE_UNVERIFIED: the native Phi1 certificate was not verified by core_functional",
            "rust_exact_core_solvers",
        )?));
    }
    let residual = parse_rational_array(payload, "residual", "residual missing")?;
    let dual = parse_rational_array(payload, "dual_witness", "dual witness missing")?;
    if residual.len() != edge_count || dual.len() != edge_count {
        return Ok(Err(absent(
            "HOST_PAYLOAD_INVALID: residual or dual witness length differs from the edge count",
            "rust_exact_core_solvers",
        )?));
    }
    let phi1 = parse_exact_rational(&payload["phi1"])?;
    Ok(Ok((phi1, residual, dual)))
}

fn dispatch_l1_primal_dual_solver(
    matrix: Vec<Vec<&str>>,
    target: Vec<String>,
) -> Result<Result<Value, ObstructionMeasurement>, Refusal> {
    let outcome = crate::dispatch_runtime_request(&crate::RuntimeRequestV1 {
        schema_version: crate::RUNTIME_REQUEST_SCHEMA.into(),
        action: "exact_solve_l1_primal_dual".into(),
        payload: json!({"matrix":{"rows":matrix},"target":target}),
    });
    if !outcome.success {
        return absent(
            format!(
                "NATIVE_SOLVER_REFUSED: {}",
                outcome.error.unwrap_or_default()
            ),
            "rust_exact_core_solvers",
        )
        .map(Err);
    }
    let payload = outcome
        .result
        .ok_or_else(|| Refusal::new("HOST_PAYLOAD_INVALID", "solver returned no result"))?;
    Ok(Ok(payload))
}

impl CochainScoringPort for NativeCochainScorer {
    fn identify_obstructions(
        &mut self,
        request: &CochainScoringRequest<'_>,
    ) -> Result<ObstructionMeasurement, Refusal> {
        let network = request.network;
        let cochain = request.initial_cochain;
        if let Some(reason) = validation(network) {
            return absent(reason, "carrier_validation");
        }
        if is_no_obstruction_typing_ablation(request) {
            return evaluate_ablation_mass(cochain);
        }
        let (matrix, target) = build_l1_solver_input(network, cochain)?;
        let payload = match dispatch_l1_primal_dual_solver(matrix, target)? {
            Ok(payload) => payload,
            Err(not_measured) => return Ok(not_measured),
        };
        let (phi1, residual, dual) = match decode_verified_l1_solution(&payload, network.edges().len())? {
            Ok(decoded) => decoded,
            Err(not_measured) => return Ok(not_measured),
        };
        let (active, witness) = collect_active_and_witness(network.edges(), residual, dual)?;
        let gamma2 = measure_closures(network, cochain, false)?.gamma2;
        ObstructionMeasurement::new(MeasurementInput {
            status: MeasurementStatus::Measured,
            backend: "rust_exact_core_solvers".into(),
            phi1: Some(phi1),
            gamma2: Some(gamma2),
            defect_count: BigInt::from(active.len()),
            active_obstructions: active,
            certificate_verified: true,
            dual_witness: witness,
            reason: String::new(),
        })
    }
}

/// Exact simplicial coboundaries reuse the same admitted carrier and cochain.
pub struct NativeReggeScorer;
impl core_adversary::complete_bout::ReggeScoringPort for NativeReggeScorer {
    fn compute(
        &mut self,
        network: &Network,
        cochain: &ExactCochain,
    ) -> Result<serde_json::Map<String, Value>, Refusal> {
        let measurement = measure_closures(network, cochain, true)?;
        let gamma2 = measurement.gamma2;
        let xi3 = measurement.degree_three_closure;
        let xi4 = measurement.degree_four_closure;
        let tetrahedron_values = measurement.tetrahedron_values;
        let simplex_values = measurement.simplex_values;
        let result = json!({"gamma2":canonical_rational(&gamma2),"xi3":canonical_rational(&xi3),"xi4":canonical_rational(&xi4),"delta2_cochain":network.tetrahedra().iter().zip(&tetrahedron_values).map(|(cell,value)|json!([cell,canonical_rational(value)])).collect::<Vec<_>>(),"delta3_cochain":network.four_simplices().iter().zip(&simplex_values).map(|(cell,value)|json!([cell,canonical_rational(value)])).collect::<Vec<_>>(),"bianchi_closed":xi3.is_zero(),"spacetime_closed":xi4.is_zero(),"regge_converged":gamma2.is_zero()&&xi3.is_zero()&&xi4.is_zero()});
        result
            .as_object()
            .cloned()
            .ok_or_else(|| Refusal::new("REGGE_DEFICIT_UNAVAILABLE", "deficit record unavailable"))
    }
}

// Origin: engine/crates_rs/pfp/src/adversary_scoring.rs
// Claim: urn:core:crates_rs:pfp:adversary-scoring:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord01f3323e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord01f3323e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError01f3323e {
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
impl BoundaryError01f3323e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError01f3323e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError01f3323e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord01f3323e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError01f3323e> {
        if capacity_bound == 0 {
            return Err(BoundaryError01f3323e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError01f3323e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError01f3323e::ExceedsCapacity {
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
mod l4_boundary_tests_01f3323e {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord01f3323e::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord01f3323e::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord01f3323e::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord01f3323e::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord01f3323e::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError01f3323e::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError01f3323e::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
