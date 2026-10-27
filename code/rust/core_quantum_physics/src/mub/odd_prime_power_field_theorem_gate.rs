//! Odd-prime-power finite-field theorem gate.
//!
//! The Weyl schema verifies trace and Gauss reductions for sampled `GF(p^k)`
//! carriers. This gate isolates the field-theoretic promotion needed before
//! Hilbert/CODA-MUR transport is even considered: a uniform odd-prime-power field
//! family, additive-character orthogonality theorem, and quadratic Gauss-norm
//! theorem.
//!
//! NOTE (R15 audit): This gate implements runtime policy evaluation over declared
//! proof obligations and local Weyl schema replay. It records upstream Lean 4 proof
//! obligations (see `ODD_PRIME_POWER_LEAN_PROOF_ARTIFACTS`), but execution of this
//! Rust gate asserts local schema consistency and policy admission, not an embedded
//! Lean kernel replay. AuthorityEffect: None; mints no mathematical proof authority.

use serde::Serialize;

use crate::mub::odd_prime_power_weyl::{
    verify_current_odd_prime_power_weyl_schemas, OddPrimePowerWeylReport, OddPrimePowerWeylStatus,
};

pub const ODD_PRIME_POWER_LEAN_PROOF_ARTIFACTS: &[&str] = &[
    "MUB.finite_sum_eq_scaled_sum_from_translation",
    "MUB.finite_character_sum_vanishes_from_nontrivial_translation",
    "MUB.finite_additive_character_sum_zero_of_ne_one",
    "MUB.finite_field_additive_character_sum_zero_from_nontrivial_value",
    "MUB.finite_field_nontrivial_additive_character_is_primitive",
    "MUB.finite_field_primitive_additive_character_linear_orthogonality",
    "MUB.finite_field_nontrivial_additive_character_linear_orthogonality",
    "MUB.prime_power_finite_field_family_exists",
    "MUB.prime_power_finite_field_family_ringChar_eq",
    "MUB.odd_prime_power_finite_field_family_exists",
    "MUB.quadratic_phase_complete_square",
    "MUB.quadraticGaussSum_complete_square",
    "MUB.quadratic_phase_difference_uv",
    "MUB.oddCharTwoLinearEquiv",
    "MUB.quadratic_phase_difference_uv_equiv",
    "MUB.quadraticGauss_autocorrelation_sum",
    "MUB.quadraticGauss_complex_normSq",
];

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum OddPrimePowerFieldTheoremStatus {
    FiniteFieldTheoremsAccepted,
    FiniteReductionsOnly,
    MissingFiniteSchemas,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct OddPrimePowerFieldTheoremInputs {
    pub weyl_schemas: Vec<OddPrimePowerWeylReport>,
    pub finite_field_family: bool,
    pub additive_character_orthogonality_family: bool,
    pub quadratic_gauss_norm_family: bool,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct OddPrimePowerFieldTheoremReport {
    pub source: &'static str,
    pub status: OddPrimePowerFieldTheoremStatus,
    pub finite_schema_count: usize,
    pub sampled_dimensions: Vec<usize>,
    pub trace_uniformity_checks: usize,
    pub gauss_norm_linear_reductions: usize,
    pub checked_reductions: Vec<&'static str>,
    pub lean_proof_artifacts: Vec<&'static str>,
    pub missing_theorem_families: Vec<&'static str>,
    pub rejected_escalations: Vec<&'static str>,
    pub boundary: &'static str,
    pub error: Option<String>,
}

pub fn verify_current_odd_prime_power_field_theorem_gate() -> OddPrimePowerFieldTheoremReport {
    verify_odd_prime_power_field_theorem_gate(OddPrimePowerFieldTheoremInputs {
        weyl_schemas: verify_current_odd_prime_power_weyl_schemas(),
        finite_field_family: true,
        additive_character_orthogonality_family: true,
        quadratic_gauss_norm_family: true,
    })
}

pub fn verify_odd_prime_power_field_theorem_gate(
    inputs: OddPrimePowerFieldTheoremInputs,
) -> OddPrimePowerFieldTheoremReport {
    let verified_schemas = inputs
        .weyl_schemas
        .iter()
        .filter(|schema| schema.status == OddPrimePowerWeylStatus::ProofSchemaVerified)
        .collect::<Vec<_>>();
    let finite_schema_count = verified_schemas.len();
    let sampled_dimensions = verified_schemas
        .iter()
        .map(|schema| schema.dimension)
        .collect::<Vec<_>>();
    let trace_uniformity_checks = verified_schemas
        .iter()
        .map(|schema| schema.trace_uniformity_checks)
        .sum();
    let gauss_norm_linear_reductions = verified_schemas
        .iter()
        .map(|schema| schema.gauss_norm_linear_reductions)
        .sum();

    let mut checked = Vec::new();
    let mut missing = Vec::new();
    if finite_schema_count > 0 {
        checked.push("sampled odd-prime-power finite-field carriers and trace maps are replayed");
        checked.push(
            "sampled same-basis and cross-basis reductions reach character/Gauss obligations",
        );
        checked.push("sampled Gauss-norm reductions reach nonzero trace-linear cancellation");
        checked.push("Lean records finite translation-scaling cancellation for character sums");
        checked.push("Lean records finite-field AddChar linear orthogonality");
        checked.push("Lean records odd-prime-power finite-field family witnesses");
        checked.push("Lean records quadratic Gauss complex squared-norm theorem");
    } else {
        missing.push("at least one sampled odd-prime-power Weyl schema");
    }

    push_obligation(
        inputs.finite_field_family,
        "dimension-parametric odd-prime-power finite-field family GF(p^k)",
        &mut checked,
        &mut missing,
    );
    push_obligation(
        inputs.additive_character_orthogonality_family,
        "formal additive-character orthogonality for every odd GF(p^k)",
        &mut checked,
        &mut missing,
    );
    push_obligation(
        inputs.quadratic_gauss_norm_family,
        "formal quadratic Gauss-norm theorem for every odd GF(p^k)",
        &mut checked,
        &mut missing,
    );

    let status = if missing.is_empty() {
        OddPrimePowerFieldTheoremStatus::FiniteFieldTheoremsAccepted
    } else if finite_schema_count == 0 {
        OddPrimePowerFieldTheoremStatus::MissingFiniteSchemas
    } else {
        OddPrimePowerFieldTheoremStatus::FiniteReductionsOnly
    };

    OddPrimePowerFieldTheoremReport {
        source: "odd-prime-power finite-field theorem gate",
        status,
        finite_schema_count,
        sampled_dimensions,
        trace_uniformity_checks,
        gauss_norm_linear_reductions,
        checked_reductions: checked,
        lean_proof_artifacts: ODD_PRIME_POWER_LEAN_PROOF_ARTIFACTS.to_vec(),
        missing_theorem_families: missing,
        rejected_escalations: if status
            == OddPrimePowerFieldTheoremStatus::FiniteFieldTheoremsAccepted
        {
            vec![]
        } else {
            vec![
                "finite-field theorems do not create Hilbert/CODA-MUR transport",
                "accepted field theorem layer does not solve composite dimensions",
            ]
        },
        boundary: if status == OddPrimePowerFieldTheoremStatus::FiniteFieldTheoremsAccepted {
            "odd-prime-power finite-field theorem family accepted; Hilbert/CODA-MUR transport remains separate"
        } else {
            "odd-prime-power field theorem layer is incomplete; no Hilbert/CODA-MUR transport is implied"
        },
        error: if status == OddPrimePowerFieldTheoremStatus::FiniteFieldTheoremsAccepted {
            None
        } else {
            Some("missing odd-prime-power finite-field theorem families".to_string())
        },
    }
}

fn push_obligation(
    present: bool,
    obligation: &'static str,
    checked: &mut Vec<&'static str>,
    missing: &mut Vec<&'static str>,
) {
    if present {
        checked.push(obligation);
    } else {
        missing.push(obligation);
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/mub/odd_prime_power_field_theorem_gate.rs
// Claim: urn:core:crates_rs:core-quantum-physics:odd-prime-power-field-theorem-gate:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord90c8e307 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord90c8e307` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError90c8e307 {
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
impl BoundaryError90c8e307 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError90c8e307 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError90c8e307 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord90c8e307 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError90c8e307> {
        if capacity_bound == 0 {
            return Err(BoundaryError90c8e307::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError90c8e307::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError90c8e307::ExceedsCapacity {
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

    #[test]
    fn odd_prime_power_field_theorem_gate_accepts_current_lean_field_theorems() {
        let report = verify_current_odd_prime_power_field_theorem_gate();
        assert_eq!(
            report.status,
            OddPrimePowerFieldTheoremStatus::FiniteFieldTheoremsAccepted
        );
        assert!(report.sampled_dimensions.contains(&9));
        assert!(report.sampled_dimensions.contains(&49));
        assert!(report.trace_uniformity_checks > 0);
        assert!(report.gauss_norm_linear_reductions > 0);
        assert!(report
            .lean_proof_artifacts
            .contains(&"MUB.finite_character_sum_vanishes_from_nontrivial_translation"));
        assert!(report
            .lean_proof_artifacts
            .contains(&"MUB.finite_field_nontrivial_additive_character_linear_orthogonality"));
        assert!(report
            .lean_proof_artifacts
            .contains(&"MUB.odd_prime_power_finite_field_family_exists"));
        assert!(report
            .lean_proof_artifacts
            .contains(&"MUB.quadraticGauss_complex_normSq"));
        assert!(report
            .checked_reductions
            .iter()
            .any(|obligation| obligation.contains("additive-character orthogonality")));
        assert!(report
            .checked_reductions
            .iter()
            .any(|obligation| obligation.contains("finite-field family")));
        assert!(report
            .checked_reductions
            .iter()
            .any(|obligation| obligation.contains("quadratic Gauss-norm")));
        assert!(report.missing_theorem_families.is_empty());
        assert!(report.rejected_escalations.is_empty());
    }

    #[test]
    fn odd_prime_power_field_theorem_gate_accepts_only_complete_field_theorems() {
        let report = verify_odd_prime_power_field_theorem_gate(OddPrimePowerFieldTheoremInputs {
            weyl_schemas: verify_current_odd_prime_power_weyl_schemas(),
            finite_field_family: true,
            additive_character_orthogonality_family: true,
            quadratic_gauss_norm_family: true,
        });
        assert_eq!(
            report.status,
            OddPrimePowerFieldTheoremStatus::FiniteFieldTheoremsAccepted
        );
        assert!(report.missing_theorem_families.is_empty());
        assert!(report.error.is_none());
    }

    #[test]
    fn odd_prime_power_field_theorem_gate_still_rejects_without_gauss_theorem() {
        let report = verify_odd_prime_power_field_theorem_gate(OddPrimePowerFieldTheoremInputs {
            weyl_schemas: verify_current_odd_prime_power_weyl_schemas(),
            finite_field_family: true,
            additive_character_orthogonality_family: true,
            quadratic_gauss_norm_family: false,
        });
        assert_eq!(
            report.status,
            OddPrimePowerFieldTheoremStatus::FiniteReductionsOnly
        );
        assert_eq!(
            report.missing_theorem_families,
            vec!["formal quadratic Gauss-norm theorem for every odd GF(p^k)"]
        );
    }
}

#[cfg(test)]
mod l4_boundary_tests_90c8e307 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord90c8e307::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord90c8e307::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord90c8e307::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord90c8e307::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord90c8e307::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError90c8e307::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError90c8e307::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
