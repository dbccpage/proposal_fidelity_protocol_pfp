//! § 5: Observer Quotient $Q^1_{\mathcal{O}}$
//!
//! The observer-visible quotient is
//! $Q^1_{\mathcal{O}} = Q^1 / \sim_{\mathcal{O}}$
//! where $\sim_{\mathcal{O}}$ is the observer-induced equivalence relation.

use crate::observer::VerifiedObserver;
use core_kernel::evidence::{
    CarrierManifestHash, EquivalenceRelationHash, ObserverMapHash, ObserverRef, QuotientSpaceHash,
    ReplayHash,
};
use serde::{Deserialize, Serialize};

#[derive(Debug, thiserror::Error, PartialEq, Eq)]
pub enum ObserverQuotientError {
    #[error("observer reference cannot be empty")]
    EmptyObserverRef,
    #[error("visible dimension {0} exceeds source dimension {1}")]
    VisibleDimExceedsSource(usize, usize),
    #[error("observer map hash cannot be zero")]
    ZeroObserverMapHash,
    #[error("equivalence relation hash cannot be zero")]
    ZeroEquivalenceRelationHash,
    #[error("carrier hash does not match source quotient carrier")]
    CarrierMismatch,
    #[error("source quotient hash cannot be zero")]
    ZeroSourceQuotientHash,
    #[error("carrier hash cannot be zero")]
    ZeroCarrierHash,
    #[error("replay hash cannot be zero")]
    ZeroReplayHash,
}

/// The observer-visible quotient space.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ObserverQuotient {
    pub observer_ref: ObserverRef,
    pub observer_map_hash: ObserverMapHash,
    pub source_quotient_hash: QuotientSpaceHash,
    pub visible_dim: usize,
    pub equivalence_relation_hash: EquivalenceRelationHash,
    pub carrier_hash: CarrierManifestHash,
    pub replay_hash: ReplayHash,
}

impl ObserverQuotient {
    #[allow(clippy::too_many_arguments)] // every argument is a distinct typed witness; bundling would blur them
    pub fn new(
        observer_ref: ObserverRef,
        observer_map_hash: ObserverMapHash,
        source_quotient_hash: QuotientSpaceHash,
        source_dim: usize,
        visible_dim: usize,
        equivalence_relation_hash: EquivalenceRelationHash,
        carrier_hash: CarrierManifestHash,
        source_carrier_hash: CarrierManifestHash,
        replay_hash: ReplayHash,
    ) -> Result<Self, ObserverQuotientError> {
        if observer_ref.is_empty() {
            return Err(ObserverQuotientError::EmptyObserverRef);
        }
        if visible_dim > source_dim {
            return Err(ObserverQuotientError::VisibleDimExceedsSource(
                visible_dim,
                source_dim,
            ));
        }
        if observer_map_hash.is_zero() {
            return Err(ObserverQuotientError::ZeroObserverMapHash);
        }
        if equivalence_relation_hash.is_zero() {
            return Err(ObserverQuotientError::ZeroEquivalenceRelationHash);
        }
        if source_quotient_hash.is_zero() {
            return Err(ObserverQuotientError::ZeroSourceQuotientHash);
        }
        if carrier_hash.is_zero() {
            return Err(ObserverQuotientError::ZeroCarrierHash);
        }
        if replay_hash.is_zero() {
            return Err(ObserverQuotientError::ZeroReplayHash);
        }
        if carrier_hash.0 .0 != source_carrier_hash.0 .0 {
            return Err(ObserverQuotientError::CarrierMismatch);
        }

        Ok(Self {
            observer_ref,
            observer_map_hash,
            source_quotient_hash,
            visible_dim,
            equivalence_relation_hash,
            carrier_hash,
            replay_hash,
        })
    }

    #[allow(clippy::too_many_arguments)] // every argument is a distinct typed witness; bundling would blur them
    pub fn try_new_with_observer(
        observer: &VerifiedObserver,
        source_quotient_hash: QuotientSpaceHash,
        source_dim: usize,
        visible_dim: usize,
        equivalence_relation_hash: EquivalenceRelationHash,
        carrier_hash: CarrierManifestHash,
        source_carrier_hash: CarrierManifestHash,
        replay_hash: ReplayHash,
    ) -> Result<Self, ObserverQuotientError> {
        let observer_ref = ObserverRef(observer.observer().id.to_string());
        let observer_map_hash =
            ObserverMapHash(observer.witness().idempotent_replay_hash.0.clone());
        Self::new(
            observer_ref,
            observer_map_hash,
            source_quotient_hash,
            source_dim,
            visible_dim,
            equivalence_relation_hash,
            carrier_hash,
            source_carrier_hash,
            replay_hash,
        )
    }
}

// Origin: engine/crates_rs/core_types/src/observer_quotient.rs
// Claim: urn:core:crates_rs:core-types:observer-quotient:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::observer::{Observer, ObserverKind, ObserverLawWitness};
    use core_kernel::evidence::Hash256;

    fn get_valid_inputs() -> (
        ObserverRef,
        ObserverMapHash,
        QuotientSpaceHash,
        usize,
        usize,
        EquivalenceRelationHash,
        CarrierManifestHash,
        CarrierManifestHash,
        ReplayHash,
    ) {
        (
            ObserverRef("test".into()),
            ObserverMapHash(Hash256([1; 32])),
            QuotientSpaceHash(Hash256([1; 32])),
            10, // source_dim
            5,  // visible_dim
            EquivalenceRelationHash(Hash256([1; 32])),
            CarrierManifestHash(Hash256([1; 32])),
            CarrierManifestHash(Hash256([1; 32])),
            ReplayHash(Hash256([1; 32])),
        )
    }

    #[test]
    fn test_observer_quotient_requires_observer_map_hash() {
        let (or, _, sqh, sd, vd, erh, ch, sch, rh) = get_valid_inputs();
        let omh = ObserverMapHash(Hash256([0; 32])); // Zero hash
        let res = ObserverQuotient::new(or, omh, sqh, sd, vd, erh, ch, sch, rh);
        assert!(matches!(
            res,
            Err(ObserverQuotientError::ZeroObserverMapHash)
        ));
    }

    #[test]
    fn test_observer_quotient_visible_dim_cannot_exceed_source_dim() {
        let (or, omh, sqh, _sd, _vd, erh, ch, sch, rh) = get_valid_inputs();
        let res = ObserverQuotient::new(or, omh, sqh, 5, 10, erh, ch, sch, rh);
        assert!(matches!(
            res,
            Err(ObserverQuotientError::VisibleDimExceedsSource(10, 5))
        ));
    }

    #[test]
    fn test_observer_quotient_requires_equivalence_relation_hash() {
        let (or, omh, sqh, sd, vd, _, ch, sch, rh) = get_valid_inputs();
        let erh = EquivalenceRelationHash(Hash256([0; 32])); // Zero hash
        let res = ObserverQuotient::new(or, omh, sqh, sd, vd, erh, ch, sch, rh);
        assert!(matches!(
            res,
            Err(ObserverQuotientError::ZeroEquivalenceRelationHash)
        ));
    }

    #[test]
    fn test_observer_quotient_carrier_matches_source_quotient() {
        let (or, omh, sqh, sd, vd, erh, ch, _, rh) = get_valid_inputs();
        let sch = CarrierManifestHash(Hash256([2; 32])); // Mismatch
        let res = ObserverQuotient::new(or, omh, sqh, sd, vd, erh, ch, sch, rh);
        assert!(matches!(res, Err(ObserverQuotientError::CarrierMismatch)));
    }

    #[test]
    fn test_observer_quotient_rejects_empty_observer_ref() {
        let (_, omh, sqh, sd, vd, erh, ch, sch, rh) = get_valid_inputs();
        let or = ObserverRef(String::new());
        let res = ObserverQuotient::new(or, omh, sqh, sd, vd, erh, ch, sch, rh);
        assert!(matches!(res, Err(ObserverQuotientError::EmptyObserverRef)));
    }

    #[test]
    fn test_observer_quotient_requires_source_quotient_hash() {
        let (or, omh, _, sd, vd, erh, ch, sch, rh) = get_valid_inputs();
        let sqh = QuotientSpaceHash(Hash256([0; 32]));
        let res = ObserverQuotient::new(or, omh, sqh, sd, vd, erh, ch, sch, rh);
        assert!(matches!(
            res,
            Err(ObserverQuotientError::ZeroSourceQuotientHash)
        ));
    }

    #[test]
    fn test_observer_quotient_requires_carrier_hash() {
        let (or, omh, sqh, sd, vd, erh, _, sch, rh) = get_valid_inputs();
        let ch = CarrierManifestHash(Hash256([0; 32]));
        let res = ObserverQuotient::new(or, omh, sqh, sd, vd, erh, ch, sch, rh);
        assert!(matches!(res, Err(ObserverQuotientError::ZeroCarrierHash)));
    }

    #[test]
    fn test_observer_quotient_requires_replay_hash() {
        let (or, omh, sqh, sd, vd, erh, ch, sch, _) = get_valid_inputs();
        let rh = ReplayHash(Hash256([0; 32]));
        let res = ObserverQuotient::new(or, omh, sqh, sd, vd, erh, ch, sch, rh);
        assert!(matches!(res, Err(ObserverQuotientError::ZeroReplayHash)));
    }

    fn verified_observer() -> VerifiedObserver {
        let observer = Observer {
            id: core_kernel::ObserverId::parse("obs.projection.001").unwrap(),
            kind: ObserverKind::Projection,
        };
        let witness = ObserverLawWitness {
            idempotent_replay_hash: ReplayHash(Hash256([1; 32])),
            repair_compat_replay_hash: ReplayHash(Hash256([2; 32])),
            lossy_phi_replay_hash: ReplayHash(Hash256([3; 32])),
        };
        VerifiedObserver::attest(observer, witness).expect("test witness is set and distinct")
    }

    #[test]
    fn test_observer_quotient_try_new_with_observer_rejects_zero_replay() {
        let res = ObserverQuotient::try_new_with_observer(
            &verified_observer(),
            QuotientSpaceHash(Hash256([1; 32])),
            10,
            5,
            EquivalenceRelationHash(Hash256([1; 32])),
            CarrierManifestHash(Hash256([1; 32])),
            CarrierManifestHash(Hash256([1; 32])),
            ReplayHash(Hash256([0; 32])),
        );
        assert!(matches!(res, Err(ObserverQuotientError::ZeroReplayHash)));
    }
}

/// A readout pair cannot be compared unless both name the same carrier states.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
#[error("{first} states in one readout, {second} in the other")]
pub struct ReadoutLengthMismatch {
    pub first: usize,
    pub second: usize,
}

/// Two states an observer identifies and another readout distinguishes.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct HiddenSeparation {
    pub first: usize,
    pub second: usize,
}

pub fn hidden_separation<O: PartialEq, H: PartialEq>(
    observer: &[O],
    hidden: &[H],
) -> Result<Option<HiddenSeparation>, ReadoutLengthMismatch> {
    if observer.len() != hidden.len() {
        return Err(ReadoutLengthMismatch {
            first: observer.len(),
            second: hidden.len(),
        });
    }
    for first in 0..observer.len() {
        for second in first + 1..observer.len() {
            if observer[first] == observer[second] && hidden[first] != hidden[second] {
                return Ok(Some(HiddenSeparation { first, second }));
            }
        }
    }
    Ok(None)
}

pub fn pair_observer<A: Clone, B: Clone>(
    first: &[A],
    second: &[B],
) -> Result<Vec<(A, B)>, ReadoutLengthMismatch> {
    if first.len() != second.len() {
        return Err(ReadoutLengthMismatch {
            first: first.len(),
            second: second.len(),
        });
    }
    Ok(first.iter().cloned().zip(second.iter().cloned()).collect())
}

#[cfg(test)]
mod finite_readout_tests {
    use super::*;
    #[test]
    fn hidden_readouts_and_product_observers_replay_their_separations() {
        let a = [0, 0, 1];
        let b = [0, 1, 1];
        let hidden = [2, 3, 4];
        assert_eq!(
            hidden_separation(&a, &hidden).unwrap(),
            Some(HiddenSeparation {
                first: 0,
                second: 1
            })
        );
        assert_eq!(
            hidden_separation(&pair_observer(&a, &b).unwrap(), &hidden).unwrap(),
            None
        );
        assert_eq!(hidden_separation(&a, &a).unwrap(), None);
        assert!(hidden_separation(&a, &hidden[..2]).is_err());
        assert!(pair_observer(&a, &b[..2]).is_err());
    }
}
