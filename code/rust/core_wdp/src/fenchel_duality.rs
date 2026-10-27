// Executable finite evidence; AuthorityEffect: None.
//! Lp-Native Cohomology & Exact Fenchel-Rockafellar Duality Solvers.
//!
//! Grounded in FOC-007 ("Lp-Native Cohomology") & FOC-037 ("L1 Obstruction Framework"):
//! - Primal: weighted L1 coboundary quotient min_phi sum_e c_e |omega_e - (d_0 phi)_e|
//! - Dual: circulation psi in ker(d_0^*) with capacity bounds |psi_e| <= c_e
//! - Zero duality gap: <omega, psi> == ||[omega]||_{1, c} over exact rationals
//! - Complementary slackness: active edges force capacity saturation psi_e = c_e * sgn(residual_e).
//!
//! The primal-dual pair is solved and replayed by `core_solvers::solver_lp_phi1_quotient`
//! on the incidence matrix of `core_homology::graph_carrier`. A receipt exists
//! only around a `VerifiedExactPhi1`, whose verifier has already checked that
//! psi is divergence-free, within capacity, and pairs with omega to the primal value.

use num_rational::BigRational;
use num_traits::Signed;
use core_functional::l1_seminorm::L1Seminorm;
use core_functional::phi1::VerifiedExactPhi1;
use core_solvers::solver_lp_phi1_quotient::solve_exact_phi1;
use serde::{Deserialize, Serialize};

use crate::cochains::{coboundary_rows, named_graph_carrier};
use crate::error::WdpError;
use crate::types::AuthorityEffect;

/// Edge saturation status under complementary slackness.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum EdgeSaturationStatus {
    SaturatedPositive, // residual > 0, psi_e == c_e
    SaturatedNegative, // residual < 0, psi_e == -c_e
    GaugeInactive,     // residual == 0, |psi_e| <= c_e
}

/// Verification receipt for exact Fenchel-Rockafellar duality.
///
/// The primal value, optimal potential (in `WeightedComplex::vertices` order)
/// and dual circulation (in edge order) are read from [`Self::phi1`].
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FenchelDualityReceipt {
    phi1: VerifiedExactPhi1,
    edge_statuses: Vec<EdgeSaturationStatus>,
    authority_effect: AuthorityEffect,
}

impl FenchelDualityReceipt {
    pub fn phi1(&self) -> &VerifiedExactPhi1 {
        &self.phi1
    }

    pub fn edge_statuses(&self) -> &[EdgeSaturationStatus] {
        &self.edge_statuses
    }

    pub fn authority_effect(&self) -> AuthorityEffect {
        self.authority_effect
    }
}

/// Weighted cell complex for Fenchel-Rockafellar duality solvers.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct WeightedComplex {
    pub vertices: Vec<String>,
    pub edges: Vec<(String, String)>,
    pub capacities: Vec<BigRational>, // positive rational edge weights c_e > 0
    pub authority_effect: AuthorityEffect,
}

impl WeightedComplex {
    pub fn new(
        vertices: Vec<String>,
        edges: Vec<(String, String)>,
        capacities: Vec<BigRational>,
    ) -> Self {
        assert_eq!(
            edges.len(),
            capacities.len(),
            "Each edge must have a capacity"
        );
        for c in &capacities {
            assert!(c.is_positive(), "Capacities must be strictly positive");
        }
        Self {
            vertices,
            edges,
            capacities,
            authority_effect: AuthorityEffect::None,
        }
    }

    /// The weighted L1 quotient `C^1 / im(d_0)` on this complex.
    pub fn l1_quotient_presentation(&self) -> Result<L1Seminorm, WdpError> {
        let carrier = named_graph_carrier(
            &self.vertices,
            &self.edges,
            &[],
            self.capacities.clone(),
            "core_wdp::WeightedComplex",
        )?;
        Ok(L1Seminorm::new(
            coboundary_rows(carrier.d0()),
            carrier.weights().to_vec(),
        )?)
    }

    /// Solves the exact rational Fenchel-Rockafellar primal-dual pair.
    pub fn solve_fenchel_duality(
        &self,
        omega: &[BigRational],
    ) -> Result<FenchelDualityReceipt, WdpError> {
        let phi1 = solve_exact_phi1(&self.l1_quotient_presentation()?, omega)?;

        let edge_statuses = phi1
            .dual_witness()
            .iter()
            .zip(&self.capacities)
            .map(|(psi_e, cap)| {
                if psi_e == cap {
                    EdgeSaturationStatus::SaturatedPositive
                } else if *psi_e == -cap {
                    EdgeSaturationStatus::SaturatedNegative
                } else {
                    EdgeSaturationStatus::GaugeInactive
                }
            })
            .collect();

        Ok(FenchelDualityReceipt {
            phi1,
            edge_statuses,
            authority_effect: AuthorityEffect::None,
        })
    }
}

// Origin: engine/crates_rs/core_wdp/src/fenchel_duality.rs
// Claim: urn:core:crates_rs:core-wdp:fenchel-duality:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use num_traits::Zero;
    use core_functional::phi1::Phi1Functional;
    use core_homology::scalar::q;

    #[test]
    fn test_fenchel_rockafellar_zero_duality_gap_triangle() {
        let vertices = vec!["0".to_string(), "1".to_string(), "2".to_string()];
        let edges = vec![
            ("0".to_string(), "1".to_string()),
            ("1".to_string(), "2".to_string()),
            ("0".to_string(), "2".to_string()),
        ];
        let capacities = vec![q(1), q(1), q(1)];
        let complex = WeightedComplex::new(vertices, edges, capacities);

        // Coboundary input (zero defect)
        let exact_omega = vec![q(2), q(3), q(5)];
        let receipt1 = complex.solve_fenchel_duality(&exact_omega).unwrap();
        assert!(receipt1.phi1().value().is_zero());
        assert_eq!(receipt1.authority_effect(), AuthorityEffect::None);

        // Non-trivial circulation defect
        let cycle_omega = vec![q(1), q(1), q(0)];
        let receipt2 = complex.solve_fenchel_duality(&cycle_omega).unwrap();
        assert_eq!(receipt2.phi1().value(), &q(2));
        // Circulation 2 on unit capacities saturates every edge of the cycle.
        assert!(receipt2
            .edge_statuses()
            .iter()
            .all(|status| *status != EdgeSaturationStatus::GaugeInactive));

        // Zero duality gap and a divergence-free, capacity-bounded dual: the
        // shared verifier replays both receipts' witnesses independently.
        for receipt in [receipt1, receipt2] {
            let replayed =
                Phi1Functional::verify_exact_certificate(receipt.phi1().certificate().clone())
                    .unwrap();
            assert_eq!(replayed.value(), receipt.phi1().value());
        }
    }
}
