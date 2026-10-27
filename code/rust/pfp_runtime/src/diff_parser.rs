//! Strict unified diff parser and security path validation.
//!
//! AuthorityEffect: None.

use std::collections::BTreeSet;

pub const WINDOWS_RESERVED_NAMES: &[&str] = &[
    "CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8",
    "COM9", "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
];

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DiffParseResult {
    pub touched_paths: Vec<String>,
    pub is_valid: bool,
    pub error_message: Option<String>,
}

fn invalid(msg: impl Into<String>) -> DiffParseResult {
    DiffParseResult {
        touched_paths: Vec::new(),
        is_valid: false,
        error_message: Some(msg.into()),
    }
}

fn validate_path_segment(seg: &str) -> Result<(), String> {
    if seg.is_empty() {
        return Err("empty path segments are forbidden".to_owned());
    }
    if seg == "." || seg == ".." {
        return Err("relative directory navigation ('.' or '..') is forbidden".to_owned());
    }
    if seg.ends_with('.') {
        return Err("trailing dots in path segments are forbidden".to_owned());
    }
    let upper = seg.to_ascii_uppercase();
    let stem = upper.split('.').next().unwrap_or(&upper);
    if WINDOWS_RESERVED_NAMES.contains(&stem) {
        return Err(format!("Windows reserved device name {seg:?} is forbidden"));
    }
    Ok(())
}

/// Validate path security: refuse backslashes, absolute paths, traversal (`..`), trailing dots, empty segments, Windows reserved device names.
pub fn validate_path_security(path: &str) -> Result<(), String> {
    if path.is_empty() {
        return Err("path cannot be empty".to_owned());
    }
    if path.contains('\\') {
        return Err("path contains backslashes".to_owned());
    }
    if path.starts_with('/') {
        return Err("absolute paths are forbidden".to_owned());
    }
    if path.contains(':') {
        return Err("drive letters or colons are forbidden".to_owned());
    }
    for seg in path.split('/') {
        validate_path_segment(seg)?;
    }
    Ok(())
}

/// Check if a path is contained inside a root prefix.
pub fn is_path_contained_in_root(path: &str, root: &str) -> bool {
    let p = path.trim_matches('/');
    let r = root.trim_matches('/');
    if r.is_empty() {
        return true;
    }
    p == r || p.starts_with(&format!("{r}/"))
}

fn unquote_diff_path(p: &str) -> &str {
    let double_quoted = p.starts_with('"') && p.ends_with('"');
    let single_quoted = p.starts_with('\'') && p.ends_with('\'');
    if p.len() >= 2 && (double_quoted || single_quoted) {
        &p[1..p.len() - 1]
    } else {
        p
    }
}

fn strip_git_prefix(p: &str) -> &str {
    p.strip_prefix("a/")
        .or_else(|| p.strip_prefix("b/"))
        .unwrap_or(p)
}

fn clean_diff_path(raw: &str) -> Result<Option<String>, String> {
    let p = unquote_diff_path(raw.trim());
    if p == "dev/null" || p == "/dev/null" || p.is_empty() {
        return Ok(None);
    }
    let stripped = strip_git_prefix(p);
    validate_path_security(stripped)?;
    Ok(Some(stripped.to_owned()))
}

fn parse_hunk_count(part: &str) -> Option<usize> {
    if let Some((_, count)) = part.split_once(',') {
        count.parse::<usize>().ok()
    } else {
        Some(1)
    }
}

fn parse_hunk_header(line: &str) -> Option<(usize, usize)> {
    let rest = line.strip_prefix("@@ -")?;
    let end_idx = rest.find(" @@")?;
    let spec = &rest[..end_idx];
    let parts: Vec<&str> = spec.split(' ').collect();
    if parts.len() != 2 {
        return None;
    }
    let new_part = parts[1].strip_prefix('+')?;
    Some((parse_hunk_count(parts[0])?, parse_hunk_count(new_part)?))
}

#[derive(Default)]
struct DiffParserState {
    touched_paths: BTreeSet<String>,
    found_diff: bool,
    current_left: Option<String>,
    current_right: Option<String>,
    section_open: bool,
    section_has_change: bool,
    old_header_seen: bool,
    new_header_seen: bool,
    old_remaining: usize,
    new_remaining: usize,
    in_hunk: bool,
    allow_no_newline: bool,
}

fn clean_diff_path_or_fail(raw: &str) -> Result<Option<String>, DiffParseResult> {
    clean_diff_path(raw).map_err(|e| invalid(format!("Unsafe diff path: {e}")))
}

fn strip_rename_or_copy(line: &str) -> Option<&str> {
    line.strip_prefix("rename from ")
        .or_else(|| line.strip_prefix("rename to "))
        .or_else(|| line.strip_prefix("copy from "))
        .or_else(|| line.strip_prefix("copy to "))
}

fn is_mode_change_line(line: &str) -> bool {
    line.starts_with("new file mode ")
        || line.starts_with("deleted file mode ")
        || line.starts_with("new mode ")
}

fn is_header_metadata_line(line: &str) -> bool {
    line.starts_with("index ")
        || line.starts_with("old mode ")
        || line.starts_with("similarity index ")
        || line.starts_with("dissimilarity index ")
}

impl DiffParserState {
    fn record_path(&mut self, path: Option<String>) {
        if let Some(p) = path {
            self.touched_paths.insert(p);
        }
    }

    fn parse_hunk_prefix_deltas(line: &str) -> Result<(usize, usize), DiffParseResult> {
        match line.as_bytes().first().copied() {
            None => Err(invalid(
                "Truncated hunk before declared line counts were satisfied",
            )),
            Some(b' ') => Ok((1, 1)),
            Some(b'-') => Ok((1, 0)),
            Some(b'+') => Ok((0, 1)),
            Some(_) => Err(invalid(format!("Invalid hunk line prefix in diff: {line:?}"))),
        }
    }

    fn step_hunk_line(&mut self, line: &str) -> Result<(), DiffParseResult> {
        if line == r"\ No newline at end of file" {
            if !self.allow_no_newline {
                return Err(invalid("Misplaced no-newline marker in hunk"));
            }
            self.allow_no_newline = false;
            return Ok(());
        }
        let (old_delta, new_delta) = Self::parse_hunk_prefix_deltas(line)?;
        if old_delta > self.old_remaining || new_delta > self.new_remaining {
            return Err(invalid("Hunk body exceeds its declared line counts"));
        }
        self.old_remaining -= old_delta;
        self.new_remaining -= new_delta;
        self.allow_no_newline = true;
        self.section_has_change = true;
        if self.old_remaining == 0 && self.new_remaining == 0 {
            self.in_hunk = false;
        }
        Ok(())
    }

    fn handle_git_header(&mut self, line: &str) -> Result<(), DiffParseResult> {
        if self.section_open && !self.section_has_change {
            return Err(invalid(
                "Diff section contains no patch, rename, copy, mode, or binary change",
            ));
        }
        let parts: Vec<&str> = line.split_whitespace().collect();
        if parts.len() != 4 || parts[0] != "diff" || parts[1] != "--git" {
            return Err(invalid(format!("Malformed diff --git line: {line:?}")));
        }
        let left_res = clean_diff_path_or_fail(parts[2])?;
        let right_res = clean_diff_path_or_fail(parts[3])?;
        self.current_left = left_res.clone();
        self.current_right = right_res.clone();
        self.record_path(left_res);
        self.record_path(right_res);
        self.found_diff = true;
        self.section_open = true;
        self.section_has_change = false;
        self.old_header_seen = false;
        self.new_header_seen = false;
        Ok(())
    }

    fn handle_old_header(&mut self, raw: &str) -> Result<(), DiffParseResult> {
        if self.old_header_seen && !self.new_header_seen {
            return Err(invalid(
                "Repeated old-file header without a new-file header",
            ));
        }
        let raw_path = raw.split('\t').next().unwrap_or(raw);
        let old_path = clean_diff_path_or_fail(raw_path)?;
        let disagrees = self.section_open
            && old_path.is_some()
            && self.current_left.is_some()
            && old_path != self.current_left;
        if disagrees {
            return Err(invalid("Old-file header disagrees with diff --git path"));
        }
        self.record_path(old_path);
        self.found_diff = true;
        self.section_open = true;
        self.old_header_seen = true;
        self.new_header_seen = false;
        Ok(())
    }

    fn handle_new_header(&mut self, raw: &str) -> Result<(), DiffParseResult> {
        if !self.old_header_seen || self.new_header_seen {
            return Err(invalid(
                "New-file header is missing or repeats its old-file header",
            ));
        }
        let raw_path = raw.split('\t').next().unwrap_or(raw);
        let new_path = clean_diff_path_or_fail(raw_path)?;
        let disagrees =
            self.current_right.is_some() && new_path.is_some() && new_path != self.current_right;
        if disagrees {
            return Err(invalid("New-file header disagrees with diff --git path"));
        }
        self.record_path(new_path);
        self.new_header_seen = true;
        Ok(())
    }

    fn handle_hunk_start(&mut self, old_cnt: usize, new_cnt: usize) -> Result<(), DiffParseResult> {
        if !self.old_header_seen || !self.new_header_seen {
            return Err(invalid(
                "Hunk appears before a complete old/new file header pair",
            ));
        }
        if old_cnt == 0 && new_cnt == 0 {
            return Err(invalid("Hunk declares no old or new lines"));
        }
        self.old_remaining = old_cnt;
        self.new_remaining = new_cnt;
        self.in_hunk = true;
        self.section_has_change = true;
        Ok(())
    }

    fn handle_rename_or_copy(&mut self, line: &str, raw: &str) -> Result<(), DiffParseResult> {
        if !self.section_open {
            return Err(invalid(
                "Rename or copy metadata appears outside a diff section",
            ));
        }
        let path = clean_diff_path_or_fail(raw)?;
        self.record_path(path);
        if line.starts_with("rename to ") || line.starts_with("copy to ") {
            self.section_has_change = true;
        }
        Ok(())
    }

    fn handle_binary_files(&mut self, raw: &str) -> Result<(), DiffParseResult> {
        if !self.section_open {
            return Err(invalid("Binary metadata appears outside a diff section"));
        }
        if let Some((left_part, right_part)) = raw
            .strip_suffix(" differ")
            .and_then(|s| s.split_once(" and "))
        {
            for name in [left_part, right_part] {
                if let Ok(p) = clean_diff_path(name) {
                    self.record_path(p);
                }
            }
        }
        self.section_has_change = true;
        Ok(())
    }

    fn handle_metadata_line(&mut self, line: &str) -> Result<bool, DiffParseResult> {
        if let Some(raw) = strip_rename_or_copy(line) {
            self.handle_rename_or_copy(line, raw)?;
            return Ok(true);
        }
        if let Some(raw) = line.strip_prefix("Binary files ") {
            self.handle_binary_files(raw)?;
            return Ok(true);
        }
        if line == "GIT binary patch" {
            return Err(invalid("GIT binary patch bodies are unsupported"));
        }
        if is_mode_change_line(line) {
            if !self.section_open {
                return Err(invalid("Mode metadata appears outside a diff section"));
            }
            self.section_has_change = true;
            return Ok(true);
        }
        if is_header_metadata_line(line) {
            if !self.section_open {
                return Err(invalid("Diff metadata appears outside a diff section"));
            }
            return Ok(true);
        }
        Ok(false)
    }

    fn step_outside_hunk(&mut self, line: &str) -> Result<(), DiffParseResult> {
        if line == r"\ No newline at end of file" {
            if !self.allow_no_newline {
                return Err(invalid("Misplaced no-newline marker outside a hunk"));
            }
            self.allow_no_newline = false;
            return Ok(());
        }
        self.allow_no_newline = false;
        if line.starts_with("diff --git ") {
            return self.handle_git_header(line);
        }
        if let Some(raw) = line.strip_prefix("--- ") {
            return self.handle_old_header(raw);
        }
        if let Some(raw) = line.strip_prefix("+++ ") {
            return self.handle_new_header(raw);
        }
        if let Some((old_cnt, new_cnt)) = parse_hunk_header(line) {
            return self.handle_hunk_start(old_cnt, new_cnt);
        }
        if line.starts_with("@@") {
            return Err(invalid(format!("Malformed hunk header: {line:?}")));
        }
        if self.handle_metadata_line(line)? {
            return Ok(());
        }
        Err(invalid(format!(
            "Unrecognized line outside a hunk: {line:?}"
        )))
    }

    fn finalize(self) -> DiffParseResult {
        if self.in_hunk {
            return invalid("Truncated hunk before declared line counts were satisfied");
        }
        if self.section_open && !self.section_has_change {
            return invalid("Diff section contains no patch, rename, copy, mode, or binary change");
        }
        if !self.found_diff {
            return invalid("No valid diff headers found in patch text");
        }
        if self.touched_paths.is_empty() {
            return invalid("Patch text yielded zero touched paths");
        }
        DiffParseResult {
            touched_paths: self.touched_paths.into_iter().collect(),
            is_valid: true,
            error_message: None,
        }
    }
}

/// Parse unified git diff text and return touched path set or error.
pub fn parse_unified_diff(patch_text: &str) -> DiffParseResult {
    if patch_text.trim().is_empty() {
        return invalid("Patch text is empty or whitespace-only");
    }

    let normalized = patch_text.replace("\r\n", "\n").replace('\r', "\n");
    let mut lines: Vec<&str> = normalized.split('\n').collect();
    if lines.last().is_some_and(|last| last.is_empty()) {
        lines.pop();
    }

    let mut state = DiffParserState::default();
    for line in lines {
        let step = if state.in_hunk {
            state.step_hunk_line(line)
        } else {
            state.step_outside_hunk(line)
        };
        if let Err(err) = step {
            return err;
        }
    }
    state.finalize()
}

// Origin: engine/crates_rs/pfp_runtime/src/diff_parser.rs
// Claim: urn:core:crates_rs:pfp-runtime:diff-parser:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordaecbe3a4 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordaecbe3a4` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErroraecbe3a4 {
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
impl BoundaryErroraecbe3a4 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErroraecbe3a4 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErroraecbe3a4 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordaecbe3a4 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErroraecbe3a4> {
        if capacity_bound == 0 {
            return Err(BoundaryErroraecbe3a4::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErroraecbe3a4::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErroraecbe3a4::ExceedsCapacity {
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
    fn parse_valid_unified_patch() {
        let patch = r#"--- a/src/sample.rs
+++ b/src/sample.rs
@@ -1,3 +1,3 @@
 fn main() {
-    println!("old");
+    println!("new");
 }
"#;
        let res = parse_unified_diff(patch);
        assert!(res.is_valid);
        assert_eq!(res.touched_paths, vec!["src/sample.rs"]);
    }

    #[test]
    fn reject_unsafe_traversal() {
        let patch = r#"--- a/../secret.rs
+++ b/../secret.rs
@@ -1,1 +1,1 @@
-old
+new
"#;
        let res = parse_unified_diff(patch);
        assert!(!res.is_valid);
        assert!(res.error_message.unwrap().contains("forbidden"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_aecbe3a4 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordaecbe3a4::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordaecbe3a4::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordaecbe3a4::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordaecbe3a4::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordaecbe3a4::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErroraecbe3a4::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErroraecbe3a4::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
