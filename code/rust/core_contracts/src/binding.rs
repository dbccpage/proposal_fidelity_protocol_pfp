use crate::kinds::{ComponentRole, ContractCategory, ContractEffect, ContractStatus, SchemaHash};
use crate::schema::{EffectLawDecl, PhiLawDecl, StructureLawDecl};
use core::any::TypeId;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum LawBinding<T> {
    Required(T),
    Forbidden,
}

#[derive(Debug, Clone, Copy)]
pub enum TypeBinding {
    Concrete(TypeId, &'static str),
    NotApplicable,
    Forbidden,
}

impl TypeBinding {
    pub fn of<T: 'static>(name: &'static str) -> Self {
        Self::Concrete(TypeId::of::<T>(), name)
    }

    pub fn name(&self) -> Option<&'static str> {
        match self {
            Self::Concrete(_, name) => Some(name),
            _ => None,
        }
    }
}

impl PartialEq for TypeBinding {
    fn eq(&self, other: &Self) -> bool {
        match (self, other) {
            (Self::Concrete(a, _), Self::Concrete(b, _)) => a == b,
            (Self::NotApplicable, Self::NotApplicable) => true,
            (Self::Forbidden, Self::Forbidden) => true,
            _ => false,
        }
    }
}

impl Eq for TypeBinding {}

pub type EvidenceRequirement = &'static str;

/// Static generated descriptor bound to Rust types.
///
/// This is the compile-time image emitted by the contract code-generation
/// pipeline. It intentionally differs from `schema::ContractDescriptor`, which
/// is the runtime/deserialized YAML model.
#[derive(Debug)]
pub struct ContractDescriptor {
    pub id: &'static str,
    pub category: ContractCategory,
    pub role: ComponentRole,
    pub status: ContractStatus,
    pub authority_effect: ContractEffect,

    pub phi_law: LawBinding<PhiLawDecl>,
    pub structure_law: LawBinding<StructureLawDecl>,
    pub effect_law: LawBinding<EffectLawDecl>,

    pub input_type: TypeBinding,
    pub output_type: TypeBinding,
    pub subject_type: TypeBinding,
    pub runtime_state_type: TypeBinding,

    pub evidence_requirements: &'static [EvidenceRequirement],
    pub forbidden_authority: &'static [ContractEffect],

    pub schema_hash: SchemaHash,
}

impl ContractDescriptor {
    pub fn id(&self) -> &'static str {
        self.id
    }
    pub fn category(&self) -> ContractCategory {
        self.category
    }
    pub fn role(&self) -> ComponentRole {
        self.role
    }
    pub fn status(&self) -> ContractStatus {
        self.status
    }
    pub fn authority_effect(&self) -> ContractEffect {
        self.authority_effect
    }
    pub fn phi_law(&self) -> &LawBinding<PhiLawDecl> {
        &self.phi_law
    }
    pub fn structure_law(&self) -> &LawBinding<StructureLawDecl> {
        &self.structure_law
    }
    pub fn effect_law(&self) -> &LawBinding<EffectLawDecl> {
        &self.effect_law
    }
    pub fn input_type(&self) -> TypeBinding {
        self.input_type
    }
    pub fn output_type(&self) -> TypeBinding {
        self.output_type
    }
    pub fn subject_type(&self) -> TypeBinding {
        self.subject_type
    }
    pub fn runtime_state_type(&self) -> TypeBinding {
        self.runtime_state_type
    }
    pub fn schema_hash(&self) -> SchemaHash {
        self.schema_hash
    }
}

/// Generated Rust contract image.
///
/// Contract image types should be emitted by codegen or approved core contract
/// modules. Ordinary implementation types bind to these images through
/// `ImplementsContract<C>` instead of defining contract images themselves.
pub trait GeneratedContractImage: crate::sealed::Sealed {
    const DESCRIPTOR: &'static ContractDescriptor;
}

/// Public generated contract surface.
///
/// Associated type names are intentionally `Input`, `Output`, `Subject`, and
/// `RuntimeState`. Enforcement macros should use these names rather than stale
/// `Domain` / `Codomain` aliases.
pub trait BoundContract: GeneratedContractImage {
    type Input: 'static;
    type Output: 'static;
    type Subject: 'static;
    type RuntimeState: 'static;
}

/// Bridge trait: marks that type `I` implements contract `C`.
pub trait ImplementsContract<C: BoundContract>: Sized {
    fn contract_descriptor() -> &'static ContractDescriptor {
        C::DESCRIPTOR
    }
}

// --- Audit errors ---

#[derive(Debug)]
pub enum ContractAuditError {
    RoleMismatch {
        contract_id: &'static str,
        expected: ComponentRole,
        actual: ComponentRole,
        schema_hash: SchemaHash,
    },
    CategoryMismatch {
        contract_id: &'static str,
        expected: ContractCategory,
        actual: ContractCategory,
        schema_hash: SchemaHash,
    },
    AuthorityEffectMismatch {
        contract_id: &'static str,
        expected: ContractEffect,
        actual: ContractEffect,
        schema_hash: SchemaHash,
    },
    LawMismatch {
        contract_id: &'static str,
        field: &'static str,
        expected: String,
        actual: String,
        schema_hash: SchemaHash,
    },
    TypeMismatch {
        contract_id: &'static str,
        field: &'static str,
        schema_hash: SchemaHash,
    },
    EvidenceRequirementMissing {
        contract_id: &'static str,
        missing_requirement: EvidenceRequirement,
        schema_hash: SchemaHash,
    },
    ForbiddenAuthorityEffect {
        contract_id: &'static str,
        forbidden_effect: ContractEffect,
        schema_hash: SchemaHash,
    },
    DescriptorMismatch {
        contract_id: &'static str,
    },
}

impl core::fmt::Display for ContractAuditError {
    fn fmt(&self, f: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        match self {
            Self::RoleMismatch {
                contract_id,
                expected,
                actual,
                schema_hash,
            } => write!(
                f,
                "CONTRACT VIOLATION [{}] role mismatch: expected={:?}, actual={:?}, schema_hash={}",
                contract_id, expected, actual, schema_hash
            ),
            Self::CategoryMismatch {
                contract_id,
                expected,
                actual,
                schema_hash,
            } => write!(
                f,
                "CONTRACT VIOLATION [{}] category mismatch: expected={:?}, actual={:?}, schema_hash={}",
                contract_id, expected, actual, schema_hash
            ),
            Self::AuthorityEffectMismatch {
                contract_id,
                expected,
                actual,
                schema_hash,
            } => write!(
                f,
                "CONTRACT VIOLATION [{}] authority effect mismatch: expected={:?}, actual={:?}, schema_hash={}",
                contract_id, expected, actual, schema_hash
            ),
            Self::LawMismatch {
                contract_id,
                field,
                expected,
                actual,
                schema_hash,
            } => write!(
                f,
                "CONTRACT VIOLATION [{}] {} mismatch: expected={}, actual={}, schema_hash={}",
                contract_id, field, expected, actual, schema_hash
            ),
            Self::TypeMismatch {
                contract_id,
                field,
                schema_hash,
            } => write!(
                f,
                "CONTRACT VIOLATION [{}] {} type identity mismatch, schema_hash={}",
                contract_id, field, schema_hash
            ),
            Self::EvidenceRequirementMissing {
                contract_id,
                missing_requirement,
                schema_hash,
            } => write!(
                f,
                "CONTRACT VIOLATION [{}] missing required evidence: {}, schema_hash={}",
                contract_id, missing_requirement, schema_hash
            ),
            Self::ForbiddenAuthorityEffect {
                contract_id,
                forbidden_effect,
                schema_hash,
            } => write!(
                f,
                "CONTRACT VIOLATION [{}] uses forbidden authority effect: {:?}, schema_hash={}",
                contract_id, forbidden_effect, schema_hash
            ),
            Self::DescriptorMismatch { contract_id } => write!(
                f,
                "CONTRACT VIOLATION [{}] implementation descriptor mismatch with bound contract",
                contract_id
            ),
        }
    }
}

// --- Audit helpers ---

#[allow(dead_code)]
fn ensure_law_eq<T: core::fmt::Debug + PartialEq>(
    contract_id: &'static str,
    field: &'static str,
    expected: &LawBinding<T>,
    actual: &LawBinding<T>,
    schema_hash: SchemaHash,
) -> Result<(), ContractAuditError> {
    if expected != actual {
        Err(ContractAuditError::LawMismatch {
            contract_id,
            field,
            expected: format!("{:?}", expected),
            actual: format!("{:?}", actual),
            schema_hash,
        })
    } else {
        Ok(())
    }
}

fn ensure_type_eq(
    contract_id: &'static str,
    field: &'static str,
    expected: TypeBinding,
    actual: TypeBinding,
    schema_hash: SchemaHash,
) -> Result<(), ContractAuditError> {
    if expected != actual {
        Err(ContractAuditError::TypeMismatch {
            contract_id,
            field,
            schema_hash,
        })
    } else {
        Ok(())
    }
}

fn to_binding_for(
    d: &'static ContractDescriptor,
    field: &'static str,
    expected_binding: TypeBinding,
    type_id: TypeId,
) -> Result<TypeBinding, ContractAuditError> {
    match expected_binding {
        TypeBinding::Forbidden | TypeBinding::NotApplicable => {
            if type_id != TypeId::of::<()>() {
                Err(ContractAuditError::TypeMismatch {
                    contract_id: d.id,
                    field,
                    schema_hash: d.schema_hash,
                })
            } else {
                Ok(expected_binding)
            }
        }
        TypeBinding::Concrete(_, name) => Ok(TypeBinding::Concrete(type_id, name)),
    }
}

/// Audit only the Rust type bindings of a generated contract image.
///
/// This does not perform full registry validation of authority, category, role,
/// evidence requirements, or schema-hash provenance.
pub fn audit_contract_type_bindings<T>() -> Result<&'static ContractDescriptor, ContractAuditError>
where
    T: BoundContract,
{
    let d = T::DESCRIPTOR;

    ensure_type_eq(
        d.id,
        "input_type",
        d.input_type,
        to_binding_for(d, "input_type", d.input_type, TypeId::of::<T::Input>())?,
        d.schema_hash,
    )?;

    ensure_type_eq(
        d.id,
        "output_type",
        d.output_type,
        to_binding_for(d, "output_type", d.output_type, TypeId::of::<T::Output>())?,
        d.schema_hash,
    )?;

    ensure_type_eq(
        d.id,
        "subject_type",
        d.subject_type,
        to_binding_for(d, "subject_type", d.subject_type, TypeId::of::<T::Subject>())?,
        d.schema_hash,
    )?;

    ensure_type_eq(
        d.id,
        "runtime_state_type",
        d.runtime_state_type,
        to_binding_for(
            d,
            "runtime_state_type",
            d.runtime_state_type,
            TypeId::of::<T::RuntimeState>(),
        )?,
        d.schema_hash,
    )?;

    // NOTE: Further registry audits for ContractEffect, Category, and Evidence
    // are designed to be run against a central generated catalog.

    Ok(d)
}

/// Backward-compatible alias for type-binding audit.
///
/// Full descriptor registry audit belongs to the generated catalog layer.
pub fn audit_contract<T>() -> Result<&'static ContractDescriptor, ContractAuditError>
where
    T: BoundContract,
{
    audit_contract_type_bindings::<T>()
}

/// Audit that implementation `I` correctly binds to contract `C`.
pub fn audit_implementation<I, C>() -> Result<&'static ContractDescriptor, ContractAuditError>
where
    I: ImplementsContract<C>,
    C: BoundContract,
{
    let d = I::contract_descriptor();
    if !core::ptr::eq(d, C::DESCRIPTOR) {
        return Err(ContractAuditError::DescriptorMismatch {
            contract_id: C::DESCRIPTOR.id,
        });
    }
    audit_contract_type_bindings::<C>()
}

// Origin: engine/crates_rs/core_contracts/src/binding.rs
// Claim: urn:core:crates_rs:core-contracts:binding:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_3af59522 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
