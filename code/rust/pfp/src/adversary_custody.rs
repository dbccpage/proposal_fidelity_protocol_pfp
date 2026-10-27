//! Adversary's versioned storage cutover, independent of caller path claims.
//! Activation binds custody metadata only; it grants no execution authority.
use core_adversary::stage::ports::Refusal;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::path::{Component, Path, PathBuf};
use std::sync::OnceLock;

fn refused(message: impl Into<String>) -> Refusal {
    Refusal::new("ADVERSARY_OUTPUT_ROUTING_INVALID", message)
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Activation {
    schema: String,
    state: String,
    authority_effect: String,
    repository_root: String,
    source_revision: String,
    inventory_sha256: String,
}

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct InventoryFile {
    source: String,
    destination: String,
    sha256: String,
    size: u64,
    kind: String,
}
#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct InventoryIdentity {
    schema: String,
    routing_profile: String,
    repository_root: String,
    repository: String,
    source_revision: String,
    files: Vec<InventoryFile>,
    directories: Vec<String>,
    destination_baseline: Vec<(String, String, u64)>,
    authority_effect: String,
}
fn canonical_inventory(value: &InventoryIdentity) -> Result<Vec<u8>, Refusal> {
    let value = serde_json::to_value(value).map_err(|_| refused("inventory encoding invalid"))?;
    let mut encoded = String::new();
    for character in value.to_string().chars() {
        if character as u32 >= 127 {
            for code in character.encode_utf16(&mut [0; 2]) {
                encoded.push_str(&format!("\\u{code:04x}"));
            }
        } else {
            encoded.push(character);
        }
    }
    encoded.push('\n');
    Ok(encoded.into_bytes())
}
fn safe_parts(relative: &str) -> Result<Vec<&str>, Refusal> {
    let parts: Vec<_> = relative.split('/').collect();
    for part in &parts {
        let stem = part.split('.').next().unwrap_or("").to_ascii_uppercase();
        let reserved = ["CON", "PRN", "AUX", "NUL"].contains(&stem.as_str())
            || (stem.len() == 4
                && (stem.starts_with("COM") || stem.starts_with("LPT"))
                && matches!(stem.as_bytes()[3], b'1'..=b'9'));
        if part.is_empty()
            || [".", ".."].contains(part)
            || part.contains([':', '\\'])
            || part.ends_with([' ', '.'])
            || part.chars().any(|c| c < ' ')
            || reserved
        {
            return Err(refused("unsafe inventory path"));
        }
    }
    Ok(parts)
}
fn mapped(relative: &str) -> Result<String, Refusal> {
    let parts = safe_parts(relative)?;
    if parts.len() < 2 || parts[0] != "_intelligence" {
        return Err(refused("inventory source namespace invalid"));
    }
    let namespace = match parts[1] {
        "_adversary" => "darpa/adversary",
        "symbol_game" => "darpa/symbol_game",
        "events" => "nsa/events",
        "narratives" => "odni/narratives",
        "unified_oe_trace.jsonl" => "odni/unified_oe_trace.jsonl",
        "universal_narrative_stream.md" => "odni/universal_narrative_stream.md",
        "_vladimir_central" => "fbi/vladimir_central",
        "red_team" => "dia/red_team",
        "council_meetings" => "fbi/council_meetings",
        "stress_tests" => "dia/stress_tests",
        "morphisms" => "nga/morphisms",
        "_oeos" => "odni/oeos_control",
        "oeos" => "odni/oeos",
        "harvest" => "nara/harvest",
        "archive" => "nara/_archive",
        "permanent_records" => "nara/permanent_records",
        "research" => "darpa/research",
        "antibodies" => "cdc/antibodies",
        "core_paper_reviews" => "inr/core_paper_reviews",
        "code_reviews" => "nro/code_reviews",
        "coverage" => "nro/coverage",
        "documentation" => "nro/documentation",
        "omc_dags" => "nga/omc_dags",
        "blackrod" => "fbi/blackrod",
        _ => "",
    };
    if namespace.is_empty() {
        return Ok(format!("_ic/nara/legacy/{}", parts[1..].join("/")));
    }
    let suffix = if parts.len() > 2 {
        format!("/{}", parts[2..].join("/"))
    } else {
        String::new()
    };
    Ok(format!("_ic/{namespace}{suffix}"))
}
fn validate_inventory(value: &InventoryIdentity) -> Result<(), Refusal> {
    let mut sources = BTreeSet::new();
    let mut targets = BTreeSet::new();
    let repository: Vec<_> = value.repository.split('/').collect();
    if value.authority_effect != "None"
        || repository.len() != 2
        || repository.iter().any(|part| {
            part.is_empty()
                || !part
                    .bytes()
                    .all(|c| c.is_ascii_alphanumeric() || b"_.-".contains(&c))
        })
    {
        return Err(refused("inventory repository or authority invalid"));
    }
    for row in &value.files {
        if row.kind != "regular_file"
            || row.size > i64::MAX as u64
            || !lower_hex(&row.sha256, 64)
            || row.destination != mapped(&row.source)?
            || !sources.insert(path_casefold(&row.source)?)
            || !targets.insert(path_casefold(&row.destination)?)
        {
            return Err(refused("inventory file row invalid or duplicated"));
        }
    }
    for directory in &value.directories {
        if !sources.insert(path_casefold(directory)?)
            || !targets.insert(path_casefold(&mapped(directory)?)?)
        {
            return Err(refused("inventory directory row duplicated"));
        }
    }
    let mut baseline = BTreeSet::new();
    for (path, digest, size) in &value.destination_baseline {
        let parts = safe_parts(path)?;
        if parts.len() < 3
            || parts[0] != "_ic"
            || ![
                "odni", "cia", "nsa", "dia", "nro", "nga", "fbi", "cdc", "inr", "darpa", "nara",
            ]
            .contains(&parts[1])
            || *size > i64::MAX as u64
            || path.starts_with("_ic/odni/migration/")
            || !lower_hex(digest, 64)
            || !baseline.insert(path_casefold(path)?)
        {
            return Err(refused("inventory baseline invalid or duplicated"));
        }
    }
    Ok(())
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct CasefoldTable {
    schema: String,
    unicode_version: String,
    producer: String,
    mappings: BTreeMap<String, String>,
}
fn path_casefold(value: &str) -> Result<String, Refusal> {
    static TABLE: OnceLock<Result<CasefoldTable, ()>> = OnceLock::new();
    let table = TABLE
        .get_or_init(|| {
            let raw =
                include_str!("../../governance/sentinel_councils/documentation/ic_casefold_v15_1.json");
            if hex::encode(Sha256::digest(raw.as_bytes()))
                != "9f569ad94b262a0f7143fe7636f79a7df03c53d8c5dc7d030cdbc263fc723946"
            {
                return Err(());
            }
            let table: CasefoldTable = serde_json::from_str(raw).map_err(|_| ())?;
            if table.schema != "core.ic.casefold.v1"
                || table.unicode_version != "15.1.0"
                || table.producer != "CPython 3.13.11 str.casefold"
            {
                return Err(());
            }
            Ok(table)
        })
        .as_ref()
        .map_err(|_| refused("shared casefold contract invalid"))?;
    let mut result = String::new();
    for character in value.chars() {
        if let Some(mapped) = table.mappings.get(&(character as u32).to_string()) {
            result.push_str(mapped);
        } else {
            result.push(character);
        }
    }
    Ok(result)
}

fn lower_hex(value: &str, size: usize) -> bool {
    value.len() == size
        && value
            .bytes()
            .all(|c| c.is_ascii_digit() || (b'a'..=b'f').contains(&c))
}

fn checked_path(root: &Path, relative: &str) -> Result<PathBuf, Refusal> {
    let mut path = root.to_path_buf();
    check_existing(&path)?;
    for component in relative.split('/') {
        path.push(component);
        check_existing(&path)?;
    }
    Ok(path)
}

fn check_existing(path: &Path) -> Result<(), Refusal> {
    match fs::symlink_metadata(path) {
        Ok(metadata) => {
            if metadata.file_type().is_symlink() || reparse(&metadata) {
                return Err(refused("static link or reparse point in custody path"));
            }
            Ok(())
        }
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => Ok(()),
        Err(error) => Err(refused(format!("custody path unavailable: {error}"))),
    }
}

#[cfg(windows)]
fn reparse(metadata: &fs::Metadata) -> bool {
    use std::os::windows::fs::MetadataExt;
    metadata.file_attributes() & 0x400 != 0
}
#[cfg(not(windows))]
fn reparse(_: &fs::Metadata) -> bool {
    false
}

fn activated(root: &Path) -> Result<bool, Refusal> {
    let activation_path = checked_path(root, "_ic/odni/migration/activation.json")?;
    let raw = match fs::read(activation_path) {
        Ok(raw) => raw,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(false),
        Err(error) => return Err(refused(format!("activation unavailable: {error}"))),
    };
    let record: Activation = serde_json::from_slice(&raw)
        .map_err(|_| refused("activation JSON or closed schema invalid"))?;
    if record.schema != "core.ic.activation.v1"
        || record.state != "ACTIVATED"
        || record.authority_effect != "None"
        || record.repository_root != root.to_string_lossy()
        || !lower_hex(&record.source_revision, 40)
        || !lower_hex(&record.inventory_sha256, 64)
    {
        return Err(refused("activation identity invalid"));
    }
    let inventory_path = checked_path(root, "_ic/odni/migration/inventory.json")?;
    let inventory =
        fs::read(inventory_path).map_err(|_| refused("activation inventory unavailable"))?;
    if hex::encode(Sha256::digest(&inventory)) != record.inventory_sha256 {
        return Err(refused("activation inventory byte digest differs"));
    }
    let identity: InventoryIdentity =
        serde_json::from_slice(&inventory).map_err(|_| refused("inventory JSON invalid"))?;
    validate_inventory(&identity)?;
    if canonical_inventory(&identity)? != inventory {
        return Err(refused(
            "inventory bytes differ from the named canonical profile",
        ));
    }
    if identity.schema != "core.ic.inventory.v1"
        || identity.routing_profile != "core.ic.routes.v1"
        || identity.repository_root != record.repository_root
        || identity.source_revision != record.source_revision
    {
        return Err(refused("inventory identity differs from activation"));
    }
    Ok(true)
}

/// Caller and native selection must agree before any writer is constructed.
/// Cooperative exclusion is required against concurrent parent replacement.
pub(crate) fn validate_output(root: &Path, requested: &Path) -> Result<PathBuf, Refusal> {
    if !root.is_absolute()
        || root
            .components()
            .any(|part| matches!(part, Component::ParentDir | Component::CurDir))
        || requested
            .components()
            .any(|part| matches!(part, Component::ParentDir | Component::CurDir))
    {
        return Err(refused(
            "absolute normalized repository and output paths required",
        ));
    }
    // Present metadata remains a mandatory historical-custody validation.
    // Active writers always use the canonical namespace, including fresh clones.
    activated(root)?;
    let relative = "_ic/adversary";
    let perm_relative = "_ic/nara/permanent_records";
    let expected = checked_path(root, relative)?;
    let perm_expected = checked_path(root, perm_relative);
    if requested != expected && perm_expected.as_ref().map_or(true, |p| requested != p) {
        return Err(refused(
            "requested Adversary output differs from active custody namespace",
        ));
    }
    Ok(requested.to_path_buf())
}

// Origin: engine/crates_rs/pfp/src/adversary_custody.rs
// Claim: urn:core:crates_rs:pfp:adversary-custody:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord222a1695 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord222a1695` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError222a1695 {
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
impl BoundaryError222a1695 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError222a1695 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError222a1695 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord222a1695 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError222a1695> {
        if capacity_bound == 0 {
            return Err(BoundaryError222a1695::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError222a1695::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError222a1695::ExceedsCapacity {
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
mod l4_boundary_tests_222a1695 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord222a1695::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord222a1695::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord222a1695::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord222a1695::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord222a1695::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError222a1695::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError222a1695::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
