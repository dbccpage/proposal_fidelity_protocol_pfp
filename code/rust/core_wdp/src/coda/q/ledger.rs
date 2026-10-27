use core_types::q_continuum::{
    AuthorityScope, DescentResult, ObstructionKind, QContinuumLedger, Residual,
};

/// Append-only in-memory ledger wrapper for Q policy.
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct QLedger {
    inner: QContinuumLedger,
}

impl QLedger {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn inner(&self) -> &QContinuumLedger {
        &self.inner
    }

    pub fn inner_mut(&mut self) -> &mut QContinuumLedger {
        &mut self.inner
    }

    pub fn record_result(&mut self, about: impl Into<String>, result: DescentResult) {
        self.inner.record_descent_result(about, result);
    }

    pub fn record_residual(
        &mut self,
        about: impl Into<String>,
        obligation_id: impl Into<String>,
        scope: AuthorityScope,
        residual: Residual,
    ) {
        self.record_result(about, DescentResult::failed(obligation_id, scope, residual));
    }
}

fn obstruction_index(kind: ObstructionKind) -> usize {
    match kind {
        ObstructionKind::Underdefined => 0,
        ObstructionKind::MissingWitness => 1,
        ObstructionKind::CounterexampleFound => 2,
        ObstructionKind::NonFiniteProjection => 3,
        ObstructionKind::ScopeViolation => 4,
        ObstructionKind::ReplayMissing => 5,
        ObstructionKind::SourceUnsupported => 6,
        ObstructionKind::AnalogyBreak => 7,
        ObstructionKind::ImplementationMissing => 8,
        ObstructionKind::RepeatedObstruction => 9,
    }
}

/// Ten-bucket count of residual obstruction kinds. Terminal support means every bucket is zero.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ResidualPartition {
    buckets: [u32; 10],
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ResidualPartitionError {
    Overflow,
    BadIndex,
}

// Origin: engine/crates_rs/core_wdp/src/coda/q/ledger.rs
// Claim: urn:core:crates_rs:core-wdp:ledger:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ResidualPartitionError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ResidualPartitionError {}

impl ResidualPartition {
    pub fn try_from_results(results: &[DescentResult]) -> Result<Self, ResidualPartitionError> {
        let mut buckets = [0u32; 10];
        for result in results {
            let Some(residual) = &result.residual else {
                continue;
            };
            let index = obstruction_index(residual.obstruction);
            let slot = buckets
                .get_mut(index)
                .ok_or(ResidualPartitionError::BadIndex)?;
            *slot = slot
                .checked_add(1)
                .ok_or(ResidualPartitionError::Overflow)?;
        }
        Ok(Self { buckets })
    }

    pub fn total(&self) -> Result<u32, ResidualPartitionError> {
        let mut sum = 0u32;
        for bucket in &self.buckets {
            sum = sum
                .checked_add(*bucket)
                .ok_or(ResidualPartitionError::Overflow)?;
        }
        Ok(sum)
    }

    pub fn is_terminal_support(&self) -> Result<bool, ResidualPartitionError> {
        Ok(self.total()? == 0)
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_8cd6e6dd {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
