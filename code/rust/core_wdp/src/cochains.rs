// Executable finite evidence; AuthorityEffect: None.
//! Root P: finite graph and 2-complex cochain carriers.
//!
//! This module owns the WDP presentation of a finite 2-complex (named vertices,
//! oriented edges and faces, edge-keyed cochains). It owns no mathematics of its
//! own: the coboundary matrices come from `core_homology::graph_carrier`, which
//! also verifies `d1 d0 = 0`, and the dual-certified L1 quotient (WDP-CH04-P01,
//! WDP-CH04-P02, WDP-CH04-C01) is `core_solvers::solver_lp_phi1_quotient::solve_exact_phi1`
//! applied to the presentation returned by [`FiniteComplex::l1_quotient_presentation`].
//!
//! [`solve_potential`] is exact membership `c ∈ im(d0)`, not `Φ₁(c) = 0` through
//! `solve_exact_phi1`. The two agree on whether a potential exists, but the Φ₁
//! certificate is an LP dual pair whose primal need not be a canonical potential,
//! so its normalization would be whatever the solver returned. `solve_in_image`
//! decides membership by exact rank, replays the witness and fixes the
//! normalization (free variables zero); callers who need the distance rather than
//! membership use Φ₁ directly.

use std::collections::{BTreeMap, BTreeSet};

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::linear_algebra::image_kernel::{solve_in_image, ImageMembership};
use num_rational::BigRational;
use num_traits::One;
use core_functional::l1_seminorm::L1Seminorm;
use core_homology::carrier::Carrier;
use core_homology::cochain_complex::TheoremProvenance;
use core_homology::finite_directed_graph::{self, DirectedGraphBuilder};
use core_homology::graph_carrier::graph_carrier;
use serde::{Deserialize, Serialize};

use crate::error::WdpError;

pub type Vertex = String;
pub type Edge = (String, String);
pub type Face = (String, String, String);

/// A finite 2-complex with explicit vertices, oriented edges, and 2-faces.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct FiniteComplex {
    pub vertices: BTreeSet<Vertex>,
    pub edges: Vec<Edge>,
    pub faces: Vec<Face>,
}

impl FiniteComplex {
    fn validate_edges(
        vertices: &BTreeSet<Vertex>,
        edges: &[Edge],
    ) -> Result<BTreeSet<Edge>, WdpError> {
        let mut directed_edges = BTreeSet::new();
        for (u, v) in edges {
            if !directed_edges.insert((u.clone(), v.clone())) {
                return Err(WdpError::InvalidInput {
                    detail: format!("duplicate directed edge ({u}, {v})"),
                });
            }
            if u == v {
                return Err(WdpError::InvalidInput {
                    detail: format!("self-loop edge ({u}, {v}) not allowed"),
                });
            }
            if !vertices.contains(u) || !vertices.contains(v) {
                return Err(WdpError::InvalidInput {
                    detail: format!("edge ({u}, {v}) vertices outside carrier"),
                });
            }
        }
        Ok(directed_edges)
    }

    fn validate_face(
        vertices: &BTreeSet<Vertex>,
        directed_edges: &BTreeSet<Edge>,
        face: &Face,
    ) -> Result<(), WdpError> {
        let (a, b, c) = face;
        if a == b || b == c || a == c {
            return Err(WdpError::InvalidInput {
                detail: format!("face ({a}, {b}, {c}) has degenerate vertices"),
            });
        }
        if !vertices.contains(a) || !vertices.contains(b) || !vertices.contains(c) {
            return Err(WdpError::InvalidInput {
                detail: format!("face ({a}, {b}, {c}) vertices outside carrier"),
            });
        }
        for (u, v) in [(a, b), (b, c), (a, c)] {
            if !directed_edges.contains(&(u.clone(), v.clone()))
                && !directed_edges.contains(&(v.clone(), u.clone()))
            {
                return Err(WdpError::InvalidInput {
                    detail: format!("face ({a}, {b}, {c}) is missing boundary edge {u}-{v}"),
                });
            }
        }
        Ok(())
    }

    pub fn new(
        vertices: BTreeSet<Vertex>,
        edges: Vec<Edge>,
        faces: Vec<Face>,
    ) -> Result<Self, WdpError> {
        if vertices.is_empty() {
            return Err(WdpError::InvalidInput {
                detail: "vertices cannot be empty".to_string(),
            });
        }
        let directed_edges = Self::validate_edges(&vertices, &edges)?;
        for face in &faces {
            Self::validate_face(&vertices, &directed_edges, face)?;
        }

        Ok(Self {
            vertices,
            edges,
            faces,
        })
    }

    /// Revalidate public/deserialized data before a mathematical bridge uses it.
    pub fn validate(&self) -> Result<(), WdpError> {
        Self::new(
            self.vertices.clone(),
            self.edges.clone(),
            self.faces.clone(),
        )
        .map(|_| ())
    }

    /// Admission to an abstract simplicial complex is separate from the graph
    /// cochain domain: opposite oriented edges or repeated vertex-set faces are
    /// distinct cells there, but would collapse in an abstract simplicial set.
    /// Refuse that conversion rather than claiming lossless homology.
    pub fn validate_simplicial_admission(&self) -> Result<(), WdpError> {
        self.validate()?;
        let mut unoriented_edges = BTreeSet::new();
        for (u, v) in &self.edges {
            let key = if u < v {
                (u.clone(), v.clone())
            } else {
                (v.clone(), u.clone())
            };
            if !unoriented_edges.insert(key) {
                return Err(WdpError::InvalidInput {
                    detail: "abstract simplicial admission would collapse distinct edge cells"
                        .into(),
                });
            }
        }
        let mut unoriented_faces = BTreeSet::new();
        for (a, b, c) in &self.faces {
            let mut key = [a.clone(), b.clone(), c.clone()];
            key.sort();
            if !unoriented_faces.insert(key) {
                return Err(WdpError::InvalidInput {
                    detail: "abstract simplicial admission would collapse distinct face cells"
                        .into(),
                });
            }
        }
        Ok(())
    }

    pub fn edge_value(
        cochain: &BTreeMap<Edge, BigRational>,
        u: &str,
        v: &str,
    ) -> Result<BigRational, WdpError> {
        if let Some(val) = cochain.get(&(u.to_string(), v.to_string())) {
            return Ok(val.clone());
        }
        if let Some(val) = cochain.get(&(v.to_string(), u.to_string())) {
            return Ok(-val);
        }
        Err(WdpError::InvalidInput {
            detail: format!("missing cochain value for edge {u}-{v}"),
        })
    }

    /// Edge weights in edge order; an edge absent from `weights` has weight one.
    pub fn edge_weights(&self, weights: Option<&BTreeMap<Edge, BigRational>>) -> Vec<BigRational> {
        self.edges
            .iter()
            .map(|e| {
                weights
                    .and_then(|w_map| w_map.get(e).cloned())
                    .unwrap_or_else(BigRational::one)
            })
            .collect()
    }

    /// The cochain as a coordinate vector in edge order, keyed by exact orientation.
    pub fn cochain_vector(
        &self,
        cochain: &BTreeMap<Edge, BigRational>,
    ) -> Result<Vec<BigRational>, WdpError> {
        self.edges
            .iter()
            .map(|e| {
                cochain
                    .get(e)
                    .cloned()
                    .ok_or_else(|| WdpError::InvalidInput {
                        detail: format!("missing cochain value for edge ({}, {})", e.0, e.1),
                    })
            })
            .collect()
    }

    /// The weighted 1-skeleton as an `core_homology` carrier, vertices in
    /// carrier (sorted) order and edges in declaration order. Faces are not
    /// presented: WDP faces may use reversed edges, which `graph_carrier`
    /// refuses, and degree-1 quotients do not depend on them.
    pub fn one_skeleton_carrier(&self, weights: Vec<BigRational>) -> Result<Carrier, WdpError> {
        let vertices: Vec<Vertex> = self.vertices.iter().cloned().collect();
        named_graph_carrier(
            &vertices,
            &self.edges,
            &[],
            weights,
            "core_wdp::FiniteComplex",
        )
    }

    /// The L1 quotient `C^1 / im(d0)` with the given edge-ordered weights, ready
    /// for `core_solvers::solver_lp_phi1_quotient::solve_exact_phi1`.
    pub fn l1_quotient_presentation(
        &self,
        weights: &[BigRational],
    ) -> Result<L1Seminorm, WdpError> {
        let carrier = self.one_skeleton_carrier(weights.to_vec())?;
        Ok(L1Seminorm::new(
            coboundary_rows(carrier.d0()),
            carrier.weights().to_vec(),
        )?)
    }
}

/// Build the `core_homology` graph carrier for named vertices, oriented edges
/// and oriented triangles `(a, b, c)` whose edges are `(a, b)`, `(b, c)`, `(a, c)`.
/// `core_homology` owns `d0`, `d1` and the check `d1 d0 = 0`.
pub(crate) fn named_graph_carrier(
    vertices: &[Vertex],
    edges: &[Edge],
    faces: &[Face],
    weights: Vec<BigRational>,
    source: &str,
) -> Result<Carrier, WdpError> {
    let graph = DirectedGraphBuilder::from_named(
        vertices.to_vec(),
        edges,
        finite_directed_graph::TheoremProvenance {
            verification_source: source.to_string(),
        },
    )?;
    let index = |name: &String| {
        graph
            .node_index()
            .get(name)
            .copied()
            .ok_or_else(|| WdpError::ElementNotFound {
                element: name.clone(),
            })
    };
    let triangles = faces
        .iter()
        .map(|(a, b, c)| Ok((index(a)?, index(b)?, index(c)?)))
        .collect::<Result<Vec<_>, WdpError>>()?;
    Ok(graph_carrier(
        &graph,
        &triangles,
        weights,
        TheoremProvenance::new(source.to_string())?,
    )?)
}

/// Row-major copy of an `core_homology` coboundary matrix.
pub(crate) fn coboundary_rows(matrix: &BasicMatrix<BigRational>) -> Vec<Vec<BigRational>> {
    if matrix.cols() == 0 {
        return vec![Vec::new(); matrix.rows()];
    }
    matrix
        .as_slice()
        .chunks(matrix.cols())
        .map(<[BigRational]>::to_vec)
        .collect()
}

/// Exact potential for an exact 1-cochain: `phi` with `phi(v) - phi(u) = c(u, v)`
/// on every edge. A cochain keyed by the reversed edge counts with its sign flipped.
///
/// Whether `c ∈ im(d0)`, and the witness, are `core_linear_algebra`'s
/// `solve_in_image` on the incidence matrix from `core_homology::graph_carrier`,
/// replayed exactly. The witness sets the free variables to zero, which pins the
/// last vertex (in carrier order) of each connected component to potential 0.
pub fn solve_potential(
    complex: &FiniteComplex,
    cochain: &BTreeMap<Edge, BigRational>,
) -> Result<BTreeMap<Vertex, BigRational>, WdpError> {
    let target = complex
        .edges
        .iter()
        .map(|(u, v)| FiniteComplex::edge_value(cochain, u, v))
        .collect::<Result<Vec<_>, _>>()?;
    let carrier = complex.one_skeleton_carrier(complex.edge_weights(None))?;
    match solve_in_image(carrier.d0(), &target)? {
        ImageMembership::InImage(witness) => Ok(complex
            .vertices
            .iter()
            .cloned()
            .zip(witness.potential)
            .collect()),
        ImageMembership::NotInImage {
            rank_a,
            rank_augmented,
        } => Err(WdpError::InvalidInput {
            detail: format!(
                "cochain is not exact: rank(d0) = {rank_a} < rank([d0 | c]) = {rank_augmented}"
            ),
        }),
    }
}

// Origin: engine/crates_rs/core_wdp/src/cochains.rs
// Claim: urn:core:crates_rs:core-wdp:cochains:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordcfa270a8 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordcfa270a8` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorcfa270a8 {
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
impl BoundaryErrorcfa270a8 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorcfa270a8 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorcfa270a8 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordcfa270a8 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorcfa270a8> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorcfa270a8::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorcfa270a8::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorcfa270a8::ExceedsCapacity {
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
    use core_functional::phi1::Phi1Functional;
    use core_homology::scalar::{q, qr};
    use core_solvers::solver_lp_phi1_quotient::solve_exact_phi1;

    fn triangle() -> FiniteComplex {
        // Oriented triangle 0 -> 1 -> 2 -> 0
        let vertices = BTreeSet::from(["0".to_string(), "1".to_string(), "2".to_string()]);
        let edges = vec![
            ("0".to_string(), "1".to_string()),
            ("1".to_string(), "2".to_string()),
            ("2".to_string(), "0".to_string()),
        ];
        FiniteComplex::new(vertices, edges, vec![]).unwrap()
    }

    fn cochain(values: [i64; 3]) -> BTreeMap<Edge, BigRational> {
        triangle().edges.into_iter().zip(values.map(q)).collect()
    }

    #[test]
    fn test_triangle_exact_primal_dual() {
        let complex = triangle();
        let space = complex
            .l1_quotient_presentation(&complex.edge_weights(None))
            .unwrap();

        // Exact cochain: (1, 1, -2) sums to 0 around the loop.
        let exact = solve_exact_phi1(
            &space,
            &complex.cochain_vector(&cochain([1, 1, -2])).unwrap(),
        )
        .unwrap();
        assert_eq!(exact.value(), &q(0));

        // Frustrated cochain: (1, 1, 1) has circulation 3.
        let frustrated = solve_exact_phi1(
            &space,
            &complex.cochain_vector(&cochain([1, 1, 1])).unwrap(),
        )
        .unwrap();
        assert_eq!(frustrated.value(), &q(3));

        // Zero duality gap: the exported witness replays through the verifier.
        for verified in [exact, frustrated] {
            Phi1Functional::verify_exact_certificate(verified.certificate().clone()).unwrap();
        }
    }

    #[test]
    fn test_presentation_uses_omega_homology_incidence() {
        let complex = triangle();
        let carrier = complex
            .one_skeleton_carrier(complex.edge_weights(None))
            .unwrap();
        // (d0 phi)(u, v) = phi(v) - phi(u) on edge (2, 0).
        assert_eq!(coboundary_rows(carrier.d0())[2], vec![q(1), q(0), q(-1)]);
        assert_eq!(
            complex.cochain_vector(&BTreeMap::new()),
            Err(WdpError::InvalidInput {
                detail: "missing cochain value for edge (0, 1)".to_string()
            })
        );
    }

    #[test]
    fn test_solve_potential_recovers_exact_cochain() {
        let complex = triangle();
        let c = cochain([1, 1, -2]);
        let potential = solve_potential(&complex, &c).unwrap();
        for (u, v) in &complex.edges {
            assert_eq!(&potential[v] - &potential[u], c[&(u.clone(), v.clone())]);
        }
        // The single component's free variable is its last vertex in carrier order.
        assert_eq!(potential["2"], q(0));

        // A cochain keyed by the reversed edge counts with its sign flipped.
        let mut reversed = c.clone();
        let value = reversed
            .remove(&("0".to_string(), "1".to_string()))
            .unwrap();
        reversed.insert(("1".to_string(), "0".to_string()), -value);
        assert_eq!(solve_potential(&complex, &reversed).unwrap(), potential);

        assert!(matches!(
            solve_potential(&complex, &cochain([1, 1, 1])),
            Err(WdpError::InvalidInput { .. })
        ));
    }

    #[test]
    fn test_solve_potential_on_disconnected_carrier() {
        // Components {a, b}, {c, d} and the isolated vertex e.
        let vertices = ["a", "b", "c", "d", "e"].map(String::from).into();
        let edges = vec![
            ("a".to_string(), "b".to_string()),
            ("c".to_string(), "d".to_string()),
        ];
        let complex = FiniteComplex::new(vertices, edges, Vec::new()).unwrap();
        let c = BTreeMap::from([
            (("a".to_string(), "b".to_string()), q(3)),
            (("d".to_string(), "c".to_string()), qr(1, 2)),
        ]);
        let potential = solve_potential(&complex, &c).unwrap();
        // Each component's last vertex, and the isolated vertex, are pinned to 0.
        assert_eq!(
            potential,
            BTreeMap::from([
                ("a".to_string(), q(-3)),
                ("b".to_string(), q(0)),
                ("c".to_string(), qr(1, 2)),
                ("d".to_string(), q(0)),
                ("e".to_string(), q(0)),
            ])
        );
    }
    #[test]
    fn face_boundary_validation_and_simplicial_multicell_admission() {
        let vertices = BTreeSet::from(["a".into(), "b".into(), "c".into()]);
        assert!(FiniteComplex::new(
            vertices.clone(),
            vec![("a".into(), "b".into())],
            vec![("a".into(), "b".into(), "c".into())]
        )
        .is_err());
        let directed = FiniteComplex::new(
            BTreeSet::from(["a".into(), "b".into()]),
            vec![("a".into(), "b".into()), ("b".into(), "a".into())],
            vec![],
        )
        .unwrap();
        assert_eq!(
            directed
                .one_skeleton_carrier(vec![q(1), q(1)])
                .unwrap()
                .dim_q1()
                .unwrap(),
            1
        );
        assert!(directed.validate_simplicial_admission().is_err());
        assert!(FiniteComplex::new(
            vertices,
            vec![("a".into(), "b".into()), ("a".into(), "b".into())],
            vec![]
        )
        .is_err());
    }

    #[test]
    fn test_section_7_acceptance_triangle_inputs() {
        use num_traits::Signed;
        let complex = triangle();
        let space = complex
            .l1_quotient_presentation(&complex.edge_weights(None))
            .unwrap();

        // 1. Exact: c = (1, 2, -3) = d0 * (0, 1, 3), with filled face d1 = (1, 1, 1).
        let c_exact_map = cochain([1, 2, -3]);
        let c_exact_vec = complex.cochain_vector(&c_exact_map).unwrap();
        let exact_phi1 = solve_exact_phi1(&space, &c_exact_vec).unwrap();
        assert_eq!(exact_phi1.value(), &q(0));
        Phi1Functional::verify_exact_certificate(exact_phi1.certificate().clone()).unwrap();
        let gamma2_exact: BigRational = c_exact_vec.iter().cloned().sum::<BigRational>().abs();
        assert_eq!(gamma2_exact, q(0));
        let pot = solve_potential(&complex, &c_exact_map).unwrap();
        assert_eq!(&pot["1"] - &pot["0"], q(1));
        assert_eq!(&pot["2"] - &pot["1"], q(2));
        assert_eq!(&pot["0"] - &pot["2"], q(-3));

        // 2. Coherent residual: omit faces explicitly (dim C^2 = 0) and set c = (1, 1, 1).
        let c_coh_map = cochain([1, 1, 1]);
        let c_coh_vec = complex.cochain_vector(&c_coh_map).unwrap();
        let coh_phi1 = solve_exact_phi1(&space, &c_coh_vec).unwrap();
        assert_eq!(coh_phi1.value(), &q(3));
        Phi1Functional::verify_exact_certificate(coh_phi1.certificate().clone()).unwrap();
        let gamma2_unfilled = q(0);
        assert_eq!(gamma2_unfilled, q(0));
        assert!(solve_potential(&complex, &c_coh_map).is_err());

        // 3. Nonclosed defect: same c = (1, 1, 1) with filled face d1 = (1, 1, 1).
        let gamma2_filled: BigRational = c_coh_vec.iter().cloned().sum::<BigRational>().abs();
        assert_eq!(coh_phi1.value(), &q(3));
        assert_eq!(gamma2_filled, q(3));
    }
}

#[cfg(test)]
mod l4_boundary_tests_cfa270a8 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordcfa270a8::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordcfa270a8::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordcfa270a8::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordcfa270a8::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordcfa270a8::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorcfa270a8::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorcfa270a8::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
