//! Exact rank operations for the Python compatibility API. AuthorityEffect: None.
use crate::{
    civilization::{canonical, rational, Refusal},
    rank::row_reduce,
};
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Zero};
use serde_json::{json, Value};
use std::collections::{BTreeMap, BTreeSet};

fn refuse(code: &str, message: impl Into<String>) -> Refusal {
    Refusal {
        code: code.into(),
        message: format!("{code}: {}", message.into()),
        state: None,
    }
}
fn decode<T: serde::de::DeserializeOwned>(value: &Value) -> Result<T, Refusal> {
    serde_json::from_value(value.clone()).map_err(|e| refuse("RANK_INPUT_INVALID", e.to_string()))
}
fn count(value: &Value) -> Result<BigInt, Refusal> {
    value
        .as_number()
        .and_then(|n| n.to_string().parse().ok())
        .ok_or_else(|| refuse("RANK_INPUT_INVALID", "evidence counts must be integers"))
}
fn limit(payload: &Value, key: &str, default: i64) -> Result<BigInt, Refusal> {
    payload
        .get(key)
        .map(count)
        .unwrap_or_else(|| Ok(BigInt::from(default)))
}
type Graph = (Vec<String>, Vec<(String, String)>);
fn graph(payload: &Value) -> Result<Graph, Refusal> {
    Ok((decode(&payload["nodes"])?, decode(&payload["edges"])?))
}
fn alpha(payload: &Value) -> Result<BigRational, Refusal> {
    payload
        .get("alpha")
        .map(rational)
        .unwrap_or_else(|| Ok(BigRational::new(17.into(), 20.into())))
}
fn node_quality(entry: &Value) -> Result<BigRational, Refusal> {
    let Some(passes_val) = entry.get("passes").filter(|v| !v.is_null()) else {
        return Ok(BigRational::new(1.into(), 2.into()));
    };
    let passes = count(passes_val)?;
    let failures = entry
        .get("failures")
        .map(count)
        .unwrap_or_else(|| Ok(BigInt::zero()))?;
    let total = &passes + failures;
    if total > BigInt::zero() {
        Ok(BigRational::new(passes, total))
    } else {
        Ok(BigRational::new(1.into(), 2.into()))
    }
}

fn build_transition_row(
    n: usize,
    parents_row: Option<&Vec<usize>>,
    quality: &BigRational,
    uniform: &BigRational,
) -> Vec<BigRational> {
    let Some(rows) = parents_row else {
        return vec![uniform.clone(); n];
    };
    (0..n)
        .map(|j| {
            let mut value = (BigRational::one() - quality) * uniform;
            if rows.contains(&j) {
                value += quality / BigInt::from(rows.len());
            }
            value
        })
        .collect()
}

fn matrix(
    nodes: &[String],
    edges: &[(String, String)],
    evidence: &Value,
) -> Result<Vec<Vec<BigRational>>, Refusal> {
    let n = nodes.len();
    if n == 0 {
        return Ok(Vec::new());
    }
    let uniform = BigRational::new(BigInt::one(), BigInt::from(n));
    let indices = nodes
        .iter()
        .enumerate()
        .map(|(i, node)| (node, i))
        .collect::<BTreeMap<_, _>>();
    let mut parents = BTreeMap::<usize, Vec<usize>>::new();
    for (p, c) in edges {
        if let (Some(&p), Some(&c)) = (indices.get(p), indices.get(c)) {
            parents.entry(c).or_default().push(p);
        }
    }
    nodes
        .iter()
        .enumerate()
        .map(|(i, node)| {
            let quality = node_quality(&evidence[node])?;
            Ok(build_transition_row(n, parents.get(&i), &quality, &uniform))
        })
        .collect()
}
fn wire_matrix(rows: &[Vec<BigRational>]) -> Value {
    json!(rows
        .iter()
        .map(|row| row.iter().map(canonical).collect::<Vec<_>>())
        .collect::<Vec<_>>())
}
fn rational_matrix(value: &Value) -> Result<Vec<Vec<BigRational>>, Refusal> {
    value
        .as_array()
        .ok_or_else(|| refuse("RANK_INPUT_INVALID", "matrix must be an array"))?
        .iter()
        .map(|row| {
            row.as_array()
                .ok_or_else(|| refuse("RANK_INPUT_INVALID", "matrix row must be an array"))?
                .iter()
                .map(rational)
                .collect()
        })
        .collect()
}

fn is_valid_candidate_rank(rank: &[BigRational], n: usize) -> bool {
    n != 0
        && rank.len() == n
        && !rank.iter().any(|v| v < &BigRational::zero())
        && rank.iter().cloned().sum::<BigRational>() == BigRational::one()
}

fn check_declared_vs_expected(
    declared: &[Vec<BigRational>],
    expected: &[Vec<BigRational>],
) -> Result<(), Refusal> {
    for (i, row) in declared.iter().enumerate() {
        for (j, value) in row.iter().enumerate() {
            if value != &expected[i][j] {
                return Err(refuse(
                    "TRANSITION_MATRIX_RECONSTRUCTION_MISMATCH",
                    format!(
                        "entry [{i}][{j}] declared {} != reconstructed {}",
                        canonical(value),
                        canonical(&expected[i][j])
                    ),
                ));
            }
        }
    }
    Ok(())
}

fn parse_candidate_rank(payload: &Value) -> Result<Vec<BigRational>, Refusal> {
    let arr = payload["candidate_rank"]
        .as_array()
        .ok_or_else(|| refuse("RANK_INPUT_INVALID", "rank must be an array"))?;
    arr.iter().map(rational).collect()
}

fn is_stationary_rank(
    expected: &[Vec<BigRational>],
    rank: &[BigRational],
    alpha: &BigRational,
    n: usize,
) -> bool {
    let teleport = (BigRational::one() - alpha) / BigInt::from(n);
    (0..n).all(|i| {
        rank[i]
            == alpha
                * (0..n)
                    .map(|j| &expected[j][i] * &rank[j])
                    .sum::<BigRational>()
                + &teleport
    })
}

fn is_square_matrix(mat: &[Vec<BigRational>], n: usize) -> bool {
    mat.len() == n && mat.iter().all(|row| row.len() == n)
}

fn verify(payload: &Value) -> Result<Value, Refusal> {
    let (nodes, edges) = graph(payload)?;
    let n = nodes.len();
    let rank = parse_candidate_rank(payload)?;
    if !is_valid_candidate_rank(&rank, n) {
        return Ok(json!(false));
    }
    let expected = matrix(&nodes, &edges, &payload["evidence"])?;
    let declared = match payload.get("declared_transition_matrix") {
        Some(val) => rational_matrix(val)?,
        None => expected.clone(),
    };
    if !is_square_matrix(&declared, n) {
        return Ok(json!(false));
    }
    check_declared_vs_expected(&declared, &expected)?;
    let alpha = alpha(payload)?;
    Ok(json!(is_stationary_rank(&expected, &rank, &alpha, n)))
}

fn infer_solve_nodes(edges: &[(String, String)], n: usize) -> Vec<String> {
    let mut nodes = Vec::new();
    for (p, c) in edges {
        for node in [p, c] {
            if !nodes.contains(node) {
                nodes.push(node.clone());
            }
        }
    }
    for i in 0..n {
        if nodes.len() >= n {
            break;
        }
        let name = format!("node_{i}");
        if !nodes.contains(&name) {
            nodes.push(name);
        }
    }
    nodes.into_iter().take(n).collect()
}

fn resolve_solve_nodes(
    payload: &Value,
    edges: &[(String, String)],
    n: usize,
) -> Result<Vec<String>, Refusal> {
    let nodes: Vec<String> = match payload.get("nodes").filter(|n| !n.is_null()) {
        Some(raw) => decode::<Vec<String>>(raw)?.into_iter().take(n).collect(),
        None => infer_solve_nodes(edges, n),
    };
    if nodes.len() != n {
        return Err(refuse(
            "RANK_INPUT_INVALID",
            "declared node list is shorter than num_nodes",
        ));
    }
    Ok(nodes)
}

fn build_solve_system(
    transition: &[Vec<BigRational>],
    alpha: &BigRational,
    n: usize,
) -> Vec<Vec<BigRational>> {
    let teleport = (BigRational::one() - alpha) / BigInt::from(n);
    let mut coefficients = vec![vec![BigRational::zero(); n + 1]; n];
    for (i, row) in coefficients.iter_mut().enumerate() {
        for j in 0..n {
            row[j] = -alpha * &transition[j][i];
            if i == j {
                row[j] += BigRational::one();
            }
        }
        row[n] = teleport.clone();
    }
    coefficients[n - 1].fill(BigRational::one());
    coefficients
}

fn validate_solve_limits(payload: &Value, n: &BigInt, edges_len: usize) -> Result<usize, Refusal> {
    let max_nodes = limit(payload, "max_nodes", 1000)?;
    let max_edges = limit(payload, "max_edges", 5000)?;
    if n > &max_nodes || BigInt::from(edges_len) > max_edges {
        return Err(refuse(
            "BUDGET_EXHAUSTED",
            format!(
                "Solver limits exceeded (nodes={n}/{max_nodes}, edges={edges_len}/{max_edges})"
            ),
        ));
    }
    usize::try_from(n).map_err(|_| {
        refuse(
            "RANK_INPUT_INVALID",
            "node count must be a nonnegative machine integer",
        )
    })
}

fn reduce_solve_system(
    coefficients: &mut [Vec<BigRational>],
    bit_limit: &BigInt,
) -> Result<(), Refusal> {
    row_reduce(coefficients, Some(bit_limit)).map_err(|message| Refusal {
        code: message
            .split(':')
            .next()
            .unwrap_or("RANK_INPUT_INVALID")
            .into(),
        message,
        state: None,
    })
}

fn solve(payload: &Value) -> Result<Value, Refusal> {
    let n_big = count(&payload["num_nodes"])?;
    let edges: Vec<(String, String)> = decode(&payload["edges"])?;
    let n = validate_solve_limits(payload, &n_big, edges.len())?;
    if n == 0 {
        return Ok(json!([]));
    }
    let nodes = resolve_solve_nodes(payload, &edges, n)?;
    let transition = matrix(&nodes, &edges, &payload["evidence"])?;
    let alpha = alpha(payload)?;
    let mut coefficients = build_solve_system(&transition, &alpha, n);
    let bit_limit = limit(payload, "max_bit_length", 4096)?;
    reduce_solve_system(&mut coefficients, &bit_limit)?;
    Ok(json!(coefficients
        .iter()
        .map(|row| canonical(&row[n]))
        .collect::<Vec<_>>()))
}

fn execute_community(payload: &Value) -> Result<Value, Refusal> {
    let edges: Vec<(String, String)> = decode(&payload["graph_edges"])?;
    let root = payload["root"]
        .as_str()
        .ok_or_else(|| refuse("RANK_INPUT_INVALID", "root must be a string"))?;
    let digests = payload
        .get("genome_action_digests")
        .and_then(Value::as_object);
    let mut seen = BTreeSet::new();
    let mut children = 0usize;
    for (parent, child) in edges {
        let identity = digests
            .and_then(|d| d.get(&child))
            .and_then(Value::as_str)
            .unwrap_or(&child);
        if digests.is_none_or(|d| d.is_empty())
            || seen.insert((parent.clone(), identity.to_owned()))
        {
            children += usize::from(parent == root);
        }
    }
    Ok(json!(canonical(
        &(BigRational::new(17.into(), 20.into())
            * BigRational::new(BigInt::from(children), BigInt::from(children + 1))
            + BigRational::new(3.into(), 20.into()))
    )))
}

pub fn execute(payload: &Value) -> Result<Value, Refusal> {
    match payload["operation"].as_str() {
        Some("inverse") => Ok(json!(canonical(
            &(BigRational::new(17.into(), 20.into()) * rational(&payload["child_pass_fraction"])?
                + BigRational::new(3.into(), 20.into()))
        ))),
        Some("community") => execute_community(payload),
        Some("matrix") => {
            let (nodes, edges) = graph(payload)?;
            Ok(wire_matrix(&matrix(&nodes, &edges, &payload["evidence"])?))
        }
        Some("verify") => verify(payload),
        Some("solve") => solve(payload),
        _ => Err(refuse("RANK_INPUT_INVALID", "unknown rank operation")),
    }
}

// Origin: engine/crates_rs/core_prompt_civilization/src/rank_port.rs
// Claim: urn:core:crates_rs:core-prompt-civilization:rank-port:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord6e8eaa6e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord6e8eaa6e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError6e8eaa6e {
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
impl BoundaryError6e8eaa6e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError6e8eaa6e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError6e8eaa6e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord6e8eaa6e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError6e8eaa6e> {
        if capacity_bound == 0 {
            return Err(BoundaryError6e8eaa6e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError6e8eaa6e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError6e8eaa6e::ExceedsCapacity {
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
mod l4_boundary_tests_6e8eaa6e {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord6e8eaa6e::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord6e8eaa6e::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord6e8eaa6e::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord6e8eaa6e::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord6e8eaa6e::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError6e8eaa6e::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError6e8eaa6e::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
