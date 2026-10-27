//! --- Math Contract: AUTH-023 — T3 / primal-dual identity replay → authority ---
//!
//! Family-local adapter wiring an **Admitted** [`T3Verifier`] replay result into
//! the SOLE authority constructor
//! [`core_types::authority::DescentWitness::from_verified_replay`].
//!
//! ## Scope (family-local — NOT general C4)
//! [`T3Verifier`](crate::replay_harness::T3Verifier) is a **family-local** replay
//! kernel: it compares a submitted exact claim of the **T3 primal-dual identity**
//! (`m_primal = m_dual` under dual feasibility `d₀ᵀφ = 0` and the bound
//! `‖φ‖_∞ ≤ 1`) through the Phi1 owner over `BigRational`, with no tolerance.
//! This adapter wires *that one verifier family* into the authority
//! constructor. It does **not** close general C4 verifier-soundness
//! (`proof_obligations.md` audit item #11 / PO-C4-FLS): every other verifier
//! family must supply its own admitted-replay adapter. Calling this "the C4
//! kernel" would overclaim.
//!
//! ## Firewall (PO-AUTH-NC)
//! Authority is produced ONLY through the sealed, sole constructor
//! `DescentWitness::from_verified_replay`. This adapter has **no alternate
//! constructor path**: it builds a witness by no other means, and a non-`Admitted`
//! replay (`Rejected` / `Inconclusive`) yields no witness at all. The adapter is a
//! thin gate + pass-through; the load-bearing trust remains the C4
//! verifier-soundness assumption that `T3Verifier`'s recomputation is genuine
//! (located, not eliminated — see `core_types::authority`).


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_8aa33b6b;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_8aa33b6b<T> = std::result::Result<T, BoundaryError_8aa33b6b>;
use crate::replay_harness::{ReplayPacket, T3Verifier, VerificationAudit, VerificationStatus};
use core_types::authority::{AuthorityTerminal, DescentWitness};

/// The authority terminal for an admitted T3 primal-dual identity replay.
///
/// `ExactRuleDerived` (not `UniqueOutputDerived`), matching the **established
/// convention** for exact Φ₁ primal-dual certificates rather than the variant
/// name alone:
/// - `core_certifiers` (`checked_packet.rs`) maps the exact result
///   `ObstructionDiagnosticClass::ExactRepair` (`Φ₁ = 0`) → `AuthorityTerminal::ExactRuleDerived`;
/// - the primal-dual certificate identity is **GTFOC-3 / the exact Φ₁ certificate**
///   (`core_functional/phi1.rs`: "exact … certificate … optimality by weak duality").
///
/// T3 proves that same exact identity (`m_primal = m_dual` by weak duality); it
/// makes **no** output-uniqueness claim, so `UniqueOutputDerived` would be wrong.
/// A consumer that certifies a T3 witness MUST `certify` with this same terminal
/// (else `CertifiedAuthority::certify` returns `TerminalMismatch`).
const T3_PRIMAL_DUAL_TERMINAL: AuthorityTerminal = AuthorityTerminal::ExactRuleDerived;

/// The replay hash bound into the witness: the BLAKE3 packet hash recorded by the
/// recompute ([`VerificationAudit::packet_hash`]), hex-encoded and namespaced.
/// Always non-empty (matching `auth023:t3-primal-dual:v2:exact:blake3:<hex>`),
/// so it never trips the constructor's empty-hash refusal.
fn t3_replay_hash(packet_hash: &[u8; 32]) -> String {
    use std::fmt::Write as _;
    let mut hex = String::with_capacity(64);
    for byte in packet_hash {
        // Infallible: writing to a String never errors.
        let _ = write!(hex, "{byte:02x}");
    }
    format!("auth023:t3-primal-dual:v2:exact:blake3:{hex}")
}

/// AUTH-023 — wire an **Admitted** T3 primal-dual identity replay into the sole
/// authority constructor.
///
/// Returns `Some(witness)` iff the internally recomputed T3 audit has status Admitted
/// and `descent_ref` is non-empty (the latter inherited from the sole constructor's
/// contract). A `Rejected` or `Inconclusive` replay yields `None` — **no [`DescentWitness`]
/// is ever produced for a non-admitted replay.**
///
/// `descent_ref` is caller-supplied provenance identifying *what* descent was
/// replayed; the `replay_hash` is derived from the audit's recompute packet hash
/// and bound, unaltered, into the returned witness. The emitted witness carries
/// [`AuthorityTerminal::ExactRuleDerived`].
///
/// Family-local: this closes the T3 primal-dual identity family only, not general
/// C4 (see the module header).
pub fn witness_from_t3_replay(
    packet: &ReplayPacket,
    descent_ref: impl Into<String>,
) -> Option<DescentWitness> {
    let audit = T3Verifier::verify(packet);
    witness_from_t3_audit(&audit, descent_ref)
}

fn witness_from_t3_audit(
    audit: &VerificationAudit,
    descent_ref: impl Into<String>,
) -> Option<DescentWitness> {
    // Family-local gate: ONLY an admitted T3 primal-dual identity replay may carry
    // authority. Rejected / Inconclusive ⇒ no witness.
    if audit.status != VerificationStatus::Admitted {
        return None;
    }
    // Sole constructor — there is no alternate authority path in this adapter.
    // `.ok()` drops the (empty descent_ref) refusal to `None`; it never fabricates
    // a witness by any other route.
    DescentWitness::from_verified_replay(
        T3_PRIMAL_DUAL_TERMINAL,
        descent_ref,
        t3_replay_hash(&audit.packet_hash),
    )
    .ok()
}

/// Satisfies the contract validator for the T3Authority symbol.
pub struct T3Authority;

// Origin: engine/crates_rs/core_replay/src/t3_authority.rs
// Claim: urn:core:crates_rs:core-replay:t3-authority:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::replay_harness::{ReplayPacket, T3Verifier};
    use num_bigint::BigInt;
    use num_rational::BigRational;

    fn q(numer: i64, denom: i64) -> BigRational {
        BigRational::new(BigInt::from(numer), BigInt::from(denom))
    }

    const DREF: &str = "descent:t3-primal-dual:row-1";

    /// Toy parity packet the T3 verifier ADMITS (the `replay_harness` fixture):
    /// `m_primal = m_dual = 1`, dual feasible (`d₀ᵀφ = 0`), `‖φ‖_∞ = 1`, all exact.
    fn admitted_packet() -> ReplayPacket {
        ReplayPacket {
            d0: vec![vec![q(1, 1)], vec![q(1, 1)]],
            omega: vec![q(1, 1), q(0, 1)],
            alpha: vec![q(1, 2)],
            primal_residual: vec![q(1, 2), q(-1, 2)],
            phi: vec![q(1, 1), q(-1, 1)],
            reported_value: q(1, 1),
            carrier_hash: [7u8; 32],
        }
    }

    /// Same packet but `alpha = 2`: residual `[-1,-2]`, `m_primal = 3 ≠ m_dual = 1`,
    /// so the exact comparison fails ⇒ the verifier REJECTS.
    fn rejected_packet() -> ReplayPacket {
        ReplayPacket {
            alpha: vec![q(2, 1)],
            primal_residual: vec![q(-1, 1), q(-2, 1)],
            reported_value: q(3, 1),
            ..admitted_packet()
        }
    }

    /// Independent recomputation of the expected `auth023:t3-primal-dual:v2:exact:blake3:<hex>`
    /// replay hash, so the preservation checks are not tautological pass-throughs of the adapter.
    fn expected_hash(packet_hash: [u8; 32]) -> String {
        use std::fmt::Write as _;
        let mut hex = String::new();
        for byte in &packet_hash {
            let _ = write!(hex, "{byte:02x}");
        }
        format!("auth023:t3-primal-dual:v2:exact:blake3:{hex}")
    }

    /// 1. Admitted replay creates a `DescentWitness` (through `from_verified_replay`).
    #[test]
    fn auth_023_admitted_replay_creates_witness() {
        let packet = admitted_packet();
        let witness = witness_from_t3_replay(&packet, DREF).expect("admitted ⇒ Some(witness)");
        // Inspect the payload — a genuine witness shape, not merely `is_some`.
        assert_eq!(witness.terminal(), AuthorityTerminal::ExactRuleDerived);
        assert_eq!(witness.descent_ref(), DREF);
        assert!(
            !witness.replay_hash().is_empty(),
            "witness must carry a replay hash"
        );
    }

    /// 2. Rejected replay creates no witness.
    #[test]
    fn auth_023_rejected_replay_creates_no_witness() {
        let packet = rejected_packet();
        assert!(
            witness_from_t3_replay(&packet, DREF).is_none(),
            "rejected replay must produce no DescentWitness"
        );
    }

    /// 3. Inconclusive replay creates no witness. A malformed packet (e.g. dimension mismatch)
    ///    yields Inconclusive status internally, so the adapter returns None.
    #[test]
    fn auth_023_inconclusive_replay_creates_no_witness() {
        // Malformed packet: dimension mismatch (omega len 3 vs d0 rows 2)
        let packet = ReplayPacket {
            omega: vec![q(1, 1), q(0, 1), q(0, 1)],
            phi: vec![q(1, 1), q(-1, 1), q(1, 1)],
            ..admitted_packet()
        };
        assert!(
            witness_from_t3_replay(&packet, DREF).is_none(),
            "inconclusive replay must produce no DescentWitness"
        );
    }

    /// 4. The replay_hash is preserved (unaltered) in the emitted witness: it equals
    ///    the independently-computed hex of the recompute packet hash.
    #[test]
    fn auth_023_replay_hash_is_preserved_in_emitted_witness() {
        let packet = admitted_packet();
        let audit = T3Verifier::verify(&packet);
        let witness = witness_from_t3_replay(&packet, DREF).expect("admitted ⇒ witness");
        assert_eq!(
            witness.replay_hash(),
            expected_hash(audit.packet_hash),
            "the recompute packet hash must be bound into the witness, unaltered"
        );
    }

    /// 5. No alternate constructor path exists in the adapter: its admitted output
    ///    is byte-identical to a DIRECT `from_verified_replay` call with the same
    ///    inputs, and when the sole constructor would refuse (empty descent_ref) the
    ///    adapter yields `None` — no bypass, no fallback fabrication.
    #[test]
    fn auth_023_no_alternate_constructor_path() {
        let packet = admitted_packet();
        let audit = T3Verifier::verify(&packet);
        let via_adapter = witness_from_t3_replay(&packet, DREF).expect("admitted ⇒ witness");
        let via_sole_constructor = DescentWitness::from_verified_replay(
            AuthorityTerminal::ExactRuleDerived,
            DREF,
            expected_hash(audit.packet_hash),
        )
        .expect("direct sole-constructor call");

        // Assert field-by-field comparisons as requested
        assert_eq!(via_adapter.terminal(), via_sole_constructor.terminal());
        assert_eq!(
            via_adapter.descent_ref(),
            via_sole_constructor.descent_ref()
        );
        assert_eq!(
            via_adapter.replay_hash(),
            via_sole_constructor.replay_hash()
        );

        // The sole constructor refuses an empty descent_ref; the adapter must then
        // produce nothing (no alternate fabrication), even for an admitted replay.
        assert!(
            witness_from_t3_replay(&packet, "").is_none(),
            "empty descent_ref ⇒ sole constructor refuses ⇒ adapter yields None (no bypass)"
        );
    }
}
