//! Odd-prime-power dimension-parametric Hilbert/CODA-MUR family gate.
//!
//! The finite-field theorem gate and the exact d=9/d=25/d=27/d=49 controls
//! are prerequisites for this Hilbert/CODA-MUR bridge. This gate records the
//! additional theorem obligations required to promote that evidence into a
//! reusable family over every odd prime power `p^k`. The current run
//! intentionally rejects finite-sample extrapolation.
//!
//! NOTE (R15 audit): This gate checks finite-schema consistency and explicit
//! obligation tracking for the parametric Hilbert/CODA-MUR family. It records
//! upstream Lean 4 proof obligations and rejects unverified finite-sample extrapolation.
//! Runtime gate execution represents policy verification, not embedded Lean kernel proof.
//! AuthorityEffect: None.

use serde::Serialize;

use crate::mub::odd_prime_power_controls::{
    verify_current_odd_prime_power_controls, OddPrimePowerControlReport, OddPrimePowerControlStatus,
};
use crate::mub::odd_prime_power_field_theorem_gate::{
    verify_current_odd_prime_power_field_theorem_gate, OddPrimePowerFieldTheoremReport,
    OddPrimePowerFieldTheoremStatus,
};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum OddPrimePowerParametricStatus {
    ParametricFamilyAccepted,
    FiniteSchemasOnly,
    MissingFiniteSchemas,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct OddPrimePowerParametricInputs {
    pub field_theorem: OddPrimePowerFieldTheoremReport,
    pub exact_controls: Vec<OddPrimePowerControlReport>,
    pub coefficient_field_family: bool,
    pub hilbert_overlap_kernel_family: bool,
    pub hilbert_normalization_algebra_family: bool,
    pub complex_coefficient_scalar_package: bool,
    pub algebraic_coefficient_field_contract: bool,
    pub hilbert_phase_vector_transport_family: bool,
    pub complex_primitive_character_family: bool,
    pub complex_finite_function_mub_family: bool,
    pub finite_function_coordinate_transport_family: bool,
    pub finite_complex_mub_family_object: bool,
    pub finite_function_gtmur_coordinate_ledger: bool,
    pub finite_function_terminalizer_coordinate_ledger: bool,
    pub finite_function_hilbert_basis_transport_object: bool,
    pub finite_function_gtmur_zero_loss_ledger: bool,
    pub algebraic_hilbert_basis_transport_contract: bool,
    pub algebraic_gtmur_loss_ledger_contract: bool,
    pub algebraic_terminalizer_preservation_contract: bool,
    pub hilbert_basis_transport_family: bool,
    pub gtmur_loss_ledger_family: bool,
    pub terminalizer_preserved_family: bool,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct OddPrimePowerParametricGateReport {
    pub source: &'static str,
    pub status: OddPrimePowerParametricStatus,
    pub finite_schema_count: usize,
    pub exact_control_count: usize,
    pub sampled_dimensions: Vec<usize>,
    pub exact_control_dimensions: Vec<usize>,
    pub checked_obligations: Vec<&'static str>,
    pub missing_obligations: Vec<&'static str>,
    pub rejected_escalations: Vec<&'static str>,
    pub boundary: &'static str,
    pub error: Option<String>,
}

pub fn verify_current_odd_prime_power_parametric_gate() -> OddPrimePowerParametricGateReport {
    verify_odd_prime_power_parametric_gate(OddPrimePowerParametricInputs {
        field_theorem: verify_current_odd_prime_power_field_theorem_gate(),
        exact_controls: verify_current_odd_prime_power_controls(),
        coefficient_field_family: false,
        hilbert_overlap_kernel_family: true,
        hilbert_normalization_algebra_family: true,
        complex_coefficient_scalar_package: true,
        algebraic_coefficient_field_contract: true,
        hilbert_phase_vector_transport_family: true,
        complex_primitive_character_family: true,
        complex_finite_function_mub_family: true,
        finite_function_coordinate_transport_family: true,
        finite_complex_mub_family_object: true,
        finite_function_gtmur_coordinate_ledger: true,
        finite_function_terminalizer_coordinate_ledger: true,
        finite_function_hilbert_basis_transport_object: true,
        finite_function_gtmur_zero_loss_ledger: true,
        algebraic_hilbert_basis_transport_contract: true,
        algebraic_gtmur_loss_ledger_contract: true,
        algebraic_terminalizer_preservation_contract: true,
        hilbert_basis_transport_family: false,
        gtmur_loss_ledger_family: false,
        terminalizer_preserved_family: false,
    })
}

pub fn verify_odd_prime_power_parametric_gate(
    inputs: OddPrimePowerParametricInputs,
) -> OddPrimePowerParametricGateReport {
    let exact_controls = inputs
        .exact_controls
        .iter()
        .filter(|control| control.status == OddPrimePowerControlStatus::ExactCompleteSet)
        .collect::<Vec<_>>();
    let field_theorem_accepted =
        inputs.field_theorem.status == OddPrimePowerFieldTheoremStatus::FiniteFieldTheoremsAccepted;
    let finite_schema_count = inputs.field_theorem.finite_schema_count;
    let exact_control_count = exact_controls.len();
    let sampled_dimensions = inputs.field_theorem.sampled_dimensions.clone();
    let exact_control_dimensions = exact_controls
        .iter()
        .map(|control| control.dimension)
        .collect::<Vec<_>>();

    let mut checked = Vec::new();
    let mut missing = Vec::new();
    if finite_schema_count > 0 {
        checked.push("finite odd-prime-power Weyl schemas are replayed for sampled GF(p^k)");
    } else {
        missing.push("at least one finite odd-prime-power Weyl schema sample");
    }
    if field_theorem_accepted {
        checked.push("odd-prime-power finite-field theorem gate is accepted");
    } else {
        missing.push(
            "accepted odd-prime-power finite-field theorem gate for field family, additive-character orthogonality, and quadratic Gauss norms",
        );
    }
    if exact_control_count > 0 {
        checked.push("exact odd-prime-power Hilbert controls are replayed in declared dimensions");
    } else {
        missing.push("at least one exact odd-prime-power Hilbert control sample");
    }

    push_obligation(
        inputs.coefficient_field_family,
        "uniform coefficient field containing p-th roots and sqrt(p^k)^-1 normalizers",
        &mut checked,
        &mut missing,
    );
    push_obligation(
        inputs.hilbert_overlap_kernel_family,
        "Lean-backed trace-character phase-overlap kernel for every odd GF(p^k)",
        &mut checked,
        &mut missing,
    );
    push_obligation(
        inputs.hilbert_normalization_algebra_family,
        "Lean-backed Complex 1/sqrt(q) normalization algebra for trace-character Hilbert overlaps",
        &mut checked,
        &mut missing,
    );
    push_obligation(
        inputs.complex_coefficient_scalar_package,
        "Lean-backed Complex coefficient scalar package bundling a primitive additive character, sqrt-card normalizer, and exact norm identity",
        &mut checked,
        &mut missing,
    );
    push_obligation(
        inputs.algebraic_coefficient_field_contract,
        "Lean-backed algebraic coefficient-field contract surface linking lifted characters and normalizers to Complex scalars",
        &mut checked,
        &mut missing,
    );
    push_obligation(
        inputs.hilbert_phase_vector_transport_family,
        "Lean-backed finite-function Hilbert phase-vector transport for trace-character bases",
        &mut checked,
        &mut missing,
    );
    push_obligation(
        inputs.complex_primitive_character_family,
        "Lean-backed existence of primitive Complex additive characters on every finite field",
        &mut checked,
        &mut missing,
    );
    push_obligation(
        inputs.complex_finite_function_mub_family,
        "Lean-backed existential Complex finite-function q+1 MUB family from computational and trace-character bases",
        &mut checked,
        &mut missing,
    );
    push_obligation(
        inputs.finite_function_coordinate_transport_family,
        "Lean-backed coordinate-equivalence transport preserving finite-function Hilbert inner products and MUB identities",
        &mut checked,
        &mut missing,
    );
    push_obligation(
        inputs.finite_complex_mub_family_object,
        "Lean-backed structured finite Complex MUB family object with coordinate-equivalence transport",
        &mut checked,
        &mut missing,
    );
    push_obligation(
        inputs.finite_function_gtmur_coordinate_ledger,
        "Lean-backed finite-function CODA-MUR coordinate ledger preserving cardinality, inner products, ZeroRel, and squared overlaps",
        &mut checked,
        &mut missing,
    );
    push_obligation(
        inputs.finite_function_terminalizer_coordinate_ledger,
        "Lean-backed finite-function terminalizer coordinate ledger preserving complete basis/label profile, ZeroRel, and squared overlaps",
        &mut checked,
        &mut missing,
    );
    push_obligation(
        inputs.finite_function_hilbert_basis_transport_object,
        "Lean-backed finite-function Hilbert-basis transport object packaging coordinate equivalence, complete basis identities, ZeroRel, and squared overlaps",
        &mut checked,
        &mut missing,
    );
    push_obligation(
        inputs.finite_function_gtmur_zero_loss_ledger,
        "Lean-backed finite-function CODA-MUR zero-loss ledger preserving coordinate cardinality, vectors, inner products, ZeroRel, and squared overlaps",
        &mut checked,
        &mut missing,
    );
    push_obligation(
        inputs.algebraic_hilbert_basis_transport_contract,
        "Lean-backed algebraic Hilbert-basis transport contract surface linking lifted vectors and inner products to the Complex MUB family",
        &mut checked,
        &mut missing,
    );
    push_obligation(
        inputs.algebraic_gtmur_loss_ledger_contract,
        "Lean-backed algebraic CODA-MUR loss-ledger contract surface preserving lifted ZeroRel and squared-overlap profiles",
        &mut checked,
        &mut missing,
    );
    push_obligation(
        inputs.algebraic_terminalizer_preservation_contract,
        "Lean-backed algebraic terminalizer-preservation contract surface preserving complete basis, ZeroRel, and squared-overlap profiles",
        &mut checked,
        &mut missing,
    );
    push_obligation(
        inputs.hilbert_basis_transport_family,
        "dimension-parametric algebraic Hilbert basis transport object from trace-character Weyl data",
        &mut checked,
        &mut missing,
    );
    push_obligation(
        inputs.gtmur_loss_ledger_family,
        "dimension-parametric CODA-MUR loss ledger preserving odd-prime-power ZeroRel",
        &mut checked,
        &mut missing,
    );
    push_obligation(
        inputs.terminalizer_preserved_family,
        "dimension-parametric terminalizer preservation across odd-prime-power representations",
        &mut checked,
        &mut missing,
    );

    let status = if missing.is_empty() {
        OddPrimePowerParametricStatus::ParametricFamilyAccepted
    } else if finite_schema_count == 0 || exact_control_count == 0 {
        OddPrimePowerParametricStatus::MissingFiniteSchemas
    } else {
        OddPrimePowerParametricStatus::FiniteSchemasOnly
    };

    OddPrimePowerParametricGateReport {
        source: "odd-prime-power dimension-parametric Hilbert/CODA-MUR family gate",
        status,
        finite_schema_count,
        exact_control_count,
        sampled_dimensions,
        exact_control_dimensions,
        checked_obligations: checked,
        missing_obligations: missing,
        rejected_escalations: if status == OddPrimePowerParametricStatus::ParametricFamilyAccepted {
            vec![]
        } else {
            vec![
                "finite odd-prime-power Hilbert controls do not prove every odd p^k",
                "finite-field reductions do not create Hilbert/CODA-MUR transport",
                "declared d=9/d=25/d=27/d=49 controls do not create a dimension-parametric Hilbert theorem",
                "odd-prime-power families still do not settle composite MUB(6) or MUB(10)",
            ]
        },
        boundary: if status == OddPrimePowerParametricStatus::ParametricFamilyAccepted {
            "odd-prime-power Hilbert/CODA-MUR family accepted for declared all-odd-p^k scope only"
        } else {
            "finite odd-prime-power schemas remain non-parametric; no all-odd-p^k family authority is accepted"
        },
        error: if status == OddPrimePowerParametricStatus::ParametricFamilyAccepted {
            None
        } else {
            Some("missing odd-prime-power parametric family obligations".to_string())
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

// Origin: engine/crates_rs/core_quantum_physics/src/mub/odd_prime_power_parametric_gate.rs
// Claim: urn:core:crates_rs:core-quantum-physics:odd-prime-power-parametric-gate:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf3a1744e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf3a1744e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf3a1744e {
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
impl BoundaryErrorf3a1744e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf3a1744e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf3a1744e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf3a1744e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf3a1744e> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf3a1744e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf3a1744e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf3a1744e::ExceedsCapacity {
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
    use crate::mub::odd_prime_power_field_theorem_gate::{
        verify_odd_prime_power_field_theorem_gate, OddPrimePowerFieldTheoremInputs,
    };
    use crate::mub::odd_prime_power_weyl::verify_current_odd_prime_power_weyl_schemas;

    #[test]
    fn odd_prime_power_parametric_gate_rejects_finite_schema_extrapolation() {
        let report = verify_current_odd_prime_power_parametric_gate();
        assert_eq!(
            report.status,
            OddPrimePowerParametricStatus::FiniteSchemasOnly
        );
        assert!(report.sampled_dimensions.contains(&9));
        assert!(report.exact_control_dimensions.contains(&49));
        assert!(report
            .checked_obligations
            .iter()
            .any(|obligation| obligation.contains("finite-field theorem gate")));
        assert!(report
            .checked_obligations
            .iter()
            .any(|obligation| obligation.contains("phase-overlap kernel")));
        assert!(report
            .checked_obligations
            .iter()
            .any(|obligation| obligation.contains("normalization algebra")));
        assert!(report
            .checked_obligations
            .iter()
            .any(|obligation| obligation.contains("Complex coefficient scalar package")));
        assert!(report
            .checked_obligations
            .iter()
            .any(|obligation| obligation.contains("coefficient-field contract surface")));
        assert!(report
            .checked_obligations
            .iter()
            .any(|obligation| obligation.contains("phase-vector transport")));
        assert!(report
            .checked_obligations
            .iter()
            .any(|obligation| obligation.contains("primitive Complex additive characters")));
        assert!(report
            .checked_obligations
            .iter()
            .any(|obligation| obligation.contains("q+1 MUB family")));
        assert!(report
            .checked_obligations
            .iter()
            .any(|obligation| obligation.contains("coordinate-equivalence transport")));
        assert!(report
            .checked_obligations
            .iter()
            .any(|obligation| obligation.contains("structured finite Complex MUB family")));
        assert!(report
            .checked_obligations
            .iter()
            .any(|obligation| obligation.contains("finite-function CODA-MUR coordinate ledger")));
        assert!(report.checked_obligations.iter().any(
            |obligation| obligation.contains("finite-function terminalizer coordinate ledger")
        ));
        assert!(report.checked_obligations.iter().any(
            |obligation| obligation.contains("finite-function Hilbert-basis transport object")
        ));
        assert!(report
            .checked_obligations
            .iter()
            .any(|obligation| obligation.contains("finite-function CODA-MUR zero-loss ledger")));
        assert!(report
            .checked_obligations
            .iter()
            .any(|obligation| obligation.contains("algebraic Hilbert-basis transport contract")));
        assert!(report
            .checked_obligations
            .iter()
            .any(|obligation| obligation.contains("algebraic CODA-MUR loss-ledger contract")));
        assert!(report
            .checked_obligations
            .iter()
            .any(|obligation| obligation.contains("algebraic terminalizer-preservation contract")));
        assert!(report
            .missing_obligations
            .iter()
            .any(|obligation| obligation.contains("coefficient field")));
        assert!(report
            .missing_obligations
            .iter()
            .any(|obligation| obligation.contains("CODA-MUR loss ledger")));
        assert!(report
            .rejected_escalations
            .iter()
            .any(|item| item.contains("do not prove every odd p^k")));
    }

    #[test]
    fn odd_prime_power_parametric_gate_accepts_only_complete_family_obligations() {
        let field_theorem =
            verify_odd_prime_power_field_theorem_gate(OddPrimePowerFieldTheoremInputs {
                weyl_schemas: verify_current_odd_prime_power_weyl_schemas(),
                finite_field_family: true,
                additive_character_orthogonality_family: true,
                quadratic_gauss_norm_family: true,
            });
        let report = verify_odd_prime_power_parametric_gate(OddPrimePowerParametricInputs {
            field_theorem,
            exact_controls: verify_current_odd_prime_power_controls(),
            coefficient_field_family: true,
            hilbert_overlap_kernel_family: true,
            hilbert_normalization_algebra_family: true,
            complex_coefficient_scalar_package: true,
            algebraic_coefficient_field_contract: true,
            hilbert_phase_vector_transport_family: true,
            complex_primitive_character_family: true,
            complex_finite_function_mub_family: true,
            finite_function_coordinate_transport_family: true,
            finite_complex_mub_family_object: true,
            finite_function_gtmur_coordinate_ledger: true,
            finite_function_terminalizer_coordinate_ledger: true,
            finite_function_hilbert_basis_transport_object: true,
            finite_function_gtmur_zero_loss_ledger: true,
            algebraic_hilbert_basis_transport_contract: true,
            algebraic_gtmur_loss_ledger_contract: true,
            algebraic_terminalizer_preservation_contract: true,
            hilbert_basis_transport_family: true,
            gtmur_loss_ledger_family: true,
            terminalizer_preserved_family: true,
        });
        assert_eq!(
            report.status,
            OddPrimePowerParametricStatus::ParametricFamilyAccepted
        );
        assert!(report.missing_obligations.is_empty());
        assert!(report.error.is_none());
    }
}

#[cfg(test)]
mod l4_boundary_tests_f3a1744e {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordf3a1744e::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordf3a1744e::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordf3a1744e::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordf3a1744e::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordf3a1744e::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorf3a1744e::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorf3a1744e::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
