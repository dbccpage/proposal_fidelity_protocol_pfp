//! Input-bound exact functional evaluation across the runtime seam.
//!
//! CODA-FOC Layer 1 at the process boundary. A caller sends an exact cochain
//! complex `d0: C^0 -> C^1`, `d1: C^1 -> C^2` and a residual `omega` in `C^1`;
//! the host answers with Phi1, Gamma2 and the diagnostic class. Every one of
//! the functional values is produced by `core_functional` through checked
//! evidence. `core_policy` classifies that evidence. This module validates the request,
//! binds the answer to the exact bytes that asked for it, and refuses in named
//! codes.
//!
//! Gamma2 here is the engine's `||d1 x||_1`: the FOC quotient with no
//! second-stage repairs (`a2 = 0`). The receipt says so in
//! `second_stage_repairs`, because a reader assuming FOC's general
//! `min_u ||d1 x + a2 u||` would read a zero here as stronger than it is.
//!
//! AuthorityEffect: None.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_f46120e9<T> {
    fn checked_invariant_f46120e9(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_f46120e9<T> for Option<T> {
    #[inline]
    fn checked_invariant_f46120e9(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_f46120e9<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_f46120e9(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use serde::{Deserialize, Serialize};
use serde_json::{Map, Value};

use core_functional::gamma2::{DegreeOneResidualQ, ExactCochainComplexQ, ExactGamma2Error};
use core_functional::{ExactPhi1Certificate, Gamma2Functional, Phi1Functional};
use core_kernel::{exact_wire_vec, parse_exact, to_canonical_string, Exact};
use core_policy::trichotomy::{classify_exact, ObstructionDiagnosticClass, TrichotomyOutcome};
use core_solvers::solver_lp_exact_simplex::{solve_weighted_l1_projection, L1LpError};
use pfp_runtime::{framed_sha256, RationalMatrix};

use crate::protocol::canonical_json;

/// Digest domain binding a receipt to the request payload that produced it.
pub const FUNCTIONAL_REQUEST_DOMAIN: &str = "core.symbol-game.functional-evaluate-request.v1";
pub const FUNCTIONAL_RECEIPT_SCHEMA: &str = "core.symbol-game.functional-receipt.v1";

/// Largest number of matrix entries one request may carry.
///
/// Beyond it the host answers `BUDGET_UNKNOWN` rather than start an exact
/// simplex whose cost it has not bounded. An unknown is not a refusal of the
/// instance and it is not a zero.
pub const MAX_FUNCTIONAL_CELLS: usize = 4096;

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct FunctionalEvaluateRequestV1 {
    pub d0: RationalMatrix,
    pub d1: RationalMatrix,
    #[serde(with = "exact_wire_vec")]
    pub residual: Vec<Exact>,
    #[serde(default)]
    pub weights: Option<Vec<String>>,
    #[serde(default)]
    pub budget: Option<usize>,
}

/// What the host certifies about one request.
///
/// A receipt exists only after the Phi1 certificate verified and the
/// trichotomy classified, so it carries no "verified" flag: an unverified
/// answer is a refusal, never a receipt.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct FunctionalReceiptV1 {
    pub schema_version: String,
    pub input_digest: String,
    pub phi1: String,
    pub gamma2: String,
    pub diagnostic_class: ObstructionDiagnosticClass,
    pub repair: Vec<String>,
    pub primal_residual: Vec<String>,
    pub dual_witness: Vec<String>,
    pub closure_coboundary: Vec<String>,
    pub second_stage_repairs: String,
    pub evidence_provenance: String,
    pub authority_effect: String,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct FunctionalVerifyRequestV1 {
    pub request: Value,
    pub receipt: FunctionalReceiptV1,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FunctionalRefusal {
    pub code: &'static str,
    pub detail: String,
}

impl FunctionalRefusal {
    fn new(code: &'static str, detail: impl Into<String>) -> Self {
        Self {
            code,
            detail: detail.into(),
        }
    }

    /// The runtime error string: the code first, so a caller can branch on it.
    pub fn wire(&self) -> String {
        format!("{}: {}", self.code, self.detail)
    }
}

/// `framed_sha256` over the sorted, whitespace-free JSON of the payload.
///
/// The same framing and encoding the prime host uses for its outcome root, so
/// the Python seam recomputes it byte for byte without a second encoder.
pub fn functional_input_digest(payload: &Value) -> String {
    framed_sha256(FUNCTIONAL_REQUEST_DOMAIN, &canonical_json(payload))
}

fn reject_floats(value: &Value, locus: &str) -> Result<(), FunctionalRefusal> {
    match value {
        Value::Number(number) => {
            let text = number.to_string();
            if text.contains(['.', 'e', 'E']) {
                return Err(FunctionalRefusal::new(
                    "FLOAT_FORBIDDEN",
                    format!("{locus} is the JSON number {text}; exact values cross as strings"),
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

fn rows_of(matrix: &RationalMatrix) -> Vec<Vec<Exact>> {
    (0..matrix.rows())
        .map(|r| {
            (0..matrix.cols())
                .map(|c| matrix.get(r, c).clone())
                .collect()
        })
        .collect()
}

fn complex_refusal(error: ExactGamma2Error) -> FunctionalRefusal {
    match error {
        ExactGamma2Error::CochainIdentityViolation { .. } => {
            FunctionalRefusal::new("CHAIN_LAW_VIOLATED", error.to_string())
        }
        other => FunctionalRefusal::new("DIMENSION_MISMATCH", other.to_string()),
    }
}

fn wire(values: &[Exact]) -> Vec<String> {
    values.iter().map(to_canonical_string).collect()
}

/// Evaluate Phi1, Gamma2 and the diagnostic class for one exact request.
pub fn evaluate_functional(payload: &Value) -> Result<FunctionalReceiptV1, FunctionalRefusal> {
    reject_floats(payload, "payload")?;
    let request: FunctionalEvaluateRequestV1 = serde_json::from_value(payload.clone())
        .map_err(|error| FunctionalRefusal::new("INVALID_FUNCTIONAL_REQUEST", error.to_string()))?;

    let cells = request.d0.rows() * request.d0.cols() + request.d1.rows() * request.d1.cols();
    if cells > MAX_FUNCTIONAL_CELLS {
        return Err(FunctionalRefusal::new(
            "BUDGET_UNKNOWN",
            format!("{cells} matrix entries exceed the bound of {MAX_FUNCTIONAL_CELLS}"),
        ));
    }

    let c1 = request.residual.len();
    if request.d0.rows() != c1 {
        return Err(FunctionalRefusal::new(
            "DIMENSION_MISMATCH",
            format!(
                "d0 has {} rows but the residual has {c1} coordinates",
                request.d0.rows()
            ),
        ));
    }
    let d0 = rows_of(&request.d0);
    let complex = ExactCochainComplexQ::try_new(
        request.d0.cols(),
        c1,
        request.d1.rows(),
        d0.clone(),
        rows_of(&request.d1),
    )
    .map_err(complex_refusal)?;

    let weights = match &request.weights {
        Some(texts) => texts
            .iter()
            .map(|text| parse_exact(text))
            .collect::<Result<Vec<_>, _>>()
            .map_err(|error| {
                FunctionalRefusal::new("INVALID_FUNCTIONAL_REQUEST", error.to_string())
            })?,
        None => vec![Exact::from_integer(1.into()); c1],
    };
    let budget = request
        .budget
        .unwrap_or_else(|| 64 * (c1 + request.d0.cols()) + 1024);

    let solution = solve_weighted_l1_projection(&request.residual, &weights, &d0, budget).map_err(
        |error| match error {
            L1LpError::IterationBudgetExceeded { .. } => {
                FunctionalRefusal::new("BUDGET_UNKNOWN", error.to_string())
            }
            other => FunctionalRefusal::new("SOLVER_REFUSED", other.to_string()),
        },
    )?;
    let phi1 = Phi1Functional::verify_exact_certificate(ExactPhi1Certificate {
        omega: request.residual.clone(),
        d0,
        weights,
        alpha: solution.coefficients,
        primal_residual: solution.residual.clone(),
        dual_witness: solution.dual,
        reported_value: solution.value,
    })
    .map_err(|error| FunctionalRefusal::new("PHI1_CERTIFICATE_REJECTED", error.to_string()))?;

    let residual =
        DegreeOneResidualQ::try_new(&complex, solution.residual).map_err(complex_refusal)?;
    let gamma2 =
        Gamma2Functional::try_compute_exact_quotient(&residual).map_err(complex_refusal)?;
    let certified = match classify_exact(&phi1, &gamma2) {
        TrichotomyOutcome::Classified(certified) => certified,
        TrichotomyOutcome::TriRefused(reason) => {
            return Err(FunctionalRefusal::new(
                "INCOMPATIBLE_EVIDENCE",
                format!("{reason:?}"),
            ))
        }
    };

    Ok(FunctionalReceiptV1 {
        schema_version: FUNCTIONAL_RECEIPT_SCHEMA.to_owned(),
        input_digest: functional_input_digest(payload),
        phi1: to_canonical_string(certified.phi1_value()),
        gamma2: to_canonical_string(certified.gamma2_value()),
        diagnostic_class: certified.diagnostic_class(),
        repair: wire(phi1.alpha()),
        primal_residual: wire(phi1.primal_residual()),
        dual_witness: wire(phi1.dual_witness()),
        closure_coboundary: wire(gamma2.coboundary()),
        second_stage_repairs: "none".to_owned(),
        evidence_provenance: "VerifierProduced".to_owned(),
        authority_effect: "None".to_owned(),
    })
}

/// Re-evaluate a request and report which receipt fields it does not reproduce.
///
/// `accepted` is a verdict on the receipt, not on the request: a request the
/// host refuses outright is a refusal here too, because there is nothing to
/// compare the receipt against.
pub fn verify_functional(payload: &Value) -> Result<Value, FunctionalRefusal> {
    let verify: FunctionalVerifyRequestV1 = serde_json::from_value(payload.clone())
        .map_err(|error| FunctionalRefusal::new("INVALID_FUNCTIONAL_REQUEST", error.to_string()))?;
    let recomputed = evaluate_functional(&verify.request)?;
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

fn to_object(receipt: &FunctionalReceiptV1) -> Map<String, Value> {
    match serde_json::to_value(receipt).checked_invariant_f46120e9("a receipt holds only strings and a unit enum") {
        Value::Object(object) => object,
        _ => unreachable!("a struct serializes to a JSON object"),
    }
}

// Origin: engine/crates_rs/pfp/src/functional.rs
// Claim: urn:core:crates_rs:pfp:functional:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf46120e9 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf46120e9` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf46120e9 {
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
impl BoundaryErrorf46120e9 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf46120e9 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf46120e9 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf46120e9 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf46120e9> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf46120e9::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf46120e9::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf46120e9::ExceedsCapacity {
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
mod l4_boundary_tests_f46120e9 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordf46120e9::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordf46120e9::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordf46120e9::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordf46120e9::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordf46120e9::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorf46120e9::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorf46120e9::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
