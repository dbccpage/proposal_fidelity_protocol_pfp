//! Published-corpus coordinates and carrier grammar, lowered from the contract
//! corpus at build time.
//!
//! Source of truth is
//! `src/contract_canonical_definitions/02_evidence/published_series_coordinates.contract.yaml`
//! and `.../published_paper_carrier.contract.yaml`. `build.rs` reads their
//! `definition` blocks and emits the constants below, so consuming crates
//! (`core_state`, `core_rip_papers`) carry no repository paths, filename
//! markers, or row counts of their own.
//!
//! Repository paths in Rust drift silently: the published-series agreement
//! matrix is compared field-wise and never resolved against the filesystem, so
//! the PR #1191 programme reorganization left every coordinate stale while the
//! crate still compiled and every test passed. Editing the contract and
//! rebuilding is now the only way to move a coordinate.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_1ac1a20e;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_1ac1a20e<T> = std::result::Result<T, BoundaryError_1ac1a20e>;
include!(concat!(env!("OUT_DIR"), "/generated_published_corpus.rs"));

impl PublishedPaperCoordinate {
    /// Look up a coordinate by its contract `paper_id` (e.g. `"paper004"`).
    #[must_use]
    pub fn by_paper_id(paper_id: &str) -> Option<&'static Self> {
        PUBLISHED_SERIES_COORDINATES
            .iter()
            .find(|c| c.paper_id == paper_id)
    }
}

/// Does `name` carry a claim-ledger marker? Case-insensitive on the marker,
/// case-sensitive on the extension: every ledger in the tree uses lowercase
/// `.md`, and both the canonical `*_Claim_Ledger.md` and the lowercase
/// `*_claim_ledger.md` spellings are accepted.
#[must_use]
pub fn is_claim_ledger_name(file_name: &str) -> bool {
    file_name.ends_with(".md")
        && file_name
            .to_ascii_lowercase()
            .contains(CLAIM_LEDGER_MARKER_LOWER)
}

/// Split a leading **local** paper key off `name` per the contracted grammar:
/// exactly [`PAPER_ID_DIGITS`] ASCII digits, an optional single lowercase letter,
/// then one of [`PAPER_ID_SEPARATORS`]. A longer digit run is rejected, not
/// truncated.
///
/// The result is the LOCAL key: the paper's id within its enclosing folder, with
/// no programme scope attached. It is ambiguous across programmes on its own —
/// `012` names both `002_finite_obstruction_calculus/006_degree_wise_dsl`'s
/// neighbour and the corpus-root `012_mutually_unbiased_bases`. Use [`PaperId`]
/// when a key must identify a paper across the whole corpus.
///
/// This function deliberately does NOT accept a scoped key: `paper_id_of` is
/// what [`is_gt_tower_prefix`] classifies on, and GT-tower-ness is a property of
/// the LEAF, so a scoped key must refuse here rather than resolve to its scope.
#[must_use]
pub fn paper_id_of(name: &str) -> Option<String> {
    let bytes = name.as_bytes();
    if bytes.len() <= PAPER_ID_DIGITS {
        return None;
    }
    if !bytes[..PAPER_ID_DIGITS].iter().all(u8::is_ascii_digit) {
        return None;
    }
    let mut end = PAPER_ID_DIGITS;
    if bytes[end].is_ascii_lowercase() {
        end += 1;
    }
    let sep = *bytes.get(end)? as char;
    if !PAPER_ID_SEPARATORS.contains(&sep) {
        return None;
    }
    Some(name[..end].to_owned())
}

/// Is `s` a bare local paper key — [`PAPER_ID_DIGITS`] ASCII digits and an
/// optional single lowercase letter, with nothing else? This is the shape
/// [`paper_id_of`] returns, minus the trailing separator it requires as a
/// delimiter.
#[must_use]
fn is_local_paper_key(s: &str) -> bool {
    let bytes = s.as_bytes();
    if bytes.len() < PAPER_ID_DIGITS {
        return false;
    }
    if !bytes[..PAPER_ID_DIGITS].iter().all(u8::is_ascii_digit) {
        return false;
    }
    match bytes.len() - PAPER_ID_DIGITS {
        0 => true,
        1 => bytes[PAPER_ID_DIGITS].is_ascii_lowercase(),
        _ => false,
    }
}

/// A corpus-wide paper key: the enclosing programme's local key, then
/// [`SCOPED_PAPER_ID_SEPARATOR`], then the paper's own local key.
///
/// A local key alone does not identify a paper — `PL-012-1` in the ledgers
/// denotes `002_finite_obstruction_calculus/006_degree_wise_dsl`, not the
/// corpus-root `012_mutually_unbiased_bases`. The scope disambiguates.
///
/// The separator is contracted (`scoped_paper_id.separator`) and is disjoint from
/// [`PAPER_ID_SEPARATORS`], which `build.rs` asserts. Disjointness is the point:
/// feeding a rendered `PaperId` back through [`paper_id_of`] yields `None` — a
/// typed refusal — where a separator drawn from [`PAPER_ID_SEPARATORS`] would
/// instead answer `Some(scope)` and silently collapse the key.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct PaperId {
    scope: String,
    leaf: String,
}

impl PaperId {
    /// Compose a scoped key from an enclosing folder name and a leaf folder name.
    ///
    /// Returns `None` when `leaf` is not paper-shaped. When `enclosing` is `None`,
    /// or names a folder that is not itself paper-shaped, the key is SELF-SCOPED
    /// (per [`SCOPED_PAPER_ID_ROOT_IS_SELF`]): scope and leaf coincide, so
    /// `999_published_in_general_media` at the corpus root keys as `999.999`.
    #[must_use]
    pub fn compose(enclosing: Option<&str>, leaf: &str) -> Option<Self> {
        let leaf_key = paper_id_of(leaf)?;
        let scope = match enclosing.and_then(paper_id_of) {
            Some(scope) => scope,
            None if SCOPED_PAPER_ID_ROOT_IS_SELF => leaf_key.clone(),
            None => return None,
        };
        Some(Self {
            scope,
            leaf: leaf_key,
        })
    }

    /// The enclosing programme's local key.
    #[must_use]
    pub fn scope(&self) -> &str {
        &self.scope
    }

    /// The paper's own local key, within its programme.
    #[must_use]
    pub fn leaf(&self) -> &str {
        &self.leaf
    }

    /// Does this key carry no enclosing programme — scope equal to leaf?
    #[must_use]
    pub fn is_self_scoped(&self) -> bool {
        self.scope == self.leaf
    }
}

impl std::fmt::Display for PaperId {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            f,
            "{}{}{}",
            self.scope, SCOPED_PAPER_ID_SEPARATOR, self.leaf
        )
    }
}

/// Why a string is not a scoped paper key.
#[derive(Debug, Clone, Copy, PartialEq, Eq, thiserror::Error)]
pub enum ParsePaperIdError {
    /// The input does not carry exactly one [`SCOPED_PAPER_ID_SEPARATOR`]. A bare
    /// local key (`009`) lands here: it names no scope, so it is not a paper key.
    #[error(
        "not a scoped paper key: expected exactly one {SCOPED_PAPER_ID_SEPARATOR:?} separator"
    )]
    NotScoped,
    /// One side of the separator is not a bare local paper key.
    #[error("scoped paper key component is not a local paper key")]
    MalformedComponent,
}

impl std::str::FromStr for PaperId {
    type Err = ParsePaperIdError;

    /// Accepts ONLY the scoped production `<scope><sep><leaf>`. An unscoped local
    /// key is refused rather than widened, so a caller cannot mistake a local key
    /// for a corpus-wide one.
    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let mut parts = s.split(SCOPED_PAPER_ID_SEPARATOR);
        let (Some(scope), Some(leaf), None) = (parts.next(), parts.next(), parts.next()) else {
            return Err(ParsePaperIdError::NotScoped);
        };
        if !is_local_paper_key(scope) || !is_local_paper_key(leaf) {
            return Err(ParsePaperIdError::MalformedComponent);
        }
        Ok(Self {
            scope: scope.to_owned(),
            leaf: leaf.to_owned(),
        })
    }
}

/// Is `name` a GT-tower folder prefix (`993_`..=`999_`)?
#[must_use]
pub fn is_gt_tower_prefix(name: &str) -> bool {
    let Some(id) = paper_id_of(name) else {
        return false;
    };
    id[..PAPER_ID_DIGITS]
        .parse::<u32>()
        .is_ok_and(|n| (GT_TOWER_PREFIX_FIRST..=GT_TOWER_PREFIX_LAST).contains(&n))
}

// Origin: engine/crates_rs/core_contracts/src/published_corpus.rs
// Claim: urn:core:crates_rs:core-contracts:published-corpus:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn coordinates_are_present_and_ascending() {
        assert!(
            !PUBLISHED_SERIES_COORDINATES.is_empty(),
            "build.rs emitted an empty coordinate table"
        );
        let mut ids: Vec<&str> = PUBLISHED_SERIES_COORDINATES
            .iter()
            .map(|c| c.paper_id)
            .collect();
        let unsorted = ids.clone();
        ids.sort_unstable();
        assert_eq!(unsorted, ids, "coordinates must stay ascending by paper_id");
        ids.dedup();
        assert_eq!(
            ids.len(),
            unsorted.len(),
            "duplicate paper_id in the corpus"
        );
    }

    #[test]
    fn composed_paths_start_at_the_published_root() {
        for c in PUBLISHED_SERIES_COORDINATES {
            for path in [c.main_path, c.claim_ledger_path] {
                assert!(
                    path.starts_with(PUBLISHED_ROOT),
                    "{}: {path} is not under {PUBLISHED_ROOT}",
                    c.paper_id
                );
            }
            assert_ne!(
                c.main_path, c.claim_ledger_path,
                "{}: manuscript and claim ledger are the same file",
                c.paper_id
            );
            assert!(c.claim_row_count > 0, "{}: zero claim rows", c.paper_id);
        }
    }

    #[test]
    fn paper_id_grammar_matches_the_contract() {
        assert_eq!(
            paper_id_of("000_primitive_axiomatics").as_deref(),
            Some("000")
        );
        assert_eq!(paper_id_of("000a_vector").as_deref(), Some("000a"));
        assert_eq!(paper_id_of("012 Degree-Wise").as_deref(), Some("012"));
        assert_eq!(paper_id_of("053a-exchange").as_deref(), Some("053a"));
        // A fourth leading digit is rejected outright, never truncated.
        assert_eq!(paper_id_of("1234_not_a_paper"), None);
        assert_eq!(paper_id_of("not_a_paper"), None);
        assert_eq!(paper_id_of("000"), None, "a bare id has no separator");
    }

    #[test]
    fn a_scoped_key_does_not_round_trip_through_paper_id_of() {
        // The property that makes `.` the correct separator. Feeding a scoped key
        // back through the LOCAL grammar must refuse, not silently truncate the key
        // to its scope. With `_` or `-` this assertion would read `Some("009")`.
        let scoped = PaperId::compose(Some("009_gtoc_ground_up"), "000_gtoc_ground_state")
            .expect("leaf is paper-shaped");
        assert_eq!(scoped.to_string(), "009.000");
        assert_eq!(
            paper_id_of(&scoped.to_string()),
            None,
            "a scoped key must be refused by the local grammar, never truncated"
        );
    }

    #[test]
    fn the_scoped_separator_is_disjoint_from_the_local_separators() {
        assert!(
            !PAPER_ID_SEPARATORS.contains(&SCOPED_PAPER_ID_SEPARATOR),
            "the scoped separator {SCOPED_PAPER_ID_SEPARATOR:?} is also a local paper-id \
             separator, so paper_id_of would truncate a scoped key to its scope"
        );
    }

    #[test]
    fn a_paper_with_no_enclosing_programme_is_self_scoped() {
        // The contracted policy this test pins. A compile-time check, so flipping
        // `root_scope_is_self` in the contract fails the build here rather than
        // leaving the assertions below quietly testing the wrong branch.
        const { assert!(SCOPED_PAPER_ID_ROOT_IS_SELF) };

        let root =
            PaperId::compose(None, "999_published_in_general_media").expect("leaf is paper-shaped");
        assert!(root.is_self_scoped());
        assert_eq!(root.scope(), "999");
        assert_eq!(root.leaf(), "999");
        assert_eq!(root.to_string(), "999.999");

        // An enclosing folder that is not itself paper-shaped is not a programme.
        let unscoped = PaperId::compose(Some("input"), "000c_Foo").expect("leaf is paper-shaped");
        assert!(unscoped.is_self_scoped());
        assert_eq!(unscoped.to_string(), "000c.000c");

        // A leaf that is not paper-shaped has no key at all.
        assert_eq!(PaperId::compose(Some("009_gtoc_ground_up"), "notes"), None);
    }

    #[test]
    fn scoped_keys_parse_back_only_in_the_scoped_production() {
        let key: PaperId = "009.000".parse().expect("scoped production");
        assert_eq!(key.scope(), "009");
        assert_eq!(key.leaf(), "000");
        assert!(!key.is_self_scoped());
        assert_eq!(
            key,
            PaperId::compose(Some("009_gtoc_ground_up"), "000_gtoc_ground_state").unwrap()
        );

        assert!("009_000".parse::<PaperId>().is_err());
        assert!("009".parse::<PaperId>().is_err());
        assert!("009.000.1".parse::<PaperId>().is_err());
        assert!("009.".parse::<PaperId>().is_err());
        assert!("abc.000".parse::<PaperId>().is_err());
    }

    #[test]
    fn gt_tower_prefixes_are_the_contracted_range() {
        assert!(is_gt_tower_prefix("999_GTLA"));
        assert!(is_gt_tower_prefix("993_GTFOC"));
        assert!(!is_gt_tower_prefix("992_not_tower"));
        assert!(!is_gt_tower_prefix("000_primitive_axiomatics"));
    }

    #[test]
    fn claim_ledger_detection_accepts_both_spellings() {
        assert!(is_claim_ledger_name(
            "000_Primitive_Axiomatics_Claim_Ledger.md"
        ));
        assert!(is_claim_ledger_name("001_gtoc_time_claim_ledger.md"));
        assert!(!is_claim_ledger_name("000_primitive_axiomatics.md"));
        assert!(!is_claim_ledger_name("some_Claim_Ledger.txt"));
    }
}
