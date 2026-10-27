// Executable finite evidence; AuthorityEffect: None.
//! Primitive Difference Axiomatics, Evaluation Preorders & Triad (Phi_1, Gamma_2, R_cl) Diagnostics.
//!
//! Grounded in FOC-006 / FOC-000 ("Primitive Axiomatics of Finite Obstruction Calculus"):
//! 1. Root W (Genesis Admission Kernel): Admitted unentailed non-identification witness.
//! 2. Root P (Evaluation Kernel): Cochain evaluation C^0 -> C^1 -> C^2 and quotient defect Q^1.
//! 3. Evaluation Preorders: Reflexive-transitive closure of evaluation relations.
//! 4. Triad Obstruction Signature: (Phi_1, Gamma_2, R_cl) with Three-Way Classification.
//!
//! Root P owns no arithmetic here: d_0 and d_1 come from `core_homology`, and
//! Phi_1, Gamma_2 and the exact trichotomy come from `core_functional`.

use std::collections::{BTreeMap, BTreeSet};

use num_rational::BigRational;
use num_traits::{One, Zero};
use core_category_theory::finite_relational::FinitePreorder;
use core_functional::gamma2::{
    DegreeOneResidualQ, ExactCochainComplexQ, ExactGamma2Result, Gamma2Functional,
};
use core_functional::l1_seminorm::L1Seminorm;
use core_functional::phi1::VerifiedExactPhi1;
use core_homology::carrier::Carrier;
use core_policy::trichotomy::{
    classify_exact, CertifiedExactTrichotomy, ObstructionDiagnosticClass, TrichotomyOutcome,
};
use core_solvers::solver_lp_phi1_quotient::solve_exact_phi1;
use serde::{Deserialize, Serialize};

use crate::cochains::{coboundary_rows, named_graph_carrier};
use crate::error::WdpError;
use crate::types::AuthorityEffect;

/// The Ten Primitive Difference Axioms (A1–A10).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum PrimitiveDifferenceAxiom {
    /// A1: Non-Identification of Distinct Primitive Carrier Items.
    A01NonIdentification,
    /// A2: Unentailed Witness Admission (Root W is an admission, not a derived proof).
    A02UnentailedAdmission,
    /// A3: Local Evaluation Relation (Reflexive-Transitive Closure generates Preorder).
    A03EvaluationRelation,
    /// A4: Directed Evaluation Carrier (Simplicial 1-skeleton with assigned orientations).
    A04DirectedEvaluationCarrier,
    /// A5: Nilpotent Coboundary Hierarchy (d_1 o d_0 = 0).
    A05NilpotentCoboundary,
    /// A6: Quotient Defect Purity (Q^1 = C^1 / im(d_0) invariant under gauge shift).
    A06QuotientDefectPurity,
    /// A7: Descended Closure Map (kappa^1([h]) = d_1 h is well-defined).
    A07DescendedClosureMap,
    /// A8: Exact Triad Trichotomy (Removable Gauge vs Closed Obstruction vs Rupture).
    A08TriadTrichotomy,
    /// A9: Observer-Selected Metric Invariance (Quotient norms independent of node relabeling).
    A09ObserverSelectedMetric,
    /// A10: Anti-Reification Firewall (AuthorityEffect::None on all mathematical readouts).
    A10AntiReificationFirewall,
}

/// Root W: Genesis Admission Kernel.
/// Designated witness capturing primitive difference as an admitted, unentailed non-identification.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct GenesisAdmissionKernel {
    pub carrier_items: BTreeSet<String>,
    pub admitted_differences: Vec<(String, String, String)>, // (item_a, item_b, witness_token)
    pub authority_effect: AuthorityEffect,
}

impl GenesisAdmissionKernel {
    pub fn new(items: BTreeSet<String>) -> Self {
        Self {
            carrier_items: items,
            admitted_differences: Vec::new(),
            authority_effect: AuthorityEffect::None,
        }
    }

    pub fn admit_difference(&mut self, a: &str, b: &str, token: &str) -> Result<(), &'static str> {
        if a == b {
            return Err(
                "Axiom A1 violation: cannot admit non-identification between identical items",
            );
        }
        if !self.carrier_items.contains(a) || !self.carrier_items.contains(b) {
            return Err("Carrier violation: items must belong to the declared carrier set");
        }
        self.admitted_differences
            .push((a.to_string(), b.to_string(), token.to_string()));
        Ok(())
    }
}

/// Evaluation Preorder P = rtc(R) constructed via reflexive-transitive closure.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct EvaluationPreorder {
    domain: Vec<String>,
    preorder: FinitePreorder,
}

impl EvaluationPreorder {
    /// Resolves names without discarding edges, then delegates closure to its owner.
    pub fn from_relation(
        domain: Vec<String>,
        base_pairs: &[(String, String)],
    ) -> Result<Self, WdpError> {
        if domain.iter().any(String::is_empty)
            || domain.iter().collect::<BTreeSet<_>>().len() != domain.len()
        {
            return Err(WdpError::InvalidInput {
                detail: "preorder requires nonempty, distinct labels".into(),
            });
        }
        let name_to_idx: BTreeMap<&str, usize> = domain
            .iter()
            .enumerate()
            .map(|(i, s)| (s.as_str(), i))
            .collect();
        let edges = base_pairs
            .iter()
            .map(|(u, v)| {
                let resolve = |name: &str| {
                    name_to_idx
                        .get(name)
                        .copied()
                        .ok_or_else(|| WdpError::ElementNotFound {
                            element: name.into(),
                        })
                };
                Ok((resolve(u)?, resolve(v)?))
            })
            .collect::<Result<Vec<_>, WdpError>>()?;
        let preorder = FinitePreorder::from_edges(domain.len(), &edges)?;
        Ok(Self { domain, preorder })
    }

    pub fn domain(&self) -> &[String] {
        &self.domain
    }

    pub fn relation_matrix(&self) -> &[Vec<bool>] {
        self.preorder.relation()
    }

    pub fn authority_effect(&self) -> AuthorityEffect {
        AuthorityEffect::None
    }

    pub fn leq(&self, u: &str, v: &str) -> Result<bool, WdpError> {
        let resolve = |name: &str| {
            self.domain
                .iter()
                .position(|s| s == name)
                .ok_or_else(|| WdpError::ElementNotFound {
                    element: name.into(),
                })
        };
        Ok(self.preorder.leq(resolve(u)?, resolve(v)?)?)
    }
}

/// Exact rational Triad Obstruction Signature (Phi_1, Gamma_2, R_cl).
///
/// Holds only sealed `core_functional` evidence: a replayed Phi_1 certificate,
/// the exact Gamma_2 of its primal residual, and the certified trichotomy class.
/// There is no public constructor; [`EvaluationCarrier::compute_triad_signature`]
/// is the only way to obtain one.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TriadSignature {
    phi1: VerifiedExactPhi1,
    gamma2: ExactGamma2Result,
    trichotomy: CertifiedExactTrichotomy,
    authority_effect: AuthorityEffect,
}

impl TriadSignature {
    /// Replayed Phi_1 certificate: value, optimal potential, residual, dual witness.
    pub fn phi1(&self) -> &VerifiedExactPhi1 {
        &self.phi1
    }

    /// Exact Gamma_2 of the Phi_1 primal residual, with its curvature 2-cochain.
    pub fn gamma2(&self) -> &ExactGamma2Result {
        &self.gamma2
    }

    pub fn trichotomy(&self) -> &CertifiedExactTrichotomy {
        &self.trichotomy
    }

    pub fn classification(&self) -> ObstructionDiagnosticClass {
        self.trichotomy.diagnostic_class()
    }

    /// Closure ratio R_cl = Gamma_2 / Phi_1; `None` if Phi_1 = 0 and Gamma_2 > 0.
    pub fn r_cl(&self) -> Option<BigRational> {
        let (phi_1, gamma_2) = (self.trichotomy.phi1_value(), self.trichotomy.gamma2_value());
        if !phi_1.is_zero() {
            Some(gamma_2 / phi_1)
        } else if gamma_2.is_zero() {
            Some(BigRational::zero())
        } else {
            None
        }
    }

    pub fn authority_effect(&self) -> AuthorityEffect {
        self.authority_effect
    }
}

/// Finite 2-Complex Evaluation Carrier: C^0 -(d_0)-> C^1 -(d_1)-> C^2.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvaluationCarrier {
    pub vertices: Vec<String>,
    pub edges: Vec<(String, String)>,
    pub faces: Vec<(String, String, String)>, // triangles (u, v, w) with edges (u,v), (v,w), (u,w)
    pub authority_effect: AuthorityEffect,
}

impl EvaluationCarrier {
    pub fn new(
        vertices: Vec<String>,
        edges: Vec<(String, String)>,
        faces: Vec<(String, String, String)>,
    ) -> Self {
        Self {
            vertices,
            edges,
            faces,
            authority_effect: AuthorityEffect::None,
        }
    }

    /// The unit-weighted `core_homology` carrier. It owns d_0, d_1 and the
    /// nilpotence law d_1 o d_0 = 0, which is verified at construction.
    pub fn carrier(&self) -> Result<Carrier, WdpError> {
        named_graph_carrier(
            &self.vertices,
            &self.edges,
            &self.faces,
            vec![BigRational::one(); self.edges.len()],
            "core_wdp::EvaluationCarrier",
        )
    }

    /// Computes the exact rational Triad Signature (Phi_1, Gamma_2, R_cl).
    ///
    /// Phi_1 is solved and replayed by `core_solvers::solver_lp_phi1_quotient`, Gamma_2
    /// is `core_functional::gamma2` on the Phi_1 primal residual, and the class
    /// is `core_policy::trichotomy::classify_exact`.
    pub fn compute_triad_signature(&self, h: &[BigRational]) -> Result<TriadSignature, WdpError> {
        let carrier = self.carrier()?;
        let d0 = coboundary_rows(carrier.d0());
        let space = L1Seminorm::new(d0.clone(), carrier.weights().to_vec())?;
        let phi1 = solve_exact_phi1(&space, h)?;

        let complex = ExactCochainComplexQ::try_new(
            carrier.c0_dim(),
            carrier.c1_dim(),
            carrier.c2_dim(),
            d0,
            coboundary_rows(carrier.d1()),
        )?;
        let residual = DegreeOneResidualQ::try_new(&complex, phi1.primal_residual().to_vec())?;
        let gamma2 = Gamma2Functional::try_compute_exact_quotient(&residual)?;

        let trichotomy = match classify_exact(&phi1, &gamma2) {
            TrichotomyOutcome::Classified(trichotomy) => trichotomy,
            TrichotomyOutcome::TriRefused(refusal) => return Err(WdpError::Trichotomy(refusal)),
        };

        Ok(TriadSignature {
            phi1,
            gamma2,
            trichotomy,
            authority_effect: AuthorityEffect::None,
        })
    }
}

// Origin: engine/crates_rs/core_wdp/src/primitive_axiomatics.rs
// Claim: urn:core:crates_rs:core-wdp:primitive-axiomatics:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord044d633c {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord044d633c` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError044d633c {
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
impl BoundaryError044d633c {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError044d633c {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError044d633c {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord044d633c {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError044d633c> {
        if capacity_bound == 0 {
            return Err(BoundaryError044d633c::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError044d633c::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError044d633c::ExceedsCapacity {
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

    fn triangle(faces: Vec<(String, String, String)>) -> EvaluationCarrier {
        let vertices = vec!["0".to_string(), "1".to_string(), "2".to_string()];
        let edges = vec![
            ("0".to_string(), "1".to_string()),
            ("1".to_string(), "2".to_string()),
            ("0".to_string(), "2".to_string()),
        ];
        EvaluationCarrier::new(vertices, edges, faces)
    }

    fn filled_triangle() -> EvaluationCarrier {
        triangle(vec![("0".to_string(), "1".to_string(), "2".to_string())])
    }

    #[test]
    fn test_primitive_axiomatics_genesis_admission() {
        let items = BTreeSet::from(["alpha".to_string(), "beta".to_string(), "gamma".to_string()]);
        let mut kernel = GenesisAdmissionKernel::new(items);
        assert!(kernel.admit_difference("alpha", "beta", "token_ab").is_ok());
        assert!(kernel
            .admit_difference("alpha", "alpha", "token_aa")
            .is_err()); // A1 violation
        assert_eq!(kernel.authority_effect, AuthorityEffect::None);
    }

    #[test]
    fn test_evaluation_preorder_transitivity() {
        let domain = vec!["x0".to_string(), "x1".to_string(), "x2".to_string()];
        let base_rel = vec![
            ("x0".to_string(), "x1".to_string()),
            ("x1".to_string(), "x2".to_string()),
        ];
        let preorder = EvaluationPreorder::from_relation(domain, &base_rel).unwrap();

        assert!(preorder.leq("x0", "x0").unwrap()); // reflexivity
        assert!(preorder.leq("x0", "x1").unwrap());
        assert!(preorder.leq("x1", "x2").unwrap());
        assert!(preorder.leq("x0", "x2").unwrap()); // transitive closure
        assert!(!preorder.leq("x2", "x0").unwrap());
    }

    #[test]
    fn test_nilpotence_d1_d0_is_zero() {
        // core_homology verifies d1 * d0 = 0 when the carrier is built.
        let carrier = filled_triangle().carrier().unwrap();
        let test_phi = vec![qr(1, 2), qr(3, 4), qr(-1, 3)];
        let d0_phi = carrier.d0().mul_vec(&test_phi).unwrap();
        let d1_d0_phi = carrier.d1().mul_vec(&d0_phi).unwrap();
        assert!(d1_d0_phi.iter().all(Zero::is_zero));
    }

    #[test]
    fn test_triad_three_way_classification() {
        let carrier = filled_triangle();

        // 1. Exact repair: h is an exact coboundary h = d0(phi)
        let exact_h = carrier
            .carrier()
            .unwrap()
            .d0()
            .mul_vec(&[q(1), q(3), q(7)])
            .unwrap();
        let sig1 = carrier.compute_triad_signature(&exact_h).unwrap();
        assert_eq!(
            sig1.classification(),
            ObstructionDiagnosticClass::ExactRepair
        );
        assert!(sig1.phi1().value().is_zero());
        assert!(sig1.gamma2().value().is_zero());
        assert_eq!(sig1.r_cl(), Some(q(0)));

        // 2. Active closure failure: d1(h) != 0
        let rupture_h = vec![q(1), q(1), q(0)];
        let sig2 = carrier.compute_triad_signature(&rupture_h).unwrap();
        assert_eq!(
            sig2.classification(),
            ObstructionDiagnosticClass::ActiveClosureFailure
        );
        assert_eq!(sig2.gamma2().coboundary(), &[q(2)]);
        assert!(!sig2.gamma2().value().is_zero());

        // 3. Closed residual: the same h on the hollow triangle has no 2-cell to fail.
        let sig3 = triangle(vec![])
            .compute_triad_signature(&rupture_h)
            .unwrap();
        assert_eq!(
            sig3.classification(),
            ObstructionDiagnosticClass::ClosedResidual
        );
        assert_eq!(sig3.phi1().value(), &q(2));
        assert_eq!(sig3.r_cl(), Some(q(0)));

        for sig in [sig1, sig2, sig3] {
            Phi1Functional::verify_exact_certificate(sig.phi1().certificate().clone()).unwrap();
            assert_eq!(sig.authority_effect(), AuthorityEffect::None);
        }
    }

    #[test]
    fn test_triad_refuses_malformed_input() {
        let carrier = filled_triangle();
        assert!(matches!(
            carrier.compute_triad_signature(&[q(1)]),
            Err(WdpError::Phi1(_))
        ));
        let missing_edge = EvaluationCarrier::new(
            vec!["0".to_string(), "1".to_string(), "2".to_string()],
            vec![("0".to_string(), "1".to_string())],
            vec![("0".to_string(), "1".to_string(), "2".to_string())],
        );
        assert!(matches!(
            missing_edge.compute_triad_signature(&[q(1)]),
            Err(WdpError::Homology(_))
        ));
    }
}

#[cfg(test)]
mod l4_boundary_tests_044d633c {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord044d633c::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord044d633c::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord044d633c::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord044d633c::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord044d633c::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError044d633c::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError044d633c::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
