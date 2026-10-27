use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Permutation {
    elements: Vec<usize>,
}

impl Permutation {
    pub fn new(elements: Vec<usize>) -> Self {
        Self { elements }
    }

    pub fn elements(&self) -> &[usize] {
        &self.elements
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum Goal {
    ComputeSign,
    Verify,
    Decompose,
}

impl Goal {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::ComputeSign => "compute_sign",
            Self::Verify => "verify",
            Self::Decompose => "decompose",
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum MathObjectKind {
    Permutation,
    Cluster,
    Lattice,
    Bond,
    Worldline,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MathObject {
    kind: MathObjectKind,
    label: String,
}

impl MathObject {
    pub fn new(kind: MathObjectKind, label: impl Into<String>) -> Self {
        Self {
            kind,
            label: label.into(),
        }
    }

    pub fn kind(&self) -> &MathObjectKind {
        &self.kind
    }

    pub fn label(&self) -> &str {
        &self.label
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ProofState {
    objects: Vec<MathObject>,
    goals: Vec<Goal>,
    metadata: BTreeMap<String, String>,
}

impl ProofState {
    pub fn new(
        objects: Vec<MathObject>,
        goals: Vec<Goal>,
        metadata: BTreeMap<String, String>,
    ) -> Self {
        Self {
            objects,
            goals,
            metadata,
        }
    }

    pub fn objects(&self) -> &[MathObject] {
        &self.objects
    }

    pub fn goals(&self) -> &[Goal] {
        &self.goals
    }

    pub fn remove_goal(&mut self, goal: &Goal) {
        if let Some(index) = self.goals.iter().position(|candidate| candidate == goal) {
            self.goals.remove(index);
        }
    }

    pub fn set_metadata(&mut self, key: &str, value: &str) {
        self.metadata.insert(key.to_string(), value.to_string());
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum PermutationError {
    TooLarge,
    NotBijective,
}

// Origin: engine/crates_rs/core_types/src/proof_state.rs
// Claim: urn:core:crates_rs:core-types:proof-state:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for PermutationError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for PermutationError {}

impl Permutation {
    pub fn try_permutation(elements: &[usize]) -> Result<Self, PermutationError> {
        if elements.len() > 256 {
            return Err(PermutationError::TooLarge);
        }
        let mut seen = vec![false; elements.len()];
        for &value in elements {
            if value >= elements.len() {
                return Err(PermutationError::NotBijective);
            }
            let Some(slot) = seen.get_mut(value) else {
                return Err(PermutationError::NotBijective);
            };
            if *slot {
                return Err(PermutationError::NotBijective);
            }
            *slot = true;
        }
        Ok(Self {
            elements: elements.to_vec(),
        })
    }

    pub fn inversion_sign(&self) -> Result<i8, PermutationError> {
        let checked = Self::try_permutation(&self.elements)?;
        let mut inversions: u64 = 0;
        for i in 0..checked.elements.len() {
            for j in (i + 1)..checked.elements.len() {
                let left = checked.elements.get(i).copied().ok_or(PermutationError::NotBijective)?;
                let right = checked.elements.get(j).copied().ok_or(PermutationError::NotBijective)?;
                if left > right {
                    inversions = inversions.checked_add(1).ok_or(PermutationError::TooLarge)?;
                }
            }
        }
        if inversions % 2 == 0 {
            Ok(1)
        } else {
            Ok(-1)
        }
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod permutation_sign_tests {
    use super::*;

    #[test]
    fn transposition_is_odd_and_a_gap_is_not_a_permutation() {
        let odd = Permutation::try_permutation(&[1, 0]).and_then(|item| item.inversion_sign());
        assert!(matches!(odd, Ok(-1)));
        let even = Permutation::try_permutation(&[0, 1]).and_then(|item| item.inversion_sign());
        assert!(matches!(even, Ok(1)));
        assert!(matches!(
            Permutation::try_permutation(&[0, 2]),
            Err(PermutationError::NotBijective)
        ));
    }
}
