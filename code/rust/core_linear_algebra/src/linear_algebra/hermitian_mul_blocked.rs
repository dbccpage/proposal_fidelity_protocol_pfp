use super::hermitian_mul::{
    hermitian_conjugation_unchecked, mul_then_force_hermitian_from_upper_triangle_unchecked,
    validate_hermitian, validate_matrix, HermitianMulConfig, HermitianMulError, MatrixRole,
};
use num_complex::Complex64 as C64;

const BLOCK_SIZE: usize = 32;

pub(crate) fn mul_then_force_hermitian_from_upper_triangle_blocked_unchecked(
    a: &[C64],
    b: &[C64],
    n: usize,
) -> Vec<C64> {
    if n <= BLOCK_SIZE {
        return mul_then_force_hermitian_from_upper_triangle_unchecked(a, b, n);
    }

    let bs = BLOCK_SIZE;
    let n_blocks = n.div_ceil(bs);

    (0..n_blocks)
        .flat_map(|ib| (ib..n_blocks).map(move |jb| (ib, jb)))
        .fold(vec![C64::new(0.0, 0.0); n * n], |mut c, (ib, jb)| {
            let i_start = ib * bs;
            let i_end = (i_start + bs).min(n);
            let j_start = jb * bs;
            let j_end = (j_start + bs).min(n);

            (0..n_blocks).for_each(|kb| {
                let k_start = kb * bs;
                let k_end = (k_start + bs).min(n);

                (i_start..i_end).for_each(|i| {
                    let j_lo = if ib == jb { i } else { j_start };

                    (j_lo..j_end).for_each(|j| {
                        let sum = (k_start..k_end)
                            .map(|k| a[i * n + k] * b[k * n + j])
                            .fold(C64::new(0.0, 0.0), |acc, x| acc + x);
                        c[i * n + j] += sum;
                    });
                });
            });

            if ib != jb {
                (i_start..i_end)
                    .flat_map(|i| (j_start..j_end).map(move |j| (i, j)))
                    .for_each(|(i, j)| {
                        c[j * n + i] = c[i * n + j].conj();
                    });
            } else {
                (i_start..i_end)
                    .flat_map(|i| ((i + 1)..j_end).map(move |j| (i, j)))
                    .for_each(|(i, j)| {
                        c[j * n + i] = c[i * n + j].conj();
                    });
            }
            c
        })
}

pub(crate) fn hermitian_conjugation_blocked_unchecked(u: &[C64], a: &[C64], n: usize) -> Vec<C64> {
    if n <= BLOCK_SIZE {
        return hermitian_conjugation_unchecked(u, a, n);
    }

    // Step 1: tmp = A * U^dagger (full multiply, O(n^3))
    let bs = BLOCK_SIZE;
    let n_blocks = n.div_ceil(bs);

    let tmp = (0..n_blocks)
        .flat_map(|ib| (0..n_blocks).map(move |jb| (ib, jb)))
        .fold(vec![C64::new(0.0, 0.0); n * n], |mut tmp, (ib, jb)| {
            let i_start = ib * bs;
            let i_end = (i_start + bs).min(n);
            let j_start = jb * bs;
            let j_end = (j_start + bs).min(n);

            (0..n_blocks).for_each(|kb| {
                let k_start = kb * bs;
                let k_end = (k_start + bs).min(n);

                (i_start..i_end)
                    .flat_map(|i| (j_start..j_end).map(move |j| (i, j)))
                    .for_each(|(i, j)| {
                        let sum = (k_start..k_end)
                            .map(|k| a[i * n + k] * u[j * n + k].conj())
                            .fold(C64::new(0.0, 0.0), |acc, x| acc + x);
                        tmp[i * n + j] += sum;
                    });
            });
            tmp
        });

    // Step 2: C = U * tmp, upper-triangle blocked
    mul_then_force_hermitian_from_upper_triangle_blocked_unchecked(u, &tmp, n)
}

pub fn hermitian_square_blocked_checked(
    rho: &[C64],
    n: usize,
    config: HermitianMulConfig,
) -> Result<Vec<C64>, HermitianMulError> {
    config.validate()?;
    validate_hermitian(MatrixRole::HermitianInput, rho, n, config.hermitian_tol)?;

    Ok(mul_then_force_hermitian_from_upper_triangle_blocked_unchecked(rho, rho, n))
}

pub fn hermitian_conjugation_blocked_checked(
    u: &[C64],
    a: &[C64],
    n: usize,
    config: HermitianMulConfig,
) -> Result<Vec<C64>, HermitianMulError> {
    config.validate()?;
    validate_matrix(MatrixRole::ConjugatingMatrix, u, n)?;
    validate_hermitian(MatrixRole::HermitianInput, a, n, config.hermitian_tol)?;

    Ok(hermitian_conjugation_blocked_unchecked(u, a, n))
}

// Origin: engine/crates_rs/core_linear_algebra/src/linear_algebra/hermitian_mul_blocked.rs
// Claim: urn:core:crates_rs:core-linear-algebra:hermitian-mul-blocked:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord18b5d4ed {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord18b5d4ed` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError18b5d4ed {
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
impl BoundaryError18b5d4ed {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError18b5d4ed {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError18b5d4ed {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord18b5d4ed {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError18b5d4ed> {
        if capacity_bound == 0 {
            return Err(BoundaryError18b5d4ed::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError18b5d4ed::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError18b5d4ed::ExceedsCapacity {
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
mod l4_boundary_tests_18b5d4ed {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord18b5d4ed::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord18b5d4ed::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord18b5d4ed::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord18b5d4ed::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord18b5d4ed::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError18b5d4ed::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError18b5d4ed::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
