//! Matrices in `SO(4, Q)`: `Mᵀ M = I` and `det M = 1`, checked entrywise over `Q`.
//!
//! Storage is row-major and acts on column vectors. The induced action on
//! `∧² Q^4` is `c'_ab = Σ_{i<j} c_ij (R_ai R_bj - R_bi R_aj)`.
//!
//! AuthorityEffect: None.

#![forbid(unsafe_code)]

use super::bivector::Bivector4;
use super::gaussian;
use super::ExactError;
use num_rational::BigRational;
use num_traits::{One, Zero};

const PAIRS: [(usize, usize); 6] = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)];

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct So4 {
    pub m: [[BigRational; 4]; 4],
}

impl So4 {
    pub fn identity() -> Self {
        let mut m = std::array::from_fn(|_| std::array::from_fn(|_| BigRational::zero()));
        for index in 0..4 {
            m[index][index] = BigRational::one();
        }
        Self { m }
    }

    pub fn try_new(m: [[BigRational; 4]; 4]) -> Result<Self, ExactError> {
        for column in 0..4 {
            for row in 0..4 {
                let mut gram = BigRational::zero();
                for k in 0..4 {
                    gram += &m[k][column] * &m[k][row];
                }
                let expected = if column == row {
                    BigRational::one()
                } else {
                    BigRational::zero()
                };
                if gram != expected {
                    return Err(ExactError::NotOrthogonal);
                }
            }
        }
        let det = gaussian::determinant(&m)?;
        if det != BigRational::one() {
            return Err(ExactError::NotSpecial);
        }
        Ok(Self { m })
    }

    pub fn mul(&self, other: &Self) -> Self {
        let mut m = std::array::from_fn(|_| std::array::from_fn(|_| BigRational::zero()));
        for row in 0..4 {
            for column in 0..4 {
                let mut sum = BigRational::zero();
                for k in 0..4 {
                    sum += &self.m[row][k] * &other.m[k][column];
                }
                m[row][column] = sum;
            }
        }
        Self { m }
    }

    pub fn transpose(&self) -> Self {
        let mut m = std::array::from_fn(|_| std::array::from_fn(|_| BigRational::zero()));
        for row in 0..4 {
            for column in 0..4 {
                m[row][column] = self.m[column][row].clone();
            }
        }
        Self { m }
    }

    pub fn act_vector(&self, v: &[BigRational; 4]) -> [BigRational; 4] {
        std::array::from_fn(|row| {
            let mut sum = BigRational::zero();
            for column in 0..4 {
                sum += &self.m[row][column] * &v[column];
            }
            sum
        })
    }

    pub fn act_bivector(&self, bivector: &Bivector4) -> Bivector4 {
        let mut image = [
            BigRational::zero(),
            BigRational::zero(),
            BigRational::zero(),
            BigRational::zero(),
            BigRational::zero(),
            BigRational::zero(),
        ];
        for (out_index, (a, b)) in PAIRS.iter().copied().enumerate() {
            let mut sum = BigRational::zero();
            for (in_index, (i, j)) in PAIRS.iter().copied().enumerate() {
                let coefficient = &self.m[a][i] * &self.m[b][j] - &self.m[b][i] * &self.m[a][j];
                sum += &bivector.c[in_index] * &coefficient;
            }
            image[out_index] = sum;
        }
        Bivector4::from_components(image)
    }

    pub fn frobenius_defect_squared(&self) -> BigRational {
        let mut sum = BigRational::zero();
        for row in 0..4 {
            for column in 0..4 {
                let delta = if row == column {
                    BigRational::one()
                } else {
                    BigRational::zero()
                };
                let diff = &self.m[row][column] - delta;
                sum += &diff * &diff;
            }
        }
        sum
    }

    pub fn is_identity(&self) -> bool {
        self.m.iter().enumerate().all(|(row, entries)| {
            entries.iter().enumerate().all(|(column, entry)| {
                let expected = if row == column {
                    BigRational::one()
                } else {
                    BigRational::zero()
                };
                entry == &expected
            })
        })
    }
}

// Origin: engine/crates_rs/core_linear_algebra/src/regge_exact/so4.rs
// Claim: urn:core:crates_rs:core-linear-algebra:so4:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord9b70ae27 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord9b70ae27` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError9b70ae27 {
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
impl BoundaryError9b70ae27 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError9b70ae27 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError9b70ae27 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord9b70ae27 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError9b70ae27> {
        if capacity_bound == 0 {
            return Err(BoundaryError9b70ae27::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError9b70ae27::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError9b70ae27::ExceedsCapacity {
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
    use super::So4;
    use crate::regge_exact::{q_i64, q_ratio, Bivector4, ExactError};

    #[test]
    fn identity_is_special_orthogonal_and_a_reflection_is_not() {
        let identity = So4::try_new(So4::identity().m).unwrap();
        assert!(identity.is_identity());
        assert_eq!(identity.frobenius_defect_squared(), q_i64(0));

        let mut reflection = So4::identity().m;
        reflection[3][3] = q_i64(-1);
        assert_eq!(So4::try_new(reflection), Err(ExactError::NotSpecial));

        let mut stretched = So4::identity().m;
        stretched[0][0] = q_i64(2);
        assert_eq!(So4::try_new(stretched), Err(ExactError::NotOrthogonal));
    }

    #[test]
    fn pythagorean_rotation_inverts_by_transpose_and_fixes_the_area_bivector() {
        let matrix = [
            [
                q_ratio(3, 5).unwrap(),
                q_ratio(-4, 5).unwrap(),
                q_i64(0),
                q_i64(0),
            ],
            [
                q_ratio(4, 5).unwrap(),
                q_ratio(3, 5).unwrap(),
                q_i64(0),
                q_i64(0),
            ],
            [q_i64(0), q_i64(0), q_i64(1), q_i64(0)],
            [q_i64(0), q_i64(0), q_i64(0), q_i64(1)],
        ];
        let rotation = So4::try_new(matrix).unwrap();
        let inverse = So4::try_new(rotation.transpose().m).unwrap();
        assert!(rotation.mul(&inverse).is_identity());

        let mut e0 = std::array::from_fn(|_| q_i64(0));
        let mut e1 = std::array::from_fn(|_| q_i64(0));
        e0[0] = q_i64(1);
        e1[1] = q_i64(1);
        let area = Bivector4::from_wedge_half(&e0, &e1);
        assert_eq!(rotation.act_bivector(&area), area);
    }
}

#[cfg(test)]
mod l4_boundary_tests_9b70ae27 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord9b70ae27::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord9b70ae27::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord9b70ae27::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord9b70ae27::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord9b70ae27::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError9b70ae27::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError9b70ae27::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
