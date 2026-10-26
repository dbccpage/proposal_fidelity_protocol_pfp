//! Sort 4 — **Event**: a presentation or an admission.
//!
//! Crate boundary: coda-carrier.  Source: `model.py`, the six event
//! dataclasses.  Exactly one variant changes nothing (`Supply`); four admit;
//! one imposes.  The grammar is closed: there is no "remove", no "rename",
//! no "observe" — observation is not an event (L7, `judgment.rs`), and
//! removal was never derived anywhere in the estate (§13.10).
//!
//! L3 is a declared API discipline. The lexical scan in census.rs does
//! not prove state-to-event functions cannot exist.

use std::fmt;

use crate::mark::Pair;
use crate::regime::{Args, FormId};
use crate::token::Token;

/// An event of the sealed grammar.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum Event {
    /// External presentation of a token.  Not an admission.  Inert (L1).
    Supply(Token),
    /// Admission of a presented token as a datum.  Re-admission of an
    /// admitted token is a designation, not a duplication (L6).
    AdmitDatum(Token),
    /// Admission of a judgment form of the given arity (`>= 1`).
    AdmitForm(usize),
    /// Admission of a judgment instance over admitted marks.
    AdmitInst(FormId, Args),
    /// Admission of the uniform all-tuples rule for a form.
    AdmitRuleAll(FormId),
    /// External requirement: the two marks must be internally separable.
    Impose(Pair),
}

impl Event {
    /// Whether this event is an admission (changes state when well-formed).
    /// `Supply` is not; `Impose` is a requirement, not an admission, and is
    /// reported separately by `is_imposition`.
    pub fn is_admission(&self) -> bool {
        matches!(
            self,
            Event::AdmitDatum(_) | Event::AdmitForm(_) | Event::AdmitInst(_, _) | Event::AdmitRuleAll(_)
        )
    }

    /// Whether this event is an externally imposed requirement.
    pub fn is_imposition(&self) -> bool {
        matches!(self, Event::Impose(_))
    }

    /// Whether this event is a bare presentation.
    pub fn is_supply(&self) -> bool {
        matches!(self, Event::Supply(_))
    }

    /// The token an event names, if it names one.  A *mention* is not an
    /// event; this is the metatheory reading the event.
    pub fn token(&self) -> Option<&Token> {
        match self {
            Event::Supply(t) | Event::AdmitDatum(t) => Some(t),
            _ => None,
        }
    }
}

/// An event is ill-formed relative to the current regime.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct AdmissionError(pub String);

impl fmt::Display for AdmissionError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "admission refused: {}", self.0)
    }
}

impl std::error::Error for AdmissionError {}

impl fmt::Display for Event {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Event::Supply(t) => write!(f, "supply {t}"),
            Event::AdmitDatum(t) => write!(f, "admit_datum {t}"),
            Event::AdmitForm(a) => write!(f, "admit_form arity={a}"),
            Event::AdmitInst(form, args) => {
                let a: Vec<String> = args.iter().map(|m| m.0.to_string()).collect();
                write!(f, "admit_inst form={form} args=[{}]", a.join(","))
            }
            Event::AdmitRuleAll(form) => write!(f, "admit_rule_all form={form}"),
            Event::Impose(p) => write!(f, "impose_separation {p}"),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn the_grammar_has_exactly_one_inert_kind() {
        let events = [
            Event::Supply(Token::new("x")),
            Event::AdmitDatum(Token::new("x")),
            Event::AdmitForm(1),
            crate::testkit::inst(0, &[0]),
            Event::AdmitRuleAll(0),
            Event::Impose(Pair::of(0, 1)),
        ];
        let inert: Vec<&Event> = events.iter().filter(|e| e.is_supply()).collect();
        assert_eq!(inert.len(), 1);
        assert_eq!(events.iter().filter(|e| e.is_admission()).count(), 4);
        assert_eq!(events.iter().filter(|e| e.is_imposition()).count(), 1);
    }
}
