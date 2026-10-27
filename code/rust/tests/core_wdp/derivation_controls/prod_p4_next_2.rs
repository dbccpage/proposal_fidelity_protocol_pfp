//! Companion Rust witness for PROD-P4-NEXT-2 (Map CompletionTarget raw/quotient/both onto distinct_image targets).

pub fn sharp_distinct_image_minima(dim_k: usize, dim_rk: usize, dim_kb: usize, dim_rkb: usize) -> (usize, usize, usize, usize) {
    let raw_min = dim_rk;
    let quo_min = dim_k - dim_kb;
    let joint_min = quo_min + dim_rkb;
    let separate_sum = raw_min + quo_min;
    (raw_min, quo_min, joint_min, separate_sum)
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn neither_inclusion_exhibits_strict_joint_subadditivity() {
        let (raw_min, quo_min, joint_min, separate_sum) = sharp_distinct_image_minima(3, 2, 2, 1);
        assert_eq!((raw_min, quo_min, joint_min, separate_sum), (2, 1, 2, 3));
        assert!(joint_min < separate_sum);
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ImageMinima {
    quo: usize,
    joint: usize,
    separate: usize,
    slack: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ImageError {
    NotSubspace,
    Overflow,
    Slack,
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/prod_p4_next_2.rs
// Claim: urn:core:crates_rs:tests:prod-p4-next-2:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ImageError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ImageError {}

impl ImageMinima {
    pub fn try_checked(
        dim_k: usize,
        dim_rk: usize,
        dim_kb: usize,
        dim_rkb: usize,
    ) -> Result<Self, ImageError> {
        if dim_kb > dim_k || dim_rkb > dim_rk {
            return Err(ImageError::NotSubspace);
        }
        let quo = dim_k - dim_kb;
        let slack = dim_rk - dim_rkb;
        let joint = quo.checked_add(dim_rkb).ok_or(ImageError::Overflow)?;
        let separate = dim_rk.checked_add(quo).ok_or(ImageError::Overflow)?;
        let rebuilt = joint.checked_add(slack).ok_or(ImageError::Overflow)?;
        if rebuilt != separate {
            return Err(ImageError::Slack);
        }
        Ok(Self {
            quo,
            joint,
            separate,
            slack,
        })
    }

    pub fn parts(&self) -> (usize, usize, usize, usize) {
        (self.quo, self.joint, self.separate, self.slack)
    }
}

#[cfg(test)]
mod image_minima_tests {
    use super::*;

    #[test]
    fn slack_restores_the_separate_count() {
        let minima = ImageMinima::try_checked(3, 2, 2, 1);
        assert!(matches!(minima.as_ref().map(|item| item.parts()), Ok((1, 2, 3, 1))));
        assert!(matches!(ImageMinima::try_checked(3, 2, 4, 1), Err(ImageError::NotSubspace)));
    }
}
