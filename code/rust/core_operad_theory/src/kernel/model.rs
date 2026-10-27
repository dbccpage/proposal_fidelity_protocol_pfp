//! Finite colours, ports, operands, and operation declarations.
//!
//! Rust face of `engine/crates/kernel/higher_operad/model.py`. Field
//! names, field order in the canonical payload, validation rules, and the
//! `canonical_id` domain strings are all load-bearing: they decide the
//! identifier, and the identifier is what the estate stores.
//!
//! AuthorityEffect: None. Nothing here mints authority; `AuthorityEffect` is a
//! declared ceiling that this module only ever checks, never raises.

use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use thiserror::Error;

use super::canonical::{canonical_id, require_digest, require_identifier, CanonicalError};

#[derive(Debug, Error, PartialEq, Eq)]
pub enum ModelError {
    #[error(transparent)]
    Canonical(#[from] CanonicalError),

    #[error("operation input port IDs must be unique")]
    DuplicatePortIds,

    #[error("{field} must not contain duplicates")]
    Duplicates { field: String },

    #[error("operation authority_effect exceeds its authority_ceiling")]
    AuthorityCeilingExceeded,
}

/// Whether an invocation is an entry point or a disciplined inner step.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum InvocationGrade {
    #[serde(rename = "entry")]
    Entry,
    #[serde(rename = "discipline")]
    Discipline,
}

impl InvocationGrade {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Entry => "entry",
            Self::Discipline => "discipline",
        }
    }
}

impl Default for InvocationGrade {
    fn default() -> Self {
        Self::Discipline
    }
}

/// The authority ladder. Ordering is the whole point: `rank` is what makes
/// "effect may not exceed ceiling" checkable.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum AuthorityEffect {
    #[serde(rename = "None")]
    None,
    #[serde(rename = "EvidenceOnly")]
    EvidenceOnly,
    #[serde(rename = "FactOnly")]
    FactOnly,
    #[serde(rename = "StateTransition")]
    StateTransition,
}

impl AuthorityEffect {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::None => "None",
            Self::EvidenceOnly => "EvidenceOnly",
            Self::FactOnly => "FactOnly",
            Self::StateTransition => "StateTransition",
        }
    }

    /// Mirrors `AUTHORITY_RANK` in the Python kernel.
    pub fn rank(self) -> u8 {
        match self {
            Self::None => 0,
            Self::EvidenceOnly => 1,
            Self::FactOnly => 2,
            Self::StateTransition => 3,
        }
    }
}

impl Default for AuthorityEffect {
    fn default() -> Self {
        Self::None
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ColourSpec {
    pub colour_id: String,
    pub family: String,
    pub schema_ref: String,
    pub schema_digest: String,
    pub validator_ref: String,
    pub validator_digest: String,
    pub schema_version: String,
}

impl ColourSpec {
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        colour_id: &str,
        family: &str,
        schema_ref: &str,
        schema_digest: &str,
        validator_ref: &str,
        validator_digest: &str,
        schema_version: &str,
    ) -> Result<Self, ModelError> {
        Ok(Self {
            colour_id: require_identifier(colour_id, "colour_id")?,
            family: require_identifier(family, "family")?,
            schema_ref: require_identifier(schema_ref, "schema_ref")?,
            schema_digest: require_digest(schema_digest, "schema_digest")?,
            validator_ref: require_identifier(validator_ref, "validator_ref")?,
            validator_digest: require_digest(validator_digest, "validator_digest")?,
            schema_version: require_identifier(schema_version, "schema_version")?,
        })
    }

    pub fn to_canonical(&self) -> Value {
        json!({
            "colour_id": self.colour_id,
            "family": self.family,
            "schema_ref": self.schema_ref,
            "schema_digest": self.schema_digest,
            "validator_ref": self.validator_ref,
            "validator_digest": self.validator_digest,
            "schema_version": self.schema_version,
        })
    }

    pub fn canonical_id(&self) -> Result<String, ModelError> {
        Ok(canonical_id("core.oewas.colour.v1", &self.to_canonical())?)
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PortSpec {
    pub port_id: String,
    pub colour_id: String,
    pub schema_ref: String,
}

impl PortSpec {
    pub fn new(port_id: &str, colour_id: &str, schema_ref: &str) -> Result<Self, ModelError> {
        Ok(Self {
            port_id: require_identifier(port_id, "port_id")?,
            colour_id: require_identifier(colour_id, "colour_id")?,
            schema_ref: require_identifier(schema_ref, "schema_ref")?,
        })
    }

    /// Type identity ignores `port_id`: two ports are the same type when their
    /// colour and schema agree, regardless of what the slot is called.
    pub fn same_type(&self, other: &PortSpec) -> bool {
        self.colour_id == other.colour_id && self.schema_ref == other.schema_ref
    }

    pub fn to_canonical(&self) -> Value {
        json!({
            "port_id": self.port_id,
            "colour_id": self.colour_id,
            "schema_ref": self.schema_ref,
        })
    }
}

/// The typed external boundary of an operation or a workflow expression.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundarySignature {
    pub inputs: Vec<PortSpec>,
    pub output: PortSpec,
}

impl BoundarySignature {
    pub fn new(inputs: Vec<PortSpec>, output: PortSpec) -> Self {
        Self { inputs, output }
    }

    /// Two boundaries are parallel when a rewrite between them is even
    /// type-admissible. This is the gate a 2-cell has to pass.
    pub fn parallel_to(&self, other: &BoundarySignature) -> bool {
        self.inputs.len() == other.inputs.len()
            && self
                .inputs
                .iter()
                .zip(other.inputs.iter())
                .all(|(left, right)| left.same_type(right))
            && self.output.same_type(&other.output)
    }

    pub fn to_canonical(&self) -> Value {
        json!({
            "inputs": self.inputs.iter().map(PortSpec::to_canonical).collect::<Vec<_>>(),
            "output": self.output.to_canonical(),
        })
    }
}

/// An immutable reference to an admitted artifact.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct OperandRef {
    pub artifact_digest: String,
    pub colour_id: String,
    pub schema_ref: String,
    pub admission_receipt_ref: String,
    pub provenance_root: String,
}

impl OperandRef {
    pub fn new(
        artifact_digest: &str,
        colour_id: &str,
        schema_ref: &str,
        admission_receipt_ref: &str,
        provenance_root: &str,
    ) -> Result<Self, ModelError> {
        Ok(Self {
            artifact_digest: require_digest(artifact_digest, "artifact_digest")?,
            colour_id: require_identifier(colour_id, "colour_id")?,
            schema_ref: require_identifier(schema_ref, "schema_ref")?,
            admission_receipt_ref: require_digest(admission_receipt_ref, "admission_receipt_ref")?,
            provenance_root: require_digest(provenance_root, "provenance_root")?,
        })
    }

    pub fn matches(&self, port: &PortSpec) -> bool {
        self.colour_id == port.colour_id && self.schema_ref == port.schema_ref
    }

    pub fn to_canonical(&self) -> Value {
        json!({
            "artifact_digest": self.artifact_digest,
            "colour_id": self.colour_id,
            "schema_ref": self.schema_ref,
            "admission_receipt_ref": self.admission_receipt_ref,
            "provenance_root": self.provenance_root,
        })
    }

    pub fn canonical_id(&self) -> Result<String, ModelError> {
        Ok(canonical_id("core.oewas.operand-ref.v1", &self.to_canonical())?)
    }
}

/// A compiled, immutable operation declaration: exact arity, one output.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct OperationSpec {
    pub operation_id: String,
    pub version: String,
    pub input_ports: Vec<PortSpec>,
    pub output_port: PortSpec,
    pub executor_ref: String,
    pub executor_digest: String,
    pub tool_refs: Vec<String>,
    pub effects: Vec<String>,
    pub invocation_grade: InvocationGrade,
    pub authority_effect: AuthorityEffect,
    pub authority_ceiling: AuthorityEffect,
}

/// Builder-shaped input so callers do not have to pass eleven positional
/// arguments in the right order.
#[derive(Debug, Clone)]
pub struct OperationSpecInput<'a> {
    pub operation_id: &'a str,
    pub version: &'a str,
    pub input_ports: Vec<PortSpec>,
    pub output_port: PortSpec,
    pub executor_ref: &'a str,
    pub executor_digest: &'a str,
    pub tool_refs: Vec<String>,
    pub effects: Vec<String>,
    pub invocation_grade: InvocationGrade,
    pub authority_effect: AuthorityEffect,
    pub authority_ceiling: AuthorityEffect,
}

impl OperationSpec {
    fn unique_identifiers(
        items: &[String],
        item_label: &str,
        field_name: &str,
    ) -> Result<Vec<String>, ModelError> {
        let mut result = Vec::with_capacity(items.len());
        let mut seen = std::collections::BTreeSet::new();
        for item in items {
            let normalized = require_identifier(item, item_label)?;
            if !seen.insert(normalized.clone()) {
                return Err(ModelError::Duplicates {
                    field: field_name.to_owned(),
                });
            }
            result.push(normalized);
        }
        Ok(result)
    }

    pub fn new(input: OperationSpecInput<'_>) -> Result<Self, ModelError> {
        let operation_id = require_identifier(input.operation_id, "operation_id")?;
        let version = require_identifier(input.version, "version")?;
        let executor_ref = require_identifier(input.executor_ref, "executor_ref")?;
        let executor_digest = require_digest(input.executor_digest, "executor_digest")?;

        let mut seen = std::collections::BTreeSet::new();
        if input
            .input_ports
            .iter()
            .any(|port| !seen.insert(port.port_id.clone()))
        {
            return Err(ModelError::DuplicatePortIds);
        }

        // Order is preserved (unlike `sorted_unique`); only duplicates are
        // refused, matching the Python constructor.
        let tool_refs = Self::unique_identifiers(&input.tool_refs, "tool_ref", "tool_refs")?;
        let effects = Self::unique_identifiers(&input.effects, "effect", "effects")?;

        if input.authority_effect.rank() > input.authority_ceiling.rank() {
            return Err(ModelError::AuthorityCeilingExceeded);
        }

        Ok(Self {
            operation_id,
            version,
            input_ports: input.input_ports,
            output_port: input.output_port,
            executor_ref,
            executor_digest,
            tool_refs,
            effects,
            invocation_grade: input.invocation_grade,
            authority_effect: input.authority_effect,
            authority_ceiling: input.authority_ceiling,
        })
    }

    pub fn key(&self) -> String {
        format!("{}@{}", self.operation_id, self.version)
    }

    pub fn boundary(&self) -> BoundarySignature {
        BoundarySignature::new(self.input_ports.clone(), self.output_port.clone())
    }

    pub fn to_canonical(&self) -> Value {
        json!({
            "operation_id": self.operation_id,
            "version": self.version,
            "input_ports": self.input_ports.iter().map(PortSpec::to_canonical).collect::<Vec<_>>(),
            "output_port": self.output_port.to_canonical(),
            "executor_ref": self.executor_ref,
            "executor_digest": self.executor_digest,
            "tool_refs": self.tool_refs,
            "effects": self.effects,
            "invocation_grade": self.invocation_grade.as_str(),
            "authority_effect": self.authority_effect.as_str(),
            "authority_ceiling": self.authority_ceiling.as_str(),
        })
    }

    pub fn canonical_id(&self) -> Result<String, ModelError> {
        Ok(canonical_id("core.oewas.operation-spec.v1", &self.to_canonical())?)
    }
}

/// Agent-path fibration from `skill_operad/hott.py`.
///
/// Mathematical identity types stay in `core_homotopy_type_theory`. This
/// record is the estate path: antibody screens, boundary agreement, and a
/// witness when transport fails. `authority_effect` is always `"None"`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum AgentPathWitness {
    Hallucination {
        claimed_source: String,
        claimed_target: String,
        antibody_name: String,
        detail: String,
    },
    PathObstruction {
        path_source: String,
        path_target: String,
        fibration_name: String,
        detail: String,
    },
}

impl AgentPathWitness {
    pub fn antibody_name(&self) -> Option<&str> {
        match self {
            Self::Hallucination { antibody_name, .. } => Some(antibody_name),
            Self::PathObstruction { .. } => None,
        }
    }

    pub fn detail(&self) -> &str {
        match self {
            Self::Hallucination { detail, .. } | Self::PathObstruction { detail, .. } => detail,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AgentPath {
    pub source: String,
    pub target: String,
    pub steps: Vec<String>,
    pub antibodies_passed: Vec<String>,
    pub witness: Option<AgentPathWitness>,
}

impl AgentPath {
    pub fn authority_effect(&self) -> &'static str {
        "None"
    }

    pub fn refl(point: impl Into<String>) -> Self {
        let point = point.into();
        Self {
            steps: vec![format!("refl({point})")],
            source: point.clone(),
            target: point,
            antibodies_passed: Vec::new(),
            witness: None,
        }
    }

    pub fn is_valid(&self) -> bool {
        self.witness.is_none()
    }

    pub fn concat(self, other: Self) -> Self {
        if self.target != other.source {
            let detail = format!(
                "target endpoint {:?} does not match source endpoint {:?}",
                self.target, other.source
            );
            let path_source = self.source.clone();
            let path_target = other.target.clone();
            return Self {
                source: self.source,
                target: other.target,
                steps: [self.steps, vec!["MISMATCH_BOUNDARY".to_owned()], other.steps].concat(),
                antibodies_passed: Vec::new(),
                witness: Some(AgentPathWitness::PathObstruction {
                    path_source,
                    path_target,
                    fibration_name: "EndpointMatching".to_owned(),
                    detail,
                }),
            };
        }
        let witness = self.witness.or(other.witness);
        Self {
            source: self.source,
            target: other.target,
            steps: [self.steps, other.steps].concat(),
            antibodies_passed: [self.antibodies_passed, other.antibodies_passed].concat(),
            witness,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AntibodyScreen {
    pub name: String,
    pub killed: bool,
    pub detail: String,
}

pub fn transport(
    candidate: &str,
    source: Option<&str>,
    battery: &[AntibodyScreen],
) -> AgentPath {
    let source = source.unwrap_or(candidate).to_owned();
    let mut passed = Vec::new();
    for screen in battery {
        if screen.killed {
            return AgentPath {
                source: source.clone(),
                target: candidate.to_owned(),
                steps: vec!["transport".to_owned(), format!("killed_by_{}", screen.name)],
                antibodies_passed: passed,
                witness: Some(AgentPathWitness::Hallucination {
                    claimed_source: source,
                    claimed_target: candidate.to_owned(),
                    antibody_name: screen.name.clone(),
                    detail: screen.detail.clone(),
                }),
            };
        }
        passed.push(screen.name.clone());
    }
    AgentPath {
        source,
        target: candidate.to_owned(),
        steps: vec!["transport".to_owned(), "all_antibodies_passed".to_owned()],
        antibodies_passed: passed,
        witness: None,
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Homotopy2Cell {
    pub name: String,
    pub source_path: AgentPath,
    pub target_path: AgentPath,
}

impl Homotopy2Cell {
    pub fn new(
        name: impl Into<String>,
        source_path: AgentPath,
        target_path: AgentPath,
    ) -> Result<Self, AgentFibrationError> {
        if source_path.source != target_path.source || source_path.target != target_path.target {
            return Err(AgentFibrationError::BoundaryMismatch);
        }
        Ok(Self {
            name: name.into(),
            source_path,
            target_path,
        })
    }

    pub fn authority_effect(&self) -> &'static str {
        "None"
    }

    pub fn is_valid(&self) -> bool {
        self.source_path.is_valid() && self.target_path.is_valid()
    }

    pub fn compose_vertical(self, other: Self) -> Result<Self, AgentFibrationError> {
        if self.target_path != other.source_path {
            return Err(AgentFibrationError::VerticalMismatch);
        }
        Ok(Self {
            name: format!("({} ∘_v {})", other.name, self.name),
            source_path: self.source_path,
            target_path: other.target_path,
        })
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AgentFibrationError {
    BoundaryMismatch,
    VerticalMismatch,
}

// Origin: engine/crates_rs/core_operad_theory/src/kernel/model.rs
// Claim: urn:core:crates_rs:core-operad-theory:model:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn port(id: &str, colour: &str) -> PortSpec {
        PortSpec::new(id, colour, "any").unwrap()
    }

    fn spec_input<'a>() -> OperationSpecInput<'a> {
        OperationSpecInput {
            operation_id: "adversary",
            version: "v1",
            input_ports: vec![port("in_0", "State"), port("in_1", "Code")],
            output_port: port("out", "Receipt"),
            executor_ref: "skill.adversary",
            executor_digest: &EXEC_DIGEST,
            tool_refs: vec![],
            effects: vec![],
            invocation_grade: InvocationGrade::Discipline,
            authority_effect: AuthorityEffect::None,
            authority_ceiling: AuthorityEffect::None,
        }
    }

    const EXEC_DIGEST: &str =
        "sha256:0000000000000000000000000000000000000000000000000000000000000000";

    #[test]
    fn authority_rank_orders_the_ladder() {
        assert!(AuthorityEffect::None.rank() < AuthorityEffect::EvidenceOnly.rank());
        assert!(AuthorityEffect::EvidenceOnly.rank() < AuthorityEffect::FactOnly.rank());
        assert!(AuthorityEffect::FactOnly.rank() < AuthorityEffect::StateTransition.rank());
    }

    #[test]
    fn effect_may_not_exceed_ceiling() {
        let mut input = spec_input();
        input.authority_effect = AuthorityEffect::StateTransition;
        input.authority_ceiling = AuthorityEffect::None;
        assert_eq!(
            OperationSpec::new(input).unwrap_err(),
            ModelError::AuthorityCeilingExceeded
        );
    }

    #[test]
    fn effect_equal_to_ceiling_is_admissible() {
        let mut input = spec_input();
        input.authority_effect = AuthorityEffect::EvidenceOnly;
        input.authority_ceiling = AuthorityEffect::EvidenceOnly;
        assert!(OperationSpec::new(input).is_ok());
    }

    #[test]
    fn duplicate_input_port_ids_are_refused() {
        let mut input = spec_input();
        input.input_ports = vec![port("in_0", "State"), port("in_0", "Code")];
        assert_eq!(OperationSpec::new(input).unwrap_err(), ModelError::DuplicatePortIds);
    }

    #[test]
    fn duplicate_tool_refs_are_refused() {
        let mut input = spec_input();
        input.tool_refs = vec!["t".to_owned(), "t".to_owned()];
        assert!(matches!(
            OperationSpec::new(input).unwrap_err(),
            ModelError::Duplicates { .. }
        ));
    }

    #[test]
    fn ports_of_the_same_colour_and_schema_are_the_same_type() {
        assert!(port("in_0", "State").same_type(&port("in_9", "State")));
        assert!(!port("in_0", "State").same_type(&port("in_0", "Code")));
    }

    #[test]
    fn parallel_boundaries_require_matching_arity_and_types() {
        let a = BoundarySignature::new(vec![port("in_0", "State")], port("out", "Receipt"));
        let b = BoundarySignature::new(vec![port("x", "State")], port("y", "Receipt"));
        let c = BoundarySignature::new(vec![port("x", "Code")], port("y", "Receipt"));
        let d = BoundarySignature::new(vec![], port("y", "Receipt"));

        assert!(a.parallel_to(&b));
        assert!(!a.parallel_to(&c));
        assert!(!a.parallel_to(&d));
    }

    #[test]
    fn key_is_id_at_version() {
        assert_eq!(OperationSpec::new(spec_input()).unwrap().key(), "adversary@v1");
    }

    #[test]
    fn canonical_id_is_stable_and_domain_separated() {
        let spec = OperationSpec::new(spec_input()).unwrap();
        let first = spec.canonical_id().unwrap();
        let second = spec.canonical_id().unwrap();
        assert_eq!(first, second);
        assert!(first.starts_with("sha256:"));

        // A different domain over the same payload must not collide.
        let raw = super::canonical_id("core.oewas.colour.v1", &spec.to_canonical()).unwrap();
        assert_ne!(first, raw);
    }

    #[test]
    fn operand_matches_a_port_by_colour_and_schema() {
        let operand = OperandRef::new(EXEC_DIGEST, "State", "any", EXEC_DIGEST, EXEC_DIGEST).unwrap();
        assert!(operand.matches(&port("in_0", "State")));
        assert!(!operand.matches(&port("in_0", "Code")));
    }

    #[test]
    fn agent_path_refl_carries_no_authority() {
        let path = AgentPath::refl("seat");
        assert!(path.is_valid());
        assert_eq!(path.authority_effect(), "None");
        assert_eq!(path.source, path.target);
        assert_eq!(path.steps, vec!["refl(seat)".to_owned()]);
    }

    #[test]
    fn transport_stops_at_the_first_killing_screen() {
        let path = transport(
            "candidate",
            Some("contract"),
            &[
                AntibodyScreen {
                    name: "kept".to_owned(),
                    killed: false,
                    detail: String::new(),
                },
                AntibodyScreen {
                    name: "cuts".to_owned(),
                    killed: true,
                    detail: "mismatch".to_owned(),
                },
                AntibodyScreen {
                    name: "later".to_owned(),
                    killed: true,
                    detail: "ignored".to_owned(),
                },
            ],
        );
        assert!(!path.is_valid());
        assert_eq!(path.antibodies_passed, vec!["kept".to_owned()]);
        assert_eq!(path.witness.as_ref().unwrap().antibody_name(), Some("cuts"));
        assert_eq!(path.authority_effect(), "None");
    }

    #[test]
    fn a_two_cell_requires_the_same_boundary() {
        let left = AgentPath::refl("a");
        let right = AgentPath::refl("b");
        assert_eq!(
            Homotopy2Cell::new("alpha", left, right).unwrap_err(),
            AgentFibrationError::BoundaryMismatch
        );
        let p = AgentPath::refl("a");
        let q = AgentPath::refl("a");
        let cell = Homotopy2Cell::new("alpha", p, q).unwrap();
        assert!(cell.is_valid());
        assert_eq!(cell.authority_effect(), "None");
    }
}
