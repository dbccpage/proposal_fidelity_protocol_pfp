//! The one definition of every operad type in this repository.
//!
//! Each closed vocabulary the operad code uses (colours, DDC letters, capability kinds, lifecycle
//! facets, dispositions, ...) is written exactly once, in [`types::OPERAD_TYPES`]. Everything else
//! reads it:
//!
//! * Rust crates depend on this crate ([`OperadColour`], [`DdcOp`], [`OPERAD_COLOURS`]).
//! * Python imports `operads/canon/_generated.py`, and data consumers read
//!   `operads/canon/operad_canon.json`. Both files are written by `cargo run -p core_operad_canon
//!   -- write` and checked by `-- check` and by this crate's tests, so they cannot be hand-edited
//!   without failing.
//! * The YAML registry in `operads/skill_operad/yaml/operad_types/` lists only where each type is
//!   used; its checker takes the canonical values from the generated JSON.
//!
//! AuthorityEffect: None. This crate names values; it admits, executes and certifies nothing.

pub mod render;
pub mod subcolour;
pub mod types;

use serde::{Deserialize, Serialize};

pub use subcolour::{schema_of, SUBCOLOUR_SCHEMAS};
pub use types::{type_by_id, OPERAD_TYPES, PYTHON_ENUMS};

/// The registry family a type belongs to; one YAML file per family.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Family {
    CapabilitiesAndLifecycle,
    ColoursAndWires,
    Operations,
    SignatureFamilies,
    Operands,
    ImmuneAndNegative,
}

impl Family {
    pub const ALL: [Family; 6] = [
        Family::CapabilitiesAndLifecycle,
        Family::ColoursAndWires,
        Family::Operations,
        Family::SignatureFamilies,
        Family::Operands,
        Family::ImmuneAndNegative,
    ];

    pub fn as_str(self) -> &'static str {
        match self {
            Family::CapabilitiesAndLifecycle => "capabilities_and_lifecycle",
            Family::ColoursAndWires => "colours_and_wires",
            Family::Operations => "operations",
            Family::SignatureFamilies => "signature_families",
            Family::Operands => "operands",
            Family::ImmuneAndNegative => "immune_and_negative",
        }
    }
}

/// `Settled` when every source agrees; `Proposed` while a decision is still open.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Status {
    Settled,
    Proposed,
}

impl Status {
    pub fn as_str(self) -> &'static str {
        match self {
            Status::Settled => "SETTLED",
            Status::Proposed => "PROPOSED",
        }
    }
}

/// One operad type: its canonical value set and, while `Proposed`, the decision it waits on.
#[derive(Debug, Clone, Copy)]
pub struct OperadType {
    pub id: &'static str,
    pub family: Family,
    pub description: &'static str,
    pub status: Status,
    /// A closed type admits no value outside `values`; an open one lists the values seen so far.
    pub closed: bool,
    pub values: &'static [&'static str],
    pub decision: Option<&'static str>,
    pub note: Option<&'static str>,
    /// Every value is a word over this other type's values (for example DDC motifs).
    pub letters_of: Option<&'static str>,
    /// Retired spellings and what they map to.
    pub legacy_map: &'static [(&'static str, &'static str)],
}

/// The ten sorts of the coloured operad. Every operation consumes colours and produces one.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum OperadColour {
    Audit,
    Code,
    Contract,
    Diagram,
    Ledger,
    Paper,
    Post,
    Proof,
    Receipt,
    State,
}

impl OperadColour {
    pub const ALL: [OperadColour; 10] = [
        OperadColour::Audit,
        OperadColour::Code,
        OperadColour::Contract,
        OperadColour::Diagram,
        OperadColour::Ledger,
        OperadColour::Paper,
        OperadColour::Post,
        OperadColour::Proof,
        OperadColour::Receipt,
        OperadColour::State,
    ];
    pub const NAMES: &'static [&'static str] = &[
        "Audit", "Code", "Contract", "Diagram", "Ledger", "Paper", "Post", "Proof", "Receipt",
        "State",
    ];

    pub fn as_str(self) -> &'static str {
        Self::NAMES[self as usize]
    }

    pub fn from_name(name: &str) -> Option<OperadColour> {
        Self::NAMES
            .iter()
            .position(|n| *n == name)
            .map(|i| Self::ALL[i])
    }

    /// What a value of this colour is, in one line.
    pub fn meaning(self) -> &'static str {
        match self {
            OperadColour::Audit => {
                "Symmetry audit, red-team diagnostic, compliance report, or defect escalation"
            }
            OperadColour::Code => {
                "Rust/Python implementation, AST, solver module, or Pydantic schema"
            }
            OperadColour::Contract => {
                "Nomos governance contract, prime rule YAML, or API boundary specification"
            }
            OperadColour::Diagram => {
                "DIME figure, quick-start card, AST graph, or visualization artifact"
            }
            OperadColour::Ledger => {
                "Claim queue row, refusal store, hypothesis tree, or issue register entry"
            }
            OperadColour::Paper => "OEARS paper package, LaTeX source, Pandoc AST, or claim ledger",
            OperadColour::Post => "Public math post, Glossa dialect draft, or forum cadence item",
            OperadColour::Proof => {
                "Lean 4 formal proof term, math derivation, or step-truth assertion"
            }
            OperadColour::Receipt => {
                "Evidence receipt, CI report, GTLA swarm review, or SHA256 manifest"
            }
            OperadColour::State => {
                "Repository, session worktree, git ref, or execution environment state"
            }
        }
    }
}

/// The colour names as a fixed array, for callers that test membership by string.
pub const OPERAD_COLOURS: [&str; 10] = [
    "Audit", "Code", "Contract", "Diagram", "Ledger", "Paper", "Post", "Proof", "Receipt", "State",
];

/// The eight lawful transitions of Discrete Deformation Calculus, `{E, R, C, I, Λ, D, M, T}`.
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

impl DdcOp {
    /// The letters in spine order, the same order as [`DdcOp::alphabet`].
    pub const LETTERS: &'static [&'static str] = &["E", "R", "C", "I", "Λ", "D", "M", "T"];

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
