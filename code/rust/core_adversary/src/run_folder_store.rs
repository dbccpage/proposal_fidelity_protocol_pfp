//! Filesystem adapter for historical bundles and consolidated UNS/DDC/UTS/MAM bundles.
use crate::mam::{render_mam, MAM_FILES, MAM_SCHEMA};
use crate::render_record::RenderRecord;
use crate::run_persistence::{
    receipt_id_from_parts, receipt_id_from_parts_v2, receipt_id_from_parts_v3, summary_core_bytes,
    validate_uts, RunArtifactPort, RUN_BUNDLE_V2, RUN_BUNDLE_V3,
};
use crate::stage::ports::Refusal;
use std::fs;
use std::path::{Path, PathBuf};
use tempfile::TempDir;

fn unavailable(message: impl Into<String>) -> Refusal {
    Refusal::new("RUN_FOLDER_IO_UNAVAILABLE", message)
}
pub struct RunFolderStore {
    output_root: PathBuf,
    temporary: Option<TempDir>,
    destination: Option<PathBuf>,
}
impl RunFolderStore {
    pub fn new(output_root: PathBuf) -> Self {
        Self {
            output_root,
            temporary: None,
            destination: None,
        }
    }
}
impl RunArtifactPort for RunFolderStore {
    fn begin(&mut self, directory_name: &str) -> Result<(), Refusal> {
        if self.temporary.is_some() {
            return Err(unavailable("run transaction already active"));
        }
        let mut components = Path::new(directory_name).components();
        if !matches!(components.next(), Some(std::path::Component::Normal(_)))
            || components.next().is_some()
        {
            return Err(unavailable("invalid run directory component"));
        }
        let root = self.output_root.join("runs");
        fs::create_dir_all(&root).map_err(|e| unavailable(e.to_string()))?;
        let destination = root.join(directory_name);
        if destination.exists() {
            return Err(Refusal::new(
                "RUN_FOLDER_EXISTS",
                format!(
                    "Refusing to overwrite existing run folder: {}",
                    destination.display()
                ),
            ));
        }
        self.temporary = Some(
            tempfile::Builder::new()
                .prefix(&format!(".{directory_name}."))
                .tempdir_in(root)
                .map_err(|e| unavailable(e.to_string()))?,
        );
        self.destination = Some(destination);
        Ok(())
    }
    fn write_artifact(&mut self, name: &str, bytes: &[u8]) -> Result<(), Refusal> {
        if ![
            "novella.md",
            "uns.md",
            "dda_actions.jsonl",
            "ddc.jsonl",
            "summary.json",
            "receipt.json",
            "uts.jsonl",
        ]
        .contains(&name)
            && !MAM_FILES.iter().any(|(file, _)| *file == name)
        {
            return Err(unavailable("unknown run artifact"));
        }
        let temporary = self
            .temporary
            .as_ref()
            .ok_or_else(|| unavailable("no active run transaction"))?;
        let path = temporary.path().join(name);
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent).map_err(|e| unavailable(e.to_string()))?;
        }
        fs::write(path, bytes).map_err(|e| unavailable(e.to_string()))
    }
    fn commit(&mut self) -> Result<String, Refusal> {
        let destination = self
            .destination
            .take()
            .ok_or_else(|| unavailable("no run destination"))?;
        let path = destination
            .to_str()
            .ok_or_else(|| unavailable("run destination must be UTF-8"))?
            .to_string();
        let temporary = self
            .temporary
            .take()
            .ok_or_else(|| unavailable("no active run transaction"))?;
        fs::rename(temporary.path(), destination).map_err(|e| unavailable(e.to_string()))?;
        let _completed_temporary_path = temporary.keep();
        Ok(path)
    }
    fn abort(&mut self) {
        self.temporary = None;
        self.destination = None;
    }
}
/// Prefer the canonical tape while retaining pre-DDC historical readback.
fn read_tape(run_dir: &Path) -> Result<Vec<u8>, Refusal> {
    let ddc = run_dir.join("ddc.jsonl");
    let path = if ddc.exists() {
        ddc
    } else {
        run_dir.join("dda_actions.jsonl")
    };
    fs::read(path).map_err(|e| unavailable(e.to_string()))
}
pub fn recompute_receipt_id(run_dir: &Path) -> Result<String, Refusal> {
    let summary =
        fs::read_to_string(run_dir.join("summary.json")).map_err(|e| unavailable(e.to_string()))?;
    let core = summary_core_bytes(&RenderRecord::from_json(&summary)?)?;
    let schema = read_receipt_schema(run_dir)?;
    let consolidated = schema.as_deref() == Some(RUN_BUNDLE_V3);
    let (novella, dda) = read_novella_and_dda(run_dir, consolidated)?;
    if consolidated {
        let uts = read_run_file(run_dir, "uts.jsonl")?;
        return receipt_id_from_parts_v3(&novella, &dda, &core, &uts);
    }
    if schema.as_deref() == Some(RUN_BUNDLE_V2) {
        let uts = read_run_file(run_dir, "uts.jsonl")?;
        return receipt_id_from_parts_v2(&novella, &dda, &core, &uts);
    }
    receipt_id_from_parts(&novella, &dda, &core)
}

fn read_run_file(run_dir: &Path, name: &str) -> Result<Vec<u8>, Refusal> {
    fs::read(run_dir.join(name)).map_err(|e| unavailable(e.to_string()))
}

fn read_receipt_schema(run_dir: &Path) -> Result<Option<String>, Refusal> {
    let receipt_path = run_dir.join("receipt.json");
    if !receipt_path.exists() {
        return Ok(None);
    }
    let receipt = fs::read_to_string(receipt_path).map_err(|e| unavailable(e.to_string()))?;
    let receipt: serde_json::Value =
        serde_json::from_str(&receipt).map_err(|e| unavailable(e.to_string()))?;
    Ok(receipt["bundle_schema_version"].as_str().map(str::to_owned))
}

fn read_novella_and_dda(run_dir: &Path, consolidated: bool) -> Result<(Vec<u8>, Vec<u8>), Refusal> {
    let novella_name = if consolidated { "uns.md" } else { "novella.md" };
    let novella = read_run_file(run_dir, novella_name)?;
    let dda = if consolidated {
        read_run_file(run_dir, "ddc.jsonl")?
    } else {
        read_tape(run_dir)?
    };
    Ok((novella, dda))
}

fn is_redirected(metadata: &fs::Metadata) -> bool {
    #[cfg(windows)]
    {
        use std::os::windows::fs::MetadataExt;
        if metadata.file_attributes() & 0x400 != 0 {
            return true;
        }
    }
    metadata.file_type().is_symlink()
}

fn ensure_regular_unredirected(path: &Path) -> Result<(), Refusal> {
    let metadata = fs::symlink_metadata(path).map_err(|e| unavailable(e.to_string()))?;
    if !metadata.is_file() || is_redirected(&metadata) {
        return Err(unavailable("bundle files must be regular files"));
    }
    Ok(())
}

/// Version-aware readback, also used for idempotent publication.
pub fn verify_reported_bundle(run_dir: &Path) -> Result<String, Refusal> {
    let dir_meta = fs::symlink_metadata(run_dir).map_err(|e| unavailable(e.to_string()))?;
    if is_redirected(&dir_meta) {
        return Err(unavailable("run folder cannot be redirected"));
    }
    ensure_regular_unredirected(&run_dir.join("receipt.json"))?;
    let receipt: serde_json::Value =
        serde_json::from_slice(&read_run_file(run_dir, "receipt.json")?)
            .map_err(|e| unavailable(e.to_string()))?;
    let (consolidated, schema) = resolve_bundle_schema(&receipt)?;
    let (legacy_dda, has_mam) = verify_bundle_directory_entries(run_dir, &receipt, consolidated)?;
    let summary = verify_bundle_digests_and_summary(
        run_dir,
        &receipt,
        schema,
        consolidated,
        legacy_dda,
        has_mam,
    )?;
    verify_bundle_uts_and_identity(run_dir, &receipt, &summary)
}

fn resolve_bundle_schema(receipt: &serde_json::Value) -> Result<(bool, &'static str), Refusal> {
    let consolidated = receipt["bundle_schema_version"] == RUN_BUNDLE_V3;
    let schema = if consolidated {
        RUN_BUNDLE_V3
    } else {
        RUN_BUNDLE_V2
    };
    if receipt["bundle_schema_version"] != schema {
        return Err(unavailable("reported bundle schema marker is unsupported"));
    }
    Ok((consolidated, schema))
}

fn read_dir_entry_names(
    dir: &Path,
    prefix: &str,
) -> Result<std::collections::BTreeSet<String>, Refusal> {
    let mut names = std::collections::BTreeSet::new();
    for entry in fs::read_dir(dir).map_err(|e| unavailable(e.to_string()))? {
        let entry = entry.map_err(|e| unavailable(e.to_string()))?;
        names.insert(format!("{prefix}{}", entry.file_name().to_string_lossy()));
    }
    Ok(names)
}

fn verify_bundle_directory_entries(
    run_dir: &Path,
    receipt: &serde_json::Value,
    consolidated: bool,
) -> Result<(bool, bool), Refusal> {
    let names = read_dir_entry_names(run_dir, "")?;
    let legacy_dda = names.contains("dda_actions.jsonl");
    // Current v3 runs add the `mam/` story; earlier v3 folders have none.
    let has_mam =
        consolidated && (names.contains("mam") || !receipt["mam_schema_version"].is_null());
    let expected = expected_bundle_entries(consolidated, legacy_dda, has_mam);
    if names != expected.iter().map(|s| (*s).to_owned()).collect() {
        return Err(unavailable(
            "reported run must contain exactly its versioned canonical files",
        ));
    }
    for name in expected {
        verify_bundle_entry_metadata(run_dir, name)?;
    }
    Ok((legacy_dda, has_mam))
}

fn expected_bundle_entries(
    consolidated: bool,
    legacy_dda: bool,
    has_mam: bool,
) -> Vec<&'static str> {
    let mut expected = if consolidated {
        vec![
            "receipt.json",
            "uns.md",
            "ddc.jsonl",
            "summary.json",
            "uts.jsonl",
        ]
    } else {
        vec![
            "receipt.json",
            "novella.md",
            "ddc.jsonl",
            "summary.json",
            "uts.jsonl",
        ]
    };
    // The original reported schema was also emitted without the redundant
    // DDA copy. Keep both historical layouts, but keep v3's names exact.
    if !consolidated && legacy_dda {
        expected.push("dda_actions.jsonl");
    }
    if has_mam {
        expected.push("mam");
    }
    expected
}

fn verify_bundle_entry_metadata(run_dir: &Path, name: &str) -> Result<(), Refusal> {
    let path = run_dir.join(name);
    if name == "mam" {
        let metadata = fs::symlink_metadata(path).map_err(|e| unavailable(e.to_string()))?;
        if !metadata.is_dir() || is_redirected(&metadata) {
            return Err(unavailable("mam must be a plain directory"));
        }
        return Ok(());
    }
    ensure_regular_unredirected(&path)
}

fn verify_legacy_dda_match(
    run_dir: &Path,
    consolidated: bool,
    legacy_dda: bool,
) -> Result<(), Refusal> {
    if !consolidated && legacy_dda {
        if read_run_file(run_dir, "dda_actions.jsonl")? != read_run_file(run_dir, "ddc.jsonl")? {
            return Err(unavailable("DDC and DDA tape bytes diverge"));
        }
    }
    Ok(())
}

fn verify_bundle_digests_and_summary(
    run_dir: &Path,
    receipt: &serde_json::Value,
    schema: &str,
    consolidated: bool,
    legacy_dda: bool,
    has_mam: bool,
) -> Result<serde_json::Value, Refusal> {
    let summary_raw = read_run_file(run_dir, "summary.json")?;
    let summary: serde_json::Value =
        serde_json::from_slice(&summary_raw).map_err(|e| unavailable(e.to_string()))?;
    if summary["bundle_schema_version"] != schema {
        return Err(unavailable("reported bundle schema markers disagree"));
    }
    for (name, key) in bound_bundle_files(consolidated, legacy_dda) {
        verify_file_sha256(run_dir, receipt, name, key)?;
    }
    if has_mam {
        let ddc_raw = read_run_file(run_dir, "ddc.jsonl")?;
        verify_mam(run_dir, receipt, &summary_raw, &ddc_raw)?;
    }
    verify_legacy_dda_match(run_dir, consolidated, legacy_dda)?;
    Ok(summary)
}

fn bound_bundle_files(consolidated: bool, legacy_dda: bool) -> Vec<(&'static str, &'static str)> {
    let mut bound_files = vec![
        ("ddc.jsonl", "ddc_sha256"),
        ("summary.json", "summary_sha256"),
        ("uts.jsonl", "uts_sha256"),
    ];
    if consolidated {
        bound_files.push(("uns.md", "uns_sha256"));
    } else {
        bound_files.push(("novella.md", "novella_sha256"));
        if legacy_dda {
            bound_files.push(("dda_actions.jsonl", "dda_actions_sha256"));
        }
    }
    bound_files
}

fn verify_file_sha256(
    run_dir: &Path,
    receipt: &serde_json::Value,
    name: &str,
    key: &str,
) -> Result<Vec<u8>, Refusal> {
    use sha2::{Digest, Sha256};
    let bytes = read_run_file(run_dir, name)?;
    if receipt[key].as_str() != Some(hex::encode(Sha256::digest(&bytes)).as_str()) {
        return Err(unavailable(format!("bundle digest mismatch: {name}")));
    }
    Ok(bytes)
}

fn verify_bundle_uts_and_identity(
    run_dir: &Path,
    receipt: &serde_json::Value,
    summary: &serde_json::Value,
) -> Result<String, Refusal> {
    let uts = String::from_utf8(read_run_file(run_dir, "uts.jsonl")?)
        .map_err(|e| unavailable(e.to_string()))?;
    validate_uts(&uts, &RenderRecord::from_json(&summary.to_string())?)?;
    let id = recompute_receipt_id(run_dir)?;
    if receipt["receipt_id"] != id || summary["receipt_id"] != id {
        return Err(unavailable("reported content-addressed identity mismatch"));
    }
    Ok(id)
}

/// The story folder holds exactly its three files, each bound by the receipt
/// and equal to a fresh rendering of the bound summary and tape.
fn verify_mam(
    run_dir: &Path,
    receipt: &serde_json::Value,
    summary: &[u8],
    tape: &[u8],
) -> Result<(), Refusal> {
    if receipt["mam_schema_version"] != MAM_SCHEMA {
        return Err(unavailable(
            "mam story schema marker is missing or unsupported",
        ));
    }
    verify_bundle_entry_metadata(run_dir, "mam")?;
    let names = read_dir_entry_names(&run_dir.join("mam"), "mam/")?;
    let expected_names: std::collections::BTreeSet<String> = MAM_FILES
        .iter()
        .map(|(name, _)| (*name).to_owned())
        .collect();
    if names != expected_names {
        return Err(unavailable(
            "mam must contain exactly mam.md, mam.tex and mam.pdf",
        ));
    }
    let book = render_mam(summary, tape)?;
    for ((name, key), expected) in
        MAM_FILES
            .iter()
            .zip([book.md.as_bytes(), book.tex.as_bytes(), &book.pdf])
    {
        ensure_regular_unredirected(&run_dir.join(name))?;
        let bytes = verify_file_sha256(run_dir, receipt, name, key)?;
        if bytes != expected {
            return Err(unavailable(format!(
                "{name} does not re-render from the bound bundle"
            )));
        }
    }
    Ok(())
}

// Origin: engine/crates_rs/core_adversary/src/run_folder_store.rs
// Claim: urn:core:crates_rs:core-adversary:run-folder-store:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord6f85bf08 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord6f85bf08` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError6f85bf08 {
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
impl BoundaryError6f85bf08 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError6f85bf08 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError6f85bf08 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord6f85bf08 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError6f85bf08> {
        if capacity_bound == 0 {
            return Err(BoundaryError6f85bf08::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError6f85bf08::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError6f85bf08::ExceedsCapacity {
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
mod reported_bundle_v3_tests {
    use super::*;
    use crate::run_persistence::{
        dda_tape, persist_bout_run_folder_v2, persist_bout_run_folder_v3, PersistenceInput,
    };
    use crate::run_reporting::project_run_reports;
    use serde_json::json;

    #[test]
    fn canonical_five_files_merge_actions_into_single_ddc_tape() {
        let source = json!({"run_id":"fresh-report", "observations":[
            {"action_id":"a1", "worker":"current IDE session", "content":"actual capture"}]});
        let projected =
            project_run_reports(&source, &json!({}), "summary.json#/source_history").unwrap();
        let summary =
            RenderRecord::from_json(&json!({"source_history":source}).to_string()).unwrap();
        let receipt = RenderRecord::from_json("{}").unwrap();
        let steps = vec![RenderRecord::from_json(
            &json!({"action_id":"a1", "kind":"captured_action"}).to_string(),
        )
        .unwrap()];
        let temporary = tempfile::tempdir().unwrap();
        let folder = persist_bout_run_folder_v3(
            &PersistenceInput {
                run_key: "fresh-report",
                receipt: &receipt,
                summary_data: &summary,
                novella_md: projected["novella_md"].as_str().unwrap(),
                dda_steps: &steps,
            },
            projected["uts_jsonl"].as_str().unwrap(),
            &mut RunFolderStore::new(temporary.path().into()),
        )
        .unwrap();
        let folder = Path::new(&folder);
        let names = fs::read_dir(folder)
            .unwrap()
            .map(|entry| entry.unwrap().file_name().to_string_lossy().into_owned())
            .collect::<std::collections::BTreeSet<_>>();
        assert_eq!(
            names,
            [
                "uns.md",
                "ddc.jsonl",
                "uts.jsonl",
                "summary.json",
                "receipt.json",
                "mam"
            ]
            .into_iter()
            .map(str::to_owned)
            .collect()
        );
        assert_eq!(
            fs::read(folder.join("ddc.jsonl")).unwrap(),
            dda_tape(&steps).unwrap().bytes
        );
        assert_eq!(
            verify_reported_bundle(folder).unwrap(),
            recompute_receipt_id(folder).unwrap()
        );
        let receipt: serde_json::Value =
            serde_json::from_slice(&fs::read(folder.join("receipt.json")).unwrap()).unwrap();
        assert!(receipt.get("uns_sha256").is_some());
        assert!(receipt.get("dda_actions_sha256").is_none());
        assert!(receipt.get("novella_sha256").is_none());
        assert_eq!(receipt["mam_schema_version"], MAM_SCHEMA);
        let story = fs::read_to_string(folder.join("mam/mam.md")).unwrap();
        assert!(story.contains("> actual capture"));
        assert!(fs::read(folder.join("mam/mam.pdf"))
            .unwrap()
            .starts_with(b"%PDF-1.4"));
        fs::write(folder.join("ddc.jsonl"), b"changed\n").unwrap();
        assert!(verify_reported_bundle(folder).is_err());
    }

    fn fresh_v3(temporary: &Path) -> std::path::PathBuf {
        let source = json!({"run_id":"mam-run", "observations":[
            {"action_id":"a1", "worker":"ide", "summary":"Four, by my whiskers.",
             "metadata":{"role_id":"gauge_breaker"}}]});
        let projected =
            project_run_reports(&source, &json!({}), "summary.json#/source_history").unwrap();
        let summary =
            RenderRecord::from_json(&json!({"source_history":source}).to_string()).unwrap();
        let receipt = RenderRecord::from_json("{}").unwrap();
        let folder = persist_bout_run_folder_v3(
            &PersistenceInput {
                run_key: "mam-run",
                receipt: &receipt,
                summary_data: &summary,
                novella_md: projected["novella_md"].as_str().unwrap(),
                dda_steps: &[],
            },
            projected["uts_jsonl"].as_str().unwrap(),
            &mut RunFolderStore::new(temporary.into()),
        )
        .unwrap();
        folder.into()
    }

    #[test]
    fn mam_story_is_bound_and_rerendered_on_readback() {
        let temporary = tempfile::tempdir().unwrap();
        let folder = fresh_v3(temporary.path());
        let identity = verify_reported_bundle(&folder).unwrap();
        let story = folder.join("mam/mam.md");
        let original = fs::read(&story).unwrap();
        // A changed story fails even when the receipt digest is updated with it.
        let edited = [original.as_slice(), b"\nAn invented scene.\n"].concat();
        fs::write(&story, &edited).unwrap();
        assert!(verify_reported_bundle(&folder).is_err());
        let receipt_path = folder.join("receipt.json");
        let mut receipt: serde_json::Value =
            serde_json::from_slice(&fs::read(&receipt_path).unwrap()).unwrap();
        receipt["mam_md_sha256"] =
            json!(hex::encode(<sha2::Sha256 as sha2::Digest>::digest(&edited)));
        fs::write(&receipt_path, serde_json::to_vec_pretty(&receipt).unwrap()).unwrap();
        let failure = verify_reported_bundle(&folder).unwrap_err();
        assert!(
            failure.message.contains("does not re-render"),
            "{}",
            failure.message
        );
        fs::write(&story, &original).unwrap();
        fs::write(folder.join("mam/extra.txt"), b"x").unwrap();
        assert!(verify_reported_bundle(&folder).is_err());
        fs::remove_file(folder.join("mam/extra.txt")).unwrap();
        // A receipt that names a story requires the folder.
        fs::remove_dir_all(folder.join("mam")).unwrap();
        assert!(verify_reported_bundle(&folder).is_err());
        // An earlier v3 folder, written before the story existed, still reads back.
        let object = receipt.as_object_mut().unwrap();
        for key in [
            "mam_schema_version",
            "mam_md_sha256",
            "mam_tex_sha256",
            "mam_pdf_sha256",
        ] {
            object.remove(key);
        }
        fs::write(&receipt_path, serde_json::to_vec_pretty(&receipt).unwrap()).unwrap();
        assert_eq!(verify_reported_bundle(&folder).unwrap(), identity);
    }

    #[test]
    fn original_reported_schema_accepts_single_tape_and_checks_any_legacy_copy() {
        let history = json!({"run_id":"reported-legacy", "observations":[]});
        let projected =
            project_run_reports(&history, &json!({}), "summary.json#/source_history").unwrap();
        let summary =
            RenderRecord::from_json(&json!({"source_history":history}).to_string()).unwrap();
        let receipt = RenderRecord::from_json("{}").unwrap();
        let temporary = tempfile::tempdir().unwrap();
        let folder = persist_bout_run_folder_v2(
            &PersistenceInput {
                run_key: "reported-legacy",
                receipt: &receipt,
                summary_data: &summary,
                novella_md: projected["novella_md"].as_str().unwrap(),
                dda_steps: &[],
            },
            projected["uts_jsonl"].as_str().unwrap(),
            &mut RunFolderStore::new(temporary.path().into()),
        )
        .unwrap();
        let folder = Path::new(&folder);
        let identity = verify_reported_bundle(folder).unwrap();
        fs::remove_file(folder.join("dda_actions.jsonl")).unwrap();
        let receipt_path = folder.join("receipt.json");
        let mut receipt: serde_json::Value =
            serde_json::from_slice(&fs::read(&receipt_path).unwrap()).unwrap();
        receipt
            .as_object_mut()
            .unwrap()
            .remove("dda_actions_sha256");
        fs::write(&receipt_path, serde_json::to_vec_pretty(&receipt).unwrap()).unwrap();
        assert_eq!(fs::read_dir(folder).unwrap().count(), 5);
        assert_eq!(verify_reported_bundle(folder).unwrap(), identity);
        assert_eq!(recompute_receipt_id(folder).unwrap(), identity);

        fs::write(folder.join("dda_actions.jsonl"), b"tampered\n").unwrap();
        assert!(verify_reported_bundle(folder).is_err());
        use sha2::{Digest, Sha256};
        receipt["dda_actions_sha256"] = json!(hex::encode(Sha256::digest(b"tampered\n")));
        fs::write(&receipt_path, serde_json::to_vec_pretty(&receipt).unwrap()).unwrap();
        assert!(verify_reported_bundle(folder).is_err());
    }
}

#[cfg(test)]
mod l4_boundary_tests_6f85bf08 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord6f85bf08::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord6f85bf08::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord6f85bf08::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord6f85bf08::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord6f85bf08::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError6f85bf08::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError6f85bf08::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
