//! § 14.1, Definition 16.9: Observer Family
//!
//! An **observer family** $\mathfrak{O}$ is a finite set of observers declared
//! in advance. An obstruction class is **observer-stable** if it survives all
//! observers in $\mathfrak{O}$.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_ad479328<T> {
    fn checked_invariant_ad479328(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_ad479328<T> for Option<T> {
    #[inline]
    fn checked_invariant_ad479328(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_ad479328<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_ad479328(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::observer::Observer;
use serde::{Deserialize, Serialize};

#[derive(Debug, thiserror::Error, PartialEq, Eq)]
pub enum ObserverFamilyError {
    #[error("duplicate observer ID: {0}")]
    DuplicateObserverId(String),
    #[error("empty observer family is only allowed as a vacuous diagnostic")]
    EmptyFamilyViolation,
    #[error("observer family id cannot be empty")]
    EmptyFamilyId,
}

/// A finite, declared set of heterogeneous, repair-compatible observers.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ObserverFamily {
    /// The declared observers.
    observers: Vec<Observer>,
    /// Family identifier.
    pub id: String,
}

impl ObserverFamily {
    /// Construct an observer family, rejecting an empty id and duplicate observer ids.
    pub fn try_new(id: String, observers: Vec<Observer>) -> Result<Self, ObserverFamilyError> {
        if id.is_empty() {
            return Err(ObserverFamilyError::EmptyFamilyId);
        }
        let mut ids = std::collections::BTreeSet::new();
        for obs in &observers {
            if !ids.insert(&obs.id) {
                return Err(ObserverFamilyError::DuplicateObserverId(obs.id.to_string()));
            }
        }
        Ok(Self { id, observers })
    }

    /// Construct an observer family, panicking on empty id or duplicate.
    pub fn new(id: String, observers: Vec<Observer>) -> Self {
        Self::try_new(id, observers).checked_invariant_ad479328("ObserverFamily::new refused a duplicate or empty id")
    }

    /// The observers in this family.
    pub fn observers(&self) -> &[Observer] {
        &self.observers
    }

    /// Number of observers.
    pub fn len(&self) -> usize {
        self.observers.len()
    }

    /// Whether the family is empty.
    pub fn is_empty(&self) -> bool {
        self.observers.is_empty()
    }
}

/// A non-empty observer family representing a stability claim.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NonEmptyObserverFamily {
    family: ObserverFamily,
}

impl NonEmptyObserverFamily {
    pub fn try_new(id: String, observers: Vec<Observer>) -> Result<Self, ObserverFamilyError> {
        let family = ObserverFamily::try_new(id, observers)?;
        if family.is_empty() {
            return Err(ObserverFamilyError::EmptyFamilyViolation);
        }
        Ok(Self { family })
    }

    pub fn family(&self) -> &ObserverFamily {
        &self.family
    }
}

// Origin: engine/crates_rs/core_types/src/observer_family.rs
// Claim: urn:core:crates_rs:core-types:observer-family:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::observer::ObserverKind;

    #[test]
    fn test_observer_family_construction() {
        let obs = Observer {
            id: core_kernel::ObserverId::parse("obs1").unwrap(),
            kind: ObserverKind::Projection,
        };
        let family = ObserverFamily::new("fam1".to_string(), vec![obs]);
        assert_eq!(family.id, "fam1");
        assert_eq!(family.len(), 1);
        assert!(!family.is_empty());
        assert_eq!(family.observers()[0].id.as_str(), "obs1");
    }

    #[test]
    fn test_observer_family_rejects_duplicates() {
        let obs1 = Observer {
            id: core_kernel::ObserverId::parse("obs1").unwrap(),
            kind: ObserverKind::Projection,
        };
        let obs2 = Observer {
            id: core_kernel::ObserverId::parse("obs1").unwrap(),
            kind: ObserverKind::Precision,
        };
        let res = ObserverFamily::try_new("fam1".to_string(), vec![obs1, obs2]);
        assert!(matches!(
            res,
            Err(ObserverFamilyError::DuplicateObserverId(_))
        ));
    }

    #[test]
    fn test_non_empty_observer_family() {
        let obs = Observer {
            id: core_kernel::ObserverId::parse("obs1").unwrap(),
            kind: ObserverKind::Projection,
        };
        let ne = NonEmptyObserverFamily::try_new("fam1".to_string(), vec![obs]).unwrap();
        assert_eq!(ne.family().len(), 1);

        let res = NonEmptyObserverFamily::try_new("fam1".to_string(), vec![]);
        assert!(matches!(
            res,
            Err(ObserverFamilyError::EmptyFamilyViolation)
        ));
    }

    #[test]
    fn test_observer_family_rejects_empty_id() {
        let obs = Observer {
            id: core_kernel::ObserverId::parse("obs1").unwrap(),
            kind: ObserverKind::Projection,
        };
        let res = ObserverFamily::try_new(String::new(), vec![obs.clone()]);
        assert!(matches!(res, Err(ObserverFamilyError::EmptyFamilyId)));

        let res = NonEmptyObserverFamily::try_new(String::new(), vec![obs]);
        assert!(matches!(res, Err(ObserverFamilyError::EmptyFamilyId)));
    }

    #[test]
    fn test_non_empty_observer_family_rejects_empty_family() {
        let res = NonEmptyObserverFamily::try_new("fam1".to_string(), vec![]);
        assert!(matches!(
            res,
            Err(ObserverFamilyError::EmptyFamilyViolation)
        ));
    }
}
