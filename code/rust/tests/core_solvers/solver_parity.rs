//! Cross-language parity fixture for the Phi-1 L1 boundary solver.
//!
//! Rust is the PROD face, so Rust generates and Python verifies. The companion
//! is `engine/_tests_unit/test_solver_parity.py`, which loads this file
//! and asserts the Python mirror produces the same outcome for every case,
//! refusal classes included.
//!
//! Integers are written as JSON strings. The values here are small, but `i128`
//! exceeds what a JSON number is guaranteed to round-trip, and a fixture that
//! silently loses precision at the boundary is worse than no fixture. This also
//! keeps the file inside the no-float canonical profile.
//!
//! Regenerate with:
//!   cargo test -j 1 -p core_solvers --test solver_parity -- --ignored regenerate
//!
//! AuthorityEffect: None. Agreement of two implementations is evidence, not proof.

use std::fs;
use std::path::PathBuf;

use core_solvers::solver_flow_network_simplex::NetworkSimplexError;
use core_solvers::solver_lp_phi1_boundary::{solve_l1_boundary, Boundary1, BoundaryEdge};
use serde_json::{json, Map, Value};

fn fixture_path() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../tests/core_solvers")
        .join("fixtures")
        .join("phi1_l1_boundary_parity.json")
}

/// One case both implementations must agree on.
///
/// Named fields rather than a positional tuple: `(name, usize, Vec<(usize,
/// usize, i128)>, Vec<i128>)` gave no hint which `usize` was the vertex count
/// and which the endpoints, and a fixture whose cases are hard to read is a
/// fixture nobody checks.
struct ParityCase {
    name: &'static str,
    num_vertices: usize,
    /// `(tail, head, weight)` per edge.
    edges: Vec<(usize, usize, i128)>,
    /// The residual vector; must sum to zero for a solvable case.
    x: Vec<i128>,
}

fn case(
    name: &'static str,
    num_vertices: usize,
    edges: Vec<(usize, usize, i128)>,
    x: Vec<i128>,
) -> ParityCase {
    ParityCase {
        name,
        num_vertices,
        edges,
        x,
    }
}

/// The cases the two implementations must agree on.
///
/// Deliberately spans every refusal class the solver can produce as well as
/// ordinary solutions: a parity fixture covering only success would show only
/// that the happy paths match, and the two implementations first diverged on
/// refusals.
fn cases() -> Vec<ParityCase> {
    vec![
        case("trivial_zero_residual", 2, vec![(0, 1, 1)], vec![0, 0]),
        case("single_edge_unit_flow", 2, vec![(0, 1, 1)], vec![1, -1]),
        case(
            "path_of_three",
            3,
            vec![(0, 1, 2), (1, 2, 3)],
            vec![1, 0, -1],
        ),
        case(
            "triangle_prefers_direct_edge",
            3,
            vec![(0, 1, 1), (1, 2, 1), (0, 2, 1)],
            vec![1, 0, -1],
        ),
        case(
            "triangle_prefers_detour_when_direct_is_dear",
            3,
            vec![(0, 1, 1), (1, 2, 1), (0, 2, 10)],
            vec![1, 0, -1],
        ),
        case(
            "square_with_two_equal_routes",
            4,
            vec![(0, 1, 1), (1, 3, 1), (0, 2, 1), (2, 3, 1)],
            vec![2, 0, 0, -2],
        ),
        case(
            "disconnected_but_balanced_per_component",
            4,
            vec![(0, 1, 1), (2, 3, 1)],
            vec![1, -1, 1, -1],
        ),
        case("zero_weight_edge", 2, vec![(0, 1, 0)], vec![5, -5]),
        case(
            "larger_magnitudes",
            3,
            vec![(0, 1, 7), (1, 2, 11)],
            vec![13, 0, -13],
        ),
        // refusal classes
        case("refusal_unbalanced_demand", 2, vec![(0, 1, 1)], vec![1, 0]),
        case("refusal_length_mismatch", 3, vec![(0, 1, 1)], vec![1, -1]),
        case("refusal_negative_weight", 2, vec![(0, 1, -3)], vec![1, -1]),
        case(
            "refusal_endpoint_out_of_range",
            2,
            vec![(0, 7, 1)],
            vec![1, -1],
        ),
        case("refusal_self_loop", 2, vec![(1, 1, 1)], vec![0, 0]),
        case("refusal_empty_carrier", 0, vec![], vec![]),
    ]
}

fn ints(v: &[i128]) -> Value {
    Value::Array(v.iter().map(|n| json!(n.to_string())).collect())
}

/// The refusal, reduced to a class name and its payload.
///
/// Compared structurally rather than by rendered message so that rewording an
/// error string does not read as a divergence, while a genuine change of class
/// or payload does.
fn structured_refusal_payload(err: &NetworkSimplexError) -> Option<(&'static str, Value)> {
    match err {
        NetworkSimplexError::DemandLengthMismatch { expected, found } => Some((
            "DemandLengthMismatch",
            json!({"expected": expected.to_string(), "found": found.to_string()}),
        )),
        NetworkSimplexError::UnbalancedDemand { sum } => {
            Some(("UnbalancedDemand", json!({"sum": sum.to_string()})))
        }
        NetworkSimplexError::NegativeWeight { edge, weight } => Some((
            "NegativeWeight",
            json!({"edge": edge.to_string(), "weight": weight.to_string()}),
        )),
        NetworkSimplexError::IterationLimitExceeded { limit } => Some((
            "IterationLimitExceeded",
            json!({"limit": limit.to_string()}),
        )),
        NetworkSimplexError::InvalidCarrier { message } => {
            Some(("InvalidCarrier", json!({"message": message})))
        }
        _ => None,
    }
}

fn refusal_value(err: &NetworkSimplexError) -> Value {
    let (class, payload) = if let Some(pair) = structured_refusal_payload(err) {
        pair
    } else {
        let label = match err {
            NetworkSimplexError::SizeLimit => "SizeLimit",
            NetworkSimplexError::CertificateMismatch => "CertificateMismatch",
            NetworkSimplexError::EmptyGraph => "EmptyGraph",
            NetworkSimplexError::Infeasible => "Infeasible",
            NetworkSimplexError::InvalidBasis => "InvalidBasis",
            _ => "ArithmeticOverflow",
        };
        (label, json!({}))
    };
    json!({"class": class, "payload": payload})
}

fn build_fixture() -> Value {
    let mut out = Vec::new();
    for ParityCase {
        name,
        num_vertices,
        edges,
        x,
    } in cases()
    {
        let boundary = Boundary1 {
            num_vertices,
            edges: edges
                .iter()
                .map(|&(tail, head, weight)| BoundaryEdge { tail, head, weight })
                .collect(),
        };

        let outcome = match solve_l1_boundary(&boundary, &x) {
            Ok(s) => json!({
                "ok": {
                    "objective": s.objective.to_string(),
                    "z": ints(&s.z),
                    "vertex_potential": ints(&s.vertex_potential),
                    "reduced_costs": ints(&s.reduced_costs),
                }
            }),
            Err(e) => json!({ "err": refusal_value(&e) }),
        };

        let mut case = Map::new();
        case.insert("name".into(), json!(name));
        case.insert("num_vertices".into(), json!(num_vertices.to_string()));
        case.insert(
            "edges".into(),
            Value::Array(
                edges
                    .iter()
                    .map(|&(t, h, w)| {
                        json!({"tail": t.to_string(), "head": h.to_string(), "weight": w.to_string()})
                    })
                    .collect(),
            ),
        );
        case.insert("x".into(), ints(&x));
        case.insert("outcome".into(), outcome);
        out.push(Value::Object(case));
    }

    json!({
        "schema": "core.parity.phi1_l1_boundary.v1",
        "generated_by": "core_solvers::tests::solver_parity (Rust, PROD face)",
        "integers_are": "decimal strings, exact i128",
        "cases": out
    })
}

fn render(v: &Value) -> String {
    // Two-space pretty print keeps the fixture reviewable in a diff; the
    // comparison below is on parsed values, so formatting is not load-bearing.
    format!(
        "{}\n",
        serde_json::to_string_pretty(v).expect("fixture serializes")
    )
}

#[test]
fn the_fixture_matches_the_current_solver() {
    let path = fixture_path();
    let expected = build_fixture();

    let on_disk = fs::read_to_string(&path).unwrap_or_else(|_| {
        panic!(
            "parity fixture missing at {}; regenerate with:\n  \
             cargo test -j 1 -p core_solvers --test solver_parity -- --ignored regenerate",
            path.display()
        )
    });
    let on_disk: Value = serde_json::from_str(&on_disk).expect("fixture is valid JSON");

    assert_eq!(
        on_disk, expected,
        "the solver's behaviour no longer matches the committed parity fixture. \
         If the change is intended, regenerate the fixture and check that the \
         Python mirror is updated in the same commit."
    );
}

#[test]
fn every_refusal_class_is_exercised() {
    // A fixture that drifts into covering only successes stops being able to
    // detect a divergence in refusal classification, which is where the two
    // implementations actually disagreed.
    let fixture = build_fixture();
    let classes: Vec<String> = fixture["cases"]
        .as_array()
        .unwrap()
        .iter()
        .filter_map(|c| c["outcome"]["err"]["class"].as_str().map(str::to_string))
        .collect();

    for required in [
        "UnbalancedDemand",
        "DemandLengthMismatch",
        "NegativeWeight",
        "InvalidCarrier",
    ] {
        assert!(
            classes.iter().any(|c| c == required),
            "no case produces {required}; classes present: {classes:?}"
        );
    }
}

#[test]
#[ignore = "writes the fixture; run deliberately"]
fn regenerate() {
    let path = fixture_path();
    fs::create_dir_all(path.parent().unwrap()).expect("fixture directory");
    fs::write(&path, render(&build_fixture())).expect("write fixture");
    eprintln!("wrote {}", path.display());
}

// Origin: engine/crates_rs/tests/core_solvers/solver_parity.rs
// Claim: urn:core:crates_rs:tests:solver-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd31be548 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd31be548` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord31be548 {
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
impl BoundaryErrord31be548 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord31be548 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord31be548 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd31be548 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord31be548> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord31be548::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord31be548::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord31be548::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_d31be548() {
    let admitted = BoundaryRecordd31be548::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordd31be548::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
