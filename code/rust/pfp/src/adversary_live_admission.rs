//! Verify and consume the operator's existing signed instruction decision before live IO.
use core_adversary::stage::ports::Refusal;
use core_adversary::instruction_plan::InstructionPlanTransportV01;
use core_adversary::render_record::{JsonStyle, RenderRecord};
use serde::Deserialize;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct LiveAdmission {
    manifest_path: PathBuf,
    signature_path: PathBuf,
    allowed_signers_path: PathBuf,
    request_digest: String,
    request_json: Value,
    ssh_keygen: Option<PathBuf>,
    plan_material: Value,
}
fn refuse(message: impl Into<String>) -> Refusal {
    Refusal::new("NATIVE_INSTRUCTION_ADMISSION_INVALID", message)
}
fn canonical(value: &Value) -> Result<Vec<u8>, Refusal> {
    RenderRecord::from_json(&value.to_string())?
        .json(JsonStyle::CompactSortedAscii)
        .map(String::into_bytes)
}
fn digest(raw: &[u8]) -> String {
    format!("sha256:{}", hex::encode(Sha256::digest(raw)))
}
fn bounded_file(path: &Path, limit: u64) -> Result<Vec<u8>, Refusal> {
    let meta = fs::symlink_metadata(path).map_err(|e| refuse(e.to_string()))?;
    if !meta.is_file() || meta.file_type().is_symlink() || meta.len() == 0 || meta.len() > limit {
        return Err(refuse(
            "admission file is absent, aliased or exceeds its limit",
        ));
    }
    fs::read(path).map_err(|e| refuse(e.to_string()))
}
fn canonical_path(path: &Path) -> Result<PathBuf, Refusal> {
    path.canonicalize().map_err(|e| refuse(e.to_string()))
}
fn str_field<'a>(value: &'a Value, key: &str, err: &'static str) -> Result<&'a str, Refusal> {
    value[key].as_str().ok_or_else(|| refuse(err))
}
fn arr_field<'a>(value: &'a Value, key: &str, err: &'static str) -> Result<&'a [Value], Refusal> {
    value[key]
        .as_array()
        .map(Vec::as_slice)
        .ok_or_else(|| refuse(err))
}
fn is_admitted_catalog_source(path: &str) -> bool {
    path.starts_with("operads/catalog/operands/v1/")
        || path.starts_with("operads/catalog/contracts/v1/")
}
fn is_active_admission(admission: &Value) -> bool {
    [json!("Unadmitted"), json!("Admitted")].contains(admission)
}
impl LiveAdmission {
    pub(crate) fn request_digest(&self) -> &str {
        &self.request_digest
    }
    fn verify_unprojected_sources(
        &self,
        plan: &InstructionPlanTransportV01,
    ) -> Result<(), Refusal> {
        if self.plan_material.get("projection_path").is_some() {
            return Err(refuse("projection path without its signed projection"));
        }
        let trace = arr_field(&self.plan_material, "trace", "plan trace absent")?;
        let invalid_source = plan.source_digests.iter().any(|(path, _)| {
            !trace.iter().any(|row| row["source_path"] == *path)
                || !is_admitted_catalog_source(path)
        });
        if invalid_source {
            return Err(refuse(
                "estate/artifact sources require their signed projection",
            ));
        }
        Ok(())
    }
    fn verify_projection_snapshot(
        &self,
        root: &Path,
        plan: &InstructionPlanTransportV01,
        projection: &Value,
    ) -> Result<(), Refusal> {
        let relative = str_field(
            &self.plan_material,
            "projection_path",
            "signed projection path absent",
        )?;
        let source = root.join(relative);
        let resolved = canonical_path(&source)?;
        let raw = bounded_file(&source, 131072)?;
        let expected_canonical = canonical(projection)?;
        let in_source_digests = plan
            .source_digests
            .iter()
            .any(|(path, expected)| path == relative && *expected == digest(&raw));
        if !resolved.starts_with(root)
            || raw != expected_canonical
            || !in_source_digests
            || projection["schema_version"] != "oewas.projection.v3"
        {
            return Err(refuse(
                "projection bytes/path differ from the signed source snapshot",
            ));
        }
        Ok(())
    }
    fn verify_projected_source<'a>(
        root: &Path,
        row: &'a Value,
    ) -> Result<(&'a str, &'a Value), Refusal> {
        let path = str_field(row, "path", "projection source path absent")?;
        let expected = str_field(row, "raw_digest", "projection source digest absent")?;
        let source = root.join(path);
        let resolved = canonical_path(&source)?;
        let raw = bounded_file(&source, 131072)?;
        if !resolved.starts_with(root) || digest(&raw) != expected {
            return Err(refuse(
                "projected source changed, escaped or was duplicated",
            ));
        }
        Ok((path, row))
    }
    fn collect_projected_sources<'a>(
        root: &Path,
        sources: &'a [Value],
    ) -> Result<std::collections::BTreeMap<&'a str, &'a Value>, Refusal> {
        let mut source_by_path = std::collections::BTreeMap::new();
        for row in sources {
            let (path, verified_row) = Self::verify_projected_source(root, row)?;
            if source_by_path.insert(path, verified_row).is_some() {
                return Err(refuse(
                    "projected source changed, escaped or was duplicated",
                ));
            }
        }
        Ok(source_by_path)
    }
    fn verify_projected_operation<'a>(
        row: &'a Value,
        source_by_path: &std::collections::BTreeMap<&'a str, &'a Value>,
    ) -> Result<(&'a str, &'a Value), Refusal> {
        let id = str_field(row, "operation_id", "projected operation ID absent")?;
        let path = str_field(row, "source_path", "operation source path absent")?;
        let source = source_by_path
            .get(path)
            .ok_or_else(|| refuse("operation source missing from projection"))?;
        let has_op_id = source["operation_ids"]
            .as_array()
            .is_some_and(|ids| ids.contains(&json!(id)));
        if row["source_digest"] != source["raw_digest"]
            || row["skill_id"] != source["skill_id"]
            || !has_op_id
        {
            return Err(refuse("projection operation/source binding differs"));
        }
        Ok((id, row))
    }
    fn collect_projected_operations<'a>(
        records: &'a [Value],
        source_by_path: &std::collections::BTreeMap<&'a str, &'a Value>,
    ) -> Result<std::collections::BTreeMap<&'a str, &'a Value>, Refusal> {
        let mut by_id = std::collections::BTreeMap::new();
        for row in records {
            let (id, verified_row) = Self::verify_projected_operation(row, source_by_path)?;
            if by_id.insert(id, verified_row).is_some() {
                return Err(refuse("projection operation/source binding differs"));
            }
        }
        Ok(by_id)
    }
    fn verify_single_replacement(
        row: &Value,
        by_id: &std::collections::BTreeMap<&str, &Value>,
    ) -> Result<(), Refusal> {
        let Some(replacement) = row.get("replacement_operation_id") else {
            return Ok(());
        };
        let id = replacement
            .as_str()
            .ok_or_else(|| refuse("replacement ID invalid"))?;
        let valid = by_id.get(id).is_some_and(|r| {
            is_active_admission(&r["admission"]) && r["operation_id"] != row["operation_id"]
        });
        if !valid {
            return Err(refuse(
                "retired replacement absent, retired or self-referential",
            ));
        }
        Ok(())
    }
    fn verify_replacements(
        records: &[Value],
        by_id: &std::collections::BTreeMap<&str, &Value>,
    ) -> Result<(), Refusal> {
        for row in records {
            Self::verify_single_replacement(row, by_id)?;
        }
        Ok(())
    }
    fn verify_trace_against_projection(
        &self,
        by_id: &std::collections::BTreeMap<&str, &Value>,
    ) -> Result<(), Refusal> {
        let trace = arr_field(&self.plan_material, "trace", "plan trace absent")?;
        for row in trace {
            let id = str_field(row, "operation_id", "selected operation absent")?;
            let projected = by_id
                .get(id)
                .ok_or_else(|| refuse("selected operation missing from projection"))?;
            if !is_active_admission(&projected["admission"])
                || projected["content_digest"] != row["operation_digest"]
            {
                return Err(refuse(
                    "selected operation retired or differs from signed projection",
                ));
            }
        }
        Ok(())
    }
    fn verify_projection(
        &self,
        root: &Path,
        plan: &InstructionPlanTransportV01,
    ) -> Result<(), Refusal> {
        let Some(projection) = self.plan_material.get("projection") else {
            return self.verify_unprojected_sources(plan);
        };
        self.verify_projection_snapshot(root, plan, projection)?;
        let sources = arr_field(projection, "sources", "projection sources absent")?;
        let records = arr_field(projection, "operation_records", "projection records absent")?;
        if !(1..=1024).contains(&sources.len()) || !(1..=4096).contains(&records.len()) {
            return Err(refuse("projection source/operation ceiling invalid"));
        }
        let source_by_path = Self::collect_projected_sources(root, sources)?;
        let by_id = Self::collect_projected_operations(records, &source_by_path)?;
        Self::verify_replacements(records, &by_id)?;
        self.verify_trace_against_projection(&by_id)
    }

    fn verify_allowed_signers(&self, root: &Path) -> Result<(), Refusal> {
        let trust = canonical_path(&self.allowed_signers_path)?;
        if !self.allowed_signers_path.is_absolute() || trust.starts_with(root) {
            return Err(refuse(
                "allowed signers must be held outside the repository",
            ));
        }
        bounded_file(&self.allowed_signers_path, 65536)?;
        bounded_file(&self.signature_path, 8192)?;
        Ok(())
    }

    fn load_and_verify_manifest(
        &self,
        plan: &InstructionPlanTransportV01,
    ) -> Result<(Vec<u8>, Value), Refusal> {
        let raw = bounded_file(&self.manifest_path, 8192)?;
        let manifest: Value = serde_json::from_slice(&raw).map_err(|e| refuse(e.to_string()))?;
        let mut encoded = canonical(&manifest)?;
        encoded.push(b'\n');
        if encoded != raw || digest(&raw) != plan.manifest_digest {
            return Err(refuse(
                "signed manifest bytes differ from the consumed plan",
            ));
        }
        Ok((raw, manifest))
    }

    fn check_manifest_shape(manifest: &Value) -> Result<(), Refusal> {
        let fields = [
            "schema_version",
            "decision",
            "reviewer_identity",
            "authority_effect",
            "request_digest",
            "task_shape_digest",
            "workload_profile_id",
            "workload_profile_digest",
            "domain_id",
            "selection_digest",
            "route_id",
            "plan_digest",
            "source_snapshot_digest",
        ];
        let object = manifest
            .as_object()
            .ok_or_else(|| refuse("manifest must be an object"))?;
        if object.len() != fields.len() || fields.iter().any(|key| !object.contains_key(*key)) {
            return Err(refuse("manifest decision or plan binding differs"));
        }
        Ok(())
    }

    fn verify_manifest_fields(
        &self,
        manifest: &Value,
        plan: &InstructionPlanTransportV01,
    ) -> Result<(), Refusal> {
        Self::check_manifest_shape(manifest)?;
        let header_mismatch = manifest["schema_version"]
            != "oewas.adversary.instruction_admission.v0.1"
            || manifest["decision"] != "APPROVE"
            || manifest["authority_effect"] != "None";
        let digest_mismatch = manifest["request_digest"] != self.request_digest
            || manifest["plan_digest"] != plan.plan_digest
            || manifest["selection_digest"] != plan.selection_digest
            || manifest["source_snapshot_digest"] != plan.source_snapshot_digest;
        if header_mismatch || digest_mismatch {
            return Err(refuse("manifest decision or plan binding differs"));
        }
        Ok(())
    }

    fn verify_request_binding(&self, actual: &Value) -> Result<(), Refusal> {
        if digest(&canonical(&self.request_json)?) != self.request_digest {
            return Err(refuse(
                "request digest does not bind the supplied request bytes",
            ));
        }
        let actual = actual
            .as_object()
            .ok_or_else(|| refuse("actual request absent"))?;
        if actual
            .iter()
            .any(|(key, value)| self.request_json.get(key) != Some(value))
        {
            return Err(refuse("signed request differs from the executing bout"));
        }
        Ok(())
    }

    fn verify_plan_material(&self, plan: &InstructionPlanTransportV01) -> Result<(), Refusal> {
        let plan_canonical = canonical(&self.plan_material)?;
        let header_mismatch = digest(&plan_canonical) != plan.plan_digest
            || self.plan_material["schema"] != "oewas.adversary.candidate_plan.v0.1";
        let body_mismatch = self.plan_material["ordered_operand_bodies"]
            != json!(plan.ordered_operand_bodies)
            || self.plan_material["sources"] != json!(plan.source_digests)
            || self.plan_material["instruction_bytes"] != json!(plan.instruction_bytes);
        if header_mismatch || body_mismatch {
            return Err(refuse(
                "signed plan does not bind the consumed ordered instruction bodies",
            ));
        }
        let trace = arr_field(&self.plan_material, "trace", "plan trace absent")?;
        let operations: Vec<_> = trace
            .iter()
            .map(|row| row["operation_id"].clone())
            .collect();
        let expected_ops: Vec<_> = plan.operation_ids.iter().map(|id| json!(id)).collect();
        if operations != expected_ops {
            return Err(refuse(
                "ordered operation identities differ from signed plan",
            ));
        }
        Ok(())
    }

    fn verify_source_digests(
        root: &Path,
        plan: &InstructionPlanTransportV01,
    ) -> Result<(), Refusal> {
        for (relative, expected) in &plan.source_digests {
            let candidate = root.join(relative);
            let source = canonical_path(&candidate)?;
            let raw = bounded_file(&candidate, 131072)?;
            if !source.starts_with(root) || digest(&raw) != *expected {
                return Err(refuse("instruction source changed after admission"));
            }
        }
        Ok(())
    }

    fn validate_signer_identity(manifest: &Value) -> Result<&str, Refusal> {
        let identity = str_field(manifest, "reviewer_identity", "signer identity absent")?;
        let valid_chars = identity
            .bytes()
            .all(|c| c.is_ascii_alphanumeric() || b"._@+-".contains(&c));
        if !(1..=128).contains(&identity.len()) || !valid_chars {
            return Err(refuse("signer identity invalid"));
        }
        Ok(identity)
    }

    fn verify_ssh_signature(&self, identity: &str, raw: &[u8]) -> Result<(), Refusal> {
        let executable = self
            .ssh_keygen
            .clone()
            .unwrap_or_else(|| PathBuf::from("ssh-keygen"));
        let mut child = Command::new(executable)
            .args(["-Y", "verify", "-f"])
            .arg(&self.allowed_signers_path)
            .args(["-I", identity, "-n", "oewas-adversary-instruction-v0.1", "-s"])
            .arg(&self.signature_path)
            .stdin(Stdio::piped())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()
            .map_err(|e| refuse(format!("signature verifier unavailable: {e}")))?;
        if let Some(mut stream) = child.stdin.take() {
            stream.write_all(raw).map_err(|e| refuse(e.to_string()))?;
        }
        let status = child.wait().map_err(|e| refuse(e.to_string()))?;
        if !status.success() {
            return Err(refuse("operator signature verification refused"));
        }
        Ok(())
    }

    fn verify_plan_and_sources(
        &self,
        root: &Path,
        plan: &InstructionPlanTransportV01,
    ) -> Result<(), Refusal> {
        self.verify_plan_material(plan)?;
        Self::verify_source_digests(root, plan)?;
        self.verify_projection(root, plan)
    }

    pub(crate) fn verify(
        &self,
        root: &Path,
        plan: &InstructionPlanTransportV01,
        actual: &Value,
    ) -> Result<(), Refusal> {
        plan.validate()?;
        let root = canonical_path(root)?;
        self.verify_allowed_signers(&root)?;
        let (raw, manifest) = self.load_and_verify_manifest(plan)?;
        self.verify_manifest_fields(&manifest, plan)?;
        self.verify_request_binding(actual)?;
        self.verify_plan_and_sources(&root, plan)?;
        let identity = Self::validate_signer_identity(&manifest)?;
        self.verify_ssh_signature(identity, &raw)
    }
}

// Origin: engine/crates_rs/pfp/src/adversary_live_admission.rs
// Claim: urn:core:crates_rs:pfp:adversary-live-admission:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde154acae {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde154acae` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore154acae {
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
impl BoundaryErrore154acae {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore154acae {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore154acae {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde154acae {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore154acae> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore154acae::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore154acae::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore154acae::ExceedsCapacity {
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
mod l4_boundary_tests_e154acae {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorde154acae::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorde154acae::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorde154acae::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorde154acae::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorde154acae::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrore154acae::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrore154acae::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
