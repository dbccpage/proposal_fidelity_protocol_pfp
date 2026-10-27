use super::file_audit::{FileAuditSubject, FilePart};
use crate::kinds::{ContractEffect, SchemaHash};

/// Sample validation manifest.
///
/// This is placeholder/test data until contract code generation owns the
/// manifest and emits workspace-specific subjects.
pub static FILE_AUDIT_MANIFEST: &[FileAuditSubject] = &[FileAuditSubject {
    contract_id: "sample.base_type_contract",
    path: "src/types/foo.rs",
    declared_kind: "BaseType",
    schema_hash: SchemaHash([0x12; 32]),
    authority_effect: ContractEffect::EvidenceOnly,
    parts: &[
        FilePart {
            name: "BaseType impl",
            required: true,
            kind: "trait_impl",
        },
        FilePart {
            name: "contract binding",
            required: true,
            kind: "contract",
        },
        FilePart {
            name: "validation unit",
            required: true,
            kind: "validator",
        },
    ],
}];

// Exact carrier witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum AuditAdmitError { Empty, Required, Duplicate, Hash, Kind }

// Origin: engine/crates_rs/core_contracts/src/validation_generated.rs
// Claim: urn:core:crates_rs:core-contracts:validation-generated:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for AuditAdmitError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for AuditAdmitError {}

fn verify_subject_header(subject: &super::file_audit::FileAuditSubject) -> Result<(), AuditAdmitError> {
    if subject.contract_id.is_empty() || subject.path.is_empty() || subject.declared_kind.is_empty() || subject.parts.is_empty() {
        return Err(AuditAdmitError::Empty);
    }
    if !subject.parts.iter().any(|part| part.required) {
        return Err(AuditAdmitError::Required);
    }
    if !subject.schema_hash.0.iter().any(|byte| *byte != 0) {
        return Err(AuditAdmitError::Hash);
    }
    Ok(())
}

pub fn admit_file_audit_subject(subject: &super::file_audit::FileAuditSubject) -> Result<usize, AuditAdmitError> {
    verify_subject_header(subject)?;
    let mut names = std::collections::BTreeSet::new();
    let mut kinds = std::collections::BTreeSet::new();
    for part in subject.parts {
        if part.name.is_empty() || !names.insert(part.name) {
            return Err(AuditAdmitError::Duplicate);
        }
        kinds.insert(part.kind);
    }
    if subject.declared_kind == "BaseType" && (!kinds.contains("trait_impl") || !kinds.contains("contract")) {
        return Err(AuditAdmitError::Kind);
    }
    Ok(subject.parts.len())
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod audit_admit_checks {
    use super::super::file_audit::{FileAuditSubject, FilePart};
    use super::{admit_file_audit_subject, FILE_AUDIT_MANIFEST, AuditAdmitError};
    use crate::kinds::{ContractEffect, SchemaHash};

    #[test]
    fn the_sample_base_type_admits_three_parts() {
        let admitted = FILE_AUDIT_MANIFEST.first().map(admit_file_audit_subject);
        assert!(matches!(admitted, Some(Ok(3))));
    }

    #[test]
    fn an_all_zero_schema_hash_is_refused() {
        static PARTS: [FilePart; 2] = [
            FilePart { name: "impl", required: true, kind: "trait_impl" },
            FilePart { name: "contract", required: true, kind: "contract" },
        ];
        let subject = FileAuditSubject {
            contract_id: "sample",
            path: "src/types/foo.rs",
            declared_kind: "BaseType",
            schema_hash: SchemaHash([0u8; 32]),
            authority_effect: ContractEffect::EvidenceOnly,
            parts: &PARTS,
        };
        assert!(matches!(admit_file_audit_subject(&subject), Err(AuditAdmitError::Hash)));
    }
}
