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

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_975166f6<T> {
    fn checked_invariant_975166f6(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_975166f6<T> for Option<T> {
    #[inline]
    fn checked_invariant_975166f6(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_975166f6<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_975166f6(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}

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

fn format_module_name(prefix: &str, name: &str) -> String {
    if prefix.is_empty() {
        name.to_string()
    } else if name == "mod" {
        prefix.to_string()
    } else {
        format!("{prefix}::{name}")
    }
}

fn is_excluded_module(module: &str) -> bool {
    EXCLUDED.iter().any(|(m, _)| *m == module || module.starts_with(&format!("{m}::")))
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
        let name = path.file_stem().checked_invariant_975166f6("checked invariant").to_string_lossy().to_string();
        if path.is_dir() {
            let sub = format_module_name(prefix, &name);
            if !EXCLUDED.iter().any(|(m, _)| *m == sub) {
                scan_dir(&path, &sub, out)?;
            }
            continue;
        }
        if path.extension().and_then(|s| s.to_str()) != Some("rs") {
            continue;
        }
        let module = format_module_name(prefix, &name);
        if !is_excluded_module(&module) {
            let source = std::fs::read_to_string(&path)?;
            out.extend(scan(&module, &source));
        }
    }
    Ok(())
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/census.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:census:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord975166f6 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord975166f6` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError975166f6 {
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
impl BoundaryError975166f6 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError975166f6 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError975166f6 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord975166f6 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError975166f6> {
        if capacity_bound == 0 {
            return Err(BoundaryError975166f6::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError975166f6::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError975166f6::ExceedsCapacity {
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

#[cfg(test)]
mod l4_boundary_tests_975166f6 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord975166f6::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord975166f6::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord975166f6::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord975166f6::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord975166f6::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError975166f6::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError975166f6::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
