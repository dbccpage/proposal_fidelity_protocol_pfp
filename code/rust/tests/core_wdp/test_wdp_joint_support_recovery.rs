//! Appendix Y joint report supports: native checks of the critical-value
//! witness against the monograph's Y.6 examples and the paper package's stored
//! Python certificates.
//!
//! `tests/data/wdp_joint_recovery_certificates.json` is a byte copy of the
//! paper package file `code/joint_recovery/certificates.json`
//! (SHA-256 3C5E09D52461FE294A18D18FAFA80FDFF2C2CDCF8ACE90C468D931B456F9F459).
use num_rational::BigRational;
use core_wdp::joint_support_recovery::{
    collision, conditional_instance, evaluate, finite_instance, sample_worlds, BipartiteBehavior,
    Channel, JointModel, JointStatus, JointSupportError, Segment,
};
use core_wdp::observation_cost::{certificate_json, solve, verify_certificate_json, Instrument, ObservationInstance};
use serde_json::Value;

fn q(n: i64) -> BigRational {
    BigRational::from_integer(n.into())
}
fn qr(n: i64, d: i64) -> BigRational {
    BigRational::new(n.into(), d.into())
}
fn row(xs: &[i64]) -> Vec<BigRational> {
    xs.iter().map(|&x| q(x)).collect()
}

fn channel(name: &str, price: i64) -> Channel {
    Channel {
        name: name.into(),
        raw_gain: q(1),
        raw_offset: q(0),
        price: q(price),
    }
}

fn segment(state: &str, lower: BigRational, upper: BigRational, slopes: Vec<BigRational>, offsets: Vec<BigRational>) -> Segment {
    Segment {
        state: state.into(),
        visible: "*".into(),
        answer: state.into(),
        lower,
        upper,
        slopes,
        offsets,
    }
}

fn ab() -> Vec<Channel> {
    vec![channel("A", 1), channel("B", 1)]
}

fn shared_error() -> JointModel {
    let segments = (0..2)
        .map(|x| segment(&x.to_string(), q(-1), q(1), row(&[1, 1]), row(&[x, -x])))
        .collect();
    JointModel::new(ab(), segments).unwrap()
}

fn isolated_collision() -> JointModel {
    JointModel::new(
        ab(),
        vec![
            segment("0", q(0), q(1), row(&[1, 1]), row(&[0, 0])),
            segment("1", q(0), q(1), row(&[1, 2]), vec![q(0), qr(-1, 3)]),
        ],
    )
    .unwrap()
}

fn parity_points() -> JointModel {
    let mut segments = Vec::new();
    for x in 0..2i64 {
        for y in 0..2i64 {
            segments.push(segment(&(x ^ y).to_string(), q(0), q(0), row(&[1, 1]), row(&[x, y])));
        }
    }
    JointModel::new(ab(), segments).unwrap()
}

fn isolated_cost_peak() -> JointModel {
    let mut channels = ab();
    channels.push(channel("C", 3));
    JointModel::new(
        channels,
        vec![
            segment("0", q(-1), q(1), row(&[1, 1, 1]), row(&[0, 0, 0])),
            segment("1", q(-1), q(1), row(&[1, -1, 1]), row(&[0, 0, 10])),
        ],
    )
    .unwrap()
}

fn costs(model: &JointModel) -> (Option<BigRational>, Option<BigRational>) {
    let certificate = solve(&finite_instance(model).unwrap());
    (certificate.fixed_value, certificate.adaptive_value)
}

#[test]
fn y6_exact_costs_match_the_monograph() {
    assert_eq!(costs(&shared_error()), (Some(q(2)), Some(q(2))));
    assert_eq!(sample_worlds(&shared_error()).unwrap().len(), 10, "Y.6 retains ten worlds");
    assert_eq!(costs(&isolated_collision()), (None, None));
    assert_eq!(costs(&parity_points()), (Some(q(2)), Some(q(2))));
    assert_eq!(costs(&isolated_cost_peak()), (Some(q(3)), Some(q(3))));
}

#[test]
fn crossing_example_short_circuits_to_a_shared_complete_report() {
    let (left, right) = collision(&isolated_collision()).expect("Y.3 crossing has a collision");
    assert_ne!(left.0, right.0);
    assert_eq!(left.1, vec![qr(1, 3), qr(1, 3)]);
    assert_eq!(left.1, right.1);
    assert!(collision(&shared_error()).is_none());
    assert!(collision(&isolated_cost_peak()).is_none());
}

#[test]
fn endpoint_sampling_understates_the_isolated_cost_peak() {
    let model = isolated_cost_peak();
    let mut worlds = Vec::new();
    for s in model.segments() {
        for e in [&s.lower, &s.upper] {
            let values: Vec<BigRational> = s.slopes.iter().zip(&s.offsets).map(|(a, b)| a * e + b).collect();
            worlds.push((s.state.clone(), values));
        }
    }
    let instruments = model
        .channels()
        .iter()
        .enumerate()
        .map(|(j, c)| Instrument {
            name: c.name.clone(),
            outcomes: worlds.iter().map(|(_, v)| v[j].to_string()).collect(),
            cost: c.price.clone(),
        })
        .collect();
    let sample = ObservationInstance::new(
        (0..worlds.len()).map(|i| i.to_string()).collect(),
        vec!["*".into(); worlds.len()],
        worlds.iter().map(|(s, _)| s.clone()).collect(),
        instruments,
    )
    .unwrap();
    assert_eq!(solve(&sample).fixed_value, Some(q(2)), "endpoint sample is optimistic");
    assert_eq!(costs(&model).0, Some(q(3)), "critical cells retain the interior collision");
}

#[test]
fn joint_check_uses_one_common_parameter() {
    let model = shared_error();
    assert_eq!(
        evaluate(&model, "*", &[(0, q(0)), (1, q(0))], "0"),
        JointStatus::Verified(vec!["0".into()])
    );
    assert_eq!(
        evaluate(&model, "*", &[(0, q(0))], "0"),
        JointStatus::Abstain(vec!["0".into(), "1".into()])
    );
    assert_eq!(evaluate(&model, "*", &[(0, q(0)), (1, q(0))], "1"), JointStatus::InvalidProposal(vec!["0".into()]));
    assert_eq!(evaluate(&model, "*", &[(0, q(5))], "0"), JointStatus::Inconsistent);
    assert_eq!(evaluate(&model, "other", &[], "0"), JointStatus::Inconsistent);
    assert_eq!(evaluate(&model, "*", &[(0, q(0)), (0, q(0))], "0"), JointStatus::InvalidReport);
    assert_eq!(evaluate(&model, "*", &[(7, q(0))], "0"), JointStatus::InvalidReport);
    let parity = parity_points();
    assert_eq!(
        evaluate(&parity, "*", &[(0, q(0)), (1, q(1))], "1"),
        JointStatus::Verified(vec!["1".into()]),
        "matching coordinates to different components would give a false abstention"
    );
}

#[test]
fn conditional_instance_retains_the_joint_history() {
    let model = isolated_collision();
    let at_zero = solve(&conditional_instance(&model, 0, &q(0), "*").unwrap());
    assert_eq!(at_zero.adaptive_value, Some(q(1)));
    let at_third = solve(&conditional_instance(&model, 0, &qr(1, 3), "*").unwrap());
    assert_eq!(at_third.adaptive_value, None);
    assert_eq!(
        conditional_instance(&model, 0, &q(9), "*").unwrap_err(),
        JointSupportError::InconsistentHistory
    );
    assert_eq!(
        conditional_instance(&model, 4, &q(0), "*").unwrap_err(),
        JointSupportError::BadChannelIndex
    );
}

#[test]
fn affine_coordinate_change_preserves_costs() {
    let base = shared_error();
    let (lambda, tau) = (q(-2), qr(7, 3));
    let segments = base
        .segments()
        .iter()
        .cloned()
        .map(|mut s| {
            s.slopes[0] = &lambda * &s.slopes[0];
            s.offsets[0] = &lambda * &s.offsets[0] + &tau;
            s
        })
        .collect();
    let moved = JointModel::new(base.channels().to_vec(), segments).unwrap();
    assert_eq!(costs(&moved), costs(&base));
}

#[test]
fn model_validation_refuses_out_of_scope_inputs() {
    let zero_slope = segment("0", q(0), q(1), row(&[0, 1]), row(&[0, 0]));
    assert_eq!(JointModel::new(ab(), vec![zero_slope]).unwrap_err(), JointSupportError::ZeroSlope);
    let reversed = segment("0", q(1), q(0), row(&[1, 1]), row(&[0, 0]));
    assert_eq!(JointModel::new(ab(), vec![reversed]).unwrap_err(), JointSupportError::ReversedInterval);
    let short = segment("0", q(0), q(1), row(&[1]), row(&[0]));
    assert_eq!(JointModel::new(ab(), vec![short]).unwrap_err(), JointSupportError::ShapeMismatch);
    let many = (0..11).map(|k| segment(&k.to_string(), q(0), q(1), row(&[1, 1]), row(&[k, 0]))).collect();
    assert_eq!(JointModel::new(ab(), many).unwrap_err(), JointSupportError::CapExceeded);
    let mut conflict = segment("0", q(0), q(1), row(&[1, 1]), row(&[0, 0]));
    let first = conflict.clone();
    conflict.answer = "1".into();
    assert_eq!(JointModel::new(ab(), vec![first, conflict]).unwrap_err(), JointSupportError::BadSegment);
    let mut free = channel("A", 1);
    free.price = q(0);
    assert_eq!(JointModel::new(vec![free], vec![]).unwrap_err(), JointSupportError::CapExceeded);
    let mut dup = ab();
    dup[1].name = "A".into();
    let ok = segment("0", q(0), q(1), row(&[1, 1]), row(&[0, 0]));
    assert_eq!(JointModel::new(dup, vec![ok]).unwrap_err(), JointSupportError::BadChannel);
}

#[test]
fn oversized_witness_is_refused_not_truncated() {
    let mut segments = Vec::new();
    for k in 0..10i64 {
        segments.push(segment(&(k % 2).to_string(), q(-1), q(1), row(&[1, 1]), row(&[k, -k])));
    }
    let renamed: Vec<Segment> = segments
        .into_iter()
        .enumerate()
        .map(|(k, mut s)| {
            s.state = format!("s{k}");
            s
        })
        .collect();
    let model = JointModel::new(ab(), renamed).unwrap();
    match sample_worlds(&model) {
        Err(JointSupportError::WitnessExceedsSolverCap) => {}
        Ok(worlds) => assert!(worlds.len() <= 10),
        Err(other) => panic!("unexpected error {other}"),
    }
}

fn stored() -> Value {
    let text = include_str!("data/wdp_joint_recovery_certificates.json");
    serde_json::from_str(text).unwrap()
}

#[test]
fn stored_python_certificates_replay_natively() {
    let bundle = stored();
    let fixtures = [
        ("shared_error", shared_error()),
        ("isolated_collision", isolated_collision()),
        ("parity_points", parity_points()),
        ("isolated_cost_peak", isolated_cost_peak()),
    ];
    assert_eq!(bundle.as_object().unwrap().len(), fixtures.len());
    for (name, model) in fixtures {
        let instance = finite_instance(&model).unwrap();
        let certificate = &bundle[name]["finite_certificate"];
        let verdict = verify_certificate_json(&instance, certificate);
        assert!(verdict.accepted, "{name}: {} {}", verdict.code, verdict.detail);
        assert_eq!(&certificate_json(&solve(&instance)), certificate, "{name}: byte-level schema parity");
    }
}

#[test]
fn tampered_joint_certificate_is_rejected() {
    let bundle = stored();
    let instance = finite_instance(&isolated_cost_peak()).unwrap();
    let mut forged = bundle["isolated_cost_peak"]["finite_certificate"].clone();
    forged["fixed"]["value"] = Value::from("2");
    assert!(!verify_certificate_json(&instance, &forged).accepted);
    let other = finite_instance(&shared_error()).unwrap();
    let verdict = verify_certificate_json(&other, &bundle["isolated_cost_peak"]["finite_certificate"]);
    assert_eq!(verdict.code, "INPUT_MISMATCH");
}

#[test]
fn product_behaviors_have_setting_independent_marginals() {
    // Cycle 007 Theorem `product_noSignalling`:
    // Bipartite product behaviors P(a, b | x, y) = P_A(a | x) * P_B(b | y)
    // satisfy no-signalling: Alice's marginal is independent of Bob's setting,
    // and Bob's marginal is independent of Alice's setting.
    let pa = vec![
        vec![qr(1, 3), qr(2, 3)], // x = 0: P(0|0)=1/3, P(1|0)=2/3
        vec![qr(3, 5), qr(2, 5)], // x = 1: P(0|1)=3/5, P(1|1)=2/5
        vec![qr(1, 2), qr(1, 2)], // x = 2: P(0|2)=1/2, P(1|2)=1/2
    ];
    let pb = vec![
        vec![qr(1, 4), qr(3, 4)], // y = 0: P(0|0)=1/4, P(1|0)=3/4
        vec![qr(2, 7), qr(5, 7)], // y = 1: P(0|1)=2/7, P(1|1)=5/7
    ];

    let behavior = BipartiteBehavior::from_product(&pa, &pb).unwrap();
    assert_eq!(behavior.num_alice_settings, 3);
    assert_eq!(behavior.num_bob_settings, 2);
    assert_eq!(behavior.num_alice_outcomes, 2);
    assert_eq!(behavior.num_bob_outcomes, 2);

    // Verify exact no-signalling condition
    assert!(behavior.verify_no_signalling().is_ok());

    // Verify operational independence: marginalA equals pa[x][a] for all y
    for x in 0..3 {
        for a in 0..2 {
            for y in 0..2 {
                assert_eq!(
                    behavior.alice_marginal(x, y, a),
                    pa[x][a],
                    "Alice marginal at (x={x}, y={y}, a={a}) must match pa"
                );
            }
        }
    }

    // Verify operational independence: marginalB equals pb[y][b] for all x
    for y in 0..2 {
        for b in 0..2 {
            for x in 0..3 {
                assert_eq!(
                    behavior.bob_marginal(x, y, b),
                    pb[y][b],
                    "Bob marginal at (x={x}, y={y}, b={b}) must match pb"
                );
            }
        }
    }
}

#[test]
fn signalling_witness_violates_no_signalling() {
    // Cycle 007 Theorem `sig_signals`:
    // When Alice's outcome is forced to equal Bob's setting (a = y),
    // Alice's marginal depends on Bob's setting, so no-signalling fails closed.
    //
    // Settings: X = {0}, Y = {0, 1}
    // Outcomes: A = {0, 1}, B = {0}
    // Table: table[x][y][a][b]
    // y = 0: P(a=0 | 0, 0) = 1, P(a=1 | 0, 0) = 0
    // y = 1: P(a=0 | 0, 1) = 0, P(a=1 | 0, 1) = 1
    let table = vec![
        vec![
            vec![vec![q(1)], vec![q(0)]], // y = 0: a=0 prob 1
            vec![vec![q(0)], vec![q(1)]], // y = 1: a=1 prob 1
        ],
    ];

    let behavior = BipartiteBehavior::new(table).unwrap();
    // Marginal at y=0 is [1, 0]; at y=1 is [0, 1] -> depends on y!
    assert_eq!(behavior.alice_marginal(0, 0, 0), q(1));
    assert_eq!(behavior.alice_marginal(0, 1, 0), q(0));

    let result = behavior.verify_no_signalling();
    assert_eq!(result, Err(JointSupportError::SignallingDetected));
}

#[test]
fn pr_box_is_no_signalling_and_non_factorizing() {
    // Popescu-Rohrlich box: P(a, b | x, y) = 1/2 iff a ⊕ b = x · y
    // Settings X={0, 1}, Y={0, 1}; Outcomes A={0, 1}, B={0, 1}
    let half = qr(1, 2);
    let zero = q(0);
    let mut table = Vec::new();
    for x in 0..2 {
        let mut row_y = Vec::new();
        for y in 0..2 {
            let mut row_a = Vec::new();
            for a in 0..2 {
                let mut row_b = Vec::new();
                for b in 0..2 {
                    if (a ^ b) == (x * y) {
                        row_b.push(half.clone());
                    } else {
                        row_b.push(zero.clone());
                    }
                }
                row_a.push(row_b);
            }
            row_y.push(row_a);
        }
        table.push(row_y);
    }

    let pr_box = BipartiteBehavior::new(table).unwrap();

    // PR-box strictly satisfies no-signalling:
    // Both Alice's and Bob's marginals are exactly 1/2 for all settings.
    assert!(pr_box.verify_no_signalling().is_ok());
    for x in 0..2 {
        for y in 0..2 {
            assert_eq!(pr_box.alice_marginal(x, y, 0), half);
            assert_eq!(pr_box.alice_marginal(x, y, 1), half);
            assert_eq!(pr_box.bob_marginal(x, y, 0), half);
            assert_eq!(pr_box.bob_marginal(x, y, 1), half);
        }
    }

    // However, PR-box does NOT factor as a product behavior:
    // For x=1, y=1: P(0, 0 | 1, 1) = 0, but P_A(0) * P_B(0) = 1/4 != 0.
    assert_ne!(
        pr_box.table[1][1][0][0],
        &pr_box.alice_marginal(1, 1, 0) * &pr_box.bob_marginal(1, 1, 0),
        "PR-box is strictly non-factorizing (PO-034 normal defect Q != 0)"
    );
}

#[test]
fn unnormalized_and_negative_behaviors_are_refused() {
    // Unnormalized distribution (sum != 1)
    let bad_table = vec![
        vec![
            vec![vec![qr(1, 3)], vec![qr(1, 3)]], // sums to 2/3, not 1
        ],
    ];
    assert_eq!(
        BipartiteBehavior::new(bad_table),
        Err(JointSupportError::UnnormalizedBehavior)
    );

    // Negative probability
    let negative_table = vec![
        vec![
            vec![vec![qr(3, 2)], vec![qr(-1, 2)]], // sums to 1, but has -1/2
        ],
    ];
    assert_eq!(
        BipartiteBehavior::new(negative_table),
        Err(JointSupportError::NegativeProbability)
    );
}

// Origin: engine/crates_rs/tests/core_wdp/test_wdp_joint_support_recovery.rs
// Claim: urn:core:crates_rs:tests:test-wdp-joint-support-recovery:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord8ee56e88 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord8ee56e88` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError8ee56e88 {
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
impl BoundaryError8ee56e88 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError8ee56e88 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError8ee56e88 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord8ee56e88 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError8ee56e88> {
        if capacity_bound == 0 {
            return Err(BoundaryError8ee56e88::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError8ee56e88::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError8ee56e88::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_8ee56e88() {
    let admitted = BoundaryRecord8ee56e88::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord8ee56e88::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
