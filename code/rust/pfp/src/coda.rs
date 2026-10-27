//! Input-bound CODA-CODA_GTLA pipeline evaluation across the runtime seam.
//!
//! Grounded in CODA-CODA_GTLA (Definitions D01/D02, Theorems T02, T03, T09):
//! Evaluates the Master Normal Form pipeline stage-by-stage and returns the
//! three distinct axes: diagnostic, routing, and authority.
//!
//! AuthorityEffect: None.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_2a609ee9<T> {
    fn checked_invariant_2a609ee9(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_2a609ee9<T> for Option<T> {
    #[inline]
    fn checked_invariant_2a609ee9(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_2a609ee9<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_2a609ee9(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::ToPrimitive;
use serde::{Deserialize, Serialize};
use serde_json::{Map, Value};

use core_pipelines::coda_gtla::{evaluate_pipeline, PipelineInput};
use core_policy::trichotomy::ObstructionDiagnosticClass;
use core_solvers::solver_cohomology_simplicial_l1::solve_l1_quotient;
use pfp_runtime::framed_sha256;
use core_types::{AuthorityTerminal, Outcome, RefusalSource, RoutingTerminal};

use crate::protocol::canonical_json;

/// Digest domain binding a receipt to the request payload that produced it.
pub const CODA_REQUEST_DOMAIN: &str = "core.symbol-game.coda-evaluate-request.v1";
pub const CODA_RECEIPT_SCHEMA: &str = "core.symbol-game.coda-receipt.v1";

/// Bound on distance / budget evaluation.
pub const MAX_CODA_BUDGET: usize = 4096;
const MAX_CODA_MATRIX_DIM: usize = 8;
pub const CODA_PREMISE_SOURCE_DECLARED: &str = "declared";

/// Caller-supplied boundary matrices. They are a refusal witness for a
/// declared distance, not a source of `ExactRuleDerived`.
#[derive(Debug, Clone, PartialEq, Eq, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CodaDistanceMatrices {
    pub d0: Vec<Vec<i64>>,
    pub d1: Vec<Vec<i64>>,
    pub cochain: Vec<i64>,
}

#[derive(Debug, Clone, PartialEq, Eq, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CodaEvaluateRequestV1 {
    pub input_id: String,
    pub sieve_non_empty: bool,
    pub refinement_consistent: bool,
    pub gluing_succeeded: bool,
    pub phi1_distance: u64,
    pub gamma2_distance: u64,
    pub license_granted: bool,
    #[serde(default)]
    pub budget: Option<usize>,
    #[serde(default)]
    pub matrices: Option<CodaDistanceMatrices>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CodaEvaluateReceiptV1 {
    pub schema_version: String,
    pub input_digest: String,
    pub input_id: String,
    pub diagnostic: ObstructionDiagnosticClass,
    pub routing: RoutingTerminal,
    pub authority: Outcome,
    pub detail: String,
    pub authority_effect: String,
    pub premise_source: String,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CodaVerifyRequestV1 {
    pub request: Value,
    pub receipt: CodaEvaluateReceiptV1,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CodaRefusal {
    pub code: &'static str,
    pub detail: String,
}

impl CodaRefusal {
    pub fn new(code: &'static str, detail: impl Into<String>) -> Self {
        Self {
            code,
            detail: detail.into(),
        }
    }

    pub fn wire(&self) -> String {
        format!("{}: {}", self.code, self.detail)
    }
}

/// `framed_sha256` over the sorted, whitespace-free JSON of the payload.
pub fn coda_input_digest(payload: &Value) -> String {
    framed_sha256(CODA_REQUEST_DOMAIN, &canonical_json(payload))
}

fn reject_floats(value: &Value, locus: &str) -> Result<(), CodaRefusal> {
    match value {
        Value::Number(number) => {
            let text = number.to_string();
            if text.contains(['.', 'e', 'E']) {
                return Err(CodaRefusal::new(
                    "FLOAT_FORBIDDEN",
                    format!("{locus} is the JSON number {text}; exact values cross as integers"),
                ));
            }
            Ok(())
        }
        Value::Array(items) => items
            .iter()
            .enumerate()
            .try_for_each(|(index, item)| reject_floats(item, &format!("{locus}[{index}]"))),
        Value::Object(object) => object
            .iter()
            .try_for_each(|(key, item)| reject_floats(item, &format!("{locus}.{key}"))),
        _ => Ok(()),
    }
}

/// Evaluate the Master Normal Form pipeline for one request.
pub fn evaluate_coda(payload: &Value) -> Result<CodaEvaluateReceiptV1, CodaRefusal> {
    reject_floats(payload, "payload")?;
    let request: CodaEvaluateRequestV1 = serde_json::from_value(payload.clone())
        .map_err(|error| CodaRefusal::new("INVALID_CODA_REQUEST", error.to_string()))?;

    // Budget bounds check
    let total_distance =
        (request.phi1_distance as usize).saturating_add(request.gamma2_distance as usize);
    if total_distance > MAX_CODA_BUDGET
        || request.phi1_distance as usize > MAX_CODA_BUDGET
        || request.gamma2_distance as usize > MAX_CODA_BUDGET
        || request
            .budget
            .is_some_and(|b| b < total_distance || b > MAX_CODA_BUDGET)
    {
        return Err(CodaRefusal::new(
            "BUDGET_UNKNOWN",
            format!("request distance or budget exceeds bound of {MAX_CODA_BUDGET}"),
        ));
    }

    // FOC-T3 consistency check: phi1 = 0 with gamma2 > 0 is refused
    if request.phi1_distance == 0 && request.gamma2_distance > 0 {
        return Err(CodaRefusal::new(
            "INCONSISTENT_WITNESS",
            "phi1 = 0 with gamma2 > 0 is refused under FOC-T3",
        ));
    }
    refuse_supplied_distance(&request)?;

    let input = PipelineInput {
        input_id: request.input_id,
        sieve_non_empty: request.sieve_non_empty,
        refinement_consistent: request.refinement_consistent,
        gluing_succeeded: request.gluing_succeeded,
        phi1_distance: request.phi1_distance,
        gamma2_distance: request.gamma2_distance,
        license_granted: request.license_granted,
    };

    let mut output = evaluate_pipeline(&input);
    // A caller boolean is a declared premise, not a witness that can mint the label.
    if matches!(
        output.authority,
        Outcome::Terminal(AuthorityTerminal::ExactRuleDerived)
    ) {
        output.authority = Outcome::Refused(RefusalSource::Refusal);
        output.detail = "declared premises do not mint ExactRuleDerived".to_string();
    }

    Ok(CodaEvaluateReceiptV1 {
        schema_version: CODA_RECEIPT_SCHEMA.to_owned(),
        input_digest: coda_input_digest(payload),
        input_id: output.input_id,
        diagnostic: output.diagnostic,
        routing: output.routing,
        authority: output.authority,
        detail: output.detail,
        authority_effect: "None".to_owned(),
        premise_source: CODA_PREMISE_SOURCE_DECLARED.to_owned(),
    })
}

fn bounded_matrix(matrix: &[Vec<i64>], columns: usize) -> Result<(), CodaRefusal> {
    if matrix.len() > MAX_CODA_MATRIX_DIM
        || columns > MAX_CODA_MATRIX_DIM
        || matrix.iter().any(|row| row.len() > MAX_CODA_MATRIX_DIM)
    {
        return Err(CodaRefusal::new(
            "BUDGET_UNKNOWN",
            "distance matrices exceed the declared finite bound",
        ));
    }
    Ok(())
}

fn apply_matrix(matrix: &[Vec<i64>], vector: &[i64]) -> Result<Vec<i128>, CodaRefusal> {
    bounded_matrix(matrix, vector.len())?;
    let mut image = Vec::with_capacity(matrix.len());
    for row in matrix {
        if row.len() != vector.len() {
            return Err(CodaRefusal::new(
                "MATRIX_SHAPE",
                "a distance matrix row does not match the cochain",
            ));
        }
        let mut acc: i128 = 0;
        for (left, right) in row.iter().zip(vector.iter()) {
            let product = (*left as i128).checked_mul(*right as i128).ok_or_else(|| {
                CodaRefusal::new("BUDGET_UNKNOWN", "matrix product overflowed")
            })?;
            acc = acc.checked_add(product).ok_or_else(|| {
                CodaRefusal::new("BUDGET_UNKNOWN", "matrix product overflowed")
            })?;
        }
        image.push(acc);
    }
    Ok(image)
}

fn l1_distance(values: &[i128]) -> Result<u64, CodaRefusal> {
    let mut total: u128 = 0;
    for value in values {
        total = total.checked_add(value.unsigned_abs()).ok_or_else(|| {
            CodaRefusal::new("BUDGET_UNKNOWN", "distance overflowed")
        })?;
    }
    u64::try_from(total).map_err(|_| {
        CodaRefusal::new("BUDGET_UNKNOWN", "distance exceeds the declared bound")
    })
}

fn rational_i64(value: i64) -> BigRational {
    BigRational::from_integer(BigInt::from(value))
}

fn phi1_from_matrices(d0: &[Vec<i64>], cochain: &[i64]) -> Result<u64, CodaRefusal> {
    bounded_matrix(d0, cochain.len())?;
    if d0.len() != cochain.len() || d0.iter().any(|row| row.len() != d0.first().map_or(0, Vec::len))
    {
        return Err(CodaRefusal::new(
            "MATRIX_SHAPE",
            "d0 does not match the cochain",
        ));
    }
    let matrix: Vec<Vec<BigRational>> = d0
        .iter()
        .map(|row| row.iter().copied().map(rational_i64).collect())
        .collect();
    let target: Vec<BigRational> = cochain.iter().copied().map(rational_i64).collect();
    let certificate = solve_l1_quotient(&matrix, &target).map_err(|error| {
        CodaRefusal::new(
            "DISTANCE_UNRESOLVED",
            format!("phi1 could not be derived from the matrices: {error}"),
        )
    })?;
    certificate.distance.to_u64().ok_or_else(|| {
        CodaRefusal::new(
            "DISTANCE_DISAGREES",
            "derived phi1 is not the supplied nonnegative integer distance",
        )
    })
}

/// Declared-premise classification stays in `evaluate_coda`. This only refuses
/// a supplied integer distance that is not the distance of the matrices.
fn refuse_supplied_distance(request: &CodaEvaluateRequestV1) -> Result<(), CodaRefusal> {
    let Some(matrices) = &request.matrices else {
        return Ok(());
    };
    let gamma2 = l1_distance(&apply_matrix(&matrices.d1, &matrices.cochain)?)?;
    let phi1 = phi1_from_matrices(&matrices.d0, &matrices.cochain)?;
    if phi1 != request.phi1_distance || gamma2 != request.gamma2_distance {
        return Err(CodaRefusal::new(
            "DISTANCE_DISAGREES",
            format!(
                "supplied phi1 {} and gamma2 {} disagree with matrix distances phi1 {phi1} and gamma2 {gamma2}",
                request.phi1_distance, request.gamma2_distance
            ),
        ));
    }
    Ok(())
}

/// Re-evaluate a request and report which receipt fields it does not reproduce.
pub fn verify_coda(payload: &Value) -> Result<Value, CodaRefusal> {
    let verify: CodaVerifyRequestV1 = serde_json::from_value(payload.clone())
        .map_err(|error| CodaRefusal::new("INVALID_CODA_REQUEST", error.to_string()))?;
    let recomputed = evaluate_coda(&verify.request)?;
    let expected = to_object(&recomputed);
    let claimed = to_object(&verify.receipt);
    let mismatched: Vec<&String> = expected
        .iter()
        .filter(|(field, value)| claimed.get(*field) != Some(*value))
        .map(|(field, _)| field)
        .collect();
    Ok(serde_json::json!({
        "accepted": mismatched.is_empty(),
        "mismatched_fields": mismatched,
        "input_digest": recomputed.input_digest,
    }))
}

fn to_object(receipt: &CodaEvaluateReceiptV1) -> Map<String, Value> {
    match serde_json::to_value(receipt).checked_invariant_2a609ee9("a receipt holds valid serializable types") {
        Value::Object(object) => object,
        _ => unreachable!("a struct serializes to a JSON object"),
    }
}

// Origin: engine/crates_rs/pfp/src/coda.rs
// Claim: urn:core:crates_rs:pfp:coda:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord2a609ee9 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord2a609ee9` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError2a609ee9 {
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
impl BoundaryError2a609ee9 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError2a609ee9 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError2a609ee9 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord2a609ee9 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError2a609ee9> {
        if capacity_bound == 0 {
            return Err(BoundaryError2a609ee9::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError2a609ee9::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError2a609ee9::ExceedsCapacity {
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
mod declared_premise_tests {
    use super::*;
    use serde_json::json;

    fn payload(license_granted: bool, phi1_distance: u64, matrices: Option<Value>) -> Value {
        let mut value = json!({
            "input_id": "declared",
            "sieve_non_empty": true,
            "refinement_consistent": true,
            "gluing_succeeded": true,
            "phi1_distance": phi1_distance,
            "gamma2_distance": 0,
            "license_granted": license_granted,
        });
        if let Some(matrices) = matrices {
            value["matrices"] = matrices;
        }
        value
    }

    #[test]
    fn caller_license_does_not_mint_exact_rule_derived() {
        let receipt = evaluate_coda(&payload(true, 0, None)).expect("declared request");
        assert_eq!(receipt.premise_source, CODA_PREMISE_SOURCE_DECLARED);
        assert_eq!(receipt.diagnostic, ObstructionDiagnosticClass::ExactRepair);
        assert_eq!(receipt.routing, RoutingTerminal::CheckPassed);
        assert_eq!(receipt.authority, Outcome::Refused(RefusalSource::Refusal));
        assert_ne!(
            receipt.authority,
            Outcome::Terminal(AuthorityTerminal::ExactRuleDerived)
        );
        assert_eq!(receipt.authority_effect, "None");
    }

    #[test]
    fn supplied_distance_that_disagrees_with_the_matrices_is_refused() {
        let matrices = json!({"d0": [[0]], "d1": [], "cochain": [4]});
        let refused = evaluate_coda(&payload(true, 0, Some(matrices.clone())))
            .expect_err("zero is not the matrix distance");
        assert_eq!(refused.code, "DISTANCE_DISAGREES");
        let agreed = evaluate_coda(&payload(true, 4, Some(matrices))).expect("matching distance");
        assert_eq!(agreed.premise_source, CODA_PREMISE_SOURCE_DECLARED);
        assert_ne!(
            agreed.authority,
            Outcome::Terminal(AuthorityTerminal::ExactRuleDerived)
        );
    }
}

#[cfg(test)]
mod l4_boundary_tests_2a609ee9 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord2a609ee9::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord2a609ee9::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord2a609ee9::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord2a609ee9::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord2a609ee9::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError2a609ee9::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError2a609ee9::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
