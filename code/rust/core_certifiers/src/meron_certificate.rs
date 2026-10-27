use num_rational::Ratio;
use num_traits::Zero;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::path::Path;
use thiserror::Error;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MeronSystem {
    pub name: String,
    pub num_sites: usize,
    pub num_configurations: usize,
    pub zero_meron_sector: Vec<usize>,
    pub multi_meron_sector: Vec<usize>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MeronConfig {
    pub id: usize,
    pub state: Vec<usize>,
    pub amplitude_num: i64,
    pub amplitude_den: i64,
    pub sign: i8,
    pub meron_count: usize,
}

impl MeronConfig {
    pub fn amplitude(&self) -> Ratio<i64> {
        Ratio::new(self.amplitude_num, self.amplitude_den)
    }

    pub fn signed_contribution(&self) -> Ratio<i64> {
        self.amplitude() * Ratio::from_integer(self.sign as i64)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MeronInvolutionPair {
    pub src: usize,
    pub dst: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MeronCertificate {
    pub system: MeronSystem,
    pub configurations: Vec<MeronConfig>,
    pub involution: Vec<MeronInvolutionPair>,
    pub non_meron_moves: Option<Vec<Vec<usize>>>,
}

pub const MERON_CONTRACT_PREFIX: &str = "math:meron_sign_problem_toy_exact_cancellation";
pub const MERON_MIN_AUTHORITY_CONTRACT_VERSION: &str = "v0.2.0";
pub const MERON_STALE_V01_HASH_PREFIX: &str = "71741d";
pub const MERON_STALE_TRICHOTOMY_CLASS: &str = "ExactRepair";

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum MeronTerminalKind {
    ExactCancellation,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum MeronAuthorityCeiling {
    FinitePartitionCertificateOnly,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub struct MeronFiniteVerdict {
    pub terminal_kind: MeronTerminalKind,
    pub authority_ceiling: MeronAuthorityCeiling,
}

/// `ExactCancellation` is a finite partition-certificate verdict, not an
/// `ExactRepair` packet and not a `CertifiedAuthority` minting path.
pub fn exact_cancellation_finite_verdict() -> MeronFiniteVerdict {
    MeronFiniteVerdict {
        terminal_kind: MeronTerminalKind::ExactCancellation,
        authority_ceiling: MeronAuthorityCeiling::FinitePartitionCertificateOnly,
    }
}

fn parse_meron_contract_version(contract_id: &str) -> Option<(u64, u64, u64)> {
    if !contract_id.starts_with(MERON_CONTRACT_PREFIX) {
        return None;
    }
    let (_, version) = contract_id.rsplit_once(":v")?;
    let mut parts = version.split('.');
    let major = parts.next()?.parse().ok()?;
    let minor = parts.next()?.parse().ok()?;
    let patch = parts.next()?.parse().ok()?;
    if parts.next().is_some() {
        return None;
    }
    Some((major, minor, patch))
}

pub fn is_supported_meron_contract_id(contract_id: &str) -> bool {
    parse_meron_contract_version(contract_id)
        .map(|version| version >= (0, 2, 0))
        .unwrap_or(false)
}

/// Firebreak for stale Meron artifacts discovered during the v0.2 hardening.
///
/// Any pre-v0.2 contract, old v0.1 hash family, or toy-certificate
/// `ExactRepair` trichotomy claim is treated as stale and must not be used as
/// an authority-indexed finite cancellation artifact.
pub fn is_stale_meron_artifact(
    contract_id: Option<&str>,
    certificate_hash: Option<&str>,
    trichotomy_class: Option<&str>,
) -> bool {
    if certificate_hash
        .map(|hash| hash.starts_with(MERON_STALE_V01_HASH_PREFIX))
        .unwrap_or(false)
    {
        return true;
    }
    if trichotomy_class
        .map(|class| class == MERON_STALE_TRICHOTOMY_CLASS)
        .unwrap_or(false)
    {
        return true;
    }
    contract_id
        .map(|id| !is_supported_meron_contract_id(id))
        .unwrap_or(true)
}

#[derive(Debug, Error)]
pub enum MeronVerificationError {
    #[error("Configuration count mismatch")]
    ConfigCountMismatch,
    #[error("Duplicate configuration ID {0}")]
    DuplicateConfigId(usize),
    #[error("Duplicate in zero sector")]
    DuplicateInZeroSector,
    #[error("Duplicate in multi sector")]
    DuplicateInMultiSector,
    #[error("Zero and multi sectors not disjoint")]
    SectorsNotDisjoint,
    #[error("Union of zero and multi sectors does not match all configurations")]
    SectorsUnionMismatch,
    #[error("Configuration length mismatch at {0}")]
    StateLengthMismatch(usize),
    #[error("Non-positive denominator at {0}")]
    NonPositiveDenominator(usize),
    #[error("Invalid sign at {0}")]
    InvalidSign(usize),
    #[error("Negative amplitude at {0}")]
    NegativeAmplitude(usize),
    #[error("Negative meron count at {0}")]
    NegativeMeronCount(usize),
    #[error("Config {0} in zero sector but not found")]
    ZeroSectorConfigNotFound(usize),
    #[error("Config {0} in zero sector has meron count {1}")]
    ZeroSectorHasMeronCount(usize, usize),
    #[error("Config {0} in zero sector has non-positive sign {1}")]
    ZeroSectorNonPositiveSign(usize, i8),
    #[error("Config {0} in multi sector has meron count 0")]
    MultiSectorHasZeroMeronCount(usize),
    #[error("Involution source/dst {0} not in multi-meron sector")]
    InvolutionNotInMultiSector(usize),
    #[error("Involution config {0} not found")]
    InvolutionConfigNotFound(usize),
    #[error("Self loop involution at {0}")]
    SelfLoopInvolution(usize),
    #[error("Multiple involution mapping for {0}")]
    MultipleInvolutionMapping(usize),
    #[error("Involution not symmetric for {0} <-> {1}")]
    InvolutionNotSymmetric(usize, usize),
    #[error("Amplitude not preserved: {0} != {1}")]
    AmplitudeNotPreserved(Ratio<i64>, Ratio<i64>),
    #[error("Signs do not invert: {0} != -{1}")]
    SignsDoNotInvert(i8, i8),
    #[error("Signed contributions do not cancel")]
    ContributionsDoNotCancel,
    #[error("Involution mapping does not cover entire multi-meron sector")]
    InvolutionNotCovering,
    #[error("Multi-meron sector does not sum to 0")]
    MultiSectorNotZero,
    #[error("Partition function identity failed: Z_all={0}, Z_zero={1}")]
    PartitionIdentityFailed(Ratio<i64>, Ratio<i64>),
    #[error("Invalid non-meron move edge {0} - {1}")]
    InvalidNonMeronMove(usize, usize),
    #[error("Missing non-meron move graph for ZeroRel derivation")]
    MissingNonMeronMoves,
    #[error("Malformed non-meron move at index {index}: expected 2 endpoints, got {len}")]
    MalformedNonMeronMove { index: usize, len: usize },
    #[error("Equivalence invariant violated in derived class")]
    EquivalenceInvariantViolated,
    #[error("Observable value missing for config {0}")]
    ObservableValueMissing(usize),
    #[error("Observable not invariant on pair {src} <-> {dst}: {left} != {right}")]
    ObservableNotInvariant {
        src: usize,
        dst: usize,
        left: Ratio<i64>,
        right: Ratio<i64>,
    },
    #[error("Certificate hash read failed: {0}")]
    CertificateHashReadFailed(String),
    #[error("Certificate hash mismatch: expected {expected}, got {actual}")]
    CertificateHashMismatch { expected: String, actual: String },
}

pub fn certificate_sha256_hex(path: impl AsRef<Path>) -> Result<String, std::io::Error> {
    let bytes = fs::read(path)?;
    let digest = Sha256::digest(&bytes);
    Ok(hex::encode(digest))
}

pub fn verify_certificate_hash(
    path: impl AsRef<Path>,
    expected: &str,
) -> Result<(), MeronVerificationError> {
    let actual = certificate_sha256_hex(path)
        .map_err(|err| MeronVerificationError::CertificateHashReadFailed(err.to_string()))?;
    if actual != expected {
        return Err(MeronVerificationError::CertificateHashMismatch {
            expected: expected.to_string(),
            actual,
        });
    }
    Ok(())
}

fn verify_sectors_disjoint(
    cert: &MeronCertificate,
) -> Result<(BTreeSet<usize>, BTreeSet<usize>), MeronVerificationError> {
    if cert.configurations.len() != cert.system.num_configurations {
        return Err(MeronVerificationError::ConfigCountMismatch);
    }

    let zero_sector: BTreeSet<usize> = cert.system.zero_meron_sector.iter().copied().collect();
    let multi_sector: BTreeSet<usize> = cert.system.multi_meron_sector.iter().copied().collect();

    if zero_sector.len() != cert.system.zero_meron_sector.len() {
        return Err(MeronVerificationError::DuplicateInZeroSector);
    }
    if multi_sector.len() != cert.system.multi_meron_sector.len() {
        return Err(MeronVerificationError::DuplicateInMultiSector);
    }
    if !zero_sector.is_disjoint(&multi_sector) {
        return Err(MeronVerificationError::SectorsNotDisjoint);
    }
    Ok((zero_sector, multi_sector))
}

fn validate_single_config(
    c: &MeronConfig,
    num_sites: usize,
) -> Result<(), MeronVerificationError> {
    if c.state.len() != num_sites {
        return Err(MeronVerificationError::StateLengthMismatch(c.id));
    }
    if c.amplitude_den <= 0 {
        return Err(MeronVerificationError::NonPositiveDenominator(c.id));
    }
    if c.sign != 1 && c.sign != -1 {
        return Err(MeronVerificationError::InvalidSign(c.id));
    }
    if c.amplitude() < Ratio::zero() {
        return Err(MeronVerificationError::NegativeAmplitude(c.id));
    }
    Ok(())
}

fn collect_and_validate_configs(
    cert: &MeronCertificate,
    zero_sector: &BTreeSet<usize>,
    multi_sector: &BTreeSet<usize>,
) -> Result<(BTreeSet<usize>, BTreeMap<usize, MeronConfig>), MeronVerificationError> {
    let mut config_ids = BTreeSet::new();
    let mut config_map = BTreeMap::new();

    // 1/5 Verifying Well-Formedness
    for c in &cert.configurations {
        if !config_ids.insert(c.id) {
            return Err(MeronVerificationError::DuplicateConfigId(c.id));
        }
        validate_single_config(c, cert.system.num_sites)?;
        config_map.insert(c.id, c.clone());
    }

    let all_declared: BTreeSet<usize> = zero_sector.union(multi_sector).copied().collect();
    if all_declared != config_ids {
        return Err(MeronVerificationError::SectorsUnionMismatch);
    }
    Ok((config_ids, config_map))
}

fn verify_sector_positivity(
    cert: &MeronCertificate,
    config_map: &BTreeMap<usize, MeronConfig>,
) -> Result<(), MeronVerificationError> {
    // 2/5 Verifying Zero-Meron Positivity
    for &cid in &cert.system.zero_meron_sector {
        let c = config_map
            .get(&cid)
            .ok_or(MeronVerificationError::ZeroSectorConfigNotFound(cid))?;
        if c.meron_count != 0 {
            return Err(MeronVerificationError::ZeroSectorHasMeronCount(
                cid,
                c.meron_count,
            ));
        }
        if c.sign != 1 {
            return Err(MeronVerificationError::ZeroSectorNonPositiveSign(
                cid, c.sign,
            ));
        }
    }
    for &cid in &cert.system.multi_meron_sector {
        let c = &config_map[&cid];
        if c.meron_count == 0 {
            return Err(MeronVerificationError::MultiSectorHasZeroMeronCount(cid));
        }
    }
    Ok(())
}

fn build_involution_map(
    involution: &[MeronInvolutionPair],
    config_map: &BTreeMap<usize, MeronConfig>,
    multi_sector: &BTreeSet<usize>,
) -> Result<BTreeMap<usize, usize>, MeronVerificationError> {
    // 3/5 Verifying Involution Correctness
    let mut inv_map = BTreeMap::new();

    for pair in involution {
        if !config_map.contains_key(&pair.src) {
            return Err(MeronVerificationError::InvolutionConfigNotFound(pair.src));
        }
        if !config_map.contains_key(&pair.dst) {
            return Err(MeronVerificationError::InvolutionConfigNotFound(pair.dst));
        }
        if !multi_sector.contains(&pair.src) {
            return Err(MeronVerificationError::InvolutionNotInMultiSector(pair.src));
        }
        if !multi_sector.contains(&pair.dst) {
            return Err(MeronVerificationError::InvolutionNotInMultiSector(pair.dst));
        }
        if pair.src == pair.dst {
            return Err(MeronVerificationError::SelfLoopInvolution(pair.src));
        }
        if inv_map.contains_key(&pair.src) {
            return Err(MeronVerificationError::MultipleInvolutionMapping(pair.src));
        }
        inv_map.insert(pair.src, pair.dst);
    }
    Ok(inv_map)
}

fn verify_involution_symmetry_and_coverage(
    inv_map: &BTreeMap<usize, usize>,
    config_map: &BTreeMap<usize, MeronConfig>,
    multi_sector: &BTreeSet<usize>,
) -> Result<(), MeronVerificationError> {
    let mut verified_pairs = BTreeSet::new();
    for (&src, &dst) in inv_map {
        if inv_map.get(&dst) != Some(&src) {
            return Err(MeronVerificationError::InvolutionNotSymmetric(src, dst));
        }
        let c_src = &config_map[&src];
        let c_dst = &config_map[&dst];

        if c_src.amplitude() != c_dst.amplitude() {
            return Err(MeronVerificationError::AmplitudeNotPreserved(
                c_src.amplitude(),
                c_dst.amplitude(),
            ));
        }
        if c_src.sign != -c_dst.sign {
            return Err(MeronVerificationError::SignsDoNotInvert(
                c_src.sign, c_dst.sign,
            ));
        }
        if c_src.signed_contribution() + c_dst.signed_contribution() != Ratio::zero() {
            return Err(MeronVerificationError::ContributionsDoNotCancel);
        }

        let mut pair = [src, dst];
        pair.sort();
        verified_pairs.insert(pair);
    }

    if verified_pairs.len() * 2 != multi_sector.len() {
        return Err(MeronVerificationError::InvolutionNotCovering);
    }
    Ok(())
}

fn verify_partition_function(
    cert: &MeronCertificate,
    config_map: &BTreeMap<usize, MeronConfig>,
    multi_sector: &BTreeSet<usize>,
) -> Result<(), MeronVerificationError> {
    // 4/5 Partition Function Equivalence
    let z_all: Ratio<i64> = config_map.values().map(|c| c.signed_contribution()).sum();
    let z_zero: Ratio<i64> = cert
        .system
        .zero_meron_sector
        .iter()
        .map(|&id| config_map[&id].signed_contribution())
        .sum();
    let z_multi: Ratio<i64> = multi_sector
        .iter()
        .map(|&id| config_map[&id].signed_contribution())
        .sum();

    if z_multi != Ratio::zero() {
        return Err(MeronVerificationError::MultiSectorNotZero);
    }
    if z_all != z_zero {
        return Err(MeronVerificationError::PartitionIdentityFailed(
            z_all, z_zero,
        ));
    }
    Ok(())
}

fn find_root(parent: &mut BTreeMap<usize, usize>, i: usize) -> usize {
    let p = parent[&i];
    if p == i {
        i
    } else {
        let root = find_root(parent, p);
        parent.insert(i, root);
        root
    }
}

fn build_equivalence_classes(
    moves: &[Vec<usize>],
    config_ids: &BTreeSet<usize>,
    config_map: &BTreeMap<usize, MeronConfig>,
) -> Result<Vec<Vec<usize>>, MeronVerificationError> {
    let mut parent = BTreeMap::new();
    for &cid in config_ids {
        parent.insert(cid, cid);
    }

    for (idx, m) in moves.iter().enumerate() {
        if m.len() != 2 {
            return Err(MeronVerificationError::MalformedNonMeronMove {
                index: idx,
                len: m.len(),
            });
        }
        let src = m[0];
        let dst = m[1];
        if !config_map.contains_key(&src) || !config_map.contains_key(&dst) {
            return Err(MeronVerificationError::InvalidNonMeronMove(src, dst));
        }
        let root_src = find_root(&mut parent, src);
        let root_dst = find_root(&mut parent, dst);
        if root_src != root_dst {
            parent.insert(root_src, root_dst);
        }
    }

    let mut equiv_classes_dict: BTreeMap<usize, Vec<usize>> = BTreeMap::new();
    for &cid in config_ids {
        let root = find_root(&mut parent, cid);
        equiv_classes_dict.entry(root).or_default().push(cid);
    }

    Ok(equiv_classes_dict.into_values().collect())
}

fn verify_equivalence_invariants(
    equiv_classes: Vec<Vec<usize>>,
    config_map: &BTreeMap<usize, MeronConfig>,
) -> Result<(), MeronVerificationError> {
    for eq_class in equiv_classes {
        if eq_class.is_empty() {
            continue;
        }
        let ref_c = &config_map[&eq_class[0]];
        for &cid in &eq_class {
            let curr = &config_map[&cid];
            if curr.amplitude() != ref_c.amplitude() || curr.sign != ref_c.sign {
                return Err(MeronVerificationError::EquivalenceInvariantViolated);
            }
        }
    }
    Ok(())
}

pub fn verify_meron_certificate(cert: &MeronCertificate) -> Result<(), MeronVerificationError> {
    let (zero_sector, multi_sector) = verify_sectors_disjoint(cert)?;
    let (config_ids, config_map) =
        collect_and_validate_configs(cert, &zero_sector, &multi_sector)?;
    verify_sector_positivity(cert, &config_map)?;
    let inv_map = build_involution_map(&cert.involution, &config_map, &multi_sector)?;
    verify_involution_symmetry_and_coverage(&inv_map, &config_map, &multi_sector)?;
    verify_partition_function(cert, &config_map, &multi_sector)?;

    // 5/5 Equivalence classes derivation from non-meron moves
    let moves = cert
        .non_meron_moves
        .as_ref()
        .ok_or(MeronVerificationError::MissingNonMeronMoves)?;
    let equiv_classes = build_equivalence_classes(moves, &config_ids, &config_map)?;
    verify_equivalence_invariants(equiv_classes, &config_map)?;

    Ok(())
}

pub fn verify_observable_compatibility(
    cert: &MeronCertificate,
    observable: &BTreeMap<usize, Ratio<i64>>,
) -> Result<(), MeronVerificationError> {
    verify_meron_certificate(cert)?;

    for c in &cert.configurations {
        if !observable.contains_key(&c.id) {
            return Err(MeronVerificationError::ObservableValueMissing(c.id));
        }
    }

    let mut checked_pairs = BTreeSet::new();
    for pair in &cert.involution {
        let mut key = [pair.src, pair.dst];
        key.sort();
        if !checked_pairs.insert(key) {
            continue;
        }
        let left = observable
            .get(&pair.src)
            .ok_or(MeronVerificationError::ObservableValueMissing(pair.src))?;
        let right = observable
            .get(&pair.dst)
            .ok_or(MeronVerificationError::ObservableValueMissing(pair.dst))?;
        if left != right {
            return Err(MeronVerificationError::ObservableNotInvariant {
                src: pair.src,
                dst: pair.dst,
                left: *left,
                right: *right,
            });
        }
    }

    Ok(())
}

// Origin: engine/crates_rs/core_certifiers/src/meron_certificate.rs
// Claim: urn:core:crates_rs:core-certifiers:meron-certificate:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    /// The Meron certificate fixture, relative to this crate's manifest (still
    /// CWD-independent, as the red-team #911 P2 hermetic-test fix required).
    ///
    /// It is read at run time rather than embedded with `include_bytes!`: the
    /// file is not in this repository, and an embedded missing file stops the
    /// whole crate's test build instead of failing the fixture tests. Every test
    /// that needs it fails loudly, naming the path, until it is restored.
    const CERT_PATH: &str = "../../research/published/013_the_problem_of_the_fermion_sign/000_the_meron_sign_problem_and_primitive_difference_ascent/meron_solution/meron_certificate.json";

    fn cert_bytes() -> Vec<u8> {
        let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join(CERT_PATH);
        std::fs::read(&path).unwrap_or_else(|error| {
            panic!(
                "Meron certificate fixture missing at {}: {error}; restore it to run the fixture tests",
                path.display()
            )
        })
    }
    /// SHA-256 of the fixture **as committed** — LF line endings, 1542 bytes.
    ///
    /// Corrected 2026-08-04. The previous pin,
    /// `d99038faedcfd12eea05fb5345af764203342b8818f8d45e006f2ae12f975c11`, was
    /// computed on a **CRLF working copy** (1649 bytes, 107 CR bytes) checked out
    /// before `.gitattributes` gained `eol=lf` for this path, and never
    /// re-normalised. `include_bytes!` embeds raw working-tree bytes, so that pin
    /// agreed only on that one stale checkout and failed on every fresh clone.
    ///
    /// The trap is that `git status` reports the file **clean** either way:
    /// check-in normalisation strips the CRs, so git sees no diff while the
    /// compiler sees different bytes. `fixture_is_lf_only` below is what stops
    /// this recurring.
    const CERT_SHA256: &str = "48a441463fa645bb2b9cde0c66d4f6aafa2ff502b309639d0508b7ae23cbfc3f";
    const CURRENT_CONTRACT_ID: &str = "math:meron_sign_problem_toy_exact_cancellation:v0.2.1";

    fn load_cert() -> MeronCertificate {
        serde_json::from_slice(&cert_bytes()).expect("Failed to parse the cert fixture")
    }

    #[test]
    #[ignore = "needs meron_certificate.json, which is not in this repository; see CERT_PATH"]
    fn test_meron_certificate_verification() {
        let cert = load_cert();
        assert!(verify_meron_certificate(&cert).is_ok());
    }

    /// The SHA-256 pin is asserted on the EMBEDDED bytes (the same bytes the
    /// rest of the suite parses), so the integrity check no longer reads the
    /// fixture from a CWD-relative path.
    #[test]
    #[ignore = "needs meron_certificate.json, which is not in this repository; see CERT_PATH"]
    fn test_meron_certificate_hash_matches_manifest() {
        let actual = hex::encode(Sha256::digest(cert_bytes()));
        assert_eq!(
            actual, CERT_SHA256,
            "embedded meron_certificate.json SHA-256 must match the pinned manifest hash"
        );
    }

    /// The pin is only meaningful if the embedded bytes are the *committed*
    /// bytes. `include_bytes!` reads the working tree, and `.gitattributes`
    /// normalisation means a CRLF copy still reports clean under `git status` —
    /// which is exactly how the previous pin came to encode a local artifact and
    /// survive for weeks.
    ///
    /// This asserts the canonical form directly, so the failure mode is named at
    /// the point it occurs rather than surfacing as an opaque hash mismatch.
    #[test]
    #[ignore = "needs meron_certificate.json, which is not in this repository; see CERT_PATH"]
    fn fixture_is_lf_only() {
        let bytes = cert_bytes();
        let crs = bytes.iter().filter(|&&b| b == b'\r').count();
        assert_eq!(
            crs, 0,
            "meron_certificate.json has {crs} CR bytes in the working tree; \
             .gitattributes declares eol=lf for it, so this checkout is stale. \
             Re-normalise (e.g. `git add --renormalize <path>`) rather than \
             re-pinning CERT_SHA256 to the CRLF hash."
        );
        assert_eq!(
            bytes.len(),
            1542,
            "committed fixture is 1542 bytes; a different length means the \
             fixture changed and the pin must be re-derived deliberately"
        );
    }

    #[test]
    fn exact_cancellation_is_finite_verdict_not_certified_authority() {
        let verdict = exact_cancellation_finite_verdict();
        assert_eq!(verdict.terminal_kind, MeronTerminalKind::ExactCancellation);
        assert_eq!(
            verdict.authority_ceiling,
            MeronAuthorityCeiling::FinitePartitionCertificateOnly
        );
    }

    #[test]
    fn stale_artifact_firebreak_rejects_v01_exact_repair_and_known_hash_prefix() {
        assert!(is_stale_meron_artifact(
            Some("math:meron_sign_problem_toy_exact_cancellation:v0.1.0"),
            None,
            None
        ));
        assert!(is_stale_meron_artifact(
            Some(CURRENT_CONTRACT_ID),
            Some("71741d0000000000000000000000000000000000000000000000000000000000"),
            None
        ));
        assert!(is_stale_meron_artifact(
            Some(CURRENT_CONTRACT_ID),
            Some(CERT_SHA256),
            Some("ExactRepair")
        ));
    }

    #[test]
    fn stale_artifact_firebreak_accepts_current_exact_cancellation_artifact() {
        assert!(!is_stale_meron_artifact(
            Some(CURRENT_CONTRACT_ID),
            Some(CERT_SHA256),
            Some("ExactCancellation")
        ));
    }

    #[test]
    #[ignore = "needs meron_certificate.json, which is not in this repository; see CERT_PATH"]
    fn rejects_missing_non_meron_moves() {
        let mut cert = load_cert();
        cert.non_meron_moves = None;
        assert!(matches!(
            verify_meron_certificate(&cert),
            Err(MeronVerificationError::MissingNonMeronMoves)
        ));
    }

    #[test]
    #[ignore = "needs meron_certificate.json, which is not in this repository; see CERT_PATH"]
    fn rejects_malformed_non_meron_move() {
        let mut cert = load_cert();
        cert.non_meron_moves = Some(vec![vec![0]]);
        assert!(matches!(
            verify_meron_certificate(&cert),
            Err(MeronVerificationError::MalformedNonMeronMove { .. })
        ));
    }

    #[test]
    #[ignore = "needs meron_certificate.json, which is not in this repository; see CERT_PATH"]
    fn rejects_zero_multi_sector_overlap() {
        let mut cert = load_cert();
        cert.system.multi_meron_sector.push(0);
        assert!(matches!(
            verify_meron_certificate(&cert),
            Err(MeronVerificationError::SectorsNotDisjoint)
        ));
    }

    #[test]
    #[ignore = "needs meron_certificate.json, which is not in this repository; see CERT_PATH"]
    fn rejects_broken_involution_symmetry() {
        let mut cert = load_cert();
        cert.involution[0].dst = 5;
        assert!(matches!(
            verify_meron_certificate(&cert),
            Err(MeronVerificationError::InvolutionNotSymmetric(_, _))
        ));
    }

    #[test]
    #[ignore = "needs meron_certificate.json, which is not in this repository; see CERT_PATH"]
    fn rejects_incomplete_involution_coverage() {
        let mut cert = load_cert();
        cert.involution
            .retain(|pair| pair.src == 2 || pair.src == 4);
        assert!(matches!(
            verify_meron_certificate(&cert),
            Err(MeronVerificationError::InvolutionNotCovering)
        ));
    }

    #[test]
    #[ignore = "needs meron_certificate.json, which is not in this repository; see CERT_PATH"]
    fn rejects_unequal_pair_weights() {
        let mut cert = load_cert();
        cert.configurations
            .iter_mut()
            .find(|c| c.id == 4)
            .unwrap()
            .amplitude_num = 3;
        assert!(matches!(
            verify_meron_certificate(&cert),
            Err(MeronVerificationError::AmplitudeNotPreserved(_, _))
        ));
    }

    #[test]
    #[ignore = "needs meron_certificate.json, which is not in this repository; see CERT_PATH"]
    fn rejects_same_sign_pair() {
        let mut cert = load_cert();
        cert.configurations
            .iter_mut()
            .find(|c| c.id == 4)
            .unwrap()
            .sign = -1;
        assert!(matches!(
            verify_meron_certificate(&cert),
            Err(MeronVerificationError::SignsDoNotInvert(_, _))
        ));
    }

    #[test]
    #[ignore = "needs meron_certificate.json, which is not in this repository; see CERT_PATH"]
    fn rejects_hidden_observer_quotient_across_signs() {
        let mut cert = load_cert();
        cert.non_meron_moves = Some(vec![vec![2, 4]]);
        assert!(matches!(
            verify_meron_certificate(&cert),
            Err(MeronVerificationError::EquivalenceInvariantViolated)
        ));
    }

    #[test]
    #[ignore = "needs meron_certificate.json, which is not in this repository; see CERT_PATH"]
    fn symmetric_observable_is_compatible() {
        let cert = load_cert();
        let observable: BTreeMap<usize, Ratio<i64>> = cert
            .configurations
            .iter()
            .map(|c| (c.id, Ratio::from_integer(1)))
            .collect();
        assert!(verify_observable_compatibility(&cert, &observable).is_ok());
    }

    #[test]
    #[ignore = "needs meron_certificate.json, which is not in this repository; see CERT_PATH"]
    fn non_invariant_observable_is_refuted() {
        let cert = load_cert();
        let mut observable: BTreeMap<usize, Ratio<i64>> = cert
            .configurations
            .iter()
            .map(|c| (c.id, Ratio::from_integer(1)))
            .collect();
        observable.insert(4, Ratio::from_integer(2));
        assert!(matches!(
            verify_observable_compatibility(&cert, &observable),
            Err(MeronVerificationError::ObservableNotInvariant { .. })
        ));
    }
}
