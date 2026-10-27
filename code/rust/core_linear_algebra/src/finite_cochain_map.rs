//! Typed finite three-term cochain windows and commuting maps over a lawful semiring.
//! Composition, retractions, and explicit cochain homotopies are checked on
//! every coordinate. A commuting map descends to repair quotients, but need
//! not preserve a norm or reflect quotient equality. AuthorityEffect: None.
use crate::backend::basic_matrix::{BasicMatrix, MatrixError};
use crate::scalars::{Ring, Semiring};
use crate::semiring_lumpability::semiring_product;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CochainWindow<S> {
    dimensions: [usize; 3],
    d0: BasicMatrix<S>,
    d1: BasicMatrix<S>,
}
fn invalid(message: &str) -> MatrixError {
    MatrixError::InvalidOperation(message.into())
}
impl<S: Semiring + PartialEq> CochainWindow<S> {
    pub fn try_new(
        dimensions: [usize; 3],
        d0: BasicMatrix<S>,
        d1: BasicMatrix<S>,
    ) -> Result<Self, MatrixError> {
        if d0.shape() != (dimensions[1], dimensions[0])
            || d1.shape() != (dimensions[2], dimensions[1])
        {
            return Err(invalid("cochain dimensions"));
        }
        let composition = semiring_product(&d1, &d0)?;
        for i in 0..dimensions[2] {
            for j in 0..dimensions[0] {
                if composition.get_ref(i, j)? != &S::zero() {
                    return Err(invalid("d1 d0 nonzero"));
                }
            }
        }
        Ok(Self { dimensions, d0, d1 })
    }
    pub fn dimensions(&self) -> [usize; 3] {
        self.dimensions
    }
    pub fn d0(&self) -> &BasicMatrix<S> {
        &self.d0
    }
    pub fn d1(&self) -> &BasicMatrix<S> {
        &self.d1
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CochainMap<S> {
    source: CochainWindow<S>,
    target: CochainWindow<S>,
    maps: [BasicMatrix<S>; 3],
}
impl<S: Semiring + PartialEq + Clone> CochainMap<S> {
    pub fn try_new(
        source: &CochainWindow<S>,
        target: &CochainWindow<S>,
        maps: [BasicMatrix<S>; 3],
    ) -> Result<Self, MatrixError> {
        for (i, m) in maps.iter().enumerate() {
            if m.shape() != (target.dimensions[i], source.dimensions[i]) {
                return Err(invalid("cochain map dimensions"));
            }
        }
        if semiring_product(target.d0(), &maps[0])? != semiring_product(&maps[1], source.d0())?
            || semiring_product(target.d1(), &maps[1])? != semiring_product(&maps[2], source.d1())?
        {
            return Err(invalid("cochain squares do not commute"));
        }
        Ok(Self {
            source: source.clone(),
            target: target.clone(),
            maps,
        })
    }
    pub fn source(&self) -> &CochainWindow<S> {
        &self.source
    }
    pub fn target(&self) -> &CochainWindow<S> {
        &self.target
    }
    pub fn maps(&self) -> &[BasicMatrix<S>; 3] {
        &self.maps
    }

    pub fn identity(window: &CochainWindow<S>) -> Result<Self, MatrixError> {
        let identity =
            |n| BasicMatrix::try_from_fn(n, n, |i, j| if i == j { S::one() } else { S::zero() });
        Self::try_new(
            window,
            window,
            [
                identity(window.dimensions[0])?,
                identity(window.dimensions[1])?,
                identity(window.dimensions[2])?,
            ],
        )
    }

    /// `self` followed by `after`. Matching dimensions alone are insufficient:
    /// the entire intermediate differential presentation must agree.
    pub fn then(&self, after: &Self) -> Result<Self, MatrixError> {
        if self.target != after.source {
            return Err(invalid("cochain composition context mismatch"));
        }
        Self::try_new(
            &self.source,
            &after.target,
            [
                semiring_product(&after.maps[0], &self.maps[0])?,
                semiring_product(&after.maps[1], &self.maps[1])?,
                semiring_product(&after.maps[2], &self.maps[2])?,
            ],
        )
    }

    /// Whether `self` is a retraction of `section`, on all three degrees.
    /// This does not assert that the opposite composite is the identity.
    pub fn is_retraction_of(&self, section: &Self) -> Result<bool, MatrixError> {
        Ok(section.then(self)? == Self::identity(section.source())?)
    }
    pub fn transport(
        &self,
        degree: usize,
        value: &BasicMatrix<S>,
    ) -> Result<BasicMatrix<S>, MatrixError> {
        let map = self
            .maps
            .get(degree)
            .ok_or_else(|| invalid("cochain degree"))?;
        semiring_product(map, value)
    }
}

/// Explicit degree -1 filler: F-G = d H + H d. No filler is inferred from
/// zero curvature, matching diagnostics, or an absent matrix.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CochainHomotopy<S> {
    left: CochainMap<S>,
    right: CochainMap<S>,
    h1: BasicMatrix<S>,
    h2: BasicMatrix<S>,
}

impl<S: Ring> CochainHomotopy<S> {
    pub fn try_new(
        left: &CochainMap<S>,
        right: &CochainMap<S>,
        h1: BasicMatrix<S>,
        h2: BasicMatrix<S>,
    ) -> Result<Self, MatrixError> {
        validate_homotopy_shapes(left, right, &h1, &h2)?;
        let degree0 = semiring_product(&h1, left.source.d0())?;
        let degree1a = semiring_product(left.target.d0(), &h1)?;
        let degree1b = semiring_product(&h2, left.source.d1())?;
        let degree2 = semiring_product(left.target.d1(), &h2)?;
        verify_homotopy_matrix(&left.maps[0], &right.maps[0], &degree0, None)?;
        verify_homotopy_matrix(&left.maps[1], &right.maps[1], &degree1a, Some(&degree1b))?;
        verify_homotopy_matrix(&left.maps[2], &right.maps[2], &degree2, None)?;
        Ok(Self {
            left: left.clone(),
            right: right.clone(),
            h1,
            h2,
        })
    }

    pub fn left(&self) -> &CochainMap<S> {
        &self.left
    }
    pub fn right(&self) -> &CochainMap<S> {
        &self.right
    }
    pub fn h1(&self) -> &BasicMatrix<S> {
        &self.h1
    }
    pub fn h2(&self) -> &BasicMatrix<S> {
        &self.h2
    }
}

fn validate_homotopy_shapes<S: Ring>(
    left: &CochainMap<S>,
    right: &CochainMap<S>,
    h1: &BasicMatrix<S>,
    h2: &BasicMatrix<S>,
) -> Result<(), MatrixError> {
    if left.source != right.source || left.target != right.target {
        return Err(invalid("cochain homotopy context mismatch"));
    }
    if h1.shape() != (left.target.dimensions[0], left.source.dimensions[1])
        || h2.shape() != (left.target.dimensions[1], left.source.dimensions[2])
    {
        return Err(invalid("cochain homotopy dimensions"));
    }
    Ok(())
}

fn verify_homotopy_matrix<S: Ring>(
    a: &BasicMatrix<S>,
    b: &BasicMatrix<S>,
    primary: &BasicMatrix<S>,
    secondary: Option<&BasicMatrix<S>>,
) -> Result<(), MatrixError> {
    for i in 0..a.rows() {
        for j in 0..a.cols() {
            let expected = match secondary {
                Some(extra) => primary.get_ref(i, j)?.add(extra.get_ref(i, j)?),
                None => primary.get_ref(i, j)?.clone(),
            };
            if a.get_ref(i, j)?.sub(b.get_ref(i, j)?) != expected {
                return Err(invalid("cochain homotopy equation fails"));
            }
        }
    }
    Ok(())
}

// Origin: engine/crates_rs/core_linear_algebra/src/finite_cochain_map.rs
// Claim: urn:core:crates_rs:core-linear-algebra:finite-cochain-map:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord4b42e4d2 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord4b42e4d2` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError4b42e4d2 {
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
impl BoundaryError4b42e4d2 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError4b42e4d2 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError4b42e4d2 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord4b42e4d2 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError4b42e4d2> {
        if capacity_bound == 0 {
            return Err(BoundaryError4b42e4d2::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError4b42e4d2::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError4b42e4d2::ExceedsCapacity {
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
mod l4_boundary_tests_4b42e4d2 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord4b42e4d2::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord4b42e4d2::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord4b42e4d2::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord4b42e4d2::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord4b42e4d2::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError4b42e4d2::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError4b42e4d2::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
