//! # The operad host for PFP workflows
//!
//! AuthorityEffect: None. This crate checks and records; it admits nothing outside its own ledger.
//! Contract: urn:pfp-operads:lib:v1
//!
//! One place, in Rust, where a workflow's operad work is checked:
//!
//! * [`term`]: operations typed by the canon's colours, with a closed set of exact bodies, composed
//!   as trees by substitution and evaluated on exact values. There is no float in this crate.
//! * [`laws`]: associativity (sequential and parallel), unit and declared symmetry, checked on
//!   structure, cost and behaviour over a finite panel of inputs.
//! * [`ledger`]: a hash-chained record of host-witnessed failures, the rules proposed from them, the
//!   held-out trial each rule must win, and the rules a later run may load.
//! * [`envelope`]: the reply envelope of the full-slot workflows (slot report, operad candidates,
//!   DDC moves), with each candidate typed against the canon.
//! * [`judge`]: the host's own exact answer to a finite task, compared with the reply's.
//! * [`mining`]: the screen of a mining reply (no digits outside quotes, well-formed and grounded
//!   candidates, guidance for every grounded slot) and signature reuse between candidate lists.
//! * [`grounding`]: the grounded slots of a solver reply, rechecked against the task's public input.
//! * [`learning`]: the ledger records the host writes itself, a failure it witnessed and a trial it
//!   scored, from answers it judges with [`judge`].
//! * [`running`]: a reply's operad candidates that name a body, run on the task's public input and
//!   compared with the judge's own result.
//! * [`loading`]: the seed a later run loads, a task's seed with the ledger's rules after it, and
//!   the check that a seed is exactly what a ledger state loads.
//! * [`turns`]: a model turn as a workflow run stores it, judged by the host into a failure record
//!   or, in fair pairs, into a rule's trial record.
//! * [`patch`]: a text patch in unified format, read strictly and applied exactly where it says.
//! * [`repair`]: bounded code repair, one supplied patch taken through capture, observe, evaluate,
//!   incorporate, disposition and terminal, with a failure record when the candidate is at fault.
//! * [`workshop`]: the source tree, run folder and local commands a repair run uses on a real
//!   machine. This is the one module that writes files and starts processes.
//! * [`datum`]: exact JSON, with integers read from their digits and nothing rounded.
//! * [`exact`]: rational arithmetic and linear algebra over unbounded integers.
//! * [`perm`]: permutations in one-line notation, composed directly and as matrices.
//! * [`families`]: the host side of a workflow family run. The host writes each prompt, refuses
//!   one that carries a sealed value, and gives the verdict with the predicates it recorded.
//! * [`host`]: the JSON entry points a workflow calls, also exposed by the `pfp_operad` binary.
//!
//! Every vocabulary (colours, DDC letters, failure classes, capability kinds, statuses) is read
//! from `core_operad_canon`. A pass here covers the supplied operations on the supplied panel; it
//! is not a proof for all terms.

pub mod datum;
pub mod envelope;
pub mod exact;
pub mod families;
pub mod grounding;
pub mod host;
pub mod judge;
pub mod laws;
pub mod learning;
pub mod ledger;
pub mod loading;
pub mod mining;
pub mod patch;
pub mod perm;
pub mod repair;
pub mod running;
pub mod term;
pub mod turns;
pub mod workshop;

use serde::Serialize;

/// A typed refusal: a stable code and a sentence for the reader.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct Refusal {
    pub code: &'static str,
    pub message: String,
}

impl Refusal {
    pub fn new(code: &'static str, message: impl Into<String>) -> Self {
        Self {
            code,
            message: message.into(),
        }
    }
}

impl std::fmt::Display for Refusal {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}: {}", self.code, self.message)
    }
}

impl std::error::Error for Refusal {}

/// The values of one canon type, or a refusal naming the missing type.
pub(crate) fn canon_values(type_id: &'static str) -> Result<&'static [&'static str], Refusal> {
    core_operad_canon::type_by_id(type_id)
        .map(|entry| entry.values)
        .ok_or_else(|| Refusal::new("CANON_TYPE_MISSING", format!("canon has no type {type_id}")))
}

#[cfg(test)]
mod tests {
    use super::{canon_values, Refusal};

    #[test]
    fn a_refusal_reads_as_code_then_message() {
        let refusal = Refusal::new("ARITY", "expected two inputs");
        assert_eq!(refusal.to_string(), "ARITY: expected two inputs");
    }

    #[test]
    fn a_canon_type_resolves_to_its_values() {
        assert_eq!(
            canon_values("operad_variant").map(<[_]>::to_vec),
            Ok(vec!["Planar", "Symmetric"])
        );
    }

    #[test]
    fn a_missing_canon_type_is_refused_by_name() {
        assert_eq!(
            canon_values("no_such_type"),
            Err(Refusal::new(
                "CANON_TYPE_MISSING",
                "canon has no type no_such_type"
            ))
        );
    }
}
