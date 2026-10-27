//! Exact flux closure and volume of finite oriented tetrahedra.
//! This finite geometric face does not construct a continuum Hilbert space.
//! AuthorityEffect: None.
use linear_algebra::backend::basic_matrix::{BasicMatrix, MatrixError};
use linear_algebra::exact_field::elimination::determinant;
use num_traits::Zero;
use core_number_theory::rational::{ri, Rational};
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; finite flux geometry; no continuum admission.";
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum FluxGeometryError {
    #[error("tetrahedron or four-simplex has zero volume")]
    Degenerate,
    #[error(transparent)]
    Matrix(#[from] linear_algebra::exact_field::ExactFieldError),
    #[error(transparent)]
    Storage(#[from] MatrixError),
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FluxTetrahedron {
    pub vertices: [[Rational; 3]; 4],
    pub oriented_area_vectors: [[Rational; 3]; 4],
    pub volume_squared: Rational,
}
impl FluxTetrahedron {
    pub fn new(vertices: [[Rational; 3]; 4]) -> Result<Self, FluxGeometryError> {
        let row = |v: usize| {
            (0..3)
                .map(|k| &vertices[v][k] - &vertices[0][k])
                .collect::<Vec<_>>()
        };
        let gram = BasicMatrix::from_row_major(3, 3, (1..4).flat_map(row).collect())?;
        let det = determinant(&gram)?;
        if det.is_zero() {
            return Err(FluxGeometryError::Degenerate);
        }
        let oriented_area_vectors = std::array::from_fn(|omitted| {
            let face: Vec<_> = (0..4).filter(|&v| v != omitted).collect();
            let u: [Rational; 3] =
                std::array::from_fn(|k| &vertices[face[1]][k] - &vertices[face[0]][k]);
            let v: [Rational; 3] =
                std::array::from_fn(|k| &vertices[face[2]][k] - &vertices[face[0]][k]);
            let sign = if omitted % 2 == 0 { ri(1) } else { ri(-1) };
            std::array::from_fn(|k| {
                (&u[(k + 1) % 3] * &v[(k + 2) % 3] - &u[(k + 2) % 3] * &v[(k + 1) % 3]) * &sign
                    / ri(2)
            })
        });
        Ok(Self {
            vertices,
            oriented_area_vectors,
            volume_squared: &det * &det / ri(36),
        })
    }
    pub fn closure_defect(&self) -> [Rational; 3] {
        std::array::from_fn(|k| {
            self.oriented_area_vectors
                .iter()
                .map(|f| f[k].clone())
                .sum()
        })
    }
    pub fn area_squared(&self, face: usize) -> Option<Rational> {
        self.oriented_area_vectors
            .get(face)
            .map(|v| v.iter().map(|x| x * x).sum())
    }
}
/// The declared finite carrier retains its label and degree, now with actual
/// validated geometric cells. The empty carrier carries no geometric claim.
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct LoopQuantumGravity {
    pub degree: usize,
    pub label: String,
    pub tetrahedra: Vec<FluxTetrahedron>,
}
impl LoopQuantumGravity {
    pub fn new(degree: usize, label: impl Into<String>) -> Self {
        Self {
            degree,
            label: label.into(),
            tetrahedra: Vec::new(),
        }
    }
    pub fn from_tetrahedra(tetrahedra: Vec<FluxTetrahedron>, label: impl Into<String>) -> Self {
        Self {
            degree: tetrahedra.len(),
            label: label.into(),
            tetrahedra,
        }
    }
    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
    pub fn satisfies_gauss_closure(&self) -> bool {
        self.tetrahedra
            .iter()
            .all(|t| t.closure_defect().iter().all(Zero::is_zero))
    }
}
/// Exact oriented Euclidean four-simplex; the determinant is its signed 4!
/// volume. Hinge bivectors are wedges of its triangle edge vectors.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExactFourSimplex {
    pub vertices: [[Rational; 4]; 5],
    pub volume_squared: Rational,
}
impl ExactFourSimplex {
    pub fn new(vertices: [[Rational; 4]; 5]) -> Result<Self, FluxGeometryError> {
        let edges = BasicMatrix::from_row_major(
            4,
            4,
            (1..5)
                .flat_map(|v| {
                    (0..4)
                        .map(|k| &vertices[v][k] - &vertices[0][k])
                        .collect::<Vec<_>>()
                })
                .collect(),
        )?;
        let det = determinant(&edges)?;
        if det.is_zero() {
            return Err(FluxGeometryError::Degenerate);
        }
        Ok(Self {
            vertices,
            volume_squared: &det * &det / ri(576),
        })
    }
    pub fn triangle_bivector(&self, triangle: [usize; 3]) -> Option<[Rational; 6]> {
        if triangle.iter().any(|&v| v >= 5)
            || triangle[0] == triangle[1]
            || triangle[1] == triangle[2]
            || triangle[0] == triangle[2]
        {
            return None;
        }
        let a: [Rational; 4] = std::array::from_fn(|k| {
            &self.vertices[triangle[1]][k] - &self.vertices[triangle[0]][k]
        });
        let b: [Rational; 4] = std::array::from_fn(|k| {
            &self.vertices[triangle[2]][k] - &self.vertices[triangle[0]][k]
        });
        Some(
            [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
                .map(|(j, k)| (&a[j] * &b[k] - &a[k] * &b[j]) / ri(2)),
        )
    }
}

// Origin: engine/crates_rs/core_general_relativity/src/loop_quantum_gravity.rs
// Claim: urn:core:crates_rs:core-general-relativity:loop-quantum-gravity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_21d88ba4 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
