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
//! * [`host`]: the JSON entry points a workflow calls, also exposed by the `pfp_operad` binary.
//!
//! Every vocabulary (colours, DDC letters, failure classes, capability kinds, statuses) is read
//! from `core_operad_canon`. A pass here covers the supplied operations on the supplied panel; it
//! is not a proof for all terms.

pub mod host;
pub mod laws;
pub mod ledger;
pub mod term;

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
