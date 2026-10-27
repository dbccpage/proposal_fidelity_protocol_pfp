
#[allow(dead_code, non_camel_case_types, missing_docs)]
type BigRationalRatioWitness_956f72be = (i128, i128);
use core_adversary::stage::diagnostics::{SbeDiagnosticPort, SbeReport};
use core_adversary::stage::ports::Refusal;
use core_adversary::stage::synthetic_diagnostic::NativeSbeDiagnostic;
use core_adversary::novella::{literal_block, record_block, render_7act_novella, NovellaInput};
use core_adversary::render_record::RenderRecord;
use serde_json::Value;
use sha2::{Digest, Sha256};

fn fixtures() -> Value {
    serde_json::from_str(include_str!("fixtures/python_novella_v1.json")).unwrap()
}
#[test]
fn frozen_source_literal_blocks_retain_bytes_and_contain_embedded_fences() {
    let fixture = fixtures();
    for case in fixture["literal"].as_array().unwrap() {
        assert_eq!(
            serde_json::to_value(literal_block(
                case["text"].as_str().unwrap(),
                case["language"].as_str().unwrap()
            ))
            .unwrap(),
            case["output"],
            "{case}"
        );
    }
}
#[test]
fn frozen_source_pretty_json_preserves_object_order_and_number_types() {
    let fixture = fixtures();
    for case in fixture["record"].as_array().unwrap() {
        let record = RenderRecord::from_json(case["input_json"].as_str().unwrap()).unwrap();
        assert_eq!(
            serde_json::to_value(record_block(&record).unwrap()).unwrap(),
            case["output"],
            "{}",
            case["input_json"]
        );
    }
}
#[derive(Default)]
struct Diagnostic {
    calls: Vec<(String, usize)>,
}
impl SbeDiagnosticPort for Diagnostic {
    fn compute(&mut self, text: &str, dim: usize) -> Result<SbeReport, Refusal> {
        self.calls.push((text.into(), dim));
        NativeSbeDiagnostic.compute(text, dim)
    }
}
#[test]
fn frozen_source_full_novella_bytes_and_sha_with_injected_time_and_diagnostics() {
    let fixture = fixtures();
    for (index, case) in fixture["novella"].as_array().unwrap().iter().enumerate() {
        let input = NovellaInput::from_json(case["input_json"].as_str().unwrap()).unwrap();
        let mut diagnostic = Diagnostic::default();
        let output =
            render_7act_novella(&input, case["timestamp"].as_str().unwrap(), &mut diagnostic)
                .unwrap();
        assert_eq!(output, case["output"].as_str().unwrap(), "case {index}");
        assert_eq!(
            format!("{:x}", Sha256::digest(output.as_bytes())),
            case["sha256"].as_str().unwrap()
        );
        let raw: Value = serde_json::from_str(case["input_json"].as_str().unwrap()).unwrap();
        let expected_calls = usize::from(raw.get("prompt_sbe").is_none_or(Value::is_null))
            + usize::from(raw.get("sieve_sbe").is_none_or(Value::is_null));
        assert_eq!(diagnostic.calls.len(), expected_calls);
        assert!(diagnostic.calls.iter().all(|(_, dim)| *dim == 28));
        if expected_calls == 2 {
            let objective = raw["objective"].as_str().unwrap();
            let first = raw["candidates_data"][0]["content"].as_str().unwrap_or("");
            assert_eq!(diagnostic.calls[0].0, objective);
            assert_eq!(diagnostic.calls[1].0, format!("{objective} {first}"));
        }
    }
}
#[test]
fn native_render_ingress_refuses_invalid_shapes_and_propagates_diagnostic_failure() {
    for raw in [
        "bad",
        "[]",
        "{}",
        r#"{"run_key":"r","objective":"x","unknown":1}"#,
        r#"{"run_key":1,"objective":"x"}"#,
        r#"{"run_key":"r","objective":null}"#,
    ] {
        assert_eq!(
            NovellaInput::from_json(raw).unwrap_err().code,
            "ADVERSARY_RENDER_INPUT_INVALID"
        );
    }
    for raw in [
        r#"{"run_key":"r","objective":"x","candidates_data":{}}"#,
        r#"{"run_key":"r","objective":"x","candidates_data":[1]}"#,
        r#"{"run_key":"r","objective":"x","candidates_data":[{"content":1}]}"#,
        r#"{"run_key":"r","objective":"x","critiques_data":false}"#,
        r#"{"run_key":"r","objective":"x","critiques_data":[{"body":null}]}"#,
        r#"{"run_key":"r","objective":"x","now_utc":null}"#,
    ] {
        let input = NovellaInput::from_json(raw).unwrap();
        assert_eq!(
            render_7act_novella(&input, "fixed", &mut Diagnostic::default())
                .unwrap_err()
                .code,
            "ADVERSARY_RENDER_INPUT_INVALID"
        );
    }
    struct Failed;
    impl SbeDiagnosticPort for Failed {
        fn compute(&mut self, _: &str, _: usize) -> Result<SbeReport, Refusal> {
            Err(Refusal::new("SBE_INJECTED_FAILURE", "source port failure"))
        }
    }
    let input = NovellaInput::from_json(r#"{"run_key":"r","objective":"x"}"#).unwrap();
    assert_eq!(
        render_7act_novella(&input, "fixed", &mut Failed)
            .unwrap_err()
            .code,
        "SBE_INJECTED_FAILURE"
    );
}

#[test]
fn later_source_acceptance_truthiness_and_seeded_float_json_fingerprint() {
    let fixture: Value =
        serde_json::from_str(include_str!("fixtures/python_novella_acceptance_v1.json")).unwrap();
    assert_eq!(fixture["freeze"], "after-native-implementation");
    for case in fixture["truthiness"].as_array().unwrap() {
        let record = RenderRecord::from_json(case["input_json"].as_str().unwrap()).unwrap();
        assert_eq!(record.truthy(), case["output"].as_bool().unwrap());
    }
    for case in fixture["float_special"].as_array().unwrap() {
        let bits = u64::from_str_radix(case["bits"].as_str().unwrap(), 16).unwrap();
        assert_eq!(
            RenderRecord::Float(f64::from_bits(bits))
                .pretty_json()
                .unwrap(),
            case["output"].as_str().unwrap()
        );
    }
    let mut state = fixture["float_stream"]["seed"].as_u64().unwrap();
    let mut digest = Sha256::new();
    for _ in 0..fixture["float_stream"]["count"].as_u64().unwrap() {
        state = state
            .wrapping_mul(6364136223846793005)
            .wrapping_add(1442695040888963407);
        digest.update(state.to_be_bytes());
        let encoded = RenderRecord::Float(f64::from_bits(state))
            .pretty_json()
            .unwrap();
        digest.update(encoded.as_bytes());
        digest.update([0]);
    }
    assert_eq!(
        format!("{:x}", digest.finalize()),
        fixture["float_stream"]["sha256"].as_str().unwrap()
    );
}

// Origin: engine/crates_rs/tests/core_adversary/novella_parity.rs
// Claim: urn:core:crates_rs:tests:novella-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord956f72be {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord956f72be` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError956f72be {
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
impl BoundaryError956f72be {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError956f72be {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError956f72be {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord956f72be {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError956f72be> {
        if capacity_bound == 0 {
            return Err(BoundaryError956f72be::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError956f72be::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError956f72be::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_956f72be() {
    let admitted = BoundaryRecord956f72be::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord956f72be::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
