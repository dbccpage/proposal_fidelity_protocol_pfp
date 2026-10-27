//! Observer comparison packets.
//!
//! A comparison packet records agreement, disagreement, or incomparability
//! between two observer-visible quotients over the same source quotient. It is
//! diagnostic evidence only: observer agreement cannot raise the authority
//! ceiling or recover distinctions erased by either observer.

use crate::observer_quotient::ObserverQuotient;
use core_kernel::evidence::{
    CarrierManifestHash, EquivalenceRelationHash, ObserverRef, QuotientSpaceHash, ReplayHash,
};
use serde::{Deserialize, Serialize};

pub const OBSERVER_COMPARISON_AUTHORITY_EFFECT: &str = "none";
pub const OBSERVER_COMPARISON_EVIDENCE_CEILING: &str = "ShapeOnly";
pub const OBSERVER_COMPARISON_CUSTOMER_CLAIM_ALLOWED: bool = false;

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum ObserverComparisonStatus {
    Agreement,
    Disagreement,
    Incomparable,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum ObserverComparisonAuthorityRequest {
    PromoteAgreementToAuthority,
    PromoteDisagreementToGlobalObstruction,
    RecoverHiddenDistinctions,
    EmitCustomerClaim,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ComparisonLaunderingRefused {
    pub packet_id: String,
    pub status: ObserverComparisonStatus,
    pub requested_promotion: ObserverComparisonAuthorityRequest,
    pub authority_effect: String,
    pub evidence_ceiling: String,
    pub customer_claim_allowed: bool,
}

impl ComparisonLaunderingRefused {
    pub const fn terminal_label(&self) -> &'static str {
        "ComparisonLaunderingRefused"
    }

    pub const fn can_mint_authority(&self) -> bool {
        false
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum ObserverComparisonResidualKind {
    NoVisibleDifference,
    ObserverDisagreement,
    IncomparableWithoutTransport,
}

impl From<ObserverComparisonStatus> for ObserverComparisonResidualKind {
    fn from(status: ObserverComparisonStatus) -> Self {
        match status {
            ObserverComparisonStatus::Agreement => Self::NoVisibleDifference,
            ObserverComparisonStatus::Disagreement => Self::ObserverDisagreement,
            ObserverComparisonStatus::Incomparable => Self::IncomparableWithoutTransport,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ObserverComparisonResidual {
    pub packet_id: String,
    pub kind: ObserverComparisonResidualKind,
    pub source_quotient_hash: QuotientSpaceHash,
    pub carrier_hash: CarrierManifestHash,
    pub comparison_replay_hash: ReplayHash,
    pub authority_effect: String,
    pub evidence_ceiling: String,
    pub customer_claim_allowed: bool,
}

impl ObserverComparisonResidual {
    pub const fn residual_label(&self) -> &'static str {
        "ObserverComparisonResidual"
    }

    pub const fn can_mint_authority(&self) -> bool {
        false
    }
}

#[derive(Debug, thiserror::Error, PartialEq, Eq)]
pub enum ObserverComparisonError {
    #[error("comparison packet ID cannot be empty")]
    EmptyPacketId,
    #[error("{0} observer reference cannot be empty")]
    EmptyObserverRef(&'static str),
    #[error("source quotient hash cannot be zero")]
    ZeroSourceQuotientHash,
    #[error("{0} equivalence relation hash cannot be zero")]
    ZeroEquivalenceRelationHash(&'static str),
    #[error("{0} replay hash cannot be zero")]
    ZeroReplayHash(&'static str),
    #[error("carrier hash cannot be zero")]
    ZeroCarrierHash,
    #[error("observer quotients have different source quotients; explicit transport is required")]
    SourceQuotientMismatch,
    #[error("observer quotients have different carriers; explicit transport is required")]
    CarrierMismatch,
    #[error("observer comparison cannot compare an observer to itself")]
    IdenticalObserverComparison,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ObserverComparisonPacket {
    pub id: String,
    pub left_observer_ref: ObserverRef,
    pub right_observer_ref: ObserverRef,
    pub source_quotient_hash: QuotientSpaceHash,
    pub carrier_hash: CarrierManifestHash,
    pub left_equivalence_relation_hash: EquivalenceRelationHash,
    pub right_equivalence_relation_hash: EquivalenceRelationHash,
    pub left_quotient_replay_hash: ReplayHash,
    pub right_quotient_replay_hash: ReplayHash,
    pub comparison_replay_hash: ReplayHash,
    pub status: ObserverComparisonStatus,
}

impl ObserverComparisonPacket {
    fn validate_refs(
        id: &str,
        left_observer_ref: &ObserverRef,
        right_observer_ref: &ObserverRef,
    ) -> Result<(), ObserverComparisonError> {
        if id.is_empty() {
            return Err(ObserverComparisonError::EmptyPacketId);
        }
        if left_observer_ref.is_empty() {
            return Err(ObserverComparisonError::EmptyObserverRef("left"));
        }
        if right_observer_ref.is_empty() {
            return Err(ObserverComparisonError::EmptyObserverRef("right"));
        }
        if left_observer_ref == right_observer_ref {
            return Err(ObserverComparisonError::IdenticalObserverComparison);
        }
        Ok(())
    }

    fn validate_hashes(
        source_quotient_hash: &QuotientSpaceHash,
        carrier_hash: &CarrierManifestHash,
        left_equivalence_relation_hash: &EquivalenceRelationHash,
        right_equivalence_relation_hash: &EquivalenceRelationHash,
        left_quotient_replay_hash: &ReplayHash,
        right_quotient_replay_hash: &ReplayHash,
        comparison_replay_hash: &ReplayHash,
    ) -> Result<(), ObserverComparisonError> {
        if source_quotient_hash.is_zero() {
            return Err(ObserverComparisonError::ZeroSourceQuotientHash);
        }
        if carrier_hash.is_zero() {
            return Err(ObserverComparisonError::ZeroCarrierHash);
        }
        if left_equivalence_relation_hash.is_zero() {
            return Err(ObserverComparisonError::ZeroEquivalenceRelationHash("left"));
        }
        if right_equivalence_relation_hash.is_zero() {
            return Err(ObserverComparisonError::ZeroEquivalenceRelationHash("right"));
        }
        if left_quotient_replay_hash.is_zero() {
            return Err(ObserverComparisonError::ZeroReplayHash("left quotient"));
        }
        if right_quotient_replay_hash.is_zero() {
            return Err(ObserverComparisonError::ZeroReplayHash("right quotient"));
        }
        if comparison_replay_hash.is_zero() {
            return Err(ObserverComparisonError::ZeroReplayHash("comparison"));
        }
        Ok(())
    }

    #[allow(clippy::too_many_arguments)]
    pub fn new(
        id: String,
        left_observer_ref: ObserverRef,
        right_observer_ref: ObserverRef,
        source_quotient_hash: QuotientSpaceHash,
        carrier_hash: CarrierManifestHash,
        left_equivalence_relation_hash: EquivalenceRelationHash,
        right_equivalence_relation_hash: EquivalenceRelationHash,
        left_quotient_replay_hash: ReplayHash,
        right_quotient_replay_hash: ReplayHash,
        comparison_replay_hash: ReplayHash,
        status: ObserverComparisonStatus,
    ) -> Result<Self, ObserverComparisonError> {
        Self::validate_refs(&id, &left_observer_ref, &right_observer_ref)?;
        Self::validate_hashes(
            &source_quotient_hash,
            &carrier_hash,
            &left_equivalence_relation_hash,
            &right_equivalence_relation_hash,
            &left_quotient_replay_hash,
            &right_quotient_replay_hash,
            &comparison_replay_hash,
        )?;
        Ok(Self {
            id,
            left_observer_ref,
            right_observer_ref,
            source_quotient_hash,
            carrier_hash,
            left_equivalence_relation_hash,
            right_equivalence_relation_hash,
            left_quotient_replay_hash,
            right_quotient_replay_hash,
            comparison_replay_hash,
            status,
        })
    }

    pub fn try_from_observer_quotients(
        id: String,
        left: &ObserverQuotient,
        right: &ObserverQuotient,
        comparison_replay_hash: ReplayHash,
        status: ObserverComparisonStatus,
    ) -> Result<Self, ObserverComparisonError> {
        if left.source_quotient_hash != right.source_quotient_hash {
            return Err(ObserverComparisonError::SourceQuotientMismatch);
        }
        if left.carrier_hash != right.carrier_hash {
            return Err(ObserverComparisonError::CarrierMismatch);
        }

        Self::new(
            id,
            left.observer_ref.clone(),
            right.observer_ref.clone(),
            left.source_quotient_hash.clone(),
            left.carrier_hash.clone(),
            left.equivalence_relation_hash.clone(),
            right.equivalence_relation_hash.clone(),
            left.replay_hash.clone(),
            right.replay_hash.clone(),
            comparison_replay_hash,
            status,
        )
    }

    pub fn try_derive_from_equivalence_hashes(
        id: String,
        left: &ObserverQuotient,
        right: &ObserverQuotient,
        comparison_replay_hash: ReplayHash,
    ) -> Result<Self, ObserverComparisonError> {
        let status = if left.equivalence_relation_hash == right.equivalence_relation_hash {
            ObserverComparisonStatus::Agreement
        } else {
            ObserverComparisonStatus::Incomparable
        };

        Self::try_from_observer_quotients(id, left, right, comparison_replay_hash, status)
    }

    pub const fn authority_effect(&self) -> &'static str {
        OBSERVER_COMPARISON_AUTHORITY_EFFECT
    }

    pub const fn evidence_ceiling(&self) -> &'static str {
        OBSERVER_COMPARISON_EVIDENCE_CEILING
    }

    pub const fn customer_claim_allowed(&self) -> bool {
        OBSERVER_COMPARISON_CUSTOMER_CLAIM_ALLOWED
    }

    pub const fn can_mint_authority(&self) -> bool {
        false
    }

    pub fn residual(&self) -> ObserverComparisonResidual {
        ObserverComparisonResidual {
            packet_id: self.id.clone(),
            kind: ObserverComparisonResidualKind::from(self.status),
            source_quotient_hash: self.source_quotient_hash.clone(),
            carrier_hash: self.carrier_hash.clone(),
            comparison_replay_hash: self.comparison_replay_hash.clone(),
            authority_effect: OBSERVER_COMPARISON_AUTHORITY_EFFECT.to_string(),
            evidence_ceiling: OBSERVER_COMPARISON_EVIDENCE_CEILING.to_string(),
            customer_claim_allowed: OBSERVER_COMPARISON_CUSTOMER_CLAIM_ALLOWED,
        }
    }

    pub fn refuse_authority_request(
        &self,
        requested_promotion: ObserverComparisonAuthorityRequest,
    ) -> ComparisonLaunderingRefused {
        ComparisonLaunderingRefused {
            packet_id: self.id.clone(),
            status: self.status,
            requested_promotion,
            authority_effect: OBSERVER_COMPARISON_AUTHORITY_EFFECT.to_string(),
            evidence_ceiling: OBSERVER_COMPARISON_EVIDENCE_CEILING.to_string(),
            customer_claim_allowed: OBSERVER_COMPARISON_CUSTOMER_CLAIM_ALLOWED,
        }
    }
}

// Origin: engine/crates_rs/core_types/src/observer_comparison.rs
// Claim: urn:core:crates_rs:core-types:observer-comparison:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use core_kernel::evidence::{Hash256, ObserverMapHash};

    fn hash(byte: u8) -> Hash256 {
        Hash256([byte; 32])
    }

    fn replay(byte: u8) -> ReplayHash {
        ReplayHash(hash(byte))
    }

    fn quotient(
        observer_id: &str,
        source_byte: u8,
        carrier_byte: u8,
        equivalence_byte: u8,
        replay_byte: u8,
    ) -> ObserverQuotient {
        ObserverQuotient::new(
            ObserverRef(observer_id.to_string()),
            ObserverMapHash(hash(11)),
            QuotientSpaceHash(hash(source_byte)),
            8,
            4,
            EquivalenceRelationHash(hash(equivalence_byte)),
            CarrierManifestHash(hash(carrier_byte)),
            CarrierManifestHash(hash(carrier_byte)),
            replay(replay_byte),
        )
        .unwrap()
    }

    fn packet_new(
        labels: [&str; 3],
        source: u8,
        carrier: u8,
        equivalence: [u8; 2],
        replay_bytes: [u8; 3],
    ) -> Result<ObserverComparisonPacket, ObserverComparisonError> {
        let [id, left, right] = labels;
        let [left_eq, right_eq] = equivalence;
        let [left_replay, right_replay, cmp_replay] = replay_bytes;
        ObserverComparisonPacket::new(
            id.to_string(),
            ObserverRef(left.to_string()),
            ObserverRef(right.to_string()),
            QuotientSpaceHash(hash(source)),
            CarrierManifestHash(hash(carrier)),
            EquivalenceRelationHash(hash(left_eq)),
            EquivalenceRelationHash(hash(right_eq)),
            replay(left_replay),
            replay(right_replay),
            replay(cmp_replay),
            ObserverComparisonStatus::Agreement,
        )
    }

    #[test]
    fn comparison_packet_from_same_source_is_diagnostic_only() {
        let left = quotient("left", 1, 2, 3, 4);
        let right = quotient("right", 1, 2, 5, 6);
        let packet = ObserverComparisonPacket::try_from_observer_quotients(
            "cmp1".to_string(),
            &left,
            &right,
            replay(7),
            ObserverComparisonStatus::Agreement,
        )
        .unwrap();

        assert_eq!(packet.status, ObserverComparisonStatus::Agreement);
        assert_eq!(packet.authority_effect(), "none");
        assert_eq!(packet.evidence_ceiling(), "ShapeOnly");
        assert!(!packet.customer_claim_allowed());
        assert!(!packet.can_mint_authority());
    }

    #[test]
    fn comparison_packet_emits_typed_residual_without_authority() {
        let left = quotient("left", 1, 2, 3, 4);
        let right = quotient("right", 1, 2, 5, 6);
        let packet = ObserverComparisonPacket::try_from_observer_quotients(
            "cmp1".to_string(),
            &left,
            &right,
            replay(7),
            ObserverComparisonStatus::Disagreement,
        )
        .unwrap();
        let residual = packet.residual();

        assert_eq!(residual.residual_label(), "ObserverComparisonResidual");
        assert_eq!(
            residual.kind,
            ObserverComparisonResidualKind::ObserverDisagreement
        );
        assert_eq!(residual.authority_effect, "none");
        assert_eq!(residual.evidence_ceiling, "ShapeOnly");
        assert!(!residual.customer_claim_allowed);
        assert!(!residual.can_mint_authority());
    }

    #[test]
    fn comparison_packet_refuses_laundering_attempts() {
        let left = quotient("left", 1, 2, 3, 4);
        let right = quotient("right", 1, 2, 5, 6);
        let packet = ObserverComparisonPacket::try_from_observer_quotients(
            "cmp1".to_string(),
            &left,
            &right,
            replay(7),
            ObserverComparisonStatus::Agreement,
        )
        .unwrap();
        let refusal = packet.refuse_authority_request(
            ObserverComparisonAuthorityRequest::PromoteAgreementToAuthority,
        );

        assert_eq!(refusal.terminal_label(), "ComparisonLaunderingRefused");
        assert_eq!(
            refusal.requested_promotion,
            ObserverComparisonAuthorityRequest::PromoteAgreementToAuthority
        );
        assert_eq!(refusal.authority_effect, "none");
        assert_eq!(refusal.evidence_ceiling, "ShapeOnly");
        assert!(!refusal.customer_claim_allowed);
        assert!(!refusal.can_mint_authority());
    }

    #[test]
    fn comparison_status_maps_to_residual_kind() {
        assert_eq!(
            ObserverComparisonResidualKind::from(ObserverComparisonStatus::Agreement),
            ObserverComparisonResidualKind::NoVisibleDifference
        );
        assert_eq!(
            ObserverComparisonResidualKind::from(ObserverComparisonStatus::Disagreement),
            ObserverComparisonResidualKind::ObserverDisagreement
        );
        assert_eq!(
            ObserverComparisonResidualKind::from(ObserverComparisonStatus::Incomparable),
            ObserverComparisonResidualKind::IncomparableWithoutTransport
        );
    }

    #[test]
    fn conservative_hash_derivation_agrees_only_on_matching_equivalence_hashes() {
        let left = quotient("left", 1, 2, 3, 4);
        let right = quotient("right", 1, 2, 3, 6);
        let packet = ObserverComparisonPacket::try_derive_from_equivalence_hashes(
            "cmp1".to_string(),
            &left,
            &right,
            replay(7),
        )
        .unwrap();

        assert_eq!(packet.status, ObserverComparisonStatus::Agreement);
        assert!(!packet.can_mint_authority());
    }

    #[test]
    fn conservative_hash_derivation_treats_different_hashes_as_incomparable() {
        let left = quotient("left", 1, 2, 3, 4);
        let right = quotient("right", 1, 2, 5, 6);
        let packet = ObserverComparisonPacket::try_derive_from_equivalence_hashes(
            "cmp1".to_string(),
            &left,
            &right,
            replay(7),
        )
        .unwrap();
        let refusal = packet.refuse_authority_request(
            ObserverComparisonAuthorityRequest::PromoteDisagreementToGlobalObstruction,
        );

        assert_eq!(packet.status, ObserverComparisonStatus::Incomparable);
        assert_eq!(
            refusal.requested_promotion,
            ObserverComparisonAuthorityRequest::PromoteDisagreementToGlobalObstruction
        );
        assert!(!refusal.can_mint_authority());
    }

    #[test]
    fn comparison_packet_rejects_cross_source_without_transport() {
        let left = quotient("left", 1, 2, 3, 4);
        let right = quotient("right", 9, 2, 5, 6);
        let packet = ObserverComparisonPacket::try_from_observer_quotients(
            "cmp1".to_string(),
            &left,
            &right,
            replay(7),
            ObserverComparisonStatus::Incomparable,
        );

        assert!(matches!(
            packet,
            Err(ObserverComparisonError::SourceQuotientMismatch)
        ));
    }

    #[test]
    fn comparison_packet_rejects_cross_carrier_without_transport() {
        let left = quotient("left", 1, 2, 3, 4);
        let right = quotient("right", 1, 9, 5, 6);
        let packet = ObserverComparisonPacket::try_from_observer_quotients(
            "cmp1".to_string(),
            &left,
            &right,
            replay(7),
            ObserverComparisonStatus::Incomparable,
        );

        assert!(matches!(
            packet,
            Err(ObserverComparisonError::CarrierMismatch)
        ));
    }

    #[test]
    fn comparison_packet_requires_comparison_replay() {
        let left = quotient("left", 1, 2, 3, 4);
        let right = quotient("right", 1, 2, 5, 6);
        let packet = ObserverComparisonPacket::try_from_observer_quotients(
            "cmp1".to_string(),
            &left,
            &right,
            replay(0),
            ObserverComparisonStatus::Disagreement,
        );

        assert!(matches!(
            packet,
            Err(ObserverComparisonError::ZeroReplayHash("comparison"))
        ));
    }

    #[test]
    fn comparison_packet_rejects_empty_observer_refs() {
        let packet = ObserverComparisonPacket::new(
            "cmp1".to_string(),
            ObserverRef(String::new()),
            ObserverRef("right".to_string()),
            QuotientSpaceHash(hash(1)),
            CarrierManifestHash(hash(2)),
            EquivalenceRelationHash(hash(3)),
            EquivalenceRelationHash(hash(4)),
            replay(5),
            replay(6),
            replay(7),
            ObserverComparisonStatus::Agreement,
        );

        assert!(matches!(
            packet,
            Err(ObserverComparisonError::EmptyObserverRef("left"))
        ));
    }

    #[test]
    fn comparison_packet_rejects_identical_observers() {
        let left = quotient("left", 1, 2, 3, 4);
        let right = quotient("left", 1, 2, 3, 6);
        let packet = ObserverComparisonPacket::try_from_observer_quotients(
            "cmp1".to_string(),
            &left,
            &right,
            replay(7),
            ObserverComparisonStatus::Agreement,
        );

        assert!(matches!(
            packet,
            Err(ObserverComparisonError::IdenticalObserverComparison)
        ));
    }

    #[test]
    fn comparison_packet_rejects_empty_packet_id() {
        let packet = packet_new(["", "left", "right"], 1, 2, [3, 4], [5, 6, 7]);
        assert!(matches!(
            packet,
            Err(ObserverComparisonError::EmptyPacketId)
        ));
    }

    #[test]
    fn comparison_packet_rejects_empty_right_observer_ref() {
        let packet = packet_new(["cmp1", "left", ""], 1, 2, [3, 4], [5, 6, 7]);
        assert!(matches!(
            packet,
            Err(ObserverComparisonError::EmptyObserverRef("right"))
        ));
    }

    #[test]
    fn comparison_packet_rejects_zero_source_quotient_hash() {
        let packet = packet_new(["cmp1", "left", "right"], 0, 2, [3, 4], [5, 6, 7]);
        assert!(matches!(
            packet,
            Err(ObserverComparisonError::ZeroSourceQuotientHash)
        ));
    }

    #[test]
    fn comparison_packet_rejects_zero_carrier_hash() {
        let packet = packet_new(["cmp1", "left", "right"], 1, 0, [3, 4], [5, 6, 7]);
        assert!(matches!(
            packet,
            Err(ObserverComparisonError::ZeroCarrierHash)
        ));
    }

    #[test]
    fn comparison_packet_rejects_zero_left_equivalence_hash() {
        let packet = packet_new(["cmp1", "left", "right"], 1, 2, [0, 4], [5, 6, 7]);
        assert!(matches!(
            packet,
            Err(ObserverComparisonError::ZeroEquivalenceRelationHash("left"))
        ));
    }

    #[test]
    fn comparison_packet_rejects_zero_right_equivalence_hash() {
        let packet = packet_new(["cmp1", "left", "right"], 1, 2, [3, 0], [5, 6, 7]);
        assert!(matches!(
            packet,
            Err(ObserverComparisonError::ZeroEquivalenceRelationHash(
                "right"
            ))
        ));
    }

    #[test]
    fn comparison_packet_rejects_zero_left_quotient_replay() {
        let packet = packet_new(["cmp1", "left", "right"], 1, 2, [3, 4], [0, 6, 7]);
        assert!(matches!(
            packet,
            Err(ObserverComparisonError::ZeroReplayHash("left quotient"))
        ));
    }

    #[test]
    fn comparison_packet_rejects_zero_right_quotient_replay() {
        let packet = packet_new(["cmp1", "left", "right"], 1, 2, [3, 4], [5, 0, 7]);
        assert!(matches!(
            packet,
            Err(ObserverComparisonError::ZeroReplayHash("right quotient"))
        ));
    }

    #[test]
    fn comparison_packet_refuses_hidden_distinction_recovery() {
        let left = quotient("left", 1, 2, 3, 4);
        let right = quotient("right", 1, 2, 5, 6);
        let packet = ObserverComparisonPacket::try_from_observer_quotients(
            "cmp1".to_string(),
            &left,
            &right,
            replay(7),
            ObserverComparisonStatus::Agreement,
        )
        .unwrap();
        let refusal = packet.refuse_authority_request(
            ObserverComparisonAuthorityRequest::RecoverHiddenDistinctions,
        );

        assert_eq!(refusal.terminal_label(), "ComparisonLaunderingRefused");
        assert_eq!(
            refusal.requested_promotion,
            ObserverComparisonAuthorityRequest::RecoverHiddenDistinctions
        );
        assert_eq!(refusal.authority_effect, "none");
        assert!(!refusal.can_mint_authority());
    }

    #[test]
    fn comparison_packet_refuses_customer_claim() {
        let left = quotient("left", 1, 2, 3, 4);
        let right = quotient("right", 1, 2, 5, 6);
        let packet = ObserverComparisonPacket::try_from_observer_quotients(
            "cmp1".to_string(),
            &left,
            &right,
            replay(7),
            ObserverComparisonStatus::Disagreement,
        )
        .unwrap();
        let refusal =
            packet.refuse_authority_request(ObserverComparisonAuthorityRequest::EmitCustomerClaim);

        assert_eq!(refusal.terminal_label(), "ComparisonLaunderingRefused");
        assert_eq!(
            refusal.requested_promotion,
            ObserverComparisonAuthorityRequest::EmitCustomerClaim
        );
        assert!(!refusal.customer_claim_allowed);
        assert!(!refusal.can_mint_authority());
    }
}
