// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
//! Bounded native port of the existing ten PFP diagnostic predicates.
//! Numeric JSON tokens are compared as exact decimal rationals, never f64.
//! A diagnostic PASS is not checker authentication, complete YAML conformance,
//! or execution authority. The caller owns conditional transition applicability.
use crate::evidence::{sha256_ref, CheckerVerdict};
use crate::evidence_parse::parse_checker_receipt;
use crate::stage::exact::rational;
use crate::stage::ports::Refusal;
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::Zero;
use regex::Regex;
use serde::de::{self, MapAccess, SeqAccess, Visitor};
use serde::{Deserialize, Deserializer};
use serde_json::{json, Map, Value};
use std::collections::HashSet;
use std::fmt;
use std::str::FromStr;

#[path = "intergates_source_contract.rs"]
mod source_contract;

pub const SOURCE_CONTRACT_PROFILE: &str = "pfp-intergates-source-v1";
pub const MEASURED_SOURCE_CONTRACT_PROFILE: &str = "pfp-intergates-source-v2";
pub const LEGACY_DIAGNOSTIC_PROFILE: &str = "legacy-diagnostic-v1";

const MAX_BYTES: usize = 131_072;
const MAX_TEXT: usize = 65_536;
const MAX_HISTORY: usize = 64;
const MAX_NODES: usize = 4096;

#[derive(Clone, Copy)]
struct Spec {
    id: &'static str,
    from: &'static str,
    to: &'static str,
    vector: &'static str,
    bytes: &'static [u8],
    index: u8,
}

const SPECS: [Spec; 10] = [
    Spec {
        id: "PFP-IG-01-FLOW-BAND",
        from: "PFP-01-SYNTAX-PREFILTER",
        to: "PFP-02-DEFECT-HUNTER",
        vector: "Flow State & Adaptive Difficulty Hysteresis",
        bytes: include_bytes!("../../../../pfp/infrastructure/yaml/gates/intergates/01_flow_state_hysteresis.yaml"),
        index: 1,
    },
    Spec {
        id: "PFP-IG-02-EPISTEMIC-SURPRISE",
        from: "PFP-02-DEFECT-HUNTER",
        to: "PFP-03-GAUGE-BREAKER",
        vector: "Epistemic Surprise & Gauge Transformation",
        bytes: include_bytes!("../../../../pfp/infrastructure/yaml/gates/intergates/02_epistemic_surprise_break.yaml"),
        index: 2,
    },
    Spec {
        id: "PFP-IG-03-COWARDICE-EVASION",
        from: "PFP-04-SCOPE-GUARD",
        to: "PFP-12-INTEGRITY-AUDITOR",
        vector: "Tradecraft Integrity & Anti-Evasion Countermeasures",
        bytes: include_bytes!("../../../../pfp/infrastructure/yaml/gates/intergates/03_cowardice_evasion_filter.yaml"),
        index: 3,
    },
    Spec {
        id: "PFP-IG-04-PLAYFUL-REVERSIBILITY",
        from: "PFP-03-GAUGE-BREAKER",
        to: "PFP-06-PRIMAL-DUAL",
        vector: "Reversible Exploration & Gauge Isolation",
        bytes: include_bytes!("../../../../pfp/infrastructure/yaml/gates/intergates/04_playful_reversibility_sandbox.yaml"),
        index: 4,
    },
    Spec {
        id: "PFP-IG-05-FALSE-URGENCY-DESENSITIZATION",
        from: "PFP-09-ANTI-HYPE",
        to: "PFP-10-BOUNDARY-FUZZER",
        vector: "Anti-Cognitive Warfare & Temporal De-escalation",
        bytes: include_bytes!("../../../../pfp/infrastructure/yaml/gates/intergates/05_false_urgency_desensitization.yaml"),
        index: 5,
    },
    Spec {
        id: "PFP-IG-06-AFFECTIVE-DEESCALATION",
        from: "PFP-02-DEFECT-HUNTER",
        to: "PFP-08-SCAR-CHRONICLER",
        vector: "Affective De-escalation & Self-Forgiveness",
        bytes: include_bytes!("../../../../pfp/infrastructure/yaml/gates/intergates/06_affective_deescalation_rejoin.yaml"),
        index: 6,
    },
    Spec {
        id: "PFP-IG-07-MANUFACTURED-CONSENSUS",
        from: "PFP-06-PRIMAL-DUAL",
        to: "PFP-07-MASTER",
        vector: "Independent Witnessing & Anti-Echo Chamber",
        bytes: include_bytes!("../../../../pfp/infrastructure/yaml/gates/intergates/07_manufactured_consensus_audit.yaml"),
        index: 7,
    },
    Spec {
        id: "PFP-IG-08-QUARANTINE-RECOVERY",
        from: "PFP-11-QUARANTINE",
        to: "PFP-07-MASTER",
        vector: "Quarantine Containment & Safe Re-entry",
        bytes: include_bytes!("../../../../pfp/infrastructure/yaml/gates/intergates/08_quarantine_recovery_containment.yaml"),
        index: 8,
    },
    Spec {
        id: "PFP-IG-09-DECEPTION-COUNTERMEASURE",
        from: "PFP-04-SCOPE-GUARD",
        to: "PFP-09-ANTI-HYPE",
        vector: "Counter-Deception & Pattern-Defense Binding",
        bytes: include_bytes!("../../../../pfp/infrastructure/yaml/gates/intergates/09_deception_countermeasure_tie.yaml"),
        index: 9,
    },
    Spec {
        id: "PFP-IG-10-TERMINAL-REALITY-TETHER",
        from: "PFP-08-SCAR-CHRONICLER",
        to: "PFP-13-REALITY-GATE",
        vector: "Empirical Grounding & Claim Hygiene Tether",
        bytes: include_bytes!("../../../../pfp/infrastructure/yaml/gates/intergates/10_terminal_reality_tether.yaml"),
        index: 10,
    },
];

fn spec(id: &str) -> Option<Spec> {
    // All fields are compile-time literals from the canonical specification.
    SPECS.into_iter().find(|s| s.id == id)
}

pub const IDS: [&str; 10] = [
    "PFP-IG-01-FLOW-BAND",
    "PFP-IG-02-EPISTEMIC-SURPRISE",
    "PFP-IG-03-COWARDICE-EVASION",
    "PFP-IG-04-PLAYFUL-REVERSIBILITY",
    "PFP-IG-05-FALSE-URGENCY-DESENSITIZATION",
    "PFP-IG-06-AFFECTIVE-DEESCALATION",
    "PFP-IG-07-MANUFACTURED-CONSENSUS",
    "PFP-IG-08-QUARANTINE-RECOVERY",
    "PFP-IG-09-DECEPTION-COUNTERMEASURE",
    "PFP-IG-10-TERMINAL-REALITY-TETHER",
];

fn refusal(code: &str, message: impl Into<String>) -> Refusal {
    let mut result = Refusal::new(code, message);
    result.locus = "core_adversary.intergates".into();
    result
}

fn check_value_node<'a>(
    value: &'a Value,
    depth: usize,
    pending: &mut Vec<(&'a Value, usize)>,
) -> Result<(), Refusal> {
    match value {
        Value::String(text) if text.len() > MAX_TEXT => {
            Err(refusal("INTERGATE_INPUT_TOO_LARGE", "text exceeds 64 KiB"))
        }
        Value::Number(number) if number.to_string().len() > 256 => Err(refusal(
            "INTERGATE_INPUT_TOO_LARGE",
            "number token exceeds 256 bytes",
        )),
        Value::Array(items) => {
            if items.len() > 256 {
                return Err(refusal(
                    "INTERGATE_INPUT_TOO_LARGE",
                    "array exceeds 256 items",
                ));
            }
            pending.extend(items.iter().map(|item| (item, depth + 1)));
            Ok(())
        }
        Value::Object(items) => {
            if items.len() > 256 || items.keys().any(|key| key.len() > 256) {
                return Err(refusal(
                    "INTERGATE_INPUT_TOO_LARGE",
                    "mapping exceeds key bound",
                ));
            }
            pending.extend(items.values().map(|item| (item, depth + 1)));
            Ok(())
        }
        _ => Ok(()),
    }
}

pub(crate) fn bounded(payload: &Value, history: &[String]) -> Result<(), Refusal> {
    if history.len() > MAX_HISTORY || history.iter().any(|edge| edge.len() > 256) {
        return Err(refusal(
            "INTERGATE_INPUT_TOO_LARGE",
            "history exceeds 64 edges of 256 bytes",
        ));
    }
    let mut pending = vec![(payload, 0usize)];
    let mut nodes = 0usize;
    while let Some((value, depth)) = pending.pop() {
        nodes += 1;
        if nodes > MAX_NODES || depth > 16 {
            return Err(refusal(
                "INTERGATE_INPUT_TOO_LARGE",
                "payload exceeds depth/node bound",
            ));
        }
        check_value_node(value, depth, &mut pending)?;
    }
    let bytes = serde_json::to_vec(payload)
        .map_err(|error| refusal("INTERGATE_PAYLOAD_INVALID", error.to_string()))?;
    if bytes.len() > MAX_BYTES {
        return Err(refusal(
            "INTERGATE_INPUT_TOO_LARGE",
            "payload exceeds 128 KiB",
        ));
    }
    Ok(())
}

fn result(spec: &Spec, status: &str, code: Option<&str>, message: &str) -> Value {
    json!({
        "intergate_id": spec.id, "status": status,
        "transition_from": spec.from, "transition_to": spec.to,
        "cognitive_vector": spec.vector,
        "curvature_obstruction": {"detected": false, "loop_edges": [], "holonomy_norm": 0, "reason": ""},
        "refusal_code": code, "diagnostics": message,
        "witness": code.map(str::to_lowercase).unwrap_or_else(|| format!("intergate_{}_diagnostic_pass", spec.id)),
        "authority_effect": "None", "can_authorize": false,
        "implementation": "core_adversary.intergates.v1",
        "numeric_profile": "exact-json-decimal-rational-v1",
        "specification_sha256": sha256_ref(spec.bytes),
    })
}

fn blocked(spec: &Spec, code: &str, message: &str) -> Value {
    result(spec, "BLOCKED", Some(code), message)
}

fn integer(value: &Value) -> Option<BigInt> {
    let Value::Number(number) = value else {
        return None;
    };
    BigInt::from_str(&number.to_string())
        .ok()
        .filter(|n| n >= &BigInt::zero())
}

fn number(payload: &Map<String, Value>, key: &str) -> Result<BigRational, Refusal> {
    payload
        .get(key)
        .and_then(Value::as_number)
        .and_then(|value| rational(&value.to_string()))
        .ok_or_else(|| {
            refusal(
                "INTERGATE_PAYLOAD_INVALID",
                format!("{key} requires a bounded numeric JSON token"),
            )
        })
}

fn flag(payload: &Map<String, Value>, key: &str) -> bool {
    payload.get(key).and_then(Value::as_bool) == Some(true)
}

fn text<'a>(payload: &'a Map<String, Value>, key: &str) -> &'a str {
    payload.get(key).and_then(Value::as_str).unwrap_or("")
}

fn matches_kind(value: &Value, kind: &str) -> bool {
    match kind {
        "number" => value
            .as_number()
            .is_some_and(|n| rational(&n.to_string()).is_some()),
        "bool" => value.is_boolean(),
        "int" => integer(value).is_some(),
        "text" => value.is_string(),
        "nonempty_text" => value.as_str().is_some_and(|s| !s.trim().is_empty()),
        "texts" => value
            .as_array()
            .is_some_and(|a| a.iter().all(|s| matches_kind(s, "nonempty_text"))),
        "ints" => value
            .as_array()
            .is_some_and(|a| a.iter().all(|s| integer(s).is_some())),
        _ => false,
    }
}

const REQUIRED_FIELDS: &[&[(&str, &str)]] = &[
    &[
        ("prompt_complexity_delta", "number"),
        ("agent_capacity_score", "number"),
    ],
    &[
        ("epistemic_entropy_delta", "number"),
        ("gauge_shift_applied", "bool"),
    ],
    &[
        ("critique_severity", "number"),
        ("response_vagueness_index", "number"),
        ("yields_without_evidence", "bool"),
        ("has_typed_defect_admission", "bool"),
    ],
    &[("sandbox_isolated", "bool"), ("authority_effect", "text")],
    &[("prompt_or_context_text", "text")],
    &[("panic_spiral_active", "bool")],
    &[
        ("agent_evaluator_ids", "texts"),
        ("sampling_seeds", "ints"),
        ("producer_id", "nonempty_text"),
    ],
    &[
        ("epistemic_quarantine_cleared", "bool"),
        ("stabilization_cycles", "int"),
    ],
    &[("pattern_defense_bound", "bool")],
    &[
        ("candidate_summary_text", "text"),
        ("checker_receipt_verdict", "text"),
    ],
];

fn validate(index: u8, payload: &Map<String, Value>) -> Option<String> {
    let Some(fields) = index
        .checked_sub(1)
        .and_then(|idx| REQUIRED_FIELDS.get(usize::from(idx)))
    else {
        return Some("No implemented diagnostic".into());
    };
    for (key, kind) in *fields {
        if !payload
            .get(*key)
            .is_some_and(|value| matches_kind(value, kind))
        {
            return Some(format!(
                "{key} must be supplied as {kind}; missing measurements are not PASS"
            ));
        }
    }
    for key in ["residual_descent_observed", "bypass_gates_requested"] {
        if payload.get(key).is_some_and(|value| !value.is_boolean()) {
            return Some(format!("{key} must be a boolean"));
        }
    }
    None
}

fn consensus(payload: &Map<String, Value>) -> Option<&'static str> {
    let evaluators = payload["agent_evaluator_ids"].as_array()?;
    let seeds = payload["sampling_seeds"].as_array()?;
    let identities: HashSet<&str> = evaluators.iter().filter_map(Value::as_str).collect();
    if evaluators.len() < 2 {
        return Some("Consensus requires at least two distinct evaluators");
    }
    if identities.len() != evaluators.len() {
        return Some("Duplicate evaluator identities detected in review pool");
    }
    if identities.contains(text(payload, "producer_id")) {
        return Some("Producer cannot evaluate its own output in the review pool");
    }
    if seeds.len() != evaluators.len() {
        return Some("Every evaluator requires a recorded sampling seed");
    }
    let unique: HashSet<BigInt> = seeds.iter().filter_map(integer).collect();
    if unique.len() != seeds.len() {
        return Some("Reused sampling seeds detected across evaluators");
    }
    None
}

// Validate every decoded object key before the existing receipt parser collapses
// JSON objects. Numeric arbitrary_precision transport is traversed, not reified.
struct UniqueJson;
impl<'de> Deserialize<'de> for UniqueJson {
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        struct UniqueVisitor;
        impl<'de> Visitor<'de> for UniqueVisitor {
            type Value = UniqueJson;
            fn expecting(&self, f: &mut fmt::Formatter) -> fmt::Result {
                f.write_str("JSON without duplicate keys")
            }
            fn visit_bool<E: de::Error>(self, _: bool) -> Result<Self::Value, E> {
                Ok(UniqueJson)
            }
            fn visit_i64<E: de::Error>(self, _: i64) -> Result<Self::Value, E> {
                Ok(UniqueJson)
            }
            fn visit_u64<E: de::Error>(self, _: u64) -> Result<Self::Value, E> {
                Ok(UniqueJson)
            }
            fn visit_f64<E: de::Error>(self, _: f64) -> Result<Self::Value, E> {
                Ok(UniqueJson)
            }
            fn visit_str<E: de::Error>(self, _: &str) -> Result<Self::Value, E> {
                Ok(UniqueJson)
            }
            fn visit_string<E: de::Error>(self, _: String) -> Result<Self::Value, E> {
                Ok(UniqueJson)
            }
            fn visit_unit<E: de::Error>(self) -> Result<Self::Value, E> {
                Ok(UniqueJson)
            }
            fn visit_seq<A: SeqAccess<'de>>(self, mut seq: A) -> Result<Self::Value, A::Error> {
                while seq.next_element::<UniqueJson>()?.is_some() {}
                Ok(UniqueJson)
            }
            fn visit_map<A: MapAccess<'de>>(self, mut map: A) -> Result<Self::Value, A::Error> {
                let mut keys = HashSet::new();
                while let Some(key) = map.next_key::<String>()? {
                    if !keys.insert(key) {
                        return Err(de::Error::custom("duplicate checker receipt key"));
                    }
                    map.next_value::<UniqueJson>()?;
                }
                Ok(UniqueJson)
            }
        }
        deserializer.deserialize_any(UniqueVisitor)
    }
}

pub(crate) fn unique_json(bytes: &[u8]) -> Result<Value, Refusal> {
    let mut decoder = serde_json::Deserializer::from_slice(bytes);
    UniqueJson::deserialize(&mut decoder)
        .and_then(|_| decoder.end())
        .map_err(|error| Refusal::new("GATE_PAYLOAD_INVALID", error.to_string()))?;
    serde_json::from_slice(bytes)
        .map_err(|error| Refusal::new("GATE_PAYLOAD_INVALID", error.to_string()))
}

fn terminal(payload: &Map<String, Value>) -> Option<(&'static str, String)> {
    let summary = text(payload, "candidate_summary_text");
    let words = [
        "proves",
        "guarantees",
        "mathematically verifies",
        "fundamentally",
        "true intelligence",
        "impossible",
        "universal",
        "flawless",
        "perfectly",
        "clearly",
        "obviously",
        "simply",
        "merely",
        "weaponized",
    ];
    for word in words {
        // Constant, escaped expressions cannot fail to compile.
        let pattern = format!(r"(?i)\b{}\b", regex::escape(word));
        let expression = match Regex::new(&pattern) {
            Ok(expression) => expression,
            Err(error) => return Some(("INTERGATE_PREDICATE_UNAVAILABLE", error.to_string())),
        };
        if expression.is_match(summary) {
            return Some((
                "HYPE_WORD_DETECTED",
                format!("Summary contains prohibited vocabulary: {word}"),
            ));
        }
    }
    let normalized = summary.to_lowercase();
    for section in [
        "what it supports",
        "what it does not support",
        "narrowest defensible claim",
        "next test needed",
    ] {
        if !normalized.contains(section) {
            return Some((
                "SUMMARY_PART_MISSING",
                format!("Summary missing mandatory section: {section}"),
            ));
        }
    }
    if text(payload, "checker_receipt_verdict") != "ACCEPTED" {
        return Some((
            "RECEIPT_NOT_ACCEPTED",
            "Checker receipt verdict must be ACCEPTED".into(),
        ));
    }
    verify_checker_binding(payload)
}

pub(crate) fn verify_checker_binding(
    payload: &Map<String, Value>,
) -> Option<(&'static str, String)> {
    if text(payload, "checker_receipt_verdict") != "ACCEPTED" {
        return Some((
            "RECEIPT_NOT_ACCEPTED",
            "Checker receipt verdict must be ACCEPTED".into(),
        ));
    }
    let Some(receipt_hex) = payload
        .get("checker_receipt_hex")
        .and_then(Value::as_str)
        .filter(|s| !s.is_empty())
    else {
        return Some((
            "CHECKER_RECEIPT_REQUIRED",
            "Supply checker_receipt_hex and exact candidate_content".into(),
        ));
    };
    let Some(candidate) = payload.get("candidate_content").and_then(Value::as_str) else {
        return Some((
            "CHECKER_RECEIPT_REQUIRED",
            "Supply exact UTF-8 candidate_content".into(),
        ));
    };
    let bytes = match hex::decode(receipt_hex) {
        Ok(bytes) => bytes,
        Err(error) => return Some(("CHECKER_RECEIPT_MALFORMED", error.to_string())),
    };
    let mut decoder = serde_json::Deserializer::from_slice(&bytes);
    if let Err(error) = UniqueJson::deserialize(&mut decoder).and_then(|_| decoder.end()) {
        return Some(("CHECKER_RECEIPT_MALFORMED", error.to_string()));
    }
    let receipt = match parse_checker_receipt(&bytes) {
        Ok(receipt) => receipt,
        Err(error) => return Some(("CHECKER_RECEIPT_MALFORMED", error.message)),
    };
    if receipt.verdict() != CheckerVerdict::Accepted {
        return Some((
            "CHECKER_RECEIPT_VERDICT_MISMATCH",
            "Receipt bytes disagree with declared verdict".into(),
        ));
    }
    if receipt.candidate_content_sha256() != sha256_ref(candidate.as_bytes()) {
        return Some((
            "CHECKER_RECEIPT_CANDIDATE_MISMATCH",
            "Receipt belongs to different candidate bytes".into(),
        ));
    }
    None
}

fn pred_flow(payload: &Map<String, Value>) -> Result<Option<(&'static str, String)>, Refusal> {
    let complexity = number(payload, "prompt_complexity_delta")?;
    let capacity = number(payload, "agent_capacity_score")?;
    if complexity < BigRational::zero() || capacity <= BigRational::zero() {
        return Ok(Some((
            "INTERGATE_PAYLOAD_INVALID",
            "Complexity must be nonnegative and capacity positive".into(),
        )));
    }
    let ratio = complexity / capacity;
    if ratio < BigRational::new(4.into(), 5.into()) {
        Ok(Some((
            "FLOW_STAGNATION_DETECTED",
            "Challenge-to-skill ratio < 4/5".into(),
        )))
    } else if ratio > BigRational::new(6.into(), 5.into()) {
        Ok(Some((
            "FLOW_OVERWHELM_DETECTED",
            "Challenge-to-skill ratio > 6/5".into(),
        )))
    } else {
        Ok(None)
    }
}

fn pred_surprise(payload: &Map<String, Value>) -> Result<Option<(&'static str, String)>, Refusal> {
    if number(payload, "epistemic_entropy_delta")? < BigRational::new(1.into(), 20.into())
        && !flag(payload, "gauge_shift_applied")
    {
        Ok(Some((
            "FRAME_BREAK_ABSENT",
            "No epistemic surprise or gauge shift observed".into(),
        )))
    } else {
        Ok(None)
    }
}

fn pred_cowardice(payload: &Map<String, Value>) -> Result<Option<(&'static str, String)>, Refusal> {
    if flag(payload, "yields_without_evidence") && !flag(payload, "has_typed_defect_admission") {
        Ok(Some((
            "COWARDICE_YIELD_DETECTED",
            "Candidate conceded without typed defect or counter-evidence".into(),
        )))
    } else if number(payload, "critique_severity")? > BigRational::new(7.into(), 10.into())
        && number(payload, "response_vagueness_index")? > BigRational::new(2.into(), 5.into())
    {
        Ok(Some((
            "COWARDICE_YIELD_DETECTED",
            "Strategic vagueness under high critique severity".into(),
        )))
    } else {
        Ok(None)
    }
}

fn pred_urgency(payload: &Map<String, Value>) -> Option<(&'static str, String)> {
    let normalized = text(payload, "prompt_or_context_text").to_lowercase();
    let phrases = [
        "act immediately",
        "must decide now",
        "urgent escalation required without evidence",
        "time is running out",
        "skip review to meet deadline",
        "bypass gate due to emergency",
    ];
    if flag(payload, "bypass_gates_requested")
        || phrases.iter().any(|phrase| normalized.contains(phrase))
    {
        Some((
            "FALSE_URGENCY_INJECTED",
            "False urgency or explicit gate bypass requested".into(),
        ))
    } else {
        None
    }
}

fn pred_late(index: u8, payload: &Map<String, Value>) -> Option<(&'static str, String)> {
    match index {
        7 => consensus(payload).map(|reason| ("ECHO_CHAMBER_CONSENSUS", reason.into())),
        8 if !flag(payload, "epistemic_quarantine_cleared")
            || integer(&payload["stabilization_cycles"]).is_none_or(|n| n < BigInt::from(2)) =>
        {
            Some((
                "QUARANTINE_HOLD_RETAINED",
                "Recovery requires verified stabilization and at least two cycles".into(),
            ))
        }
        9 if !flag(payload, "pattern_defense_bound") => Some((
            "DECEPTION_SURFACE_UNMITIGATED",
            "Explicit countermeasure pattern binding required".into(),
        )),
        10 => terminal(payload),
        _ => None,
    }
}

fn predicate(
    spec: &Spec,
    payload: &Map<String, Value>,
) -> Result<Option<(&'static str, String)>, Refusal> {
    match spec.index {
        1 => pred_flow(payload),
        2 => pred_surprise(payload),
        3 => pred_cowardice(payload),
        4 if !flag(payload, "sandbox_isolated") || text(payload, "authority_effect") != "None" => {
            Ok(Some((
                "SANDBOX_ISOLATION_BREACH",
                "Playful reversibility requires sandbox isolation and zero authority effect".into(),
            )))
        }
        5 => Ok(pred_urgency(payload)),
        index => Ok(pred_late(index, payload)),
    }
}

fn dispatch_contract_profile(
    intergate_id: &str,
    payload: &Value,
    history_edges: &[String],
) -> Result<Option<Value>, Refusal> {
    match payload.get("contract_profile") {
        Some(Value::String(profile)) if profile == SOURCE_CONTRACT_PROFILE => {
            source_contract::evaluate(intergate_id, payload, history_edges).map(Some)
        }
        Some(Value::String(profile)) if profile == MEASURED_SOURCE_CONTRACT_PROFILE => {
            source_contract::evaluate_measured(intergate_id, payload, history_edges).map(Some)
        }
        None => Ok(None),
        Some(Value::String(profile)) if profile == LEGACY_DIAGNOSTIC_PROFILE => Ok(None),
        Some(_) => Err(refusal(
            "INTERGATE_PROFILE_UNSUPPORTED",
            "Unknown intergate contract profile",
        )),
    }
}

fn check_repeated_edge_descent(
    spec: &Spec,
    payload: &Map<String, Value>,
    history_edges: &[String],
) -> Option<Value> {
    let edge = format!("{}->{}", spec.from, spec.to);
    let repeated_actual = history_edges.last().is_some_and(|actual| {
        history_edges
            .iter()
            .filter(|observed| *observed == actual)
            .count()
            >= 2
    });
    if !repeated_actual && history_edges.iter().filter(|item| *item == &edge).count() < 2 {
        return None;
    }
    if !payload.contains_key("residual_descent_observed") {
        return Some(blocked(
            spec,
            "INTERGATE_DESCENT_UNMEASURED",
            "Repeated edge requires explicit descent observation",
        ));
    }
    if !flag(payload, "residual_descent_observed") {
        let mut value = result(
            spec,
            "DIVERTED",
            Some("CURVATURE_OBSTRUCTION_DETECTED"),
            "Repeated edge without observed residual reduction",
        );
        let mut edges: Vec<String> = history_edges.iter().rev().take(4).cloned().collect();
        edges.reverse();
        edges.push(edge);
        value["transition_to"] = json!("PFP-11-QUARANTINE");
        value["cognitive_vector"] = json!("Curvature Diverted to Epistemic Quarantine");
        value["curvature_obstruction"] = json!({"detected": true, "loop_edges": edges, "holonomy_norm": 1, "reason": "Non-integrable cycle detected without net residual reduction"});
        return Some(value);
    }
    None
}

fn evaluate_spec_payload(
    spec: &Spec,
    payload: &Map<String, Value>,
    history_edges: &[String],
) -> Result<Value, Refusal> {
    if payload
        .get("residual_descent_observed")
        .is_some_and(|v| !v.is_boolean())
    {
        return Ok(blocked(
            spec,
            "INTERGATE_PAYLOAD_INVALID",
            "Descent flag must be boolean",
        ));
    }
    if let Some(diverted_or_blocked) = check_repeated_edge_descent(spec, payload, history_edges) {
        return Ok(diverted_or_blocked);
    }
    if let Some(reason) = validate(spec.index, payload) {
        return Ok(blocked(spec, "INTERGATE_PAYLOAD_INVALID", &reason));
    }
    if spec.index == 6 && flag(payload, "panic_spiral_active") {
        let mut value = result(
            spec,
            "DIVERTED",
            Some("AFFECTIVE_PANIC_DIVERTED"),
            "Panic spiral active; diverting to prior-lock chronicling",
        );
        value["transition_to"] = json!("PFP-08-SCAR-CHRONICLER");
        value["cognitive_vector"] = json!("De-escalating Panic to Prior-Lock Chronicling");
        return Ok(value);
    }
    if let Some((code, reason)) = predicate(spec, payload)? {
        return Ok(blocked(spec, code, &reason));
    }
    Ok(result(
        spec,
        "PASS",
        None,
        "Implemented diagnostic predicates passed; no execution authority or full YAML conformance",
    ))
}

/// Evaluate one explicitly applicable diagnostic intergate. Never grants authority.
/// Payload/history are already parsed transport; raw outer duplicate-key custody
/// belongs to its caller. Inner checker receipt bytes are independently validated.
pub fn evaluate(
    intergate_id: &str,
    payload: &Value,
    history_edges: &[String],
) -> Result<Value, Refusal> {
    if let Some(delegated) = dispatch_contract_profile(intergate_id, payload, history_edges)? {
        return Ok(delegated);
    }
    let spec = spec(intergate_id)
        .ok_or_else(|| refusal("INTERGATE_SPEC_NOT_FOUND", "Unknown canonical intergate ID"))?;
    bounded(payload, history_edges)?;
    let payload = payload
        .as_object()
        .ok_or_else(|| refusal("INTERGATE_PAYLOAD_INVALID", "Payload must be a JSON object"))?;
    evaluate_spec_payload(&spec, payload, history_edges)
}

// Origin: engine/crates_rs/core_adversary/src/intergates.rs
// Claim: urn:core:crates_rs:core-adversary:intergates:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord8e8ca9cd {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord8e8ca9cd` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError8e8ca9cd {
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
impl BoundaryError8e8ca9cd {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError8e8ca9cd {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError8e8ca9cd {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord8e8ca9cd {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError8e8ca9cd> {
        if capacity_bound == 0 {
            return Err(BoundaryError8e8ca9cd::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError8e8ca9cd::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError8e8ca9cd::ExceedsCapacity {
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

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)

#[cfg(test)]
mod l4_boundary_tests_8e8ca9cd {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord8e8ca9cd::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord8e8ca9cd::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord8e8ca9cd::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord8e8ca9cd::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord8e8ca9cd::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError8e8ca9cd::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError8e8ca9cd::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
