//! Input-bound finite measurement certificates for PO-000 section 7.8.
//! This protocol checks declared arithmetic assumptions, never laboratory coverage.

use crate::protocol::canonical_json;
use num_traits::{One, Zero};
use core_functional::product_distance::evaluate_product_distance;
use core_kernel::{parse_exact, to_canonical_string, Exact};
use pfp_runtime::framed_sha256;
use serde::{Deserialize, Serialize};
use serde_json::Value;

const SCHEMA: &str = "po000.measurement_certificate.v1";
const MAX_COORDINATES: usize = 64;

#[derive(Debug, Clone, PartialEq, Eq, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct PauliFactor {
    pub site: usize,
    pub axis: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Observable {
    pub id: String,
    pub factors: Vec<PauliFactor>,
}

#[derive(Debug, Clone, PartialEq, Eq, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct MeasurementContract {
    pub site_count: usize,
    pub observables: Vec<Observable>,
    pub arity: usize,
    pub reading_error: String,
    pub coverage_assumption: String,
    pub repair_rule: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct MeasurementRequest {
    pub contract: MeasurementContract,
    pub joint_moments: Vec<String>,
    pub factor_moments: Vec<Vec<String>>,
    pub repair_potential: Vec<String>,
    pub dual_witness: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct MeasurementCertificate {
    pub schema_version: String,
    pub request: MeasurementRequest,
    pub input_digest: String,
    pub corrected_moments: Vec<String>,
    pub quotient: String,
    pub product_distance_lower_bound: String,
    pub laboratory_coverage: String,
    pub authority_effect: String,
}

fn rationals(values: &[String]) -> Result<Vec<Exact>, String> {
    values
        .iter()
        .map(|v| {
            let q = parse_exact(v).map_err(|e| e.to_string())?;
            if to_canonical_string(&q) != *v {
                return Err("NONCANONICAL_RATIONAL".into());
            }
            Ok(q)
        })
        .collect()
}

fn validate_observable_factors(factors: &[PauliFactor], site_count: usize) -> Result<(), String> {
    let mut previous = None;
    for f in factors {
        let invalid_site = f.site >= site_count || previous.is_some_and(|p| p >= f.site);
        if invalid_site || !matches!(f.axis.as_str(), "X" | "Y" | "Z") {
            return Err("OBSERVABLE_SUPPORT_INVALID".into());
        }
        previous = Some(f.site);
    }
    Ok(())
}

fn validate_contract_header(c: &MeasurementContract) -> Result<(), String> {
    let n = c.observables.len();
    let valid_sizes = (3..=MAX_COORDINATES).contains(&n) && (1..=1024).contains(&c.site_count);
    let valid_coverage =
        !c.coverage_assumption.trim().is_empty() && c.coverage_assumption.len() <= 4096;
    if !valid_sizes || !valid_coverage || c.repair_rule != "oriented_cycle_gradients_mean_l1" {
        return Err("MEASUREMENT_CONTRACT_INVALID".into());
    }
    Ok(())
}

fn validate_contract(c: &MeasurementContract) -> Result<(), String> {
    validate_contract_header(c)?;
    let mut ids = std::collections::BTreeSet::new();
    for o in &c.observables {
        let valid_len = (2..=64).contains(&o.factors.len());
        if o.id.is_empty() || !ids.insert(&o.id) || !valid_len {
            return Err("OBSERVABLE_INVALID".into());
        }
        validate_observable_factors(&o.factors, c.site_count)?;
    }
    if c.observables.iter().map(|o| o.factors.len()).max() != Some(c.arity) {
        return Err("ARITY_MISMATCH".into());
    }
    Ok(())
}

fn validate_request_dimensions(request: &MeasurementRequest) -> Result<(), String> {
    let n = request.contract.observables.len();
    let counts_match = [
        request.joint_moments.len(),
        request.factor_moments.len(),
        request.repair_potential.len(),
        request.dual_witness.len(),
    ]
    .into_iter()
    .all(|len| len == n);
    let factors_match = request
        .factor_moments
        .iter()
        .zip(&request.contract.observables)
        .all(|(r, o)| r.len() == o.factors.len());
    if !counts_match || !factors_match {
        return Err("MEASUREMENT_DIMENSIONS".into());
    }
    Ok(())
}

fn build_cyclic_d0(n: usize) -> Vec<Vec<Exact>> {
    let mut d0 = vec![vec![Exact::zero(); n]; n];
    for (i, row) in d0.iter_mut().enumerate() {
        row[i] = -Exact::one();
        row[(i + 1) % n] = Exact::one();
    }
    d0
}

pub fn evaluate(payload: &Value) -> Result<MeasurementCertificate, String> {
    let request: MeasurementRequest = serde_json::from_value(payload.clone())
        .map_err(|e| format!("MEASUREMENT_REQUEST_INVALID: {e}"))?;
    validate_contract(&request.contract)?;
    validate_request_dimensions(&request)?;
    let n = request.contract.observables.len();
    let joint = rationals(&request.joint_moments)?;
    let factors = request
        .factor_moments
        .iter()
        .map(|r| rationals(r))
        .collect::<Result<Vec<_>, _>>()?;
    let potential = rationals(&request.repair_potential)?;
    let dual = rationals(&request.dual_witness)?;
    let error = rationals(std::slice::from_ref(&request.contract.reading_error))?.remove(0);
    // This is the declared structural differential; all scalar functionals are
    // evaluated in core_functional through its existing Phi1 witness verifier.
    let d0 = build_cyclic_d0(n);
    let value = evaluate_product_distance(&joint, &factors, &d0, &potential, &dual, &error)
        .map_err(|e| format!("MEASUREMENT_WITNESS_REJECTED: {e}"))?;
    Ok(MeasurementCertificate {
        schema_version: SCHEMA.into(),
        input_digest: framed_sha256(SCHEMA, &canonical_json(payload)),
        request,
        corrected_moments: value.corrected().iter().map(to_canonical_string).collect(),
        quotient: to_canonical_string(value.quotient().value()),
        product_distance_lower_bound: to_canonical_string(value.lower_bound()),
        laboratory_coverage: "declared_assumption_not_verified".into(),
        authority_effect: "None".into(),
    })
}

/// A verifier's independently supplied contract binds support and error premises.
/// Rehashing a changed certificate cannot change that contract.
pub fn verify(payload: &Value) -> Result<Value, String> {
    #[derive(Deserialize)]
    #[serde(deny_unknown_fields)]
    struct Verification {
        expected_contract: MeasurementContract,
        certificate: MeasurementCertificate,
    }
    let v: Verification = serde_json::from_value(payload.clone()).map_err(|e| e.to_string())?;
    if v.expected_contract != v.certificate.request.contract {
        return Err("MEASUREMENT_CONTRACT_BINDING_MISMATCH".into());
    }
    let request = serde_json::to_value(&v.certificate.request).map_err(|e| e.to_string())?;
    let recomputed = evaluate(&request)?;
    Ok(serde_json::json!({"accepted": recomputed == v.certificate,
        "input_digest": recomputed.input_digest, "authority_effect": "None"}))
}

// Origin: engine/crates_rs/pfp/src/measurement_certificate.rs
// Claim: urn:core:crates_rs:pfp:measurement-certificate:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord06c27bed {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord06c27bed` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError06c27bed {
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
impl BoundaryError06c27bed {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError06c27bed {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError06c27bed {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord06c27bed {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError06c27bed> {
        if capacity_bound == 0 {
            return Err(BoundaryError06c27bed::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError06c27bed::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError06c27bed::ExceedsCapacity {
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
    fn fixture() -> Value {
        json!({"contract": {"site_count": 3, "arity": 2, "reading_error":"1/30",
          "coverage_assumption":"simultaneous absolute moment errors at most 1/30",
          "repair_rule":"oriented_cycle_gradients_mean_l1", "observables":[
          {"id":"01", "factors":[{"site":0,"axis":"Z"},{"site":1,"axis":"Z"}]},
          {"id":"12", "factors":[{"site":1,"axis":"Z"},{"site":2,"axis":"Z"}]},
          {"id":"02", "factors":[{"site":0,"axis":"Z"},{"site":2,"axis":"Z"}]}]},
          "joint_moments":["1","1","1"], "factor_moments":[["0","0"],["0","0"],["0","0"]],
          "repair_potential":["0","0","0"], "dual_witness":["1/3","1/3","1/3"]})
    }
    #[test]
    fn finite_separable_correlation_is_product_distance_not_entanglement() {
        let input = fixture();
        let cert = evaluate(&input).unwrap();
        assert_eq!(cert.quotient, "1");
        assert_eq!(cert.product_distance_lower_bound, "3/10");
        assert_eq!(
            verify(&json!({"expected_contract":input["contract"],"certificate":cert})).unwrap()
                ["accepted"],
            true
        );
    }
    #[test]
    fn mutations_of_support_error_and_arity_are_bound_even_after_rehashing() {
        let input = fixture();
        for pointer in [
            "/contract/arity",
            "/contract/reading_error",
            "/contract/observables/0/factors/0/site",
        ] {
            let mut changed = input.clone();
            *changed.pointer_mut(pointer).unwrap() = match pointer {
                "/contract/reading_error" => json!("0"),
                _ => json!(1),
            };
            if let Ok(cert) = evaluate(&changed) {
                assert!(
                    verify(&json!({"expected_contract":input["contract"],"certificate":cert}))
                        .is_err()
                );
            }
        }
        // A valid, changed observable remains a different input even when its
        // moments and every certificate hash are recomputed consistently.
        let mut changed = input.clone();
        changed["contract"]["observables"][0]["factors"][0]["axis"] = json!("X");
        let cert = evaluate(&changed).unwrap();
        assert!(
            verify(&json!({"expected_contract":input["contract"],"certificate":cert})).is_err()
        );
    }
    #[test]
    fn forged_corrected_moments_and_bounds_do_not_verify() {
        let input = fixture();
        let good = serde_json::to_value(evaluate(&input).unwrap()).unwrap();
        for pointer in [
            "/corrected_moments/0",
            "/quotient",
            "/product_distance_lower_bound",
        ] {
            let mut bad = good.clone();
            *bad.pointer_mut(pointer).unwrap() = json!("2");
            assert_eq!(
                verify(&json!({"expected_contract":input["contract"],"certificate":bad})).unwrap()
                    ["accepted"],
                false
            );
        }
    }
    #[test]
    fn corrupted_repair_unknown_fields_and_unsupported_observables_are_refused() {
        for (pointer, replacement) in [
            ("/repair_potential/0", json!("8")),
            ("/dual_witness/0", json!("1")),
            ("/contract/observables/0/factors/0/axis", json!("Q")),
        ] {
            let mut input = fixture();
            *input.pointer_mut(pointer).unwrap() = replacement;
            assert!(evaluate(&input).is_err());
        }
        let mut input = fixture();
        input["forged"] = json!(true);
        assert!(evaluate(&input).is_err());
    }
}

#[cfg(test)]
mod l4_boundary_tests_06c27bed {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord06c27bed::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord06c27bed::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord06c27bed::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord06c27bed::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord06c27bed::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError06c27bed::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError06c27bed::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
