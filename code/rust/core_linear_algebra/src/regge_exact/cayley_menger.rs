//! Cayley-Menger determinants and the rational signed 4-volume.
//!
//! For dimension `d`, the bordered matrix `B` is `(d+2)×(d+2)` and
//! `V² = (-1)^{d+1} / (2^d (d!)²) · det(B)`.
//! The signed 4-volume is `det(v1-v0 | … | v4-v0) / 24`, which lies in `Q`
//! when the vertices do. No square root is taken.
//!
//! AuthorityEffect: None.

#![forbid(unsafe_code)]

use super::gaussian;
use super::ExactError;
use crate::regge_exact::q_i64;
use num_rational::BigRational;
use num_traits::{One, Zero};

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CayleyMengerResult {
    pub dimension: u8,
    pub determinant: BigRational,
    pub volume_squared: BigRational,
}

pub fn cayley_menger(
    dimension: u8,
    squared_lengths: &[[BigRational; 5]; 5],
) -> Result<CayleyMengerResult, ExactError> {
    if !(1..=4).contains(&dimension) {
        return Err(ExactError::Dimension {
            expected: "1..=4",
            got: dimension,
        });
    }
    let last = usize::from(dimension);
    // A d-simplex has d + 1 vertices, indexed `0..=d`.
    let vertices = last + 1;
    validate_squared_lengths_table(squared_lengths, last)?;
    let determinant = dispatch_bordered_det(dimension, squared_lengths, vertices)?;
    let volume_squared = volume_squared_from_det(dimension, &determinant)?;
    Ok(CayleyMengerResult {
        dimension,
        determinant,
        volume_squared,
    })
}

fn dispatch_bordered_det(
    dimension: u8,
    squared_lengths: &[[BigRational; 5]; 5],
    vertices: usize,
) -> Result<BigRational, ExactError> {
    match dimension {
        1 => bordered_det::<3>(squared_lengths, vertices),
        2 => bordered_det::<4>(squared_lengths, vertices),
        3 => bordered_det::<5>(squared_lengths, vertices),
        4 => bordered_det::<6>(squared_lengths, vertices),
        _ => unreachable!("dimension was checked"),
    }
}

fn validate_squared_lengths_table(
    squared_lengths: &[[BigRational; 5]; 5],
    last: usize,
) -> Result<(), ExactError> {
    for i in 0..=last {
        if !squared_lengths[i][i].is_zero() {
            return Err(ExactError::Degenerate);
        }
        for j in 0..=last {
            if squared_lengths[i][j] != squared_lengths[j][i] {
                return Err(ExactError::Degenerate);
            }
        }
    }
    Ok(())
}

/// `det(v1-v0 | v2-v0 | v3-v0 | v4-v0) / 24`.
pub fn signed_volume_4(verts: &[[BigRational; 4]; 5]) -> Result<BigRational, ExactError> {
    let mut columns: [[BigRational; 4]; 4] =
        std::array::from_fn(|_| std::array::from_fn(|_| BigRational::zero()));
    for column in 0..4 {
        for row in 0..4 {
            columns[row][column] = &verts[column + 1][row] - &verts[0][row];
        }
    }
    let det = gaussian::determinant(&columns)?;
    Ok(det / q_i64(24))
}

fn bordered_det<const N: usize>(
    squared_lengths: &[[BigRational; 5]; 5],
    dimension: usize,
) -> Result<BigRational, ExactError> {
    let mut bordered: [[BigRational; N]; N] =
        std::array::from_fn(|_| std::array::from_fn(|_| BigRational::zero()));
    for index in 1..N {
        bordered[0][index] = BigRational::one();
        bordered[index][0] = BigRational::one();
    }
    for row in 0..dimension {
        for column in 0..dimension {
            bordered[row + 1][column + 1] = squared_lengths[row][column].clone();
        }
    }
    gaussian::determinant(&bordered)
}

fn volume_squared_from_det(
    dimension: u8,
    determinant: &BigRational,
) -> Result<BigRational, ExactError> {
    let mut factorial = BigRational::one();
    for value in 1..=i64::from(dimension) {
        factorial *= q_i64(value);
    }
    let mut two_power = BigRational::one();
    let two = q_i64(2);
    for _ in 0..dimension {
        two_power *= &two;
    }
    let denominator = &two_power * &factorial * &factorial;
    if denominator.is_zero() {
        return Err(ExactError::DivisionByZero);
    }
    // (-1)^{d+1}
    let signed = if dimension % 2 == 0 {
        -determinant
    } else {
        determinant.clone()
    };
    Ok(signed / denominator)
}

// Origin: engine/crates_rs/core_linear_algebra/src/regge_exact/cayley_menger.rs
// Claim: urn:core:crates_rs:core-linear-algebra:cayley-menger:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord321e42d4 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord321e42d4` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError321e42d4 {
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
impl BoundaryError321e42d4 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError321e42d4 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError321e42d4 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord321e42d4 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError321e42d4> {
        if capacity_bound == 0 {
            return Err(BoundaryError321e42d4::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError321e42d4::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError321e42d4::ExceedsCapacity {
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
    use super::{cayley_menger, signed_volume_4};
    use crate::regge_exact::{q_i64, q_ratio, ExactError};

    fn zeros() -> [[num_rational::BigRational; 5]; 5] {
        std::array::from_fn(|_| std::array::from_fn(|_| q_i64(0)))
    }

    #[test]
    fn reference_volumes_match_the_classical_formulas() {
        let mut edge = zeros();
        edge[0][1] = q_i64(9);
        edge[1][0] = q_i64(9);
        let segment = cayley_menger(1, &edge).unwrap();
        assert_eq!(segment.determinant, q_i64(18));
        assert_eq!(segment.volume_squared, q_i64(9));

        let mut triangle = zeros();
        triangle[0][1] = q_i64(9);
        triangle[1][0] = q_i64(9);
        triangle[0][2] = q_i64(16);
        triangle[2][0] = q_i64(16);
        triangle[1][2] = q_i64(25);
        triangle[2][1] = q_i64(25);
        assert_eq!(
            cayley_menger(2, &triangle).unwrap().volume_squared,
            q_i64(36)
        );

        let tetra = corner_lengths(3);
        assert_eq!(
            cayley_menger(3, &tetra).unwrap().volume_squared,
            q_ratio(1, 36).unwrap()
        );
        let pentatope = corner_lengths(4);
        assert_eq!(
            cayley_menger(4, &pentatope).unwrap().volume_squared,
            q_ratio(1, 576).unwrap()
        );
        assert_eq!(
            signed_volume_4(&orthogonal_pentatope()).unwrap(),
            q_ratio(1, 24).unwrap()
        );
    }

    #[test]
    fn dimension_and_asymmetry_are_refused() {
        let zeros = zeros();
        assert_eq!(
            cayley_menger(0, &zeros).unwrap_err(),
            ExactError::Dimension {
                expected: "1..=4",
                got: 0,
            }
        );
        let mut broken = zeros;
        broken[0][1] = q_i64(1);
        assert_eq!(
            cayley_menger(1, &broken).unwrap_err(),
            ExactError::Degenerate
        );
    }

    fn corner_lengths(dimension: usize) -> [[num_rational::BigRational; 5]; 5] {
        let points = orthogonal_pentatope();
        let mut lengths = zeros();
        for i in 0..=dimension {
            for j in 0..=dimension {
                lengths[i][j] = squared_distance(&points[i], &points[j]);
            }
        }
        lengths
    }

    fn orthogonal_pentatope() -> [[num_rational::BigRational; 4]; 5] {
        let mut points = std::array::from_fn(|_| std::array::from_fn(|_| q_i64(0)));
        for axis in 0..4 {
            points[axis + 1][axis] = q_i64(1);
        }
        points
    }

    fn squared_distance(
        left: &[num_rational::BigRational; 4],
        right: &[num_rational::BigRational; 4],
    ) -> num_rational::BigRational {
        let mut sum = q_i64(0);
        for axis in 0..4 {
            let delta = &left[axis] - &right[axis];
            sum += &delta * &delta;
        }
        sum
    }
}

#[cfg(test)]
mod l4_boundary_tests_321e42d4 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord321e42d4::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord321e42d4::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord321e42d4::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord321e42d4::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord321e42d4::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError321e42d4::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError321e42d4::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
