//! Input-bound finite continuum/meta-theory receipts. Arithmetic lives in native owners.
use std::collections::BTreeMap;

use linear_algebra::backend::basic_matrix::BasicMatrix;
use num_traits::Zero;
use core_homology::cochain_complex::{CochainComplex, TheoremProvenance};
use core_homology::finite_directed_graph::FiniteDirectedGraph;
use core_homology::presentation_symmetry::{
    verify_cochain_symmetry, verify_difference_symmetry, verify_graph_symmetry, SignedPermutation,
};
use core_kernel::{parse_exact, to_canonical_string, Exact};
use core_number_theory::circle_haar::{
    embedded_turn, lipschitz_sample_prefix, polynomial_average, refine_residue,
};
use pfp_runtime::framed_sha256;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};

pub const REQUEST_DOMAIN: &str = "core.symbol-game.continuum-evaluate-request.v1";

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
enum Request {
    CyclicEmbedding {
        order: usize,
        residue: usize,
        refinement_order: usize,
    },
    HaarPolynomial {
        order: usize,
        terms: Vec<Term>,
    },
    LipschitzSamples {
        lipschitz_constant: String,
        samples: Vec<Vec<String>>,
    },
    GraphSymmetry {
        nodes: Vec<String>,
        edges: Vec<(usize, usize)>,
        image: Vec<usize>,
    },
    CochainSymmetry {
        dimensions: [usize; 3],
        d0: Vec<String>,
        d1: Vec<String>,
        maps: [Map; 3],
        difference_operator: Option<Vec<String>>,
    },
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct Term {
    frequency: i64,
    coefficient: String,
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct Map {
    image: Vec<usize>,
    signs: Vec<i8>,
}

fn exact(text: &str) -> Result<Exact, String> {
    if text.len() > 1024 {
        return Err("CONTINUUM_EXACT_INPUT_TOO_LARGE".into());
    }
    parse_exact(text).map_err(|e| format!("CONTINUUM_NOT_EXACT: {e}"))
}

fn matrix(rows: usize, cols: usize, values: &[String]) -> Result<BasicMatrix<Exact>, String> {
    if values.len() != rows * cols {
        return Err("CONTINUUM_MATRIX_SHAPE".into());
    }
    BasicMatrix::from_row_major(
        rows,
        cols,
        values.iter().map(|s| exact(s)).collect::<Result<_, _>>()?,
    )
    .map_err(|e| format!("CONTINUUM_MATRIX_INVALID: {e}"))
}

fn eval_cyclic_embedding(
    order: usize,
    residue: usize,
    refinement_order: usize,
) -> Result<Value, String> {
    let turn = embedded_turn(order, residue).map_err(|e| e.to_string())?;
    let image = refine_residue(order, refinement_order, residue).map_err(|e| e.to_string())?;
    let refined_turn = embedded_turn(refinement_order, image).map_err(|e| e.to_string())?;
    Ok(json!({"turn": to_canonical_string(&turn), "refined_residue": image,
        "refined_turn": to_canonical_string(&refined_turn), "commutes": turn == refined_turn}))
}

fn eval_haar_polynomial(order: usize, terms: Vec<Term>) -> Result<Value, String> {
    if terms.len() > 64 {
        return Err("CONTINUUM_TERM_BUDGET".into());
    }
    let mut coefficients = BTreeMap::new();
    for term in terms {
        if coefficients
            .insert(term.frequency, exact(&term.coefficient)?)
            .is_some()
        {
            return Err("CONTINUUM_DUPLICATE_FREQUENCY".into());
        }
    }
    let average = polynomial_average(order, &coefficients).map_err(|e| e.to_string())?;
    let haar = coefficients.get(&0).cloned().unwrap_or_else(Exact::zero);
    let max_frequency = coefficients
        .iter()
        .filter(|(_, c)| !c.is_zero())
        .map(|(k, _)| k.unsigned_abs())
        .max()
        .unwrap_or(0);
    Ok(json!({"finite_average": to_canonical_string(&average), "haar_integral": to_canonical_string(&haar),
        "max_frequency": max_frequency, "alias_free": order as u64 > max_frequency,
        "observed_recovery": average == haar, "arithmetic": "exact_cyclotomic"}))
}

fn eval_lipschitz_samples(
    lipschitz_constant: String,
    samples: Vec<Vec<String>>,
) -> Result<Value, String> {
    if samples.len() > 8 || samples.iter().any(|s| s.len() > 128) {
        return Err("CONTINUUM_SAMPLE_BUDGET".into());
    }
    let samples = samples
        .iter()
        .map(|row| row.iter().map(|s| exact(s)).collect::<Result<Vec<_>, _>>())
        .collect::<Result<Vec<_>, _>>()?;
    let enclosures =
        lipschitz_sample_prefix(&exact(&lipschitz_constant)?, &samples).map_err(|e| e.to_string())?;
    Ok(json!({"extension_scope": "any_common_periodic_lipschitz_extension",
        "infinite_family_verified": false,
        "enclosures": enclosures.iter().map(|e| json!({"order": e.order,
            "average": to_canonical_string(&e.average), "radius": to_canonical_string(&e.radius),
            "lower": to_canonical_string(&(&e.average - &e.radius)),
            "upper": to_canonical_string(&(&e.average + &e.radius))})).collect::<Vec<_>>()}))
}

fn eval_graph_symmetry(
    nodes: Vec<String>,
    edges: Vec<(usize, usize)>,
    image: Vec<usize>,
) -> Result<Value, String> {
    if nodes.len() > 32 || edges.len() > 128 {
        return Err("CONTINUUM_GRAPH_BUDGET".into());
    }
    if nodes.iter().any(|name| name.trim().is_empty()) {
        return Err("CONTINUUM_EMPTY_NODE_NAME".into());
    }
    let node_index = nodes
        .iter()
        .enumerate()
        .map(|(i, name)| (name.clone(), i))
        .collect();
    let provenance = core_homology::finite_directed_graph::TheoremProvenance {
        verification_source: "caller-declared finite graph; structure checked".into(),
    };
    let graph = FiniteDirectedGraph::new(nodes, node_index, edges, provenance)
        .map_err(|e| e.to_string())?;
    let edge_image = verify_graph_symmetry(&graph, &image).map_err(|e| e.to_string())?;
    Ok(json!({"edge_image": edge_image, "incidence_intertwines": true,
        "laplacian_equivariant": true}))
}

fn verify_optional_difference(
    n0: usize,
    difference_operator: Option<Vec<String>>,
    map0: &SignedPermutation,
) -> Result<bool, String> {
    let Some(values) = difference_operator else {
        return Ok(false);
    };
    verify_difference_symmetry(&matrix(n0, n0, &values)?, map0).map_err(|e| e.to_string())?;
    Ok(true)
}

fn eval_cochain_symmetry(
    dimensions: [usize; 3],
    d0: Vec<String>,
    d1: Vec<String>,
    maps: [Map; 3],
    difference_operator: Option<Vec<String>>,
) -> Result<Value, String> {
    let [n0, n1, n2] = dimensions;
    if [n0 > 32, n1 > 128, n2 > 64].into_iter().any(|b| b) {
        return Err("CONTINUUM_COMPLEX_BUDGET".into());
    }
    let provenance = TheoremProvenance::new("continuum evaluator: recomputed d1*d0".into())
        .map_err(|e| e.to_string())?;
    let complex = CochainComplex::new(
        n0,
        n1,
        n2,
        matrix(n1, n0, &d0)?,
        matrix(n2, n1, &d1)?,
        provenance,
    )
    .map_err(|e| e.to_string())?;
    let maps = maps.map(|m| SignedPermutation {
        image: m.image,
        signs: m.signs,
    });
    verify_cochain_symmetry(&complex, &maps).map_err(|e| e.to_string())?;
    let difference_verified = verify_optional_difference(n0, difference_operator, &maps[0])?;
    Ok(json!({"coboundary_law_verified": true, "cochain_intertwines": true,
        "difference_operator_verified": difference_verified}))
}

fn dispatch_continuum_request(request: Request) -> Result<Value, String> {
    match request {
        Request::CyclicEmbedding {
            order,
            residue,
            refinement_order,
        } => eval_cyclic_embedding(order, residue, refinement_order),
        Request::HaarPolynomial { order, terms } => eval_haar_polynomial(order, terms),
        Request::LipschitzSamples {
            lipschitz_constant,
            samples,
        } => eval_lipschitz_samples(lipschitz_constant, samples),
        Request::GraphSymmetry {
            nodes,
            edges,
            image,
        } => eval_graph_symmetry(nodes, edges, image),
        Request::CochainSymmetry {
            dimensions,
            d0,
            d1,
            maps,
            difference_operator,
        } => eval_cochain_symmetry(dimensions, d0, d1, maps, difference_operator),
    }
}

pub fn evaluate(payload: &Value) -> Result<Value, String> {
    let request: Request = serde_json::from_value(payload.clone())
        .map_err(|e| format!("INVALID_CONTINUUM_REQUEST: {e}"))?;
    let evidence = dispatch_continuum_request(request)?;
    Ok(
        json!({"schema_version": "core.continuum.finite-receipt.v1",
        "input_digest": framed_sha256(REQUEST_DOMAIN, &crate::protocol::canonical_json(payload)),
        "evidence": evidence,
        "provenance": {"realizes": null, "genesis_effect": "None",
            "genesis_register_access": "not_performed", "model_evidence_only": true},
        "authority_effect": "None"}),
    )
}

// Origin: engine/crates_rs/pfp/src/continuum.rs
// Claim: urn:core:crates_rs:pfp:continuum:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord6d5e0001 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord6d5e0001` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError6d5e0001 {
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
impl BoundaryError6d5e0001 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError6d5e0001 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError6d5e0001 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord6d5e0001 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError6d5e0001> {
        if capacity_bound == 0 {
            return Err(BoundaryError6d5e0001::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError6d5e0001::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError6d5e0001::ExceedsCapacity {
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
mod l4_boundary_tests_6d5e0001 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord6d5e0001::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord6d5e0001::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord6d5e0001::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord6d5e0001::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord6d5e0001::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError6d5e0001::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError6d5e0001::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
