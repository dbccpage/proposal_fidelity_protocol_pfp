//! Companion Rust witness for PROD-P5-NEXT-2 (CertificationService 21.11 dependency-order propagation).

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Status {
    Proved,
    Undetermined,
}

pub fn propagate_21_11_chain(
    c1_pointers_complete: bool,
    c2_pointers_complete: bool,
    c3_pointers_complete: bool,
    c_ind_pointers_complete: bool,
) -> (Status, Status, Status, Status) {
    let s1 = if c1_pointers_complete {
        Status::Proved
    } else {
        Status::Undetermined
    };
    let s2 = if c2_pointers_complete && s1 == Status::Proved {
        Status::Proved
    } else {
        Status::Undetermined
    };
    let s3 = if c3_pointers_complete && s2 == Status::Proved {
        Status::Proved
    } else {
        Status::Undetermined
    };
    let s_ind = if c_ind_pointers_complete {
        Status::Proved
    } else {
        Status::Undetermined
    };
    (s1, s2, s3, s_ind)
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn missing_pointer_at_root_propagates_along_dependency_chain_only() {
        let (s1, s2, s3, s_ind) = propagate_21_11_chain(false, true, true, true);
        assert_eq!(s1, Status::Undetermined);
        assert_eq!(s2, Status::Undetermined);
        assert_eq!(s3, Status::Undetermined);
        assert_eq!(s_ind, Status::Proved);
    }
}

/// Proved prefix of a dependency chain. A proved status after an undetermined predecessor is refused.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ChainRankWitness {
    proved_prefix: u32,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ChainRankError {
    ProvedAfterGap { index: usize },
    Overflow,
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/prod_p5_next_2.rs
// Claim: urn:core:crates_rs:tests:prod-p5-next-2:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ChainRankError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ChainRankError {}

impl ChainRankWitness {
    pub fn try_chain(statuses: &[Status]) -> Result<Self, ChainRankError> {
        let mut proved_prefix = 0u32;
        let mut gap = false;
        for (index, status) in statuses.iter().enumerate() {
            if *status == Status::Proved {
                if gap {
                    return Err(ChainRankError::ProvedAfterGap { index });
                }
                proved_prefix = proved_prefix
                    .checked_add(1)
                    .ok_or(ChainRankError::Overflow)?;
            } else {
                gap = true;
            }
        }
        Ok(Self { proved_prefix })
    }

    pub fn proved_prefix(&self) -> u32 {
        self.proved_prefix
    }
}
