//! Executable bounded predicates for 22 primary and three empirical PFP gates.
//! Missing finite witnesses HOLD. The optional process profile authenticates
//! configured host observations; no diagnostic result grants execution authority.
#[path = "kernel_observation.rs"]
mod kernel_observation;
#[path = "process_observation.rs"]
mod process_observation;
use crate::evidence::{canonical_rational, is_sha256_ref, parse_exact_rational, sha256_ref};
use crate::exact::integer;
use crate::intergates;
use crate::stage::exact::rational;
use crate::stage::ports::Refusal;
use crate::wire_json::python_ascii_json;
use num_bigint::BigInt;
use num_rational::BigRational as Q;
use num_traits::{One, Signed, ToPrimitive, Zero};
use regex::Regex;
use serde_json::{json, Map, Value};
use std::collections::BTreeSet;
type Fields = Map<String, Value>;
type GateResult = Result<Value, Refusal>;
struct Spec {
    id: &'static str,
    name: &'static str,
    bytes: &'static [u8],
    index: usize,
    required: &'static [&'static str],
}
pub const IDS: [&str; 25] = [
    "PFP-01-SYNTAX-PREFILTER",
    "PFP-02-DEFECT-HUNTER",
    "PFP-03-GAUGE-BREAKER",
    "PFP-04-SCOPE-GUARD",
    "PFP-05-BACKDOOR-AUDITOR",
    "PFP-06-PRIMAL-DUAL",
    "PFP-07-MANUSCRIPT-TRUTH",
    "PFP-08-SCAR-CHRONICLER",
    "PFP-09-ANTI-HYPE",
    "PFP-10-BOUNDARY-FUZZER",
    "PFP-11-QUARANTINE",
    "PFP-12-INTEGRITY-AUDITOR",
    "PFP-13-REALITY-GATE",
    "PFP-14-CONTEXT-TRANSPORT",
    "PFP-15-BARE-METAL-ANCHOR",
    "PFP-16-RESILIENCE",
    "PFP-17-OVERCONFIDENCE-PROBE",
    "PFP-18-PUNCHLIST",
    "PFP-19-CUSTODY",
    "PFP-20-COVERT-VERIFIER",
    "PFP-21-TRUTH-REPAIR",
    "PFP-22-HARDWARE-CONSTRAINT",
    "PFP-EMP-GATE-001",
    "PFP-EMP-GATE-002",
    "PFP-EMP-GATE-003",
];
static SPECS: [Spec;25] = [
    Spec {id:"PFP-01-SYNTAX-PREFILTER",name:"Syntax Prefilter Cold Syntax Pre-Filter (Prime 000 Admission)",index:1,bytes:include_bytes!("../../../../pfp/infrastructure/yaml/gates/01_cold_syntax.yaml"),required:&["packet_id","is_admitted","candidate_content","carrier","omega","d0","d1"]},
    Spec {id:"PFP-02-DEFECT-HUNTER",name:"Defect Hunter Nocebo Plunge (LGGR Defect Hunter)",index:2,bytes:include_bytes!("../../../../pfp/infrastructure/yaml/gates/02_nocebo_plunge.yaml"),required:&["carrier","omega","d0","d1"]},
    Spec {id:"PFP-03-GAUGE-BREAKER",name:"Gauge Breaker 9-Dot Gauge Break (Class Lambda Licensed Lift)",index:3,bytes:include_bytes!("../../../../pfp/infrastructure/yaml/gates/03_gauge_break.yaml"),required:&["round_number","residual_history","lift_requested"]},
    Spec {id:"PFP-04-SCOPE-GUARD",name:"Scope Guard Scope & Resource Assassin",index:4,bytes:include_bytes!("../../../../pfp/infrastructure/yaml/gates/04_scope_assassin.yaml"),required:&["round_number","vertex_count","edge_count","face_count","estimated_cost_usd","wire_packet_utf8"]},
    Spec {id:"PFP-05-BACKDOOR-AUDITOR",name:"Backdoor Auditor Zero-Backdoor Annihilator",index:5,bytes:include_bytes!("../../../../pfp/infrastructure/yaml/gates/05_terminal_gaze.yaml"),required:&["core_types","random_seed_declared","random_seed","solver_method","carrier","omega","d0","d1"]},
    Spec {id:"PFP-06-PRIMAL-DUAL",name:"Primal Dual Primal-Dual Cochain Evaluator",index:6,bytes:include_bytes!("../../../../pfp/infrastructure/yaml/gates/06_primal_dual.yaml"),required:&["carrier","omega","d0","d1","alpha","dual_witness","ordered_basis","tie_break_certificates"]},
    Spec {id:"PFP-07-MANUSCRIPT-TRUTH",name:"Manuscript Truth Constructive Mechanization (Manuscript Truth)",index:7,bytes:include_bytes!("../../../../pfp/infrastructure/yaml/gates/07_manuscript_truth_manuscript_truth.yaml"),required:&["claim_statement","has_mechanized_proof","proof_kernel","proof_artifact_utf8","proof_artifact_sha256","proof_execution"]},
    Spec {id:"PFP-08-SCAR-CHRONICLER",name:"Scar Chronicler Lamarckian Scar Chronicler",index:8,bytes:include_bytes!("../../../../pfp/infrastructure/yaml/gates/08_scar_chronicler.yaml"),required:&["candidate_hash","candidate_content","prior_scar_ledger","active_obstruction_id","repair_targets"]},
    Spec {id:"PFP-09-ANTI-HYPE",name:"Anti-Hype Anti-Hype Razor (WDP Demarcation)",index:9,bytes:include_bytes!("../../../../pfp/infrastructure/yaml/gates/09_anti_hype.yaml"),required:&["candidate_prose","claim_tier","receipt_attached","receipt_utf8","receipt_sha256","claim_scope","evidence_scope"]},
    Spec {id:"PFP-10-BOUNDARY-FUZZER",name:"Boundary Fuzzer Sunflower Oil Spill (Boundary Perturbation Fuzzer)",index:10,bytes:include_bytes!("../../../../pfp/infrastructure/yaml/gates/10_oil_spill.yaml"),required:&["carrier","omega","d0","d1","alpha","dual_witness","ordered_basis","tie_break_certificates","fuzz_iterations","perturbations"]},
    Spec {id:"PFP-11-QUARANTINE",name:"Quarantine Psychiatric Quarantine (DDC Class M Refusal)",index:11,bytes:include_bytes!("../../../../pfp/infrastructure/yaml/gates/11_quarantine.yaml"),required:&["agent_state","observed_behavior","cycle_count","residual_descent_observed"]},
    Spec {id:"PFP-12-INTEGRITY-AUDITOR",name:"Integrity Auditor Anti-Cowardice Audit (Integrity Guardian)",index:12,bytes:include_bytes!("../../../../pfp/infrastructure/yaml/gates/12_anti_cowardice.yaml"),required:&["pipeline_stage","prior_stage_status","has_mock_injection","skipped_checks","suppressed_errors"]},
    Spec {id:"PFP-13-REALITY-GATE",name:"Adversary Master Reality Gatekeeper",index:13,bytes:include_bytes!("../../../../pfp/infrastructure/yaml/gates/13_terminal_reality.yaml"),required:&["packet_id","phi1","gamma2","is_refused","refusal_code","carrier","omega","d0","d1","alpha","dual_witness","ordered_basis","tie_break_certificates","checker_receipt_hex","checker_receipt_verdict","candidate_content"]},
    Spec {id:"PFP-14-CONTEXT-TRANSPORT",name:"Context Transport Fast-Path Context Transport (Preservation Guardian)",index:14,bytes:include_bytes!("../../../../pfp/infrastructure/yaml/gates/14_context_transport.yaml"),required:&["snapshot_id","origin_payload_utf8","origin_checksum","payload_utf8","payload_checksum","origin_coordinates","retained_coordinates","dropped_coordinates"]},
    Spec {id:"PFP-15-BARE-METAL-ANCHOR",name:"Bare-Metal Solver & Bare-Metal Reality Anchor",index:15,bytes:include_bytes!("../../../../pfp/infrastructure/yaml/gates/15_ground_reality.yaml"),required:&["candidate_id","has_executable_test","runtime_exit_code","abstract_bloat_score","has_mock_injection","executable_utf8","executable_sha256","execution_log_utf8","execution_log_sha256","observed_executable_sha256"]},
    Spec {id:"PFP-16-RESILIENCE",name:"Resilience Practical Resilience & Crisis Resolution Anchor",index:16,bytes:include_bytes!("../../../../pfp/infrastructure/yaml/gates/16_resilience.yaml"),required:&["crisis_severity","core_state_intact","recovery_attempts","recovery_budget","core_before_utf8","core_before_sha256","core_after_utf8","core_after_sha256","fallback_utf8","fallback_sha256"]},
    Spec {id:"PFP-17-OVERCONFIDENCE-PROBE",name:"Overconfidence Probe Lateral Gauge-Breaker & Overconfidence Probe",index:17,bytes:include_bytes!("../../../../pfp/infrastructure/yaml/gates/17_gauge_breaker.yaml"),required:&["candidate_id","self_confidence_score","machine_receipt_present","detected_circularities","machine_receipt_utf8","machine_receipt_sha256"]},
    Spec {id:"PFP-18-PUNCHLIST",name:"Punchlist Methodical Precision & Punchlist Discipline",index:18,bytes:include_bytes!("../../../../pfp/infrastructure/yaml/gates/18_discipline.yaml"),required:&["task_list_id","open_obligations_count","certified_receipts","obligations"]},
    Spec {id:"PFP-19-CUSTODY",name:"Custody Unyielding Record Keeper & Custody Auditor",index:19,bytes:include_bytes!("../../../../pfp/infrastructure/yaml/gates/19_custody_custody.yaml"),required:&["journal_chain_root","observed_tip_hash","citations","chain_entries","citation_artifacts"]},
    Spec {id:"PFP-20-COVERT-VERIFIER",name:"Covert Verifier Covert Verification & Asynchronous Execution Auditor",index:20,bytes:include_bytes!("../../../../pfp/infrastructure/yaml/gates/20_covert_verification.yaml"),required:&["task_id","reported_status","os_exit_code","process_terminated","log_output_utf8","log_output_hash"]},
    Spec {id:"PFP-21-TRUTH-REPAIR",name:"Truth Repair Radical Invariance & Truth Repair",index:21,bytes:include_bytes!("../../../../pfp/infrastructure/yaml/gates/21_truth_repair.yaml"),required:&["candidate_id","detected_defect","proposed_repair","invariants_preserved","sibling_invariants_before","sibling_invariants_after","original_fences","repaired_fences","checker_receipt_hex","checker_receipt_verdict","candidate_content"]},
    Spec {id:"PFP-22-HARDWARE-CONSTRAINT",name:"Hardware Constraint Brute Hardware & Resource Constraint",index:22,bytes:include_bytes!("../../../../pfp/infrastructure/yaml/gates/22_hardware_constraint.yaml"),required:&["task_pid","elapsed_seconds","timeout_ceiling_seconds","resident_memory_bytes","memory_limit_bytes"]},
    Spec {id:"PFP-EMP-GATE-001",name:"Batched Token Amortization Gate",index:23,bytes:include_bytes!("../../../../pfp/infrastructure/yaml/gates/empirical/01_token_amortization_gate.yaml"),required:&["batch_size_k","marginal_token_symbolic","marginal_token_raw","total_batched_symbolic_tokens","total_batched_raw_tokens","batch_observations"]},
    Spec {id:"PFP-EMP-GATE-002",name:"Prompt Injection Containment Rate Gate",index:24,bytes:include_bytes!("../../../../pfp/infrastructure/yaml/gates/empirical/02_injection_containment_gate.yaml"),required:&["total_injection_trials","successful_containments","containment_rate"]},
    Spec {id:"PFP-EMP-GATE-003",name:"E-Graph Equational Constraint Preservation Gate",index:25,bytes:include_bytes!("../../../../pfp/infrastructure/yaml/gates/empirical/03_egraph_preservation_gate.yaml"),required:&["total_rewrites","dropped_constraints","constraint_loss_rate","constraints_before","constraints_after"]},
];
pub fn known_gate_id(id: &str) -> bool {
    IDS.contains(&id)
}

/// Compile-time primary-gate selection over the existing executable predicates.
///
/// A marker proves only that this validator is available in this build. Missing
/// evidence still HOLDs; neither a selected Rust type nor a PASS grants authority.
/// Historical dynamic evaluation and its canonical receipt bytes are unchanged.
pub mod typed {
    use crate::stage::ports::Refusal;
    use serde_json::Value;

    mod sealed {
        pub trait Sealed {}
    }

    pub trait PrimaryGateValidator: sealed::Sealed {
        const ID: &'static str;
    }

    pub fn evaluate<G: PrimaryGateValidator>(
        payload: &Value,
        history_edges: &[String],
    ) -> Result<Value, Refusal> {
        super::evaluate(G::ID, payload, history_edges)
    }

    macro_rules! primary_validators {
        ($($name:ident => $id:literal),+ $(,)?) => {
            $(
                #[derive(Debug, Clone, Copy)]
                pub struct $name;
                impl sealed::Sealed for $name {}
                impl PrimaryGateValidator for $name {
                    const ID: &'static str = $id;
                }
            )+

            /// Runtime wire adapter for exactly the compiled primary selectors.
            pub fn evaluate_by_id(
                gate_id: &str,
                payload: &Value,
                history_edges: &[String],
            ) -> Result<Value, Refusal> {
                match gate_id {
                    $($id => evaluate::<$name>(payload, history_edges),)+
                    _ => Err(super::err("GATE_SPEC_NOT_FOUND", "unknown typed primary gate ID")),
                }
            }
        };
    }

    primary_validators! {
        SyntaxPrefilter => "PFP-01-SYNTAX-PREFILTER",
        DefectHunter => "PFP-02-DEFECT-HUNTER",
        GaugeBreaker => "PFP-03-GAUGE-BREAKER",
        ScopeGuard => "PFP-04-SCOPE-GUARD",
        BackdoorAuditor => "PFP-05-BACKDOOR-AUDITOR",
        PrimalDual => "PFP-06-PRIMAL-DUAL",
        ManuscriptTruth => "PFP-07-MANUSCRIPT-TRUTH",
        ScarChronicler => "PFP-08-SCAR-CHRONICLER",
        AntiHype => "PFP-09-ANTI-HYPE",
        BoundaryFuzzer => "PFP-10-BOUNDARY-FUZZER",
        Quarantine => "PFP-11-QUARANTINE",
        IntegrityAuditor => "PFP-12-INTEGRITY-AUDITOR",
        Adversary => "PFP-13-REALITY-GATE",
        ContextTransport => "PFP-14-CONTEXT-TRANSPORT",
        BareMetalAnchor => "PFP-15-BARE-METAL-ANCHOR",
        Resilience => "PFP-16-RESILIENCE",
        OverconfidenceProbe => "PFP-17-OVERCONFIDENCE-PROBE",
        Punchlist => "PFP-18-PUNCHLIST",
        Custody => "PFP-19-CUSTODY",
        CovertVerifier => "PFP-20-COVERT-VERIFIER",
        TruthRepair => "PFP-21-TRUTH-REPAIR",
        HardwareConstraint => "PFP-22-HARDWARE-CONSTRAINT",
    }
}

// Origin: engine/crates_rs/core_adversary/src/primary_gates.rs
// Claim: urn:core:crates_rs:core-adversary:primary-gates:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod typed_validator_tests {
    use super::*;

    fn same<G: typed::PrimaryGateValidator>(payload: &Value) {
        assert_eq!(
            typed::evaluate::<G>(payload, &[]).unwrap(),
            evaluate(G::ID, payload, &[]).unwrap()
        );
    }

    #[test]
    fn typed_primary_selection_preserves_all_existing_empty_holds() {
        let payload = json!({});
        same::<typed::SyntaxPrefilter>(&payload);
        same::<typed::DefectHunter>(&payload);
        same::<typed::GaugeBreaker>(&payload);
        same::<typed::ScopeGuard>(&payload);
        same::<typed::BackdoorAuditor>(&payload);
        same::<typed::PrimalDual>(&payload);
        same::<typed::ManuscriptTruth>(&payload);
        same::<typed::ScarChronicler>(&payload);
        same::<typed::AntiHype>(&payload);
        same::<typed::BoundaryFuzzer>(&payload);
        same::<typed::Quarantine>(&payload);
        same::<typed::IntegrityAuditor>(&payload);
        same::<typed::Adversary>(&payload);
        same::<typed::ContextTransport>(&payload);
        same::<typed::BareMetalAnchor>(&payload);
        same::<typed::Resilience>(&payload);
        same::<typed::OverconfidenceProbe>(&payload);
        same::<typed::Punchlist>(&payload);
        same::<typed::Custody>(&payload);
        same::<typed::CovertVerifier>(&payload);
        same::<typed::TruthRepair>(&payload);
        same::<typed::HardwareConstraint>(&payload);
        for gate_id in &IDS[..22] {
            assert_eq!(
                typed::evaluate_by_id(gate_id, &payload, &[]).unwrap()["status"],
                "HOLD"
            );
        }
    }

    #[test]
    fn typed_selection_reuses_success_and_refusal_not_a_boolean_wrapper() {
        let mut payload = json!({"pipeline_stage":1,"prior_stage_status":"PASS",
            "has_mock_injection":false,"skipped_checks":[],"suppressed_errors":[]});
        same::<typed::IntegrityAuditor>(&payload);
        assert_eq!(
            typed::evaluate::<typed::IntegrityAuditor>(&payload, &[]).unwrap()["status"],
            "PASS"
        );
        payload["has_mock_injection"] = json!(true);
        same::<typed::IntegrityAuditor>(&payload);
        assert_eq!(
            typed::evaluate::<typed::IntegrityAuditor>(&payload, &[]).unwrap()["status"],
            "REFUSE"
        );
        for unknown in ["PFP-UNKNOWN", "PFP-EMP-GATE-001"] {
            assert_eq!(
                typed::evaluate_by_id(unknown, &payload, &[])
                    .unwrap_err()
                    .code,
                "GATE_SPEC_NOT_FOUND"
            );
        }
    }
}
fn err(code: &str, message: impl Into<String>) -> Refusal {
    let mut value = Refusal::new(code, message);
    value.locus = "core_adversary.primary_gates".into();
    value
}
fn hold(field: &str) -> Refusal {
    err(
        "GATE_WITNESS_UNMEASURED",
        format!("Required witness unavailable: {field}"),
    )
}
fn invalid(field: &str) -> Refusal {
    err(
        "GATE_PAYLOAD_INVALID",
        format!("Malformed witness: {field}"),
    )
}
fn require<'a>(p: &'a Fields, key: &str) -> Result<&'a Value, Refusal> {
    p.get(key).filter(|v| !v.is_null()).ok_or_else(|| hold(key))
}
fn object<'a>(v: &'a Value, key: &str) -> Result<&'a Fields, Refusal> {
    v.as_object().ok_or_else(|| invalid(key))
}
fn text<'a>(p: &'a Fields, key: &str) -> Result<&'a str, Refusal> {
    require(p, key)?
        .as_str()
        .filter(|s| !s.trim().is_empty())
        .ok_or_else(|| invalid(key))
}
fn flag(p: &Fields, key: &str) -> Result<bool, Refusal> {
    require(p, key)?.as_bool().ok_or_else(|| invalid(key))
}
fn list<'a>(p: &'a Fields, key: &str) -> Result<&'a Vec<Value>, Refusal> {
    require(p, key)?.as_array().ok_or_else(|| invalid(key))
}
fn uint(p: &Fields, key: &str) -> Result<BigInt, Refusal> {
    integer(require(p, key)?)
        .filter(|n| n >= &BigInt::zero())
        .ok_or_else(|| invalid(key))
}
fn count(p: &Fields, key: &str) -> Result<usize, Refusal> {
    uint(p, key)?.to_usize().ok_or_else(|| invalid(key))
}
fn scalar(v: &Value) -> Result<Q, Refusal> {
    parse_exact_rational(v).map_err(|r| err("NON_RATIONAL_FIELD", r.message))
}
fn metric(p: &Fields, key: &str) -> Result<Q, Refusal> {
    match require(p, key)? {
        Value::Number(n) => rational(&n.to_string()),
        Value::String(s) => rational(s),
        _ => None,
    }
    .ok_or_else(|| invalid(key))
}
fn strings(p: &Fields, key: &str) -> Result<Vec<String>, Refusal> {
    list(p, key)?
        .iter()
        .map(|v| {
            v.as_str()
                .filter(|s| !s.trim().is_empty())
                .map(str::to_owned)
                .ok_or_else(|| invalid(key))
        })
        .collect()
}
fn check(ok: bool, code: &str, detail: &str) -> Result<(), Refusal> {
    if ok {
        Ok(())
    } else {
        Err(err(code, detail))
    }
}
fn digest(p: &Fields, key: &str) -> Result<String, Refusal> {
    let v = require(p, key)?;
    check(is_sha256_ref(v), "GATE_PAYLOAD_INVALID", key)?;
    Ok(v.as_str().ok_or_else(|| invalid(key))?.into())
}
fn artifact<'a>(p: &'a Fields, body: &str, hash: &str) -> Result<&'a str, Refusal> {
    let content = text(p, body)?;
    check(
        sha256_ref(content.as_bytes()) == digest(p, hash)?,
        "ARTIFACT_DIGEST_MISMATCH",
        body,
    )?;
    Ok(content)
}
fn vector(v: &Value, label: &str) -> Result<Vec<Q>, Refusal> {
    let a = v.as_array().ok_or_else(|| invalid(label))?;
    check(a.len() <= 128, "COMPLEXITY_EXCEEDED", label)?;
    a.iter().map(scalar).collect()
}
fn matrix(v: &Value, label: &str) -> Result<Vec<Vec<Q>>, Refusal> {
    let a = v.as_array().ok_or_else(|| invalid(label))?;
    check(a.len() <= 128, "COMPLEXITY_EXCEEDED", label)?;
    let rows = a
        .iter()
        .map(|row| vector(row, label))
        .collect::<Result<Vec<_>, _>>()?;
    let width = rows.first().map_or(0, Vec::len);
    check(
        rows.iter().all(|row| row.len() == width),
        "MAP_UNDEFINED",
        "ragged boundary matrix",
    )?;
    Ok(rows)
}
fn norm(v: &[Q]) -> Q {
    v.iter().map(Signed::abs).sum()
}
fn dot(a: &[Q], b: &[Q]) -> Q {
    a.iter().zip(b).map(|(x, y)| x * y).sum()
}
fn product(a: &[Vec<Q>], x: &[Q], width: usize) -> Result<Vec<Q>, Refusal> {
    check(
        a.iter().all(|row| row.len() == width) && x.len() == width,
        "MAP_UNDEFINED",
        "matrix/vector dimensions disagree",
    )?;
    Ok(a.iter().map(|row| dot(row, x)).collect())
}
fn req_vector(p: &Fields, key: &'static str) -> Result<Vec<Q>, Refusal> {
    vector(require(p, key)?, key)
}
fn req_matrix(p: &Fields, key: &'static str) -> Result<Vec<Vec<Q>>, Refusal> {
    matrix(require(p, key)?, key)
}
fn req_object<'a>(p: &'a Fields, key: &'static str) -> Result<&'a Fields, Refusal> {
    object(require(p, key)?, key)
}
fn req_scalar(p: &Fields, key: &'static str) -> Result<Q, Refusal> {
    scalar(require(p, key)?)
}
fn carrier_counts(p: &Fields) -> Result<(usize, usize, usize), Refusal> {
    let carrier = req_object(p, "carrier")?;
    Ok((
        list(carrier, "vertices")?.len(),
        list(carrier, "edges")?.len(),
        list(carrier, "faces")?.len(),
    ))
}
fn complex(p: &Fields) -> Result<(Vec<Q>, Vec<Vec<Q>>, Vec<Vec<Q>>), Refusal> {
    let w = req_vector(p, "omega")?;
    let d0 = req_matrix(p, "d0")?;
    let d1 = req_matrix(p, "d1")?;
    let (n, m, f) = carrier_counts(p)?;
    check_complex_bounds(&w, &d0, &d1, n, m, f)?;
    check_complex_nilpotency(&d0, &d1, n)?;
    Ok((w, d0, d1))
}

fn check_complex_bounds(
    w: &[Q],
    d0: &[Vec<Q>],
    d1: &[Vec<Q>],
    n: usize,
    m: usize,
    f: usize,
) -> Result<(), Refusal> {
    let within_limits = [n <= 64, m <= 128, f <= 64].into_iter().all(|b| b);
    check(
        within_limits,
        "COMPLEXITY_EXCEEDED",
        "carrier exceeds 64/128/64 cells",
    )?;
    let dims_ok = [
        w.len() == m,
        d0.len() == m,
        d0.iter().all(|r| r.len() == n),
        d1.len() == f,
        d1.iter().all(|r| r.len() == m),
    ]
    .into_iter()
    .all(|b| b);
    check(
        dims_ok,
        "MAP_UNDEFINED",
        "carrier/boundary dimensions disagree",
    )
}

fn check_complex_nilpotency(d0: &[Vec<Q>], d1: &[Vec<Q>], n: usize) -> Result<(), Refusal> {
    for row in d1 {
        for j in 0..n {
            let column = d0.iter().map(|r| r[j].clone()).collect::<Vec<_>>();
            check(
                dot(row, &column).is_zero(),
                "MAP_UNDEFINED",
                "d1 d0 is nonzero",
            )?;
        }
    }
    Ok(())
}
fn summary(p: &Fields, key: &str) -> Result<(), Refusal> {
    let s = text(p, key)?.to_lowercase();
    for part in [
        "what it supports",
        "what it does not support",
        "narrowest defensible claim",
        "next test needed",
    ] {
        check(s.contains(part), "SUMMARY_PART_MISSING", part)?;
    }
    Ok(())
}
fn checker(p: &Fields) -> Result<(), Refusal> {
    require(p, "checker_receipt_hex")?;
    require(p, "candidate_content")?;
    require(p, "checker_receipt_verdict")?;
    if let Some((code, detail)) = intergates::verify_checker_binding(p) {
        return Err(err(code, detail));
    }
    Ok(())
}
fn syntax_prefilter(p: &Fields) -> GateResult {
    text(p, "packet_id")?;
    check(
        flag(p, "is_admitted")?,
        "UNADMITTED_PACKET",
        "admission must precede measurement",
    )?;
    let prose = text(p, "candidate_content")?.to_lowercase();
    for filler in [
        "certainly!",
        "i would be happy to help",
        "of course!",
        "as an ai language model",
    ] {
        check(
            !prose.contains(filler),
            "POLICY_VIOLATION",
            "conversational filler",
        )?;
    }
    complex(p)?;
    Ok(json!({"admission_precedes_measurement":true,"boundary_nilpotency_checked":true}))
}
fn defect_hunter(p: &Fields) -> GateResult {
    let (w, _, d1) = complex(p)?;
    let flux = product(&d1, &w, w.len())?;
    let gamma = norm(&flux);
    check(
        gamma.is_zero(),
        "LGGR_DEFECT_DETECTED",
        "global face coboundary nonzero: OpenObstruction, Delta_E=-1",
    )?;
    Ok(
        json!({"gamma2":canonical_rational(&gamma),"checked_face_flux":flux.iter().map(canonical_rational).collect::<Vec<_>>()}),
    )
}
fn gauge_breaker(p: &Fields) -> GateResult {
    uint(p, "round_number")?;
    let history = vector(require(p, "residual_history")?, "residual_history")?;
    let stagnant = history.len() >= 3
        && history[history.len() - 3..]
            .windows(2)
            .all(|x| x[0] == x[1]);
    let requested = match p.get("lift_requested") {
        Some(v) => v.as_bool().ok_or_else(|| invalid("lift_requested"))?,
        None => false,
    };
    if stagnant || requested {
        return Err(hold("licensed lift: independent obstruction/domain-exhaustion/comparison-map/progress certificate"));
    }
    Ok(json!({"stagnation_triggered":false,"lift_applied":false}))
}
fn scope_guard(p: &Fields) -> GateResult {
    for (key, limit) in [
        ("round_number", 10),
        ("vertex_count", 64),
        ("edge_count", 128),
        ("face_count", 64),
    ] {
        check(
            uint(p, key)? <= BigInt::from(limit),
            "COMPLEXITY_EXCEEDED",
            key,
        )?;
    }
    let cost = metric(p, "estimated_cost_usd")?;
    check(
        cost >= Q::zero() && cost <= Q::new(1.into(), 100.into()),
        "RESOURCE_EXHAUSTED",
        "estimated spend exceeds one cent",
    )?;
    let wire = text(p, "wire_packet_utf8")?;
    check(
        wire.len() <= 65_536,
        "RESOURCE_EXHAUSTED",
        "wire exceeds 64 KiB",
    )?;
    Ok(
        json!({"estimated_cost_usd":canonical_rational(&cost),"wire_bytes":wire.len(),"billed_cost_verified":false}),
    )
}
fn backdoor_auditor(p: &Fields) -> GateResult {
    let kinds = strings(p, "core_types")?;
    check(
        kinds
            .iter()
            .all(|s| ["int", "integer", "Fraction", "rational"].contains(&s.as_str())),
        "NON_RATIONAL_FIELD",
        "cochains require exact rationals",
    )?;
    check(
        flag(p, "random_seed_declared")?,
        "BACKDOOR_DETECTED",
        "replay seed required",
    )?;
    uint(p, "random_seed")?;
    let method = text(p, "solver_method")?.to_lowercase();
    check(
        ![
            "gradient",
            "continuous",
            "relaxation",
            "heuristic",
            "random_search",
        ]
        .iter()
        .any(|s| method.contains(s)),
        "BACKDOOR_DETECTED",
        "continuous/unreplayable method",
    )?;
    let (w, d0, d1) = complex(p)?;
    Ok(
        json!({"exact_values_checked":w.len()+d0.iter().map(Vec::len).sum::<usize>()+d1.iter().map(Vec::len).sum::<usize>()}),
    )
}

// Exact LP dual bounds on successive residual coordinates over the L1 optimum
// face. z=e_j+u-v+prefix(mu); u,v>=0, lambda=u+v, d0^T z=0.
fn parse_usize_permutation(
    items: &[Value],
    field: &str,
    len: usize,
) -> Result<Vec<usize>, Refusal> {
    let basis = items
        .iter()
        .map(|v| {
            integer(v)
                .and_then(|n| n.to_usize())
                .ok_or_else(|| invalid(field))
        })
        .collect::<Result<Vec<_>, _>>()?;
    let expected = (0..len).collect::<BTreeSet<_>>();
    let is_perm = basis.len() == len && basis.iter().copied().collect::<BTreeSet<_>>() == expected;
    if !is_perm {
        return Err(err(
            "TIER_CERTIFICATE_INVALID",
            "basis must be exact edge permutation",
        ));
    }
    Ok(basis)
}

fn tie_r(p: &Fields, w: &[Q], d0: &[Vec<Q>], h: &[Q], phi: &Q) -> Result<(), Refusal> {
    let basis = parse_usize_permutation(list(p, "ordered_basis")?, "ordered_basis", w.len())?;
    let certificates = list(p, "tie_break_certificates")?;
    check(
        certificates.len() == basis.len(),
        "TIER_CERTIFICATE_INVALID",
        "one bound per residual coordinate required",
    )?;
    let n = d0.first().map_or(0, Vec::len);
    for (step, item) in certificates.iter().enumerate() {
        verify_tie_step(step, item, &basis, w, d0, h, phi, n)?;
    }
    Ok(())
}

#[allow(clippy::too_many_arguments)]
fn verify_tie_step(
    step: usize,
    item: &Value,
    basis: &[usize],
    w: &[Q],
    d0: &[Vec<Q>],
    h: &[Q],
    phi: &Q,
    n: usize,
) -> Result<(), Refusal> {
    let c = object(item, "tie_break_certificates")?;
    let u = req_vector(c, "upper")?;
    let v = req_vector(c, "lower")?;
    let mu = req_vector(c, "prefix")?;
    let lambda = req_scalar(c, "norm_multiplier")?;
    check_tie_multipliers(&u, &v, &mu, &lambda, w.len(), step)?;
    let mut z = u.iter().zip(&v).map(|(a, b)| a - b).collect::<Vec<_>>();
    z[basis[step]] += Q::one();
    for (i, q) in mu.iter().enumerate() {
        z[basis[i]] += q;
    }
    check_zero_d0_transpose(
        d0,
        &z,
        n,
        "TIER_CERTIFICATE_INVALID",
        "alpha stationarity failed",
    )?;
    let prefix: Q = mu.iter().enumerate().map(|(i, q)| q * &h[basis[i]]).sum();
    let bound = dot(&z, w) - &lambda * phi - prefix;
    check(
        bound == h[basis[step]],
        "TIER_CERTIFICATE_INVALID",
        "sequential lower bound does not match residual coordinate",
    )
}

fn check_tie_multipliers(
    u: &[Q],
    v: &[Q],
    mu: &[Q],
    lambda: &Q,
    w_len: usize,
    step: usize,
) -> Result<(), Refusal> {
    let dims_ok = [u.len() == w_len, v.len() == w_len, mu.len() == step]
        .into_iter()
        .all(|b| b);
    check(
        dims_ok,
        "TIER_CERTIFICATE_INVALID",
        "dual dimensions disagree",
    )?;
    check(
        u.iter().chain(v).all(|q| q >= &Q::zero()),
        "TIER_CERTIFICATE_INVALID",
        "negative inequality multiplier",
    )?;
    check(
        u.iter().zip(v).all(|(a, b)| &(a + b) == lambda),
        "TIER_CERTIFICATE_INVALID",
        "norm stationarity failed",
    )
}

fn check_zero_d0_transpose(
    d0: &[Vec<Q>],
    vec: &[Q],
    n: usize,
    code: &'static str,
    msg: &'static str,
) -> Result<(), Refusal> {
    for j in 0..n {
        let column = d0.iter().map(|r| r[j].clone()).collect::<Vec<_>>();
        check(dot(&column, vec).is_zero(), code, msg)?;
    }
    Ok(())
}

fn primal_dual(p: &Fields) -> GateResult {
    let (w, d0, d1) = complex(p)?;
    let alpha = req_vector(p, "alpha")?;
    let (n, _, _) = carrier_counts(p)?;
    let image = product(&d0, &alpha, n)?;
    let h = w.iter().zip(image).map(|(a, b)| a - b).collect::<Vec<_>>();
    let phi = norm(&h);
    let gamma = norm(&product(&d1, &w, w.len())?);
    verify_primal_dual_dual(p, &w, &d0, n, &phi, &gamma)?;
    tie_r(p, &w, &d0, &h, &phi)?;
    Ok(
        json!({"phi1":canonical_rational(&phi),"gamma2":canonical_rational(&gamma),"primal_dual_gap":"0","tier_verified":true,"residual":h.iter().map(canonical_rational).collect::<Vec<_>>()}),
    )
}

fn verify_primal_dual_dual(
    p: &Fields,
    w: &[Q],
    d0: &[Vec<Q>],
    n: usize,
    phi: &Q,
    gamma: &Q,
) -> Result<(), Refusal> {
    let y = vector(require(p, "dual_witness")?, "dual_witness")?;
    let valid_norm = y.len() == w.len() && y.iter().all(|q| q.abs() <= Q::one());
    check(
        valid_norm,
        "DUAL_CERTIFICATE_INVALID",
        "dual infinity norm/dimension invalid",
    )?;
    check_zero_d0_transpose(d0, &y, n, "DUAL_CERTIFICATE_INVALID", "d0^T y nonzero")?;
    check(
        &dot(&y, w) == phi,
        "DUAL_CERTIFICATE_INVALID",
        "primal-dual gap nonzero",
    )?;
    check_optional_scalar(p, "phi1", phi, "Phi1 differs from replay")?;
    check_optional_scalar(p, "gamma2", gamma, "Gamma2 differs from replay")
}

fn check_optional_scalar(
    p: &Fields,
    key: &str,
    expected: &Q,
    msg: &'static str,
) -> Result<(), Refusal> {
    if let Some(v) = p.get(key) {
        check(&scalar(v)? == expected, "MEASUREMENT_MISMATCH", msg)?;
    }
    Ok(())
}

fn master(p: &Fields) -> GateResult {
    let claim = text(p, "claim_statement")?;
    check(
        flag(p, "has_mechanized_proof")?,
        "UNMECHANIZED_SPECULATION",
        "mechanized proof absent",
    )?;
    let kernel = text(p, "proof_kernel")?;
    check(
        ["lean4", "rust_oracle"].contains(&kernel),
        "PROOF_KERNEL_UNSUPPORTED",
        "unknown kernel",
    )?;
    let body = artifact(p, "proof_artifact_utf8", "proof_artifact_sha256")?;
    verify_master_proof_body_and_exec(p, claim, body)?;
    Err(hold("authenticated proof-kernel observation; payload bytes alone cannot authenticate kernel execution"))
}

fn verify_master_proof_body_and_exec(p: &Fields, claim: &str, body: &str) -> Result<(), Refusal> {
    let forbidden = Regex::new(r"\b(sorry|admit|axiom)\b").map_err(|e| invalid(&e.to_string()))?;
    check(
        !forbidden.is_match(body),
        "UNCHECKED_AXIOM",
        "unchecked proof marker",
    )?;
    let observed = req_object(p, "proof_execution")?;
    check(
        integer(require(observed, "exit_code")?) == Some(BigInt::zero()),
        "PROOF_KERNEL_FAILED",
        "kernel exit observation nonzero",
    )?;
    let art_ok = digest(observed, "artifact_sha256")? == sha256_ref(body.as_bytes());
    let claim_ok = digest(observed, "claim_sha256")? == sha256_ref(claim.as_bytes());
    check(
        [art_ok, claim_ok].into_iter().all(|b| b),
        "PROOF_BINDING_MISMATCH",
        "kernel observation binds different claim/artifact",
    )?;
    artifact(observed, "log_utf8", "log_sha256")?;
    Ok(())
}

fn scar_chronicler(p: &Fields) -> GateResult {
    let hash = digest(p, "candidate_hash")?;
    check(
        hash == sha256_ref(text(p, "candidate_content")?.as_bytes()),
        "ARTIFACT_DIGEST_MISMATCH",
        "candidate hash mismatch",
    )?;
    check_scar_ledger(p, &hash)?;
    if let Some(Value::String(id)) = p.get("active_obstruction_id") {
        check(
            strings(p, "repair_targets")?.contains(id),
            "SCAR_REPAIR_UNTARGETED",
            "active defect not targeted",
        )?;
    }
    Ok(json!({"known_candidate_replay":false,"ledger_custody":"owning_journal_port"}))
}

fn check_scar_ledger(p: &Fields, hash: &str) -> Result<(), Refusal> {
    for item in list(p, "prior_scar_ledger")? {
        let scar = object(item, "prior_scar_ledger")?;
        let old = digest(scar, "candidate_hash")?;
        text(scar, "obstruction_id")?;
        check(
            old != hash,
            "KNOWN_OBSTRUCTION",
            "exact rejected candidate repeated",
        )?;
    }
    Ok(())
}

fn anti_hype(p: &Fields) -> GateResult {
    summary(p, "candidate_prose")?;
    let tier = uint(p, "claim_tier")?;
    let tier_ok = tier >= BigInt::one() && tier <= BigInt::from(4);
    check(tier_ok, "CLAIM_TIER_INVALID", "WDP tier must be 1..4")?;
    check(
        flag(p, "receipt_attached")?,
        "CLAIM_ARTIFACT_REQUIRED",
        "scope needs an artifact",
    )?;
    artifact(p, "receipt_utf8", "receipt_sha256")?;
    verify_anti_hype_scope(p)?;
    Ok(
        json!({"claim_tier_preserved":tier.to_string(),"scope_relation_verified":true,"natural_language_truth_verified":false,"keyword_matches_alone_determine_tier":false}),
    )
}

fn verify_anti_hype_scope(p: &Fields) -> Result<(), Refusal> {
    let claim = strings(p, "claim_scope")?
        .into_iter()
        .collect::<BTreeSet<_>>();
    let evidence = strings(p, "evidence_scope")?
        .into_iter()
        .collect::<BTreeSet<_>>();
    check(
        claim.is_subset(&evidence),
        "UNSUPPORTED_SCOPE_PROMOTION",
        "declared claim exceeds artifact scope",
    )
}

fn boundary_fuzzer(p: &Fields) -> GateResult {
    let baseline = primal_dual(p)?;
    let (w, d0, d1) = complex(p)?;
    let iterations = count(p, "fuzz_iterations")?;
    let cases = list(p, "perturbations")?;
    let count_ok = [iterations > 0, iterations <= 64, cases.len() == iterations]
        .into_iter()
        .all(|b| b);
    check(
        count_ok,
        "PERTURBATION_EVIDENCE_INVALID",
        "one replay per declared perturbation required",
    )?;
    for case in cases {
        verify_boundary_fuzzer_case(case, &w, &d0, &d1)?;
    }
    Ok(
        json!({"finite_perturbations_verified":iterations,"baseline_primal_dual":baseline,"scope":"declared signed edge permutations"}),
    )
}

fn verify_boundary_fuzzer_case(
    case: &Value,
    w: &[Q],
    d0: &[Vec<Q>],
    d1: &[Vec<Q>],
) -> Result<(), Refusal> {
    let c = object(case, "perturbations")?;
    let permutation =
        parse_usize_permutation(list(c, "edge_permutation")?, "edge_permutation", w.len())
            .map_err(|_| err("PERTURBATION_EVIDENCE_INVALID", "invalid permutation"))?;
    let signs = vector(require(c, "edge_signs")?, "edge_signs")?;
    let signs_ok = signs.len() == w.len() && signs.iter().all(|s| s.abs() == Q::one());
    check(
        signs_ok,
        "PERTURBATION_EVIDENCE_INVALID",
        "signs must be +/-1",
    )?;
    check_boundary_fuzzer_moved(c, &permutation, &signs, w, d0, d1)
}

fn check_boundary_fuzzer_moved(
    c: &Fields,
    permutation: &[usize],
    signs: &[Q],
    w: &[Q],
    d0: &[Vec<Q>],
    d1: &[Vec<Q>],
) -> Result<(), Refusal> {
    let moved_w = vector(require(c, "omega")?, "omega")?;
    let moved_d0 = matrix(require(c, "d0")?, "d0")?;
    let moved_d1 = matrix(require(c, "d1")?, "d1")?;
    let expected_w = permutation
        .iter()
        .enumerate()
        .map(|(i, j)| &signs[i] * &w[*j])
        .collect::<Vec<_>>();
    let expected_d0 = permutation
        .iter()
        .enumerate()
        .map(|(i, j)| d0[*j].iter().map(|x| &signs[i] * x).collect::<Vec<_>>())
        .collect::<Vec<_>>();
    let expected_d1 = d1
        .iter()
        .map(|row| {
            permutation
                .iter()
                .enumerate()
                .map(|(i, j)| &signs[i] * &row[*j])
                .collect::<Vec<_>>()
        })
        .collect::<Vec<_>>();
    let rep_ok = [
        moved_w == expected_w,
        moved_d0 == expected_d0,
        moved_d1 == expected_d1,
    ]
    .into_iter()
    .all(|b| b);
    check(
        rep_ok,
        "ORIENTATION_INVARIANCE_FAILED",
        "perturbation does not preserve signed chain representation",
    )?;
    check(
        norm(&product(&moved_d1, &moved_w, w.len())?) == norm(&product(d1, w, w.len())?),
        "ORIENTATION_INVARIANCE_FAILED",
        "Gamma2 changed under signed permutation",
    )
}

fn quarantine(p: &Fields) -> GateResult {
    let state = text(p, "agent_state")?;
    text(p, "observed_behavior")?;
    let cycles = uint(p, "cycle_count")?;
    if [
        "infinite_regress",
        "carrier_regress",
        "difference_regress",
        "ungrounded_origin",
    ]
    .contains(&state)
    {
        return Err(err(
            "CARRIER_REGRESS",
            "ungrounded carrier/difference regression",
        ));
    }
    if [
        "infinite_loop",
        "circular_dependency",
        "uncomputable",
        "hallucination",
    ]
    .contains(&state)
    {
        return Err(err(
            "CIRCULAR_DEPENDENCY",
            "pathological typed state quarantined",
        ));
    }
    check(
        ["ready", "stable", "running", "recovering", "halted"].contains(&state),
        "BEHAVIOR_UNCLASSIFIED",
        "unknown behavior classification",
    )?;
    if cycles >= BigInt::from(2) {
        check(
            flag(p, "residual_descent_observed")?,
            "CIRCULAR_DEPENDENCY",
            "repeated attempts without progress",
        )?;
    }
    Ok(json!({"typed_state":state,"ddc_letter_m_required":false}))
}
fn integrity_auditor(p: &Fields) -> GateResult {
    uint(p, "pipeline_stage")?;
    check(
        !flag(p, "has_mock_injection")?,
        "COWARDICE_DETECTED",
        "mock injection at exact boundary",
    )?;
    check(
        ["PASS", "ACCEPTED", "COMPLETED"].contains(&text(p, "prior_stage_status")?),
        "COWARDICE_DETECTED",
        "upstream non-success cannot become completion",
    )?;
    check(
        strings(p, "skipped_checks")?.is_empty(),
        "COWARDICE_DETECTED",
        "required checks skipped",
    )?;
    check(
        strings(p, "suppressed_errors")?.is_empty(),
        "COWARDICE_DETECTED",
        "upstream errors suppressed",
    )?;
    Ok(json!({"upstream_success_preserved":true}))
}
fn adversary(p: &Fields) -> GateResult {
    text(p, "packet_id")?;
    if flag(p, "is_refused")? {
        return Err(err(text(p, "refusal_code")?, "upstream refusal retained"));
    }
    checker(p)?;
    let replay = primal_dual(p)?;
    let phi = req_scalar(p, "phi1")?;
    let gamma = req_scalar(p, "gamma2")?;
    let classification = classify_cochain(&phi, &gamma);
    Ok(
        json!({"cochain_class":classification,"replayed_witnesses":replay,"checker_authentication":"owning_checker_port","classification_is_not_execution_authority":true}),
    )
}

fn classify_cochain(phi: &Q, gamma: &Q) -> &'static str {
    if gamma > &Q::zero() {
        "OpenObstruction"
    } else if phi > &Q::zero() {
        "StabilizedSurvivor"
    } else {
        "Exact"
    }
}

pub const PROMPT_TRANSPORT_POOL_PROFILE: &str = "adversary.pfp-transport-pool.v2";

fn context_transport(p: &Fields) -> GateResult {
    if let Some(profile) = p.get("transport_profile") {
        return context_transport_pool(p, profile);
    }
    context_transport_legacy(p)
}

fn context_transport_pool(p: &Fields, profile: &Value) -> GateResult {
    check(
        profile.as_str() == Some(PROMPT_TRANSPORT_POOL_PROFILE),
        "GATE_TRANSPORT_PROFILE_INVALID",
        "unsupported prompt transport profile",
    )?;
    let no_mixed = !p.contains_key("origin_payload_utf8") && !p.contains_key("payload_utf8");
    check(
        no_mixed,
        "GATE_PAYLOAD_INVALID",
        "mixed prompt transport representations",
    )?;
    let (pool, origin, received) = extract_pool_indices(p)?;
    let mut expanded = p.clone();
    expanded.remove("transport_profile");
    expanded.insert("origin_payload_utf8".into(), json!(pool[origin]));
    expanded.insert("payload_utf8".into(), json!(pool[received]));
    let mut witness = context_transport_legacy(&expanded)?;
    witness
        .as_object_mut()
        .ok_or_else(|| invalid("prompt_transport_witness"))?
        .insert(
            "transport_profile".into(),
            json!(PROMPT_TRANSPORT_POOL_PROFILE),
        );
    Ok(witness)
}

fn extract_pool_indices(p: &Fields) -> Result<(Vec<String>, usize, usize), Refusal> {
    let pool = strings(p, "payload_pool_utf8")?;
    let origin = count(p, "origin_payload_index")?;
    let received = count(p, "payload_index")?;
    let valid_occ = [
        origin == 0,
        matches!(pool.len(), 1 | 2),
        received < pool.len(),
    ]
    .into_iter()
    .all(|b| b);
    check(
        valid_occ,
        "GATE_PAYLOAD_INVALID",
        "invalid prompt transport occurrences",
    )?;
    let valid_ref = match (pool.len(), received) {
        (1, 0) => true,
        (2, 1) => pool[0] != pool[1],
        _ => false,
    };
    check(
        valid_ref,
        "GATE_PAYLOAD_INVALID",
        "duplicate or unreferenced prompt transport text",
    )?;
    Ok((pool, origin, received))
}

fn context_transport_legacy(p: &Fields) -> GateResult {
    text(p, "snapshot_id")?;
    let origin = artifact(p, "origin_payload_utf8", "origin_checksum")?;
    let received = artifact(p, "payload_utf8", "payload_checksum")?;
    check(
        origin.as_bytes() == received.as_bytes(),
        "CONTEXT_TRANSPORT_CORRUPTED",
        "context bytes changed",
    )?;
    check(
        strings(p, "dropped_coordinates")?.is_empty(),
        "CONTEXT_TRANSPORT_CORRUPTED",
        "coordinates dropped",
    )?;
    let expected = strings(p, "origin_coordinates")?
        .into_iter()
        .collect::<BTreeSet<_>>();
    let retained = strings(p, "retained_coordinates")?
        .into_iter()
        .collect::<BTreeSet<_>>();
    check(
        expected == retained,
        "CONTEXT_TRANSPORT_CORRUPTED",
        "retained coordinates differ from origin",
    )?;
    Ok(json!({"lossless_bytes_verified":true,"coordinates_verified":retained.len()}))
}
fn bare_metal_anchor(p: &Fields) -> GateResult {
    text(p, "candidate_id")?;
    check(
        flag(p, "has_executable_test")?,
        "NON_EXECUTABLE_THEORY",
        "executable absent",
    )?;
    check(
        integer(require(p, "runtime_exit_code")?) == Some(BigInt::zero()),
        "NON_EXECUTABLE_THEORY",
        "runtime exit observation nonzero",
    )?;
    check(
        !flag(p, "has_mock_injection")?,
        "NON_EXECUTABLE_THEORY",
        "mock execution is not live evidence",
    )?;
    verify_bare_metal_anchor_artifacts(p)?;
    Err(hold("authenticated process execution observation; caller-supplied exit/log fields are not OS authority"))
}

fn verify_bare_metal_anchor_artifacts(p: &Fields) -> Result<(), Refusal> {
    let content = artifact(p, "executable_utf8", "executable_sha256")?;
    artifact(p, "execution_log_utf8", "execution_log_sha256")?;
    check(
        digest(p, "observed_executable_sha256")? == sha256_ref(content.as_bytes()),
        "EXECUTION_BINDING_MISMATCH",
        "observation belongs to different executable",
    )?;
    let score = metric(p, "abstract_bloat_score")?;
    let in_range = score >= Q::zero() && score <= Q::one();
    check(
        in_range,
        "GATE_PAYLOAD_INVALID",
        "bloat score outside 0..1; no invented threshold",
    )
}

fn resilience(p: &Fields) -> GateResult {
    let crisis = text(p, "crisis_severity")?;
    check(
        flag(p, "core_state_intact")?,
        "EQUILIBRIUM_COLLAPSE",
        "core compromised",
    )?;
    let before = artifact(p, "core_before_utf8", "core_before_sha256")?;
    let after = artifact(p, "core_after_utf8", "core_after_sha256")?;
    check(
        before == after,
        "EQUILIBRIUM_COLLAPSE",
        "peripheral failure changed core bytes",
    )?;
    verify_resilience_recovery(p, crisis, before)?;
    Ok(json!({"core_bytes_preserved":true,"recovery_within_budget":true}))
}

fn verify_resilience_recovery(p: &Fields, crisis: &str, before: &str) -> Result<(), Refusal> {
    let attempts = uint(p, "recovery_attempts")?;
    let budget = uint(p, "recovery_budget")?;
    check(
        attempts <= budget,
        "EQUILIBRIUM_COLLAPSE",
        "recovery budget exceeded",
    )?;
    if ["transient", "network", "timeout"].contains(&crisis) && attempts.is_zero() {
        return Err(hold("bounded transient recovery observation"));
    }
    check(
        ["none", "transient", "network", "timeout", "critical"].contains(&crisis),
        "GATE_PAYLOAD_INVALID",
        "unknown crisis classification",
    )?;
    if crisis == "critical" {
        check(
            artifact(p, "fallback_utf8", "fallback_sha256")? == before,
            "EQUILIBRIUM_COLLAPSE",
            "fallback changed core state",
        )?;
    }
    Ok(())
}

fn overconfidence_probe(p: &Fields) -> GateResult {
    text(p, "candidate_id")?;
    let confidence = metric(p, "self_confidence_score")?;
    let in_range = confidence >= Q::zero() && confidence <= Q::one();
    check(in_range, "GATE_PAYLOAD_INVALID", "confidence outside 0..1")?;
    verify_overconfidence_probe_receipt(p, &confidence)?;
    Ok(json!({"confidence":canonical_rational(&confidence),"gauge_rotation_required":false}))
}

fn verify_overconfidence_probe_receipt(p: &Fields, confidence: &Q) -> Result<(), Refusal> {
    let receipt = flag(p, "machine_receipt_present")?;
    let ok_conf = confidence <= &Q::new(19.into(), 20.into()) || receipt;
    check(
        ok_conf,
        "GAUGE_ROTATION_REQUIRED",
        "high confidence lacks receipt",
    )?;
    check(
        strings(p, "detected_circularities")?.is_empty(),
        "GAUGE_ROTATION_REQUIRED",
        "circular reasoning requires gauge rotation",
    )?;
    if receipt {
        artifact(p, "machine_receipt_utf8", "machine_receipt_sha256")?;
    }
    Ok(())
}

fn punchlist(p: &Fields) -> GateResult {
    text(p, "task_list_id")?;
    check(
        uint(p, "open_obligations_count")?.is_zero(),
        "UNRESOLVED_OBLIGATION",
        "declared obligations open",
    )?;
    let rows = list(p, "obligations")?;
    let certificates = strings(p, "certified_receipts")?
        .into_iter()
        .collect::<BTreeSet<_>>();
    let mut closed: BTreeSet<String> = BTreeSet::new();
    let mut observed = BTreeSet::new();
    for row in rows {
        verify_punchlist_row(row, &mut closed, &mut observed)?;
    }
    check(
        observed == certificates,
        "UNRESOLVED_OBLIGATION",
        "certified receipts differ from verified obligations",
    )?;
    Ok(json!({"closed_obligations":closed.len(),"dependency_order_verified":true}))
}

fn verify_punchlist_row(
    row: &Value,
    closed: &mut BTreeSet<String>,
    observed: &mut BTreeSet<String>,
) -> Result<(), Refusal> {
    let item = object(row, "obligations")?;
    let id = text(item, "id")?;
    check(
        !closed.contains(id),
        "UNRESOLVED_OBLIGATION",
        "duplicate obligation",
    )?;
    check(
        text(item, "status")? == "CLOSED",
        "UNRESOLVED_OBLIGATION",
        "actual obligation not closed",
    )?;
    check(
        strings(item, "dependencies")?
            .iter()
            .all(|d| closed.contains(d)),
        "UNRESOLVED_OBLIGATION",
        "dependency not yet verified",
    )?;
    verify_punchlist_receipt(item, id, observed)?;
    closed.insert(id.to_string());
    Ok(())
}

fn verify_punchlist_receipt(
    item: &Fields,
    id: &str,
    observed: &mut BTreeSet<String>,
) -> Result<(), Refusal> {
    let body = artifact(item, "artifact_utf8", "artifact_sha256")?;
    let receipt = artifact(item, "receipt_utf8", "receipt_sha256")?;
    let parsed: Value = intergates::unique_json(receipt.as_bytes())?;
    let valid_binding = [
        parsed["obligation_id"] == id,
        parsed["artifact_sha256"] == sha256_ref(body.as_bytes()),
        parsed["status"] == "CLOSED",
    ]
    .into_iter()
    .all(|b| b);
    check(
        valid_binding,
        "UNRESOLVED_OBLIGATION",
        "receipt binds different obligation/artifact/status",
    )?;
    observed.insert(digest(item, "receipt_sha256")?);
    Ok(())
}

fn verify_levy_chain_entry(row: &Value, previous: &str) -> Result<String, Refusal> {
    let item = object(row, "chain_entries")?;
    let raw = artifact(item, "record_utf8", "record_sha256")?;
    let value: Value = intergates::unique_json(raw.as_bytes())?;
    check(
        value["prev_sha256"] == previous,
        "CHAIN_OF_CUSTODY_BROKEN",
        "chain link mismatch",
    )?;
    digest(item, "record_sha256")
}

fn levy(p: &Fields) -> GateResult {
    let mut previous = digest(p, "journal_chain_root")?;
    let retained = digest(p, "observed_tip_hash")?;
    let entries = list(p, "chain_entries")?;
    for row in entries {
        previous = verify_levy_chain_entry(row, &previous)?;
    }
    check(
        previous == retained,
        "CHAIN_OF_CUSTODY_BROKEN",
        "chain does not reach retained tip",
    )?;
    verify_levy_citations(p)?;
    Ok(
        json!({"verified_entries":entries.len(),"verified_tip":previous,"profile":"raw-record-utf8-sha256-prev-field-v1","tip_authentication":"independently_retained_host_input"}),
    )
}

fn verify_levy_citations(p: &Fields) -> Result<(), Refusal> {
    let cited = strings(p, "citations")?
        .into_iter()
        .collect::<BTreeSet<_>>();
    let mut resolved = BTreeSet::new();
    for row in list(p, "citation_artifacts")? {
        let item = object(row, "citation_artifacts")?;
        let id = text(item, "citation_id")?;
        artifact(item, "content_utf8", "content_sha256")?;
        check(
            resolved.insert(id.to_owned()),
            "CHAIN_OF_CUSTODY_BROKEN",
            "duplicate citation",
        )?;
    }
    check(
        cited == resolved,
        "CHAIN_OF_CUSTODY_BROKEN",
        "citation bytes do not cover declared citation set",
    )
}

fn covert_verifier(p: &Fields) -> GateResult {
    text(p, "task_id")?;
    let status = text(p, "reported_status")?;
    let exit = integer(require(p, "os_exit_code")?).ok_or_else(|| invalid("os_exit_code"))?;
    check(
        flag(p, "process_terminated")?,
        "FALSE_GREEN_DETECTED",
        "child remains live",
    )?;
    let _log = artifact(p, "log_output_utf8", "log_output_hash")?;
    check_covert_verifier_exit(status, &exit)?;
    Err(hold(
        "authenticated OS process termination observation from the owning host port",
    ))
}

fn check_covert_verifier_exit(status: &str, exit: &BigInt) -> Result<(), Refusal> {
    if ["PASS", "COMPLETED", "ACCEPTED"].contains(&status) {
        check(
            exit.is_zero(),
            "FALSE_GREEN_DETECTED",
            "success disagrees with OS exit",
        )?;
    }
    check(
        exit.is_zero(),
        "PROCESS_EXECUTION_FAILED",
        "child process failed",
    )
}

fn truth_repair(p: &Fields) -> GateResult {
    text(p, "candidate_id")?;
    text(p, "detected_defect")?;
    object(require(p, "proposed_repair")?, "proposed_repair")?;
    check(
        flag(p, "invariants_preserved")?,
        "TRUTH_REPAIR_INADMISSIBLE",
        "broken invariant reported",
    )?;
    verify_truth_repair_fences_and_siblings(p)?;
    checker(p)?;
    Ok(
        json!({"declared_fences_preserved":true,"declared_siblings_preserved":true,"finite_repair_checker_bytes_bound":true}),
    )
}

fn verify_truth_repair_fences_and_siblings(p: &Fields) -> Result<(), Refusal> {
    let before = object(
        require(p, "sibling_invariants_before")?,
        "sibling_invariants_before",
    )?;
    let after = object(
        require(p, "sibling_invariants_after")?,
        "sibling_invariants_after",
    )?;
    check(
        before == after,
        "TRUTH_REPAIR_INADMISSIBLE",
        "valid siblings changed",
    )?;
    check(
        object(require(p, "original_fences")?, "original_fences")?
            == object(require(p, "repaired_fences")?, "repaired_fences")?,
        "TRUTH_REPAIR_INADMISSIBLE",
        "fences changed",
    )
}

fn hardware_constraint(p: &Fields) -> GateResult {
    check(
        uint(p, "task_pid")? > BigInt::zero(),
        "GATE_PAYLOAD_INVALID",
        "PID must be positive",
    )?;
    let elapsed = metric(p, "elapsed_seconds")?;
    let timeout = metric(p, "timeout_ceiling_seconds")?;
    let memory = uint(p, "resident_memory_bytes")?;
    let limit = uint(p, "memory_limit_bytes")?;
    let env_ok = [
        elapsed >= Q::zero(),
        timeout > Q::zero(),
        limit > BigInt::zero(),
    ]
    .into_iter()
    .all(|b| b);
    check(env_ok, "GATE_PAYLOAD_INVALID", "invalid resource envelope")?;
    let within_limits = elapsed <= timeout && memory < limit;
    check(
        within_limits,
        "RESOURCE_LIMIT_EXCEEDED",
        "time/memory envelope breached; host must stop work",
    )?;
    Ok(
        json!({"observed_resources_within_envelope":true,"process_termination_owner":"host_process_port"}),
    )
}

const RESOURCE_PROFILE: &str = "adversary.host-job-resources.v1";
fn resource_observation(p: &Fields) -> GateResult {
    check(
        text(p, "resource_profile")? == RESOURCE_PROFILE,
        "RESOURCE_PROFILE_UNKNOWN",
        "unsupported resource profile",
    )?;
    let record = require(p, "resource_observation")?;
    if record.is_null() {
        return Err(err(
            "GATE_WITNESS_UNMEASURED",
            "no current sandbox observation",
        ));
    }
    let record = object(record, "resource_observation")?;
    let expected = req_object(p, "resource_expected")?;
    verify_resource_context(record, expected)?;
    verify_resource_outcome(record)?;
    verify_resource_measurements(record, expected)?;
    Ok(
        json!({"resource_profile":RESOURCE_PROFILE,"memory_metric":"windows_job_peak_committed_bytes",
        "observed_resources_within_envelope":true,"observation_authenticated":false,
        "scope":"finite host-captured Windows job measurements; not RSS or descendant termination attestation"}),
    )
}

fn verify_resource_context(record: &Fields, expected: &Fields) -> Result<(), Refusal> {
    check(
        object(require(record, "context")?, "context")? == expected,
        "RESOURCE_BINDING_MISMATCH",
        "resource observation belongs to another task/checker/candidate",
    )?;
    for key in [
        "run_id",
        "task_id",
        "source_digest",
        "checker_id",
        "candidate_sha256",
    ] {
        check(
            !text(expected, key)?.is_empty(),
            "RESOURCE_BINDING_MISMATCH",
            "empty task binding",
        )?;
    }
    Ok(())
}

fn verify_resource_outcome(record: &Fields) -> Result<(), Refusal> {
    let outcome = record
        .get("native_outcome")
        .and_then(Value::as_str)
        .unwrap_or("");
    const EXCEEDED: [&str; 5] = [
        "TimedOut",
        "MemoryLimitExceeded",
        "CpuLimitExceeded",
        "OutputLimitExceeded",
        "ProcessLimitExceeded",
    ];
    if EXCEEDED.contains(&outcome) {
        return Err(err(
            "RESOURCE_LIMIT_EXCEEDED",
            format!("sandbox reported {outcome}"),
        ));
    }
    let completed =
        outcome == "Completed" && record.get("failure_code").is_some_and(Value::is_null);
    check(
        completed,
        "GATE_WITNESS_UNMEASURED",
        "sandbox did not yield current complete measurements",
    )
}

fn req_u64(fields: &Fields, key: &str) -> Result<u64, Refusal> {
    require(fields, key)?.as_u64().ok_or_else(|| {
        err(
            "GATE_PAYLOAD_INVALID",
            format!("{key} must be an unsigned JSON integer"),
        )
    })
}

fn verify_resource_measurements(record: &Fields, expected: &Fields) -> Result<(), Refusal> {
    let m = object(require(record, "measurements")?, "measurements")?;
    let meas_ok = [
        m.get("isolation_applied") == Some(&Value::Bool(true)),
        m.get("measurement_error").is_some_and(Value::is_null),
        m.get("memory_bytes").is_some_and(|v| !v.is_null()),
    ]
    .into_iter()
    .all(|b| b);
    check(
        meas_ok,
        "GATE_WITNESS_UNMEASURED",
        "job isolation or memory query unavailable",
    )?;
    check(
        text(m, "memory_metric")? == "windows_job_peak_committed_bytes",
        "RESOURCE_METRIC_MISMATCH",
        "job committed bytes must not be relabelled as RSS",
    )?;
    check_resource_limits(record, m, expected)
}

fn check_resource_limits(record: &Fields, m: &Fields, expected: &Fields) -> Result<(), Refusal> {
    let config = req_object(expected, "configuration")?;
    let timeout = req_u64(config, "timeout_ms")?;
    let limit = req_u64(config, "memory_limit_bytes")?;
    let pid = req_u64(m, "task_pid")?;
    let elapsed = req_u64(m, "elapsed_ms")?;
    let mem = req_u64(m, "memory_bytes")?;
    let pos_ok = [pid > 0, timeout > 0, limit > 0].into_iter().all(|b| b);
    check(
        pos_ok,
        "GATE_PAYLOAD_INVALID",
        "PID and declared limits must be positive",
    )?;
    let within_env = [elapsed <= timeout, mem < limit].into_iter().all(|b| b);
    check(
        within_env,
        "RESOURCE_LIMIT_EXCEEDED",
        "observed time/job committed memory exceeded the declared envelope",
    )?;
    check(
        text(record, "native_result_sha256")?.len() == 64,
        "RESOURCE_BINDING_MISMATCH",
        "retained sandbox response digest required",
    )
}

fn empirical(index: usize, p: &Fields) -> GateResult {
    match index {
        23 => empirical_23(p),
        24 => empirical_24(p),
        25 => empirical_25(p),
        _ => Err(err("GATE_SPEC_NOT_FOUND", "unknown empirical gate")),
    }
}

fn empirical_23(p: &Fields) -> GateResult {
    let k = uint(p, "batch_size_k")?;
    let symbolic = uint(p, "marginal_token_symbolic")?;
    let raw = uint(p, "marginal_token_raw")?;
    let k_ok = [k >= BigInt::from(10), symbolic < raw]
        .into_iter()
        .all(|b| b);
    check(
        k_ok,
        "AMORTIZATION_GATE_FAILED",
        "requires K>=10 and symbolic marginal tokens below raw",
    )?;
    let tot_sym = uint(p, "total_batched_symbolic_tokens")?;
    let tot_raw = uint(p, "total_batched_raw_tokens")?;
    check(
        tot_sym < tot_raw,
        "AMORTIZATION_GATE_FAILED",
        "total symbolic token cost must also be below raw",
    )?;
    check_batch_history(list(p, "batch_observations")?)?;
    Ok(json!({"scope":"supplied finite batch observations","cross_model_generalization":false}))
}

fn check_batch_history(history: &[Value]) -> Result<(), Refusal> {
    check(
        history.len() >= 2,
        "AMORTIZATION_EVIDENCE_INCOMPLETE",
        "two increasing batch observations required",
    )?;
    let mut previous: Option<(BigInt, Q)> = None;
    for row in history {
        let item = object(row, "batch_observations")?;
        let size = uint(item, "batch_size_k")?;
        let marginal = metric(item, "marginal_symbolic_tokens")?;
        check(
            marginal >= Q::zero(),
            "GATE_PAYLOAD_INVALID",
            "negative token count",
        )?;
        if let Some((old, value)) = &previous {
            let dec_ok = size > *old && marginal < *value;
            check(
                dec_ok,
                "AMORTIZATION_GATE_FAILED",
                "marginal cost must decrease with increasing batch size",
            )?;
        }
        previous = Some((size, marginal));
    }
    Ok(())
}

fn empirical_24(p: &Fields) -> GateResult {
    let total = uint(p, "total_injection_trials")?;
    let successes = uint(p, "successful_containments")?;
    let valid_counts = total > BigInt::zero() && successes <= total;
    check(
        valid_counts,
        "GATE_PAYLOAD_INVALID",
        "invalid containment counts",
    )?;
    let rate = Q::new(successes, total);
    check(
        metric(p, "containment_rate")? == rate,
        "MEASUREMENT_MISMATCH",
        "rate differs from exact success/total",
    )?;
    check(
        rate >= Q::new(19.into(), 20.into()),
        "INJECTION_GATE_FAILED",
        "containment below 19/20",
    )?;
    Ok(
        json!({"exact_containment_rate":canonical_rational(&rate),"scope":"supplied finite trials; not universal injection safety"}),
    )
}

fn empirical_25(p: &Fields) -> GateResult {
    let total = uint(p, "total_rewrites")?;
    let dropped = uint(p, "dropped_constraints")?;
    let valid_counts = [total > BigInt::zero(), dropped <= total]
        .into_iter()
        .all(|b| b);
    check(
        valid_counts,
        "GATE_PAYLOAD_INVALID",
        "invalid rewrite counts",
    )?;
    check(
        metric(p, "constraint_loss_rate")? == Q::new(dropped.clone(), total),
        "MEASUREMENT_MISMATCH",
        "loss rate differs from counts",
    )?;
    check(
        dropped.is_zero(),
        "EGRAPH_CONSTRAINT_LOSS",
        "constraint spans dropped",
    )?;
    check(
        req_object(p, "constraints_before")? == req_object(p, "constraints_after")?,
        "EGRAPH_CONSTRAINT_LOSS",
        "exact constraint spans changed",
    )?;
    Ok(
        json!({"constraint_loss":"0","scope":"declared exact constraint spans; not arbitrary semantic equivalence"}),
    )
}

pub fn describe() -> Value {
    json!({"schema":"adversary.pfp.executable-gates.v1","authority_effect":"None","gate_count":25,
        "input_profile":"explicit finite witnesses; reserved _adversary_scene binds execution but supplies no proof",
        "numeric_profile":"exact integer/rational cochains; exact decimal telemetry","statuses":["PASS","HOLD","REFUSE"],
        "process_profiles":[process_observation::PROFILE],
        "kernel_profiles":[kernel_observation::PROFILE],
        "resource_profiles":[RESOURCE_PROFILE],
        "transport_profiles":[PROMPT_TRANSPORT_POOL_PROFILE],
        "gates":SPECS.iter().map(|s|json!({"gate_id":s.id,"name":s.name,"kind":if s.index<=22 {"PrimaryGate"} else {"EmpiricalBenchmarkGate"},"specification_sha256":sha256_ref(s.bytes),"required_witness_fields":s.required,"can_authorize":false})).collect::<Vec<_>>()})
}
pub fn evaluate(gate_id: &str, payload: &Value, history_edges: &[String]) -> GateResult {
    let spec = SPECS
        .iter()
        .find(|s| s.id == gate_id)
        .ok_or_else(|| err("GATE_SPEC_NOT_FOUND", "unknown primary/empirical gate ID"))?;
    intergates::bounded(payload, history_edges)
        .map_err(|r| err("GATE_INPUT_TOO_LARGE", r.message))?;
    let p = object(payload, "gate_payload")?;
    let outcome = dispatch_primary_gate(spec, p);
    let (status, code, detail, witness) = unpack_gate_outcome(outcome);
    let input = python_ascii_json(payload)?;
    let mut receipt = json!({"schema":"adversary.pfp.gate-receipt.v1","gate_id":spec.id,"status":status,"refusal_code":code,
        "diagnostics":detail,"witness":witness,"input_sha256":sha256_ref(input.as_bytes()),
        "input_digest_profile":"python-sorted-spaced-ascii-json-v1","specification_sha256":sha256_ref(spec.bytes),
        "authority_effect":"None","can_authorize":false,"observation_authentication":"owning_host_ports", "general_theorem_verified":false,"diagnostic_only":true,"scope":"finite supplied-witness replay, not source theorem or external observation authentication"});
    decorate_gate_receipt(&mut receipt, spec, p, status);
    Ok(receipt)
}

fn dispatch_primary_gate(spec: &Spec, p: &Fields) -> GateResult {
    if spec.index == 22 && p.contains_key("resource_profile") {
        resource_observation(p)
    } else if matches!(spec.index, 15 | 20) && p.contains_key("process_profile") {
        process_observation::evaluate(spec, p)
    } else if spec.index == 7 && p.contains_key("kernel_profile") {
        kernel_observation::evaluate(spec, p)
    } else {
        dispatch_gate_index(spec.index, p)
    }
}

fn dispatch_gate_index(index: usize, p: &Fields) -> GateResult {
    const HANDLERS: [fn(&Fields) -> GateResult; 22] = [
        syntax_prefilter, defect_hunter, gauge_breaker, scope_guard, backdoor_auditor, primal_dual, master, scar_chronicler, anti_hype,
        boundary_fuzzer, quarantine, integrity_auditor, adversary, context_transport, bare_metal_anchor, resilience, overconfidence_probe, punchlist, levy,
        covert_verifier, truth_repair, hardware_constraint,
    ];
    if (1..=22).contains(&index) {
        HANDLERS[index - 1](p)
    } else if (23..=25).contains(&index) {
        empirical(index, p)
    } else {
        Err(err("GATE_SPEC_NOT_FOUND", "unknown compiled gate index"))
    }
}

fn unpack_gate_outcome(outcome: GateResult) -> (&'static str, Option<String>, String, Value) {
    match outcome {
        Ok(witness) => (
            "PASS",
            None,
            "Supplied finite witnesses passed the implemented predicate".to_string(),
            witness,
        ),
        Err(r) if r.code == "GATE_WITNESS_UNMEASURED" => {
            ("HOLD", Some(r.code), r.message, Value::Null)
        }
        Err(r) => ("REFUSE", Some(r.code), r.message, Value::Null),
    }
}

fn decorate_gate_receipt(receipt: &mut Value, spec: &Spec, p: &Fields, status: &str) {
    let auth = if status == "PASS" {
        "configured_owning_host_signature"
    } else {
        "not_admitted"
    };
    if matches!(spec.index, 15 | 20) && p.contains_key("process_profile") {
        receipt["process_profile"] = p["process_profile"].clone();
        receipt["observation_authentication"] = json!(auth);
        receipt["scope"] = json!("finite configured-host direct-child execution observation; no process-tree, sandbox or general program-safety proof");
    }
    if spec.index == 7 && p.contains_key("kernel_profile") {
        receipt["kernel_profile"] = p["kernel_profile"].clone();
        receipt["observation_authentication"] = json!(auth);
        receipt["scope"] = json!("configured-host Lean elaboration of the exact submitted proof and required statements under the pinned axiom policy; no general theorem or OS sandbox claim");
    }
    if spec.index == 22 && p.contains_key("resource_profile") {
        receipt["resource_profile"] = p["resource_profile"].clone();
        receipt["observation_authentication"] = json!("unsigned_host_capture");
        receipt["scope"] = json!("finite host-captured Windows job committed memory/time; no RSS, authenticated observer or descendant termination claim");
    }
}
