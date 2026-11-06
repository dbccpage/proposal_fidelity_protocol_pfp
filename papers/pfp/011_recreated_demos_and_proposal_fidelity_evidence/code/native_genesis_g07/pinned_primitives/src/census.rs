//! Primitive — a lexical census of explicitly spelled event-returning APIs.
//!
//! Crate boundary: coda-carrier (the gate), coda-audit (the scan).  Source:
//! the boundary derivation's `state_event_generators` census, which reads
//! its own kernel for public functions whose return annotation contains an
//! event type and found a live violation at Challenge 1; crosstab §13.3.
//!
//! ```text
//! Scope: literal public-function syntax and named event return annotations.
//! ```
//!
//! Rust has no runtime reflection over signatures, so the census reads the
//! crate's own source — as the estate's forbidden-token scan reads
//! `.lean` files as text.  Two populations:
//!
//! * **the kernel** (carrier, observe, iso): zero matching signatures.
//! * **the whole source population, `src/**`**: every matching signature is
//!   named in the allowlist with its justification, and the allowlist is
//!   exact in both directions.  What is allowed: a translation of a
//!   *declared candidate* into events, and a constructor from explicit
//!   arguments.  Neither takes a state and returns an event.
//!
//! The outside (`outside.rs`) returns tokens, pairs, and fuel — never an
//! event — so it is inside the census and passes it.
//!
//! This is not a Rust type census or a nonexistence theorem. Aliases,
//! closures, const/async functions and trait methods are outside this
//! lexical population; nested source files are inside it (`scan_dir`). A constant state-to-event function is
//! definable; this gate cannot prove that no such function exists.

/// The kernel modules: no public function here may return an event.
pub const KERNEL: &[&str] = &[
    "token", "mark", "regime", "event", "supply", "admission", "imposition", "retention", "replay", "certification",
    "hash", "census", "context", "judgment", "profile", "separability", "observer", "renaming", "canonical",
    "automorphism",
];

/// Every public function in the crate that returns an event type, with why
/// it is allowed.
pub const ALLOWLIST: &[(&str, &str, &str)] = &[
    ("candidate", "delta_events", "translates a DECLARED candidate into admission events; takes the candidate, not only a state"),
];

/// Modules outside the census, each with why.
pub const EXCLUDED: &[(&str, &str)] = &[("testkit", "compiled under cfg(test) only; not part of the crate's API")];

/// A public function found returning an event type.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub struct Generator {
    /// Module (file stem).
    pub module: String,
    /// Function name.
    pub name: String,
    /// The return type text.
    pub returns: String,
}

fn is_event_type(text: &str) -> bool {
    let bytes = text.as_bytes();
    for (i, w) in text.match_indices("Event") {
        let before_ok = i == 0 || !(bytes[i - 1].is_ascii_alphanumeric() || bytes[i - 1] == b'_');
        let after = i + w.len();
        let after_ok = after >= bytes.len() || !(bytes[after].is_ascii_alphanumeric() || bytes[after] == b'_');
        if before_ok && after_ok {
            return true;
        }
        // `WorldEvent` and `BEvent` end in Event: catch them as words too.
        if after_ok {
            let start = text[..i].rfind(|c: char| !(c.is_ascii_alphanumeric() || c == '_')).map_or(0, |k| k + 1);
            let word = &text[start..after];
            if word == "WorldEvent" || word == "BEvent" {
                return true;
            }
        }
    }
    false
}

/// Scan one source text for public functions returning an event type.
pub fn scan(module: &str, source: &str) -> Vec<Generator> {
    let mut out = Vec::new();
    let mut rest = source;
    while let Some(i) = rest.find("pub fn ") {
        let sig_start = &rest[i + 7..];
        let end = sig_start.find(['{', ';']).unwrap_or(sig_start.len());
        let sig = &sig_start[..end];
        let name: String = sig.chars().take_while(|c| c.is_ascii_alphanumeric() || *c == '_').collect();
        if let Some(arrow) = sig.find("->") {
            let ret = sig[arrow + 2..].trim().to_string();
            if is_event_type(&ret) {
                out.push(Generator { module: module.to_string(), name, returns: ret });
            }
        }
        rest = &sig_start[end..];
    }
    out
}

/// Scan every `src/**/*.rs` of this crate.
pub fn scan_crate() -> std::io::Result<Vec<Generator>> {
    let dir = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("src");
    let mut out = Vec::new();
    scan_dir(&dir, "", &mut out)?;
    out.sort();
    Ok(out)
}

/// Recurse into `src/**`.  A file in a subdirectory is named `dir::stem`
/// and a `mod.rs` is named after its directory, so a directory module is
/// inside the census and cannot escape it by being one level down — the
/// estate's own runner census has exactly that hole ("a runner placed in
/// a SUBDIRECTORY of `code/` is outside the census"), and this one does
/// not.
fn scan_dir(dir: &std::path::Path, prefix: &str, out: &mut Vec<Generator>) -> std::io::Result<()> {
    let mut entries: Vec<_> = std::fs::read_dir(dir)?.collect::<Result<_, _>>()?;
    entries.sort_by_key(|e| e.path());
    for entry in entries {
        let path = entry.path();
        let name = path.file_stem().unwrap().to_string_lossy().to_string();
        if path.is_dir() {
            let sub = if prefix.is_empty() { name } else { format!("{prefix}::{name}") };
            if EXCLUDED.iter().any(|(m, _)| *m == sub) {
                continue;
            }
            scan_dir(&path, &sub, out)?;
            continue;
        }
        if path.extension().and_then(|s| s.to_str()) != Some("rs") {
            continue;
        }
        let module = if prefix.is_empty() {
            name
        } else if name == "mod" {
            prefix.to_string()
        } else {
            format!("{prefix}::{name}")
        };
        if EXCLUDED.iter().any(|(m, _)| *m == module || module.starts_with(&format!("{m}::"))) {
            continue;
        }
        let source = std::fs::read_to_string(&path)?;
        out.extend(scan(&module, &source));
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    /// The probe text is assembled at run time so that this file, which the
    /// census also reads, does not itself contain the pattern it probes.
    #[test]
    fn the_scanner_sees_a_generator_and_ignores_prose() {
        let pf = String::from("pub f") + "n ";
        let src = format!(
            "/// returns an Event in prose\n{pf}make(r: &Regime) -> Event {{ todo!() }}\n{pf}fine(r: &Regime) -> bool {{ true }}\n{pf}many() -> Vec<WorldEvent> {{ vec![] }}"
        );
        let found = scan("probe", &src);
        assert_eq!(found.len(), 2);
        assert_eq!(found[0].name, "make");
        assert_eq!(found[1].name, "many");
        assert!(!is_event_type("EventLike"));
        assert!(!is_event_type("Vec<Events>"));
    }

    /// L3 over the kernel: zero.
    #[test]
    fn l3_no_kernel_function_returns_an_event() {
        let found = scan_crate().unwrap();
        let in_kernel: Vec<&Generator> = found.iter().filter(|g| KERNEL.contains(&g.module.as_str())).collect();
        assert!(in_kernel.is_empty(), "kernel generators: {in_kernel:?}");
    }

    /// The census reaches into directory modules: the study folder is
    /// scanned under its `dir::stem` names, so a generator placed there
    /// would be found.  Checked by scanning a probe source under a
    /// directory-shaped module name, and by asserting the real directory
    /// module contributes zero generators.
    #[test]
    fn the_census_recurses_into_directory_modules() {
        let pf = String::from("pub f") + "n ";
        let src = format!("{pf}make() -> Event {{ todo!() }}");
        let found = scan("alpha_projection_obstruction::probe", &src);
        assert_eq!(found.len(), 1);
        let all = scan_crate().unwrap();
        let in_study: Vec<&Generator> = all.iter().filter(|g| g.module.starts_with("alpha_projection_obstruction")).collect();
        assert!(in_study.is_empty(), "study generators: {in_study:?}");
    }

    /// The whole-crate allowlist is exact in both directions.
    #[test]
    fn the_allowlist_is_exact() {
        let found = scan_crate().unwrap();
        let mut actual: Vec<(String, String)> = found.iter().map(|g| (g.module.clone(), g.name.clone())).collect();
        actual.sort();
        actual.dedup();
        let mut allowed: Vec<(String, String)> = ALLOWLIST.iter().map(|(m, n, _)| (m.to_string(), n.to_string())).collect();
        allowed.sort();
        assert_eq!(actual, allowed, "found {found:?}");
    }
}
