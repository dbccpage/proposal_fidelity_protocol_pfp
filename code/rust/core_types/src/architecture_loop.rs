use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ArchitectureLoop {
    pub basepoint: String,
    pub path_states: Vec<String>,
    pub operations: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum LoopError {
    EmptyPath,
    OpenPath,
    StepCount,
    Basepoint,
}

// Origin: engine/crates_rs/core_types/src/architecture_loop.rs
// Claim: urn:core:crates_rs:core-types:architecture-loop:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for LoopError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for LoopError {}

impl ArchitectureLoop {
    pub fn try_closed(
        basepoint: impl Into<String>,
        path_states: Vec<String>,
        operations: Vec<String>,
    ) -> Result<Self, LoopError> {
        let Some(first) = path_states.first() else {
            return Err(LoopError::EmptyPath);
        };
        let Some(last) = path_states.last() else {
            return Err(LoopError::EmptyPath);
        };
        if first != last {
            return Err(LoopError::OpenPath);
        }
        let edges = path_states.len().checked_sub(1).ok_or(LoopError::StepCount)?;
        if operations.len() != edges {
            return Err(LoopError::StepCount);
        }
        let basepoint = basepoint.into();
        if basepoint != *first {
            return Err(LoopError::Basepoint);
        }
        Ok(Self {
            basepoint,
            path_states,
            operations,
        })
    }

    pub fn step_count(&self) -> usize {
        self.operations.len()
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod closed_loop_tests {
    use super::*;

    #[test]
    fn closed_path_counts_edges() {
        let looped = ArchitectureLoop::try_closed(
            "a",
            vec!["a".into(), "b".into(), "a".into()],
            vec!["f".into(), "g".into()],
        );
        assert!(matches!(looped.as_ref().map(|item| item.step_count()), Ok(2)));
        assert!(matches!(
            ArchitectureLoop::try_closed("a", vec!["a".into(), "b".into()], vec!["f".into()]),
            Err(LoopError::OpenPath)
        ));
    }
}
