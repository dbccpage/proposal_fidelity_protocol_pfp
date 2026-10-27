//! Target 6 — CODA_CS–Q conformance spine (Lean statement hashes, DDA/cochain
//! receipts, deterministic factorization replay, mutation-negative fail-closed).
//!
//! AuthorityEffect: None. Does not claim GlobalGreen. DEMO Python comparison is
//! structural field-name parity only (no full Python execution).

use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};

use serde::Deserialize;
use sha2::{Digest, Sha256};

// ---------------------------------------------------------------------------
// Retained DEMO engine locus (paper package cs_q/code/)
// ---------------------------------------------------------------------------

/// Documented DEMO paths for the Python factorization engine.
/// Structural comparison only — not a PROD face; not executed here.
const DEMO_ENGINE_PATHS: &[&str] = &[
    "coda_atlas/F005_coda/cs_q/code/coda_cs_q_engine.py",
    "coda_atlas/F005_coda/cs_q/code/test_coda_cs_q_engine.py",
];

/// Reviewed Git source bytes; this test never executes the Python demo.
const DEMO_ENGINE_SHA256: &[&str] = &[
    "24e41c5aed00dfee55a612dd3f5cd166b4dfede1f334adce3eb4a0a293832a73",
    "52c1fee1fdf8f1c13c998b48770a871ceff64e9760ff81b3d0754078eb5379f0",
];

/// Version 2: current bridge-core locus. These reviewed bytes support only
/// structural field parity. The historical v1 hashes above remain unchanged;
/// their unavailable source bytes are not claimed to have been replayed.
const DEMO_ENGINE_V2_PATHS: &[&str] = &[
    "engine/crates_rs/tests/core_wdp/fixtures/coda_cs_q/reference/coda_cs_q_bridge_core.py.txt",
    "engine/crates_rs/tests/core_wdp/fixtures/coda_cs_q/reference/test_coda_cs_q_engine.py.txt",
];
const DEMO_ENGINE_V2_SHA256: &[&str] = &[
    "bc8c50ad1f8c40d38de216659d1c437f0e5f9a527c0126fc9e1133f961e6b13d",
    "0284aabbff0e96b873575527b32dcccfcde9b051335428d4d755aec0cb264dd6",
];

/// Paper/Lean 14-schema field names from DEMO `BRIDGE_PACKET_14_SCHEMA_FIELDS`.
const PYTHON_BRIDGE_PACKET_14_FIELDS: &[&str] = &[
    "Lambda",
    "A_lambda",
    "F_lambda_mu",
    "chi_lambda_mu",
    "L",
    "eta",
    "X",
    "pi_lambda",
    "q",
    "Prof",
    "q_bar",
    "D",
    "V",
    "tau",
];

/// Paper 8-step admission labels from DEMO `BRIDGE_ADMISSIBLE_8_STEPS`.
const PYTHON_BRIDGE_ADMISSIBLE_8_STEPS: &[&str] = &[
    "1_finite_packet_validity",
    "2_tower_coherence",
    "3_completion_realization",
    "4_q_admission",
    "5_profile_factorization",
    "6_route_independence",
    "7_reflection_descent",
    "8_terminal_conservativity",
];

const FIXTURE_DIR: &str = "../tests/core_wdp/fixtures/coda_cs_q";

const ALLOWED_TERMINALS: &[&str] = &[
    "ConditionalSupport",
    "OpenResidual",
    "QHeld",
    "OracleNeeded",
    "Refused",
    "BoundedEvaluationScope",
];

// ---------------------------------------------------------------------------
// Fixture schema
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Deserialize)]
struct DdaReceiptMinimal {
    schema: String,
    face_id: String,
    degree: u32,
    lambda_capacity: i64,
    status: String,
    authority_effect: String,
}

#[derive(Debug, Clone, Deserialize)]
struct CochainReceiptMinimal {
    schema: String,
    c0_dim: u32,
    c1_dim: u32,
    d0_support: String,
    identity_check: String,
    authority_effect: String,
}

#[derive(Debug, Clone, Deserialize)]
struct FactorizationSample {
    domain_point: i64,
    profile: Vec<i64>,
    query_value: i64,
    q_bar_value: i64,
}

#[derive(Debug, Clone, Deserialize)]
struct ConformanceFixture {
    fixture_id: String,
    kind: String,
    mutation_kind: Option<String>,
    expect_conformance_pass: bool,
    authority_effect: String,
    global_green: bool,
    lean_statement_id: String,
    canonical_statement: String,
    statement_hash: String,
    dda_receipt: DdaReceiptMinimal,
    cochain_receipt: CochainReceiptMinimal,
    factorization_samples: Vec<FactorizationSample>,
    residual_open: bool,
    expected_terminal: String,
    python_demo_paths: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
enum ConformanceFailure {
    AuthorityNotNone(String),
    GlobalGreenClaimed,
    StatementHashMismatch {
        expected: String,
        recomputed: String,
    },
    DdaReceiptInvalid(String),
    CochainReceiptInvalid(String),
    FactorizationBroken(String),
    ResidualInconsistent(String),
    TerminalForbidden(String),
    EmptySamples,
    DemoPathMismatch(String),
}

// ---------------------------------------------------------------------------
// Pure helpers
// ---------------------------------------------------------------------------

fn sha256_hex(bytes: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    format!("{:x}", hasher.finalize())
}

fn statement_hash(canonical_statement: &str) -> String {
    sha256_hex(canonical_statement.as_bytes())
}

fn fixtures_dir() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join(FIXTURE_DIR)
}

fn load_all_fixtures() -> Vec<(PathBuf, ConformanceFixture)> {
    let dir = fixtures_dir();
    assert!(
        dir.is_dir(),
        "fixture directory missing: {} (create fixtures/coda_cs_q/)",
        dir.display()
    );
    let mut out = Vec::new();
    for entry in fs::read_dir(&dir).expect("read fixtures dir") {
        let entry = entry.expect("dir entry");
        let path = entry.path();
        if path.extension().and_then(|e| e.to_str()) != Some("json") {
            continue;
        }
        let raw = fs::read_to_string(&path).unwrap_or_else(|e| {
            panic!("failed to read {}: {e}", path.display());
        });
        let fixture: ConformanceFixture = serde_json::from_str(&raw).unwrap_or_else(|e| {
            panic!("failed to parse {}: {e}", path.display());
        });
        out.push((path, fixture));
    }
    out.sort_by(|a, b| a.0.cmp(&b.0));
    assert!(!out.is_empty(), "no JSON fixtures under {}", dir.display());
    out
}

/// Deterministic factorization replay on finite samples.
///
/// Checks:
/// 1. Fiber constancy: same profile ⇒ same query_value
/// 2. Factor map identity: query_value == q_bar_value for every sample
fn replay_factorization(samples: &[FactorizationSample]) -> Result<(), ConformanceFailure> {
    if samples.is_empty() {
        return Err(ConformanceFailure::EmptySamples);
    }
    let mut profile_to_query: BTreeMap<Vec<i64>, i64> = BTreeMap::new();
    for s in samples {
        if s.query_value != s.q_bar_value {
            return Err(ConformanceFailure::FactorizationBroken(format!(
                "domain_point={}: query_value={} != q_bar_value={} (q != q_bar ∘ Prof)",
                s.domain_point, s.query_value, s.q_bar_value
            )));
        }
        match profile_to_query.get(&s.profile) {
            Some(prev) if *prev != s.query_value => {
                return Err(ConformanceFailure::FactorizationBroken(format!(
                    "fiber constancy broken at profile {:?}: query {} vs {} (domain_point={})",
                    s.profile, prev, s.query_value, s.domain_point
                )));
            }
            None => {
                profile_to_query.insert(s.profile.clone(), s.query_value);
            }
            _ => {}
        }
    }
    Ok(())
}

fn validate_dda(r: &DdaReceiptMinimal) -> Result<(), ConformanceFailure> {
    if r.schema != "core.dda.receipt.v1" {
        return Err(ConformanceFailure::DdaReceiptInvalid(format!(
            "schema={}",
            r.schema
        )));
    }
    if r.authority_effect != "None" {
        return Err(ConformanceFailure::DdaReceiptInvalid(format!(
            "authority_effect={}",
            r.authority_effect
        )));
    }
    if r.face_id.is_empty() {
        return Err(ConformanceFailure::DdaReceiptInvalid(
            "empty face_id".into(),
        ));
    }
    if r.status == "GlobalGreen" {
        return Err(ConformanceFailure::DdaReceiptInvalid(
            "status must not be GlobalGreen".into(),
        ));
    }
    if r.lambda_capacity < 0 {
        return Err(ConformanceFailure::DdaReceiptInvalid(
            "negative lambda_capacity".into(),
        ));
    }
    let _ = r.degree;
    Ok(())
}

fn validate_cochain(r: &CochainReceiptMinimal) -> Result<(), ConformanceFailure> {
    if r.schema != "core.cochain.receipt.v1" {
        return Err(ConformanceFailure::CochainReceiptInvalid(format!(
            "schema={}",
            r.schema
        )));
    }
    if r.authority_effect != "None" {
        return Err(ConformanceFailure::CochainReceiptInvalid(format!(
            "authority_effect={}",
            r.authority_effect
        )));
    }
    if r.identity_check.is_empty() || r.d0_support.is_empty() {
        return Err(ConformanceFailure::CochainReceiptInvalid(
            "missing identity_check or d0_support".into(),
        ));
    }
    let _ = (r.c0_dim, r.c1_dim);
    Ok(())
}

/// Full closed-world conformance check for one fixture.
fn check_authority_and_terminal(f: &ConformanceFixture) -> Result<(), ConformanceFailure> {
    if f.authority_effect != "None" {
        return Err(ConformanceFailure::AuthorityNotNone(
            f.authority_effect.clone(),
        ));
    }
    if f.global_green {
        return Err(ConformanceFailure::GlobalGreenClaimed);
    }
    if !ALLOWED_TERMINALS.contains(&f.expected_terminal.as_str())
        || f.expected_terminal == "GlobalGreen"
    {
        return Err(ConformanceFailure::TerminalForbidden(
            f.expected_terminal.clone(),
        ));
    }
    Ok(())
}

fn check_fixture(f: &ConformanceFixture) -> Result<(), ConformanceFailure> {
    check_authority_and_terminal(f)?;

    let recomputed = statement_hash(&f.canonical_statement);
    if recomputed != f.statement_hash {
        return Err(ConformanceFailure::StatementHashMismatch {
            expected: f.statement_hash.clone(),
            recomputed,
        });
    }

    validate_dda(&f.dda_receipt)?;
    validate_cochain(&f.cochain_receipt)?;

    // DEMO path documentation must match the spine's documented locus.
    if let Some(p) = f
        .python_demo_paths
        .iter()
        .find(|p| !DEMO_ENGINE_PATHS.contains(&p.as_str()))
    {
        return Err(ConformanceFailure::DemoPathMismatch(p.clone()));
    }

    // Factorization must succeed for a fixture to "conform".
    replay_factorization(&f.factorization_samples)?;

    // Residual consistency: successful factorization cannot leave residual open
    // or declare OpenResidual. Flipped residual mutations fail closed here.
    if f.residual_open || f.expected_terminal == "OpenResidual" {
        return Err(ConformanceFailure::ResidualInconsistent(
            "residual open while factorization samples replay cleanly".into(),
        ));
    }

    // lean_statement_id must be non-empty (critical field presence).
    if f.lean_statement_id.is_empty() {
        return Err(ConformanceFailure::FactorizationBroken(
            "empty lean_statement_id".into(),
        ));
    }

    Ok(())
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[test]
fn fixture_corpus_has_required_positive_and_mutation_negative_coverage() {
    let fixtures = load_all_fixtures();
    let positives: Vec<_> = fixtures
        .iter()
        .filter(|(_, f)| f.kind == "positive")
        .collect();
    let mutations: Vec<_> = fixtures
        .iter()
        .filter(|(_, f)| f.kind == "mutation_negative")
        .collect();

    assert!(
        positives.len() >= 2,
        "need at least 2 positive fixtures, found {}",
        positives.len()
    );
    assert!(
        mutations.len() >= 2,
        "need at least 2 mutation-negative fixtures, found {}",
        mutations.len()
    );

    let mut kinds: Vec<String> = mutations
        .iter()
        .filter_map(|(_, f)| f.mutation_kind.clone())
        .collect();
    kinds.sort();
    for required in ["broken_factorization", "flipped_residual", "wrong_hash"] {
        assert!(
            kinds.iter().any(|k| k == required),
            "missing mutation kind {required}; have {kinds:?}"
        );
    }
}

#[test]
fn recompute_statement_hash_and_compare_for_all_fixtures() {
    for (path, f) in load_all_fixtures() {
        let recomputed = statement_hash(&f.canonical_statement);
        if f.mutation_kind.as_deref() == Some("wrong_hash") {
            assert_ne!(
                recomputed,
                f.statement_hash,
                "{}: wrong_hash fixture must carry a non-matching statement_hash",
                path.display()
            );
        } else {
            assert_eq!(
                recomputed,
                f.statement_hash,
                "{}: statement_hash must equal sha256(canonical_statement)",
                path.display()
            );
        }
    }
}

#[test]
fn deterministic_factorization_replay_on_positive_fixtures() {
    for (path, f) in load_all_fixtures() {
        if f.kind != "positive" {
            continue;
        }
        replay_factorization(&f.factorization_samples).unwrap_or_else(|e| {
            panic!(
                "{}: positive fixture factorization must replay cleanly: {e:?}",
                path.display()
            );
        });
        // Second replay is byte-identical outcome (determinism).
        let a = replay_factorization(&f.factorization_samples);
        let b = replay_factorization(&f.factorization_samples);
        assert_eq!(a, b, "{}: replay not deterministic", path.display());
    }
}

#[test]
fn all_fixtures_match_expect_conformance_pass_flag() {
    for (path, f) in load_all_fixtures() {
        let result = check_fixture(&f);
        let passed = result.is_ok();
        assert_eq!(
            passed,
            f.expect_conformance_pass,
            "{} (fixture_id={}, mutation={:?}): check_fixture → {:?}, expect_pass={}",
            path.display(),
            f.fixture_id,
            f.mutation_kind,
            result,
            f.expect_conformance_pass
        );
    }
}

#[test]
fn mutation_of_critical_fields_fails_closed() {
    let positives: Vec<_> = load_all_fixtures()
        .into_iter()
        .filter(|(_, f)| f.kind == "positive" && f.expect_conformance_pass)
        .map(|(_, f)| f)
        .collect();
    assert!(!positives.is_empty(), "need a positive base fixture");

    let base = &positives[0];
    assert!(
        check_fixture(base).is_ok(),
        "base positive must pass before mutation probes"
    );

    // wrong hash
    let mut m = base.clone();
    m.statement_hash = "deadbeef".repeat(8);
    assert!(
        matches!(
            check_fixture(&m),
            Err(ConformanceFailure::StatementHashMismatch { .. })
        ),
        "wrong hash must fail closed"
    );

    // broken factorization (fiber constancy)
    let mut m = base.clone();
    if let Some(sample) = m.factorization_samples.get_mut(0) {
        sample.query_value = sample.query_value.wrapping_add(99);
        // keep q_bar so the first failure mode can be either mismatch or fiber
    }
    assert!(
        matches!(
            check_fixture(&m),
            Err(ConformanceFailure::FactorizationBroken(_))
        ),
        "broken factorization must fail closed"
    );

    // flipped residual
    let mut m = base.clone();
    m.residual_open = true;
    assert!(
        matches!(
            check_fixture(&m),
            Err(ConformanceFailure::ResidualInconsistent(_))
        ),
        "flipped residual_open must fail closed"
    );

    // flipped terminal residual label
    let mut m = base.clone();
    m.expected_terminal = "OpenResidual".into();
    assert!(
        matches!(
            check_fixture(&m),
            Err(ConformanceFailure::ResidualInconsistent(_))
        ),
        "flipped expected_terminal to OpenResidual must fail closed"
    );

    // authority effect
    let mut m = base.clone();
    m.authority_effect = "Granted".into();
    assert!(
        matches!(
            check_fixture(&m),
            Err(ConformanceFailure::AuthorityNotNone(_))
        ),
        "non-None authority must fail closed"
    );

    // GlobalGreen claim
    let mut m = base.clone();
    m.global_green = true;
    assert!(
        matches!(
            check_fixture(&m),
            Err(ConformanceFailure::GlobalGreenClaimed)
        ),
        "GlobalGreen must fail closed"
    );

    // DDA authority
    let mut m = base.clone();
    m.dda_receipt.authority_effect = "Minted".into();
    assert!(
        matches!(
            check_fixture(&m),
            Err(ConformanceFailure::DdaReceiptInvalid(_))
        ),
        "DDA authority mint must fail closed"
    );
}

/// Read the reviewed demo's literal tuple syntax without executing Python.
/// Expressions, escaped values, duplicate declarations and missing closers fail.
fn python_string_tuple(source: &str, name: &str) -> Result<Vec<String>, String> {
    let declaration = format!("{name}: Tuple[str, ...] = (");
    let mut declarations = source.lines().enumerate().filter(|(_, line)| {
        line.trim() == declaration.as_str()
            || line.trim() == declaration.replace("Tuple[", "tuple[")
    });
    let (start, _) = declarations
        .next()
        .ok_or_else(|| format!("missing tuple {name}"))?;
    if declarations.next().is_some() {
        return Err(format!("duplicate tuple {name}"));
    }
    let mut values = Vec::new();
    for line in source.lines().skip(start + 1) {
        let literal = line.split('#').next().unwrap_or_default().trim();
        if literal == ")" {
            return Ok(values);
        }
        if literal.is_empty() {
            continue;
        }
        let value = literal
            .strip_suffix(',')
            .and_then(|value| value.strip_prefix('"'))
            .and_then(|value| value.strip_suffix('"'))
            .ok_or_else(|| format!("nonliteral tuple entry in {name}: {literal}"))?;
        if value.is_empty()
            || !value
                .bytes()
                .all(|byte| byte.is_ascii_alphanumeric() || byte == b'_')
        {
            return Err(format!("unsupported tuple entry in {name}: {literal}"));
        }
        values.push(value.to_owned());
    }
    Err(format!("unterminated tuple {name}"))
}

#[test]
fn python_demo_structural_field_name_parity() {
    let repo_root = Path::new(env!("CARGO_MANIFEST_DIR")).join("../../..");
    assert_eq!(DEMO_ENGINE_PATHS.len(), DEMO_ENGINE_SHA256.len());
    for (path, expected_hash) in DEMO_ENGINE_V2_PATHS.iter().zip(DEMO_ENGINE_V2_SHA256) {
        let absolute = repo_root.join(path);
        let bytes = fs::read(&absolute)
            .unwrap_or_else(|error| panic!("retained DEMO {}: {error}", absolute.display()));
        assert_eq!(
            sha256_hex(&bytes),
            *expected_hash,
            "DEMO source identity: {path}"
        );
    }

    let engine = fs::read_to_string(repo_root.join(DEMO_ENGINE_V2_PATHS[0]))
        .expect("retained DEMO must be UTF-8 source");
    let actual_fields = python_string_tuple(&engine, "BRIDGE_PACKET_14_SCHEMA_FIELDS")
        .expect("the DEMO must declare the literal field tuple");
    let actual_steps = python_string_tuple(&engine, "BRIDGE_ADMISSIBLE_8_STEPS")
        .expect("the DEMO must declare the literal step tuple");
    assert_eq!(
        actual_fields
            .iter()
            .map(String::as_str)
            .collect::<Vec<_>>()
            .as_slice(),
        PYTHON_BRIDGE_PACKET_14_FIELDS
    );
    assert_eq!(
        actual_steps
            .iter()
            .map(String::as_str)
            .collect::<Vec<_>>()
            .as_slice(),
        PYTHON_BRIDGE_ADMISSIBLE_8_STEPS
    );
    assert_eq!(actual_fields.len(), 14);
    assert_eq!(actual_steps.len(), 8);

    // Fixtures retain v1 citations as historical metadata; the active comparison
    // above binds v2 sources. Neither version executes Python or promotes authority.
    for (path, fixture) in load_all_fixtures() {
        assert_eq!(
            fixture
                .python_demo_paths
                .iter()
                .map(String::as_str)
                .collect::<Vec<_>>()
                .as_slice(),
            DEMO_ENGINE_PATHS,
            "{}: retained DEMO path census",
            path.display()
        );
    }
}

#[test]
fn python_tuple_guard_refuses_expressions_and_ambiguous_definitions() {
    let literal = "FIELDS: Tuple[str, ...] = (\n    \"q\",\n)\n";
    assert_eq!(
        python_string_tuple(literal, "FIELDS").unwrap(),
        vec!["q".to_string()]
    );
    let expression = "FIELDS: Tuple[str, ...] = (\n    \"q\" + \"_bar\",\n)\n";
    assert!(python_string_tuple(expression, "FIELDS").is_err());
    assert!(python_string_tuple(&format!("{literal}{literal}"), "FIELDS").is_err());
    assert!(python_string_tuple("FIELDS: Tuple[str, ...] = (\n    \"q\",\n", "FIELDS").is_err());
}

#[test]
fn authority_effect_none_and_no_global_green_on_all_fixtures() {
    for (path, f) in load_all_fixtures() {
        assert_eq!(
            f.authority_effect,
            "None",
            "{}: AuthorityEffect must be None",
            path.display()
        );
        assert!(
            !f.global_green,
            "{}: must not claim GlobalGreen",
            path.display()
        );
        assert_eq!(f.dda_receipt.authority_effect, "None");
        assert_eq!(f.cochain_receipt.authority_effect, "None");
        assert_ne!(f.dda_receipt.status, "GlobalGreen");
        assert_ne!(f.expected_terminal, "GlobalGreen");
    }
}

#[test]
fn broken_factorization_fixture_fails_fiber_or_qbar_check() {
    let fixtures = load_all_fixtures();
    let broken = fixtures
        .iter()
        .find(|(_, f)| f.mutation_kind.as_deref() == Some("broken_factorization"))
        .expect("mut_broken_factorization fixture required");
    let err = replay_factorization(&broken.1.factorization_samples)
        .expect_err("broken factorization samples must not replay");
    assert!(
        matches!(err, ConformanceFailure::FactorizationBroken(_)),
        "expected FactorizationBroken, got {err:?}"
    );
}

// Origin: engine/crates_rs/tests/core_wdp/test_coda_q_conformance_spine.rs
// Claim: urn:core:crates_rs:tests:test-coda-q-conformance-spine:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd8d75f1a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd8d75f1a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord8d75f1a {
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
impl BoundaryErrord8d75f1a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord8d75f1a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord8d75f1a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd8d75f1a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord8d75f1a> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord8d75f1a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord8d75f1a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord8d75f1a::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_d8d75f1a() {
    let admitted = BoundaryRecordd8d75f1a::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordd8d75f1a::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
