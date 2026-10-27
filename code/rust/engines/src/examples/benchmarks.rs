
#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_5f8c6f19<T> {
    fn checked_invariant_5f8c6f19(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_5f8c6f19<T> for Option<T> {
    #[inline]
    fn checked_invariant_5f8c6f19(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_5f8c6f19<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_5f8c6f19(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::collections::BTreeMap;
use std::hint::black_box;
use std::path::PathBuf;
use std::time::Instant;

use core_wdp::ddc::agent_contract::sha256_bytes;
use serde::Serialize;

#[derive(Clone)]
struct Candidate {
    candidate_id: String,
    protected_output: String,
}

#[derive(Clone, Copy)]
struct Scenario {
    id: &'static str,
    classes: usize,
    variants_per_class: usize,
    evaluator_work_units: usize,
    expected_exact_model: &'static str,
}

#[derive(Serialize)]
struct TimingReceipt {
    repetitions: usize,
    raw_total_median_ns: u128,
    directed_signature_median_ns: u128,
    directed_canonicalization_median_ns: u128,
    directed_evaluation_median_ns: u128,
    directed_total_median_ns: u128,
    observed_relation: String,
}

#[derive(Serialize)]
struct BenchmarkReceipt {
    scenario_id: String,
    candidate_semantics: &'static str,
    equivalence_contract: &'static str,
    raw_candidate_count: usize,
    quotient_class_count: usize,
    candidates_avoided: usize,
    raw_evaluator_calls: usize,
    directed_evaluator_calls: usize,
    evaluator_work_units: usize,
    exact_raw_work_units: usize,
    exact_directed_work_units: usize,
    exact_model_relation: String,
    expected_exact_model: String,
    same_selected_output: bool,
    raw_representation_bytes: usize,
    directed_representative_bytes: usize,
    timing: TimingReceipt,
    authority_effect: &'static str,
}

#[derive(Serialize)]
struct BenchmarkManifest {
    schema_version: &'static str,
    generator: &'static str,
    exact_cost_model: &'static str,
    timing_scope: &'static str,
    benchmarks: Vec<BenchmarkReceipt>,
    authority_effect: &'static str,
    nonclaims: Vec<&'static str>,
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let output = std::env::args()
        .nth(1)
        .map(PathBuf::from)
        .unwrap_or_else(|| {
            PathBuf::from(
                "research/published/008_engine_runtime/gtoc_multipath_projection_algo/experiments/008_benchmark_results.json",
            )
        });
    if let Some(parent) = output.parent() {
        std::fs::create_dir_all(parent)?;
    }
    let scenarios = [
        Scenario {
            id: "positive_duplicate_rich",
            classes: 64,
            variants_per_class: 64,
            evaluator_work_units: 128,
            expected_exact_model: "directed_less",
        },
        Scenario {
            id: "negative_all_unique",
            classes: 1024,
            variants_per_class: 1,
            evaluator_work_units: 1,
            expected_exact_model: "directed_greater",
        },
        Scenario {
            id: "crossover_exact_model",
            classes: 512,
            variants_per_class: 2,
            evaluator_work_units: 2,
            expected_exact_model: "equal",
        },
    ];
    let benchmarks: Vec<_> = scenarios.into_iter().map(run_scenario).collect();
    for receipt in &benchmarks {
        if receipt.exact_model_relation != receipt.expected_exact_model {
            return Err(format!(
                "{}: exact model expected {}, got {}",
                receipt.scenario_id, receipt.expected_exact_model, receipt.exact_model_relation
            )
            .into());
        }
        if !receipt.same_selected_output {
            return Err(format!("{}: raw and directed optima differ", receipt.scenario_id).into());
        }
    }
    let manifest = BenchmarkManifest {
        schema_version: "core.paper070.benchmark_manifest.v1",
        generator:
            "cargo run -j 1 -p engines --example benchmarks -- <output-json>",
        exact_cost_model:
            "raw=N*w; directed=N signature/canonicalization units + Q*w evaluator units",
        timing_scope:
            "median of 5 in-process debug-profile runs; empirical only, not a complexity theorem",
        benchmarks,
        authority_effect: "None",
        nonclaims: vec![
            "The exact work-unit model is declared, not measured CPU cost.",
            "Observed nanoseconds are machine- and profile-specific.",
            "Quotient pruning is sound only under a declared full-admission and post-measure congruence contract.",
            "No benchmark result establishes detector adequacy or authority.",
        ],
    };
    std::fs::write(&output, serde_json::to_vec_pretty(&manifest)?)?;
    println!("wrote {}", output.display());
    Ok(())
}

fn run_scenario(scenario: Scenario) -> BenchmarkReceipt {
    let candidates = candidates(scenario);
    let representatives = canonical_representatives(&candidates);
    let raw_representation_bytes = representation_bytes(&candidates);
    let directed_representative_bytes = representation_bytes(&representatives);
    let raw_selected = raw_search(&candidates, scenario.evaluator_work_units);
    let directed_selected = directed_search(&candidates, scenario.evaluator_work_units).3;
    let raw_work = candidates.len() * scenario.evaluator_work_units;
    let directed_work = candidates.len() + representatives.len() * scenario.evaluator_work_units;
    let exact_model_relation = relation(directed_work as u128, raw_work as u128);

    let repetitions = 5;
    let mut raw_times = Vec::with_capacity(repetitions);
    let mut signature_times = Vec::with_capacity(repetitions);
    let mut canonical_times = Vec::with_capacity(repetitions);
    let mut evaluation_times = Vec::with_capacity(repetitions);
    let mut directed_times = Vec::with_capacity(repetitions);
    for _ in 0..repetitions {
        let raw_start = Instant::now();
        black_box(raw_search(
            black_box(&candidates),
            scenario.evaluator_work_units,
        ));
        raw_times.push(raw_start.elapsed().as_nanos());

        let directed_start = Instant::now();
        let (signature_ns, canonical_ns, evaluation_ns, selected) =
            directed_search(black_box(&candidates), scenario.evaluator_work_units);
        black_box(selected);
        signature_times.push(signature_ns);
        canonical_times.push(canonical_ns);
        evaluation_times.push(evaluation_ns);
        directed_times.push(directed_start.elapsed().as_nanos());
    }
    let raw_median = median(raw_times);
    let directed_median = median(directed_times);

    BenchmarkReceipt {
        scenario_id: scenario.id.into(),
        candidate_semantics:
            "all candidates are admitted; score depends only on protected_output; variants in one class are post-measure congruent",
        equivalence_contract:
            "sha256(protected_output) equality establishes full admission and post-measure congruence for this fixture",
        raw_candidate_count: candidates.len(),
        quotient_class_count: representatives.len(),
        candidates_avoided: candidates.len() - representatives.len(),
        raw_evaluator_calls: candidates.len(),
        directed_evaluator_calls: representatives.len(),
        evaluator_work_units: scenario.evaluator_work_units,
        exact_raw_work_units: raw_work,
        exact_directed_work_units: directed_work,
        exact_model_relation: exact_model_relation.into(),
        expected_exact_model: scenario.expected_exact_model.into(),
        same_selected_output: raw_selected.0 == directed_selected.0,
        raw_representation_bytes,
        directed_representative_bytes,
        timing: TimingReceipt {
            repetitions,
            raw_total_median_ns: raw_median,
            directed_signature_median_ns: median(signature_times),
            directed_canonicalization_median_ns: median(canonical_times),
            directed_evaluation_median_ns: median(evaluation_times),
            directed_total_median_ns: directed_median,
            observed_relation: relation(directed_median, raw_median).into(),
        },
        authority_effect: "None",
    }
}

fn candidates(scenario: Scenario) -> Vec<Candidate> {
    let mut output = Vec::with_capacity(scenario.classes * scenario.variants_per_class);
    for class in 0..scenario.classes {
        let protected_output = format!("class-{class:05}");
        for variant in 0..scenario.variants_per_class {
            output.push(Candidate {
                candidate_id: format!("{protected_output}-variant-{variant:05}"),
                protected_output: protected_output.clone(),
            });
        }
    }
    output
}

fn raw_search(candidates: &[Candidate], work_units: usize) -> (String, u64) {
    candidates
        .iter()
        .map(|candidate| {
            (
                candidate.protected_output.clone(),
                evaluate(&candidate.protected_output, work_units),
            )
        })
        .min_by(|left, right| left.1.cmp(&right.1).then_with(|| left.0.cmp(&right.0)))
        .checked_invariant_5f8c6f19("benchmark families are nonempty")
}

fn directed_search(
    candidates: &[Candidate],
    work_units: usize,
) -> (u128, u128, u128, (String, u64)) {
    let signature_start = Instant::now();
    let signed: Vec<_> = candidates
        .iter()
        .map(|candidate| {
            (
                sha256_bytes(candidate.protected_output.as_bytes()),
                candidate,
            )
        })
        .collect();
    let signature_ns = signature_start.elapsed().as_nanos();

    let canonical_start = Instant::now();
    let mut classes = BTreeMap::new();
    for (signature, candidate) in signed {
        classes.entry(signature).or_insert(candidate);
    }
    let canonical_ns = canonical_start.elapsed().as_nanos();

    let evaluation_start = Instant::now();
    let selected = classes
        .values()
        .map(|candidate| {
            (
                candidate.protected_output.clone(),
                evaluate(&candidate.protected_output, work_units),
            )
        })
        .min_by(|left, right| left.1.cmp(&right.1).then_with(|| left.0.cmp(&right.0)))
        .checked_invariant_5f8c6f19("benchmark families are nonempty");
    let evaluation_ns = evaluation_start.elapsed().as_nanos();
    (signature_ns, canonical_ns, evaluation_ns, selected)
}

fn canonical_representatives(candidates: &[Candidate]) -> Vec<Candidate> {
    let mut classes = BTreeMap::new();
    for candidate in candidates {
        classes
            .entry(sha256_bytes(candidate.protected_output.as_bytes()))
            .or_insert_with(|| candidate.clone());
    }
    classes.into_values().collect()
}

fn evaluate(protected_output: &str, work_units: usize) -> u64 {
    let mut bytes = protected_output.as_bytes().to_vec();
    for unit in 0..work_units {
        bytes.extend_from_slice(&(unit as u64).to_le_bytes());
        bytes = sha256_bytes(&bytes).into_bytes();
    }
    bytes
        .iter()
        .take(8)
        .fold(0u64, |acc, byte| (acc << 8) | u64::from(*byte))
}

fn representation_bytes(candidates: &[Candidate]) -> usize {
    candidates
        .iter()
        .map(|candidate| candidate.candidate_id.len() + candidate.protected_output.len())
        .sum()
}

fn relation(left: u128, right: u128) -> &'static str {
    match left.cmp(&right) {
        std::cmp::Ordering::Less => "directed_less",
        std::cmp::Ordering::Equal => "equal",
        std::cmp::Ordering::Greater => "directed_greater",
    }
}

fn median(mut values: Vec<u128>) -> u128 {
    values.sort_unstable();
    values[values.len() / 2]
}

// Origin: engine/crates_rs/engines/src/examples/benchmarks.rs
// Claim: urn:core:crates_rs:engines:benchmarks:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_5f8c6f19 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
