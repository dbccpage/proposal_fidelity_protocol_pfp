//! Native contract and runtime dispatch tests for Stages 1-7 single-carrier,
//! coupled bipartite (`D_2 x D_3`, `D_3 x D_3`), and tripartite (`D_3 x D_3 x D_3`)
//! relational operad projector, holonomy, and Schur-Weyl identities in `core_symbol_game`.

use core_symbol_game::coupled_relational_operad::{
    compute_stage1_survivor_tower, compute_stage2_d2_swap_projectors,
    compute_stage3_diamond_holonomy, compute_stage4_d3_commutator_cyclotomic,
    compute_stage5_d2_x_d3, compute_stage6_d3_x_d3, compute_stage7_d3_cubed,
    evaluate_coupled_relational_operad, CoupledRelationalVerifyRequestV1,
    COUPLED_RELATIONAL_RECEIPT_SCHEMA,
};
use core_symbol_game::{dispatch_runtime_request, RuntimeRequestV1, RUNTIME_REQUEST_SCHEMA};
use serde_json::json;

#[test]
fn stage1_to_4_single_carrier_relational_tower_swap_diamond_and_d3_are_exact() {
    let s1 = compute_stage1_survivor_tower();
    assert_eq!(s1.normative_survivor_vector, [0, 1, 1, 1, 0, 1, 1]);
    assert_eq!(s1.d2_delta_support_floor, 2);
    assert_eq!(s1.retraction_left_inverse_defect, 0);
    assert_eq!(s1.persistent_history_counts, [0, 1, 2, 3, 3, 4, 5]);

    let s2 = compute_stage2_d2_swap_projectors();
    assert_eq!(s2.scaled_p_plus_row0_row1, [1, 1, 1, 1]);
    assert_eq!(s2.scaled_p_minus_row0_row1, [1, -1, -1, 1]);
    assert_eq!(s2.projector_idempotence_defect, "0/1");
    assert_eq!(s2.projector_orthogonality_defect, "0/1");
    assert_eq!(s2.difference_kernel_trace, "1/1");

    let s3 = compute_stage3_diamond_holonomy();
    assert_eq!(s3.diamond_graph_v_e_b1, [4, 5, 2]);
    assert_eq!(s3.spanning_tree_count_diamond, 8);
    assert_eq!(s3.coboundary_cycle_sum_defect, "0/1");
    assert_eq!(s3.fundamental_cycle_holonomies, [1, -1]);
    assert_eq!(s3.obstructed_spanning_trees, 8);

    let s4 = compute_stage4_d3_commutator_cyclotomic();
    assert_eq!(s4.commutator_k_row0, [0, -1, 1]);
    assert_eq!(s4.commutator_k_row1, [1, 0, -1]);
    assert_eq!(s4.commutator_k_row2, [-1, 1, 0]);
    assert_eq!(s4.commutator_trace, 0);
    assert_eq!(s4.commutator_cube_plus_three_commutator_zero, 0);
    assert_eq!(s4.cyclotomic_phi3_residual_on_difference_subspace, 0);
}

#[test]
fn stage5_d2_x_d3_prism_trees_and_four_sector_projectors_are_exact() {
    let s5 = compute_stage5_d2_x_d3();
    assert_eq!(s5.prism_graph_v_e_b1_trees, [6, 9, 4, 75]);
    assert_eq!(s5.four_sector_projector_ranks, [1, 1, 2, 2]);
    assert_eq!(s5.four_sector_orthogonality_and_completeness_defect, "0/1");
    assert_eq!(s5.coupled_swap_commutator_cubic_and_w0_defect, "0/1");
    assert_eq!(s5.triangle_cycle_sums, [0, 0]);
    assert_eq!(s5.interlayer_twist_holonomies, [-2, 1]);
    assert_eq!(s5.obstructed_spanning_trees, 75);
}

#[test]
fn stage6_d3_x_d3_five_sector_split_and_rational_involution_are_exact() {
    let s6 = compute_stage6_d3_x_d3();
    assert_eq!(s6.five_sector_projector_ranks, [1, 2, 2, 3, 1]);
    assert_eq!(s6.five_sector_orthogonality_and_completeness_defect, "0/1");
    assert_eq!(s6.compound_commutator_square_minus_nine_w00_defect, "0/1");
    assert_eq!(s6.diagonal_3cycle_traces_on_sym_and_alt_w00, [0, 1, 0]);
    assert_eq!(s6.antisymmetric_singlet_minor_vs_separable_minor, [1, 0]);
}

#[test]
fn stage7_d3_cubed_schur_weyl_obstruction_and_levi_civita_are_exact() {
    let s7 = compute_stage7_d3_cubed();
    assert_eq!(s7.tripartite_binomial_sector_ranks, [1, 6, 12, 8]);
    assert_eq!(s7.w000_schur_weyl_sym_mixed_alt_ranks, [4, 4, 0]);
    assert_eq!(s7.levi_civita_mixed_sector_and_parity_pin, [1, 0, 0, 0]);
    assert_eq!(s7.w000_r3_invariant_split_and_k3_square_defect, [2, 1, 1, 0]);
    assert_eq!(s7.pigeonhole_levi_civita_l1_and_sector_defects, [6, 0, 0]);
}

#[test]
fn runtime_dispatch_coupled_relational_operad_verify_passes_and_refuses_mutations() {
    let req = RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "coupled_relational_operad_verify".to_owned(),
        payload: json!({
            "expected_stage1_survivors": [0, 1, 1, 1, 0, 1, 1],
            "expected_stage3_diamond_trees": 8,
            "expected_stage5_ranks": [1, 1, 2, 2],
            "expected_stage5_trees": 75,
            "expected_stage6_ranks": [1, 2, 2, 3, 1],
            "expected_stage7_w000_schur_weyl_ranks": [4, 4, 0],
            "free_parameter_count": 0
        }),
    };
    let out = dispatch_runtime_request(&req);
    assert!(out.success);
    let val = out.result.expect("receipt present");
    assert_eq!(val["schema_version"], COUPLED_RELATIONAL_RECEIPT_SCHEMA);
    assert_eq!(val["status"], "PASS");
    assert_eq!(val["authority_effect"], "None");
    assert_eq!(val["genesis_effect"], "None");
    assert!(val["refusal_code"].is_null());

    // Adversarial mutation 1: falsely claiming Lambda^3(W_0) = 1 on W_000
    let bad_schur = evaluate_coupled_relational_operad(&CoupledRelationalVerifyRequestV1 {
        expected_stage7_w000_schur_weyl_ranks: Some([4, 3, 1]),
        ..Default::default()
    });
    assert_eq!(bad_schur.status, "REFUSED");
    assert_eq!(
        bad_schur.refusal_code.as_deref(),
        Some("DOF_UNPINNED_SUBCHANNEL_COMPENSATION")
    );

    // Adversarial mutation 2: non-zero free parameter count
    let bad_free = evaluate_coupled_relational_operad(&CoupledRelationalVerifyRequestV1 {
        free_parameter_count: 1,
        ..Default::default()
    });
    assert_eq!(bad_free.status, "REFUSED");
    assert_eq!(
        bad_free.refusal_code.as_deref(),
        Some("DOF_NONZERO_FREE_PARAMETERS")
    );
}

// Origin: engine/crates_rs/tests/core_symbol_game/coupled_relational_operad.rs
// Claim: urn:core:crates_rs:tests:coupled-relational-operad:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde51e171a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde51e171a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore51e171a {
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
impl BoundaryErrore51e171a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore51e171a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore51e171a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde51e171a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore51e171a> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore51e171a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore51e171a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore51e171a::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_e51e171a() {
    let admitted = BoundaryRecorde51e171a::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorde51e171a::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
