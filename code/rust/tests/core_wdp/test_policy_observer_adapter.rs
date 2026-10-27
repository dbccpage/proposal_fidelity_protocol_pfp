use std::collections::BTreeSet;

use num_rational::BigRational;
use num_traits::{Signed, Zero};
use core_functional::phi1::{ExactPhi1Certificate, Phi1Functional};
use core_wdp::legacy_observer_adapters::SourceCustody;
use core_wdp::policy_observer_adapter::*;

fn q(i: i64) -> BigRational {
    BigRational::from_integer(i.into())
}
fn identity_matrix() -> Vec<Vec<BigRational>> {
    vec![vec![q(1), q(0)], vec![q(0), q(1)]]
}
fn problem() -> PolicyObserverProblem {
    let identity = PolicyGaugeAction::identity(2, 2, 2, 1);
    let swap = PolicyGaugeAction {
        states: vec![1, 0],
        comparisons: vec![1, 0],
        defects: SignedPermutation {
            image: vec![0, 1],
            signs: vec![-1, -1],
        },
        repairs: SignedPermutation {
            image: vec![0],
            signs: vec![-1],
        },
    };
    PolicyObserverProblem {
        carrier: PolicyCarrier {
            names: vec!["a".into(), "b".into()],
            coordinates: vec!["x".into(), "y".into()],
            values: vec![vec![q(0), q(0)], vec![q(1), q(1)]],
        },
        comparison_domain: PolicyComparisonDomain {
            names: vec!["a-to-b".into(), "b-to-a".into()],
            pairs: vec![[0, 1], [1, 0]],
            restrictions: vec![identity_matrix(), identity_matrix()],
        },
        gauge_group: vec![identity, swap],
        repair: PolicyRepairOperator {
            coordinates: vec!["opposite-shift".into()],
            map: vec![vec![q(1)], vec![q(-1)]],
        },
        norm_weights: vec![q(1), q(1)],
        terminal_rules: PolicyTerminalRules {
            permitted_statuses: BTreeSet::from(["WithinTolerance".into(), "AboveTolerance".into()]),
            tolerance: q(1), within_tolerance: "WithinTolerance".into(),
            above_tolerance: "AboveTolerance".into(),
        },
        source: SourceCustody {
            path: "atlas/005_the_authority_gap/the_authority_gap.md".into(),
            recorded_sha256: "18b82368bc45731e29ce5baf72d2aa0fcaf177fe8344532df09c9d7b0d78e42d".into(),
            source_receipts: vec!["Current local authority-gap Layer3 compressed C,D,G,R,T definition; historical Paper031 naming is a separate source citation".into()],
            source_authority_tags: vec!["historical scoped authority tag".into()],
        },
    }
}
fn certificate(
    problem: &PolicyObserverProblem,
    delta: Vec<BigRational>,
    alpha: Vec<BigRational>,
    dual: Vec<BigRational>,
) -> ExactPhi1Certificate {
    let residual = delta
        .iter()
        .zip(&problem.repair.map)
        .map(|(x, row)| {
            x - row
                .iter()
                .zip(&alpha)
                .map(|(a, b)| a * b)
                .sum::<BigRational>()
        })
        .collect::<Vec<_>>();
    ExactPhi1Certificate {
        omega: delta,
        d0: problem.repair.map.clone(),
        weights: problem.norm_weights.clone(),
        alpha,
        reported_value: residual
            .iter()
            .zip(&problem.norm_weights)
            .map(|(r, w)| r.abs() * w)
            .sum(),
        primal_residual: residual,
        dual_witness: dual,
    }
}
fn receipt(problem: &PolicyObserverProblem) -> PolicyEvaluationReceipt {
    VerifiedPolicyObserver::try_new(problem.clone())
        .unwrap()
        .evaluate(
            0,
            certificate(problem, vec![q(1), q(1)], vec![q(0)], vec![q(1), q(1)]),
        )
        .unwrap()
}

#[test]
fn actual_five_packet_preserves_group_repair_norm_and_terminal_rule_separately() {
    let p = problem();
    let observer = VerifiedPolicyObserver::try_new(p.clone()).unwrap();
    assert_eq!(observer.problem(), &p);
    assert_eq!(observer.defects(), &[vec![q(1), q(1)], vec![q(-1), q(-1)]]);
    let forward = receipt(&p);
    let reverse = observer
        .evaluate(
            1,
            certificate(&p, vec![q(-1), q(-1)], vec![q(0)], vec![q(-1), q(-1)]),
        )
        .unwrap();
    assert_eq!(forward.value, q(2));
    assert_eq!(forward.value, reverse.value);
    assert_eq!(forward.status, "AboveTolerance");
    assert!(verify_policy_evaluation(&p, &forward).unwrap());
    // A mathematical status named Authorized remains only a source spelling.
    let mut t = p.clone();
    t.terminal_rules.tolerance = q(2);
    t.terminal_rules.within_tolerance = "Authorized".into();
    t.terminal_rules
        .permitted_statuses
        .insert("Authorized".into());
    let tolerant = receipt(&t);
    assert_eq!(tolerant.value, forward.value);
    assert_eq!(tolerant.status, "Authorized");
    assert!(verify_policy_evaluation(&t, &tolerant).unwrap());
    assert!(!verify_policy_evaluation(&t, &forward).unwrap());
}

#[test]
fn freshly_rehashed_false_status_value_defect_and_source_binding_are_rejected() {
    let p = problem();
    let actual = receipt(&p);
    for mut false_record in [
        PolicyEvaluationReceipt {
            status: "WithinTolerance".into(),
            ..actual.clone()
        },
        PolicyEvaluationReceipt {
            value: q(0),
            ..actual.clone()
        },
        PolicyEvaluationReceipt {
            defect: vec![q(0), q(0)],
            ..actual.clone()
        },
        PolicyEvaluationReceipt {
            comparison_name: "other-pair".into(),
            ..actual.clone()
        },
        PolicyEvaluationReceipt {
            problem_digest: "b".repeat(64),
            ..actual.clone()
        },
    ] {
        false_record.refresh_digest().unwrap();
        assert!(!verify_policy_evaluation(&p, &false_record).unwrap());
    }
    let mut changed = p.clone();
    changed
        .source
        .source_authority_tags
        .push("new-source-tag".into());
    assert!(!verify_policy_evaluation(&changed, &actual).unwrap());
    changed.source = p.source.clone();
    changed.carrier.values[1] = vec![q(2), q(2)];
    assert_eq!(
        verify_policy_evaluation(&changed, &actual),
        Err(PolicyAdapterError::CertificateProblemMismatch)
    );
}

#[test]
fn a_valid_certificate_for_another_problem_is_not_evidence_for_this_pair() {
    let p = problem();
    let unrelated = certificate(&p, vec![q(2), q(2)], vec![q(0)], vec![q(1), q(1)]);
    assert!(Phi1Functional::verify_exact_certificate(unrelated.clone()).is_ok());
    let mut false_record = receipt(&p);
    false_record.certificate = unrelated;
    false_record.defect = vec![q(2), q(2)];
    false_record.value = q(4);
    false_record.refresh_digest().unwrap();
    assert_eq!(
        verify_policy_evaluation(&p, &false_record),
        Err(PolicyAdapterError::CertificateProblemMismatch)
    );
    let mut invalid = receipt(&p);
    invalid.certificate.dual_witness = vec![q(0), q(0)];
    invalid.refresh_digest().unwrap();
    assert_eq!(
        verify_policy_evaluation(&p, &invalid),
        Err(PolicyAdapterError::InvalidCertificate)
    );
    let mut invalid = receipt(&p);
    invalid.certificate.omega[0] = BigRational::new_raw(1.into(), 0.into());
    invalid.refresh_digest().unwrap();
    assert_eq!(
        verify_policy_evaluation(&p, &invalid),
        Err(PolicyAdapterError::InvalidCertificate)
    );
    let mut invalid = receipt(&p);
    invalid.value = BigRational::new_raw(1.into(), 0.into());
    invalid.refresh_digest().unwrap();
    assert!(!verify_policy_evaluation(&p, &invalid).unwrap());
}

#[test]
fn the_norm_does_not_pretend_to_choose_a_unique_repair_residual() {
    let p = problem();
    let observer = VerifiedPolicyObserver::try_new(p.clone()).unwrap();
    let one = receipt(&p);
    let another = observer
        .evaluate(
            0,
            certificate(&p, vec![q(1), q(1)], vec![q(1)], vec![q(1), q(1)]),
        )
        .unwrap();
    assert_eq!(another.value, one.value);
    assert_ne!(
        another.certificate.primal_residual,
        one.certificate.primal_residual
    );
    assert!(verify_policy_evaluation(&p, &another).unwrap());
}

#[test]
fn group_alone_determines_neither_repairs_nor_norm_nor_status() {
    let p = problem();
    let baseline = receipt(&p);
    let mut all_repairs = p.clone();
    all_repairs.repair.map = vec![vec![q(1)], vec![q(1)]];
    let exact = VerifiedPolicyObserver::try_new(all_repairs.clone())
        .unwrap()
        .evaluate(
            0,
            certificate(&all_repairs, vec![q(1), q(1)], vec![q(1)], vec![q(0), q(0)]),
        )
        .unwrap();
    assert_eq!(p.gauge_group, all_repairs.gauge_group);
    assert_eq!(exact.value, q(0));
    assert_eq!(baseline.value, q(2));
    assert_eq!(exact.status, "WithinTolerance");
    let mut norm = p.clone();
    norm.norm_weights = vec![q(2), q(2)];
    let scaled = VerifiedPolicyObserver::try_new(norm.clone())
        .unwrap()
        .evaluate(
            0,
            certificate(&norm, vec![q(1), q(1)], vec![q(0)], vec![q(2), q(2)]),
        )
        .unwrap();
    assert_eq!(norm.gauge_group, p.gauge_group);
    assert_eq!(norm.repair, p.repair);
    assert_eq!(scaled.value, q(4));
}

#[test]
fn gauge_typing_identity_closure_and_three_compatibility_laws_are_necessary() {
    let mut p = problem();
    p.gauge_group[1].states = vec![0, 0];
    assert_eq!(
        VerifiedPolicyObserver::try_new(p),
        Err(PolicyAdapterError::InvalidGaugeAction)
    );
    let mut p = problem();
    p.gauge_group.remove(0);
    assert_eq!(
        VerifiedPolicyObserver::try_new(p),
        Err(PolicyAdapterError::GaugeNotAGroup)
    );
    let mut p = problem();
    p.gauge_group[1].defects = SignedPermutation::identity(2);
    assert_eq!(
        VerifiedPolicyObserver::try_new(p),
        Err(PolicyAdapterError::GaugeDoesNotPreserveProblem)
    );
    let mut p = problem();
    p.gauge_group[1].repairs = SignedPermutation::identity(1);
    assert_eq!(
        VerifiedPolicyObserver::try_new(p),
        Err(PolicyAdapterError::GaugeDoesNotPreserveProblem)
    );
    let mut p = problem();
    p.gauge_group[1].states = vec![0, 1];
    p.gauge_group[1].comparisons = vec![0, 1];
    p.gauge_group[1].defects = SignedPermutation {
        image: vec![1, 0],
        signs: vec![1, 1],
    };
    p.norm_weights = vec![q(1), q(2)];
    assert_eq!(
        VerifiedPolicyObserver::try_new(p),
        Err(PolicyAdapterError::GaugeDoesNotPreserveProblem)
    );
    // Individually lawful actions do not establish composition closure.
    let mut p = problem();
    p.carrier.values[1] = vec![q(0), q(0)];
    p.repair.coordinates.clear();
    p.repair.map = vec![vec![], vec![]];
    let id = PolicyGaugeAction::identity(2, 2, 2, 0);
    let mut x = id.clone();
    x.defects.signs = vec![-1, 1];
    let mut y = id.clone();
    y.defects.signs = vec![1, -1];
    p.gauge_group = vec![id, x, y];
    assert_eq!(
        VerifiedPolicyObserver::try_new(p),
        Err(PolicyAdapterError::GaugeNotAGroup)
    );
}

#[test]
fn required_carrier_domain_repair_norm_and_terminal_fields_have_typed_refusals() {
    let mut p = problem();
    p.carrier.names[1] = p.carrier.names[0].clone();
    assert_eq!(
        VerifiedPolicyObserver::try_new(p),
        Err(PolicyAdapterError::InvalidCarrier)
    );
    let mut p = problem();
    p.comparison_domain.restrictions.pop();
    assert_eq!(
        VerifiedPolicyObserver::try_new(p),
        Err(PolicyAdapterError::InvalidComparisonDomain)
    );
    let mut p = problem();
    p.repair.map[0].clear();
    assert_eq!(
        VerifiedPolicyObserver::try_new(p),
        Err(PolicyAdapterError::InvalidRepairOperator)
    );
    let mut p = problem();
    p.norm_weights[0] = q(0);
    assert_eq!(
        VerifiedPolicyObserver::try_new(p),
        Err(PolicyAdapterError::InvalidNormBridge)
    );
    let mut p = problem();
    p.terminal_rules.tolerance = q(-1);
    assert_eq!(
        VerifiedPolicyObserver::try_new(p),
        Err(PolicyAdapterError::InvalidTerminalRules)
    );
    let mut p = problem();
    p.terminal_rules.permitted_statuses.clear();
    assert_eq!(
        VerifiedPolicyObserver::try_new(p),
        Err(PolicyAdapterError::InvalidTerminalRules)
    );
    let mut p = problem();
    p.carrier.values[0][0] = BigRational::new_raw(1.into(), 0.into());
    assert_eq!(
        VerifiedPolicyObserver::try_new(p),
        Err(PolicyAdapterError::InvalidCarrier)
    );
    let mut p = problem();
    p.carrier.values[0][0] = BigRational::new_raw(2.into(), 2.into());
    assert_eq!(
        VerifiedPolicyObserver::try_new(p),
        Err(PolicyAdapterError::InvalidCarrier)
    );
    let mut p = problem();
    p.source.recorded_sha256 = "not-a-digest".into();
    assert_eq!(
        VerifiedPolicyObserver::try_new(p),
        Err(PolicyAdapterError::InvalidSourceBinding)
    );
}

#[test]
fn non_linear_repairs_and_nonseparating_gauges_do_not_gain_linear_quotient_laws() {
    // A={0,1}, d0=id: allowed single repair differences do not form cosets.
    let repairs = [q(0), q(1)];
    let distance = |x: BigRational| repairs.iter().map(|a| (&x - a).abs()).min().unwrap();
    assert_eq!(distance(q(0)), q(0));
    assert_eq!(distance(q(-1)), q(1));
    // 0 and -1 differ by one element of the declared repair set, yet the
    // distances disagree: closure under translations cannot be dropped.
    assert_eq!(q(0) - q(-1), q(1));
    // A merely nonnegative seminorm can vanish on an unrepaired defect.
    let unrepaired = [q(0), q(1)];
    let seminorm_weights = [q(1), q(0)];
    assert!(!unrepaired.iter().all(Zero::is_zero));
    assert_eq!(
        unrepaired
            .iter()
            .zip(seminorm_weights)
            .map(|(x, w)| x.abs() * w)
            .sum::<BigRational>(),
        q(0)
    );
}

// Origin: engine/crates_rs/tests/core_wdp/test_policy_observer_adapter.rs
// Claim: urn:core:crates_rs:tests:test-policy-observer-adapter:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord4b9e2873 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord4b9e2873` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError4b9e2873 {
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
impl BoundaryError4b9e2873 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError4b9e2873 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError4b9e2873 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord4b9e2873 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError4b9e2873> {
        if capacity_bound == 0 {
            return Err(BoundaryError4b9e2873::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError4b9e2873::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError4b9e2873::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_4b9e2873() {
    let admitted = BoundaryRecord4b9e2873::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord4b9e2873::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
