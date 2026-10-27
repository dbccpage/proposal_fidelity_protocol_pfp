use serde::{Deserialize, Serialize};
use thiserror::Error;

/// The identity every claim is indexed by. Grammar matches the canonical
/// identifier used by the digest envelope: a leading alphanumeric, then any of
/// `A-Za-z0-9._-:/@`.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(try_from = "String", into = "String")]
pub struct ObserverId(String);

#[derive(Debug, Error, PartialEq, Eq)]
#[error("not a canonical observer id ({reason}): {value:?}")]
pub struct ObserverIdError {
    pub value: String,
    pub reason: &'static str,
}

impl ObserverId {
    pub fn parse(value: &str) -> Result<Self, ObserverIdError> {
        let fail = |reason| ObserverIdError {
            value: value.to_owned(),
            reason,
        };
        let mut chars = value.chars();
        let first = chars.next().ok_or_else(|| fail("empty"))?;
        if !first.is_ascii_alphanumeric() {
            return Err(fail("must start with an ascii alphanumeric"));
        }
        if !chars
            .all(|c| c.is_ascii_alphanumeric() || matches!(c, '.' | '_' | '-' | ':' | '/' | '@'))
        {
            return Err(fail("may contain only ascii alphanumerics and . _ - : / @"));
        }
        Ok(Self(value.to_owned()))
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl TryFrom<String> for ObserverId {
    type Error = ObserverIdError;
    fn try_from(value: String) -> Result<Self, Self::Error> {
        Self::parse(&value)
    }
}

impl From<ObserverId> for String {
    fn from(id: ObserverId) -> Self {
        id.0
    }
}

impl std::fmt::Display for ObserverId {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(&self.0)
    }
}

/// A value bound to the observer that produced it.
///
/// Zero View-from-Nowhere is a law about what can be *said*, so it is enforced
/// by what can be *constructed*: `T` reaches a consumer only inside this
/// wrapper, and the wrapper cannot be built without an [`ObserverId`].
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Observed<T> {
    observer: ObserverId,
    value: T,
}

impl<T> Observed<T> {
    pub fn new(observer: ObserverId, value: T) -> Self {
        Self { observer, value }
    }

    pub fn observer(&self) -> &ObserverId {
        &self.observer
    }

    pub fn value(&self) -> &T {
        &self.value
    }

    pub fn into_value(self) -> T {
        self.value
    }

    pub fn map<U, F: FnOnce(T) -> U>(self, f: F) -> Observed<U> {
        Observed {
            observer: self.observer,
            value: f(self.value),
        }
    }
}

// Origin: engine/crates_rs/core_kernel/src/observer.rs
// Claim: urn:core:crates_rs:core-kernel:observer:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn the_grammar_matches_the_digest_envelopes_identifier() {
        for good in ["core.oewas.colour.v1", "a-b_c:d/e@f", "x", "0"] {
            assert!(ObserverId::parse(good).is_ok(), "{good} must parse");
        }
        for bad in [".leading", "-leading", "has space", "has!bang", "", "café"] {
            assert!(ObserverId::parse(bad).is_err(), "{bad} must be refused");
        }
    }

    #[test]
    fn deserialize_refuses_what_parse_refuses() {
        assert!(serde_json::from_str::<ObserverId>("\"has space\"").is_err());
        assert_eq!(
            serde_json::from_str::<ObserverId>("\"core.test.v1\"").unwrap(),
            ObserverId::parse("core.test.v1").unwrap()
        );
    }

    #[test]
    fn an_id_serializes_as_a_bare_string() {
        let id = ObserverId::parse("core.test.v1").unwrap();
        assert_eq!(serde_json::to_string(&id).unwrap(), "\"core.test.v1\"");
    }

    #[test]
    fn an_observed_value_carries_its_observer_through_a_round_trip() {
        let observed = Observed::new(ObserverId::parse("core.measurer.v1").unwrap(), 42_u32);
        let json = serde_json::to_string(&observed).unwrap();
        let back: Observed<u32> = serde_json::from_str(&json).unwrap();
        assert_eq!(back.observer().as_str(), "core.measurer.v1");
        assert_eq!(*back.value(), 42);
    }

    #[test]
    fn mapping_a_value_preserves_the_observer() {
        let observed = Observed::new(ObserverId::parse("core.measurer.v1").unwrap(), 2_u32);
        let mapped = observed.map(|v| v * 3);
        assert_eq!(mapped.observer().as_str(), "core.measurer.v1");
        assert_eq!(*mapped.value(), 6);
    }

    #[test]
    fn an_observation_cannot_be_deserialized_without_an_observer() {
        assert!(serde_json::from_str::<Observed<u32>>(r#"{"value":1}"#).is_err());
    }

    #[test]
    fn two_observers_reporting_the_same_value_remain_distinguishable() {
        let a = Observed::new(ObserverId::parse("a.v1").unwrap(), 1_u32);
        let b = Observed::new(ObserverId::parse("b.v1").unwrap(), 1_u32);
        assert_ne!(a, b);
    }
}
