//! Authority effect and level types for the Omega Tower firewall.
//!
//! # Authority Non-Construction (firewall)
//!
//! Authority is produced ONLY by terminalized finite descent through the
//! declared pipeline `Π♯`. In the canonical spine, certified authority is the
//! inhabited dependent pair
//!
//! ```text
//! Authority(x) := Σ(t : T_auth)(Π♯(x) = inl(t))
//! ```
//!
//! This module is the Rust realization of that firewall. There is **no free
//! (nullary) constructor** for certified authority: the former bare unit
//! variants `AuthorityEffect::Certified` / `AuthorityLevel::Certified` are
//! replaced by data-carrying variants whose payload is a sealed
//! [`CertifiedAuthority`] object. To obtain a `CertifiedAuthority` you must
//! present
//!
//! - `t : T_auth` — an [`AuthorityTerminal`] (the only authority-bearing
//!   terminals; naming a terminal is not authority); and
//! - `p` — a [`DescentWitness`] binding `t`, the replayed descent reference,
//!   and a non-empty replay hash.
//!
//! See `proof_obligations.md` (SG-AUTH-001 / "Authority Non-Construction
//! Theorem") for the proof. Note the **located, not eliminated** trust base:
//! this module enforces that a witness of the required *shape* is present; it
//! does not (and within `omega_types` cannot) prove that `replay_hash`
//! corresponds to a genuine recomputation. That semantic guarantee is the
//! responsibility of the replay/verification boundary that calls
//! [`DescentWitness::from_verified_replay`], and is exactly the
//! ASSUMED-LOAD-BEARING C4 verifier-soundness axiom (proof_obligations.md
//! audit item #11).

use serde::{Deserialize, Serialize};

use crate::fda::{derive_guards, GuardEvidence};
use thiserror::Error;

/// How strongly an artifact's claim has been witnessed.
///
/// This is evidence only. In particular, neither an algebraic witness nor a
/// cryptographic authentication grants normative or release authority.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum EvidenceStatus {
    Unwitnessed,
    Tested,
    AlgebraicallyWitnessed,
    CryptographicallyAuthenticated,
}

/// The normative role an artifact is permitted to play.
///
/// This dimension is deliberately independent from [`EvidenceStatus`] and
/// [`OperationalEffect`]. Strong evidence can still be only a proposal.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum NormativeEffect {
    Proposal,
    Evaluation,
    AuthorizationRequest,
    Authorized,
    Refused,
    Terminalized,
}

/// The concrete operational side effect associated with an action.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum OperationalEffect {
    Read,
    Write,
    NetworkCall,
    ChargeAttempt,
    QuarantineMove,
    CapabilityChange,
    PublicationProposal,
}

/// Implementation progress, kept separate from evidence and authority.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum ImplementationState {
    Planned,
    Implemented,
    Verified,
}

/// Release posture for an artifact.
///
/// There is intentionally no freely constructible `Authorized` variant. A
/// host-controlled release path may require admission, but algebraic evidence
/// cannot represent or mint that admission.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum ReleaseAuthority {
    NotGranted,
    HostAdmissionRequired,
}

/// `T_auth`: the authority-bearing terminal statuses.
///
/// Naming a terminal is **not** authority, so this enum is freely
/// constructible and deserializable. It is the first component `t` of the
/// dependent pair `Σ(t:T_auth)(Π♯(x)=inl(t))`. Only these two terminals may
/// ever carry certified authority; every other terminal status maps to a
/// non-authority level.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum AuthorityTerminal {
    ExactRuleDerived,
    UniqueOutputDerived,
}

/// Refusal returned when a certification attempt lacks a valid descent witness.
///
/// A refusal carries no authority, so it is freely constructible. Implements
/// `Display` (via `thiserror`) so it can serve as the `TryFrom` error in the
/// gated `#[serde(try_from = ...)]` deserialization paths below.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Error)]
pub enum AuthorityRefusal {
    /// The replay hash was empty: no finite-replay evidence of `Π♯(x)=inl(t)`.
    #[error("empty replay hash: no finite-replay evidence of terminalization")]
    EmptyReplayHash,
    /// The descent reference was empty: nothing identifies what was replayed.
    #[error("empty descent reference: nothing identifies the replayed descent")]
    EmptyDescentRef,
    /// The witness terminal did not match the terminal being certified.
    #[error("terminal mismatch: witness terminal does not match the certified terminal")]
    TerminalMismatch,
    /// The supplied terminal status is not authority-bearing (not in `T_auth`).
    #[error("terminal is not authority-bearing: cannot be certified")]
    NotAuthorityBearing,
    /// The `IsAuth(t)` seven-guard predicate did not hold (some guard was false).
    #[error("IsAuth guards unsatisfied: the seven-guard predicate did not hold")]
    GuardsUnsatisfied,
}

/// Descent witness `p`: finite-replay evidence that `Π♯(x)` terminalized at
/// `inl(t)`.
///
/// This is the second component of the dependent pair. Its fields are
/// **private**: there is no struct-literal constructor outside this module, and
/// `#[serde(try_from = "RawDescentWitness")]` routes deserialization through the
/// same validating constructor, so JSON cannot fabricate one (a derived
/// `Deserialize` would populate the private fields directly and bypass the
/// gate — that is why deserialization is gated, not derived).
///
/// The sole constructor is [`DescentWitness::from_verified_replay`], the API the
/// replay/verification boundary calls after a genuine recomputation.
// `Deserialize` is derived together with `#[serde(try_from)]`: serde generates
// `deserialize` as "deserialize RawDescentWitness, then `TryFrom`", so the
// private fields are NEVER populated directly from the wire. Deriving
// `Deserialize` WITHOUT `try_from` would expand in-module and set the private
// fields directly, bypassing the gate — that is the footgun this avoids.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(try_from = "RawDescentWitness")]
pub struct DescentWitness {
    terminal: AuthorityTerminal,
    descent_ref: String,
    replay_hash: String,
}

impl DescentWitness {
    /// Sole constructor for a descent witness. Intended to be called by the
    /// replay/verification boundary after a genuine recomputation of `Π♯`
    /// produced `replay_hash` for `descent_ref` ending at `terminal`.
    ///
    /// Returns `Err` if either the descent reference or the replay hash is
    /// empty. (The `terminal` is statically constrained to `T_auth` by the
    /// [`AuthorityTerminal`] type.)
    pub fn from_verified_replay(
        terminal: AuthorityTerminal,
        descent_ref: impl Into<String>,
        replay_hash: impl Into<String>,
    ) -> Result<Self, AuthorityRefusal> {
        let descent_ref = descent_ref.into();
        let replay_hash = replay_hash.into();
        if descent_ref.trim().is_empty() {
            return Err(AuthorityRefusal::EmptyDescentRef);
        }
        if replay_hash.trim().is_empty() {
            return Err(AuthorityRefusal::EmptyReplayHash);
        }
        Ok(Self {
            terminal,
            descent_ref,
            replay_hash,
        })
    }

    pub fn terminal(&self) -> AuthorityTerminal {
        self.terminal
    }

    pub fn descent_ref(&self) -> &str {
        &self.descent_ref
    }

    pub fn replay_hash(&self) -> &str {
        &self.replay_hash
    }
}

/// Deserialization transport for [`DescentWitness`]. Public fields make it
/// freely deserializable, but the only way it yields a `DescentWitness` is the
/// `TryFrom` impl, which routes through the validating constructor.
#[derive(Deserialize)]
struct RawDescentWitness {
    terminal: AuthorityTerminal,
    descent_ref: String,
    replay_hash: String,
}

impl TryFrom<RawDescentWitness> for DescentWitness {
    type Error = AuthorityRefusal;

    fn try_from(raw: RawDescentWitness) -> Result<Self, Self::Error> {
        DescentWitness::from_verified_replay(raw.terminal, raw.descent_ref, raw.replay_hash)
    }
}

/// `CertifiedAuthority`: the inhabited dependent pair `Σ(t:T_auth)(Π♯(x)=inl(t))`.
///
/// The private fields [`DescentWitness`] and [`IsAuth`] (both sealed) mean there is
/// **no struct-literal constructor outside this module**, and
/// `#[serde(try_from = "RawCertifiedAuthority")]` means there is **no
/// deserialization bypass**. The sole producer is [`CertifiedAuthority::certify`].
// Gated `Deserialize` (see `DescentWitness`): routes through
// `RawCertifiedAuthority` + `TryFrom`, never populating the private field.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(try_from = "RawCertifiedAuthority")]
pub struct CertifiedAuthority {
    witness: DescentWitness,
    is_auth: IsAuth,
}

impl CertifiedAuthority {
    /// Sole constructor. Consumes the descent witness `p` and admissibility token `is_auth`.
    /// Returns `Err` unless both the witness's terminal and the `is_auth` terminal match
    /// the `terminal` being certified.
    ///
    /// There is no path to a `CertifiedAuthority` that does not present a
    /// `DescentWitness` and an `IsAuth` token.
    pub fn certify(
        terminal: AuthorityTerminal,
        witness: DescentWitness,
        is_auth: IsAuth,
    ) -> Result<Self, AuthorityRefusal> {
        if witness.terminal() != terminal {
            return Err(AuthorityRefusal::TerminalMismatch);
        }
        if is_auth.terminal() != terminal {
            return Err(AuthorityRefusal::TerminalMismatch);
        }
        Ok(Self { witness, is_auth })
    }

    pub fn terminal(&self) -> AuthorityTerminal {
        self.witness.terminal()
    }

    pub fn witness(&self) -> &DescentWitness {
        &self.witness
    }

    pub fn is_auth(&self) -> &IsAuth {
        &self.is_auth
    }
}

/// Deserialization transport for [`CertifiedAuthority`]. The inner
/// `DescentWitness` is itself gated, so a forged certified-authority JSON with
/// an empty replay hash fails to deserialize at the inner witness gate.
#[derive(Deserialize)]
struct RawCertifiedAuthority {
    witness: DescentWitness,
    is_auth: Option<IsAuth>,
}

impl TryFrom<RawCertifiedAuthority> for CertifiedAuthority {
    type Error = AuthorityRefusal;

    fn try_from(raw: RawCertifiedAuthority) -> Result<Self, Self::Error> {
        let terminal = raw.witness.terminal();
        let is_auth = raw.is_auth.ok_or(AuthorityRefusal::GuardsUnsatisfied)?;
        CertifiedAuthority::certify(terminal, raw.witness, is_auth)
    }
}

/// Authority effect tag for an artifact.
///
/// The `Certified` case carries an unforgeable [`CertifiedAuthority`]; there is
/// no bare `Certified` token. `None` means the artifact carries no authority
/// (the safe default for diagnostics, proposals, and LLM output).
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum AuthorityEffect {
    None,
    Certified(CertifiedAuthority),
    Refused,
    Uncertified,
}

impl AuthorityEffect {
    pub fn is_none(&self) -> bool {
        matches!(self, Self::None)
    }

    pub fn is_certified(&self) -> bool {
        matches!(self, Self::Certified(_))
    }

    /// Projection onto the canonical authority-strength lattice
    /// ([`crate::authority_lattice::AuthorityEffectLevel`]). This is the
    /// same-crate demonstration of the STORY-108-004 ADR mapping: the
    /// firewall's payload-carrying effect tag has a well-defined strength level.
    pub fn level(&self) -> crate::authority_lattice::AuthorityEffectLevel {
        use crate::authority_lattice::AuthorityEffectLevel as L;
        match self {
            Self::None => L::None,
            Self::Certified(_) => L::Certified,
            Self::Refused => L::Refused,
            Self::Uncertified => L::Uncertified,
        }
    }
}

/// Authority level produced by terminalization.
///
/// `Certifiable` is the level of an authority-bearing terminal **before** a
/// descent witness has been supplied: the terminal tag alone is not authority.
/// `Certified` carries the unforgeable [`CertifiedAuthority`] obtained once the
/// witness is present.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum AuthorityLevel {
    Certified(CertifiedAuthority),
    Certifiable,
    Refused,
    Uncertified,
}

impl AuthorityLevel {
    pub fn is_certified(&self) -> bool {
        matches!(self, Self::Certified(_))
    }
}

// ── Encode-Decode Firewall (PO-D6) ──────────────────────────────────────────
//
// The pipeline coproduct `T + F`. The canonical firewall is coproduct
// disjointness: `inr(φ) ≠ inl(t)`, hence
// `Σ(t:T_auth)(inr(φ)=inl(t)) ≃ ∅`. In Rust this disjointness is a *language
// guarantee*: a value of the `Outcome` enum is `Terminal(_)` XOR `Refused(_)` —
// it can never be both, and the arms cannot be confused (the Rust analogue
// of HoTT `Sum.noConfusion` / the encode-decode `Code(inr,inl)=0`). With the
// three-way partition `T = T_auth ⊔ T_scoped_neg`, the same disjointness holds
// across all three `Outcome` arms. The operational realization is
// `authority_from_outcome_f13`: only `Terminal`
// (`T_auth`) can project to an `AuthorityTerminal`; scoped negatives and every
// refusal source yield `None`, regardless of any witness.

/// The `inr(φ)` side of `T + F`: the sources the firewall keeps OUT of
/// authority. No value of this type can be converted to a [`CertifiedAuthority`]
/// — there is deliberately **no** `From<RefusalSource> for CertifiedAuthority`,
/// no `From<RefusalSource> for AuthorityTerminal`, and no other producer (the
/// sole producer of authority remains `CertifiedAuthority::certify`, PO-AUTH-NC).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum RefusalSource {
    /// A typed refusal (`Refused`, `ParseRefused`, …).
    Refusal,
    /// A repairable obstruction (CODA-FOC Exact/Survivor; `RepairRequired`).
    Repair,
    /// Resolution requires an external oracle / exceeds the evidence ceiling.
    OracleNeeded,
    /// A finite curvature-ledger (BCDL) residue — implementation scaffolding,
    /// never foundation (PO-D22).
    CurvatureLedger,
    /// A CODA-A residual-closure residue (Anomalon); classifies, never authorizes.
    Residual,
    /// Refusal Calculus Gate: Graph-only topology changes when \Phi_1 > 0.
    /// Blocks pure-graph solutions without higher-dimensional cell injection.
    NoLiftFound,
}

/// `T_scoped_neg`: the scoped-negative terminal statuses — **verified local
/// absence**, NOT global falsity and NOT a refusal.
///
/// Per the canonical terminal partition `T = T_auth ⊔ T_scoped_neg`
/// (`canonical_omega_math_spine.md`), scoped negatives are a **separate** terminal
/// class from [`AuthorityTerminal`]: the `Π♯` descent genuinely halted with a
/// verified negative result. They are terminals (not refusals), but they are
/// **not** authority-bearing — naming one is never authority, and there is no
/// producer of [`CertifiedAuthority`] from this type.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum ScopedNegativeTerminal {
    /// `NoRule` — local verified absence of an applicable rule (NOT global
    /// falsity). The canonical scoped-negative terminal (CODA-FDA terminal table).
    NoRule,
}

/// Living CODA-A 5-case residual taxonomy (CODA_GTLA-01).
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum ResidualTerminal {
    ClosureAbsorbed,
    ClosedResidual,
    OpenResidual,
    LiftRequired,
    RefusedClosure,
}

impl ResidualTerminal {
    /// True strictly for `ClosedResidual` (the Anomalon terminal).
    pub fn is_anomalon(&self) -> bool {
        matches!(self, ResidualTerminal::ClosedResidual)
    }
}

/// Pipeline outcome: the partition `P → T ⊔ F` with `T = T_auth ⊔ T_scoped_neg ⊔ T_res`.
///
/// - `Terminal(t)` is `inl(t)` — an authority-bearing terminal (`T_auth`); still
///   requires a descent witness to certify (PO-AUTH-NC).
/// - `ScopedNegative(s)` is a verified-local-absence terminal (`T_scoped_neg`):
///   a genuine terminal that is **not** a refusal and **not** authority-bearing.
/// - `Residual(r)` is a typed residual closure terminal (`T_res`):
///   a genuine terminal from the CODA-A taxonomy that is **not** authority-bearing.
/// - `Refused(φ)` is `inr(φ)` — the `F` side.
///
/// Authority arises **only** from the `Terminal` arm: `authority_terminal()`
/// returns `Some` for `Terminal` and `None` for `ScopedNegative`, `Residual`, and
/// `Refused`, so neither scoped negatives, residuals, nor refusals can ever become authority.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum Outcome {
    Terminal(AuthorityTerminal),
    ScopedNegative(ScopedNegativeTerminal),
    Residual(ResidualTerminal),
    Refused(RefusalSource),
}

impl Outcome {
    /// `T_auth` projection. `Some(t)` **only** on the `Terminal` branch;
    /// `ScopedNegative`, `Residual`, and `Refused` yield `None`. This keeps authority confined
    /// to the authority-bearing terminal class: a scoped negative or residual is a real
    /// terminal but produces no `AuthorityTerminal`, and a refusal never does either.
    pub fn authority_terminal(&self) -> Option<AuthorityTerminal> {
        match self {
            Outcome::Terminal(t) => Some(*t),
            Outcome::ScopedNegative(_) => None,
            Outcome::Residual(_) => None,
            Outcome::Refused(_) => None,
        }
    }

    /// True only for the `F` side. A scoped negative or residual is a verified terminal, **not**
    /// a refusal, so this returns `false` for `ScopedNegative` and `Residual` (the distinction
    /// F11/AUTH-006 requires: verified local absence is not conflated with refusal).
    pub fn is_refused(&self) -> bool {
        matches!(self, Outcome::Refused(_))
    }

    /// True only for the scoped-negative terminal class (`T_scoped_neg`).
    pub fn is_scoped_negative(&self) -> bool {
        matches!(self, Outcome::ScopedNegative(_))
    }

    /// `T_scoped_neg` projection: `Some(s)` only on the `ScopedNegative` branch.
    pub fn scoped_negative(&self) -> Option<ScopedNegativeTerminal> {
        match self {
            Outcome::ScopedNegative(s) => Some(*s),
            _ => None,
        }
    }

    /// True only for the residual terminal class (`T_res`).
    pub fn is_residual(&self) -> bool {
        matches!(self, Outcome::Residual(_))
    }

    /// `T_res` projection: `Some(r)` only on the `Residual` branch.
    pub fn residual(&self) -> Option<ResidualTerminal> {
        match self {
            Outcome::Residual(r) => Some(*r),
            _ => None,
        }
    }
}

// ── F13: the decidable `IsAuth(t)` predicate ─────────────────────────────────
//
// `IsAuth(t) := acc ∧ det ∧ (Φ* = 0) ∧ Exh ∧ skel ∧ ¬lift ∧ ¬refuse`
//
// The seven-guard predicate evaluated at the descent halt (spine F13 /
// AUTH-013–015). It is the decidable *admissibility* check that was previously
// only presupposed by `DescentWitness` (a post-hoc certificate). It does NOT
// itself grant authority — the dependent pair (terminal + descent witness) is
// unchanged — but on the F13 path authority may not be admitted without it.

/// The seven decidable guards of the `IsAuth(t)` predicate (F13). Each field is
/// `true` exactly when its guard is satisfied; `no_lift` is `¬lift` (no lifting
/// obligation remains) and `no_refuse` is `¬refuse` (the halt is not a refusal).
///
/// Freely constructible: the guards are observations at the halt, not authority.
/// Authority arises only when ALL seven hold *and* a descent witness is present.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct AuthorityGuards {
    /// `acc` — the halt is accessible.
    pub accessible: bool,
    /// `det` — the descent is deterministic.
    pub deterministic: bool,
    /// `Φ* = 0` — the obstruction class vanishes.
    pub obstruction_vanishes: bool,
    /// `Exh` — the search was exhaustive.
    pub exhaustive: bool,
    /// `skel` — the result is skeletal (no redundant structure).
    pub skeletal: bool,
    /// `¬lift` — no lifting obligation remains.
    pub no_lift: bool,
    /// `¬refuse` — the halt is not a refusal.
    pub no_refuse: bool,
}

impl AuthorityGuards {
    /// The decidable body of `IsAuth(t)`: the conjunction of all seven guards.
    /// There is no partial-credit path — a single false guard fails the predicate.
    pub fn all_hold(&self) -> bool {
        self.accessible
            && self.deterministic
            && self.obstruction_vanishes
            && self.exhaustive
            && self.skeletal
            && self.no_lift
            && self.no_refuse
    }
}

/// `IsAuth(t)` (F13): a sealed token witnessing that the seven guards held for
/// `terminal` at the descent halt, derived from typed evidence.
///
/// There is **no struct-literal constructor outside this module** (private
/// fields) and **no deserialization bypass** (`#[serde(try_from)]` routes through
/// [`IsAuth::decide`]). The sole producer is [`IsAuth::decide`], which yields
/// `Some` only when every guard derived from typed [`GuardEvidence`] holds.
/// Possessing an `IsAuth` is decidable evidence that `IsAuth(terminal)` evaluated true.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(try_from = "RawIsAuth")]
pub struct IsAuth {
    terminal: AuthorityTerminal,
    guards: AuthorityGuards,
    evidence: GuardEvidence,
}

impl IsAuth {
    /// Sole constructor. Decides `IsAuth(terminal)`: computes the seven guards
    /// from typed evidence. Returns `Some` iff all seven derived guards hold.
    pub fn decide(terminal: AuthorityTerminal, evidence: GuardEvidence) -> Option<IsAuth> {
        let guards = derive_guards(&evidence);
        if guards.all_hold() {
            Some(IsAuth {
                terminal,
                guards,
                evidence,
            })
        } else {
            None
        }
    }

    pub fn terminal(&self) -> AuthorityTerminal {
        self.terminal
    }

    pub fn guards(&self) -> AuthorityGuards {
        self.guards
    }

    pub fn evidence(&self) -> &GuardEvidence {
        &self.evidence
    }
}

/// Deserialization transport for [`IsAuth`]. Public fields make it freely
/// deserializable, but the only way it yields an `IsAuth` is the `TryFrom` impl,
/// which re-derives the guards from the typed evidence and refuses on any mismatch
/// or unsatisfied guard.
#[derive(Deserialize)]
struct RawIsAuth {
    terminal: AuthorityTerminal,
    guards: AuthorityGuards,
    evidence: GuardEvidence,
}

impl TryFrom<RawIsAuth> for IsAuth {
    type Error = AuthorityRefusal;

    fn try_from(raw: RawIsAuth) -> Result<Self, Self::Error> {
        let derived = derive_guards(&raw.evidence);
        if derived != raw.guards || !derived.all_hold() {
            return Err(AuthorityRefusal::GuardsUnsatisfied);
        }
        Ok(IsAuth {
            terminal: raw.terminal,
            guards: derived,
            evidence: raw.evidence,
        })
    }
}

/// The only bridge from a pipeline outcome to certified authority. It requires
/// a decided [`IsAuth`] token whose terminal matches the outcome's terminal.
/// Authority is admitted only when ALL of:
///
/// - the outcome is `Terminal(t)` (every refusal source yields `None`);
/// - `IsAuth(t)` was decided true (the seven guards) and its terminal matches;
/// - a descent witness `p` certifies `t`.
///
/// This adds the decidable predicate *in front of* the existing dependent pair;
/// it introduces **no new free path** to [`CertifiedAuthority`] (the sole
/// producer remains `CertifiedAuthority::certify`, PO-AUTH-NC).
pub fn authority_from_outcome_f13(
    outcome: Outcome,
    witness: Option<DescentWitness>,
    is_auth: Option<IsAuth>,
) -> Option<CertifiedAuthority> {
    let terminal = outcome.authority_terminal()?; // None for every RefusalSource
    let is_auth = is_auth?; // F13: no admissibility predicate ⇒ no authority
    if is_auth.terminal() != terminal {
        return None; // the predicate was decided for a different terminal
    }
    let witness = witness?;
    CertifiedAuthority::certify(terminal, witness, is_auth).ok()
}

// Origin: omega_engine/crates_rs/omega_types/src/authority.rs
// Claim: urn:omega:crates_rs:omega-types:authority:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn valid_witness() -> DescentWitness {
        DescentWitness::from_verified_replay(
            AuthorityTerminal::ExactRuleDerived,
            "descent:row-1",
            "blake3:deadbeef",
        )
        .expect("nonempty refs produce a witness")
    }

    fn valid_evidence() -> GuardEvidence {
        GuardEvidence::new_valid(["cand_01"], "K_carrier_01", "blake3:deadbeef")
    }

    fn valid_is_auth() -> IsAuth {
        IsAuth::decide(AuthorityTerminal::ExactRuleDerived, valid_evidence())
            .expect("valid evidence")
    }

    #[test]
    fn certify_requires_nonempty_replay_hash() {
        let err = DescentWitness::from_verified_replay(
            AuthorityTerminal::ExactRuleDerived,
            "descent:row-1",
            "",
        )
        .unwrap_err();
        assert_eq!(err, AuthorityRefusal::EmptyReplayHash);

        let err_space = DescentWitness::from_verified_replay(
            AuthorityTerminal::ExactRuleDerived,
            "descent:row-1",
            "   ",
        )
        .unwrap_err();
        assert_eq!(err_space, AuthorityRefusal::EmptyReplayHash);
    }

    #[test]
    fn certify_requires_nonempty_descent_ref() {
        let err = DescentWitness::from_verified_replay(
            AuthorityTerminal::ExactRuleDerived,
            "",
            "blake3:deadbeef",
        )
        .unwrap_err();
        assert_eq!(err, AuthorityRefusal::EmptyDescentRef);

        let err_space = DescentWitness::from_verified_replay(
            AuthorityTerminal::ExactRuleDerived,
            "   ",
            "blake3:deadbeef",
        )
        .unwrap_err();
        assert_eq!(err_space, AuthorityRefusal::EmptyDescentRef);
    }

    #[test]
    fn certify_rejects_terminal_mismatch() {
        let witness = valid_witness(); // terminal = ExactRuleDerived
        let is_auth = valid_is_auth();

        // 1) Test witness terminal mismatch
        let wrong_witness = DescentWitness::from_verified_replay(
            AuthorityTerminal::UniqueOutputDerived,
            "descent:row-2",
            "blake3:deadbeef",
        )
        .unwrap();
        let err = CertifiedAuthority::certify(
            AuthorityTerminal::ExactRuleDerived,
            wrong_witness,
            is_auth,
        )
        .unwrap_err();
        assert_eq!(err, AuthorityRefusal::TerminalMismatch);

        // 2) Test is_auth terminal mismatch
        let wrong_auth =
            IsAuth::decide(AuthorityTerminal::UniqueOutputDerived, valid_evidence()).unwrap();
        let err2 =
            CertifiedAuthority::certify(AuthorityTerminal::ExactRuleDerived, witness, wrong_auth)
                .unwrap_err();
        assert_eq!(err2, AuthorityRefusal::TerminalMismatch);
    }

    #[test]
    fn certify_accepts_matching_witness() {
        let witness = valid_witness();
        let is_auth = valid_is_auth();
        let ca = CertifiedAuthority::certify(AuthorityTerminal::ExactRuleDerived, witness, is_auth)
            .expect("matching terminal certifies");
        assert_eq!(ca.terminal(), AuthorityTerminal::ExactRuleDerived);
        assert_eq!(ca.witness().replay_hash(), "blake3:deadbeef");
    }

    #[test]
    fn certified_effect_requires_a_certified_authority() {
        let ca = CertifiedAuthority::certify(
            AuthorityTerminal::ExactRuleDerived,
            valid_witness(),
            valid_is_auth(),
        )
        .unwrap();
        let effect = AuthorityEffect::Certified(ca);
        assert!(!effect.is_none());
        assert!(effect.is_certified());
        assert!(AuthorityEffect::None.is_none());
        assert!(!AuthorityEffect::Refused.is_none());
        assert!(!AuthorityEffect::Uncertified.is_none());
    }

    #[test]
    fn forged_certified_json_with_empty_hash_fails_to_deserialize() {
        // A genuine certified authority round-trips.
        let ca = CertifiedAuthority::certify(
            AuthorityTerminal::ExactRuleDerived,
            valid_witness(),
            valid_is_auth(),
        )
        .unwrap();
        let json = serde_json::to_string(&ca).unwrap();
        let back: CertifiedAuthority = serde_json::from_str(&json).unwrap();
        assert_eq!(back, ca);

        // A forged payload with an empty replay hash is rejected at the gate,
        // even though every field name is present.
        let forged = r#"{"witness":{"terminal":"ExactRuleDerived","descent_ref":"descent:row-1","replay_hash":""}}"#;
        let result: Result<CertifiedAuthority, _> = serde_json::from_str(forged);
        assert!(
            result.is_err(),
            "forged certified authority with empty replay hash must not deserialize"
        );

        // A forged payload with whitespace replay hash fails deserialization.
        let forged_whitespace = r#"{"witness":{"terminal":"ExactRuleDerived","descent_ref":"descent:row-1","replay_hash":"   "}}"#;
        let result_ws: Result<CertifiedAuthority, _> = serde_json::from_str(forged_whitespace);
        assert!(
            result_ws.is_err(),
            "forged certified authority with whitespace replay hash must not deserialize"
        );
    }

    #[test]
    fn forged_certified_json_omitting_is_auth_fails_to_deserialize() {
        // Regression lock for the `raw.is_auth.ok_or(GuardsUnsatisfied)?` gate (F13 / AC-1):
        // a payload whose witness is SHAPE-VALID (non-empty descent_ref + replay_hash) but
        // which OMITS `is_auth` must refuse — the admissibility token may not be silently
        // synthesized. The empty-hash forgeries above would pass even if this gate were
        // removed (the witness gate fires first); this payload PASSES the witness gate, so
        // it is the only test that actually exercises the omitted-`is_auth` path.
        let forged = r#"{"witness":{"terminal":"ExactRuleDerived","descent_ref":"descent:row-1","replay_hash":"blake3:deadbeef"}}"#;
        let result: Result<CertifiedAuthority, _> = serde_json::from_str(forged);
        assert!(
            result.is_err(),
            "omitting is_auth must refuse, not synthesize all-seven-guards-true"
        );
    }

    #[test]
    fn forged_witness_json_with_empty_hash_fails_to_deserialize() {
        let forged = r#"{"terminal":"UniqueOutputDerived","descent_ref":"d","replay_hash":""}"#;
        let result: Result<DescentWitness, _> = serde_json::from_str(forged);
        assert!(
            result.is_err(),
            "forged witness with empty hash must not deserialize"
        );

        let forged_ws =
            r#"{"terminal":"UniqueOutputDerived","descent_ref":"d","replay_hash":"   "}"#;
        let result_ws: Result<DescentWitness, _> = serde_json::from_str(forged_ws);
        assert!(
            result_ws.is_err(),
            "forged witness with whitespace hash must not deserialize"
        );
    }

    // ── Encode-Decode Firewall (PO-D6) tests ────────────────────────────────

    const ALL_REFUSAL_SOURCES: [RefusalSource; 5] = [
        RefusalSource::Refusal,
        RefusalSource::Repair,
        RefusalSource::OracleNeeded,
        RefusalSource::CurvatureLedger,
        RefusalSource::Residual,
    ];

    #[test]
    fn refusal_outcome_never_yields_a_terminal() {
        for src in ALL_REFUSAL_SOURCES {
            assert!(Outcome::Refused(src).authority_terminal().is_none());
            assert!(Outcome::Refused(src).is_refused());
        }
        assert_eq!(
            Outcome::Terminal(AuthorityTerminal::ExactRuleDerived).authority_terminal(),
            Some(AuthorityTerminal::ExactRuleDerived)
        );
    }

    #[test]
    fn refusal_plus_valid_witness_is_still_not_authority() {
        // The firewall: inr(φ) ≠ inl(t). Even with a genuine descent witness in
        // hand, NO refusal source converts to certified authority.
        let is_auth = valid_is_auth();
        for src in ALL_REFUSAL_SOURCES {
            let got = authority_from_outcome_f13(
                Outcome::Refused(src),
                Some(valid_witness()),
                Some(is_auth.clone()),
            );
            assert!(
                got.is_none(),
                "RefusalSource::{src:?} must not produce authority even with a valid witness"
            );
        }
    }

    #[test]
    fn terminal_needs_a_witness_to_become_authority() {
        let t = Outcome::Terminal(AuthorityTerminal::ExactRuleDerived);
        let is_auth = valid_is_auth();
        // inl(t) without the descent proof p: not yet authority.
        assert!(authority_from_outcome_f13(t, None, Some(is_auth.clone())).is_none());
        // inl(t) with a matching descent witness p: certified.
        let ca = authority_from_outcome_f13(t, Some(valid_witness()), Some(is_auth))
            .expect("t + p certifies");
        assert_eq!(ca.terminal(), AuthorityTerminal::ExactRuleDerived);
    }

    // ── F13: IsAuth seven-guard predicate tests ─────────────────────────────

    #[test]
    fn is_auth_decides_true_only_when_all_seven_guards_hold() {
        // All seven hold ⇒ Some, carrying the terminal it was decided for.
        let ok = IsAuth::decide(AuthorityTerminal::ExactRuleDerived, valid_evidence())
            .expect("all seven guards ⇒ IsAuth");
        assert_eq!(ok.terminal(), AuthorityTerminal::ExactRuleDerived);
        assert!(ok.guards().all_hold());

        // Each guard failing via invalid typed evidence yields None
        let mut base = valid_evidence();
        base.execution_trace_len = 0;
        assert!(IsAuth::decide(AuthorityTerminal::ExactRuleDerived, base).is_none());

        let mut base = valid_evidence();
        base.replay_hash = "wrong".to_string();
        assert!(IsAuth::decide(AuthorityTerminal::ExactRuleDerived, base).is_none());

        let mut base = valid_evidence();
        base.residual_mass = num_rational::BigRational::from_integer(1.into());
        assert!(IsAuth::decide(AuthorityTerminal::ExactRuleDerived, base).is_none());

        let mut base = valid_evidence();
        base.checked_candidates.clear();
        assert!(IsAuth::decide(AuthorityTerminal::ExactRuleDerived, base).is_none());

        let mut base = valid_evidence();
        base.verified_carrier = "wrong".to_string();
        assert!(IsAuth::decide(AuthorityTerminal::ExactRuleDerived, base).is_none());

        let mut base = valid_evidence();
        base.pending_lifts = 1;
        assert!(IsAuth::decide(AuthorityTerminal::ExactRuleDerived, base).is_none());

        let mut base = valid_evidence();
        base.active_refusal = Some("refused".to_string());
        assert!(IsAuth::decide(AuthorityTerminal::ExactRuleDerived, base).is_none());
    }

    #[test]
    fn f13_bridge_requires_is_auth_token() {
        let t = Outcome::Terminal(AuthorityTerminal::ExactRuleDerived);
        let is_auth = valid_is_auth();

        // Terminal + witness but NO IsAuth ⇒ not authority on the F13 path.
        assert!(authority_from_outcome_f13(t, Some(valid_witness()), None).is_none());
        // Terminal + witness + decided IsAuth ⇒ certified.
        let ca = authority_from_outcome_f13(t, Some(valid_witness()), Some(is_auth))
            .expect("t + p + IsAuth(t) certifies");
        assert_eq!(ca.terminal(), AuthorityTerminal::ExactRuleDerived);
    }

    #[test]
    fn f13_bridge_needs_a_witness_even_with_is_auth() {
        let t = Outcome::Terminal(AuthorityTerminal::ExactRuleDerived);
        let is_auth = valid_is_auth();
        // IsAuth alone (no descent witness) is not authority.
        assert!(authority_from_outcome_f13(t, None, Some(is_auth)).is_none());
    }

    #[test]
    fn f13_bridge_rejects_is_auth_for_a_different_terminal() {
        // IsAuth decided for ExactRuleDerived cannot admit a UniqueOutputDerived outcome.
        let outcome = Outcome::Terminal(AuthorityTerminal::UniqueOutputDerived);
        let is_auth = valid_is_auth();
        assert!(
            authority_from_outcome_f13(outcome, Some(valid_witness()), Some(is_auth)).is_none()
        );
    }

    #[test]
    fn f13_bridge_refusal_never_authorizes_even_with_witness_and_is_auth() {
        // Firewall preserved on the F13 path: no refusal source becomes authority,
        // even with a valid witness AND a decided IsAuth in hand.
        let is_auth = valid_is_auth();
        for src in ALL_REFUSAL_SOURCES {
            let got = authority_from_outcome_f13(
                Outcome::Refused(src),
                Some(valid_witness()),
                Some(is_auth.clone()),
            );
            assert!(
                got.is_none(),
                "RefusalSource::{src:?} must not authorize on the F13 path"
            );
        }
    }

    #[test]
    fn authority_effect_projects_onto_the_canonical_lattice() {
        use crate::authority_lattice::AuthorityEffectLevel as L;
        let ca = CertifiedAuthority::certify(
            AuthorityTerminal::ExactRuleDerived,
            valid_witness(),
            valid_is_auth(),
        )
        .unwrap();
        // Each firewall effect maps to its strength level; Certified is the top.
        assert_eq!(AuthorityEffect::Certified(ca.clone()).level(), L::Certified);
        assert_eq!(AuthorityEffect::None.level(), L::None);
        assert_eq!(AuthorityEffect::Uncertified.level(), L::Uncertified);
        assert_eq!(AuthorityEffect::Refused.level(), L::Refused);
        // Strength ordering is respected: Certified is strictly the strongest.
        assert!(AuthorityEffect::Refused.level() < AuthorityEffect::None.level());
        assert!(AuthorityEffect::Uncertified.level() < AuthorityEffect::Certified(ca).level());
    }

    // ── F11/AUTH-006: four-way Outcome (T_auth ⊔ T_scoped_neg ⊔ T_res ⊔ F) tests ────

    const ALL_SCOPED_NEGATIVES: [ScopedNegativeTerminal; 1] = [ScopedNegativeTerminal::NoRule];
    const ALL_RESIDUALS: [ResidualTerminal; 5] = [
        ResidualTerminal::ClosureAbsorbed,
        ResidualTerminal::ClosedResidual,
        ResidualTerminal::OpenResidual,
        ResidualTerminal::LiftRequired,
        ResidualTerminal::RefusedClosure,
    ];

    #[test]
    fn scoped_negative_is_a_terminal_but_neither_authority_nor_refusal() {
        for s in ALL_SCOPED_NEGATIVES {
            let o = Outcome::ScopedNegative(s);
            // Not authority-bearing: no AuthorityTerminal projection.
            assert!(
                o.authority_terminal().is_none(),
                "scoped negative is not T_auth"
            );
            // Not a refusal: the F11/AUTH-006 distinction (verified absence ≠ refusal).
            assert!(!o.is_refused(), "scoped negative must NOT read as refused");
            // It IS a scoped-negative terminal, and projects to itself.
            assert!(o.is_scoped_negative());
            assert_eq!(o.scoped_negative(), Some(s));
            assert!(!o.is_residual());
        }
    }

    #[test]
    fn residual_is_a_terminal_but_neither_authority_nor_refusal() {
        for r in ALL_RESIDUALS {
            let o = Outcome::Residual(r);
            assert!(o.authority_terminal().is_none(), "residual is not T_auth");
            assert!(!o.is_refused(), "residual is not refusal");
            assert!(!o.is_scoped_negative(), "residual is not scoped negative");
            assert!(o.is_residual());
            assert_eq!(o.residual(), Some(r));
        }
    }

    #[test]
    fn the_four_arms_are_mutually_exclusive() {
        let flags = |o: &Outcome| {
            (
                o.authority_terminal().is_some(),
                o.is_refused(),
                o.is_scoped_negative(),
                o.is_residual(),
            )
        };
        let t = Outcome::Terminal(AuthorityTerminal::ExactRuleDerived);
        let s = Outcome::ScopedNegative(ScopedNegativeTerminal::NoRule);
        let r = Outcome::Residual(ResidualTerminal::ClosedResidual);
        let f = Outcome::Refused(RefusalSource::Refusal);

        // Terminal: authority-projectable, not refused, not scoped-negative, not residual.
        assert_eq!(flags(&t), (true, false, false, false));
        // ScopedNegative: not authority, not refused, IS scoped-negative, not residual.
        assert_eq!(flags(&s), (false, false, true, false));
        // Residual: not authority, not refused, not scoped-negative, IS residual.
        assert_eq!(flags(&r), (false, false, false, true));
        // Refused: not authority, IS refused, not scoped-negative, not residual.
        assert_eq!(flags(&f), (false, true, false, false));
    }

    #[test]
    fn scoped_negative_never_authorizes_even_with_witness_and_is_auth() {
        // Firewall: a scoped-negative terminal cannot become authority through
        // either bridge, even with a valid witness and a decided IsAuth in hand.
        let is_auth = valid_is_auth();
        for s in ALL_SCOPED_NEGATIVES {
            let o = Outcome::ScopedNegative(s);
            assert!(
                authority_from_outcome_f13(o, Some(valid_witness()), Some(is_auth.clone()))
                    .is_none()
            );
        }
    }

    #[test]
    fn residual_never_authorizes_even_with_witness_and_is_auth() {
        let is_auth = valid_is_auth();
        for r in ALL_RESIDUALS {
            let o = Outcome::Residual(r);
            assert!(
                authority_from_outcome_f13(o, Some(valid_witness()), Some(is_auth.clone()))
                    .is_none()
            );
        }
    }

    #[test]
    fn forged_is_auth_json_with_a_false_guard_fails_to_deserialize() {
        // A genuine IsAuth round-trips.
        let ok = valid_is_auth();
        let json = serde_json::to_string(&ok).unwrap();
        let back: IsAuth = serde_json::from_str(&json).unwrap();
        assert_eq!(back, ok);

        // Forged guards claiming true when evidence fails obstruction_vanishes
        let forged_mismatch = serde_json::json!({
            "terminal": "ExactRuleDerived",
            "guards": {
                "accessible": true,
                "deterministic": true,
                "obstruction_vanishes": true,
                "exhaustive": true,
                "skeletal": true,
                "no_lift": true,
                "no_refuse": true
            },
            "evidence": {
                "execution_trace_len": 1,
                "execution_hash": "blake3:deadbeef",
                "replay_hash": "blake3:deadbeef",
                "residual_mass": "1/2",
                "declared_candidates": ["cand_01"],
                "checked_candidates": ["cand_01"],
                "declared_carrier": "K_carrier_01",
                "verified_carrier": "K_carrier_01",
                "pending_lifts": 0,
                "active_refusal": null
            }
        });
        let result: Result<IsAuth, _> = serde_json::from_value(forged_mismatch);
        assert!(
            result.is_err(),
            "forged IsAuth with mismatched evidence must not deserialize"
        );

        // Forged token asserting IsAuth held while guards field has false
        let forged_false = serde_json::json!({
            "terminal": "ExactRuleDerived",
            "guards": {
                "accessible": true,
                "deterministic": true,
                "obstruction_vanishes": false,
                "exhaustive": true,
                "skeletal": true,
                "no_lift": true,
                "no_refuse": true
            },
            "evidence": {
                "execution_trace_len": 1,
                "execution_hash": "blake3:deadbeef",
                "replay_hash": "blake3:deadbeef",
                "residual_mass": "0",
                "declared_candidates": ["cand_01"],
                "checked_candidates": ["cand_01"],
                "declared_carrier": "K_carrier_01",
                "verified_carrier": "K_carrier_01",
                "pending_lifts": 0,
                "active_refusal": null
            }
        });
        let result: Result<IsAuth, _> = serde_json::from_value(forged_false);
        assert!(
            result.is_err(),
            "forged IsAuth with false guard must not deserialize"
        );
    }
}
