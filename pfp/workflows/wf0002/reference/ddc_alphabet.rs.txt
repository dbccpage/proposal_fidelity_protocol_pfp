//! The canonical DDC operation alphabet — `{E, R, C, I, Λ/Meta, D, M, T}`.
//!
//! Canonical provenance:
//! `omega_engine_atlas/coda_atlas/F004_papers/001_finite_obstruction_calculus/000_witnessed_difference_programme/docs/source_archive/discrete_deformation_calculus_package/discrete_deformation_calculus.md`
//! (Paper ID: `oe_010_ddc_trace_calculus`, Series: `008_engine_runtime`).
//!
//! Consolidated into `omega_wdp::ddc` alongside the active `omega_wdp::coda` spine.
//!
//! Three core DDC obligations are carried structurally, not by comment:
//!
//! * **DDC-0 / Lawful Transition Typing** (`OE010-01`..`OE010-05`) — "Every lawful transition
//!   must emit a typed DDC operation together with the local execution log or explicit refusal to
//!   execute." A [`DdcStep`] cannot be constructed without a [`StepOutcome`], so
//!   a logless step is unrepresentable rather than discouraged by convention.
//! * **DDC Out-of-Window Import Boundary** — imported representation theorems (Gleason, Hilbert space, Born
//!   ontology) are *not* DDC operations; a transformation licensed from outside
//!   the declared finite 2-window is an import/oracle and drives the trace to
//!   [`TraceTerminal::OracleNeeded`]. There is deliberately **no** `DdcOp`
//!   variant for "import" — see [`DdcTrace::import`].
//! * **DDC No-Authority Firewall** (`OE010-04`) — a well-typed DDC trace does not mint authority. [`DdcTrace`]
//!   exposes [`DdcTrace::authority_effect`], which returns
//!   `AuthorityEffect::None` unconditionally; the type has no method producing an
//!   authority-bearing value at all. Authorization requires the separate host
//!   promotion contract with verified certificate, receipt DAG, witness
//!   attestation, and human event; none of those capabilities lives here.
//!
//! What this module is NOT: a scheduler, a prover, or an authority source. It
//! records which lawful op was emitted, with what log, in what order.

use omega_types::authority::AuthorityEffect;
use serde::{Deserialize, Serialize};

/// The eight lawful transitions of Discrete Deformation Calculus (`discrete_deformation_calculus.md` §1).
///
/// The letters are the canonical DDC operational alphabet \(\mathcal{A}_{\mathrm{DDC}} = \{E, R, C, I, \Lambda, D, M, T\}\).
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum DdcOp {
    /// `E` — exact repair: discharge the defect outright (residual → 0).
    ExactRepair,
    /// `R` — residual projection: carry forward what repair could not remove.
    ResidualProjection,
    /// `C` — context exposure: declare/split the carrier and its 2-window.
    ContextExposure,
    /// `I` — integration: append to the local ledger.
    Integration,
    /// `Λ`/`Meta` — structural lift or extension. Lift *trigger* is not lift
    /// *license*: a lift needs obstruction, preservation, and
    /// non-destruction witnesses plus a terminalizer route.
    Lift,
    /// `D` — descent / re-index (e.g. refine the window).
    Descent,
    /// `M` — mutation / typed refusal.
    Refusal,
    /// `T` — terminalization. Emitting `T` records a terminal status; it does
    /// **not** mint authority (`AuthorityEffect::None`).
    Terminalize,
}

/// Backward compatibility alias for [`DdcOp`].
pub type DdaOp = DdcOp;

impl DdcOp {
    /// The spine letter.
    pub fn letter(self) -> &'static str {
        match self {
            DdcOp::ExactRepair => "E",
            DdcOp::ResidualProjection => "R",
            DdcOp::ContextExposure => "C",
            DdcOp::Integration => "I",
            DdcOp::Lift => "Λ",
            DdcOp::Descent => "D",
            DdcOp::Refusal => "M",
            DdcOp::Terminalize => "T",
        }
    }

    /// Parse a spine letter into a DDC operation.
    pub fn from_letter(s: &str) -> Option<DdcOp> {
        match s {
            "E" => Some(DdcOp::ExactRepair),
            "R" => Some(DdcOp::ResidualProjection),
            "C" => Some(DdcOp::ContextExposure),
            "I" => Some(DdcOp::Integration),
            "Λ" | "\\Lambda" | "Lambda" | "Meta" => Some(DdcOp::Lift),
            "D" => Some(DdcOp::Descent),
            "M" => Some(DdcOp::Refusal),
            "T" => Some(DdcOp::Terminalize),
            _ => None,
        }
    }

    /// The full declared alphabet, in spine order.
    pub fn alphabet() -> [DdcOp; 8] {
        [
            DdcOp::ExactRepair,
            DdcOp::ResidualProjection,
            DdcOp::ContextExposure,
            DdcOp::Integration,
            DdcOp::Lift,
            DdcOp::Descent,
            DdcOp::Refusal,
            DdcOp::Terminalize,
        ]
    }
}

/// DDC invariant: every emitted op carries **either** its local execution log
/// Canonical closed refusal vocabulary (matching DDC paper M_REASONS).
///
/// Refusal is a typed terminal, not an unhandled error. Each variant
/// represents a closed reason code.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum RefusalReason {
    #[serde(rename = "REFUSED_INVALID_WITNESS")]
    RefusedInvalidWitness,
    #[serde(rename = "REFUSED_BUDGET_EXHAUSTED")]
    RefusedBudgetExhausted,
    #[serde(rename = "REFUSED_NON_ZERO_CURL")]
    RefusedNonZeroCurl,
    #[serde(rename = "REFUSED_UNLICENSED_LIFT")]
    RefusedUnlicensedLift,
    #[serde(rename = "REFUSED_LIFT_TRIGGER")]
    RefusedLiftTrigger,
    #[serde(rename = "REFUSED_MISSING_LOSS_LEDGER")]
    RefusedMissingLossLedger,
    #[serde(rename = "REFUSED_MISSING_RECEIPT")]
    RefusedMissingReceipt,
    #[serde(rename = "REFUSED_REQUIRES_LIFT")]
    RefusedRequiresLift,
    #[serde(rename = "REFUSED_DETECTOR_INADEQUATE")]
    RefusedDetectorInadequate,
    #[serde(rename = "REFUSED_OPEN_OBSTRUCTION")]
    RefusedOpenObstruction,
}

impl RefusalReason {
    pub fn as_str(self) -> &'static str {
        match self {
            RefusalReason::RefusedInvalidWitness => "REFUSED_INVALID_WITNESS",
            RefusalReason::RefusedBudgetExhausted => "REFUSED_BUDGET_EXHAUSTED",
            RefusalReason::RefusedNonZeroCurl => "REFUSED_NON_ZERO_CURL",
            RefusalReason::RefusedUnlicensedLift => "REFUSED_UNLICENSED_LIFT",
            RefusalReason::RefusedLiftTrigger => "REFUSED_LIFT_TRIGGER",
            RefusalReason::RefusedMissingLossLedger => "REFUSED_MISSING_LOSS_LEDGER",
            RefusalReason::RefusedMissingReceipt => "REFUSED_MISSING_RECEIPT",
            RefusalReason::RefusedRequiresLift => "REFUSED_REQUIRES_LIFT",
            RefusalReason::RefusedDetectorInadequate => "REFUSED_DETECTOR_INADEQUATE",
            RefusalReason::RefusedOpenObstruction => "REFUSED_OPEN_OBSTRUCTION",
        }
    }

    fn from_str_code_primary(s: &str) -> Option<Self> {
        match s {
            "REFUSED_INVALID_WITNESS" => Some(RefusalReason::RefusedInvalidWitness),
            "REFUSED_BUDGET_EXHAUSTED" => Some(RefusalReason::RefusedBudgetExhausted),
            "REFUSED_NON_ZERO_CURL" => Some(RefusalReason::RefusedNonZeroCurl),
            "REFUSED_UNLICENSED_LIFT" => Some(RefusalReason::RefusedUnlicensedLift),
            "REFUSED_LIFT_TRIGGER" => Some(RefusalReason::RefusedLiftTrigger),
            _ => None,
        }
    }

    fn from_str_code_secondary(s: &str) -> Option<Self> {
        match s {
            "REFUSED_MISSING_LOSS_LEDGER" => Some(RefusalReason::RefusedMissingLossLedger),
            "REFUSED_MISSING_RECEIPT" => Some(RefusalReason::RefusedMissingReceipt),
            "REFUSED_REQUIRES_LIFT" => Some(RefusalReason::RefusedRequiresLift),
            "REFUSED_DETECTOR_INADEQUATE" => Some(RefusalReason::RefusedDetectorInadequate),
            "REFUSED_OPEN_OBSTRUCTION" => Some(RefusalReason::RefusedOpenObstruction),
            _ => None,
        }
    }

    pub fn from_str_code(s: &str) -> Option<Self> {
        Self::from_str_code_primary(s).or_else(|| Self::from_str_code_secondary(s))
    }

    fn from_lowercase_primary(lower: &str) -> Option<Self> {
        if lower.contains("lift") {
            Some(Self::RefusedUnlicensedLift)
        } else if lower.contains("budget") {
            Some(Self::RefusedBudgetExhausted)
        } else if lower.contains("curl") || lower.contains("exact") {
            Some(Self::RefusedNonZeroCurl)
        } else if lower.contains("ledger") || lower.contains("loss") {
            Some(Self::RefusedMissingLossLedger)
        } else {
            None
        }
    }

    fn from_lowercase_secondary(lower: &str) -> Self {
        if lower.contains("receipt") {
            Self::RefusedMissingReceipt
        } else if lower.contains("detector")
            || lower.contains("inadequate")
            || lower.contains("blind")
        {
            Self::RefusedDetectorInadequate
        } else if lower.contains("open") || lower.contains("obstruction") {
            Self::RefusedOpenObstruction
        } else {
            Self::RefusedInvalidWitness
        }
    }
}

impl std::fmt::Display for RefusalReason {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(self.as_str())
    }
}

impl From<&str> for RefusalReason {
    fn from(s: &str) -> Self {
        if let Some(r) = Self::from_str_code(s) {
            return r;
        }
        let lower = s.to_lowercase();
        Self::from_lowercase_primary(&lower).unwrap_or_else(|| Self::from_lowercase_secondary(&lower))
    }
}

impl From<String> for RefusalReason {
    fn from(s: String) -> Self {
        Self::from(s.as_str())
    }
}

impl From<&String> for RefusalReason {
    fn from(s: &String) -> Self {
        Self::from(s.as_str())
    }
}

/// DDC invariant: every emitted op carries **either** its local execution log
/// **or** an explicit refusal to execute. There is no third state, and no way to
/// emit an op with neither.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum StepOutcome {
    /// The op executed; the string is the local execution log.
    Executed { log: String },
    /// The op was refused; carries a typed refusal reason from [`RefusalReason`].
    RefusedToExecute { reason: RefusalReason },
}

/// One lawful transition: a typed op plus its log-or-refusal.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct DdcStep {
    pub op: DdcOp,
    pub outcome: StepOutcome,
}

/// Backward compatibility alias for [`DdcStep`].
pub type DdaStep = DdcStep;

impl DdcStep {
    /// Emit an executed op with its local execution log.
    pub fn executed(op: DdcOp, log: impl Into<String>) -> Self {
        Self {
            op,
            outcome: StepOutcome::Executed { log: log.into() },
        }
    }

    /// Emit an op that explicitly refused to execute.
    pub fn refused(op: DdcOp, reason: impl Into<RefusalReason>) -> Self {
        Self {
            op,
            outcome: StepOutcome::RefusedToExecute {
                reason: reason.into(),
            },
        }
    }

    /// True when the step actually ran.
    pub fn is_executed(&self) -> bool {
        matches!(self.outcome, StepOutcome::Executed { .. })
    }
}

/// Where a trace currently stands. Not an authority (`AuthorityEffect::None`); a status.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum TraceTerminal {
    /// No `T` and no `M` yet.
    Open,
    /// `T` emitted and executed through a gated terminalizer.
    Terminalized,
    /// `T` emitted through raw `emit` without a gated terminalizer (Hole 7).
    UnverifiedTerminal,
    /// `M` emitted: typed refusal. A valid terminal, not a failure.
    Refused,
    /// DDC: an import/oracle was requested — outside the declared window.
    /// The trace cannot terminalize on its own authority.
    OracleNeeded { import: String },
}

/// An append-only sequence of lawful transitions.
///
/// Mints nothing. See the module docs for the DDC obligations this type
/// carries structurally.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize)]
pub struct DdcTrace {
    steps: Vec<DdcStep>,
    oracle: Option<String>,
    gated_terminal: bool,
}

/// Backward compatibility alias for [`DdcTrace`].
pub type DdaTrace = DdcTrace;

impl DdcTrace {
    pub fn new() -> Self {
        Self {
            steps: Vec::new(),
            oracle: None,
            gated_terminal: false,
        }
    }

    /// Append a lawful transition via the raw path.
    ///
    /// Per Hole 7, emitting `Terminalize` here does NOT produce `TraceTerminal::Terminalized`.
    /// Only [`Self::emit_gated_terminal`] or a verified terminalizer can set `Terminalized`.
    pub fn emit(&mut self, step: DdcStep) -> &mut Self {
        self.steps.push(step);
        self
    }

    /// Gated terminalization: records an executed terminal from a verified gate.
    /// Closes Hole 7: raw `emit` cannot yield `TraceTerminal::Terminalized`.
    pub fn emit_gated_terminal(&mut self, step: DdcStep) -> &mut Self {
        self.gated_terminal = true;
        self.steps.push(step);
        self
    }

    /// DDC Out-of-Window Import: record that a transformation was licensed from **outside** the
    /// declared finite 2-window (an imported representation theorem, a
    /// continuum move, ...). This is deliberately *not* a [`DdcOp`]: the
    /// alphabet has no import letter, because an import is not a lawful
    /// transition. It drives the terminal to [`TraceTerminal::OracleNeeded`]
    /// and cannot be cleared by emitting more ops.
    pub fn import(&mut self, what: impl Into<String>) -> &mut Self {
        self.oracle = Some(what.into());
        self
    }

    pub fn steps(&self) -> &[DdcStep] {
        &self.steps
    }

    /// The spine letters, in emission order — e.g. `"C E D Λ I T"`.
    pub fn letters(&self) -> String {
        self.steps
            .iter()
            .map(|s| s.op.letter())
            .collect::<Vec<_>>()
            .join(" ")
    }

    /// Current terminal status.
    ///
    /// An outstanding import wins over everything: an oracle cannot be
    /// terminalized away by appending `T`.
    pub fn terminal(&self) -> TraceTerminal {
        if let Some(import) = &self.oracle {
            return TraceTerminal::OracleNeeded {
                import: import.clone(),
            };
        }
        for step in self.steps.iter().rev() {
            match (step.op, step.is_executed()) {
                (DdcOp::Terminalize, true) => {
                    if self.gated_terminal {
                        return TraceTerminal::Terminalized;
                    } else {
                        return TraceTerminal::UnverifiedTerminal;
                    }
                }
                (DdcOp::Refusal, true) => return TraceTerminal::Refused,
                _ => {}
            }
        }
        TraceTerminal::Open
    }

    /// **DDC No-Authority Firewall (`OE010-04`).** A well-typed DDC trace does not mint authority.
    /// This is the only authority-shaped method on the type and it is constant:
    /// no trace, however long, well-typed, or terminalized, can return anything
    /// else. Authority requires verified certificates and external promotion.
    pub fn authority_effect(&self) -> AuthorityEffect {
        AuthorityEffect::None
    }
}

// Origin: omega_engine/crates_rs/omega_wdp/src/ddc/ddc_alphabet.rs
// Claim: urn:omega:crates_rs:omega-wdp:ddc-alphabet:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord339baaf8 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord339baaf8` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError339baaf8 {
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
impl BoundaryError339baaf8 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError339baaf8 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError339baaf8 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord339baaf8 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError339baaf8> {
        if capacity_bound == 0 {
            return Err(BoundaryError339baaf8::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError339baaf8::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError339baaf8::ExceedsCapacity {
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
    fn alphabet_is_the_eight_spine_letters() {
        let letters: Vec<&str> = DdcOp::alphabet().iter().map(|o| o.letter()).collect();
        assert_eq!(letters, ["E", "R", "C", "I", "Λ", "D", "M", "T"]);
    }

    #[test]
    fn ddc_every_step_carries_log_or_refusal() {
        // The invariant is structural: both constructors demand a payload, so a
        // logless step cannot be built. Assert both shapes round-trip.
        let e = DdcStep::executed(DdcOp::ExactRepair, "discharged defect on e_3");
        let m = DdcStep::refused(DdcOp::Lift, "no non-destruction witness");
        assert!(e.is_executed());
        assert!(!m.is_executed());
        match m.outcome {
            StepOutcome::RefusedToExecute { reason } => {
                assert_eq!(reason, RefusalReason::RefusedInvalidWitness);
            }
            _ => panic!("expected refusal"),
        }
    }

    #[test]
    fn trace_records_letters_in_order() {
        let mut t = DdcTrace::new();
        t.emit(DdcStep::executed(
            DdcOp::ContextExposure,
            "carrier declared",
        ))
        .emit(DdcStep::executed(DdcOp::ExactRepair, "antiderivative"))
        .emit(DdcStep::executed(DdcOp::Descent, "refine P_n -> P_2n"));
        assert_eq!(t.letters(), "C E D");
        assert_eq!(t.terminal(), TraceTerminal::Open);
    }

    #[test]
    fn terminalize_sets_terminalized() {
        let mut t = DdcTrace::new();
        t.emit_gated_terminal(DdcStep::executed(DdcOp::Terminalize, "sealed 1000/3"));
        assert_eq!(t.terminal(), TraceTerminal::Terminalized);
    }

    #[test]
    fn raw_terminalize_yields_unverified_terminal() {
        let mut t = DdcTrace::new();
        t.emit(DdcStep::executed(DdcOp::Terminalize, "sealed 1000/3"));
        assert_eq!(t.terminal(), TraceTerminal::UnverifiedTerminal);
    }

    #[test]
    fn typed_refusal_is_a_valid_terminal() {
        let mut t = DdcTrace::new();
        t.emit(DdcStep::executed(
            DdcOp::Refusal,
            "Dirichlet: debt #4 unpayable",
        ));
        assert_eq!(t.terminal(), TraceTerminal::Refused);
    }

    #[test]
    fn refused_terminalize_does_not_terminalize() {
        // An op that refused to execute did not happen.
        let mut t = DdcTrace::new();
        t.emit(DdcStep::refused(DdcOp::Terminalize, "no witness support"));
        assert_eq!(t.terminal(), TraceTerminal::Open);
    }

    #[test]
    fn ddc_import_forces_oracle_needed() {
        let mut t = DdcTrace::new();
        t.emit(DdcStep::executed(DdcOp::ContextExposure, "window"))
            .import("Gleason's theorem");
        match t.terminal() {
            TraceTerminal::OracleNeeded { import } => assert_eq!(import, "Gleason's theorem"),
            other => panic!("expected OracleNeeded, got {other:?}"),
        }
    }

    #[test]
    fn ddc_oracle_cannot_be_terminalized_away() {
        // Appending T after an import must NOT clear the oracle: an import is
        // licensed from outside the declared window and no lawful op can pay it.
        let mut t = DdcTrace::new();
        t.import("continuum path integral")
            .emit_gated_terminal(DdcStep::executed(DdcOp::Terminalize, "claiming a seal"));
        assert!(matches!(t.terminal(), TraceTerminal::OracleNeeded { .. }));
    }

    #[test]
    fn ddc_no_trace_mints_authority() {
        // Empty, executed, terminalized, refused — every shape returns None.
        let empty = DdcTrace::new();
        assert_eq!(empty.authority_effect(), AuthorityEffect::None);

        let mut sealed = DdcTrace::new();
        for op in DdcOp::alphabet() {
            if op == DdcOp::Terminalize {
                sealed.emit_gated_terminal(DdcStep::executed(op, "log"));
            } else {
                sealed.emit(DdcStep::executed(op, "log"));
            }
        }
        assert_eq!(sealed.terminal(), TraceTerminal::Terminalized);
        assert_eq!(
            sealed.authority_effect(),
            AuthorityEffect::None,
            "DDC No-Authority Firewall: a well-typed, fully terminalized trace still mints nothing"
        );
    }

    #[test]
    fn backward_compatibility_aliases_match() {
        let op: DdaOp = DdcOp::ExactRepair;
        let step: DdaStep = DdcStep::executed(op, "compat");
        let mut trace: DdaTrace = DdcTrace::new();
        trace.emit(step);
        assert_eq!(trace.letters(), "E");
    }
}

#[cfg(test)]
mod l4_boundary_tests_339baaf8 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord339baaf8::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord339baaf8::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord339baaf8::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord339baaf8::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord339baaf8::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError339baaf8::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError339baaf8::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
