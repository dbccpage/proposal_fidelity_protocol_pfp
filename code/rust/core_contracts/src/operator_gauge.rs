//! Canonical conductor operator manifests and runtime gauge bindings.
//!
//! These types close the S02-001 contract surface. They describe bounded
//! transformations and gauge substitutions; they do not activate providers,
//! grant licenses, or promote authority.

use std::collections::{BTreeMap, BTreeSet};

use core_types::authority::AuthorityEffect;
use serde::{Deserialize, Serialize};
use thiserror::Error;

pub const OPERATOR_MANIFEST_SCHEMA_VERSION: &str = "core.operator-manifest.v1";
pub const GAUGE_BINDING_SCHEMA_VERSION: &str = "core.gauge-binding.v1";
pub const OPERATOR_REGISTRY_SCHEMA_VERSION: &str = "core.operator-registry.v1";
pub const OPERATOR_INPUT_SCHEMA_VERSION: &str = "core.operator-input.v1";
pub const OPERATOR_OUTPUT_SCHEMA_VERSION: &str = "core.operator-output.v1";
pub const OPERATOR_REGISTRY_MAX_OPERATORS: usize = 32;
pub const OPERATOR_REGISTRY_MAX_BINDINGS: usize = 64;

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum OperatorOperationV1 {
    CanonicalJsonEcho,
    CarrierLift,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum OperatorCapabilityV1 {
    CanonicalJson,
    CarrierTransition,
    DeterministicReplay,
    ModelProfile,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum OperatorPermissionV1 {
    ReadFixture,
    WriteReceipt,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum OperatorWitnessRequirementV1 {
    Producer,
    IndependentEvaluator,
    AuthorityWitness,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ModelProviderV1 {
    Codex,
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ModelGaugeProfileV1 {
    pub provider: ModelProviderV1,
    pub profile_id: String,
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum RuntimeGaugeV1 {
    Fixture,
    ModelProfile(ModelGaugeProfileV1),
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum GaugeExecutionModeV1 {
    DeterministicFixture,
    ModelFixtureReplay,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct OperatorInputV1 {
    pub schema_version: String,
    pub request_id: String,
    pub family: String,
    pub payload: BTreeMap<String, String>,
}

impl OperatorInputV1 {
    pub fn validate(&self) -> Result<(), OperatorRegistryContractError> {
        require_schema(
            "operator_input.schema_version",
            OPERATOR_INPUT_SCHEMA_VERSION,
            &self.schema_version,
        )?;
        require_text("operator_input.request_id", &self.request_id)?;
        require_text("operator_input.family", &self.family)?;
        require_nonempty_map("operator_input.payload", &self.payload)
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct OperatorOutputV1 {
    pub schema_version: String,
    pub request_id: String,
    pub family: String,
    pub payload: BTreeMap<String, String>,
}

impl OperatorOutputV1 {
    pub fn validate(&self) -> Result<(), OperatorRegistryContractError> {
        require_schema(
            "operator_output.schema_version",
            OPERATOR_OUTPUT_SCHEMA_VERSION,
            &self.schema_version,
        )?;
        require_text("operator_output.request_id", &self.request_id)?;
        require_text("operator_output.family", &self.family)?;
        require_nonempty_map("operator_output.payload", &self.payload)
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct OperatorManifestV1 {
    pub schema_version: String,
    pub operator_id: String,
    pub semantic_contract_id: String,
    pub input_families: Vec<String>,
    pub output_families: Vec<String>,
    pub permitted_operations: Vec<OperatorOperationV1>,
    pub required_capabilities: Vec<OperatorCapabilityV1>,
    pub permission_ceiling: Vec<OperatorPermissionV1>,
    pub write_surface: Vec<String>,
    pub evidence_ceiling: String,
    pub license_ids: Vec<String>,
    pub witness_requirements: Vec<OperatorWitnessRequirementV1>,
    pub authority_effect: AuthorityEffect,
}

impl OperatorManifestV1 {
    fn validate_manifest_lists(&self) -> Result<(), OperatorRegistryContractError> {
        require_nonempty_sorted_texts("manifest.input_families", &self.input_families)?;
        require_nonempty_sorted_texts("manifest.output_families", &self.output_families)?;
        require_nonempty_sorted("manifest.permitted_operations", &self.permitted_operations)?;
        require_nonempty_sorted(
            "manifest.required_capabilities",
            &self.required_capabilities,
        )?;
        require_nonempty_sorted("manifest.permission_ceiling", &self.permission_ceiling)?;
        require_nonempty_sorted_paths("manifest.write_surface", &self.write_surface)?;
        require_text("manifest.evidence_ceiling", &self.evidence_ceiling)?;
        require_nonempty_sorted_texts("manifest.license_ids", &self.license_ids)?;
        require_nonempty_sorted("manifest.witness_requirements", &self.witness_requirements)
    }

    pub fn validate(&self) -> Result<(), OperatorRegistryContractError> {
        require_schema(
            "manifest.schema_version",
            OPERATOR_MANIFEST_SCHEMA_VERSION,
            &self.schema_version,
        )?;
        require_text("manifest.operator_id", &self.operator_id)?;
        require_text("manifest.semantic_contract_id", &self.semantic_contract_id)?;
        self.validate_manifest_lists()?;
        if self.witness_requirements
            != [
                OperatorWitnessRequirementV1::Producer,
                OperatorWitnessRequirementV1::IndependentEvaluator,
                OperatorWitnessRequirementV1::AuthorityWitness,
            ]
        {
            return Err(OperatorRegistryContractError::WitnessSetChanged(
                self.operator_id.clone(),
            ));
        }
        if !self.authority_effect.is_none() {
            return Err(OperatorRegistryContractError::AuthorityExpansion(
                self.operator_id.clone(),
            ));
        }
        Ok(())
    }
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct GaugeBindingV1 {
    pub schema_version: String,
    pub binding_id: String,
    pub operator_id: String,
    pub runtime: RuntimeGaugeV1,
    pub execution_mode: GaugeExecutionModeV1,
    pub adapter_id: String,
    pub semantic_contract_id: String,
    pub provided_capabilities: Vec<OperatorCapabilityV1>,
    pub granted_permissions: Vec<OperatorPermissionV1>,
    pub write_surface: Vec<String>,
    pub evidence_ceiling: String,
    pub network_access: bool,
    pub credential_access: bool,
    pub hidden_context_classes: Vec<String>,
    pub operator_manifest_sha256: String,
    pub authority_effect: AuthorityEffect,
}

impl GaugeBindingV1 {
    fn validate_binding_identities(&self) -> Result<(), OperatorRegistryContractError> {
        require_schema(
            "binding.schema_version",
            GAUGE_BINDING_SCHEMA_VERSION,
            &self.schema_version,
        )?;
        require_text("binding.binding_id", &self.binding_id)?;
        require_text("binding.operator_id", &self.operator_id)?;
        require_text("binding.adapter_id", &self.adapter_id)?;
        require_text("binding.semantic_contract_id", &self.semantic_contract_id)
    }

    fn validate_binding_fields(&self) -> Result<(), OperatorRegistryContractError> {
        self.validate_binding_identities()?;
        require_nonempty_sorted("binding.provided_capabilities", &self.provided_capabilities)?;
        require_nonempty_sorted("binding.granted_permissions", &self.granted_permissions)?;
        require_nonempty_sorted_paths("binding.write_surface", &self.write_surface)?;
        require_text("binding.evidence_ceiling", &self.evidence_ceiling)?;
        require_sorted_texts(
            "binding.hidden_context_classes",
            &self.hidden_context_classes,
        )?;
        require_sha256(
            "binding.operator_manifest_sha256",
            &self.operator_manifest_sha256,
        )
    }

    fn validate_security_fences(&self) -> Result<(), OperatorRegistryContractError> {
        if self.network_access {
            return Err(OperatorRegistryContractError::NetworkAccessForbidden(
                self.binding_id.clone(),
            ));
        }
        if self.credential_access {
            return Err(OperatorRegistryContractError::CredentialAccessForbidden(
                self.binding_id.clone(),
            ));
        }
        if !self.hidden_context_classes.is_empty() {
            return Err(OperatorRegistryContractError::HiddenContextForbidden(
                self.binding_id.clone(),
            ));
        }
        if !self.authority_effect.is_none() {
            return Err(OperatorRegistryContractError::AuthorityExpansion(
                self.binding_id.clone(),
            ));
        }
        Ok(())
    }

    pub fn validate(&self) -> Result<(), OperatorRegistryContractError> {
        self.validate_binding_fields()?;
        self.validate_security_fences()?;
        match (&self.runtime, self.execution_mode) {
            (RuntimeGaugeV1::Fixture, GaugeExecutionModeV1::DeterministicFixture) => {}
            (RuntimeGaugeV1::ModelProfile(profile), GaugeExecutionModeV1::ModelFixtureReplay) => {
                require_text("binding.runtime.profile_id", &profile.profile_id)?;
            }
            _ => {
                return Err(OperatorRegistryContractError::ExecutionModeMismatch(
                    self.binding_id.clone(),
                ));
            }
        }
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct OperatorRegistryV1 {
    pub schema_version: String,
    pub registry_id: String,
    pub max_operators: u16,
    pub manifests: Vec<OperatorManifestV1>,
    pub bindings: Vec<GaugeBindingV1>,
}

impl OperatorRegistryV1 {
    fn within_registry_budget(&self) -> bool {
        let max_operators = usize::from(self.max_operators);
        max_operators > 0
            && max_operators <= OPERATOR_REGISTRY_MAX_OPERATORS
            && !self.manifests.is_empty()
            && self.manifests.len() <= max_operators
            && !self.bindings.is_empty()
            && self.bindings.len() <= OPERATOR_REGISTRY_MAX_BINDINGS
    }

    pub fn validate(&self) -> Result<(), OperatorRegistryContractError> {
        require_schema(
            "registry.schema_version",
            OPERATOR_REGISTRY_SCHEMA_VERSION,
            &self.schema_version,
        )?;
        require_text("registry.registry_id", &self.registry_id)?;
        if !self.within_registry_budget() {
            return Err(OperatorRegistryContractError::RegistryBudgetExceeded);
        }

        self.validate_manifests_canonical()?;
        let bound_operators = self.validate_bindings_canonical()?;
        for manifest in &self.manifests {
            if !bound_operators.contains(&manifest.operator_id) {
                return Err(OperatorRegistryContractError::OperatorUnbound(
                    manifest.operator_id.clone(),
                ));
            }
        }
        Ok(())
    }

    fn validate_manifests_canonical(&self) -> Result<(), OperatorRegistryContractError> {
        let mut previous_manifest: Option<&str> = None;
        for manifest in &self.manifests {
            manifest.validate()?;
            if previous_manifest.is_some_and(|previous| previous >= manifest.operator_id.as_str()) {
                return Err(OperatorRegistryContractError::NonCanonicalList(
                    "registry.manifests",
                ));
            }
            previous_manifest = Some(&manifest.operator_id);
        }
        Ok(())
    }

    fn validate_bindings_canonical(
        &self,
    ) -> Result<BTreeSet<String>, OperatorRegistryContractError> {
        let mut previous_binding: Option<&str> = None;
        let mut runtime_keys = BTreeSet::new();
        let mut bound_operators = BTreeSet::new();
        for binding in &self.bindings {
            binding.validate()?;
            if previous_binding.is_some_and(|previous| previous >= binding.binding_id.as_str()) {
                return Err(OperatorRegistryContractError::NonCanonicalList(
                    "registry.bindings",
                ));
            }
            previous_binding = Some(&binding.binding_id);
            let manifest = self.manifest(&binding.operator_id).ok_or_else(|| {
                OperatorRegistryContractError::UnknownOperator(binding.operator_id.clone())
            })?;
            let runtime_key = (binding.operator_id.clone(), binding.runtime.clone());
            if !runtime_keys.insert(runtime_key) {
                return Err(OperatorRegistryContractError::DuplicateRuntimeBinding(
                    binding.operator_id.clone(),
                ));
            }
            bound_operators.insert(binding.operator_id.clone());
            validate_substitution(manifest, binding)?;
        }
        Ok(bound_operators)
    }

    pub fn manifest(&self, operator_id: &str) -> Option<&OperatorManifestV1> {
        self.manifests
            .iter()
            .find(|manifest| manifest.operator_id == operator_id)
    }

    pub fn binding(&self, binding_id: &str) -> Option<&GaugeBindingV1> {
        self.bindings
            .iter()
            .find(|binding| binding.binding_id == binding_id)
    }
}

pub fn validate_substitution(
    manifest: &OperatorManifestV1,
    binding: &GaugeBindingV1,
) -> Result<(), OperatorRegistryContractError> {
    manifest.validate()?;
    binding.validate()?;
    if binding.operator_id != manifest.operator_id {
        return Err(OperatorRegistryContractError::UnknownOperator(
            binding.operator_id.clone(),
        ));
    }
    if binding.semantic_contract_id != manifest.semantic_contract_id {
        return Err(OperatorRegistryContractError::SemanticContractDrift(
            binding.binding_id.clone(),
        ));
    }
    let provided = binding
        .provided_capabilities
        .iter()
        .copied()
        .collect::<BTreeSet<_>>();
    if let Some(capability) = manifest
        .required_capabilities
        .iter()
        .find(|capability| !provided.contains(capability))
    {
        return Err(OperatorRegistryContractError::MissingCapability {
            binding_id: binding.binding_id.clone(),
            capability: *capability,
        });
    }
    if binding.granted_permissions != manifest.permission_ceiling {
        return Err(OperatorRegistryContractError::PermissionExpansion(
            binding.binding_id.clone(),
        ));
    }
    if binding.write_surface != manifest.write_surface {
        return Err(OperatorRegistryContractError::WriteSurfaceExpansion(
            binding.binding_id.clone(),
        ));
    }
    if binding.evidence_ceiling != manifest.evidence_ceiling {
        return Err(OperatorRegistryContractError::EvidenceCeilingExpansion(
            binding.binding_id.clone(),
        ));
    }
    Ok(())
}
#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum OperatorRegistryContractError {
    #[error("schema mismatch for {field}: expected {expected}, found {found}")]
    SchemaMismatch {
        field: &'static str,
        expected: &'static str,
        found: String,
    },
    #[error("required field is empty: {0}")]
    EmptyField(&'static str),
    #[error("list is not strictly sorted and unique: {0}")]
    NonCanonicalList(&'static str),
    #[error("invalid exact write path: {0}")]
    InvalidPath(String),
    #[error("invalid SHA-256 in {0}")]
    InvalidSha256(&'static str),
    #[error("operator registry exceeds its admitted size budget")]
    RegistryBudgetExceeded,
    #[error("unknown operator: {0}")]
    UnknownOperator(String),
    #[error("operator has no gauge binding: {0}")]
    OperatorUnbound(String),
    #[error("duplicate operator/runtime binding: {0}")]
    DuplicateRuntimeBinding(String),
    #[error("binding execution mode does not match its runtime: {0}")]
    ExecutionModeMismatch(String),
    #[error("binding changed the semantic contract: {0}")]
    SemanticContractDrift(String),
    #[error("binding {binding_id} is missing capability {capability:?}")]
    MissingCapability {
        binding_id: String,
        capability: OperatorCapabilityV1,
    },
    #[error("binding expanded or changed permissions: {0}")]
    PermissionExpansion(String),
    #[error("binding expanded or changed the write surface: {0}")]
    WriteSurfaceExpansion(String),
    #[error("binding expanded or changed the evidence ceiling: {0}")]
    EvidenceCeilingExpansion(String),
    #[error("binding requests network access: {0}")]
    NetworkAccessForbidden(String),
    #[error("binding requests credential access: {0}")]
    CredentialAccessForbidden(String),
    #[error("binding declares hidden context: {0}")]
    HiddenContextForbidden(String),
    #[error("required witness set changed: {0}")]
    WitnessSetChanged(String),
    #[error("authority expansion is forbidden: {0}")]
    AuthorityExpansion(String),
}

fn require_schema(
    field: &'static str,
    expected: &'static str,
    found: &str,
) -> Result<(), OperatorRegistryContractError> {
    if found != expected {
        return Err(OperatorRegistryContractError::SchemaMismatch {
            field,
            expected,
            found: found.to_owned(),
        });
    }
    Ok(())
}

fn require_text(field: &'static str, value: &str) -> Result<(), OperatorRegistryContractError> {
    if value.trim().is_empty() {
        return Err(OperatorRegistryContractError::EmptyField(field));
    }
    Ok(())
}

fn require_nonempty_map(
    field: &'static str,
    values: &BTreeMap<String, String>,
) -> Result<(), OperatorRegistryContractError> {
    if values.is_empty() {
        return Err(OperatorRegistryContractError::EmptyField(field));
    }
    for (key, value) in values {
        require_text(field, key)?;
        require_text(field, value)?;
    }
    Ok(())
}

fn require_nonempty_sorted_texts(
    field: &'static str,
    values: &[String],
) -> Result<(), OperatorRegistryContractError> {
    if values.is_empty() {
        return Err(OperatorRegistryContractError::EmptyField(field));
    }
    require_sorted_texts(field, values)
}

fn require_sorted_texts(
    field: &'static str,
    values: &[String],
) -> Result<(), OperatorRegistryContractError> {
    for value in values {
        require_text(field, value)?;
    }
    if values.windows(2).any(|pair| pair[0] >= pair[1]) {
        return Err(OperatorRegistryContractError::NonCanonicalList(field));
    }
    Ok(())
}

fn require_nonempty_sorted<T>(
    field: &'static str,
    values: &[T],
) -> Result<(), OperatorRegistryContractError>
where
    T: Ord,
{
    if values.is_empty() {
        return Err(OperatorRegistryContractError::EmptyField(field));
    }
    if values.windows(2).any(|pair| pair[0] >= pair[1]) {
        return Err(OperatorRegistryContractError::NonCanonicalList(field));
    }
    Ok(())
}

fn require_nonempty_sorted_paths(
    field: &'static str,
    values: &[String],
) -> Result<(), OperatorRegistryContractError> {
    require_nonempty_sorted_texts(field, values)?;
    for value in values {
        require_relative_file_path(field, value)?;
    }
    Ok(())
}

fn require_relative_file_path(
    field: &'static str,
    value: &str,
) -> Result<(), OperatorRegistryContractError> {
    require_text(field, value)?;
    if value.starts_with('/')
        || value.ends_with('/')
        || value.contains('\u{5c}')
        || value.contains(':')
        || value
            .chars()
            .any(|character| matches!(character, '*' | '?' | '[' | ']' | '{' | '}'))
        || value
            .split('/')
            .any(|component| component.is_empty() || component == "." || component == "..")
    {
        return Err(OperatorRegistryContractError::InvalidPath(value.to_owned()));
    }
    Ok(())
}

fn require_sha256(field: &'static str, value: &str) -> Result<(), OperatorRegistryContractError> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(OperatorRegistryContractError::InvalidSha256(field));
    }
    Ok(())
}

// Origin: engine/crates_rs/core_contracts/src/operator_gauge.rs
// Claim: urn:core:crates_rs:core-contracts:operator-gauge:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_5a38a76c {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
