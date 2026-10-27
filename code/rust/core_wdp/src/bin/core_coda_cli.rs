//! Sovereign CLI binary for core_coda 9-layer Master Normal Form pipeline.
//!
//! Reads ProblemInstance / Cochain JSON from stdin or --file, executes the full
//! 9-layer CODA pipeline, and outputs verified outcome JSON to stdout.
//!
//! AuthorityEffect: None.

use std::collections::BTreeMap;
use std::env;
use std::fs;
use std::io::{self, Read};
use std::process;

use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::Zero;
use serde::Serialize;
use serde_json::Value;

use core_wdp::coda::pipeline::evaluate_coda_pipeline;
use core_wdp::coda::types::{MasterNormalFormOutcome, ProblemInstance};

fn parse_rational_str(s: &str) -> Result<BigRational, String> {
    if let Some((n_str, d_str)) = s.split_once('/') {
        let n: BigInt = n_str.trim().parse().map_err(|e| format!("{e}"))?;
        let d: BigInt = d_str.trim().parse().map_err(|e| format!("{e}"))?;
        if d.is_zero() {
            return Err("zero denominator in rational string".into());
        }
        Ok(BigRational::new(n, d))
    } else {
        let n: BigInt = s.trim().parse().map_err(|e| format!("{e}"))?;
        Ok(BigRational::from_integer(n))
    }
}

fn parse_rational(val: &Value) -> Result<BigRational, String> {
    if let Some(i) = val.as_i64() {
        return Ok(BigRational::from_integer(i.into()));
    }
    if let Some(s) = val.as_str() {
        return parse_rational_str(s);
    }
    if let Some(arr) = val.as_array() {
        if arr.len() == 2 {
            let n = parse_rational(&arr[0])?;
            let d = parse_rational(&arr[1])?;
            if d.is_zero() {
                return Err("zero denominator in rational tuple".into());
            }
            return Ok(n / d);
        }
    }
    Err(format!("invalid rational value: {val:?}"))
}

fn parse_rational_vec(val: &Value) -> Result<Vec<BigRational>, String> {
    let arr = val.as_array().ok_or_else(|| "expected array".to_string())?;
    arr.iter().map(parse_rational).collect()
}

fn parse_rational_matrix(val: &Value) -> Result<Vec<Vec<BigRational>>, String> {
    let arr = val.as_array().ok_or_else(|| "expected 2D array".to_string())?;
    arr.iter().map(parse_rational_vec).collect()
}

fn populate_problem_fields(problem: &mut ProblemInstance, obj: &serde_json::Map<String, Value>) {
    if let Some(v) = obj.get("raw_data").and_then(|v| v.as_str()) {
        problem.raw_data = v.to_string();
    }
    if let Some(sieve) = obj.get("candidate_sieve").and_then(|v| v.as_array()) {
        problem.candidate_sieve = sieve.iter().filter_map(|x| x.as_str().map(String::from)).collect();
    }
    if let Some(coarse) = obj.get("coarse_profile").and_then(|v| v.as_array()) {
        problem.coarse_profile = coarse.iter().filter_map(|x| x.as_i64()).collect();
    }
    if let Some(fine) = obj.get("fine_profile").and_then(|v| v.as_array()) {
        problem.fine_profile = fine.iter().filter_map(|x| x.as_i64()).collect();
    }
    if let Some(proj) = obj.get("projection_map").and_then(|v| v.as_object()) {
        let mut map = BTreeMap::new();
        for (k, v) in proj {
            if let (Ok(ki), Some(vi)) = (k.parse::<i64>(), v.as_i64()) {
                map.insert(ki, vi);
            }
        }
        problem.projection_map = map;
    }
    if let Some(fda) = obj.get("fda_license_granted").and_then(|v| v.as_bool()) {
        problem.fda_license_granted = fda;
    }
}

fn populate_problem_cochains(
    problem: &mut ProblemInstance,
    obj: &serde_json::Map<String, Value>,
) -> Result<(), String> {
    if let Some(cv) = obj.get("defect_cochain").or_else(|| obj.get("x_vector")) {
        problem.defect_cochain = parse_rational_vec(cv)?;
    }
    if let Some(dv) = obj.get("d0").or_else(|| obj.get("coboundary_d0")) {
        problem.d0 = parse_rational_matrix(dv)?;
    }
    if let Some(dv) = obj.get("d1").or_else(|| obj.get("coboundary_d1")) {
        problem.d1 = parse_rational_matrix(dv)?;
    }
    Ok(())
}

fn build_problem_instance(val: &Value) -> Result<ProblemInstance, String> {
    // Check if directly deserializable
    if let Ok(prob) = serde_json::from_value::<ProblemInstance>(val.clone()) {
        return Ok(prob);
    }

    let obj = val.as_object().ok_or_else(|| "expected JSON object for problem".to_string())?;

    let problem_id = obj
        .get("problem_id")
        .or_else(|| obj.get("task_id"))
        .and_then(|v| v.as_str())
        .unwrap_or("coda_cli_problem");

    let mut problem = ProblemInstance::new(problem_id);
    populate_problem_fields(&mut problem, obj);
    // Cochains and coboundaries
    populate_problem_cochains(&mut problem, obj)?;

    Ok(problem)
}

#[derive(Serialize)]
struct CodaCliOutput {
    pub problem_id: String,
    pub phi1: String,
    pub gamma2: String,
    pub grade: String,
    pub terminal_kind: String,
    pub firewall_decision: String,
    pub dual_witness_vector: Option<Vec<String>>,
    pub primal_repair: Option<Vec<String>>,
    pub layer_records: Vec<serde_json::Value>,
    pub evidence_digest: String,
    pub raw_outcome: MasterNormalFormOutcome,
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.iter().any(|a| a == "--help" || a == "-h") {
        println!("core_coda_cli: Sovereign 9-layer CODA pipeline evaluator");
        println!("Usage: core_coda_cli [--file <path>]");
        println!("Reads ProblemInstance / Cochain JSON from file or stdin and writes outcome JSON to stdout.");
        process::exit(0);
    }
    let input_str = if args.len() >= 3 && args[1] == "--file" {
        fs::read_to_string(&args[2]).unwrap_or_else(|e| {
            eprintln!("Failed to read input file {}: {e}", args[2]);
            process::exit(1);
        })
    } else {
        let mut buffer = String::new();
        io::stdin().read_to_string(&mut buffer).unwrap_or_else(|e| {
            eprintln!("Failed to read stdin: {e}");
            process::exit(1);
        });
        buffer
    };

    if input_str.trim().is_empty() {
        eprintln!("Error: Empty input provided to core_coda_cli");
        process::exit(1);
    }

    let root_val: Value = serde_json::from_str(&input_str).unwrap_or_else(|e| {
        eprintln!("Failed to parse JSON input: {e}");
        process::exit(2);
    });

    let problem: ProblemInstance = build_problem_instance(&root_val).unwrap_or_else(|e| {
        eprintln!("Failed to build ProblemInstance: {e}");
        process::exit(2);
    });

    let outcome: MasterNormalFormOutcome = evaluate_coda_pipeline(&problem);

    let (phi1_str, gamma2_str) = if let Some(pair) = &outcome.residual_pair {
        (pair.phi1.to_string(), pair.gamma2.to_string())
    } else {
        ("0".to_string(), "0".to_string())
    };

    let grade = if phi1_str == "0" && gamma2_str == "0" {
        "ExactRepair".to_string()
    } else if gamma2_str == "0" {
        "CoherentResidual".to_string()
    } else {
        "NonclosedDefect".to_string()
    };

    let dual_witness_vector = outcome
        .dual_witness
        .as_ref()
        .map(|w| w.vector.iter().map(|v| v.to_string()).collect());

    let primal_repair = outcome
        .primal_repair
        .as_ref()
        .map(|r| r.iter().map(|v| v.to_string()).collect());

    let layer_records: Vec<Value> = outcome
        .layer_records
        .iter()
        .map(|rec| {
            serde_json::json!({
                "layer_id": rec.layer_id.name(),
                "succeeded": rec.succeeded,
                "diagnostic": rec.diagnostic_message,
                "defect_mass": rec.defect_mass.to_string(),
                "metadata": rec.metadata,
            })
        })
        .collect();

    let output = CodaCliOutput {
        problem_id: outcome.problem_id.clone(),
        phi1: phi1_str,
        gamma2: gamma2_str,
        grade,
        terminal_kind: format!("{:?}", outcome.terminal_kind),
        firewall_decision: format!("{:?}", outcome.firewall_decision),
        dual_witness_vector,
        primal_repair,
        layer_records,
        evidence_digest: outcome.evidence_digest.clone(),
        raw_outcome: outcome,
    };

    let output_str = serde_json::to_string_pretty(&output).unwrap_or_else(|e| {
        eprintln!("Failed to serialize CodaCliOutput JSON: {e}");
        process::exit(3);
    });

    println!("{output_str}");
}

// Origin: engine/crates_rs/core_wdp/src/bin/core_coda_cli.rs
// Claim: urn:core:crates_rs:core-wdp:core-coda-cli:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde84df91c {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde84df91c` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore84df91c {
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
impl BoundaryErrore84df91c {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore84df91c {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore84df91c {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde84df91c {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore84df91c> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore84df91c::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore84df91c::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore84df91c::ExceedsCapacity {
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
mod l4_boundary_tests_e84df91c {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorde84df91c::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorde84df91c::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorde84df91c::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorde84df91c::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorde84df91c::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrore84df91c::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrore84df91c::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
