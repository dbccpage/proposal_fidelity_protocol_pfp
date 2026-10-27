//! Shared native owner for intelligence intake, transfer, certification, and
//! retention policy. Mathematical verification and immune admission remain in
//! their existing kernels and cross this crate through evidence receipts.

mod lifecycle;
mod manifest;
pub mod port;
mod refusal;
mod retention;

pub use lifecycle::{
    decode_error, evaluate_lifecycle, ClosureReceipt, DigestionState, ExtractionRecord,
    FindingRecord, FindingTransferBinding, LifecycleCertificate, LifecycleDecision,
    LifecycleRequest, LifecycleResidual, SourceRegistration, TransferReceipt,
    LIFECYCLE_CERTIFICATE_SCHEMA, LIFECYCLE_DECISION_SCHEMA,
};
pub use manifest::{
    framed_sha256, seal_bytes, seal_manifest, ArtifactEntry, SealManifestRequest, SealedManifest,
    MANIFEST_DOMAIN, SOURCE_ID_DOMAIN, SOURCE_MANIFEST_SCHEMA,
};
pub use refusal::Refusal;
pub use retention::{evaluate_retention, RetentionDecision, RetentionRequest, StorageState};

// Origin: engine/crates_rs/core_intelligence/src/lib.rs
// Claim: urn:core:crates_rs:core-intelligence:lib:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord0bd4db3d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord0bd4db3d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError0bd4db3d {
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
impl BoundaryError0bd4db3d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError0bd4db3d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError0bd4db3d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord0bd4db3d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError0bd4db3d> {
        if capacity_bound == 0 {
            return Err(BoundaryError0bd4db3d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError0bd4db3d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError0bd4db3d::ExceedsCapacity {
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

    fn entry(path: &str, bytes: &[u8]) -> ArtifactEntry {
        use sha2::{Digest, Sha256};
        ArtifactEntry {
            path: path.into(),
            size_bytes: bytes.len() as u64,
            sha256: format!("sha256:{}", hex::encode(Sha256::digest(bytes))),
        }
    }

    fn source() -> SourceRegistration {
        SourceRegistration {
            source_id: "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
                .into(),
            producer_id: "core_adversary".into(),
            source_class: "run_bundle".into(),
            source_schema_version: SOURCE_MANIFEST_SCHEMA.into(),
            manifest_sha256:
                "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb".into(),
            sealed: true,
            producer_lease_active: false,
            review_scope: "core.intelligence.test.v1".into(),
        }
    }

    fn extraction() -> ExtractionRecord {
        ExtractionRecord {
            complete: true,
            extractor_version: "extractor-test-v1".into(),
            checker_version: "checker-test-v1".into(),
            coverage_gaps: Vec::new(),
            parse_residuals: Vec::new(),
        }
    }

    fn transfer() -> TransferReceipt {
        TransferReceipt {
            destination_id: "obligation:one".into(),
            target_revision:
                "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc".into(),
            acknowledgement_ref:
                "sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd".into(),
            kind: "OPEN_OBLIGATION".into(),
        }
    }

    #[test]
    fn framed_manifest_distinguishes_ambiguous_concatenation() {
        let left = seal_manifest(SealManifestRequest {
            producer_id: "producer".into(),
            source_class: "fixture".into(),
            source_locator: "left".into(),
            entries: vec![entry("a", b"bc")],
        })
        .unwrap();
        let right = seal_manifest(SealManifestRequest {
            producer_id: "producer".into(),
            source_class: "fixture".into(),
            source_locator: "right".into(),
            entries: vec![entry("ab", b"c")],
        })
        .unwrap();
        assert_ne!(left.manifest_sha256, right.manifest_sha256);
    }

    #[test]
    fn manifest_identity_is_order_invariant_but_rejects_duplicate_paths() {
        let first = seal_manifest(SealManifestRequest {
            producer_id: "producer".into(),
            source_class: "fixture".into(),
            source_locator: "scope".into(),
            entries: vec![entry("b", b"b"), entry("a", b"a")],
        })
        .unwrap();
        let second = seal_manifest(SealManifestRequest {
            producer_id: "producer".into(),
            source_class: "fixture".into(),
            source_locator: "scope".into(),
            entries: vec![entry("a", b"a"), entry("b", b"b")],
        })
        .unwrap();
        assert_eq!(first, second);
        assert!(seal_manifest(SealManifestRequest {
            producer_id: "producer".into(),
            source_class: "fixture".into(),
            source_locator: "scope".into(),
            entries: vec![entry("a", b"a"), entry("a", b"b")],
        })
        .is_err());
    }

    #[test]
    fn untransferred_finding_cannot_be_absorbed() {
        let decision = evaluate_lifecycle(&LifecycleRequest {
            source: source(),
            extraction: extraction(),
            findings: vec![FindingRecord {
                finding_id: "finding:one".into(),
                kind: "DEFECT".into(),
                applicable: true,
                transfer: None,
                closure: None,
                evidence_refs: Vec::new(),
            }],
        });
        assert_eq!(decision.state, DigestionState::Extracted);
        assert!(!decision.archive_eligible);
        assert_eq!(decision.pending_finding_ids, vec!["finding:one"]);
    }

    #[test]
    fn durable_open_obligation_absorbs_without_discharging() {
        let decision = evaluate_lifecycle(&LifecycleRequest {
            source: source(),
            extraction: extraction(),
            findings: vec![FindingRecord {
                finding_id: "finding:one".into(),
                kind: "DEFECT".into(),
                applicable: true,
                transfer: Some(transfer()),
                closure: None,
                evidence_refs: Vec::new(),
            }],
        });
        assert_eq!(decision.state, DigestionState::Absorbed);
        assert!(decision.archive_eligible);
        assert_eq!(decision.transferred_open_finding_ids, vec!["finding:one"]);
        assert_eq!(decision.certificate.unwrap().kind, "ABSORPTION");
    }

    #[test]
    fn checked_closure_discharges_and_active_leases_block() {
        let closed = evaluate_lifecycle(&LifecycleRequest {
            source: source(),
            extraction: extraction(),
            findings: vec![FindingRecord {
                finding_id: "finding:one".into(),
                kind: "DEFECT".into(),
                applicable: true,
                transfer: Some(transfer()),
                closure: Some(ClosureReceipt {
                    checker_id: "native-checker".into(),
                    closure_ref:
                        "sha256:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
                            .into(),
                    verified: true,
                }),
                evidence_refs: Vec::new(),
            }],
        });
        assert_eq!(closed.state, DigestionState::Discharged);
        let mut leased_source = source();
        leased_source.producer_lease_active = true;
        let blocked = evaluate_lifecycle(&LifecycleRequest {
            source: leased_source,
            extraction: extraction(),
            findings: Vec::new(),
        });
        assert_eq!(blocked.state, DigestionState::Blocked);
        assert!(!blocked.archive_eligible);
    }

    fn open_finding(finding_id: &str, destination_id: &str) -> FindingRecord {
        let mut receipt = transfer();
        receipt.destination_id = destination_id.into();
        FindingRecord {
            finding_id: finding_id.into(),
            kind: "DEFECT".into(),
            applicable: true,
            transfer: Some(receipt),
            closure: None,
            evidence_refs: Vec::new(),
        }
    }

    #[test]
    fn absorption_certificate_is_invariant_under_finding_order() {
        let forward = evaluate_lifecycle(&LifecycleRequest {
            source: source(),
            extraction: extraction(),
            findings: vec![
                open_finding("finding:b", "obligation:b"),
                open_finding("finding:a", "obligation:a"),
            ],
        });
        let reverse = evaluate_lifecycle(&LifecycleRequest {
            source: source(),
            extraction: extraction(),
            findings: vec![
                open_finding("finding:a", "obligation:a"),
                open_finding("finding:b", "obligation:b"),
            ],
        });
        let forward_certificate = forward.certificate.expect("forward certificate");
        let reverse_certificate = reverse.certificate.expect("reverse certificate");
        assert_eq!(forward_certificate, reverse_certificate);
        assert_eq!(
            forward_certificate.certificate_id,
            reverse_certificate.certificate_id
        );
        assert_eq!(
            forward_certificate.open_obligation_finding_ids,
            vec!["finding:a", "finding:b"]
        );
        assert_eq!(
            forward.transferred_open_finding_ids,
            reverse.transferred_open_finding_ids
        );
    }

    fn absorption_certificate(findings: Vec<FindingRecord>) -> LifecycleCertificate {
        let decision = evaluate_lifecycle(&LifecycleRequest {
            source: source(),
            extraction: extraction(),
            findings,
        });
        assert_eq!(decision.state, DigestionState::Absorbed);
        assert!(decision.archive_eligible);
        decision.certificate.expect("absorption certificate")
    }

    fn assert_transfer_change_changes_certificate(change: impl FnOnce(&mut TransferReceipt)) {
        let original = open_finding("finding:one", "obligation:one");
        let before = absorption_certificate(vec![original.clone()]);
        let mut changed = original;
        change(changed.transfer.as_mut().expect("fixture transfer"));
        let after = absorption_certificate(vec![changed]);
        assert_ne!(before.certificate_id, after.certificate_id);
    }

    #[test]
    fn certificate_binds_transfer_destination() {
        assert_transfer_change_changes_certificate(|receipt| {
            receipt.destination_id = "obligation:transplanted".into();
        });
    }

    #[test]
    fn certificate_binds_transfer_target_revision() {
        assert_transfer_change_changes_certificate(|receipt| {
            receipt.target_revision = format!("sha256:{}", "e".repeat(64));
        });
    }

    #[test]
    fn certificate_binds_transfer_acknowledgement() {
        assert_transfer_change_changes_certificate(|receipt| {
            receipt.acknowledgement_ref = format!("sha256:{}", "f".repeat(64));
        });
    }

    #[test]
    fn certificate_binds_transfer_kind() {
        assert_transfer_change_changes_certificate(|receipt| {
            receipt.kind = "CANDIDATE_ANTIBODY_OPEN_OBLIGATION".into();
        });
    }

    #[test]
    fn certificate_binds_finding_to_transfer_assignment() {
        let first = open_finding("finding:a", "obligation:a");
        let mut second = open_finding("finding:b", "obligation:b");
        second.transfer.as_mut().unwrap().acknowledgement_ref =
            format!("sha256:{}", "e".repeat(64));
        let before = absorption_certificate(vec![first.clone(), second.clone()]);
        let swapped = vec![
            FindingRecord {
                transfer: second.transfer.clone(),
                ..first
            },
            FindingRecord {
                transfer: first.transfer.clone(),
                ..second
            },
        ];
        let after = absorption_certificate(swapped);
        assert_eq!(before.finding_ids, after.finding_ids);
        assert_eq!(
            before.destination_receipt_refs,
            after.destination_receipt_refs
        );
        assert_eq!(
            before.open_obligation_finding_ids,
            after.open_obligation_finding_ids
        );
        assert_ne!(before.certificate_id, after.certificate_id);
    }

    #[test]
    fn certificate_v2_exposes_sorted_complete_transfer_bindings() {
        let certificate = absorption_certificate(vec![
            open_finding("finding:b", "obligation:b"),
            open_finding("finding:a", "obligation:a"),
        ]);
        let wire = serde_json::to_value(&certificate).unwrap();
        assert_eq!(
            wire["schema_version"],
            "core.intelligence.lifecycle-certificate.v2"
        );
        assert_eq!(wire["authority_effect"], "None");
        let revision = format!("sha256:{}", "c".repeat(64));
        let acknowledgement = format!("sha256:{}", "d".repeat(64));
        assert_ne!(revision, acknowledgement);
        assert_eq!(
            wire["transfer_bindings"],
            serde_json::json!([
                {"finding_id": "finding:a", "destination_id": "obligation:a",
                 "target_revision": revision, "acknowledgement_ref": acknowledgement,
                 "kind": "OPEN_OBLIGATION"},
                {"finding_id": "finding:b", "destination_id": "obligation:b",
                 "target_revision": revision, "acknowledgement_ref": acknowledgement,
                 "kind": "OPEN_OBLIGATION"},
            ])
        );
        assert_eq!(certificate.destination_receipt_refs, vec![acknowledgement]);
        assert_eq!(
            certificate.open_obligation_finding_ids,
            vec!["finding:a", "finding:b"]
        );
    }

    #[test]
    fn certificate_digest_uses_v2_domain_and_emitted_bindings() {
        use sha2::{Digest, Sha256};

        let certificate =
            absorption_certificate(vec![open_finding("finding:one", "obligation:one")]);
        let mut material = serde_json::to_value(&certificate).unwrap();
        let fields = material.as_object_mut().unwrap();
        fields.remove("certificate_id");
        fields.remove("authority_effect");
        let bytes = serde_json::to_vec(&material).unwrap();
        let domain = b"core.intelligence.lifecycle-certificate.v2";
        let mut hasher = Sha256::new();
        hasher.update((domain.len() as u32).to_be_bytes());
        hasher.update(domain);
        hasher.update((bytes.len() as u64).to_be_bytes());
        hasher.update(bytes);
        assert_eq!(
            certificate.certificate_id,
            format!("sha256:{:x}", hasher.finalize())
        );
    }

    fn retention_request() -> RetentionRequest {
        RetentionRequest {
            digestion_state: DigestionState::Discharged,
            storage_state: StorageState::Cold,
            active_lease: false,
            evidence_reachable: true,
            holds: Vec::new(),
            dependency_refs: Vec::new(),
            grace_elapsed: true,
        }
    }

    #[test]
    fn absorbed_open_obligation_is_retained_even_after_grace() {
        let mut request = retention_request();
        request.digestion_state = DigestionState::Absorbed;
        let decision = evaluate_retention(&request);
        assert!(decision.cold_eligible);
        assert!(!decision.disposal_eligible);
        assert_eq!(decision.target_storage_state, StorageState::Cold);
        assert_eq!(
            decision.residuals,
            vec!["TRANSFERRED_OPEN_OBLIGATIONS_RETAIN_REQUIRED_EVIDENCE"]
        );
        assert_eq!(decision.authority_effect, "None");
    }

    #[test]
    fn discharged_retention_requires_every_independent_fence() {
        let ready = evaluate_retention(&retention_request());
        assert!(ready.disposal_eligible);
        assert_eq!(ready.target_storage_state, StorageState::DisposalEligible);
        assert_eq!(ready.authority_effect, "None");
        for (index, expected_residual) in [
            "ACTIVE_LEASE_RETAINS_SOURCE",
            "EVIDENCE_REACHABILITY_UNVERIFIED",
            "RETENTION_HOLD_ACTIVE",
            "DEPENDENCY_REFERENCES_RETAIN_SOURCE",
            "RETENTION_GRACE_NOT_ELAPSED",
        ]
        .into_iter()
        .enumerate()
        {
            let mut request = retention_request();
            match index {
                0 => request.active_lease = true,
                1 => request.evidence_reachable = false,
                2 => request.holds.push("hold:review".into()),
                3 => request.dependency_refs.push("dependency:one".into()),
                4 => request.grace_elapsed = false,
                _ => unreachable!(),
            }
            let decision = evaluate_retention(&request);
            assert!(!decision.disposal_eligible, "{expected_residual}");
            assert_eq!(decision.target_storage_state, StorageState::Cold);
            assert!(decision
                .residuals
                .iter()
                .any(|residual| residual == expected_residual));
            assert_eq!(decision.authority_effect, "None");
        }
    }
}

#[cfg(test)]
mod l4_boundary_tests_0bd4db3d {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord0bd4db3d::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord0bd4db3d::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord0bd4db3d::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord0bd4db3d::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord0bd4db3d::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError0bd4db3d::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError0bd4db3d::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
