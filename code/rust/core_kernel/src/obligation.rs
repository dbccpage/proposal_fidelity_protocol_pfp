//! Laws: `urn:core:rust:core_kernel:obligation:v1.0.0`.

use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use thiserror::Error;

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(try_from = "String", into = "String")]
pub struct ObligationId(String);

#[derive(Debug, Error, PartialEq, Eq)]
#[error("not a canonical obligation id ({reason}): {value:?}")]
pub struct ObligationIdError {
    pub value: String,
    pub reason: &'static str,
}

impl ObligationId {
    pub fn parse(value: &str) -> Result<Self, ObligationIdError> {
        let fail = |reason| ObligationIdError {
            value: value.to_owned(),
            reason,
        };
        let mut chars = value.chars();
        let first = chars.next().ok_or_else(|| fail("empty"))?;
        if !first.is_ascii_alphanumeric() {
            return Err(fail("must start with an ascii alphanumeric"));
        }
        if !chars.all(|c| c.is_ascii_alphanumeric() || matches!(c, '.' | '_' | '-' | ':')) {
            return Err(fail("may contain only ascii alphanumerics and . _ - :"));
        }
        Ok(Self(value.to_owned()))
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl TryFrom<String> for ObligationId {
    type Error = ObligationIdError;
    fn try_from(value: String) -> Result<Self, Self::Error> {
        Self::parse(&value)
    }
}

impl From<ObligationId> for String {
    fn from(id: ObligationId) -> Self {
        id.0
    }
}

impl std::fmt::Display for ObligationId {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(&self.0)
    }
}

/// An element of the free commutative monoid on obligation ids: a multiset,
/// carried as ordered counts. A zero count is not an element; the wire refuses
/// one instead of storing a multiset for which `is_empty` is false and
/// `total` is zero.
#[derive(Debug, Clone, PartialEq, Eq, Default, Serialize)]
#[serde(transparent)]
pub struct Obligations {
    counts: BTreeMap<ObligationId, u64>,
}

impl<'de> Deserialize<'de> for Obligations {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let counts = BTreeMap::<ObligationId, u64>::deserialize(deserializer)?;
        if counts.values().any(|count| *count == 0) {
            return Err(serde::de::Error::custom(
                "a zero obligation count is not a canonical multiset entry",
            ));
        }
        Ok(Self { counts })
    }
}

#[derive(Debug, Error, PartialEq, Eq)]
pub enum ObligationError {
    #[error("cannot discharge {id}: it was never generated")]
    NeverGenerated { id: String },

    #[error("cannot discharge {id} {requested} time(s): only {outstanding} outstanding")]
    OverDischarge {
        id: String,
        requested: u64,
        outstanding: u64,
    },

    #[error("obligation count for {id} would overflow")]
    CountOverflow { id: String },
}

impl Obligations {
    pub fn empty() -> Self {
        Self::default()
    }

    pub fn single(id: ObligationId) -> Self {
        Self::of(id, 1)
    }

    pub fn of(id: ObligationId, count: u64) -> Self {
        let mut counts = BTreeMap::new();
        if count > 0 {
            counts.insert(id, count);
        }
        Self { counts }
    }

    /// The monoid operation. Commutative and associative, with `empty` as unit.
    pub fn combine(&self, other: &Self) -> Result<Self, ObligationError> {
        let mut counts = self.counts.clone();
        for (id, n) in &other.counts {
            let slot = counts.entry(id.clone()).or_insert(0);
            *slot = slot
                .checked_add(*n)
                .ok_or_else(|| ObligationError::CountOverflow { id: id.to_string() })?;
        }
        Ok(Self { counts })
    }

    pub fn count(&self, id: &ObligationId) -> u64 {
        self.counts.get(id).copied().unwrap_or(0)
    }

    pub fn is_empty(&self) -> bool {
        self.counts.is_empty()
    }

    pub fn distinct(&self) -> usize {
        self.counts.len()
    }

    /// `None` when the sum exceeds `u64::MAX`.
    ///
    /// Saturating here would hand back `u64::MAX` — a plausible number that is
    /// not the total — for the same reason `approximate` refuses to return NAN:
    /// a lost value that still looks like a value is worse than no value.
    pub fn total(&self) -> Option<u64> {
        self.counts
            .values()
            .copied()
            .try_fold(0u64, |acc, n| acc.checked_add(n))
    }

    pub fn ids(&self) -> impl Iterator<Item = &ObligationId> {
        self.counts.keys()
    }
}

/// Generated and discharged obligations, and the difference between them.
///
/// Fields are private because the ledger's whole content is the invariant that
/// `discharged` never exceeds `generated`. A settable pair could record a
/// transition that discharged an obligation nothing raised.
#[derive(Debug, Clone, PartialEq, Eq, Default, Serialize, Deserialize)]
#[serde(try_from = "LedgerWire", into = "LedgerWire")]
pub struct ObligationLedger {
    generated: Obligations,
    discharged: Obligations,
}

impl ObligationLedger {
    pub fn new(generated: Obligations) -> Self {
        Self {
            generated,
            discharged: Obligations::empty(),
        }
    }

    pub fn generate(&mut self, id: ObligationId, count: u64) -> Result<(), ObligationError> {
        self.generated = self.generated.combine(&Obligations::of(id, count))?;
        Ok(())
    }

    /// Discharge `count` instances of `id`.
    ///
    /// Refuses when nothing outstanding matches. This is the ledger's reason to
    /// exist: an obligation that was never generated cannot be discharged, and a
    /// transition claiming otherwise is claiming to have settled a debt no one
    /// was owed.
    pub fn discharge(&mut self, id: &ObligationId, count: u64) -> Result<(), ObligationError> {
        if count == 0 {
            return Ok(());
        }
        let generated = self.generated.count(id);
        if generated == 0 {
            return Err(ObligationError::NeverGenerated { id: id.to_string() });
        }
        let outstanding = generated - self.discharged.count(id);
        if count > outstanding {
            return Err(ObligationError::OverDischarge {
                id: id.to_string(),
                requested: count,
                outstanding,
            });
        }
        self.discharged = self
            .discharged
            .combine(&Obligations::of(id.clone(), count))?;
        Ok(())
    }

    pub fn generated(&self) -> &Obligations {
        &self.generated
    }

    pub fn discharged(&self) -> &Obligations {
        &self.discharged
    }

    /// What is still owed: generated minus discharged, per id.
    pub fn outstanding(&self) -> Obligations {
        let mut counts = BTreeMap::new();
        for (id, generated) in &self.generated.counts {
            let remaining = generated - self.discharged.count(id);
            if remaining > 0 {
                counts.insert(id.clone(), remaining);
            }
        }
        Obligations { counts }
    }

    pub fn is_settled(&self) -> bool {
        self.outstanding().is_empty()
    }
}

#[derive(Serialize, Deserialize)]
struct LedgerWire {
    generated: Obligations,
    discharged: Obligations,
}

impl TryFrom<LedgerWire> for ObligationLedger {
    type Error = ObligationError;
    fn try_from(wire: LedgerWire) -> Result<Self, Self::Error> {
        for (id, discharged) in &wire.discharged.counts {
            let generated = wire.generated.count(id);
            if generated == 0 {
                return Err(ObligationError::NeverGenerated { id: id.to_string() });
            }
            if *discharged > generated {
                return Err(ObligationError::OverDischarge {
                    id: id.to_string(),
                    requested: *discharged,
                    outstanding: generated,
                });
            }
        }
        Ok(Self {
            generated: wire.generated,
            discharged: wire.discharged,
        })
    }
}

impl From<ObligationLedger> for LedgerWire {
    fn from(ledger: ObligationLedger) -> Self {
        Self {
            generated: ledger.generated,
            discharged: ledger.discharged,
        }
    }
}

// Origin: engine/crates_rs/core_kernel/src/obligation.rs
// Claim: urn:core:crates_rs:core-kernel:obligation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn id(text: &str) -> ObligationId {
        ObligationId::parse(text).expect("test ids are canonical")
    }

    fn obs(pairs: &[(&str, u64)]) -> Obligations {
        pairs.iter().fold(Obligations::empty(), |acc, (name, n)| {
            acc.combine(&Obligations::of(id(name), *n)).unwrap()
        })
    }

    #[test]
    fn an_obligation_id_must_be_canonical() {
        assert!(ObligationId::parse("PO-D6").is_ok());
        assert!(ObligationId::parse("core.replay.manifest").is_ok());
        for bad in ["", " leading", "has space", "has!bang"] {
            assert!(ObligationId::parse(bad).is_err(), "{bad:?} must be refused");
        }
    }

    #[test]
    fn combine_is_commutative() {
        let a = obs(&[("PO-A", 2), ("PO-B", 1)]);
        let b = obs(&[("PO-B", 3), ("PO-C", 1)]);
        assert_eq!(a.combine(&b).unwrap(), b.combine(&a).unwrap());
    }

    #[test]
    fn combine_is_associative() {
        let (a, b, c) = (obs(&[("x", 1)]), obs(&[("y", 2)]), obs(&[("x", 3)]));
        let left = a.combine(&b).unwrap().combine(&c).unwrap();
        let right = a.combine(&b.combine(&c).unwrap()).unwrap();
        assert_eq!(left, right);
    }

    #[test]
    fn empty_is_the_identity() {
        let a = obs(&[("PO-A", 2)]);
        assert_eq!(a.combine(&Obligations::empty()).unwrap(), a);
        assert_eq!(Obligations::empty().combine(&a).unwrap(), a);
    }

    #[test]
    fn counts_add_rather_than_replace() {
        let a = obs(&[("PO-A", 2)]);
        let combined = a.combine(&obs(&[("PO-A", 3)])).unwrap();
        assert_eq!(combined.count(&id("PO-A")), 5);
        assert_eq!(combined.distinct(), 1);
    }

    #[test]
    fn a_zero_count_contributes_nothing() {
        assert!(Obligations::of(id("PO-A"), 0).is_empty());
    }

    #[test]
    fn a_zero_count_on_the_wire_is_refused() {
        // `of` drops a zero. Accepting one on the wire made `is_empty` false
        // for a multiset whose total is still zero.
        assert!(serde_json::from_str::<Obligations>(r#"{"PO-A":0}"#).is_err());
        assert!(serde_json::from_str::<ObligationLedger>(
            r#"{"generated":{"PO-A":0},"discharged":{}}"#
        )
        .is_err());
        assert!(serde_json::from_str::<ObligationLedger>(
            r#"{"generated":{"PO-A":1},"discharged":{"PO-A":0}}"#
        )
        .is_err());
    }

    #[test]
    fn combining_past_the_count_ceiling_is_refused_not_wrapped() {
        // The whole-count law says overflow is refused, never wrapped. Nothing
        // exercised that path until now: checked_add guarded it and no test
        // reached the guard.
        let ceiling = Obligations::of(id("PO-A"), u64::MAX);
        assert_eq!(
            ceiling
                .combine(&Obligations::of(id("PO-A"), 1))
                .unwrap_err(),
            ObligationError::CountOverflow {
                id: "PO-A".to_owned()
            }
        );
        // A different id shares no counter, so it still combines.
        assert!(ceiling.combine(&Obligations::of(id("PO-B"), 1)).is_ok());
    }

    #[test]
    fn a_total_that_would_overflow_is_none_rather_than_saturated() {
        let mut counted = Obligations::of(id("PO-A"), u64::MAX);
        counted = counted.combine(&Obligations::of(id("PO-B"), 1)).unwrap();
        assert_eq!(counted.total(), None);
        assert_eq!(obs(&[("PO-A", 2), ("PO-B", 3)]).total(), Some(5));
    }

    #[test]
    fn an_obligation_never_generated_cannot_be_discharged() {
        let mut ledger = ObligationLedger::new(obs(&[("PO-A", 1)]));
        assert_eq!(
            ledger.discharge(&id("PO-B"), 1).unwrap_err(),
            ObligationError::NeverGenerated {
                id: "PO-B".to_owned()
            }
        );
    }

    #[test]
    fn discharging_more_than_outstanding_is_refused() {
        let mut ledger = ObligationLedger::new(obs(&[("PO-A", 2)]));
        ledger.discharge(&id("PO-A"), 1).unwrap();
        assert_eq!(
            ledger.discharge(&id("PO-A"), 2).unwrap_err(),
            ObligationError::OverDischarge {
                id: "PO-A".to_owned(),
                requested: 2,
                outstanding: 1,
            }
        );
    }

    #[test]
    fn outstanding_is_generated_minus_discharged() {
        let mut ledger = ObligationLedger::new(obs(&[("PO-A", 3), ("PO-B", 1)]));
        ledger.discharge(&id("PO-A"), 2).unwrap();
        let outstanding = ledger.outstanding();
        assert_eq!(outstanding.count(&id("PO-A")), 1);
        assert_eq!(outstanding.count(&id("PO-B")), 1);
        assert!(!ledger.is_settled());
    }

    #[test]
    fn a_ledger_is_settled_only_when_nothing_is_outstanding() {
        let mut ledger = ObligationLedger::new(obs(&[("PO-A", 2)]));
        assert!(!ledger.is_settled());
        ledger.discharge(&id("PO-A"), 2).unwrap();
        assert!(ledger.is_settled());
        assert!(ledger.outstanding().is_empty());
    }

    #[test]
    fn an_empty_ledger_is_settled() {
        assert!(ObligationLedger::new(Obligations::empty()).is_settled());
    }

    #[test]
    fn a_forged_ledger_is_refused_on_deserialize() {
        // discharged an obligation that was never generated
        let json = r#"{"generated":{"PO-A":1},"discharged":{"PO-B":1}}"#;
        assert!(serde_json::from_str::<ObligationLedger>(json).is_err());

        // discharged more than generated
        let json = r#"{"generated":{"PO-A":1},"discharged":{"PO-A":5}}"#;
        assert!(serde_json::from_str::<ObligationLedger>(json).is_err());
    }

    #[test]
    fn an_honest_ledger_round_trips() {
        let mut ledger = ObligationLedger::new(obs(&[("PO-A", 2), ("PO-B", 1)]));
        ledger.discharge(&id("PO-A"), 1).unwrap();
        let json = serde_json::to_string(&ledger).unwrap();
        assert_eq!(
            serde_json::from_str::<ObligationLedger>(&json).unwrap(),
            ledger
        );
    }

    #[test]
    fn the_wire_form_is_ordered_so_equal_multisets_serialize_alike() {
        // Insertion order differs; the multiset does not.
        let a = obs(&[("PO-B", 1), ("PO-A", 2)]);
        let b = obs(&[("PO-A", 2), ("PO-B", 1)]);
        assert_eq!(a, b);
        assert_eq!(
            serde_json::to_string(&a).unwrap(),
            serde_json::to_string(&b).unwrap()
        );
    }

    #[test]
    fn discharging_zero_is_a_no_op_even_for_an_unknown_id() {
        let mut ledger = ObligationLedger::new(Obligations::empty());
        assert!(ledger.discharge(&id("PO-UNKNOWN"), 0).is_ok());
        assert!(ledger.is_settled());
    }
}
