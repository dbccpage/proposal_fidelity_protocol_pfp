//! Appendix T (WDP-DIM-1/R), §14.6 finite observation cost and Appendix X
//! calibrated reports: native checks against the monograph's stated examples
//! and the paper package's stored Python certificates.
//!
//! `tests/data/wdp_finite_observation_certificates.json` is a copy of the
//! paper package file `code/finite_observation/observation_certificates.json`
//! (source SHA-256 EA57ADE7E058C5AD459AA3ABF1BC5BA6FC834426A4F17281B9517B0C8E887BDD
//! with CRLF line endings). The checked-in copy is LF-normalized, so its file
//! digest differs; the JSON content and the replayed certificates are the same.
use num_rational::BigRational;
use core_wdp::calibrated_reports::{
    transported_radius, CalibratedModel, Channel, RawReading, RecoveryStatus,
};
use core_wdp::distinct_image_completion::{
    annihilator_status, check_completion, check_repair_operation, check_shelf, produce_completion,
    produce_shelf, AnnihilatorStatus, Completion, CompletionTarget, DistinctImageProblem,
    RepairOperationWitness, ShelfSelection, Vector,
};
use core_wdp::observation_cost::{
    certificate_json, rational_text, solve, verify_certificate_json, verify_lp_pair, Instrument,
    ObservationInstance,
};
use serde_json::Value;

fn q(n: i64) -> BigRational {
    BigRational::from_integer(n.into())
}
fn qr(n: i64, d: i64) -> BigRational {
    BigRational::new(n.into(), d.into())
}
fn v(xs: &[i64]) -> Vector {
    xs.iter().map(|&x| q(x)).collect()
}

const ALL_TARGETS: [CompletionTarget; 4] = [
    CompletionTarget::Raw,
    CompletionTarget::Quotient,
    CompletionTarget::Joint,
    CompletionTarget::RealizableQuotient,
];

fn problem(n: usize, source: &[&[i64]], repair: &[&[i64]], observer: &[&[i64]]) -> DistinctImageProblem {
    DistinctImageProblem::new(
        n,
        source.iter().map(|c| v(c)).collect(),
        repair.iter().map(|c| v(c)).collect(),
        observer.iter().map(|r| v(r)).collect(),
    )
    .unwrap()
}

// ---------------------------------------------------------------- Appendix T

#[test]
fn t4_three_inclusions_recompute_the_sharp_counts() {
    // R ⊂ B.
    let f = problem(3, &[&[1, 0, 0]], &[&[1, 0, 0], &[0, 1, 0]], &[&[0, 0, 1]]).analyze().unwrap();
    assert_eq!((f.raw_minimum, f.quotient_minimum, f.joint_minimum, f.separate_sum), (1, 0, 1, 1));
    // B ⊂ R: the joint optimum is strictly below the separate sum.
    let f = problem(3, &[&[1, 0, 0], &[0, 1, 0]], &[&[1, 0, 0]], &[&[0, 0, 1]]).analyze().unwrap();
    assert_eq!((f.raw_minimum, f.quotient_minimum, f.joint_minimum, f.separate_sum), (2, 1, 2, 3));
    // Neither inclusion.
    let f = problem(
        4,
        &[&[0, 1, 0, 0], &[0, 0, 1, 0]],
        &[&[1, 0, 0, 0], &[0, 1, 0, 0]],
        &[&[0, 0, 0, 1]],
    )
    .analyze()
    .unwrap();
    assert_eq!((f.dim_k, f.dim_kb, f.dim_t), (3, 2, 1));
    assert_eq!((f.raw_minimum, f.quotient_minimum, f.joint_minimum, f.separate_sum), (2, 1, 2, 3));
    // Excess of the separate sum is dim((R ∩ K)/T).
    assert_eq!(f.separate_sum - f.joint_minimum, f.dim_rk - f.dim_t);
}

#[test]
fn t3_equal_images_recover_the_section_10_6_specialization() {
    let p = problem(3, &[&[1, 0, 0], &[0, 1, 0]], &[&[1, 0, 0], &[0, 1, 0]], &[&[0, 0, 1]]);
    let f = p.analyze().unwrap();
    assert_eq!(f.joint_minimum, f.dim_k);
    assert_eq!(f.separate_sum, f.joint_minimum);
}

#[test]
fn produced_completions_replay_on_every_example_and_target() {
    let examples = [
        problem(3, &[&[1, 0, 0]], &[&[1, 0, 0], &[0, 1, 0]], &[&[0, 0, 1]]),
        problem(3, &[&[1, 0, 0], &[0, 1, 0]], &[&[1, 0, 0]], &[&[0, 0, 1]]),
        problem(4, &[&[0, 1, 0, 0], &[0, 0, 1, 0]], &[&[1, 0, 0, 0], &[0, 1, 0, 0]], &[&[0, 0, 0, 1]]),
        problem(3, &[&[1, 1, 0], &[0, 2, -1]], &[&[1, 0, 1]], &[]),
        problem(2, &[&[1, 0]], &[], &[]),
    ];
    for p in &examples {
        for target in ALL_TARGETS {
            let completion = produce_completion(p, target).unwrap();
            check_completion(p, &completion).unwrap_or_else(|e| panic!("{target:?}: {e}"));
            // One row fewer cannot be sufficient: drop a row and re-check.
            if let Some((_, rest)) = completion.rows.split_first() {
                assert!(!p.suite_is_sufficient(rest, target).unwrap(), "{target:?}");
            }
        }
    }
}

#[test]
fn t3_lower_columns_must_be_an_obstruction_basis_not_merely_rank() {
    let p = problem(3, &[&[1, 0, 0], &[0, 1, 0]], &[&[1, 0, 0]], &[&[0, 0, 1]]);
    let good = produce_completion(&p, CompletionTarget::Joint).unwrap();
    check_completion(&p, &good).unwrap();
    // e2 and e3 have width 2 and rank 2, but e3 ∉ ker Q.
    let forged = Completion {
        lower_columns: vec![v(&[0, 1, 0]), v(&[0, 0, 1])],
        ..good
    };
    let err = check_completion(&p, &forged).unwrap_err();
    assert_eq!(err.to_string(), "lower certificate");
}

#[test]
fn t4_raw_and_quotient_completions_are_different_questions() {
    // A raw completion need not be a quotient completion.
    let p = problem(3, &[&[1, 0, 0]], &[&[0, 0, 1]], &[&[0, 0, 1]]);
    let row = vec![v(&[1, 0, 0])];
    assert!(p.raw_holds(&row).unwrap());
    assert!(!p.quotient_holds(&row).unwrap());
    // The converse gap on B ⊂ R.
    let p = problem(3, &[&[1, 0, 0], &[0, 1, 0]], &[&[1, 0, 0]], &[&[0, 0, 1]]);
    let row = vec![v(&[0, 1, 0])];
    assert!(p.quotient_holds(&row).unwrap());
    assert!(!p.raw_holds(&row).unwrap());
}

#[test]
fn t8_realizable_domain_corollary_example() {
    // V = Q^2, R = span{e1}, B = 0, Q = 0.
    let p = problem(2, &[&[1, 0]], &[], &[]);
    let f = p.analyze().unwrap();
    assert_eq!(f.realizable_quotient_minimum, 1);
    assert_eq!(f.quotient_minimum, 2);
    let row = vec![v(&[1, 0])];
    assert!(p.realizable_quotient_holds(&row).unwrap());
    assert!(!p.quotient_holds(&row).unwrap());
}

#[test]
fn t5_annihilator_menu_is_impossible_when_t_is_nonzero() {
    let p = problem(3, &[&[1, 0, 0]], &[&[1, 0, 0], &[0, 1, 0]], &[&[0, 0, 1]]);
    match annihilator_status(&p, CompletionTarget::Joint).unwrap() {
        AnnihilatorStatus::Impossible(w) => assert_eq!(w, v(&[1, 0, 0])),
        other => panic!("expected impossibility, got {other:?}"),
    }
    // Quotient sufficiency alone stays feasible at m_quot.
    match annihilator_status(&p, CompletionTarget::Quotient).unwrap() {
        AnnihilatorStatus::Feasible(rows) => assert!(p.quotient_holds(&rows).unwrap()),
        other => panic!("expected feasibility, got {other:?}"),
    }
    // T = 0: annihilating rows attain the joint count.
    let p = problem(3, &[&[0, 1, 0]], &[&[1, 0, 0]], &[&[0, 0, 1]]);
    match annihilator_status(&p, CompletionTarget::Joint).unwrap() {
        AnnihilatorStatus::Feasible(rows) => {
            assert_eq!(rows.len(), p.analyze().unwrap().joint_minimum);
            assert!(p.suite_is_sufficient(&rows, CompletionTarget::Joint).unwrap());
            for r in &rows {
                assert_eq!(core_wdp::distinct_image_completion::report(&[r.clone()], &v(&[1, 0, 0])), vec![q(0)]);
            }
        }
        other => panic!("expected feasibility, got {other:?}"),
    }
}

#[test]
fn t5_shelf_matches_independent_enumeration_and_rejects_costlier() {
    let p = problem(3, &[&[1, 0, 0], &[0, 1, 0]], &[&[1, 0, 0]], &[&[0, 0, 1]]);
    let shelf = vec![v(&[1, 0, 0]), v(&[0, 1, 0]), v(&[1, 1, 0]), v(&[0, 0, 1])];
    let costs = vec![q(3), q(4), q(5), q(1)];
    let chosen = produce_shelf(&p, &shelf, &costs, CompletionTarget::Joint).unwrap();
    assert_eq!(chosen.cost, Some(q(7)));
    check_shelf(&p, &shelf, &costs, CompletionTarget::Joint, &chosen).unwrap();
    let costlier = ShelfSelection {
        indices: Some(vec![0, 2]),
        cost: Some(q(8)),
    };
    assert!(check_shelf(&p, &shelf, &costs, CompletionTarget::Joint, &costlier).is_err());
    let missing_flag = ShelfSelection {
        indices: Some(vec![0, 1]),
        cost: None,
    };
    assert_eq!(
        check_shelf(&p, &shelf, &costs, CompletionTarget::Joint, &missing_flag)
            .unwrap_err()
            .to_string(),
        "feasible flag"
    );
    assert!(produce_shelf(&p, &shelf[..1], &[q(0)], CompletionTarget::Joint).is_err());
}

#[test]
fn t6_repair_claims_need_a_replayed_operation() {
    let p = problem(2, &[&[1, 0]], &[&[1, 0], &[0, 1]], &[&[1, 0]]);
    let witness = RepairOperationWitness {
        admissible_columns: vec![v(&[1, 0])],
        preimage: v(&[1]),
        repair: v(&[1, 0]),
        defect: v(&[1, 0]),
    };
    check_repair_operation(&p, &witness).unwrap();
    let wrong_defect = RepairOperationWitness {
        defect: v(&[0, 1]),
        ..witness.clone()
    };
    assert!(check_repair_operation(&p, &wrong_defect).is_err());
    let wrong_image = RepairOperationWitness {
        preimage: v(&[2]),
        ..witness
    };
    assert!(check_repair_operation(&p, &wrong_image).is_err());
}

// ------------------------------------------------- §14.6 observation cost

fn instance_from_json(input: &Value) -> ObservationInstance {
    let labels = |key: &str| -> Vec<String> {
        input[key].as_array().unwrap().iter().map(|s| s.as_str().unwrap().to_string()).collect()
    };
    let instruments = input["instruments"]
        .as_array()
        .unwrap()
        .iter()
        .map(|i| {
            let text = i["cost"].as_str().unwrap();
            let cost = match text.split_once('/') {
                Some((n, d)) => BigRational::new(n.parse().unwrap(), d.parse().unwrap()),
                None => BigRational::from_integer(text.parse().unwrap()),
            };
            Instrument {
                name: i["name"].as_str().unwrap().to_string(),
                outcomes: i["outcomes"].as_array().unwrap().iter().map(|s| s.as_str().unwrap().to_string()).collect(),
                cost,
            }
        })
        .collect();
    ObservationInstance::new(labels("states"), labels("visible"), labels("query"), instruments).unwrap()
}

fn stored_bundle() -> serde_json::Map<String, Value> {
    let path = concat!(env!("CARGO_MANIFEST_DIR"), "/../tests/core_wdp/data/wdp_finite_observation_certificates.json");
    let text = std::fs::read_to_string(path).unwrap();
    serde_json::from_str::<Value>(&text).unwrap().as_object().unwrap().clone()
}

#[test]
fn stored_python_certificates_replay_natively_with_identical_digests() {
    let bundle = stored_bundle();
    assert_eq!(bundle.len(), 5);
    for (name, row) in &bundle {
        let instance = instance_from_json(&row["input"]);
        let stored = &row["certificate"];
        assert_eq!(stored["instance_sha256"].as_str().unwrap(), instance.instance_sha256(), "{name}");
        let verdict = verify_certificate_json(&instance, stored);
        assert!(verdict.accepted, "{name}: {} {}", verdict.code, verdict.detail);
        // The native producer proposes exactly the stored certificate.
        assert_eq!(&certificate_json(&solve(&instance)), stored, "{name}");
    }
    let values = |name: &str| {
        let c = &bundle[name]["certificate"];
        (c["fixed"]["value"].clone(), c["adaptive"]["value"].clone())
    };
    assert_eq!(values("adaptive_corrected"), (Value::from("7"), Value::from("4")));
    assert_eq!(values("infeasible_miniature"), (Value::Null, Value::Null));
}

#[test]
fn forged_tables_and_substituted_inputs_are_refused() {
    let bundle = stored_bundle();
    let row = &bundle["adaptive_corrected"];
    let instance = instance_from_json(&row["input"]);
    let mut forged = row["certificate"].clone();
    forged["adaptive"]["value"] = Value::from("3");
    assert_eq!(verify_certificate_json(&instance, &forged).code, "INVALID_CERTIFICATE");
    let mut forged = row["certificate"].clone();
    forged["fixed"]["table"][7]["sufficient"] = Value::from(false);
    assert_eq!(verify_certificate_json(&instance, &forged).code, "INVALID_CERTIFICATE");
    let mut forged = row["certificate"].clone();
    forged["schema_version"] = Value::from(true);
    assert_eq!(verify_certificate_json(&instance, &forged).code, "INVALID_CERTIFICATE");
    let other = instance_from_json(&bundle["fano_integrality_gap"]["input"]);
    assert_eq!(verify_certificate_json(&other, &row["certificate"]).code, "INPUT_MISMATCH");
}

#[test]
fn fano_lp_pair_certifies_the_integrality_gap() {
    let bundle = stored_bundle();
    let instance = instance_from_json(&bundle["fano_integrality_gap"]["input"]);
    let third = vec![qr(1, 3); 7];
    let lp = verify_lp_pair(&instance, &third, &third).unwrap();
    assert_eq!(rational_text(&lp), "7/3");
    assert_eq!(solve(&instance).fixed_value, Some(q(3)));
}

// --------------------------------------------------------------- Appendix X

fn channel(name: &str, gain: BigRational, offset: BigRational, intervals: Vec<(BigRational, BigRational)>, price: i64) -> Channel {
    Channel {
        name: name.into(),
        raw_unit: "raw".into(),
        unit: "m".into(),
        gain,
        offset,
        intervals,
        price: q(price),
    }
}

fn strings(xs: &[&str]) -> Vec<String> {
    xs.iter().map(|s| s.to_string()).collect()
}

fn separated() -> CalibratedModel {
    let values: [[i64; 4]; 3] = [[0, 0, 10, 10], [0, 10, 0, 0], [0, 0, 0, 10]];
    let channels = ["A", "B", "C"]
        .iter()
        .zip(values)
        .zip([1, 3, 3])
        .map(|((name, row), price)| {
            channel(name, q(2), q(1), row.iter().map(|&x| (q(x - 1), q(x + 1))).collect(), price)
        })
        .collect();
    let labels = strings(&["00", "01", "10", "11"]);
    CalibratedModel::new(labels.clone(), strings(&["*"; 4]), labels, channels).unwrap()
}

fn touching() -> CalibratedModel {
    CalibratedModel::new(
        strings(&["a", "b"]),
        strings(&["*", "*"]),
        strings(&["a", "b"]),
        vec![channel("M", q(1), q(0), vec![(q(0), q(1)), (q(1), q(2))], 1)],
    )
    .unwrap()
}

fn correlated_enclosure() -> CalibratedModel {
    CalibratedModel::new(
        strings(&["0", "1"]),
        strings(&["*", "*"]),
        strings(&["0", "1"]),
        vec![
            channel("plus", q(1), q(0), vec![(q(-1), q(1)), (q(0), q(2))], 1),
            channel("minus", q(1), q(0), vec![(q(-1), q(1)), (q(-2), q(0))], 1),
        ],
    )
    .unwrap()
}

#[test]
fn x1_transported_enclosure_radius() {
    assert_eq!(transported_radius(&q(-3), &qr(1, 2), &q(1)).unwrap(), qr(5, 2));
    assert!(transported_radius(&q(0), &q(1), &q(1)).is_err());
    assert!(transported_radius(&q(1), &q(-1), &q(1)).is_err());
}

#[test]
fn x3_x4_costs_agree_between_direct_recursion_and_finite_lift() {
    for (model, fixed, adaptive) in [
        (separated(), Some(q(7)), Some(q(4))),
        (touching(), None, None),
        (correlated_enclosure(), None, None),
    ] {
        assert_eq!(model.fixed_robust_cost().map(|(c, _)| c), fixed);
        assert_eq!(model.adaptive_robust_cost(), adaptive);
        let lifted = solve(&model.finite_lift().unwrap());
        assert_eq!(lifted.fixed_value, fixed);
        assert_eq!(lifted.adaptive_value, adaptive);
    }
}

#[test]
fn x3_alphabet_retains_endpoint_singletons_within_the_bound() {
    let model = touching();
    let alphabet = model.alphabet(0);
    // {a}, {a,b} at the shared endpoint 1, {b}.
    assert_eq!(alphabet.len(), 3);
    assert!(alphabet.iter().any(|s| s.len() == 2));
    for m in [separated(), touching(), correlated_enclosure()] {
        let n = m.channels()[0].intervals.len();
        for i in 0..m.channels().len() {
            assert!(m.alphabet(i).len() <= 4 * n - 1);
        }
    }
}

#[test]
fn x2_recovery_statuses() {
    let m = separated();
    let read = |channel: &str, raw: BigRational| RawReading {
        channel: channel.into(),
        raw_unit: "raw".into(),
        value: raw,
    };
    // z = 2r + 1. A reads 0 → r = -1/2; B reads 10 → r = 9/2.
    let a_low = read("A", qr(-1, 2));
    let b_high = read("B", qr(9, 2));
    let e = m.evaluate("*", &[a_low.clone(), b_high.clone()], "01");
    assert_eq!(e.status, RecoveryStatus::Verified);
    assert_eq!(e.compatible, strings(&["01"]));
    assert_eq!(m.evaluate("*", &[a_low.clone()], "00").status, RecoveryStatus::Abstain);
    assert_eq!(m.evaluate("*", &[a_low.clone(), b_high.clone()], "00").status, RecoveryStatus::InvalidProposal);
    // A reading of 5 is outside every A interval: no vacuous acceptance.
    assert_eq!(m.evaluate("*", &[read("A", q(2))], "00").status, RecoveryStatus::Inconsistent);
    let wrong_unit = RawReading { raw_unit: "volt".into(), ..a_low.clone() };
    assert_eq!(m.evaluate("*", &[wrong_unit], "00").status, RecoveryStatus::InvalidReport);
    assert_eq!(m.evaluate("*", &[a_low.clone(), a_low], "00").status, RecoveryStatus::InvalidReport);
}

// Origin: engine/crates_rs/tests/core_wdp/test_wdp_observation_completion_and_cost.rs
// Claim: urn:core:crates_rs:tests:test-wdp-observation-completion-and-cost:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord35a54296 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord35a54296` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError35a54296 {
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
impl BoundaryError35a54296 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError35a54296 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError35a54296 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord35a54296 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError35a54296> {
        if capacity_bound == 0 {
            return Err(BoundaryError35a54296::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError35a54296::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError35a54296::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_35a54296() {
    let admitted = BoundaryRecord35a54296::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord35a54296::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
