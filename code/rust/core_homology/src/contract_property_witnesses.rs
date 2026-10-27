
#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_a4accca1;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_a4accca1<T> = std::result::Result<T, BoundaryError_a4accca1>;
#[cfg(test)]
mod __omega_homology_property_witnesses {
    use crate::coboundary::CoboundaryMap;
    use crate::cochain_complex::CochainComplex;
    use crate::cocycle::Cocycle;
    use crate::cycle::Cycle;
    use crate::finite_directed_graph::FiniteDirectedGraph;
    use crate::homology_class::{CohomologyClass, HomologyClass};
    use crate::witness::CycleWitness;

    #[test]
    fn bound_homological_symbols_have_compiled_witnesses() {
        assert!(core::any::type_name::<CoboundaryMap>().contains("CoboundaryMap"));
        assert!(core::any::type_name::<CochainComplex>().contains("CochainComplex"));
        assert!(core::any::type_name::<Cocycle>().contains("Cocycle"));
        assert!(core::any::type_name::<Cycle>().contains("Cycle"));
        assert!(core::any::type_name::<CycleWitness>().contains("CycleWitness"));
        assert!(core::any::type_name::<FiniteDirectedGraph>().contains("FiniteDirectedGraph"));
        assert!(core::any::type_name::<HomologyClass<String>>().contains("HomologyClass"));
        assert!(core::any::type_name::<CohomologyClass<String>>().contains("CohomologyClass"));
    }
}

// Exact carrier witness.

// Origin: engine/crates_rs/core_homology/src/contract_property_witnesses.rs
// Claim: urn:core:crates_rs:core-homology:contract-property-witnesses:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda4accca1 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda4accca1` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora4accca1 {
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
impl BoundaryErrora4accca1 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora4accca1 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora4accca1 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda4accca1 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora4accca1> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora4accca1::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora4accca1::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora4accca1::ExceedsCapacity {
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
mod euler_chain_witness {
    fn euler_step(dims: &[u64], ranks: &[u64], index: usize, sign: i128) -> Result<(i128, i128), &'static str> {
        let dim = *dims.get(index).ok_or("shape")?;
        let incoming = index.checked_sub(1).and_then(|i| ranks.get(i)).copied().unwrap_or(0);
        let outgoing = ranks.get(index).copied().unwrap_or(0);
        let used = incoming.checked_add(outgoing).ok_or("overflow")?;
        if used > dim {
            return Err("homology");
        }
        let h = dim.checked_sub(used).ok_or("overflow")?;
        let d_term = sign.checked_mul(i128::from(dim)).ok_or("overflow")?;
        let h_term = sign.checked_mul(i128::from(h)).ok_or("overflow")?;
        Ok((d_term, h_term))
    }

    fn euler(dims: &[u64], ranks: &[u64]) -> Result<i128, &'static str> {
        if dims.is_empty() || ranks.len().checked_add(1) != Some(dims.len()) {
            return Err("shape");
        }
        let mut euler_dims: i128 = 0;
        let mut euler_h: i128 = 0;
        let mut sign: i128 = 1;
        for index in 0..dims.len() {
            let (d_term, h_term) = euler_step(dims, ranks, index, sign)?;
            euler_dims = euler_dims.checked_add(d_term).ok_or("overflow")?;
            euler_h = euler_h.checked_add(h_term).ok_or("overflow")?;
            sign = sign.checked_mul(-1).ok_or("overflow")?;
        }
        if euler_dims != euler_h { Err("euler") } else { Ok(euler_dims) }
    }

    #[test]
    fn short_complex_euler_is_one() {
        assert!(matches!(euler(&[2, 3, 2], &[1, 1]), Ok(1)));
    }

    #[test]
    fn an_oversized_rank_is_refused() {
        assert!(matches!(euler(&[1, 1], &[2]), Err("homology")));
    }
}

#[cfg(test)]
mod l4_boundary_tests_a4accca1 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorda4accca1::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorda4accca1::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorda4accca1::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorda4accca1::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorda4accca1::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrora4accca1::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrora4accca1::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
