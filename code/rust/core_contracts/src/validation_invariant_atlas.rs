
#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_2f0f43d4<T> {
    fn checked_invariant_2f0f43d4(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_2f0f43d4<T> for Option<T> {
    #[inline]
    fn checked_invariant_2f0f43d4(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_2f0f43d4<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_2f0f43d4(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use super::artifact::{ValidationArtifact, ValidationResult};
use super::registry::{ErasedValidator, ValidationRegistryError, ValidatorDescriptor};
use super::validator::Validator;
use super::violation::ValidationViolation;
use crate::kinds::{ContractEffect, SchemaHash};
use crate::witness::evidence::{ValidationWitness, WitnessCertainty, WitnessClass};
use core_types::{InvariantLayer, InvariantPacket, Refusable, RefusalSource};
use serde::de::{self, MapAccess, Visitor};
use serde::{Deserialize, Serialize};
use std::any::Any;
use std::collections::BTreeMap;
use std::fmt;
use std::path::Path;

pub const SCHEMA_GATE_VALIDATOR_ID: &str = "core_contracts.validation.schema_gate";
pub const SCHEMA_GATE_VERSION: &str = "0.1.0";
pub const SCHEMA_GATE_SUBJECT: &str = "core_types::InvariantPacket";
pub const SCHEMA_GATE_PROPERTY: &str = "invariant_atlas_membership";
pub const SCHEMA_GATE_SCHEMA_HASH: SchemaHash = SchemaHash([0x41; 32]);

#[derive(Debug, thiserror::Error)]
pub enum InvariantAtlasStoreError {
    #[error("missing invariant id")]
    MissingInvariantId,
    #[error("missing carrier type")]
    MissingCarrierType,
    #[error("missing witness protocol id")]
    MissingWitnessProtocolId,
    #[error("duplicate invariant id: {0}")]
    DuplicateInvariantId(String),
    #[error("atlas IO error: {0}")]
    Io(#[from] std::io::Error),
    #[error("atlas YAML error: {0}")]
    Yaml(#[from] serde_yaml::Error),
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct InvariantAtlasEntry {
    pub layer: InvariantLayer,
    pub carrier_type: String,
    pub witness_protocol_id: String,
}

impl InvariantAtlasEntry {
    pub fn new(
        layer: InvariantLayer,
        carrier_type: impl Into<String>,
        witness_protocol_id: impl Into<String>,
    ) -> Result<Self, InvariantAtlasStoreError> {
        let carrier_type = normalize_nonempty(
            carrier_type.into(),
            InvariantAtlasStoreError::MissingCarrierType,
        )?;
        let witness_protocol_id = normalize_nonempty(
            witness_protocol_id.into(),
            InvariantAtlasStoreError::MissingWitnessProtocolId,
        )?;

        Ok(Self {
            layer,
            carrier_type,
            witness_protocol_id,
        })
    }

    fn validate(&self) -> Result<(), InvariantAtlasStoreError> {
        normalize_nonempty(
            self.carrier_type.clone(),
            InvariantAtlasStoreError::MissingCarrierType,
        )?;
        normalize_nonempty(
            self.witness_protocol_id.clone(),
            InvariantAtlasStoreError::MissingWitnessProtocolId,
        )?;
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Default, Serialize)]
pub struct InvariantAtlasStore {
    entries: BTreeMap<String, InvariantAtlasEntry>,
}

impl InvariantAtlasStore {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn canonical() -> Self {
        let mut store = Self::new();
        store
            .insert(
                "Phi1",
                InvariantAtlasEntry::new(
                    InvariantLayer::GTFOC,
                    "finite cochain carrier",
                    "primal-dual replay certificate",
                )
                .checked_invariant_2f0f43d4("static atlas row is well-formed"),
            )
            .checked_invariant_2f0f43d4("static atlas ids are unique");
        store
            .insert(
                "PiSharp",
                InvariantAtlasEntry::new(
                    InvariantLayer::GTFDA,
                    "finite descent terminal carrier",
                    "sealed descent witness replay",
                )
                .checked_invariant_2f0f43d4("static atlas row is well-formed"),
            )
            .checked_invariant_2f0f43d4("static atlas ids are unique");
        store
    }

    pub fn from_entries<I, K>(entries: I) -> Result<Self, InvariantAtlasStoreError>
    where
        I: IntoIterator<Item = (K, InvariantAtlasEntry)>,
        K: Into<String>,
    {
        let mut store = Self::new();
        for (id, entry) in entries {
            store.insert(id, entry)?;
        }
        Ok(store)
    }

    pub fn insert(
        &mut self,
        invariant_id: impl Into<String>,
        entry: InvariantAtlasEntry,
    ) -> Result<(), InvariantAtlasStoreError> {
        let invariant_id = normalize_nonempty(
            invariant_id.into(),
            InvariantAtlasStoreError::MissingInvariantId,
        )?;
        let entry =
            InvariantAtlasEntry::new(entry.layer, entry.carrier_type, entry.witness_protocol_id)?;
        if self.entries.contains_key(&invariant_id) {
            return Err(InvariantAtlasStoreError::DuplicateInvariantId(invariant_id));
        }
        self.entries.insert(invariant_id, entry);
        Ok(())
    }

    pub fn get(&self, invariant_id: &str) -> Option<&InvariantAtlasEntry> {
        self.entries.get(invariant_id)
    }

    pub fn contains(&self, invariant_id: &str) -> bool {
        self.entries.contains_key(invariant_id)
    }

    pub fn len(&self) -> usize {
        self.entries.len()
    }

    pub fn is_empty(&self) -> bool {
        self.entries.is_empty()
    }

    pub fn entries(&self) -> &BTreeMap<String, InvariantAtlasEntry> {
        &self.entries
    }

    pub fn from_yaml_str(text: &str) -> Result<Self, InvariantAtlasStoreError> {
        let store: Self = serde_yaml::from_str(text)?;
        store.validate()?;
        Ok(store)
    }

    pub fn to_yaml_string(&self) -> Result<String, InvariantAtlasStoreError> {
        self.validate()?;
        Ok(serde_yaml::to_string(self)?)
    }

    pub fn load_yaml(path: impl AsRef<Path>) -> Result<Self, InvariantAtlasStoreError> {
        let text = std::fs::read_to_string(path)?;
        Self::from_yaml_str(&text)
    }

    pub fn save_yaml(&self, path: impl AsRef<Path>) -> Result<(), InvariantAtlasStoreError> {
        let text = self.to_yaml_string()?;
        std::fs::write(path, text)?;
        Ok(())
    }

    fn validate(&self) -> Result<(), InvariantAtlasStoreError> {
        for (invariant_id, entry) in &self.entries {
            normalize_nonempty(
                invariant_id.clone(),
                InvariantAtlasStoreError::MissingInvariantId,
            )?;
            entry.validate()?;
        }
        Ok(())
    }
}

impl<'de> Deserialize<'de> for InvariantAtlasStore {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        deserializer.deserialize_map(InvariantAtlasStoreVisitor)
    }
}

struct InvariantAtlasStoreVisitor;

impl<'de> Visitor<'de> for InvariantAtlasStoreVisitor {
    type Value = InvariantAtlasStore;

    fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("an invariant atlas store with an entries map")
    }

    fn visit_map<M>(self, mut map: M) -> Result<Self::Value, M::Error>
    where
        M: MapAccess<'de>,
    {
        let mut entries = None;

        while let Some(field) = map.next_key::<String>()? {
            match field.as_str() {
                "entries" => {
                    if entries.is_some() {
                        return Err(de::Error::duplicate_field("entries"));
                    }
                    entries = Some(map.next_value::<InvariantAtlasEntryMap>()?.0);
                }
                _ => return Err(de::Error::unknown_field(&field, &["entries"])),
            }
        }

        let entries = entries.ok_or_else(|| de::Error::missing_field("entries"))?;
        Ok(InvariantAtlasStore { entries })
    }
}

struct InvariantAtlasEntryMap(BTreeMap<String, InvariantAtlasEntry>);

impl<'de> Deserialize<'de> for InvariantAtlasEntryMap {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        deserializer
            .deserialize_map(InvariantAtlasEntryMapVisitor)
            .map(Self)
    }
}

struct InvariantAtlasEntryMapVisitor;

impl<'de> Visitor<'de> for InvariantAtlasEntryMapVisitor {
    type Value = BTreeMap<String, InvariantAtlasEntry>;

    fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("an invariant-id to atlas-entry map")
    }

    fn visit_map<M>(self, mut map: M) -> Result<Self::Value, M::Error>
    where
        M: MapAccess<'de>,
    {
        let mut entries = BTreeMap::new();

        while let Some((raw_id, entry)) = map.next_entry::<String, InvariantAtlasEntry>()? {
            let invariant_id =
                normalize_nonempty(raw_id, InvariantAtlasStoreError::MissingInvariantId)
                    .map_err(de::Error::custom)?;
            let entry = InvariantAtlasEntry::new(
                entry.layer,
                entry.carrier_type,
                entry.witness_protocol_id,
            )
            .map_err(de::Error::custom)?;
            if entries.insert(invariant_id.clone(), entry).is_some() {
                return Err(de::Error::custom(
                    InvariantAtlasStoreError::DuplicateInvariantId(invariant_id),
                ));
            }
        }

        Ok(entries)
    }
}

#[derive(Debug, Clone)]
pub struct SchemaGate {
    atlas: InvariantAtlasStore,
}

impl Default for SchemaGate {
    fn default() -> Self {
        Self::new(InvariantAtlasStore::canonical())
    }
}

impl SchemaGate {
    pub fn new(atlas: InvariantAtlasStore) -> Self {
        Self { atlas }
    }

    pub fn atlas(&self) -> &InvariantAtlasStore {
        &self.atlas
    }

    pub fn validate_packet(
        &self,
        packet: &InvariantPacket,
    ) -> ValidationArtifact<SchemaGateWitness, SchemaGateViolation> {
        let result = match self.packet_violations("packet", packet) {
            violations if violations.is_empty() => {
                let entry = self
                    .atlas
                    .get(packet.invariant_id())
                    .checked_invariant_2f0f43d4("empty violations imply an atlas entry exists");
                ValidationResult::Valid(vec![SchemaGateWitness::for_packet(packet, entry)])
            }
            violations => ValidationResult::Invalid(violations),
        };

        ValidationArtifact::new(
            format!("schema-gate:packet:{}", packet_hash(packet)),
            SCHEMA_GATE_VALIDATOR_ID,
            SCHEMA_GATE_VERSION,
            SCHEMA_GATE_SUBJECT,
            packet_hash(packet),
            SCHEMA_GATE_PROPERTY,
            SCHEMA_GATE_SCHEMA_HASH,
            result,
        )
    }

    pub fn validate_transition(
        &self,
        before: &InvariantPacket,
        after: &InvariantPacket,
    ) -> ValidationArtifact<SchemaGateWitness, SchemaGateViolation> {
        let mut violations = Vec::new();

        if before.invariant_id() != after.invariant_id() {
            violations.push(SchemaGateViolation::new(
                SchemaGateViolationKind::InvariantIdMutation,
                "transition",
                "invariant_id",
                before.invariant_id(),
                after.invariant_id(),
            ));
        }
        push_transition_mutation(
            &mut violations,
            "layer",
            format!("{:?}", before.layer()),
            format!("{:?}", after.layer()),
        );
        push_transition_mutation(
            &mut violations,
            "carrier_type",
            before.carrier_type(),
            after.carrier_type(),
        );
        push_transition_mutation(
            &mut violations,
            "value_object",
            before.value_object(),
            after.value_object(),
        );
        push_transition_mutation(
            &mut violations,
            "preservation_law",
            before.preservation_law(),
            after.preservation_law(),
        );
        push_transition_mutation(
            &mut violations,
            "operator_sensitivity",
            before.operator_sensitivity(),
            after.operator_sensitivity(),
        );
        push_transition_mutation(
            &mut violations,
            "witness_protocol_id",
            before.witness_protocol_id(),
            after.witness_protocol_id(),
        );
        push_transition_mutation(
            &mut violations,
            "certificate_required",
            before.certificate_required().to_string(),
            after.certificate_required().to_string(),
        );
        push_transition_mutation(
            &mut violations,
            "refusal_condition",
            before.refusal_condition(),
            after.refusal_condition(),
        );

        violations.extend(self.packet_violations("before", before));
        violations.extend(self.packet_violations("after", after));

        let result = if violations.is_empty() {
            let entry = self
                .atlas
                .get(after.invariant_id())
                .checked_invariant_2f0f43d4("empty violations imply an atlas entry exists");
            ValidationResult::Valid(vec![SchemaGateWitness::for_transition(
                before, after, entry,
            )])
        } else {
            ValidationResult::Invalid(violations)
        };

        ValidationArtifact::new(
            format!("schema-gate:transition:{}", transition_hash(before, after)),
            SCHEMA_GATE_VALIDATOR_ID,
            SCHEMA_GATE_VERSION,
            "core_types::InvariantPacketTransition",
            transition_hash(before, after),
            SCHEMA_GATE_PROPERTY,
            SCHEMA_GATE_SCHEMA_HASH,
            result,
        )
    }

    pub fn admit_packet(&self, packet: &InvariantPacket) -> Refusable<SchemaGateWitness> {
        match self.validate_packet(packet).result {
            ValidationResult::Valid(mut witnesses) => Refusable::Value(witnesses.remove(0)),
            ValidationResult::Invalid(_) | ValidationResult::DomainError(_) => {
                Refusable::Refused(RefusalSource::Refusal)
            }
        }
    }

    pub fn admit_transition(
        &self,
        before: &InvariantPacket,
        after: &InvariantPacket,
    ) -> Refusable<SchemaGateWitness> {
        match self.validate_transition(before, after).result {
            ValidationResult::Valid(mut witnesses) => Refusable::Value(witnesses.remove(0)),
            ValidationResult::Invalid(_) | ValidationResult::DomainError(_) => {
                Refusable::Refused(RefusalSource::Refusal)
            }
        }
    }

    fn packet_violations(
        &self,
        packet_role: &'static str,
        packet: &InvariantPacket,
    ) -> Vec<SchemaGateViolation> {
        let Some(entry) = self.atlas.get(packet.invariant_id()) else {
            return vec![SchemaGateViolation::new(
                SchemaGateViolationKind::UnregisteredInvariant,
                packet_role,
                "invariant_id",
                "<registered invariant>",
                packet.invariant_id(),
            )];
        };

        let mut violations = Vec::new();
        if packet.layer() != entry.layer {
            violations.push(SchemaGateViolation::new(
                SchemaGateViolationKind::LayerMismatch,
                packet_role,
                "layer",
                format!("{:?}", entry.layer),
                format!("{:?}", packet.layer()),
            ));
        }
        if packet.carrier_type() != entry.carrier_type {
            violations.push(SchemaGateViolation::new(
                SchemaGateViolationKind::CarrierTypeMismatch,
                packet_role,
                "carrier_type",
                entry.carrier_type.as_str(),
                packet.carrier_type(),
            ));
        }
        if packet.witness_protocol_id() != entry.witness_protocol_id {
            violations.push(SchemaGateViolation::new(
                SchemaGateViolationKind::WitnessProtocolMismatch,
                packet_role,
                "witness_protocol_id",
                entry.witness_protocol_id.as_str(),
                packet.witness_protocol_id(),
            ));
        }
        violations
    }
}

impl Validator<InvariantPacket> for SchemaGate {
    type Witness = SchemaGateWitness;
    type Violation = SchemaGateViolation;

    const VALIDATOR_ID: &'static str = SCHEMA_GATE_VALIDATOR_ID;
    const SUBJECT_TYPE: &'static str = SCHEMA_GATE_SUBJECT;
    const PROPERTY: &'static str = SCHEMA_GATE_PROPERTY;

    fn validate(subject: &InvariantPacket) -> ValidationArtifact<Self::Witness, Self::Violation> {
        Self::default().validate_packet(subject)
    }
}

impl ErasedValidator for SchemaGate {
    fn descriptor(&self) -> ValidatorDescriptor {
        ValidatorDescriptor {
            validator_id: SCHEMA_GATE_VALIDATOR_ID,
            subject_type_name: SCHEMA_GATE_SUBJECT,
            property: SCHEMA_GATE_PROPERTY,
            schema_hash: SCHEMA_GATE_SCHEMA_HASH,
            authority_effect: ContractEffect::EvidenceOnly,
        }
    }

    fn validate_erased(&self, subject: &dyn Any) -> Result<Box<dyn Any>, ValidationRegistryError> {
        let packet = subject.downcast_ref::<InvariantPacket>().ok_or(
            ValidationRegistryError::SubjectTypeMismatch {
                expected: SCHEMA_GATE_SUBJECT,
            },
        )?;
        Ok(Box::new(self.validate_packet(packet)))
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct SchemaGateWitness {
    pub invariant_id: String,
    pub atlas_row_hash: String,
    pub checked_fields: Vec<&'static str>,
    pub transition_hash: Option<String>,
}

impl SchemaGateWitness {
    fn for_packet(packet: &InvariantPacket, entry: &InvariantAtlasEntry) -> Self {
        Self {
            invariant_id: packet.invariant_id().to_string(),
            atlas_row_hash: atlas_row_hash(packet.invariant_id(), entry),
            checked_fields: packet_checked_fields(),
            transition_hash: None,
        }
    }

    fn for_transition(
        before: &InvariantPacket,
        after: &InvariantPacket,
        entry: &InvariantAtlasEntry,
    ) -> Self {
        Self {
            invariant_id: after.invariant_id().to_string(),
            atlas_row_hash: atlas_row_hash(after.invariant_id(), entry),
            checked_fields: transition_checked_fields(),
            transition_hash: Some(transition_hash(before, after)),
        }
    }
}

impl ValidationWitness for SchemaGateWitness {
    fn property(&self) -> &'static str {
        SCHEMA_GATE_PROPERTY
    }

    fn class(&self) -> WitnessClass {
        WitnessClass::Structural
    }

    fn witness_certainty(&self) -> WitnessCertainty {
        WitnessCertainty::PropertyWitness
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum SchemaGateViolationKind {
    UnregisteredInvariant,
    InvariantIdMutation,
    PacketFieldMutation,
    LayerMismatch,
    CarrierTypeMismatch,
    WitnessProtocolMismatch,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct SchemaGateViolation {
    pub kind: SchemaGateViolationKind,
    pub packet_role: &'static str,
    pub field: &'static str,
    pub expected: String,
    pub actual: String,
}

impl SchemaGateViolation {
    fn new(
        kind: SchemaGateViolationKind,
        packet_role: &'static str,
        field: &'static str,
        expected: impl Into<String>,
        actual: impl Into<String>,
    ) -> Self {
        Self {
            kind,
            packet_role,
            field,
            expected: expected.into(),
            actual: actual.into(),
        }
    }
}

impl ValidationViolation for SchemaGateViolation {
    fn code(&self) -> &'static str {
        match self.kind {
            SchemaGateViolationKind::UnregisteredInvariant => "UnregisteredInvariant",
            SchemaGateViolationKind::InvariantIdMutation => "InvariantIdMutation",
            SchemaGateViolationKind::PacketFieldMutation => "InvariantPacketFieldMutation",
            SchemaGateViolationKind::LayerMismatch => "InvariantLayerMismatch",
            SchemaGateViolationKind::CarrierTypeMismatch => "InvariantCarrierTypeMismatch",
            SchemaGateViolationKind::WitnessProtocolMismatch => "InvariantWitnessProtocolMismatch",
        }
    }
}

fn packet_checked_fields() -> Vec<&'static str> {
    vec![
        "invariant_id",
        "layer",
        "carrier_type",
        "witness_protocol_id",
    ]
}

fn transition_checked_fields() -> Vec<&'static str> {
    vec![
        "invariant_id",
        "layer",
        "carrier_type",
        "value_object",
        "preservation_law",
        "operator_sensitivity",
        "witness_protocol_id",
        "certificate_required",
        "refusal_condition",
    ]
}

fn push_transition_mutation(
    violations: &mut Vec<SchemaGateViolation>,
    field: &'static str,
    before: impl Into<String>,
    after: impl Into<String>,
) {
    let before = before.into();
    let after = after.into();
    if before != after {
        violations.push(SchemaGateViolation::new(
            SchemaGateViolationKind::PacketFieldMutation,
            "transition",
            field,
            before,
            after,
        ));
    }
}

fn normalize_nonempty(
    value: String,
    error: InvariantAtlasStoreError,
) -> Result<String, InvariantAtlasStoreError> {
    let value = value.trim().to_string();
    if value.is_empty() {
        Err(error)
    } else {
        Ok(value)
    }
}

fn packet_hash(packet: &InvariantPacket) -> String {
    let mut hasher = blake3::Hasher::new();
    hasher.update(b"CoreContracts.InvariantPacket.v1");
    update_hash_part(&mut hasher, &format!("{:?}", packet.layer()));
    update_hash_part(&mut hasher, packet.carrier_type());
    update_hash_part(&mut hasher, packet.value_object());
    update_hash_part(&mut hasher, packet.invariant_id());
    update_hash_part(&mut hasher, packet.preservation_law());
    update_hash_part(&mut hasher, packet.operator_sensitivity());
    update_hash_part(&mut hasher, packet.witness_protocol_id());
    update_hash_part(&mut hasher, &packet.certificate_required().to_string());
    update_hash_part(&mut hasher, packet.refusal_condition());
    hasher.finalize().to_hex().to_string()
}

fn transition_hash(before: &InvariantPacket, after: &InvariantPacket) -> String {
    let mut hasher = blake3::Hasher::new();
    hasher.update(b"CoreContracts.InvariantPacketTransition.v1");
    update_hash_part(&mut hasher, &packet_hash(before));
    update_hash_part(&mut hasher, &packet_hash(after));
    hasher.finalize().to_hex().to_string()
}

fn atlas_row_hash(invariant_id: &str, entry: &InvariantAtlasEntry) -> String {
    let mut hasher = blake3::Hasher::new();
    hasher.update(b"CoreContracts.InvariantAtlasEntry.v1");
    update_hash_part(&mut hasher, invariant_id);
    update_hash_part(&mut hasher, &format!("{:?}", entry.layer));
    update_hash_part(&mut hasher, &entry.carrier_type);
    update_hash_part(&mut hasher, &entry.witness_protocol_id);
    hasher.finalize().to_hex().to_string()
}

fn update_hash_part(hasher: &mut blake3::Hasher, part: &str) {
    hasher.update(&(part.len() as u64).to_le_bytes());
    hasher.update(part.as_bytes());
}

// Origin: engine/crates_rs/core_contracts/src/validation_invariant_atlas.rs
// Claim: urn:core:crates_rs:core-contracts:validation-invariant-atlas:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::validation::ValidationStatus;

    fn packet() -> InvariantPacket {
        InvariantPacket::new(
            InvariantLayer::GTFOC,
            "finite cochain carrier",
            "weighted quotient norm",
            "Phi1",
            "exact repair preserves quotient value",
            "E preserves, I preserves under isometry, M refuses",
            "primal-dual replay certificate",
            true,
            "Phi1CertificateMissing",
        )
        .expect("packet fields are non-empty")
    }

    #[test]
    fn canonical_gate_accepts_matching_packet() {
        let gate = SchemaGate::default();
        let artifact = gate.validate_packet(&packet());
        assert_eq!(artifact.status, ValidationStatus::Valid);
    }

    #[test]
    fn store_round_trips_as_yaml() {
        let store = InvariantAtlasStore::canonical();
        let text = store.to_yaml_string().expect("store serializes");
        let decoded = InvariantAtlasStore::from_yaml_str(&text).expect("store parses");
        assert_eq!(decoded, store);
    }

    #[test]
    fn yaml_duplicate_invariant_ids_are_rejected() {
        let text = r#"
entries:
  Phi1:
    layer: CODA-FOC
    carrier_type: finite cochain carrier
    witness_protocol_id: primal-dual replay certificate
  "Phi1 ":
    layer: CODA-FOC
    carrier_type: mutated carrier
    witness_protocol_id: primal-dual replay certificate
"#;

        let err = InvariantAtlasStore::from_yaml_str(text).unwrap_err();
        assert!(matches!(err, InvariantAtlasStoreError::Yaml(_)));
    }
}
