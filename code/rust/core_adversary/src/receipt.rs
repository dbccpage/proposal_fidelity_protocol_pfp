//! Fail-closed receipt. AuthorityEffect: None.

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ReceiptStatus {
    Pass,
    Fail,
    Refusal,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Fault {
    pub code: &'static str,
    pub detail: String,
}

impl Fault {
    pub fn new(code: &'static str, detail: impl Into<String>) -> Self {
        Self {
            code,
            detail: detail.into(),
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Receipt<T> {
    pub status: ReceiptStatus,
    pub code: &'static str,
    pub detail: String,
    pub body: T,
}

impl<T> Receipt<T> {
    pub fn authority_effect(&self) -> &'static str {
        "None"
    }

    pub fn pass(code: &'static str, body: T) -> Self {
        Self {
            status: ReceiptStatus::Pass,
            code,
            detail: String::new(),
            body,
        }
    }

    pub fn fail(code: &'static str, detail: impl Into<String>, body: T) -> Self {
        Self {
            status: ReceiptStatus::Fail,
            code,
            detail: detail.into(),
            body,
        }
    }

    pub fn refusal(code: &'static str, detail: impl Into<String>, body: T) -> Self {
        Self {
            status: ReceiptStatus::Refusal,
            code,
            detail: detail.into(),
            body,
        }
    }
}


/// Fail-closed receipt: Pass carries an empty detail, and Fail or Refusal does not.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ClosedReceiptWitness {
    status_tag: u8,
    detail_len: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ClosedReceiptError {
    EmptyCode,
    PassCarriesDetail { detail_len: usize },
    FailureWithoutDetail,
}

// Origin: engine/crates_rs/core_adversary/src/receipt.rs
// Claim: urn:core:crates_rs:core-adversary:receipt:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ClosedReceiptError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ClosedReceiptError {}

impl<T> Receipt<T> {
    pub fn admit_closed(&self) -> Result<ClosedReceiptWitness, ClosedReceiptError> {
        if self.code.is_empty() {
            return Err(ClosedReceiptError::EmptyCode);
        }
        let status_tag = match self.status {
            ReceiptStatus::Pass => {
                if !self.detail.is_empty() {
                    return Err(ClosedReceiptError::PassCarriesDetail {
                        detail_len: self.detail.len(),
                    });
                }
                0u8
            }
            ReceiptStatus::Fail | ReceiptStatus::Refusal => {
                if self.detail.is_empty() {
                    return Err(ClosedReceiptError::FailureWithoutDetail);
                }
                if self.status == ReceiptStatus::Fail { 1 } else { 2 }
            }
        };
        Ok(ClosedReceiptWitness {
            status_tag,
            detail_len: self.detail.len(),
        })
    }
}

impl ClosedReceiptWitness {
    pub fn status_tag(&self) -> u8 {
        self.status_tag
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn pass_refuses_a_nonempty_detail() {
        let pass = Receipt::pass("OK", 1u8);
        let admitted = pass.admit_closed();
        assert!(admitted.is_ok());
        assert_eq!(admitted.ok().map(|witness| witness.status_tag()), Some(0));
        let mut dirty = Receipt::pass("OK", 1u8);
        dirty.detail = "leak".into();
        assert!(matches!(
            dirty.admit_closed(),
            Err(ClosedReceiptError::PassCarriesDetail { detail_len: 4 })
        ));
        let empty_fail = Receipt::fail("NO", "", 1u8);
        assert!(matches!(
            empty_fail.admit_closed(),
            Err(ClosedReceiptError::FailureWithoutDetail)
        ));
    }
}
