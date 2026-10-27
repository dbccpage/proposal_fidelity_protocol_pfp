//! H-O3: Nine Up-Lift certificate bits bound field-by-field to
//! `PaperER003.LicensedLiftCertificate`, used as the Algorithm Prime 000
//! **step-9** lift gate.
//!
//! Lean source of truth:
//! `engine/lean4/research_programs/paper_er003_licensed_lift_certificate.lean`
//! (`PaperER003.LicensedLiftCertificate`).
//!
//! MSS nine conditions:
//! `research/published/008_engine_runtime/007_the_symbol_game/016_mss_reconstruction_spine.md`
//!
//! This module mints **no** authority. A green gate is residual-reduction
//! evidence under `AuthorityEffect::None`, not `IsAuth`.

use core_types::authority::AuthorityEffect;
use serde::{Deserialize, Serialize};
use std::fmt;

// ---------------------------------------------------------------------------
// Nine MSS Up-Lift certificate bits
// ---------------------------------------------------------------------------

/// The nine mandatory Up-Lift certificate conditions (MSS spine §Nine Conditions).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize, Default)]
pub struct NineUpLiftBits {
    /// (1) Exhaustion Trace — same-level repair/quotient exhausted and recorded.
    pub exhaustion_trace: bool,
    /// (2) Refusal / Failure Witness — same-level closure failed or refused.
    pub refusal_or_failure_witness: bool,
    /// (3) Generator Traceability — every new generator traces to the obstruction.
    pub generator_traceability: bool,
    /// (4) Preservation — prior admitted judgments remain valid.
    pub preservation: bool,
    /// (5) Conservativity — no new theorems in the restricted prior vocabulary.
    pub conservativity: bool,
    /// (6) Obstruction Resolution — named target obstruction resolved or refined.
    pub obstruction_resolution: bool,
    /// (7) Minimality — removing any single new generator restores the obstruction.
    pub minimality: bool,
    /// (8) Replayability — finite, deterministic, machine-checkable evaluation.
    pub replayability: bool,
    /// (9) Authority Preservation — `AuthorityEffect::None`; no silent promotion.
    pub authority_preservation: bool,
}

impl NineUpLiftBits {
    pub const FIELD_NAMES: [&'static str; 9] = [
        "exhaustion_trace",
        "refusal_or_failure_witness",
        "generator_traceability",
        "preservation",
        "conservativity",
        "obstruction_resolution",
        "minimality",
        "replayability",
        "authority_preservation",
    ];

    pub fn all_satisfied(&self) -> bool {
        self.exhaustion_trace
            && self.refusal_or_failure_witness
            && self.generator_traceability
            && self.preservation
            && self.conservativity
            && self.obstruction_resolution
            && self.minimality
            && self.replayability
            && self.authority_preservation
    }

    pub fn failed_bits(&self) -> Vec<&'static str> {
        let flags = [
            (self.exhaustion_trace, "exhaustion_trace"),
            (
                self.refusal_or_failure_witness,
                "refusal_or_failure_witness",
            ),
            (self.generator_traceability, "generator_traceability"),
            (self.preservation, "preservation"),
            (self.conservativity, "conservativity"),
            (self.obstruction_resolution, "obstruction_resolution"),
            (self.minimality, "minimality"),
            (self.replayability, "replayability"),
            (self.authority_preservation, "authority_preservation"),
        ];
        flags
            .into_iter()
            .filter_map(|(ok, name)| if ok { None } else { Some(name) })
            .collect()
    }

    /// All-true bits with authority preserved (for fully licensed candidates).
    pub fn all_true() -> Self {
        Self {
            exhaustion_trace: true,
            refusal_or_failure_witness: true,
            generator_traceability: true,
            preservation: true,
            conservativity: true,
            obstruction_resolution: true,
            minimality: true,
            replayability: true,
            authority_preservation: true,
        }
    }
}

// ---------------------------------------------------------------------------
// PaperER003.LicensedLiftCertificate mirrors (runtime)
// ---------------------------------------------------------------------------

/// Mirror of Lean `LiftEvidenceChecklist` (boolean preflight).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize, Default)]
pub struct LiftEvidenceChecklist {
    pub source_residual_hash: bool,
    pub target_carrier_hash: bool,
    pub operator_hash: bool,
    pub replay_hash: bool,
    pub closure_check_hash: bool,
    pub residual_reduced: bool,
    pub closure_preserved: bool,
}

impl LiftEvidenceChecklist {
    pub const FIELD_NAMES: [&'static str; 7] = [
        "source_residual_hash",
        "target_carrier_hash",
        "operator_hash",
        "replay_hash",
        "closure_check_hash",
        "residual_reduced",
        "closure_preserved",
    ];

    /// Lean `liftChecklistComplete`.
    pub fn lift_checklist_complete(&self) -> bool {
        self.source_residual_hash
            && self.target_carrier_hash
            && self.operator_hash
            && self.replay_hash
            && self.closure_check_hash
            && self.residual_reduced
            && self.closure_preserved
    }

    /// Lean `liftChecklistDecision` Present iff complete.
    pub fn decision_present(&self) -> bool {
        self.lift_checklist_complete()
    }
}

/// Mirror of Lean `LiftCertificate` (string hashes + readiness flags).
///
/// Prop-level non-emptiness proofs are runtime checks: hashes must be non-empty.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct PaperEr003LiftCertificate {
    pub source_residual_hash: String,
    pub target_carrier_hash: String,
    pub operator_hash: String,
    pub replay_hash: String,
    pub closure_check_hash: String,
    pub residual_reduced: bool,
    pub replay_checked: bool,
    pub closure_preserved: bool,
    pub policy_violation: bool,
}

impl PaperEr003LiftCertificate {
    /// Lean hash-presence obligations (runtime).
    pub fn hashes_present(&self) -> bool {
        !self.source_residual_hash.is_empty()
            && !self.target_carrier_hash.is_empty()
            && !self.operator_hash.is_empty()
            && !self.replay_hash.is_empty()
            && !self.closure_check_hash.is_empty()
    }

    /// Lean `liftReady`.
    pub fn lift_ready(&self) -> bool {
        self.residual_reduced && self.replay_checked && self.closure_preserved
    }

    /// Lean `checklistOfCertificate` (hashes assumed present when this is used post-check).
    pub fn checklist_of_certificate(&self) -> LiftEvidenceChecklist {
        LiftEvidenceChecklist {
            source_residual_hash: !self.source_residual_hash.is_empty(),
            target_carrier_hash: !self.target_carrier_hash.is_empty(),
            operator_hash: !self.operator_hash.is_empty(),
            replay_hash: !self.replay_hash.is_empty(),
            closure_check_hash: !self.closure_check_hash.is_empty(),
            residual_reduced: self.residual_reduced,
            // Lean: closure_preserved := cert.closure_preserved && cert.replay_checked
            closure_preserved: self.closure_preserved && self.replay_checked,
        }
    }

    /// Demo certificate aligned with Lean `demoLiftCertificate`.
    pub fn demo() -> Self {
        Self {
            source_residual_hash: "residual:demo".into(),
            target_carrier_hash: "carrier:demo".into(),
            operator_hash: "operator:demo".into(),
            replay_hash: "replay:lift-demo".into(),
            closure_check_hash: "closure:demo".into(),
            residual_reduced: true,
            replay_checked: true,
            closure_preserved: true,
            policy_violation: false,
        }
    }
}

// ---------------------------------------------------------------------------
// Field-by-field binding table (H-O3)
// ---------------------------------------------------------------------------

/// One row of the nine-bit ↔ PaperER003 field binding.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct NineBitBinding {
    /// Index 1..=9 of the MSS nine conditions.
    pub nine_index: u8,
    pub nine_field: &'static str,
    /// PaperER003.LicensedLiftCertificate field path(s).
    pub paper_er003_fields: &'static [&'static str],
    pub lean_anchor: &'static str,
}

/// Binding table: each of the nine bits maps to named PaperER003 fields.
///
/// | # | Nine bit | PaperER003 fields |
/// |---|---|---|
/// | 1 | exhaustion_trace | source_residual_hash (present) |
/// | 2 | refusal_or_failure_witness | source_residual_hash (obstruction residual declared) |
/// | 3 | generator_traceability | operator_hash |
/// | 4 | preservation | closure_preserved |
/// | 5 | conservativity | closure_check_hash + closure_preserved |
/// | 6 | obstruction_resolution | residual_reduced |
/// | 7 | minimality | target_carrier_hash + operator_hash |
/// | 8 | replayability | replay_hash + replay_checked |
/// | 9 | authority_preservation | policy_violation = false (+ AuthorityEffect::None) |
pub const NINE_BIT_BINDINGS: [NineBitBinding; 9] = [
    NineBitBinding {
        nine_index: 1,
        nine_field: "exhaustion_trace",
        paper_er003_fields: &["LiftCertificate.source_residual_hash"],
        lean_anchor: "PaperER003.LicensedLiftCertificate.LiftCertificate.source_residual_hash",
    },
    NineBitBinding {
        nine_index: 2,
        nine_field: "refusal_or_failure_witness",
        paper_er003_fields: &["LiftCertificate.source_residual_hash"],
        lean_anchor: "PaperER003.LicensedLiftCertificate (source residual as refusal witness host)",
    },
    NineBitBinding {
        nine_index: 3,
        nine_field: "generator_traceability",
        paper_er003_fields: &["LiftCertificate.operator_hash"],
        lean_anchor: "PaperER003.LicensedLiftCertificate.LiftCertificate.operator_hash",
    },
    NineBitBinding {
        nine_index: 4,
        nine_field: "preservation",
        paper_er003_fields: &["LiftCertificate.closure_preserved"],
        lean_anchor: "PaperER003.LicensedLiftCertificate.LiftCertificate.closure_preserved",
    },
    NineBitBinding {
        nine_index: 5,
        nine_field: "conservativity",
        paper_er003_fields: &[
            "LiftCertificate.closure_check_hash",
            "LiftCertificate.closure_preserved",
        ],
        lean_anchor: "PaperER003.LicensedLiftCertificate.closure_check_hash + closure_preserved",
    },
    NineBitBinding {
        nine_index: 6,
        nine_field: "obstruction_resolution",
        paper_er003_fields: &["LiftCertificate.residual_reduced"],
        lean_anchor: "PaperER003.LicensedLiftCertificate.LiftCertificate.residual_reduced",
    },
    NineBitBinding {
        nine_index: 7,
        nine_field: "minimality",
        paper_er003_fields: &[
            "LiftCertificate.target_carrier_hash",
            "LiftCertificate.operator_hash",
        ],
        lean_anchor: "PaperER003.LicensedLiftCertificate target_carrier_hash + operator_hash",
    },
    NineBitBinding {
        nine_index: 8,
        nine_field: "replayability",
        paper_er003_fields: &[
            "LiftCertificate.replay_hash",
            "LiftCertificate.replay_checked",
        ],
        lean_anchor: "PaperER003.LicensedLiftCertificate.replay_hash + replay_checked",
    },
    NineBitBinding {
        nine_index: 9,
        nine_field: "authority_preservation",
        paper_er003_fields: &["LiftCertificate.policy_violation"],
        lean_anchor: "PaperER003.LicensedLiftCertificate.policy_violation = false (GTOC-5 None)",
    },
];

/// Project nine bits onto the Lean checklist (when certificate hashes are present).
///
/// This is the **forward** binding used by the step-9 gate: a bit that is true
/// may only remain true if the corresponding PaperER003 fields hold on `cert`.
pub fn project_nine_onto_checklist(
    bits: &NineUpLiftBits,
    cert: &PaperEr003LiftCertificate,
) -> LiftEvidenceChecklist {
    // Hash presence
    let (source_residual_hash, target_carrier_hash, operator_hash, replay_hash, closure_check_hash) =
        project_hash_checklist_bits(bits, cert);

    LiftEvidenceChecklist {
        // (1)(2) → source residual hash
        source_residual_hash,
        // (7) → target carrier
        target_carrier_hash,
        // (3)(7) → operator
        operator_hash,
        // (8) → replay hash
        replay_hash,
        // (5) → closure check hash
        closure_check_hash,
        // (6) → residual reduced
        residual_reduced: bits.obstruction_resolution && cert.residual_reduced,
        // (4)(5)(8) → closure preserved (Lean also folds replay_checked)
        closure_preserved: project_closure_preserved_bit(bits, cert),
    }
}

fn project_hash_checklist_bits(
    bits: &NineUpLiftBits,
    cert: &PaperEr003LiftCertificate,
) -> (bool, bool, bool, bool, bool) {
    let src = !cert.source_residual_hash.is_empty();
    let tgt = !cert.target_carrier_hash.is_empty();
    let op = !cert.operator_hash.is_empty();
    let replay_h = !cert.replay_hash.is_empty();
    let closure_h = !cert.closure_check_hash.is_empty();
    (
        bits.exhaustion_trace && bits.refusal_or_failure_witness && src,
        bits.minimality && tgt,
        bits.generator_traceability && bits.minimality && op,
        bits.replayability && replay_h,
        bits.conservativity && closure_h,
    )
}

fn project_closure_preserved_bit(bits: &NineUpLiftBits, cert: &PaperEr003LiftCertificate) -> bool {
    bits.preservation
        && bits.conservativity
        && cert.closure_preserved
        && cert.replay_checked
        && bits.replayability
}

/// Verify that each true nine-bit has its bound PaperER003 fields satisfied.
pub fn verify_field_binding(
    bits: &NineUpLiftBits,
    cert: &PaperEr003LiftCertificate,
) -> Result<(), Vec<&'static str>> {
    let mut fails = Vec::new();
    check_field_bindings_1_to_3(bits, cert, &mut fails);
    check_field_bindings_4_to_6(bits, cert, &mut fails);
    check_field_bindings_7_to_9(bits, cert, &mut fails);

    if fails.is_empty() {
        Ok(())
    } else {
        Err(fails)
    }
}

fn check_field_bindings_1_to_3(
    bits: &NineUpLiftBits,
    cert: &PaperEr003LiftCertificate,
    fails: &mut Vec<&'static str>,
) {
    // 1 Exhaustion → source residual hash present
    if bits.exhaustion_trace && cert.source_residual_hash.is_empty() {
        fails.push("bit1_exhaustion_requires_source_residual_hash");
    }
    // 2 Refusal witness → source residual hash present
    if bits.refusal_or_failure_witness && cert.source_residual_hash.is_empty() {
        fails.push("bit2_refusal_witness_requires_source_residual_hash");
    }
    // 3 Traceability → operator_hash
    if bits.generator_traceability && cert.operator_hash.is_empty() {
        fails.push("bit3_traceability_requires_operator_hash");
    }
}

fn check_field_bindings_4_to_6(
    bits: &NineUpLiftBits,
    cert: &PaperEr003LiftCertificate,
    fails: &mut Vec<&'static str>,
) {
    // 4 Preservation → closure_preserved
    if bits.preservation && !cert.closure_preserved {
        fails.push("bit4_preservation_requires_closure_preserved");
    }
    // 5 Conservativity → closure_check_hash + closure_preserved
    if bits.conservativity && (cert.closure_check_hash.is_empty() || !cert.closure_preserved) {
        fails.push("bit5_conservativity_requires_closure_check_and_preserved");
    }
    // 6 Obstruction resolution → residual_reduced
    if bits.obstruction_resolution && !cert.residual_reduced {
        fails.push("bit6_resolution_requires_residual_reduced");
    }
}

fn check_field_bindings_7_to_9(
    bits: &NineUpLiftBits,
    cert: &PaperEr003LiftCertificate,
    fails: &mut Vec<&'static str>,
) {
    // 7 Minimality → target_carrier_hash + operator_hash
    if bits.minimality && (cert.target_carrier_hash.is_empty() || cert.operator_hash.is_empty()) {
        fails.push("bit7_minimality_requires_target_carrier_and_operator_hash");
    }
    // 8 Replayability → replay_hash + replay_checked
    if bits.replayability && (cert.replay_hash.is_empty() || !cert.replay_checked) {
        fails.push("bit8_replayability_requires_replay_hash_and_checked");
    }
    // 9 Authority → !policy_violation
    if bits.authority_preservation && cert.policy_violation {
        fails.push("bit9_authority_requires_no_policy_violation");
    }
}

// ---------------------------------------------------------------------------
// Step-9 gate
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum LiftGateRefusal {
    NineBitsIncomplete { failed: Vec<String> },
    FieldBindingFailed { reasons: Vec<String> },
    HashesMissing,
    ChecklistIncomplete,
    LiftNotReady,
    PolicyViolation,
    AuthorityNotNone,
}

impl fmt::Display for LiftGateRefusal {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            LiftGateRefusal::NineBitsIncomplete { failed } => {
                write!(f, "nine Up-Lift bits incomplete: {failed:?}")
            }
            LiftGateRefusal::FieldBindingFailed { reasons } => {
                write!(f, "nine↔PaperER003 field binding failed: {reasons:?}")
            }
            LiftGateRefusal::HashesMissing => {
                write!(f, "PaperER003 LiftCertificate hashes missing")
            }
            LiftGateRefusal::ChecklistIncomplete => {
                write!(f, "PaperER003 liftChecklistComplete = false")
            }
            LiftGateRefusal::LiftNotReady => {
                write!(f, "PaperER003 liftReady = false")
            }
            LiftGateRefusal::PolicyViolation => {
                write!(f, "PaperER003 policy_violation = true")
            }
            LiftGateRefusal::AuthorityNotNone => {
                write!(f, "authority_effect must be None")
            }
        }
    }
}

/// Admitted step-9 lift under the bound gate (still AuthorityEffect::None).
///
/// **Sealed.** Fields are private and there is no `Deserialize`: the only way to
/// obtain one is [`step9_licensed_lift_gate`], which checks all nine up-lift
/// bits and the certificate. Previously the fields were public and the type
/// derived `Deserialize`, so a caller could assemble an admission with a
/// hand-filled checklist and any consumer inspecting `checklist` was reading the
/// caller's assertion rather than the gate's verdict.
///
/// `Serialize` is retained because receipts embed admissions; deserialization is
/// not, because a type you can deserialize is a type you can forge by writing
/// JSON.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct LicensedLiftAdmission {
    generators: Vec<String>,
    nine_bits: NineUpLiftBits,
    checklist: LiftEvidenceChecklist,
    certificate: PaperEr003LiftCertificate,
    lean_module: &'static str,
    authority_effect: AuthorityEffect,
}

impl LicensedLiftAdmission {
    pub fn generators(&self) -> &[String] {
        &self.generators
    }
    pub fn nine_bits(&self) -> &NineUpLiftBits {
        &self.nine_bits
    }
    pub fn checklist(&self) -> &LiftEvidenceChecklist {
        &self.checklist
    }
    pub fn certificate(&self) -> &PaperEr003LiftCertificate {
        &self.certificate
    }
    pub fn lean_module(&self) -> &'static str {
        self.lean_module
    }
    pub fn authority_effect(&self) -> &AuthorityEffect {
        &self.authority_effect
    }
}

/// **Step-9 gate:** admit a lift only if
/// 1. all nine MSS bits are true,
/// 2. each true bit's PaperER003 fields hold (field binding),
/// 3. certificate hashes present,
/// 4. Lean `liftChecklistComplete` on projected checklist,
/// 5. Lean `liftReady`,
/// 6. `policy_violation = false`,
/// 7. `AuthorityEffect::None`.
pub fn step9_licensed_lift_gate(
    generators: Vec<String>,
    nine_bits: NineUpLiftBits,
    certificate: PaperEr003LiftCertificate,
) -> Result<LicensedLiftAdmission, LiftGateRefusal> {
    // 7 — authority always None at this gate
    let authority = AuthorityEffect::None;

    if !nine_bits.authority_preservation {
        return Err(LiftGateRefusal::AuthorityNotNone);
    }
    if !nine_bits.all_satisfied() {
        return Err(LiftGateRefusal::NineBitsIncomplete {
            failed: nine_bits
                .failed_bits()
                .into_iter()
                .map(str::to_string)
                .collect(),
        });
    }
    if certificate.policy_violation {
        return Err(LiftGateRefusal::PolicyViolation);
    }
    if !certificate.hashes_present() {
        return Err(LiftGateRefusal::HashesMissing);
    }
    if let Err(reasons) = verify_field_binding(&nine_bits, &certificate) {
        return Err(LiftGateRefusal::FieldBindingFailed {
            reasons: reasons.into_iter().map(str::to_string).collect(),
        });
    }
    if !certificate.lift_ready() {
        return Err(LiftGateRefusal::LiftNotReady);
    }

    let checklist = project_nine_onto_checklist(&nine_bits, &certificate);
    if !checklist.lift_checklist_complete() {
        return Err(LiftGateRefusal::ChecklistIncomplete);
    }

    // Consistency with Lean checklistOfCertificate path
    let lean_checklist = certificate.checklist_of_certificate();
    if !lean_checklist.decision_present() {
        return Err(LiftGateRefusal::ChecklistIncomplete);
    }

    Ok(LicensedLiftAdmission {
        generators,
        nine_bits,
        checklist,
        certificate,
        lean_module: "PaperER003.LicensedLiftCertificate",
        authority_effect: authority,
    })
}

/// Build a certificate from residual/operator/carrier labels (deterministic hashes).
pub fn certificate_from_labels(
    residual_label: &str,
    carrier_label: &str,
    operator_label: &str,
    residual_reduced: bool,
    replay_checked: bool,
    closure_preserved: bool,
    policy_violation: bool,
) -> PaperEr003LiftCertificate {
    PaperEr003LiftCertificate {
        source_residual_hash: format!("residual:{residual_label}"),
        target_carrier_hash: format!("carrier:{carrier_label}"),
        operator_hash: format!("operator:{operator_label}"),
        replay_hash: format!("replay:{operator_label}"),
        closure_check_hash: format!("closure:{carrier_label}"),
        residual_reduced,
        replay_checked,
        closure_preserved,
        policy_violation,
    }
}

// Origin: engine/crates_rs/core_wdp/src/prime_algos/licensed_lift_gate.rs
// Claim: urn:core:crates_rs:core-wdp:licensed-lift-gate:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn binding_table_has_nine_rows() {
        assert_eq!(NINE_BIT_BINDINGS.len(), 9);
        for (i, row) in NINE_BIT_BINDINGS.iter().enumerate() {
            assert_eq!(row.nine_index as usize, i + 1);
            assert!(!row.paper_er003_fields.is_empty());
        }
    }

    #[test]
    fn demo_certificate_passes_step9_gate() {
        let bits = NineUpLiftBits::all_true();
        let cert = PaperEr003LiftCertificate::demo();
        let adm = step9_licensed_lift_gate(vec!["resolve_delta_0".into()], bits, cert)
            .expect("demo should admit");
        assert!(adm.checklist.lift_checklist_complete());
        assert_eq!(adm.authority_effect, AuthorityEffect::None);
        assert_eq!(adm.lean_module, "PaperER003.LicensedLiftCertificate");
    }

    #[test]
    fn missing_replay_blocks_gate() {
        let bits = NineUpLiftBits::all_true();
        let mut cert = PaperEr003LiftCertificate::demo();
        cert.replay_checked = false;
        let err = step9_licensed_lift_gate(vec!["g".into()], bits, cert).unwrap_err();
        assert!(matches!(
            err,
            LiftGateRefusal::FieldBindingFailed { .. } | LiftGateRefusal::LiftNotReady
        ));
    }

    #[test]
    fn incomplete_nine_bits_block() {
        let mut bits = NineUpLiftBits::all_true();
        bits.minimality = false;
        let cert = PaperEr003LiftCertificate::demo();
        let err = step9_licensed_lift_gate(vec!["g".into()], bits, cert).unwrap_err();
        match err {
            LiftGateRefusal::NineBitsIncomplete { failed } => {
                assert!(failed.iter().any(|f| f == "minimality"));
            }
            other => panic!("expected NineBitsIncomplete, got {other:?}"),
        }
    }

    #[test]
    fn policy_violation_blocks() {
        let bits = NineUpLiftBits::all_true();
        let mut cert = PaperEr003LiftCertificate::demo();
        cert.policy_violation = true;
        let err = step9_licensed_lift_gate(vec!["g".into()], bits, cert).unwrap_err();
        assert_eq!(err, LiftGateRefusal::PolicyViolation);
    }

    #[test]
    fn empty_operator_hash_fails_binding() {
        let bits = NineUpLiftBits::all_true();
        let mut cert = PaperEr003LiftCertificate::demo();
        cert.operator_hash.clear();
        let err = step9_licensed_lift_gate(vec!["g".into()], bits, cert).unwrap_err();
        assert!(matches!(
            err,
            LiftGateRefusal::HashesMissing | LiftGateRefusal::FieldBindingFailed { .. }
        ));
    }

    #[test]
    fn project_nine_matches_complete_checklist_on_demo() {
        let bits = NineUpLiftBits::all_true();
        let cert = PaperEr003LiftCertificate::demo();
        let cl = project_nine_onto_checklist(&bits, &cert);
        assert!(cl.lift_checklist_complete());
    }
}
