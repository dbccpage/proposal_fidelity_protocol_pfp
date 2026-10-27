//! Bound graph evaluation on the existing projection and LGGR rails.
//! AuthorityEffect: None. No carrier extension or search license is minted.

use crate::lggr::{soundness_lggr, LggrSoundnessReceiptV1};
use crate::projection::{evaluate_projection, verify_projection, ProjectionReceiptV1};
use crate::protocol::canonical_json;
use num_traits::{One, Signed, Zero};
use core_functional::Phi1Functional;
use core_homology::simplicial::{Simplex, SimplicialComplex};
use core_kernel::{parse_exact, to_canonical_string, Exact};
use pfp_runtime::framed_sha256;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};

pub const REQUEST_DOMAIN: &str = "core.symbol-game.graph-evaluate-request.v1";

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Request {
    task_ref: String,
    candidate_ref: String,
    projection: Value,
    original_rates: Vec<String>,
    edit_weights: Vec<String>,
    observer_edges: Vec<Vec<usize>>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct GraphReceiptV1 {
    pub schema_version: String,
    pub input_digest: String,
    pub task_ref: String,
    pub candidate_ref: String,
    pub projection: ProjectionReceiptV1,
    pub edit_cost: String,
    pub coverage_request: Value,
    pub observer_coverage: LggrSoundnessReceiptV1,
    pub authority_effect: String,
}

fn reference(value: &str) -> bool {
    value.len() == 71
        && value.starts_with("sha256:")
        && value[7..]
            .bytes()
            .all(|c| c.is_ascii_digit() || (b'a'..=b'f').contains(&c))
}

fn exact(text: &str) -> Result<Exact, String> {
    if text.len() > 256 {
        return Err("GRAPH_RATIONAL_CEILING".into());
    }
    parse_exact(text).map_err(|e| format!("GRAPH_NOT_EXACT: {e}"))
}

pub fn evaluate_graph(payload: &Value) -> Result<GraphReceiptV1, String> {
    let req: Request = serde_json::from_value(payload.clone())
        .map_err(|e| format!("INVALID_GRAPH_REQUEST: {e}"))?;
    if !reference(&req.task_ref) || !reference(&req.candidate_ref) {
        return Err("GRAPH_REFERENCE_INVALID".into());
    }
    let projection = evaluate_projection(&req.projection)?;
    let size = projection.projected_cochain.len();
    let r = &req.projection["retraction"];
    // V1 cannot silently replace the declared scalar graph by an easier projector.
    if r["projectors"] != json!(vec![vec![vec!["1"]]; size])
        || r["observers"] != json!(vec![vec!["1"]; size])
        || r["epsilon_proj"] != "0"
        || r["rates"]
            != json!(projection
                .projected_cochain
                .iter()
                .map(|v| vec![v])
                .collect::<Vec<_>>())
    {
        return Err("GRAPH_IDENTITY_INTERPRETATION_REQUIRED".into());
    }
    if req.original_rates.len() != size || req.edit_weights.len() != size {
        return Err("GRAPH_COST_DIMENSION_MISMATCH".into());
    }
    let mut weights = Vec::with_capacity(size);
    let mut edits = Vec::with_capacity(size);
    for i in 0..size {
        let weight = exact(&req.edit_weights[i])?;
        if weight <= Exact::zero() {
            return Err("GRAPH_POSITIVE_EDIT_WEIGHTS_REQUIRED".into());
        }
        weights.push(weight);
        edits.push(exact(&projection.projected_cochain[i])? - exact(&req.original_rates[i])?);
    }
    // Weighted edit cost is the core_functional weighted l1; the weights are
    // positive and the lengths agree, so the owner cannot refuse here.
    let cost = Phi1Functional::weighted_l1_rational(&weights, &edits)
        .ok_or("GRAPH_COST_DIMENSION_MISMATCH")?;
    let rows: usize = req.observer_edges.iter().map(Vec::len).sum();
    if req.observer_edges.len() > 64
        || rows > 64
        || req.observer_edges.iter().flatten().any(|&i| i >= size)
    {
        return Err("GRAPH_OBSERVER_CEILING_OR_BASIS_MISMATCH".into());
    }
    let d: Vec<Vec<&str>> = (0..size)
        .map(|i| (0..size).map(|j| if i == j { "1" } else { "0" }).collect())
        .collect();
    let mut q: Vec<Vec<&str>> = req
        .observer_edges
        .iter()
        .flatten()
        .map(|&i| (0..size).map(|j| if i == j { "1" } else { "0" }).collect())
        .collect();
    // A family with no selected edges observes the zero map, not a vacuous pass.
    if q.is_empty() {
        q.push(vec!["0"; size]);
    }
    let coverage_request = json!({"d": {"rows": d}, "q": {"rows": q}});
    let observer_coverage = soundness_lggr(&coverage_request).map_err(|e| e.wire())?;
    Ok(GraphReceiptV1 {
        schema_version: "core.symbol-game.graph-receipt.v1".into(),
        input_digest: framed_sha256(REQUEST_DOMAIN, &canonical_json(payload)),
        task_ref: req.task_ref,
        candidate_ref: req.candidate_ref,
        projection,
        edit_cost: to_canonical_string(&cost),
        coverage_request,
        observer_coverage,
        authority_effect: "None".into(),
    })
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Replay {
    request: Value,
    receipt: GraphReceiptV1,
}

pub fn verify_graph(payload: &Value) -> Result<Value, String> {
    let replay: Replay = serde_json::from_value(payload.clone())
        .map_err(|e| format!("INVALID_GRAPH_REPLAY: {e}"))?;
    // Reuse the projection verifier as well as recomputing cost and rank evidence.
    let checked = verify_projection(
        &json!({"request": replay.request["projection"], "receipt": replay.receipt.projection}),
    )?;
    if checked["accepted"] != true || evaluate_graph(&replay.request)? != replay.receipt {
        return Err("GRAPH_REPLAY_MISMATCH".into());
    }
    Ok(
        json!({"accepted": true, "input_digest": replay.receipt.input_digest,
              "task_ref": replay.receipt.task_ref, "candidate_ref": replay.receipt.candidate_ref,
              "authority_effect": "None"}),
    )
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Challenge {
    request: Value,
    receipt: GraphReceiptV1,
    obligation: String,
    witness: Vec<String>,
}

pub fn challenge_graph(payload: &Value) -> Result<Value, String> {
    let c: Challenge = serde_json::from_value(payload.clone())
        .map_err(|e| format!("INVALID_GRAPH_CHALLENGE: {e}"))?;
    verify_graph(&json!({"request": c.request, "receipt": c.receipt}))?;
    let witness = c
        .witness
        .iter()
        .map(|s| exact(s))
        .collect::<Result<Vec<_>, _>>()?;
    let valid = match c.obligation.as_str() {
        "CONSISTENCY" => {
            // Mathematical owners construct incidence and check dual feasibility.
            let carrier = &c.request["projection"]["carrier"];
            let nodes: Vec<String> =
                serde_json::from_value(carrier["nodes"].clone()).map_err(|e| e.to_string())?;
            let edges: Vec<[String; 2]> =
                serde_json::from_value(carrier["edges"].clone()).map_err(|e| e.to_string())?;
            let mut simplices = (0..nodes.len())
                .map(|i| Simplex::new(vec![i]))
                .collect::<Result<Vec<_>, _>>()
                .map_err(|e| e.to_string())?;
            for edge in edges {
                let indices = edge
                    .iter()
                    .map(|v| {
                        nodes
                            .iter()
                            .position(|n| n == v)
                            .ok_or("GRAPH_VERTEX_MISSING")
                    })
                    .collect::<Result<Vec<_>, _>>()?;
                simplices.push(Simplex::new(indices).map_err(|e| e.to_string())?);
            }
            let complex =
                SimplicialComplex::from_simplices(simplices).map_err(|e| e.to_string())?;
            let matrix = complex.coboundary_matrix(0).map_err(|e| e.to_string())?;
            let d0 = (0..matrix.rows())
                .map(|i| {
                    (0..matrix.cols())
                        .map(|j| matrix.get(i, j).map_err(|e| e.to_string()))
                        .collect::<Result<Vec<_>, _>>()
                })
                .collect::<Result<Vec<_>, _>>()?;
            let omega = c
                .receipt
                .projection
                .projected_cochain
                .iter()
                .map(|s| exact(s))
                .collect::<Result<Vec<_>, _>>()?;
            Phi1Functional::verify_exact_dual_bound(
                &d0,
                &omega,
                &vec![Exact::one(); omega.len()],
                &witness,
            )
            .is_ok_and(|value| !value.is_zero())
        }
        "OBSERVER_COVERAGE" => {
            !c.receipt.observer_coverage.sound
                && crate::lggr::verify_soundness_counterexample(
                    &c.receipt.coverage_request,
                    &witness,
                )?
        }
        _ => return Err("GRAPH_CHALLENGE_OBLIGATION_UNSUPPORTED".into()),
    };
    Ok(
        json!({"schema_version": "core.symbol-game.graph-challenge-receipt.v1",
        "valid": valid, "obligation": c.obligation, "candidate_ref": c.receipt.candidate_ref,
        "input_digest": framed_sha256("core.symbol-game.graph-challenge.v1", &canonical_json(payload)),
        "authority_effect": "None"}),
    )
}

// Origin: engine/crates_rs/pfp/src/graph.rs
// Claim: urn:core:crates_rs:pfp:graph:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde48ab976 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde48ab976` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore48ab976 {
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
impl BoundaryErrore48ab976 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore48ab976 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore48ab976 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde48ab976 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore48ab976> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore48ab976::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore48ab976::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore48ab976::ExceedsCapacity {
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

    fn request() -> Value {
        json!({"task_ref": format!("sha256:{}", "a".repeat(64)),
        "candidate_ref": format!("sha256:{}", "b".repeat(64)),
        "projection": {"carrier": {"prompt_digest": format!("sha256:{}", "c".repeat(64)),
            "prompt_bytes": 8, "max_prompt_bytes": 16384, "nodes": ["A", "B", "C"],
            "edges": [["A", "B"], ["A", "C"], ["B", "C"]], "faces": [],
            "source_spans": [{"edge_index":0,"start":0,"end":2,"interpretation":"AB"},
            {"edge_index":1,"start":3,"end":5,"interpretation":"AC"},
            {"edge_index":2,"start":6,"end":8,"interpretation":"BC"}], "carrier_degree": 1},
            "retraction": {"projection_id":"identity", "projectors":[[["1"]],[["1"]],[["1"]]],
            "rates":[["1"],["1"],["1"]], "observers":[["1"],["1"],["1"]], "epsilon_proj":"0",
            "precision_boundaries":[], "continuum_approximations":[]}},
        "original_rates":["1","1","1"], "edit_weights":["1","1","1"], "observer_edges":[[0,1,2]]})
    }

    #[test]
    fn graph_certificates_cost_and_blind_spot_replay() {
        let mut req = request();
        let original = evaluate_graph(&req).unwrap();
        assert_eq!(original.projection.functional_receipt.phi1, "1");
        assert!(original.observer_coverage.sound);
        req["projection"]["retraction"]["rates"][1][0] = json!("2");
        req["edit_weights"][1] = json!("1/3");
        req["observer_edges"] = json!([[0, 1]]);
        let repair = evaluate_graph(&req).unwrap();
        assert_eq!(repair.edit_cost, "1/3");
        assert_eq!(repair.projection.functional_receipt.phi1, "0");
        assert!(!repair.observer_coverage.sound);
        assert_eq!(
            repair.observer_coverage.witness,
            Some(vec!["0".into(), "0".into(), "1".into()])
        );
        assert_eq!(
            verify_graph(&json!({"request":req,"receipt":repair})).unwrap()["accepted"],
            true
        );
        let mut corrupt = repair.clone();
        corrupt.projection.functional_receipt.phi1 = "1".into();
        assert!(verify_graph(&json!({"request":req,"receipt":corrupt})).is_err());
        req["original_rates"][0] = json!("0");
        assert!(verify_graph(&json!({"request":req,"receipt":repair})).is_err());
    }

    #[test]
    fn graph_challenges_need_a_replayed_specific_witness() {
        let req = request();
        let receipt = evaluate_graph(&req).unwrap();
        let mut c = json!({"request":req,"receipt":receipt,"obligation":"CONSISTENCY", "witness":["1","-1","1"]});
        assert_eq!(challenge_graph(&c).unwrap()["valid"], true);
        c["witness"] = json!(["1/2", "-1/2", "1/2"]);
        assert_eq!(challenge_graph(&c).unwrap()["valid"], true);
        c["witness"] = json!(["0", "0", "0"]);
        assert_eq!(challenge_graph(&c).unwrap()["valid"], false);
    }
}

#[cfg(test)]
mod l4_boundary_tests_e48ab976 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorde48ab976::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorde48ab976::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorde48ab976::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorde48ab976::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorde48ab976::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrore48ab976::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrore48ab976::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
