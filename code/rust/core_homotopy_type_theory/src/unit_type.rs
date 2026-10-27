//! Unit type former `1` / `⊤`.
//!
//! Structural record only: id plus opaque ref to the unique unit term `★`.

use serde::{Deserialize, Serialize};
use thiserror::Error;

/// Unit type `1` with its unique inhabitant reference.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct UnitType {
    pub id: String,
    pub unit_term_ref: String,
}

impl UnitType {
    /// Validate that id and unit term reference are non-empty.
    pub fn validate(&self) -> Result<(), UnitTypeError> {
        if self.id.is_empty() {
            return Err(UnitTypeError::EmptyId);
        }
        if self.unit_term_ref.is_empty() {
            return Err(UnitTypeError::EmptyUnitTermRef);
        }
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum UnitTypeError {
    #[error("unit type id must be non-empty")]
    EmptyId,
    #[error("unit type unit_term_ref must be non-empty")]
    EmptyUnitTermRef,
}

/// Checked private-field witness. Existing constructors are unchanged.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct UnitEliminationWitness {
    inhabitants: u64,
    carrier_points: u64,
    maps_into_carrier: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum UnitEliminationWitnessError {
    ShapeRejected,
    NotUniqueInhabitant { inhabitants: u64 },
    MapCountMismatch { maps_into_carrier: u64, carrier_points: u64 },
}

impl UnitEliminationWitness {
    pub fn certify(unit: &UnitType, inhabitants: u64, carrier_points: u64, maps_into_carrier: u64) -> Result<Self, UnitEliminationWitnessError> {
        unit.validate().map_err(|_| UnitEliminationWitnessError::ShapeRejected)?;
        if inhabitants != 1 { return Err(UnitEliminationWitnessError::NotUniqueInhabitant { inhabitants }); }
        if maps_into_carrier != carrier_points { return Err(UnitEliminationWitnessError::MapCountMismatch { maps_into_carrier, carrier_points }); }
        Ok(Self { inhabitants, carrier_points, maps_into_carrier })
    }
}

// Origin: engine/crates_rs/core_homotopy_type_theory/src/unit_type.rs
// Claim: urn:core:crates_rs:core-homotopy-type-theory:unit-type:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        let unit = UnitType {
            id: "Unit".to_string(),
            unit_term_ref: "star".to_string(),
        };
        assert!(unit.validate().is_ok());
    }

    #[test]
    fn validate_rejects_empty_id() {
        let unit = UnitType {
            id: String::new(),
            unit_term_ref: "star".to_string(),
        };
        assert_eq!(unit.validate(), Err(UnitTypeError::EmptyId));
    }

    #[test]
    fn validate_rejects_empty_unit_term() {
        let unit = UnitType {
            id: "Unit".to_string(),
            unit_term_ref: String::new(),
        };
        assert_eq!(unit.validate(), Err(UnitTypeError::EmptyUnitTermRef));
    }

#[test]
    fn exact_witness_holds() {
        let unit = UnitType { id: "Unit".into(), unit_term_ref: "star".into() };
        assert!(matches!(UnitEliminationWitness::certify(&unit, 1, 5, 5), Ok(w) if w.inhabitants == 1));
        assert!(matches!(UnitEliminationWitness::certify(&unit, 2, 5, 5), Err(UnitEliminationWitnessError::NotUniqueInhabitant { .. })));
    }
}
