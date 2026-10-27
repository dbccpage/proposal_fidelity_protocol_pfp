//! PRIME-ALGORITHM-001 — intake and inter-carrier transport soundness.
//!
//! Canonical source: `research/prime_algos/`
//! §1, which assigns Prime 001 to *"intake and inter-carrier transport
//! soundness, enforcing that translation into an `CorePacket` does not confer
//! validity and tracking all lost data in explicit loss ledgers
//! ($L_\text{adapter}$)."*
//!
//! An earlier cut of this crate used the name `prime_algorithm_1` for the continuation
//! predicate. That is Prime **002**; see [`crate::prime_algos::prime_algorithm_2`].
//!
//! # The one law
//!
//! **Translation does not confer validity.** A judgment that held on carrier A
//! arrives on carrier B as *proposed*, never as *admitted*. This is not a
//! stylistic preference: an adapter that upgrades status while moving carriers
//! is an authority-laundering device, and it is the cheapest one to build by
//! accident.
//!
//! [`TransportedPacket`] therefore has no constructor that yields an admitted
//! status, and [`TransportStatus`] has no variant meaning "valid here because it
//! was valid there".
//!
//! # Loss ledgers
//!
//! Every transport books what it dropped. A ledger is **sealed** on
//! construction and its entries cannot be edited afterwards, so a caller cannot
//! shrink a loss after the fact. An *empty* ledger is a positive claim that
//! nothing was lost — it is not the same as no ledger, and
//! [`LossLedger::is_empty`] is what Prime 002's skeleton-preservation law reads
//! to tell the two apart.
//!
//! `AuthorityEffect: None`.

use crate::prime_algos::prime_scope::{digest, ScopeBinding};
use core_kernel::evidence::Hash256;
use core_types::authority::AuthorityEffect;
use serde::Serialize;
use std::collections::BTreeMap;
use std::fmt;

const LEDGER_DOMAIN: &str = "oeprm.ledger.v1";

/// What an adapter dropped in translation, booked and sealed.
///
/// Entries are private and there is no mutator: a ledger cannot be shrunk after
/// the checks that read it.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct LossLedger {
    scope: ScopeBinding,
    entries: BTreeMap<String, usize>,
    /// False when the ledger was constructed from an inconsistent report.
    sound: bool,
}

impl LossLedger {
    /// A ledger asserting that nothing was lost.
    ///
    /// This is a *claim*, not an absence. Prime 002 distinguishes "nothing was
    /// lost" from "no ledger was produced".
    pub fn empty(scope: ScopeBinding) -> Self {
        Self {
            scope,
            entries: BTreeMap::new(),
            sound: true,
        }
    }

    /// Book losses. A zero-count entry is unsound: booking "we lost 0 faces" as
    /// an entry rather than omitting it hides the difference between a measured
    /// zero and an unmeasured field.
    pub fn booked(entries: Vec<(String, usize)>, scope: ScopeBinding) -> Self {
        let sound = entries.iter().all(|(k, n)| *n > 0 && !k.trim().is_empty());
        Self {
            scope,
            entries: entries.into_iter().collect(),
            sound,
        }
    }

    pub fn scope(&self) -> &ScopeBinding {
        &self.scope
    }

    pub fn is_sound(&self) -> bool {
        self.sound
    }

    /// True when the ledger books no losses.
    pub fn is_empty(&self) -> bool {
        self.entries.is_empty()
    }

    pub fn total_lost(&self) -> usize {
        self.entries.values().sum()
    }

    pub fn entries(&self) -> &BTreeMap<String, usize> {
        &self.entries
    }

    /// Canonical commitment, so a tape head can bind the ledger that was read.
    pub fn commit(&self) -> Hash256 {
        let mut parts: Vec<Vec<u8>> = Vec::new();
        parts.push(self.scope.commit().0.to_vec());
        for (k, n) in &self.entries {
            parts.push(k.as_bytes().to_vec());
            parts.push((*n as u64).to_le_bytes().to_vec());
        }
        parts.push(vec![u8::from(self.sound)]);
        let refs: Vec<&[u8]> = parts.iter().map(|p| p.as_slice()).collect();
        digest(LEDGER_DOMAIN, &refs)
    }
}

impl fmt::Display for LossLedger {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        if self.entries.is_empty() {
            return write!(f, "L_adapter: nothing lost (claimed)");
        }
        write!(
            f,
            "L_adapter: {} item(s), {} total [{}]",
            self.entries.len(),
            self.total_lost(),
            self.entries
                .iter()
                .map(|(k, n)| format!("{k}={n}"))
                .collect::<Vec<_>>()
                .join(", ")
        )
    }
}

/// Status of a packet after transport.
///
/// There is deliberately **no** `AdmittedBecauseItWasAdmittedThere`. Crossing a
/// carrier boundary cannot raise status.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TransportStatus {
    /// The only status transport can produce. Whatever the source status was,
    /// the packet arrives as a proposal for the target carrier's own checks.
    Proposed,
}

/// Why a transport was refused.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub enum TransportRefusal {
    /// The adapter reported losses inconsistently.
    UnsoundLedger { detail: String },
    /// Source and target carrier are the same; transport is not the operation
    /// wanted, and calling it transport would book a loss that did not occur.
    SameCarrier,
}

impl fmt::Display for TransportRefusal {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            TransportRefusal::UnsoundLedger { detail } => {
                write!(f, "transport refused: unsound loss ledger: {detail}")
            }
            TransportRefusal::SameCarrier => {
                write!(
                    f,
                    "transport refused: source and target carrier are identical"
                )
            }
        }
    }
}

impl std::error::Error for TransportRefusal {}

/// A packet that has crossed a carrier boundary.
///
/// Fields are private and there is exactly one constructor, [`transport`], so a
/// packet cannot be assembled with a status it did not earn.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TransportedPacket {
    from: Hash256,
    to: Hash256,
    payload: Hash256,
    ledger: LossLedger,
    status: TransportStatus,
}

impl TransportedPacket {
    pub fn from_carrier(&self) -> &Hash256 {
        &self.from
    }
    pub fn to_carrier(&self) -> &Hash256 {
        &self.to
    }
    pub fn payload(&self) -> &Hash256 {
        &self.payload
    }
    pub fn ledger(&self) -> &LossLedger {
        &self.ledger
    }
    /// Always [`TransportStatus::Proposed`]. Kept as an accessor rather than a
    /// constant so the type reads the same as the other evidence surfaces.
    pub fn status(&self) -> TransportStatus {
        self.status
    }
}

/// Move a packet between carriers, booking what was lost.
///
/// The result is always [`TransportStatus::Proposed`], whatever the source
/// status was. `source_was_admitted` is accepted **and deliberately ignored for
/// status purposes** — it exists so the signature makes the discarded
/// information visible at every call site rather than silently absent.
pub fn transport(
    from: Hash256,
    to: Hash256,
    payload: Hash256,
    ledger: LossLedger,
    _source_was_admitted: bool,
) -> Result<TransportedPacket, TransportRefusal> {
    if from == to {
        return Err(TransportRefusal::SameCarrier);
    }
    if ledger.scope().carrier() != &from {
        return Err(TransportRefusal::UnsoundLedger {
            detail: format!(
                "ledger bound to carrier {} does not match transport source {}",
                crate::prime_algos::prime_scope::short(ledger.scope().carrier()),
                crate::prime_algos::prime_scope::short(&from),
            ),
        });
    }
    if !ledger.is_sound() {
        return Err(TransportRefusal::UnsoundLedger {
            detail: ledger.to_string(),
        });
    }
    Ok(TransportedPacket {
        from,
        to,
        payload,
        ledger,
        status: TransportStatus::Proposed,
    })
}

/// Authority effect of this module.
pub const AUTHORITY_EFFECT: AuthorityEffect = AuthorityEffect::None;

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn h(n: u8) -> Hash256 {
        Hash256([n; 32])
    }

    fn test_scope(carrier: Hash256) -> ScopeBinding {
        ScopeBinding::with_carrier_and_d0(h(0), carrier, h(100), h(200), None, 0)
    }

    /// The one law of Prime 001, stated as a test: an admitted source packet
    /// arrives proposed.
    #[test]
    fn translation_does_not_confer_validity() {
        let p = transport(h(1), h(2), h(9), LossLedger::empty(test_scope(h(1))), true)
            .expect("a sound transport must succeed");
        assert_eq!(
            p.status(),
            TransportStatus::Proposed,
            "an admitted packet must arrive as a proposal"
        );
    }

    /// Anti-vacuity for the law above: the status is not constant
    /// because transport always fails. It succeeds, and still does not upgrade.
    #[test]
    fn transport_succeeds_for_both_source_statuses_and_upgrades_neither() {
        for was_admitted in [true, false] {
            let p = transport(
                h(1),
                h(2),
                h(9),
                LossLedger::empty(test_scope(h(1))),
                was_admitted,
            )
            .unwrap();
            assert_eq!(p.status(), TransportStatus::Proposed);
        }
    }

    #[test]
    fn an_unsound_ledger_refuses() {
        let bad = LossLedger::booked(vec![("dropped".into(), 0)], test_scope(h(1)));
        assert!(!bad.is_sound(), "a zero-count entry is unsound");
        let err = transport(h(1), h(2), h(9), bad, false).expect_err("must refuse");
        assert!(matches!(err, TransportRefusal::UnsoundLedger { .. }));
    }

    #[test]
    fn a_blank_loss_key_is_unsound() {
        assert!(!LossLedger::booked(vec![("   ".into(), 3)], test_scope(h(1))).is_sound());
    }

    #[test]
    fn transport_to_the_same_carrier_refuses() {
        let err =
            transport(h(1), h(1), h(9), LossLedger::empty(test_scope(h(1))), false).unwrap_err();
        assert_eq!(err, TransportRefusal::SameCarrier);
    }

    #[test]
    fn transport_with_mismatched_ledger_carrier_refuses() {
        let err = transport(
            h(1),
            h(2),
            h(9),
            LossLedger::empty(test_scope(h(99))),
            false,
        )
        .unwrap_err();
        assert!(matches!(err, TransportRefusal::UnsoundLedger { .. }));
    }

    /// An empty ledger is a *claim* that nothing was lost; the absence of a
    /// ledger is a different thing, and Prime 002 reads exactly this
    /// distinction.
    #[test]
    fn an_empty_ledger_is_a_claim_not_an_absence() {
        let l = LossLedger::empty(test_scope(h(1)));
        assert!(l.is_empty());
        assert!(l.is_sound());
        assert_eq!(l.total_lost(), 0);
    }

    #[test]
    fn a_booked_ledger_reports_its_total() {
        let l = LossLedger::booked(
            vec![("faces".into(), 2), ("orientations".into(), 5)],
            test_scope(h(1)),
        );
        assert!(l.is_sound());
        assert!(!l.is_empty());
        assert_eq!(l.total_lost(), 7);
    }

    /// The commitment must distinguish ledgers, or a tape head could not bind
    /// which ledger was read.
    #[test]
    fn distinct_ledgers_commit_distinctly() {
        let a = LossLedger::booked(vec![("faces".into(), 2)], test_scope(h(1)));
        let b = LossLedger::booked(vec![("faces".into(), 3)], test_scope(h(1)));
        let c = LossLedger::booked(vec![("edges".into(), 2)], test_scope(h(1)));
        assert_ne!(a.commit(), b.commit(), "count must be committed");
        assert_ne!(a.commit(), c.commit(), "key must be committed");
        assert_ne!(a.commit(), LossLedger::empty(test_scope(h(1))).commit());
        assert_eq!(
            a.commit(),
            LossLedger::booked(vec![("faces".into(), 2)], test_scope(h(1))).commit()
        );
    }

    /// Soundness is committed too: an unsound ledger must not share a
    /// commitment with a sound one.
    #[test]
    fn soundness_is_committed() {
        let sound = LossLedger::empty(test_scope(h(1)));
        let unsound = LossLedger::booked(vec![("x".into(), 0)], test_scope(h(1)));
        assert_ne!(sound.commit(), unsound.commit());
    }

    #[test]
    fn display_never_panics_on_hostile_keys() {
        let l = LossLedger::booked(vec![("\u{1F600}\u{00E9}".into(), 1)], test_scope(h(1)));
        assert!(!l.to_string().is_empty());
    }

    #[test]
    fn authority_effect_is_none() {
        assert_eq!(AUTHORITY_EFFECT, AuthorityEffect::None);
    }
}
