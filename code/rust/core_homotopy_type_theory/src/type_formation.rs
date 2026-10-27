//! Type formation records: which former built a type, at which universe.

use serde::{Deserialize, Serialize};
use thiserror::Error;

/// Which type former produced a [`TypeRecord`].
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum FormationKind {
    Base,
    Pi,
    Sigma,
    Sum,
    Identity,
    Unit,
    Empty,
    Hit,
    Other,
}

/// Finite structural record of a formed type.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct TypeRecord {
    pub id: String,
    pub universe_level: u32,
    pub formation: FormationKind,
}

impl TypeRecord {
    /// Validate structural well-formedness: id must be non-empty.
    pub fn validate(&self) -> Result<(), TypeFormationError> {
        if self.id.is_empty() {
            return Err(TypeFormationError::EmptyId);
        }
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum TypeFormationError {
    #[error("type record id must be non-empty")]
    EmptyId,
}

// Origin: engine/crates_rs/core_homotopy_type_theory/src/type_formation.rs
// Claim: urn:core:crates_rs:core-homotopy-type-theory:type-formation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok_pi_formation() {
        let t = TypeRecord {
            id: "Pi_A_B".to_string(),
            universe_level: 0,
            formation: FormationKind::Pi,
        };
        assert!(t.validate().is_ok());
    }

    #[test]
    fn validate_rejects_empty_id() {
        let t = TypeRecord {
            id: String::new(),
            universe_level: 0,
            formation: FormationKind::Base,
        };
        assert_eq!(t.validate(), Err(TypeFormationError::EmptyId));
    }

    #[test]
    fn all_formation_kinds_construct() {
        let kinds = [
            FormationKind::Base,
            FormationKind::Pi,
            FormationKind::Sigma,
            FormationKind::Sum,
            FormationKind::Identity,
            FormationKind::Unit,
            FormationKind::Empty,
            FormationKind::Hit,
            FormationKind::Other,
        ];
        for (i, formation) in kinds.into_iter().enumerate() {
            let t = TypeRecord {
                id: format!("t{i}"),
                universe_level: i as u32,
                formation,
            };
            assert!(t.validate().is_ok());
        }
    }
}

// --- exact carrier witness ---
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum UniverseFormationError {
    EmptyId,
    DeclaredLevel,
}

/// Cumulative universe levels for Pi, identity, and unit formation.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CumulativeFormer {
    record: TypeRecord,
}

impl CumulativeFormer {
    pub fn try_pi(id: &str, domain_level: u32, family_level: u32, declared: u32) -> Result<Self, UniverseFormationError> {
        if id.is_empty() {
            return Err(UniverseFormationError::EmptyId);
        }
        let level = domain_level.max(family_level);
        if declared != level {
            return Err(UniverseFormationError::DeclaredLevel);
        }
        let record = TypeRecord { id: id.to_string(), universe_level: level, formation: FormationKind::Pi };
        record.validate().map_err(|_| UniverseFormationError::EmptyId)?;
        Ok(Self { record })
    }

    pub fn try_identity(id: &str, base_level: u32, declared: u32) -> Result<Self, UniverseFormationError> {
        if id.is_empty() {
            return Err(UniverseFormationError::EmptyId);
        }
        if declared != base_level {
            return Err(UniverseFormationError::DeclaredLevel);
        }
        let record = TypeRecord { id: id.to_string(), universe_level: declared, formation: FormationKind::Identity };
        record.validate().map_err(|_| UniverseFormationError::EmptyId)?;
        Ok(Self { record })
    }

    pub fn try_cumulative_unit(id: &str, base_level: u32, declared: u32) -> Result<Self, UniverseFormationError> {
        if id.is_empty() {
            return Err(UniverseFormationError::EmptyId);
        }
        if declared < base_level {
            return Err(UniverseFormationError::DeclaredLevel);
        }
        let record = TypeRecord { id: id.to_string(), universe_level: declared, formation: FormationKind::Unit };
        record.validate().map_err(|_| UniverseFormationError::EmptyId)?;
        Ok(Self { record })
    }

    pub fn level(&self) -> u32 { self.record.universe_level }
}

#[cfg(test)]
mod universe_tests {
    use super::*;

    #[test]
    fn pi_sits_at_the_maximum_of_the_domain_and_family() {
        let former = CumulativeFormer::try_pi("Pi", 1, 3, 3);
        assert!(matches!(former, Ok(ref former) if former.level() == 3));
    }

    #[test]
    fn a_lower_declared_pi_level_is_refused() {
        let former = CumulativeFormer::try_pi("Pi", 1, 3, 2);
        assert!(matches!(former, Err(UniverseFormationError::DeclaredLevel)));
    }
}
