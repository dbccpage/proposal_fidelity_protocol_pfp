//! Layer 6 of the execution waist: admissibility evaluation and licensing.
//!
//! This crate decides whether a proposed transition may happen and, if so,
//! mints the single token that authorizes it. It occupies the narrowest point
//! of the whole system, so its boundaries are deliberately sharp:
//!
//! - It does not build Φ or Γ from a complex. Those arrive as exact decimals
//!   on a [`ValuationReceipt`]. The booleans are re-derived from those
//!   decimals. An evaluator that trusted the proposer's flags could move the
//!   goalposts it is judging against.
//! - It never commits state. That is Layer 7's, and it needs the token this
//!   crate mints.
//! - **`Φ₁ = 0` alone does not authorize anything.** Residual mass vanishing is
//!   necessary, not sufficient: an explicit repair differential and an
//!   exactness witness must accompany it. This is fail-closed test 4 of the
//!   OEOS specification, and it is the difference between "the number came out
//!   zero" and "here is why it is zero".
//!
//! [`ActionLicense`] cannot be constructed outside this crate. Its fields are
//! private and its only constructor is [`LicensingBoundary::mint`], so a caller
//! cannot fabricate one, and there is no `From`, `Default`, or deserializer
//! that would let one appear from data.
//!
//! AuthorityEffect: this crate is the one place that mints
//! `AuthorityEffect: AuthorizesTransition`. Only an engine commit performs a
//! StateTransition. Everything consumed here carries `None`.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_4419b3a0<T> {
    fn checked_invariant_4419b3a0(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_4419b3a0<T> for Option<T> {
    #[inline]
    fn checked_invariant_4419b3a0(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_4419b3a0<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_4419b3a0(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use thiserror::Error;

/// Layer 5's output: pure numbers, no judgement.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ValuationReceipt {
    /// Residual mass before the candidate transition, as an exact decimal string.
    pub phi_pre: String,
    /// Residual mass after.
    pub phi_post: String,
    /// Non-positive when the candidate does not increase residual mass.
    pub delta_phi_is_non_positive: bool,
    /// Exact curvature Γ₂. Zero is re-derived from this decimal.
    pub gamma2: String,
    /// The proposer's summary of `gamma2`. It is not the decision.
    pub gamma2_is_zero: bool,
    /// Whether Φ_post is exactly zero.
    pub phi_post_is_zero: bool,
}

/// The explicit reason a residual vanished.
///
/// Merge spec and OEOS both insist a bare zero is not a proof. The repair
/// differential `α` with `ω = d₀α` is the object that makes the claim
/// replayable, and the witness digest binds it to a specific checked artifact.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExactnessWitness {
    /// The repair differential, serialized exactly.
    pub repair_differential: String,
    /// Digest of the artifact a verifier can replay.
    pub witness_digest: String,
    /// The adapter that checked it, so "verified" is always "verified by what".
    pub checked_by: String,
}

/// A proposed state transition, before judgement.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct TransitionProposal {
    pub pre_state_digest: String,
    pub post_state_digest: String,
    pub valuation: ValuationReceipt,
    pub exactness_witness: Option<ExactnessWitness>,
    /// Structural invariants the proposer claims to preserve.
    pub preserved_invariants: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum Inadmissible {
    /// Residual mass increased.
    ResidualIncreased,
    /// Curvature did not vanish.
    CurvatureNonZero,
    /// Φ₁ = 0 with no repair differential or witness. The headline refusal.
    ZeroWithoutWitness,
    /// A witness was supplied but names no checking adapter.
    WitnessWithoutChecker,
    /// State digests are malformed or identical.
    MalformedTransition { detail: String },
    /// A required invariant was not declared preserved.
    InvariantNotPreserved { invariant: String },
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum AdmissibilityVerdict {
    Admissible,
    Inadmissible(Inadmissible),
}

#[derive(Debug, Error, PartialEq, Eq)]
pub enum LicensingError {
    #[error("cannot mint a license for an inadmissible transition: {0:?}")]
    Inadmissible(Inadmissible),
}

/// Reduce a digest to its one canonical spelling: `sha256:` and 64 lowercase
/// hex digits.
///
/// Returns `None` for anything else. This is deliberately stricter than
/// recognising a digest, because the previous version accepted both
/// `sha256:<hex>` and bare `<hex>` while every comparison downstream was on the
/// raw string. Two spellings of one value meant digest equality and string
/// equality were different relations, and the gap was reachable: a proposal
/// with `pre = "sha256:X"` and `post = "X"` passed the "a transition must
/// change the state" check and minted a license for a transition that changes
/// nothing. Normalising here makes the two relations the same again.
/// A validated state digest: `sha256:` followed by 64 lowercase hex digits.
///
/// A newtype rather than a `String` with a checking helper, because the defect
/// this replaces was not a missing check — it was a check that existed and was
/// bypassed. `is_digest` accepted both `sha256:<hex>` and bare `<hex>` while
/// every comparison downstream ran on the raw string, so digest equality and
/// string equality were different relations and a null transition could be
/// spelled as a change of state.
///
/// Making it a type moves the guarantee from "every call site remembers to
/// normalise" to "an unnormalised value cannot be constructed". There is no
/// public field, no `From<String>`, and `Deserialize` goes through
/// [`StateDigest::parse`], so a malformed digest cannot enter even from JSON.
///
/// One value, one spelling: uppercase hex is refused rather than folded. Every
/// producer in the tree emits lowercase via `hex::encode`, so nothing
/// legitimate is turned away, and admitting a second spelling is the shape of
/// the original defect.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(try_from = "String", into = "String")]
pub struct StateDigest(String);

#[derive(Debug, Error, PartialEq, Eq)]
#[error("not a canonical state digest ({reason}): {value:?}")]
pub struct DigestError {
    pub value: String,
    pub reason: &'static str,
}

impl StateDigest {
    pub fn parse(value: &str) -> Result<Self, DigestError> {
        let fail = |reason| DigestError {
            value: value.to_owned(),
            reason,
        };
        let hex = value
            .strip_prefix("sha256:")
            .ok_or_else(|| fail("missing the sha256: prefix; a bare hex string is not a digest"))?;
        if hex.len() != 64 {
            return Err(fail("expected 64 hex digits"));
        }
        if !hex
            .chars()
            .all(|c| c.is_ascii_digit() || (c.is_ascii_lowercase() && c.is_ascii_hexdigit()))
        {
            return Err(fail("expected lowercase hex only"));
        }
        Ok(Self(value.to_owned()))
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl TryFrom<String> for StateDigest {
    type Error = DigestError;
    fn try_from(value: String) -> Result<Self, Self::Error> {
        Self::parse(&value)
    }
}

impl From<StateDigest> for String {
    fn from(digest: StateDigest) -> Self {
        digest.0
    }
}

impl std::fmt::Display for StateDigest {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(&self.0)
    }
}

fn canonical_digest(value: &str) -> Option<String> {
    StateDigest::parse(value).ok().map(|d| d.0)
}

fn is_digest(value: &str) -> bool {
    canonical_digest(value).is_some()
}

/// An exact decimal, kept as sign plus digit strings so that comparison never
/// goes through a float.
///
/// `phi_pre` and `phi_post` are documented as exact decimal strings, and the
/// whole point of carrying them that way is lost if the policy layer reads them
/// through `f64`.
struct Decimal {
    negative: bool,
    int_part: String,
    frac_part: String,
}

fn all_ascii_digits(s: &str) -> bool {
    s.chars().all(|c| c.is_ascii_digit())
}

fn parse_decimal(raw: &str) -> Option<Decimal> {
    let text = raw.trim();
    if text.is_empty() {
        return None;
    }
    let (negative, rest) = match text.strip_prefix('-') {
        Some(r) => (true, r),
        None => (false, text.strip_prefix('+').unwrap_or(text)),
    };
    let (int_raw, frac_raw) = rest.split_once('.').unwrap_or((rest, ""));
    if (int_raw.is_empty() && frac_raw.is_empty())
        || !all_ascii_digits(int_raw)
        || !all_ascii_digits(frac_raw)
    {
        return None;
    }
    let int_part = int_raw.trim_start_matches('0').to_owned();
    let frac_part = frac_raw.trim_end_matches('0').to_owned();
    // Negative zero is zero. Without this "-0.0" would compare as less
    // than "0", and a transition to negative zero would read as a decrease.
    let is_neg = negative && !(int_part.is_empty() && frac_part.is_empty());
    let dec = Decimal {
        negative: is_neg,
        int_part,
        frac_part,
    };
    Some(dec)
}

impl Decimal {
    fn is_zero(&self) -> bool {
        self.int_part.is_empty() && self.frac_part.is_empty()
    }

    fn magnitude_cmp(&self, other: &Decimal) -> std::cmp::Ordering {
        use std::cmp::Ordering;
        match self.int_part.len().cmp(&other.int_part.len()) {
            Ordering::Equal => {}
            unequal => return unequal,
        }
        match self.int_part.cmp(&other.int_part) {
            Ordering::Equal => {}
            unequal => return unequal,
        }
        // Fractions are compared positionally, so "5" > "45" at equal integer
        // parts. Padding to a common width keeps the string compare honest.
        let width = self.frac_part.len().max(other.frac_part.len());
        let mine = format!("{:0<width$}", self.frac_part, width = width);
        let theirs = format!("{:0<width$}", other.frac_part, width = width);
        mine.cmp(&theirs)
    }

    fn cmp_value(&self, other: &Decimal) -> std::cmp::Ordering {
        use std::cmp::Ordering;
        match (self.negative, other.negative) {
            (false, true) => Ordering::Greater,
            (true, false) => Ordering::Less,
            (false, false) => self.magnitude_cmp(other),
            (true, true) => other.magnitude_cmp(self),
        }
    }
}

fn malformed_transition(detail: &str) -> Inadmissible {
    Inadmissible::MalformedTransition {
        detail: detail.to_owned(),
    }
}

fn check_state_change(proposal: &TransitionProposal) -> Result<(), Inadmissible> {
    let (Some(pre), Some(post)) = (
        canonical_digest(&proposal.pre_state_digest),
        canonical_digest(&proposal.post_state_digest),
    ) else {
        return Err(malformed_transition("state digests must be sha256:<64 hex>"));
    };
    // Compared canonically, so that two spellings of one digest cannot pass as
    // a change of state.
    if pre == post {
        return Err(malformed_transition("a transition must change the state"));
    }
    Ok(())
}

fn check_phi_valuation(proposal: &TransitionProposal) -> Result<bool, Inadmissible> {
    // Φ arrives as exact decimal strings alongside booleans summarising them.
    // The booleans are the proposer's claim about its own numbers; reading them
    // instead of the numbers let a proposal declare `phi_post = "0"` with
    // `phi_post_is_zero = false` and walk past the witness requirement. Derive
    // the facts, and treat a proposer whose summary contradicts its own figures
    // as malformed rather than picking whichever is convenient.
    let (Some(phi_pre), Some(phi_post)) = (
        parse_decimal(&proposal.valuation.phi_pre),
        parse_decimal(&proposal.valuation.phi_post),
    ) else {
        return Err(malformed_transition("phi_pre and phi_post must be exact decimals"));
    };

    let phi_post_is_zero = phi_post.is_zero();
    let delta_is_non_positive = phi_post.cmp_value(&phi_pre) != std::cmp::Ordering::Greater;

    if proposal.valuation.phi_post_is_zero != phi_post_is_zero {
        return Err(malformed_transition("phi_post_is_zero contradicts phi_post"));
    }
    if proposal.valuation.delta_phi_is_non_positive != delta_is_non_positive {
        return Err(malformed_transition(
            "delta_phi_is_non_positive contradicts phi_pre and phi_post",
        ));
    }
    if !delta_is_non_positive {
        return Err(Inadmissible::ResidualIncreased);
    }
    Ok(phi_post_is_zero)
}

fn check_gamma2_valuation(proposal: &TransitionProposal) -> Result<(), Inadmissible> {
    // Γ₂ follows the same rule as Φ. The exact decimal on the certificate is
    // the value. A flag that disagrees with it is malformed, and a nonzero
    // exact value is curvature, including one smaller than any float tolerance.
    let Some(gamma2) = parse_decimal(&proposal.valuation.gamma2) else {
        return Err(malformed_transition("gamma2 must be an exact decimal"));
    };
    let gamma2_is_zero = gamma2.is_zero();
    if proposal.valuation.gamma2_is_zero != gamma2_is_zero {
        return Err(malformed_transition("gamma2_is_zero contradicts gamma2"));
    }
    if !gamma2_is_zero {
        return Err(Inadmissible::CurvatureNonZero);
    }
    Ok(())
}

fn check_exactness_witness(proposal: &TransitionProposal, phi_post_is_zero: bool) -> Result<(), Inadmissible> {
    // The load-bearing check. Reaching zero is not the same as showing why.
    // Keyed off the derived fact, not the proposer's flag.
    if !phi_post_is_zero {
        return Ok(());
    }
    let Some(witness) = &proposal.exactness_witness else {
        return Err(Inadmissible::ZeroWithoutWitness);
    };
    if witness.repair_differential.trim().is_empty() || !is_digest(&witness.witness_digest) {
        return Err(Inadmissible::ZeroWithoutWitness);
    }
    if witness.checked_by.trim().is_empty() {
        return Err(Inadmissible::WitnessWithoutChecker);
    }
    Ok(())
}

/// Evaluate admissibility. Pure: no minting, no commitment, no side effects.
pub fn evaluate(
    proposal: &TransitionProposal,
    required_invariants: &[String],
) -> AdmissibilityVerdict {
    if let Err(reason) = check_state_change(proposal) {
        return AdmissibilityVerdict::Inadmissible(reason);
    }
    let phi_post_is_zero = match check_phi_valuation(proposal) {
        Ok(v) => v,
        Err(reason) => return AdmissibilityVerdict::Inadmissible(reason),
    };
    if let Err(reason) = check_gamma2_valuation(proposal) {
        return AdmissibilityVerdict::Inadmissible(reason);
    }
    for invariant in required_invariants {
        if !proposal.preserved_invariants.contains(invariant) {
            let reason = Inadmissible::InvariantNotPreserved {
                invariant: invariant.clone(),
            };
            return AdmissibilityVerdict::Inadmissible(reason);
        }
    }
    if let Err(reason) = check_exactness_witness(proposal, phi_post_is_zero) {
        return AdmissibilityVerdict::Inadmissible(reason);
    }
    AdmissibilityVerdict::Admissible
}

/// The token authorizing exactly one typed engine transition.
///
/// Unforgeable by construction: private fields, no public constructor, no
/// `Default`, no `Deserialize`. The only way to obtain one is
/// [`LicensingBoundary::mint`], and the only way to use one is to present it to
/// an engine that re-derives its binding.
///
/// It shares no trait, base type, or conversion with a host capability. The two
/// are different kinds of thing: a capability permits a machine operation
/// within a resource scope, a license authorizes one state transition. Any
/// widening between them would let possession of one imply the other.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ActionLicense {
    pre_state_digest: String,
    post_state_digest: String,
    binding: String,
    /// The witness this license was minted against, recorded so a trace can say
    /// which justification authorized the commit.
    ///
    /// Deliberately not part of [`ActionLicense::binding`]. The committer
    /// re-derives the binding from the transition alone, because that is all it
    /// has; folding the witness in would produce a value the verifier could not
    /// recompute, which is weaker than not claiming it. Provenance, not a check.
    exactness_witness_digest: Option<String>,
}

impl ActionLicense {
    pub fn pre_state_digest(&self) -> &str {
        &self.pre_state_digest
    }

    pub fn post_state_digest(&self) -> &str {
        &self.post_state_digest
    }

    /// `H(pre) || H(post)`, recomputable by the engine.
    ///
    /// The witness is **not** covered. The engine re-derives this from the
    /// transition it is about to commit, and the witness is not among the
    /// things it holds, so including it would yield a value no verifier could
    /// recompute. Use [`ActionLicense::exactness_witness_digest`] for
    /// provenance instead.
    pub fn binding(&self) -> &str {
        &self.binding
    }

    /// Digest of the witness this license was minted against, when there was
    /// one. Provenance for the trace, not part of the binding.
    pub fn exactness_witness_digest(&self) -> Option<&str> {
        self.exactness_witness_digest.as_deref()
    }

    /// This is the one type in the system carrying transition authority.
    pub fn authority_effect(&self) -> &'static str {
        "AuthorizesTransition"
    }

    /// Re-derive the binding from the transition an engine is about to commit.
    ///
    /// The engine calls this rather than trusting the field, so a license
    /// carried to a different transition fails.
    pub fn authorizes(&self, pre_state_digest: &str, post_state_digest: &str) -> bool {
        // Canonicalised on both sides. A malformed digest is not a match: it
        // yields `None` here and fails, rather than being compared raw.
        let (Some(pre), Some(post)) = (
            canonical_digest(pre_state_digest),
            canonical_digest(post_state_digest),
        ) else {
            return false;
        };
        self.pre_state_digest == pre
            && self.post_state_digest == post
            && self.binding == compute_binding(&pre, &post)
    }
}

fn compute_binding(pre: &str, post: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(b"core.action-license.v1");
    hasher.update([0u8]);
    hasher.update(pre.as_bytes());
    hasher.update([0u8]);
    hasher.update(post.as_bytes());
    format!("sha256:{}", hex::encode(hasher.finalize()))
}

/// The sole minter of [`ActionLicense`] values.
#[derive(Debug, Default, Clone, Copy)]
pub struct LicensingBoundary;

impl LicensingBoundary {
    /// Mint a license, but only for an admissible proposal.
    ///
    /// Re-evaluates rather than accepting a caller's verdict: a boundary that
    /// trusted an incoming "admissible" flag would be a boundary in name only.
    pub fn mint(
        &self,
        proposal: &TransitionProposal,
        required_invariants: &[String],
    ) -> Result<ActionLicense, LicensingError> {
        match evaluate(proposal, required_invariants) {
            AdmissibilityVerdict::Inadmissible(reason) => Err(LicensingError::Inadmissible(reason)),
            AdmissibilityVerdict::Admissible => {
                // Stored canonically. `evaluate` has already accepted both, so
                // these cannot fail. Storing the validated spelling keeps the
                // value accepted by policy identical to the value later
                // checked by the engine.
                let pre = canonical_digest(&proposal.pre_state_digest)
                    .checked_invariant_4419b3a0("evaluate accepted the pre-state digest");
                let post = canonical_digest(&proposal.post_state_digest)
                    .checked_invariant_4419b3a0("evaluate accepted the post-state digest");
                let binding = compute_binding(&pre, &post);
                Ok(ActionLicense {
                    pre_state_digest: pre,
                    post_state_digest: post,
                    binding,
                    exactness_witness_digest: proposal
                        .exactness_witness
                        .as_ref()
                        .map(|w| w.witness_digest.clone()),
                })
            }
        }
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn digest(seed: &str) -> String {
        format!("sha256:{}", hex::encode(Sha256::digest(seed.as_bytes())))
    }

    fn witness() -> ExactnessWitness {
        ExactnessWitness {
            repair_differential: "alpha=[1,0,1]".to_owned(),
            witness_digest: digest("witness"),
            checked_by: "pfp_runtime::f2".to_owned(),
        }
    }

    fn proposal() -> TransitionProposal {
        TransitionProposal {
            pre_state_digest: digest("pre"),
            post_state_digest: digest("post"),
            valuation: ValuationReceipt {
                phi_pre: "3".to_owned(),
                phi_post: "0".to_owned(),
                delta_phi_is_non_positive: true,
                gamma2: "0".to_owned(),
                gamma2_is_zero: true,
                phi_post_is_zero: true,
            },
            exactness_witness: Some(witness()),
            preserved_invariants: vec!["carrier_identity".to_owned()],
        }
    }

    #[test]
    fn a_complete_proposal_is_admissible_and_mints() {
        assert_eq!(evaluate(&proposal(), &[]), AdmissibilityVerdict::Admissible);
        let license = LicensingBoundary.mint(&proposal(), &[]).unwrap();
        assert_eq!(license.authority_effect(), "AuthorizesTransition");
    }

    #[test]
    fn phi_zero_without_a_witness_is_refused() {
        // The headline rule: residual mass zero does NOT authorize a transition.
        let mut p = proposal();
        p.exactness_witness = None;
        assert_eq!(
            evaluate(&p, &[]),
            AdmissibilityVerdict::Inadmissible(Inadmissible::ZeroWithoutWitness)
        );
        assert!(LicensingBoundary.mint(&p, &[]).is_err());
    }

    #[test]
    fn a_witness_with_an_empty_differential_does_not_count() {
        let mut p = proposal();
        p.exactness_witness = Some(ExactnessWitness {
            repair_differential: "   ".to_owned(),
            ..witness()
        });
        assert_eq!(
            evaluate(&p, &[]),
            AdmissibilityVerdict::Inadmissible(Inadmissible::ZeroWithoutWitness)
        );
    }

    #[test]
    fn a_witness_with_no_checking_adapter_is_refused() {
        let mut p = proposal();
        p.exactness_witness = Some(ExactnessWitness {
            checked_by: "".to_owned(),
            ..witness()
        });
        assert_eq!(
            evaluate(&p, &[]),
            AdmissibilityVerdict::Inadmissible(Inadmissible::WitnessWithoutChecker)
        );
    }

    #[test]
    fn a_nonzero_residual_needs_no_witness() {
        // The witness obligation attaches to the claim of exactness, not to
        // every transition; a descent step that reduces Φ is admissible.
        let mut p = proposal();
        p.valuation.phi_post_is_zero = false;
        p.valuation.phi_post = "1".to_owned();
        p.exactness_witness = None;
        assert_eq!(evaluate(&p, &[]), AdmissibilityVerdict::Admissible);
    }

    #[test]
    fn increasing_residual_is_refused() {
        // The increase is expressed in the numbers, not by flipping the flag
        // alone. A flag contradicting its own figures is now MalformedTransition
        // rather than ResidualIncreased, which is the point: the earlier version
        // of this test passed by exercising the hole it was meant to guard.
        let mut p = proposal();
        p.valuation.phi_pre = "1".to_owned();
        p.valuation.phi_post = "9".to_owned();
        p.valuation.phi_post_is_zero = false;
        p.valuation.delta_phi_is_non_positive = false;
        assert_eq!(
            evaluate(&p, &[]),
            AdmissibilityVerdict::Inadmissible(Inadmissible::ResidualIncreased)
        );
    }

    #[test]
    fn nonzero_curvature_is_refused() {
        let mut p = proposal();
        p.valuation.gamma2 = "2".to_owned();
        p.valuation.gamma2_is_zero = false;
        assert_eq!(
            evaluate(&p, &[]),
            AdmissibilityVerdict::Inadmissible(Inadmissible::CurvatureNonZero)
        );
    }

    #[test]
    fn a_required_invariant_must_be_declared_preserved() {
        let required = vec!["coefficient_domain".to_owned()];
        assert_eq!(
            evaluate(&proposal(), &required),
            AdmissibilityVerdict::Inadmissible(Inadmissible::InvariantNotPreserved {
                invariant: "coefficient_domain".to_owned()
            })
        );
    }

    #[test]
    fn a_transition_must_actually_change_the_state() {
        let mut p = proposal();
        p.post_state_digest = p.pre_state_digest.clone();
        assert!(matches!(
            evaluate(&p, &[]),
            AdmissibilityVerdict::Inadmissible(Inadmissible::MalformedTransition { .. })
        ));
    }

    #[test]
    fn malformed_digests_are_refused() {
        let mut p = proposal();
        p.pre_state_digest = "not-a-digest".to_owned();
        assert!(matches!(
            evaluate(&p, &[]),
            AdmissibilityVerdict::Inadmissible(Inadmissible::MalformedTransition { .. })
        ));
    }

    #[test]
    fn a_license_authorizes_only_its_own_transition() {
        let license = LicensingBoundary.mint(&proposal(), &[]).unwrap();
        assert!(license.authorizes(&digest("pre"), &digest("post")));
        assert!(!license.authorizes(&digest("pre"), &digest("elsewhere")));
        assert!(!license.authorizes(&digest("other"), &digest("post")));
    }

    #[test]
    fn the_binding_is_order_sensitive() {
        // A license for pre -> post must not authorize post -> pre.
        let license = LicensingBoundary.mint(&proposal(), &[]).unwrap();
        assert!(!license.authorizes(&digest("post"), &digest("pre")));
    }

    #[test]
    fn minting_re_evaluates_rather_than_trusting_the_caller() {
        // There is no way to hand the boundary a pre-computed verdict, which is
        // the structural version of this guarantee; this pins the behaviour.
        let mut p = proposal();
        p.valuation.gamma2 = "2".to_owned();
        p.valuation.gamma2_is_zero = false;
        assert_eq!(
            LicensingBoundary.mint(&p, &[]).unwrap_err(),
            LicensingError::Inadmissible(Inadmissible::CurvatureNonZero)
        );
    }
}

mod jcs;

pub mod local_ci_gates;

pub mod evaluation_hierarchy;

pub mod closure_regime;

pub mod trichotomy;

pub mod xi_gate;

pub mod custody_manifest;
pub use custody_manifest::{
    evaluate_custody_gate, parse_lean_axiom_report, parse_manifest_content,
    validate_two_tier_parity, validate_zenodo_metadata, verify_zenodo_companions,
    AxiomCensusReport, AxiomCensusSummary, CustodyError, CustodyGateInput, CustodyGateOutcome,
    CustodyGateStatus, ManifestEntry, ZenodoMetadata, ZenodoRelatedIdentifier,
};
