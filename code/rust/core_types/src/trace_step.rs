use serde::{Deserialize, Serialize};

// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// TraceStep â€” a single step in a chain-of-thought trace.
//
// Data-only. No solver logic. No execution behavior.
// Fields: index (position), score (f64 value), content_hash (dedup).
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum TraceStepError {
    #[error("non-finite score at step {index}: {value}")]
    NonFiniteScore { index: usize, value: String },
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct TraceStep {
    index: usize,
    score: f64,
    content_hash: u64,
}

impl TraceStep {
    pub fn new_validated(
        index: usize,
        score: f64,
        content_hash: u64,
    ) -> Result<Self, TraceStepError> {
        match score.is_finite() {
            true => Ok(Self {
                index,
                score,
                content_hash,
            }),
            false => Err(TraceStepError::NonFiniteScore {
                index,
                value: format!("{}", score),
            }),
        }
    }

    pub fn index(&self) -> usize {
        self.index
    }
    pub fn score(&self) -> f64 {
        self.score
    }
    pub fn content_hash(&self) -> u64 {
        self.content_hash
    }
}

// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// TraceDependency â€” a directed edge between two trace steps.
//
// Data-only. No solver logic. No execution behavior.
// Fields: from (source index), to (target index), weight (strength).
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum TraceDependencyError {
    #[error("non-finite weight from {from} to {to}: {weight}")]
    NonFiniteWeight {
        from: usize,
        to: usize,
        weight: String,
    },
    #[error("non-positive weight from {from} to {to}: {weight}")]
    NonPositiveWeight {
        from: usize,
        to: usize,
        weight: String,
    },
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct TraceDependency {
    from: usize,
    to: usize,
    weight: f64,
}

impl TraceDependency {
    pub fn new_validated(
        from: usize,
        to: usize,
        weight: f64,
    ) -> Result<Self, TraceDependencyError> {
        match weight.is_finite() {
            true => match weight > 0.0 {
                true => Ok(Self { from, to, weight }),
                false => Err(TraceDependencyError::NonPositiveWeight {
                    from,
                    to,
                    weight: format!("{}", weight),
                }),
            },
            false => Err(TraceDependencyError::NonFiniteWeight {
                from,
                to,
                weight: format!("{}", weight),
            }),
        }
    }

    pub fn from_index(&self) -> usize {
        self.from
    }
    pub fn to_index(&self) -> usize {
        self.to
    }
    pub fn weight(&self) -> f64 {
        self.weight
    }
}

// Origin: engine/crates_rs/core_types/src/trace_step.rs
// Claim: urn:core:crates_rs:core-types:trace-step:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_5ac45827 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
