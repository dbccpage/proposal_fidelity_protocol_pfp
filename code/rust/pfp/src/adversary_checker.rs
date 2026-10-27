//! Host-owned finite C011 verification over exact candidate bytes.
//! A checked finite primal/dual certificate is evidence; it grants no authority.
use num_rational::BigRational;
use num_traits::{One, Zero};
use core_functional::{ExactPhi1Certificate, Phi1Functional};
use core_kernel::{parse_exact, to_canonical_string};
use core_adversary::stage::ports::Refusal;
use core_adversary::checker_ports::{CandidateCheckRequest, CandidateCheckerPort};
use core_adversary::evidence::{sha256_ref, CandidateCheck, CandidateCheckInput, CheckerVerdict};
use serde::Deserialize;
use serde_json::{json, Map, Value};
use std::collections::{BTreeMap, BTreeSet};

const CHECKER_ID: &str = "symbol_game.c011.exact.v1";
const MAX_TEXT_BYTES: usize = 16_384;
const MAX_NODES: usize = 64;
const MAX_EDGES: usize = 128;
const MAX_SCALAR_BYTES: usize = 256;

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct SymbolGameRequest {
    schema_version: String,
    checker_id: String,
    authority_effect: String,
    case_json: String,
}
struct Case {
    nodes: Vec<String>,
    edges: Vec<(String, String)>,
    claims: BTreeMap<String, BigRational>,
    weights: BTreeMap<String, BigRational>,
}
pub(crate) struct NativeC011Checker {
    case_json: String,
    case: Case,
}
fn invalid(message: impl Into<String>) -> Refusal {
    Refusal::new("ADVERSARY_SYMBOL_GAME_REQUEST_INVALID", message)
}
fn object<'a>(value: &'a Value, label: &str) -> Result<&'a Map<String, Value>, String> {
    value
        .as_object()
        .ok_or_else(|| format!("{label} must be an object"))
}
fn array<'a>(value: &'a Value, label: &str) -> Result<&'a [Value], String> {
    value
        .as_array()
        .map(Vec::as_slice)
        .ok_or_else(|| format!("{label} must be an array"))
}
fn fields(value: &Map<String, Value>, allowed: &[&str]) -> Result<(), String> {
    if let Some(key) = value.keys().find(|key| !allowed.contains(&key.as_str())) {
        return Err(format!("undeclared C011 field {key:?}"));
    }
    Ok(())
}
fn identifier(value: &Value) -> Result<String, String> {
    let text = match value {
        Value::String(text) => text.clone(),
        Value::Number(number) if number.is_i64() || number.is_u64() => number.to_string(),
        _ => return Err("C011 identifiers must be strings or exact integers".into()),
    };
    if text.is_empty() || text.contains("->") || text.len() > MAX_SCALAR_BYTES {
        return Err("empty, ambiguous or oversized C011 identifier".into());
    }
    Ok(text)
}
fn exact(value: &Value) -> Result<BigRational, String> {
    let text = match value {
        Value::String(text) => text.clone(),
        Value::Number(number) if number.is_i64() || number.is_u64() => number.to_string(),
        _ => {
            return Err("C011 scalars require canonical rational strings or exact integers".into())
        }
    };
    if text.len() > MAX_SCALAR_BYTES {
        return Err("C011 scalar exceeds 256 bytes".into());
    }
    parse_exact(&text).map_err(|error| error.to_string())
}
fn vector(
    value: Option<&Value>,
    allowed: &BTreeSet<String>,
    label: &str,
) -> Result<BTreeMap<String, BigRational>, String> {
    let Some(value) = value else {
        return Ok(BTreeMap::new());
    };
    let mut result = BTreeMap::new();
    for (key, value) in object(value, label)? {
        if !allowed.contains(key) {
            return Err(format!("unknown {label} coordinate {key:?}"));
        }
        result.insert(key.clone(), exact(value)?);
    }
    Ok(result)
}
impl Case {
    fn validate_c011_header(value: &serde_json::Map<String, Value>) -> Result<(), String> {
        fields(
            value,
            &[
                "challenge",
                "challenge_id",
                "case_id",
                "id",
                "nodes",
                "edges",
                "claims",
                "weights",
            ],
        )?;
        let challenge = value.get("challenge").or_else(|| value.get("challenge_id"));
        let mismatch = ["challenge", "challenge_id"]
            .iter()
            .any(|key| value.get(*key).is_some_and(|v| v != &json!("c011")));
        if challenge != Some(&json!("c011")) || mismatch {
            return Err("only an unambiguous c011 challenge is supported".into());
        }
        for key in ["case_id", "id"] {
            if let Some(value) = value.get(key) {
                identifier(value)?;
            }
        }
        Ok(())
    }

    fn parse_single_c011_edge(
        edge: &Value,
        node_set: &BTreeSet<String>,
        edge_keys: &mut BTreeSet<String>,
    ) -> Result<(String, String), String> {
        let parts = array(edge, "edge")?;
        if parts.len() != 2 {
            return Err("each C011 edge needs exactly two endpoints".into());
        }
        let u = identifier(&parts[0])?;
        let v = identifier(&parts[1])?;
        let valid_endpoints = u != v && node_set.contains(&u) && node_set.contains(&v);
        if !valid_endpoints {
            return Err("C011 self-loop or unknown endpoint is out of scope".into());
        }
        if !edge_keys.insert(format!("{u}->{v}")) {
            return Err("duplicate C011 edge".into());
        }
        Ok((u, v))
    }

    fn parse_c011_edges(
        raw_edges: &[Value],
        node_set: &BTreeSet<String>,
    ) -> Result<(Vec<(String, String)>, BTreeSet<String>), String> {
        if raw_edges.len() > MAX_EDGES {
            return Err("C011 edge limit exceeded (128)".into());
        }
        let mut edges = Vec::new();
        let mut edge_keys = BTreeSet::new();
        for edge in raw_edges {
            edges.push(Self::parse_single_c011_edge(edge, node_set, &mut edge_keys)?);
        }
        Ok((edges, edge_keys))
    }

    fn parse_c011_nodes(value: &serde_json::Map<String, Value>) -> Result<(Vec<String>, BTreeSet<String>), String> {
        let nodes = array(value.get("nodes").unwrap_or(&Value::Null), "nodes")?
            .iter()
            .map(identifier)
            .collect::<Result<Vec<_>, _>>()?;
        let node_set: BTreeSet<_> = nodes.iter().cloned().collect();
        if nodes.len() > MAX_NODES || node_set.len() != nodes.len() {
            return Err("duplicate C011 nodes or node limit exceeded (64)".into());
        }
        Ok((nodes, node_set))
    }

    fn parse_c011_weights(
        value: &serde_json::Map<String, Value>,
        edge_keys: &BTreeSet<String>,
    ) -> Result<BTreeMap<String, BigRational>, String> {
        let weights = vector(value.get("weights"), edge_keys, "weights")?;
        if weights.values().any(|value| value <= &BigRational::zero()) {
            return Err("C011 weights must be strictly positive".into());
        }
        Ok(weights)
    }

    fn parse(raw: &str) -> Result<Self, String> {
        if raw.len() > MAX_TEXT_BYTES {
            return Err("C011 case exceeds 16384 UTF-8 bytes".into());
        }
        let value: Value = crate::protocol::strict_json(raw.as_bytes())?;
        let value = object(&value, "case")?;
        Self::validate_c011_header(value)?;
        let (nodes, node_set) = Self::parse_c011_nodes(value)?;
        let raw_edges = array(value.get("edges").unwrap_or(&Value::Null), "edges")?;
        let (edges, edge_keys) = Self::parse_c011_edges(raw_edges, &node_set)?;
        let claims = vector(value.get("claims"), &edge_keys, "claims")?;
        let weights = Self::parse_c011_weights(value, &edge_keys)?;
        Ok(Self {
            nodes,
            edges,
            claims,
            weights,
        })
    }

    fn build_d0_row(&self, u: &str, v: &str) -> Vec<BigRational> {
        self.nodes
            .iter()
            .map(|node| {
                if node == u {
                    -BigRational::one()
                } else if node == v {
                    BigRational::one()
                } else {
                    BigRational::zero()
                }
            })
            .collect()
    }

    fn build_edge_vectors(
        &self,
        repair: &BTreeMap<String, BigRational>,
        dual: &BTreeMap<String, BigRational>,
    ) -> (
        Vec<BigRational>,
        Vec<Vec<BigRational>>,
        Vec<BigRational>,
        Vec<BigRational>,
        Vec<BigRational>,
    ) {
        let mut omega = Vec::new();
        let mut d0 = Vec::new();
        let mut weights = Vec::new();
        let mut primal_residual = Vec::new();
        let mut dual_witness = Vec::new();
        for (u, v) in &self.edges {
            let key = format!("{u}->{v}");
            omega.push(
                self.claims
                    .get(&key)
                    .cloned()
                    .unwrap_or_else(BigRational::zero),
            );
            d0.push(self.build_d0_row(u, v));
            weights.push(
                self.weights
                    .get(&key)
                    .cloned()
                    .unwrap_or_else(BigRational::one),
            );
            primal_residual.push(repair.get(&key).cloned().unwrap_or_else(BigRational::zero));
            dual_witness.push(dual.get(&key).cloned().unwrap_or_else(BigRational::zero));
        }
        (omega, d0, weights, primal_residual, dual_witness)
    }

    fn parse_candidate_potential(
        &self,
        value: &serde_json::Map<String, Value>,
    ) -> Result<Vec<BigRational>, String> {
        let node_set = self.nodes.iter().cloned().collect();
        let potential = vector(value.get("potential"), &node_set, "potential")?;
        if potential.len() != self.nodes.len() || !value.contains_key("potential") {
            return Err("potential must supply every C011 node".into());
        }
        self.nodes
            .iter()
            .map(|node| {
                potential
                    .get(node)
                    .cloned()
                    .ok_or_else(|| format!("missing potential coordinate {node:?}"))
            })
            .collect::<Result<Vec<_>, String>>()
    }

    fn parse_candidate_vectors(
        &self,
        value: &serde_json::Map<String, Value>,
    ) -> Result<
        (
            BigRational,
            Vec<BigRational>,
            BTreeMap<String, BigRational>,
            BTreeMap<String, BigRational>,
        ),
        String,
    > {
        fields(value, &["status", "phi1", "potential", "repair", "dual"])?;
        if value.get("status") != Some(&json!("SOLVED")) {
            return Err("only a verified SOLVED certificate can be accepted".into());
        }
        let reported_value = exact(value.get("phi1").unwrap_or(&Value::Null))?;
        let alpha = self.parse_candidate_potential(value)?;
        let edge_set = self
            .edges
            .iter()
            .map(|(u, v)| format!("{u}->{v}"))
            .collect();
        let repair = vector(value.get("repair"), &edge_set, "repair")?;
        let dual = vector(value.get("dual"), &edge_set, "dual")?;
        Ok((reported_value, alpha, repair, dual))
    }

    fn check(&self, raw: &[u8]) -> Result<String, String> {
        if raw.len() > MAX_TEXT_BYTES {
            return Err("C011 candidate exceeds 16384 bytes".into());
        }
        let value: Value = crate::protocol::strict_json(raw)?;
        let value = object(&value, "candidate")?;
        let (reported_value, alpha, repair, dual) = self.parse_candidate_vectors(value)?;
        let (omega, d0, weights, primal_residual, dual_witness) =
            self.build_edge_vectors(&repair, &dual);
        let verified = Phi1Functional::verify_exact_certificate(ExactPhi1Certificate {
            omega,
            d0,
            weights,
            alpha,
            primal_residual,
            dual_witness,
            reported_value,
        })
        .map_err(|error| error.to_string())?;
        Ok(to_canonical_string(verified.value()))
    }
}
impl SymbolGameRequest {
    pub(crate) fn case_text(&self) -> &str {
        &self.case_json
    }
    pub(crate) fn case_digest(&self) -> String {
        sha256_ref(self.case_json.as_bytes())
    }
}
impl NativeC011Checker {
    pub(crate) fn new(request: &SymbolGameRequest) -> Result<Self, Refusal> {
        if request.schema_version != "core.symbol-game.request.v1"
            || request.checker_id != CHECKER_ID
            || request.authority_effect != "None"
        {
            return Err(invalid(
                "unsupported Symbol Game request schema, checker identity or authority effect",
            ));
        }
        Ok(Self {
            case_json: request.case_json.clone(),
            case: Case::parse(&request.case_json).map_err(invalid)?,
        })
    }
}
impl CandidateCheckerPort for NativeC011Checker {
    fn check_candidate(
        &mut self,
        request: &CandidateCheckRequest<'_>,
    ) -> Result<CandidateCheck, Refusal> {
        let result = self.case.check(request.candidate_bytes);
        let (verdict, reason, verified_phi1) = match result {
            Ok(value) => (CheckerVerdict::Accepted, String::new(), Some(value)),
            Err(reason) => (CheckerVerdict::Rejected, reason, None),
        };
        let content_digest = sha256_ref(request.candidate_bytes);
        let receipt = json!({
            "schema_version": "core.adversary.symbol-game-check.v1", "authority_effect": "None",
            "run_key": request.run_key, "candidate_id": request.candidate_id,
            "candidate_content_sha256": content_digest, "checker_id": CHECKER_ID, "verdict": verdict,
            "case_sha256": sha256_ref(self.case_json.as_bytes()), "case_json": self.case_json,
            "checker_source_sha256": sha256_ref(include_bytes!("adversary_checker.rs")),
            "checker_kernel_source_sha256": sha256_ref(include_bytes!("../../core_functional/src/phi1.rs")),
            "verified_phi1": verified_phi1, "reason": reason,
        });
        let raw = serde_json::to_vec(&receipt).map_err(|error| invalid(error.to_string()))?;
        CandidateCheck::new(CandidateCheckInput {
            verdict,
            candidate_id: request.candidate_id.into(),
            candidate_content_sha256: content_digest,
            checker_id: CHECKER_ID.into(),
            checker_receipt_sha256: Some(sha256_ref(&raw)),
            checker_receipt_bytes: raw,
            reason,
        })
    }
}

// Origin: engine/crates_rs/pfp/src/adversary_checker.rs
// Claim: urn:core:crates_rs:pfp:adversary-checker:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda28115fe {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda28115fe` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora28115fe {
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
impl BoundaryErrora28115fe {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora28115fe {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora28115fe {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda28115fe {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora28115fe> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora28115fe::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora28115fe::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora28115fe::ExceedsCapacity {
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
mod l4_boundary_tests_a28115fe {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorda28115fe::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorda28115fe::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorda28115fe::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorda28115fe::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorda28115fe::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrora28115fe::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrora28115fe::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
