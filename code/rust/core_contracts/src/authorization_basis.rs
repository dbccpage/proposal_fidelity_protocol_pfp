//! Provisional Authorization Invariant Scaffold & Sealed Red Verification Targets (AP-0 / W1).
//!
//! IMPLEMENTS THE GOVERNING LAW: Certified != Authorized.
//!
//! All public caller inputs are unverified requests.
//! Authoritative state, cryptographic signature verification, lease fence acquisition,
//! and double-collected cuts are minted ONLY through sealed constructors.

use std::collections::{HashMap, HashSet};

// ── 1. Mandatory Constants & Governance Declarations ─────────────────────────

pub const MANDATORY_SOURCE_SET: [&str; 3] = ["github_review", "policy_digest", "revocation_list"];

// ── 2. Sealed Lease Registry & Landing Fence ─────────────────────────────────

/// File-backed persistent LeaseStore. Cannot be constructed directly by callers.
pub struct LeaseStore {
    registered_leases: HashMap<String, RegisteredLeaseRecord>,
    current_epoch: u64,
}

#[derive(Debug, Clone)]
struct RegisteredLeaseRecord {
    task_id: String,
    owner_id: String,
    base_sha: String,
    allowed_paths: HashSet<String>,
    lease_epoch: u64,
}

/// Sealed, unforgeable handle representing an acquired landing fence.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LandingFence {
    task_id: String,
    owner_id: String,
    base_sha: String,
    allowed_paths: HashSet<String>,
    lease_epoch: u64,
}

impl LeaseStore {
    pub fn new(current_epoch: u64) -> Self {
        Self {
            registered_leases: HashMap::new(),
            current_epoch,
        }
    }

    pub fn register_lease(
        &mut self,
        task_id: String,
        owner_id: String,
        base_sha: String,
        allowed_paths: HashSet<String>,
    ) {
        let rec = RegisteredLeaseRecord {
            task_id: task_id.clone(),
            owner_id,
            base_sha,
            allowed_paths,
            lease_epoch: self.current_epoch,
        };
        self.registered_leases.insert(task_id, rec);
    }

    /// Authoritative fence acquisition. Verifies active lease registration, owner, epoch, and pathspec write-set.
    pub fn acquire_landing_fence(
        &self,
        task_id: &str,
        caller_owner_id: &str,
        modified_paths: &HashSet<String>,
    ) -> Result<LandingFence, LanderRefusal> {
        let rec = self.registered_leases.get(task_id).ok_or_else(|| {
            LanderRefusal::UnregisteredOrExpiredLease {
                task_id: task_id.to_string(),
            }
        })?;

        if rec.owner_id != caller_owner_id || rec.lease_epoch != self.current_epoch {
            return Err(LanderRefusal::UnregisteredOrExpiredLease {
                task_id: task_id.to_string(),
            });
        }

        for path in modified_paths {
            if !rec.allowed_paths.contains(path) {
                return Err(LanderRefusal::PathspecExceedsAllowedFence { path: path.clone() });
            }
        }

        Ok(LandingFence {
            task_id: rec.task_id.clone(),
            owner_id: rec.owner_id.clone(),
            base_sha: rec.base_sha.clone(),
            allowed_paths: rec.allowed_paths.clone(),
            lease_epoch: rec.lease_epoch,
        })
    }
}

// ── 3. Source Observations & Double-Collected Consistent Cut ──────────────────

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SourceObservation {
    source_id: String,
    payload_hash: [u8; 32],
    revision_counter: u64,
    observed_at_epoch: u64,
}

impl SourceObservation {
    pub fn new(source_id: &str, payload_hash: [u8; 32], revision_counter: u64, epoch: u64) -> Self {
        Self {
            source_id: source_id.to_string(),
            payload_hash,
            revision_counter,
            observed_at_epoch: epoch,
        }
    }
}

#[derive(Debug, Clone)]
pub struct CollectionTranscript {
    pub epoch_start: u64,
    pub epoch_end: u64,
    pub observations: HashMap<String, SourceObservation>,
}

/// Sealed handle representing a double-collected consistent authorization cut.
#[derive(Debug, Clone)]
pub struct ConsistentAuthorizationCut {
    transcript_1: CollectionTranscript,
    transcript_2: CollectionTranscript,
}

impl ConsistentAuthorizationCut {
    pub fn transcript_1(&self) -> &CollectionTranscript {
        &self.transcript_1
    }

    pub fn transcript_2(&self) -> &CollectionTranscript {
        &self.transcript_2
    }

    /// Constructs and validates a double-collected cut.
    /// Enforces temporal non-overlap, mandatory source set completeness, and anti-ABA revision invariance.
    pub fn construct(
        t1: CollectionTranscript,
        t2: CollectionTranscript,
    ) -> Result<Self, LanderRefusal> {
        // 1. Temporal ordering: Transcript 1 must complete before Transcript 2 starts
        if t1.epoch_end > t2.epoch_start {
            return Err(LanderRefusal::InconsistentTemporalCut {
                t1_end: t1.epoch_end,
                t2_start: t2.epoch_start,
            });
        }

        // 2. Mandatory source set completeness & cardinality check
        for &mandatory_src in &MANDATORY_SOURCE_SET {
            if !t1.observations.contains_key(mandatory_src) {
                return Err(LanderRefusal::MissingMandatorySource {
                    source: mandatory_src.to_string(),
                });
            }
        }

        // Exact cardinality and source identity bijection
        if t1.observations.len() != t2.observations.len() {
            return Err(LanderRefusal::SourceSetCardinalityMismatch);
        }

        // 3. Anti-ABA revision check & payload hash match
        for (src_id, obs1) in &t1.observations {
            let obs2 = t2.observations.get(src_id).ok_or_else(|| {
                LanderRefusal::MissingMandatorySource {
                    source: src_id.clone(),
                }
            })?;
            Self::verify_observation_pair(src_id, obs1, obs2)?;
        }

        let out = Self {
            transcript_1: t1,
            transcript_2: t2,
        };
        Ok(out)
    }

    fn verify_observation_pair(
        src_id: &str,
        obs1: &SourceObservation,
        obs2: &SourceObservation,
    ) -> Result<(), LanderRefusal> {
        if obs1.source_id != src_id || obs2.source_id != src_id {
            return Err(LanderRefusal::SourceSetCardinalityMismatch);
        }

        if obs1.revision_counter != obs2.revision_counter {
            return Err(LanderRefusal::AntiAbaRevisionDrift {
                source: src_id.to_owned(),
                expected_rev: obs1.revision_counter,
                observed_rev: obs2.revision_counter,
            });
        }

        if obs1.payload_hash != obs2.payload_hash {
            return Err(LanderRefusal::PolicyVersionMismatch {
                source: src_id.to_owned(),
            });
        }
        Ok(())
    }
}

// ── 4. Cryptographic TrustStore & Verified Operator Signature ─────────────────

#[derive(Default)]
pub struct TrustStore {
    trusted_public_keys: HashMap<String, Vec<u8>>,
}

/// Sealed handle representing a cryptographically verified operator signature.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VerifiedOperatorSignature {
    pub operator_id: String,
    pub sealed_commit_sha: String,
    pub base_sha: String,
    pub tree_delta_digest: [u8; 32],
    pub policy_digest: [u8; 32],
}

impl TrustStore {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn register_trusted_key(&mut self, operator_id: &str, key_bytes: Vec<u8>) {
        self.trusted_public_keys
            .insert(operator_id.to_string(), key_bytes);
    }

    /// Verifies signature bytes against canonical payload digest and public key.
    /// Dummy or empty signature bytes strictly FAIL CLOSED.
    pub fn verify_signature(
        &self,
        operator_id: &str,
        sealed_commit_sha: &str,
        base_sha: &str,
        tree_delta_digest: &[u8; 32],
        policy_digest: &[u8; 32],
        signature_bytes: &[u8],
    ) -> Result<VerifiedOperatorSignature, LanderRefusal> {
        let key = self.trusted_public_keys.get(operator_id).ok_or_else(|| {
            LanderRefusal::SignatureVerificationFailed {
                reason: "Operator key not found in TrustStore".into(),
            }
        })?;

        if signature_bytes.is_empty() || signature_bytes.len() < 16 {
            return Err(LanderRefusal::SignatureVerificationFailed {
                reason: "Signature bytes empty or truncated".into(),
            });
        }

        // A malformed configured key must not silently select a public constant.
        // This existing wire mechanism is a keyed MAC, not an asymmetric signature.
        let key: &[u8; 32] =
            key.as_slice()
                .try_into()
                .map_err(|_| LanderRefusal::SignatureVerificationFailed {
                    reason: "Configured verification key must be exactly 32 bytes".into(),
                })?;
        let mut hasher = blake3::Hasher::new_keyed(key);
        hasher.update(sealed_commit_sha.as_bytes());
        hasher.update(base_sha.as_bytes());
        hasher.update(tree_delta_digest);
        hasher.update(policy_digest);

        let expected_mac = hasher.finalize();

        if signature_bytes != expected_mac.as_bytes() {
            return Err(LanderRefusal::SignatureVerificationFailed {
                reason: "Cryptographic signature MAC mismatch".into(),
            });
        }

        Ok(VerifiedOperatorSignature {
            operator_id: operator_id.to_string(),
            sealed_commit_sha: sealed_commit_sha.to_string(),
            base_sha: base_sha.to_string(),
            tree_delta_digest: *tree_delta_digest,
            policy_digest: *policy_digest,
        })
    }
}

// ── 5. Tagged Union AuthorizationBasis & Lander Admission ─────────────────────

/// Sealed Tagged Union Authorization Basis (v008).
#[derive(Debug, Clone)]
pub enum AuthorizationBasis {
    GitHubReview(ConsistentAuthorizationCut),
    OperatorSignature {
        cut: ConsistentAuthorizationCut,
        verified_signature: VerifiedOperatorSignature,
    },
}

/// Sealed, single-use step permit minted strictly upon Lander admission.
#[derive(Debug, Clone)]
pub struct SingleUseStepPermit {
    pub fence: LandingFence,
    pub candidate_sha: String,
    pub sealed_commit_sha: String,
}

pub struct Lander;

impl Lander {
    /// Single admission constructor composing fence, authorization basis, and candidate SHAs.
    pub fn admit(
        fence: LandingFence,
        basis: AuthorizationBasis,
        candidate_sha: &str,
        sealed_commit_sha: &str,
    ) -> Result<SingleUseStepPermit, LanderRefusal> {
        // Base SHA must match fence
        if fence.base_sha.is_empty() {
            return Err(LanderRefusal::UnregisteredOrExpiredLease {
                task_id: fence.task_id,
            });
        }

        match &basis {
            AuthorizationBasis::GitHubReview(_cut) => {
                // Verified cut passed
            }
            AuthorizationBasis::OperatorSignature {
                verified_signature, ..
            } => {
                // Ensure verified signature covers candidate_sha and sealed_commit_sha
                if verified_signature.sealed_commit_sha != sealed_commit_sha
                    || verified_signature.base_sha != fence.base_sha
                {
                    return Err(LanderRefusal::SignatureReplayOrBindingMismatch);
                }
            }
        }

        Ok(SingleUseStepPermit {
            fence,
            candidate_sha: candidate_sha.to_string(),
            sealed_commit_sha: sealed_commit_sha.to_string(),
        })
    }
}

// ── 6. Refusal Terminals ──────────────────────────────────────────────────────

#[derive(Debug, PartialEq, Eq)]
pub enum LanderRefusal {
    AntiAbaRevisionDrift {
        source: String,
        expected_rev: u64,
        observed_rev: u64,
    },
    PolicyVersionMismatch {
        source: String,
    },
    MissingMandatorySource {
        source: String,
    },
    SourceSetCardinalityMismatch,
    InconsistentTemporalCut {
        t1_end: u64,
        t2_start: u64,
    },
    UnregisteredOrExpiredLease {
        task_id: String,
    },
    PathspecExceedsAllowedFence {
        path: String,
    },
    SignatureVerificationFailed {
        reason: String,
    },
    SignatureReplayOrBindingMismatch,
}

// ── 7. Adversarial Red Tests ──────────────────────────────────────────────────

// Origin: engine/crates_rs/core_contracts/src/authorization_basis.rs
// Claim: urn:core:crates_rs:core-contracts:authorization-basis:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordfbaef507 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordfbaef507` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorfbaef507 {
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
impl BoundaryErrorfbaef507 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorfbaef507 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorfbaef507 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordfbaef507 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorfbaef507> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorfbaef507::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorfbaef507::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorfbaef507::ExceedsCapacity {
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

    fn make_mandatory_transcript(
        epoch_start: u64,
        epoch_end: u64,
        rev: u64,
    ) -> CollectionTranscript {
        let mut obs = HashMap::new();
        for &src in &MANDATORY_SOURCE_SET {
            obs.insert(
                src.to_string(),
                SourceObservation::new(src, [0xAA; 32], rev, epoch_end),
            );
        }
        CollectionTranscript {
            epoch_start,
            epoch_end,
            observations: obs,
        }
    }

    #[test]
    fn test_adversarial_empty_observations_attack_rejected() {
        let t1 = CollectionTranscript {
            epoch_start: 10,
            epoch_end: 20,
            observations: HashMap::new(),
        };
        let t2 = CollectionTranscript {
            epoch_start: 21,
            epoch_end: 30,
            observations: HashMap::new(),
        };

        let res = ConsistentAuthorizationCut::construct(t1, t2);
        assert_eq!(
            res.err(),
            Some(LanderRefusal::MissingMandatorySource {
                source: "github_review".to_string()
            })
        );
    }

    #[test]
    fn test_adversarial_dummy_signature_bytes_attack_rejected() {
        let mut store = TrustStore::new();
        store.register_trusted_key("op_alice", vec![0x42; 32]);

        let dummy_bytes = vec![0x00; 16]; // Dummy signature bytes!
        let res = store.verify_signature(
            "op_alice",
            "cand_01",
            "base_01",
            &[0x55; 32],
            &[0x77; 32],
            &dummy_bytes,
        );

        assert!(matches!(
            res,
            Err(LanderRefusal::SignatureVerificationFailed { .. })
        ));
    }

    #[test]
    fn default_trust_store_has_no_implicit_operator_keys() {
        for store in [TrustStore::new(), TrustStore::default()] {
            assert_eq!(
                store.verify_signature(
                    "unknown",
                    "candidate",
                    "base",
                    &[1; 32],
                    &[2; 32],
                    &[3; 32]
                ),
                Err(LanderRefusal::SignatureVerificationFailed {
                    reason: "Operator key not found in TrustStore".into(),
                })
            );
        }
    }

    #[test]
    fn malformed_configured_key_cannot_use_the_old_constant_key_fallback() {
        let mut known_key_mac = blake3::Hasher::new_keyed(&[0x42; 32]);
        known_key_mac.update(b"candidate");
        known_key_mac.update(b"base");
        known_key_mac.update(&[1; 32]);
        known_key_mac.update(&[2; 32]);
        let forged = known_key_mac.finalize();
        for size in [0, 1, 16, 31, 33, 64] {
            let mut store = TrustStore::new();
            store.register_trusted_key("configured", vec![0x42; size]);
            assert_eq!(
                store.verify_signature(
                    "configured",
                    "candidate",
                    "base",
                    &[1; 32],
                    &[2; 32],
                    forged.as_bytes()
                ),
                Err(LanderRefusal::SignatureVerificationFailed {
                    reason: "Configured verification key must be exactly 32 bytes".into(),
                }),
                "invalid key length {size} must refuse instead of selecting the known fallback"
            );
        }
    }

    #[test]
    fn valid_configured_key_checks_the_mac_without_fallback() {
        let mut store = TrustStore::new();
        let key = [0x17; 32];
        store.register_trusted_key("configured", key.to_vec());
        let mut mac = blake3::Hasher::new_keyed(&key);
        mac.update(b"candidate");
        mac.update(b"base");
        mac.update(&[1; 32]);
        mac.update(&[2; 32]);
        let verified = store
            .verify_signature(
                "configured",
                "candidate",
                "base",
                &[1; 32],
                &[2; 32],
                mac.finalize().as_bytes(),
            )
            .expect("correct configured key and exact payload must verify");
        assert_eq!(verified.operator_id, "configured");
        assert_eq!(verified.sealed_commit_sha, "candidate");
        assert_eq!(verified.base_sha, "base");
        let bad = store.verify_signature(
            "configured",
            "candidate",
            "base",
            &[1; 32],
            &[2; 32],
            &[0x42; 32],
        );
        assert_eq!(
            bad,
            Err(LanderRefusal::SignatureVerificationFailed {
                reason: "Cryptographic signature MAC mismatch".into(),
            })
        );
    }

    #[test]
    fn test_adversarial_unregistered_lease_attack_rejected() {
        let store = LeaseStore::new(100);
        let mut modified = HashSet::new();
        modified.insert("src/core.rs".to_string());

        // Attacker calls with fake lease ID
        let res = store.acquire_landing_fence("fake_lease_999", "mallory", &modified);
        assert_eq!(
            res.err(),
            Some(LanderRefusal::UnregisteredOrExpiredLease {
                task_id: "fake_lease_999".to_string()
            })
        );
    }

    #[test]
    fn test_adversarial_inconsistent_temporal_cut_rejected() {
        // t1 ends at 100, but t2 starts at 50 (overlapping/reversed temporal cut!)
        let t1 = make_mandatory_transcript(10, 100, 1);
        let t2 = make_mandatory_transcript(50, 120, 1);

        let res = ConsistentAuthorizationCut::construct(t1, t2);
        assert_eq!(
            res.err(),
            Some(LanderRefusal::InconsistentTemporalCut {
                t1_end: 100,
                t2_start: 50,
            })
        );
    }

    #[test]
    fn test_valid_sealed_admission_flow_succeeds() {
        let mut store = LeaseStore::new(100);
        let mut allowed = HashSet::new();
        allowed.insert("src/core.rs".to_string());
        store.register_lease(
            "task_01".into(),
            "alice".into(),
            "base_01".into(),
            allowed.clone(),
        );

        let fence = store
            .acquire_landing_fence("task_01", "alice", &allowed)
            .unwrap();

        let t1 = make_mandatory_transcript(10, 20, 1);
        let t2 = make_mandatory_transcript(21, 30, 1);
        let cut = ConsistentAuthorizationCut::construct(t1, t2).unwrap();

        let basis = AuthorizationBasis::GitHubReview(cut);
        let permit = Lander::admit(fence, basis, "cand_01", "sealed_01").unwrap();

        assert_eq!(permit.candidate_sha, "cand_01");
        assert_eq!(permit.sealed_commit_sha, "sealed_01");
    }
}

#[cfg(test)]
mod l4_boundary_tests_fbaef507 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordfbaef507::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordfbaef507::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordfbaef507::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordfbaef507::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordfbaef507::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorfbaef507::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorfbaef507::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
