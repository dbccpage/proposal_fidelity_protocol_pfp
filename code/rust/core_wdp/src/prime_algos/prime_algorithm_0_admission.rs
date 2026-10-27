//! Admission gate for Algorithm Prime 000.
//!
//! # Two-Phase Discipline
//!
//! Prime 000 has two distinct phases:
//! 1. **Admission** (7-step declaration): carrier, primitive difference, ZeroRel,
//!    cochain justification, observer, and witnesses.
//! 2. **Execution** (12-step fill): residual projection, measurement of (Φ₁, Γ₂),
//!    operator/lift search, survivor routing, terminalization, and post-terminal
//!    literature comparison.
//!
//! The admission gate refuses before any Φ₁ or Γ₂ is computed when no observer,
//! or no witness-or-refusal route, is declared. Because [`run_prime_algorithm_0`](crate::prime_algos::prime_algorithm_0::run_admitted)
//! accepts only an [`AdmittedDeclaration`], typestate makes measuring before
//! admission unrepresentable.
//!
//! AuthorityEffect: None.

use crate::prime_algos::prime_algorithm_0::{
    CochainSlot, CochainWindow, DeclarationFill, DefectBranch, DomainAdapter, LiftSearch,
    PrimeAlgorithm0Receipt, PrimeStepRecord, PrimeTerminal,
};
use crate::ddc::dda_alphabet::{DdaOp, DdaStep, DdaTrace, TraceTerminal};
use core_types::authority::AuthorityEffect;
use serde::Serialize;
use std::fmt;

/// An admitted declaration whose 7 declaration steps have passed the gate.
///
/// Private fields and no public constructor: can only be constructed by [`admit`].
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct AdmittedDeclaration {
    carrier: String,
    primitive_difference: String,
    zero_rel: String,
    cochain: CochainSlot,
    observer: String,
    witnesses: Vec<String>,
}

impl AdmittedDeclaration {
    pub fn carrier(&self) -> &str {
        &self.carrier
    }

    pub fn primitive_difference(&self) -> &str {
        &self.primitive_difference
    }

    pub fn zero_rel(&self) -> &str {
        &self.zero_rel
    }

    pub fn cochain(&self) -> &CochainSlot {
        &self.cochain
    }

    pub fn observer(&self) -> &str {
        &self.observer
    }

    pub fn witnesses(&self) -> &[String] {
        &self.witnesses
    }
}

/// A refusal during Prime 000 admission, occurring before any measurement.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct AdmissionRefusal {
    pub prime_step: u8,
    pub reason: &'static str,
    pub detail: String,
}

impl fmt::Display for AdmissionRefusal {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "admission refused at step {}: {} ({})",
            self.prime_step, self.reason, self.detail
        )
    }
}

impl std::error::Error for AdmissionRefusal {}

impl AdmissionRefusal {
    /// Convert an admission refusal into a [`PrimeAlgorithm0Receipt`].
    ///
    /// The receipt records execution up to the point of refusal and terminalizes
    /// with [`PrimeTerminal::Refusal`]. Crucially, `phi1` and `gamma2` are `None`:
    /// no diagnostic measurement ever took place.
    pub fn to_receipt(&self, adapter: &dyn DomainAdapter) -> PrimeAlgorithm0Receipt {
        let decl = adapter.declaration();
        let family = adapter.residual_family_label();
        let mut trace = DdaTrace::new();
        let mut steps: Vec<PrimeStepRecord> = Vec::new();

        let mut emit = |prime_step: u8, op: DdaOp, executed: bool, message: String| {
            if executed {
                trace.emit(DdaStep::executed(op, message.clone()));
            } else {
                trace.emit(DdaStep::refused(op, message.clone()));
            }
            steps.push(PrimeStepRecord {
                prime_step,
                op: op.letter().to_string(),
                executed,
                message,
                phi1_after: None,
                gamma2_after: None,
                loss_ledger: None,
            });
        };

        self.emit_steps_1_to_3(&decl, &mut emit);

        // Step 4: cochain
        let cochain = self.emit_step4_cochain(adapter, &mut emit);

        // Step 7: observer (if failed at step 7)
        let observer = self.emit_step7_observer(&decl, &mut emit);

        // Step 8: witnesses (if failed at step 8)
        let witnesses = self.emit_step8_witnesses(&decl, &mut emit);

        // Terminalize Refusal at step 11
        emit(
            11,
            DdaOp::Terminalize,
            true,
            format!("terminalize Refusal reason={}", self.reason),
        );

        let letter_tape: String = steps.iter().map(|s| s.op.as_str()).collect();
        let letters_spaced = trace.letters();
        let trace_terminal = Self::format_trace_terminal(trace.terminal());

        PrimeAlgorithm0Receipt {
            domain: adapter.domain(),
            carrier: decl.carrier,
            primitive_difference: decl.primitive_difference,
            zero_rel: decl.zero_rel,
            cochain,
            q1: None,
            phi1: None,
            gamma2: None,
            observer,
            witnesses,
            structure_search: LiftSearch::SkippedClosed,
            licensed_lift: None,
            routing: "blocked_at_admission".into(),
            literature_compare: None,
            branch: DefectBranch::Unset,
            terminal: PrimeTerminal::Refusal,
            letter_tape,
            letters_spaced,
            trace_terminal,
            residual_family_label: family,
            authority_effect: AuthorityEffect::None,
            steps,
            evidence_provenance: adapter.evidence_provenance(),
        }
    }

    fn emit_steps_1_to_3(
        &self,
        decl: &DeclarationFill,
        emit: &mut dyn FnMut(u8, DdaOp, bool, String),
    ) {
        // Step 1: carrier
        if self.prime_step == 1 {
            emit(
                1,
                DdaOp::Refusal,
                false,
                format!("step1 refuse: {}", self.reason),
            );
        } else {
            emit(
                1,
                DdaOp::ContextExposure,
                true,
                format!("declare carrier={}", decl.carrier.as_deref().unwrap_or("")),
            );
            emit(1, DdaOp::Integration, true, "ledger open".into());
        }

        // Step 2: primitive difference
        Self::emit_step_if_reached(
            self.prime_step,
            2,
            self.reason,
            "step2 refuse",
            "declare δ",
            decl.primitive_difference.as_deref().unwrap_or(""),
            emit,
        );

        // Step 3: zero_rel
        Self::emit_step_if_reached(
            self.prime_step,
            3,
            self.reason,
            "step3 refuse",
            "declare ZeroRel",
            decl.zero_rel.as_deref().unwrap_or(""),
            emit,
        );
    }

    fn emit_step_if_reached(
        failed_step: u8,
        step: u8,
        reason: &str,
        refuse_prefix: &str,
        declare_prefix: &str,
        value: &str,
        emit: &mut dyn FnMut(u8, DdaOp, bool, String),
    ) {
        if failed_step < step {
            return;
        }
        if failed_step == step {
            emit(step, DdaOp::Refusal, false, format!("{refuse_prefix}: {reason}"));
        } else {
            emit(
                step,
                DdaOp::Integration,
                true,
                format!("{declare_prefix}={value}"),
            );
        }
    }

    fn emit_step4_cochain(
        &self,
        adapter: &dyn DomainAdapter,
        emit: &mut dyn FnMut(u8, DdaOp, bool, String),
    ) -> CochainSlot {
        if self.prime_step == 4 {
            emit(
                4,
                DdaOp::Refusal,
                false,
                format!("step4 refuse: {}", self.reason),
            );
            return self.refused_cochain_slot(adapter);
        }
        if self.prime_step > 4 {
            if let Some(w) = adapter.cochain_window() {
                emit(
                    4,
                    DdaOp::ContextExposure,
                    true,
                    format!(
                        "construct C• dims=({},{},{}) d∘d=0 ok",
                        w.dim_c0, w.dim_c1, w.dim_c2
                    ),
                );
                return CochainSlot::Constructed {
                    dim_c0: w.dim_c0,
                    dim_c1: w.dim_c1,
                    dim_c2: w.dim_c2,
                    square_zero: true,
                };
            }
        }
        CochainSlot::BlockedEarly
    }

    fn refused_cochain_slot(&self, adapter: &dyn DomainAdapter) -> CochainSlot {
        if self.reason == "COCHAIN_NOT_SQUARE_ZERO" {
            let mass = adapter
                .cochain_window()
                .map(|w| w.l1_defect_mass)
                .unwrap_or(0);
            CochainSlot::RefusedNotSquareZero {
                l1_defect_mass: mass,
            }
        } else {
            CochainSlot::MissingUnjustified
        }
    }

    fn emit_step7_observer(
        &self,
        decl: &DeclarationFill,
        emit: &mut dyn FnMut(u8, DdaOp, bool, String),
    ) -> Option<String> {
        if self.prime_step == 7 {
            emit(
                7,
                DdaOp::Refusal,
                false,
                "step7: observer undeclared — refuse view-from-nowhere".into(),
            );
            Some("MISSING_observer".into())
        } else {
            decl.observer.clone()
        }
    }

    fn emit_step8_witnesses(
        &self,
        decl: &DeclarationFill,
        emit: &mut dyn FnMut(u8, DdaOp, bool, String),
    ) -> Vec<String> {
        if self.prime_step == 8 {
            emit(
                8,
                DdaOp::Refusal,
                false,
                "step8: no witness supplied — a declared difference is not its own evidence".into(),
            );
            vec![]
        } else {
            decl.witnesses.clone()
        }
    }

    fn format_trace_terminal(terminal: TraceTerminal) -> String {
        match terminal {
            TraceTerminal::Open => "Open".into(),
            TraceTerminal::Terminalized => "Terminalized".into(),
            TraceTerminal::Refused => "Refused".into(),
            TraceTerminal::OracleNeeded { import } => format!("OracleNeeded:{import}"),
            TraceTerminal::UnverifiedTerminal => "UnverifiedTerminal".into(),
        }
    }
}

/// Run the 7-step admission gate on a declaration.
///
/// Refuses early before any measuring takes place:
/// - Step 1: carrier declared and non-empty
/// - Step 2: primitive difference declared and non-empty
/// - Step 3: ZeroRel declared and non-empty
/// - Step 4: cochain construction justified and window satisfies d₁∘d₀ = 0
/// - Step 7: observer declared (no view-from-nowhere)
/// - Step 8: witnesses non-empty (a difference is not its own evidence)
pub fn admit(
    decl: &DeclarationFill,
    justify_cochain: bool,
    window: Option<&CochainWindow>,
) -> Result<AdmittedDeclaration, AdmissionRefusal> {
    // Step 1 — carrier
    let carrier = require_non_empty_slot(
        &decl.carrier,
        1,
        "MISSING_carrier",
        "carrier undeclared or empty",
    )?;

    // Step 2 — primitive difference δ
    let primitive_difference = require_non_empty_slot(
        &decl.primitive_difference,
        2,
        "MISSING_primitive_difference",
        "primitive difference undeclared or empty",
    )?;

    // Step 3 — ZeroRel
    let zero_rel = require_non_empty_slot(
        &decl.zero_rel,
        3,
        "MISSING_zero_rel",
        "zero_rel undeclared or empty",
    )?;

    // Step 4 — C• cochain window
    let cochain = admit_cochain_window(justify_cochain, window)?;

    // Step 7 — observer
    let observer = admit_observer_slot(&decl.observer)?;

    // Step 8 — witnesses
    if decl.witnesses.is_empty() {
        return Err(AdmissionRefusal {
            prime_step: 8,
            reason: "MISSING_witness",
            detail: "no witness supplied — a declared difference is not its own evidence".into(),
        });
    }
    let witnesses = decl.witnesses.clone();

    Ok(AdmittedDeclaration {
        carrier,
        primitive_difference,
        zero_rel,
        cochain,
        observer,
        witnesses,
    })
}

fn require_non_empty_slot(
    slot: &Option<String>,
    prime_step: u8,
    reason: &'static str,
    detail: &'static str,
) -> Result<String, AdmissionRefusal> {
    match slot {
        Some(v) if !v.trim().is_empty() => Ok(v.clone()),
        _ => Err(AdmissionRefusal {
            prime_step,
            reason,
            detail: detail.into(),
        }),
    }
}

fn admit_cochain_window(
    justify_cochain: bool,
    window: Option<&CochainWindow>,
) -> Result<CochainSlot, AdmissionRefusal> {
    if !justify_cochain {
        return Err(AdmissionRefusal {
            prime_step: 4,
            reason: "COCHAIN_UNJUSTIFIED",
            detail: "cochain not justified by δ/ZeroRel".into(),
        });
    }
    match window {
        None => Err(AdmissionRefusal {
            prime_step: 4,
            reason: "COCHAIN_WINDOW_MISSING",
            detail: "cochain justified but window missing".into(),
        }),
        Some(w) if !w.square_zero => Err(AdmissionRefusal {
            prime_step: 4,
            reason: "COCHAIN_NOT_SQUARE_ZERO",
            detail: format!("d1∘d0 ≠ 0, mass={}", w.l1_defect_mass),
        }),
        Some(w) => Ok(CochainSlot::Constructed {
            dim_c0: w.dim_c0,
            dim_c1: w.dim_c1,
            dim_c2: w.dim_c2,
            square_zero: true,
        }),
    }
}

fn admit_observer_slot(observer: &Option<String>) -> Result<String, AdmissionRefusal> {
    match observer {
        Some(o) if !o.trim().is_empty() && o != "MISSING_observer" => Ok(o.clone()),
        _ => Err(AdmissionRefusal {
            prime_step: 7,
            reason: "MISSING_observer",
            detail: "observer undeclared — refuse view-from-nowhere".into(),
        }),
    }
}

// Origin: engine/crates_rs/core_wdp/src/prime_algos/prime_algorithm_0_admission.rs
// Claim: urn:core:crates_rs:core-wdp:prime-algorithm-0-admission:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn valid_fill() -> DeclarationFill {
        DeclarationFill {
            carrier: Some("torus".into()),
            primitive_difference: Some("d0".into()),
            zero_rel: Some("z0".into()),
            observer: Some("observer_alpha".into()),
            witnesses: vec!["w1".into()],
        }
    }

    fn valid_window() -> CochainWindow {
        CochainWindow {
            dim_c0: 2,
            dim_c1: 3,
            dim_c2: 1,
            square_zero: true,
            l1_defect_mass: 0,
        }
    }

    #[test]
    fn valid_declaration_admits() {
        let decl = valid_fill();
        let win = valid_window();
        let admitted = admit(&decl, true, Some(&win)).expect("should admit valid declaration");
        assert_eq!(admitted.carrier(), "torus");
        assert_eq!(admitted.observer(), "observer_alpha");
        assert_eq!(admitted.witnesses(), &["w1"]);
    }

    #[test]
    fn missing_carrier_refuses_at_step_1() {
        let mut decl = valid_fill();
        decl.carrier = None;
        let win = valid_window();
        let err = admit(&decl, true, Some(&win)).expect_err("missing carrier must refuse");
        assert_eq!(err.prime_step, 1);
        assert_eq!(err.reason, "MISSING_carrier");
    }

    #[test]
    fn missing_primitive_difference_refuses_at_step_2() {
        let mut decl = valid_fill();
        decl.primitive_difference = Some("".into());
        let win = valid_window();
        let err = admit(&decl, true, Some(&win)).expect_err("empty delta must refuse");
        assert_eq!(err.prime_step, 2);
        assert_eq!(err.reason, "MISSING_primitive_difference");
    }

    #[test]
    fn missing_zero_rel_refuses_at_step_3() {
        let mut decl = valid_fill();
        decl.zero_rel = None;
        let win = valid_window();
        let err = admit(&decl, true, Some(&win)).expect_err("missing zero_rel must refuse");
        assert_eq!(err.prime_step, 3);
        assert_eq!(err.reason, "MISSING_zero_rel");
    }

    #[test]
    fn unjustified_cochain_refuses_at_step_4() {
        let decl = valid_fill();
        let win = valid_window();
        let err = admit(&decl, false, Some(&win)).expect_err("unjustified cochain must refuse");
        assert_eq!(err.prime_step, 4);
        assert_eq!(err.reason, "COCHAIN_UNJUSTIFIED");
    }

    #[test]
    fn non_square_zero_cochain_refuses_at_step_4() {
        let decl = valid_fill();
        let mut win = valid_window();
        win.square_zero = false;
        win.l1_defect_mass = 5;
        let err = admit(&decl, true, Some(&win)).expect_err("non square-zero cochain must refuse");
        assert_eq!(err.prime_step, 4);
        assert_eq!(err.reason, "COCHAIN_NOT_SQUARE_ZERO");
    }

    #[test]
    fn missing_observer_refuses_at_step_7() {
        let mut decl = valid_fill();
        decl.observer = None;
        let win = valid_window();
        let err = admit(&decl, true, Some(&win)).expect_err("missing observer must refuse");
        assert_eq!(err.prime_step, 7);
        assert_eq!(err.reason, "MISSING_observer");
    }

    #[test]
    fn empty_witnesses_refuses_at_step_8() {
        let mut decl = valid_fill();
        decl.witnesses = vec![];
        let win = valid_window();
        let err = admit(&decl, true, Some(&win)).expect_err("empty witnesses must refuse");
        assert_eq!(err.prime_step, 8);
        assert_eq!(err.reason, "MISSING_witness");
    }
}
