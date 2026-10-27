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
//! The author's Core engine has five stopping points.  Two are named in the
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

fn terminalize_quiescent(witnesses: &[(Pair, String)]) -> (Terminal, Option<Certificate>, String) {
    use crate::certificate::{CheckId, ObjectId};
    if witnesses.is_empty() {
        (Terminal::Unresolved, None, "no separating witnesses supplied".into())
    } else {
        (
            Terminal::Accepted,
            Some(Certificate::Witness {
                object: ObjectId(format!("{} separating context(s)", witnesses.len())),
                check: CheckId("separability::witness on every recorded requirement".into()),
            }),
            "every recorded requirement is met and witnessed".to_string(),
        )
    }
}

fn terminalize_obstructed(certificate: &Certificate) -> (Terminal, Option<Certificate>, String) {
    if matches!(certificate, Certificate::Exhaustion { .. }) {
        (
            Terminal::Refused,
            Some(certificate.clone()),
            "an obstruction is recorded with its exhaustion certificate and nothing else remains".to_string(),
        )
    } else {
        (Terminal::Unresolved, None, "refusal requires an exhaustion declaration".into())
    }
}

impl Terminalizer for DeclaredTerminalizer {
    fn terminalize(&self, verdict: &RunVerdict, scope: &Scope) -> Terminated {
        let (terminal, certificate, reason) = match verdict {
            RunVerdict::InvalidInput { reason } => (Terminal::Unresolved, None, reason.clone()),
            RunVerdict::Quiescent { witnesses } => terminalize_quiescent(witnesses),
            RunVerdict::NothingAsked => (Terminal::Unresolved, None, "no separation requirement was recorded".to_string()),
            RunVerdict::Obstructed { certificate } => terminalize_obstructed(certificate),
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

// Origin: engine/crates_rs/core_ooutwire_primitives/src/terminal.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:terminal:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord43a75660 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord43a75660` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError43a75660 {
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
impl BoundaryError43a75660 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError43a75660 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError43a75660 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord43a75660 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError43a75660> {
        if capacity_bound == 0 {
            return Err(BoundaryError43a75660::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError43a75660::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError43a75660::ExceedsCapacity {
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

#[cfg(test)]
mod l4_boundary_tests_43a75660 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord43a75660::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord43a75660::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord43a75660::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord43a75660::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord43a75660::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError43a75660::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError43a75660::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
