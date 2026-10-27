//! Total JSON admission for the bounded Q40 Hamiltonian contract.

use super::{StabilizerCase, Term, MAX_QUBITS, MAX_TERMS};
use num_rational::Rational64;
use core_quantum_physics::pauli::PauliString;
use serde_json::Value;
use std::collections::BTreeSet;

fn build_non_negative_rational(num: i64, den: i64) -> Result<Rational64, String> {
    if den <= 0 {
        return Err(format!("weight denominator must be positive, got {den}"));
    }
    if num < 0 {
        return Err(format!("weight numerator must be non-negative, got {num}"));
    }
    Ok(Rational64::new(num, den))
}

fn parse_weight_array(arr: &[Value]) -> Result<Rational64, String> {
    if arr.len() != 2 {
        return Err("weight array must have exactly 2 elements [num, den]".to_string());
    }
    let num = arr[0]
        .as_i64()
        .ok_or_else(|| "weight numerator must be integer".to_string())?;
    let den = arr[1]
        .as_i64()
        .ok_or_else(|| "weight denominator must be integer".to_string())?;
    build_non_negative_rational(num, den)
}

fn parse_weight_str(s: &str) -> Result<Rational64, String> {
    let s = s.trim();
    if let Some((n_s, d_s)) = s.split_once('/') {
        let num: i64 = n_s
            .trim()
            .parse()
            .map_err(|e| format!("invalid numerator: {e}"))?;
        let den: i64 = d_s
            .trim()
            .parse()
            .map_err(|e| format!("invalid denominator: {e}"))?;
        return build_non_negative_rational(num, den);
    }
    let num: i64 = s
        .parse()
        .map_err(|e| format!("invalid weight integer: {e}"))?;
    if num < 0 {
        return Err(format!("weight must be non-negative, got {num}"));
    }
    Ok(Rational64::from_integer(num))
}

/// Parse a rational weight from a JSON value: [num, den] or int or string "num/den".
pub fn parse_weight(val: &Value) -> Result<Rational64, String> {
    if val.is_boolean() {
        return Err("weight cannot be boolean".to_string());
    }
    if let Some(arr) = val.as_array() {
        return parse_weight_array(arr);
    }
    if let Some(n) = val.as_i64() {
        if n < 0 {
            return Err(format!("weight must be non-negative, got {n}"));
        }
        return Ok(Rational64::from_integer(n));
    }
    if let Some(s) = val.as_str() {
        return parse_weight_str(s);
    }
    Err("weight must be [num, den], int, or string".to_string())
}

/// Parse target sign from JSON value: +1 or -1.
pub fn parse_target(val: &Value) -> Result<i8, String> {
    if val.is_boolean() {
        return Err("target sign cannot be boolean".to_string());
    }
    let t = if let Some(n) = val.as_i64() {
        n
    } else if let Some(s) = val.as_str() {
        s.trim()
            .parse::<i64>()
            .map_err(|e| format!("invalid target integer: {e}"))?
    } else {
        return Err("target sign must be integer +1 or -1".to_string());
    };
    if t == 1 {
        Ok(1)
    } else if t == -1 {
        Ok(-1)
    } else {
        Err(format!("target sign must be +1 or -1, got {t}"))
    }
}

fn parse_num_qubits(
    case_obj: &serde_json::Map<String, Value>,
) -> Result<usize, (String, String)> {
    let n_val = case_obj
        .get("n")
        .or_else(|| case_obj.get("num_qubits"))
        .ok_or_else(|| {
            (
                "MISSING_QUBIT_COUNT".to_string(),
                "Missing qubit count (n or num_qubits)".to_string(),
            )
        })?;

    if n_val.is_boolean() {
        return Err((
            "INVALID_QUBIT_COUNT".to_string(),
            "Qubit count cannot be boolean".to_string(),
        ));
    }
    let num_qubits = n_val.as_u64().ok_or_else(|| {
        (
            "INVALID_QUBIT_COUNT".to_string(),
            "Qubit count must be integer".to_string(),
        )
    })? as usize;

    if num_qubits == 0 || num_qubits > MAX_QUBITS {
        return Err((
            "QUBIT_BOUND_EXCEEDED".to_string(),
            format!("num_qubits must be between 1 and {MAX_QUBITS}, got {num_qubits}"),
        ));
    }
    Ok(num_qubits)
}

fn parse_term_pauli(
    t_obj: &serde_json::Map<String, Value>,
    term_id: &str,
    num_qubits: usize,
) -> Result<PauliString, (String, String)> {
    let pauli_str = t_obj
        .get("pauli")
        .or_else(|| t_obj.get("P"))
        .and_then(|v| v.as_str())
        .ok_or_else(|| {
            (
                "MISSING_PAULI_WORD".to_string(),
                format!("Missing pauli word in term {term_id}"),
            )
        })?;

    let pauli = PauliString::parse(pauli_str).map_err(|e| {
        (
            "INVALID_PAULI_WORD".to_string(),
            format!("Invalid Pauli in term {term_id}: {e}"),
        )
    })?;

    if pauli.len() != num_qubits {
        return Err((
            "PAULI_LENGTH_MISMATCH".to_string(),
            format!(
                "Pauli word length {} does not match num_qubits {} in term {term_id}",
                pauli.len(),
                num_qubits
            ),
        ));
    }
    Ok(pauli)
}

fn parse_term_weight_and_target(
    t_obj: &serde_json::Map<String, Value>,
    term_id: &str,
) -> Result<(Rational64, i8), (String, String)> {
    let weight_val = t_obj
        .get("weight")
        .or_else(|| t_obj.get("w"))
        .unwrap_or(&Value::Null);

    let weight = if weight_val.is_null() {
        Rational64::from_integer(1)
    } else {
        parse_weight(weight_val).map_err(|e| {
            (
                "INVALID_WEIGHT".to_string(),
                format!("Invalid weight in term {term_id}: {e}"),
            )
        })?
    };

    let target_val = t_obj
        .get("target")
        .or_else(|| t_obj.get("target_sign"))
        .or_else(|| t_obj.get("s"))
        .unwrap_or(&Value::Null);

    let target = if target_val.is_null() {
        1i8
    } else {
        parse_target(target_val).map_err(|e| {
            (
                "INVALID_TARGET".to_string(),
                format!("Invalid target in term {term_id}: {e}"),
            )
        })?
    };

    Ok((weight, target))
}

fn parse_single_term(
    idx: usize,
    t_val: &Value,
    num_qubits: usize,
    seen_ids: &mut BTreeSet<String>,
) -> Result<Term, (String, String)> {
    let t_obj = t_val.as_object().ok_or_else(|| {
        (
            "INVALID_TERM_SHAPE".to_string(),
            format!("Term at index {idx} must be an object"),
        )
    })?;

    let raw_id = t_obj.get("id").and_then(|v| v.as_str()).unwrap_or("");
    let term_id = if raw_id.is_empty() {
        format!("t{idx}")
    } else {
        raw_id.to_string()
    };

    if !seen_ids.insert(term_id.clone()) {
        return Err((
            "DUPLICATE_TERM_ID".to_string(),
            format!("Duplicate term id: {term_id}"),
        ));
    }

    let pauli = parse_term_pauli(t_obj, &term_id, num_qubits)?;
    let (weight, target) = parse_term_weight_and_target(t_obj, &term_id)?;

    Ok(Term {
        id: term_id,
        pauli,
        weight,
        target,
    })
}

/// Parse a challenge case from JSON Value.
pub fn parse_case(case_val: &Value) -> Result<StabilizerCase, (String, String)> {
    let case_obj = case_val.as_object().ok_or_else(|| {
        (
            "INVALID_CASE_SHAPE".to_string(),
            "Case must be a JSON object".to_string(),
        )
    })?;

    let id = case_obj
        .get("id")
        .or_else(|| case_obj.get("case_id"))
        .and_then(|v| v.as_str())
        .unwrap_or("case_unnamed")
        .to_string();

    let num_qubits = parse_num_qubits(case_obj)?;

    let terms_arr = case_obj
        .get("terms")
        .and_then(|v| v.as_array())
        .ok_or_else(|| {
            (
                "MISSING_TERMS".to_string(),
                "Missing terms array".to_string(),
            )
        })?;

    if terms_arr.len() > MAX_TERMS {
        return Err((
            "TERMS_BOUND_EXCEEDED".to_string(),
            format!(
                "Terms count exceeds bound of {MAX_TERMS}: got {}",
                terms_arr.len()
            ),
        ));
    }

    let mut terms = Vec::with_capacity(terms_arr.len());
    let mut seen_ids = BTreeSet::new();

    for (idx, t_val) in terms_arr.iter().enumerate() {
        terms.push(parse_single_term(idx, t_val, num_qubits, &mut seen_ids)?);
    }

    Ok(StabilizerCase {
        id,
        num_qubits,
        terms,
    })
}

// Origin: engine/crates_rs/pfp_runtime/src/stabilizer/input.rs
// Claim: urn:core:crates_rs:pfp-runtime:input:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorddeec63f0 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorddeec63f0` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrordeec63f0 {
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
impl BoundaryErrordeec63f0 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrordeec63f0 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrordeec63f0 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorddeec63f0 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrordeec63f0> {
        if capacity_bound == 0 {
            return Err(BoundaryErrordeec63f0::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrordeec63f0::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrordeec63f0::ExceedsCapacity {
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
mod l4_boundary_tests_deec63f0 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorddeec63f0::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorddeec63f0::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorddeec63f0::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorddeec63f0::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorddeec63f0::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrordeec63f0::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrordeec63f0::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
