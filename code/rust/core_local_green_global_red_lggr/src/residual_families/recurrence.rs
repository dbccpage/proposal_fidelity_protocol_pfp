//! Registry-exercise accounting.
//!
//! [`registry_hit_recurrence`] counts distinct shape keys with `hits >= 2`.
//! NOT a Phi_1 measurement — the system-wide $\Phi_1$ closure for the
//! packet's $Q^1$ depends on consumer-side wiring (`core_solvers`,
//! `core_epk`, `pfp` consulting [`crate::residual_families::FamilyRegistry::lookup`]
//! before re-deriving). That wiring is `defer: PD-RF-PHI1-WIRING` -> successor
//! packet `core_residual_families_wiring_packet.md` (not yet authored).

use crate::residual_families::registry::FamilyRegistry;

/// Number of distinct shape keys in `reg` whose `hits >= 2`.
///
/// Measures **registry exercise** — i.e. how often the lookup surface saw the
/// same shape more than once. NOT a Phi_1 measurement.
///
/// Downstream consumers (solvers / EPK / Symbol Game) closing
/// $\Phi_1$ system-wide would require this module's `lookup` to be CALLED before
/// re-deriving residuals, which is `defer: PD-RF-PHI1-WIRING` and out of scope
/// for the registry crate itself.
#[must_use]
pub fn registry_hit_recurrence(reg: &FamilyRegistry) -> u64 {
    reg.iter_records().filter(|rec| rec.hits >= 2).count() as u64
}

// Exact carrier witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RegistryExercisePartition { recurrent: u64, once: u64 }

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ExerciseError { ZeroHits, Overflow, Recurrence }

// Origin: engine/crates_rs/core_local_green_global_red_lggr/src/residual_families/recurrence.rs
// Claim: urn:core:crates_rs:core-local-green-global-red-lggr:recurrence:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ExerciseError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ExerciseError {}

impl RegistryExercisePartition {
    pub fn recurrent(&self) -> u64 { self.recurrent }
    pub fn once(&self) -> u64 { self.once }
}

/// Split registry hits into once and recurrent, and match `registry_hit_recurrence`.
pub fn partition_registry_exercise(reg: &FamilyRegistry) -> Result<RegistryExercisePartition, ExerciseError> {
    let mut recurrent = 0u64;
    let mut once = 0u64;
    for record in reg.iter_records() {
        if record.hits == 0 {
            return Err(ExerciseError::ZeroHits);
        } else if record.hits == 1 {
            once = once.checked_add(1).ok_or(ExerciseError::Overflow)?;
        } else {
            recurrent = recurrent.checked_add(1).ok_or(ExerciseError::Overflow)?;
        }
    }
    if recurrent != registry_hit_recurrence(reg) {
        return Err(ExerciseError::Recurrence);
    }
    Ok(RegistryExercisePartition { recurrent, once })
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod exercise_checks {
    use super::*;
    use crate::residual_families::record::{Gamma2ClassId, Q1ClassId};
    use crate::residual_families::signature::ShapeSignature;

    #[test]
    fn one_repeat_and_one_single_hit_partition() {
        let mut reg = FamilyRegistry::new();
        let repeated = ShapeSignature::from_bytes([1u8; 32]);
        reg.record(repeated, Q1ClassId::from_u64(1), Gamma2ClassId::from_u64(1));
        reg.record(repeated, Q1ClassId::from_u64(1), Gamma2ClassId::from_u64(1));
        reg.record(ShapeSignature::from_bytes([2u8; 32]), Q1ClassId::from_u64(3), Gamma2ClassId::from_u64(4));
        let part = partition_registry_exercise(&reg);
        assert!(matches!(part, Ok(p) if p.recurrent() == 1 && p.once() == 1 && p.recurrent() == registry_hit_recurrence(&reg)));
    }

    #[test]
    fn an_empty_registry_partitions_to_zero() {
        let reg = FamilyRegistry::new();
        assert!(matches!(partition_registry_exercise(&reg), Ok(p) if p.recurrent() == 0 && p.once() == 0));
    }
}
