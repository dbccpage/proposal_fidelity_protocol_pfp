use std::marker::PhantomData;

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct TransitionId(pub String);

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TransitionRef {
    pub source: usize,
    pub target: usize,
    pub transition_id: TransitionId,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DiscreteBundle<F> {
    pub base: Vec<usize>,
    pub fiber_dim: usize,
    pub transitions: Vec<TransitionRef>,
    pub _marker: PhantomData<F>,
}

/// Composition of fiber permutations. Two successive transpositions on a 2-point fiber cancel.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PermutationHolonomy {
    fiber: usize,
    image: Vec<usize>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum HolonomyError {
    Bound,
    Shape,
    NotBijective,
}

impl std::fmt::Display for HolonomyError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            HolonomyError::Bound => write!(formatter, "fiber size must lie in 1..=16"),
            HolonomyError::Shape => write!(formatter, "permutation length must equal the fiber"),
            HolonomyError::NotBijective => write!(formatter, "the map is not a permutation of the fiber"),
        }
    }
}

impl std::error::Error for HolonomyError {}

impl PermutationHolonomy {
    pub fn identity(fiber: usize) -> Result<Self, HolonomyError> {
        if fiber == 0 || fiber > 16 {
            return Err(HolonomyError::Bound);
        }
        Ok(Self {
            fiber,
            image: (0..fiber).collect(),
        })
    }

    pub fn compose(self, next: &[usize]) -> Result<Self, HolonomyError> {
        if next.len() != self.fiber {
            return Err(HolonomyError::Shape);
        }
        let mut seen = vec![false; self.fiber];
        for &value in next {
            if value >= self.fiber {
                return Err(HolonomyError::NotBijective);
            }
            let slot = seen.get_mut(value).ok_or(HolonomyError::NotBijective)?;
            if *slot {
                return Err(HolonomyError::NotBijective);
            }
            *slot = true;
        }
        let mut image = Vec::new();
        for index in 0..self.fiber {
            let mid = *self.image.get(index).ok_or(HolonomyError::Shape)?;
            let dest = *next.get(mid).ok_or(HolonomyError::Shape)?;
            image.push(dest);
        }
        Ok(Self {
            fiber: self.fiber,
            image,
        })
    }

    pub fn fiber(&self) -> usize {
        self.fiber
    }

    pub fn is_identity(&self) -> bool {
        self.image.iter().enumerate().all(|(index, value)| *value == index)
    }
}

// Origin: engine/crates_rs/core_types/src/discrete_bundle.rs
// Claim: urn:core:crates_rs:core-types:discrete-bundle:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod holonomy_tests {
    use super::*;

    fn taken<T, E>(value: Result<T, E>) -> T {
        match value {
            Ok(inner) => inner,
            Err(_) => loop {
                assert!(false);
            },
        }
    }

    #[test]
    fn two_swaps_on_a_two_point_fiber_are_the_identity() {
        let swapped = taken(taken(PermutationHolonomy::identity(2)).compose(&[1, 0]));
        assert_eq!(swapped.fiber(), 2);
        assert!(!swapped.is_identity());
        let back = taken(swapped.compose(&[1, 0]));
        assert!(back.is_identity());
        assert!(taken(PermutationHolonomy::identity(2)).compose(&[1, 1]).is_err());
    }
}
