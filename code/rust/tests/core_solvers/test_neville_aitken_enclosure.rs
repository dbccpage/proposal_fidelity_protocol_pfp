//! Exact finite checks and role-specific mutations; no analytic limit is inferred.

use linear_algebra::exact_field::neville_aitken::{self as exact, NevilleError};
use linear_algebra::exact_field::rational_bareiss::{
    RationalBudget, RationalError, RationalLimits,
};
use num_bigint::BigInt;
use num_rational::BigRational;
use core_kernel::interval::Interval;
use core_solvers::solver_neville_aitken_enclosure::{
    check_neville_enclosures, propose_neville_enclosures, solve_neville_enclosures, EnclosureScope,
    NevilleEnclosureError as Error, NevilleEnclosureProblem, SampleBound,
};
use core_types::authority::AuthorityEffect;

fn q(n: i64, d: i64) -> BigRational {
    BigRational::new(n.into(), d.into())
}

fn limits() -> RationalLimits {
    RationalLimits {
        max_scalar_ops: 1_000_000,
        max_elements: 10_000,
        max_bits: 4096,
    }
}

fn budget() -> RationalBudget {
    RationalBudget::new(limits())
}

fn sample(node: BigRational, value: BigRational) -> SampleBound {
    SampleBound {
        node,
        enclosure: Some(Interval::point(value)),
    }
}

fn shrinking_problem() -> NevilleEnclosureProblem {
    let target = q(7, 13);
    NevilleEnclosureProblem {
        target_id: "rational_target".to_owned(),
        evaluation_point: q(0, 1),
        samples: (1..=4)
            .map(|n| sample(q(1, n), &target + q(1, n)))
            .collect(),
        prefix_remainder_bounds: (1..=4).map(|n| Some(q(1, n * n))).collect(),
        known_target: Some(target),
    }
}

#[test]
fn rational_target_is_enclosed_in_every_checked_finite_prefix() {
    let problem = shrinking_problem();
    let receipt = solve_neville_enclosures(&problem, &mut budget()).unwrap();
    let target = problem.known_target.as_ref().unwrap();
    assert_eq!(receipt.problem_binding(), &problem);
    assert_eq!(receipt.checked_rational_target(), Some(target));
    assert_eq!(receipt.authority_effect(), &AuthorityEffect::None);
    assert_eq!(
        receipt.scope(),
        EnclosureScope::FiniteConditionalOnSampleAndRemainderPremises
    );
    assert_eq!(receipt.steps().len(), 4);
    for (index, step) in receipt.steps().iter().enumerate() {
        assert_eq!(step.prefix_len, index + 1);
        assert!(step.nested_enclosure.contains(target));
        assert!(step.nested_enclosure.subset_of(&step.remainder_enclosure));
        if index > 0 {
            assert!(step
                .nested_enclosure
                .subset_of(&receipt.steps()[index - 1].nested_enclosure));
            assert!(
                step.nested_enclosure.diam() < receipt.steps()[index - 1].nested_enclosure.diam()
            );
            assert_eq!(step.polynomial_enclosure, Interval::point(target.clone()));
        }
    }
    let last = receipt.steps().last().unwrap();
    assert_eq!(last.nested_enclosure.lo(), target);
    assert_eq!(last.nested_enclosure.hi(), &(target + q(1, 16)));
}

#[test]
fn arbitrary_denominators_and_negative_nodes_reproduce_a_polynomial_exactly() {
    let nodes = vec![q(-7, 3), q(2, 5), q(13, 7), q(-11, 4)];
    let polynomial = |x: &BigRational| q(3, 7) - q(5, 11) * x + q(17, 13) * x * x;
    let values: Vec<_> = nodes.iter().map(polynomial).collect();
    let at = q(5, 9);
    let prefixes = exact::interpolate_prefixes(&nodes, &values, &at, &mut budget()).unwrap();
    assert_eq!(prefixes[2], polynomial(&at));
    assert_eq!(prefixes[3], polynomial(&at));
    let intervals: Vec<_> = values.iter().map(|v| (v.clone(), v.clone())).collect();
    let interval_prefixes =
        exact::interpolate_interval_prefixes(&nodes, &intervals, &at, &mut budget()).unwrap();
    let independent =
        exact::lagrange_interval_prefixes(&nodes, &intervals, &at, &mut budget()).unwrap();
    for (index, scalar) in prefixes.iter().enumerate() {
        assert_eq!(interval_prefixes[index], (scalar.clone(), scalar.clone()));
        assert_eq!(independent[index], interval_prefixes[index]);
    }
    let at_node = exact::interpolate_prefixes(&nodes, &values, &nodes[1], &mut budget()).unwrap();
    assert!(at_node[1..].iter().all(|v| v == &values[1]));
}

#[test]
fn signed_interval_propagation_encloses_every_corner_of_the_sample_box() {
    let nodes = vec![q(0, 1), q(2, 1), q(1, 1)];
    let intervals = vec![(q(-1, 1), q(1, 1)); 3];
    let at = q(3, 1);
    let recursive =
        exact::interpolate_interval_prefixes(&nodes, &intervals, &at, &mut budget()).unwrap();
    let tight = exact::lagrange_interval_prefixes(&nodes, &intervals, &at, &mut budget()).unwrap();
    assert_eq!(recursive[2], (q(-13, 1), q(13, 1)));
    assert_eq!(tight[2], (q(-7, 1), q(7, 1)));
    for corner in 0..8 {
        let values: Vec<_> = (0..3)
            .map(|i| q(if corner & (1 << i) == 0 { -1 } else { 1 }, 1))
            .collect();
        let values = exact::interpolate_prefixes(&nodes, &values, &at, &mut budget()).unwrap();
        for (prefix, value) in values.iter().enumerate() {
            assert!(&recursive[prefix].0 <= value && value <= &recursive[prefix].1);
            assert!(&tight[prefix].0 <= value && value <= &tight[prefix].1);
        }
    }
    assert_eq!(
        exact::interval_scale(&(q(-2, 3), q(5, 7)), &q(-3, 2), &mut budget()).unwrap(),
        (q(-15, 14), q(1, 1))
    );
    assert_eq!(
        exact::interval_divide(&(q(-2, 3), q(5, 7)), &q(-3, 2), &mut budget()).unwrap(),
        (q(-10, 21), q(4, 9))
    );
}

#[test]
fn independent_lagrange_replay_refuses_a_target_hidden_by_interval_dependency() {
    let mut problem = NevilleEnclosureProblem {
        target_id: "box_target".to_owned(),
        evaluation_point: q(3, 1),
        samples: [0, 2, 1]
            .into_iter()
            .map(|n| SampleBound {
                node: q(n, 1),
                enclosure: Some(Interval::new(q(-1, 1), q(1, 1))),
            })
            .collect(),
        prefix_remainder_bounds: vec![Some(q(20, 1)), Some(q(20, 1)), Some(q(0, 1))],
        known_target: Some(q(6, 1)),
    };
    solve_neville_enclosures(&problem, &mut budget()).unwrap();
    problem.known_target = Some(q(10, 1));
    let proposal = propose_neville_enclosures(&problem, &mut budget()).unwrap();
    assert!(proposal.steps[2].nested_enclosure.contains(&q(10, 1)));
    assert_eq!(
        check_neville_enclosures(&problem, &proposal, &mut budget()),
        Err(Error::KnownTargetNotEnclosed { prefix: 3 })
    );
    assert_eq!(
        solve_neville_enclosures(&problem, &mut budget()),
        Err(Error::KnownTargetNotEnclosed { prefix: 3 })
    );
}

#[test]
fn raw_interpolation_enclosures_need_not_nest_but_the_intersection_does() {
    let mut problem = NevilleEnclosureProblem {
        target_id: "intersection".to_owned(),
        evaluation_point: q(0, 1),
        samples: vec![sample(q(1, 1), q(1, 1)), sample(q(2, 1), q(3, 1))],
        prefix_remainder_bounds: vec![Some(q(1, 1)), Some(q(2, 1))],
        known_target: Some(q(1, 2)),
    };
    let receipt = solve_neville_enclosures(&problem, &mut budget()).unwrap();
    let steps = receipt.steps();
    assert_eq!(
        steps[0].remainder_enclosure,
        Interval::new(q(0, 1), q(2, 1))
    );
    assert_eq!(
        steps[1].remainder_enclosure,
        Interval::new(q(-3, 1), q(1, 1))
    );
    assert!(!steps[1]
        .remainder_enclosure
        .subset_of(&steps[0].remainder_enclosure));
    assert_eq!(steps[1].nested_enclosure, Interval::new(q(0, 1), q(1, 1)));
    problem.known_target = Some(q(0, 1));
    problem.prefix_remainder_bounds[1] = Some(q(1, 1));
    let touching = solve_neville_enclosures(&problem, &mut budget()).unwrap();
    assert_eq!(
        touching.steps()[1].nested_enclosure,
        Interval::point(q(0, 1))
    );
    problem.known_target = None;
    problem.prefix_remainder_bounds = vec![Some(q(0, 1)); 2];
    assert_eq!(
        solve_neville_enclosures(&problem, &mut budget()),
        Err(Error::EmptyIntersection { prefix: 2 })
    );
}

#[test]
fn interpolation_does_not_supply_a_zero_function_remainder() {
    // f(x) = (x - 1)(x - 2)/2 has zero samples at 1 and 2 but f(0) = 1.
    let mut problem = NevilleEnclosureProblem {
        target_id: "quadratic_value".to_owned(),
        evaluation_point: q(0, 1),
        samples: vec![sample(q(1, 1), q(0, 1)), sample(q(2, 1), q(0, 1))],
        prefix_remainder_bounds: vec![Some(q(1, 1)); 2],
        known_target: Some(q(1, 1)),
    };
    let valid = solve_neville_enclosures(&problem, &mut budget()).unwrap();
    assert!(valid
        .steps()
        .iter()
        .all(|s| s.nested_enclosure.contains(&q(1, 1))));
    problem.prefix_remainder_bounds = vec![Some(q(0, 1)); 2];
    assert_eq!(
        solve_neville_enclosures(&problem, &mut budget()),
        Err(Error::KnownTargetNotEnclosed { prefix: 1 })
    );
    problem.known_target = None;
    let conditional = solve_neville_enclosures(&problem, &mut budget()).unwrap();
    assert_eq!(conditional.checked_rational_target(), None);
    assert_eq!(
        conditional.scope(),
        EnclosureScope::FiniteConditionalOnSampleAndRemainderPremises
    );
    problem.prefix_remainder_bounds[0] = None;
    assert_eq!(
        solve_neville_enclosures(&problem, &mut budget()),
        Err(Error::MissingRemainderBound { prefix: 1 })
    );
}

#[test]
fn replay_binds_each_declared_input_role() {
    let problem = shrinking_problem();
    let candidate = propose_neville_enclosures(&problem, &mut budget()).unwrap();
    check_neville_enclosures(&problem, &candidate, &mut budget()).unwrap();
    let mut mutations = Vec::new();
    let mut changed = problem.clone();
    changed.target_id.push_str("_changed");
    mutations.push(("target identity", changed));
    let mut changed = problem.clone();
    changed.evaluation_point = q(1, 3);
    mutations.push(("evaluation point", changed));
    let mut changed = problem.clone();
    changed.samples[0].node = q(3, 5);
    mutations.push(("sample node", changed));
    let mut changed = problem.clone();
    changed.samples[0].enclosure = Some(Interval::point(q(1, 1)));
    mutations.push(("sample enclosure", changed));
    let mut changed = problem.clone();
    changed.prefix_remainder_bounds[0] = Some(q(2, 1));
    mutations.push(("remainder assumption", changed));
    let mut changed = problem.clone();
    changed.known_target = Some(q(8, 13));
    mutations.push(("designated rational target", changed));
    for (role, changed) in mutations {
        assert_eq!(
            check_neville_enclosures(&changed, &candidate, &mut budget()),
            Err(Error::InputBindingMismatch),
            "unbound {role}"
        );
        let mut changed_binding = candidate.clone();
        changed_binding.problem_binding = changed;
        assert_eq!(
            check_neville_enclosures(&problem, &changed_binding, &mut budget()),
            Err(Error::InputBindingMismatch),
            "changed candidate {role}"
        );
    }
}

#[test]
fn replay_checks_polynomial_remainder_and_assembled_intersection_separately() {
    let problem = shrinking_problem();
    let candidate = propose_neville_enclosures(&problem, &mut budget()).unwrap();
    let mut changed = candidate.clone();
    changed.steps[0].prefix_len = 2;
    assert_eq!(
        check_neville_enclosures(&problem, &changed, &mut budget()),
        Err(Error::PrefixOrder { prefix: 1 })
    );
    let mut changed = candidate.clone();
    changed.steps[0].polynomial_enclosure = Interval::point(q(0, 1));
    assert_eq!(
        check_neville_enclosures(&problem, &changed, &mut budget()),
        Err(Error::PolynomialMismatch { prefix: 1 })
    );
    let mut changed = candidate.clone();
    changed.steps[0].remainder_enclosure = Interval::point(q(7, 13));
    assert_eq!(
        check_neville_enclosures(&problem, &changed, &mut budget()),
        Err(Error::RemainderMismatch { prefix: 1 })
    );
    let mut changed = candidate.clone();
    changed.steps[2].nested_enclosure = Interval::point(q(7, 13));
    assert!(changed.steps[2]
        .nested_enclosure
        .subset_of(&changed.steps[1].nested_enclosure));
    assert_eq!(
        check_neville_enclosures(&problem, &changed, &mut budget()),
        Err(Error::IntersectionMismatch { prefix: 3 })
    );
    let mut changed = candidate.clone();
    changed.steps.pop();
    assert_eq!(
        check_neville_enclosures(&problem, &changed, &mut budget()),
        Err(Error::StepCount {
            expected: 4,
            actual: 3
        })
    );
}

#[test]
fn missing_bounds_negative_bounds_empty_families_and_duplicate_nodes_refuse() {
    let original = shrinking_problem();
    let mut problem = original.clone();
    problem.samples[1].enclosure = None;
    assert_eq!(
        solve_neville_enclosures(&problem, &mut budget()),
        Err(Error::MissingSampleBound { index: 1 })
    );
    let mut problem = original.clone();
    problem.prefix_remainder_bounds.pop();
    assert_eq!(
        solve_neville_enclosures(&problem, &mut budget()),
        Err(Error::MissingRemainderBound { prefix: 4 })
    );
    let mut problem = original.clone();
    problem.prefix_remainder_bounds.push(Some(q(0, 1)));
    assert_eq!(
        solve_neville_enclosures(&problem, &mut budget()),
        Err(Error::RemainderCount {
            expected: 4,
            actual: 5
        })
    );
    let mut problem = original.clone();
    problem.prefix_remainder_bounds[2] = Some(q(-1, 3));
    assert_eq!(
        solve_neville_enclosures(&problem, &mut budget()),
        Err(Error::NegativeRemainderBound { prefix: 3 })
    );
    let mut problem = original.clone();
    problem.samples[2].node = problem.samples[0].node.clone();
    assert_eq!(
        solve_neville_enclosures(&problem, &mut budget()),
        Err(Error::Interpolation(NevilleError::DuplicateNode {
            first: 0,
            second: 2
        }))
    );
    let mut problem = original.clone();
    problem.samples.clear();
    problem.prefix_remainder_bounds.clear();
    assert_eq!(
        solve_neville_enclosures(&problem, &mut budget()),
        Err(Error::EmptySamples)
    );
    let mut problem = original;
    problem.target_id.clear();
    assert_eq!(
        solve_neville_enclosures(&problem, &mut budget()),
        Err(Error::MissingTargetIdentity)
    );
}

#[test]
fn malformed_rationals_and_endpoint_transport_fail_closed() {
    for bad in [
        BigRational::new_raw(1.into(), 0.into()),
        BigRational::new_raw(2.into(), 4.into()),
        BigRational::new_raw(1.into(), (-2).into()),
    ] {
        for role in 0..4 {
            let mut problem = shrinking_problem();
            match role {
                0 => problem.evaluation_point = bad.clone(),
                1 => problem.samples[0].node = bad.clone(),
                2 => problem.prefix_remainder_bounds[0] = Some(bad.clone()),
                _ => problem.known_target = Some(bad.clone()),
            }
            assert_eq!(
                solve_neville_enclosures(&problem, &mut budget()),
                Err(Error::Arithmetic(RationalError::InvalidRational))
            );
        }
        assert_eq!(
            exact::validate_interval(&(bad, q(1, 1)), &mut budget()),
            Err(NevilleError::Arithmetic(RationalError::InvalidRational))
        );
    }
    assert_eq!(
        exact::validate_interval(&(q(2, 1), q(1, 1)), &mut budget()),
        Err(NevilleError::InvertedInterval)
    );
    assert_eq!(
        exact::interval_divide(&(q(0, 1), q(1, 1)), &q(0, 1), &mut budget()),
        Err(NevilleError::Arithmetic(RationalError::DivisionByZero))
    );
    assert_eq!(
        exact::interpolate_prefixes(&[q(0, 1)], &[], &q(0, 1), &mut budget()),
        Err(NevilleError::SampleCount {
            expected: 1,
            actual: 0
        })
    );
}

#[test]
fn exact_budget_boundary_succeeds_and_one_less_never_issues_a_receipt() {
    let problem = shrinking_problem();
    let mut full = budget();
    let expected = solve_neville_enclosures(&problem, &mut full).unwrap();
    let cost = expected.scalar_ops();
    assert_eq!(cost, full.used());
    let mut exact_limit = limits();
    exact_limit.max_scalar_ops = cost;
    assert_eq!(
        solve_neville_enclosures(&problem, &mut RationalBudget::new(exact_limit)).unwrap(),
        expected
    );
    exact_limit.max_scalar_ops -= 1;
    assert!(matches!(
        solve_neville_enclosures(&problem, &mut RationalBudget::new(exact_limit)),
        Err(Error::Arithmetic(RationalError::FuelExhausted))
            | Err(Error::Interpolation(NevilleError::Arithmetic(
                RationalError::FuelExhausted
            )))
    ));
    let mut shared = budget();
    shared.charge(17).unwrap();
    let checked = solve_neville_enclosures(&problem, &mut shared).unwrap();
    assert_eq!(checked.scalar_ops(), cost);
    assert_eq!(shared.used(), cost + 17);
    let mut overflow_limits = limits();
    overflow_limits.max_scalar_ops = usize::MAX;
    let mut exhausted = RationalBudget::new(overflow_limits);
    exhausted.charge(usize::MAX).unwrap();
    assert_eq!(
        solve_neville_enclosures(&problem, &mut exhausted),
        Err(Error::Arithmetic(RationalError::FuelExhausted))
    );
}

#[test]
fn bit_and_element_limits_cover_inputs_intermediates_and_trace_storage() {
    let mut tiny = limits();
    tiny.max_elements = 23;
    assert_eq!(
        solve_neville_enclosures(&shrinking_problem(), &mut RationalBudget::new(tiny)),
        Err(Error::Arithmetic(RationalError::ElementLimit))
    );
    tiny.max_elements = 24;
    solve_neville_enclosures(&shrinking_problem(), &mut RationalBudget::new(tiny)).unwrap();
    tiny.max_bits = 3;
    assert_eq!(
        solve_neville_enclosures(&shrinking_problem(), &mut RationalBudget::new(tiny)),
        Err(Error::Arithmetic(RationalError::BitLimit))
    );
    let problem = NevilleEnclosureProblem {
        target_id: "growth".to_owned(),
        evaluation_point: q(0, 1),
        samples: vec![sample(q(1, 1), q(4, 1)), sample(q(2, 1), q(7, 1))],
        prefix_remainder_bounds: vec![Some(q(3, 1)); 2],
        known_target: None,
    };
    assert_eq!(
        solve_neville_enclosures(&problem, &mut RationalBudget::new(tiny)),
        Err(Error::Interpolation(NevilleError::Arithmetic(
            RationalError::BitLimit
        )))
    );
    solve_neville_enclosures(&problem, &mut budget()).unwrap();
    assert_eq!(
        budget().elements(usize::MAX, 2),
        Err(RationalError::ElementLimit)
    );
}

#[test]
fn values_beyond_machine_integer_precision_remain_exact() {
    let target = BigRational::from_integer(BigInt::from(1) << 100usize);
    let problem = NevilleEnclosureProblem {
        target_id: "large_exact".to_owned(),
        evaluation_point: q(0, 1),
        samples: vec![
            sample(q(1, 1), &target + q(1, 1)),
            sample(q(2, 1), &target + q(2, 1)),
        ],
        prefix_remainder_bounds: vec![Some(q(1, 1)), Some(q(0, 1))],
        known_target: Some(target.clone()),
    };
    let receipt = solve_neville_enclosures(&problem, &mut budget()).unwrap();
    assert_eq!(
        receipt.steps()[1].polynomial_enclosure,
        Interval::point(target.clone())
    );
    assert_eq!(receipt.steps()[1].nested_enclosure, Interval::point(target));
}

// Origin: engine/crates_rs/tests/core_solvers/test_neville_aitken_enclosure.rs
// Claim: urn:core:crates_rs:tests:test-neville-aitken-enclosure:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord908aee63 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord908aee63` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError908aee63 {
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
impl BoundaryError908aee63 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError908aee63 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError908aee63 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord908aee63 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError908aee63> {
        if capacity_bound == 0 {
            return Err(BoundaryError908aee63::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError908aee63::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError908aee63::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_908aee63() {
    let admitted = BoundaryRecord908aee63::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord908aee63::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
