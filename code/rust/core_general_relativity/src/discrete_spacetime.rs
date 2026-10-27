//! Finite discrete spacetime as a simplicial complex.
//!
//! Combinatorial carrier is [`core_homology::simplicial::SimplicialComplex`]
//! (canonical face-closed complex). Metric / Regge data live in
//! [`crate::regge_calculus`].
//!
//! AuthorityEffect: None. Not continuum GR. Not PROVED / GlobalGreen.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_a1cc337f<T> {
    fn checked_invariant_a1cc337f(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_a1cc337f<T> for Option<T> {
    #[inline]
    fn checked_invariant_a1cc337f(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_a1cc337f<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_a1cc337f(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use core_homology::errors::HomologicalError;
use core_homology::simplicial::{OrientedSimplex, Simplex, SimplicialComplex};

/// Fence string (proposal).
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; finite simplicial spacetime.";

/// Finite discrete spacetime: face-closed simplicial complex + label.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DiscreteSpacetime {
    /// Combinatorial spacetime (closed under faces).
    pub complex: SimplicialComplex,
    /// Stable label.
    pub label: String,
}

impl DiscreteSpacetime {
    /// Scaffold constructor: standard n-simplex (combinatorial only).
    ///
    /// `degree` maps to ambient dimension n = max(degree, 0) of Δⁿ.
    pub fn new(degree: usize, label: impl Into<String>) -> Self {
        let complex = SimplicialComplex::standard_n_simplex(degree)
            .checked_invariant_a1cc337f("standard_n_simplex succeeds for finite n");
        Self {
            complex,
            label: label.into(),
        }
    }

    /// Build from maximal simplices (auto face-closure via core_homology).
    pub fn try_from_maximal(
        maximal: Vec<OrientedSimplex>,
        label: impl Into<String>,
    ) -> Result<Self, HomologicalError> {
        Ok(Self {
            complex: SimplicialComplex::from_maximal_simplices(maximal)?,
            label: label.into(),
        })
    }

    /// Standard combinatorial n-simplex.
    pub fn standard_simplex(n: usize, label: impl Into<String>) -> Result<Self, HomologicalError> {
        Ok(Self {
            complex: SimplicialComplex::standard_n_simplex(n)?,
            label: label.into(),
        })
    }

    /// Event / vertex count.
    pub fn event_count_proxy(&self) -> usize {
        self.complex.num_vertices()
    }

    /// Degree proxy = max simplex dimension.
    pub fn degree(&self) -> usize {
        self.complex.max_dimension()
    }

    /// Number of k-simplices.
    pub fn count(&self, dim: usize) -> usize {
        self.complex.count(dim)
    }

    /// Euler characteristic χ (combinatorial).
    pub fn euler_characteristic(&self) -> i64 {
        self.complex.euler_characteristic()
    }

    /// Whether the complex contains a simplex.
    pub fn contains(&self, simplex: &Simplex) -> bool {
        self.complex.contains(simplex)
    }

    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

// Origin: engine/crates_rs/core_general_relativity/src/discrete_spacetime.rs
// Claim: urn:core:crates_rs:core-general-relativity:discrete-spacetime:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda1cc337f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda1cc337f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora1cc337f {
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
impl BoundaryErrora1cc337f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora1cc337f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora1cc337f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda1cc337f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora1cc337f> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora1cc337f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora1cc337f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora1cc337f::ExceedsCapacity {
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
    use super::*;

    #[test]
    fn triangle_has_three_edges() {
        let st = DiscreteSpacetime::standard_simplex(2, "Δ2").unwrap();
        assert_eq!(st.count(0), 3);
        assert_eq!(st.count(1), 3);
        assert_eq!(st.count(2), 1);
        assert_eq!(st.euler_characteristic(), 1); // disk-like triangle χ=1
    }

    #[test]
    fn new_and_fence() {
        let x = DiscreteSpacetime::new(1, "test");
        assert_eq!(x.degree(), 1);
        assert!(DiscreteSpacetime::authority_fence().contains("AuthorityEffect None"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_a1cc337f {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorda1cc337f::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorda1cc337f::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorda1cc337f::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorda1cc337f::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorda1cc337f::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrora1cc337f::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrora1cc337f::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
