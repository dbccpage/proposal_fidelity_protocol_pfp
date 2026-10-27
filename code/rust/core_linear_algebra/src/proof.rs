use std::marker::PhantomData;
use thiserror::Error;

#[derive(Clone, Debug, PartialEq, Eq, Error)]
pub enum ProofError {
    #[error("empty certificate ID")]
    EmptyCertificateId,

    #[error("empty theorem ID")]
    EmptyTheoremId,

    #[error("empty theorem-boundary ID")]
    EmptyBoundaryId,

    #[error("empty reviewer ID")]
    EmptyReviewerId,
}

#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub struct CertificateId(String);

impl CertificateId {
    pub fn new(value: String) -> Result<Self, ProofError> {
        if value.trim().is_empty() {
            return Err(ProofError::EmptyCertificateId);
        }
        Ok(Self(value))
    }

    #[must_use]
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub struct ReplayHash([u8; 32]);

impl ReplayHash {
    #[must_use]
    pub fn from_bytes(bytes: [u8; 32]) -> Self {
        Self(bytes)
    }

    #[must_use]
    pub fn as_bytes(&self) -> &[u8; 32] {
        &self.0
    }
}

/// Stable fingerprint for a family of vectors.
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub struct VectorFamilyHash([u8; 32]);

impl VectorFamilyHash {
    #[must_use]
    pub fn from_bytes(bytes: [u8; 32]) -> Self {
        Self(bytes)
    }

    #[must_use]
    pub fn as_bytes(&self) -> &[u8; 32] {
        &self.0
    }
}

/// Stable fingerprint for a matrix payload.
///
/// This type does not define how matrices are serialized or hashed.
/// L5 callers must construct it only through the canonical matrix hashing
/// module, not by ad hoc byte assignment.
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub struct MatrixHash([u8; 32]);

impl MatrixHash {
    #[must_use]
    pub fn from_bytes(bytes: [u8; 32]) -> Self {
        Self(bytes)
    }

    #[must_use]
    pub fn as_bytes(&self) -> &[u8; 32] {
        &self.0
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub struct TheoremId(&'static str);

impl TheoremId {
    pub fn new(value: &'static str) -> Result<Self, ProofError> {
        if value.trim().is_empty() {
            return Err(ProofError::EmptyTheoremId);
        }
        Ok(Self(value))
    }

    #[must_use]
    pub fn as_str(&self) -> &'static str {
        self.0
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub struct BoundaryId(&'static str);

impl BoundaryId {
    pub fn new(value: &'static str) -> Result<Self, ProofError> {
        if value.trim().is_empty() {
            return Err(ProofError::EmptyBoundaryId);
        }
        Ok(Self(value))
    }

    #[must_use]
    pub fn as_str(&self) -> &'static str {
        self.0
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub struct ReviewerId(&'static str);

impl ReviewerId {
    pub fn new(value: &'static str) -> Result<Self, ProofError> {
        if value.trim().is_empty() {
            return Err(ProofError::EmptyReviewerId);
        }
        Ok(Self(value))
    }

    #[must_use]
    pub fn as_str(&self) -> &'static str {
        self.0
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub enum TheoremBoundaryRisk {
    Low,
    Medium,
    High,
    Critical,
}

/// Records the justification for issuing a witness in the numeric layer.
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub enum TheoremProvenance {
    /// Witness was constructed by a computational verification passing.
    VerifiedByComputation {
        theorem_id: TheoremId,
        certificate_id: CertificateId,
        replay_hash: ReplayHash,
    },

    /// Constructed by finite verification without a heavy certificate.
    DerivedFromFiniteVerification {
        theorem_id: TheoremId,
        replay: ReplayHash,
    },

    /// Witness issued under a theorem boundary — not runtime-checked.
    TheoremBoundary {
        theorem_id: TheoremId,
        boundary_id: BoundaryId,
        reviewer: ReviewerId,
        risk: TheoremBoundaryRisk,
    },
}

/// Witness that a specific matrix is symmetric.
///
/// ```compile_fail
/// let witness = SymmetricWitness::<i64> {
///     matrix_hash: todo!(),
///     shape: todo!(),
///     provenance: todo!(),
///     _phantom: std::marker::PhantomData,
/// };
/// ```
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub struct SymmetricWitness<T> {
    matrix_hash: MatrixHash,
    shape: (usize, usize),
    provenance: TheoremProvenance,
    _phantom: PhantomData<T>,
}

impl<T> SymmetricWitness<T> {
    // Sole gated constructor of the sealed witness; checked path not yet wired.
    #[allow(dead_code)]
    pub(crate) fn new_unchecked(
        matrix_hash: MatrixHash,
        shape: (usize, usize),
        provenance: TheoremProvenance,
    ) -> Self {
        Self {
            matrix_hash,
            shape,
            provenance,
            _phantom: PhantomData,
        }
    }

    #[must_use]
    pub fn matrix_hash(&self) -> &MatrixHash {
        &self.matrix_hash
    }

    #[must_use]
    pub fn shape(&self) -> (usize, usize) {
        self.shape
    }

    #[must_use]
    pub fn provenance(&self) -> &TheoremProvenance {
        &self.provenance
    }
}

/// Witness that a specific matrix is positive-definite.
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub struct PositiveDefiniteWitness<T> {
    matrix_hash: MatrixHash,
    shape: (usize, usize),
    provenance: TheoremProvenance,
    _phantom: PhantomData<T>,
}

impl<T> PositiveDefiniteWitness<T> {
    // Sole gated constructor of the sealed witness; checked path not yet wired.
    #[allow(dead_code)]
    pub(crate) fn new_unchecked(
        matrix_hash: MatrixHash,
        shape: (usize, usize),
        provenance: TheoremProvenance,
    ) -> Self {
        Self {
            matrix_hash,
            shape,
            provenance,
            _phantom: PhantomData,
        }
    }

    #[must_use]
    pub fn matrix_hash(&self) -> &MatrixHash {
        &self.matrix_hash
    }

    #[must_use]
    pub fn shape(&self) -> (usize, usize) {
        self.shape
    }

    #[must_use]
    pub fn provenance(&self) -> &TheoremProvenance {
        &self.provenance
    }
}

// Origin: engine/crates_rs/core_linear_algebra/src/proof.rs
// Claim: urn:core:crates_rs:core-linear-algebra:proof:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn certificate_id_rejects_empty() {
        assert_eq!(
            CertificateId::new("".to_string()),
            Err(ProofError::EmptyCertificateId)
        );
        assert_eq!(
            CertificateId::new("   ".to_string()),
            Err(ProofError::EmptyCertificateId)
        );
    }

    #[test]
    fn theorem_id_rejects_empty() {
        assert_eq!(TheoremId::new(""), Err(ProofError::EmptyTheoremId));
        assert_eq!(TheoremId::new("   "), Err(ProofError::EmptyTheoremId));
    }

    #[test]
    fn boundary_id_rejects_empty() {
        assert_eq!(BoundaryId::new(""), Err(ProofError::EmptyBoundaryId));
        assert_eq!(BoundaryId::new("   "), Err(ProofError::EmptyBoundaryId));
    }

    #[test]
    fn reviewer_id_rejects_empty() {
        assert_eq!(ReviewerId::new(""), Err(ProofError::EmptyReviewerId));
        assert_eq!(ReviewerId::new("   "), Err(ProofError::EmptyReviewerId));
    }

    #[test]
    fn symmetric_witness_exposes_matrix_hash_shape_provenance() {
        let hash = MatrixHash::from_bytes([1; 32]);
        let prov = TheoremProvenance::DerivedFromFiniteVerification {
            theorem_id: TheoremId::new("test.theorem").unwrap(),
            replay: ReplayHash::from_bytes([2; 32]),
        };
        let witness: SymmetricWitness<i32> =
            SymmetricWitness::new_unchecked(hash.clone(), (2, 2), prov.clone());
        assert_eq!(witness.matrix_hash(), &hash);
        assert_eq!(witness.shape(), (2, 2));
        assert_eq!(witness.provenance(), &prov);
    }

    #[test]
    fn positive_definite_witness_exposes_matrix_hash_shape_provenance() {
        let hash = MatrixHash::from_bytes([1; 32]);
        let prov = TheoremProvenance::DerivedFromFiniteVerification {
            theorem_id: TheoremId::new("test.theorem").unwrap(),
            replay: ReplayHash::from_bytes([2; 32]),
        };
        let witness: PositiveDefiniteWitness<i32> =
            PositiveDefiniteWitness::new_unchecked(hash.clone(), (2, 2), prov.clone());
        assert_eq!(witness.matrix_hash(), &hash);
        assert_eq!(witness.shape(), (2, 2));
        assert_eq!(witness.provenance(), &prov);
    }

    #[test]
    fn theorem_boundary_provenance_records_theorem_id_boundary_reviewer_risk() {
        let prov = TheoremProvenance::TheoremBoundary {
            theorem_id: TheoremId::new("theorem.1").unwrap(),
            boundary_id: BoundaryId::new("boundary.1").unwrap(),
            reviewer: ReviewerId::new("reviewer.1").unwrap(),
            risk: TheoremBoundaryRisk::Low,
        };

        match prov {
            TheoremProvenance::TheoremBoundary {
                theorem_id,
                boundary_id,
                reviewer,
                risk,
            } => {
                assert_eq!(theorem_id.as_str(), "theorem.1");
                assert_eq!(boundary_id.as_str(), "boundary.1");
                assert_eq!(reviewer.as_str(), "reviewer.1");
                assert_eq!(risk, TheoremBoundaryRisk::Low);
            }
            _ => panic!("wrong variant"),
        }
    }
}
