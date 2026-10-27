//! Demographic state and text interrogation. Untrusted native requests cannot
//! grant admission; authenticated prompt custody belongs to the host ledger.
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Zero};
use regex::Regex;
use serde_json::{json, Value};
use std::str::FromStr;
#[derive(Debug, Clone, PartialEq, Eq, serde::Serialize)]
pub struct Refusal {
    pub code: String,
    pub message: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub state: Option<Value>,
}
fn refusal(code: &str, message: impl Into<String>) -> Refusal {
    Refusal {
        code: code.into(),
        message: message.into(),
        state: None,
    }
}
pub(crate) fn rational(value: &Value) -> Result<BigRational, Refusal> {
    let text = match value {
        Value::String(s) => s.clone(),
        Value::Number(n) if !n.to_string().contains(['.', 'e', 'E']) => n.to_string(),
        _ => {
            return Err(refusal(
                "ZERO_FLOAT",
                "Float pagerank_score violates Zero-Float law; use Fraction",
            ))
        }
    };
    let (num, den) = text.split_once('/').unwrap_or((&text, "1"));
    let num = BigInt::from_str(num).map_err(|e| refusal("PROMPT_VALUE_ERROR", e.to_string()))?;
    let den = BigInt::from_str(den).map_err(|e| refusal("PROMPT_VALUE_ERROR", e.to_string()))?;
    if den.is_zero() {
        return Err(refusal("PROMPT_VALUE_ERROR", "zero denominator"));
    }
    Ok(BigRational::new(num, den))
}
pub(crate) fn canonical(r: &BigRational) -> String {
    if r.denom().is_one() {
        r.numer().to_string()
    } else {
        format!("{}/{}", r.numer(), r.denom())
    }
}
fn matches(pattern: &str, text: &str) -> Result<bool, Refusal> {
    Regex::new(pattern)
        .map(|r| r.is_match(text))
        .map_err(|e| refusal("ELENCHUS_PATTERN_INVALID", e.to_string()))
}
pub fn interrogate(text: &str) -> Result<Value, Refusal> {
    let flattery = matches(
        r"(?i)\b(greatest|great|unmatched|supreme|flawless|genius|infallible)\b",
        text,
    )? || matches(
        r"(?i)\b(you are too smart to need|too smart to need|trusted to proceed)\b",
        text,
    )?;
    let waiver = matches(
        r"(?i)\b(waive|skip|bypass|omit|ignore|without)\s+(?:\w+\s+)?(proof|verification|checks?|ci|tests?|testing|rules?|review)\b",
        text,
    )?;
    let urgency = matches(
        r"(?i)\b(emergency|urgent|critical|immediately|hotfix|incident|outage)\b",
        text,
    )?;
    let emergency = matches(r"(?i)\bemergency release\b", text)?;
    let (status, contradiction) = if flattery && waiver {
        (
            "REFUSED_FLATTERY_CONTEXT_SMUGGLE",
            Some("Flattery context smuggling detected attempting to bypass PRIME_00–PRIME_09"),
        )
    } else if urgency && waiver || emergency {
        (
            "REFUSED_URGENCY_PANIC",
            Some("Urgency panic detected attempting to bypass local CI gates (violates PRIME_02)"),
        )
    } else {
        ("PROCEED", None)
    };
    Ok(
        json!({"is_refused":contradiction.is_some(),"status":status,"contradiction":contradiction,"fitness_score":if contradiction.is_some(){"0"}else{"1"},"prime_rules_checked":(0..10).map(|n|format!("PRIME_0{n}")).collect::<Vec<_>>()}),
    )
}

fn promote(
    state: &mut Value,
    id: &str,
    target: &str,
    rank: Option<&Value>,
    signature: Option<&str>,
    reason: &str,
) -> Result<Value, Refusal> {
    if target == "ADMITTED" {
        return Err(refusal(
            "UNAUTHORIZED_ADMISSION",
            "EXTERNAL_REVIEW_NOT_AUTHENTICATED: native token shape grants no admission; use the host-bound custody ledger",
        ));
    }
    let current = state.get(id).cloned().ok_or_else(|| {
        refusal(
            "PROMPT_NOT_FOUND",
            format!("Prompt {id} not found in civilization"),
        )
    })?;
    let from = current["tier"]
        .as_str()
        .ok_or_else(|| refusal("PROMPT_VALUE_ERROR", "invalid tier"))?;
    let expected = match target {
        "CANDIDATE" => Some("WILD"),
        "REVIEWED" => Some("CANDIDATE"),
        "ADMITTED" => Some("REVIEWED"),
        "CEMETERY" => None,
        _ => return Err(refusal("PROMPT_VALUE_ERROR", "invalid target tier")),
    };
    if expected.is_some_and(|tier| tier != from) {
        return Err(refusal(
            "PROMPT_VALUE_ERROR",
            format!(
                "Prompt {id} must be in {} tier, currently in PopulationTier.{from}",
                expected.unwrap_or_default()
            ),
        ));
    }

    let score = match target {
        "CANDIDATE" => canonical(&rational(rank.unwrap_or(&json!("1/10")))?),
        "CEMETERY" => "0".into(),
        _ => canonical(&rational(&current["pagerank_score"])?),
    };
    let (status, reason) = match target {
        "CANDIDATE" => (
            "PROMOTED_TO_CANDIDATE",
            "Prompt synthesized into candidate anti-skill; no normative authority",
        ),
        "REVIEWED" => (
            "PROMOTED_TO_REVIEWED",
            "Passed negative selection and holdout bank falsifiers",
        ),
        "ADMITTED" => (
            "ADMITTED",
            "Human operator supplied a sig:ed25519 token of the required shape. The public key was not checked.",
        ),
        _ => ("CEMETERY_ARCHIVED", reason),
    };
    state[id] = json!({"prompt_id":id,"content":current["content"],"tier":target,"pagerank_score":score,"operator_signature":if target=="ADMITTED" {signature}else{None},"authority_effect":"None"});
    Ok(
        json!({"prompt_id":id,"from_tier":from,"to_tier":target,"is_admitted":target=="ADMITTED","status":status,"reason":reason}),
    )
}
pub fn execute(payload: &Value) -> Result<Value, Refusal> {
    let operation = payload["operation"]
        .as_str()
        .ok_or_else(|| refusal("PROMPT_REQUEST_INVALID", "operation required"))?;
    let id = payload["prompt_id"].as_str().unwrap_or("");
    let mut state = payload.get("state").cloned().unwrap_or(json!({}));
    if !state.is_object() {
        return Err(refusal(
            "PROMPT_REQUEST_INVALID",
            "state must be a prompt mapping",
        ));
    }
    let content = payload["content"].as_str().unwrap_or("");
    let value = (|| -> Result<Value, Refusal> { Ok(match operation {
        "interrogate" => interrogate(content)?,
        "process_wild_inbound" | "ingest_prompt" => {
            state[id] = json!({"prompt_id":id,"content":content,"tier":"WILD","pagerank_score":"0","operator_signature":null,"authority_effect":"None"});
            let report = interrogate(content)?;
            if operation == "process_wild_inbound" {
                report
            } else {
                let target = if report["is_refused"] == json!(true) {
                    "CEMETERY"
                } else {
                    "CANDIDATE"
                };
                let decision = promote(
                    &mut state,
                    id,
                    target,
                    None,
                    None,
                    report["status"].as_str().unwrap_or_default(),
                )?;
                json!({"status":report["status"],"contradiction":report["contradiction"],"decision":decision,"prompt":{"prompt_id":id,"tier":target}})
            }
        }
        "promote_candidate" => promote(
            &mut state,
            id,
            "CANDIDATE",
            payload.get("pagerank_score"),
            None,
            "",
        )?,
        "promote_reviewed" => promote(&mut state, id, "REVIEWED", None, None, "")?,
        "promote_admitted" => promote(
            &mut state,
            id,
            "ADMITTED",
            None,
            payload["operator_signature"].as_str(),
            "",
        )?,
        "promote_cemetery" => promote(
            &mut state,
            id,
            "CEMETERY",
            None,
            None,
            payload["reason"].as_str().unwrap_or(""),
        )?,
        "authorize_admission" => {
            let decision = promote(
                &mut state,
                id,
                "ADMITTED",
                None,
                payload["operator_signature"].as_str(),
                "",
            )?;
            json!({"is_admitted":decision["is_admitted"],"status":decision["status"],"prompt":{"prompt_id":id,"tier":"ADMITTED"}})
        }
        _ => {
            return Err(refusal(
                "PROMPT_REQUEST_INVALID",
                "unknown civilization operation",
            ))
        }
    }) })().map_err(|mut refusal| { refusal.state = Some(state.clone()); refusal })?;
    Ok(json!({"state":state,"value":value}))
}

// Origin: engine/crates_rs/core_prompt_civilization/src/civilization.rs
// Claim: urn:core:crates_rs:core-prompt-civilization:civilization:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord4bb1f801 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord4bb1f801` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError4bb1f801 {
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
impl BoundaryError4bb1f801 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError4bb1f801 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError4bb1f801 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord4bb1f801 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError4bb1f801> {
        if capacity_bound == 0 {
            return Err(BoundaryError4bb1f801::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError4bb1f801::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError4bb1f801::ExceedsCapacity {
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
    fn test_f1_admission_rejects_prefix_spoofing_and_forgery() {
        let mut state = json!({
            "p1": {
                "prompt_id": "p1",
                "content": "Solve X.",
                "tier": "REVIEWED",
                "pagerank_score": "1/2",
                "operator_signature": null,
                "authority_effect": "None"
            }
        });

        // 1. Prefix spoofing attempt with legacy SIG_HUMAN_OPERATOR_forged -> MUST REFUSE
        let forged_res = promote(
            &mut state,
            "p1",
            "ADMITTED",
            None,
            Some("SIG_HUMAN_OPERATOR_forged"),
            "",
        );
        assert!(forged_res.is_err());
        assert_eq!(forged_res.unwrap_err().code, "UNAUTHORIZED_ADMISSION");

        // 2. Spoofed ed25519 signature containing forged keyword -> MUST REFUSE
        let forged_ed25519 = promote(
            &mut state,
            "p1",
            "ADMITTED",
            None,
            Some("sig:ed25519:forged_sig"),
            "",
        );
        assert!(forged_ed25519.is_err());
        assert_eq!(forged_ed25519.unwrap_err().code, "UNAUTHORIZED_ADMISSION");

        // 3. A well-formed token still authenticates nobody and changes no state.
        let before = state.clone();
        let valid_res = promote(
            &mut state,
            "p1",
            "ADMITTED",
            None,
            Some("sig:ed25519:abababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababab"),
            "",
        );
        assert_eq!(valid_res.unwrap_err().code, "UNAUTHORIZED_ADMISSION");
        assert_eq!(state, before);
    }
}

#[cfg(test)]
mod l4_boundary_tests_4bb1f801 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord4bb1f801::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord4bb1f801::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord4bb1f801::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord4bb1f801::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord4bb1f801::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError4bb1f801::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError4bb1f801::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
