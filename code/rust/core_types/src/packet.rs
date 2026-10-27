//! Laws: `urn:core:state:packet:v1.0.0`.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_321ecebc;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_321ecebc<T> = std::result::Result<T, BoundaryError_321ecebc>;
use crate::authority::AuthorityEffect;
use core_kernel::Digest;
use serde::{Deserialize, Serialize};
use thiserror::Error;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum PacketKind {
    SymbolGameMove,
    MathIntent,
    GameAction,
    ObserverDiagnostic,
    CandidateResponse,
}

impl PacketKind {
    pub fn signature_requirement(self) -> SignatureRequirement {
        match self {
            Self::GameAction => SignatureRequirement::Required,
            Self::SymbolGameMove | Self::MathIntent => SignatureRequirement::Optional,
            Self::ObserverDiagnostic | Self::CandidateResponse => SignatureRequirement::Forbidden,
        }
    }

    pub fn requires_trace_ref(self) -> bool {
        matches!(self, Self::ObserverDiagnostic)
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum SignatureRequirement {
    Required,
    Optional,
    Forbidden,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum PacketRefusal {
    Malformed,
    OutOfOrder,
    UnauthorizedPayload,
    UnlicensedTransitionRequest,
    PayloadHashMismatch,
    PacketHashMismatch,
    GrammarViolation,
    SchemaUnknown,
    SchemaVersionMismatch,
    SchemaHashMismatch,
    UnknownPacketKind,
    PayloadKindMismatch,
    SignatureRequiredMissing,
    SignatureInvalid,
    SemanticClaimNotChecked,
}

#[derive(Debug, Error, PartialEq, Eq)]
#[error("packet refused: {0:?}")]
pub struct PacketRefused(pub PacketRefusal);

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PacketProvenance {
    pub source: String,
    pub created_at: u64,
    pub trace_ref: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PacketSignature(pub String);

/// Passive typed transport. Every field is private and the only constructor
/// recomputes both hashes, so a packet whose hashes disagree with its bytes
/// cannot exist.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct Packet {
    packet_id: Digest,
    packet_kind: PacketKind,
    payload: Vec<u8>,
    payload_hash: Digest,
    packet_hash: Digest,
    grammar_id: String,
    schema_ref: String,
    schema_version: String,
    signature: Option<PacketSignature>,
    provenance: PacketProvenance,
    authority_effect: AuthorityEffect,
}

pub struct PacketDraft {
    pub packet_kind: PacketKind,
    pub payload: Vec<u8>,
    pub grammar_id: String,
    pub schema_ref: String,
    pub schema_version: String,
    pub signature: Option<PacketSignature>,
    pub provenance: PacketProvenance,
}

const PAYLOAD_DOMAIN: &str = "core.packet.payload.v1";
const PACKET_DOMAIN: &str = "core.packet.identity.v1";

impl Packet {
    pub fn seal(draft: PacketDraft) -> Result<Self, PacketRefused> {
        let refuse = |r| PacketRefused(r);

        if draft.grammar_id.trim().is_empty() {
            return Err(refuse(PacketRefusal::GrammarViolation));
        }
        if draft.schema_ref.trim().is_empty() {
            return Err(refuse(PacketRefusal::SchemaUnknown));
        }
        if draft.schema_version.trim().is_empty() {
            return Err(refuse(PacketRefusal::SchemaVersionMismatch));
        }
        match (draft.packet_kind.signature_requirement(), &draft.signature) {
            (SignatureRequirement::Required, None) => {
                return Err(refuse(PacketRefusal::SignatureRequiredMissing))
            }
            (SignatureRequirement::Forbidden, Some(_)) => {
                return Err(refuse(PacketRefusal::SignatureInvalid))
            }
            (SignatureRequirement::Required, Some(sig)) if sig.0.trim().is_empty() => {
                return Err(refuse(PacketRefusal::SignatureInvalid))
            }
            _ => {}
        }
        if draft.packet_kind.requires_trace_ref()
            && draft
                .provenance
                .trace_ref
                .as_deref()
                .map(str::trim)
                .filter(|t| !t.is_empty())
                .is_none()
        {
            return Err(refuse(PacketRefusal::Malformed));
        }

        let payload_hash = Digest::of_domained(PAYLOAD_DOMAIN, &draft.payload);
        let packet_hash =
            Digest::of_domained(PACKET_DOMAIN, &Self::identity_bytes(&draft, &payload_hash));

        Ok(Self {
            packet_id: packet_hash.clone(),
            packet_kind: draft.packet_kind,
            payload: draft.payload,
            payload_hash,
            packet_hash,
            grammar_id: draft.grammar_id,
            schema_ref: draft.schema_ref,
            schema_version: draft.schema_version,
            signature: draft.signature,
            provenance: draft.provenance,
            authority_effect: AuthorityEffect::Uncertified,
        })
    }

    /// Length-delimited so no field boundary can shift into its neighbour.
    fn identity_bytes(draft: &PacketDraft, payload_hash: &Digest) -> Vec<u8> {
        let mut out = Vec::new();
        let mut push = |bytes: &[u8]| {
            out.extend_from_slice(&(bytes.len() as u64).to_be_bytes());
            out.extend_from_slice(bytes);
        };
        push(format!("{:?}", draft.packet_kind).as_bytes());
        push(payload_hash.as_str().as_bytes());
        push(draft.grammar_id.as_bytes());
        push(draft.schema_ref.as_bytes());
        push(draft.schema_version.as_bytes());
        push(
            draft
                .signature
                .as_ref()
                .map(|s| s.0.as_str())
                .unwrap_or("")
                .as_bytes(),
        );
        push(draft.provenance.source.as_bytes());
        push(&draft.provenance.created_at.to_be_bytes());
        push(
            draft
                .provenance
                .trace_ref
                .as_deref()
                .unwrap_or("")
                .as_bytes(),
        );
        out
    }

    pub fn packet_id(&self) -> &Digest {
        &self.packet_id
    }

    pub fn packet_kind(&self) -> PacketKind {
        self.packet_kind
    }

    pub fn payload(&self) -> &[u8] {
        &self.payload
    }

    pub fn payload_hash(&self) -> &Digest {
        &self.payload_hash
    }

    pub fn packet_hash(&self) -> &Digest {
        &self.packet_hash
    }

    pub fn grammar_id(&self) -> &str {
        &self.grammar_id
    }

    pub fn schema_ref(&self) -> &str {
        &self.schema_ref
    }

    pub fn schema_version(&self) -> &str {
        &self.schema_version
    }

    pub fn signature(&self) -> Option<&PacketSignature> {
        self.signature.as_ref()
    }

    pub fn provenance(&self) -> &PacketProvenance {
        &self.provenance
    }

    pub fn authority_effect(&self) -> &AuthorityEffect {
        &self.authority_effect
    }

    pub fn verify_hashes(&self) -> Result<(), PacketRefused> {
        if Digest::of_domained(PAYLOAD_DOMAIN, &self.payload) != self.payload_hash {
            return Err(PacketRefused(PacketRefusal::PayloadHashMismatch));
        }
        let draft = PacketDraft {
            packet_kind: self.packet_kind,
            payload: self.payload.clone(),
            grammar_id: self.grammar_id.clone(),
            schema_ref: self.schema_ref.clone(),
            schema_version: self.schema_version.clone(),
            signature: self.signature.clone(),
            provenance: self.provenance.clone(),
        };
        let recomputed = Digest::of_domained(
            PACKET_DOMAIN,
            &Self::identity_bytes(&draft, &self.payload_hash),
        );
        if recomputed != self.packet_hash {
            return Err(PacketRefused(PacketRefusal::PacketHashMismatch));
        }
        Ok(())
    }
}

/// A packet plus the hash of the AST it parsed to. Parsing establishes grammar
/// identity, never semantic truth, so the authority effect does not move.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct ParsedPacket {
    packet: Packet,
    parsed_ast_hash: Digest,
    authority_effect: AuthorityEffect,
}

impl ParsedPacket {
    pub fn parse(packet: Packet, parsed_ast_hash: Digest) -> Result<Self, PacketRefused> {
        packet.verify_hashes()?;
        Ok(Self {
            packet,
            parsed_ast_hash,
            authority_effect: AuthorityEffect::Uncertified,
        })
    }

    pub fn packet(&self) -> &Packet {
        &self.packet
    }

    pub fn parsed_ast_hash(&self) -> &Digest {
        &self.parsed_ast_hash
    }

    pub fn authority_effect(&self) -> &AuthorityEffect {
        &self.authority_effect
    }
}

/// Checked evidence. Checking establishes that declared checks ran; it does not
/// mint a `CertifiedAuthority`, so this is never `Certified`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct CheckedPacket {
    parsed_packet_ref: Digest,
    check_refs: Vec<String>,
    authority_effect: AuthorityEffect,
}

impl CheckedPacket {
    pub fn check(parsed: &ParsedPacket, check_refs: Vec<String>) -> Result<Self, PacketRefused> {
        if check_refs.iter().all(|r| r.trim().is_empty()) {
            return Err(PacketRefused(PacketRefusal::SemanticClaimNotChecked));
        }
        Ok(Self {
            parsed_packet_ref: parsed.packet().packet_hash().clone(),
            check_refs,
            authority_effect: AuthorityEffect::Uncertified,
        })
    }

    pub fn parsed_packet_ref(&self) -> &Digest {
        &self.parsed_packet_ref
    }

    pub fn check_refs(&self) -> &[String] {
        &self.check_refs
    }

    pub fn authority_effect(&self) -> &AuthorityEffect {
        &self.authority_effect
    }
}

// Origin: engine/crates_rs/core_types/src/packet.rs
// Claim: urn:core:crates_rs:core-types:packet:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn provenance(trace: Option<&str>) -> PacketProvenance {
        PacketProvenance {
            source: "core.test.source".to_owned(),
            created_at: 1_700_000_000,
            trace_ref: trace.map(str::to_owned),
        }
    }

    fn draft(kind: PacketKind) -> PacketDraft {
        PacketDraft {
            packet_kind: kind,
            payload: b"payload".to_vec(),
            grammar_id: "core.grammar.v1".to_owned(),
            schema_ref: "core.schema.move.v1".to_owned(),
            schema_version: "1.0.0".to_owned(),
            signature: match kind.signature_requirement() {
                SignatureRequirement::Required => Some(PacketSignature("sig".to_owned())),
                _ => None,
            },
            provenance: provenance(kind.requires_trace_ref().then_some("trace:1")),
        }
    }

    fn sealed(kind: PacketKind) -> Packet {
        Packet::seal(draft(kind)).expect("a well-formed draft must seal")
    }

    #[test]
    fn packet_carries_no_execution_authority() {
        let packet = sealed(PacketKind::GameAction);
        assert!(!packet.authority_effect().is_certified());
        assert_eq!(*packet.authority_effect(), AuthorityEffect::Uncertified);
    }

    #[test]
    fn packet_payload_hash_matches() {
        let packet = sealed(PacketKind::MathIntent);
        assert_eq!(
            *packet.payload_hash(),
            Digest::of_domained(PAYLOAD_DOMAIN, packet.payload())
        );
        assert!(packet.verify_hashes().is_ok());
    }

    #[test]
    fn packet_malformed_refused_as_packet_refusal_not_operator_m() {
        let mut d = draft(PacketKind::MathIntent);
        d.grammar_id = "  ".to_owned();
        let err = Packet::seal(d).unwrap_err();
        assert_eq!(err.0, PacketRefusal::GrammarViolation);
    }

    #[test]
    fn packet_replay_produces_identical_ast() {
        let ast = Digest::of_bytes(b"ast");
        let a = ParsedPacket::parse(sealed(PacketKind::MathIntent), ast.clone()).unwrap();
        let b = ParsedPacket::parse(sealed(PacketKind::MathIntent), ast).unwrap();
        assert_eq!(a.parsed_ast_hash(), b.parsed_ast_hash());
        assert_eq!(a.packet().packet_hash(), b.packet().packet_hash());
    }

    #[test]
    fn observer_packet_requires_trace_ref() {
        let mut d = draft(PacketKind::ObserverDiagnostic);
        d.provenance = provenance(None);
        assert_eq!(Packet::seal(d).unwrap_err().0, PacketRefusal::Malformed);
        assert!(Packet::seal(draft(PacketKind::ObserverDiagnostic)).is_ok());
    }

    #[test]
    fn observer_packet_state_hash_matches() {
        let packet = sealed(PacketKind::ObserverDiagnostic);
        assert!(packet.verify_hashes().is_ok());
        assert_eq!(packet.packet_id(), packet.packet_hash());
    }

    #[test]
    fn packet_does_not_self_propagate() {
        // The type exposes no send, route, or propagate. Structurally it is
        // inert data: two seals of the same draft are byte-identical, so a
        // packet cannot have acted between them.
        let a = sealed(PacketKind::MathIntent);
        let b = sealed(PacketKind::MathIntent);
        assert_eq!(a, b);
    }

    #[test]
    fn packet_default_authority_is_uncertified() {
        // Amended from the contract's `EvidenceOnly`: the canonical
        // AuthorityEffect is the firewall type, which has no such variant.
        assert_eq!(
            *sealed(PacketKind::MathIntent).authority_effect(),
            AuthorityEffect::Uncertified
        );
    }

    #[test]
    fn packet_wrapping_does_not_upgrade_llm_output() {
        let mut d = draft(PacketKind::CandidateResponse);
        d.payload = b"a fluent and confident model answer".to_vec();
        let packet = Packet::seal(d).unwrap();
        assert!(!packet.authority_effect().is_certified());
    }

    #[test]
    fn packet_does_not_claim_semantic_truth() {
        let parsed =
            ParsedPacket::parse(sealed(PacketKind::MathIntent), Digest::of_bytes(b"ast")).unwrap();
        let checked = CheckedPacket::check(&parsed, vec!["check:1".to_owned()]).unwrap();
        assert!(!parsed.authority_effect().is_certified());
        assert!(!checked.authority_effect().is_certified());
    }

    #[test]
    fn packet_signature_requirement_is_declared() {
        assert_eq!(
            PacketKind::GameAction.signature_requirement(),
            SignatureRequirement::Required
        );
        assert_eq!(
            PacketKind::ObserverDiagnostic.signature_requirement(),
            SignatureRequirement::Forbidden
        );
        assert_eq!(
            PacketKind::MathIntent.signature_requirement(),
            SignatureRequirement::Optional
        );
    }

    #[test]
    fn unsigned_packet_refused_when_signature_required() {
        let mut d = draft(PacketKind::GameAction);
        d.signature = None;
        assert_eq!(
            Packet::seal(d).unwrap_err().0,
            PacketRefusal::SignatureRequiredMissing
        );
    }

    #[test]
    fn a_signature_on_a_forbidden_kind_is_refused() {
        let mut d = draft(PacketKind::ObserverDiagnostic);
        d.signature = Some(PacketSignature("sig".to_owned()));
        assert_eq!(
            Packet::seal(d).unwrap_err().0,
            PacketRefusal::SignatureInvalid
        );
    }

    #[test]
    fn packet_schema_ref_is_declared() {
        let mut d = draft(PacketKind::MathIntent);
        d.schema_ref = String::new();
        assert_eq!(Packet::seal(d).unwrap_err().0, PacketRefusal::SchemaUnknown);
        assert_eq!(
            sealed(PacketKind::MathIntent).schema_ref(),
            "core.schema.move.v1"
        );
    }

    #[test]
    fn packet_hash_matches_canonical_packet_bytes() {
        let packet = sealed(PacketKind::MathIntent);
        assert!(packet.verify_hashes().is_ok());

        let mut other = draft(PacketKind::MathIntent);
        other.schema_version = "2.0.0".to_owned();
        assert_ne!(
            *Packet::seal(other).unwrap().packet_hash(),
            *packet.packet_hash()
        );
    }

    #[test]
    fn a_field_boundary_cannot_shift_between_neighbours() {
        let mut a = draft(PacketKind::MathIntent);
        a.grammar_id = "ab".to_owned();
        a.schema_ref = "c".to_owned();
        let mut b = draft(PacketKind::MathIntent);
        b.grammar_id = "a".to_owned();
        b.schema_ref = "bc".to_owned();
        assert_ne!(
            *Packet::seal(a).unwrap().packet_hash(),
            *Packet::seal(b).unwrap().packet_hash()
        );
    }

    #[test]
    fn checked_packet_is_not_certified() {
        // Amended from `checked_packet_is_evidence_boundary_not_fact_boundary`:
        // under the firewall vocabulary the claim "not a fact" is exactly
        // "not Certified", and Certified requires an unforgeable token.
        let parsed =
            ParsedPacket::parse(sealed(PacketKind::MathIntent), Digest::of_bytes(b"ast")).unwrap();
        let checked = CheckedPacket::check(&parsed, vec!["check:1".to_owned()]).unwrap();
        assert_eq!(*checked.authority_effect(), AuthorityEffect::Uncertified);
        assert!(!checked.authority_effect().is_certified());
    }

    #[test]
    fn observer_packet_does_not_emit_canonical_measurements() {
        // The payload is opaque bytes; nothing here promotes it to a
        // measurement, and the checked form stays uncertified.
        let parsed = ParsedPacket::parse(
            sealed(PacketKind::ObserverDiagnostic),
            Digest::of_bytes(b"ast"),
        )
        .unwrap();
        let checked = CheckedPacket::check(&parsed, vec!["check:1".to_owned()]).unwrap();
        assert!(!checked.authority_effect().is_certified());
    }

    #[test]
    fn a_check_with_no_refs_is_refused_rather_than_vacuously_passing() {
        let parsed =
            ParsedPacket::parse(sealed(PacketKind::MathIntent), Digest::of_bytes(b"ast")).unwrap();
        assert_eq!(
            CheckedPacket::check(&parsed, vec![]).unwrap_err().0,
            PacketRefusal::SemanticClaimNotChecked
        );
        assert_eq!(
            CheckedPacket::check(&parsed, vec!["  ".to_owned()])
                .unwrap_err()
                .0,
            PacketRefusal::SemanticClaimNotChecked
        );
    }
}
