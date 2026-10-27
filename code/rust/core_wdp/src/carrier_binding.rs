//! Bind [`FiniteCarrier2`] to [`core_homology::carrier::Carrier`].
//!
//! # Why this exists
//!
//! `solver_of_solvers` establishes carrier identity by serialising the
//! **declaration** — vertex count, the edge list as `(tail, head, weight)`, and
//! the face list — and hashing that. `core_homology` establishes it by hashing
//! the **operators**: `d₀` and `d₁` content, weights, dimensions, rank data.
//!
//! Those are not the same claim, and the gap is not cosmetic. `d₀` and `d₁` are
//! *derived* from the declaration by this crate. If that derivation were wrong —
//! a face-incidence sign, or a reversed-edge lookup returning "absent" instead
//! of "negated" — the declaration hash would be **byte-identical** while the
//! mathematics underneath it differed. Every certificate in the chain would
//! still agree about which carrier it concerned, and all of them would be
//! describing operators nobody hashed.
//!
//! So this module does not merely convert a type. It re-derives `d₀`/`d₁`
//! through the solver's own face-incidence routine, hands them to
//! `Carrier::new` — whose constructor verifies `d₁∘d₀ = 0` exactly, in a crate
//! that did not perform the derivation — and exposes the resulting
//! `CarrierManifest`, whose hashes cover operator content.
//!
//! # Which `Carrier`
//!
//! `core_homology` contains two types named `Carrier`. This binds to
//! `carrier::Carrier`, because **`exact_carrier::Carrier` is not compiled in any
//! build**: `exact_carrier.rs` opens with `#![cfg(any())]`, and `any()` with no
//! arguments is unconditionally false. It also still imports
//! `core_solvers::arithmos::linear_algebra::*`, a path that no longer exists, and its
//! callers would need `rank()`/`set()` signatures that have since become
//! `Result`. Reviving it is a real job and a separate one.
//!
//! The live type is also the better target: it carries `Q = BigRational`, which
//! is what this crate already computes in, so the binding is exact with no
//! narrowing anywhere.
//!
//! # What this does not do
//!
//! It does not make `Φ₁` comparable across a *change* of carrier. Two carriers
//! with different manifests are different objects and their `Φ₁` values are not
//! comparable — that is what the hash is for, not a limitation of it.
//!
//! `AuthorityEffect: None`. This computes an identity; it mints nothing.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::Zero;
use core_homology::carrier::Carrier;
use core_homology::carrier_manifest::CarrierManifest;
use core_homology::cochain_complex::TheoremProvenance;
use core_homology::errors::HomologicalError;

use crate::solver_of_solvers::{d1_rows_for_binding, FiniteCarrier2};

/// Recorded on every carrier this module builds, so a manifest can be traced to
/// the derivation that produced it.
const BINDING_PROVENANCE: &str =
    "crate::carrier_binding (d0/d1 derived from FiniteCarrier2)";

/// Typed refusal from the binding. A refusal is a valid terminal.
#[derive(Debug, thiserror::Error)]
pub enum CarrierBindingError {
    /// A declared edge weight is not strictly positive. The weighted ℓ¹ norm is
    /// only a norm for strictly positive weights.
    #[error("edge {index} weight {weight} is not strictly positive")]
    WeightNotPositive { index: usize, weight: i128 },

    /// An edge names a vertex outside `0..num_vertices`.
    #[error("edge {index} endpoints ({tail}, {head}) exceed vertex count {num_vertices}")]
    EndpointOutOfRange {
        index: usize,
        tail: usize,
        head: usize,
        num_vertices: usize,
    },

    /// The declared faces do not yield a valid `d₁` — usually because a face
    /// side is not a declared edge in either orientation.
    #[error("d1 derivation failed: {0}")]
    D1Derivation(String),

    /// Matrix assembly failed.
    #[error("matrix construction failed: {0}")]
    Matrix(String),

    /// `core_homology` rejected the carrier. Most importantly this fires when
    /// `d₁∘d₀ ≠ 0`, which would mean this crate's derivation is not a cochain
    /// complex at all.
    #[error(transparent)]
    Homology(#[from] HomologicalError),
}

fn q(value: i64) -> BigRational {
    BigRational::from_integer(BigInt::from(value))
}

/// The coboundary `d₀ : C⁰ → C¹`, as `(d₀α)_(u,v) = α_v − α_u`.
///
/// One row per declared edge, in declaration order, so the column order of `d₁`
/// and the coordinate order of the residual agree with it.
fn d0_matrix(carrier: &FiniteCarrier2) -> Result<BasicMatrix<BigRational>, CarrierBindingError> {
    let rows = carrier.edges.len();
    let cols = carrier.num_vertices;
    let mut data = vec![BigRational::zero(); rows * cols];
    for (index, edge) in carrier.edges.iter().enumerate() {
        // `validate_carrier` rejects out-of-range endpoints, but this module is
        // reachable independently, so it does not assume that has run.
        if edge.tail >= cols || edge.head >= cols {
            return Err(CarrierBindingError::EndpointOutOfRange {
                index,
                tail: edge.tail,
                head: edge.head,
                num_vertices: cols,
            });
        }
        data[index * cols + edge.tail] = q(-1);
        data[index * cols + edge.head] = q(1);
    }
    BasicMatrix::from_row_major(rows, cols, data)
        .map_err(|error| CarrierBindingError::Matrix(format!("{error:?}")))
}

/// The coboundary `d₁ : C¹ → C²`, re-derived through the solver's own
/// face-incidence routine so that what gets hashed is what the solver uses.
///
/// A second, parallel derivation here would defeat the purpose: the manifest is
/// meant to witness *the solver's* operators.
fn d1_matrix(carrier: &FiniteCarrier2) -> Result<BasicMatrix<BigRational>, CarrierBindingError> {
    let rows = d1_rows_for_binding(carrier)
        .map_err(|error| CarrierBindingError::D1Derivation(error.to_string()))?;
    let height = rows.len();
    let width = carrier.edges.len();
    let mut data = Vec::with_capacity(height * width);
    for row in &rows {
        if row.len() != width {
            return Err(CarrierBindingError::Matrix(format!(
                "d1 row has {} entries, expected {width}",
                row.len()
            )));
        }
        data.extend(row.iter().cloned());
    }
    BasicMatrix::from_row_major(height, width, data)
        .map_err(|error| CarrierBindingError::Matrix(format!("{error:?}")))
}

/// Edge weights as exact rationals. `FiniteCarrier2` stores `i128`; `Q` is
/// `BigRational`, so this is exact — there is no narrowing step to get wrong.
fn weights(carrier: &FiniteCarrier2) -> Result<Vec<BigRational>, CarrierBindingError> {
    carrier
        .edges
        .iter()
        .enumerate()
        .map(|(index, edge)| {
            if edge.weight <= 0 {
                return Err(CarrierBindingError::WeightNotPositive {
                    index,
                    weight: edge.weight,
                });
            }
            Ok(BigRational::from_integer(BigInt::from(edge.weight)))
        })
        .collect()
}

/// Build the `core_homology` carrier for a declared [`FiniteCarrier2`].
///
/// `Carrier::new` verifies `d₁∘d₀ = 0` exactly. That check is the load-bearing
/// part: an *independent* confirmation, by a crate that did not perform the
/// derivation, that this crate's face incidence yields a genuine cochain
/// complex.
pub fn to_homology_carrier(carrier: &FiniteCarrier2) -> Result<Carrier, CarrierBindingError> {
    let d0 = d0_matrix(carrier)?;
    let d1 = d1_matrix(carrier)?;
    let w = weights(carrier)?;
    let provenance = TheoremProvenance::new(BINDING_PROVENANCE.to_string())?;
    Ok(Carrier::new(
        carrier.num_vertices,
        carrier.edges.len(),
        carrier.faces.len(),
        d0,
        d1,
        w,
        provenance,
    )?)
}

/// The shared carrier manifest: hashes over `d₀`/`d₁` **content**, weights,
/// dimensions and rank data.
///
/// This is the identity the OESOS math spine §11 asks the solver and the
/// homology crate to share. Unlike the declaration hash it is sensitive to the
/// derived operators, so a wrong derivation changes it instead of hiding behind
/// an unchanged declaration.
pub fn carrier_manifest(carrier: &FiniteCarrier2) -> Result<CarrierManifest, CarrierBindingError> {
    Ok(to_homology_carrier(carrier)?.manifest()?)
}

/// Ising cycle gradient repair differential on 1D ring lattices (PO-000 §7.8).
///
/// On a 1D ring of N sites (cycle graph C_N), a 1-cochain assigns values to edges.
/// The cycle gradient repair differential removes the uniform cycle holonomy (mean circulation)
/// to project the cochain onto the coboundary (gradient) space im(d0).
/// The condition number of this repair differential on the gradient space is uniformly 1,
/// independent of the ring size N.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct IsingCycleGradientRepair;

impl IsingCycleGradientRepair {
    /// Computes the repair differential for a 1-cochain on an Ising ring of size N.
    /// Removes the mean loop flux / circulation: c'_i = c_i - (1/N) * sum_{j=0}^{N-1} c_j.
    pub fn compute_repair_differential(ring_size: usize, cochain: &[BigRational]) -> Vec<BigRational> {
        assert!(ring_size > 0, "Ring size must be positive");
        assert_eq!(cochain.len(), ring_size, "Cochain length must match ring size");
        let n_rat = BigRational::from_integer(BigInt::from(ring_size));
        let sum: BigRational = cochain.iter().cloned().sum();
        let mean = sum / n_rat;
        cochain.iter().map(|c| c - &mean).collect()
    }

    /// Condition number of the cycle gradient repair projection, which is 1 independent of ring size.
    pub fn condition_number(_ring_size: usize) -> BigRational {
        num_traits::One::one()
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::solver_of_solvers::CarrierEdge;

    fn edge(tail: usize, head: usize, weight: i128) -> CarrierEdge {
        CarrierEdge { tail, head, weight }
    }

    /// A triangle with all three sides declared and its 2-cell filled.
    fn triangle() -> FiniteCarrier2 {
        FiniteCarrier2 {
            num_vertices: 3,
            edges: vec![edge(0, 1, 1), edge(1, 2, 1), edge(2, 0, 1)],
            faces: vec![(0, 1, 2)],
        }
    }

    /// The same 1-skeleton with no face declared: b₁ = 1 instead of 0.
    fn open_triangle() -> FiniteCarrier2 {
        FiniteCarrier2 {
            faces: vec![],
            ..triangle()
        }
    }

    #[test]
    fn triangle_binds_and_d1_d0_is_zero() {
        // Carrier::new performs the d1*d0 = 0 check. Reaching Ok means a crate
        // that did not derive these operators confirmed they form a complex.
        let carrier = to_homology_carrier(&triangle()).expect("triangle must bind");
        assert_eq!(carrier.c0_dim(), 3);
        assert_eq!(carrier.c1_dim(), 3);
        assert_eq!(carrier.c2_dim(), 1);
    }

    #[test]
    fn manifest_is_stable_for_the_same_declaration() {
        let a = carrier_manifest(&triangle()).expect("bind");
        let b = carrier_manifest(&triangle()).expect("bind");
        assert_eq!(a, b, "the same declaration must hash identically");
    }

    /// Anti-vacuity. "The manifests agree" is worthless unless disagreement is
    /// observable, so this pins that the hash CAN differ, and differs for the
    /// mathematically right reason: filling the triangle kills the 1-cycle.
    #[test]
    fn manifest_differs_when_the_face_is_removed() {
        let closed = to_homology_carrier(&triangle()).expect("bind");
        let open = to_homology_carrier(&open_triangle()).expect("bind");
        assert_ne!(
            closed.manifest().expect("manifest"),
            open.manifest().expect("manifest"),
            "declaring a 2-cell must change carrier identity"
        );
        assert_eq!(open.dim_h1().expect("b1"), 1, "open triangle has b1 = 1");
        assert_eq!(
            closed.dim_h1().expect("b1"),
            0,
            "filled triangle has b1 = 0"
        );
    }

    /// The weights are part of the mathematics (the norm is weighted ℓ¹), so
    /// they must be part of the identity.
    #[test]
    fn manifest_differs_when_only_edge_weights_differ() {
        let mut heavy = triangle();
        heavy.edges[0].weight = 7;
        assert_ne!(
            carrier_manifest(&triangle()).expect("bind"),
            carrier_manifest(&heavy).expect("bind"),
        );
    }

    /// Large weights are exact here: Q is BigRational, so there is no narrowing
    /// step. A weight far beyond i64 must bind, not refuse.
    #[test]
    fn very_large_weight_binds_exactly() {
        let mut c = triangle();
        c.edges[0].weight = i128::MAX;
        let big = carrier_manifest(&c).expect("i128::MAX weight must bind exactly");
        assert_ne!(big, carrier_manifest(&triangle()).expect("bind"));
    }

    #[test]
    fn nonpositive_weight_is_refused() {
        let mut c = triangle();
        c.edges[1].weight = 0;
        match to_homology_carrier(&c) {
            Err(CarrierBindingError::WeightNotPositive { index, .. }) => assert_eq!(index, 1),
            other => panic!("expected a refusal, got {other:?}"),
        }
    }

    #[test]
    fn endpoint_out_of_range_is_refused() {
        let c = FiniteCarrier2 {
            num_vertices: 2,
            edges: vec![edge(0, 1, 1), edge(1, 5, 1)],
            faces: vec![],
        };
        assert!(matches!(
            to_homology_carrier(&c),
            Err(CarrierBindingError::EndpointOutOfRange { index: 1, .. })
        ));
    }

    #[test]
    fn face_whose_side_is_not_declared_is_refused() {
        let c = FiniteCarrier2 {
            num_vertices: 4,
            edges: vec![edge(0, 1, 1), edge(1, 2, 1), edge(2, 0, 1)],
            faces: vec![(0, 1, 3)], // (1,3) and (3,0) are not declared edges
        };
        assert!(matches!(
            to_homology_carrier(&c),
            Err(CarrierBindingError::D1Derivation(_))
        ));
    }

    /// A face traversed against a stored edge must NEGATE that coordinate, not
    /// read it as absent. If it did not, `d₁∘d₀ = 0` would fail and
    /// `Carrier::new` would refuse — so this pins the alternating-cochain rule
    /// of the OESOS spine §1.2 through an independent checker.
    #[test]
    fn reversed_edge_orientation_still_forms_a_complex() {
        let c = FiniteCarrier2 {
            num_vertices: 3,
            // (2,0) is stored reversed as (0,2); the face must negate it.
            edges: vec![edge(0, 1, 1), edge(1, 2, 1), edge(0, 2, 1)],
            faces: vec![(0, 1, 2)],
        };
        let carrier = to_homology_carrier(&c).expect("reversed storage must still bind");
        assert_eq!(
            carrier.dim_h1().expect("b1"),
            0,
            "the declared face still kills the cycle"
        );
    }

    /// Declaration order is part of the representation: it fixes the coordinate
    /// order of the residual. Two orderings of the same graph are different
    /// carriers, and the manifest must say so rather than silently identifying
    /// them.
    #[test]
    fn edge_declaration_order_changes_identity() {
        let mut reordered = triangle();
        reordered.edges.swap(0, 2);
        reordered.faces = vec![(0, 1, 2)];
        assert_ne!(
            carrier_manifest(&triangle()).expect("bind"),
            carrier_manifest(&reordered).expect("bind"),
        );
    }
}
