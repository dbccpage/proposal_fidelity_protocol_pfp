//! Compile-time images of retained, validated `core.contract.v1` declarations.
//! Images do not establish that a Rust implementation exists or obeys the laws.
//! Executable realization is checked separately through explicit Rust bindings.
//!
//! The generated file is emitted by `build.rs` after running the shared v1 validator. It
//! preserves the existing public image names such as `InvariantDefectProfileContract`,
//! `CochainComplexContract`, `FiniteObstructionTrichotomyContract`, and
//! `CouncilDecisionContract`.

include!(concat!(env!("OUT_DIR"), "/generated_contract_images.rs"));

use std::collections::BTreeSet;

/// Exact carrier witness.
/// Canonical and staged images are admitted. Archived and deprecated images are refused.
/// The two counts are a partition of the included catalog, whose length is measured from the slice.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ContractImageCensus {
    admitted: i64,
    refused: i64,
    included_len: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ContractImageCensusError {
    Empty,
    EmptyIdentity,
    Duplicate,
    Missing,
    Overflow,
    Partition,
}

// Origin: engine/crates_rs/core_contracts/src/contract_images.rs
// Claim: urn:core:crates_rs:core-contracts:contract-images:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ContractImageCensusError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ContractImageCensusError {}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
struct ImageStatusRow<'a> {
    id: &'a str,
    image_type: &'a str,
    status: ContractStatus,
}

impl ContractImageCensus {
    pub fn admitted(self) -> i64 {
        self.admitted
    }

    pub fn refused(self) -> i64 {
        self.refused
    }

    pub fn included_len(self) -> i64 {
        self.included_len
    }

    pub fn try_from_rows(rows: &[ImageStatusRow<'_>]) -> Result<Self, ContractImageCensusError> {
        if rows.is_empty() {
            return Err(ContractImageCensusError::Empty);
        }
        let mut seen = BTreeSet::new();
        let mut admitted = 0i64;
        let mut refused = 0i64;
        let mut index = 0usize;
        while index < rows.len() {
            let row = rows.get(index).ok_or(ContractImageCensusError::Missing)?;
            Self::tally_row(row, &mut seen, &mut admitted, &mut refused)?;
            index = index.checked_add(1).ok_or(ContractImageCensusError::Overflow)?;
        }
        let summed = admitted
            .checked_add(refused)
            .ok_or(ContractImageCensusError::Overflow)?;
        let included_len = i64::try_from(rows.len()).map_err(|_| ContractImageCensusError::Overflow)?;
        if summed != included_len || i64::try_from(seen.len()).ok() != Some(included_len) {
            return Err(ContractImageCensusError::Partition);
        }
        let out = Self { admitted, refused, included_len };
        Ok(out)
    }

    fn tally_row<'a>(
        row: &ImageStatusRow<'a>,
        seen: &mut BTreeSet<&'a str>,
        admitted: &mut i64,
        refused: &mut i64,
    ) -> Result<(), ContractImageCensusError> {
        if row.id.is_empty() || row.image_type.is_empty() {
            return Err(ContractImageCensusError::EmptyIdentity);
        }
        if !seen.insert(row.id) {
            return Err(ContractImageCensusError::Duplicate);
        }
        match row.status {
            ContractStatus::Canonical | ContractStatus::Staged => {
                *admitted = admitted.checked_add(1).ok_or(ContractImageCensusError::Overflow)?;
            }
            ContractStatus::Archived | ContractStatus::Deprecated => {
                *refused = refused.checked_add(1).ok_or(ContractImageCensusError::Overflow)?;
            }
        }
        Ok(())
    }
}

pub fn census_generated_contract_images() -> Result<ContractImageCensus, ContractImageCensusError> {
    let mut rows = Vec::new();
    let mut index = 0usize;
    while index < GENERATED_CONTRACT_IMAGE_CATALOG.len() {
        let entry = GENERATED_CONTRACT_IMAGE_CATALOG
            .get(index)
            .ok_or(ContractImageCensusError::Missing)?;
        rows.push(ImageStatusRow {
            id: entry.id,
            image_type: entry.image_type,
            status: entry.descriptor.status,
        });
        index = index.checked_add(1).ok_or(ContractImageCensusError::Overflow)?;
    }
    ContractImageCensus::try_from_rows(&rows)
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::{
        census_generated_contract_images, ContractImageCensus, ContractImageCensusError, ImageStatusRow,
    };
    use crate::kinds::ContractStatus;

    #[test]
    fn status_buckets_partition_the_rows_they_were_counted_from() {
        let rows = [
            ImageStatusRow { id: "canonical-a", image_type: "A", status: ContractStatus::Canonical },
            ImageStatusRow { id: "staged-b", image_type: "B", status: ContractStatus::Staged },
            ImageStatusRow { id: "archived-c", image_type: "C", status: ContractStatus::Archived },
            ImageStatusRow { id: "deprecated-d", image_type: "D", status: ContractStatus::Deprecated },
        ];
        let census = ContractImageCensus::try_from_rows(&rows);
        assert!(matches!(
            census,
            Ok(value)
                if value.admitted() == 2
                    && value.refused() == 2
                    && value.admitted().checked_add(value.refused()) == Some(value.included_len())
                    && value.included_len() == 4
        ));
    }

    #[test]
    fn an_empty_duplicate_or_blank_image_is_refused() {
        assert!(matches!(
            ContractImageCensus::try_from_rows(&[]),
            Err(ContractImageCensusError::Empty)
        ));
        let blank = [ImageStatusRow { id: "", image_type: "A", status: ContractStatus::Canonical }];
        assert!(matches!(
            ContractImageCensus::try_from_rows(&blank),
            Err(ContractImageCensusError::EmptyIdentity)
        ));
        let duplicated = [
            ImageStatusRow { id: "same", image_type: "A", status: ContractStatus::Canonical },
            ImageStatusRow { id: "same", image_type: "B", status: ContractStatus::Deprecated },
        ];
        assert!(matches!(
            ContractImageCensus::try_from_rows(&duplicated),
            Err(ContractImageCensusError::Duplicate)
        ));
    }

    #[test]
    fn the_included_catalog_census_uses_the_generated_length() {
        assert!(matches!(
            census_generated_contract_images(),
            Ok(census)
                if census.included_len() > 0
                    && census.admitted().checked_add(census.refused()) == Some(census.included_len())
        ));
    }
}
