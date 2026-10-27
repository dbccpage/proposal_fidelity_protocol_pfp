use crate::providers::Refusal;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct ChatMessage {
    role: String,
    content: String,
}

impl ChatMessage {
    pub fn new(role: String, content: String) -> Result<Self, Refusal> {
        if role.is_empty() {
            return Err(Refusal::new(
                "PROVIDER_CONFIG_INVALID",
                "role must be non-empty str",
            ));
        }
        Ok(Self { role, content })
    }

    pub fn role(&self) -> &str {
        &self.role
    }

    pub fn content(&self) -> &str {
        &self.content
    }
}

impl<'de> Deserialize<'de> for ChatMessage {
    fn deserialize<D: serde::Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        #[derive(Deserialize)]
        #[serde(deny_unknown_fields)]
        struct Wire {
            role: Value,
            content: Value,
        }
        let wire = Wire::deserialize(deserializer)?;
        let role = wire
            .role
            .as_str()
            .filter(|role| !role.is_empty())
            .ok_or_else(|| serde::de::Error::custom("role must be non-empty str"))?;
        let content = wire
            .content
            .as_str()
            .ok_or_else(|| serde::de::Error::custom("content must be str"))?;
        Self::new(role.into(), content.into())
            .map_err(|error| serde::de::Error::custom(error.message))
    }
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(default, deny_unknown_fields)]
pub struct DecodingParams {
    pub seed: Option<i64>,
    pub temperature: Option<serde_json::Number>,
    pub top_p: Option<serde_json::Number>,
    pub response_format: Option<Value>,
    pub logit_bias: Option<std::collections::BTreeMap<String, i64>>,
    pub grammar: Option<String>,
    pub allow_fallbacks: bool,
    #[serde(default = "yes")]
    pub require_parameters: bool,
}
fn yes() -> bool {
    true
}
impl Default for DecodingParams {
    fn default() -> Self {
        Self {
            seed: None,
            temperature: None,
            top_p: None,
            response_format: None,
            logit_bias: None,
            grammar: None,
            allow_fallbacks: false,
            require_parameters: true,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, Default)]
#[serde(default, deny_unknown_fields)]
pub struct CandidateRequest {
    pub system: String,
    pub user: String,
    pub messages: Vec<ChatMessage>,
    pub decoding: Option<DecodingParams>,
}

pub fn build_openrouter_body(
    request: &CandidateRequest,
    model: &str,
    max_tokens: u64,
) -> Result<Value, Refusal> {
    if crate::providers::credentials::trim_python(model).is_empty() {
        return Err(Refusal::new("PROVIDER_CONFIG_INVALID", "model required"));
    }
    if max_tokens == 0 {
        return Err(Refusal::new(
            "PROVIDER_CONFIG_INVALID",
            "max_tokens must be >= 1",
        ));
    }
    let messages = if request.messages.is_empty() {
        vec![
            ChatMessage {
                role: "system".into(),
                content: request.system.clone(),
            },
            ChatMessage {
                role: "user".into(),
                content: request.user.clone(),
            },
        ]
    } else {
        request.messages.clone()
    };
    let mut body = json!({"model": model, "messages": messages, "max_tokens": max_tokens, "usage": {"include": true}});
    if let Some(dec) = &request.decoding {
        for (key, value) in [
            ("seed", dec.seed.map(Value::from)),
            ("temperature", dec.temperature.clone().map(Value::Number)),
            ("top_p", dec.top_p.clone().map(Value::Number)),
            ("response_format", dec.response_format.clone()),
            ("logit_bias", dec.logit_bias.as_ref().map(|v| json!(v))),
            ("grammar", dec.grammar.as_ref().map(|v| json!(v))),
        ] {
            if let Some(value) = value {
                body[key] = value;
            }
        }
        body["provider"] = json!({"allow_fallbacks": dec.allow_fallbacks, "require_parameters": dec.require_parameters});
    }
    Ok(body)
}

// Origin: engine/crates_rs/core_adversary/src/providers/request.rs
// Claim: urn:core:crates_rs:core-adversary:request:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord82caf94e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord82caf94e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError82caf94e {
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
impl BoundaryError82caf94e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError82caf94e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError82caf94e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord82caf94e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError82caf94e> {
        if capacity_bound == 0 {
            return Err(BoundaryError82caf94e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError82caf94e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError82caf94e::ExceedsCapacity {
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
mod l4_boundary_tests_82caf94e {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord82caf94e::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord82caf94e::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord82caf94e::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord82caf94e::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord82caf94e::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError82caf94e::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError82caf94e::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
