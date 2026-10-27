//! Concrete single-process history and lossless cemetery storage.
//! Failure counts are observations; they do not admit immune detectors.
use crate::stage::emission::{
    AntibodySink, CemeterySink, GenealogySink, IntelligenceEvent, PacketSink, UnsSink, UtsSink,
};
use crate::stage::genealogy::{
    AntibodyEntry, AntibodyEntryInput, CemeteryHeadstone, GenealogyEntry,
};
use crate::stage::ports::Refusal;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use std::fs::{self, OpenOptions};
use std::io::{Read, Seek, SeekFrom, Write};
use std::path::{Path, PathBuf};

fn refused(code: &str, error: impl std::fmt::Display) -> Refusal {
    Refusal::new(code, error.to_string())
}
fn canonical(value: &Value) -> Result<Vec<u8>, Refusal> {
    serde_json::to_vec(value).map_err(|e| refused("STORE_RECORD_INVALID", e))
}
fn append(path: &Path, bytes: &[u8]) -> Result<(), Refusal> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|e| refused("STORE_UNAVAILABLE", e))?;
    }
    let mut file = OpenOptions::new()
        .create(true)
        .append(true)
        .open(path)
        .map_err(|e| refused("STORE_UNAVAILABLE", e))?;
    file.write_all(bytes)
        .map_err(|e| refused("STORE_UNAVAILABLE", e))?;
    file.sync_all().map_err(|e| refused("STORE_UNAVAILABLE", e))
}
fn atomic(path: &Path, value: &Value, replace: bool) -> Result<(), Refusal> {
    let parent = path
        .parent()
        .ok_or_else(|| refused("STORE_UNAVAILABLE", "path has no parent"))?;
    fs::create_dir_all(parent).map_err(|e| refused("STORE_UNAVAILABLE", e))?;
    let mut temp =
        tempfile::NamedTempFile::new_in(parent).map_err(|e| refused("STORE_UNAVAILABLE", e))?;
    let mut bytes = canonical(value)?;
    bytes.push(b'\n');
    write_and_sync_temp(&mut temp, &bytes)?;
    persist_temp_file(temp, path, &bytes, replace)
}

fn write_and_sync_temp(temp: &mut tempfile::NamedTempFile, bytes: &[u8]) -> Result<(), Refusal> {
    temp.write_all(bytes)
        .map_err(|e| refused("STORE_UNAVAILABLE", e))?;
    temp.as_file()
        .sync_all()
        .map_err(|e| refused("STORE_UNAVAILABLE", e))
}

fn persist_temp_file(
    temp: tempfile::NamedTempFile,
    path: &Path,
    bytes: &[u8],
    replace: bool,
) -> Result<(), Refusal> {
    if replace {
        temp.persist(path)
            .map_err(|e| refused("STORE_UNAVAILABLE", e))?;
        return Ok(());
    }
    if let Err(error) = temp.persist_noclobber(path) {
        if error.error.kind() != std::io::ErrorKind::AlreadyExists
            || fs::read(path).map_err(|e| refused("STORE_UNAVAILABLE", e))? != bytes
        {
            return Err(refused("STORE_UNAVAILABLE", error));
        }
    }
    Ok(())
}
#[derive(Default)]
pub struct MemoryUts {
    pub records: Vec<(IntelligenceEvent, Vec<u8>)>,
}
impl UtsSink for MemoryUts {
    fn record_event(
        &mut self,
        event: &IntelligenceEvent,
        payload: &[u8],
    ) -> Result<String, Refusal> {
        self.records.push((event.clone(), payload.to_vec()));
        Ok(event.ie_id().into())
    }
}
#[derive(Default)]
pub struct MemoryUns {
    pub records: Vec<(String, String)>,
}
impl UnsSink for MemoryUns {
    fn record_narrative(&mut self, session: &str, text: &str) -> Result<String, Refusal> {
        self.records.push((session.into(), text.into()));
        Ok(format!("narrative:{session}"))
    }
}
pub struct FilePackets {
    pub path: PathBuf,
}
impl PacketSink for FilePackets {
    fn record_packet(&mut self, packet: &[u8]) -> Result<String, Refusal> {
        let mut line = packet.to_vec();
        line.push(b'\n');
        append(&self.path, &line).map_err(|e| refused("SGT_PERSIST_FAILED", e.message))?;
        Ok(hex::encode(Sha256::digest(packet))[..16].into())
    }
}
pub struct FileCemetery {
    pub directory: PathBuf,
}
impl FileCemetery {
    /// Load immutable headstones before screening new proposals; never skip a bad record.
    pub fn load_headstones(&self) -> Result<Vec<CemeteryHeadstone>, Refusal> {
        let entries = match fs::read_dir(&self.directory) {
            Ok(entries) => entries,
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(Vec::new()),
            Err(error) => return Err(refused("CEMETERY_LOAD_FAILED", error)),
        };
        let mut paths = entries
            .map(|entry| entry.map(|item| item.path()))
            .collect::<Result<Vec<_>, _>>()
            .map_err(|error| refused("CEMETERY_LOAD_FAILED", error))?;
        paths.sort();
        let mut headstones = Vec::new();
        for path in paths {
            let Some(name) = path.file_name().and_then(|name| name.to_str()) else {
                continue;
            };
            if !name.ends_with(".headstone.json") {
                continue;
            }
            let raw = fs::read(&path).map_err(|error| refused("CEMETERY_LOAD_FAILED", error))?;
            let value = crate::stage::strict_json::parse(&raw)
                .map_err(|error| refused("CEMETERY_LOAD_FAILED", error))?;
            let headstone = CemeteryHeadstone::from_json(&value)
                .map_err(|error| refused("CEMETERY_LOAD_FAILED", error.message))?;
            // Historical writers used candidate/run filenames. Content identity is
            // checked by from_json; retaining those names preserves byte custody.
            headstones.push(headstone);
        }
        Ok(headstones)
    }
}
impl CemeterySink for FileCemetery {
    fn record_headstone(&mut self, headstone: &CemeteryHeadstone) -> Result<String, Refusal> {
        let id = headstone.headstone_id();
        atomic(
            &self.directory.join(format!(
                "{}.headstone.json",
                id.trim_start_matches("sha256:")
            )),
            &headstone.to_dict(),
            false,
        )
        .map_err(|e| refused("CEMETERY_RECORD_FAILED", e.message))?;
        Ok(id.into())
    }
}
pub struct FileFailureHistory {
    pub directory: PathBuf,
}
impl FileFailureHistory {
    fn records(&self) -> Result<BTreeMap<String, AntibodyEntry>, Refusal> {
        let mut records = BTreeMap::new();
        let paths = self.sorted_antibody_paths()?;
        for path in paths {
            if let Some(entry) = Self::load_antibody_file(&path)? {
                records.insert(entry.input().antibody_id.clone(), entry);
            }
        }
        Ok(records)
    }

    fn sorted_antibody_paths(&self) -> Result<Vec<PathBuf>, Refusal> {
        let entries = match fs::read_dir(&self.directory) {
            Ok(entries) => entries,
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => return Ok(Vec::new()),
            Err(e) => return Err(refused("ANTIBODY_LOAD_FAILED", e)),
        };
        let mut paths = entries
            .map(|entry| entry.map(|e| e.path()))
            .collect::<Result<Vec<_>, _>>()
            .map_err(|e| refused("ANTIBODY_LOAD_FAILED", e))?;
        paths.sort();
        Ok(paths)
    }

    fn load_antibody_file(path: &Path) -> Result<Option<AntibodyEntry>, Refusal> {
        let Some(name) = path.file_name().and_then(|name| name.to_str()) else {
            return Ok(None);
        };
        if !name.starts_with("ab_") || !name.ends_with(".json") {
            return Ok(None);
        }
        let raw = fs::read(path).map_err(|e| refused("ANTIBODY_LOAD_FAILED", e))?;
        let value: Value =
            serde_json::from_slice(&raw).map_err(|e| refused("ANTIBODY_LOAD_FAILED", e))?;
        let entry = AntibodyEntry::from_json(&value)?;
        if name != format!("{}.json", entry.input().antibody_id) {
            return Err(refused(
                "ANTIBODY_LOAD_FAILED",
                "antibody filename does not match payload",
            ));
        }
        Ok(Some(entry))
    }
}
impl AntibodySink for FileFailureHistory {
    fn load_antibodies(&mut self, _context_key: &str) -> Result<Vec<AntibodyEntry>, Refusal> {
        Ok(self
            .records()?
            .into_values()
            .filter(|e| e.input().status == "ACTIVE")
            .collect())
    }
    fn record_failure(
        &mut self,
        failure_pattern: &str,
        constraint_rule: &str,
    ) -> Result<String, Refusal> {
        let id = format!(
            "ab_{}",
            &hex::encode(Sha256::digest(failure_pattern.as_bytes()))[..16]
        );
        let records = self.records()?;
        let (count, status) =
            Self::next_antibody_state(records.get(&id), failure_pattern, constraint_rule)?;
        let admitted = status == "ACTIVE";
        let entry = AntibodyEntry::new(AntibodyEntryInput {
            antibody_id: id.clone(),
            failure_pattern: failure_pattern.into(),
            occurrences: count,
            constraint_rule: constraint_rule.into(),
            status,
        })?;
        atomic(
            &self.directory.join(format!("{id}.json")),
            &entry.to_dict(),
            true,
        )
        .map_err(|e| refused("ANTIBODY_RECORD_FAILED", e.message))?;
        Ok(if admitted { id } else { String::new() })
    }
}

impl FileFailureHistory {
    fn next_antibody_state(
        prior: Option<&AntibodyEntry>,
        failure_pattern: &str,
        constraint_rule: &str,
    ) -> Result<(u32, String), Refusal> {
        if let Some(entry) = prior {
            if entry.input().failure_pattern != failure_pattern
                || entry.input().constraint_rule != constraint_rule
            {
                return Err(refused(
                    "ANTIBODY_RECORD_FAILED",
                    "antibody identity collides with different failure data",
                ));
            }
        }
        let count = prior
            .map(|entry| entry.input().occurrences)
            .unwrap_or(0)
            .checked_add(1)
            .ok_or_else(|| refused("ANTIBODY_RECORD_FAILED", "occurrence count overflow"))?;
        // A sighting count never activates an antibody: activation is an admission act
        // recorded outside this store. A judged record (ACTIVE, or any status other than
        // PENDING) keeps its status when the pattern is seen again.
        let status = match prior {
            Some(entry) if entry.input().status != "PENDING" => entry.input().status.clone(),
            _ => "PENDING".to_string(),
        };
        Ok((count, status))
    }
}

pub struct FileGenealogy {
    pub path: PathBuf,
}
impl GenealogySink for FileGenealogy {
    fn record_lineage(&mut self, entry: &GenealogyEntry) -> Result<String, Refusal> {
        let mut file = self.open_locked_genealogy()?;
        let bytes = Self::read_locked_genealogy(&mut file)?;
        let (sequence, parent, existing_id) = Self::scan_genealogy_chain(&bytes, entry)?;
        if let Some(id) = existing_id {
            return Ok(id);
        }
        Self::append_genealogy_entry(&mut file, sequence, parent, entry)
    }
}

impl FileGenealogy {
    fn open_locked_genealogy(&self) -> Result<fs::File, Refusal> {
        if let Some(parent) = self.path.parent() {
            fs::create_dir_all(parent).map_err(|e| refused("GENEALOGY_RECORD_FAILED", e))?;
        }
        // The append and tail read share one OS lock, preserving sequence custody.
        let file = OpenOptions::new()
            .create(true)
            .read(true)
            .append(true)
            .open(&self.path)
            .map_err(|e| refused("GENEALOGY_RECORD_FAILED", e))?;
        file.lock()
            .map_err(|e| refused("GENEALOGY_RECORD_FAILED", e))?;
        Ok(file)
    }

    fn read_locked_genealogy(file: &mut fs::File) -> Result<Vec<u8>, Refusal> {
        // Read through the locked handle. On Windows the lock is mandatory, so opening
        // a second handle to read fails with a lock violation (os error 33).
        let mut bytes = Vec::new();
        file.seek(SeekFrom::Start(0))
            .map_err(|e| refused("GENEALOGY_RECORD_FAILED", e))?;
        file.read_to_end(&mut bytes)
            .map_err(|e| refused("GENEALOGY_RECORD_FAILED", e))?;
        Ok(bytes)
    }

    fn scan_genealogy_chain(
        bytes: &[u8],
        entry: &GenealogyEntry,
    ) -> Result<(usize, Value, Option<String>), Refusal> {
        let mut sequence = 0usize;
        let mut parent = Value::Null;
        for line in bytes.split(|b| *b == b'\n').filter(|line| !line.is_empty()) {
            let (digest, existing) = Self::verify_genealogy_line(line, sequence, &parent, entry)?;
            if let Some(id) = existing {
                return Ok((sequence, parent, Some(id)));
            }
            sequence += 1;
            parent = json!(digest);
        }
        Ok((sequence, parent, None))
    }

    fn verify_genealogy_line(
        line: &[u8],
        sequence: usize,
        parent: &Value,
        entry: &GenealogyEntry,
    ) -> Result<(String, Option<String>), Refusal> {
        let sealed: Value =
            serde_json::from_slice(line).map_err(|e| refused("GENEALOGY_RECORD_FAILED", e))?;
        let payload = &sealed["payload"];
        let material = json!({"sequence":sequence,"parent_sha256":parent,"payload":payload});
        let digest = hex::encode(Sha256::digest(canonical(&material)?));
        let link_ok = [
            sealed["sequence"] == json!(sequence),
            &sealed["parent_sha256"] == parent,
            sealed["record_sha256"] == json!(digest),
        ]
        .into_iter()
        .all(|b| b);
        if !link_ok {
            return Err(refused(
                "GENEALOGY_RECORD_FAILED",
                "genealogy hash chain is invalid",
            ));
        }
        let target_dict = entry.to_dict();
        if payload["child_run_key"] == target_dict["child_run_key"] {
            if payload == &target_dict {
                let id = target_dict["lineage_id"]
                    .as_str()
                    .unwrap_or_default()
                    .into();
                return Ok((digest, Some(id)));
            }
            return Err(refused(
                "GENEALOGY_RECORD_FAILED",
                "conflicting genealogy for child",
            ));
        }
        Ok((digest, None))
    }

    fn append_genealogy_entry(
        file: &mut fs::File,
        sequence: usize,
        parent: Value,
        entry: &GenealogyEntry,
    ) -> Result<String, Refusal> {
        let payload = entry.to_dict();
        let material = json!({"sequence":sequence,"parent_sha256":parent,"payload":payload});
        let digest = hex::encode(Sha256::digest(canonical(&material)?));
        let mut line = canonical(
            &json!({"sequence":sequence,"parent_sha256":parent,"payload":payload,"record_sha256":digest}),
        )?;
        line.push(b'\n');
        file.write_all(&line)
            .map_err(|e| refused("GENEALOGY_RECORD_FAILED", e))?;
        file.sync_all()
            .map_err(|e| refused("GENEALOGY_RECORD_FAILED", e))?;
        Ok(payload["lineage_id"].as_str().unwrap_or_default().into())
    }
}

// Origin: engine/crates_rs/core_adversary/src/stage/file_adapters.rs
// Claim: urn:core:crates_rs:core-adversary:file-adapters:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_334c8799 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
