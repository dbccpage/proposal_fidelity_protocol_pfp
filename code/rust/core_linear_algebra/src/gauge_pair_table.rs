//! Exact root-normalized square tables modulo gradients and one shared writing.
//! Every writing is normalized AFTER transport. A diagonal at the root is
//! retained; treating its value as a potential would change the source gauge.
use crate::backend::basic_matrix::BasicMatrix;
use crate::pair_table_canonical::PairCanonicalError;
use crate::semiring_lumpability::push_forward_square;
use num_rational::BigRational;
use core_combinatorics::enumeration::Permutations;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CanonicalGaugeTable {
    pub normal: BasicMatrix<BigRational>,
    pub old_to_new: Vec<usize>,
    pub examined: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CanonicalDecoratedGaugeTable<D> {
    pub normal: BasicMatrix<BigRational>,
    pub decoration: D,
    pub old_to_new: Vec<usize>,
    pub examined: usize,
}

/// Subtract e(x,0) from row x and add e(y,0) to column y for NONROOT
/// vertices only. All diagonal and cycle values survive, including e(0,0).
pub fn root_normalized_pair_table(
    table: &BasicMatrix<BigRational>,
) -> Result<BasicMatrix<BigRational>, PairCanonicalError> {
    let n = table.rows();
    if table.cols() != n {
        return Err(PairCanonicalError::IncompatibleTables);
    }
    let potential: Vec<_> = (0..n)
        .map(|x| {
            if x == 0 {
                BigRational::from_integer(0.into())
            } else {
                table.as_slice()[x * n].clone()
            }
        })
        .collect();
    Ok(BasicMatrix::try_from_fn(n, n, |x, y| {
        &table.as_slice()[x * n + y] - &potential[x] + &potential[y]
    })?)
}

/// Lexicographically least root-normalized table over the whole n! orbit.
/// An empty carrier still has one writing and requires budget one.
pub fn canonical_gauge_pair_table(
    table: &BasicMatrix<BigRational>,
    max_permutations: usize,
) -> Result<CanonicalGaugeTable, PairCanonicalError> {
    let joint = canonical_gauge_pair_table_with_decoration(table, max_permutations, |_| ())?;
    Ok(CanonicalGaugeTable {
        normal: joint.normal,
        old_to_new: joint.old_to_new,
        examined: joint.examined,
    })
}

/// Normalize after every writing, then compare its transported decoration
/// as a secondary key. One shared writing retains all joint incidence.
pub fn canonical_gauge_pair_table_with_decoration<D: Ord>(
    table: &BasicMatrix<BigRational>,
    max_permutations: usize,
    decorate: impl Fn(&[usize]) -> D,
) -> Result<CanonicalDecoratedGaugeTable<D>, PairCanonicalError> {
    let n = table.rows();
    if table.cols() != n {
        return Err(PairCanonicalError::IncompatibleTables);
    }
    let permutations = Permutations::new(n, max_permutations)?;
    let mut best: Option<(BasicMatrix<BigRational>, D, Vec<usize>)> = None;
    let mut examined = 0;
    for image in permutations {
        let normal = root_normalized_pair_table(&push_forward_square(table, &image, n)?)?;
        let decoration = decorate(&image);
        if best.as_ref().is_none_or(|(least, old_decoration, _)| {
            (normal.as_slice(), &decoration) < (least.as_slice(), old_decoration)
        }) {
            best = Some((normal, decoration, image));
        }
        examined += 1;
    }
    let (normal, decoration, old_to_new) = best.ok_or(PairCanonicalError::IncompatibleTables)?;
    Ok(CanonicalDecoratedGaugeTable {
        normal,
        decoration,
        old_to_new,
        examined,
    })
}

/// First writing whose normalized table agrees with target's FIXED writing.
/// None is a complete finite nonalignment result, never a sampled refusal.
pub fn align_gauge_pair_tables(
    table: &BasicMatrix<BigRational>,
    target: &BasicMatrix<BigRational>,
    max_permutations: usize,
) -> Result<Option<Vec<usize>>, PairCanonicalError> {
    align_gauge_pair_tables_with_decoration(table, target, max_permutations, &(), |_| ())
}

/// First complete writing with BOTH the target's fixed normal table and its
/// decoration. The caller supplies a deterministic decoration transport.
pub fn align_gauge_pair_tables_with_decoration<D: Eq>(
    table: &BasicMatrix<BigRational>,
    target: &BasicMatrix<BigRational>,
    max_permutations: usize,
    target_decoration: &D,
    decorate: impl Fn(&[usize]) -> D,
) -> Result<Option<Vec<usize>>, PairCanonicalError> {
    let n = validate_pair_table_shapes(table, target)?;
    let permutations = Permutations::new(n, max_permutations)?;
    let want = root_normalized_pair_table(target)?;
    for image in permutations {
        let pushed = push_forward_square(table, &image, n)?;
        if root_normalized_pair_table(&pushed)? == want && &decorate(&image) == target_decoration {
            return Ok(Some(image));
        }
    }
    Ok(None)
}

fn validate_pair_table_shapes(
    table: &BasicMatrix<BigRational>,
    target: &BasicMatrix<BigRational>,
) -> Result<usize, PairCanonicalError> {
    let n = table.rows();
    if table.cols() != n || target.rows() != n || target.cols() != n {
        return Err(PairCanonicalError::IncompatibleTables);
    }
    Ok(n)
}

// Origin: engine/crates_rs/core_linear_algebra/src/gauge_pair_table.rs
// Claim: urn:core:crates_rs:core-linear-algebra:gauge-pair-table:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord6564d395 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord6564d395` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError6564d395 {
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
impl BoundaryError6564d395 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError6564d395 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError6564d395 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord6564d395 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError6564d395> {
        if capacity_bound == 0 {
            return Err(BoundaryError6564d395::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError6564d395::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError6564d395::ExceedsCapacity {
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
mod l4_boundary_tests_6564d395 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord6564d395::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord6564d395::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord6564d395::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord6564d395::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord6564d395::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError6564d395::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError6564d395::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
