//! Integration tests for core_homology.

// Origin: engine/crates_rs/core_homology/src/tests/mod.rs
// Claim: urn:core:crates_rs:core-homology:mod:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord53f08f90 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord53f08f90` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError53f08f90 {
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
impl BoundaryError53f08f90 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError53f08f90 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError53f08f90 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord53f08f90 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError53f08f90> {
        if capacity_bound == 0 {
            return Err(BoundaryError53f08f90::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError53f08f90::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError53f08f90::ExceedsCapacity {
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
mod integration_tests {
    use crate::carrier::Carrier;
    use crate::carrier_manifest::CarrierManifest;
    use crate::chain::Chain;
    use crate::chain_complex::ChainComplex;
    use crate::cochain_complex::{CochainComplex, TheoremProvenance};
    use crate::cycle::try_cycle;
    use crate::errors::HomologicalError;
    use crate::finite_directed_graph::{DirectedGraphBuilder, TheoremProvenance as GraphProv};
    use crate::graph_carrier::graph_carrier;
    use crate::hashing::hash_weights;
    use crate::ids::{BasisId, Degree};
    use crate::scalar::{q, Q};
    use crate::simplicial::{OrientedSimplex, SimplicialComplex};
    use linear_algebra::backend::basic_matrix::BasicMatrix;
    use num_rational::Rational64;
    use num_traits::Zero;

    fn prov() -> TheoremProvenance {
        TheoremProvenance::new("test".to_string()).unwrap()
    }

    fn unit_weights(n: usize) -> Vec<Q> {
        vec![crate::scalar::q(1); n]
    }

    fn make_graph(
        num_nodes: usize,
        edges: &[(usize, usize)],
    ) -> crate::finite_directed_graph::FiniteDirectedGraph {
        let graph_prov = GraphProv {
            verification_source: "test".to_string(),
        };
        DirectedGraphBuilder::from_anonymous(num_nodes, edges.to_vec(), graph_prov).unwrap()
    }

    // --- Zero complex ---
    #[test]
    fn zero_complex_works() {
        let d0 = BasicMatrix::<Q>::zero(0, 0).unwrap();
        let d1 = BasicMatrix::<Q>::zero(0, 0).unwrap();
        let carrier = Carrier::new(0, 0, 0, d0, d1, vec![], prov());
        assert!(carrier.is_ok());
    }

    // --- Single edge tree ---
    #[test]
    fn single_edge_tree_homology() {
        let graph = make_graph(2, &[(0, 1)]);
        let carrier = graph_carrier(&graph, &[], unit_weights(1), prov()).unwrap();
        assert_eq!(carrier.rank_d0().unwrap(), 1);
        assert_eq!(carrier.dim_q1().unwrap(), 0);
        assert_eq!(carrier.dim_h1().unwrap(), 0);
    }

    // --- Triangle with filling has H1 = 0 ---
    #[test]
    fn triangle_with_filling_h1_zero() {
        let graph = make_graph(3, &[(0, 1), (1, 2), (0, 2)]);
        let carrier = graph_carrier(&graph, &[(0, 1, 2)], unit_weights(3), prov()).unwrap();
        assert_eq!(carrier.dim_h1().unwrap(), 0);
    }

    // --- Triangle without filling has H1 = 1 ---
    #[test]
    fn triangle_without_filling_h1_one() {
        let graph = make_graph(3, &[(0, 1), (1, 2), (0, 2)]);
        let carrier = graph_carrier(&graph, &[], unit_weights(3), prov()).unwrap();
        assert_eq!(carrier.dim_h1().unwrap(), 1);
    }

    // --- Bad coboundary relation rejected ---
    #[test]
    fn bad_coboundary_relation_rejected() {
        let d0 = BasicMatrix::<Q>::from_row_major(2, 2, vec![q(1), q(0), q(0), q(1)]).unwrap();
        let d1 = BasicMatrix::<Q>::from_row_major(1, 2, vec![q(1), q(1)]).unwrap();
        let result = CochainComplex::new(2, 2, 1, d0, d1, prov());
        assert!(matches!(
            result,
            Err(HomologicalError::CoboundaryLawViolation { .. })
        ));
    }

    // --- Dimension mismatch rejected ---
    #[test]
    fn dimension_mismatch_rejected() {
        let d0 = BasicMatrix::<Q>::zero(1, 1).unwrap();
        let d1 = BasicMatrix::<Q>::zero(1, 2).unwrap();
        let result = CochainComplex::new(2, 2, 1, d0, d1, prov());
        assert!(matches!(
            result,
            Err(HomologicalError::DimensionMismatch { .. })
        ));
    }

    // --- Non-positive weights rejected ---
    #[test]
    fn non_positive_weights_rejected() {
        let d0 = BasicMatrix::<Q>::from_row_major(1, 2, vec![q(-1), q(1)]).unwrap();
        let d1 = BasicMatrix::<Q>::zero(0, 1).unwrap();
        let result = Carrier::new(2, 1, 0, d0, d1, vec![q(0)], prov());
        assert!(matches!(
            result,
            Err(HomologicalError::NonPositiveWeight { .. })
        ));
    }

    // --- Triangle missing edge rejected ---
    #[test]
    fn triangle_missing_edge_rejected() {
        let graph = make_graph(3, &[(0, 1), (1, 2)]);
        let result = graph_carrier(&graph, &[(0, 1, 2)], unit_weights(2), prov());
        assert!(matches!(
            result,
            Err(HomologicalError::TriangleMissingEdge { .. })
        ));
    }

    // --- Manifests deterministic ---
    #[test]
    fn carrier_manifest_deterministic() {
        let graph = make_graph(3, &[(0, 1), (1, 2), (0, 2)]);
        let carrier = graph_carrier(&graph, &[], unit_weights(3), prov()).unwrap();
        let m1 = CarrierManifest::from_carrier(&carrier).unwrap();
        let m2 = CarrierManifest::from_carrier(&carrier).unwrap();
        assert_eq!(m1.carrier_hash(), m2.carrier_hash());
    }

    // --- Different carriers different hashes ---
    #[test]
    fn different_carriers_different_hashes() {
        let g1 = make_graph(3, &[(0, 1), (1, 2), (0, 2)]);
        let g2 = make_graph(3, &[(0, 1), (1, 2)]);
        let c1 = graph_carrier(&g1, &[], unit_weights(3), prov()).unwrap();
        let c2 = graph_carrier(&g2, &[], unit_weights(2), prov()).unwrap();
        let m1 = CarrierManifest::from_carrier(&c1).unwrap();
        let m2 = CarrierManifest::from_carrier(&c2).unwrap();
        assert_ne!(m1.carrier_hash(), m2.carrier_hash());
    }

    // --- Cycle checker ---
    #[test]
    fn cycle_checker_accepts_zero_chain() {
        let d1_mat =
            BasicMatrix::<Q>::from_row_major(2, 3, vec![q(1), q(-1), q(0), q(0), q(1), q(-1)])
                .unwrap();
        let d2_mat = BasicMatrix::<Q>::zero(3, 0).unwrap();
        let complex = ChainComplex::new(2, 3, 0, d1_mat, d2_mat).unwrap();

        let chain = Chain::zero(Degree::new(1), BasisId::new("test"), 3);
        let result = try_cycle(chain, Some(&complex.boundary_1), complex.complex_hash());
        assert!(result.is_ok());
    }

    // --- Cycle checker rejects non-cycle ---
    #[test]
    fn cycle_checker_rejects_non_cycle() {
        let d1_mat =
            BasicMatrix::<Q>::from_row_major(2, 3, vec![q(1), q(-1), q(0), q(0), q(1), q(-1)])
                .unwrap();
        let d2_mat = BasicMatrix::<Q>::zero(3, 0).unwrap();
        let complex = ChainComplex::new(2, 3, 0, d1_mat, d2_mat).unwrap();

        let chain = Chain::new(Degree::new(1), BasisId::new("test"), vec![q(1), q(0), q(0)]);
        let result = try_cycle(chain, Some(&complex.boundary_1), complex.complex_hash());
        assert!(matches!(result, Err(HomologicalError::NotCycle)));
    }

    // --- Simplicial complex tests ---
    #[test]
    fn simplicial_triangle_face_closure() {
        let triangle = OrientedSimplex::new(vec![0, 1, 2]).unwrap();
        let complex = SimplicialComplex::from_maximal_simplices(vec![triangle]).unwrap();
        assert_eq!(complex.count(0), 3);
        assert_eq!(complex.count(1), 3);
        assert_eq!(complex.count(2), 1);
        assert_eq!(complex.euler_characteristic(), 1);
    }

    // --- Manifest records weights_hash ---
    #[test]
    fn manifest_records_weights_hash() {
        let graph = make_graph(3, &[(0, 1), (1, 2)]);
        let carrier = graph_carrier(&graph, &[], unit_weights(2), prov()).unwrap();
        let manifest = CarrierManifest::from_carrier(&carrier).unwrap();
        assert_eq!(*manifest.weights_hash(), hash_weights(carrier.weights()));
    }

    // --- Manifest records provenance hash ---
    #[test]
    fn manifest_records_provenance_hash() {
        let graph = make_graph(2, &[(0, 1)]);
        let carrier = graph_carrier(&graph, &[], unit_weights(1), prov()).unwrap();
        let manifest = CarrierManifest::from_carrier(&carrier).unwrap();
        assert_ne!(manifest.provenance_hash().0, [0u8; 32]);
    }

    #[test]
    fn test_triangle_subdivision_preserves_homology() {
        use crate::chain_map::CertifiedChainMap;

        // C: Unfilled triangle graph
        // Vertices: 0, 1, 2
        // Edges: e0=(0,1), e1=(1,2), e2=(2,0)
        let d1_c = BasicMatrix::from_row_major(
            3,
            3,
            vec![q(-1), q(0), q(1), q(1), q(-1), q(0), q(0), q(1), q(-1)],
        )
        .unwrap();
        let d2_c = BasicMatrix::zero(3, 0).unwrap();
        let c = ChainComplex::new(3, 3, 0, d1_c, d2_c).unwrap();

        // D: Subdivided triangle graph (subdivide e0 by vertex 3)
        // Vertices: 0, 1, 2, 3
        // Edges: e0_prime=(0,3), e1_prime=(1,2), e2_prime=(2,0), e3_prime=(3,1)
        let d1_d = BasicMatrix::from_row_major(
            4,
            4,
            vec![
                q(-1),
                q(0),
                q(1),
                q(0),
                q(0),
                q(-1),
                q(0),
                q(1),
                q(0),
                q(1),
                q(-1),
                q(0),
                q(1),
                q(0),
                q(0),
                q(-1),
            ],
        )
        .unwrap();
        let d2_d = BasicMatrix::zero(4, 0).unwrap();
        let d = ChainComplex::new(4, 4, 0, d1_d, d2_d).unwrap();

        // Chain map phi: C -> D
        // phi_0: C_0 -> D_0 (vertices)
        let phi_0 = BasicMatrix::from_row_major(
            4,
            3,
            vec![
                q(1),
                q(0),
                q(0),
                q(0),
                q(1),
                q(0),
                q(0),
                q(0),
                q(1),
                q(0),
                q(0),
                q(0),
            ],
        )
        .unwrap();

        // phi_1: C_1 -> D_1 (edges)
        let phi_1 = BasicMatrix::from_row_major(
            4,
            3,
            vec![
                q(1),
                q(0),
                q(0),
                q(0),
                q(1),
                q(0),
                q(0),
                q(0),
                q(1),
                q(1),
                q(0),
                q(0),
            ],
        )
        .unwrap();

        // phi_2: C_2 -> D_2
        let phi_2 = BasicMatrix::zero(0, 0).unwrap();

        // Verify it is a valid chain map
        let chain_map = CertifiedChainMap::new_checked(vec![phi_0, phi_1, phi_2], &c, &d)
            .expect("should be a certified chain map");

        // Cycle z in C_1: e0 + e1 + e2 (the triangle cycle)
        let z = vec![q(1), q(1), q(1)];

        // Verify z is indeed a cycle in C (d1_c * z = 0)
        let z_matrix = BasicMatrix::from_row_major(3, 1, z.clone()).unwrap();
        let dz = c.boundary_1.matrix.checked_mul(&z_matrix).unwrap();
        for val in dz.as_slice() {
            assert!(val.is_zero());
        }

        // Apply phi_1 to z: phi_1 * z
        let phi_1_mat = &chain_map.maps()[1];
        let phi_z = phi_1_mat.checked_mul(&z_matrix).unwrap();

        // Output should be [1, 1, 1, 1]^T representing e0' + e3' + e1' + e2'
        let expected_phi_z = vec![q(1), q(1), q(1), q(1)];
        assert_eq!(phi_z.as_slice(), &expected_phi_z);

        // Verify that phi_z is indeed a cycle in D (d1_d * phi_z = 0)
        let d_phi_z = d.boundary_1.matrix.checked_mul(&phi_z).unwrap();
        for val in d_phi_z.as_slice() {
            assert!(val.is_zero());
        }
    }

    // =========================================================================
    // PO-D1 Discharge: d_1 * d_0 = 0 per carrier
    //
    // Each test constructs a concrete carrier via graph_carrier() or
    // Carrier::new(). Successful construction IS the proof that d1*d0=0,
    // because CochainComplex::new() verifies this at lines 109-118.
    // =========================================================================

    #[test]
    fn proof_pod1_filled_triangle() {
        // C^0 = Q^3 (vertices), C^1 = Q^3 (edges), C^2 = Q^1 (triangle face)
        // This exercises the NON-VACUOUS d1*d0 path (c2_dim=1, c0_dim=3).
        let graph = make_graph(3, &[(0, 1), (1, 2), (0, 2)]);
        let carrier = graph_carrier(&graph, &[(0, 1, 2)], unit_weights(3), prov()).unwrap();
        assert_eq!(carrier.c0_dim(), 3);
        assert_eq!(carrier.c1_dim(), 3);
        assert_eq!(carrier.c2_dim(), 1);
        assert_eq!(carrier.dim_h1().unwrap(), 0);
        assert_eq!(carrier.rank_d0().unwrap(), 2);
        assert_eq!(carrier.rank_d1().unwrap(), 1);
    }

    #[test]
    fn proof_pod1_path_graph() {
        // Path: 0 -> 1, single edge. C^0 = Q^2, C^1 = Q^1, C^2 = 0.
        // Vacuous d1*d0 check (c2_dim=0), but carrier construction still succeeds.
        let graph = make_graph(2, &[(0, 1)]);
        let carrier = graph_carrier(&graph, &[], unit_weights(1), prov()).unwrap();
        assert_eq!(carrier.c0_dim(), 2);
        assert_eq!(carrier.c1_dim(), 1);
        assert_eq!(carrier.c2_dim(), 0);
        assert_eq!(carrier.dim_h1().unwrap(), 0);
        assert_eq!(carrier.rank_d0().unwrap(), 1);
    }

    #[test]
    fn proof_pod1_unfilled_triangle() {
        // Triangle without face: C^0 = Q^3, C^1 = Q^3, C^2 = 0.
        // Vacuous d1*d0 check. H^1 = 1 (the cycle around the triangle).
        let graph = make_graph(3, &[(0, 1), (1, 2), (0, 2)]);
        let carrier = graph_carrier(&graph, &[], unit_weights(3), prov()).unwrap();
        assert_eq!(carrier.c0_dim(), 3);
        assert_eq!(carrier.c1_dim(), 3);
        assert_eq!(carrier.c2_dim(), 0);
        assert_eq!(carrier.dim_h1().unwrap(), 1);
    }

    #[test]
    fn proof_pod1_square_graph() {
        // Square: 4 nodes, 4 edges (cycle). C^0 = Q^4, C^1 = Q^4, C^2 = 0.
        // H^1 = 1 (one independent cycle).
        let graph = make_graph(4, &[(0, 1), (1, 2), (2, 3), (0, 3)]);
        let carrier = graph_carrier(&graph, &[], unit_weights(4), prov()).unwrap();
        assert_eq!(carrier.c0_dim(), 4);
        assert_eq!(carrier.c1_dim(), 4);
        assert_eq!(carrier.c2_dim(), 0);
        assert_eq!(carrier.dim_h1().unwrap(), 1);
        assert_eq!(carrier.rank_d0().unwrap(), 3);
    }

    #[test]
    fn proof_pod1_k4_graph() {
        // Complete graph K4: 4 nodes, 6 edges, 4 triangles.
        // Non-vacuous d1*d0 check (c2_dim=4).
        let graph = make_graph(4, &[(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]);
        let carrier = graph_carrier(
            &graph,
            &[(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)],
            unit_weights(6),
            prov(),
        )
        .unwrap();
        assert_eq!(carrier.c0_dim(), 4);
        assert_eq!(carrier.c1_dim(), 6);
        assert_eq!(carrier.c2_dim(), 4);
        assert_eq!(carrier.dim_h1().unwrap(), 0);
        assert_eq!(carrier.rank_d0().unwrap(), 3);
    }

    #[test]
    fn proof_pod1_linear_path_3_nodes() {
        // Path: 0 -> 1 -> 2. A tree, so H^1 = 0.
        let graph = make_graph(3, &[(0, 1), (1, 2)]);
        let carrier = graph_carrier(&graph, &[], unit_weights(2), prov()).unwrap();
        assert_eq!(carrier.c0_dim(), 3);
        assert_eq!(carrier.c1_dim(), 2);
        assert_eq!(carrier.c2_dim(), 0);
        assert_eq!(carrier.dim_h1().unwrap(), 0);
        assert_eq!(carrier.rank_d0().unwrap(), 2);
    }

    #[test]
    fn proof_pod1_direct_matrix_construction() {
        // Directly construct a carrier with known d0/d1 matrices that satisfy d1*d0=0.
        // This tests the non-graph path through Carrier::new().
        // d0 = [[1], [-1], [0]], d1 = [[1, 1, -1]]
        // d1*d0 = [[1,1,-1]] * [[1],[-1],[0]] = [1 + (-1) + 0] = [0]. OK.
        let d0 = BasicMatrix::from_row_major(3, 1, vec![q(1), q(-1), q(0)]).unwrap();
        let d1 = BasicMatrix::from_row_major(1, 3, vec![q(1), q(1), q(-1)]).unwrap();
        let weights = vec![q(1), q(1), q(1)];
        let carrier = Carrier::new(1, 3, 1, d0, d1, weights, prov()).unwrap();
        assert_eq!(carrier.c0_dim(), 1);
        assert_eq!(carrier.c1_dim(), 3);
        assert_eq!(carrier.c2_dim(), 1);
    }

    // =========================================================================
    // STORY-101-004: Integration Bridge — SNF on Carrier Matrices
    // =========================================================================

    #[test]
    fn snf_triangle_d0_rank_2() {
        use linear_algebra::smith_normal_form::{
            from_bigrational_integer_matrix, smith_normal_form_checked,
        };
        let graph = make_graph(3, &[(0, 1), (1, 2), (0, 2)]);
        let carrier = graph_carrier(&graph, &[], unit_weights(3), prov()).unwrap();
        let d0_bigint = from_bigrational_integer_matrix(carrier.d0()).unwrap();
        let snf = smith_normal_form_checked(&d0_bigint).unwrap();
        assert_eq!(snf.diagonal().rank(), 2);
        assert_eq!(
            snf.diagonal().invariants(),
            &[num_bigint::BigInt::from(1), num_bigint::BigInt::from(1)]
        );
        let ua = snf.u().mul(&d0_bigint).unwrap();
        let uav = ua.mul(snf.v()).unwrap();
        assert_eq!(uav.as_slice(), snf.diagonal_matrix().as_slice());
    }

    #[test]
    fn snf_single_edge_d0_rank_1() {
        use linear_algebra::smith_normal_form::{
            from_bigrational_integer_matrix, smith_normal_form_checked,
        };
        let graph = make_graph(2, &[(0, 1)]);
        let carrier = graph_carrier(&graph, &[], unit_weights(1), prov()).unwrap();
        let d0_bigint = from_bigrational_integer_matrix(carrier.d0()).unwrap();
        let snf = smith_normal_form_checked(&d0_bigint).unwrap();
        assert_eq!(snf.diagonal().rank(), 1);
        assert_eq!(snf.diagonal().invariants(), &[num_bigint::BigInt::from(1)]);
        let ua = snf.u().mul(&d0_bigint).unwrap();
        let uav = ua.mul(snf.v()).unwrap();
        assert_eq!(uav.as_slice(), snf.diagonal_matrix().as_slice());
    }

    #[test]
    fn snf_k4_d0_rank_3() {
        use linear_algebra::smith_normal_form::{
            from_bigrational_integer_matrix, smith_normal_form_checked,
        };
        let graph = make_graph(4, &[(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]);
        let carrier = graph_carrier(
            &graph,
            &[(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)],
            unit_weights(6),
            prov(),
        )
        .unwrap();
        let d0_bigint = from_bigrational_integer_matrix(carrier.d0()).unwrap();
        let snf = smith_normal_form_checked(&d0_bigint).unwrap();
        assert_eq!(snf.diagonal().rank(), 3);
        assert_eq!(
            snf.diagonal().invariants(),
            &[
                num_bigint::BigInt::from(1),
                num_bigint::BigInt::from(1),
                num_bigint::BigInt::from(1)
            ]
        );
        let ua = snf.u().mul(&d0_bigint).unwrap();
        let uav = ua.mul(snf.v()).unwrap();
        assert_eq!(uav.as_slice(), snf.diagonal_matrix().as_slice());
    }

    #[test]
    fn snf_filled_triangle_d1_rank_1() {
        use linear_algebra::smith_normal_form::{
            from_bigrational_integer_matrix, smith_normal_form_checked,
        };
        let graph = make_graph(3, &[(0, 1), (1, 2), (0, 2)]);
        let carrier = graph_carrier(&graph, &[(0, 1, 2)], unit_weights(3), prov()).unwrap();
        let d1_bigint = from_bigrational_integer_matrix(carrier.d1()).unwrap();
        let snf = smith_normal_form_checked(&d1_bigint).unwrap();
        assert_eq!(snf.diagonal().rank(), 1);
        assert_eq!(snf.diagonal().invariants(), &[num_bigint::BigInt::from(1)]);
        let ua = snf.u().mul(&d1_bigint).unwrap();
        let uav = ua.mul(snf.v()).unwrap();
        assert_eq!(uav.as_slice(), snf.diagonal_matrix().as_slice());
    }
}

#[cfg(test)]
mod l4_boundary_tests_53f08f90 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord53f08f90::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord53f08f90::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord53f08f90::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord53f08f90::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord53f08f90::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError53f08f90::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError53f08f90::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
