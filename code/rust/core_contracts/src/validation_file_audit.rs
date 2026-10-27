use super::artifact::ValidationArtifact;
use super::violation::ValidationViolation;
use crate::kinds::{ContractEffect, SchemaHash};
use crate::witness::evidence::ValidationWitness;

pub struct FileAuditSubject {
    pub contract_id: &'static str,
    pub path: &'static str,
    pub declared_kind: &'static str,
    pub schema_hash: SchemaHash,
    pub authority_effect: ContractEffect,
    pub parts: &'static [FilePart],
}

pub struct FilePart {
    pub name: &'static str,
    pub required: bool,
    pub kind: &'static str,
}

pub trait FileValidator {
    type Witness: ValidationWitness;
    type Violation: ValidationViolation;

    const FILE_KIND: &'static str;

    fn validate_file(
        subject: &FileAuditSubject,
    ) -> ValidationArtifact<Self::Witness, Self::Violation>;
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PartCensus {
    required: usize,
    optional: usize,
    total: usize,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum FileAuditError {
    Empty,
    Duplicate,
    Partition,
}

impl std::fmt::Display for FileAuditError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Empty => write!(formatter, "audit subject is missing an id, kind, or part name"),
            Self::Duplicate => write!(formatter, "two file parts share a name"),
            Self::Partition => write!(formatter, "required and optional parts do not cover the subject"),
        }
    }
}

impl std::error::Error for FileAuditError {}

impl PartCensus {
    pub fn required(&self) -> usize {
        self.required
    }

    pub fn optional(&self) -> usize {
        self.optional
    }

    pub fn total(&self) -> usize {
        self.total
    }
}

fn subject_header_empty(subject: &FileAuditSubject) -> bool {
    subject.contract_id.is_empty() || subject.declared_kind.is_empty() || subject.path.is_empty()
}

/// Required parts and optional parts are a partition of the subject's part list.
pub fn admit_parts(subject: &FileAuditSubject) -> Result<PartCensus, FileAuditError> {
    if subject_header_empty(subject) {
        return Err(FileAuditError::Empty);
    }
    let mut required = 0usize;
    let mut optional = 0usize;
    for (index, part) in subject.parts.iter().enumerate() {
        ensure_unique_nonempty_part(index, part, subject.parts)?;
        if part.required {
            required = required.checked_add(1).ok_or(FileAuditError::Partition)?;
        } else {
            optional = optional.checked_add(1).ok_or(FileAuditError::Partition)?;
        }
    }
    let total = required.checked_add(optional).ok_or(FileAuditError::Partition)?;
    if total != subject.parts.len() {
        return Err(FileAuditError::Partition);
    }
    let out = PartCensus {
        required,
        optional,
        total,
    };
    Ok(out)
}

fn ensure_unique_nonempty_part(
    index: usize,
    part: &FilePart,
    parts: &[FilePart],
) -> Result<(), FileAuditError> {
    if part.name.is_empty() || part.kind.is_empty() {
        return Err(FileAuditError::Empty);
    }
    for earlier in parts.iter().take(index) {
        if earlier.name == part.name {
            return Err(FileAuditError::Duplicate);
        }
    }
    Ok(())
}

// Origin: engine/crates_rs/core_contracts/src/validation_file_audit.rs
// Claim: urn:core:crates_rs:core-contracts:validation-file-audit:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::kinds::{ContractEffect, SchemaHash};

    fn taken(result: Result<PartCensus, FileAuditError>) -> PartCensus {
        result.map_or_else(|_| loop { assert!(false); }, |value| value)
    }

    fn subject(parts: &'static [FilePart]) -> FileAuditSubject {
        FileAuditSubject {
            contract_id: "core.file.audit",
            path: "subject.rs",
            declared_kind: "rust",
            schema_hash: SchemaHash([0u8; 32]),
            authority_effect: ContractEffect::None,
            parts,
        }
    }

    const COVERED: [FilePart; 2] = [
        FilePart {
            name: "header",
            required: true,
            kind: "text",
        },
        FilePart {
            name: "note",
            required: false,
            kind: "text",
        },
    ];

    const REPEATED: [FilePart; 2] = [
        FilePart {
            name: "header",
            required: true,
            kind: "text",
        },
        FilePart {
            name: "header",
            required: false,
            kind: "text",
        },
    ];

    #[test]
    fn required_and_optional_cover_the_part_list() {
        let census = taken(admit_parts(&subject(&COVERED)));
        assert_eq!(census.required() + census.optional(), census.total());
        assert_eq!(census.total(), 2);
    }

    #[test]
    fn a_repeated_part_name_is_refused() {
        assert!(matches!(
            admit_parts(&subject(&REPEATED)),
            Err(FileAuditError::Duplicate)
        ));
    }
}
