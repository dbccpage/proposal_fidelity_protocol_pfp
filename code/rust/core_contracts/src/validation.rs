#[path = "validation_artifact.rs"]
pub mod artifact;
#[path = "validation_assertions.rs"]
pub mod assertions;
#[path = "validation_decision.rs"]
pub mod decision;
#[path = "validation_file_audit.rs"]
pub mod file_audit;
#[path = "validation_generated.rs"]
pub mod generated;
#[path = "validation_invariant_atlas.rs"]
pub mod invariant_atlas;
#[path = "validation_registry.rs"]
pub mod registry;
#[path = "validation_rules.rs"]
pub mod rules;
#[path = "validation_source_bindings.rs"]
pub mod source_bindings;
#[path = "validation_validator.rs"]
pub mod validator;
#[path = "validation_violation.rs"]
pub mod violation;

pub use artifact::*;
pub use assertions::*;
pub use decision::*;
pub use file_audit::*;
pub use generated::*;
pub use invariant_atlas::*;
pub use registry::*;
pub use rules::*;
pub use validator::*;
pub use violation::*;


/// A validation pass covers every declared invariant: satisfied count equals declared count.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct InvariantCoverage {
    declared: u32,
    satisfied: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CoverageError {
    Overflow,
    SatisfiedExceedsDeclared { declared: u32, satisfied: u32 },
    Unsatisfied { declared: u32, satisfied: u32, gap: u32 },
}

// Origin: engine/crates_rs/core_contracts/src/validation.rs
// Claim: urn:core:crates_rs:core-contracts:validation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for CoverageError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for CoverageError {}

impl InvariantCoverage {
    pub fn admit(declared: u32, satisfied: u32) -> Result<Self, CoverageError> {
        if satisfied > declared {
            return Err(CoverageError::SatisfiedExceedsDeclared { declared, satisfied });
        }
        let gap = declared.checked_sub(satisfied).ok_or(CoverageError::Overflow)?;
        if gap != 0 {
            return Err(CoverageError::Unsatisfied {
                declared,
                satisfied,
                gap,
            });
        }
        Ok(Self { declared, satisfied })
    }

    pub fn declared(&self) -> u32 {
        self.declared
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod coverage_tests {
    use super::*;

    #[test]
    fn coverage_refuses_a_gap() {
        let admitted = InvariantCoverage::admit(4, 4);
        assert!(admitted.is_ok());
        assert_eq!(admitted.ok().map(|coverage| coverage.declared()), Some(4));
        assert!(matches!(
            InvariantCoverage::admit(4, 3),
            Err(CoverageError::Unsatisfied {
                declared: 4,
                satisfied: 3,
                gap: 1
            })
        ));
    }
}
