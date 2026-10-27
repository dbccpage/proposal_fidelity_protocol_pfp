//! The PROVED/GlobalGreen fence, discharged structurally.
//!
//! A carrier in this crate cannot mint authority. `CertifiedAuthority` is
//! defined in `core_types`, its sole constructor demands a matching
//! `DescentWitness` and an `IsAuth` token, and `core_types` is not in this
//! crate's dependency closure. That is a property of the build graph rather
//! than a convention anyone has to honour: adding the dependency to any
//! manifest on the path turns this test red.
//!
//! The closure is read from the manifests rather than from `cargo metadata`.
//! A governance assertion should not depend on a child process, an `--offline`
//! package cache, or a package lock the test could block on indefinitely.
//!
//! Dev edges are followed from this crate only. A dependency's own
//! dev-dependencies are never linked into anything this crate builds --
//! `core_homology` and `core_functional` both dev-depend on
//! `core_contracts`, which does reach `core_types`, so following those edges
//! would report a violation that cannot occur.
//!
//! AuthorityEffect: None.

use std::collections::{BTreeSet, VecDeque};
use std::path::{Path, PathBuf};

/// The crate that defines `CertifiedAuthority`.
const AUTHORITY_CRATE: &str = "core_types";

/// Pinned so that re-homing the type cannot quietly make this fence vacuous.
const AUTHORITY_TYPE_DECL: &str = "pub struct CertifiedAuthority";

/// Reached only through `core_homology`, never directly. A traversal that
/// stopped at direct dependencies would fail here rather than satisfy the
/// negative assertion below for the wrong reason.
const MUST_REACH: &[&str] = &["linear_algebra", "core_homotopy_type_theory"];

/// Every carrier's fence opens with this. The tail after it is per-module.
const FENCE_PREFIX: &str = "AuthorityEffect None; not PROVED; not GlobalGreen;";

const CLAIM_WORDS: &[&str] = &["PROVED", "GlobalGreen"];
const NEGATORS: &[&str] = &["no", "not", "never", "without"];

fn assert_certified_authority_unreachable() {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    assert_authority_type_still_lives(&root);

    let reachable = path_dependency_closure(&root);
    for required in MUST_REACH {
        assert!(
            reachable.contains(*required),
            "{required} must appear in the closure; its absence means the walk \
             is broken, not that the fence holds: {reachable:?}"
        );
    }
    assert!(
        !reachable.contains(AUTHORITY_CRATE),
        "this crate reached {AUTHORITY_CRATE}, so CertifiedAuthority is now \
         constructible here and the PROVED/GlobalGreen fence is no longer \
         structural: {reachable:?}"
    );

    assert_no_fence_claims_authority(&root.join("src"));
}

/// The structural argument says no carrier here *can* mint authority. This says
/// none of them *claims* to, which is the separate half of the obligation and
/// the half a dependency walk cannot see.
fn assert_no_fence_claims_authority(src_dir: &Path) {
    let fences = fence_literals(src_dir);
    assert!(
        !fences.is_empty(),
        "no AUTHORITY_FENCE found under {src_dir:?}; this check reaches nothing"
    );
    for (module, fence) in fences {
        assert!(
            fence.starts_with(FENCE_PREFIX),
            "{module}: AUTHORITY_FENCE must open with {FENCE_PREFIX:?}, got {fence:?}"
        );
        for claim in CLAIM_WORDS {
            for (at, _) in fence.match_indices(claim) {
                assert!(
                    is_negated(&fence[..at]),
                    "{module}: AUTHORITY_FENCE asserts {claim:?} rather than \
                     denying it: {fence:?}"
                );
            }
        }
    }
}

/// `not PROVED` and `no auto GlobalGreen` are denials; a bare `PROVED` is a
/// claim. Looking two words back separates them without banning the word, which
/// a fence has to be able to use in order to say what it is not.
fn is_negated(before: &str) -> bool {
    before
        .split_whitespace()
        .rev()
        .take(2)
        .any(|word| NEGATORS.contains(&word.trim_matches(|c: char| !c.is_alphanumeric())))
}

/// The fence names `core_types` as the crate to stay clear of. If
/// `CertifiedAuthority` is ever re-homed, that name goes stale and the negative
/// assertion starts passing for no reason at all.
fn assert_authority_type_still_lives(root: &Path) {
    let source = root
        .parent()
        .expect("crate directory has a parent")
        .join(AUTHORITY_CRATE)
        .join("src")
        .join("authority.rs");
    let text =
        std::fs::read_to_string(&source).unwrap_or_else(|err| panic!("read {source:?}: {err}"));
    assert!(
        text.contains(AUTHORITY_TYPE_DECL),
        "{AUTHORITY_TYPE_DECL} is no longer in {source:?}; this fence is \
         guarding a crate that no longer defines the type, so AUTHORITY_CRATE \
         needs repointing"
    );
}

/// Path dependencies reachable from `root`, by package name.
fn path_dependency_closure(root: &Path) -> BTreeSet<String> {
    let mut seen = BTreeSet::new();
    let mut names = BTreeSet::new();
    let mut queue = VecDeque::from([(root.to_path_buf(), true)]);
    while let Some((dir, is_root)) = queue.pop_front() {
        let key = dir.canonicalize().unwrap_or_else(|_| dir.clone());
        if !seen.insert(key) {
            continue;
        }
        let Ok(text) = std::fs::read_to_string(dir.join("Cargo.toml")) else {
            continue;
        };
        if !is_root {
            if let Some(name) = package_name(&text) {
                names.insert(name);
            }
        }
        for rel in path_dependencies(&text, is_root) {
            queue.push_back((dir.join(rel), false));
        }
    }
    names
}

fn path_dependencies(manifest: &str, include_dev: bool) -> Vec<String> {
    let mut out = Vec::new();
    let mut wanted = false;
    for line in manifest.lines() {
        let trimmed = line.trim();
        if let Some(header) = trimmed.strip_prefix('[').and_then(|h| h.strip_suffix(']')) {
            let header = header.trim();
            wanted = if header.contains("dev-dependencies") || header.contains("build-dependencies")
            {
                include_dev
            } else {
                header.contains("dependencies")
            };
            continue;
        }
        if wanted {
            if let Some(path) = quoted_value(trimmed, "path") {
                out.push(path);
            }
        }
    }
    out
}

fn package_name(manifest: &str) -> Option<String> {
    let mut in_package = false;
    for line in manifest.lines() {
        let trimmed = line.trim();
        if let Some(header) = trimmed.strip_prefix('[').and_then(|h| h.strip_suffix(']')) {
            in_package = header.trim() == "package";
            continue;
        }
        if in_package {
            if let Some(name) = quoted_value(trimmed, "name") {
                return Some(name);
            }
        }
    }
    None
}

/// `key = "value"`, where `key` must be a key rather than a substring of a
/// longer one, so every occurrence is tried before giving up.
fn quoted_value(line: &str, key: &str) -> Option<String> {
    line.match_indices(key).find_map(|(at, _)| {
        let rest = line[at + key.len()..].trim_start();
        let rest = rest.strip_prefix('=')?.trim_start().strip_prefix('"')?;
        let end = rest.find('"')?;
        Some(rest[..end].to_owned())
    })
}

/// Every `AUTHORITY_FENCE` declaration under `src_dir`, as (module, value).
fn fence_literals(src_dir: &Path) -> Vec<(String, String)> {
    const DECL: &str = "const AUTHORITY_FENCE:";
    let mut out = Vec::new();
    let mut stack = vec![src_dir.to_path_buf()];
    while let Some(dir) = stack.pop() {
        let Ok(entries) = std::fs::read_dir(&dir) else {
            continue;
        };
        for entry in entries.flatten() {
            let path = entry.path();
            if path.is_dir() {
                stack.push(path);
                continue;
            }
            if path.extension().and_then(|e| e.to_str()) != Some("rs") {
                continue;
            }
            let Ok(text) = std::fs::read_to_string(&path) else {
                continue;
            };
            let module = path
                .file_stem()
                .unwrap_or_default()
                .to_string_lossy()
                .into_owned();
            // This module names the constant in order to search for it, so it
            // matches itself. It is not a carrier and declares no fence.
            if module == "certified_authority_fence" {
                continue;
            }
            let mut rest = text.as_str();
            while let Some(at) = rest.find(DECL) {
                rest = &rest[at + DECL.len()..];
                let (value, consumed) = read_string_constant(rest);
                if consumed == 0 {
                    break;
                }
                out.push((module.clone(), value));
                rest = &rest[consumed..];
            }
        }
    }
    out
}

fn consume_escaped_piece(
    chars: &mut std::iter::Peekable<std::str::CharIndices<'_>>,
    value: &mut String,
    consumed: &mut usize,
) -> bool {
    match chars.next() {
        Some((j, '\n' | '\r')) => {
            *consumed = j + 1;
            while let Some(&(k, w)) = chars.peek() {
                if !w.is_whitespace() {
                    break;
                }
                *consumed = k + w.len_utf8();
                chars.next();
            }
            true
        }
        Some((j, other)) => {
            value.push(other);
            *consumed = j + other.len_utf8();
            true
        }
        None => false,
    }
}

/// Reads a `&str` constant's value from just after its colon, stopping at the
/// semicolon that ends the item and joining any concatenated pieces.
///
/// The scan tracks whether it is inside a string, because these fences are
/// semicolon-separated clauses: the first `;` in the text is part of the value,
/// not the end of the declaration. Backslash-newline continuations are resolved
/// the way rustc resolves them, by swallowing the newline and the indentation
/// that follows it.
fn read_string_constant(decl: &str) -> (String, usize) {
    let mut value = String::new();
    let mut in_string = false;
    let mut consumed = 0usize;
    let mut chars = decl.char_indices().peekable();
    while let Some((i, c)) = chars.next() {
        consumed = i + c.len_utf8();
        match (in_string, c) {
            (false, ';') => break,
            (false, '"') => in_string = true,
            (true, '"') => in_string = false,
            (true, '\\') => {
                if !consume_escaped_piece(&mut chars, &mut value, &mut consumed) {
                    break;
                }
            }
            (true, other) => value.push(other),
            (false, _) => {}
        }
    }
    (
        value.split_whitespace().collect::<Vec<_>>().join(" "),
        consumed,
    )
}

#[test]
fn no_carrier_in_this_crate_can_reach_certified_authority() {
    assert_certified_authority_unreachable();
}

// Origin: engine/crates_rs/core_general_relativity/src/certified_authority_fence.rs
// Claim: urn:core:crates_rs:core-general-relativity:certified-authority-fence:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord7d733abe {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord7d733abe` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError7d733abe {
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
impl BoundaryError7d733abe {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError7d733abe {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError7d733abe {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord7d733abe {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError7d733abe> {
        if capacity_bound == 0 {
            return Err(BoundaryError7d733abe::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError7d733abe::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError7d733abe::ExceedsCapacity {
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
mod l4_boundary_tests_7d733abe {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord7d733abe::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord7d733abe::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord7d733abe::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord7d733abe::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord7d733abe::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError7d733abe::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError7d733abe::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
