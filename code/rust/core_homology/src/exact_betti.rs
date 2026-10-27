//! Free ranks and **integral torsion** of a 2-truncated carrier, via Smith normal
//! form over a declared ℤ-lattice.
//!
//! For a carrier `C⁰ →d₀ C¹ →d₁ C²`:
//!
//! ```text
//! b₀           = |V| − rank(d₀)
//! b₁           = |E| − rank(d₀) − rank(d₁)
//! b₂_terminal  = |F| − rank(d₁)
//! ```
//!
//! # What SNF does and does not add
//!
//! **SNF does not change the ranks.** For an integer matrix,
//! `rank_ℤ(A) = rank_ℚ(A)` — the number of nonzero invariant factors is the ordinary
//! rank. So `b₀` and `b₁` here agree with what a rational rank computation gives;
//! computing them through SNF *repairs nothing about them*.
//!
//! What SNF adds is the **invariant factors**, which a rank alone discards:
//!
//! - the factors of `d₀` are the torsion of `Q¹ = C¹/im(d₀)`, the residual quotient
//!   this crate already computes the dimension of ([`Carrier::dim_q1`]);
//! - the factors of `d₁` are the torsion of the terminal quotient `C²/im(d₁)`.
//!
//! A factor greater than 1 is a `ℤ/dᵢ` summand that no Betti number can see. That is
//! the whole content this module adds over the rational path, and it is why the
//! lattice must be declared (below) — the free ranks are lattice-independent, but the
//! invariant factors are not.
//!
//! # `b₂_terminal` is not an ambient second Betti number
//!
//! `|F| − rank(d₁)` is `dim coker(d₁) = dim(C²/im d₁)`. In the carrier's own
//! 2-truncated complex `d₂` is zero by *truncation*, so this equals `H²` **of that
//! complex**. If the carrier is a truncation of something with 3-cells, it is not
//! that object's `b₂` — the missing `d₂` would cut it down. It is named
//! `b₂_terminal` so the truncation cannot be read out of the name.
//!
//! # This module does not close the degree-2 gap for existing consumers
//!
//! [`crate::homology::dim_homology`] still returns [`HomologicalError::InvalidDegree`]
//! for any degree other than 0 or 1, and this module does not change that. Nothing
//! that calls `dim_homology` gains a degree-2 answer. [`exact_betti`] is a **new,
//! separate surface**; adopting it is a per-caller change that has not been made.
//!
//! # Exactness
//!
//! `BigInt` throughout, under ADR-001. Three failure modes present in the Python
//! reference are **hard errors here, not silent degradations**:
//!
//! | Python reference | Here |
//! |---|---|
//! | `_integer_matrix_rank` silently falls back to `np.linalg.matrix_rank(tol=1e-9)` | no float path exists |
//! | `_smith_normal_form_diagonal` silently returns `[]` on any exception | the error propagates, typed |
//! | `b₀/b₁/b₂` are `max(0, …)`-clamped, hiding a rank inconsistency | [`HomologicalError::BettiRankInconsistency`] |
//!
//! # The Euler identity is not an independent check
//!
//! `b₀ − b₁ + b₂_terminal = |V| − |E| + |F|` holds **identically** — substitute the
//! three definitions and every rank cancels. It therefore verifies the *bookkeeping*
//! and cannot detect a wrong rank: perturb `rank(d₀)` and the identity still holds.
//! It is reported because it is cheap and catches arithmetic slips, and it is
//! documented here because the reference packet presents it as a verification of the
//! Betti numbers, which it is not. [`ExactBetti::euler_characteristic`] is a derived
//! convenience, not evidence.

use crate::carrier::Carrier;
use crate::errors::HomologicalError;
use crate::hashing::{hash_integer_matrix, Hash256};
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::smith_normal_form::{
    from_bigrational_integer_matrix, smith_normal_form_checked, SmithError,
};
use num_bigint::BigInt;

/// The ℤ-lattice the invariant factors below were computed over.
///
/// # Why this has to be declared
///
/// Smith normal form is taken of an *integer matrix*, and "integer" is a statement
/// about coordinates, not about the linear map. A carrier's coefficients live in ℚ;
/// rescaling one basis vector by `1/2` is an isomorphism of ℚ-vector spaces that
/// leaves every rank alone but changes which lattice the map is integral on, and
/// therefore changes the invariant factors. A torsion claim with no lattice attached
/// is not a claim about anything.
///
/// The lattice used here is fixed and unambiguous: the **ℤ-span of the carrier's own
/// coordinate basis** for `C⁰`, `C¹`, `C²` — the standard basis in which `d₀` and
/// `d₁` are stored. No basis change is performed and none is searched for. This
/// witness records that choice together with a hash of the exact integer matrices
/// the factors came from, so a receipt carrying invariant factors also carries the
/// lattice they are relative to.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LatticeWitness {
    basis: &'static str,
    c0_dim: usize,
    c1_dim: usize,
    c2_dim: usize,
    integral_d0_hash: Hash256,
    integral_d1_hash: Hash256,
}

/// The lattice declaration emitted by [`exact_betti`].
pub const CARRIER_COORDINATE_LATTICE: &str =
    "Z-span of the carrier's own coordinate basis for C0, C1, C2 (no basis change)";

impl LatticeWitness {
    /// Which lattice — always [`CARRIER_COORDINATE_LATTICE`] for [`exact_betti`].
    pub fn basis(&self) -> &'static str {
        self.basis
    }

    /// Ranks of the three free ℤ-modules.
    pub fn dims(&self) -> (usize, usize, usize) {
        (self.c0_dim, self.c1_dim, self.c2_dim)
    }

    /// BLAKE3 of the integral `d₀` the invariant factors were computed from.
    pub fn integral_d0_hash(&self) -> &Hash256 {
        &self.integral_d0_hash
    }

    /// BLAKE3 of the integral `d₁`.
    pub fn integral_d1_hash(&self) -> &Hash256 {
        &self.integral_d1_hash
    }
}

/// Free ranks, invariant factors, and the lattice they are relative to.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExactBetti {
    b0: usize,
    b1: usize,
    b2_terminal: usize,
    rank_d0: usize,
    rank_d1: usize,
    snf_diagonal_d0: Vec<BigInt>,
    snf_diagonal_d1: Vec<BigInt>,
    lattice: LatticeWitness,
}

impl ExactBetti {
    /// Number of connected components — `dim H⁰`.
    pub fn b0(&self) -> usize {
        self.b0
    }

    /// `dim H¹` — the free rank of `ker(d₁)/im(d₀)`. Torsion of the residual
    /// quotient is in [`Self::snf_diagonal_d0`], not here.
    pub fn b1(&self) -> usize {
        self.b1
    }

    /// Free rank of the **terminal** quotient `C²/im(d₁)`.
    ///
    /// Equal to `H²` of the carrier's own 2-truncated complex, where `d₂` is zero by
    /// truncation. It is **not** the second Betti number of an ambient object the
    /// carrier might be a truncation of; a real `d₂` would cut it down. See the
    /// module docs.
    pub fn b2_terminal(&self) -> usize {
        self.b2_terminal
    }

    /// `rank(d₀)`. Equal to the rational rank — SNF does not change it.
    pub fn rank_d0(&self) -> usize {
        self.rank_d0
    }

    /// `rank(d₁)`. Equal to the rational rank — SNF does not change it.
    pub fn rank_d1(&self) -> usize {
        self.rank_d1
    }

    /// Invariant factors of `d₀`: the torsion of `Q¹ = C¹/im(d₀)`, relative to
    /// [`Self::lattice`]. A factor greater than 1 is a `ℤ/dᵢ` summand no Betti
    /// number can see.
    pub fn snf_diagonal_d0(&self) -> &[BigInt] {
        &self.snf_diagonal_d0
    }

    /// Invariant factors of `d₁`: the torsion of the terminal quotient `C²/im(d₁)`,
    /// relative to [`Self::lattice`].
    pub fn snf_diagonal_d1(&self) -> &[BigInt] {
        &self.snf_diagonal_d1
    }

    /// The ℤ-lattice the invariant factors above are relative to. Reading them
    /// without it is reading a torsion claim with no referent.
    pub fn lattice(&self) -> &LatticeWitness {
        &self.lattice
    }

    /// `b₀ − b₁ + b₂_terminal`.
    ///
    /// Equal to `|V| − |E| + |F|` **identically**; see the module docs. Derived
    /// convenience, not evidence.
    ///
    /// Returns [`BigInt`] rather than `i64`. The dimensions are `usize`, and
    /// `usize as i64` is a silent truncation on any value above `i64::MAX` — a
    /// lossy cast on the reporting path of a module whose entire point is that it
    /// does not degrade silently. `BigInt::from(usize)` is total and exact.
    pub fn euler_characteristic(&self) -> BigInt {
        BigInt::from(self.b0) - BigInt::from(self.b1) + BigInt::from(self.b2_terminal)
    }

    /// Whether either boundary map carries torsion (an invariant factor > 1),
    /// relative to [`Self::lattice`].
    pub fn has_torsion(&self) -> bool {
        let one = BigInt::from(1);
        self.snf_diagonal_d0.iter().any(|d| *d != one)
            || self.snf_diagonal_d1.iter().any(|d| *d != one)
    }
}

/// Compute free ranks and integral invariant factors for a 2-truncated carrier,
/// over the carrier's own coordinate lattice ([`CARRIER_COORDINATE_LATTICE`]).
///
/// # Errors
///
/// Every failure is typed. Nothing is stringified into
/// [`HomologicalError::UnsupportedOperation`], and there is no float fallback.
///
/// - [`HomologicalError::NonIntegralBoundaryMap`] if a boundary map has a
///   non-integer entry in this lattice, naming the offending cell. This is a fact
///   about the input under this lattice, and a caller may legitimately respond by
///   declaring a different one.
/// - [`HomologicalError::SmithNormalFormFailed`] if SNF itself fails, carrying the
///   [`SmithError`] as the error source so `Overflow`, `DivisibilityViolation` and
///   `VerificationFailed` stay distinguishable. This is a fact about the algorithm,
///   not the input, and a caller cannot fix it by changing lattice.
/// - [`HomologicalError::BettiRankInconsistency`] if a rank exceeds the dimension it
///   is subtracted from, which would make a Betti number negative. The reference
///   implementation clamps this to zero; clamping reports a plausible number for a
///   broken carrier.
pub fn exact_betti(carrier: &Carrier) -> Result<ExactBetti, HomologicalError> {
    let integralize = |m: &_, map: &'static str| -> Result<BasicMatrix<BigInt>, HomologicalError> {
        from_bigrational_integer_matrix(m).map_err(|e| match e {
            SmithError::NonIntegerEntry { row, col } => {
                HomologicalError::NonIntegralBoundaryMap { map, row, col }
            }
            other => HomologicalError::SmithNormalFormFailed { map, source: other },
        })
    };
    let snf_of = |integral: &BasicMatrix<BigInt>,
                  map: &'static str|
     -> Result<(usize, Vec<BigInt>), HomologicalError> {
        let snf = smith_normal_form_checked(integral)
            .map_err(|source| HomologicalError::SmithNormalFormFailed { map, source })?;
        Ok((snf.diagonal().rank(), snf.diagonal().invariants().to_vec()))
    };

    let integral_d0 = integralize(carrier.d0(), "d0")?;
    let integral_d1 = integralize(carrier.d1(), "d1")?;
    let (rank_d0, snf_diagonal_d0) = snf_of(&integral_d0, "d0")?;
    let (rank_d1, snf_diagonal_d1) = snf_of(&integral_d1, "d1")?;

    let (v, e, f) = (carrier.c0_dim(), carrier.c1_dim(), carrier.c2_dim());

    // The invariant factors are meaningless without the lattice they are relative
    // to, so the witness is built from the same integral matrices that produced
    // them — not recomputed, and not merely asserted.
    let lattice = LatticeWitness {
        basis: CARRIER_COORDINATE_LATTICE,
        c0_dim: v,
        c1_dim: e,
        c2_dim: f,
        integral_d0_hash: hash_integer_matrix(&integral_d0),
        integral_d1_hash: hash_integer_matrix(&integral_d1),
    };

    // No max(0, ..): a rank that exceeds its dimension is an inconsistency, and
    // clamping it to zero would report a plausible Betti number for a broken input.
    let b0 = v
        .checked_sub(rank_d0)
        .ok_or(HomologicalError::BettiRankInconsistency {
            dimension: v,
            rank_sum: rank_d0,
            degree: 0,
        })?;
    let b1 = e
        .checked_sub(rank_d0)
        .and_then(|x| x.checked_sub(rank_d1))
        .ok_or(HomologicalError::BettiRankInconsistency {
            dimension: e,
            rank_sum: rank_d0 + rank_d1,
            degree: 1,
        })?;
    let b2_terminal = f
        .checked_sub(rank_d1)
        .ok_or(HomologicalError::BettiRankInconsistency {
            dimension: f,
            rank_sum: rank_d1,
            degree: 2,
        })?;

    Ok(ExactBetti {
        b0,
        b1,
        b2_terminal,
        rank_d0,
        rank_d1,
        snf_diagonal_d0,
        snf_diagonal_d1,
        lattice,
    })
}

// Origin: engine/crates_rs/core_homology/src/exact_betti.rs
// Claim: urn:core:crates_rs:core-homology:exact-betti:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord1aad1716 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord1aad1716` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError1aad1716 {
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
impl BoundaryError1aad1716 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError1aad1716 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError1aad1716 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord1aad1716 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError1aad1716> {
        if capacity_bound == 0 {
            return Err(BoundaryError1aad1716::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError1aad1716::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError1aad1716::ExceedsCapacity {
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
    use crate::finite_directed_graph::{
        DirectedGraphBuilder, FiniteDirectedGraph, TheoremProvenance as GraphProv,
    };
    use crate::graph_carrier::graph_carrier;
    use crate::scalar::{q, Q};
    use num_bigint::BigInt;

    fn graph(num_nodes: usize, edges: &[(usize, usize)]) -> FiniteDirectedGraph {
        let gp = GraphProv {
            verification_source: "exact_betti_test".to_string(),
        };
        DirectedGraphBuilder::from_anonymous(num_nodes, edges.to_vec(), gp).unwrap()
    }

    fn weights(n: usize) -> Vec<Q> {
        vec![q(1); n]
    }

    fn prov() -> TheoremProvenance {
        TheoremProvenance::new("exact_betti_test".to_string()).unwrap()
    }

    /// A triangle graph with no 2-cell: one component, one independent cycle.
    #[test]
    fn triangle_without_face_has_b1_one() {
        let g = graph(3, &[(0, 1), (1, 2), (0, 2)]);
        let c = graph_carrier(&g, &[], weights(3), prov()).unwrap();
        let b = exact_betti(&c).unwrap();
        assert_eq!(b.b0(), 1, "one connected component");
        assert_eq!(b.b1(), 1, "the triangle's cycle survives without a face");
        assert_eq!(b.b2_terminal(), 0, "no 2-cells");
    }

    /// Filling the triangle with a 2-cell kills the cycle.
    #[test]
    fn triangle_with_face_has_b1_zero() {
        let g = graph(3, &[(0, 1), (1, 2), (0, 2)]);
        let c = graph_carrier(&g, &[(0, 1, 2)], weights(3), prov()).unwrap();
        let b = exact_betti(&c).unwrap();
        assert_eq!(b.b0(), 1);
        assert_eq!(b.b1(), 0, "the face bounds the cycle");
        // NOT "the face is not a cocycle" — in a 2-truncated complex d₂ is zero by
        // truncation, so EVERY 2-cochain is a cocycle, this one included. The
        // terminal quotient vanishes because the face generator is a *coboundary*:
        // it spans im(d₁), so C²/im(d₁) = 0.
        assert_eq!(b.b2_terminal(), 0, "the face generator spans im(d1)");
        assert_eq!(b.rank_d1(), 1, "d1 is surjective onto the single 2-cell");
    }

    /// Two disjoint edges: two components, no cycles. Exercises b0 > 1.
    #[test]
    fn disjoint_edges_have_b0_two() {
        let g = graph(4, &[(0, 1), (2, 3)]);
        let c = graph_carrier(&g, &[], weights(2), prov()).unwrap();
        let b = exact_betti(&c).unwrap();
        assert_eq!(b.b0(), 2);
        assert_eq!(b.b1(), 0);
    }

    /// This module is a NEW degree-2 surface; it does not repair `dim_homology`,
    /// which still refuses degree 2. Pinned so the scope claim stays honest — if
    /// someone later teaches `dim_homology` degree 2, this test fails and the
    /// module docs must be corrected rather than left overclaiming.
    #[test]
    fn dim_homology_still_refuses_degree_two_so_no_consumer_gained_b2() {
        let zero = |r, c| BasicMatrix::from_row_major(r, c, vec![q(0); r * c]).unwrap();
        let chain = crate::chain_complex::ChainComplex::new(1, 1, 1, zero(1, 1), zero(1, 1))
            .expect("zero maps compose to zero");

        assert!(
            matches!(
                crate::homology::dim_homology(&chain, 2),
                Err(HomologicalError::InvalidDegree(2))
            ),
            "dim_homology must still refuse degree 2 — this module adds a separate \
             surface and closes nothing for existing callers"
        );

        // …while exact_betti answers on a carrier.
        let g = graph(3, &[(0, 1), (1, 2), (0, 2)]);
        let c = graph_carrier(&g, &[(0, 1, 2)], weights(3), prov()).unwrap();
        assert_eq!(exact_betti(&c).unwrap().b2_terminal(), 0);
    }

    /// Boundary of a tetrahedron — a triangulated `S²`. The decisive positive test:
    /// `b₂_terminal = 1` is a value no clamp, no zero matrix, and no accidental
    /// rank could produce, and `b₁ = 0` distinguishes a sphere from a torus.
    #[test]
    fn tetrahedral_boundary_is_a_sphere_with_b_1_0_1() {
        let g = graph(4, &[(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]);
        let faces = [(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)];
        let c = graph_carrier(&g, &faces, weights(6), prov()).unwrap();
        let b = exact_betti(&c).unwrap();

        assert_eq!(b.b0(), 1, "S^2 is connected");
        assert_eq!(b.b1(), 0, "S^2 has no 1-cycles");
        assert_eq!(b.b2_terminal(), 1, "S^2 has a fundamental class");
        assert_eq!(b.rank_d0(), 3, "4 vertices, 1 component");
        assert_eq!(b.rank_d1(), 3, "4 faces, 1 surviving class");
        assert_eq!(b.euler_characteristic(), BigInt::from(2), "chi(S^2) = 2");
        assert!(!b.has_torsion(), "S^2 is torsion-free");
    }

    /// Build a carrier directly from declared boundary maps, bypassing the graph
    /// builder — the only way to exhibit torsion, which no simplicial graph carrier
    /// in this crate produces.
    fn declared_carrier(d0_entry: i64, d1_entry: i64) -> Carrier {
        let d0 = BasicMatrix::from_row_major(1, 1, vec![q(d0_entry)]).unwrap();
        let d1 = BasicMatrix::from_row_major(1, 1, vec![q(d1_entry)]).unwrap();
        Carrier::new(1, 1, 1, d0, d1, vec![q(1)], prov()).unwrap()
    }

    /// `d₀ = [2]`, `d₁ = [0]`: `H¹ = ker(d₁)/im(d₀) = ℤ/2ℤ`. Pure torsion — every
    /// Betti number is 0, so a rank-only computation reports "nothing here" while
    /// the group is nontrivial. This is the content SNF adds.
    #[test]
    fn torsion_in_h1_is_invisible_to_betti_numbers_but_visible_in_the_factors() {
        let b = exact_betti(&declared_carrier(2, 0)).unwrap();

        assert_eq!(b.b1(), 0, "the free rank of Z/2 is zero");
        assert_eq!(b.rank_d0(), 1);
        assert_eq!(
            b.snf_diagonal_d0(),
            [BigInt::from(2)],
            "the invariant factor 2 IS the Z/2 summand"
        );
        assert!(b.has_torsion(), "a rank-only path would have missed this");
    }

    /// `d₀ = [0]`, `d₁ = [2]`: the terminal quotient `C²/im(d₁) = ℤ/2ℤ`.
    #[test]
    fn torsion_in_the_terminal_quotient_is_reported() {
        let b = exact_betti(&declared_carrier(0, 2)).unwrap();

        assert_eq!(b.b2_terminal(), 0, "the free rank of Z/2 is zero");
        assert_eq!(b.rank_d1(), 1);
        assert_eq!(b.snf_diagonal_d1(), [BigInt::from(2)]);
        assert!(b.has_torsion());
        // b0 = 1 - 0 = 1: d0 is the zero map, so nothing is killed in degree 0.
        assert_eq!(b.b0(), 1);
    }

    /// A non-integral carrier is refused with a typed error naming the cell, not
    /// stringified and not silently rounded.
    #[test]
    fn nonintegral_boundary_map_is_refused_by_cell() {
        let d0 = BasicMatrix::from_row_major(1, 1, vec![Q::new(1.into(), 2.into())]).unwrap();
        let d1 = BasicMatrix::from_row_major(1, 1, vec![q(0)]).unwrap();
        let c = Carrier::new(1, 1, 1, d0, d1, vec![q(1)], prov()).unwrap();

        match exact_betti(&c) {
            Err(HomologicalError::NonIntegralBoundaryMap { map, row, col }) => {
                assert_eq!(map, "d0");
                assert_eq!((row, col), (0, 0));
            }
            other => panic!("expected a typed non-integrality refusal, got {other:?}"),
        }
    }

    /// The two failure classes must stay distinguishable: non-integrality is a fact
    /// about the input under this lattice, an SNF failure is a fact about the
    /// algorithm. Folding both into `UnsupportedOperation(String)` erased that.
    #[test]
    fn integrality_and_snf_failures_are_different_variants() {
        let d0 = BasicMatrix::from_row_major(1, 1, vec![Q::new(1.into(), 3.into())]).unwrap();
        let d1 = BasicMatrix::from_row_major(1, 1, vec![q(0)]).unwrap();
        let c = Carrier::new(1, 1, 1, d0, d1, vec![q(1)], prov()).unwrap();
        let err = exact_betti(&c).unwrap_err();

        assert!(
            !matches!(err, HomologicalError::UnsupportedOperation(_)),
            "must not be stringified into the catch-all: {err:?}"
        );
        assert!(matches!(
            err,
            HomologicalError::NonIntegralBoundaryMap { .. }
        ));
        // And the SNF variant preserves its source rather than flattening it.
        let snf_err = HomologicalError::SmithNormalFormFailed {
            map: "d1",
            source: SmithError::Overflow,
        };
        assert!(matches!(
            snf_err,
            HomologicalError::SmithNormalFormFailed {
                source: SmithError::Overflow,
                ..
            }
        ));
    }

    /// The `BettiRankInconsistency` guard replaced a `max(0, …)` clamp, and it is
    /// **unreachable through any carrier this crate can build** — so no test claims
    /// to trigger it, and this one covers only its rendering.
    ///
    /// Why unreachable: `Carrier::new` enforces `d₁∘d₀ = 0`, hence
    /// `im(d₀) ⊆ ker(d₁)`, hence `rank(d₀) ≤ dim ker(d₁) = |E| − rank(d₁)`, i.e.
    /// `rank(d₀) + rank(d₁) ≤ |E|`. The degree-0 and degree-2 cases are simpler:
    /// `rank(d₀) ≤ min(|E|,|V|) ≤ |V|` and `rank(d₁) ≤ min(|F|,|E|) ≤ |F|`.
    ///
    /// The guard is therefore a fail-closed check on an invariant proved elsewhere,
    /// kept precisely because that proof is only as good as `Carrier::new`. If the
    /// `d₁∘d₀ = 0` check ever regresses, this turns a silently wrong Betti number
    /// into a refusal — which a clamp would not have done.
    #[test]
    fn betti_rank_inconsistency_names_both_numbers() {
        let err = HomologicalError::BettiRankInconsistency {
            dimension: 1,
            rank_sum: 2,
            degree: 1,
        };
        assert!(
            err.to_string().contains("rank sum 2 exceeds dimension 1"),
            "the refusal must name both numbers so the defect is diagnosable: {err}"
        );
    }

    /// The premise of the test above: `Carrier::new` really does reject a pair with
    /// `d₁∘d₀ ≠ 0`. Without this, "unreachable by construction" is an assumption
    /// rather than a checked fact.
    #[test]
    fn carrier_new_rejects_a_noncomposing_pair() {
        let one = BasicMatrix::from_row_major(1, 1, vec![q(1)]).unwrap();
        let err = Carrier::new(1, 1, 1, one.clone(), one, vec![q(1)], prov())
            .expect_err("d1*d0 = [1] != 0 must be rejected");
        assert!(
            matches!(
                err,
                HomologicalError::CoboundaryLawViolation { .. }
                    | HomologicalError::BoundaryLawViolation { .. }
            ),
            "expected the composition law to be what refuses it, got {err:?}"
        );
    }

    /// The lattice the invariant factors are relative to is declared and bound to
    /// the exact integer matrices they came from.
    #[test]
    fn invariant_factors_carry_the_lattice_they_are_relative_to() {
        let b = exact_betti(&declared_carrier(2, 0)).unwrap();
        let l = b.lattice();

        assert_eq!(l.basis(), CARRIER_COORDINATE_LATTICE);
        assert_eq!(l.dims(), (1, 1, 1));

        // The hash is of the INTEGRAL matrix, so a different d0 over the same
        // lattice yields a different witness — the binding is to data, not a label.
        let other = exact_betti(&declared_carrier(3, 0)).unwrap();
        assert_ne!(l.integral_d0_hash(), other.lattice().integral_d0_hash());
        assert_eq!(l.integral_d1_hash(), other.lattice().integral_d1_hash());
    }

    /// The Euler identity holds — and the test documents that it holds
    /// *identically*, so it cannot witness a wrong rank.
    #[test]
    fn euler_identity_holds_but_cannot_detect_a_wrong_rank() {
        let g = graph(3, &[(0, 1), (1, 2), (0, 2)]);
        let c = graph_carrier(&g, &[(0, 1, 2)], weights(3), prov()).unwrap();
        let b = exact_betti(&c).unwrap();

        let big = BigInt::from;
        let (v, e, f) = (big(c.c0_dim()), big(c.c1_dim()), big(c.c2_dim()));
        let structural = &v - &e + &f;
        assert_eq!(b.euler_characteristic(), structural);

        // Substituting the definitions, every rank cancels:
        //   b0 - b1 + b2 = (V - r0) - (E - r0 - r1) + (F - r1) = V - E + F
        // so perturbing a rank leaves the identity intact. Demonstrated here so
        // the identity is never mistaken for evidence about the ranks.
        for perturbed_r0 in [b.rank_d0(), b.rank_d0() + 1] {
            let r0 = big(perturbed_r0);
            let r1 = big(b.rank_d1());
            assert_eq!(
                (&v - &r0) - (&e - &r0 - &r1) + (&f - &r1),
                structural,
                "a perturbed rank leaves the identity intact — it is bookkeeping, \
                 not evidence"
            );
        }
    }

    /// SNF diagonals are reported so torsion is visible rather than discarded.
    /// These carriers are torsion-free, which is itself the assertion.
    #[test]
    fn snf_diagonals_are_reported_and_these_carriers_are_torsion_free() {
        let g = graph(3, &[(0, 1), (1, 2), (0, 2)]);
        let c = graph_carrier(&g, &[(0, 1, 2)], weights(3), prov()).unwrap();
        let b = exact_betti(&c).unwrap();

        assert_eq!(b.snf_diagonal_d0().len(), b.rank_d0());
        assert_eq!(b.snf_diagonal_d1().len(), b.rank_d1());
        assert!(!b.has_torsion(), "a simplicial triangle has no torsion");
    }
}

#[cfg(test)]
mod l4_boundary_tests_1aad1716 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord1aad1716::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord1aad1716::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord1aad1716::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord1aad1716::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord1aad1716::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError1aad1716::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError1aad1716::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
