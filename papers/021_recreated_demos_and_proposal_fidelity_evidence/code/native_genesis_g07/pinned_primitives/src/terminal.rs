//! Sort 11 — **Terminal**: a declared final status, and the terminalizer
//! that assigns one.
//!
//! Crate boundary: coda-terminal.  Source: crosstab §13.9 (the five
//! statuses); Lean `refusal_non_absorbing` — *refusal is a record, not a
//! terminal; termination belongs to whatever produces the history*.
//!
//! The estate has **no terminalizer primitive** (crosstab §3): `terminal` is
//! a node status, and the run ends when the history producer stops
//! producing.  So the terminalizer here is *outside the object language by
//! construction*: it reads a run verdict and a scope and names a status.  It
//! never changes state.
//!
//! The author's Omega engine has five stopping points.  Two are named in the
//! conversation: **exact** and **budget unknown** ("I give you a budget and
//! you've overran it").  The mapping used here:
//!
//! | author's terminalizer | this crate | when |
//! |---|---|---|
//! | exact | `Accepted` | every recorded requirement is met and witnessed |
//! | budget unknown | `BudgetExceeded` | fuel or the round bound ran out first |
//! | — | `Refused` | an exhaustion certificate was recorded and nothing else remains |
//! | — | `Unresolved` | a tie was retained and no outside declaration broke it, or a licence was withheld, or nothing was asked |
//! | — | `ObserverIncomplete` | the declared panel cannot certify what the metatheory sees |
//!
//! A `Terminal` is **never** returned bare: `Terminated` carries the scope
//! and the certificate (`FW-SCOPE`).

use std::fmt;

use crate::certificate::Certificate;
use crate::mark::Pair;
use crate::scope::Scope;

/// The five declared final statuses.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum Terminal {
    /// Every recorded requirement is met, with a witness.
    Accepted,
    /// An obstruction was recorded with its exhaustion certificate.
    Refused,
    /// No status can be assigned without an outside declaration.
    Unresolved,
    /// The declared budget or round bound ran out.
    BudgetExceeded,
    /// The declared observer panel cannot see what the metatheory sees.
    ObserverIncomplete,
}

/// What a run reports to the terminalizer.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum RunVerdict {
    /// All recorded requirements satisfied; the witnesses.
    Quiescent {
        /// One witness per requirement.
        witnesses: Vec<(Pair, String)>,
    },
    /// Nothing was asked and nothing moved.
    NothingAsked,
    /// Invalid configuration, history, or outside answer; no success claim.
    InvalidInput {
        /// The rejected input.
        reason: String,
    },
    /// Every remaining violated requirement carries a refusal.
    Obstructed {
        /// The first refusal's certificate.
        certificate: Certificate,
    },
    /// The fuel or the round bound ran out.
    OutOfBudget {
        /// Which bound.
        which: String,
    },
    /// A tie was retained and the outside declared nothing.
    TieRetained {
        /// How many classes.
        classes: usize,
    },
    /// Structure was needed and the licence was withheld.
    LicenceWithheld,
    /// The declared panel cannot certify a satisfied requirement.
    PanelBlind {
        /// Which pairs.
        pairs: Vec<Pair>,
    },
}

/// A terminal with its scope and certificate.  The only way a `Terminal`
/// leaves this module.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Terminated {
    /// The status.
    pub terminal: Terminal,
    /// The certificate, if the status rests on one.
    pub certificate: Option<Certificate>,
    /// The scope.
    pub scope: Scope,
    /// One sentence.
    pub reason: String,
}

/// `τ` — assigns a status.  Reads; never writes.
pub trait Terminalizer {
    /// Terminalize a run verdict under a scope.
    fn terminalize(&self, verdict: &RunVerdict, scope: &Scope) -> Terminated;
}

/// A mapping of caller-declared verdicts, not an independent witness checker.
#[derive(Clone, Copy, Debug, Default)]
pub struct DeclaredTerminalizer;

impl Terminalizer for DeclaredTerminalizer {
    fn terminalize(&self, verdict: &RunVerdict, scope: &Scope) -> Terminated {
        use crate::certificate::{CheckId, ObjectId};
        let (terminal, certificate, reason) = match verdict {
            RunVerdict::InvalidInput { reason } => (Terminal::Unresolved, None, reason.clone()),
            RunVerdict::Quiescent { witnesses } if witnesses.is_empty() => (
                Terminal::Unresolved, None, "no separating witnesses supplied".into()),
            RunVerdict::Quiescent { witnesses } => (
                Terminal::Accepted,
                Some(Certificate::Witness {
                    object: ObjectId(format!("{} separating context(s)", witnesses.len())),
                    check: CheckId("separability::witness on every recorded requirement".into()),
                }),
                "every recorded requirement is met and witnessed".to_string(),
            ),
            RunVerdict::NothingAsked => (Terminal::Unresolved, None, "no separation requirement was recorded".to_string()),
            RunVerdict::Obstructed { certificate } if matches!(certificate, Certificate::Exhaustion { .. }) => (
                Terminal::Refused,
                Some(certificate.clone()),
                "an obstruction is recorded with its exhaustion certificate and nothing else remains".to_string(),
            ),
            RunVerdict::Obstructed { .. } => (
                Terminal::Unresolved, None, "refusal requires an exhaustion declaration".into()),
            RunVerdict::OutOfBudget { which } => (Terminal::BudgetExceeded, None, format!("the declared {which} ran out")),
            RunVerdict::TieRetained { classes } => (
                Terminal::Unresolved,
                None,
                format!("{classes} tied classes retained; no outside declaration selected one"),
            ),
            RunVerdict::LicenceWithheld => (Terminal::Unresolved, None, "structure was needed and the licence was withheld".to_string()),
            RunVerdict::PanelBlind { pairs } => (
                Terminal::ObserverIncomplete,
                None,
                format!("the declared panel cannot certify {} satisfied pair(s)", pairs.len()),
            ),
        };
        Terminated { terminal, certificate, scope: scope.clone(), reason }
    }
}

impl fmt::Display for Terminal {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let s = match self {
            Terminal::Accepted => "ACCEPTED",
            Terminal::Refused => "REFUSED",
            Terminal::Unresolved => "UNRESOLVED",
            Terminal::BudgetExceeded => "BUDGET_EXCEEDED",
            Terminal::ObserverIncomplete => "OBSERVER_INCOMPLETE",
        };
        write!(f, "{s}")
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn a_terminal_never_leaves_without_its_scope() {
        let t = DeclaredTerminalizer.terminalize(&RunVerdict::NothingAsked, &Scope::sealed("L", "genesis"));
        assert_eq!(t.terminal, Terminal::Unresolved);
        assert_eq!(t.scope.reading, "L");
        assert!(t.certificate.is_none());
    }

    #[test]
    fn accepted_rests_on_a_witness_and_refused_on_an_exhaustion() {
        let s = Scope::sealed("F", "run");
        let empty = DeclaredTerminalizer.terminalize(&RunVerdict::Quiescent { witnesses: vec![] }, &s);
        assert_eq!(empty.terminal, Terminal::Unresolved);
        let a = DeclaredTerminalizer.terminalize(&RunVerdict::Quiescent {
            witnesses: vec![(Pair { i: crate::mark::Mark(0), j: crate::mark::Mark(1) }, "declared context".into())]
        }, &s);
        assert_eq!(a.terminal, Terminal::Accepted);
        let wrong_kind = DeclaredTerminalizer.terminalize(&RunVerdict::Obstructed {
            certificate: a.certificate.clone().unwrap()
        }, &s);
        assert_eq!(wrong_kind.terminal, Terminal::Unresolved);
        assert_eq!(a.certificate.unwrap().kind(), crate::certificate::CertKind::Witness);
        let cert = Certificate::Exhaustion {
            space: crate::certificate::SpaceId("menu".into()),
            bound: crate::certificate::Bound("b".into()),
            searched: 9,
        };
        let r = DeclaredTerminalizer.terminalize(&RunVerdict::Obstructed { certificate: cert.clone() }, &s);
        assert_eq!(r.terminal, Terminal::Refused);
        assert_eq!(r.certificate, Some(cert));
        let b = DeclaredTerminalizer.terminalize(&RunVerdict::OutOfBudget { which: "fuel".into() }, &s);
        assert_eq!(b.terminal, Terminal::BudgetExceeded);
    }
}
