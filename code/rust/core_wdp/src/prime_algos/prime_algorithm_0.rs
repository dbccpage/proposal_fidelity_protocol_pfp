//! Algorithm Prime 000 — binding twelve-step obstruction packet fill order.
//!
//! Canonical protocol:
//! `engine/research/theory_wip/07_algorithm_prime_000_protocol.md`
//!
//! This module is the **PROD Rust face** of the paper-022b toys under
//! `research/published/008_engine_runtime/005_the_engine/_code/`.
//!
//! Every run emits a [`crate::prime_algos::dda_alphabet::DdaTrace`] (letter tape).  
//! AuthorityEffect is always [`AuthorityEffect::None`].

#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_52b54418;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_52b54418<T> = std::result::Result<T, BoundaryError_52b54418>;
use crate::ddc::dda_alphabet::{DdaOp, DdaStep, DdaTrace, TraceTerminal};
use crate::prime_algos::licensed_lift_gate::{
    step9_licensed_lift_gate, LicensedLiftAdmission, NineUpLiftBits, PaperEr003LiftCertificate,
};
use core_types::authority::AuthorityEffect;
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::fmt;

pub use crate::prime_algos::prime_algorithm_0_admission::{
    admit, AdmissionRefusal, AdmittedDeclaration,
};

/// How a receipt's inputs were obtained.
///
/// The distinction is not cosmetic. An adapter that returns constant masses and
/// `NineUpLiftBits::all_true()` produces a receipt whose *structure* is real and
/// whose *numbers* are fixtures. Publishing the second as though it were the first
/// is the failure this enum exists to prevent, so every receipt states which it is
/// rather than leaving it to be inferred from the adapter's source.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum EvidenceProvenance {
    /// Adapter-declared constants. Structure real, numbers fixtures.
    FixtureDrivenStructuralDemo,
    /// Masses computed by a verifier in this crate from an actual finite object.
    VerifierProduced,
}

/// Declared domain labels (schema enum + Symbol Game).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum PrimeDomain {
    Generic,
    Mub,
    Fsp,
    Coda,
    SymbolGame,
}

impl PrimeDomain {
    pub fn as_str(self) -> &'static str {
        match self {
            PrimeDomain::Generic => "generic",
            PrimeDomain::Mub => "mub",
            PrimeDomain::Fsp => "fsp",
            PrimeDomain::Coda => "coda",
            PrimeDomain::SymbolGame => "symbol_game",
        }
    }
}

impl fmt::Display for PrimeDomain {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.as_str())
    }
}

/// Defect trichotomy (DDA Rosetta branch).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum DefectBranch {
    Closed,
    Open,
    StabilizedSurvivor,
    Unset,
}

impl DefectBranch {
    pub fn as_str(self) -> &'static str {
        match self {
            DefectBranch::Closed => "Closed",
            DefectBranch::Open => "Open",
            DefectBranch::StabilizedSurvivor => "StabilizedSurvivor",
            DefectBranch::Unset => "Unset",
        }
    }

    pub fn from_masses(phi1: u64, gamma2: u64) -> Self {
        if phi1 == 0 && gamma2 == 0 {
            DefectBranch::Closed
        } else if gamma2 > 0 {
            DefectBranch::Open
        } else {
            DefectBranch::StabilizedSurvivor
        }
    }
}

/// Step-11 terminal kinds (protocol + engine face).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum PrimeTerminal {
    ExactClass,
    ClosedResidual,
    OpenResidual,
    Refusal,
    OracleNeeded,
    Repair,
    Certificate,
    Pending,
}

impl PrimeTerminal {
    pub fn as_str(self) -> &'static str {
        match self {
            PrimeTerminal::ExactClass => "ExactClass",
            PrimeTerminal::ClosedResidual => "ClosedResidual",
            PrimeTerminal::OpenResidual => "OpenResidual",
            PrimeTerminal::Refusal => "Refusal",
            PrimeTerminal::OracleNeeded => "OracleNeeded",
            PrimeTerminal::Repair => "Repair",
            PrimeTerminal::Certificate => "Certificate",
            PrimeTerminal::Pending => "Pending",
        }
    }
}

/// Step-4 cochain slot.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum CochainSlot {
    /// Steps 1–3 incomplete.
    BlockedEarly,
    /// Not justified by δ / ZeroRel.
    MissingUnjustified,
    /// Justified and square-zero holds.
    Constructed {
        dim_c0: usize,
        dim_c1: usize,
        dim_c2: usize,
        square_zero: bool,
    },
    /// Justified but d₁∘d₀ ≠ 0.
    RefusedNotSquareZero { l1_defect_mass: u64 },
}

/// Result of step-9 operator / lift search (post gate).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum LiftSearch {
    SkippedClosed,
    SameLevelRepairAttempted,
    /// Admitted only after H-O3 nine-bit ↔ PaperER003.LicensedLiftCertificate gate.
    LiftAdmitted {
        generators: Vec<String>,
        nine_bits: NineUpLiftBits,
        lean_module: String,
    },
    LiftRefused {
        reason: String,
    },
    OracleGap {
        note: String,
    },
}

/// Pre-gate proposal from a domain adapter (step 9 input).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum LiftProposal {
    SkipClosed,
    SameLevelRepair,
    OracleGap {
        note: String,
    },
    /// Candidate must pass [`step9_licensed_lift_gate`].
    Candidate {
        generators: Vec<String>,
        nine_bits: NineUpLiftBits,
        certificate: PaperEr003LiftCertificate,
    },
}

/// Run the H-O3 step-9 gate on a proposal.
pub fn evaluate_lift_proposal(proposal: LiftProposal) -> LiftSearch {
    match proposal {
        LiftProposal::SkipClosed => LiftSearch::SkippedClosed,
        LiftProposal::SameLevelRepair => LiftSearch::SameLevelRepairAttempted,
        LiftProposal::OracleGap { note } => LiftSearch::OracleGap { note },
        LiftProposal::Candidate {
            generators,
            nine_bits,
            certificate,
        } => match step9_licensed_lift_gate(generators.clone(), nine_bits, certificate) {
            Ok(adm) => LiftSearch::LiftAdmitted {
                generators: adm.generators().to_vec(),
                nine_bits: *adm.nine_bits(),
                lean_module: adm.lean_module().to_string(),
            },
            Err(e) => LiftSearch::LiftRefused {
                reason: e.to_string(),
            },
        },
    }
}

/// Declaration fill from a domain adapter (steps 1–3, 7–8 seeds).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DeclarationFill {
    pub carrier: Option<String>,
    pub primitive_difference: Option<String>,
    pub zero_rel: Option<String>,
    pub observer: Option<String>,
    pub witnesses: Vec<String>,
}

/// Optional cochain window when the domain justifies construction.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CochainWindow {
    pub dim_c0: usize,
    pub dim_c1: usize,
    pub dim_c2: usize,
    /// True iff d₁∘d₀ = 0 on the declared window.
    pub square_zero: bool,
    /// ℓ¹ mass of d₁∘d₀ when not square-zero.
    pub l1_defect_mass: u64,
}

/// Domain adapter: fills Prime 000 slots; runner emits DDA letter tape.
pub trait DomainAdapter {
    fn domain(&self) -> PrimeDomain;
    fn declaration(&self) -> DeclarationFill;
    /// Whether δ + ZeroRel justify a FOC cochain packet.
    fn justify_cochain(&self) -> bool;
    fn cochain_window(&self) -> Option<CochainWindow>;
    /// (Φ₁, Γ₂) diagnostic masses — stored separately, never merged.
    fn residual_masses(&self) -> (u64, u64);
    /// Pre-gate lift proposal; runner applies H-O3 step-9 gate.
    fn lift_proposal(&self, branch: DefectBranch) -> LiftProposal;
    fn literature_note(&self) -> Option<String>;
    /// Where this adapter's masses come from.
    ///
    /// Defaults to [`EvidenceProvenance::FixtureDrivenStructuralDemo`], which is
    /// the honest answer for an adapter returning constants. Override it only
    /// when `residual_masses` is genuinely computed from a finite object.
    fn evidence_provenance(&self) -> EvidenceProvenance {
        EvidenceProvenance::FixtureDrivenStructuralDemo
    }

    /// Optional residual-family label for Rosetta stats (not authority).
    fn residual_family_label(&self) -> String {
        format!("{}:default", self.domain())
    }

    /// Deprecated path name: routes through [`Self::lift_proposal`] + gate.
    fn lift_search(&self, branch: DefectBranch) -> LiftSearch {
        evaluate_lift_proposal(self.lift_proposal(branch))
    }
}

/// Full receipt of one Prime 000 run.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct PrimeAlgorithm0Receipt {
    pub domain: PrimeDomain,
    pub carrier: Option<String>,
    pub primitive_difference: Option<String>,
    pub zero_rel: Option<String>,
    pub cochain: CochainSlot,
    pub q1: Option<String>,
    pub phi1: Option<u64>,
    pub gamma2: Option<u64>,
    pub observer: Option<String>,
    pub witnesses: Vec<String>,
    pub structure_search: LiftSearch,
    /// Present when step-9 admitted a lift under PaperER003 gate.
    pub licensed_lift: Option<LicensedLiftAdmission>,
    pub routing: String,
    pub literature_compare: Option<String>,
    pub branch: DefectBranch,
    pub terminal: PrimeTerminal,
    /// Compact letter tape, e.g. `"CIRIRT"` (no spaces) for Rosetta compare.
    pub letter_tape: String,
    /// Spaced spine letters from [`DdaTrace::letters`].
    pub letters_spaced: String,
    pub trace_terminal: String,
    pub residual_family_label: String,
    pub authority_effect: AuthorityEffect,
    pub steps: Vec<PrimeStepRecord>,
    /// Whether this run's masses were computed or declared. See [`EvidenceProvenance`].
    pub evidence_provenance: EvidenceProvenance,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct PrimeStepRecord {
    pub prime_step: u8,
    pub op: String,
    pub executed: bool,
    pub message: String,
    /// Residual state **as of the end of this step**.
    ///
    /// `None` before step 6 (the masses do not exist yet) and on any run that
    /// refused before reaching it. Recording this is what makes the `R` law
    /// ("a residual projection must not move Φ₁") decidable from a receipt: the
    /// checker compares consecutive records instead of declaring the law
    /// unevaluable. See `prime_algorithm_0_conformance`.
    pub phi1_after: Option<u64>,
    pub gamma2_after: Option<u64>,
    /// What this step discarded, keyed by what it was.
    ///
    /// `None` for every step the current runner emits — nothing here performs a
    /// lossy descent. The field exists so that `D` cannot be emitted without
    /// accounting for its loss: `prime_algorithm_0_conformance` refuses a `D` step whose
    /// ledger is absent or empty.
    ///
    /// The shape mirrors `DDAStepCert.loss_ledger` in
    /// `research/ooutwire_docs/universe_sentinelica/code/dda_engine.py`, which
    /// populates entries such as `gauge_potentials_removed` and
    /// `curl_mass_canceled` from real gauge fixing.
    pub loss_ledger: Option<BTreeMap<String, u64>>,
}

impl PrimeAlgorithm0Receipt {
    /// The recorded authority effect.
    ///
    /// This used to `return AuthorityEffect::None` unconditionally, ignoring the
    /// public `authority_effect` field — so the accessor agreed with the invariant
    /// even when the struct did not, and any test calling it asserted a literal.
    /// It now reads the field; [`Self::authority_is_none`] is the invariant check.
    pub fn authority_effect(&self) -> &AuthorityEffect {
        &self.authority_effect
    }

    /// CODA-5 invariant: an algorithm receipt never carries authority.
    ///
    /// Separated from the accessor so a violation is *detectable* rather than
    /// definitionally impossible.
    pub fn authority_is_none(&self) -> bool {
        self.authority_effect == AuthorityEffect::None
    }

    /// Write `letter_tape.txt` + the receipt JSON under `run_dir`.
    ///
    /// The receipt is written under `prime_algorithm_0_receipt.json`, as well as
    /// the backward-compatible `oeprmalg0_receipt.json` and `prime000_receipt.json`,
    /// with identical bytes, per ADR-009.
    pub fn write_files(&self, run_dir: &std::path::Path) -> std::io::Result<()> {
        std::fs::create_dir_all(run_dir)?;
        std::fs::write(
            run_dir.join("letter_tape.txt"),
            format!(
                "{}\nbranch={}\nterminal={}\nauthority_effect={:?}\n",
                self.letter_tape,
                self.branch.as_str(),
                self.terminal.as_str(),
                self.authority_effect
            ),
        )?;
        let json = serde_json::to_vec_pretty(self)
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))?;
        std::fs::write(run_dir.join("prime_algorithm_0_receipt.json"), &json)?;
        std::fs::write(run_dir.join("oeprmalg0_receipt.json"), &json)?;
        std::fs::write(run_dir.join("prime000_receipt.json"), &json)?;
        Ok(())
    }
}

pub type Oeprmalg0Receipt = PrimeAlgorithm0Receipt;

/// Run Algorithm Prime 000 for one domain adapter; emit DDA letter tape.
/// Run Algorithm Prime 000 for one admitted declaration and domain adapter.
///
/// Measuring before admission is unrepresentable: this function requires
/// an [`AdmittedDeclaration`], which can only be obtained through [`admit`](crate::prime_algos::prime_algorithm_0_admission::admit).
///
/// ```compile_fail
/// use crate::prime_algos::prime_algorithm_0::{run_admitted, DeclarationFill};
/// use crate::ddc::domain_adapters::GenericMss0Adapter;
///
/// let unadmitted = DeclarationFill {
///     carrier: Some("torus".into()),
///     primitive_difference: Some("d0".into()),
///     zero_rel: Some("z0".into()),
///     observer: Some("obs".into()),
///     witnesses: vec!["w".into()],
/// };
/// run_admitted(&unadmitted, &GenericMss0Adapter);
/// ```
pub fn run_admitted(
    admitted: &AdmittedDeclaration,
    adapter: &dyn DomainAdapter,
) -> PrimeAlgorithm0Receipt {
    let mut trace = DdaTrace::new();
    let mut steps: Vec<PrimeStepRecord> = Vec::new();
    let family = adapter.residual_family_label();

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

    // Step 1 — carrier (already admitted)
    emit(
        1,
        DdaOp::ContextExposure,
        true,
        format!("declare carrier={}", admitted.carrier()),
    );
    emit(1, DdaOp::Integration, true, "ledger open".into());

    // Step 2 — δ (already admitted)
    emit(
        2,
        DdaOp::Integration,
        true,
        format!("declare δ={}", admitted.primitive_difference()),
    );

    // Step 3 — ZeroRel (already admitted)
    emit(
        3,
        DdaOp::Integration,
        true,
        format!("declare ZeroRel={}", admitted.zero_rel()),
    );

    // Step 4 — C• (already admitted)
    let cochain = admitted.cochain().clone();
    if let CochainSlot::Constructed {
        dim_c0,
        dim_c1,
        dim_c2,
        ..
    } = &cochain
    {
        emit(
            4,
            DdaOp::ContextExposure,
            true,
            format!(
                "construct C• dims=({},{},{}) d∘d=0 ok",
                dim_c0, dim_c1, dim_c2
            ),
        );
    }

    // Step 5 — Q¹
    let delta = admitted.primitive_difference();
    let q1 = Some(format!("Q1[{delta}]"));
    emit(
        5,
        DdaOp::ResidualProjection,
        true,
        format!("compute Q¹ residual core=[{delta}]"),
    );

    // Step 6 — separate Φ₁ from Γ₂ (MEASUREMENT: occurs strictly after admission!)
    let (p, g) = adapter.residual_masses();
    let phi1 = Some(p);
    let gamma2 = Some(g);
    let branch = DefectBranch::from_masses(p, g);
    emit(
        6,
        DdaOp::Integration,
        true,
        format!("separate Φ₁={p} from Γ₂={g}; branch={}", branch.as_str()),
    );

    // Step 7 — observer (already admitted)
    let observer = Some(admitted.observer().to_string());
    emit(
        7,
        DdaOp::Integration,
        true,
        format!("declare observer/profile={}", admitted.observer()),
    );

    // Step 8 — witnesses (already admitted)
    let witnesses = admitted.witnesses().to_vec();
    emit(
        8,
        DdaOp::Integration,
        true,
        format!("identify witnesses={witnesses:?}"),
    );

    // Step 9 — operator / lift search under H-O3 PaperER003 nine-bit gate
    let (structure_search, licensed_lift) = run_step9_lift_gate(adapter.lift_proposal(branch));
    let (step9_op, step9_exec, step9_msg) = format_step9_emission(&structure_search);
    emit(9, step9_op, step9_exec, step9_msg);

    // Step 10 — route survivors
    let routing = format!(
        "branch={}; survivors={:?}; lift={:?}",
        branch.as_str(),
        q1,
        structure_search
    );
    emit(
        10,
        DdaOp::ResidualProjection,
        true,
        format!("route survivors branch={}", branch.as_str()),
    );

    // Step 11 — terminalize
    let term = select_prime_terminal(&branch, &structure_search);
    emit(
        11,
        DdaOp::Terminalize,
        true,
        format!("terminalize {}", term.as_str()),
    );
    let terminal = term;

    // Step 12 — literature only after terminal
    let (lit_msg, literature_compare) =
        format_step12_literature(adapter.literature_note().as_deref(), terminal);
    emit(12, DdaOp::Integration, true, lit_msg);

    // Backfill per-step residual state
    for record in steps.iter_mut() {
        if record.prime_step >= 6 {
            record.phi1_after = phi1;
            record.gamma2_after = gamma2;
        }
    }

    let letter_tape: String = steps.iter().map(|s| s.op.as_str()).collect();
    let letters_spaced = trace.letters();
    let trace_terminal = format_trace_terminal(trace.terminal());

    debug_assert_eq!(trace.authority_effect(), AuthorityEffect::None);

    PrimeAlgorithm0Receipt {
        domain: adapter.domain(),
        carrier: Some(admitted.carrier().to_string()),
        primitive_difference: Some(admitted.primitive_difference().to_string()),
        zero_rel: Some(admitted.zero_rel().to_string()),
        cochain,
        q1,
        phi1,
        gamma2,
        observer,
        witnesses,
        structure_search,
        licensed_lift,
        routing,
        literature_compare,
        branch,
        terminal,
        letter_tape,
        letters_spaced,
        trace_terminal,
        residual_family_label: family,
        authority_effect: AuthorityEffect::None,
        steps,
        evidence_provenance: adapter.evidence_provenance(),
    }
}

fn run_step9_lift_gate(proposal: LiftProposal) -> (LiftSearch, Option<LicensedLiftAdmission>) {
    match proposal {
        LiftProposal::Candidate {
            generators,
            nine_bits,
            certificate,
        } => match step9_licensed_lift_gate(generators, nine_bits, certificate) {
            Ok(adm) => (
                LiftSearch::LiftAdmitted {
                    generators: adm.generators().to_vec(),
                    nine_bits: *adm.nine_bits(),
                    lean_module: adm.lean_module().to_string(),
                },
                Some(adm),
            ),
            Err(e) => (
                LiftSearch::LiftRefused {
                    reason: e.to_string(),
                },
                None,
            ),
        },
        other => (evaluate_lift_proposal(other), None),
    }
}

fn format_step9_emission(structure_search: &LiftSearch) -> (DdaOp, bool, String) {
    match structure_search {
        LiftSearch::LiftAdmitted {
            generators,
            lean_module,
            ..
        } => (
            DdaOp::Lift,
            true,
            format!("lift admitted under {lean_module} nine-bit gate: {generators:?}"),
        ),
        LiftSearch::LiftRefused { reason } => (
            DdaOp::Refusal,
            false,
            format!("lift refused by step-9 gate: {reason}"),
        ),
        LiftSearch::SameLevelRepairAttempted => (
            DdaOp::ExactRepair,
            true,
            "search same-level exact repair for Γ₂>0 open branch".into(),
        ),
        LiftSearch::OracleGap { note } => (DdaOp::Refusal, false, format!("oracle gap: {note}")),
        LiftSearch::SkippedClosed => (
            DdaOp::Integration,
            true,
            "no lift search: branch Closed or Unset".into(),
        ),
    }
}

fn select_prime_terminal(branch: &DefectBranch, structure_search: &LiftSearch) -> PrimeTerminal {
    match (branch, structure_search) {
        (DefectBranch::Closed, _) => PrimeTerminal::Certificate,
        (_, LiftSearch::LiftAdmitted { .. }) => PrimeTerminal::Repair,
        (DefectBranch::StabilizedSurvivor, _) => PrimeTerminal::OracleNeeded,
        (DefectBranch::Open, _) => PrimeTerminal::OpenResidual,
        (DefectBranch::Unset, _) => PrimeTerminal::ClosedResidual,
    }
}

fn format_step12_literature(
    note: Option<&str>,
    terminal: PrimeTerminal,
) -> (String, Option<String>) {
    if let Some(note) = note {
        (
            format!(
                "literature compare after terminal={}: {note}",
                terminal.as_str()
            ),
            Some(format!(
                "after_terminal={}; feeds_authority=false; {note}",
                terminal.as_str()
            )),
        )
    } else {
        (
            "literature compare skipped (no note); still post-terminal only".into(),
            None,
        )
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

/// Run Algorithm Prime 000 for one domain adapter; emit DDA letter tape.
///
/// Phase 1 evaluates the 7-step admission gate without measuring residual masses.
/// If admission succeeds, Phase 2 executes the full 12-step fill order.
pub fn run_prime_algorithm_0(adapter: &dyn DomainAdapter) -> PrimeAlgorithm0Receipt {
    let decl = adapter.declaration();
    match crate::prime_algos::prime_algorithm_0_admission::admit(
        &decl,
        adapter.justify_cochain(),
        adapter.cochain_window().as_ref(),
    ) {
        Ok(admitted) => run_admitted(&admitted, adapter),
        Err(refusal) => refusal.to_receipt(adapter),
    }
}

pub use run_prime_algorithm_0 as run_oeprmalg0;

// Origin: engine/crates_rs/core_wdp/src/prime_algos/prime_algorithm_0.rs
// Claim: urn:core:crates_rs:core-wdp:prime-algorithm-0:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::prime_algos::domain_adapters::{
        CodaResidualAdapter, FspChannelAAdapter, GenericMss0Adapter, MubWallAdapter,
    };

    #[test]
    fn generic_mss0_emits_letter_tape_with_crt() {
        let r = run_prime_algorithm_0(&GenericMss0Adapter);
        assert_eq!(r.authority_effect, AuthorityEffect::None);
        assert!(r.letter_tape.contains('C'));
        assert!(r.letter_tape.contains('R'));
        assert!(r.letter_tape.contains('T'));
        assert_eq!(r.branch, DefectBranch::StabilizedSurvivor);
        assert!(matches!(
            r.terminal,
            PrimeTerminal::Repair | PrimeTerminal::OracleNeeded
        ));
        // H-O3: step-9 admission carries PaperER003 binding
        let lift = r.licensed_lift.expect("generic MSS-0 should admit lift");
        assert!(lift.nine_bits().all_satisfied());
        assert_eq!(lift.lean_module(), "PaperER003.LicensedLiftCertificate");
        assert!(lift.checklist().lift_checklist_complete());
        // literature is last prime step
        let last_lit = r.steps.iter().filter(|s| s.prime_step == 12).count();
        assert!(last_lit >= 1);
        let first_t = r.steps.iter().position(|s| s.op == "T").unwrap();
        assert!(r.steps[..first_t].iter().all(|s| s.prime_step != 12));
    }

    #[test]
    fn missing_carrier_refuses() {
        struct Bad;
        impl DomainAdapter for Bad {
            fn domain(&self) -> PrimeDomain {
                PrimeDomain::Generic
            }
            fn declaration(&self) -> DeclarationFill {
                DeclarationFill {
                    carrier: None,
                    primitive_difference: Some("d".into()),
                    zero_rel: Some("z".into()),
                    observer: Some("o".into()),
                    witnesses: vec![],
                }
            }
            fn justify_cochain(&self) -> bool {
                false
            }
            fn cochain_window(&self) -> Option<CochainWindow> {
                None
            }
            fn residual_masses(&self) -> (u64, u64) {
                (0, 0)
            }
            fn lift_proposal(&self, _: DefectBranch) -> LiftProposal {
                LiftProposal::SkipClosed
            }
            fn literature_note(&self) -> Option<String> {
                None
            }
        }
        let r = run_prime_algorithm_0(&Bad);
        assert_eq!(r.terminal, PrimeTerminal::Refusal);
        assert!(r.letter_tape.contains('M'));
        assert!(r.letter_tape.contains('T'));
    }

    #[test]
    fn multi_domain_adapters_all_none_authority() {
        let adapters: Vec<&dyn DomainAdapter> = vec![
            &GenericMss0Adapter,
            &MubWallAdapter,
            &FspChannelAAdapter,
            &CodaResidualAdapter,
        ];
        for a in adapters {
            let r = run_prime_algorithm_0(a);
            assert_eq!(r.authority_effect, AuthorityEffect::None);
            assert!(!r.letter_tape.is_empty());
        }
    }

    #[test]
    fn write_files_emits_letter_tape_and_receipt() {
        let r = run_prime_algorithm_0(&GenericMss0Adapter);
        let dir =
            std::env::temp_dir().join(format!("core_prime_algorithm_0_{}", std::process::id()));
        let _ = std::fs::remove_dir_all(&dir);
        r.write_files(&dir).expect("write_files");
        assert!(dir.join("letter_tape.txt").is_file());
        assert!(dir.join("prime_algorithm_0_receipt.json").is_file());
        assert!(dir.join("oeprmalg0_receipt.json").is_file());
        let tape = std::fs::read_to_string(dir.join("letter_tape.txt")).unwrap();
        assert!(tape.starts_with(&r.letter_tape));
        let _ = std::fs::remove_dir_all(&dir);
    }

    /// ADR-009: the pre-rename artifact name is still emitted, byte-identical.
    #[test]
    fn write_files_still_emits_the_pre_rename_receipt_name() {
        let r = run_prime_algorithm_0(&GenericMss0Adapter);
        let dir = std::env::temp_dir().join(format!(
            "core_prime_algorithm_0_compat_{}",
            std::process::id()
        ));
        let _ = std::fs::remove_dir_all(&dir);
        r.write_files(&dir).expect("write_files");

        let primary_name = dir.join("prime_algorithm_0_receipt.json");
        let new_name = dir.join("oeprmalg0_receipt.json");
        let old_name = dir.join("prime000_receipt.json");
        assert!(primary_name.is_file(), "primary receipt name was dropped");
        assert!(new_name.is_file(), "oeprmalg0 receipt name was dropped");
        assert!(old_name.is_file(), "pre-rename receipt name was dropped");
        assert_eq!(
            std::fs::read(&primary_name).unwrap(),
            std::fs::read(&old_name).unwrap(),
            "the receipt artifacts must be byte-identical"
        );
        let _ = std::fs::remove_dir_all(&dir);
    }
}
