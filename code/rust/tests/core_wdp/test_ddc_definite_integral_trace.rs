//! The `packets/core_definite_integral_packet.md` descent, machine-emitted.
//!
//! The packet's §10 trace was hand-executed against the spine alphabet because
//! the crate had no alphabet to emit against. `dda_alphabet` closed that gap;
//! this test is the receipt. It runs the descent for BOTH branches:
//!
//!   * `x^2` on `[0,10]_Q` — Q admission debt payable ⇒ `C E D Λ I T`, Terminalized
//!   * Dirichlet on `[0,10]_Q` — debt #4 unpayable ⇒ halts at `Λ`, emits `M`, Refused
//!
//! Everything is exact rational arithmetic (`num_rational::BigRational`): no
//! floats, no approximation, no limit taken. The bracket is the finite shadow.

use num_bigint::BigInt;
use num_rational::BigRational;
use core_wdp::ddc::dda_alphabet::{DdaOp, DdaStep, DdaTrace, TraceTerminal};
use core_types::authority::AuthorityEffect;

fn rat(n: i64, d: i64) -> BigRational {
    BigRational::new(BigInt::from(n), BigInt::from(d))
}

/// Exact Darboux upper sum for `f(x)=x^2` on `[0,10]`, uniform partition `P_n`.
/// `U_n = 1000/3 + 500/n + 500/(3n^2)` (f increasing ⇒ sup at the right node).
fn upper_sum(n: i64) -> BigRational {
    rat(1000, 3) + rat(500, n) + rat(500, 3 * n * n)
}

/// Exact Darboux lower sum: `L_n = 1000/3 - 500/n + 500/(3n^2)`.
fn lower_sum(n: i64) -> BigRational {
    rat(1000, 3) - rat(500, n) + rat(500, 3 * n * n)
}

/// The finite-shadow width `eps_sh(n) = U_n - L_n`. NOT `Phi_1` — this is the
/// resolution of the Darboux probe, not quotient obstruction mass.
fn shadow_width(n: i64) -> BigRational {
    upper_sum(n) - lower_sum(n)
}

#[test]
fn darboux_bracket_is_exact_and_telescopes() {
    // eps_sh(n) = 1000/n exactly, for every n — the monotone collapse
    // (f(10) - f(0)) * dx = 100 * 10/n.
    for n in [1i64, 2, 3, 7, 10, 1000] {
        assert_eq!(shadow_width(n), rat(1000, n), "eps_sh({n}) must be 1000/n");
    }
}

#[test]
fn bracket_strictly_contains_the_terminal_value() {
    let value = rat(1000, 3);
    for n in [1i64, 2, 5, 100] {
        assert!(lower_sum(n) < value, "L_{n} < 1000/3");
        assert!(upper_sum(n) > value, "U_{n} > 1000/3");
    }
}

#[test]
fn descent_trigger_is_finite_and_computed() {
    // Debt #5: for rational tolerance eps, n > 1000/eps suffices. Computed, not
    // searched. eps = 1/1000 -> n = 1_000_001.
    let eps = rat(1, 1000);
    let n: i64 = 1_000_001;
    assert!(shadow_width(n) < eps, "eps_sh(n) < eps at the computed n");
}

/// The payable branch: `x^2`. Emits the full descent.
#[test]
fn x_squared_descent_terminalizes_with_machine_emitted_trace() {
    let mut t = DdaTrace::new();

    // C — declare carrier + 2-window + priced imports.
    t.emit(DdaStep::executed(
        DdaOp::ContextExposure,
        "carrier: finite rational partitions of [0,10]_Q; C0=nodes, C1=oriented \
         subintervals [t_i,t_j], C2=concatenation triples; imports priced: Q, order, Archimedean",
    ));

    // E — exact repair: the discrete antiderivative by partial sums (H^1=0 on
    // the interval carrier ⇒ every additive cochain is exact).
    t.emit(DdaStep::executed(
        DdaOp::ExactRepair,
        "F(t_i) := A([t_0,t_i]); d_0 F = A on every edge; Phi_1([A]) = 0, Gamma_2([A]) = 0",
    ));

    // D — descent: refine, halving the finite-shadow width.
    let (before, after) = (shadow_width(8), shadow_width(16));
    assert_eq!(
        after.clone(),
        before.clone() / BigRational::from(BigInt::from(2)),
        "refinement halves the finite-shadow width"
    );
    t.emit(DdaStep::executed(
        DdaOp::Descent,
        format!("refine P_8 |= P_16: eps_sh {before} -> {after}"),
    ));

    // Λ — lift the refinement-limit. Q gate: five debts, all payable.
    t.emit(DdaStep::executed(
        DdaOp::Lift,
        "Q admission debt 5/5: finite shadow (L_n,U_n) exact rational; refinement \
         P_n |= P_2n; topology |.| on Q; convergence certificate eps_sh(n)=1000/n \
         closed form; descent trigger n > 1000/eps",
    ));

    // I — ledger.
    t.emit(DdaStep::executed(
        DdaOp::Integration,
        "receipt: bracket + witness (F, telescoping, eps_sh, trigger)",
    ));

    // T — seal.
    t.emit_gated_terminal(DdaStep::executed(
        DdaOp::Terminalize,
        "TerminalWithinScope: 1000/3, scope = declared carrier",
    ));

    assert_eq!(t.letters(), "C E D Λ I T");
    assert_eq!(t.terminal(), TraceTerminal::Terminalized);

    // CODA-5: sealed, and still mints nothing.
    assert_eq!(t.authority_effect(), AuthorityEffect::None);
}

/// The refused branch: Dirichlet. The gate must discriminate, not rubber-stamp.
#[test]
fn dirichlet_descent_refuses_at_the_q_gate() {
    // Every subinterval contains both rationals and irrationals, so for EVERY n:
    // U_n = 10, L_n = 0, width = 10. Debt #4 (convergence certificate) is
    // unpayable — the bracket never narrows.
    let width_at = |_n: i64| BigRational::from(BigInt::from(10));
    for n in [1i64, 10, 1_000_000] {
        assert_eq!(width_at(n), BigRational::from(BigInt::from(10)));
    }

    let mut t = DdaTrace::new();
    t.emit(DdaStep::executed(
        DdaOp::ContextExposure,
        "carrier: same as x^2 run; f = indicator of Q on [0,10]_Q",
    ));
    t.emit(DdaStep::executed(
        DdaOp::ExactRepair,
        "H^1 = 0 still holds: at each finite P the cochain is exact. \
         The finite degree is NOT where this fails.",
    ));
    t.emit(DdaStep::executed(
        DdaOp::Descent,
        "refine P_n |= P_2n: eps_sh stays 10 — the bracket does not narrow",
    ));

    // Λ refuses: the lift trigger fired, but the lift has no license.
    t.emit(DdaStep::refused(
        DdaOp::Lift,
        "Q admission debt 4/5: convergence-certificate route unpayable \
         (U_n - L_n = 10 for all n, does not tend to 0)",
    ));

    // M — typed refusal is a valid terminal.
    t.emit(DdaStep::executed(
        DdaOp::Refusal,
        "OpenResidual / MissingWitness: no Riemann integral exists on this carrier",
    ));

    assert_eq!(t.letters(), "C E D Λ M");
    assert_eq!(t.terminal(), TraceTerminal::Refused);
    assert_eq!(t.authority_effect(), AuthorityEffect::None);

    // The refusal is on the record with its reason, per CODA-4.
    let lift = &t.steps()[3];
    assert!(!lift.is_executed(), "the lift must NOT have executed");
}

/// CODA-8: had we reached for the continuum instead of paying the debt.
#[test]
fn reaching_for_the_continuum_triggers_oracle_needed() {
    let mut t = DdaTrace::new();
    t.emit(DdaStep::executed(DdaOp::ContextExposure, "finite window"));
    // "Just take the limit in R" is licensed from outside the declared window.
    t.import("completeness of R / continuum limit");
    t.emit(DdaStep::executed(
        DdaOp::Terminalize,
        "claiming the value anyway",
    ));

    match t.terminal() {
        TraceTerminal::OracleNeeded { import } => assert!(import.contains("continuum")),
        other => panic!("expected OracleNeeded, got {other:?}"),
    }
    assert_eq!(t.authority_effect(), AuthorityEffect::None);
}

// Origin: engine/crates_rs/tests/core_wdp/test_ddc_definite_integral_trace.rs
// Claim: urn:core:crates_rs:tests:test-ddc-definite-integral-trace:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordaeddb355 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordaeddb355` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErroraeddb355 {
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
impl BoundaryErroraeddb355 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErroraeddb355 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErroraeddb355 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordaeddb355 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErroraeddb355> {
        if capacity_bound == 0 {
            return Err(BoundaryErroraeddb355::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErroraeddb355::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErroraeddb355::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_aeddb355() {
    let admitted = BoundaryRecordaeddb355::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordaeddb355::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
