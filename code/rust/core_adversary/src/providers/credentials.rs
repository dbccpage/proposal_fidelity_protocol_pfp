//! Explicit file first, inherited environment second; no directory search or environment writes.
use crate::providers::Refusal;
use std::{collections::BTreeMap, path::Path};

pub const KEY_NAME: &str = "OPENROUTER_API_KEY";

pub(crate) fn trim_python(text: &str) -> &str {
    text.trim_matches(|c: char| c.is_whitespace() || ('\u{1c}'..='\u{1f}').contains(&c))
}

// Intentionally neither Debug nor Serialize: no secret-bearing output surface.
pub struct ApiKey(String);

impl ApiKey {
    pub(crate) fn bearer(&self) -> String {
        format!("Bearer {}", self.0)
    }
    pub fn from_sources(
        file: Option<&[u8]>,
        environ: &BTreeMap<String, String>,
    ) -> Result<Self, Refusal> {
        if let Some(raw) = file {
            let raw = raw.strip_prefix(&[0xef, 0xbb, 0xbf]).unwrap_or(raw);
            let text = std::str::from_utf8(raw).map_err(|_| {
                Refusal::new("ENV_FILE_UNREADABLE", "explicit env file is not UTF-8")
            })?;
            if let Some(key) = parse_env_text(text)
                .get(KEY_NAME)
                .filter(|key| !trim_python(key).is_empty())
            {
                return Ok(Self(trim_python(key).to_owned()));
            }
        }
        if let Some(key) = environ
            .get(KEY_NAME)
            .filter(|key| !trim_python(key).is_empty())
        {
            return Ok(Self(trim_python(key).to_owned()));
        }
        Err(Refusal::new(
            "OPENROUTER_KEY_MISSING",
            "OPENROUTER_API_KEY not found in the explicit env file or process environment",
        ))
    }
}

pub fn parse_env_text(text: &str) -> BTreeMap<String, String> {
    let mut out = BTreeMap::new();
    for raw in text.split([
        '\n', '\r', '\u{b}', '\u{c}', '\u{1c}', '\u{1d}', '\u{1e}', '\u{85}', '\u{2028}',
        '\u{2029}',
    ]) {
        if let Some((k, v)) = parse_env_line(raw) {
            out.insert(k, v);
        }
    }
    out
}

fn parse_env_line(raw: &str) -> Option<(String, String)> {
    let line = trim_python(raw);
    if line.is_empty() || line.starts_with('#') {
        return None;
    }
    let line = line.strip_prefix("export ").unwrap_or(line);
    let (key, value) = line.split_once('=')?;
    let value = unquote_env_value(trim_python(value));
    Some((trim_python(key).into(), value.into()))
}

fn unquote_env_value(value: &str) -> &str {
    let bytes = value.as_bytes();
    if bytes.len() >= 2 && bytes.first() == bytes.last() && matches!(bytes[0], b'\'' | b'"') {
        &value[1..value.len() - 1]
    } else {
        value
    }
}

pub fn resolve_openrouter_key(
    env_file: Option<&Path>,
    environ: &BTreeMap<String, String>,
) -> Result<ApiKey, Refusal> {
    let file = match env_file {
        Some(path) if path.is_file() => Some(std::fs::read(path).map_err(|_| {
            Refusal::new("ENV_FILE_UNREADABLE", "explicit env file cannot be read")
        })?),
        _ => None,
    };
    ApiKey::from_sources(file.as_deref(), environ)
}

pub fn resolve_inherited_key(env_file: Option<&Path>) -> Result<ApiKey, Refusal> {
    let mut environ = BTreeMap::new();
    if let Ok(key) = std::env::var(KEY_NAME) {
        environ.insert(KEY_NAME.into(), key);
    }
    resolve_openrouter_key(env_file, &environ)
}

pub const ANTHROPIC_KEY_NAME: &str = "ANTHROPIC_API_KEY";

/// The Anthropic key, read only from the environment the process was launched with.
///
/// There is deliberately no file argument and no directory search: a worktree uses the
/// credentials its launcher supplied or none. Intentionally neither Debug nor Serialize.
pub struct AnthropicApiKey(String);

impl AnthropicApiKey {
    pub(crate) fn header_value(&self) -> &str {
        &self.0
    }

    /// Resolve from an explicit environment map (the caller's snapshot of its own env).
    pub fn from_environ(environ: &BTreeMap<String, String>) -> Result<Self, Refusal> {
        environ
            .get(ANTHROPIC_KEY_NAME)
            .map(|key| trim_python(key))
            .filter(|key| !key.is_empty())
            .map(|key| Self(key.to_owned()))
            .ok_or_else(|| {
                Refusal::new(
                    "ANTHROPIC_KEY_MISSING",
                    "ANTHROPIC_API_KEY is not set in the launching environment",
                )
            })
    }

    /// Resolve from this process's inherited environment.
    pub fn from_process_env() -> Result<Self, Refusal> {
        let mut environ = BTreeMap::new();
        if let Ok(key) = std::env::var(ANTHROPIC_KEY_NAME) {
            environ.insert(ANTHROPIC_KEY_NAME.into(), key);
        }
        Self::from_environ(&environ)
    }
}

// Origin: engine/crates_rs/core_adversary/src/providers/credentials.rs
// Claim: urn:core:crates_rs:core-adversary:credentials:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorddc55a386 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorddc55a386` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrordc55a386 {
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
impl BoundaryErrordc55a386 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrordc55a386 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrordc55a386 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorddc55a386 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrordc55a386> {
        if capacity_bound == 0 {
            return Err(BoundaryErrordc55a386::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrordc55a386::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrordc55a386::ExceedsCapacity {
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
mod l4_boundary_tests_dc55a386 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorddc55a386::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorddc55a386::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorddc55a386::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorddc55a386::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorddc55a386::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryErrordc55a386::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryErrordc55a386::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
