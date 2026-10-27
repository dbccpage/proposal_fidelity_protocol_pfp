// AuthorityEffect: None.

//! Finite cochain packets on declared oriented 2-complexes.
//!
//! A packet is a finite oriented cell complex ([`core_holonomy::CellComplex`])
//! with strictly positive edge weights. Two coboundaries are read off it:
//! the primitive difference `d0 : C^0 -> C^1`, `(d0 f)(u,v) = f(v) - f(u)`,
//! and the face coboundary `d1 : C^1 -> C^2`, from each face's oriented
//! boundary steps. `d1 d0 = 0` is replayed at construction, not assumed.
//!
//! Nothing is optimised here. The weighted-`L1` quotient mass
//! `Phi1([x]) = min_a ||x - d0 a||_{1,w}` is proposed by
//! `core_solvers::solver_lp_exact_simplex` and accepted only after
//! `core_functional::phi1` replays its primal and dual witnesses. The closure
//! defect `Gamma2([x]) = ||d1 x||_1` and the exact trichotomy come from
//! `core_functional`. Ranks and matrix actions use canonical exact linear algebra.
//!
//! The raw edge mass `I1(x) = sum_e w_e |x_e|` depends on the representative;
//! `Phi1` does not. They are different quantities and are kept apart.

use crate::solver_cohomology_quotient_phi1::certified_phi1;
use linear_algebra::backend::basic_matrix::{BasicMatrix, OperationLimits as MatrixLimits};
use linear_algebra::exact_field::{elimination, matrix};
use num_traits::{One, Signed};
use core_functional::gamma2::{
    DegreeOneResidualQ, ExactCochainComplexQ, ExactGamma2Result, Gamma2Functional,
};
use core_functional::phi1::VerifiedExactPhi1;
use core_holonomy::CellComplex;
use core_kernel::resource_limits::OperationLimits;
use core_policy::trichotomy::{classify_exact, CertifiedExactTrichotomy, TrichotomyOutcome};

use core_number_theory::rational::Rational;

/// Refusals raised while declaring or evaluating a packet.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum CochainPacketError {
    #[error(transparent)]
    LinearAlgebra(#[from] linear_algebra::exact_field::ExactFieldError),
    #[error(transparent)]
    Storage(#[from] linear_algebra::backend::basic_matrix::MatrixError),
    #[error("cochain packet dimension {requested} exceeds {limit}")]
    ResourceBudget { requested: usize, limit: usize },
    #[error("{map} has incompatible declared shape {expected:?}")]
    MapShape {
        map: &'static str,
        expected: (usize, usize),
    },
    #[error("edge {edge} is a self-loop at {vertex}; primitive difference is irreflexive")]
    SelfLoop { edge: usize, vertex: String },
    #[error("{weights} weights declared for {edges} edges")]
    WeightCountMismatch { edges: usize, weights: usize },
    #[error("weight of edge {edge} is not strictly positive")]
    NonPositiveWeight { edge: usize },
    #[error("cochain has {actual} coordinates, expected {expected}")]
    CochainLength { expected: usize, actual: usize },
    #[error("d1 d0 is nonzero at face {face}, vertex {vertex}")]
    Nilpotence { face: usize, vertex: usize },
    #[error("complex construction refused: {0}")]
    Complex(String),
    #[error("exact L1 solver refused: {0}")]
    Solver(String),
    #[error("Phi1 certificate replay refused: {0}")]
    Certificate(String),
    #[error("Gamma2 evaluation refused: {0}")]
    ClosureDefect(String),
    #[error("trichotomy refused: {0}")]
    Trichotomy(String),
}

/// Exact ranks and cohomology dimensions of `C^0 -> C^1 -> C^2`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct CochainDimensions {
    pub c0: usize,
    pub c1: usize,
    pub c2: usize,
    /// `dim B^1 = rank d0`.
    pub b1: usize,
    /// `dim Z^1 = c1 - rank d1`.
    pub z1: usize,
    /// `dim H^1 = dim Z^1 - dim B^1`.
    pub h1: usize,
}

/// A declared finite cochain packet.
#[derive(Debug, Clone)]
pub struct FiniteCochainPacket {
    complex: CellComplex,
    weights: Vec<Rational>,
    d0: Vec<Vec<Rational>>,
    d1: Vec<Vec<Rational>>,
    d0_matrix: BasicMatrix<Rational>,
    d1_matrix: BasicMatrix<Rational>,
    ranks: [usize; 2],
}

const MATRIX_LIMITS: MatrixLimits = MatrixLimits {
    max_elements: 1 << 20,
    max_scalar_ops: 1 << 26,
};
/// Every cochain axis is bounded, including zero-row maps which carry preimage vectors.
pub const MAX_PACKET_DIMENSION: usize = 4096;

impl FiniteCochainPacket {
    fn validate_packet_inputs(
        complex: &CellComplex,
        weights: &[Rational],
    ) -> Result<(), CochainPacketError> {
        let requested = complex
            .vertices
            .len()
            .max(complex.edges.len())
            .max(complex.faces.len());
        if requested > MAX_PACKET_DIMENSION {
            return Err(CochainPacketError::ResourceBudget {
                requested,
                limit: MAX_PACKET_DIMENSION,
            });
        }
        for edge in &complex.edges {
            if edge.source == edge.target {
                return Err(CochainPacketError::SelfLoop {
                    edge: edge.index,
                    vertex: edge.source.clone(),
                });
            }
        }
        if weights.len() != complex.edges.len() {
            return Err(CochainPacketError::WeightCountMismatch {
                edges: complex.edges.len(),
                weights: weights.len(),
            });
        }
        if let Some(edge) = weights.iter().position(|w| !w.is_positive()) {
            return Err(CochainPacketError::NonPositiveWeight { edge });
        }
        Ok(())
    }

    /// Declare a packet. Weights are indexed by the complex's edge indices.
    pub fn new(complex: CellComplex, weights: Vec<Rational>) -> Result<Self, CochainPacketError> {
        Self::validate_packet_inputs(&complex, &weights)?;
        let (d0, d1) = complex
            .cochain_matrices()
            .map_err(|e| CochainPacketError::Complex(e.to_string()))?;
        let d0_matrix = BasicMatrix::from_row_major(
            complex.edges.len(),
            complex.vertices.len(),
            d0.iter().flatten().cloned().collect(),
        )?;
        let d1_matrix = BasicMatrix::from_row_major(
            complex.faces.len(),
            complex.edges.len(),
            d1.iter().flatten().cloned().collect(),
        )?;
        let ranks = [
            elimination::rank_with_limits(&d0_matrix, MATRIX_LIMITS)?,
            elimination::rank_with_limits(&d1_matrix, MATRIX_LIMITS)?,
        ];
        Ok(Self {
            complex,
            weights,
            d0,
            d1,
            d0_matrix,
            d1_matrix,
            ranks,
        })
    }

    /// Declare a packet with every edge weight equal to one.
    pub fn with_unit_weights(complex: CellComplex) -> Result<Self, CochainPacketError> {
        if complex.edges.len() > MAX_PACKET_DIMENSION {
            return Err(CochainPacketError::ResourceBudget {
                requested: complex.edges.len(),
                limit: MAX_PACKET_DIMENSION,
            });
        }
        let weights = vec![Rational::one(); complex.edges.len()];
        Self::new(complex, weights)
    }

    /// Build a complex from named vertices, directed edges and closed faces.
    ///
    /// Faces are vertex cycles; each consecutive pair must be a declared edge
    /// in one of its two orientations.
    pub fn build_complex(
        vertices: &[&str],
        edges: &[(&str, &str)],
        faces: &[&[&str]],
    ) -> Result<CellComplex, CochainPacketError> {
        let requested = vertices.len().max(edges.len()).max(faces.len());
        if requested > MAX_PACKET_DIMENSION {
            return Err(CochainPacketError::ResourceBudget {
                requested,
                limit: MAX_PACKET_DIMENSION,
            });
        }
        let mut complex = CellComplex::new(OperationLimits::holonomy());
        for v in vertices {
            complex
                .add_vertex(*v)
                .map_err(|e| CochainPacketError::Complex(e.to_string()))?;
        }
        for (u, v) in edges {
            complex
                .add_edge(u, v)
                .map_err(|e| CochainPacketError::Complex(e.to_string()))?;
        }
        for (index, cycle) in faces.iter().enumerate() {
            let cycle: Vec<String> = cycle.iter().map(|s| s.to_string()).collect();
            complex
                .add_face(format!("f{index}"), &cycle)
                .map_err(|e| CochainPacketError::Complex(e.to_string()))?;
        }
        Ok(complex)
    }

    pub fn complex(&self) -> &CellComplex {
        &self.complex
    }

    pub fn weights(&self) -> &[Rational] {
        &self.weights
    }

    /// `d0` as an `edges x vertices` matrix.
    pub fn d0(&self) -> &[Vec<Rational>] {
        &self.d0
    }

    /// `d1` as a `faces x edges` matrix.
    pub fn d1(&self) -> &[Vec<Rational>] {
        &self.d1
    }

    pub fn vertex_count(&self) -> usize {
        self.complex.vertices.len()
    }

    pub fn edge_count(&self) -> usize {
        self.complex.edges.len()
    }

    pub fn face_count(&self) -> usize {
        self.complex.faces.len()
    }

    fn check_len(&self, x: &[Rational], expected: usize) -> Result<(), CochainPacketError> {
        if x.len() != expected {
            return Err(CochainPacketError::CochainLength {
                expected,
                actual: x.len(),
            });
        }
        Ok(())
    }

    /// `(d0 f)(u,v) = f(v) - f(u)`.
    pub fn primitive_difference(
        &self,
        f: &[Rational],
    ) -> Result<Vec<Rational>, CochainPacketError> {
        self.check_len(f, self.vertex_count())?;
        Ok(matrix::multiply_vector_with_limits(
            &self.d0_matrix,
            f,
            MATRIX_LIMITS,
        )?)
    }

    /// `d1 x`.
    pub fn face_coboundary(&self, x: &[Rational]) -> Result<Vec<Rational>, CochainPacketError> {
        self.check_len(x, self.edge_count())?;
        Ok(matrix::multiply_vector_with_limits(
            &self.d1_matrix,
            x,
            MATRIX_LIMITS,
        )?)
    }

    /// Raw edge mass `I1(x) = sum_e w_e |x_e|`. Representative-dependent.
    pub fn raw_mass(&self, x: &[Rational]) -> Result<Rational, CochainPacketError> {
        self.check_len(x, self.edge_count())?;
        core_functional::Phi1Functional::weighted_l1_rational(&self.weights, x)
            .ok_or_else(|| CochainPacketError::Certificate("invalid raw mass inputs".into()))
    }

    /// The exact quotient mass `Phi1([x])`, as a replayed primal-dual certificate.
    ///
    /// The dual witness `z` satisfies `d0^T z = 0` and `|z_e| <= w_e`, and pairs
    /// with `x` to the same value as the primal residual's weighted norm.
    pub fn quotient_mass(&self, x: &[Rational]) -> Result<VerifiedExactPhi1, CochainPacketError> {
        self.check_len(x, self.edge_count())?;
        certified_phi1(self.vertex_count(), &self.d0, x, &self.weights, 16_384)
            .map_err(|e| CochainPacketError::Solver(e.to_string()))
    }

    /// The closure defect `Gamma2([x]) = ||d1 x||_1`, evaluated by `core_functional`.
    pub fn closure_defect(&self, x: &[Rational]) -> Result<ExactGamma2Result, CochainPacketError> {
        self.check_len(x, self.edge_count())?;
        certified_closure_defect(self.vertex_count(), &self.d0, &self.d1, x)
    }

    /// Exact trichotomy of `[x]`: `ExactRepair`, `ClosedResidual` or
    /// `ActiveClosureFailure`, from a replayed `Phi1` and the `Gamma2` of the
    /// same primal residual.
    pub fn classify(&self, x: &[Rational]) -> Result<CertifiedExactTrichotomy, CochainPacketError> {
        self.check_len(x, self.edge_count())?;
        certified_trichotomy(self.vertex_count(), &self.d0, &self.d1, &self.weights, x)
    }

    /// Exact ranks and cohomology dimensions.
    pub fn dimensions(&self) -> CochainDimensions {
        let (c0, c1, c2) = (self.vertex_count(), self.edge_count(), self.face_count());
        let [rank_d0, rank_d1] = self.ranks;
        let z1 = c1 - rank_d1;
        CochainDimensions {
            c0,
            c1,
            c2,
            b1: rank_d0,
            z1,
            h1: z1 - rank_d0,
        }
    }
}

/// `Gamma2([x]) = ||d1 x||_1` for any exact complex `Q^c0 -> Q^m -> Q^n`;
/// `core_functional` replays `d1 d0 = 0` before evaluating it.
pub fn certified_closure_defect(
    c0: usize,
    d0: &[Vec<Rational>],
    d1: &[Vec<Rational>],
    x: &[Rational],
) -> Result<ExactGamma2Result, CochainPacketError> {
    certified_closure_defect_with_limits(c0, d0, d1, x, MAX_PACKET_DIMENSION, MATRIX_LIMITS)
}

fn enforce_closure_defect_budgets(
    c0: usize,
    c1: usize,
    c2: usize,
    d0_len: usize,
    max_dimension: usize,
    limits: MatrixLimits,
) -> Result<(), CochainPacketError> {
    use linear_algebra::backend::basic_matrix::MatrixError;
    let requested = c0.max(c1).max(c2).max(d0_len);
    if requested > max_dimension {
        return Err(CochainPacketError::ResourceBudget {
            requested,
            limit: max_dimension,
        });
    }
    let entries = c0
        .checked_mul(c1)
        .and_then(|entries| {
            c1.checked_mul(c2)
                .and_then(|other| entries.checked_add(other))
        })
        .and_then(|entries| entries.checked_add(c1))
        .and_then(|entries| entries.checked_add(c2))
        .and_then(|entries| entries.checked_mul(4))
        .ok_or(MatrixError::OperationCountOverflow)?;
    if entries > limits.max_elements {
        return Err(MatrixError::AllocationLimitExceeded {
            requested: entries,
            limit: limits.max_elements,
        }
        .into());
    }
    let work = c0
        .checked_mul(c1)
        .and_then(|work| work.checked_mul(c2))
        .and_then(|work| work.checked_mul(8))
        .and_then(|work| {
            c1.checked_mul(c2)
                .and_then(|other| other.checked_mul(8))
                .and_then(|other| work.checked_add(other))
        })
        .and_then(|work| work.checked_add(entries))
        .ok_or(MatrixError::OperationCountOverflow)?;
    if work > limits.max_scalar_ops {
        return Err(MatrixError::OperationLimitExceeded {
            requested: work,
            limit: limits.max_scalar_ops,
        }
        .into());
    }
    Ok(())
}

/// [`certified_closure_defect`] with explicit axis, aggregate storage and work
/// limits. Admission precedes every matrix or residual clone, including empty axes.
pub fn certified_closure_defect_with_limits(
    c0: usize,
    d0: &[Vec<Rational>],
    d1: &[Vec<Rational>],
    x: &[Rational],
    max_dimension: usize,
    limits: MatrixLimits,
) -> Result<ExactGamma2Result, CochainPacketError> {
    let (c1, c2) = (x.len(), d1.len());
    enforce_closure_defect_budgets(c0, c1, c2, d0.len(), max_dimension, limits)?;
    if d0.len() != c1 || d0.iter().any(|row| row.len() != c0) {
        return Err(CochainPacketError::MapShape {
            map: "d0",
            expected: (c1, c0),
        });
    }
    if d1.iter().any(|row| row.len() != c1) {
        return Err(CochainPacketError::MapShape {
            map: "d1",
            expected: (c2, c1),
        });
    }
    let complex = ExactCochainComplexQ::try_new(c0, x.len(), d1.len(), d0.to_vec(), d1.to_vec())
        .map_err(|e| CochainPacketError::ClosureDefect(e.to_string()))?;
    let residual = DegreeOneResidualQ::try_new(&complex, x.to_vec())
        .map_err(|e| CochainPacketError::ClosureDefect(e.to_string()))?;
    Gamma2Functional::try_compute_exact_quotient(&residual)
        .map_err(|e| CochainPacketError::ClosureDefect(e.to_string()))
}

/// The exact trichotomy of `[x]` from a replayed `Phi1` and the `Gamma2` of
/// the same primal residual, decided by `core_functional`.
pub fn certified_trichotomy(
    c0: usize,
    d0: &[Vec<Rational>],
    d1: &[Vec<Rational>],
    weights: &[Rational],
    x: &[Rational],
) -> Result<CertifiedExactTrichotomy, CochainPacketError> {
    let phi1 = certified_phi1(c0, d0, x, weights, 16_384)
        .map_err(|e| CochainPacketError::Solver(e.to_string()))?;
    let gamma2 = certified_closure_defect(c0, d0, d1, phi1.primal_residual())?;
    match classify_exact(&phi1, &gamma2) {
        TrichotomyOutcome::Classified(certified) => Ok(certified),
        TrichotomyOutcome::TriRefused(reason) => {
            Err(CochainPacketError::Trichotomy(format!("{reason:?}")))
        }
    }
}

// Origin: engine/crates_rs/core_solvers/src/data_cochain_packet.rs
// Claim: urn:core:crates_rs:core-solvers:data-cochain-packet:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod checked_packet_tests {
    use super::*;
    use num_traits::Zero;
    use core_number_theory::rational::ri;
    #[test]
    fn edge_free_closure_outputs_obey_explicit_storage_and_work_budgets() {
        use linear_algebra::backend::basic_matrix::MatrixError;
        let faces = vec![vec![], vec![]];
        let zero = MatrixLimits {
            max_elements: 0,
            max_scalar_ops: 0,
        };
        assert!(matches!(
            certified_closure_defect_with_limits(3, &[], &faces, &[], 3, zero),
            Err(CochainPacketError::Storage(
                MatrixError::AllocationLimitExceeded {
                    requested: 8,
                    limit: 0
                }
            ))
        ));
        let short_work = MatrixLimits {
            max_elements: 8,
            max_scalar_ops: 7,
        };
        assert!(matches!(
            certified_closure_defect_with_limits(3, &[], &faces, &[], 3, short_work),
            Err(CochainPacketError::Storage(
                MatrixError::OperationLimitExceeded {
                    requested: 8,
                    limit: 7
                }
            ))
        ));
        let admitted = certified_closure_defect_with_limits(
            3,
            &[],
            &faces,
            &[],
            3,
            MatrixLimits {
                max_elements: 8,
                max_scalar_ops: 8,
            },
        )
        .unwrap();
        assert_eq!(admitted.complex().c0_dim(), 3);
        assert_eq!(admitted.complex().c1_dim(), 0);
        assert_eq!(admitted.complex().c2_dim(), 2);
        assert_eq!(admitted.coboundary(), &[ri(0), ri(0)]);
        assert_eq!(admitted.value(), &ri(0));
        assert!(certified_closure_defect_with_limits(0, &[], &[], &[], 3, zero).is_ok());
        assert!(certified_closure_defect_with_limits(3, &[], &[], &[], 3, zero).is_ok());
    }
    #[test]
    fn closure_admission_precedes_clones_and_preserves_empty_carriers() {
        assert!(matches!(
            certified_closure_defect(usize::MAX, &[], &[], &[]),
            Err(CochainPacketError::ResourceBudget { .. })
        ));
        let d0 = vec![vec![ri(0)]];
        let d1 = vec![vec![ri(0)]];
        let tiny = MatrixLimits {
            max_elements: 3,
            max_scalar_ops: 1024,
        };
        assert!(matches!(
            certified_closure_defect_with_limits(1, &d0, &d1, &[ri(2)], 2, tiny),
            Err(CochainPacketError::Storage(
                linear_algebra::backend::basic_matrix::MatrixError::AllocationLimitExceeded { .. }
            ))
        ));
        let work = MatrixLimits {
            max_elements: 1024,
            max_scalar_ops: 1,
        };
        assert!(matches!(
            certified_closure_defect_with_limits(1, &d0, &d1, &[ri(2)], 2, work),
            Err(CochainPacketError::Storage(
                linear_algebra::backend::basic_matrix::MatrixError::OperationLimitExceeded { .. }
            ))
        ));
        assert!(certified_closure_defect(0, &[], &[], &[]).is_ok());
        assert!(certified_closure_defect(3, &[], &[vec![], vec![]], &[]).is_ok());
        assert!(matches!(
            certified_closure_defect(1, &[vec![]], &[], &[ri(0)]),
            Err(CochainPacketError::MapShape { map: "d0", .. })
        ));
    }
    #[test]
    fn empty_and_edge_free_complexes_keep_their_mathematical_shapes() {
        let empty =
            FiniteCochainPacket::with_unit_weights(CellComplex::new(OperationLimits::holonomy()))
                .unwrap();
        assert_eq!(
            empty.dimensions(),
            CochainDimensions {
                c0: 0,
                c1: 0,
                c2: 0,
                b1: 0,
                z1: 0,
                h1: 0
            }
        );
        assert!(empty.primitive_difference(&[]).unwrap().is_empty());
        assert!(empty.face_coboundary(&[]).unwrap().is_empty());
        assert_eq!(empty.quotient_mass(&[]).unwrap().value(), &Rational::zero());
        let complex = FiniteCochainPacket::build_complex(&["v"], &[], &[]).unwrap();
        let point = FiniteCochainPacket::with_unit_weights(complex).unwrap();
        assert_eq!(point.dimensions().c0, 1);
        assert_eq!(point.dimensions().h1, 0);
        assert!(point.primitive_difference(&[ri(7)]).unwrap().is_empty());
        let mut oversized = CellComplex::new(OperationLimits::holonomy());
        for vertex in 0..=MAX_PACKET_DIMENSION {
            oversized.add_vertex(format!("v{vertex}")).unwrap();
        }
        assert!(matches!(
            FiniteCochainPacket::with_unit_weights(oversized),
            Err(CochainPacketError::ResourceBudget { .. })
        ));
    }
    #[test]
    fn public_complex_tampering_is_a_typed_packet_refusal() {
        let c = FiniteCochainPacket::build_complex(&["a", "b"], &[("a", "b")], &[]).unwrap();
        let mut bad = c.clone();
        bad.vertex_map.remove("a");
        assert!(matches!(
            FiniteCochainPacket::with_unit_weights(bad),
            Err(CochainPacketError::Complex(_))
        ));
        let mut bad = c;
        bad.edges[0].index = usize::MAX;
        assert!(matches!(
            FiniteCochainPacket::with_unit_weights(bad),
            Err(CochainPacketError::Complex(_))
        ));
    }
}
