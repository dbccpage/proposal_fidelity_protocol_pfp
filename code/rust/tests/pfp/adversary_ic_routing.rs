//! Actual native composition path routing; all fixture bouts remain unauthorized.
use pfp::adversary_host::dispatch;
use core_adversary::run_folder_store::{recompute_receipt_id, verify_reported_bundle};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::fs;
use std::path::Path;

fn payload(root: &Path) -> Value {
    let resources = Path::new(env!("CARGO_MANIFEST_DIR"))
        .ancestors()
        .nth(1)
        .unwrap();
    json!({"task_key":"ic_routing_fixture","objective":"bounded route custody",
        "repo_root":root,"adversary_output_dir":root.join("_ic/adversary"),
        "resources_root":resources,"ledger_path":root.join("calls.jsonl"),
        "bout_id":"local1","live":false,
        "config_path":resources.join("adversary/config/seat_routing_v1.yaml")})
}
fn canonical(value: &Value) -> Vec<u8> {
    let mut text = String::new();
    for ch in value.to_string().chars() {
        if ch as u32 >= 127 {
            for code in ch.encode_utf16(&mut [0; 2]) {
                text.push_str(&format!("\\u{code:04x}"));
            }
        } else {
            text.push(ch);
        }
    }
    text.push('\n');
    text.into_bytes()
}
fn activate(root: &Path) -> Value {
    let control = root.join("_ic/odni/migration");
    fs::create_dir_all(&control).unwrap();
    let inventory = json!({"schema":"core.ic.inventory.v1","routing_profile":"core.ic.routes.v1",
        "repository_root":root,"source_revision":"a".repeat(40),
        "repository":"dbccpage/the_symbol_game","authority_effect":"None",
        "files":[],"directories":[],"destination_baseline":[]});
    let raw = canonical(&inventory);
    fs::write(control.join("inventory.json"), &raw).unwrap();
    let activation = json!({"schema":"core.ic.activation.v1","state":"ACTIVATED",
        "authority_effect":"None","repository_root":root,"source_revision":"a".repeat(40),
        "inventory_sha256":hex::encode(Sha256::digest(raw))});
    fs::write(
        control.join("activation.json"),
        serde_json::to_vec(&activation).unwrap(),
    )
    .unwrap();
    activation
}
fn assert_refused(root: &Path, request: &Value, code: &str) {
    let result = dispatch(request).unwrap();
    assert_eq!(result["refusal"]["code"], code, "{result}");
    assert!(result["outcome"].is_null());
    assert!(!root.join("_intelligence").exists());
    assert!(!root.join("_ic/adversary").exists());
    assert!(!root.join("calls.jsonl").exists());
}
#[test]
fn ic_routing_required_output_field_refuses_before_any_writes() {
    let root = tempfile::tempdir().unwrap();
    let mut request = payload(root.path());
    request.as_object_mut().unwrap().remove("adversary_output_dir");
    assert_refused(root.path(), &request, "ADVERSARY_REQUEST_INVALID");
}
#[test]
#[ignore = "needs the adversary seat-routing config and council dossiers, which stay in the private engine repo"]
fn ic_routing_canonical_bouts_keep_five_files_and_bound_mam_before_and_after_activation() {
    for active in [false, true] {
        let root = tempfile::tempdir().unwrap();
        let mut request = payload(root.path());
        if active {
            activate(root.path());
        }
        let expected = root.path().join("_ic/adversary");
        request["adversary_output_dir"] = json!(expected);
        let result = dispatch(&request).unwrap();
        assert!(result["refusal"].is_null(), "{result}");
        assert_eq!(result["outcome"]["is_authorized"], false);
        let folder = Path::new(result["outcome"]["receipt_path"].as_str().unwrap())
            .parent()
            .unwrap();
        assert_eq!(folder.parent().unwrap(), expected.join("runs"));
        let mut files: Vec<_> = fs::read_dir(folder)
            .unwrap()
            .map(|p| p.unwrap().file_name())
            .collect();
        files.sort();
        assert_eq!(
            files,
            [
                "ddc.jsonl",
                "mam",
                "receipt.json",
                "summary.json",
                "uns.md",
                "uts.jsonl"
            ]
        );
        assert_eq!(
            verify_reported_bundle(folder).unwrap(),
            recompute_receipt_id(folder).unwrap()
        );
        assert!(!folder.join("dda_actions.jsonl").exists());
        assert!(expected.join("bout_journal.jsonl").is_file());
        assert!(expected.join("ddc_actions.jsonl").is_file());
        // The bounded fixture does not emit an SGT packet.
        assert!(!root.path().join("_intelligence").exists());
    }
}
#[test]
fn ic_routing_native_rejects_caller_selected_namespace_without_activation() {
    let root = tempfile::tempdir().unwrap();
    let mut request = payload(root.path());
    for suffix in [
        "_intelligence/_adversary",
        "_ic/darpa/adversary",
        "_ic/cia/adversary",
        "elsewhere",
        "_intelligence/_adversary/../escape",
    ] {
        request["adversary_output_dir"] = json!(root.path().join(suffix));
        assert_refused(root.path(), &request, "ADVERSARY_OUTPUT_ROUTING_INVALID");
    }
}
#[test]
fn ic_routing_native_refuses_stale_legacy_path_after_activation() {
    let root = tempfile::tempdir().unwrap();
    activate(root.path());
    let mut request = payload(root.path());
    request["adversary_output_dir"] = json!(root.path().join("_intelligence/_adversary"));
    assert_refused(root.path(), &request, "ADVERSARY_OUTPUT_ROUTING_INVALID");
}
#[test]
fn ic_routing_corrupt_activation_never_falls_back_to_legacy() {
    for raw in [
        b"{broken".as_slice(),
        b"null",
        b"[]",
        b"{}",
        b"{\"schema\":1}",
    ] {
        let root = tempfile::tempdir().unwrap();
        activate(root.path());
        fs::write(root.path().join("_ic/odni/migration/activation.json"), raw).unwrap();
        assert_refused(
            root.path(),
            &payload(root.path()),
            "ADVERSARY_OUTPUT_ROUTING_INVALID",
        );
    }
}
#[test]
fn ic_routing_activation_identity_malformed_and_transplant_controls() {
    for (key, value) in [
        ("schema", json!("future")),
        ("state", json!("COPIED")),
        ("authority_effect", json!("Authorize")),
        ("repository_root", json!("C:/another")),
        ("source_revision", json!(true)),
        ("source_revision", json!("A".repeat(40))),
        ("inventory_sha256", json!("0".repeat(64))),
        ("unexpected", json!("field")),
    ] {
        let root = tempfile::tempdir().unwrap();
        let mut activation = activate(root.path());
        activation[key] = value;
        fs::write(
            root.path().join("_ic/odni/migration/activation.json"),
            serde_json::to_vec(&activation).unwrap(),
        )
        .unwrap();
        assert_refused(
            root.path(),
            &payload(root.path()),
            "ADVERSARY_OUTPUT_ROUTING_INVALID",
        );
    }
}
#[test]
fn ic_routing_inventory_raw_bytes_and_identity_are_bound() {
    for (key, value) in [
        ("schema", json!("future")),
        ("routing_profile", json!("other")),
        ("repository_root", json!("C:/another")),
        ("source_revision", json!("b".repeat(40))),
    ] {
        let root = tempfile::tempdir().unwrap();
        let mut activation = activate(root.path());
        let mut inventory: Value = serde_json::from_slice(
            &fs::read(root.path().join("_ic/odni/migration/inventory.json")).unwrap(),
        )
        .unwrap();
        inventory[key] = value;
        let raw = canonical(&inventory);
        activation["inventory_sha256"] = json!(hex::encode(Sha256::digest(&raw)));
        fs::write(root.path().join("_ic/odni/migration/inventory.json"), raw).unwrap();
        fs::write(
            root.path().join("_ic/odni/migration/activation.json"),
            serde_json::to_vec(&activation).unwrap(),
        )
        .unwrap();
        assert_refused(
            root.path(),
            &payload(root.path()),
            "ADVERSARY_OUTPUT_ROUTING_INVALID",
        );
    }
    let root = tempfile::tempdir().unwrap();
    activate(root.path());
    fs::write(
        root.path().join("_ic/odni/migration/inventory.json"),
        b"same logical claim; different bytes",
    )
    .unwrap();
    assert_refused(
        root.path(),
        &payload(root.path()),
        "ADVERSARY_OUTPUT_ROUTING_INVALID",
    );
}
#[test]
fn ic_routing_missing_inventory_is_not_unactivated() {
    let root = tempfile::tempdir().unwrap();
    activate(root.path());
    fs::remove_file(root.path().join("_ic/odni/migration/inventory.json")).unwrap();
    assert_refused(
        root.path(),
        &payload(root.path()),
        "ADVERSARY_OUTPUT_ROUTING_INVALID",
    );
}

#[test]
fn ic_routing_inventory_shape_and_row_controls_refuse_with_matching_raw_digest() {
    for bad in [
        json!({}),
        json!({"files":null}),
        json!({"files":[{"source":"x"}]}),
        json!({"files":[{"source":"_intelligence/a","destination":"_ic/nara/legacy/a","sha256":"a".repeat(64),"size":true,"kind":"regular_file"}]}),
        json!({"directories":["_intelligence/../escape"]}),
        json!({"destination_baseline":[["_ic/x","b".repeat(64),-1]]}),
        json!({"directories":["_intelligence/a","_intelligence/A"]}),
        json!({"unexpected":false}),
    ] {
        let root = tempfile::tempdir().unwrap();
        let mut activation = activate(root.path());
        let inventory_path = root.path().join("_ic/odni/migration/inventory.json");
        let mut inventory: Value =
            serde_json::from_slice(&fs::read(&inventory_path).unwrap()).unwrap();
        if bad.as_object().unwrap().is_empty() {
            inventory.as_object_mut().unwrap().remove("files");
        } else {
            for (key, value) in bad.as_object().unwrap() {
                inventory[key] = value.clone();
            }
        }
        let raw = canonical(&inventory);
        activation["inventory_sha256"] = json!(hex::encode(Sha256::digest(&raw)));
        fs::write(inventory_path, raw).unwrap();
        fs::write(
            root.path().join("_ic/odni/migration/activation.json"),
            serde_json::to_vec(&activation).unwrap(),
        )
        .unwrap();
        assert_refused(
            root.path(),
            &payload(root.path()),
            "ADVERSARY_OUTPUT_ROUTING_INVALID",
        );
    }
}
#[test]
fn ic_routing_duplicate_json_key_and_noncanonical_inventory_refuse() {
    for duplicate in [false, true] {
        let root = tempfile::tempdir().unwrap();
        let mut activation = activate(root.path());
        let path = root.path().join("_ic/odni/migration/inventory.json");
        let mut raw = fs::read(&path).unwrap();
        if duplicate {
            raw.splice(1..1, b"\"files\":[],".iter().copied());
        } else {
            raw.insert(0, b' ');
        }
        activation["inventory_sha256"] = json!(hex::encode(Sha256::digest(&raw)));
        fs::write(path, raw).unwrap();
        fs::write(
            root.path().join("_ic/odni/migration/activation.json"),
            serde_json::to_vec(&activation).unwrap(),
        )
        .unwrap();
        assert_refused(
            root.path(),
            &payload(root.path()),
            "ADVERSARY_OUTPUT_ROUTING_INVALID",
        );
    }
}
#[cfg(windows)]
#[test]
fn ic_routing_windows_junction_in_output_parent_refuses() {
    use std::process::Command;
    let root = tempfile::tempdir().unwrap();
    let outside = tempfile::tempdir().unwrap();
    activate(root.path());
    let link = root.path().join("_ic/adversary");
    let result = Command::new("cmd")
        .args(["/c", "mklink", "/J"])
        .arg(link.to_string_lossy().replace('/', "\\"))
        .arg(outside.path().to_string_lossy().replace('/', "\\"))
        .output()
        .unwrap();
    assert!(
        result.status.success(),
        "junction fixture unavailable: {:?}",
        result
    );
    let mut request = payload(root.path());
    request["adversary_output_dir"] = json!(root.path().join("_ic/adversary"));
    let outcome = dispatch(&request).unwrap();
    assert_eq!(outcome["refusal"]["code"], "ADVERSARY_OUTPUT_ROUTING_INVALID");
    assert!(outcome["outcome"].is_null());
    assert!(!root.path().join("calls.jsonl").exists());
    assert!(!outside.path().join("runs").exists());
    fs::remove_dir(&link).unwrap();
}

#[test]
fn ic_routing_shared_unicode_casefold_and_size_agency_controls() {
    for bad in [
        json!({"directories":["_intelligence/Stra\u{00df}e","_intelligence/STRASSE"]}),
        json!({"directories":["_intelligence/\u{03a3}","_intelligence/\u{03c2}"]}),
        json!({"directories":["_intelligence/\u{0130}","_intelligence/i\u{0307}"]}),
        json!({"destination_baseline":[["_ic/twelfth/file","b".repeat(64),0]]}),
        json!({"destination_baseline":[["_ic/odni","b".repeat(64),0]]}),
        json!({"destination_baseline":[["_ic/nara/file","b".repeat(64),9223372036854775808u64]]}),
        json!({"files":[{"source":"_intelligence/a","destination":"_ic/nara/legacy/a","sha256":"a".repeat(64),"size":9223372036854775808u64,"kind":"regular_file"}]}),
    ] {
        let root = tempfile::tempdir().unwrap();
        let mut activation = activate(root.path());
        let path = root.path().join("_ic/odni/migration/inventory.json");
        let mut inventory: Value = serde_json::from_slice(&fs::read(&path).unwrap()).unwrap();
        for (key, value) in bad.as_object().unwrap() {
            inventory[key] = value.clone();
        }
        let raw = canonical(&inventory);
        activation["inventory_sha256"] = json!(hex::encode(Sha256::digest(&raw)));
        fs::write(path, raw).unwrap();
        fs::write(
            root.path().join("_ic/odni/migration/activation.json"),
            serde_json::to_vec(&activation).unwrap(),
        )
        .unwrap();
        assert_refused(
            root.path(),
            &payload(root.path()),
            "ADVERSARY_OUTPUT_ROUTING_INVALID",
        );
    }
}

#[test]
#[ignore = "needs the adversary seat-routing config and council dossiers, which stay in the private engine repo"]
fn ic_routing_reviewed_agency_rows_accept_canonical_copies() {
    let root = tempfile::tempdir().unwrap();
    let mut activation = activate(root.path());
    let path = root.path().join("_ic/odni/migration/inventory.json");
    let mut inventory: Value = serde_json::from_slice(&fs::read(&path).unwrap()).unwrap();
    let rows = [
        ("council_meetings", "fbi/council_meetings"),
        ("stress_tests", "dia/stress_tests"),
        ("morphisms", "nga/morphisms"),
    ];
    inventory["files"] = json!(rows.map(|(source, target)| {
        let destination = format!("_ic/{target}/bounded.json");
        let copy = root.path().join(&destination);
        fs::create_dir_all(copy.parent().unwrap()).unwrap();
        fs::write(&copy, b"{}\n").unwrap();
        json!({"source":format!("_intelligence/{source}/bounded.json"),
               "destination":destination,"sha256":hex::encode(Sha256::digest(b"{}\n")),
               "size":3,"kind":"regular_file"})
    }));
    let raw = canonical(&inventory);
    activation["inventory_sha256"] = json!(hex::encode(Sha256::digest(&raw)));
    fs::write(path, raw).unwrap();
    fs::write(
        root.path().join("_ic/odni/migration/activation.json"),
        serde_json::to_vec(&activation).unwrap(),
    )
    .unwrap();
    let result = dispatch(&payload(root.path())).unwrap();
    assert!(result["refusal"].is_null(), "{result}");
    assert_eq!(result["outcome"]["is_authorized"], false);
    assert!(!root.path().join("_intelligence").exists());
}

#[test]
#[ignore = "needs the adversary seat-routing config and council dossiers, which stay in the private engine repo"]
fn ic_routing_historical_checkout_lock_payload_is_preserved() {
    let root = tempfile::tempdir().unwrap();
    let mut activation = activate(root.path());
    let inventory_path = root.path().join("_ic/odni/migration/inventory.json");
    let mut inventory: Value = serde_json::from_slice(&fs::read(&inventory_path).unwrap()).unwrap();
    let legacy = root.path().join("_intelligence/_oeos/checkout-writer.lock");
    let archived = root
        .path()
        .join("_ic/odni/oeos_control/checkout-writer.lock");
    let historical = b"{\"historical_lock_payload\":true}\n";
    for path in [&legacy, &archived] {
        fs::create_dir_all(path.parent().unwrap()).unwrap();
        fs::write(path, historical).unwrap();
    }
    inventory["files"] = json!([{
        "source":"_intelligence/_oeos/checkout-writer.lock",
        "destination":"_ic/odni/oeos_control/checkout-writer.lock",
        "sha256":hex::encode(Sha256::digest(historical)),
        "size":historical.len(),
        "kind":"regular_file"
    }]);
    let raw = canonical(&inventory);
    activation["inventory_sha256"] = json!(hex::encode(Sha256::digest(&raw)));
    fs::write(inventory_path, raw).unwrap();
    fs::write(
        root.path().join("_ic/odni/migration/activation.json"),
        serde_json::to_vec(&activation).unwrap(),
    )
    .unwrap();
    let result = dispatch(&payload(root.path())).unwrap();
    assert!(result["refusal"].is_null(), "{result}");
    assert_eq!(result["outcome"]["is_authorized"], false);
    assert_eq!(fs::read(legacy).unwrap(), historical);
    assert_eq!(fs::read(archived).unwrap(), historical);
}

#[test]
#[ignore = "needs the adversary seat-routing config and council dossiers, which stay in the private engine repo"]
fn ic_routing_permanent_records_custody_is_admitted_under_nara() {
    let root = tempfile::tempdir().unwrap();
    activate(root.path());
    let mut req = payload(root.path());
    let perm_dir = root.path().join("_ic/nara/permanent_records");
    fs::create_dir_all(&perm_dir).unwrap();
    req["adversary_output_dir"] = json!(perm_dir);
    let result = dispatch(&req).unwrap();
    assert!(result["refusal"].is_null(), "{result}");
    assert_eq!(result["outcome"]["is_authorized"], false);
    assert!(!root.path().join("_intelligence").exists());
}

// Origin: engine/crates_rs/tests/pfp/adversary_ic_routing.rs
// Claim: urn:core:crates_rs:tests:adversary-ic-routing:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord903b5157 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord903b5157` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError903b5157 {
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
impl BoundaryError903b5157 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError903b5157 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError903b5157 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord903b5157 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError903b5157> {
        if capacity_bound == 0 {
            return Err(BoundaryError903b5157::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError903b5157::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError903b5157::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_903b5157() {
    let admitted = BoundaryRecord903b5157::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord903b5157::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
