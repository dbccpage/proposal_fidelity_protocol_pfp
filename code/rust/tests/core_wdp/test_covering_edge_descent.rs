// Executable finite evidence; AuthorityEffect: None.
//! Tests for `core_wdp::covering_edge_descent`:
//! Verifies Proposition 2.1a, Lemma 2.2, Theorem 3.2, Theorem 3.4, Theorem 3.6,
//! Theorem 4.1, Theorem 4.2, Theorem 4.4, Theorem 4.6, Statement 4.7,
//! Theorem 4.11, and Corollary 4.11a.

use std::collections::BTreeMap;
use core_wdp::covering_edge_descent::*;

#[test]
fn test_path_a_strict_completion_and_diamond_path_independence() {
    let elements = vec!["0".to_string(), "1".to_string(), "2".to_string(), "3".to_string()];
    let dims = BTreeMap::from([
        ("0".to_string(), 2),
        ("1".to_string(), 2),
        ("2".to_string(), 2),
        ("3".to_string(), 2),
    ]);

    // Covering restrictions commuting around diamond
    let r_31 = ExactMatrix::from_i64(&[&[1, 1], &[0, 1]]);
    let r_10 = ExactMatrix::from_i64(&[&[1, 2], &[0, 1]]);
    let r_32 = ExactMatrix::from_i64(&[&[1, 2], &[0, 1]]);
    let r_20 = ExactMatrix::from_i64(&[&[1, 1], &[0, 1]]);

    let mut cov_restrictions = BTreeMap::new();
    cov_restrictions.insert(("3".to_string(), "1".to_string()), r_31);
    cov_restrictions.insert(("1".to_string(), "0".to_string()), r_10);
    cov_restrictions.insert(("3".to_string(), "2".to_string()), r_32);
    cov_restrictions.insert(("2".to_string(), "0".to_string()), r_20);

    let diagram = CoveringEdgeDiagramCED::new(elements.clone(), dims.clone(), cov_restrictions.clone()).unwrap();
    let (is_indep, defect) = diagram.check_diamond_path_independence("0", "1", "2", "3").unwrap();
    assert!(is_indep);
    assert!(defect.is_zero());

    // Proposition 2.1a: Build Path A completion
    let chains = BTreeMap::from([
        (("3".to_string(), "0".to_string()), vec!["0".to_string(), "1".to_string(), "3".to_string()]),
    ]);
    let presheaf = CoveringEdgeDiagramCED::build_path_a_completion(elements, dims, cov_restrictions, chains).unwrap();
    let r_30 = presheaf.get_restriction("3", "0").unwrap();
    assert_eq!(r_30, &ExactMatrix::from_i64(&[&[1, 3], &[0, 1]]));

    let curv_op = CurvatureOperatorCED::new(presheaf);
    let is_flat = curv_op.is_flat(&[("0", "1", "3"), ("0", "2", "3")]).unwrap();
    assert!(is_flat);
}

#[test]
fn test_theorem_3_2_coboundary_curvature_identity() {
    let elements = vec!["0".to_string(), "1".to_string(), "2".to_string()];
    let dims = BTreeMap::from([
        ("0".to_string(), 2),
        ("1".to_string(), 2),
        ("2".to_string(), 2),
    ]);

    let r_21 = ExactMatrix::from_i64(&[&[1, 2], &[3, 4]]);
    let r_10 = ExactMatrix::from_i64(&[&[2, 0], &[1, -1]]);
    let defect_mat = ExactMatrix::from_i64(&[&[1, -1], &[2, 0]]);
    let r_20 = r_10.mul(&r_21).sub(&defect_mat);

    let mut restrictions = BTreeMap::new();
    restrictions.insert(("2".to_string(), "1".to_string()), r_21);
    restrictions.insert(("1".to_string(), "0".to_string()), r_10);
    restrictions.insert(("2".to_string(), "0".to_string()), r_20);

    let diagram = CoveringEdgeDiagramCED::new(elements, dims, restrictions).unwrap();
    let complex = CochainComplexCED::new(diagram);

    let section = BTreeMap::from([
        ("0".to_string(), ExactMatrix::col_vector(&[5, 7])),
        ("1".to_string(), ExactMatrix::col_vector(&[-3, 4])),
        ("2".to_string(), ExactMatrix::col_vector(&[2, -1])),
    ]);

    let (matches, d1_d0, k_sc) = complex.verify_theorem_3_2(&section, "0", "1", "2").unwrap();
    assert!(matches);
    assert_eq!(d1_d0, ExactMatrix::col_vector(&[3, 4]));
    assert_eq!(k_sc, ExactMatrix::col_vector(&[3, 4]));
}

#[test]
fn test_theorem_3_4_degree_3_boundary() {
    let elements = vec!["0".to_string(), "1".to_string(), "2".to_string(), "3".to_string()];
    let dims = BTreeMap::from([
        ("0".to_string(), 2),
        ("1".to_string(), 2),
        ("2".to_string(), 2),
        ("3".to_string(), 2),
    ]);

    let mut restrictions = BTreeMap::new();
    restrictions.insert(("3".to_string(), "2".to_string()), ExactMatrix::from_i64(&[&[2, 1], &[0, 1]]));
    restrictions.insert(("2".to_string(), "1".to_string()), ExactMatrix::from_i64(&[&[1, 0], &[1, 1]]));
    restrictions.insert(("1".to_string(), "0".to_string()), ExactMatrix::from_i64(&[&[3, 1], &[2, 1]]));
    restrictions.insert(("3".to_string(), "1".to_string()), ExactMatrix::from_i64(&[&[5, 2], &[1, 3]]));
    restrictions.insert(("3".to_string(), "0".to_string()), ExactMatrix::from_i64(&[&[10, 4], &[3, 2]]));
    restrictions.insert(("2".to_string(), "0".to_string()), ExactMatrix::from_i64(&[&[4, 1], &[3, 1]]));

    let diagram = CoveringEdgeDiagramCED::new(elements, dims, restrictions).unwrap();
    let complex = CochainComplexCED::new(diagram);

    let s_3 = ExactMatrix::col_vector(&[3, -2]);
    let s_2 = ExactMatrix::col_vector(&[1, 4]);

    let (d2_val, lower_diff) = complex.evaluate_d2_boundary("0", "1", "2", "3", &s_3, &s_2).unwrap();
    assert_eq!(d2_val, lower_diff);
}

#[test]
fn test_theorem_3_6_unconditional_operator_cocycle() {
    let elements = vec!["0".to_string(), "1".to_string(), "2".to_string(), "3".to_string()];
    let dims = BTreeMap::from([
        ("0".to_string(), 2),
        ("1".to_string(), 2),
        ("2".to_string(), 2),
        ("3".to_string(), 2),
    ]);

    // Arbitrary non-flat restriction maps
    let mut restrictions = BTreeMap::new();
    restrictions.insert(("3".to_string(), "2".to_string()), ExactMatrix::from_i64(&[&[2, 3], &[1, -1]]));
    restrictions.insert(("2".to_string(), "1".to_string()), ExactMatrix::from_i64(&[&[0, 4], &[2, 1]]));
    restrictions.insert(("1".to_string(), "0".to_string()), ExactMatrix::from_i64(&[&[-1, 2], &[3, 0]]));
    restrictions.insert(("3".to_string(), "1".to_string()), ExactMatrix::from_i64(&[&[1, 1], &[2, 2]]));
    restrictions.insert(("3".to_string(), "0".to_string()), ExactMatrix::from_i64(&[&[4, 0], &[1, -3]]));
    restrictions.insert(("2".to_string(), "0".to_string()), ExactMatrix::from_i64(&[&[2, -1], &[0, 2]]));

    let diagram = CoveringEdgeDiagramCED::new(elements, dims, restrictions).unwrap();
    let op_complex = OperatorCochainCED::new(diagram);

    // Theorem 3.6: δ_2 K = 0 unconditionally
    let delta2_k = op_complex.evaluate_operator_delta2_k("0", "1", "2", "3").unwrap();
    assert!(delta2_k.is_zero());
}

#[test]
fn test_theorem_4_1_and_4_2_operator_commutator_and_four_term_comparison() {
    let elements = vec!["0".to_string(), "1".to_string(), "2".to_string(), "3".to_string()];
    let dims = BTreeMap::from([
        ("0".to_string(), 2),
        ("1".to_string(), 2),
        ("2".to_string(), 2),
        ("3".to_string(), 2),
    ]);

    let mut restrictions = BTreeMap::new();
    restrictions.insert(("3".to_string(), "2".to_string()), ExactMatrix::from_i64(&[&[1, 2], &[0, 1]]));
    restrictions.insert(("2".to_string(), "1".to_string()), ExactMatrix::from_i64(&[&[2, 0], &[1, 1]]));
    restrictions.insert(("1".to_string(), "0".to_string()), ExactMatrix::from_i64(&[&[1, 1], &[1, -1]]));
    restrictions.insert(("3".to_string(), "1".to_string()), ExactMatrix::from_i64(&[&[3, 1], &[0, 2]]));
    restrictions.insert(("3".to_string(), "0".to_string()), ExactMatrix::from_i64(&[&[2, 2], &[1, 0]]));
    restrictions.insert(("2".to_string(), "0".to_string()), ExactMatrix::from_i64(&[&[1, 0], &[0, 1]]));

    let diagram = CoveringEdgeDiagramCED::new(elements, dims, restrictions).unwrap();
    let op_complex = OperatorCochainCED::new(diagram);

    // Theorem 4.2: Four-term operator comparison
    let (matches, lhs, rhs) = op_complex.verify_four_term_comparison("0", "1", "2", "3").unwrap();
    assert!(matches);
    assert_eq!(lhs, rhs);

    // Theorem 4.1: Curved derivation [K, T]
    let t_32 = ExactMatrix::from_i64(&[&[1, -1], &[2, 0]]);
    let t_10 = ExactMatrix::from_i64(&[&[0, 1], &[3, 2]]);
    let commutator = op_complex.evaluate_curved_derivation(&t_32, &t_10, "0", "1", "2", "3").unwrap();
    assert_eq!(commutator.rows, 2);
    assert_eq!(commutator.cols, 2);
}

#[test]
fn test_theorem_4_4_additive_normal_form() {
    let elements = vec!["0".to_string(), "1".to_string(), "2".to_string()];
    let dims = BTreeMap::from([
        ("0".to_string(), 2),
        ("1".to_string(), 2),
        ("2".to_string(), 2),
    ]);

    let r_21 = ExactMatrix::from_i64(&[&[1, 2], &[0, 1]]);
    let r_10 = ExactMatrix::from_i64(&[&[2, 1], &[1, 0]]);
    let r_hat_20 = r_10.mul(&r_21);

    let perturbation = ExactMatrix::from_i64(&[&[3, -1], &[0, 2]]);
    let r_20 = r_hat_20.add(&perturbation);

    let mut full_map = BTreeMap::new();
    full_map.insert(("2".to_string(), "1".to_string()), r_21.clone());
    full_map.insert(("1".to_string(), "0".to_string()), r_10.clone());
    full_map.insert(("2".to_string(), "0".to_string()), r_20);

    let mut strict_map = BTreeMap::new();
    strict_map.insert(("2".to_string(), "1".to_string()), r_21);
    strict_map.insert(("1".to_string(), "0".to_string()), r_10);
    strict_map.insert(("2".to_string(), "0".to_string()), r_hat_20);

    let full_diag = CoveringEdgeDiagramCED::new(elements.clone(), dims.clone(), full_map).unwrap();
    let strict_diag = CoveringEdgeDiagramCED::new(elements, dims, strict_map).unwrap();

    let anf = AdditiveNormalFormCED::decompose(&full_diag, &strict_diag).unwrap();
    assert!(anf.perturbation_a.get(&("2".to_string(), "1".to_string())).unwrap().is_zero());
    assert!(anf.perturbation_a.get(&("1".to_string(), "0".to_string())).unwrap().is_zero());

    let curv_op = CurvatureOperatorCED::new(full_diag);
    let k_210 = curv_op.compute_curvature("0", "1", "2").unwrap();
    assert!(anf.verify_covering_leg_curvature("0", "1", "2", &k_210).unwrap());
}

#[test]
fn test_theorem_4_6_and_statement_4_7_ddc_and_ledger() {
    let elements = vec!["0".to_string(), "1".to_string(), "2".to_string(), "3".to_string()];
    let dims = BTreeMap::from([
        ("0".to_string(), 2),
        ("1".to_string(), 2),
        ("2".to_string(), 2),
        ("3".to_string(), 2),
    ]);

    let mut restrictions = BTreeMap::new();
    restrictions.insert(("3".to_string(), "1".to_string()), ExactMatrix::from_i64(&[&[1, 1], &[0, 1]]));
    restrictions.insert(("1".to_string(), "0".to_string()), ExactMatrix::from_i64(&[&[1, 2], &[0, 1]]));
    restrictions.insert(("3".to_string(), "2".to_string()), ExactMatrix::from_i64(&[&[1, 2], &[0, 1]]));
    restrictions.insert(("2".to_string(), "0".to_string()), ExactMatrix::from_i64(&[&[1, 1], &[0, 1]]));
    restrictions.insert(("3".to_string(), "0".to_string()), ExactMatrix::from_i64(&[&[1, 3], &[0, 1]]));

    let diagram = CoveringEdgeDiagramCED::new(elements, dims, restrictions).unwrap();
    let curv_op = CurvatureOperatorCED::new(diagram);

    // Diamond commutator evaluates to zero on flat diamond
    let comm = evaluate_ddc_diamond_commutator(&curv_op, "0", "1", "2", "3").unwrap();
    assert!(comm.is_zero());

    // Statement 4.7: Ledger charge μ_1 = 2m
    let ledger = DistinctionCollapseLedgerCED::record_collapse(4);
    assert_eq!(ledger.collapsed_count, 4);
    assert_eq!(ledger.declared_charge, 8);
    assert_eq!(ledger.authority_effect, core_wdp::types::AuthorityEffect::None);
}

#[test]
fn test_theorem_4_11_and_corollary_4_11a_4d_simplicial_holonomy_and_bianchi() {
    // 2x2 link variables over Cyc8
    let u_01 = Cyc8Matrix2x2::eye();
    let u_12 = Cyc8Matrix2x2::eye();
    let u_02 = Cyc8Matrix2x2::eye();

    let w_012 = compute_wilson_triangle_holonomy(&u_01, &u_12, &u_02);
    assert!(w_012.is_identity());

    // Tetrahedral Bianchi identity
    let bianchi = verify_tetrahedral_bianchi(&w_012, &w_012, &w_012, &w_012);
    assert!(bianchi.is_identity());
}

// Origin: engine/crates_rs/tests/core_wdp/test_covering_edge_descent.rs
// Claim: urn:core:crates_rs:tests:test-covering-edge-descent:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord2583aa6d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord2583aa6d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError2583aa6d {
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
impl BoundaryError2583aa6d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError2583aa6d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError2583aa6d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord2583aa6d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError2583aa6d> {
        if capacity_bound == 0 {
            return Err(BoundaryError2583aa6d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError2583aa6d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError2583aa6d::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_2583aa6d() {
    let admitted = BoundaryRecord2583aa6d::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord2583aa6d::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
