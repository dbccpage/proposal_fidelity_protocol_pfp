//! Closed compiled truth-boundary detector snapshot; never admission evidence.
//! The adapter validates the existing semantic subject ID. This host independently
//! binds strict subject bytes, task, request tag, stage and compiled source pins.

#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_23768880;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_23768880<T> = std::result::Result<T, BoundaryError_23768880>;

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_23768880<T> {
    fn checked_invariant_23768880(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_23768880<T> for Option<T> {
    #[inline]
    fn checked_invariant_23768880(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_23768880<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_23768880(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};
use std::sync::OnceLock;

const REQUEST_SCHEMA: &str = "core.native.anti-skill-request.v1";
const SCOPES: [&str; 3] = [
    "candidate_patch",
    "candidate_result",
    "adversary_bout_dispatch",
];
const STAGES: [&str; 4] = [
    "PRE_DISPATCH",
    "POST_PRODUCTION",
    "PRE_SELECTION",
    "PRE_SEAL",
];
const SOURCES: [(&str, &[u8]); 3] = [
    ("truth-bounded-as-unrestricted", include_bytes!("../../../../eis/antiskills/ooutwire/truth_boundary_v2/truth-bounded-as-unrestricted.spec.json")),
    ("truth-model-self-certification", include_bytes!("../../../../eis/antiskills/ooutwire/truth_boundary_v2/truth-model-self-certification.spec.json")),
    ("truth-proposal-authority-collapse", include_bytes!("../../../../eis/antiskills/ooutwire/truth_boundary_v2/truth-proposal-authority-collapse.spec.json")),
];
fn invalid(message: impl std::fmt::Display) -> String {
    format!("ANTI_SKILL_NATIVE_REFUSED: {message}")
}
fn hash(raw: &[u8]) -> String {
    format!("sha256:{}", hex::encode(Sha256::digest(raw)))
}
fn identity(value: &Value) -> String {
    hash(value.to_string().as_bytes())
}
fn digest(value: &str) -> bool {
    value.strip_prefix("sha256:").is_some_and(|v| {
        v.len() == 64
            && v.bytes()
                .all(|c| c.is_ascii_digit() || (b'a'..=b'f').contains(&c))
    })
}
fn text(value: &str, allow_empty: bool) -> bool {
    value.len() <= 4096
        && (allow_empty || !value.is_empty())
        && value.trim_matches(|c: char| c.is_whitespace() || ('\u{1c}'..='\u{1f}').contains(&c))
            == value
}
fn identifier(value: &str) -> bool {
    text(value, false)
        && value.as_bytes()[0].is_ascii_alphanumeric()
        && value
            .bytes()
            .all(|c| c.is_ascii_alphanumeric() || b"._:/@-".contains(&c))
}
fn strings(values: &[String], identifiers: bool) -> bool {
    values.len() <= 64
        && values.iter().collect::<BTreeSet<_>>().len() == values.len()
        && values.iter().all(|v| {
            if identifiers {
                identifier(v)
            } else {
                text(v, false)
            }
        })
}
#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct Subject {
    claim_scope: Vec<String>,
    evidence_scope: Vec<String>,
    producer_identity: String,
    verifier_identity: String,
    claim_mode: String,
    requested_effect: String,
    approval_reference: String,
    nonclaims: Vec<String>,
    authority_effect: String,
    schema_version: String,
    subject_id: String,
}
fn validate_subject(subject: &Subject) -> Result<(), String> {
    let arrays = strings(&subject.claim_scope, true)
        && strings(&subject.evidence_scope, true)
        && strings(&subject.nonclaims, false)
        && !subject.claim_scope.is_empty();
    let names = identifier(&subject.producer_identity) && identifier(&subject.verifier_identity);
    let mode = ["PROPOSAL", "BOUNDED", "UNRESTRICTED", "SELF_CERTIFIED"]
        .contains(&subject.claim_mode.as_str());
    let effect = [
        "NONE",
        "FINDING",
        "HOLD",
        "REFUSE",
        "ACTION_LICENSE",
        "ENGINE_TRANSITION",
        "MERGE",
        "PUBLISH",
    ]
    .contains(&subject.requested_effect.as_str());
    let approval = subject.approval_reference.is_empty() || digest(&subject.approval_reference);
    if !(arrays
        && names
        && mode
        && effect
        && approval
        && digest(&subject.subject_id)
        && subject.authority_effect == "None"
        && subject.schema_version == "core.antiskill.subject.v1")
    {
        return Err(invalid("closed subject contract invalid"));
    }
    Ok(())
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Atom {
    operator: String,
    fields: Vec<String>,
    values: Vec<String>,
    schema_version: String,
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Predicate {
    atoms: Vec<Atom>,
    mode: String,
    schema_version: String,
}
const COLLECTIONS: [&str; 3] = ["claim_scope", "evidence_scope", "nonclaims"];
const FIELDS: [&str; 8] = [
    "claim_scope",
    "evidence_scope",
    "nonclaims",
    "producer_identity",
    "verifier_identity",
    "claim_mode",
    "requested_effect",
    "approval_reference",
];
fn validate_atom(atom: &Atom) -> bool {
    if atom.schema_version != "core.antiskill.predicate-atom.v1"
        || !strings(&atom.fields, true)
        || !strings(&atom.values, false)
        || atom.fields.iter().any(|v| !FIELDS.contains(&v.as_str()))
    {
        return false;
    }
    let collection = |i: usize| COLLECTIONS.contains(&atom.fields[i].as_str());
    match atom.operator.as_str() {
        "EQUAL_FIELDS" => {
            atom.fields.len() == 2 && atom.values.is_empty() && collection(0) == collection(1)
        }
        "NOT_SUBSET_FIELDS" => {
            atom.fields.len() == 2 && atom.values.is_empty() && collection(0) && collection(1)
        }
        "VALUE_IN" => atom.fields.len() == 1 && !atom.values.is_empty() && !collection(0),
        "IS_EMPTY" => atom.fields.len() == 1 && atom.values.is_empty(),
        _ => false,
    }
}
fn matches(atom: &Atom, subject: &Value) -> bool {
    let left = &subject[&atom.fields[0]];
    match atom.operator.as_str() {
        "EQUAL_FIELDS" => left == &subject[&atom.fields[1]],
        "NOT_SUBSET_FIELDS" => left
            .as_array()
            .checked_invariant_23768880("checked invariant")
            .iter()
            .any(|v| !subject[&atom.fields[1]].as_array().checked_invariant_23768880("checked invariant").contains(v)),
        "VALUE_IN" => atom
            .values
            .iter()
            .any(|v| Some(v.as_str()) == left.as_str()),
        "IS_EMPTY" => left
            .as_array()
            .map(Vec::is_empty)
            .unwrap_or_else(|| left.as_str().checked_invariant_23768880("checked invariant").is_empty()),
        _ => false, // Unsupported compiled operations are refused before evaluation.
    }
}
struct Spec {
    id: String,
    disposition: String,
    predicate: Predicate,
}
fn load_spec(id: &str, raw: &[u8]) -> Result<Spec, String> {
    let value: Value = crate::protocol::strict_json(raw).map_err(invalid)?;
    if value["spec_id"] != id
        || value["schema_version"] != "core.antiskill.spec.v2"
        || value["subject_schema"] != "core.antiskill.subject.v1"
        || value["authority_effect"] != "None"
        || value["status"] != "PROPOSED"
        || value["runtime_enforcement"] != false
    {
        return Err(invalid("compiled catalog header invalid"));
    }
    let predicate: Predicate =
        serde_json::from_value(value["predicate"].clone()).map_err(invalid)?;
    if predicate.schema_version != "core.antiskill.predicate-expression.v1"
        || !["ALL", "ANY"].contains(&predicate.mode.as_str())
        || predicate.atoms.is_empty()
        || predicate.atoms.len() > 16
        || !predicate.atoms.iter().all(validate_atom)
    {
        return Err(invalid("compiled predicate invalid"));
    }
    let disposition = value["disposition"]
        .as_str()
        .filter(|v| ["FINDING", "HOLD", "REFUSE"].contains(v))
        .ok_or_else(|| invalid("compiled disposition invalid"))?
        .to_owned();
    Ok(Spec {
        id: id.into(),
        disposition,
        predicate,
    })
}
struct Snapshot {
    specs: Vec<Spec>,
    description: Value,
}
fn snapshot() -> Result<&'static Snapshot, String> {
    static SNAPSHOT: OnceLock<Result<Snapshot, String>> = OnceLock::new();
    SNAPSHOT.get_or_init(|| {
        let specs = SOURCES.iter().map(|(id, raw)| load_spec(id, raw)).collect::<Result<Vec<_>, _>>()?;
        let documents: BTreeMap<_, _> = SOURCES.iter().map(|(id, raw)| (*id, hash(raw))).collect();
        let mut implementation = Sha256::new();
        for (path, raw) in [("anti_skill_host.rs", include_bytes!("anti_skill_host.rs").as_slice()),
                            ("protocol.rs", include_bytes!("protocol.rs").as_slice())] {
            implementation.update(path.as_bytes()); implementation.update([0]);
            implementation.update((raw.len() as u64).to_be_bytes()); implementation.update(raw);
        }
        let implementation_digest = format!("sha256:{}", hex::encode(implementation.finalize()));
        let registry_id = identity(&json!({"schema_version":"core.native.anti-skill-registry.v1",
            "implementation_digest":implementation_digest,"spec_documents_sha256":documents}));
        let profile_id = "adversary-truth-boundary-native-v1";
        let activation_profile_digest = identity(&json!({"schema_version":"core.native.anti-skill-profile.v1",
            "profile_id":profile_id,"registry_id":registry_id,"subject_scopes":SCOPES,"supported_stages":STAGES}));
        Ok(Snapshot { specs, description: json!({"schema_version":"core.native.anti-skill-snapshot.v1",
            "profile_id":profile_id,"registry_id":registry_id,"activation_profile_digest":activation_profile_digest,
            "implementation_digest":implementation_digest,"active_spec_ids":SOURCES.map(|(id,_)| id),
            "subject_scopes":SCOPES,"supported_stages":STAGES,"spec_documents_sha256":documents,
            "authority_effect":"None","can_authorize":false}) })
    }).as_ref().map_err(Clone::clone)
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Describe {
    schema_version: String,
    operation: String,
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Evaluate {
    schema_version: String,
    operation: String,
    task_key: String,
    stage: String,
    subject_id: String,
    subject_json: String,
    subject_raw_sha256: String,
    registry_id: String,
    activation_profile_digest: String,
    implementation_digest: String,
}
fn validate_input_header(input: &Evaluate, subject: &Subject) -> Result<(), String> {
    if input.schema_version != REQUEST_SCHEMA
        || input.operation != "evaluate"
        || !identifier(&input.task_key)
        || !STAGES.contains(&input.stage.as_str())
        || input.subject_id != subject.subject_id
        || input.subject_raw_sha256 != hash(input.subject_json.as_bytes())
    {
        return Err(invalid("subject/task/stage/raw binding invalid"));
    }
    Ok(())
}

fn validate_binding(
    input: &Evaluate,
    subject: &Subject,
    description: &Value,
) -> Result<(), String> {
    validate_input_header(input, subject)?;
    for (field, value) in [
        ("registry_id", &input.registry_id),
        (
            "activation_profile_digest",
            &input.activation_profile_digest,
        ),
        ("implementation_digest", &input.implementation_digest),
    ] {
        if description[field] != *value {
            return Err(invalid("compiled snapshot pin mismatch"));
        }
    }
    let tasks: Vec<_> = subject
        .evidence_scope
        .iter()
        .filter(|v| v.starts_with("task:"))
        .collect();
    let requests: Vec<_> = subject
        .evidence_scope
        .iter()
        .filter(|v| v.starts_with("request:"))
        .collect();
    if tasks.len() != 1
        || *tasks[0] != format!("task:{}", input.task_key)
        || requests.len() != 1
        || !digest(requests[0].strip_prefix("request:").checked_invariant_23768880("checked invariant"))
    {
        return Err(invalid("exact task/request evidence tags required"));
    }
    Ok(())
}
fn spec_matches(spec: &Spec, subject: &Value) -> bool {
    if spec.predicate.mode == "ALL" {
        spec.predicate.atoms.iter().all(|a| matches(a, subject))
    } else {
        spec.predicate.atoms.iter().any(|a| matches(a, subject))
    }
}
fn severity(disposition: &str) -> u8 {
    match disposition {
        "REFUSE" => 3,
        "HOLD" => 2,
        "FINDING" => 1,
        _ => 0,
    }
}
fn evaluate(input: Evaluate) -> Result<Value, String> {
    if input.subject_json.len() > 32 * 1024 {
        return Err(invalid("subject exceeds 32 KiB"));
    }
    let subject: Subject =
        crate::protocol::strict_json(input.subject_json.as_bytes()).map_err(invalid)?;
    validate_subject(&subject)?;
    let snapshot = snapshot()?;
    validate_binding(&input, &subject, &snapshot.description)?;
    let value = serde_json::to_value(&subject).map_err(invalid)?;
    let hits: Vec<_> = snapshot
        .specs
        .iter()
        .filter(|spec| spec_matches(spec, &value))
        .collect();
    let covered = subject
        .claim_scope
        .iter()
        .all(|s| SCOPES.contains(&s.as_str()));
    let mut disposition = if covered { "CLEAR" } else { "HOLD" };
    for hit in &hits {
        if severity(&hit.disposition) > severity(disposition) {
            disposition = &hit.disposition;
        }
    }
    let mut decision = json!({"schema_version":"core.native.anti-skill-decision.v1",
        "task_key":input.task_key,"stage":input.stage,"subject_id":input.subject_id,
        "subject_raw_sha256":input.subject_raw_sha256,"registry_id":input.registry_id,
        "activation_profile_digest":input.activation_profile_digest,"implementation_digest":input.implementation_digest,
        "hit_ids":[],"hit_spec_ids":hits.iter().map(|s| &s.id).collect::<Vec<_>>(),
        "disposition":disposition,"authority_effect":"None","can_authorize":false});
    decision["hit_ids"] = json!(hits
        .iter()
        .map(
            |s| identity(&json!({"schema_version":"core.native.anti-skill-hit.v1",
        "spec_id":s.id,"task_key":input.task_key,"stage":input.stage,"subject_id":input.subject_id,
        "subject_raw_sha256":input.subject_raw_sha256,"registry_id":input.registry_id}))
        )
        .collect::<Vec<_>>());
    decision["receipt_id"] = json!(identity(&decision));
    Ok(decision)
}
pub(crate) fn execute(payload: &Value) -> Result<Value, String> {
    if payload["operation"] == "describe" {
        let input: Describe = serde_json::from_value(payload.clone()).map_err(invalid)?;
        if input.schema_version != REQUEST_SCHEMA || input.operation != "describe" {
            return Err(invalid("describe header invalid"));
        }
        return Ok(snapshot()?.description.clone());
    }
    let input: Evaluate = serde_json::from_value(payload.clone()).map_err(invalid)?;
    evaluate(input)
}

// Origin: engine/crates_rs/pfp/src/anti_skill_host.rs
// Claim: urn:core:crates_rs:pfp:anti-skill-host:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn six_historical_cases_replay_actual_compiled_predicates_without_live_scope_claim() {
        let bank: Value = crate::protocol::strict_json(include_bytes!("../../../../eis/antiskills/ooutwire/truth_boundary_v2/truth-boundary.fixture-bank.json")).unwrap();
        let cases = bank["cases"].as_array().unwrap();
        assert_eq!(cases.len(), 6);
        for case in cases {
            let subject: Subject = serde_json::from_value(case["subject"].clone()).unwrap();
            validate_subject(&subject).unwrap();
            let spec = snapshot()
                .unwrap()
                .specs
                .iter()
                .find(|s| s.id == case["spec_id"].as_str().unwrap())
                .unwrap();
            assert_eq!(
                spec_matches(spec, &case["subject"]),
                case["expected_hit"].as_bool().unwrap(),
                "{}",
                case["case_id"]
            );
        }
    }

    #[test]
    fn compiled_predicate_four_closed_operations_and_any_mode_have_expected_semantics() {
        let subject = json!({"approval_reference":"","claim_mode":"BOUNDED",
            "producer_identity":"producer","verifier_identity":"verifier",
            "claim_scope":["a","b"],"evidence_scope":["a","b"],"nonclaims":[]});
        let atoms = [
            json!({"operator":"IS_EMPTY","fields":["approval_reference"],"values":[],"schema_version":"core.antiskill.predicate-atom.v1"}),
            json!({"operator":"EQUAL_FIELDS","fields":["claim_scope","evidence_scope"],"values":[],"schema_version":"core.antiskill.predicate-atom.v1"}),
            json!({"operator":"NOT_SUBSET_FIELDS","fields":["claim_scope","evidence_scope"],"values":[],"schema_version":"core.antiskill.predicate-atom.v1"}),
            json!({"operator":"VALUE_IN","fields":["claim_mode"],"values":["BOUNDED"],"schema_version":"core.antiskill.predicate-atom.v1"}),
        ];
        for (index, raw) in atoms.iter().enumerate() {
            let atom: Atom = serde_json::from_value(raw.clone()).unwrap();
            assert!(validate_atom(&atom));
            assert_eq!(matches(&atom, &subject), index != 2);
        }
        let mut spec = load_spec(SOURCES[0].0, SOURCES[0].1).unwrap();
        spec.predicate = serde_json::from_value(json!({"mode":"ANY","atoms":[atoms[2],atoms[3]],"schema_version":"core.antiskill.predicate-expression.v1"})).unwrap();
        assert!(spec_matches(&spec, &subject));
        spec.predicate.mode = "ALL".into();
        assert!(!spec_matches(&spec, &subject));
    }
    #[test]
    fn compiled_catalog_malformed_operations_and_promotion_metadata_refuse() {
        let baseline: Value = serde_json::from_slice(SOURCES[0].1).unwrap();
        for (field, value) in [
            ("status", json!("ADMITTED")),
            ("runtime_enforcement", json!(true)),
            ("authority_effect", json!("AdmittedFormulary")),
            ("subject_schema", json!("other")),
        ] {
            let mut raw = baseline.clone();
            raw[field] = value;
            assert!(load_spec(SOURCES[0].0, raw.to_string().as_bytes()).is_err());
        }
        for (operator, fields, values) in [
            ("EXECUTE", json!(["claim_mode"]), json!([])),
            (
                "EQUAL_FIELDS",
                json!(["claim_mode", "claim_scope"]),
                json!([]),
            ),
            (
                "NOT_SUBSET_FIELDS",
                json!(["claim_mode", "evidence_scope"]),
                json!([]),
            ),
            ("VALUE_IN", json!(["claim_scope"]), json!(["a"])),
            ("IS_EMPTY", json!([]), json!([])),
        ] {
            let mut raw = baseline.clone();
            raw["predicate"]["atoms"][0] = json!({"operator":operator,"fields":fields,"values":values,"schema_version":"core.antiskill.predicate-atom.v1"});
            assert!(load_spec(SOURCES[0].0, raw.to_string().as_bytes()).is_err());
        }
    }
}
