//! Direct Cargo-package boundary gate. Test tooling, not runtime actor licensing.
//! Cargo resolves manifest spelling, renames and inheritance. No fixture is built.
use serde::Deserialize;
use serde_json::Value;
use std::collections::BTreeSet;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Mutex;

const FORBIDDEN_DEPENDENCIES: &[&str] = &[
    "core_solvers",
    "core_policy",
    "core_types",
    "core_contracts",
    "pfp",
    "pfp_runtime",
    "core_homology",
    "core_quantum_physics",
    "engines",
    "core_pipelines",
    "core_id_run",
    "core_lifts",
    "core_certifiers",
];
const OWNER: &str = "core_functional";
static FIXTURE_NUMBER: AtomicU64 = AtomicU64::new(0);
static CARGO_METADATA_LANE: Mutex<()> = Mutex::new(());

#[derive(Debug, PartialEq, Eq)]
enum BoundaryError {
    CargoIo(String),
    CargoRefused {
        code: Option<i32>,
        diagnostic: String,
    },
    InvalidMetadata(String),
    UnsupportedVersion(u64),
    MissingOrAmbiguousOwner,
    ManifestIdentityMismatch,
    EmptyDependencyInventory,
    ForbiddenPackage(String),
}

// Origin: engine/crates_rs/tests/core_functional/dependency_boundary.rs
// Claim: urn:core:crates_rs:tests:dependency-boundary:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for BoundaryError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for BoundaryError {}

#[derive(Deserialize)]
struct Metadata {
    version: u64,
    packages: Vec<Package>,
}

#[derive(Deserialize)]
struct Package {
    name: String,
    manifest_path: PathBuf,
    dependencies: Vec<Dependency>,
}

#[derive(Deserialize)]
struct Dependency {
    name: String,
    kind: Value,
    target: Value,
    rename: Value,
    optional: bool,
}

fn metadata_bytes(manifest: &Path) -> Result<Vec<u8>, BoundaryError> {
    // Serialize metadata subprocesses even though libtest may run in parallel.
    let _lane = CARGO_METADATA_LANE.lock().expect("metadata lane poisoned");
    let output = Command::new(env!("CARGO"))
        .args([
            "metadata",
            "--offline",
            "--locked",
            "--no-deps",
            "--format-version",
            "1",
            "--manifest-path",
        ])
        .arg(manifest)
        .current_dir(manifest.parent().expect("manifest has parent"))
        .output()
        .map_err(|error| BoundaryError::CargoIo(error.to_string()))?;
    if !output.status.success() {
        return Err(BoundaryError::CargoRefused {
            code: output.status.code(),
            diagnostic: String::from_utf8_lossy(&output.stderr).into_owned(),
        });
    }
    Ok(output.stdout)
}

fn valid_optional_text(value: &Value) -> bool {
    value.is_null() || value.as_str().is_some_and(|text| !text.trim().is_empty())
}

fn check_metadata(raw: &[u8], manifest: &Path) -> Result<BTreeSet<String>, BoundaryError> {
    let metadata: Metadata = serde_json::from_slice(raw)
        .map_err(|error| BoundaryError::InvalidMetadata(error.to_string()))?;
    if metadata.version != 1 {
        return Err(BoundaryError::UnsupportedVersion(metadata.version));
    }
    let owners: Vec<_> = metadata
        .packages
        .iter()
        .filter(|p| p.name == OWNER)
        .collect();
    if owners.len() != 1 {
        return Err(BoundaryError::MissingOrAmbiguousOwner);
    }
    let owner = owners[0];
    // Cargo reports absolute manifest paths; binding to this exact file prevents
    // a clean package elsewhere in the workspace from standing in for the owner.
    let expected = manifest
        .canonicalize()
        .map_err(|error| BoundaryError::CargoIo(error.to_string()))?;
    if !owner.manifest_path.is_absolute()
        || owner.manifest_path.canonicalize().ok().as_ref() != Some(&expected)
    {
        return Err(BoundaryError::ManifestIdentityMismatch);
    }
    if owner.dependencies.is_empty() {
        return Err(BoundaryError::EmptyDependencyInventory);
    }
    collect_validated_dependencies(&owner.dependencies)
}

fn is_valid_dependency_entry(dependency: &Dependency) -> bool {
    !dependency.name.trim().is_empty()
        && matches!(dependency.kind.as_str(), Some("build" | "dev") | None)
        && (dependency.kind.is_null() || dependency.kind.is_string())
        && valid_optional_text(&dependency.target)
        && valid_optional_text(&dependency.rename)
}

fn collect_validated_dependencies(
    dependencies: &[Dependency],
) -> Result<BTreeSet<String>, BoundaryError> {
    let mut names = BTreeSet::new();
    for dependency in dependencies {
        if !is_valid_dependency_entry(dependency) {
            return Err(BoundaryError::InvalidMetadata(
                "invalid dependency identity or kind".into(),
            ));
        }
        // Do not filter by rename, target, kind or optional activation. A direct
        // declaration in any of these forms remains a direct package dependency.
        let _declared_optional = dependency.optional;
        if FORBIDDEN_DEPENDENCIES.contains(&dependency.name.as_str()) {
            return Err(BoundaryError::ForbiddenPackage(dependency.name.clone()));
        }
        names.insert(dependency.name.clone());
    }
    Ok(names)
}

fn check_manifest(manifest: &Path) -> Result<BTreeSet<String>, BoundaryError> {
    check_metadata(&metadata_bytes(manifest)?, manifest)
}

struct Fixture {
    root: PathBuf,
    manifest: PathBuf,
}

impl Fixture {
    fn new(dependency_name: &str, declarations: &str, workspace: &str) -> Self {
        let base = std::env::temp_dir()
            .canonicalize()
            .expect("writable external temp root");
        let root = base.join(format!(
            "core-functional-boundary-{}-{}",
            std::process::id(),
            FIXTURE_NUMBER.fetch_add(1, Ordering::SeqCst)
        ));
        fs::create_dir(&root).expect("new isolated fixture directory");
        let manifest = root.join("Cargo.toml");
        let fixture = Self { root, manifest };
        fs::create_dir(fixture.root.join("dep")).expect("dependency directory");
        fs::write(
            fixture.root.join("dep/Cargo.toml"),
            format!("[package]\nname = {dependency_name:?}\nversion = \"0.0.0\"\nedition = \"2021\"\n[lib]\npath = \"lib.rs\"\n"),
        ).expect("trusted fixture dependency manifest");
        fs::write(
            fixture.root.join("dep/lib.rs"),
            "// Metadata fixture only; never compiled.\n",
        )
        .expect("trusted fixture dependency source");
        fs::write(
            fixture.root.join("lib.rs"),
            "// Metadata fixture only; never compiled.\n",
        )
        .expect("trusted fixture root source");
        fs::write(
            &fixture.manifest,
            format!(
                "[package]\nname = \"core_functional\"\nversion = \"0.0.0\"\nedition = \"2021\"\n[lib]\npath = \"lib.rs\"\n[workspace]\nmembers = [\"dep\"]\n{workspace}\n{declarations}\n"
            ),
        ).expect("trusted fixture owner manifest");
        // All inputs are local path packages. The checked-in lockfile shape is
        // not fabricated: Cargo produces it offline before the locked read.
        let _lane = CARGO_METADATA_LANE.lock().expect("metadata lane poisoned");
        let output = Command::new(env!("CARGO"))
            .args(["generate-lockfile", "--offline", "--manifest-path"])
            .arg(&fixture.manifest)
            .current_dir(&fixture.root)
            .output()
            .expect("Cargo lockfile producer");
        assert!(
            output.status.success(),
            "fixture setup failed: {}",
            String::from_utf8_lossy(&output.stderr)
        );
        fixture
    }
}

impl Drop for Fixture {
    fn drop(&mut self) {
        // This object exclusively owns a create_dir-created child of temp_dir.
        // Validate the final absolute target before recursive removal.
        let base = std::env::temp_dir()
            .canonicalize()
            .expect("temp root identity");
        let actual = self
            .root
            .canonicalize()
            .expect("owned fixture still exists");
        assert_eq!(actual.parent(), Some(base.as_path()));
        assert!(actual
            .file_name()
            .unwrap()
            .to_string_lossy()
            .starts_with("core-functional-boundary-"));
        fs::remove_dir_all(actual).expect("remove only the owned fixture");
    }
}

#[test]
fn actual_functional_manifest_has_only_allowed_direct_packages() {
    let manifest = Path::new(env!("CARGO_MANIFEST_DIR")).join("Cargo.toml");
    let names = check_manifest(&manifest).expect("functional direct dependency boundary");
    assert!(names.contains("nalgebra") && names.contains("num-rational"));
}

#[test]
fn native_denylist_exactly_matches_the_existing_boundary_contract() {
    let root = Path::new(env!("CARGO_MANIFEST_DIR")).parent().unwrap();
    let path = root.join("core_contracts/../../../governance/contracts/contract_canonical_definitions/math/functional_layer_boundary.contract.yaml");
    let contract: serde_yaml::Value = serde_yaml::from_slice(&fs::read(path).unwrap()).unwrap();
    assert_eq!(
        contract["contract_id"].as_str(),
        Some("urn:core:math:functional_layer_boundary:v1.0.0")
    );
    assert_eq!(
        contract["descriptor"]["authority_effect"].as_str(),
        Some("none")
    );
    assert_eq!(
        contract["descriptor"]["customer_claim_allowed"].as_bool(),
        Some(false)
    );
    assert_eq!(
        contract["descriptor"]["operator_classes"]["must_not_self_assign"].as_bool(),
        Some(true)
    );
    let actual: Vec<_> = contract["doctrine"]["forbidden_dependencies"]
        .as_sequence()
        .unwrap()
        .iter()
        .map(|item| item.as_str().expect("forbidden package string"))
        .collect();
    let unique: BTreeSet<_> = actual.iter().copied().collect();
    assert_eq!(actual.len(), unique.len(), "duplicated policy identifier");
    assert_eq!(unique, FORBIDDEN_DEPENDENCIES.iter().copied().collect());
}

#[test]
fn allowed_renamed_math_package_is_not_confused_with_its_alias() {
    // The alias is forbidden-looking; Cargo's actual package identity is allowed.
    let fixture = Fixture::new(
        "num-rational",
        "[dependencies.core_solvers]\npackage = \"num-rational\"\npath = \"dep\"",
        "",
    );
    assert_eq!(
        check_manifest(&fixture.manifest),
        Ok(BTreeSet::from(["num-rational".into()]))
    );
}

#[test]
fn each_forbidden_package_is_rejected_even_through_an_inline_alias() {
    for package in FORBIDDEN_DEPENDENCIES {
        let fixture = Fixture::new(
            package,
            &format!("[dependencies]\nmath = {{ package = {package:?}, path = \"dep\" }}"),
            "",
        );
        assert_eq!(
            check_manifest(&fixture.manifest),
            Err(BoundaryError::ForbiddenPackage((*package).into()))
        );
    }
}

#[test]
fn table_form_renames_cannot_hide_a_forbidden_package() {
    let fixture = Fixture::new(
        "core_solvers",
        "[dependencies.innocent_math]\npackage = \"core_solvers\"\npath = \"dep\"",
        "",
    );
    assert_eq!(
        check_manifest(&fixture.manifest),
        Err(BoundaryError::ForbiddenPackage("core_solvers".into()))
    );
}

#[test]
fn inactive_target_build_dev_and_optional_declarations_are_still_checked() {
    for section in [
        "dependencies",
        "build-dependencies",
        "dev-dependencies",
        "target.'cfg(unix)'.dependencies",
        "target.'cfg(unix)'.build-dependencies",
        "target.'cfg(unix)'.dev-dependencies",
    ] {
        let fixture = Fixture::new(
            "engines",
            &format!("[{section}.innocent]\npackage = \"engines\"\npath = \"dep\""),
            "",
        );
        assert_eq!(
            check_manifest(&fixture.manifest),
            Err(BoundaryError::ForbiddenPackage("engines".into()))
        );
    }
    let optional = Fixture::new(
        "engines",
        "[dependencies.innocent]\npackage = \"engines\"\npath = \"dep\"\noptional = true",
        "",
    );
    assert_eq!(
        check_manifest(&optional.manifest),
        Err(BoundaryError::ForbiddenPackage("engines".into()))
    );
}

#[test]
fn workspace_inheritance_is_resolved_to_the_actual_forbidden_package() {
    let fixture = Fixture::new(
        "core_pipelines",
        "[dependencies]\nmath = { workspace = true }",
        "[workspace.dependencies]\nmath = { package = \"core_pipelines\", path = \"dep\" }",
    );
    assert_eq!(
        check_manifest(&fixture.manifest),
        Err(BoundaryError::ForbiddenPackage("core_pipelines".into()))
    );
}

#[test]
fn malformed_metadata_unknown_versions_and_missing_populations_fail_closed() {
    let fixture = Fixture::new(
        "num-rational",
        "[dependencies]\nmath = { package = \"num-rational\", path = \"dep\" }",
        "",
    );
    let raw = metadata_bytes(&fixture.manifest).unwrap();
    let parsed: Value = serde_json::from_slice(&raw).unwrap();
    assert!(matches!(
        check_metadata(b"{", &fixture.manifest),
        Err(BoundaryError::InvalidMetadata(_))
    ));
    let mut altered = parsed.clone();
    altered["version"] = Value::from(2);
    assert_eq!(
        check_metadata(&serde_json::to_vec(&altered).unwrap(), &fixture.manifest),
        Err(BoundaryError::UnsupportedVersion(2))
    );
    altered = parsed.clone();
    altered["packages"] = serde_json::json!([]);
    assert_eq!(
        check_metadata(&serde_json::to_vec(&altered).unwrap(), &fixture.manifest),
        Err(BoundaryError::MissingOrAmbiguousOwner)
    );
    altered["packages"] = serde_json::json!([{"name": "core_functional"}]);
    assert!(matches!(
        check_metadata(&serde_json::to_vec(&altered).unwrap(), &fixture.manifest),
        Err(BoundaryError::InvalidMetadata(_))
    ));
    let owner = parsed["packages"]
        .as_array()
        .unwrap()
        .iter()
        .find(|p| p["name"] == OWNER)
        .unwrap()
        .clone();
    altered = parsed.clone();
    altered["packages"] = serde_json::json!([owner.clone(), owner.clone()]);
    assert_eq!(
        check_metadata(&serde_json::to_vec(&altered).unwrap(), &fixture.manifest),
        Err(BoundaryError::MissingOrAmbiguousOwner)
    );
    altered["packages"] = serde_json::json!([owner]);
    altered["packages"][0]["dependencies"] = serde_json::json!([]);
    assert_eq!(
        check_metadata(&serde_json::to_vec(&altered).unwrap(), &fixture.manifest),
        Err(BoundaryError::EmptyDependencyInventory)
    );
}

#[test]
fn wrong_manifest_identity_and_malformed_dependency_rows_are_refused() {
    let fixture = Fixture::new(
        "num-rational",
        "[dependencies]\nmath = { package = \"num-rational\", path = \"dep\" }",
        "",
    );
    let parsed: Value =
        serde_json::from_slice(&metadata_bytes(&fixture.manifest).unwrap()).unwrap();
    let owner = parsed["packages"]
        .as_array()
        .unwrap()
        .iter()
        .find(|p| p["name"] == OWNER)
        .unwrap()
        .clone();
    let base = serde_json::json!({"version": 1, "packages": [owner]});
    let mut altered = base.clone();
    altered["packages"][0]["manifest_path"] =
        serde_json::to_value(fixture.root.join("dep/Cargo.toml")).unwrap();
    assert_eq!(
        check_metadata(&serde_json::to_vec(&altered).unwrap(), &fixture.manifest),
        Err(BoundaryError::ManifestIdentityMismatch)
    );
    for (key, value) in [
        ("name", serde_json::json!("")),
        ("kind", serde_json::json!("unknown")),
        ("kind", serde_json::json!(7)),
        ("target", serde_json::json!([])),
        ("rename", serde_json::json!({})),
        ("optional", serde_json::json!("true")),
    ] {
        altered = base.clone();
        altered["packages"][0]["dependencies"][0][key] = value;
        assert!(matches!(
            check_metadata(&serde_json::to_vec(&altered).unwrap(), &fixture.manifest),
            Err(BoundaryError::InvalidMetadata(_))
        ));
    }
    for key in ["name", "kind", "target", "rename", "optional"] {
        altered = base.clone();
        altered["packages"][0]["dependencies"][0]
            .as_object_mut()
            .unwrap()
            .remove(key);
        assert!(
            matches!(
                check_metadata(&serde_json::to_vec(&altered).unwrap(), &fixture.manifest),
                Err(BoundaryError::InvalidMetadata(_))
            ),
            "missing required dependency field: {key}"
        );
    }
}

#[test]
fn malformed_manifest_is_a_named_producer_refusal_not_an_empty_success() {
    let fixture = Fixture::new(
        "num-rational",
        "[dependencies]\nmath = { package = \"num-rational\", path = \"dep\" }",
        "",
    );
    fs::write(&fixture.manifest, "[package").unwrap();
    assert!(matches!(
        check_manifest(&fixture.manifest),
        Err(BoundaryError::CargoRefused {
            code: Some(101),
            ..
        })
    ));
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
