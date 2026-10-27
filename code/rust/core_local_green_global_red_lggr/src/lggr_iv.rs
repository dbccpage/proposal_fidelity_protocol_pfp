//! LGGR IV — Finite presentations, compatible inverse-system threads, and completion reflection.
//!
//! Models a finite stage tower $X_N \xrightarrow{\pi_{N-1}} \cdots \xrightarrow{\pi_0} X_0$
//! with an explicit subset $S \subseteq X_N$ of original source witnesses.
//! Distinguishes a compatible thread in the finite inverse limit from an element
//! lifted from the original source $S$.
//!
//! AuthorityEffect: None.

use serde::{Deserialize, Serialize};
use thiserror::Error;

/// Canonical schema for LGGR IV completion reflection reports.
pub const LGGR_IV_COMPLETION_SCHEMA: &str = "core.epk.lggr-iv-completion.v1";

/// Errors encountered when validating a finite inverse tower or thread.
#[derive(Debug, Clone, PartialEq, Eq, Error, Serialize, Deserialize)]
pub enum LggrIvError {
    #[error("tower must have at least one transition map")]
    EmptyTower,
    #[error("stage {stage} transition table is empty")]
    EmptyStage { stage: usize },
    #[error("stage {stage} maps element {element} to out-of-range target {target} (codomain size {codomain_size})")]
    TargetOutOfRange {
        stage: usize,
        element: usize,
        target: usize,
        codomain_size: usize,
    },
    #[error("thread length {thread_len} does not match expected stage count {expected_stages}")]
    ThreadLengthMismatch {
        thread_len: usize,
        expected_stages: usize,
    },
    #[error("thread entry {value} at stage {stage} exceeds stage size {stage_size}")]
    ThreadElementOutOfRange {
        stage: usize,
        value: usize,
        stage_size: usize,
    },
    #[error("source witness index {witness} exceeds top stage size {top_stage_size}")]
    SourceWitnessOutOfRange {
        witness: usize,
        top_stage_size: usize,
    },
}

/// Finite inverse tower $X_N \to X_{N-1} \to \dots \to X_0$.
///
/// `transitions[k]` maps each element $x \in \{0, \dots, |X_{k+1}| - 1\}$ at stage $k+1$
/// to its projection $\pi_k(x) \in \{0, \dots, |X_k| - 1\}$ at stage $k$.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct FiniteInverseTower {
    /// Size $|X_0|$ of the base stage $0$.
    pub base_stage_size: usize,
    /// Transition maps $\pi_0, \dots, \pi_{N-1}$ where `transitions[k][x]` is $\pi_k(x) \in X_k$.
    pub transitions: Vec<Vec<usize>>,
    /// Explicit subset $S \subseteq X_N$ of original source witnesses at the top stage $N$.
    pub original_source_witnesses: Vec<usize>,
}

/// Verdict comparing compatible inverse-system threads against original source witnesses.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CompletionReflectionReport {
    /// Schema identifier.
    pub schema: String,
    /// Number of stages $N + 1$ in the finite tower.
    pub stage_count: usize,
    /// True iff every stage $X_k$ is non-empty.
    pub all_stages_nonempty: bool,
    /// True iff the supplied thread satisfies $\pi_k(x_{k+1}) = x_k$ for all $0 \le k < N$.
    pub is_compatible_thread: bool,
    /// First stage $k$ where $\pi_k(x_{k+1}) \neq x_k$, if any.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub first_mismatch_stage: Option<usize>,
    /// True iff the thread is compatible and its top element $x_N$ belongs to $S$.
    pub is_original_source_witness: bool,
    /// Total number of compatible threads across the entire tower.
    pub compatible_thread_count: usize,
    /// Number of compatible threads whose top element belongs to $S$.
    pub source_backed_thread_count: usize,
    /// True iff at least one compatible thread exists outside the original source subset $S$.
    pub has_completion_only_thread: bool,
    /// Canonical authority effect: None.
    pub authority_effect: String,
}

impl FiniteInverseTower {
    /// Validate stage dimensions, transition targets, and original source indices.
    pub fn validate(&self) -> Result<(), LggrIvError> {
        if self.transitions.is_empty() {
            return Err(LggrIvError::EmptyTower);
        }
        if self.base_stage_size == 0 {
            return Err(LggrIvError::EmptyStage { stage: 0 });
        }
        let mut codomain_size = self.base_stage_size;
        for (stage_idx, map) in self.transitions.iter().enumerate() {
            if map.is_empty() {
                return Err(LggrIvError::EmptyStage {
                    stage: stage_idx + 1,
                });
            }
            for (elem, &target) in map.iter().enumerate() {
                if target >= codomain_size {
                    return Err(LggrIvError::TargetOutOfRange {
                        stage: stage_idx + 1,
                        element: elem,
                        target,
                        codomain_size,
                    });
                }
            }
            codomain_size = map.len();
        }
        for &w in &self.original_source_witnesses {
            if w >= codomain_size {
                return Err(LggrIvError::SourceWitnessOutOfRange {
                    witness: w,
                    top_stage_size: codomain_size,
                });
            }
        }
        Ok(())
    }

    /// Number of stages $N + 1$ in the tower.
    pub fn stage_count(&self) -> usize {
        self.transitions.len() + 1
    }

    /// Size $|X_k|$ of stage $k$.
    pub fn stage_size(&self, stage: usize) -> Option<usize> {
        if stage == 0 {
            Some(self.base_stage_size)
        } else {
            self.transitions.get(stage - 1).map(Vec::len)
        }
    }
}

/// Evaluate a candidate thread $t = (x_0, x_1, \dots, x_N)$ against a [`FiniteInverseTower`].
pub fn check_completion_reflection(
    tower: &FiniteInverseTower,
    candidate_thread: &[usize],
) -> Result<CompletionReflectionReport, LggrIvError> {
    tower.validate()?;
    let expected_stages = tower.stage_count();
    if candidate_thread.len() != expected_stages {
        return Err(LggrIvError::ThreadLengthMismatch {
            thread_len: candidate_thread.len(),
            expected_stages,
        });
    }
    for (stage, &val) in candidate_thread.iter().enumerate() {
        let stage_size = tower.stage_size(stage).unwrap_or(0);
        if val >= stage_size {
            return Err(LggrIvError::ThreadElementOutOfRange {
                stage,
                value: val,
                stage_size,
            });
        }
    }

    let mut first_mismatch_stage = None;
    for (k, map) in tower.transitions.iter().enumerate() {
        let projected = map[candidate_thread[k + 1]];
        if projected != candidate_thread[k] {
            first_mismatch_stage = Some(k);
            break;
        }
    }
    let is_compatible_thread = first_mismatch_stage.is_none();
    let top_elem = candidate_thread[expected_stages - 1];
    let is_original_source_witness =
        is_compatible_thread && tower.original_source_witnesses.contains(&top_elem);

    // Every compatible thread in a finite tower is uniquely determined by its top element x_N,
    // because pi_k is a total function X_{k+1} -> X_k.
    let top_size = tower.stage_size(expected_stages - 1).unwrap_or(0);
    let compatible_thread_count = top_size;
    let mut source_backed_thread_count = 0usize;
    for x_top in 0..top_size {
        if tower.original_source_witnesses.contains(&x_top) {
            source_backed_thread_count += 1;
        }
    }
    let has_completion_only_thread = compatible_thread_count > source_backed_thread_count;

    Ok(CompletionReflectionReport {
        schema: LGGR_IV_COMPLETION_SCHEMA.to_owned(),
        stage_count: expected_stages,
        all_stages_nonempty: true,
        is_compatible_thread,
        first_mismatch_stage,
        is_original_source_witness,
        compatible_thread_count,
        source_backed_thread_count,
        has_completion_only_thread,
        authority_effect: "None".to_owned(),
    })
}

// Origin: engine/crates_rs/core_local_green_global_red_lggr/src/lggr_iv.rs
// Claim: urn:core:crates_rs:core-local-green-global-red-lggr:lggr-iv:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn completion_thread_is_distinguished_from_original_source_witness() {
        // X_2 = {0, 1} -> X_1 = {0, 1} -> X_0 = {0}, with original source S = {0} subset of X_2.
        // Element 1 in X_2 generates a compatible thread (0, 1, 1) that is NOT in S.
        let tower = FiniteInverseTower {
            base_stage_size: 1,
            transitions: vec![vec![0, 0], vec![0, 1]],
            original_source_witnesses: vec![0],
        };

        let completion_only = check_completion_reflection(&tower, &[0, 1, 1]).unwrap();
        assert!(completion_only.is_compatible_thread);
        assert!(!completion_only.is_original_source_witness);
        assert!(completion_only.has_completion_only_thread);
        assert_eq!(completion_only.compatible_thread_count, 2);
        assert_eq!(completion_only.source_backed_thread_count, 1);
        assert_eq!(completion_only.authority_effect, "None");

        let source_witness = check_completion_reflection(&tower, &[0, 0, 0]).unwrap();
        assert!(source_witness.is_compatible_thread);
        assert!(source_witness.is_original_source_witness);

        let incompatible = check_completion_reflection(&tower, &[0, 0, 1]).unwrap();
        assert!(!incompatible.is_compatible_thread);
        assert_eq!(incompatible.first_mismatch_stage, Some(1));
        assert!(!incompatible.is_original_source_witness);
    }
}
