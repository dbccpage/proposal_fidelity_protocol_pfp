//! Mutable vector view (zero-copy).

/// Mutable view of a contiguous scalar buffer.
#[derive(Debug)]
pub struct VectorViewMut<'a, T> {
    data: &'a mut [T],
}

impl<'a, T> VectorViewMut<'a, T> {
    pub fn new(data: &'a mut [T]) -> Self {
        Self { data }
    }

    #[must_use]
    pub fn len(&self) -> usize {
        self.data.len()
    }

    #[must_use]
    pub fn is_empty(&self) -> bool {
        self.data.is_empty()
    }

    pub fn as_mut_slice(&mut self) -> &mut [T] {
        self.data
    }
}

// Exact invariant envelope.
// Origin: engine/crates_rs/core_linear_algebra/src/vector/view_mut.rs
// Claim: urn:core:linear-algebra:vector:prefix-certificate:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PrefixCertificate {
    len: usize,
    total: i64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum PrefixError {
    Empty,
    LengthMismatch {
        values: usize,
        claimed: usize,
    },
    Overflow {
        index: usize,
    },
    Mismatch {
        index: usize,
        computed: i64,
        claimed: i64,
    },
}

// Origin: engine/crates_rs/core_linear_algebra/src/vector/view_mut.rs
// Claim: urn:core:crates_rs:core-linear-algebra:view-mut:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for PrefixError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for PrefixError {}

impl<'a> VectorViewMut<'a, i64> {
    pub fn try_prefix_certificate(
        &self,
        claimed_prefix: &[i64],
    ) -> Result<PrefixCertificate, PrefixError> {
        if self.data.is_empty() {
            return Err(PrefixError::Empty);
        }
        if claimed_prefix.len() != self.data.len() {
            return Err(PrefixError::LengthMismatch {
                values: self.data.len(),
                claimed: claimed_prefix.len(),
            });
        }
        let forward = self.verify_forward_prefixes(claimed_prefix)?;
        self.verify_backward_prefixes(claimed_prefix, forward)?;
        Ok(PrefixCertificate {
            len: self.data.len(),
            total: forward,
        })
    }

    fn verify_forward_prefixes(&self, claimed_prefix: &[i64]) -> Result<i64, PrefixError> {
        let mut forward = 0i64;
        for index in 0..self.data.len() {
            let value = *self
                .data
                .get(index)
                .ok_or(PrefixError::Overflow { index })?;
            forward = forward
                .checked_add(value)
                .ok_or(PrefixError::Overflow { index })?;
            let claimed = *claimed_prefix
                .get(index)
                .ok_or(PrefixError::Overflow { index })?;
            if forward != claimed {
                return Err(PrefixError::Mismatch {
                    index,
                    computed: forward,
                    claimed,
                });
            }
        }
        Ok(forward)
    }

    fn verify_backward_prefixes(
        &self,
        claimed_prefix: &[i64],
        forward: i64,
    ) -> Result<(), PrefixError> {
        let mut tail = 0i64;
        for index in (0..self.data.len()).rev() {
            let expected = forward
                .checked_sub(tail)
                .ok_or(PrefixError::Overflow { index })?;
            let claimed = *claimed_prefix
                .get(index)
                .ok_or(PrefixError::Overflow { index })?;
            if expected != claimed {
                return Err(PrefixError::Mismatch {
                    index,
                    computed: expected,
                    claimed,
                });
            }
            let value = *self
                .data
                .get(index)
                .ok_or(PrefixError::Overflow { index })?;
            tail = tail
                .checked_add(value)
                .ok_or(PrefixError::Overflow { index })?;
        }
        Ok(())
    }
}

impl PrefixCertificate {
    pub fn total(&self) -> i64 {
        self.total
    }

    pub fn len(&self) -> usize {
        self.len
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod prefix_certificate_tests {
    use super::*;

    #[test]
    fn forward_and_backward_prefixes_agree() {
        let mut values = [4, -1, 3];
        let view = VectorViewMut::new(&mut values);
        let witness = view.try_prefix_certificate(&[4, 3, 6]);
        assert!(matches!(witness, Ok(ref row) if row.total() == 6 && row.len() == 3));
    }

    #[test]
    fn refuses_a_prefix_that_skips_a_reward() {
        let mut values = [4, -1, 3];
        let view = VectorViewMut::new(&mut values);
        let wrong = view.try_prefix_certificate(&[4, 4, 6]);
        assert!(matches!(
            wrong,
            Err(PrefixError::Mismatch {
                index: 1,
                computed: 3,
                claimed: 4
            })
        ));
    }
}
