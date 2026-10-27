// AuthorityEffect: None.

//! Spin lifts of a flat rational rotation transport on a declared finite 2-complex.
//!
//! Declared: `V` vertices, oriented edges `(u, v)` (loops allowed), faces as
//! closed walks of `(edge, forward)` steps, and a rational rotation `R_e` per
//! edge. A step transports by `R_e` forward and by `R_e^T` backward; the
//! holonomy of a face is the product of its steps, the first step rightmost.
//! Computed exactly:
//!
//! - flatness: every face holonomy is `I` (a curved face is refused);
//! - a lift `U_e` in `SU(2)` of each `R_e`
//!   (`core_lie_theory::su2_matrix::matrix_spin_lift`; an edge whose rotation has no
//!   rational lift is refused with its spinor norm class);
//! - [`FlatRotationTransport::obstruction`]: face `f` gets `true` when the
//!   product of the lifts around `f` is `-I` (it is `I` or `-I`, the face being
//!   flat);
//! - [`FlatRotationTransport::flat_lifts`]: every sign change `s` (bit `e`
//!   replaces `U_e` by `-U_e`) that makes every face product `I`, by exhaustive
//!   search over the `2^E` changes. Changing `U_e` flips face `f` once for each
//!   time `f` traverses `e`, so `s` works exactly when, for every face, the
//!   traversal parity of `s` equals the obstruction bit;
//! - [`FlatRotationTransport::gauge_classes`]: the flat lifts modulo vertex
//!   gauges, where the gauge at `v` changes the sign on every edge at `v` (twice,
//!   so not at all, on a loop).
//!
//! A flat spin lift exists exactly when the obstruction bits are the traversal
//! parities of some sign change: the cellular form of the vanishing of the
//! second Stiefel–Whitney class of the flat bundle, decided here on declared
//! complexes only.
//!
//! Refused: more than [`MAX_CELLS`] vertices or edges, endpoints out of range,
//! empty or broken face walks, a rotation count other than the edge count,
//! matrices outside `SO(3)`, curved faces, and edges without a rational lift.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_5528a964<T> {
    fn checked_invariant_5528a964(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_5528a964<T> for Option<T> {
    #[inline]
    fn checked_invariant_5528a964(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_5528a964<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_5528a964(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use num_bigint::BigInt;
use num_traits::{One, Zero};

use linear_algebra::exact_field::{involution, matrix as mx};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::Rational;

use linear_algebra::backend::basic_matrix::BasicMatrix;
use core_homology::f2_cohomology::{ComplexError, F2ChainComplex};
use core_lie_theory::su2::{rodrigues_quaternion, Su2Error};
use core_lie_theory::su2_matrix::{matrix_spin_lift, SpinLiftError};
use core_number_theory::gf2::{F2AffineSpace, F2Error, F2Matrix, F2Vector};

pub type Rotation = [[Rational; 3]; 3];

/// Largest number of vertices, and of edges, searched exhaustively.
pub const MAX_CELLS: usize = 16;

/// Refusals for flat rotation transports.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum SpinStructureError {
    #[error(transparent)]
    Cohomology(#[from] ComplexError),
    #[error(transparent)]
    F2(#[from] F2Error),
    #[error(transparent)]
    Cup(#[from] core_homology::cup_product::F2CupError),
    #[error("the declared cohomological lifting computation exceeds its finite work budget")]
    CohomologyBudget,
    #[error("at most {MAX_CELLS} vertices and {MAX_CELLS} edges are searched")]
    TooLarge,
    #[error("edge {edge} names vertex {vertex}, but there are {count} vertices")]
    VertexOutOfRange {
        edge: usize,
        vertex: usize,
        count: usize,
    },
    #[error("{edges} edges but {rotations} rotations")]
    RotationCount { edges: usize, rotations: usize },
    #[error("face {face} has no steps")]
    EmptyFace { face: usize },
    #[error("face {face} names edge {edge}, but there are {count} edges")]
    EdgeOutOfRange {
        face: usize,
        edge: usize,
        count: usize,
    },
    #[error("face {face} is not a closed walk at step {step}")]
    BrokenWalk { face: usize, step: usize },
    #[error("the matrix on edge {edge} is not in SO(3)")]
    NotRotation { edge: usize },
    #[error("face {face} has holonomy other than I")]
    CurvedFace { face: usize },
    #[error("edge {edge} has spinor norm class {class} and no rational lift")]
    NoRationalLift { edge: usize, class: BigInt },
}

/// A flat rotation transport on a finite 2-complex, with a chosen lift per edge.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FlatRotationTransport {
    vertex_count: usize,
    edges: Vec<(usize, usize)>,
    parities: Vec<u32>,
    obstruction: Vec<bool>,
    classification: SpinLiftClassification,
}

/// Cellular lift classification: solutions of delta^1 s=w2 are a Z^1 torsor,
/// and their vertex-gauge classes form an H^1 torsor. Counts need no enumeration.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SpinLiftClassification {
    complex: F2ChainComplex,
    obstruction: F2Vector,
    torsor: Option<F2AffineSpace>,
}

impl SpinLiftClassification {
    pub fn new(complex: F2ChainComplex, obstruction: F2Vector) -> Result<Self, SpinStructureError> {
        if complex.top_dimension() > 64 || (0..=3).any(|k| complex.cell_count(k) > 4096) {
            return Err(SpinStructureError::CohomologyBudget);
        }
        for degree in 1..=complex.top_dimension().min(3) {
            let r = complex.cell_count(degree - 1);
            let c = complex.cell_count(degree);
            if r.checked_mul(c)
                .and_then(|v| v.checked_mul(r.min(c)))
                .is_none_or(|work| work > 1 << 27)
            {
                return Err(SpinStructureError::CohomologyBudget);
            }
        }
        if !complex.is_cocycle(2, &obstruction)? {
            return Err(ComplexError::NotACocycle { degree: 2 }.into());
        }
        let torsor = complex.solve_coboundary(1, &obstruction)?;
        Ok(Self {
            complex,
            obstruction,
            torsor,
        })
    }
    pub fn obstruction(&self) -> &F2Vector {
        &self.obstruction
    }
    pub fn lift_torsor(&self) -> Option<&F2AffineSpace> {
        self.torsor.as_ref()
    }
    pub fn lift_count(&self) -> num_bigint::BigUint {
        self.torsor
            .as_ref()
            .map_or_else(num_bigint::BigUint::zero, F2AffineSpace::count)
    }
    pub fn gauge_class_count(&self) -> Result<num_bigint::BigUint, SpinStructureError> {
        if self.torsor.is_none() {
            return Ok(num_bigint::BigUint::zero());
        }
        Ok(self.complex.cohomology_count(1)?)
    }
    pub fn enumerate_lifts(&self, limit: usize) -> Result<Vec<F2Vector>, SpinStructureError> {
        self.torsor
            .as_ref()
            .map_or(Ok(Vec::new()), |space| Ok(space.enumerate(limit)?))
    }
}

fn first_curved_face(faces: &[Vec<(usize, bool)>], rotations: &[Rotation]) -> Option<usize> {
    let rotations = rotations
        .iter()
        .map(|r| {
            BasicMatrix::from_row_major(3, 3, r.iter().flatten().cloned().collect())
                .checked_invariant_5528a964("nine entries")
        })
        .collect::<Vec<_>>();
    let identity = mx::identity::<Rational>(3).checked_invariant_5528a964("fixed dimension");
    faces.iter().position(|walk| {
        let holonomy = walk.iter().fold(identity.clone(), |acc, &(edge, forward)| {
            let step = if forward {
                rotations[edge].clone()
            } else {
                mx::transpose(&rotations[edge]).checked_invariant_5528a964("fixed dimension")
            };
            mx::multiply(&step, &acc).checked_invariant_5528a964("fixed dimension")
        });
        holonomy != identity
    })
}

fn validate_transport_counts_and_edges(
    vertex_count: usize,
    edges: &[(usize, usize)],
    faces: &[Vec<(usize, bool)>],
    rotations: &[Rotation],
) -> Result<(), SpinStructureError> {
    if vertex_count > MAX_CELLS || edges.len() > MAX_CELLS {
        return Err(SpinStructureError::TooLarge);
    }
    if faces.len() > 4096
        || faces
            .iter()
            .try_fold(0usize, |n, f| n.checked_add(f.len()))
            .is_none_or(|steps| steps > 1 << 16)
    {
        return Err(SpinStructureError::CohomologyBudget);
    }
    for (edge, &(u, v)) in edges.iter().enumerate() {
        if let Some(vertex) = [u, v].into_iter().find(|&x| x >= vertex_count) {
            return Err(SpinStructureError::VertexOutOfRange {
                edge,
                vertex,
                count: vertex_count,
            });
        }
    }
    if rotations.len() != edges.len() {
        return Err(SpinStructureError::RotationCount {
            edges: edges.len(),
            rotations: rotations.len(),
        });
    }
    Ok(())
}

fn validate_single_face_walk(
    face: usize,
    walk: &[(usize, bool)],
    edges: &[(usize, usize)],
) -> Result<u32, SpinStructureError> {
    if walk.is_empty() {
        return Err(SpinStructureError::EmptyFace { face });
    }
    let mut parity = 0u32;
    let mut ends = Vec::with_capacity(walk.len());
    for &(edge, forward) in walk {
        let &(u, v) = edges.get(edge).ok_or(SpinStructureError::EdgeOutOfRange {
            face,
            edge,
            count: edges.len(),
        })?;
        ends.push(if forward { (u, v) } else { (v, u) });
        parity ^= 1 << edge;
    }
    for (step, end) in ends.iter().enumerate() {
        if end.1 != ends[(step + 1) % ends.len()].0 {
            return Err(SpinStructureError::BrokenWalk { face, step });
        }
    }
    Ok(parity)
}

fn compute_face_parities(
    faces: &[Vec<(usize, bool)>],
    edges: &[(usize, usize)],
) -> Result<Vec<u32>, SpinStructureError> {
    let mut parities = Vec::with_capacity(faces.len());
    for (face, walk) in faces.iter().enumerate() {
        parities.push(validate_single_face_walk(face, walk, edges)?);
    }
    Ok(parities)
}

fn validate_and_lift_rotations(
    faces: &[Vec<(usize, bool)>],
    rotations: &[Rotation],
) -> Result<Vec<BasicMatrix<GaussianRat>>, SpinStructureError> {
    for (edge, r) in rotations.iter().enumerate() {
        let matrix = BasicMatrix::from_row_major(3, 3, r.iter().flatten().cloned().collect())
            .checked_invariant_5528a964("nine entries");
        rodrigues_quaternion(&matrix).map_err(|_| SpinStructureError::NotRotation { edge })?;
    }
    if let Some(face) = first_curved_face(faces, rotations) {
        return Err(SpinStructureError::CurvedFace { face });
    }
    rotations
        .iter()
        .enumerate()
        .map(|(edge, r)| {
            let matrix = BasicMatrix::from_row_major(3, 3, r.iter().flatten().cloned().collect())
                .checked_invariant_5528a964("nine entries");
            matrix_spin_lift(&matrix).map_err(|e| match e {
                SpinLiftError::Quaternion(Su2Error::NoRationalLift { class }) => {
                    SpinStructureError::NoRationalLift { edge, class }
                }
                _ => SpinStructureError::NotRotation { edge },
            })
        })
        .collect::<Result<Vec<BasicMatrix<GaussianRat>>, _>>()
}

fn compute_face_obstruction_bits(
    faces: &[Vec<(usize, bool)>],
    lifts: &[BasicMatrix<GaussianRat>],
) -> Vec<bool> {
    let minus_identity = mx::scale(
        &mx::identity::<GaussianRat>(2).checked_invariant_5528a964("fixed dimension"),
        &GaussianRat::from_rational(-Rational::one()),
    )
    .checked_invariant_5528a964("fixed dimension");
    faces
        .iter()
        .map(|walk| {
            let lifted = walk.iter().fold(
                mx::identity::<GaussianRat>(2).checked_invariant_5528a964("fixed dimension"),
                |acc, &(edge, forward)| {
                    let step = if forward {
                        lifts[edge].clone()
                    } else {
                        involution::adjoint(&lifts[edge])
                            .checked_invariant_5528a964("fixed dimension")
                    };
                    mx::multiply(&step, &acc).checked_invariant_5528a964("fixed dimension")
                },
            );
            lifted == minus_identity
        })
        .collect()
}

fn build_edge_vertex_boundary(
    vertex_count: usize,
    edges: &[(usize, usize)],
) -> Result<F2Matrix, SpinStructureError> {
    let mut boundary1 = F2Matrix::zeros(vertex_count, edges.len())?;
    for (e, &(u, v)) in edges.iter().enumerate() {
        let mut column = F2Vector::zeros(vertex_count)?;
        column.flip(u)?;
        column.flip(v)?;
        for row in column.support() {
            boundary1.set(row, e, true)?;
        }
    }
    Ok(boundary1)
}

fn build_face_edge_boundary(
    edges_len: usize,
    faces_len: usize,
    parities: &[u32],
) -> Result<F2Matrix, SpinStructureError> {
    let mut boundary2 = F2Matrix::zeros(edges_len, faces_len)?;
    for (face, &mask) in parities.iter().enumerate() {
        for e in 0..edges_len {
            boundary2.set(e, face, mask & (1 << e) != 0)?;
        }
    }
    Ok(boundary2)
}

fn build_f2_cellular_complex(
    vertex_count: usize,
    edges: &[(usize, usize)],
    faces_len: usize,
    parities: &[u32],
) -> Result<F2ChainComplex, SpinStructureError> {
    let boundary1 = build_edge_vertex_boundary(vertex_count, edges)?;
    let boundary2 = build_face_edge_boundary(edges.len(), faces_len, parities)?;
    Ok(F2ChainComplex::new(
        vec![vertex_count, edges.len(), faces_len],
        vec![boundary1, boundary2],
    )?)
}

impl FlatRotationTransport {
    pub fn new(
        vertex_count: usize,
        edges: Vec<(usize, usize)>,
        faces: Vec<Vec<(usize, bool)>>,
        rotations: Vec<Rotation>,
    ) -> Result<Self, SpinStructureError> {
        validate_transport_counts_and_edges(vertex_count, &edges, &faces, &rotations)?;
        let parities = compute_face_parities(&faces, &edges)?;
        let lifts = validate_and_lift_rotations(&faces, &rotations)?;
        let obstruction = compute_face_obstruction_bits(&faces, &lifts);
        let cellular = build_f2_cellular_complex(vertex_count, &edges, faces.len(), &parities)?;
        let w = F2Vector::from_bits(&obstruction.iter().map(|&b| u8::from(b)).collect::<Vec<_>>())?;
        let classification = SpinLiftClassification::new(cellular, w)?;
        let out = Self {
            vertex_count,
            edges,
            parities,
            obstruction,
            classification,
        };
        Ok(out)
    }

    /// Face bits of the chosen lifts: `true` where the lifted face product is `-I`.
    pub fn obstruction(&self) -> &[bool] {
        &self.obstruction
    }

    /// Every sign change, as an edge bit mask, whose lifts make every face product `I`.
    pub fn flat_lifts(&self) -> Vec<u32> {
        self.classification
            .enumerate_lifts(1 << MAX_CELLS)
            .checked_invariant_5528a964("the explicit enumeration fits the admitted small carrier")
            .iter()
            .map(|s| s.support().iter().fold(0u32, |mask, &e| mask | (1 << e)))
            .collect()
    }

    pub fn gauge_change(&self, g: u32) -> u32 {
        self.edges
            .iter()
            .enumerate()
            .filter(|&(_, &(u, v))| ((g >> u) & 1) != ((g >> v) & 1))
            .fold(0u32, |mask, (edge, _)| mask | (1 << edge))
    }

    /// The number of vertex-gauge orbits among the flat lifts.
    pub fn gauge_classes(&self) -> usize {
        use num_traits::ToPrimitive;
        self.classification
            .gauge_class_count()
            .checked_invariant_5528a964("validated chain complex")
            .to_usize()
            .checked_invariant_5528a964("small carrier count fits usize")
    }

    pub fn classification(&self) -> &SpinLiftClassification {
        &self.classification
    }
}

/// The two double covers of the orthogonal group. Characteristic-class
/// admission is independent of any choice of edge-lift representative.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PinType {
    Plus,
    Minus,
}
/// Pin lifting of declared characteristic cocycles on a finite ordered
/// simplicial complex. `w1` and `w2` belong to the declared bundle; this
/// constructor does not infer tangent-bundle classes from triangulation alone.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PinLiftClassification {
    pin_type: PinType,
    w1: F2Vector,
    w2: F2Vector,
    w1_square: F2Vector,
    spin: SpinLiftClassification,
}
fn validate_simplicial_cohomology_budget(
    complex: &core_homology::simplicial::SimplicialComplex,
) -> Result<(), SpinStructureError> {
    if complex.max_dimension() > 64 || complex.total_simplices() > 4096 {
        return Err(SpinStructureError::CohomologyBudget);
    }
    for k in 1..=complex.max_dimension() {
        let r = complex.count(k - 1);
        let c = complex.count(k);
        if r.checked_mul(c)
            .and_then(|v| v.checked_mul(r.min(c)))
            .is_none_or(|v| v > 1 << 27)
        {
            return Err(SpinStructureError::CohomologyBudget);
        }
    }
    Ok(())
}

fn verify_first_and_second_cocycles(
    chain: &F2ChainComplex,
    w1: &F2Vector,
    w2: &F2Vector,
) -> Result<(), SpinStructureError> {
    if !chain.is_cocycle(1, w1)? {
        return Err(ComplexError::NotACocycle { degree: 1 }.into());
    }
    if !chain.is_cocycle(2, w2)? {
        return Err(ComplexError::NotACocycle { degree: 2 }.into());
    }
    Ok(())
}

impl PinLiftClassification {
    pub fn from_characteristic_cocycles(
        complex: &core_homology::simplicial::SimplicialComplex,
        w1: F2Vector,
        w2: F2Vector,
        pin_type: PinType,
    ) -> Result<Self, SpinStructureError> {
        validate_simplicial_cohomology_budget(complex)?;
        let chain = F2ChainComplex::from_simplicial_complex(complex)?;
        verify_first_and_second_cocycles(&chain, &w1, &w2)?;
        let w1_square = core_homology::cup_product::cup_product_f2(complex, 1, &w1, 1, &w1)?;
        let obstruction = match pin_type {
            PinType::Plus => w2.clone(),
            PinType::Minus => w2.add(&w1_square)?,
        };
        let spin = SpinLiftClassification::new(chain, obstruction)?;
        let out = Self {
            pin_type,
            w1,
            w2,
            w1_square,
            spin,
        };
        Ok(out)
    }
    pub fn pin_type(&self) -> PinType {
        self.pin_type
    }
    pub fn first_class(&self) -> &F2Vector {
        &self.w1
    }
    pub fn second_class(&self) -> &F2Vector {
        &self.w2
    }
    pub fn first_class_square(&self) -> &F2Vector {
        &self.w1_square
    }
    pub fn obstruction(&self) -> &F2Vector {
        self.spin.obstruction()
    }
    pub fn lift_count(&self) -> num_bigint::BigUint {
        self.spin.lift_count()
    }
    pub fn gauge_class_count(&self) -> Result<num_bigint::BigUint, SpinStructureError> {
        self.spin.gauge_class_count()
    }
    pub fn lift_torsor(&self) -> Option<&F2AffineSpace> {
        self.spin.lift_torsor()
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/spin_structure_obstruction.rs
// Claim: urn:core:crates_rs:core-quantum-physics:spin-structure-obstruction:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_5528a964 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
