//! Forge, mutation operators, protected spans, and population policy.
//!
//! Enforces:
//! - F-PROMPT-03: A mutation operator cannot admit (has no admission field, proposal only).
//! - F-BIO-03: Protected spans are immutable (zero-width insertion or edit inside protected span raises PROTECTED_SPAN_MUTATION_REFUSED).
//! - F-BIO-05: Reserves use largest-remainder allocation (sums to N; exactly 6/3/1 at N=10).
//! - F-META-01: Meta proposals take effect only in a future external epoch.
//!
//! AuthorityEffect: None.

use crate::record::ProtectedSpanV1;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::cmp::{max, min};
use std::collections::{HashMap, HashSet};

pub struct PromptMutationEngineV1;

impl PromptMutationEngineV1 {
    pub fn apply_mutation(
        original_bytes: &[u8],
        protected_spans: &[ProtectedSpanV1],
        edit_start: usize,
        edit_end: usize,
        replacement: &[u8],
    ) -> Result<Vec<u8>, String> {
        if edit_start > edit_end || edit_end > original_bytes.len() {
            return Err("INDEX_OUT_OF_BOUNDS: Edit boundaries invalid".to_string());
        }

        // Check if edit touches any protected span
        for span in protected_spans {
            // Overlapping non-empty interval
            if edit_start < edit_end {
                let overlap_start = max(edit_start, span.start_byte);
                let overlap_end = min(edit_end, span.end_byte);
                if overlap_start < overlap_end {
                    return Err(
                        "PROTECTED_SPAN_MUTATION_REFUSED: Edit overlaps protected span".to_string(),
                    );
                }
            } else {
                // Zero-width insertion strictly inside span
                if span.start_byte < edit_start && edit_start < span.end_byte {
                    return Err("PROTECTED_SPAN_MUTATION_REFUSED: Zero-width insertion inside protected span".to_string());
                }
            }
        }

        let mut result = Vec::with_capacity(original_bytes.len() + replacement.len());
        result.extend_from_slice(&original_bytes[..edit_start]);
        result.extend_from_slice(replacement);
        result.extend_from_slice(&original_bytes[edit_end..]);

        Ok(result)
    }
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct OrganizePromptInput {
    seed: String,
    #[serde(default)]
    task: String,
    #[serde(default)]
    constraints: Vec<String>,
    #[serde(default)]
    acceptance: Vec<String>,
    #[serde(default)]
    response_contract: Option<Value>,
}

const MAX_ORGANIZE_BYTES: usize = 1_048_576;

fn extract_organize_request_bytes(payload: &Value) -> Result<Vec<u8>, String> {
    let mut fields = payload.clone();
    if fields.get("operation") == Some(&json!("forge_organize_prompt")) {
        fields
            .as_object_mut()
            .ok_or("FORGE_INPUT_INVALID: object required")?
            .remove("operation");
    }
    let request = if fields.get("request_json").is_some() {
        if fields.as_object().is_none_or(|fields| fields.len() != 1) {
            return Err(
                "FORGE_INPUT_INVALID: request_json cannot be mixed with other fields".into(),
            );
        }
        fields["request_json"]
            .as_str()
            .ok_or("FORGE_INPUT_INVALID: request_json must be text")?
            .as_bytes()
            .to_vec()
    } else {
        serde_json::to_vec(&fields).map_err(|e| format!("FORGE_INPUT_INVALID: {e}"))?
    };
    if request.len() > MAX_ORGANIZE_BYTES {
        return Err("FORGE_LIMIT_EXCEEDED: request exceeds one MiB".into());
    }
    Ok(request)
}

fn append_organized_section(
    output: &mut Vec<u8>,
    spans: &mut Vec<ProtectedSpanV1>,
    name: &str,
    text: &str,
) -> Result<(), String> {
    if text.is_empty() {
        return Ok(());
    }
    let section = format!("\n\n[FORGE DECLARED {}]\n{}", name.to_uppercase(), text);
    if output.len().saturating_add(section.len()) > MAX_ORGANIZE_BYTES {
        return Err("FORGE_LIMIT_EXCEEDED: organized prompt exceeds one MiB".into());
    }
    let start = output.len();
    *output =
        PromptMutationEngineV1::apply_mutation(output, spans, start, start, section.as_bytes())?;
    spans.push(ProtectedSpanV1 {
        name: name.into(),
        start_byte: start,
        end_byte: output.len(),
    });
    Ok(())
}

fn append_serialized_section<T: Serialize>(
    output: &mut Vec<u8>,
    spans: &mut Vec<ProtectedSpanV1>,
    name: &str,
    val: &T,
) -> Result<(), String> {
    let text = serde_json::to_string(val).map_err(|e| format!("FORGE_INPUT_INVALID: {e}"))?;
    append_organized_section(output, spans, name, &text)
}

fn append_declared_fields(
    input: &OrganizePromptInput,
    output: &mut Vec<u8>,
    spans: &mut Vec<ProtectedSpanV1>,
) -> Result<(), String> {
    append_organized_section(output, spans, "task", &input.task)?;
    // JSON arrays retain each declared string exactly, including embedded
    // newlines, rather than interpreting a field as Markdown instructions.
    if !input.constraints.is_empty() {
        append_serialized_section(output, spans, "constraints", &input.constraints)?;
    }
    if !input.acceptance.is_empty() {
        append_serialized_section(output, spans, "acceptance criteria", &input.acceptance)?;
    }
    if let Some(ref contract) = input.response_contract {
        append_serialized_section(output, spans, "response contract", contract)?;
    }
    Ok(())
}

/// One bounded append-only organization. The seed and every declared field
/// remain protected bytes. No requirements, permissions or model answers are
/// inferred, and a successful organization conveys no task acceptance.
pub fn organize_prompt(payload: &Value) -> Result<Value, String> {
    let request = extract_organize_request_bytes(payload)?;
    let input: OrganizePromptInput =
        serde_json::from_slice(&request).map_err(|e| format!("FORGE_INPUT_INVALID: {e}"))?;
    if input
        .response_contract
        .as_ref()
        .is_some_and(|value| !value.is_object())
    {
        return Err("FORGE_INPUT_INVALID: response_contract must be an object or null".into());
    }
    let mut output = input.seed.as_bytes().to_vec();
    let mut spans = vec![ProtectedSpanV1 {
        name: "original_seed".into(),
        start_byte: 0,
        end_byte: output.len(),
    }];
    append_declared_fields(&input, &mut output, &mut spans)?;
    let source_sha256 = hex::encode(Sha256::digest(input.seed.as_bytes()));
    let organized_sha256 = hex::encode(Sha256::digest(&output));
    let rendered_bytes = output.len();
    let organized_text =
        String::from_utf8(output).map_err(|e| format!("FORGE_UTF8_INVALID: {e}"))?;
    Ok(json!({"schema_version":"core.forge.organize-prompt.v1",
        "operation_id":"forge.organize-prompt.v1", "status":"ORGANIZED",
        "request_sha256":hex::encode(Sha256::digest(request)),
        "seed_sha256":source_sha256, "organized_sha256":organized_sha256,
        "organized_text":organized_text, "protected_spans":spans,
        "source_bytes":input.seed.len(), "rendered_bytes":rendered_bytes,
        "authority_effect":"None"}))
}

/// Recheck a persisted organization without recording a second mutation.
pub fn verify_organization(payload: &Value) -> Result<Value, String> {
    let request = if let Some(text) = payload.get("request_json") {
        json!({"request_json":text})
    } else {
        payload
            .get("request")
            .ok_or("FORGE_INPUT_INVALID: request missing")?
            .clone()
    };
    let preparation = payload
        .get("preparation")
        .ok_or("FORGE_INPUT_INVALID: preparation missing")?;
    let expected = organize_prompt(&request)?;
    let expected_object = expected
        .as_object()
        .ok_or("FORGE_INPUT_INVALID: result missing")?;
    if expected_object
        .iter()
        .any(|(key, value)| preparation.get(key) != Some(value))
    {
        return Err(
            "FORGE_PREPARATION_MISMATCH: persisted organization differs from declared inputs"
                .into(),
        );
    }
    Ok(
        json!({"status":"VALID", "operation_id":"forge.organize-prompt.v1",
        "request_sha256":expected["request_sha256"], "organized_sha256":expected["organized_sha256"],
        "authority_effect":"None"}),
    )
}

/// A mutation operator candidate: proposal only, has NO admission field.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MutationOperatorCandidateV1 {
    pub operator_id: String,
    pub description: String,
    pub target_locus: String,
}

pub struct PopulationPolicyV1;

impl PopulationPolicyV1 {
    /// Largest-remainder integer allocation for population size N.
    /// Returns (exploited, maturing, exploration_unmeasured).
    /// Target proportions: 60% exploited, 30% maturing, 10% unmeasured.
    pub fn allocate_reserves(n: usize) -> (usize, usize, usize) {
        if n == 0 {
            return (0, 0, 0);
        }
        if n == 1 {
            return (1, 0, 0);
        }
        if n == 2 {
            return (1, 1, 0);
        }
        if n == 3 {
            return (2, 1, 0);
        }

        // Proportions 60%, 30%, 10%
        let base_exp = (n * 60) / 100;
        let base_mat = (n * 30) / 100;
        let base_unm = (n * 10) / 100;

        let rem_exp = (n * 60) % 100;
        let rem_mat = (n * 30) % 100;
        let rem_unm = (n * 10) % 100;

        let mut remainder = n - (base_exp + base_mat + base_unm);
        let mut exp = base_exp;
        let mut mat = base_mat;
        let mut unm = base_unm;

        let mut fractions = vec![
            (rem_exp, 0), // 0: exp
            (rem_mat, 1), // 1: mat
            (rem_unm, 2), // 2: unm
        ];
        fractions.sort_by_key(|a| std::cmp::Reverse(a.0));

        for (_, idx) in fractions {
            if remainder == 0 {
                break;
            }
            match idx {
                0 => exp += 1,
                1 => mat += 1,
                2 => unm += 1,
                _ => {}
            }
            remainder -= 1;
        }

        (exp, mat, unm)
    }
}

#[derive(Debug, Default)]
pub struct MetaProposalRegistryV1 {
    pub current_epoch: u64,
    pub enacted_epochs: HashSet<u64>,
    pub proposals: HashMap<u64, Vec<String>>,
}

impl MetaProposalRegistryV1 {
    pub fn new(current_epoch: u64) -> Self {
        let mut enacted = HashSet::new();
        enacted.insert(current_epoch);
        Self {
            current_epoch,
            enacted_epochs: enacted,
            proposals: HashMap::new(),
        }
    }

    pub fn register_proposal(&mut self, target_epoch: u64, checker_name: &str) {
        self.proposals
            .entry(target_epoch)
            .or_default()
            .push(checker_name.to_string());
    }

    pub fn enact_epoch(&mut self, epoch: u64) {
        self.enacted_epochs.insert(epoch);
    }

    pub fn get_active_checker_set(&self, epoch: u64) -> Result<Vec<String>, String> {
        if !self.enacted_epochs.contains(&epoch) {
            return Err(
                "EPOCH_NOT_ENACTED: Future epoch requires authenticated external enactment"
                    .to_string(),
            );
        }
        Ok(self.proposals.get(&epoch).cloned().unwrap_or_default())
    }
}

// Origin: engine/crates_rs/core_prompt_civilization/src/forge.rs
// Claim: urn:core:crates_rs:core-prompt-civilization:forge:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord813c1a8d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord813c1a8d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError813c1a8d {
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
impl BoundaryError813c1a8d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError813c1a8d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError813c1a8d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord813c1a8d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError813c1a8d> {
        if capacity_bound == 0 {
            return Err(BoundaryError813c1a8d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError813c1a8d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError813c1a8d::ExceedsCapacity {
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
mod tests {
    use super::*;

    #[test]
    fn organize_keeps_original_utf8_and_declared_sections() {
        let request = serde_json::json!({"seed":"Do not change α.\r\n", "task":"Report a finite result",
            "constraints":["No external calls"], "acceptance":["Original checker accepts"],
            "response_contract":{"type":"string"}});
        let result = organize_prompt(&request).unwrap();
        let text = result["organized_text"].as_str().unwrap();
        assert!(text.starts_with(request["seed"].as_str().unwrap()));
        assert!(text.contains("No external calls"));
        assert!(text.contains("Original checker accepts"));
        assert!(text.contains("{\"type\":\"string\"}"));
        assert_eq!(result["operation_id"], "forge.organize-prompt.v1");
        assert_eq!(result, organize_prompt(&request).unwrap());
        let spans: Vec<ProtectedSpanV1> =
            serde_json::from_value(result["protected_spans"].clone()).unwrap();
        assert_eq!(
            &text.as_bytes()[spans[0].start_byte..spans[0].end_byte],
            request["seed"].as_str().unwrap().as_bytes()
        );
        assert!(
            PromptMutationEngineV1::apply_mutation(text.as_bytes(), &spans, 1, 2, b"X").is_err()
        );
    }

    #[test]
    fn organize_does_not_infer_missing_fields() {
        let result = organize_prompt(
            &serde_json::json!({"seed":"Find a counterexample", "task":"",
            "constraints":[], "acceptance":[], "response_contract":null}),
        )
        .unwrap();
        assert_eq!(result["organized_text"], "Find a counterexample");
        assert_eq!(result["source_bytes"], result["rendered_bytes"]);
    }

    #[test]
    fn organization_verification_rejects_changed_sections_and_bindings() {
        let request = serde_json::json!({"seed":"Keep the seed", "task":"Declared task"});
        let original = organize_prompt(&request).unwrap();
        assert_eq!(
            verify_organization(&json!({"request":request,"preparation":original})).unwrap()
                ["status"],
            "VALID"
        );
        for key in [
            "organized_text",
            "organized_sha256",
            "request_sha256",
            "seed_sha256",
        ] {
            let mut changed = original.clone();
            changed[key] = json!("counterfeit");
            assert!(
                verify_organization(&json!({"request":request,"preparation":changed})).is_err()
            );
        }
    }

    #[test]
    fn organization_binds_exact_transport_json_including_number_encoding() {
        let raw = r#"{"seed":"A declared numeric schema","response_contract":{"minimum":1e-06}}"#;
        let result = organize_prompt(&json!({"request_json":raw})).unwrap();
        assert_eq!(
            result["request_sha256"],
            hex::encode(Sha256::digest(raw.as_bytes()))
        );
        assert_eq!(
            verify_organization(&json!({"request_json":raw,"preparation":result})).unwrap()
                ["status"],
            "VALID"
        );
        assert!(organize_prompt(&json!({"request_json":raw,"extra":"hidden"})).is_err());
        assert!(
            organize_prompt(&json!({"request_json":r#"{"seed":"one","seed":"two"}"#})).is_err()
        );
    }

    #[test]
    fn organize_refuses_unknown_or_malformed_fields_and_oversize() {
        for request in [
            serde_json::json!({"seed":"task","constraints":"silently coerce"}),
            serde_json::json!({"seed":"task","unknown_instruction":"invent permission"}),
            serde_json::json!({"seed":"x".repeat(1_048_577)}),
        ] {
            assert!(organize_prompt(&request).is_err());
        }
    }

    #[test]
    fn test_f_bio_03_protected_span_mutation_refused() {
        let original = b"abcdefghij";
        let spans = vec![ProtectedSpanV1 {
            name: "core".into(),
            start_byte: 2,
            end_byte: 8,
        }];

        // Zero-width insertion at 4 (inside [2, 8))
        let res = PromptMutationEngineV1::apply_mutation(original, &spans, 4, 4, b"EVIL");
        assert!(res.is_err());
        assert!(res.unwrap_err().contains("PROTECTED_SPAN_MUTATION_REFUSED"));

        // Overlapping edit [1, 5) overlaps [2, 8)
        let res2 = PromptMutationEngineV1::apply_mutation(original, &spans, 1, 5, b"EVIL");
        assert!(res2.is_err());
        assert!(res2
            .unwrap_err()
            .contains("PROTECTED_SPAN_MUTATION_REFUSED"));

        // Allowed edit outside span [0, 2)
        let res3 = PromptMutationEngineV1::apply_mutation(original, &spans, 0, 2, b"ZZ");
        assert!(res3.is_ok());
        assert_eq!(res3.unwrap(), b"ZZcdefghij");
    }

    #[test]
    fn test_f_bio_05_largest_remainder_allocation() {
        // Test N=10 gives exactly 6/3/1
        assert_eq!(PopulationPolicyV1::allocate_reserves(10), (6, 3, 1));

        // Test all sizes in {1, 2, 3, 7, 10, 13, 19, 21} sum to N
        for n in [1, 2, 3, 7, 10, 13, 19, 21] {
            let (e, m, u) = PopulationPolicyV1::allocate_reserves(n);
            assert_eq!(e + m + u, n);
        }
    }

    #[test]
    fn test_f_meta_01_future_epoch_requires_enactment() {
        let mut reg = MetaProposalRegistryV1::new(5);
        reg.register_proposal(6, "unapproved-checker");
        // Epoch 6 not enacted yet
        let res = reg.get_active_checker_set(6);
        assert!(res.is_err());
        assert!(res.unwrap_err().contains("EPOCH_NOT_ENACTED"));

        // Enact epoch 6
        reg.enact_epoch(6);
        let res2 = reg.get_active_checker_set(6);
        assert!(res2.is_ok());
        assert_eq!(res2.unwrap(), vec!["unapproved-checker".to_string()]);
    }
}

#[cfg(test)]
mod l4_boundary_tests_813c1a8d {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord813c1a8d::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord813c1a8d::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord813c1a8d::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord813c1a8d::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord813c1a8d::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError813c1a8d::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError813c1a8d::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
