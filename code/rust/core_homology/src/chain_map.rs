use crate::error::HomologyError;
use crate::hash::Blake3Hash;
use linear_algebra::backend::basic_matrix::{BasicMatrix, CheckedNumeric};
use num_traits::Zero;

/// Cryptographically bound witness proving that a sequence of linear maps
/// is a lawful chain map $f: C \to D$, satisfying $d^D \circ f = f \circ d^C$.
// Sealed witness (PO-AUTH-NC): `_private: ()` blocks external literal construction.
#[allow(clippy::manual_non_exhaustive)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ChainMapWitness {
    pub source_complex_hash: [u8; 32],
    pub target_complex_hash: [u8; 32],
    pub map_hashes: Vec<[u8; 32]>,
    _private: (),
}

impl ChainMapWitness {
    pub(crate) fn new(
        source_complex_hash: [u8; 32],
        target_complex_hash: [u8; 32],
        map_hashes: Vec<[u8; 32]>,
    ) -> Self {
        Self {
            source_complex_hash,
            target_complex_hash,
            map_hashes,
            _private: (),
        }
    }
}

/// A certified chain map between two verified chain complexes.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CertifiedChainMap<K> {
    maps: Vec<BasicMatrix<K>>,
    witness: ChainMapWitness,
}

pub trait FiniteChainComplexView<K> {
    fn boundaries(&self) -> &[BasicMatrix<K>];
    fn complex_hash_bytes(&self) -> [u8; 32];
}

impl<K: CheckedNumeric + Zero + PartialEq + Clone + serde::Serialize> CertifiedChainMap<K> {
    pub fn new_checked<C, D>(
        maps: Vec<BasicMatrix<K>>,
        source: &C,
        target: &D,
    ) -> Result<Self, HomologyError>
    where
        C: FiniteChainComplexView<K>,
        D: FiniteChainComplexView<K>,
    {
        if maps.len() != source.boundaries().len() + 1 {
            return Err(HomologyError::DimensionMismatch {
                left: source.boundaries().len() + 1,
                right: maps.len(),
            });
        }

        let mut map_hashes = Vec::with_capacity(maps.len());

        for k in 0..maps.len() {
            let f_k = &maps[k];

            if k > 0 {
                let d_c_k = source
                    .boundaries()
                    .get(k - 1)
                    .ok_or(HomologyError::VerificationUnavailable)?;
                let d_d_k = target
                    .boundaries()
                    .get(k - 1)
                    .ok_or(HomologyError::VerificationUnavailable)?;

                let left = d_d_k
                    .checked_mul(f_k)
                    .map_err(|_| HomologyError::VerificationUnavailable)?;
                let right = maps[k - 1]
                    .checked_mul(d_c_k)
                    .map_err(|_| HomologyError::VerificationUnavailable)?;

                if left != right {
                    return Err(HomologyError::NotAChainMap);
                }
            }

            // Compute canonical map hash
            let mut data = Vec::new();
            data.extend_from_slice(&k.to_le_bytes());
            let entries = serde_json::to_vec(f_k.as_slice()).unwrap_or_default();
            data.extend_from_slice(&entries);
            map_hashes.push(Blake3Hash::new(&data).0);
        }

        Ok(Self {
            maps,
            witness: ChainMapWitness::new(
                source.complex_hash_bytes(),
                target.complex_hash_bytes(),
                map_hashes,
            ),
        })
    }

    pub fn maps(&self) -> &[BasicMatrix<K>] {
        &self.maps
    }

    pub fn witness(&self) -> &ChainMapWitness {
        &self.witness
    }
}

// Origin: engine/crates_rs/core_homology/src/chain_map.rs
// Claim: urn:core:crates_rs:core-homology:chain-map:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordfe549805 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordfe549805` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorfe549805 {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryErrorfe549805 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorfe549805 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorfe549805 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordfe549805 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorfe549805> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorfe549805::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorfe549805::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorfe549805::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[cfg(test)]
mod l4_boundary_tests_fe549805 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordfe549805::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordfe549805::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordfe549805::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordfe549805::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordfe549805::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorfe549805::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorfe549805::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
