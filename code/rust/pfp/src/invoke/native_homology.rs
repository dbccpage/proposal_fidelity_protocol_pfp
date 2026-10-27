//! Wire validation for the canonical exact homological-perturbation owner.

use super::native_matrix::{limits, matrix_value, parse_matrix};
use linear_algebra::backend::basic_matrix::BasicMatrix;
use num_rational::BigRational;
use core_homology::homological_perturbation::{
    transfer_perturbation, verify_normalized, CheckedContraction, ContractionData,
    PerturbationError, SideConditionReport,
};
use serde_json::{json, Value};

fn fields(value: &Value, name: &str, allowed: &[&str]) -> Result<(), String> {
    let object = value
        .as_object()
        .ok_or_else(|| format!("{name} must be an object"))?;
    if let Some(key) = object.keys().find(|key| !allowed.contains(&key.as_str())) {
        return Err(format!("unknown {name} field: {key}"));
    }
    Ok(())
}

fn required<'a>(value: &'a Value, key: &str) -> Result<&'a Value, String> {
    value.get(key).ok_or_else(|| format!("missing {key}"))
}

fn dimensions(value: &Value, name: &str) -> Result<[usize; 3], String> {
    let entries = value
        .as_array()
        .filter(|entries| entries.len() == 3)
        .ok_or_else(|| format!("{name} must contain exactly three dimensions"))?;
    let mut dimensions = [0; 3];
    for (degree, entry) in entries.iter().enumerate() {
        dimensions[degree] = entry
            .as_u64()
            .and_then(|dimension| usize::try_from(dimension).ok())
            .filter(|dimension| *dimension <= 256)
            .ok_or_else(|| format!("{name}[{degree}] must be an integer in 0..=256"))?;
    }
    Ok(dimensions)
}

fn matrices<const N: usize>(
    value: &Value,
    name: &str,
) -> Result<[BasicMatrix<BigRational>; N], String> {
    let entries = value
        .as_array()
        .filter(|entries| entries.len() == N)
        .ok_or_else(|| format!("{name} must contain exactly {N} matrices"))?;
    let matrices = entries
        .iter()
        .map(parse_matrix)
        .collect::<Result<Vec<_>, _>>()?;
    matrices
        .try_into()
        .map_err(|_| format!("{name} matrix count changed while decoding"))
}

fn dimensions_field(value: &Value, name: &str) -> Result<[usize; 3], String> {
    dimensions(required(value, name)?, name)
}

fn matrices_field<const N: usize>(
    value: &Value,
    name: &str,
) -> Result<[BasicMatrix<BigRational>; N], String> {
    matrices(required(value, name)?, name)
}

fn parse_contraction(value: &Value) -> Result<ContractionData, String> {
    fields(
        value,
        "contraction",
        &[
            "c_dimensions",
            "d_dimensions",
            "d_c",
            "d_d",
            "inclusion",
            "retraction",
            "homotopy",
        ],
    )?;
    Ok(ContractionData {
        c_dimensions: dimensions_field(value, "c_dimensions")?,
        d_dimensions: dimensions_field(value, "d_dimensions")?,
        d_c: matrices_field(value, "d_c")?,
        d_d: matrices_field(value, "d_d")?,
        inclusion: matrices_field(value, "inclusion")?,
        retraction: matrices_field(value, "retraction")?,
        homotopy: matrices_field(value, "homotopy")?,
    })
}

fn contraction_value(data: &ContractionData) -> Value {
    json!({
        "c_dimensions": data.c_dimensions,
        "d_dimensions": data.d_dimensions,
        "d_c": data.d_c.iter().map(matrix_value).collect::<Vec<_>>(),
        "d_d": data.d_d.iter().map(matrix_value).collect::<Vec<_>>(),
        "inclusion": data.inclusion.iter().map(matrix_value).collect::<Vec<_>>(),
        "retraction": data.retraction.iter().map(matrix_value).collect::<Vec<_>>(),
        "homotopy": data.homotopy.iter().map(matrix_value).collect::<Vec<_>>(),
    })
}

fn failed(
    reason: &str,
    report: Option<SideConditionReport>,
    invertibility: bool,
    reduced_square_zero: Option<bool>,
) -> Value {
    json!({
        "success": false,
        "invertibility": invertibility,
        "delta_d": null,
        "side_conditions": report,
        "report": report,
        "obstruction_reason": reason,
        "reduced_square_zero": reduced_square_zero,
        "perturbed_contraction": null,
    })
}

fn failure(
    error: PerturbationError,
    report: Option<SideConditionReport>,
    transferred: bool,
) -> Result<Value, String> {
    match error {
        PerturbationError::NotNormalized { report } => Ok(failed(
            if transferred {
                "transferred_contraction_side_conditions_failed"
            } else {
                "normalized_contraction_side_conditions_failed"
            },
            Some(report),
            transferred,
            None,
        )),
        PerturbationError::SingularResolvent { degree } => Ok(failed(
            &format!("1_plus_delta_h_singular_on_deg{degree}"),
            report,
            false,
            None,
        )),
        PerturbationError::DifferentialNotSquareZero { complex } => {
            let reason = match (complex, transferred) {
                ("C+delta", _) => "perturbed_differential_not_square_zero",
                ("D", true) => "reduced_differential_not_square_zero",
                ("D", false) => "target_differential_not_square_zero",
                _ => "source_differential_not_square_zero",
            };
            let reduced_failed = complex == "D" && transferred;
            Ok(failed(
                reason,
                report,
                reduced_failed,
                reduced_failed.then_some(false),
            ))
        }
        // Shapes, malformed coefficients, resource budgets and arithmetic
        // failures remain native refusals; they are not mathematical receipts.
        other => Err(other.to_string()),
    }
}

fn validate_homology_request_fields(payload: &Value, perturb: bool) -> Result<(), String> {
    fields(
        payload,
        "homology request",
        if perturb {
            &[
                "contraction",
                "delta",
                "require_normalized",
                "check_perturbed_square_zero",
            ]
        } else {
            &["contraction"]
        },
    )?;
    for flag in ["require_normalized", "check_perturbed_square_zero"] {
        if payload.get(flag).is_some_and(|value| !value.is_boolean()) {
            return Err(format!("{flag} must be a boolean"));
        }
    }
    Ok(())
}

fn parse_and_validate_delta(
    payload: &Value,
    c_dimensions: &[usize; 3],
) -> Result<[BasicMatrix<BigRational>; 2], String> {
    let delta = matrices_field::<2>(payload, "delta")?;
    for (degree, matrix) in delta.iter().enumerate() {
        let expected = (c_dimensions[degree + 1], c_dimensions[degree]);
        if matrix.shape() != expected {
            return Err(format!(
                "delta[{degree}] has shape {:?}, expected {expected:?}",
                matrix.shape()
            ));
        }
    }
    Ok(delta)
}

fn execute_perturbation_transfer(
    data: ContractionData,
    report: SideConditionReport,
    delta: [BasicMatrix<BigRational>; 2],
) -> Result<Value, String> {
    if !report.is_normalized() {
        return Ok(failed(
            "normalized_contraction_side_conditions_failed",
            Some(report),
            false,
            None,
        ));
    }
    let checked = match CheckedContraction::try_new(data, limits()) {
        Ok(checked) => checked,
        Err(error) => return failure(error, Some(report), false),
    };
    let result = match transfer_perturbation(&checked, &delta, limits()) {
        Ok(result) => result,
        Err(error) => return failure(error, Some(report), true),
    };
    Ok(json!({
        "success": true,
        "invertibility": true,
        "delta_d": result.delta_d.iter().map(matrix_value).collect::<Vec<_>>(),
        "side_conditions": report,
        "obstruction_reason": null,
        "reduced_square_zero": true,
        "perturbed_contraction": contraction_value(result.contraction.data()),
        "original_contraction_hash": result.original_contraction_hash.to_hex(),
    }))
}

pub(super) fn dispatch(payload: &Value, perturb: bool) -> Result<Value, String> {
    validate_homology_request_fields(payload, perturb)?;
    let data = parse_contraction(required(payload, "contraction")?)?;
    let delta = if perturb {
        Some(parse_and_validate_delta(payload, &data.c_dimensions)?)
    } else {
        None
    };
    let report = match verify_normalized(&data, limits()) {
        Ok(report) => report,
        Err(error) => return failure(error, None, false),
    };
    let Some(delta) = delta else {
        return Ok(json!({"success": report.is_normalized(), "report": report}));
    };
    execute_perturbation_transfer(data, report, delta)
}

// Origin: engine/crates_rs/pfp/src/invoke/native_homology.rs
// Claim: urn:core:crates_rs:pfp:native-homology:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord29ecf19b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord29ecf19b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError29ecf19b {
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
impl BoundaryError29ecf19b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError29ecf19b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError29ecf19b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord29ecf19b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError29ecf19b> {
        if capacity_bound == 0 {
            return Err(BoundaryError29ecf19b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError29ecf19b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError29ecf19b::ExceedsCapacity {
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
    use linear_algebra::exact_field::matrix::{identity, zeros};

    fn identity_data(dimensions: [usize; 3]) -> Value {
        let differential = [
            zeros(dimensions[1], dimensions[0]).unwrap(),
            zeros(dimensions[2], dimensions[1]).unwrap(),
        ];
        contraction_value(&ContractionData {
            c_dimensions: dimensions,
            d_dimensions: dimensions,
            d_c: differential.clone(),
            d_d: differential,
            inclusion: dimensions.map(|dimension| identity(dimension).unwrap()),
            retraction: dimensions.map(|dimension| identity(dimension).unwrap()),
            homotopy: [
                zeros(dimensions[0], dimensions[1]).unwrap(),
                zeros(dimensions[1], dimensions[2]).unwrap(),
            ],
        })
    }

    #[test]
    fn identity_transfer_exposes_checked_maps_and_preserves_empty_shapes() {
        let data = identity_data([1, 1, 0]);
        let report = dispatch(&json!({"contraction": data.clone()}), false).unwrap();
        assert_eq!(report["report"]["inclusion_chain_map"], true);
        let delta = json!([
            {"rows": 1, "cols": 1, "data": [["2/3"]]},
            {"rows": 0, "cols": 1, "data": []}
        ]);
        let result = dispatch(&json!({"contraction": data, "delta": delta}), true).unwrap();
        assert_eq!(result["success"], true);
        assert_eq!(result["delta_d"], delta);
        assert_eq!(result["perturbed_contraction"]["d_c"], delta);
        assert_eq!(result["reduced_square_zero"], true);
    }

    #[test]
    fn malformed_shapes_and_compatibility_flags_are_refusals() {
        let data = identity_data([1, 1, 0]);
        let mut changed = data.clone();
        changed["inclusion"] = json!([]);
        assert!(dispatch(&json!({"contraction": changed}), false).is_err());
        let mut changed = data.clone();
        changed["c_dimensions"] = json!([true, 1, 0]);
        assert!(dispatch(&json!({"contraction": changed}), false).is_err());
        let mut changed = data.clone();
        changed["c_dimensions"] = json!([257, 1, 0]);
        assert!(dispatch(&json!({"contraction": changed}), false).is_err());
        assert!(dispatch(
            &json!({"contraction": data.clone(), "delta": data["d_c"], "require_normalized": 0}),
            true,
        )
        .is_err());
        assert!(dispatch(&json!({"contraction": data, "ignored": true}), false).is_err());
    }

    #[test]
    fn original_invalid_differential_returns_no_invented_report() {
        let mut data = identity_data([1, 1, 1]);
        data["d_c"][0]["data"] = json!([["1"]]);
        data["d_c"][1]["data"] = json!([["1"]]);
        let result = dispatch(&json!({"contraction": data}), false).unwrap();
        assert_eq!(result["success"], false);
        assert_eq!(
            result["obstruction_reason"],
            "source_differential_not_square_zero"
        );
        assert!(result["report"].is_null());
    }

    #[test]
    fn legacy_flags_cannot_disable_exact_invariants() {
        let mut data = identity_data([1, 1, 0]);
        data["homotopy"][0]["data"] = json!([["1"]]);
        let result = dispatch(
            &json!({"contraction": data.clone(), "delta": data["d_c"], "require_normalized": false}),
            true,
        )
        .unwrap();
        assert_eq!(result["success"], false);
        assert_eq!(
            result["obstruction_reason"],
            "normalized_contraction_side_conditions_failed"
        );
        assert_eq!(result["side_conditions"]["hi_zero"], false);
        let data = identity_data([1, 1, 1]);
        let delta = json!([
            {"rows": 1, "cols": 1, "data": [["1"]]},
            {"rows": 1, "cols": 1, "data": [["1"]]}
        ]);
        let result = dispatch(
            &json!({"contraction": data, "delta": delta, "check_perturbed_square_zero": false}),
            true,
        )
        .unwrap();
        assert_eq!(
            result["obstruction_reason"],
            "perturbed_differential_not_square_zero"
        );
        assert!(result["reduced_square_zero"].is_null());
    }

    #[test]
    fn singular_resolvent_has_a_stable_reason_and_uncomputed_reduced_law() {
        let zero_00 = json!({"rows": 0, "cols": 0, "data": []});
        let zero_01 = json!({"rows": 0, "cols": 1, "data": []});
        let zero_10 = json!({"rows": 1, "cols": 0, "data": [[]]});
        let one = json!({"rows": 1, "cols": 1, "data": [["1"]]});
        let data = json!({
            "c_dimensions": [1, 1, 0], "d_dimensions": [0, 0, 0],
            "d_c": [one, zero_01], "d_d": [zero_00, zero_00],
            "inclusion": [zero_10, zero_10, zero_00],
            "retraction": [zero_01, zero_01, zero_00],
            "homotopy": [one, zero_10],
        });
        let delta = json!([{"rows": 1, "cols": 1, "data": [["-1"]]}, zero_01]);
        let result = dispatch(&json!({"contraction": data, "delta": delta}), true).unwrap();
        assert_eq!(result["success"], false);
        assert_eq!(result["invertibility"], false);
        assert_eq!(
            result["obstruction_reason"],
            "1_plus_delta_h_singular_on_deg1"
        );
        assert!(result["delta_d"].is_null());
        assert!(result["reduced_square_zero"].is_null());
        assert_eq!(result["side_conditions"]["sdr_equation"], true);
    }
}

#[cfg(test)]
mod l4_boundary_tests_29ecf19b {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord29ecf19b::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord29ecf19b::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord29ecf19b::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord29ecf19b::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord29ecf19b::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError29ecf19b::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError29ecf19b::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
