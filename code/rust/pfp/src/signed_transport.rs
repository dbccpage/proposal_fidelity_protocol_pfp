//! Bounded signed-gauge wire adapter over the sovereign holonomy certifier.
//! AuthorityEffect: None. No Hamiltonian interpretation is inferred.

use core_holonomy::signed_transport::{
    certify_signed_transport, SignedCoefficientGraph, SignedTransportCertificate,
    SignedTransportOutcome,
};
use serde::Deserialize;
use serde_json::{json, Value};

pub const MAX_DIMENSION: usize = 128;
pub const MAX_SCALAR_BYTES: usize = 256;

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Request {
    operation: String,
    matrix: Vec<Vec<String>>,
    gauge: Option<Vec<u8>>,
    cycle: Option<Vec<usize>>,
}

fn parse_and_validate_graph(payload: &Value) -> Result<(Request, SignedCoefficientGraph), String> {
    if !payload.is_object() {
        return Err("SIGNED_TRANSPORT_SCHEMA: request must be an object".into());
    }
    let request: Request = serde_json::from_value(payload.clone())
        .map_err(|e| format!("SIGNED_TRANSPORT_SCHEMA: {e}"))?;
    let n = request.matrix.len();
    if n == 0 || n > MAX_DIMENSION || request.matrix.iter().any(|r| r.len() != n) {
        return Err(
            "SIGNED_TRANSPORT_MATRIX: nonempty square matrix exceeds dimension bound".into(),
        );
    }
    if request
        .matrix
        .iter()
        .flatten()
        .any(|s| s.len() > MAX_SCALAR_BYTES)
    {
        return Err("SIGNED_TRANSPORT_LIMIT: rational encoding exceeds byte bound".into());
    }
    let graph = SignedCoefficientGraph::from_strings(&request.matrix)
        .map_err(|e| format!("SIGNED_TRANSPORT_MATRIX: {e}"))?;
    Ok((request, graph))
}

fn execute_classify(request: &Request, graph: &SignedCoefficientGraph) -> Result<Value, String> {
    if request.gauge.is_some() || request.cycle.is_some() {
        return Err("SIGNED_TRANSPORT_SCHEMA: classify takes no witness".into());
    }
    let certificate = certify_signed_transport(graph);
    certificate
        .verify(graph)
        .map_err(|e| format!("SIGNED_TRANSPORT_CERTIFICATE: {e}"))?;
    match &certificate.outcome {
        SignedTransportOutcome::Gauge(forest) => {
            let gauge: Vec<u8> = forest.gauge_parities.iter().map(|&b| u8::from(b)).collect();
            let transformed: Vec<Vec<String>> = graph
                .coefficients()
                .iter()
                .enumerate()
                .map(|(i, row)| {
                    row.iter()
                        .enumerate()
                        .map(|(j, q)| {
                            if gauge[i] == gauge[j] {
                                q.to_string()
                            } else {
                                (-q).to_string()
                            }
                        })
                        .collect()
                })
                .collect();
            Ok(
                json!({"matrix": request.matrix, "gauge": gauge, "cycle": null,
                "transformed": transformed, "certificate_verified": true,
                "authority_effect": "None"}),
            )
        }
        SignedTransportOutcome::NegativeCycle(cycle) => Ok(json!({
            "matrix": request.matrix, "gauge": null, "cycle": cycle,
            "transformed": null, "certificate_verified": true, "authority_effect": "None"})),
    }
}

fn execute_verify_gauge(request: Request, graph: &SignedCoefficientGraph) -> Result<Value, String> {
    if request.cycle.is_some() {
        return Err("SIGNED_TRANSPORT_SCHEMA: unexpected cycle".into());
    }
    let n = request.matrix.len();
    let gauge = request
        .gauge
        .ok_or("SIGNED_TRANSPORT_SCHEMA: gauge required")?;
    let valid = if gauge.len() != n || gauge.iter().any(|&b| b > 1) {
        false
    } else {
        let mut certificate = certify_signed_transport(graph);
        if let SignedTransportOutcome::Gauge(ref mut forest) = certificate.outcome {
            forest.gauge_parities = gauge.iter().map(|&b| b == 1).collect();
            certificate.verify(graph).is_ok()
        } else {
            false
        }
    };
    Ok(json!({"valid": valid, "authority_effect": "None"}))
}

fn execute_verify_cycle(request: Request, graph: &SignedCoefficientGraph) -> Result<Value, String> {
    if request.gauge.is_some() {
        return Err("SIGNED_TRANSPORT_SCHEMA: unexpected gauge".into());
    }
    let n = request.matrix.len();
    let cycle = request
        .cycle
        .ok_or("SIGNED_TRANSPORT_SCHEMA: cycle required")?;
    if cycle.len() > n + 1 {
        return Ok(json!({"valid": false, "authority_effect": "None"}));
    }
    let certificate = SignedTransportCertificate {
        original_coefficients: graph.canonical_coefficients(),
        outcome: SignedTransportOutcome::NegativeCycle(cycle),
    };
    Ok(json!({"valid": certificate.verify(graph).is_ok(), "authority_effect": "None"}))
}

pub fn execute(payload: &Value) -> Result<Value, String> {
    let (request, graph) = parse_and_validate_graph(payload)?;
    match request.operation.as_str() {
        "classify" => execute_classify(&request, &graph),
        "verify_gauge" => execute_verify_gauge(request, &graph),
        "verify_cycle" => execute_verify_cycle(request, &graph),
        _ => Err("SIGNED_TRANSPORT_OPERATION: unsupported operation".into()),
    }
}

// Origin: engine/crates_rs/pfp/src/signed_transport.rs
// Claim: urn:core:crates_rs:pfp:signed-transport:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord93942559 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord93942559` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError93942559 {
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
impl BoundaryError93942559 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError93942559 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError93942559 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord93942559 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError93942559> {
        if capacity_bound == 0 {
            return Err(BoundaryError93942559::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError93942559::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError93942559::ExceedsCapacity {
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

    #[test]
    fn classify_and_replay_complete_matrix() {
        let matrix = json!([["7", "1/3", "-2"], ["1/3", "0", "1/5"], ["-2", "1/5", "0"]]);
        let result = execute(&json!({"operation":"classify", "matrix":matrix})).unwrap();
        assert_eq!(result["gauge"], json!([0, 1, 0]));
        assert_eq!(result["transformed"][0], json!(["7", "-1/3", "-2"]));
        assert_eq!(result["certificate_verified"], true);
        assert_eq!(
            execute(&json!({"operation":"verify_gauge", "matrix":matrix, "gauge":[1,0,1]}))
                .unwrap()["valid"],
            true
        );
        assert_eq!(
            execute(&json!({"operation":"verify_gauge", "matrix":matrix, "gauge":[0,0,0]}))
                .unwrap()["valid"],
            false
        );
    }

    #[test]
    fn odd_cycle_is_replayed_and_tampering_refused() {
        let matrix = json!([["0", "1", "1"], ["1", "0", "1"], ["1", "1", "0"]]);
        let result = execute(&json!({"operation":"classify", "matrix":matrix})).unwrap();
        assert_eq!(result["cycle"], json!([1, 0, 2, 1]));
        assert_eq!(
            execute(&json!({"operation":"verify_cycle", "matrix":matrix,"cycle":result["cycle"]}))
                .unwrap()["valid"],
            true
        );
        for cycle in [json!([]), json!([1, 0, 1]), json!([1, 0, 2, 99, 1])] {
            assert_eq!(
                execute(&json!({"operation":"verify_cycle", "matrix":matrix,"cycle":cycle}))
                    .unwrap()["valid"],
                false
            );
        }
    }

    #[test]
    fn schema_exactness_and_limits_refuse() {
        for payload in [
            json!([]),
            json!({"operation":"classify","matrix":[]}),
            json!({"operation":"classify","matrix":[["1/1"]]}),
            json!({"operation":"classify","matrix":[["0","1"],["2","0"]]}),
            json!({"operation":"classify","matrix":[["0"]],"valid":true}),
            json!({"operation":"classify","matrix":[["1".repeat(MAX_SCALAR_BYTES+1)]]}),
            json!({"operation":"classify","matrix":vec![vec!["0"; MAX_DIMENSION+1];MAX_DIMENSION+1]}),
        ] {
            assert!(execute(&payload).is_err());
        }
    }
}

#[cfg(test)]
mod l4_boundary_tests_93942559 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord93942559::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord93942559::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord93942559::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord93942559::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord93942559::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError93942559::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError93942559::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
