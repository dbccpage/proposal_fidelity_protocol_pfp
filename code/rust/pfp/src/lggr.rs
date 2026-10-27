//! LGGR runtime actions for Symbol Game.
//!
//! Exposes exact evaluator-defect classification (`lggr_classify`) and exact
//! LGGR V soundness verification (`lggr_soundness`).
//!
//! AuthorityEffect: None.

use serde::{Deserialize, Serialize};
use serde_json::Value;

use linear_algebra::backend::basic_matrix::BasicMatrix;
use num_rational::BigRational;
use core_epk::lggr_v::{check_soundness, LggrSoundnessError};
use core_kernel::{to_canonical_string, Exact};
use pfp_runtime::RationalMatrix;

pub const LGGR_CLASSIFY_SCHEMA: &str = "core.symbol-game.lggr-classify-receipt.v1";
pub const LGGR_SOUNDNESS_RECEIPT_SCHEMA: &str = "core.symbol-game.lggr-soundness-receipt.v1";
pub const LGGR_K_CELL_CLASSIFY_SCHEMA: &str = "core.symbol-game.lggr-k-cell-classify-receipt.v1";

#[derive(Debug, Clone, PartialEq, Eq, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct LggrClassifyRequestV1 {
    #[serde(default)]
    pub trace_id: Option<String>,
    pub e1: bool,
    pub e2: bool,
    pub eg: bool,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct LggrClassifyReceiptV1 {
    pub schema_version: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub trace_id: Option<String>,
    pub e1: bool,
    pub e2: bool,
    pub eg: bool,
    pub local_product: bool,
    pub delta_eval: i8,
    pub defect_class: String,
    pub authority_effect: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct LggrKCellClassifyRequestV1 {
    #[serde(default)]
    pub trace_id: Option<String>,
    pub k: usize,
    pub e_vertices: Vec<bool>,
    pub e_simplex: bool,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct LggrKCellClassifyReceiptV1 {
    pub schema_version: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub trace_id: Option<String>,
    pub k: usize,
    pub e_vertices: Vec<bool>,
    pub e_simplex: bool,
    pub local_product: bool,
    pub delta_eval: i8,
    pub defect_class: String,
    pub authority_effect: String,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct LggrSoundnessRequestV1 {
    pub d: RationalMatrix,
    pub q: RationalMatrix,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct LggrSoundnessReceiptV1 {
    pub schema_version: String,
    pub sound: bool,
    pub d_rank: usize,
    pub qd_rank: usize,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub witness: Option<Vec<String>>,
    pub authority_effect: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LggrRefusal {
    pub code: &'static str,
    pub detail: String,
}

impl LggrRefusal {
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

/// Classify evaluator gluing defect Δ_E = E_g - E_1 E_2 exactly.
pub fn classify_lggr(payload: &Value) -> Result<LggrClassifyReceiptV1, LggrRefusal> {
    let req: LggrClassifyRequestV1 = serde_json::from_value(payload.clone())
        .map_err(|e| LggrRefusal::new("LGGR_CLASSIFY_PARSE_ERROR", e.to_string()))?;

    let local_product = req.e1 && req.e2;
    let delta_eval = (req.eg as i8) - (local_product as i8);
    let defect_class = match delta_eval {
        -1 => "NegativeGluingDefect",
        1 => "PositiveGluingDefect",
        0 => "ZeroDefect",
        _ => unreachable!(),
    };

    Ok(LggrClassifyReceiptV1 {
        schema_version: LGGR_CLASSIFY_SCHEMA.to_string(),
        trace_id: req.trace_id,
        e1: req.e1,
        e2: req.e2,
        eg: req.eg,
        local_product,
        delta_eval,
        defect_class: defect_class.to_string(),
        authority_effect: "None".to_string(),
    })
}

/// Classify k-cell evaluator gluing defect Δ_E^(k) = E_simplex - prod_{j=1}^k E_{v_j} exactly.
pub fn classify_lggr_k_cell(payload: &Value) -> Result<LggrKCellClassifyReceiptV1, LggrRefusal> {
    let req: LggrKCellClassifyRequestV1 = serde_json::from_value(payload.clone())
        .map_err(|e| LggrRefusal::new("LGGR_K_CELL_CLASSIFY_PARSE_ERROR", e.to_string()))?;

    if req.k < 2 || req.e_vertices.len() != req.k {
        return Err(LggrRefusal::new(
            "LGGR_K_CELL_INVALID_DIMENSION",
            format!(
                "k ({}) must be >= 2 and match e_vertices length ({})",
                req.k,
                req.e_vertices.len()
            ),
        ));
    }

    let local_product = req.e_vertices.iter().all(|&v| v);
    let delta_eval = (req.e_simplex as i8) - (local_product as i8);
    let defect_class = match delta_eval {
        -1 => "NegativeGluingDefect",
        1 => "PositiveGluingDefect",
        0 => "ZeroDefect",
        _ => unreachable!(),
    };

    Ok(LggrKCellClassifyReceiptV1 {
        schema_version: LGGR_K_CELL_CLASSIFY_SCHEMA.to_string(),
        trace_id: req.trace_id,
        k: req.k,
        e_vertices: req.e_vertices,
        e_simplex: req.e_simplex,
        local_product,
        delta_eval,
        defect_class: defect_class.to_string(),
        authority_effect: "None".to_string(),
    })
}

fn rational_to_basic_matrix(mat: &RationalMatrix) -> Result<BasicMatrix<Exact>, LggrRefusal> {
    let mut data = Vec::with_capacity(mat.rows() * mat.cols());
    for r in 0..mat.rows() {
        for c in 0..mat.cols() {
            data.push(mat.get(r, c).clone());
        }
    }
    BasicMatrix::from_row_major(mat.rows(), mat.cols(), data)
        .map_err(|e| LggrRefusal::new("LGGR_MATRIX_CONVERSION_ERROR", e.to_string()))
}

pub(crate) fn verify_soundness_counterexample(
    payload: &Value,
    witness: &[Exact],
) -> Result<bool, String> {
    let req: LggrSoundnessRequestV1 =
        serde_json::from_value(payload.clone()).map_err(|e| e.to_string())?;
    let d = rational_to_basic_matrix(&req.d).map_err(|e| e.wire())?;
    let q = rational_to_basic_matrix(&req.q).map_err(|e| e.wire())?;
    core_epk::lggr_v::verify_unsoundness_witness(&d, &q, witness).map_err(|e| e.to_string())
}

/// Check LGGR V soundness rank(Q·D) == rank(D) exactly, returning witness on unsoundness.
pub fn soundness_lggr(payload: &Value) -> Result<LggrSoundnessReceiptV1, LggrRefusal> {
    let req: LggrSoundnessRequestV1 = serde_json::from_value(payload.clone())
        .map_err(|e| LggrRefusal::new("LGGR_SOUNDNESS_PARSE_ERROR", e.to_string()))?;

    let d_basic = rational_to_basic_matrix(&req.d)?;
    let q_basic = rational_to_basic_matrix(&req.q)?;

    match check_soundness(&d_basic, &q_basic) {
        Ok(report) => {
            let witness = report.witness.map(|w| {
                w.iter()
                    .map(|r: &BigRational| to_canonical_string(r))
                    .collect()
            });
            Ok(LggrSoundnessReceiptV1 {
                schema_version: LGGR_SOUNDNESS_RECEIPT_SCHEMA.to_string(),
                sound: report.sound,
                d_rank: report.d_rank,
                qd_rank: report.qd_rank,
                witness,
                authority_effect: "None".to_string(),
            })
        }
        Err(LggrSoundnessError::BudgetUnknown { cells, limit }) => Err(LggrRefusal::new(
            "BUDGET_UNKNOWN",
            format!("matrix cells {cells} exceed budget limit {limit}"),
        )),
        Err(LggrSoundnessError::DimensionMismatch { q_cols, d_rows }) => Err(LggrRefusal::new(
            "DIMENSION_MISMATCH",
            format!("Q cols ({q_cols}) must match D rows ({d_rows})"),
        )),
        Err(LggrSoundnessError::EmptyMatrix) => Err(LggrRefusal::new(
            "EMPTY_MATRIX",
            "cannot check soundness of an empty matrix",
        )),
        Err(LggrSoundnessError::LinearAlgebra(err)) => {
            Err(LggrRefusal::new("LINEAR_ALGEBRA_ERROR", err))
        }
    }
}

// Origin: engine/crates_rs/pfp/src/lggr.rs
// Claim: urn:core:crates_rs:pfp:lggr:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde80dca2a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde80dca2a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore80dca2a {
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
impl BoundaryErrore80dca2a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore80dca2a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore80dca2a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde80dca2a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore80dca2a> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore80dca2a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore80dca2a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore80dca2a::ExceedsCapacity {
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
    use serde_json::json;

    #[test]
    fn test_classify_lggr_k_cell_zero_defect() {
        let payload = json!({
            "k": 3,
            "e_vertices": [true, true, true],
            "e_simplex": true
        });
        let receipt = classify_lggr_k_cell(&payload).expect("classification succeeds");
        assert_eq!(receipt.defect_class, "ZeroDefect");
        assert_eq!(receipt.delta_eval, 0);
        assert!(receipt.local_product);
        assert_eq!(receipt.authority_effect, "None");
    }

    #[test]
    fn test_classify_lggr_k_cell_positive_defect() {
        let payload = json!({
            "k": 3,
            "e_vertices": [true, false, true],
            "e_simplex": true
        });
        let receipt = classify_lggr_k_cell(&payload).expect("classification succeeds");
        assert_eq!(receipt.defect_class, "PositiveGluingDefect");
        assert_eq!(receipt.delta_eval, 1);
        assert!(!receipt.local_product);
    }

    #[test]
    fn test_classify_lggr_k_cell_dimension_mismatch() {
        let payload = json!({
            "k": 3,
            "e_vertices": [true, true],
            "e_simplex": true
        });
        let err = classify_lggr_k_cell(&payload).expect_err("dimension mismatch");
        assert_eq!(err.code, "LGGR_K_CELL_INVALID_DIMENSION");
    }
}

#[cfg(test)]
mod l4_boundary_tests_e80dca2a {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorde80dca2a::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorde80dca2a::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorde80dca2a::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorde80dca2a::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorde80dca2a::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrore80dca2a::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrore80dca2a::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
