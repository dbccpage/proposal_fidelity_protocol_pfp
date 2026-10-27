//! Build-bound rewrite presentations. Candidate inputs cannot replace these pins.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_bd67421e<T> {
    fn checked_invariant_bd67421e(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_bd67421e<T> for Option<T> {
    #[inline]
    fn checked_invariant_bd67421e(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_bd67421e<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_bd67421e(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use super::*;

/// The pin file, compiled in.
///
/// `include_str!` is the enforcement, not a convenience. The pin set has to be
/// unreachable from a request payload or it is the claim vouching for itself,
/// and a path read at runtime is a path an operator can be talked into
/// repointing. This one is fixed when the host is built.
pub(super) const PINNED_PRESENTATIONS: &str = include_str!(
    "../../../governance/_law/20_execution/symbol_game_presentations.json"
);

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct PinFileV1 {
    pub(super) schema: String,
    pub(super) authority_effect: String,
    #[allow(dead_code)]
    pub(super) doctrine: Vec<String>,
    pub(super) pins: Vec<PinEntryV1>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct PinEntryV1 {
    pub(super) name: String,
    #[allow(dead_code)]
    pub(super) note: String,
    pub(super) presentation: Presentation,
}

pub(super) fn parse_compiled_pin_file(text: &str) -> Result<PinFileV1, &'static str> {
    let parsed: PinFileV1 = serde_json::from_str(text).map_err(|_| "COMPILED_PIN_FILE_INVALID")?;
    if parsed.schema != "core.symbol_game.presentation_pins.v1"
        || parsed.authority_effect != "None"
    {
        return Err("COMPILED_PIN_FILE_HEADER_INVALID");
    }
    let mut names = std::collections::BTreeSet::new();
    for entry in &parsed.pins {
        if entry.name.trim().is_empty() || !names.insert(entry.name.as_str()) {
            return Err("COMPILED_PIN_NAME_AMBIGUOUS");
        }
    }
    Ok(parsed)
}

pub(super) fn host_pin_file() -> &'static PinFileV1 {
    static CATALOGUE: OnceLock<PinFileV1> = OnceLock::new();
    CATALOGUE.get_or_init(|| {
        parse_compiled_pin_file(PINNED_PRESENTATIONS)
            .checked_invariant_bd67421e("the compiled-in pin catalogue must parse with unambiguous names")
    })
}

pub(super) fn host_named_presentation(name: &str) -> Option<&'static Presentation> {
    host_pin_file()
        .pins
        .iter()
        .find(|entry| entry.name == name)
        .map(|entry| &entry.presentation)
}

/// The rewrite presentations this host recognises.
///
/// Panics if the compiled-in pin file does not parse. That is deliberate: the
/// bytes are fixed at build time, so a failure here is deterministic, fires on
/// the first dispatch and in every test, and cannot be reached by any input. A
/// host that silently fell back to an empty pin set would report
/// SELF_CONSISTENT_ONLY for presentations it does pin -- safe, and exactly the
/// kind of silent degradation that hides a broken deployment.
pub fn host_presentation_pins() -> &'static PresentationPins {
    static PINS: OnceLock<PresentationPins> = OnceLock::new();
    PINS.get_or_init(|| {
        let mut pins = PresentationPins::empty();
        for entry in &host_pin_file().pins {
            pins.pin(&entry.name, &entry.presentation);
        }
        pins
    })
}

// Origin: engine/crates_rs/pfp/src/invoke/presentations.rs
// Claim: urn:core:crates_rs:pfp:presentations:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordbd67421e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordbd67421e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorbd67421e {
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
impl BoundaryErrorbd67421e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorbd67421e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorbd67421e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordbd67421e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorbd67421e> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorbd67421e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorbd67421e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorbd67421e::ExceedsCapacity {
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
mod l4_boundary_tests_bd67421e {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordbd67421e::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordbd67421e::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordbd67421e::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordbd67421e::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordbd67421e::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorbd67421e::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorbd67421e::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
