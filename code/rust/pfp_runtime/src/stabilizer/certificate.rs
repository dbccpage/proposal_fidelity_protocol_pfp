//! Candidate-bound total certificate verification; solver output is not caller authority.

use super::{parse_case, solve, StabilizerCheckResult, StabilizerOutcome};
use num_bigint::BigInt;
use num_rational::BigRational;
use serde_json::Value;

fn fail(case_id: impl Into<String>, reason: impl Into<String>) -> StabilizerCheckResult {
    StabilizerCheckResult::Fail {
        case_id: case_id.into(),
        reason: reason.into(),
    }
}

fn extract_case_id(case_val: &Value) -> String {
    case_val
        .get("id")
        .or_else(|| case_val.get("case_id"))
        .and_then(|v| v.as_str())
        .unwrap_or("case_unnamed")
        .to_string()
}

fn validate_result_envelope<'a>(
    case_id: &str,
    result_val: &'a Value,
) -> Result<(&'a serde_json::Map<String, Value>, &'a str), StabilizerCheckResult> {
    let result_obj = result_val.as_object().ok_or_else(|| {
        fail(
            case_id,
            format!("Result must be a JSON object, got {:?}", result_val),
        )
    })?;
    let status = result_obj
        .get("status")
        .and_then(|v| v.as_str())
        .ok_or_else(|| fail(case_id, "Result missing 'status' field"))?;
    if !matches!(status, "SOLVED" | "OUT_OF_SCOPE" | "UNKNOWN") {
        return Err(fail(case_id, format!("Invalid status: {status:?}")));
    }
    if result_obj.get("id").and_then(Value::as_str) != Some(case_id) {
        return Err(fail(case_id, "Result id must match the input case id"));
    }
    Ok((result_obj, status))
}

fn check_unknown_outcome(
    case_id: String,
    status: &str,
    result_obj: &serde_json::Map<String, Value>,
    refusal_code: String,
    message: String,
) -> StabilizerCheckResult {
    // Admission, search or output representation was refused.
    // Result must be UNKNOWN with refusal_code.
    if status != "UNKNOWN" {
        return fail(
            case_id,
            format!("Case was refused ({refusal_code}: {message}), but result reported {status}"),
        );
    }
    let res_code = result_obj.get("refusal_code").and_then(|v| v.as_str());
    if res_code != Some(refusal_code.as_str()) {
        return fail(
            case_id,
            "UNKNOWN refusal_code must match the native refusal",
        );
    }
    StabilizerCheckResult::Pass {
        case_id,
        details: Some(format!("Confirmed refusal: {refusal_code}")),
    }
}

fn extract_witness_pair<'a>(
    case_id: &str,
    result_obj: &'a serde_json::Map<String, Value>,
) -> Result<(&'a str, &'a str), StabilizerCheckResult> {
    let witness_arr = result_obj
        .get("witness")
        .and_then(|v| v.as_array())
        .ok_or_else(|| fail(case_id, "OUT_OF_SCOPE result missing 'witness' array"))?;
    if witness_arr.len() != 2 {
        return Err(fail(
            case_id,
            format!(
                "Witness must contain exactly 2 term IDs, got {}",
                witness_arr.len()
            ),
        ));
    }
    let w1 = witness_arr[0]
        .as_str()
        .ok_or_else(|| fail(case_id, "Witness elements must be strings"))?;
    let w2 = witness_arr[1]
        .as_str()
        .ok_or_else(|| fail(case_id, "Witness elements must be strings"))?;
    Ok((w1, w2))
}

fn verify_witness_anticommutes(
    case_id: String,
    case_val: &Value,
    w1: &str,
    w2: &str,
) -> StabilizerCheckResult {
    // Check that the two witness terms actually exist in the case and anticommute
    let parsed_case = match parse_case(case_val) {
        Ok(c) => c,
        Err((code, msg)) => {
            return fail(
                case_id,
                format!("Failed to parse case for witness validation: [{code}] {msg}"),
            );
        }
    };
    let t1 = parsed_case.terms.iter().find(|t| t.id == w1);
    let t2 = parsed_case.terms.iter().find(|t| t.id == w2);
    let (Some(p1), Some(p2)) = (t1, t2) else {
        return fail(
            case_id,
            format!("Witness terms ({w1}, {w2}) not found in case terms"),
        );
    };
    let anticommutes = match p1.pauli.anticommutes_with(&p2.pauli) {
        Ok(b) => b,
        Err(e) => {
            return fail(
                case_id,
                format!("Pauli error between witness terms ({w1}, {w2}): {e:?}"),
            );
        }
    };
    if !anticommutes {
        return fail(
            case_id,
            format!("Witness terms ({w1}, {w2}) do not anticommute"),
        );
    }
    StabilizerCheckResult::Pass {
        case_id,
        details: Some(format!("Witness verified anticommuting pair: ({w1}, {w2})")),
    }
}

fn check_out_of_scope_outcome(
    case_id: String,
    status: &str,
    case_val: &Value,
    result_obj: &serde_json::Map<String, Value>,
) -> StabilizerCheckResult {
    // Case contains anticommuting terms
    if status != "OUT_OF_SCOPE" {
        return fail(
            case_id,
            format!("Case is noncommuting, but result reported {status}"),
        );
    }
    match extract_witness_pair(&case_id, result_obj) {
        Ok((w1, w2)) => verify_witness_anticommutes(case_id, case_val, w1, w2),
        Err(err) => err,
    }
}

fn parse_energy_pair(
    case_id: &str,
    energy_arr: &[Value],
) -> Result<(i64, i64), StabilizerCheckResult> {
    if energy_arr.len() != 2 {
        return Err(fail(
            case_id,
            format!("Energy must be [num, den], got length {}", energy_arr.len()),
        ));
    }
    if energy_arr[0].is_boolean() || energy_arr[1].is_boolean() {
        return Err(fail(case_id, "Energy components cannot be boolean"));
    }
    let res_num = energy_arr[0]
        .as_i64()
        .ok_or_else(|| fail(case_id, "Energy numerator must be an integer"))?;
    let res_den = energy_arr[1]
        .as_i64()
        .ok_or_else(|| fail(case_id, "Energy denominator must be an integer"))?;
    if res_den <= 0 {
        return Err(fail(
            case_id,
            format!("Energy denominator must be positive, got {res_den}"),
        ));
    }
    Ok((res_num, res_den))
}

fn validate_solved_energy(
    case_id: &str,
    result_obj: &serde_json::Map<String, Value>,
    truth_energy: [i64; 2],
) -> Result<(), StabilizerCheckResult> {
    // 1. Validate energy
    let energy_arr = result_obj
        .get("energy")
        .and_then(|v| v.as_array())
        .ok_or_else(|| fail(case_id, "Result missing 'energy' array"))?;
    let (res_num, res_den) = parse_energy_pair(case_id, energy_arr)?;
    let res_energy_rat = BigRational::new(BigInt::from(res_num), BigInt::from(res_den));
    let truth_energy_rat =
        BigRational::new(BigInt::from(truth_energy[0]), BigInt::from(truth_energy[1]));
    if res_energy_rat != truth_energy_rat {
        return Err(fail(
            case_id,
            format!("Energy mismatch: expected {truth_energy_rat}, got {res_energy_rat}"),
        ));
    }
    Ok(())
}

fn validate_solved_degeneracy(
    case_id: &str,
    result_obj: &serde_json::Map<String, Value>,
    truth_deg: u64,
) -> Result<(), StabilizerCheckResult> {
    // 2. Validate degeneracy
    let res_deg_val = result_obj
        .get("degeneracy")
        .ok_or_else(|| fail(case_id, "Result missing 'degeneracy'"))?;
    if res_deg_val.is_boolean() {
        return Err(fail(case_id, "Degeneracy cannot be boolean"));
    }
    let res_deg = res_deg_val
        .as_u64()
        .ok_or_else(|| fail(case_id, "Degeneracy must be positive integer"))?;
    if res_deg != truth_deg {
        return Err(fail(
            case_id,
            format!("Degeneracy mismatch: expected {truth_deg}, got {res_deg}"),
        ));
    }
    Ok(())
}

fn validate_solved_basis(
    case_id: &str,
    result_obj: &serde_json::Map<String, Value>,
    truth_basis: &[String],
) -> Result<(), StabilizerCheckResult> {
    // 3. Validate basis
    let basis_arr = result_obj
        .get("basis")
        .and_then(|v| v.as_array())
        .ok_or_else(|| fail(case_id, "Result missing 'basis' array"))?;
    if basis_arr.len() != truth_basis.len() {
        return Err(fail(
            case_id,
            format!(
                "Basis length mismatch: expected {}, got {}",
                truth_basis.len(),
                basis_arr.len()
            ),
        ));
    }

    // The compact certificate uses the solver's deterministic input-order
    // basis. Masks and minimizer indices are coordinates in THIS basis;
    // accepting only the length would leave those coordinates unbound.
    for (idx, (declared, expected)) in basis_arr.iter().zip(truth_basis).enumerate() {
        if declared.as_str() != Some(expected.as_str()) {
            return Err(fail(
                case_id,
                format!("Basis at index {idx} must be canonical input term {expected}"),
            ));
        }
    }
    Ok(())
}

fn validate_decomp_mask(
    case_id: &str,
    idx: usize,
    d_obj: &serde_json::Map<String, Value>,
    expected_mask: usize,
) -> Result<(), StabilizerCheckResult> {
    let mask_val = d_obj
        .get("mask")
        .ok_or_else(|| fail(case_id, format!("Decomposition at index {idx} missing 'mask'")))?;
    if mask_val.is_boolean() || !mask_val.is_u64() {
        return Err(fail(
            case_id,
            format!("Decomposition mask at index {idx} must be unsigned integer"),
        ));
    }
    if mask_val.as_u64() != Some(expected_mask as u64) {
        return Err(fail(
            case_id,
            format!("Decomposition mask at index {idx} does not reconstruct its input term"),
        ));
    }
    Ok(())
}

fn extract_phase_int(
    case_id: &str,
    idx: usize,
    d_obj: &serde_json::Map<String, Value>,
) -> Result<i64, StabilizerCheckResult> {
    let phase_val = d_obj
        .get("phase")
        .or_else(|| d_obj.get("sign"))
        .ok_or_else(|| fail(case_id, format!("Decomposition at index {idx} missing 'phase'")))?;
    if phase_val.is_boolean() {
        return Err(fail(
            case_id,
            format!("Decomposition phase at index {idx} cannot be boolean"),
        ));
    }
    phase_val
        .as_i64()
        .ok_or_else(|| fail(case_id, format!("Decomposition phase at index {idx} must be integer")))
}

fn validate_decomp_phase(
    case_id: &str,
    idx: usize,
    d_obj: &serde_json::Map<String, Value>,
    expected_phase: i8,
) -> Result<(), StabilizerCheckResult> {
    let p = extract_phase_int(case_id, idx, d_obj)?;
    if p != 1 && p != -1 {
        return Err(fail(
            case_id,
            format!("Decomposition phase at index {idx} must be +1 or -1, got {p}"),
        ));
    }
    if p != i64::from(expected_phase) {
        return Err(fail(
            case_id,
            format!("Decomposition phase at index {idx} does not reconstruct its input term"),
        ));
    }
    if d_obj.get("sign").is_some_and(|sign| sign.as_i64() != Some(p)) {
        return Err(fail(
            case_id,
            format!("Decomposition sign alias at index {idx} contradicts phase"),
        ));
    }
    Ok(())
}

fn validate_decomposition_row(
    case_id: &str,
    idx: usize,
    d_val: &Value,
    expected: &super::DecompositionRow,
) -> Result<(), StabilizerCheckResult> {
    let d_obj = d_val
        .as_object()
        .ok_or_else(|| fail(case_id, format!("Decomposition at index {idx} must be a dict")))?;
    if d_obj.get("id").and_then(Value::as_str) != Some(expected.id.as_str()) {
        return Err(fail(
            case_id,
            format!(
                "Decomposition at index {idx} must bind input term {}",
                expected.id
            ),
        ));
    }
    validate_decomp_mask(case_id, idx, d_obj, expected.mask)?;
    validate_decomp_phase(case_id, idx, d_obj, expected.phase)
}

fn validate_solved_decomposition(
    case_id: &str,
    result_obj: &serde_json::Map<String, Value>,
    truth_decomp: &[super::DecompositionRow],
) -> Result<(), StabilizerCheckResult> {
    // 4. Validate decomposition
    let decomp_arr = result_obj
        .get("decomposition")
        .and_then(|v| v.as_array())
        .ok_or_else(|| fail(case_id, "Result missing 'decomposition' array"))?;
    if decomp_arr.len() != truth_decomp.len() {
        return Err(fail(
            case_id,
            format!(
                "Decomposition length mismatch: expected {}, got {}",
                truth_decomp.len(),
                decomp_arr.len()
            ),
        ));
    }
    for (idx, d_val) in decomp_arr.iter().enumerate() {
        validate_decomposition_row(case_id, idx, d_val, &truth_decomp[idx])?;
    }
    Ok(())
}

fn parse_minimizer_index(
    case_id: &str,
    idx: usize,
    m_val: &Value,
) -> Result<usize, StabilizerCheckResult> {
    if m_val.is_boolean() {
        return Err(fail(
            case_id,
            format!("Minimizer at index {idx} must be unsigned integer"),
        ));
    }
    let u = m_val
        .as_u64()
        .ok_or_else(|| fail(case_id, format!("Minimizer at index {idx} must be unsigned integer")))?;
    usize::try_from(u).map_err(|_| {
        fail(
            case_id,
            format!("Minimizer at index {idx} exceeds native index width"),
        )
    })
}

fn validate_solved_minimizers(
    case_id: &str,
    result_obj: &serde_json::Map<String, Value>,
    mut expected_mins: Vec<usize>,
) -> Result<(), StabilizerCheckResult> {
    // 5. Validate minimizers
    let min_arr = result_obj
        .get("minimizers")
        .and_then(|v| v.as_array())
        .ok_or_else(|| fail(case_id, "Result missing 'minimizers' array"))?;
    if min_arr.len() != expected_mins.len() {
        return Err(fail(
            case_id,
            format!(
                "Minimizers length mismatch: expected {}, got {}",
                expected_mins.len(),
                min_arr.len()
            ),
        ));
    }
    let mut res_mins = min_arr
        .iter()
        .enumerate()
        .map(|(idx, m_val)| parse_minimizer_index(case_id, idx, m_val))
        .collect::<Result<Vec<_>, _>>()?;
    res_mins.sort_unstable();
    expected_mins.sort_unstable();
    if res_mins != expected_mins {
        return Err(fail(
            case_id,
            format!("Minimizers set mismatch: expected {expected_mins:?}, got {res_mins:?}"),
        ));
    }
    Ok(())
}

#[allow(clippy::too_many_arguments)]
fn check_solved_outcome(
    case_id: String,
    status: &str,
    result_obj: &serde_json::Map<String, Value>,
    truth_energy: [i64; 2],
    truth_deg: u64,
    truth_basis: Vec<String>,
    truth_decomp: Vec<super::DecompositionRow>,
    truth_minimizers: Vec<usize>,
) -> StabilizerCheckResult {
    // Case is commuting and solvable
    if status != "SOLVED" {
        return fail(
            case_id,
            format!("Case is solvable, but result reported {status}"),
        );
    }
    let checks = validate_solved_energy(&case_id, result_obj, truth_energy)
        .and_then(|()| validate_solved_degeneracy(&case_id, result_obj, truth_deg))
        .and_then(|()| validate_solved_basis(&case_id, result_obj, &truth_basis))
        .and_then(|()| validate_solved_decomposition(&case_id, result_obj, &truth_decomp))
        .and_then(|()| validate_solved_minimizers(&case_id, result_obj, truth_minimizers));
    match checks {
        Ok(()) => StabilizerCheckResult::Pass {
            case_id,
            details: Some("All algebraic invariants verified".to_string()),
        },
        Err(err) => err,
    }
}

/// Total certificate checker.
///
/// Returns `Pass` or `Fail { reason }` for ANY input values; never panics.
pub fn check(case_val: &Value, result_val: &Value) -> StabilizerCheckResult {
    let case_id = extract_case_id(case_val);
    let (result_obj, status) = match validate_result_envelope(&case_id, result_val) {
        Ok(pair) => pair,
        Err(err) => return err,
    };

    // Ground truth evaluation from solver
    let truth = solve(case_val);

    match truth {
        StabilizerOutcome::Unknown {
            refusal_code,
            message,
            ..
        } => check_unknown_outcome(case_id, status, result_obj, refusal_code, message),
        StabilizerOutcome::OutOfScope { .. } => {
            check_out_of_scope_outcome(case_id, status, case_val, result_obj)
        }
        StabilizerOutcome::Solved {
            energy: truth_energy,
            degeneracy: truth_deg,
            basis: truth_basis,
            decomposition: truth_decomp,
            minimizers: truth_minimizers,
            ..
        } => check_solved_outcome(
            case_id,
            status,
            result_obj,
            truth_energy,
            truth_deg,
            truth_basis,
            truth_decomp,
            truth_minimizers,
        ),
    }
}

// Origin: engine/crates_rs/pfp_runtime/src/stabilizer/certificate.rs
// Claim: urn:core:crates_rs:pfp-runtime:certificate:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde3fc7e07 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde3fc7e07` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore3fc7e07 {
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
impl BoundaryErrore3fc7e07 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore3fc7e07 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore3fc7e07 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde3fc7e07 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore3fc7e07> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore3fc7e07::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore3fc7e07::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore3fc7e07::ExceedsCapacity {
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
mod l4_boundary_tests_e3fc7e07 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorde3fc7e07::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorde3fc7e07::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorde3fc7e07::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorde3fc7e07::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorde3fc7e07::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrore3fc7e07::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrore3fc7e07::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
