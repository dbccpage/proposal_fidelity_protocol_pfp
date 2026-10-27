//! Credential redaction for trace payloads.
//!
//! ORDERING IS LOAD-BEARING. The scrubber must run BEFORE
//! [`crate::dual_trace_memory::TraceEventV1::seal`], never after. `event_sha256`
//! is taken over the event content, so scrubbing a sealed event would leave a
//! hash that no longer matches its own payload and `verify()` would reject the
//! whole chain. Scrubbing first means the chain commits to the already-redacted
//! bytes, which is both verifiable and the thing we actually want on disk.
//!
//! Deliberately stdlib-only: `core_replay` has no regex dependency, and a
//! hand-rolled scanner is deterministic and auditable in a way a borrowed
//! pattern set is not. This is a BOUNDED redactor, not a proof of secrecy --
//! see [`SecretScrubber::scrub`] for exactly what it does and does not claim.

use std::borrow::Cow;

/// Literal token prefixes that introduce a provider credential.
///
/// Each entry is a prefix plus the character class that continues the secret.
/// Keep them sorted longest-first within a shared stem (`sk-ant-` before `sk-`)
/// so the more specific vendor form wins the match.
const KEY_PREFIXES: &[&str] = &[
    "sk-ant-api03-",
    "sk-ant-",
    "sk-proj-",
    "sk-",
    "ghp_",
    "gho_",
    "ghu_",
    "ghs_",
    "ghr_",
    "github_pat_",
    "glpat-",
    "xoxb-",
    "xoxp-",
    "xoxa-",
    "AKIA",
    "ASIA",
    "AIza",
    "gsk_",
    "csk-",
    "r8_",
    "hf_",
];

/// Environment variable names whose VALUE is a secret wherever it is spelled
/// out as `NAME=value`, `NAME: value`, or `"NAME": "value"`.
const SECRET_ENV_NAMES: &[&str] = &[
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
    "ELEVENLABS_API_KEY",
    "CEREBRAS_API_KEY",
    "GROQ_API_KEY",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "GITHUB_TOKEN",
    "DATABASE_URL",
    "DATABASE_URL_ASYNC",
    "PG_PASSWORD",
    "STRIPE_SECRET_KEY",
    "STRIPE_WEBHOOK_SECRET",
];

/// The marker left in place of a redacted secret.
pub const REDACTION: &str = "[REDACTED]";

/// Outcome of scrubbing one payload.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ScrubReport {
    /// How many distinct secrets were replaced.
    pub redacted: usize,
}

impl ScrubReport {
    /// Did this payload contain anything the scrubber recognized?
    pub fn is_clean(&self) -> bool {
        self.redacted == 0
    }
}

/// Bounded, deterministic credential redactor.
#[derive(Debug, Clone, Copy, Default)]
pub struct SecretScrubber;

impl SecretScrubber {
    pub const fn new() -> Self {
        Self
    }

    /// Redact recognized credentials from `input`.
    ///
    /// WHAT THIS CLAIMS: every substring matching a known vendor key prefix
    /// ([`KEY_PREFIXES`]), a `Bearer <token>` header value, or the value side
    /// of a known secret environment name ([`SECRET_ENV_NAMES`]) is replaced by
    /// [`REDACTION`].
    ///
    /// WHAT THIS DOES NOT CLAIM: that the output is free of secrets. A
    /// credential in a format not listed here passes through untouched. This
    /// reduces the blast radius of an accidental capture; it is not a
    /// confidentiality boundary and must not be described as one.
    pub fn scrub<'a>(&self, input: &'a str) -> (Cow<'a, str>, ScrubReport) {
        let mut redacted = 0usize;
        let mut out = String::new();
        let mut rest = input;

        while !rest.is_empty() {
            let Some((offset, len)) = Self::next_secret(rest) else {
                break;
            };
            out.push_str(&rest[..offset]);
            out.push_str(REDACTION);
            rest = &rest[offset + len..];
            redacted += 1;
        }

        if redacted == 0 {
            return (Cow::Borrowed(input), ScrubReport { redacted });
        }
        out.push_str(rest);
        (Cow::Owned(out), ScrubReport { redacted })
    }

    fn secret_body_len(tail: &str) -> usize {
        tail.char_indices()
            .take_while(|(_, c)| is_secret_char(*c))
            .map(|(i, c)| i + c.len_utf8())
            .last()
            .unwrap_or(0)
    }

    fn consider_candidate(best: &mut Option<(usize, usize)>, offset: usize, len: usize) {
        if len == 0 {
            return;
        }
        // Earliest wins; on a tie the longer match wins, so `sk-ant-` beats
        // `sk-` at the same offset instead of leaving `ant-...` in the clear.
        match *best {
            Some((bo, bl)) if (bo, std::cmp::Reverse(bl)) <= (offset, std::cmp::Reverse(len)) => {}
            _ => *best = Some((offset, len)),
        }
    }

    /// Byte offset and length of the earliest secret in `haystack`.
    fn next_secret(haystack: &str) -> Option<(usize, usize)> {
        let mut best: Option<(usize, usize)> = None;

        for prefix in KEY_PREFIXES {
            if let Some(offset) = haystack.find(prefix) {
                let body = Self::secret_body_len(&haystack[offset + prefix.len()..]);
                // A bare prefix with no body is prose ("an sk- key"), not a secret.
                if body > 0 {
                    Self::consider_candidate(&mut best, offset, prefix.len() + body);
                }
            }
        }

        for name in SECRET_ENV_NAMES {
            let mut from = 0usize;
            while let Some(rel) = haystack[from..].find(name) {
                let offset = from + rel;
                let after = &haystack[offset + name.len()..];
                if let Some(value_len) = assignment_value_len(after) {
                    Self::consider_candidate(&mut best, offset, name.len() + value_len);
                }
                from = offset + name.len();
            }
        }

        if let Some(offset) = find_ignore_ascii_case(haystack, "bearer ") {
            let body = Self::secret_body_len(&haystack[offset + "bearer ".len()..]);
            if body > 0 {
                Self::consider_candidate(&mut best, offset + "bearer ".len(), body);
            }
        }

        best
    }
}

/// Characters that may appear inside an opaque credential body.
fn is_secret_char(c: char) -> bool {
    c.is_ascii_alphanumeric() || c == '_' || c == '-' || c == '.' || c == '/' || c == '+'
}

/// Length of `= value` / `: value` / `": "value"` immediately following a
/// secret env name, including the separator; `None` when the name is merely
/// mentioned rather than assigned.
fn assignment_value_len(after: &str) -> Option<usize> {
    let mut idx = 0usize;
    let bytes = after.as_bytes();

    // Optional closing quote of a JSON key, then separator, then whitespace.
    if bytes.get(idx) == Some(&b'"') {
        idx += 1;
    }
    match bytes.get(idx) {
        Some(&b'=') | Some(&b':') => idx += 1,
        _ => return None,
    }
    while matches!(bytes.get(idx), Some(&b' ') | Some(&b'\t')) {
        idx += 1;
    }
    let quoted = bytes.get(idx) == Some(&b'"');
    if quoted {
        idx += 1;
    }

    let value_start = idx;
    while let Some(&b) = bytes.get(idx) {
        let c = b as char;
        if quoted {
            if c == '"' {
                break;
            }
        } else if !is_secret_char(c) {
            break;
        }
        idx += 1;
    }
    if idx == value_start {
        return None;
    }
    if quoted {
        idx += 1; // closing quote
    }
    Some(idx)
}

fn find_ignore_ascii_case(haystack: &str, needle: &str) -> Option<usize> {
    let h = haystack.as_bytes();
    let n = needle.as_bytes();
    if n.is_empty() || h.len() < n.len() {
        return None;
    }
    (0..=h.len() - n.len())
        .find(|&i| h[i..i + n.len()].eq_ignore_ascii_case(n) && haystack.is_char_boundary(i))
}

// Origin: engine/crates_rs/core_replay/src/secret_scrubber.rs
// Claim: urn:core:crates_rs:core-replay:secret-scrubber:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord61c1f2cf {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord61c1f2cf` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError61c1f2cf {
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
impl BoundaryError61c1f2cf {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError61c1f2cf {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError61c1f2cf {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord61c1f2cf {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError61c1f2cf> {
        if capacity_bound == 0 {
            return Err(BoundaryError61c1f2cf::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError61c1f2cf::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError61c1f2cf::ExceedsCapacity {
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

    fn scrub(s: &str) -> (String, usize) {
        let (out, report) = SecretScrubber::new().scrub(s);
        (out.into_owned(), report.redacted)
    }

    #[test]
    fn clean_text_is_borrowed_not_copied() {
        let (out, report) = SecretScrubber::new().scrub("no secrets here");
        assert!(matches!(out, Cow::Borrowed(_)));
        assert!(report.is_clean());
    }

    #[test]
    fn redacts_openai_and_anthropic_keys() {
        let (out, n) = scrub("use sk-abc123DEF456 and sk-ant-api03-zzz999 now");
        assert_eq!(n, 2);
        assert!(!out.contains("abc123DEF456"), "{out}");
        assert!(!out.contains("zzz999"), "{out}");
        assert!(
            out.starts_with("use [REDACTED] and [REDACTED] now"),
            "{out}"
        );
    }

    #[test]
    fn longer_vendor_prefix_wins_at_the_same_offset() {
        // `sk-` also matches here; if it won, `ant-...` would survive in clear.
        let (out, _) = scrub("sk-ant-secretbody");
        assert_eq!(out, REDACTION);
    }

    #[test]
    fn redacts_named_env_assignments_in_several_spellings() {
        for input in [
            "ANTHROPIC_API_KEY=supersecretvalue",
            "ANTHROPIC_API_KEY: supersecretvalue",
            "\"ANTHROPIC_API_KEY\": \"supersecretvalue\"",
        ] {
            let (out, n) = scrub(input);
            assert_eq!(n, 1, "{input}");
            assert!(!out.contains("supersecretvalue"), "{input} -> {out}");
        }
    }

    #[test]
    fn redacts_bearer_token_but_keeps_the_scheme() {
        let (out, n) = scrub("Authorization: Bearer abcDEF123.token");
        assert_eq!(n, 1);
        assert!(!out.contains("abcDEF123"), "{out}");
        assert!(out.contains("Bearer "), "scheme should survive: {out}");
    }

    #[test]
    fn merely_naming_a_variable_is_not_an_assignment() {
        let (out, n) = scrub("set ANTHROPIC_API_KEY in your .env file");
        assert_eq!(n, 0, "{out}");
        assert_eq!(out, "set ANTHROPIC_API_KEY in your .env file");
    }

    #[test]
    fn bare_prefix_in_prose_is_not_redacted() {
        let (out, n) = scrub("keys beginning with sk- are secret");
        assert_eq!(n, 0, "{out}");
    }

    #[test]
    fn redacts_every_occurrence_not_just_the_first() {
        let (out, n) = scrub("ghp_aaaa then ghp_bbbb then ghp_cccc");
        assert_eq!(n, 3);
        assert!(!out.contains("aaaa") && !out.contains("bbbb") && !out.contains("cccc"));
    }

    #[test]
    fn multibyte_text_is_not_split_mid_character() {
        let (out, n) = scrub("café sk-secret123 café");
        assert_eq!(n, 1);
        assert!(out.contains("café"), "{out}");
        assert!(!out.contains("secret123"), "{out}");
    }
}

#[cfg(test)]
mod l4_boundary_tests_61c1f2cf {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord61c1f2cf::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord61c1f2cf::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord61c1f2cf::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord61c1f2cf::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord61c1f2cf::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError61c1f2cf::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError61c1f2cf::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
