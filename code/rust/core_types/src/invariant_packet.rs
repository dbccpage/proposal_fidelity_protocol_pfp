//! Invariant atlas packets.
//!
//! `InvariantPacket` makes the invariant atlas first-class without granting
//! authority. It names what is measured, how preservation is expected, what
//! operator behavior is sensitive to it, which witness protocol applies, and
//! the typed refusal condition when the packet is incomplete.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_37b9b0f2;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_37b9b0f2<T> = std::result::Result<T, BoundaryError_37b9b0f2>;
use serde::{Deserialize, Serialize};
use thiserror::Error;

/// Tower layers.
///
/// The seven CODA layer papers took collision-proof `paper_identity` values on
/// 2026-07-28 (`GTFOC` -> `CODA-FOC`, …). The general layered-authority theory is the
/// `CodaGtla` variant, serialized as `GTLA`. These wire names are the **serde wire format** and are
/// embedded in golden fixtures under `core_sweep_kernel/tests/fixtures/` and in the
/// contract corpus, so the identifiers are deliberately NOT renamed — and `CODA-FOC` is
/// not a legal Rust identifier in any case.
///
/// Each variant instead carries a serde `alias`, so a packet written with the new
/// spelling deserializes, while everything this crate *emits* stays byte-identical to
/// every fixture already on disk. Switching emission to the new spelling is a one-line
/// change (`alias` -> `rename`) plus a fixture migration; that is deliberately not done
/// here.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum InvariantLayer {
    #[serde(rename = "GTLA")]
    CodaGtla,
    #[serde(alias = "CODA-FOC")]
    GTFOC,
    #[serde(alias = "CODA-FDA")]
    GTFDA,
    #[serde(alias = "CODA-MUR")]
    GTMUR,
    #[serde(alias = "CODA-OR")]
    GTOR,
    #[serde(alias = "CODA-CS")]
    GTTC,
    #[serde(alias = "CODA-A")]
    GTTA,
    Product,
}

// Origin: engine/crates_rs/core_types/src/invariant_packet.rs
// Claim: urn:core:crates_rs:core-types:invariant-packet:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod invariant_layer_alias_tests {
    use super::InvariantLayer;

    #[test]
    fn new_coda_spelling_deserializes_to_the_same_variant() {
        for (spelling, expected) in [
            ("\"CODA-FOC\"", InvariantLayer::GTFOC),
            ("\"CODA-FDA\"", InvariantLayer::GTFDA),
            ("\"CODA-MUR\"", InvariantLayer::GTMUR),
            ("\"CODA-OR\"", InvariantLayer::GTOR),
            ("\"CODA-CS\"", InvariantLayer::GTTC),
            ("\"CODA-A\"", InvariantLayer::GTTA),
        ] {
            let got: InvariantLayer = serde_json::from_str(spelling).unwrap();
            assert_eq!(got, expected, "{spelling} must map to {expected:?}");
        }
    }

    #[test]
    fn legacy_gt_spelling_still_deserializes() {
        let got: InvariantLayer = serde_json::from_str("\"GTFOC\"").unwrap();
        assert_eq!(got, InvariantLayer::GTFOC);
    }

    #[test]
    fn emission_is_unchanged_so_golden_fixtures_stay_valid() {
        // The whole point of alias-not-rename: what we WRITE must not move.
        assert_eq!(
            serde_json::to_string(&InvariantLayer::GTFOC).unwrap(),
            "\"GTFOC\""
        );
        assert_eq!(
            serde_json::to_string(&InvariantLayer::GTTA).unwrap(),
            "\"GTTA\""
        );
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum InvariantPacketError {
    #[error("missing carrier")]
    MissingCarrier,
    #[error("missing value object")]
    MissingValueObject,
    #[error("missing invariant map")]
    MissingInvariantMap,
    #[error("missing preservation law")]
    MissingPreservationLaw,
    #[error("missing operator sensitivity")]
    MissingOperatorSensitivity,
    #[error("missing witness protocol")]
    MissingWitnessProtocol,
    #[error("missing refusal condition")]
    MissingRefusalCondition,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(try_from = "RawInvariantPacket")]
pub struct InvariantPacket {
    layer: InvariantLayer,
    carrier: String,
    value_object: String,
    invariant_map: String,
    preservation_law: String,
    operator_sensitivity: String,
    witness_protocol: String,
    certificate_required: bool,
    refusal_condition: String,
}

#[derive(Deserialize)]
struct RawInvariantPacket {
    layer: InvariantLayer,
    carrier: String,
    value_object: String,
    invariant_map: String,
    preservation_law: String,
    operator_sensitivity: String,
    witness_protocol: String,
    certificate_required: bool,
    refusal_condition: String,
}

impl TryFrom<RawInvariantPacket> for InvariantPacket {
    type Error = InvariantPacketError;

    fn try_from(raw: RawInvariantPacket) -> Result<Self, Self::Error> {
        InvariantPacket::new(
            raw.layer,
            raw.carrier,
            raw.value_object,
            raw.invariant_map,
            raw.preservation_law,
            raw.operator_sensitivity,
            raw.witness_protocol,
            raw.certificate_required,
            raw.refusal_condition,
        )
    }
}

impl InvariantPacket {
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        layer: InvariantLayer,
        carrier: impl Into<String>,
        value_object: impl Into<String>,
        invariant_map: impl Into<String>,
        preservation_law: impl Into<String>,
        operator_sensitivity: impl Into<String>,
        witness_protocol: impl Into<String>,
        certificate_required: bool,
        refusal_condition: impl Into<String>,
    ) -> Result<Self, InvariantPacketError> {
        let carrier = require_nonempty(carrier, InvariantPacketError::MissingCarrier)?;
        let value_object =
            require_nonempty(value_object, InvariantPacketError::MissingValueObject)?;
        let invariant_map =
            require_nonempty(invariant_map, InvariantPacketError::MissingInvariantMap)?;
        let preservation_law = require_nonempty(
            preservation_law,
            InvariantPacketError::MissingPreservationLaw,
        )?;
        let operator_sensitivity = require_nonempty(
            operator_sensitivity,
            InvariantPacketError::MissingOperatorSensitivity,
        )?;
        let witness_protocol = require_nonempty(
            witness_protocol,
            InvariantPacketError::MissingWitnessProtocol,
        )?;
        let refusal_condition = require_nonempty(
            refusal_condition,
            InvariantPacketError::MissingRefusalCondition,
        )?;

        Ok(Self {
            layer,
            carrier,
            value_object,
            invariant_map,
            preservation_law,
            operator_sensitivity,
            witness_protocol,
            certificate_required,
            refusal_condition,
        })
    }

    pub fn layer(&self) -> InvariantLayer {
        self.layer
    }

    pub fn invariant_id(&self) -> &str {
        &self.invariant_map
    }

    pub fn carrier(&self) -> &str {
        &self.carrier
    }

    pub fn carrier_type(&self) -> &str {
        &self.carrier
    }

    pub fn value_object(&self) -> &str {
        &self.value_object
    }

    pub fn invariant_map(&self) -> &str {
        &self.invariant_map
    }

    pub fn preservation_law(&self) -> &str {
        &self.preservation_law
    }

    pub fn operator_sensitivity(&self) -> &str {
        &self.operator_sensitivity
    }

    pub fn witness_protocol(&self) -> &str {
        &self.witness_protocol
    }

    pub fn witness_protocol_id(&self) -> &str {
        &self.witness_protocol
    }

    pub fn certificate_required(&self) -> bool {
        self.certificate_required
    }

    pub fn refusal_condition(&self) -> &str {
        &self.refusal_condition
    }
}

fn require_nonempty(
    value: impl Into<String>,
    error: InvariantPacketError,
) -> Result<String, InvariantPacketError> {
    let value = value.into();
    let value = value.trim().to_string();
    if value.is_empty() {
        Err(error)
    } else {
        Ok(value)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn complete_invariant_packet_constructs() {
        let packet = InvariantPacket::new(
            InvariantLayer::GTFOC,
            "finite cochain carrier",
            "weighted quotient norm",
            "Phi1",
            "exact repair preserves quotient value",
            "E preserves, I preserves under isometry, M destroys",
            "primal-dual replay certificate",
            true,
            "Phi1CertificateMissing",
        )
        .expect("complete invariant packet");

        assert_eq!(packet.layer(), InvariantLayer::GTFOC);
        assert!(packet.certificate_required());
        assert_eq!(packet.invariant_id(), "Phi1");
        assert_eq!(packet.carrier_type(), "finite cochain carrier");
        assert_eq!(packet.invariant_map(), "Phi1");
        assert_eq!(
            packet.witness_protocol_id(),
            "primal-dual replay certificate"
        );
    }

    #[test]
    fn missing_invariant_witness_protocol_refuses() {
        assert_eq!(
            InvariantPacket::new(
                InvariantLayer::GTFOC,
                "finite cochain carrier",
                "weighted quotient norm",
                "Phi1",
                "exact repair preserves quotient value",
                "E preserves, I preserves under isometry, M destroys",
                "",
                true,
                "Phi1CertificateMissing",
            )
            .unwrap_err(),
            InvariantPacketError::MissingWitnessProtocol
        );
    }

    #[test]
    fn deserialization_rejects_invalid_packets() {
        let json_bad_carrier = r#"{"layer":"GTFOC","carrier":"   ","value_object":"val","invariant_map":"inv","preservation_law":"law","operator_sensitivity":"sens","witness_protocol":"prot","certificate_required":true,"refusal_condition":"cond"}"#;
        let res: Result<InvariantPacket, _> = serde_json::from_str(json_bad_carrier);
        assert!(res.is_err());

        let json_bad_protocol = r#"{"layer":"GTFOC","carrier":"carr","value_object":"val","invariant_map":"inv","preservation_law":"law","operator_sensitivity":"sens","witness_protocol":"   ","certificate_required":true,"refusal_condition":"cond"}"#;
        let res: Result<InvariantPacket, _> = serde_json::from_str(json_bad_protocol);
        assert!(res.is_err());
    }
}
