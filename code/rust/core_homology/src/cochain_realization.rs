//! Exact finite admission from active presentation demands to a cochain window.
//!
//! Rust face of `engine/kernel/cochain_realization.py`.

use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::BTreeSet;
use thiserror::Error;

pub type IntegerVector = Vec<i64>;
pub type IntegerMatrix = Vec<Vec<i64>>;

#[derive(Debug, Error, PartialEq, Eq)]
pub enum CochainRealizationError {
    #[error("validation error: {0}")]
    Validation(String),

    #[error("cochain window violates d1 * d0 = 0")]
    BoundaryCompositionNonZero,

    #[error("coordinate binding mismatch: {0}")]
    BindingMismatch(String),

    #[error("refusal: {code} - {message}")]
    Refusal { code: String, message: String },
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ClosureStatus {
    #[serde(rename = "Closed")]
    Closed,
    #[serde(rename = "ActiveClosureFailure")]
    ActiveClosureFailure,
}

pub fn canonical_sha256(domain: &str, payload: &Value) -> Result<String, CochainRealizationError> {
    let mut canonical_payload = payload.clone();
    canonical_payload.sort_all_objects();
    let raw = serde_json::to_string(&canonical_payload)
        .map_err(|e| CochainRealizationError::Validation(e.to_string()))?;
    let mut hasher = Sha256::new();
    hasher.update(domain.as_bytes());
    hasher.update(b":");
    hasher.update(raw.as_bytes());
    Ok(format!("sha256:{}", hex::encode(hasher.finalize())))
}

pub fn mat_vec(matrix: &[Vec<i64>], vector: &[i64]) -> IntegerVector {
    matrix
        .iter()
        .map(|row| row.iter().zip(vector.iter()).map(|(a, b)| a * b).sum())
        .collect()
}

pub fn mat_mul(left: &[Vec<i64>], right: &[Vec<i64>]) -> IntegerMatrix {
    let right_cols = if right.is_empty() { 0 } else { right[0].len() };
    let mut result = Vec::with_capacity(left.len());
    for row in left {
        let mut row_res = Vec::with_capacity(right_cols);
        for col in 0..right_cols {
            let mut sum = 0i64;
            for inner in 0..right.len() {
                sum += row[inner] * right[inner][col];
            }
            row_res.push(sum);
        }
        result.push(row_res);
    }
    result
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CochainWindowV1 {
    pub repair_parameter_ids: Vec<String>,
    pub demand_coordinate_ids: Vec<String>,
    pub face_ids: Vec<String>,
    pub d0: IntegerMatrix,
    pub d1: IntegerMatrix,
    #[serde(default = "default_authority")]
    pub authority_effect: String,
}

fn default_authority() -> String {
    "None".into()
}

impl CochainWindowV1 {
    pub fn new(
        repair_parameter_ids: Vec<String>,
        demand_coordinate_ids: Vec<String>,
        face_ids: Vec<String>,
        d0: IntegerMatrix,
        d1: IntegerMatrix,
    ) -> Result<Self, CochainRealizationError> {
        if demand_coordinate_ids.is_empty() {
            return Err(CochainRealizationError::Validation(
                "a cochain realization needs at least one C1 coordinate".into(),
            ));
        }

        Self::ensure_unique(&repair_parameter_ids, "repair_parameter_ids must not contain duplicates")?;
        Self::ensure_unique(&demand_coordinate_ids, "demand_coordinate_ids must not contain duplicates")?;
        Self::ensure_unique(&face_ids, "face_ids must not contain duplicates")?;
        Self::ensure_shape(
            &d0,
            demand_coordinate_ids.len(),
            repair_parameter_ids.len(),
            "d0",
            "demand_coordinate_ids",
            "repair_parameter_ids",
        )?;
        Self::ensure_shape(
            &d1,
            face_ids.len(),
            demand_coordinate_ids.len(),
            "d1",
            "face_ids",
            "demand_coordinate_ids",
        )?;
        Self::ensure_zero_product(&d1, &d0)?;

        Ok(Self {
            repair_parameter_ids,
            demand_coordinate_ids,
            face_ids,
            d0,
            d1,
            authority_effect: "None".into(),
        })
    }

    fn ensure_unique(ids: &[String], msg: &'static str) -> Result<(), CochainRealizationError> {
        let mut seen = BTreeSet::new();
        for id in ids {
            if !seen.insert(id.clone()) {
                return Err(CochainRealizationError::Validation(msg.into()));
            }
        }
        Ok(())
    }

    fn ensure_shape(
        mat: &IntegerMatrix,
        expected_rows: usize,
        expected_cols: usize,
        mat_name: &str,
        row_label: &str,
        col_label: &str,
    ) -> Result<(), CochainRealizationError> {
        if mat.len() != expected_rows {
            return Err(CochainRealizationError::Validation(format!(
                "{} row count {} must match {} length {}",
                mat_name,
                mat.len(),
                row_label,
                expected_rows
            )));
        }
        for row in mat {
            if row.len() != expected_cols {
                return Err(CochainRealizationError::Validation(format!(
                    "{} col count {} must match {} length {}",
                    mat_name,
                    row.len(),
                    col_label,
                    expected_cols
                )));
            }
        }
        Ok(())
    }

    fn ensure_zero_product(d1: &IntegerMatrix, d0: &IntegerMatrix) -> Result<(), CochainRealizationError> {
        // Exact verification of d1 * d0 == 0
        let prod = mat_mul(d1, d0);
        for row in &prod {
            for &val in row {
                if val != 0 {
                    return Err(CochainRealizationError::BoundaryCompositionNonZero);
                }
            }
        }
        Ok(())
    }

    pub fn to_canonical(&self) -> Value {
        json!({
            "repair_parameter_ids": self.repair_parameter_ids,
            "demand_coordinate_ids": self.demand_coordinate_ids,
            "face_ids": self.face_ids,
            "d0": self.d0,
            "d1": self.d1,
            "authority_effect": self.authority_effect,
        })
    }

    pub fn canonical_id(&self) -> Result<String, CochainRealizationError> {
        canonical_sha256("core.cochain-realization.window.v1", &self.to_canonical())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CochainRealizationV1 {
    pub presentation_id: String,
    pub obstruction_ids: Vec<String>,
    pub omega: IntegerVector,
    pub window: CochainWindowV1,
    #[serde(default = "default_authority")]
    pub authority_effect: String,
}

impl CochainRealizationV1 {
    pub fn new(
        presentation_id: &str,
        obstruction_ids: Vec<String>,
        omega: IntegerVector,
        window: CochainWindowV1,
    ) -> Result<Self, CochainRealizationError> {
        if obstruction_ids.is_empty() {
            return Err(CochainRealizationError::Validation(
                "obstruction_ids must be non-empty".into(),
            ));
        }
        let mut seen = BTreeSet::new();
        for id in &obstruction_ids {
            if !seen.insert(id.clone()) {
                return Err(CochainRealizationError::Validation(
                    "obstruction_ids must be unique".into(),
                ));
            }
        }
        if omega.len() != obstruction_ids.len() {
            return Err(CochainRealizationError::Validation(
                "omega length must match obstruction_ids length".into(),
            ));
        }
        if omega.contains(&0) {
            return Err(CochainRealizationError::Validation(
                "each active obstruction coordinate must have a nonzero faithful coefficient"
                    .into(),
            ));
        }
        if window.demand_coordinate_ids != obstruction_ids {
            return Err(CochainRealizationError::BindingMismatch(
                "C1 coordinate order must equal the admitted obstruction order".into(),
            ));
        }

        Ok(Self {
            presentation_id: presentation_id.to_string(),
            obstruction_ids,
            omega,
            window,
            authority_effect: "None".into(),
        })
    }

    pub fn to_canonical(&self) -> Result<Value, CochainRealizationError> {
        let win_id = self.window.canonical_id()?;
        Ok(json!({
            "presentation_id": self.presentation_id,
            "obstruction_ids": self.obstruction_ids,
            "omega": self.omega,
            "window_id": win_id,
            "authority_effect": self.authority_effect,
        }))
    }

    pub fn canonical_id(&self) -> Result<String, CochainRealizationError> {
        let canon = self.to_canonical()?;
        canonical_sha256("core.cochain-realization.realization.v1", &canon)
    }

    pub fn closure(&self) -> IntegerVector {
        mat_vec(&self.window.d1, &self.omega)
    }

    pub fn closure_of(&self, cochain: &[i64]) -> IntegerVector {
        mat_vec(&self.window.d1, cochain)
    }

    pub fn closure_status(&self) -> ClosureStatus {
        let c = self.closure();
        if c.iter().all(|&v| v == 0) {
            ClosureStatus::Closed
        } else {
            ClosureStatus::ActiveClosureFailure
        }
    }

    pub fn repaired(&self, parameters: &[i64]) -> IntegerVector {
        let correction = mat_vec(&self.window.d0, parameters);
        self.omega
            .iter()
            .zip(correction.iter())
            .map(|(w, delta)| w + delta)
            .collect()
    }

    pub fn exact_repair_witness(&self, parameters: &[i64]) -> bool {
        self.repaired(parameters).iter().all(|&v| v == 0)
    }
}

// Origin: engine/crates_rs/core_homology/src/cochain_realization.rs
// Claim: urn:core:crates_rs:core-homology:cochain-realization:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod canonical_hash_tests {
    use super::canonical_sha256;
    use serde_json::{json, Map, Value};

    #[test]
    fn canonical_sha256_sorts_nested_maps_without_reordering_arrays() {
        fn payload(reverse: bool) -> Value {
            let mut nested = Map::new();
            let pairs = if reverse {
                [("z", 1), ("a", 2)]
            } else {
                [("a", 2), ("z", 1)]
            };
            for (key, value) in pairs {
                nested.insert(key.into(), json!(value));
            }
            let array = Value::Array(vec![Value::Object(nested), json!(9)]);
            let mut outer = Map::new();
            if reverse {
                outer.insert("z".into(), json!(0));
                outer.insert("a".into(), array);
            } else {
                outer.insert("a".into(), array);
                outer.insert("z".into(), json!(0));
            }
            Value::Object(outer)
        }

        let first = payload(true);
        let second = payload(false);
        let original_bytes = serde_json::to_vec(&first).unwrap();
        assert_eq!(first, second);
        let digest = canonical_sha256("core.test", &first).unwrap();
        assert_eq!(digest, canonical_sha256("core.test", &second).unwrap());
        // SHA-256 of core.test:{"a":[{"a":2,"z":1},9],"z":0}.
        assert_eq!(
            digest,
            "sha256:313091eac13c51f1d7324dd237ffc4d68c1f72c87e258533feeced122b8c9d05"
        );
        assert_eq!(original_bytes, serde_json::to_vec(&first).unwrap());
        assert_ne!(
            canonical_sha256("core.test", &json!([1, 2])).unwrap(),
            canonical_sha256("core.test", &json!([2, 1])).unwrap()
        );
        assert_ne!(digest, canonical_sha256("core.other", &second).unwrap());
    }
}
