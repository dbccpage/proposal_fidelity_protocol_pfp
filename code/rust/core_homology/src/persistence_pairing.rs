//! Creator/destroyer pairing of filtration indices.
//!
//! AuthorityEffect: None. Shell / best-effort computational topology.
//! Not PROVED; not GlobalGreen.

use serde::{Deserialize, Serialize};

/// Pairing of simplices: creator index -> destroyer index (None = essential).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PersistencePairing {
    /// `pairs[i] = Some(j)` means simplex i creates a class destroyed by j.
    /// `pairs[i] = None` and i is unpaired creator => infinite bar, or i is not a creator.
    pub pairs: Vec<Option<usize>>,
}

impl PersistencePairing {
    pub fn new(n: usize) -> Self {
        Self {
            pairs: vec![None; n],
        }
    }

    pub fn set_pair(&mut self, creator: usize, destroyer: usize) {
        if creator < self.pairs.len() {
            self.pairs[creator] = Some(destroyer);
        }
    }

    pub fn destroyer_of(&self, creator: usize) -> Option<usize> {
        self.pairs.get(creator).copied().flatten()
    }

    pub fn essential_creators(&self) -> impl Iterator<Item = usize> + '_ {
        self.pairs
            .iter()
            .enumerate()
            .filter_map(|(i, p)| if p.is_none() { Some(i) } else { None })
    }
}


/// Persistence pairs are injective and the destroyer index is strictly later.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AdmittedPair {
    creator: usize,
    destroyer: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum PairAdmitError {
    CreatorOutOfRange { creator: usize, len: usize },
    DestroyerOutOfRange { destroyer: usize, len: usize },
    DestroyerNotAfter { creator: usize, destroyer: usize },
    DestroyerCollision { destroyer: usize },
}

// Origin: engine/crates_rs/core_homology/src/persistence_pairing.rs
// Claim: urn:core:crates_rs:core-homology:persistence-pairing:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for PairAdmitError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for PairAdmitError {}

impl PersistencePairing {
    pub fn try_admit_pair(
        &mut self,
        creator: usize,
        destroyer: usize,
    ) -> Result<AdmittedPair, PairAdmitError> {
        if creator >= self.pairs.len() {
            return Err(PairAdmitError::CreatorOutOfRange {
                creator,
                len: self.pairs.len(),
            });
        }
        if destroyer >= self.pairs.len() {
            return Err(PairAdmitError::DestroyerOutOfRange {
                destroyer,
                len: self.pairs.len(),
            });
        }
        if destroyer <= creator {
            return Err(PairAdmitError::DestroyerNotAfter { creator, destroyer });
        }
        if self.pairs.iter().any(|pair| *pair == Some(destroyer)) {
            return Err(PairAdmitError::DestroyerCollision { destroyer });
        }
        self.pairs[creator] = Some(destroyer);
        Ok(AdmittedPair { creator, destroyer })
    }
}

impl AdmittedPair {
    pub fn destroyer(&self) -> usize {
        self.destroyer
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn pair_roundtrip() {
        let mut p = PersistencePairing::new(4);
        p.set_pair(0, 3);
        assert_eq!(p.destroyer_of(0), Some(3));
    }

    #[test]
    fn admitted_pairs_are_injective_and_ordered() {
        let mut pairing = PersistencePairing::new(4);
        let admitted = pairing.try_admit_pair(0, 3);
        assert!(admitted.is_ok());
        assert_eq!(admitted.ok().map(|pair| pair.destroyer()), Some(3));
        assert!(matches!(
            pairing.try_admit_pair(1, 3),
            Err(PairAdmitError::DestroyerCollision { destroyer: 3 })
        ));
        assert!(matches!(
            pairing.try_admit_pair(2, 2),
            Err(PairAdmitError::DestroyerNotAfter {
                creator: 2,
                destroyer: 2
            })
        ));
    }

}
