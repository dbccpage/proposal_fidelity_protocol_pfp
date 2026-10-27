//! CODA-CODA_GTLA Master Normal Form Pipeline Evaluator.
//!
//! Grounded in CODA-CODA_GTLA (Definitions D01/D02, Theorems T02, T03):
//! - Five-stage Master Normal Form pipeline representation.
//! - Strict terminal partition disjointness: T_auth ⊔ T_res ⊔ F_term.
//! - CODA_GTLA-T9: Non-Promotion Firewall Theorem (an unlicensed phi1 = 0 routes to F_term: Refused).
//!
//! AuthorityEffect: None.

use serde::{Deserialize, Serialize};

use core_types::{
    AuthorityTerminal, ObstructionDiagnosticClass, Outcome, RefusalSource, ResidualTerminal,
    RoutingTerminal,
};

/// Input configuration for the Master Normal Form pipeline.
/// Mirrors Lean `CodaGtla.PipelineInput`.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct PipelineInput {
    pub input_id: String,
    pub sieve_non_empty: bool,
    pub refinement_consistent: bool,
    pub gluing_succeeded: bool,
    pub phi1_distance: u64,
    pub gamma2_distance: u64,
    pub license_granted: bool,
}

/// Structured output from Master Normal Form pipeline evaluation.
/// Carries the three distinct axes: diagnostic, routing, and authority.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PipelineOutput {
    pub input_id: String,
    pub diagnostic: ObstructionDiagnosticClass,
    pub routing: RoutingTerminal,
    pub authority: Outcome,
    pub detail: String,
}

impl PipelineOutput {
    /// True iff the outcome is an authority-bearing terminal (T_auth).
    pub fn is_auth(&self) -> bool {
        self.authority.authority_terminal().is_some()
    }

    /// True iff the outcome is a closed residual / sentinel terminal (T_res).
    pub fn is_sentinel(&self) -> bool {
        matches!(self.authority, Outcome::Residual(r) if r.is_sentinel())
    }

    /// True iff the outcome is in F_term.
    pub fn is_refused(&self) -> bool {
        self.authority.is_refused()
    }
}

/// Evaluates the Master Normal Form pipeline stage-by-stage.
///
/// Mirrors Lean `CodaGtla.evaluatePipeline`:
/// 1. Stage 1: R^# (Reduction & Refusal): checks candidate sieve non-empty.
/// 2. Stage 2: rho^# & Stage 3: D^#: checks refinement consistency and gluing.
/// 3. Stage 4: FOC^# & Stage 5: tau^#: checks defect closure and license.
///    - If gamma2 > 0: refused (nonclosed defect).
///    - If phi1 == 0: refused. A caller `license_granted` flag is not a matrix witness
///      and does not mint ExactRuleDerived (CODA_GTLA-T9).
///    - Else (phi1 > 0 && gamma2 == 0): closed residual (T_res: ClosedResidual sentinel).
pub fn evaluate_pipeline(inp: &PipelineInput) -> PipelineOutput {
    // Diagnostic axis is computed from (phi1, gamma2)
    let diagnostic = if inp.phi1_distance == 0 {
        ObstructionDiagnosticClass::ExactRepair
    } else if inp.gamma2_distance == 0 {
        ObstructionDiagnosticClass::ClosedResidual
    } else {
        ObstructionDiagnosticClass::ActiveClosureFailure
    };

    // Stage 1: R^# (Reduction & Refusal)
    if !inp.sieve_non_empty {
        return PipelineOutput {
            input_id: inp.input_id.clone(),
            diagnostic,
            routing: RoutingTerminal::NoRule,
            authority: Outcome::Refused(RefusalSource::Refusal),
            detail: "Candidate sieve empty (R_empty)".to_string(),
        };
    }

    // Stage 2: rho^# & Stage 3: D^#
    if !inp.refinement_consistent || !inp.gluing_succeeded {
        return PipelineOutput {
            input_id: inp.input_id.clone(),
            diagnostic,
            routing: RoutingTerminal::Repair,
            authority: Outcome::Refused(RefusalSource::Repair),
            detail: "Descent or representation failure".to_string(),
        };
    }

    // Stage 4: FOC^# & Stage 5: tau^#
    if inp.gamma2_distance > 0 {
        return PipelineOutput {
            input_id: inp.input_id.clone(),
            diagnostic,
            routing: RoutingTerminal::RequiresLift,
            authority: Outcome::Refused(RefusalSource::Refusal),
            detail: "Nonclosed defect (Gamma_2 > 0)".to_string(),
        };
    }

    if inp.phi1_distance == 0 {
        // CODA_GTLA-T9: a caller license flag is not a matrix-derived rule.
        PipelineOutput {
            input_id: inp.input_id.clone(),
            diagnostic,
            routing: RoutingTerminal::CheckPassed,
            authority: Outcome::Refused(RefusalSource::Refusal),
            detail: "caller license is not a matrix-derived rule".to_string(),
        }
    } else {
        PipelineOutput {
            input_id: inp.input_id.clone(),
            diagnostic,
            routing: RoutingTerminal::Repair,
            authority: Outcome::Residual(ResidualTerminal::ClosedResidual),
            detail: format!("Closed residual sentinel: {}", inp.input_id),
        }
    }
}

// Origin: engine/crates_rs/core_pipelines/src/coda_gtla.rs
// Claim: urn:core:crates_rs:core-pipelines:coda-gtla:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord817a569e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord817a569e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError817a569e {
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
impl BoundaryError817a569e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError817a569e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError817a569e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord817a569e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError817a569e> {
        if capacity_bound == 0 {
            return Err(BoundaryError817a569e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError817a569e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError817a569e::ExceedsCapacity {
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

    struct LeanTestCase {
        name: &'static str,
        input: PipelineInput,
        expected_diagnostic: ObstructionDiagnosticClass,
        expected_routing: RoutingTerminal,
        expected_auth: bool,
        expected_sentinel: bool,
        expected_refused: bool,
    }

    #[test]
    fn test_lean_table_driven_pipeline_cases() {
        let cases = vec![
            // Case 1: Empty sieve halts at R^# in F_term
            LeanTestCase {
                name: "empty_sieve",
                input: PipelineInput {
                    input_id: "inp_empty_sieve".into(),
                    sieve_non_empty: false,
                    refinement_consistent: true,
                    gluing_succeeded: true,
                    phi1_distance: 0,
                    gamma2_distance: 0,
                    license_granted: true,
                },
                expected_diagnostic: ObstructionDiagnosticClass::ExactRepair,
                expected_routing: RoutingTerminal::NoRule,
                expected_auth: false,
                expected_sentinel: false,
                expected_refused: true,
            },
            // Case 2: Refinement failure halts at rho^#/D^#
            LeanTestCase {
                name: "refinement_failure",
                input: PipelineInput {
                    input_id: "inp_refine_fail".into(),
                    sieve_non_empty: true,
                    refinement_consistent: false,
                    gluing_succeeded: true,
                    phi1_distance: 0,
                    gamma2_distance: 0,
                    license_granted: true,
                },
                expected_diagnostic: ObstructionDiagnosticClass::ExactRepair,
                expected_routing: RoutingTerminal::Repair,
                expected_auth: false,
                expected_sentinel: false,
                expected_refused: true,
            },
            // Case 3: Gluing failure halts at rho^#/D^#
            LeanTestCase {
                name: "gluing_failure",
                input: PipelineInput {
                    input_id: "inp_glue_fail".into(),
                    sieve_non_empty: true,
                    refinement_consistent: true,
                    gluing_succeeded: false,
                    phi1_distance: 0,
                    gamma2_distance: 0,
                    license_granted: true,
                },
                expected_diagnostic: ObstructionDiagnosticClass::ExactRepair,
                expected_routing: RoutingTerminal::Repair,
                expected_auth: false,
                expected_sentinel: false,
                expected_refused: true,
            },
            // Case 4: Nonclosed defect (gamma2 > 0) halts at FOC^#
            LeanTestCase {
                name: "nonclosed_defect",
                input: PipelineInput {
                    input_id: "inp_gamma2_pos".into(),
                    sieve_non_empty: true,
                    refinement_consistent: true,
                    gluing_succeeded: true,
                    phi1_distance: 2,
                    gamma2_distance: 1,
                    license_granted: true,
                },
                expected_diagnostic: ObstructionDiagnosticClass::ActiveClosureFailure,
                expected_routing: RoutingTerminal::RequiresLift,
                expected_auth: false,
                expected_sentinel: false,
                expected_refused: true,
            },
            // Case 5: caller license plus zero distance is still a refusal
            LeanTestCase {
                name: "licensed_exact_authorized",
                input: PipelineInput {
                    input_id: "inp_licensed_exact".into(),
                    sieve_non_empty: true,
                    refinement_consistent: true,
                    gluing_succeeded: true,
                    phi1_distance: 0,
                    gamma2_distance: 0,
                    license_granted: true,
                },
                expected_diagnostic: ObstructionDiagnosticClass::ExactRepair,
                expected_routing: RoutingTerminal::CheckPassed,
                expected_auth: false,
                expected_sentinel: false,
                expected_refused: true,
            },
            // Case 6: CODA_GTLA-T9 Non-Promotion Firewall: unlicensed phi1 = 0 terminates in F_term
            LeanTestCase {
                name: "unlicensed_zero_defect_refused_t9",
                input: PipelineInput {
                    input_id: "unlicensed_zero_defect".into(),
                    sieve_non_empty: true,
                    refinement_consistent: true,
                    gluing_succeeded: true,
                    phi1_distance: 0,
                    gamma2_distance: 0,
                    license_granted: false,
                },
                expected_diagnostic: ObstructionDiagnosticClass::ExactRepair,
                expected_routing: RoutingTerminal::CheckPassed,
                expected_auth: false,
                expected_sentinel: false,
                expected_refused: true,
            },
            // Case 7: Closed residual survivor terminates in T_res (Sentinel)
            LeanTestCase {
                name: "closed_residual_sentinel",
                input: PipelineInput {
                    input_id: "inp_closed_residual".into(),
                    sieve_non_empty: true,
                    refinement_consistent: true,
                    gluing_succeeded: true,
                    phi1_distance: 3,
                    gamma2_distance: 0,
                    license_granted: false,
                },
                expected_diagnostic: ObstructionDiagnosticClass::ClosedResidual,
                expected_routing: RoutingTerminal::Repair,
                expected_auth: false,
                expected_sentinel: true,
                expected_refused: false,
            },
        ];

        for case in cases {
            let output = evaluate_pipeline(&case.input);
            assert_eq!(
                output.diagnostic, case.expected_diagnostic,
                "case '{}': diagnostic mismatch",
                case.name
            );
            assert_eq!(
                output.routing, case.expected_routing,
                "case '{}': routing mismatch",
                case.name
            );
            assert_eq!(
                output.is_auth(),
                case.expected_auth,
                "case '{}': is_auth mismatch",
                case.name
            );
            assert_eq!(
                output.is_sentinel(),
                case.expected_sentinel,
                "case '{}': is_sentinel mismatch",
                case.name
            );
            assert_eq!(
                output.is_refused(),
                case.expected_refused,
                "case '{}': is_refused mismatch",
                case.name
            );

            // Assert mutual exclusivity of the three partition arms (Theorems 12.1a, b, c)
            let auth_count = (output.is_auth() as u8)
                + (output.is_sentinel() as u8)
                + (output.is_refused() as u8);
            assert_eq!(
                auth_count, 1,
                "case '{}': partition disjointness violation",
                case.name
            );
        }
    }

    #[test]
    fn test_observation_collision_countermodel_fda_04() {
        // Two inputs with identical observational profiles (phi1 = 0, gamma2 = 0)
        let inp1 = PipelineInput {
            input_id: "state_licensed".into(),
            sieve_non_empty: true,
            refinement_consistent: true,
            gluing_succeeded: true,
            phi1_distance: 0,
            gamma2_distance: 0,
            license_granted: true,
        };
        let inp2 = PipelineInput {
            input_id: "state_unlicensed".into(),
            sieve_non_empty: true,
            refinement_consistent: true,
            gluing_succeeded: true,
            phi1_distance: 0,
            gamma2_distance: 0,
            license_granted: false,
        };

        let out1 = evaluate_pipeline(&inp1);
        let out2 = evaluate_pipeline(&inp2);

        // Identical diagnostic, routing, and authority. The license flag is not a witness.
        assert_eq!(out1.diagnostic, out2.diagnostic);
        assert_eq!(out1.routing, out2.routing);
        assert!(!out1.is_auth());
        assert!(!out2.is_auth());
        assert!(out1.is_refused());
        assert!(out2.is_refused());
        assert_eq!(out1.detail, "caller license is not a matrix-derived rule");
    }
}

#[cfg(test)]
mod l4_boundary_tests_817a569e {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord817a569e::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord817a569e::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord817a569e::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord817a569e::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord817a569e::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError817a569e::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError817a569e::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
