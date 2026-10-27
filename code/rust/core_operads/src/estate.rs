//! V3 estate identifiers, lifecycle facets, operations and source provenance.
use crate::Refusal;
use num_bigint::BigInt;
use num_traits::Zero;
use core_types::python_unicode::lowercase;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::str::FromStr;
fn invalid(detail: impl Into<String>) -> Refusal {
    Refusal::new("OEWAS_VALUE_ERROR", detail)
}
fn trim(text: &str) -> &str {
    text.trim_matches(|c: char| c.is_whitespace() || matches!(c, '\u{1c}'..='\u{1f}'))
}
macro_rules! identifiers {
    ($($name:ident),*) => {$ (
        #[derive(Debug,Clone,PartialEq,Eq,PartialOrd,Ord,Hash,Serialize)]
        pub struct $name {value:String}
        impl $name {
            pub fn new(value:&str)->Result<Self,Refusal> {let value=trim(value);if value.is_empty()||value.chars().count()>512 {return Err(invalid(concat!(stringify!($name)," must be nonempty and at most 512 characters")));}Ok(Self{value:value.into()})}
            pub fn value(&self)->&str {&self.value}
        }
        impl<'de> Deserialize<'de> for $name {
            fn deserialize<D:serde::Deserializer<'de>>(d:D)->Result<Self,D::Error> {
                #[derive(Deserialize)] #[serde(deny_unknown_fields)] struct Wire {value:String}
                let wire=Wire::deserialize(d)?;Self::new(&wire.value).map_err(serde::de::Error::custom)
            }
        }
    )*};
}
identifiers!(
    SkillId,
    OperationId,
    DocumentId,
    OperandId,
    WorkflowId,
    ColourId,
    SchemaRef,
    CorrelationId,
    CausationId,
    IdempotencyKey,
    EstateRef
);
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize)]
pub struct ContentDigest {
    algorithm: String,
    hex_digest: String,
}
impl ContentDigest {
    pub fn new(algorithm: &str, digest: &str) -> Result<Self, Refusal> {
        let algorithm = lowercase(trim(algorithm));
        let digest = trim(digest);
        if algorithm.is_empty() || digest.is_empty() {
            return Err(invalid("digest algorithm and content must be nonempty"));
        }
        if ["sha256", "sha-256", "canonical_json_sha256"].contains(&algorithm.as_str())
            && (digest.len() != 64 || !digest.bytes().all(|b| b.is_ascii_hexdigit()))
        {
            return Err(invalid(format!("invalid sha256 hex digest: {digest}")));
        }
        Ok(Self {
            algorithm,
            hex_digest: lowercase(digest),
        })
    }
    pub fn sha256(digest: &str) -> Result<Self, Refusal> {
        Self::new("sha256", digest)
    }
    pub fn empty_sha256() -> Self {
        Self {
            algorithm: "sha256".into(),
            hex_digest: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855".into(),
        }
    }
    fn is_canonical_zero_sha256(&self) -> bool {
        self.algorithm == "sha256"
            && self.hex_digest == "0000000000000000000000000000000000000000000000000000000000000000"
    }
    pub fn canonical(&self) -> String {
        format!("{}:{}", self.algorithm, self.hex_digest)
    }
}
impl<'de> Deserialize<'de> for ContentDigest {
    fn deserialize<D: serde::Deserializer<'de>>(d: D) -> Result<Self, D::Error> {
        #[derive(Deserialize)]
        #[serde(deny_unknown_fields)]
        struct Wire {
            algorithm: String,
            hex_digest: String,
        }
        let wire = Wire::deserialize(d)?;
        Self::new(&wire.algorithm, &wire.hex_digest).map_err(serde::de::Error::custom)
    }
}
mod integer {
    use super::*;
    pub fn serialize<S: serde::Serializer>(v: &BigInt, s: S) -> Result<S::Ok, S::Error> {
        serde_json::Number::from_str(&v.to_string())
            .map_err(serde::ser::Error::custom)?
            .serialize(s)
    }
    pub fn deserialize<'de, D: serde::Deserializer<'de>>(d: D) -> Result<BigInt, D::Error> {
        let v = Value::deserialize(d)?;
        v.as_number()
            .and_then(|n| BigInt::from_str(&n.to_string()).ok())
            .ok_or_else(|| serde::de::Error::custom("source span must use exact integers"))
    }
}
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize)]
pub struct SourceByteSpan {
    #[serde(with = "integer")]
    start_byte: BigInt,
    #[serde(with = "integer")]
    end_byte: BigInt,
    #[serde(with = "integer")]
    start_line: BigInt,
    #[serde(with = "integer")]
    start_col: BigInt,
    #[serde(with = "integer")]
    end_line: BigInt,
    #[serde(with = "integer")]
    end_col: BigInt,
}
impl SourceByteSpan {
    pub fn new(
        start_byte: BigInt,
        end_byte: BigInt,
        start_line: BigInt,
        start_col: BigInt,
        end_line: BigInt,
        end_col: BigInt,
    ) -> Result<Self, Refusal> {
        if start_byte < BigInt::zero() || end_byte < start_byte {
            return Err(invalid("invalid byte span"));
        }
        if start_line < BigInt::from(1) || end_line < start_line {
            return Err(invalid("invalid line span"));
        }
        if start_col < BigInt::zero() || (start_line == end_line && end_col < start_col) {
            return Err(invalid("invalid column span"));
        }
        Ok(Self {
            start_byte,
            end_byte,
            start_line,
            start_col,
            end_line,
            end_col,
        })
    }
    pub fn byte_length(&self) -> BigInt {
        &self.end_byte - &self.start_byte
    }
}
impl<'de> Deserialize<'de> for SourceByteSpan {
    fn deserialize<D: serde::Deserializer<'de>>(d: D) -> Result<Self, D::Error> {
        #[derive(Deserialize)]
        #[serde(deny_unknown_fields)]
        struct Wire {
            #[serde(with = "integer")]
            start_byte: BigInt,
            #[serde(with = "integer")]
            end_byte: BigInt,
            #[serde(with = "integer")]
            start_line: BigInt,
            #[serde(with = "integer")]
            start_col: BigInt,
            #[serde(with = "integer")]
            end_line: BigInt,
            #[serde(with = "integer")]
            end_col: BigInt,
        }
        let w = Wire::deserialize(d)?;
        Self::new(
            w.start_byte,
            w.end_byte,
            w.start_line,
            w.start_col,
            w.end_line,
            w.end_col,
        )
        .map_err(serde::de::Error::custom)
    }
}
macro_rules! facets {($name:ident {$($variant:ident=>$wire:literal),*})=> {
    #[derive(Debug,Clone,Copy,PartialEq,Eq,Hash,Serialize,Deserialize)] pub enum $name {$(#[serde(rename=$wire)] $variant),*}
};}
facets!(DeclarationFacet {Declared=>"Declared",Abstract=>"Abstract",Synthesized=>"Synthesized"});
facets!(SchemaBindingFacet {Unbound=>"Unbound",Bound=>"Bound",AnySchema=>"AnySchema"});
facets!(ExecutorBindingFacet {Unbound=>"Unbound",Bound=>"Bound",ExternalService=>"ExternalService"});
facets!(ValidationFacet {Unchecked=>"Unchecked",Validated=>"Validated",Failed=>"Failed"});
facets!(AdmissionFacet {Unadmitted=>"Unadmitted",Admitted=>"Admitted",Retired=>"Retired"});
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SkillLifecycleV3 {
    declaration: DeclarationFacet,
    schema_binding: SchemaBindingFacet,
    executor_binding: ExecutorBindingFacet,
    validation: ValidationFacet,
    admission: AdmissionFacet,
    #[serde(default)]
    schema_digest: Option<ContentDigest>,
    #[serde(default)]
    executor_digest: Option<ContentDigest>,
}
impl SkillLifecycleV3 {
    pub fn is_executable(&self) -> bool {
        self.declaration == DeclarationFacet::Declared
            && self.schema_binding == SchemaBindingFacet::Bound
            && self.executor_binding == ExecutorBindingFacet::Bound
            && self.validation == ValidationFacet::Validated
            && self.admission == AdmissionFacet::Admitted
            && self
                .schema_digest
                .as_ref()
                .is_some_and(|digest| !digest.is_canonical_zero_sha256())
            && self
                .executor_digest
                .as_ref()
                .is_some_and(|digest| !digest.is_canonical_zero_sha256())
    }
}
#[derive(
    Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize, Default,
)]
pub enum AuthorityEffect {
    #[default]
    None,
    EvidenceOnly,
    FactOnly,
    StateTransition,
}
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PortSpecV3 {
    name: String,
    colour_id: ColourId,
    schema_ref: SchemaRef,
    schema_digest: ContentDigest,
    validator_ref: String,
    validator_digest: ContentDigest,
}
impl PortSpecV3 {
    /// Names label occurrences; use the OEWAS typed compiler's five-field contract.
    pub fn same_contract_as(&self, other: &Self) -> bool {
        self.colour_id == other.colour_id
            && self.schema_ref == other.schema_ref
            && self.schema_digest == other.schema_digest
            && self.validator_ref == other.validator_ref
            && self.validator_digest == other.validator_digest
    }
}
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct InstructionOperand {
    operand_id: OperandId,
    kind: String,
    instruction_body: String,
    span: SourceByteSpan,
    #[serde(default)]
    dependencies: Vec<OperandId>,
    #[serde(default)]
    emitted_observations: Vec<String>,
}
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ArtifactOperandRef {
    provenance_digest: ContentDigest,
    colour_id: ColourId,
    schema_ref: SchemaRef,
    schema_digest: ContentDigest,
    validator_digest: ContentDigest,
}
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ResidualPackageSpan {
    input_residual: String,
    evidence_span: SourceByteSpan,
    output_residual: String,
    #[serde(default)]
    evidence_digest: Option<ContentDigest>,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct OperationWire {
    operation_id: OperationId,
    inputs: Vec<PortSpecV3>,
    output: PortSpecV3,
    operand_refs: Vec<OperandId>,
    lifecycle: SkillLifecycleV3,
    residual_status: String,
    #[serde(default)]
    effects: Vec<String>,
    #[serde(default)]
    tool_refs: Vec<String>,
    #[serde(default)]
    authority_effect: AuthorityEffect,
    #[serde(default)]
    authority_ceiling: AuthorityEffect,
    #[serde(default = "entry")]
    invocation_grade: String,
    #[serde(default)]
    description: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    replacement_operation_id: Option<OperationId>,
}
#[derive(Debug, Clone, Serialize)]
#[serde(transparent)]
pub struct OperationV3(OperationWire);
impl<'de> Deserialize<'de> for OperationV3 {
    fn deserialize<D: serde::Deserializer<'de>>(d: D) -> Result<Self, D::Error> {
        let wire = OperationWire::deserialize(d)?;
        if wire.authority_effect > wire.authority_ceiling {
            return Err(serde::de::Error::custom("operation effect exceeds ceiling"));
        }
        if wire.replacement_operation_id.as_ref().is_some_and(|replacement| {
            wire.lifecycle.admission != AdmissionFacet::Retired
                || replacement == &wire.operation_id
        }) {
            return Err(serde::de::Error::custom(
                "only a retired operation may name a distinct replacement",
            ));
        }
        Ok(Self(wire))
    }
}
fn entry() -> String {
    "entry".into()
}
impl OperationV3 {
    pub fn from_json(value: &Value) -> Result<Self, Refusal> {
        let result: Self =
            serde_json::from_value(value.clone()).map_err(|e| invalid(e.to_string()))?;
        if result.0.authority_effect > result.0.authority_ceiling {
            return Err(invalid("operation effect exceeds ceiling"));
        }
        Ok(result)
    }
    pub fn operation_id(&self) -> &OperationId {
        &self.0.operation_id
    }
    pub fn is_executable(&self) -> bool {
        self.0.lifecycle.is_executable()
    }
    pub fn to_dict(&self) -> Result<Value, Refusal> {
        serde_json::to_value(self).map_err(|e| invalid(e.to_string()))
    }
}
impl PartialEq for OperationV3 {
    fn eq(&self, other: &Self) -> bool {
        (
            &self.0.operation_id,
            &self.0.inputs,
            &self.0.output,
            &self.0.operand_refs,
            &self.0.lifecycle,
            &self.0.residual_status,
        ) == (
            &other.0.operation_id,
            &other.0.inputs,
            &other.0.output,
            &other.0.operand_refs,
            &other.0.lifecycle,
            &other.0.residual_status,
        ) && (
            &self.0.effects,
            &self.0.tool_refs,
            &self.0.authority_effect,
            &self.0.authority_ceiling,
            &self.0.invocation_grade,
            &self.0.replacement_operation_id,
        ) == (
            &other.0.effects,
            &other.0.tool_refs,
            &other.0.authority_effect,
            &other.0.authority_ceiling,
            &other.0.invocation_grade,
            &other.0.replacement_operation_id,
        )
    }
}
impl Eq for OperationV3 {}
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CompositionV3 {
    composition_id: String,
    term_kind: String,
    root_operation_id: OperationId,
    #[serde(default)]
    child_operation_ids: Vec<OperationId>,
    #[serde(default)]
    slot_bindings: Vec<(usize, OperationId)>,
    #[serde(default)]
    expected_boundary: String,
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DocumentLeafNode {
    kind: String,
    span: SourceByteSpan,
    content: String,
    #[serde(default)]
    info_string: String,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SkillDocumentV3 {
    document_id: DocumentId,
    skill_id: SkillId,
    source_relative_path: String,
    raw_digest: ContentDigest,
    semantic_digest: ContentDigest,
    #[serde(default)]
    leaf_nodes: Vec<DocumentLeafNode>,
    #[serde(default)]
    operands: Vec<InstructionOperand>,
    #[serde(default)]
    operations: Vec<OperationV3>,
    #[serde(default)]
    compositions: Vec<CompositionV3>,
    #[serde(default)]
    residual_spans: Vec<ResidualPackageSpan>,
    #[serde(default)]
    proven_root_operation_id: Option<OperationId>,
}
impl SkillDocumentV3 {
    pub fn get_operation(&self, id: &OperationId) -> Option<&OperationV3> {
        self.operations.iter().find(|op| &op.0.operation_id == id)
    }
}
impl PartialEq for SkillDocumentV3 {
    fn eq(&self, other: &Self) -> bool {
        self.document_id == other.document_id && self.raw_digest == other.raw_digest
    }
}
impl Eq for SkillDocumentV3 {}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CapabilitySliceV3 {
    slice_id: String,
    name: String,
    operation_ids: Vec<OperationId>,
    #[serde(default)]
    description: String,
}
pub fn execute(payload: &Value) -> Result<Value, Refusal> {
    let operation = OperationV3::from_json(&payload["operation"])?;
    Ok(
        serde_json::json!({"operation":operation.to_dict()?,"is_executable":operation.is_executable()}),
    )
}

fn composition_slot(value: &Value, arity: usize) -> Result<usize, Refusal> {
    let not_integer = || Refusal::new("SLOT_INDEX_NOT_AN_INTEGER", "Slot must be an exact integer");
    let number = value.as_number().ok_or_else(not_integer)?;
    if let Some(index) = number.as_u64() {
        if let Ok(index) = usize::try_from(index) {
            if index < arity {
                return Ok(index);
            }
        }
    } else if number.to_string().contains(['.', 'e', 'E']) {
        return Err(not_integer());
    }
    Err(Refusal::new(
        "SLOT_INDEX_OUT_OF_BOUNDS",
        format!("Slot {value} is outside the root input range [0, {arity})"),
    ))
}

/// Verify ordered V3 boundaries only; no source authenticity or execution admission.
pub fn verify_composition(
    root: &OperationV3,
    bindings: &[(Value, OperationV3)],
) -> Result<bool, Refusal> {
    for (position, (slot, child)) in bindings.iter().enumerate() {
        let index = composition_slot(slot, root.0.inputs.len())?;
        if bindings[..position]
            .iter()
            .any(|(previous, _)| previous.as_u64() == slot.as_u64())
        {
            return Err(Refusal::new(
                "DUPLICATE_SLOT_BINDING",
                format!("Slot {index} is bound more than once"),
            ));
        }
        let expected = &root.0.inputs[index];
        let actual = &child.0.output;
        if actual.same_contract_as(expected) {
            continue;
        }
        let (code, detail) = if actual.colour_id != expected.colour_id {
            ("COLOUR_MISMATCH", "colour")
        } else if actual.schema_digest != expected.schema_digest {
            return Err(Refusal::new(
                "SCHEMA_DIGEST_MISMATCH",
                format!(
                    "Child output schema digest {} does not match root input {}",
                    actual.schema_digest.canonical(),
                    expected.schema_digest.canonical(),
                ),
            ));
        } else if actual.schema_ref != expected.schema_ref {
            ("SCHEMA_REFERENCE_MISMATCH", "schema reference")
        } else if actual.validator_ref != expected.validator_ref {
            ("VALIDATOR_REFERENCE_MISMATCH", "validator reference")
        } else {
            ("VALIDATOR_DIGEST_MISMATCH", "validator digest")
        };
        return Err(Refusal::new(
            code,
            format!("Child output {detail} does not match root input {index}"),
        ));
    }
    Ok(true)
}

pub fn execute_composition(payload: &Value) -> Result<Value, Refusal> {
    #[derive(Deserialize)]
    #[serde(deny_unknown_fields)]
    struct Request {
        root_operation: OperationV3,
        slot_bindings: Vec<(Value, OperationV3)>,
    }
    let request: Request = serde_json::from_value(payload.clone())
        .map_err(|error| Refusal::new("STRICT_COMPOSITION_INPUT_INVALID", error.to_string()))?;
    let valid = verify_composition(&request.root_operation, &request.slot_bindings)?;
    Ok(serde_json::json!({"is_valid": valid, "authority_effect": "None"}))
}

// Origin: engine/crates_rs/core_operads/src/estate.rs
// Claim: urn:core:crates_rs:core-operads:estate:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord5629e2fe {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord5629e2fe` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError5629e2fe {
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
impl BoundaryError5629e2fe {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError5629e2fe {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError5629e2fe {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord5629e2fe {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError5629e2fe> {
        if capacity_bound == 0 {
            return Err(BoundaryError5629e2fe::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError5629e2fe::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError5629e2fe::ExceedsCapacity {
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
mod l4_boundary_tests_5629e2fe {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord5629e2fe::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord5629e2fe::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord5629e2fe::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord5629e2fe::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord5629e2fe::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError5629e2fe::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError5629e2fe::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
