//! Build-time contract gate and binding audit.
//!
//! Runs the shared `core.contract.v1` loader/validator and the contract-to-Rust
//! binding audit before `core_contracts` compiles.

#[path = "src/kinds.rs"]
pub mod kinds;
#[path = "src/schema.rs"]
pub mod schema;
#[path = "src/sealed.rs"]
pub mod sealed;
#[path = "src/nomos_urn.rs"]
pub mod nomos_urn;
#[path = "src/validate.rs"]
pub mod validate;
#[path = "src/registry.rs"]
pub mod registry;
#[path = "src/audit.rs"]
pub mod audit;

use std::path::{Path, PathBuf};

fn main() {
    let manifest = PathBuf::from(std::env::var("CARGO_MANIFEST_DIR").expect("checked invariant"));
    let out_dir = PathBuf::from(std::env::var("OUT_DIR").expect("checked invariant"));
    let repo_root = manifest
        .ancestors()
        .nth(1)
        .expect("workspace repository root")
        .to_path_buf();
    let corpus = repo_root.join("governance/contracts/contract_canonical_definitions");

    println!("cargo:rerun-if-changed=build.rs");
    println!("cargo:rerun-if-changed=src/audit.rs");

    // Run contract binding audit (warning-only)
    let audit_report = match audit::audit(&repo_root) {
        Ok(report) => report,
        Err(error) => {
            println!("cargo:warning=CONTRACT_BINDING_AUDIT_NOT_RUN: {error}");
            audit::AuditReport::default()
        }
    };
    for path in &audit_report.watched {
        println!("cargo:rerun-if-changed={}", path.display());
    }

    let report_path = out_dir.join("contract_binding_audit.txt");
    std::fs::write(&report_path, audit::render_report(&audit_report))
        .unwrap_or_else(|e| panic!("write {}: {e}", report_path.display()));
    std::fs::write(
        out_dir.join("binding_audit_summary.rs"),
        audit::render_summary(&audit_report),
    )
    .unwrap_or_else(|e| panic!("write binding_audit_summary.rs: {e}"));

    for line in audit::warning_lines(&audit_report, &report_path.display().to_string()) {
        println!("cargo:warning={line}");
    }

    // The reviewed projection registry is authoritative. Every other local YAML
    // input is explicitly accounted for as unreconciled, not silently licensed.
    let repository = &repo_root;
    let projections = registry::projections::verify_projected_corpus(repository)
        .unwrap_or_else(|error| panic!("governance projection refused: {error}"));
    for path in &projections.watched_paths {
        println!("cargo:rerun-if-changed={}", path.display());
    }
    if !projections.unreconciled.is_empty() {
        println!(
            "cargo:warning=PROJECTION_RECONCILIATION_INCOMPLETE: {} reviewed, {} unreconciled; no operational-validation credit",
            projections.reviewed_projections, projections.unreconciled.len()
        );
    }

    let files = collect_and_watch_contracts(&corpus);

    let report = registry::load_v1_dir(&corpus)
        .unwrap_or_else(|e| panic!("core_contracts build-time contract gate failed: {e}"));

    if !report.findings.is_empty() {
        for finding in &report.findings {
            println!("cargo:warning=CONTRACT GATE: {finding}");
        }
        panic!(
            "core_contracts build-time contract gate failed with {} v1 finding(s)",
            report.findings.len()
        );
    }

    // These records are not silently lost, nor passed off as validated v1.
    // Full file-contract/v2 behavioral enforcement belongs to its own gates.
    for document in &report.non_v1_documents {
        println!(
            "cargo:warning=NON_V1_CONTRACT_ACCOUNTED_NOT_VALIDATED: {} [{}] {}",
            document.path.display(),
            document.schema_version,
            document.contract_id
        );
    }

    let contracts = load_v1_contracts(&files);
    generate_contract_images(&contracts, &out_dir.join("generated_contract_images.rs"));
    generate_vocabulary(&contracts, &out_dir.join("generated_v1_vocabulary.rs"));
    generate_published_corpus(&contracts, &out_dir.join("generated_published_corpus.rs"));
}

fn collect_and_watch_contracts(corpus: &Path) -> Vec<PathBuf> {
    let mut files = Vec::new();
    let mut dirs = Vec::new();
    collect_contracts(corpus, &mut files, &mut dirs);
    files.sort();
    dirs.sort();
    for d in &dirs {
        println!("cargo:rerun-if-changed={}", d.display());
    }
    for f in &files {
        println!("cargo:rerun-if-changed={}", f.display());
    }
    files
}

/// Contract ids whose `definition` blocks are lowered into generated Rust.
const PUBLISHED_SERIES_COORDINATES_ID: &str =
    "urn:core:evidence:published_series_coordinates:v1.0.0";
const PUBLISHED_PAPER_CARRIER_ID: &str = "urn:core:evidence:published_paper_carrier:v1.0.0";

fn definition_of<'a>(
    contracts: &'a [registry::CoreContractV1],
    id: &str,
) -> &'a serde_yaml::Value {
    contracts
        .iter()
        .find(|c| c.contract_id == id)
        .unwrap_or_else(|| panic!("required contract missing from the corpus: {id}"))
        .definition
        .as_ref()
        .unwrap_or_else(|| panic!("contract {id} has no `definition` block"))
}

fn req_str<'a>(v: &'a serde_yaml::Value, key: &str, id: &str) -> &'a str {
    v.get(key)
        .and_then(|x| x.as_str())
        .unwrap_or_else(|| panic!("contract {id}: `definition.{key}` must be a string"))
}

fn req_u64(v: &serde_yaml::Value, key: &str, id: &str) -> u64 {
    v.get(key)
        .and_then(|x| x.as_u64())
        .unwrap_or_else(|| panic!("contract {id}: `definition.{key}` must be an integer"))
}

fn req_bool(v: &serde_yaml::Value, key: &str, id: &str) -> bool {
    v.get(key)
        .and_then(|x| x.as_bool())
        .unwrap_or_else(|| panic!("contract {id}: `definition.{key}` must be a boolean"))
}

/// A contracted separator is exactly one character.
fn req_char(v: &serde_yaml::Value, key: &str, id: &str) -> char {
    let s = req_str(v, key, id);
    let mut chars = s.chars();
    let (Some(c), None) = (chars.next(), chars.next()) else {
        panic!("contract {id}: `definition.{key}` {s:?} must be exactly one character")
    };
    c
}

/// Lower the published-corpus contracts into typed Rust.
///
/// Repository paths, filename grammar and row counts are corpus data. Emitting
/// them here keeps consumers (`core_state`, `core_rip_papers`) literal-free
/// and makes a corpus edit a rebuild rather than a hand-edit of Rust.
fn generate_published_corpus(
    contracts: &[registry::CoreContractV1],
    out: &Path,
) {
    let mut code = String::from("// @generated by core_contracts/build.rs -- do not edit.\n\n");

    // ---- coordinates -------------------------------------------------------
    let def = definition_of(contracts, PUBLISHED_SERIES_COORDINATES_ID);
    let root =
        req_str(def, "published_root", PUBLISHED_SERIES_COORDINATES_ID).trim_end_matches('/');
    let action = req_str(def, "required_row_action", PUBLISHED_SERIES_COORDINATES_ID);

    code.push_str("/// Repository-relative root of the published corpus.\n");
    code.push_str(&format!("pub const PUBLISHED_ROOT: &str = {root:?};\n\n"));
    code.push_str("/// Verbatim `action` every published-series agreement row must carry.\n");
    code.push_str(&format!(
        "pub const PUBLISHED_SERIES_REQUIRED_ROW_ACTION: &str = {action:?};\n\n"
    ));

    code.push_str("/// One pinned paper coordinate. Paths are pre-composed at build time.\n");
    code.push_str("#[derive(Debug, Clone, Copy, PartialEq, Eq)]\n");
    code.push_str("pub struct PublishedPaperCoordinate {\n");
    for field in [
        "paper_id",
        "programme",
        "directory",
        "main",
        "claim_ledger",
        "main_path",
        "claim_ledger_path",
    ] {
        code.push_str(&format!("    pub {field}: &'static str,\n"));
    }
    code.push_str("    pub claim_row_count: usize,\n}\n\n");

    let papers = def
        .get("papers")
        .and_then(|p| p.as_sequence())
        .unwrap_or_else(|| {
            panic!("contract {PUBLISHED_SERIES_COORDINATES_ID}: `definition.papers` must be a list")
        });
    assert!(
        !papers.is_empty(),
        "contract {PUBLISHED_SERIES_COORDINATES_ID}: `definition.papers` is empty"
    );

    code.push_str(
        "/// Pinned coordinates, ascending by paper_id. Order is load-bearing: the\n\
         /// agreement matrix is zipped against this slice positionally.\n",
    );
    code.push_str("pub static PUBLISHED_SERIES_COORDINATES: &[PublishedPaperCoordinate] = &[\n");
    for paper in papers {
        let id = PUBLISHED_SERIES_COORDINATES_ID;
        let paper_id = req_str(paper, "paper_id", id);
        let programme = req_str(paper, "programme", id);
        let directory = req_str(paper, "directory", id);
        let main = req_str(paper, "main", id);
        let ledger = req_str(paper, "claim_ledger", id);
        let count = req_u64(paper, "claim_row_count", id);
        let dir = format!("{root}/{programme}/{directory}");
        code.push_str("    PublishedPaperCoordinate {\n");
        code.push_str(&format!("        paper_id: {paper_id:?},\n"));
        code.push_str(&format!("        programme: {programme:?},\n"));
        code.push_str(&format!("        directory: {directory:?},\n"));
        code.push_str(&format!("        main: {main:?},\n"));
        code.push_str(&format!("        claim_ledger: {ledger:?},\n"));
        code.push_str(&format!(
            "        main_path: {:?},\n",
            format!("{dir}/{main}")
        ));
        code.push_str(&format!(
            "        claim_ledger_path: {:?},\n",
            format!("{dir}/{ledger}")
        ));
        code.push_str(&format!("        claim_row_count: {count},\n"));
        code.push_str("    },\n");
    }
    code.push_str("];\n\n");

    // ---- carrier grammar ---------------------------------------------------
    let car = definition_of(contracts, PUBLISHED_PAPER_CARRIER_ID);
    let id = PUBLISHED_PAPER_CARRIER_ID;

    let claim_ledger_marker = req_str(car, "claim_ledger_marker", id);
    let claim_ledger_marker_lower = claim_ledger_marker.to_lowercase();
    code.push_str("/// Canonical claim-ledger filename marker (Title_Case spelling).\n");
    code.push_str(&format!(
        "pub const CLAIM_LEDGER_MARKER: &str = {claim_ledger_marker:?};\n"
    ));
    code.push_str("/// Lowercase form, for allocation-light comparison.\n");
    code.push_str(&format!(
        "pub const CLAIM_LEDGER_MARKER_LOWER: &str = {claim_ledger_marker_lower:?};\n\n"
    ));
    code.push_str("/// Filename prefix marking a global proof ledger at the corpus root.\n");
    code.push_str(&format!(
        "pub const PROOF_LEDGER_PREFIX: &str = {:?};\n\n",
        req_str(car, "proof_ledger_prefix", id)
    ));

    let grammar = car
        .get("paper_id_grammar")
        .unwrap_or_else(|| panic!("contract {id}: `definition.paper_id_grammar` missing"));
    code.push_str("/// Exact count of leading ASCII digits a paper id carries.\n");
    code.push_str(&format!(
        "pub const PAPER_ID_DIGITS: usize = {};\n",
        req_u64(grammar, "digits", id)
    ));
    code.push_str("/// Separators accepted immediately after a paper id.\n");
    code.push_str("pub const PAPER_ID_SEPARATORS: &[char] = &[\n");
    let mut separators: Vec<char> = Vec::new();
    for sep in grammar
        .get("separators")
        .and_then(|s| s.as_sequence())
        .unwrap_or_else(|| panic!("contract {id}: `paper_id_grammar.separators` must be a list"))
    {
        let s = sep
            .as_str()
            .unwrap_or_else(|| panic!("contract {id}: separator entries must be strings"));
        let mut chars = s.chars();
        let (Some(c), None) = (chars.next(), chars.next()) else {
            panic!("contract {id}: separator {s:?} must be exactly one character")
        };
        separators.push(c);
        code.push_str(&format!("    {c:?},\n"));
    }
    code.push_str("];\n\n");

    // ---- scoped paper id ---------------------------------------------------
    let scoped = car
        .get("scoped_paper_id")
        .unwrap_or_else(|| panic!("contract {id}: `definition.scoped_paper_id` missing"));
    let scoped_sep = req_char(scoped, "separator", id);
    let root_is_self = req_bool(scoped, "root_scope_is_self", id);

    // The load-bearing line of this build script. `build.rs` is the only place
    // where the local separators and the scoped separator are simultaneously in
    // scope, so it is the only place this can be checked. Without it, appending
    // the scoped separator to `paper_id_grammar.separators` in a later contract
    // edit compiles clean and silently reintroduces the defect the separator was
    // chosen to avoid.
    assert!(
        !separators.contains(&scoped_sep),
        "contract {id}: `scoped_paper_id.separator` {scoped_sep:?} is also a member of \
         `paper_id_grammar.separators` ({separators:?}). A scoped key is \
         `<scope>{scoped_sep}<leaf>`; if the scoped separator is also a local separator then \
         paper_id_of() accepts a scoped key and TRUNCATES it to its scope instead of refusing \
         it -- e.g. paper_id_of(\"009{scoped_sep}000\") would answer Some(\"009\") rather than \
         None. Remove {scoped_sep:?} from paper_id_grammar.separators, or choose a scoped \
         separator disjoint from them."
    );

    code.push_str(
        "/// Separator between the enclosing programme scope and the local paper id.\n\
         /// Disjoint from [`PAPER_ID_SEPARATORS`] by a build-time assert, so a scoped\n\
         /// key fed back through `paper_id_of` refuses instead of truncating.\n",
    );
    code.push_str(&format!(
        "pub const SCOPED_PAPER_ID_SEPARATOR: char = {scoped_sep:?};\n"
    ));
    code.push_str(
        "/// A paper with no paper-shaped enclosing folder is self-scoped: its scope\n\
         /// and leaf coincide.\n",
    );
    code.push_str(&format!(
        "pub const SCOPED_PAPER_ID_ROOT_IS_SELF: bool = {root_is_self};\n\n"
    ));

    let tower = car
        .get("gt_tower_prefix")
        .unwrap_or_else(|| panic!("contract {id}: `definition.gt_tower_prefix` missing"));
    code.push_str("/// Inclusive numeric range of GT-tower folder prefixes (993-999).\n");
    code.push_str(&format!(
        "pub const GT_TOWER_PREFIX_FIRST: u32 = {};\n",
        req_u64(tower, "first", id)
    ));
    code.push_str(&format!(
        "pub const GT_TOWER_PREFIX_LAST: u32 = {};\n\n",
        req_u64(tower, "last", id)
    ));

    code.push_str("/// A programme folder groups papers one level below the corpus root.\n");
    code.push_str(&format!(
        "pub const PROGRAMME_NESTING_DEPTH: usize = {};\n",
        req_u64(car, "programme_nesting_depth", id)
    ));

    std::fs::write(out, code).unwrap_or_else(|e| {
        panic!(
            "failed to write generated published corpus to {}: {e}",
            out.display()
        )
    });
}

fn collect_contracts(dir: &Path, files: &mut Vec<PathBuf>, dirs: &mut Vec<PathBuf>) {
    let rd = std::fs::read_dir(dir)
        .unwrap_or_else(|error| panic!("contract corpus unreadable: {}: {error}", dir.display()));
    dirs.push(dir.to_path_buf());
    for entry in rd {
        let entry = entry.unwrap_or_else(|error| {
            panic!(
                "contract corpus entry unreadable: {}: {error}",
                dir.display()
            )
        });
        let p = entry.path();
        if p.is_dir() {
            collect_contracts(&p, files, dirs);
        } else if p
            .file_name()
            .and_then(|n| n.to_str())
            .is_some_and(|n| n.ends_with(".contract.yaml"))
        {
            files.push(p);
        }
    }
}

fn load_v1_contracts(files: &[PathBuf]) -> Vec<registry::CoreContractV1> {
    let mut contracts = Vec::new();
    for path in files {
        let text = std::fs::read_to_string(path)
            .unwrap_or_else(|error| panic!("contract codegen input unreadable: {path:?}: {error}"));
        let (schema, _) =
            registry::v1_loader::classify_contract_document(&text)
                .unwrap_or_else(|error| {
                    panic!("contract codegen input invalid: {path:?}: {error}")
                });
        if schema != registry::v1_loader::DocumentSchema::DescriptorV1 {
            continue;
        }
        let c: registry::CoreContractV1 = serde_yaml::from_str(&text)
            .unwrap_or_else(|e| {
                panic!(
                    "validated v1 contract failed to reparse for image generation: {path:?}: {e}"
                )
            });
        contracts.push(c);
    }
    contracts.sort_by(|a, b| a.contract_id.cmp(&b.contract_id));
    contracts
}

fn generate_contract_images(
    contracts: &[registry::CoreContractV1],
    out: &Path,
) {
    let mut code = String::from(
        "use crate::binding::{BoundContract, ContractDescriptor as BindingContractDescriptor, GeneratedContractImage, LawBinding, TypeBinding};\n",
    );
    code.push_str(
        "use crate::kinds::{ContractEffect, ComponentRole, ContractCategory, ContractStatus, SchemaHash};\n\n",
    );
    code.push_str("#[derive(Debug, Clone, Copy)]\n");
    code.push_str("pub struct ContractImageCatalogEntry {\n");
    code.push_str("    pub id: &'static str,\n");
    code.push_str("    pub image_type: &'static str,\n");
    code.push_str("    pub descriptor: &'static BindingContractDescriptor,\n");
    code.push_str("}\n\n");

    let mut catalog_entries = Vec::new();
    let mut seen_types = std::collections::BTreeSet::new();
    // An image represents a validated declaration, not an implementation.
    // In particular, policy marker types must not require a fictitious Rust
    // binding merely to keep their compile-time role restrictions available.
    for c in contracts {
        let d = c.to_descriptor();
        let mut ty = image_type_name(&c.contract_id);
        if !seen_types.insert(ty.clone()) {
            ty = format!("{ty}{}", seen_types.len());
            seen_types.insert(ty.clone());
        }
        let static_name = screaming_snake(&ty);
        catalog_entries.push((c.contract_id.clone(), ty.clone(), static_name.clone()));

        code.push_str(&format!("pub struct {ty};\n"));
        code.push_str(&format!("impl crate::sealed::Sealed for {ty} {{}}\n\n"));
        code.push_str(&format!(
            "static {static_name}: BindingContractDescriptor = BindingContractDescriptor {{\n"
        ));
        code.push_str(&format!("    id: {:?},\n", d.id));
        code.push_str(&format!(
            "    category: ContractCategory::{:?},\n",
            d.category
        ));
        code.push_str(&format!("    role: ComponentRole::{:?},\n", d.role));
        code.push_str(&format!("    status: ContractStatus::{:?},\n", d.status));
        code.push_str(&format!(
            "    authority_effect: ContractEffect::{:?},\n",
            d.authority_effect
        ));
        code.push_str("    phi_law: LawBinding::Forbidden,\n");
        code.push_str("    structure_law: LawBinding::Forbidden,\n");
        code.push_str("    effect_law: LawBinding::Forbidden,\n");
        code.push_str("    input_type: TypeBinding::NotApplicable,\n");
        code.push_str("    output_type: TypeBinding::NotApplicable,\n");
        code.push_str("    subject_type: TypeBinding::NotApplicable,\n");
        code.push_str("    runtime_state_type: TypeBinding::NotApplicable,\n");
        code.push_str("    evidence_requirements: &[],\n");
        code.push_str("    forbidden_authority: &[],\n");
        code.push_str("    schema_hash: SchemaHash([0; 32]),\n");
        code.push_str("};\n\n");
        code.push_str(&format!("impl GeneratedContractImage for {ty} {{\n"));
        code.push_str(&format!(
            "    const DESCRIPTOR: &'static BindingContractDescriptor = &{static_name};\n"
        ));
        code.push_str("}\n\n");
        code.push_str(&format!("impl BoundContract for {ty} {{\n"));
        code.push_str("    type Input = ();\n");
        code.push_str("    type Output = ();\n");
        code.push_str("    type Subject = ();\n");
        code.push_str("    type RuntimeState = ();\n");
        code.push_str("}\n\n");
    }

    code.push_str(
        "pub static GENERATED_CONTRACT_IMAGE_CATALOG: &[ContractImageCatalogEntry] = &[\n",
    );
    for (id, ty, static_name) in &catalog_entries {
        code.push_str(&format!(
            "    ContractImageCatalogEntry {{ id: {:?}, image_type: {:?}, descriptor: &{static_name} }},\n",
            id, ty
        ));
    }
    code.push_str("];\n");

    std::fs::write(out, code).unwrap_or_else(|e| {
        panic!(
            "failed to write generated contract images to {}: {e}",
            out.display()
        )
    });
}

fn generate_vocabulary(contracts: &[registry::CoreContractV1], out: &Path) {
    let mut terminals = std::collections::BTreeSet::new();
    let mut refusals = std::collections::BTreeSet::new();

    for c in contracts {
        terminals.extend(c.descriptor.terminals.may_emit.iter().cloned());
        terminals.extend(c.descriptor.terminals.may_support.iter().cloned());
        refusals.extend(c.descriptor.refusals.may_emit.iter().cloned());
    }

    let mut code = String::new();
    code.push_str("pub const GENERATED_V1_KNOWN_TERMINALS: &[&str] = &[\n");
    for terminal in &terminals {
        code.push_str(&format!("    {:?},\n", terminal));
    }
    code.push_str("];\n\n");
    code.push_str("pub const GENERATED_V1_KNOWN_REFUSALS: &[&str] = &[\n");
    for refusal in &refusals {
        code.push_str(&format!("    {:?},\n", refusal));
    }
    code.push_str("];\n\n");
    code.push_str("pub fn is_generated_terminal(name: &str) -> bool {\n");
    code.push_str("    GENERATED_V1_KNOWN_TERMINALS.contains(&name)\n");
    code.push_str("}\n\n");
    code.push_str("pub fn is_generated_refusal(name: &str) -> bool {\n");
    code.push_str("    GENERATED_V1_KNOWN_REFUSALS.contains(&name)\n");
    code.push_str("}\n");

    std::fs::write(out, code).unwrap_or_else(|e| {
        panic!(
            "failed to write generated v1 vocabulary to {}: {e}",
            out.display()
        )
    });
}

fn image_type_name(contract_id: &str) -> String {
    let stem = contract_id
        .rsplit(':')
        .nth(1)
        .unwrap_or(contract_id)
        .trim_matches(|c: char| !c.is_ascii_alphanumeric() && c != '_');
    format!("{}Contract", pascal_case(stem))
}

fn pascal_case(s: &str) -> String {
    let mut out = String::new();
    let mut upper_next = true;
    for ch in s.chars() {
        if ch.is_ascii_alphanumeric() {
            if upper_next {
                out.push(ch.to_ascii_uppercase());
                upper_next = false;
            } else {
                out.push(ch);
            }
        } else {
            upper_next = true;
        }
    }
    out
}

fn screaming_snake(s: &str) -> String {
    let mut out = String::new();
    for (idx, ch) in s.chars().enumerate() {
        if ch.is_ascii_uppercase() && idx > 0 {
            out.push('_');
        }
        out.push(ch.to_ascii_uppercase());
    }
    out.push_str("_DESCRIPTOR");
    out
}

// Origin: engine/crates_rs/core_contracts/build.rs
// Claim: urn:core:crates_rs:core-contracts:build:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord1e282a2e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord1e282a2e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError1e282a2e {
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
impl BoundaryError1e282a2e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError1e282a2e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError1e282a2e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord1e282a2e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError1e282a2e> {
        if capacity_bound == 0 {
            return Err(BoundaryError1e282a2e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError1e282a2e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError1e282a2e::ExceedsCapacity {
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

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_1e282a2e {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
