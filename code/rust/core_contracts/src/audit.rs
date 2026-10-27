//! Discovery audit of contract-to-Rust bindings, and of how many compiled
//! source files any contract names at all.
//!
//! It reads every YAML document under
//! `governance/contracts/contracts_oe/` and
//! checks the two ways a contract points at Rust:
//!
//! - `rust_binding: { crate, module, symbols }` on an object contract;
//! - `kind: rust_file_contract` with `file:`, which names one file.
//!   When the file contract also declares `crate` and `module_path`, their
//!   crate names must agree with the file location.
//!
//! Resolution follows the rules of the centralized
//! `crates_rs/tests/core_contracts/math_contract_gate.rs`,
//! so the two cannot disagree about what "resolves" means. `crate` is a
//! directory under `crates_rs/`. `module` is a path under that crate's `src/`,
//! where `a::b` is `src/a/b.rs` or `src/a/b/mod.rs`. A symbol is defined by a
//! declaring keyword, or by a named, non-glob `pub use`.
//!
//! It adds one check the gate does not make. A file that exists but is reached
//! by no `mod` declaration is never compiled, so a binding to it describes
//! nothing that runs. Such a binding is reported as resolving to an uncompiled
//! file.
//!
//! This module reports; it does not fail anything. The build script prints its
//! findings as cargo warnings. AuthorityEffect: None.

use serde::Deserialize;
use std::collections::{BTreeMap, BTreeSet};
use std::path::{Component, Path, PathBuf};

pub const CONTRACTS_DIR: &str = "governance/contracts/contracts_oe";
pub const ENGINE_DIR: &str = "engine";
pub const CRATES_RS_DIR: &str = "engine/crates_rs";

const FILE_CONTRACT_KIND: &str = "rust_file_contract";
const RETIRED_STATUSES: [&str; 2] = ["superseded", "retired"];
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BindingTarget {
    Module {
        krate: String,
        module: String,
        symbols: Vec<String>,
    },
    File {
        file: String,
    },
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DeclaredBinding {
    /// Repository-relative path of the contract document.
    pub contract: String,
    pub contract_id: String,
    pub target: BindingTarget,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Unresolved {
    UnknownCrate { krate: String },
    ModuleFileMissing { krate: String, module: String },
    MissingSymbols { file: String, symbols: Vec<String> },
    FileMissing { file: String },
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Resolution {
    /// `compiled` is `None` when the file is outside a declared Cargo target.
    Resolved {
        file: String,
        compiled: Option<bool>,
    },
    Unresolved(Unresolved),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BindingOutcome {
    pub binding: DeclaredBinding,
    pub resolution: Resolution,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CrateCoverage {
    pub krate: String,
    /// Source files reached from a crate root through `mod` declarations,
    /// excluding `#[cfg(test)]` modules.
    pub compiled: usize,
    /// Compiled source files that at least one resolved binding names.
    pub bound: usize,
    /// `.rs` files in the crate's source tree that no `mod` declaration reaches.
    pub uncompiled: Vec<String>,
    pub unbound: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct AuditReport {
    pub outcomes: Vec<BindingOutcome>,
    pub malformed: Vec<String>,
    pub skipped_retired: usize,
    pub coverage: Vec<CrateCoverage>,
    /// Paths whose change must rerun the audit.
    pub watched: Vec<PathBuf>,
}

impl AuditReport {
    pub fn unresolved(&self) -> impl Iterator<Item = &BindingOutcome> {
        self.outcomes
            .iter()
            .filter(|o| matches!(o.resolution, Resolution::Unresolved(_)))
    }

    pub fn not_compiled(&self) -> impl Iterator<Item = &BindingOutcome> {
        self.outcomes.iter().filter(|o| {
            matches!(
                o.resolution,
                Resolution::Resolved {
                    compiled: Some(false),
                    ..
                }
            )
        })
    }

    pub fn compiled_files(&self) -> usize {
        self.coverage.iter().map(|c| c.compiled).sum()
    }

    pub fn bound_files(&self) -> usize {
        self.coverage.iter().map(|c| c.bound).sum()
    }
}

#[derive(Debug)]
pub enum AuditError {
    WorkspaceManifest { path: PathBuf, reason: String },
}

impl std::fmt::Display for AuditError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            AuditError::WorkspaceManifest { path, reason } => {
                write!(f, "workspace manifest {}: {reason}", path.display())
            }
        }
    }
}

impl std::error::Error for AuditError {}

pub fn audit(repo_root: &Path) -> Result<AuditReport, AuditError> {
    let crates_rs = repo_root.join(CRATES_RS_DIR);
    let engine = repo_root.join(ENGINE_DIR);
    let contracts_dir = repo_root.join(CONTRACTS_DIR);

    let members = workspace_members(&crates_rs)?;
    let mut sources: BTreeMap<String, CrateSources> = BTreeMap::new();
    for member in &members {
        let dir = normalize(&crates_rs.join(member));
        sources.insert(member.clone(), crate_sources(&dir));
    }

    let mut report = AuditReport::default();
    let declared = collect_bindings(repo_root, &contracts_dir, &mut report);

    let mut bound_files: BTreeSet<PathBuf> = BTreeSet::new();
    for binding in declared {
        let (resolution, file) = resolve(&binding.target, &crates_rs, &engine, &sources);
        if let (Some(file), Resolution::Resolved { .. }) = (file, &resolution) {
            bound_files.insert(file);
        }
        report.outcomes.push(BindingOutcome {
            binding,
            resolution: relativize(repo_root, resolution),
        });
    }

    for (krate, crate_sources) in &sources {
        let unbound: Vec<String> = crate_sources
            .compiled
            .iter()
            .filter(|f| !bound_files.contains(*f))
            .map(|f| display_relative(repo_root, f))
            .collect();
        report.coverage.push(CrateCoverage {
            krate: krate.clone(),
            compiled: crate_sources.compiled.len(),
            bound: crate_sources.compiled.len() - unbound.len(),
            uncompiled: crate_sources
                .uncompiled
                .iter()
                .map(|f| display_relative(repo_root, f))
                .collect(),
            unbound,
        });
    }

    report.watched.push(contracts_dir);
    report.watched.push(crates_rs.join("Cargo.toml"));
    report
        .watched
        .extend(sources.values().map(|s| s.dir.clone()));
    Ok(report)
}

/// Lines for cargo warnings, without the `cargo:warning=` prefix. One line
/// per finding, then one line per crate, then a summary line that names
/// `report_path`.
pub fn warning_lines(report: &AuditReport, report_path: &str) -> Vec<String> {
    let mut lines = Vec::new();
    for outcome in report.unresolved() {
        if let Resolution::Unresolved(reason) = &outcome.resolution {
            lines.push(format!(
                "CONTRACT_BINDING_UNRESOLVED: {} ({}): {}",
                outcome.binding.contract,
                outcome.binding.contract_id,
                describe(reason)
            ));
        }
    }
    for outcome in report.not_compiled() {
        if let Resolution::Resolved { file, .. } = &outcome.resolution {
            lines.push(format!(
                "CONTRACT_BINDING_NOT_COMPILED: {} ({}): {file} is reached by no mod declaration",
                outcome.binding.contract, outcome.binding.contract_id
            ));
        }
    }
    for finding in &report.malformed {
        lines.push(format!("CONTRACT_BINDING_MALFORMED: {finding}"));
    }
    for c in &report.coverage {
        lines.push(format!(
            "CONTRACT_COVERAGE: {}: {}/{} compiled source files named by a contract; {} .rs files not compiled",
            c.krate,
            c.bound,
            c.compiled,
            c.uncompiled.len()
        ));
    }
    lines.push(format!(
        "CONTRACT_BINDING_AUDIT: {} bindings declared, {} unresolved, {} resolve to uncompiled files, {} malformed, {} retired skipped; {}/{} compiled source files named by a contract; report: {report_path}",
        report.outcomes.len(),
        report.unresolved().count(),
        report.not_compiled().count(),
        report.malformed.len(),
        report.skipped_retired,
        report.bound_files(),
        report.compiled_files(),
    ));
    lines
}

/// The full report, including every unbound and uncompiled file.
pub fn render_report(report: &AuditReport) -> String {
    let mut out =
        String::from("# Contract binding audit (warning-only; AuthorityEffect: None)\n\n");
    for line in warning_lines(report, "this file") {
        out.push_str(&line);
        out.push('\n');
    }
    for c in &report.coverage {
        if c.unbound.is_empty() && c.uncompiled.is_empty() {
            continue;
        }
        out.push_str(&format!("\n## {}\n", c.krate));
        for f in &c.unbound {
            out.push_str(&format!("unbound     {f}\n"));
        }
        for f in &c.uncompiled {
            out.push_str(&format!("uncompiled  {f}\n"));
        }
    }
    out
}

/// Constants a later hard-fail test can assert on.
pub fn render_summary(report: &AuditReport) -> String {
    format!(
        "pub const DECLARED: usize = {};\n\
         pub const UNRESOLVED: usize = {};\n\
         pub const NOT_COMPILED: usize = {};\n\
         pub const MALFORMED: usize = {};\n\
         pub const COMPILED_SOURCE_FILES: usize = {};\n\
         pub const BOUND_SOURCE_FILES: usize = {};\n",
        report.outcomes.len(),
        report.unresolved().count(),
        report.not_compiled().count(),
        report.malformed.len(),
        report.compiled_files(),
        report.bound_files(),
    )
}

pub fn describe(reason: &Unresolved) -> String {
    match reason {
        Unresolved::UnknownCrate { krate } => {
            format!("crate `{krate}` is not a directory under crates_rs/")
        }
        Unresolved::ModuleFileMissing { krate, module } => {
            format!("module `{krate}::{module}` has no src/ file")
        }
        Unresolved::MissingSymbols { file, symbols } => {
            format!("{file} defines none of: {}", symbols.join(", "))
        }
        Unresolved::FileMissing { file } => format!("file `{file}` does not exist"),
    }
}

/// Syntax-level declarations shared with the v1 conformance gate. Comments,
/// strings and glob imports cannot establish a binding; behavior is separate.
#[path = "audit_declarations.rs"]
pub mod declarations;

pub fn defines_symbol(source: &str, symbol: &str) -> bool {
    declarations::declares_symbol(source, symbol).unwrap_or(false)
}

struct CrateSources {
    dir: PathBuf,
    compiled: BTreeSet<PathBuf>,
    uncompiled: BTreeSet<PathBuf>,
}

fn resolve(
    target: &BindingTarget,
    crates_rs: &Path,
    engine: &Path,
    sources: &BTreeMap<String, CrateSources>,
) -> (Resolution, Option<PathBuf>) {
    match target {
        BindingTarget::Module {
            krate,
            module,
            symbols,
        } => {
            let crate_dir = crates_rs.join(krate);
            if !crate_dir.join("Cargo.toml").is_file() {
                return (
                    Resolution::Unresolved(Unresolved::UnknownCrate {
                        krate: krate.clone(),
                    }),
                    None,
                );
            }
            let rel = module.trim_start_matches("crate::").replace("::", "/");
            let src = crate_dir.join("src");
            let Some(file) = [src.join(format!("{rel}.rs")), src.join(&rel).join("mod.rs")]
                .into_iter()
                .find(|p| p.is_file())
            else {
                return (
                    Resolution::Unresolved(Unresolved::ModuleFileMissing {
                        krate: krate.clone(),
                        module: module.clone(),
                    }),
                    None,
                );
            };
            let file = normalize(&file);
            let text = std::fs::read_to_string(&file).unwrap_or_default();
            let missing: Vec<String> = symbols
                .iter()
                .filter(|s| !defines_symbol(&text, s))
                .cloned()
                .collect();
            if !missing.is_empty() {
                return (
                    Resolution::Unresolved(Unresolved::MissingSymbols {
                        file: file.display().to_string(),
                        symbols: missing,
                    }),
                    None,
                );
            }
            let compiled = compiled_status(&file, sources);
            (
                Resolution::Resolved {
                    file: file.display().to_string(),
                    compiled,
                },
                Some(file),
            )
        }
        BindingTarget::File { file } => {
            let path = match file.strip_prefix("engine/") {
                Some(rest) => engine.join(rest),
                None => engine.join(file),
            };
            let path = normalize(&path);
            if !path.is_file() {
                return (
                    Resolution::Unresolved(Unresolved::FileMissing { file: file.clone() }),
                    None,
                );
            }
            let compiled = compiled_status(&path, sources);
            (
                Resolution::Resolved {
                    file: path.display().to_string(),
                    compiled,
                },
                Some(path),
            )
        }
    }
}

fn relativize(repo_root: &Path, resolution: Resolution) -> Resolution {
    match resolution {
        Resolution::Resolved { file, compiled } => Resolution::Resolved {
            file: display_relative(repo_root, Path::new(&file)),
            compiled,
        },
        Resolution::Unresolved(Unresolved::MissingSymbols { file, symbols }) => {
            Resolution::Unresolved(Unresolved::MissingSymbols {
                file: display_relative(repo_root, Path::new(&file)),
                symbols,
            })
        }
        other => other,
    }
}

fn compiled_status(file: &Path, sources: &BTreeMap<String, CrateSources>) -> Option<bool> {
    if sources.values().any(|source| source.compiled.contains(file)) {
        Some(true)
    } else if sources
        .values()
        .any(|source| source.uncompiled.contains(file))
    {
        Some(false)
    } else {
        None
    }
}

fn collect_bindings(
    repo_root: &Path,
    contracts_dir: &Path,
    report: &mut AuditReport,
) -> Vec<DeclaredBinding> {
    let mut files = Vec::new();
    walk(contracts_dir, &mut |p| {
        if p.extension().is_some_and(|e| e == "yaml") {
            files.push(p.to_path_buf());
        }
    });
    files.sort();

    let mut declared = Vec::new();
    for path in files {
        let rel = display_relative(repo_root, &path);
        let raw = match std::fs::read_to_string(&path) {
            Ok(raw) => raw,
            Err(err) => {
                report.malformed.push(format!("{rel}: unreadable: {err}"));
                continue;
            }
        };
        for document in serde_yaml::Deserializer::from_str(&raw) {
            let value = match serde_yaml::Value::deserialize(document) {
                Ok(value) => value,
                Err(err) => {
                    report
                        .malformed
                        .push(format!("{rel}: YAML parse failed: {err}"));
                    break;
                }
            };
            collect_document_bindings(&rel, &value, report, &mut declared);
        }
    }
    declared
}

fn collect_document_bindings(
    rel: &str,
    value: &serde_yaml::Value,
    report: &mut AuditReport,
    declared: &mut Vec<DeclaredBinding>,
) {
    let Some(map) = value.as_mapping() else {
        return;
    };
    let field = |k: &str| map.get(serde_yaml::Value::from(k));
    let text = |k: &str| field(k).and_then(|v| v.as_str()).map(str::to_owned);
    let contract_id = text("contract_id").unwrap_or_else(|| "<no contract_id>".into());
    let is_file_contract = text("kind").as_deref() == Some(FILE_CONTRACT_KIND);
    let binding = field("rust_binding");
    if binding.is_none() && !is_file_contract {
        return;
    }
    if text("status").is_some_and(|s| RETIRED_STATUSES.contains(&s.as_str())) {
        report.skipped_retired += 1;
        return;
    }
    if let Some(binding) = binding {
        match module_target(binding) {
            Ok(target) => declared.push(DeclaredBinding {
                contract: rel.to_owned(),
                contract_id: contract_id.clone(),
                target,
            }),
            Err(reason) => report
                .malformed
                .push(format!("{rel} ({contract_id}): rust_binding {reason}")),
        }
    }
    if is_file_contract {
        collect_file_contract_binding(rel, &contract_id, map, report, declared);
    }
}

fn collect_file_contract_binding(
    rel: &str,
    contract_id: &str,
    map: &serde_yaml::Mapping,
    report: &mut AuditReport,
    declared: &mut Vec<DeclaredBinding>,
) {
    let text = |k: &str| {
        map.get(serde_yaml::Value::from(k))
            .and_then(|v| v.as_str())
            .map(str::to_owned)
    };
    match text("file") {
        Some(file) => {
            if let Some(krate) = text("crate") {
                let path = file.strip_prefix("engine/").unwrap_or(&file);
                let crate_prefix = format!("crates_rs/{krate}/");
                let shared_test_prefix = format!("crates_rs/tests/{krate}/");
                if !path.starts_with(crate_prefix.as_str())
                    && !path.starts_with(shared_test_prefix.as_str())
                {
                    report.malformed.push(format!(
                        "{rel} ({contract_id}): rust_file_contract crate `{krate}` disagrees with file `{file}`"
                    ));
                }
                if let Some(module_path) = text("module_path") {
                    let module_prefix = format!("{krate}::");
                    if module_path != krate && !module_path.starts_with(module_prefix.as_str()) {
                        report.malformed.push(format!(
                            "{rel} ({contract_id}): rust_file_contract module_path `{module_path}` disagrees with crate `{krate}`"
                        ));
                    }
                }
            }
            declared.push(DeclaredBinding {
                contract: rel.to_owned(),
                contract_id: contract_id.to_owned(),
                target: BindingTarget::File { file },
            });
        }
        None => report.malformed.push(format!(
            "{rel} ({contract_id}): rust_file_contract has no `file`"
        )),
    }
}

fn module_target(binding: &serde_yaml::Value) -> Result<BindingTarget, String> {
    let map = binding.as_mapping().ok_or("is not a mapping")?;
    let text = |k: &str| {
        map.get(serde_yaml::Value::from(k))
            .and_then(|v| v.as_str())
            .map(str::to_owned)
    };
    let krate = text("crate").ok_or("has no string `crate`")?;
    let module = text("module").ok_or("has no string `module`")?;
    let symbols = match map.get(serde_yaml::Value::from("symbols")) {
        None => Vec::new(),
        Some(v) => v
            .as_sequence()
            .ok_or("`symbols` is not a list")?
            .iter()
            .map(|s| {
                s.as_str()
                    .map(str::to_owned)
                    .ok_or("`symbols` holds a non-string")
            })
            .collect::<Result<Vec<String>, &str>>()?,
    };
    Ok(BindingTarget::Module {
        krate,
        module,
        symbols,
    })
}

fn workspace_members(crates_rs: &Path) -> Result<Vec<String>, AuditError> {
    let path = crates_rs.join("Cargo.toml");
    let manifest = std::fs::read_to_string(&path).map_err(|e| AuditError::WorkspaceManifest {
        path: path.clone(),
        reason: e.to_string(),
    })?;
    let start = manifest
        .find("members")
        .and_then(|i| manifest[i..].find('[').map(|j| i + j + 1))
        .ok_or_else(|| AuditError::WorkspaceManifest {
            path: path.clone(),
            reason: "no members array".into(),
        })?;
    let end = manifest[start..]
        .find(']')
        .map(|j| start + j)
        .ok_or_else(|| AuditError::WorkspaceManifest {
            path: path.clone(),
            reason: "unterminated members array".into(),
        })?;
    Ok(manifest[start..end]
        .split(',')
        .filter_map(|item| {
            let item = item.split('#').next().unwrap_or("").trim();
            item.strip_prefix('"')?.strip_suffix('"').map(str::to_owned)
        })
        .collect())
}

fn initial_crate_roots(dir: &Path, manifest: &str) -> Vec<PathBuf> {
    let mut roots: Vec<PathBuf> = target_paths(manifest, &["[lib]", "[[bin]]"])
        .into_iter()
        .map(|p| normalize(&dir.join(p)))
        .collect();
    if !roots.iter().any(|r| r.ends_with("lib.rs")) {
        roots.push(dir.join("src/lib.rs"));
    }
    roots.push(dir.join("src/main.rs"));
    walk(&dir.join("src/bin"), &mut |p| {
        let is_bin_root = p.extension().is_some_and(|e| e == "rs")
            && (p.parent().is_some_and(|parent| parent.ends_with("src/bin"))
                || p.file_name().is_some_and(|n| n == "main.rs"));
        if is_bin_root {
            roots.push(p.to_path_buf());
        }
    });
    roots
}

fn crate_sources(dir: &Path) -> CrateSources {
    let manifest = std::fs::read_to_string(dir.join("Cargo.toml")).unwrap_or_default();
    let roots = initial_crate_roots(dir, &manifest);
    // Test, bench and example targets are not library or binary source.
    let mut test_only: BTreeSet<PathBuf> =
        target_paths(&manifest, &["[[test]]", "[[bench]]", "[[example]]"])
            .into_iter()
            .map(|p| normalize(&dir.join(p)))
            .collect();

    let mut compiled = BTreeSet::new();
    let mut stack: Vec<(PathBuf, bool)> = roots
        .into_iter()
        .filter(|r| r.is_file())
        .map(|r| (normalize(&r), true))
        .collect();
    while let Some((file, is_root)) = stack.pop() {
        if !compiled.insert(file.clone()) {
            continue;
        }
        let text = std::fs::read_to_string(&file).unwrap_or_default();
        for decl in module_decls(&text) {
            if decl.inline {
                continue;
            }
            let Some(child) = child_file(&file, is_root, &decl) else {
                continue;
            };
            if decl.test_only {
                test_only.insert(child);
            } else {
                stack.push((child, false));
            }
        }
        for included in included_files(&file, &text) {
            stack.push((included, false));
        }
    }

    let mut all = BTreeSet::new();
    walk(&dir.join("src"), &mut |p| {
        if p.extension().is_some_and(|e| e == "rs") {
            all.insert(normalize(p));
        }
    });
    let uncompiled = all
        .into_iter()
        .filter(|f| !compiled.contains(f) && !test_only.contains(f))
        .collect();
    CrateSources {
        dir: dir.to_path_buf(),
        compiled,
        uncompiled,
    }
}

/// `path = "..."` values under the given manifest section headers.
fn target_paths(manifest: &str, sections: &[&str]) -> Vec<String> {
    let mut section = "";
    let mut out = Vec::new();
    for line in manifest.lines() {
        let line = line.trim();
        if line.starts_with('[') {
            section = line;
            continue;
        }
        if !sections.contains(&section) {
            continue;
        }
        if let Some(value) = line
            .strip_prefix("path")
            .map(str::trim_start)
            .and_then(|r| r.strip_prefix('='))
        {
            if let Some(p) = quoted(value.trim()) {
                out.push(p);
            }
        }
    }
    out
}

struct ModDecl {
    name: String,
    path: Option<String>,
    inline: bool,
    test_only: bool,
}

fn module_decls(source: &str) -> Vec<ModDecl> {
    let mut out = Vec::new();
    let mut attrs: Vec<String> = Vec::new();
    let mut in_block_comment = false;
    for raw in source.lines() {
        let mut line = raw.trim();
        if in_block_comment {
            match line.find("*/") {
                Some(i) => {
                    line = line[i + 2..].trim();
                    in_block_comment = false;
                }
                None => continue,
            }
        }
        if line.starts_with("/*") && !line.contains("*/") {
            in_block_comment = true;
            continue;
        }
        if line.is_empty() || line.starts_with("//") {
            continue;
        }
        let rest = drain_leading_attrs(line, &mut attrs);
        if rest.is_empty() {
            continue;
        }
        if let Some((name, inline)) = mod_item(rest) {
            out.push(ModDecl {
                name,
                path: attrs.iter().find_map(|a| path_attribute(a)),
                inline,
                test_only: attrs.iter().any(|a| is_cfg_test(a)),
            });
        }
        attrs.clear();
    }
    out
}

fn drain_leading_attrs<'a>(mut rest: &'a str, attrs: &mut Vec<String>) -> &'a str {
    while let Some(body) = rest.strip_prefix("#[") {
        match bracket_end(body) {
            Some(end) => {
                attrs.push(body[..end].to_owned());
                rest = body[end + 1..].trim_start();
            }
            None => {
                attrs.push(body.to_owned());
                rest = "";
            }
        }
    }
    rest
}

/// `mod name;` or `mod name {`, after an optional visibility.
fn mod_item(line: &str) -> Option<(String, bool)> {
    let mut rest = line;
    if let Some(after) = rest.strip_prefix("pub(") {
        rest = after.split_once(')')?.1.trim_start();
    } else if let Some(after) = rest.strip_prefix("pub ") {
        rest = after.trim_start();
    }
    let rest = rest.strip_prefix("mod ")?.trim_start();
    let name: String = rest
        .chars()
        .take_while(|c| c.is_alphanumeric() || *c == '_')
        .collect();
    if name.is_empty() {
        return None;
    }
    match rest[name.len()..].trim_start().chars().next() {
        Some(';') => Some((name, false)),
        Some('{') => Some((name, true)),
        _ => None,
    }
}

fn child_file(parent: &Path, parent_is_root: bool, decl: &ModDecl) -> Option<PathBuf> {
    let parent_dir = parent.parent()?;
    if let Some(path) = &decl.path {
        return Some(normalize(&parent_dir.join(path)));
    }
    let owns_directory = parent_is_root
        || parent
            .file_name()
            .is_some_and(|n| n == "mod.rs" || n == "lib.rs" || n == "main.rs");
    let dir = if owns_directory {
        parent_dir.to_path_buf()
    } else {
        parent_dir.join(parent.file_stem()?)
    };
    [
        dir.join(format!("{}.rs", decl.name)),
        dir.join(&decl.name).join("mod.rs"),
    ]
    .into_iter()
    .find(|p| p.is_file())
    .map(|p| normalize(&p))
}

/// `.rs` files pulled in with `include!("literal")`, relative to `file`.
fn included_files(file: &Path, text: &str) -> Vec<PathBuf> {
    let Some(dir) = file.parent() else {
        return Vec::new();
    };
    text.match_indices("include!(")
        .filter_map(|(i, m)| quoted(text[i + m.len()..].trim_start()))
        .filter(|p| p.ends_with(".rs"))
        .map(|p| normalize(&dir.join(p)))
        .filter(|p| p.is_file())
        .collect()
}

fn bracket_end(body: &str) -> Option<usize> {
    let mut depth = 0usize;
    let mut in_string = false;
    let mut escaped = false;
    for (i, c) in body.char_indices() {
        if in_string {
            match c {
                _ if escaped => escaped = false,
                '\\' => escaped = true,
                '"' => in_string = false,
                _ => {}
            }
            continue;
        }
        match c {
            '"' => in_string = true,
            '[' => depth += 1,
            ']' if depth == 0 => return Some(i),
            ']' => depth -= 1,
            _ => {}
        }
    }
    None
}

fn path_attribute(attr: &str) -> Option<String> {
    let rest = attr
        .trim()
        .strip_prefix("path")?
        .trim_start()
        .strip_prefix('=')?;
    quoted(rest.trim())
}

fn is_cfg_test(attr: &str) -> bool {
    let compact: String = attr.chars().filter(|c| !c.is_whitespace()).collect();
    compact == "cfg(test)" || compact.starts_with("cfg(all(test,")
}

/// The contents of a leading `"..."`, without escape handling.
fn quoted(s: &str) -> Option<String> {
    let rest = s.strip_prefix('"')?;
    rest.split_once('"').map(|(inner, _)| inner.to_owned())
}

fn walk(dir: &Path, visit: &mut dyn FnMut(&Path)) {
    if dir.is_file() {
        visit(dir);
        return;
    }
    let Ok(entries) = std::fs::read_dir(dir) else {
        return;
    };
    let mut paths: Vec<PathBuf> = entries.flatten().map(|e| e.path()).collect();
    paths.sort();
    for path in paths {
        if path.is_dir() {
            walk(&path, visit);
        } else {
            visit(&path);
        }
    }
}

/// Lexical normalisation, so `a/b/../c.rs` and `a/c.rs` compare equal without
/// touching the filesystem (`canonicalize` adds a `\\?\` prefix on Windows).
fn normalize(path: &Path) -> PathBuf {
    let mut out = PathBuf::new();
    for component in path.components() {
        match component {
            Component::CurDir => {}
            Component::ParentDir => {
                if !out.pop() {
                    out.push("..");
                }
            }
            other => out.push(other.as_os_str()),
        }
    }
    out
}

fn display_relative(repo_root: &Path, path: &Path) -> String {
    let root = normalize(repo_root);
    let path = normalize(path);
    path.strip_prefix(&root)
        .unwrap_or(&path)
        .components()
        .map(|c| c.as_os_str().to_string_lossy())
        .collect::<Vec<_>>()
        .join("/")
}

// Origin: engine/crates_rs/core_contracts/src/audit.rs
// Claim: urn:core:crates_rs:core-contracts:audit:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
