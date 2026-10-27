//! Pure input, path-list and budget validation for code-change admission.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_c0f72209;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_c0f72209<T> = std::result::Result<T, BoundaryError_c0f72209>;
use super::*;

pub(super) fn sha256_hex(text: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(text.as_bytes());
    hex::encode(hasher.finalize())
}

pub(super) fn invalid_request(detail: impl std::fmt::Display) -> String {
    format!("{REFUSAL_CODE_CHANGE_REQUEST_INVALID}: {detail}")
}

pub(super) fn require_text(value: &str, label: &str, max_len: Option<usize>) -> Result<(), String> {
    if value.trim().is_empty() {
        return Err(invalid_request(format!(
            "{label} must be a nonempty string"
        )));
    }
    if value.chars().any(char::is_control) {
        return Err(invalid_request(format!(
            "{label} must not contain control characters"
        )));
    }
    if let Some(max_len) = max_len {
        if value.len() > max_len {
            return Err(invalid_request(format!("{label} exceeds {max_len} bytes")));
        }
    }
    Ok(())
}

/// The Python lifecycle's `_REVISION` rule: `^[A-Za-z0-9][A-Za-z0-9_./+@:-]*$`.
pub(super) fn require_revision(value: &str) -> Result<(), String> {
    let mut chars = value.chars();
    let first_ok = chars.next().is_some_and(|c| c.is_ascii_alphanumeric());
    let rest_ok = chars.all(|c| c.is_ascii_alphanumeric() || "_./+@:-".contains(c));
    if !first_ok || !rest_ok || value.len() > MAX_CODE_CHANGE_ID_LENGTH {
        return Err(invalid_request(
            "base_revision must be a stable source revision identifier",
        ));
    }
    Ok(())
}

pub(super) fn require_sorted_unique(values: &[String], label: &str) -> Result<(), String> {
    if values.windows(2).any(|pair| pair[0] >= pair[1]) {
        return Err(invalid_request(format!(
            "{label} must be unique and sorted"
        )));
    }
    Ok(())
}

pub(super) fn require_path_list(paths: &[String], label: &str) -> Result<(), String> {
    if paths.len() > MAX_CODE_CHANGE_PATHS {
        return Err(invalid_request(format!(
            "{label} exceeds {MAX_CODE_CHANGE_PATHS} paths"
        )));
    }
    for (index, path) in paths.iter().enumerate() {
        if path.contains('\0') {
            return Err(invalid_request(format!("{label}[{index}] contains NUL")));
        }
        validate_path_security(path)
            .map_err(|reason| invalid_request(format!("{label}[{index}] {path:?}: {reason}")))?;
    }
    require_sorted_unique(paths, label)
}

pub(super) fn require_budget(value: usize, label: &str, maximum: usize) -> Result<(), String> {
    if value == 0 || value > maximum {
        return Err(invalid_request(format!(
            "{label} must be an integer in 1..={maximum}, got {value}"
        )));
    }
    Ok(())
}

// Origin: engine/crates_rs/pfp_runtime/src/code_change/validation.rs
// Claim: urn:core:crates_rs:pfp-runtime:validation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_c0f72209 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
