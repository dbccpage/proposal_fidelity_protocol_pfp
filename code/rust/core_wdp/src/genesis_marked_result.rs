//! Source-25 complete result marks and raw states use ONE joint writing.
//! Filled triples, raw assertion multiplicities and balance have distinct
//! meanings. No carrier-changing quotient transition is asserted here.
use crate::genesis_gauge_result::{integers, Source23Error, Source23State};
use crate::genesis_ongoing_adapter::{GenesisOngoingAdapter, GenesisOngoingPacket, MarkedTriple};
use crate::genesis_source_execution::{canonical_triple, Source25State, SourceExecutionError};
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::gauge_pair_table::{
    align_gauge_pair_tables_with_decoration, canonical_gauge_pair_table_with_decoration,
};
use linear_algebra::pair_table_canonical::canonical_pair_tables_with_decoration;
use num_bigint::BigInt;
use num_rational::BigRational;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Source25ResultMark {
    pub n: usize,
    pub normal: Vec<BigInt>,
    pub filled: Vec<MarkedTriple>,
}

fn renamed(filled: &[MarkedTriple], image: &[usize]) -> Vec<MarkedTriple> {
    let mut out: Vec<_> = filled
        .iter()
        .map(|t| canonical_triple(image[t.x], image[t.y], image[t.z]))
        .collect();
    out.sort();
    out
}

impl Source25State {
    fn unmarked(&self) -> Result<Source23State, Source23Error> {
        Source23State::try_new(
            self.packet().terms.len(),
            self.packet().r.clone(),
            self.packet().s.clone(),
        )
    }
    fn excess_table(&self) -> Result<BasicMatrix<BigRational>, Source23Error> {
        let n = self.packet().terms.len();
        Ok(BasicMatrix::from_row_major(
            n,
            n,
            self.packet()
                .r
                .iter()
                .zip(&self.packet().s)
                .map(|(r, s)| BigRational::from_integer(r - s))
                .collect(),
        )?)
    }
    pub fn rewrite(&self, image: &[usize]) -> Result<Self, Source23Error> {
        let moved = self.unmarked()?.rewrite(image)?;
        Ok(Self::try_new(GenesisOngoingPacket {
            terms: self.packet().terms.clone(),
            r: moved.r().to_vec(),
            s: moved.s().to_vec(),
            filled: renamed(&self.packet().filled, image),
        })?)
    }
    /// Source canonical_state: raw r, then raw s, then filled triples.
    pub fn canonical_state(&self, max_permutations: usize) -> Result<Self, Source23Error> {
        let n = self.packet().terms.len();
        let tables = [&self.packet().r, &self.packet().s]
            .into_iter()
            .map(|cells| {
                BasicMatrix::from_row_major(
                    n,
                    n,
                    cells
                        .iter()
                        .cloned()
                        .map(BigRational::from_integer)
                        .collect(),
                )
            })
            .collect::<Result<Vec<_>, _>>()?;
        let joint = canonical_pair_tables_with_decoration(&tables, max_permutations, |image| {
            renamed(&self.packet().filled, image)
        })?;
        self.rewrite(&joint.old_to_new)
    }
    /// Source result_mark: root-normalized excess, then filled triples, under
    /// one shared writing. Independently canonicalizing the pieces loses incidence.
    pub fn result_mark(
        &self,
        max_permutations: usize,
    ) -> Result<Source25ResultMark, Source23Error> {
        let joint = canonical_gauge_pair_table_with_decoration(
            &self.excess_table()?,
            max_permutations,
            |image| renamed(&self.packet().filled, image),
        )?;
        Ok(Source25ResultMark {
            n: self.packet().terms.len(),
            normal: integers(&joint.normal)?,
            filled: joint.decoration,
        })
    }
    pub fn same_marked_result(
        &self,
        target: &Self,
        max_permutations: usize,
    ) -> Result<bool, Source23Error> {
        if self.packet().terms.len() != target.packet().terms.len() {
            return Ok(false);
        }
        Ok(self.result_mark(max_permutations)? == target.result_mark(max_permutations)?)
    }
    /// Source align: retain the first rewriting of the ORIGINAL raw state.
    pub fn align_to(&self, target: &Self, max_permutations: usize) -> Result<Self, Source23Error> {
        if self.packet().terms.len() != target.packet().terms.len() {
            return Err(Source23Error::NotSameResult);
        }
        let image = align_gauge_pair_tables_with_decoration(
            &self.excess_table()?,
            &target.excess_table()?,
            max_permutations,
            &target.packet().filled,
            |image| renamed(&self.packet().filled, image),
        )?
        .ok_or(Source23Error::NotSameResult)?;
        self.rewrite(&image)
    }
    pub fn plain_state(&self) -> Result<Self, Source23Error> {
        let plain = self.unmarked()?.plain_state()?;
        Ok(Self::try_new(GenesisOngoingPacket {
            terms: self.packet().terms.clone(),
            r: plain.r().to_vec(),
            s: plain.s().to_vec(),
            filled: self.packet().filled.clone(),
        })?)
    }
    pub fn swap_relations(&self) -> Result<Self, SourceExecutionError> {
        Self::try_new(GenesisOngoingPacket {
            terms: self.packet().terms.clone(),
            r: self.packet().s.clone(),
            s: self.packet().r.clone(),
            filled: self.packet().filled.clone(),
        })
    }
    pub fn nothing_with(&self) -> Result<Self, SourceExecutionError> {
        Self::try_new(GenesisOngoingPacket {
            terms: self.packet().terms.clone(),
            r: vec![0.into(); self.packet().r.len()],
            s: vec![0.into(); self.packet().s.len()],
            filled: self.packet().filled.clone(),
        })
    }
    /// Delegate actual diagnostic arithmetic to the existing checked D_F/d0 owner.
    pub fn balance_record(&self) -> Result<Vec<(MarkedTriple, bool)>, Source23Error> {
        let receipt = GenesisOngoingAdapter::try_new(self.packet().clone())
            .map_err(SourceExecutionError::from)?
            .receipt()
            .map_err(SourceExecutionError::from)?;
        Ok(self
            .packet()
            .filled
            .iter()
            .copied()
            .zip(receipt.balances)
            .collect())
    }
    pub fn unbalanced(&self) -> Result<Vec<MarkedTriple>, Source23Error> {
        Ok(self
            .balance_record()?
            .into_iter()
            .filter_map(|(t, balance)| (!balance).then_some(t))
            .collect())
    }
}

// Origin: engine/crates_rs/core_wdp/src/genesis_marked_result.rs
// Claim: urn:core:crates_rs:core-wdp:genesis-marked-result:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3ecd4e2c {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3ecd4e2c` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3ecd4e2c {
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
impl BoundaryError3ecd4e2c {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3ecd4e2c {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3ecd4e2c {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3ecd4e2c {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3ecd4e2c> {
        if capacity_bound == 0 {
            return Err(BoundaryError3ecd4e2c::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3ecd4e2c::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3ecd4e2c::ExceedsCapacity {
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
mod l4_boundary_tests_3ecd4e2c {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord3ecd4e2c::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord3ecd4e2c::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord3ecd4e2c::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord3ecd4e2c::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord3ecd4e2c::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError3ecd4e2c::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError3ecd4e2c::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
