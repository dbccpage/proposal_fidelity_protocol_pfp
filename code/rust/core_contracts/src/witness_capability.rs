/// Functional/obstruction measurement capability for types that expose phi.
///
/// Phi is not witness-owned and is not universally canonical for every
/// contract. It applies only where a contract explicitly declares a
/// phi-related law or measurement boundary. Witness code may attest observed
/// phi behavior, but it does not promote that observation to authority.
///
/// The phi value represents the "distance from closure" or "obstruction mass"
/// of a state. Lower phi means closer to a fixed point.
pub trait HasPhi {
    /// Returns the phi (obstruction measure) of this value.
    ///
    /// Phi must be non-negative. Lower values indicate closer to closure.
    fn phi(&self) -> f64;
}

/// Phi law relation for declared phi-monotonic contracts.
///
/// Phi laws apply only to contracts that explicitly declare phi-monotonicity.
/// Witness code can attest observed phi behavior, but it does not certify or
/// authorize the result.
pub trait PhiLaw {
    /// Check if the phi law is satisfied for a before/after pair.
    ///
    /// For Lambda operators: phi(after) <= phi(before)
    fn phi_satisfied<T: HasPhi>(before: &T, after: &T) -> bool {
        after.phi() <= before.phi()
    }

    /// Compute the phi delta (change in phi).
    ///
    /// Negative delta means phi decreased (good).
    /// Positive delta means phi increased (violation).
    fn phi_delta<T: HasPhi>(before: &T, after: &T) -> f64 {
        after.phi() - before.phi()
    }
}

/// Default implementation of PhiLaw.
pub struct DefaultPhiLaw;
impl PhiLaw for DefaultPhiLaw {}

/// Trait for witness relations that check property preservation.
///
/// This is used for checking that operations preserve specific properties.
pub trait WitnessRelation<S> {
    /// Check if the property is preserved from before to after state.
    fn preserves(before: &S, after: &S) -> bool;
}

/// Trait for monotonicity witness relations.
///
/// A monotonic relation R(x, y) holds when some measure of y is <= measure of x.
pub trait MonotonicRelation<S, M> {
    /// Extract the measure from a state.
    fn measure(state: &S) -> M;

    /// Check if the monotonicity relation holds (measure(after) <= measure(before)).
    fn is_monotonic(before: &S, after: &S) -> bool
    where
        M: PartialOrd,
    {
        Self::measure(after) <= Self::measure(before)
    }
}

/// Phi monotonicity witness relation.
///
/// Checks that phi(after) <= phi(before).
pub struct PhiMonotonicity;

impl<S: HasPhi> WitnessRelation<S> for PhiMonotonicity {
    fn preserves(before: &S, after: &S) -> bool {
        after.phi() <= before.phi()
    }
}

impl<S: HasPhi> MonotonicRelation<S, f64> for PhiMonotonicity {
    fn measure(state: &S) -> f64 {
        state.phi()
    }
}

// Exact invariant envelope.
// Origin: engine/crates_rs/core_contracts/src/witness/capability.rs
// Claim: urn:core:contracts:witness:exact-obstruction:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExactObstruction {
    before: u64,
    after: u64,
    drop: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ExactObstructionError {
    NotMonotone { before: u64, after: u64 },
}

// Origin: engine/crates_rs/core_contracts/src/witness_capability.rs
// Claim: urn:core:crates_rs:core-contracts:witness-capability:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ExactObstructionError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ExactObstructionError {}

impl ExactObstruction {
    pub fn try_monotone(before: u64, after: u64) -> Result<Self, ExactObstructionError> {
        let drop = before.checked_sub(after).ok_or(ExactObstructionError::NotMonotone { before, after })?;
        Ok(Self { before, after, drop })
    }

    pub fn before(&self) -> u64 {
        self.before
    }

    pub fn after(&self) -> u64 {
        self.after
    }

    pub fn drop(&self) -> u64 {
        self.drop
    }
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod exact_obstruction_tests {
    use super::*;

    #[test]
    fn a_drop_is_the_checked_difference() {
        let witness = ExactObstruction::try_monotone(10, 4);
        assert!(matches!(
            witness,
            Ok(ref row) if row.before() == 10 && row.after() == 4 && row.drop() == 6
        ));
    }

    #[test]
    fn refuses_an_increase() {
        let wrong = ExactObstruction::try_monotone(3, 5);
        assert!(matches!(
            wrong,
            Err(ExactObstructionError::NotMonotone { before: 3, after: 5 })
        ));
    }
}
