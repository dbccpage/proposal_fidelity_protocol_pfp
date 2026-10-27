//! Bounded WDP paper controls, integrated into the canonical Cargo workspace.
//! Each private module retains its declared carrier and refusal tests.
//! These are test fixtures, not production APIs or proofs of unrestricted claims.
#![allow(dead_code)]

#[path = "plan_wdp_math_premises.rs"]
mod plan_wdp_math_premises;

#[path = "prod_kernel.rs"]
mod prod_kernel;

#[path = "prod_kernel_kill.rs"]
mod prod_kernel_kill;

#[path = "prod_kernel_next_1.rs"]
mod prod_kernel_next_1;

#[path = "prod_kernel_next_2.rs"]
mod prod_kernel_next_2;

#[path = "../test_finite_routing.rs"]
mod prod_kernel_routing;

#[path = "prod_kernel_stub_1.rs"]
mod prod_kernel_stub_1;

#[path = "prod_p1.rs"]
mod prod_p1;

#[path = "prod_p1_kill.rs"]
mod prod_p1_kill;

#[path = "prod_p1_next_1.rs"]
mod prod_p1_next_1;

#[path = "prod_p1_next_2.rs"]
mod prod_p1_next_2;

#[path = "prod_p2.rs"]
mod prod_p2;

#[path = "prod_p2_kill.rs"]
mod prod_p2_kill;

#[path = "prod_p2_next_1.rs"]
mod prod_p2_next_1;

#[path = "prod_p2_next_2.rs"]
mod prod_p2_next_2;

#[path = "prod_p3.rs"]
mod prod_p3;

#[path = "prod_p3_kill.rs"]
mod prod_p3_kill;

#[path = "prod_p3_next_1.rs"]
mod prod_p3_next_1;

#[path = "prod_p3_next_2.rs"]
mod prod_p3_next_2;

#[path = "prod_p4.rs"]
mod prod_p4;

#[path = "prod_p4_kill.rs"]
mod prod_p4_kill;

#[path = "prod_p4_next_1.rs"]
mod prod_p4_next_1;

#[path = "prod_p4_next_2.rs"]
mod prod_p4_next_2;

#[path = "prod_p5.rs"]
mod prod_p5;

#[path = "prod_p5_kill.rs"]
mod prod_p5_kill;

#[path = "prod_p5_next_1.rs"]
mod prod_p5_next_1;

#[path = "prod_p5_next_2.rs"]
mod prod_p5_next_2;

#[path = "rev_smrm_p1_loss.rs"]
mod rev_smrm_p1_loss;

#[path = "rev_smrm_p1_quotient.rs"]
mod rev_smrm_p1_quotient;

#[path = "rev_smrm_p2_numeral.rs"]
mod rev_smrm_p2_numeral;

#[path = "rev_smrm_p3_mine.rs"]
mod rev_smrm_p3_mine;

#[path = "rev_smrm_p4_future.rs"]
mod rev_smrm_p4_future;

#[path = "wdp_21_16_fsp.rs"]
mod wdp_21_16_fsp;

#[path = "wdp_21_16_majorana.rs"]
mod wdp_21_16_majorana;

#[path = "wdp_21_16_mub6.rs"]
mod wdp_21_16_mub6;

#[path = "wdp_21_16_wdp.rs"]
mod wdp_21_16_wdp;

#[path = "wdp_appm_m4_remainder.rs"]
mod wdp_appm_m4_remainder;

#[path = "wdp_appm_t1.rs"]
mod wdp_appm_t1;

#[path = "wdp_appm_t2.rs"]
mod wdp_appm_t2;

#[path = "wdp_appm_t3.rs"]
mod wdp_appm_t3;

#[path = "wdp_appm_t4.rs"]
mod wdp_appm_t4;

#[path = "wdp_appw_all_m_inertia.rs"]
mod wdp_appw_all_m_inertia;

#[path = "wdp_appw_extinction_positivity.rs"]
mod wdp_appw_extinction_positivity;

#[path = "wdp_appw_gaussian_limits.rs"]
mod wdp_appw_gaussian_limits;

#[path = "wdp_appw_joint_spatial_reconstruction.rs"]
mod wdp_appw_joint_spatial_reconstruction;

#[path = "wdp_appw_uniform_volume.rs"]
mod wdp_appw_uniform_volume;

#[path = "wdp_appx_joint_support.rs"]
mod wdp_appx_joint_support;

#[path = "wdp_appx_report_domain.rs"]
mod wdp_appx_report_domain;

#[path = "wdp_ch17_semiring_classification.rs"]
mod wdp_ch17_semiring_classification;

#[path = "wdp_chs_o01.rs"]
mod wdp_chs_o01;

#[path = "wdp_chs_o02.rs"]
mod wdp_chs_o02;

#[path = "wdp_joint_continuum.rs"]
mod wdp_joint_continuum;

#[path = "wdp_o10_signed_measure_positivity.rs"]
mod wdp_o10_signed_measure_positivity;

#[path = "wdp_o12_real_time.rs"]
mod wdp_o12_real_time;

#[path = "wdp_o12_theta_above_1_128.rs"]
mod wdp_o12_theta_above_1_128;

#[path = "wdp_o12_xlm_comparison.rs"]
mod wdp_o12_xlm_comparison;

#[path = "wdp_o8_critical_scaling.rs"]
mod wdp_o8_critical_scaling;

#[path = "wdp_o8_susceptibility.rs"]
mod wdp_o8_susceptibility;

#[path = "wdp_repair_policy.rs"]
mod wdp_repair_policy;

#[path = "bridge_nc_identity.rs"]
mod bridge_nc_identity;

#[path = "bridge_wsc_nonselection.rs"]
mod bridge_wsc_nonselection;

#[path = "plan_qp_1.rs"]
mod plan_qp_1;

#[path = "plan_qp_2.rs"]
mod plan_qp_2;

#[path = "plan_qp_3.rs"]
mod plan_qp_3;

#[path = "plan_qp_4.rs"]
mod plan_qp_4;

#[path = "plan_qp_5.rs"]
mod plan_qp_5;

#[path = "plan_qp_6.rs"]
mod plan_qp_6;

#[path = "plan_qp_7.rs"]
mod plan_qp_7;

#[path = "plan_qp_8.rs"]
mod plan_qp_8;

#[path = "plan_qp_9.rs"]
mod plan_qp_9;

#[path = "plan_qp_10.rs"]
mod plan_qp_10;

#[path = "plan_qp_c1.rs"]
mod plan_qp_c1;

#[path = "plan_qp_c2.rs"]
mod plan_qp_c2;

#[path = "plan_qp_c3.rs"]
mod plan_qp_c3;

#[path = "plan_qp_c4.rs"]
mod plan_qp_c4;

#[path = "plan_qp_c5.rs"]
mod plan_qp_c5;

#[path = "plan_qp_c6.rs"]
mod plan_qp_c6;

#[path = "plan_qp_c7.rs"]
mod plan_qp_c7;

#[path = "plan_qp_c8.rs"]
mod plan_qp_c8;

#[path = "plan_qp_c9.rs"]
mod plan_qp_c9;

#[path = "bridge_closure_ratio_lower.rs"]
mod bridge_closure_ratio_lower;

#[path = "bridge_mub6_coverage.rs"]
mod bridge_mub6_coverage;

#[path = "plan_wdp_editorial.rs"]
mod plan_wdp_editorial;

#[path = "plan_wdp_review_closeout.rs"]
mod plan_wdp_review_closeout;

#[path = "plan_wdp_release_checks.rs"]
mod plan_wdp_release_checks;

#[path = "plan_7d_preflight.rs"]
mod plan_7d_preflight;

#[path = "plan_7d_next_2.rs"]
mod plan_7d_next_2;

#[path = "plan_7d_day_3.rs"]
mod plan_7d_day_3;

#[path = "plan_7d_day_4.rs"]
mod plan_7d_day_4;

#[path = "sg_40.rs"]
mod sg_40;

#[path = "sg_48.rs"]
mod sg_48;

#[path = "plan_7d_next_3.rs"]
mod plan_7d_next_3;

#[path = "plan_7d_day_5.rs"]
mod plan_7d_day_5;

#[path = "plan_7d_day_6.rs"]
mod plan_7d_day_6;

#[path = "plan_7d_day_7.rs"]
mod plan_7d_day_7;

#[path = "wf_research_bind_oewas.rs"]
mod wf_research_bind_oewas;

#[path = "wf_research_bind_prompts.rs"]
mod wf_research_bind_prompts;

#[path = "wf_research_bind_runner.rs"]
mod wf_research_bind_runner;

#[path = "wf_research_bind_hosts.rs"]
mod wf_research_bind_hosts;

#[path = "wf_research_bind_oeeis.rs"]
mod wf_research_bind_oeeis;
mod wdp_dp4_03;
mod wdp_dp7_03;
mod wdp_p2a_residual;
mod wdp_dp2_01_residual;
mod wdp_dp6_01_residual;
mod wdp_dp8_01_residual;
mod wdp_appm_t5;
mod wdp_appw_native_repair_bindings;
mod wdp_appx_cost_formalization;
mod wdp_ch23_next_test;
mod wdp_chs_o03;
mod wdp_dp1_02_residual;
mod wdp_dp4_02_residual;
mod wdp_o12_lean_analytic;
mod wdp_21_8_lean_extension;
mod ch19_o04;
mod dec_wdp_repin;
mod ms_release;
mod plan_odm_guarded_open;
mod gen_wdp_o02;
mod gen_wdp_o03;
mod gen_wdp_o04;
mod gen_wdp_o05;
mod wdp_appm_field_theory_route;
mod doc_five_4_general;
mod doc_msl_g2;
mod doc_msl_g3;
mod doc_msl_g4;
mod doc_msl_g5;
mod doc_msl_spacetime_limit;
mod plan_7d_csq_character_classification;
mod plan_7d_csq_pontryagin;
mod plan_odm_4;
mod plan_odm_6;
mod plan_odm_6_pr426;
mod plan_odm_9_open;
mod plan_odm_10_open;
mod plan_odm_11;
mod plan_odm_14_open;
mod plan_odm_17_open;
mod plan_odm_observer_open;
mod plan_odm_progress_open;
mod plan_odm_quotient_open;
mod plan_odm_retention_open;
mod plan_odm_reuse_open;
mod plan_odm_faithful_open;
mod plan_odm_coda_prime;
mod po001_native_transport;
mod ms_po001_residual;
mod plan_7d_pfp50_catalog;
mod plan_7d_pfp25_catalog;
mod plan_7d_sg_catalog;
mod plan_odm_pfp_interventions;

// --- exact carrier witness ---
use std::collections::BTreeSet;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ControlDagError {
    Shape,
    Edge,
    Cycle,
    Budget { longest: u32 },
    Overflow,
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/mod.rs
// Claim: urn:core:crates_rs:tests:mod:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ControlDagError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ControlDagError {}

/// An acyclic control graph whose longest path fits an integer budget.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ControlDagBudget {
    nodes: usize,
    longest: u32,
}

impl ControlDagBudget {
    fn build_graph(
        nodes: usize,
        edges: &[(usize, usize)],
    ) -> Result<(Vec<u32>, Vec<Vec<usize>>), ControlDagError> {
        let mut seen = BTreeSet::new();
        let mut indegree = vec![0u32; nodes];
        let mut adjacent = vec![Vec::<usize>::new(); nodes];
        for &(from, to) in edges {
            if from >= nodes || to >= nodes || from == to || !seen.insert((from, to)) {
                return Err(ControlDagError::Edge);
            }
            indegree[to] = indegree[to].checked_add(1).ok_or(ControlDagError::Overflow)?;
            adjacent[from].push(to);
        }
        Ok((indegree, adjacent))
    }

    fn topological_order(
        nodes: usize,
        mut indegree: Vec<u32>,
        adjacent: &[Vec<usize>],
    ) -> Result<Vec<usize>, ControlDagError> {
        let mut queue: Vec<usize> = (0..nodes).filter(|&node| indegree[node] == 0).collect();
        let mut order = Vec::new();
        let mut cursor = 0usize;
        while cursor < queue.len() {
            let node = queue[cursor];
            cursor += 1;
            order.push(node);
            for &child in &adjacent[node] {
                indegree[child] -= 1;
                if indegree[child] == 0 {
                    queue.push(child);
                }
            }
        }
        if order.len() != nodes {
            return Err(ControlDagError::Cycle);
        }
        Ok(order)
    }

    fn longest_path(
        nodes: usize,
        order: &[usize],
        adjacent: &[Vec<usize>],
    ) -> Result<u32, ControlDagError> {
        let mut distance = vec![0u32; nodes];
        let mut longest = 0u32;
        for &node in order {
            let next = distance[node].checked_add(1).ok_or(ControlDagError::Overflow)?;
            for &child in &adjacent[node] {
                distance[child] = distance[child].max(next);
                longest = longest.max(next);
            }
        }
        Ok(longest)
    }

    pub fn try_new(nodes: usize, edges: &[(usize, usize)], budget: u32) -> Result<Self, ControlDagError> {
        if nodes == 0 || nodes > 32 {
            return Err(ControlDagError::Shape);
        }
        let (indegree, adjacent) = Self::build_graph(nodes, edges)?;
        let order = Self::topological_order(nodes, indegree, &adjacent)?;
        let longest = Self::longest_path(nodes, &order, &adjacent)?;
        if longest > budget {
            return Err(ControlDagError::Budget { longest });
        }
        Ok(Self { nodes, longest })
    }

    pub fn nodes(&self) -> usize { self.nodes }
    pub fn longest(&self) -> u32 { self.longest }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod control_dag_tests {
    use super::*;

    #[test]
    fn a_path_of_two_edges_fits_budget_two() {
        let dag = ControlDagBudget::try_new(3, &[(0, 1), (1, 2)], 2);
        assert!(matches!(dag, Ok(ref dag) if dag.nodes() == 3 && dag.longest() == 2));
    }

    #[test]
    fn a_two_cycle_is_refused() {
        let dag = ControlDagBudget::try_new(2, &[(0, 1), (1, 0)], 2);
        assert!(matches!(dag, Err(ControlDagError::Cycle)));
    }
}
