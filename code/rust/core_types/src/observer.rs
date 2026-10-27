//! § 5, § 14, Definition 16.8: Observer
//!
//! An **observer** is a deterministic, idempotent map
//! $\mathcal{O}: Q^1 \to Q^1_{\mathcal{O}}$ satisfying:
//! 1. $\mathcal{O} \circ \mathcal{O} = \mathcal{O}$ (idempotent)
//! 2. $\mathcal{O}(q) = \mathcal{O}(q + b)$ for all $b \in B^1$ (repair-compatible)
//! 3. $\Phi_1(\mathcal{O}(q)) = \Phi_1(q)$ (projector purity)
//!
//! Executable projection checks preserve Phi1 and check idempotence on the
//! supplied carrier. Historical replay hashes remain metadata, not law proofs.
//!
//! Laws: `urn:core:rust:core_functional:observer:v1.1.0`.

use num_rational::BigRational;
use core_kernel::evidence::ReplayHash;
use core_kernel::ObserverId;
use serde::{Deserialize, Serialize};
use thiserror::Error;

/// Observer kind, matching § 14.1 and § 15.6.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum ObserverKind {
    /// Structure erasure (projection observer).
    Projection,
    /// Budget awareness ($\mathcal{O}(q) = \lfloor q / \epsilon \rfloor$).
    Precision,
    /// Sign/orientation eraser ($\mathcal{O}([x]) = [|x|]$).
    SignEraser,
    /// Forgets lift lineage and operator provenance.
    LineageForget,
    /// Budget-blind: erases explicit counters.
    BudgetBlind,
    /// Witness-blind: erases explicit $\varphi$ annotations.
    WitnessBlind,
    /// Custom observer with declared name.
    Custom(String),
}

/// One replay hash per observer law. The three laws are independent, so three
/// distinct replays are required to witness them.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ObserverLawWitness {
    pub idempotent_replay_hash: ReplayHash,
    pub repair_compat_replay_hash: ReplayHash,
    pub lossy_phi_replay_hash: ReplayHash,
}

#[derive(Debug, Error, PartialEq, Eq)]
pub enum ObserverAttestationError {
    #[error("the {law} replay hash is unset")]
    UnsetReplay { law: &'static str },

    #[error("the {left} and {right} laws present the same replay hash; one replay cannot witness two independent laws")]
    ReusedReplay {
        left: &'static str,
        right: &'static str,
    },
}

#[derive(Debug, Error, PartialEq, Eq)]
pub enum ObserverProjectionError {
    #[error("observer projection changes exact Phi1")]
    PhiChanged,
    #[error("observer projection is not idempotent on the supplied carrier")]
    NotIdempotent,
    #[error("observer projection differs on declared repair-equivalent carrier {index}")]
    RepairIncompatible { index: usize },
}

/// An observer as a typed, declared structure.
///
/// The actual map is not stored here — it is applied by the solver or
/// evaluator. This struct records the observer's identity and kind for
/// audit, hashing, and family membership.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Observer {
    /// Unique identifier for this observer.
    pub id: ObserverId,
    /// The kind of observer.
    pub kind: ObserverKind,
}

/// An observer carrying a replay witness for each of its three laws.
///
/// Fields are private and [`VerifiedObserver::attest`] is the only constructor,
/// so a consumer that demands this type — [`crate::observer_quotient`] does —
/// cannot be handed a bare `Observer` wearing the name.
///
/// What `attest` establishes is narrow and worth stating exactly: three
/// distinct, set replays were recorded. It does **not** re-run the observer map,
/// because the map is not stored here, so it does not establish that the three
/// laws hold. Whoever produced the replays vouches for that.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(try_from = "UntrustedVerifiedObserverWire")]
pub struct VerifiedObserver {
    observer: Observer,
    witness: ObserverLawWitness,
}

/// Inbound, untrusted representation of a verified observer.
///
/// Deserialization must populate this wire type first and then pass through
/// [`VerifiedObserver::attest`]. Deriving `Deserialize` directly over the
/// private fields would otherwise bypass the attestation gate.
#[derive(Debug, Clone, Serialize, Deserialize)]
struct UntrustedVerifiedObserverWire {
    observer: Observer,
    witness: ObserverLawWitness,
}

impl TryFrom<UntrustedVerifiedObserverWire> for VerifiedObserver {
    type Error = ObserverAttestationError;

    fn try_from(wire: UntrustedVerifiedObserverWire) -> Result<Self, Self::Error> {
        Self::attest(wire.observer, wire.witness)
    }
}

impl VerifiedObserver {
    /// Apply and check the map on this carrier and caller-declared repairs.
    ///
    /// This is finite execution evidence, not a theorem over unseen carriers.
    /// Replay hashes alone cannot authorize an unchecked carrier transformation.
    pub fn project_checked<Q: Eq>(
        &self,
        state: &Q,
        repair_equivalents: &[Q],
        project: impl Fn(&Q) -> Q,
        phi1: impl Fn(&Q) -> BigRational,
    ) -> Result<Q, ObserverProjectionError> {
        let projected = project(state);
        if phi1(&projected) != phi1(state) {
            return Err(ObserverProjectionError::PhiChanged);
        }
        if project(&projected) != projected {
            return Err(ObserverProjectionError::NotIdempotent);
        }
        for (index, repaired) in repair_equivalents.iter().enumerate() {
            if project(repaired) != projected {
                return Err(ObserverProjectionError::RepairIncompatible { index });
            }
        }
        Ok(projected)
    }

    pub fn attest(
        observer: Observer,
        witness: ObserverLawWitness,
    ) -> Result<Self, ObserverAttestationError> {
        let laws = [
            ("idempotent", &witness.idempotent_replay_hash),
            ("repair_compat", &witness.repair_compat_replay_hash),
            ("lossy_phi", &witness.lossy_phi_replay_hash),
        ];
        for (law, hash) in laws {
            if hash.is_zero() {
                return Err(ObserverAttestationError::UnsetReplay { law });
            }
        }
        for i in 0..laws.len() {
            for j in (i + 1)..laws.len() {
                if laws[i].1 == laws[j].1 {
                    return Err(ObserverAttestationError::ReusedReplay {
                        left: laws[i].0,
                        right: laws[j].0,
                    });
                }
            }
        }
        Ok(Self { observer, witness })
    }

    pub fn observer(&self) -> &Observer {
        &self.observer
    }

    pub fn witness(&self) -> &ObserverLawWitness {
        &self.witness
    }
}

// Origin: engine/crates_rs/core_types/src/observer.rs
// Claim: urn:core:crates_rs:core-types:observer:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use core_kernel::evidence::Hash256;

    fn id(text: &str) -> ObserverId {
        ObserverId::parse(text).expect("test ids are canonical")
    }

    fn hash(seed: u8) -> ReplayHash {
        ReplayHash(Hash256([seed; 32]))
    }

    fn observer() -> Observer {
        Observer {
            id: id("obs.projection.001"),
            kind: ObserverKind::Projection,
        }
    }

    fn witness() -> ObserverLawWitness {
        ObserverLawWitness {
            idempotent_replay_hash: hash(1),
            repair_compat_replay_hash: hash(2),
            lossy_phi_replay_hash: hash(3),
        }
    }

    #[test]
    fn an_observer_id_must_be_canonical() {
        assert!(ObserverId::parse("obs.projection.001").is_ok());
        // A bare String field would have accepted every one of these.
        for bad in ["", " leading", "has space", "has!bang"] {
            assert!(ObserverId::parse(bad).is_err(), "{bad:?} must be refused");
        }
    }

    #[test]
    fn three_distinct_replays_attest() {
        let verified = VerifiedObserver::attest(observer(), witness()).expect("must attest");
        assert_eq!(verified.observer().id, id("obs.projection.001"));
        assert_eq!(verified.witness().idempotent_replay_hash, hash(1));
    }

    #[test]
    fn projector_executes_exact_purity_idempotence_and_repair_checks() {
        let verified = VerifiedObserver::attest(observer(), witness()).unwrap();
        let state = (3_i64, 9_i64);
        let phi = |q: &(i64, i64)| BigRational::from_integer(q.0.into());
        assert_eq!(
            verified.project_checked(&state, &[(3, 7)], |q| (q.0, 0), phi),
            Ok((3, 0))
        );
        assert_eq!(
            verified.project_checked(&state, &[], |q| (q.0 - 1, 0), phi),
            Err(ObserverProjectionError::PhiChanged)
        );
        assert_eq!(
            verified.project_checked(&state, &[], |q| (q.0, q.1 + 1), phi),
            Err(ObserverProjectionError::NotIdempotent)
        );
        assert_eq!(
            verified.project_checked(&state, &[(4, 7)], |q| (q.0, 0), phi),
            Err(ObserverProjectionError::RepairIncompatible { index: 0 })
        );
    }

    #[test]
    fn an_unset_replay_is_refused_for_each_law() {
        for (law, mut w) in [
            ("idempotent", witness()),
            ("repair_compat", witness()),
            ("lossy_phi", witness()),
        ] {
            match law {
                "idempotent" => w.idempotent_replay_hash = ReplayHash(Hash256([0; 32])),
                "repair_compat" => w.repair_compat_replay_hash = ReplayHash(Hash256([0; 32])),
                _ => w.lossy_phi_replay_hash = ReplayHash(Hash256([0; 32])),
            }
            assert_eq!(
                VerifiedObserver::attest(observer(), w).unwrap_err(),
                ObserverAttestationError::UnsetReplay { law }
            );
        }
    }

    #[test]
    fn one_replay_cannot_witness_two_laws() {
        let mut w = witness();
        w.repair_compat_replay_hash = w.idempotent_replay_hash.clone();
        assert_eq!(
            VerifiedObserver::attest(observer(), w).unwrap_err(),
            ObserverAttestationError::ReusedReplay {
                left: "idempotent",
                right: "repair_compat",
            }
        );
    }

    #[test]
    fn repair_compat_and_lossy_phi_cannot_share_a_replay() {
        let mut w = witness();
        w.lossy_phi_replay_hash = w.repair_compat_replay_hash.clone();
        assert_eq!(
            VerifiedObserver::attest(observer(), w).unwrap_err(),
            ObserverAttestationError::ReusedReplay {
                left: "repair_compat",
                right: "lossy_phi",
            }
        );
    }

    #[test]
    fn all_three_laws_sharing_one_replay_is_refused() {
        let shared = hash(7);
        let w = ObserverLawWitness {
            idempotent_replay_hash: shared.clone(),
            repair_compat_replay_hash: shared.clone(),
            lossy_phi_replay_hash: shared,
        };
        assert!(VerifiedObserver::attest(observer(), w).is_err());
    }

    #[test]
    fn a_verified_observer_cannot_be_built_from_its_parts() {
        // The fields are private, so the direct construction route is attest().
        // The deserialization route is checked separately below.
        let verified = VerifiedObserver::attest(observer(), witness()).unwrap();
        assert_eq!(verified.observer().kind, ObserverKind::Projection);
    }

    #[test]
    fn an_unset_replay_cannot_deserialize_as_verified() {
        let mut invalid = witness();
        invalid.lossy_phi_replay_hash = ReplayHash(Hash256([0; 32]));
        let wire = UntrustedVerifiedObserverWire {
            observer: observer(),
            witness: invalid,
        };
        let json = serde_json::to_string(&wire).expect("wire serializes");

        serde_json::from_str::<UntrustedVerifiedObserverWire>(&json)
            .expect("payload is well-formed at the wire layer");
        assert!(serde_json::from_str::<VerifiedObserver>(&json).is_err());
    }

    #[test]
    fn a_reused_replay_cannot_deserialize_as_verified() {
        let mut invalid = witness();
        invalid.lossy_phi_replay_hash = invalid.idempotent_replay_hash.clone();
        let wire = UntrustedVerifiedObserverWire {
            observer: observer(),
            witness: invalid,
        };
        let json = serde_json::to_string(&wire).expect("wire serializes");

        serde_json::from_str::<UntrustedVerifiedObserverWire>(&json)
            .expect("payload is well-formed at the wire layer");
        assert!(serde_json::from_str::<VerifiedObserver>(&json).is_err());
    }

    #[test]
    fn a_verified_observer_survives_a_serde_round_trip() {
        let verified = VerifiedObserver::attest(observer(), witness()).unwrap();
        let json = serde_json::to_string(&verified).expect("serializes");
        let restored: VerifiedObserver = serde_json::from_str(&json).expect("round-trips");
        assert_eq!(restored, verified);
    }

    #[test]
    fn an_observer_survives_a_serde_round_trip() {
        let obs = Observer {
            id: id("serde.test.v1"),
            kind: ObserverKind::SignEraser,
        };
        let json = serde_json::to_string(&obs).unwrap();
        assert!(json.contains("\"serde.test.v1\""));
        assert_eq!(serde_json::from_str::<Observer>(&json).unwrap(), obs);
    }

    #[test]
    fn a_malformed_observer_id_is_refused_on_the_wire() {
        let json = r#"{"id":"has space","kind":"SignEraser"}"#;
        assert!(serde_json::from_str::<Observer>(json).is_err());
    }

    #[test]
    fn a_custom_observer_declares_its_name() {
        let obs = Observer {
            id: id("custom.01"),
            kind: ObserverKind::Custom("my_observer".to_string()),
        };
        assert_eq!(obs.kind, ObserverKind::Custom("my_observer".to_string()));
    }
}
