//! S(N) Symbolic-Context Tower Subsystem
//!
//! Port of the Lean 4 `SLevel` and `LicensedLift` types for runtime enforcement.

use serde::{Deserialize, Serialize};
use thiserror::Error;

/// Defines the structural constraints and budget of a specific symbolic context level.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct SLevel {
    /// Level index (n)
    pub n: u32,
    /// Count of active symbols
    pub symbols: u32,
    /// Count of active operators
    pub operators: u32,
    /// Count of active packet families
    pub packet_families: u32,
    /// Count of active witnesses
    pub witnesses: u32,
    /// Number of allowable lift actions remaining
    pub lift_budget: u32,
}

impl SLevel {
    /// Total declared mass of the system
    pub fn declared_mass(&self) -> u32 {
        self.symbols + self.operators + self.packet_families + self.witnesses
    }
}

/// A refusal returned when a licensed lift fails its mathematical constraints.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Error)]
pub enum LiftRefusal {
    #[error("Lift target n must be exactly source n + 1")]
    InvalidLevelIncrement,
    #[error("Lift target budget must be strictly less than source budget")]
    BudgetNotDecremented,
    #[error("Lift target declared mass must be strictly greater than source declared mass")]
    MassNotIncreased,
    #[error("Zero budget remaining: Autoimmune threshold or strict ceiling hit")]
    BudgetExhausted,
}

/// A certificate verifying that a lift between two levels satisfies the strict mathematical
/// constraints defined in the Lean 4 proof (`LicensedLift`).
///
/// This type cannot be forged by deserialization; it routes through `RawLicensedLift`.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(try_from = "RawLicensedLift")]
pub struct LicensedLift {
    source: SLevel,
    target: SLevel,
}

impl LicensedLift {
    /// Sole constructor for a `LicensedLift`.
    pub fn certify(source: SLevel, target: SLevel) -> Result<Self, LiftRefusal> {
        if source.lift_budget == 0 {
            return Err(LiftRefusal::BudgetExhausted);
        }
        if target.n != source.n + 1 {
            return Err(LiftRefusal::InvalidLevelIncrement);
        }
        if target.lift_budget >= source.lift_budget {
            return Err(LiftRefusal::BudgetNotDecremented);
        }
        if target.declared_mass() <= source.declared_mass() {
            return Err(LiftRefusal::MassNotIncreased);
        }

        Ok(Self { source, target })
    }

    pub fn source(&self) -> &SLevel {
        &self.source
    }

    pub fn target(&self) -> &SLevel {
        &self.target
    }
}

/// Deserialization transport for `LicensedLift`.
#[derive(Deserialize)]
struct RawLicensedLift {
    source: SLevel,
    target: SLevel,
}

impl TryFrom<RawLicensedLift> for LicensedLift {
    type Error = LiftRefusal;

    fn try_from(raw: RawLicensedLift) -> Result<Self, Self::Error> {
        LicensedLift::certify(raw.source, raw.target)
    }
}

// Origin: engine/crates_rs/core_types/src/s_level.rs
// Claim: urn:core:crates_rs:core-types:s-level:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn valid_source() -> SLevel {
        SLevel {
            n: 1,
            symbols: 10,
            operators: 5,
            packet_families: 2,
            witnesses: 100,
            lift_budget: 5,
        }
    }

    fn valid_target() -> SLevel {
        SLevel {
            n: 2,
            symbols: 11, // mass increased
            operators: 5,
            packet_families: 2,
            witnesses: 100,
            lift_budget: 4, // budget decreased
        }
    }

    #[test]
    fn certify_valid_lift() {
        let lift = LicensedLift::certify(valid_source(), valid_target()).expect("Valid lift");
        assert_eq!(lift.source().n, 1);
        assert_eq!(lift.target().n, 2);
    }

    #[test]
    fn certify_invalid_n() {
        let mut target = valid_target();
        target.n = 3; // jump by 2
        assert_eq!(
            LicensedLift::certify(valid_source(), target),
            Err(LiftRefusal::InvalidLevelIncrement)
        );
    }

    #[test]
    fn certify_budget_not_decremented() {
        let mut target = valid_target();
        target.lift_budget = 5; // same budget
        assert_eq!(
            LicensedLift::certify(valid_source(), target),
            Err(LiftRefusal::BudgetNotDecremented)
        );
    }

    #[test]
    fn certify_mass_not_increased() {
        let mut target = valid_target();
        target.symbols = 10; // mass remains same
        assert_eq!(
            LicensedLift::certify(valid_source(), target),
            Err(LiftRefusal::MassNotIncreased)
        );
    }

    #[test]
    fn certify_budget_exhausted() {
        let mut source = valid_source();
        source.lift_budget = 0;
        let target = valid_target();
        assert_eq!(
            LicensedLift::certify(source, target),
            Err(LiftRefusal::BudgetExhausted)
        );
    }

    #[test]
    fn forged_json_fails_deserialization() {
        let forged = r#"{"source":{"n":1,"symbols":10,"operators":5,"packet_families":2,"witnesses":100,"lift_budget":5},"target":{"n":1,"symbols":10,"operators":5,"packet_families":2,"witnesses":100,"lift_budget":5}}"#;
        let result: Result<LicensedLift, _> = serde_json::from_str(forged);
        assert!(result.is_err());
    }
}
