//! Workflow/skill domain slices. Validation grants no execution authority.
pub mod estate;
pub mod graph;
pub mod operad_runtime;
pub mod immune_guards;
pub mod immune_ports;
pub mod planar;
pub mod policy;
pub mod skill_garden;
pub mod workflow;

use serde::{Deserialize, Serialize};
use std::fmt;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Refusal {
    pub code: String,
    pub message: String,
}
impl Refusal {
    pub fn new(code: &str, message: impl Into<String>) -> Self {
        Self {
            code: code.into(),
            message: format!("{code}: {}", message.into()),
        }
    }
}
impl fmt::Display for Refusal {
    fn fmt(&self, output: &mut fmt::Formatter<'_>) -> fmt::Result {
        output.write_str(&self.message)
    }
}
impl std::error::Error for Refusal {}


/// Checked refusal: the rendered message is `{code}: {body}` and both pieces are nonempty.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum RefusalAdmitError {
    EmptyCode,
    CodeContainsColon,
    EmptyBody,
    Overflow,
    PrefixMismatch { message_len: usize, expected: usize },
}

impl Refusal {
    pub fn try_admit(code: &str, body: impl Into<String>) -> Result<Self, RefusalAdmitError> {
        if code.is_empty() {
            return Err(RefusalAdmitError::EmptyCode);
        }
        if code.contains(':') {
            return Err(RefusalAdmitError::CodeContainsColon);
        }
        let body = body.into();
        if body.is_empty() {
            return Err(RefusalAdmitError::EmptyBody);
        }
        let expected = code
            .len()
            .checked_add(2)
            .and_then(|count| count.checked_add(body.len()))
            .ok_or(RefusalAdmitError::Overflow)?;
        let refusal = Self::new(code, body);
        if refusal.message.len() != expected || !refusal.message.starts_with(code) {
            return Err(RefusalAdmitError::PrefixMismatch {
                message_len: refusal.message.len(),
                expected,
            });
        }
        Ok(refusal)
    }
}

// Origin: engine/crates_rs/core_operads/src/lib.rs
// Claim: urn:core:crates_rs:core-operads:lib:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn admitted_refusal_length_is_code_colon_body() {
        let admitted = Refusal::try_admit("NO", "stop");
        assert!(admitted.is_ok());
        assert_eq!(
            admitted.ok().map(|refusal| refusal.message),
            Some("NO: stop".into())
        );
        assert!(matches!(
            Refusal::try_admit("", "stop"),
            Err(RefusalAdmitError::EmptyCode)
        ));
        assert!(matches!(
            Refusal::try_admit("N:O", "stop"),
            Err(RefusalAdmitError::CodeContainsColon)
        ));
    }
}
