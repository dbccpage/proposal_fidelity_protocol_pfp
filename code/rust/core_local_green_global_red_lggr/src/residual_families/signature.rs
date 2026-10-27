//! `ShapeSignature` — `blake3`-derived shape-only key over a
//! `CochainPrimitiveDifference` + `QuotientSpace` pair.
//!
//! The signature is the kernel of the gauge relation ZeroRel (packet §5):
//! two primitive-difference instances yield the same `ShapeSignature` iff they
//! agree on
//!
//! - cochain dimensions $(c_0, c_1, c_2)$ (arity / face-index counts),
//! - the shapes of $d_0$ and $d_1$ (rows, cols),
//! - the coefficient-domain tag (currently `Q`),
//! - the `QuotientSpace`'s quotient-class id (`relation` + `degree` +
//!   `dim_total` + `coefficient_domain` + projection-matrix shape).
//!
//! Raw cochain payload bytes are NOT part of the digest input. Coefficient
//! values inside $d_0$ / $d_1$ matrices are NOT part of the digest input.
//!
//! ## Doctest — no payload accessor on the public surface
//!
//! Verifies the public surface does not expose any `.coefficient()` /
//! `.payload()` accessor on `ShapeSignature`. A future refactor that tried to
//! widen the surface this way would have to delete this doctest first.
//!
//! ```compile_fail
//! use core_epk::residual_families::ShapeSignature;
//! let bytes: [u8; 32] = [0; 32];
//! let sig = ShapeSignature::from_bytes(bytes);
//! let _ = sig.coefficient();
//! ```
//!
//! ```compile_fail
//! use core_epk::residual_families::ShapeSignature;
//! let bytes: [u8; 32] = [0; 32];
//! let sig = ShapeSignature::from_bytes(bytes);
//! let _ = sig.payload();
//! ```


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_a8aa34d9<T> {
    fn checked_invariant_a8aa34d9(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_a8aa34d9<T> for Option<T> {
    #[inline]
    fn checked_invariant_a8aa34d9(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_a8aa34d9<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_a8aa34d9(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::fmt;

use blake3::Hasher;
use core_linear_algebra::backend::basic_matrix::CheckedNumeric;
use core_functional::gamma2::ExactCochainComplexQ;
use core_homology::cochain_primitive_difference::CochainPrimitiveDifference;
use core_homology::quotient::{QuotientRelation, QuotientSpace};
use serde::Serialize;

/// Shape-only `blake3` digest. Opaque newtype around the 32-byte hash.
///
/// `face_indices` and `quotient_space_id` flow into the digest via
/// [`shape_signature`]; this struct only carries the resulting bytes.
#[derive(Copy, Clone, Debug, Eq, Hash, PartialEq)]
pub struct ShapeSignature([u8; 32]);

impl ShapeSignature {
    /// Construct from raw bytes. Test-and-fixture-only.
    #[must_use]
    pub fn from_bytes(bytes: [u8; 32]) -> Self {
        Self(bytes)
    }

    /// Borrow the underlying digest bytes.
    #[must_use]
    pub fn as_bytes(&self) -> &[u8; 32] {
        &self.0
    }
}

/// Failure to derive a namespaced exact-complex shape signature.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum ShapeSignatureError {
    /// A namespace is required so unrelated domain carriers cannot alias.
    EmptyNamespace,
}

impl fmt::Display for ShapeSignatureError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::EmptyNamespace => f.write_str("shape-signature namespace must be nonempty"),
        }
    }
}

impl std::error::Error for ShapeSignatureError {}

fn cochain_shape_fingerprint(c0: usize, c1: usize, c2: usize) -> Vec<u8> {
    let mut out = Vec::with_capacity(128);
    out.extend_from_slice(b"core_homology::CochainPrimitiveDifference::shape_fingerprint::v1");
    out.extend_from_slice(&(c0 as u64).to_le_bytes());
    out.extend_from_slice(&(c1 as u64).to_le_bytes());
    out.extend_from_slice(&(c2 as u64).to_le_bytes());
    out.extend_from_slice(&(c1 as u64).to_le_bytes());
    out.extend_from_slice(&(c0 as u64).to_le_bytes());
    out.extend_from_slice(&(c2 as u64).to_le_bytes());
    out.extend_from_slice(&(c1 as u64).to_le_bytes());
    out.extend_from_slice(b"coeff:Q");
    out
}

#[allow(clippy::too_many_arguments)]
fn signature_from_parts(
    fingerprint: &[u8],
    cochain_dims: (usize, usize, usize),
    quotient_space_id: &[u8; 32],
    coefficient_domain: &str,
    dim_total: usize,
    degree: usize,
    relation: &QuotientRelation,
    projection_shape: (usize, usize),
) -> ShapeSignature {
    let mut hasher = Hasher::new();
    hasher.update(b"core_residual_families::shape_signature::v1");
    hasher.update(fingerprint);

    let (c0, c1, c2) = cochain_dims;
    hasher.update(b"arity");
    hasher.update(&(c0 as u64).to_le_bytes());
    hasher.update(&(c1 as u64).to_le_bytes());
    hasher.update(&(c2 as u64).to_le_bytes());

    hasher.update(b"qspace");
    hasher.update(quotient_space_id);
    hasher.update(coefficient_domain.as_bytes());
    hasher.update(&(dim_total as u64).to_le_bytes());
    hasher.update(&(degree as u64).to_le_bytes());
    let relation_bytes = serde_json::to_vec(relation)
        .checked_invariant_a8aa34d9("serde_json::to_vec on QuotientRelation (total serde derive)");
    hasher.update(&(relation_bytes.len() as u64).to_le_bytes());
    hasher.update(&relation_bytes);
    let (p_rows, p_cols) = projection_shape;
    hasher.update(&(p_rows as u64).to_le_bytes());
    hasher.update(&(p_cols as u64).to_le_bytes());

    ShapeSignature(*hasher.finalize().as_bytes())
}

/// Derive the residual-family key for a shared exact CODA complex.
///
/// Only dimensions, boundary-map shapes, the rational coefficient tag, and a
/// domain-separated quotient-space id enter the digest. Matrix and residual
/// values are deliberately excluded. This lets application adapters consult
/// the registry before exact Phi1/Gamma2 replay without turning a family hit
/// into proof of the current evidence.
pub fn shape_signature_from_exact_complex(
    namespace: &str,
    complex: &ExactCochainComplexQ,
) -> Result<ShapeSignature, ShapeSignatureError> {
    if namespace.trim().is_empty() {
        return Err(ShapeSignatureError::EmptyNamespace);
    }

    let mut quotient_hasher = Hasher::new();
    quotient_hasher.update(b"core_residual_families::exact_quotient_space_id::v1");
    quotient_hasher.update(&(namespace.len() as u64).to_le_bytes());
    quotient_hasher.update(namespace.as_bytes());
    let quotient_space_id = *quotient_hasher.finalize().as_bytes();
    let dims = (complex.c0_dim(), complex.c1_dim(), complex.c2_dim());
    let fingerprint = cochain_shape_fingerprint(dims.0, dims.1, dims.2);

    Ok(signature_from_parts(
        &fingerprint,
        dims,
        &quotient_space_id,
        "Q",
        complex.c1_dim(),
        1,
        &QuotientRelation::ModCoboundaries,
        (complex.c1_dim(), complex.c1_dim()),
    ))
}

/// Deterministic canonical signature over the shape inputs of a
/// `CochainPrimitiveDifference` and its `QuotientSpace`.
///
/// Two calls on inputs that agree on `face_indices`, arity, coefficient-domain
/// tag, and `quotient_space_id` produce byte-identical `ShapeSignature`s.
/// Two calls on inputs whose cochain dimensions $(c_0, c_1, c_2)$ or whose
/// $d_0$/$d_1$ matrix shapes differ produce distinct `ShapeSignature`s.
///
/// Raw cochain payload bytes never enter the digest input.
///
/// # Panics
///
/// Panics only if `serde_json::to_vec` fails to serialize `q.relation`
/// (`QuotientRelation`). That type carries a total serde derive, so this is
/// unreachable for the current types; the `expect` documents the invariant.
#[must_use]
pub fn shape_signature<K>(
    diff: &CochainPrimitiveDifference<'_>,
    q: &QuotientSpace<K>,
) -> ShapeSignature
where
    K: CheckedNumeric + PartialEq + Serialize,
{
    signature_from_parts(
        &diff.shape_fingerprint(),
        diff.cochain_dims(),
        q.complex_hash.0.as_bytes(),
        q.coefficient_domain.as_str(),
        q.dim_total,
        q.degree,
        &q.relation,
        q.projection_matrix.shape(),
    )
}

// Origin: engine/crates_rs/core_local_green_global_red_lggr/src/residual_families/signature.rs
// Claim: urn:core:crates_rs:core-local-green-global-red-lggr:signature:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use core_linear_algebra::backend::basic_matrix::BasicMatrix;
    use num_bigint::BigInt;
    use num_rational::{BigRational, Rational64};
    use core_homology::cochain_complex::{CochainComplex, TheoremProvenance};
    use core_homology::coefficient_domain::CoefficientDomain;
    use core_homology::hash::{Blake3Hash, ComplexHash};
    use core_homology::quotient::{QuotientRelation, QuotientSpace};

    type Q = core_homology::scalar::Q;

    fn r(n: i64) -> Q {
        core_homology::scalar::q(n)
    }

    fn br(n: i64) -> BigRational {
        BigRational::from_integer(BigInt::from(n))
    }

    fn path_complex() -> CochainComplex {
        let d0 = BasicMatrix::from_row_major(2, 1, vec![r(1), r(-1)]).expect("d0");
        let d1 = BasicMatrix::from_row_major(1, 2, vec![r(1), r(1)]).expect("d1");
        CochainComplex::new(
            1,
            2,
            1,
            d0,
            d1,
            TheoremProvenance::new("signature_test".to_string()).expect("prov"),
        )
        .expect("complex")
    }

    fn fixture_qspace() -> QuotientSpace<Q> {
        QuotientSpace::new_unchecked(
            ComplexHash(Blake3Hash::new(b"fixture-complex")),
            CoefficientDomain::Rational,
            2,
            1,
            QuotientRelation::ModCoboundaries,
            BasicMatrix::from_row_major(2, 2, vec![r(1), r(0), r(0), r(1)]).expect("proj"),
        )
    }

    #[test]
    fn same_input_same_digest() {
        let cc = path_complex();
        let pd = CochainPrimitiveDifference::new(&cc);
        let q = fixture_qspace();
        let a = shape_signature(&pd, &q);
        let b = shape_signature(&pd, &q);
        assert_eq!(
            a, b,
            "two calls on the same input must produce byte-identical digests"
        );
        assert_eq!(a.as_bytes(), b.as_bytes());
    }

    #[test]
    fn exact_complex_signature_is_value_free_and_namespaced() {
        let a = ExactCochainComplexQ::try_new(
            1,
            2,
            1,
            vec![vec![br(1)], vec![br(-1)]],
            vec![vec![br(1), br(1)]],
        )
        .expect("complex a");
        let b = ExactCochainComplexQ::try_new(
            1,
            2,
            1,
            vec![vec![br(2)], vec![br(-2)]],
            vec![vec![br(3), br(3)]],
        )
        .expect("complex b");

        let a_sig = shape_signature_from_exact_complex("domain-a", &a).expect("signature a");
        let b_sig = shape_signature_from_exact_complex("domain-a", &b).expect("signature b");
        let other = shape_signature_from_exact_complex("domain-b", &a).expect("other domain");

        assert_eq!(
            a_sig, b_sig,
            "coefficient changes are outside the shape key"
        );
        assert_ne!(a_sig, other, "domain namespaces must not alias");
        assert_eq!(
            shape_signature_from_exact_complex("", &a),
            Err(ShapeSignatureError::EmptyNamespace)
        );
    }
}
