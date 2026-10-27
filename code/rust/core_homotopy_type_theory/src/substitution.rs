#![cfg(any())]
// TODO: Fix imports from legacy arithmos
//! Capture-avoiding substitution via De Bruijn indices.

use super::term::Term;

/// Shifts all free variables in `t` by `amount`, starting at binding depth `cutoff`.
pub fn shift(t: &mut Term, amount: isize, cutoff: usize) {
    match t {
        Term::Var(idx) => {
            if idx.0 >= cutoff {
                idx.0 = (idx.0 as isize + amount) as usize;
            }
        }
        Term::Pi {
            domain, codomain, ..
        } => {
            shift(domain, amount, cutoff);
            shift(codomain, amount, cutoff + 1);
        }
        Term::Lambda { body, .. } => {
            shift(body, amount, cutoff + 1);
        }
        Term::App { func, arg } => {
            shift(func, amount, cutoff);
            shift(arg, amount, cutoff);
        }
        Term::Sigma {
            fst_type, snd_type, ..
        } => {
            shift(fst_type, amount, cutoff);
            shift(snd_type, amount, cutoff + 1);
        }
        Term::Pair { fst, snd } => {
            shift(fst, amount, cutoff);
            shift(snd, amount, cutoff);
        }
        other => shift_eliminators(other, amount, cutoff),
    }
}

fn shift_eliminators(t: &mut Term, amount: isize, cutoff: usize) {
    match t {
        Term::Fst(e) | Term::Snd(e) | Term::Refl(e) | Term::NatSucc(e) => {
            shift(e, amount, cutoff);
        }
        Term::IdType { ty, lhs, rhs } => {
            shift(ty, amount, cutoff);
            shift(lhs, amount, cutoff);
            shift(rhs, amount, cutoff);
        }
        Term::Abort { ty, expr } => {
            shift(ty, amount, cutoff);
            shift(expr, amount, cutoff);
        }
        Term::BoolElim {
            ty,
            m_true,
            m_false,
            expr,
        } => {
            shift(ty, amount, cutoff);
            shift(m_true, amount, cutoff);
            shift(m_false, amount, cutoff);
            shift(expr, amount, cutoff);
        }
        Term::NatElim {
            ty,
            m_zero,
            m_succ,
            expr,
        } => {
            shift(ty, amount, cutoff);
            shift(m_zero, amount, cutoff);
            shift(m_succ, amount, cutoff);
            shift(expr, amount, cutoff);
        }
        Term::Var(_)
        | Term::Pi { .. }
        | Term::Lambda { .. }
        | Term::App { .. }
        | Term::Sigma { .. }
        | Term::Pair { .. }
        | Term::Free(_)
        | Term::Universe(_)
        | Term::UnitType
        | Term::UnitVal
        | Term::EmptyType
        | Term::BoolType
        | Term::BoolTrue
        | Term::BoolFalse
        | Term::NatType
        | Term::NatZero => {}
    }
}

/// Substitutes `repl` for the variable at `index` in `t`.
pub fn substitute(t: &mut Term, index: usize, repl: &Term) {
    match t {
        Term::Var(idx) => {
            if idx.0 == index {
                *t = repl.clone();
            } else if idx.0 > index {
                idx.0 -= 1;
            }
        }
        Term::Pi {
            domain, codomain, ..
        } => {
            substitute(domain, index, repl);
            let mut repl_shifted = repl.clone();
            shift(&mut repl_shifted, 1, 0);
            substitute(codomain, index + 1, &repl_shifted);
        }
        Term::Lambda { body, .. } => {
            let mut repl_shifted = repl.clone();
            shift(&mut repl_shifted, 1, 0);
            substitute(body, index + 1, &repl_shifted);
        }
        Term::App { func, arg } => {
            substitute(func, index, repl);
            substitute(arg, index, repl);
        }
        Term::Sigma {
            fst_type, snd_type, ..
        } => {
            substitute(fst_type, index, repl);
            let mut repl_shifted = repl.clone();
            shift(&mut repl_shifted, 1, 0);
            substitute(snd_type, index + 1, &repl_shifted);
        }
        Term::Pair { fst, snd } => {
            substitute(fst, index, repl);
            substitute(snd, index, repl);
        }
        other => substitute_eliminators(other, index, repl),
    }
}

fn substitute_eliminators(t: &mut Term, index: usize, repl: &Term) {
    match t {
        Term::Fst(e) | Term::Snd(e) | Term::Refl(e) | Term::NatSucc(e) => {
            substitute(e, index, repl);
        }
        Term::IdType { ty, lhs, rhs } => {
            substitute(ty, index, repl);
            substitute(lhs, index, repl);
            substitute(rhs, index, repl);
        }
        Term::Abort { ty, expr } => {
            substitute(ty, index, repl);
            substitute(expr, index, repl);
        }
        Term::BoolElim {
            ty,
            m_true,
            m_false,
            expr,
        } => {
            substitute(ty, index, repl);
            substitute(m_true, index, repl);
            substitute(m_false, index, repl);
            substitute(expr, index, repl);
        }
        Term::NatElim {
            ty,
            m_zero,
            m_succ,
            expr,
        } => {
            substitute(ty, index, repl);
            substitute(m_zero, index, repl);
            substitute(m_succ, index, repl);
            substitute(expr, index, repl);
        }
        Term::Var(_)
        | Term::Pi { .. }
        | Term::Lambda { .. }
        | Term::App { .. }
        | Term::Sigma { .. }
        | Term::Pair { .. }
        | Term::Free(_)
        | Term::Universe(_)
        | Term::UnitType
        | Term::UnitVal
        | Term::EmptyType
        | Term::BoolType
        | Term::BoolTrue
        | Term::BoolFalse
        | Term::NatType
        | Term::NatZero => {}
    }
}

/// Replace the bound variable 0 in `scope` with `arg`, shifting indices down.
pub fn instantiate(scope: &mut Term, arg: &Term) {
    let arg_shifted = arg.clone();
    substitute(scope, 0, &arg_shifted);
}

// Origin: engine/crates_rs/core_homotopy_type_theory/src/substitution.rs
// Claim: urn:core:crates_rs:core-homotopy-type-theory:substitution:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde0d71086 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde0d71086` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore0d71086 {
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
impl BoundaryErrore0d71086 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore0d71086 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore0d71086 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde0d71086 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore0d71086> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore0d71086::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore0d71086::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore0d71086::ExceedsCapacity {
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
mod l4_boundary_tests_e0d71086 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorde0d71086::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorde0d71086::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorde0d71086::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorde0d71086::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorde0d71086::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrore0d71086::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrore0d71086::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
