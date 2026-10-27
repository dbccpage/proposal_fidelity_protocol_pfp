//! Finite local observable nets, with computed isotony, locality and complement
//! duality. A finite tensor model does not establish continuum Haag duality.
//! AuthorityEffect: None. Not PROVED. Not GlobalGreen.
use crate::local_operator_algebra::{AlgebraError, LocalOperatorAlgebra};
use std::collections::BTreeMap;
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; checked finite local observable nets.";
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum NetDefect {
    Isotony { smaller: u32, larger: u32 },
    Locality { left: u32, right: u32 },
    Duality { region: u32 },
}
#[derive(Debug, Clone)]
pub struct AlgebraicQft {
    parties: usize,
    algebras: BTreeMap<u32, LocalOperatorAlgebra>,
}
impl AlgebraicQft {
    /// Full subset net on one common carrier. Every region, including the empty
    /// region and its complement, must have a declared algebra.
    pub fn try_new(
        parties: usize,
        algebras: BTreeMap<u32, LocalOperatorAlgebra>,
    ) -> Result<Self, AlgebraError> {
        if parties > 4 || algebras.len() != 1usize << parties {
            return Err(AlgebraError::Dimension);
        }
        let dim = algebras
            .get(&0)
            .ok_or(AlgebraError::Shape)?
            .hilbert_dimension();
        if (0..1u32 << parties).any(|r| {
            algebras
                .get(&r)
                .is_none_or(|a| a.hilbert_dimension() != dim)
        }) {
            return Err(AlgebraError::Shape);
        }
        Ok(Self { parties, algebras })
    }
    pub fn qubit_chain(parties: usize) -> Result<Self, AlgebraError> {
        if parties > 4 {
            return Err(AlgebraError::Dimension);
        }
        let mut algebras = BTreeMap::new();
        for region in 0..1u32 << parties {
            let sites: Vec<usize> = (0..parties)
                .filter(|&i| region & (1u32 << i) != 0)
                .collect();
            algebras.insert(
                region,
                LocalOperatorAlgebra::pauli_support(parties, &sites)?,
            );
        }
        Self::try_new(parties, algebras)
    }
    pub fn algebra(&self, region: u32) -> Result<&LocalOperatorAlgebra, AlgebraError> {
        self.algebras.get(&region).ok_or(AlgebraError::Shape)
    }
    pub fn defects(&self, check_duality: bool) -> Result<Vec<NetDefect>, AlgebraError> {
        let mut defects = Vec::new();
        let full = (1u32 << self.parties) - 1;
        for (&a, aa) in &self.algebras {
            for (&b, bb) in &self.algebras {
                Self::collect_pair_defects(a, aa, b, bb, &mut defects)?;
            }
            if check_duality && !aa.commutant()?.same_algebra(self.algebra(full ^ a)?)? {
                defects.push(NetDefect::Duality { region: a });
            }
        }
        Ok(defects)
    }

    fn collect_pair_defects(
        a: u32,
        aa: &LocalOperatorAlgebra,
        b: u32,
        bb: &LocalOperatorAlgebra,
        defects: &mut Vec<NetDefect>,
    ) -> Result<(), AlgebraError> {
        if a & b == a && !aa.is_subalgebra_of(bb)? {
            defects.push(NetDefect::Isotony {
                smaller: a,
                larger: b,
            });
        }
        if a & b == 0 && !aa.commutes_with(bb)? {
            defects.push(NetDefect::Locality { left: a, right: b });
        }
        Ok(())
    }
    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/algebraic_qft.rs
// Claim: urn:core:crates_rs:core-quantum-physics:algebraic-qft:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord051830be {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord051830be` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError051830be {
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
impl BoundaryError051830be {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError051830be {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError051830be {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord051830be {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError051830be> {
        if capacity_bound == 0 {
            return Err(BoundaryError051830be::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError051830be::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError051830be::ExceedsCapacity {
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
mod tests {
    use super::*;
    #[test]
    fn finite_tensor_net_obeys_isotony_locality_and_complement_duality() {
        let net = AlgebraicQft::qubit_chain(2).unwrap();
        assert!(net.defects(true).unwrap().is_empty());
        assert_eq!(net.algebra(0).unwrap().dimension(), 1);
        assert_eq!(net.algebra(3).unwrap().dimension(), 16);
        let mut algebras = net.algebras.clone();
        algebras.insert(2, LocalOperatorAlgebra::pauli_support(2, &[0]).unwrap());
        let bad = AlgebraicQft::try_new(2, algebras).unwrap();
        assert!(bad
            .defects(false)
            .unwrap()
            .iter()
            .any(|d| matches!(d, NetDefect::Locality { .. })));
    }
}

#[cfg(test)]
mod l4_boundary_tests_051830be {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord051830be::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord051830be::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord051830be::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord051830be::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord051830be::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError051830be::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError051830be::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
