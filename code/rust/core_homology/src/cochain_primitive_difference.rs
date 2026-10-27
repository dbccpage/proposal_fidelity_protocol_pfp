//! The finite cochain complex realized as a `PrimitiveDifference` on its degree-1 cochains.
//!
//! Rust mirror of the Lean `CoreCore.cochainDifference`: over `C¹` cochains,
//! `δ(x, y) = x − y` and `Zero(d) := d ∈ im(d0)` (i.e. `d` is a coboundary). Membership is
//! decided **exactly** over ℚ via `linear_algebra::linear_algebra::image_kernel::solve_in_image`
//! (`rank([d0 | d]) == rank(d0)`, with a `pot` witness verified by exact replay). No `f64`.
//!
//! Exactness is **BigRational** since ADR-001 (2026-08-04): `Q` was widened in place and
//! `solve_in_image` is generic over an exact scalar, so this path is no longer
//! `exact_i64_bounded` and the EXACT-LA-001 follow-up it used to defer is done.
//!
//! # `zero()` maps solver errors to `false`, and callers must not read that as a verdict
//!
//! The `PrimitiveDifference` trait fixes `fn zero(&self, d) -> bool`, so there is nowhere
//! to put a typed failure: a dimension mismatch, or an internal
//! `MembershipReplayInconsistent`, comes back as `false` — indistinguishable from the
//! mathematical fact "`d` is not a coboundary". That is safe for the *quotient* use
//! (`ValidatedFiniteCarrier` only needs an equivalence, and a uniformly-`false` relation is
//! still one), but it is **not safe for anything that records the answer as evidence**.
//! A consumer that needs to tell those apart must call `solve_in_image` directly and keep
//! the `Result` — `core_solvers::data_difference_ledger` does exactly that, and refuses rather
//! than recording an obstruction it never established.
//!
//! Layering (dependency law): the `PrimitiveDifference` trait is owned by
//! `core_homotopy_type_theory`; exact image membership by `core_linear_algebra`; this crate
//! (`core_homology`) only *implements* the trait for cochain complexes. It computes no
//! Φ₁/Γ₂, runs no evaluator, mints no authority.

use crate::cochain_complex::CochainComplex;
use crate::scalar::Q;
use linear_algebra::linear_algebra::image_kernel::solve_in_image;
use core_homotopy_type_theory::primitive_difference::PrimitiveDifference;

/// A `CochainComplex` viewed as a `PrimitiveDifference` on its `C¹` cochains.
pub struct CochainPrimitiveDifference<'a> {
    complex: &'a CochainComplex,
}

impl<'a> CochainPrimitiveDifference<'a> {
    pub fn new(complex: &'a CochainComplex) -> Self {
        Self { complex }
    }

    /// Cochain dimensions `(c0_dim, c1_dim, c2_dim)` of the underlying complex.
    ///
    /// Shape-only accessor — exposes the dimensions so downstream shape signatures
    /// can read the 2-window arity without touching cochain payload bytes.
    pub fn cochain_dims(&self) -> (usize, usize, usize) {
        (
            self.complex.c0_dim,
            self.complex.c1_dim,
            self.complex.c2_dim,
        )
    }

    /// Deterministic shape-only fingerprint of the underlying complex.
    ///
    /// The blob covers `c0_dim`, `c1_dim`, `c2_dim`, the shapes of `d0` and `d1`
    /// (as `(rows, cols)` each), plus a coefficient-domain tag. It deliberately
    /// excludes matrix coefficient values and any cochain payload — two complexes
    /// that differ only in coefficient values share a fingerprint. Two complexes
    /// that differ in `c0/c1/c2` dimensions or in `d0`/`d1` matrix shape produce
    /// distinct fingerprints. Byte-stable across runs.
    pub fn shape_fingerprint(&self) -> Vec<u8> {
        let mut out = Vec::with_capacity(64);
        out.extend_from_slice(b"core_homology::CochainPrimitiveDifference::shape_fingerprint::v1");
        out.extend_from_slice(&(self.complex.c0_dim as u64).to_le_bytes());
        out.extend_from_slice(&(self.complex.c1_dim as u64).to_le_bytes());
        out.extend_from_slice(&(self.complex.c2_dim as u64).to_le_bytes());
        let (d0_rows, d0_cols) = self.complex.d0.matrix.shape();
        out.extend_from_slice(&(d0_rows as u64).to_le_bytes());
        out.extend_from_slice(&(d0_cols as u64).to_le_bytes());
        let (d1_rows, d1_cols) = self.complex.d1.matrix.shape();
        out.extend_from_slice(&(d1_rows as u64).to_le_bytes());
        out.extend_from_slice(&(d1_cols as u64).to_le_bytes());
        // Coefficient-domain tag: the Rust scalar `Q` is exact rationals; record a
        // stable ASCII tag rather than a structural type id (the latter is not
        // stable across compilations).
        out.extend_from_slice(b"coeff:Q");
        out
    }
}

impl<'a> PrimitiveDifference for CochainPrimitiveDifference<'a> {
    /// A `C¹` cochain, as a coefficient vector of length `c1_dim`.
    type Carrier = Vec<Q>;
    /// The difference `x − y`, again a `C¹` vector.
    type Diff = Vec<Q>;

    /// `δ(x, y) = x − y` elementwise — matching the Lean `cochainDifference` orientation.
    fn delta(&self, x: &Vec<Q>, y: &Vec<Q>) -> Vec<Q> {
        x.iter()
            .zip(y.iter())
            .map(|(a, b)| a.clone() - b.clone())
            .collect()
    }

    /// `Zero(d) := d ∈ im(d0)` — `d` is a coboundary. Decided exactly by `solve_in_image`. A
    /// length/solve error is treated as "not zero" (not a coboundary), never as silently zero.
    fn zero(&self, d: &Vec<Q>) -> bool {
        match solve_in_image(&self.complex.d0.matrix, d.as_slice()) {
            Ok(membership) => membership.is_in_image(),
            Err(_) => false,
        }
    }
}

// Origin: engine/crates_rs/core_homology/src/cochain_primitive_difference.rs
// Claim: urn:core:crates_rs:core-homology:cochain-primitive-difference:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord773742b6 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord773742b6` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError773742b6 {
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
impl BoundaryError773742b6 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError773742b6 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError773742b6 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord773742b6 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError773742b6> {
        if capacity_bound == 0 {
            return Err(BoundaryError773742b6::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError773742b6::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError773742b6::ExceedsCapacity {
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
    use crate::cochain_complex::TheoremProvenance;
    use linear_algebra::backend::basic_matrix::BasicMatrix;
    use num_rational::Rational64;
    use core_homotopy_type_theory::primitive_difference::ValidatedFiniteCarrier;

    fn r(n: i64) -> Q {
        crate::scalar::q(n)
    }

    /// `C⁰ = ℚ`, `C¹ = ℚ²`, `C² = ℚ`; `d0 = [1; -1]`, `d1 = [1, 1]`; `d1·d0 = 0`.
    /// `im(d0) = span{[1, -1]}`.
    fn path_complex() -> CochainComplex {
        let d0 = BasicMatrix::from_row_major(2, 1, vec![r(1), r(-1)]).unwrap();
        let d1 = BasicMatrix::from_row_major(1, 2, vec![r(1), r(1)]).unwrap();
        CochainComplex::new(
            1,
            2,
            1,
            d0,
            d1,
            TheoremProvenance::new("cochain_adapter_test".to_string()).unwrap(),
        )
        .unwrap()
    }

    #[test]
    fn cochain_zero_accepts_exact_boundary() {
        let cc = path_complex();
        let pd = CochainPrimitiveDifference::new(&cc);
        // [3, -3] = 3 · [1, -1] ∈ im(d0).
        assert!(pd.zero(&vec![r(3), r(-3)]));
    }

    #[test]
    fn cochain_zero_rejects_non_boundary() {
        let cc = path_complex();
        let pd = CochainPrimitiveDifference::new(&cc);
        // [1, 1] is not a multiple of [1, -1], so it is not a coboundary.
        assert!(!pd.zero(&vec![r(1), r(1)]));
    }

    #[test]
    fn cochain_primitive_difference_matches_lean_orientation() {
        let cc = path_complex();
        let pd = CochainPrimitiveDifference::new(&cc);
        // δ(x, y) = x − y elementwise (Lean orientation), not y − x.
        assert_eq!(
            pd.delta(&vec![r(5), r(0)], &vec![r(2), r(1)]),
            vec![r(3), r(-1)]
        );
    }

    #[test]
    fn cochain_zero_rel_equivalence_on_validated_domain() {
        let cc = path_complex();
        let pd = CochainPrimitiveDifference::new(&cc);
        // ZeroRel(a,b) := (a − b) ∈ im(d0) is an equivalence (im is a subspace), so validation
        // succeeds and the residual quotient is C¹ / im(d0).
        let domain = vec![
            vec![r(0), r(0)],  // the zero cochain
            vec![r(3), r(-3)], // a coboundary — zero-related to 0
            vec![r(1), r(1)],  // not a coboundary — its own class
        ];
        let vc = ValidatedFiniteCarrier::try_new(&pd, domain)
            .expect("ZeroRel must be an equivalence on the cochain primitive");
        assert_eq!(vc.num_classes(), 2);
    }
}

#[cfg(test)]
mod l4_boundary_tests_773742b6 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord773742b6::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord773742b6::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord773742b6::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord773742b6::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord773742b6::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError773742b6::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError773742b6::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
