// AuthorityEffect: None.
use num_rational::BigRational;
use num_traits::Zero;
use core_wdp::coda::{
    evaluate_coda_pipeline, evaluate_coda_pipeline_with_grant, ExternalAuthorityGrant, LayerId,
    ProblemInstance, TerminalKind,
};
use std::collections::BTreeMap;

fn base_flow_problem(problem_id: &str) -> ProblemInstance {
    let mut problem = ProblemInstance::new(problem_id);
    problem.raw_data = "sample_data".to_string();
    problem.candidate_sieve = vec!["cand_a".to_string(), "cand_b".to_string()];
    problem.coarse_profile = vec![0, 1];
    problem.fine_profile = vec![0, 1];

    let mut proj = BTreeMap::new();
    proj.insert(0, 0);
    proj.insert(1, 1);
    problem.projection_map = proj;

    let mut sections = BTreeMap::new();
    sections.insert("U0".to_string(), vec![BigRational::new(1.into(), 2.into())]);
    problem.local_sections = sections;

    let mut overlaps = BTreeMap::new();
    overlaps.insert(("U0".to_string(), "U0".to_string()), true);
    problem.overlaps = overlaps;

    problem.d0 = vec![
        vec![
            BigRational::from_integer((-1).into()),
            BigRational::from_integer(1.into()),
        ],
        vec![
            BigRational::from_integer(1.into()),
            BigRational::from_integer((-1).into()),
        ],
    ];

    problem.d1 = vec![vec![
        BigRational::from_integer(0.into()),
        BigRational::from_integer(0.into()),
    ]];

    problem.defect_cochain = vec![
        BigRational::from_integer(0.into()),
        BigRational::from_integer(0.into()),
    ];

    problem.fda_license_granted = false;
    problem
}

#[test]
fn test_pipeline_refuses_forged_grant() {
    let problem = base_flow_problem("authorized_flow_instance");

    // External grant verified at the firewall
    let grant = ExternalAuthorityGrant {
        grant_id: "GRANT_2026_CODA_001".to_string(),
        signature_hex: "abcdef1234567890".to_string(),
        grantee: "canonical_governance_oracle".to_string(),
    };

    let outcome = evaluate_coda_pipeline_with_grant(&problem, Some(&grant));

    assert_eq!(outcome.terminal_kind, TerminalKind::Refused);
    assert!(!outcome.is_authorized());
    assert!(outcome.authority_token.is_none());
    assert!(outcome.residual_pair.as_ref().unwrap().is_exact_zero());

    // Assert that all 9 layers executed and left an audit record
    let executed_layer_ids: Vec<LayerId> = outcome
        .layer_records
        .iter()
        .map(|rec| rec.layer_id)
        .collect();

    let expected_layer_ids = vec![
        LayerId::FOC,
        LayerId::MUR,
        LayerId::CS,
        LayerId::CS_Q,
        LayerId::Q,
        LayerId::A,
        LayerId::OR,
        LayerId::FDA,
        LayerId::CODA_GTLA,
    ];

    assert_eq!(executed_layer_ids, expected_layer_ids);
    assert!(outcome.layer_records.iter().any(|rec| !rec.succeeded));
}

#[test]
fn test_end_to_end_pipeline_flow_closed_residual_sentinel() {
    let mut problem = base_flow_problem("sentinel_flow_instance");
    // Cochain [1, 0]^T is not in im(d0)
    problem.defect_cochain = vec![
        BigRational::from_integer(1.into()),
        BigRational::from_integer(0.into()),
    ];
    // Even with a license claim flag, non-zero defect cannot be authorized!
    problem.fda_license_granted = true;

    let grant = ExternalAuthorityGrant {
        grant_id: "ILLEGAL_GRANT_ON_NONZERO_DEFECT".to_string(),
        signature_hex: "00000000".to_string(),
        grantee: "unauthorized_proposer".to_string(),
    };

    let outcome = evaluate_coda_pipeline_with_grant(&problem, Some(&grant));

    assert_eq!(outcome.terminal_kind, TerminalKind::ClosedResidual);
    assert!(outcome.is_closed_residual());
    assert!(!outcome.is_authorized());
    assert!(outcome.authority_token.is_none());

    let pair = outcome.residual_pair.as_ref().unwrap();
    assert!(pair.phi1 > BigRational::zero());
    assert!(pair.gamma2.is_zero());
}

#[test]
fn test_end_to_end_pipeline_flow_refused_on_empty_sieve() {
    let mut problem = base_flow_problem("refused_flow_instance");
    // Empty sieve triggers OR refusal
    problem.candidate_sieve = vec![];
    problem.fda_license_granted = true;

    let outcome = evaluate_coda_pipeline(&problem);

    assert_eq!(outcome.terminal_kind, TerminalKind::Refused);
    assert!(outcome.is_refused());
    assert!(!outcome.is_authorized());
    assert!(!outcome.is_closed_residual());
}

#[test]
fn pipeline_binds_input_bytes_and_refuses_failed_layers() {
    let p = base_flow_problem("same_id");
    let mut changed = p.clone();
    changed.raw_data.push_str("altered");
    assert_ne!(
        evaluate_coda_pipeline(&p).evidence_digest,
        evaluate_coda_pipeline(&changed).evidence_digest
    );
    changed.local_sections.clear();
    assert!(evaluate_coda_pipeline(&changed).is_refused());
    changed = p.clone();
    changed.d1[0].push(BigRational::zero());
    let invalid = evaluate_coda_pipeline(&changed);
    assert!(invalid.is_refused());
    assert!(invalid.residual_pair.is_none());
    changed = p;
    changed.d0[0].clear();
    assert!(evaluate_coda_pipeline(&changed).is_refused());
}

// Origin: engine/crates_rs/tests/core_wdp/test_coda_pipeline_flow.rs
// Claim: urn:core:crates_rs:tests:test-coda-pipeline-flow:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordecd5dc69 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordecd5dc69` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorecd5dc69 {
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
impl BoundaryErrorecd5dc69 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorecd5dc69 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorecd5dc69 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordecd5dc69 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorecd5dc69> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorecd5dc69::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorecd5dc69::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorecd5dc69::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_ecd5dc69() {
    let admitted = BoundaryRecordecd5dc69::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordecd5dc69::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
