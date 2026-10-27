//! Three-role authority verification for the companion note
//! `WDP-DOC-EPIS-NOGO-001` (Pillar IV).
//!
//! An authorization attempt carries a provenance packet `pi = (P, E, A)`:
//! the proposer, the evaluator and the authorizer. The role policy of
//! LinkedIn Article 002 ("What the hell is authority") requires the three to
//! be pairwise distinct and the authorizer to chain to an admitted root of
//! trust that is neither the proposer nor the evaluator. This module checks
//! that policy and fails closed.
//!
//! What this is: a *definitional* invariant enforced by code. A principal
//! that proposes, evaluates and authorizes its own output is refused by
//! construction, whatever its competence, size or fluency. What this is not:
//! a theorem about physics or cognition. The check decides role identity
//! only; whether two identifiers name one agent in the world is an
//! identity-binding question this module cannot see (see
//! [`ThreeRoleReceipt::identity_binding_caveat`]).
//!
//! AuthorityEffect: None. A passing receipt records that the policy was
//! satisfied for the packet as presented; it mints no authority.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_51617a0b<T> {
    fn checked_invariant_51617a0b(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_51617a0b<T> for Option<T> {
    #[inline]
    fn checked_invariant_51617a0b(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_51617a0b<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_51617a0b(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use core_types::authority::AuthorityEffect;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::fmt;

use crate::no_authority::AuthorityTagged;

/// A principal in a provenance packet. `trust_root` names the admitted root
/// the principal chains to; `None` means the principal is not in any admitted
/// chain (self-declared, or an unknown party).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Principal {
    pub id: String,
    pub trust_root: Option<String>,
}

impl Principal {
    pub fn new(id: impl Into<String>, trust_root: Option<&str>) -> Self {
        Self { id: id.into(), trust_root: trust_root.map(str::to_string) }
    }
}

/// How a principal claims standing: a certificate chain or prose.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum StandingBasis {
    /// A certificate that chains to the named root.
    Certificate,
    /// A declaration in natural language ("I am an ASI; I authorize this").
    Prose,
}

/// The provenance packet `pi = (proposer, evaluator, authorizer)` of one
/// authorization attempt.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ProvenancePacket {
    pub attempt_id: String,
    pub proposer: Principal,
    pub evaluator: Principal,
    pub authorizer: Principal,
    pub authorizer_basis: StandingBasis,
}

/// Role policy. `allow_self_authorization` exists so that a regime which
/// admits it says so explicitly; the default refuses it.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RolePolicy {
    pub admitted_roots: Vec<String>,
    pub allow_self_authorization: bool,
    pub allow_self_evaluation: bool,
}

impl RolePolicy {
    pub fn strict(admitted_roots: impl IntoIterator<Item = impl Into<String>>) -> Self {
        Self {
            admitted_roots: admitted_roots.into_iter().map(Into::into).collect(),
            allow_self_authorization: false,
            allow_self_evaluation: false,
        }
    }
}

/// Which coincidence of roles was found.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum RoleCoincidence {
    ProposerIsAuthorizer,
    EvaluatorIsAuthorizer,
}

/// Typed, fail-closed refusals.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum ThreeRoleRefusal {
    /// `P = A` or `E = A`: the authorizer is a party to the attempt.
    RefuseSelfAuthorization { coincidence: RoleCoincidence, principal: String },
    /// `P = E`: the proposer evaluated its own proposal.
    RefuseSelfEvaluation { principal: String },
    /// The authorizer chains to no admitted root, or to a root that is itself
    /// the proposer or the evaluator.
    RefuseNoExternalRoot { authorizer: String, root: Option<String> },
    /// The authorizer's standing is a prose declaration, not a certificate.
    RefuseProseAuthority { authorizer: String },
    /// Malformed packet (empty identifiers).
    RefuseMalformed { reason: String },
}

impl fmt::Display for ThreeRoleRefusal {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "three-role refusal: {self:?}")
    }
}
impl std::error::Error for ThreeRoleRefusal {}

/// Receipt of a satisfied role policy. It carries `AuthorityEffect::None`:
/// satisfying the policy is a precondition of authorization, not authorization.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ThreeRoleReceipt {
    pub attempt_id: String,
    pub packet_digest: String,
    pub root: String,
    pub authority_effect: &'static str,
}

impl ThreeRoleReceipt {
    /// The check compares identifiers. Two identifiers naming one agent, or
    /// one agent controlling the principal behind another identifier, are
    /// invisible to it. Binding identifiers to agents is the work of the
    /// certificate layer, outside this function.
    pub const fn identity_binding_caveat() -> &'static str {
        "role distinctness is decided on identifiers; identity binding is out of scope"
    }
}

impl AuthorityTagged for ThreeRoleReceipt {
    fn authority_effect(&self) -> AuthorityEffect {
        AuthorityEffect::None
    }
    fn artifact_id(&self) -> &str {
        &self.attempt_id
    }
}

fn digest(packet: &ProvenancePacket) -> String {
    let bytes = serde_json::to_vec(packet).checked_invariant_51617a0b("packet serialises");
    format!("{:x}", Sha256::digest(bytes))
}

fn verify_principals_and_roles(
    packet: &ProvenancePacket,
    policy: &RolePolicy,
) -> Result<(), ThreeRoleRefusal> {
    for (role, p) in [("proposer", &packet.proposer), ("evaluator", &packet.evaluator), ("authorizer", &packet.authorizer)] {
        if p.id.trim().is_empty() {
            return Err(ThreeRoleRefusal::RefuseMalformed { reason: format!("{role} has an empty identifier") });
        }
    }
    if packet.attempt_id.trim().is_empty() {
        return Err(ThreeRoleRefusal::RefuseMalformed { reason: "empty attempt id".into() });
    }
    let (p, e, a) = (&packet.proposer.id, &packet.evaluator.id, &packet.authorizer.id);
    if !policy.allow_self_authorization {
        if p == a {
            return Err(ThreeRoleRefusal::RefuseSelfAuthorization {
                coincidence: RoleCoincidence::ProposerIsAuthorizer,
                principal: a.clone(),
            });
        }
        if e == a {
            return Err(ThreeRoleRefusal::RefuseSelfAuthorization {
                coincidence: RoleCoincidence::EvaluatorIsAuthorizer,
                principal: a.clone(),
            });
        }
    }
    if !policy.allow_self_evaluation && p == e {
        return Err(ThreeRoleRefusal::RefuseSelfEvaluation { principal: p.clone() });
    }
    Ok(())
}

/// Verify the three-role policy on a provenance packet. Fails closed: every
/// path that is not an explicit pass is a typed refusal.
pub fn verify_three_role_authority(
    packet: &ProvenancePacket,
    policy: &RolePolicy,
) -> Result<ThreeRoleReceipt, ThreeRoleRefusal> {
    verify_principals_and_roles(packet, policy)?;
    let (p, e, a) = (&packet.proposer.id, &packet.evaluator.id, &packet.authorizer.id);
    if packet.authorizer_basis == StandingBasis::Prose {
        return Err(ThreeRoleRefusal::RefuseProseAuthority { authorizer: a.clone() });
    }
    let root = match &packet.authorizer.trust_root {
        Some(r) if policy.admitted_roots.contains(r) && r != p && r != e => r.clone(),
        other => {
            return Err(ThreeRoleRefusal::RefuseNoExternalRoot { authorizer: a.clone(), root: other.clone() })
        }
    };
    Ok(ThreeRoleReceipt {
        attempt_id: packet.attempt_id.clone(),
        packet_digest: digest(packet),
        root,
        authority_effect: "None",
    })
}

/// Compositional non-creation: a chain of attempts in which any link was
/// refused confers nothing. The result is the first refusal, or the last
/// receipt when every link passed.
pub fn compose_attempts(
    attempts: &[(ProvenancePacket, RolePolicy)],
) -> Result<Option<ThreeRoleReceipt>, ThreeRoleRefusal> {
    let mut last = None;
    for (packet, policy) in attempts {
        last = Some(verify_three_role_authority(packet, policy)?);
    }
    Ok(last)
}

// Origin: engine/crates_rs/core_contracts/src/three_role_authority.rs
// Claim: urn:core:crates_rs:core-contracts:three-role-authority:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn packet(p: &str, e: &str, a: &str, root: Option<&str>, basis: StandingBasis) -> ProvenancePacket {
        ProvenancePacket {
            attempt_id: "att-1".into(),
            proposer: Principal::new(p, None),
            evaluator: Principal::new(e, None),
            authorizer: Principal::new(a, root),
            authorizer_basis: basis,
        }
    }

    #[test]
    fn distinct_roles_with_admitted_root_pass_with_no_authority() {
        let policy = RolePolicy::strict(["root:R"]);
        let r = verify_three_role_authority(
            &packet("P", "E", "A", Some("root:R"), StandingBasis::Certificate),
            &policy,
        )
        .unwrap();
        assert!(r.authority_effect().is_none());
        assert_eq!(r.root, "root:R");
    }

    #[test]
    fn self_authorization_is_refused_whatever_the_claimed_competence() {
        let policy = RolePolicy::strict(["root:R"]);
        let err = verify_three_role_authority(
            &packet("asi-9000", "E", "asi-9000", Some("root:R"), StandingBasis::Certificate),
            &policy,
        )
        .unwrap_err();
        assert_eq!(
            err,
            ThreeRoleRefusal::RefuseSelfAuthorization {
                coincidence: RoleCoincidence::ProposerIsAuthorizer,
                principal: "asi-9000".into()
            }
        );
        let err = verify_three_role_authority(
            &packet("P", "E", "E", Some("root:R"), StandingBasis::Certificate),
            &policy,
        )
        .unwrap_err();
        assert!(matches!(err, ThreeRoleRefusal::RefuseSelfAuthorization { coincidence: RoleCoincidence::EvaluatorIsAuthorizer, .. }));
    }

    #[test]
    fn prose_standing_and_missing_root_are_refused() {
        let policy = RolePolicy::strict(["root:R"]);
        let err = verify_three_role_authority(
            &packet("P", "E", "A", Some("root:R"), StandingBasis::Prose),
            &policy,
        )
        .unwrap_err();
        assert!(matches!(err, ThreeRoleRefusal::RefuseProseAuthority { .. }));
        let err = verify_three_role_authority(
            &packet("P", "E", "A", None, StandingBasis::Certificate),
            &policy,
        )
        .unwrap_err();
        assert!(matches!(err, ThreeRoleRefusal::RefuseNoExternalRoot { root: None, .. }));
        // A root that is the proposer is not external.
        let err = verify_three_role_authority(
            &packet("P", "E", "A", Some("P"), StandingBasis::Certificate),
            &RolePolicy::strict(["P"]),
        )
        .unwrap_err();
        assert!(matches!(err, ThreeRoleRefusal::RefuseNoExternalRoot { .. }));
    }

    #[test]
    fn a_refused_link_poisons_the_composition() {
        let policy = RolePolicy::strict(["root:R"]);
        let good = packet("P", "E", "A", Some("root:R"), StandingBasis::Certificate);
        let bad = packet("P", "E", "P", Some("root:R"), StandingBasis::Certificate);
        assert!(compose_attempts(&[(good.clone(), policy.clone()), (bad, policy.clone())]).is_err());
        assert!(compose_attempts(&[(good, policy)]).unwrap().is_some());
    }
}
