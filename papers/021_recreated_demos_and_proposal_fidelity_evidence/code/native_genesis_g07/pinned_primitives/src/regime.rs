//! Sort 3 — **Regime**: admitted state, and nothing else.
//!
//! Crate boundary: coda-carrier.  Source: `code/derivation/model.py`,
//! `class Regime` — the frozen five-field record.
//!
//! ```text
//! data   admitted data in admission order; entries are presentation tokens,
//!        internal identity is the index
//! forms  admitted judgment forms; entry a at index f means form f has arity a >= 1
//! insts  admitted judgment instances (form, args)
//! rules  forms carrying the uniform all-tuples rule
//! reqs   externally imposed persistent separation requirements (i, j), i < j
//! ```
//!
//! A regime carries **no history, no provenance, no cache**.  Provenance lives
//! in the history (`retention.rs`).  A regime that remembers how it was
//! reached is a different sort wearing this one's name (§13.3).
//!
//! There is no `&mut` API on purpose.  Every function that "changes" a regime
//! returns a new one. Fields are crate-visible, not publicly writable;
//! admission and renaming are separate constructors of values. This API
//! boundary does not establish a value's admission history: replay does.

use std::collections::BTreeSet;

use crate::mark::{Mark, Pair};
use crate::token::Token;

/// The index of an admitted judgment form.
pub type FormId = usize;

/// The argument tuple of a judgment instance: admitted marks, one per slot.
pub type Args = Vec<Mark>;

/// An admitted judgment instance: a form applied to admitted marks.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Inst {
    /// Which form.
    pub form: FormId,
    /// Which marks, in slot order.
    pub args: Args,
}

impl Inst {
    /// Build an instance.
    pub fn new(form: FormId, args: Args) -> Inst {
        Inst { form, args }
    }
}

/// Admitted state, externally read-only; trusted crate code can construct it.
///
/// ```compile_fail
/// use omega_ooutwire_primitives::regime::Regime;
/// let mut r = Regime::genesis();
/// r.data.clear();
/// ```
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Regime {
    /// Admitted data in admission order.  Entries are presentation tokens.
    pub(crate) data: Vec<Token>,
    /// Admitted forms: `forms[f]` is the arity of form `f`.
    pub(crate) forms: Vec<usize>,
    /// Admitted instances.
    pub(crate) insts: BTreeSet<Inst>,
    /// Forms carrying the uniform all-tuples rule.
    pub(crate) rules: BTreeSet<FormId>,
    /// Imposed separation requirements.
    pub(crate) reqs: BTreeSet<Pair>,
}

impl Regime {
    /// Read the admitted tokens without mutable access.
    pub fn data(&self) -> &[Token] { &self.data }
    /// Read form arities.
    pub fn forms(&self) -> &[usize] { &self.forms }
    /// Read instances.
    pub fn insts(&self) -> &BTreeSet<Inst> { &self.insts }
    /// Read uniform rules.
    pub fn rules(&self) -> &BTreeSet<FormId> { &self.rules }
    /// Read imposed requirements.
    pub fn reqs(&self) -> &BTreeSet<Pair> { &self.reqs }

    /// `∅` — genesis: nothing admitted.
    pub fn genesis() -> Regime {
        Regime {
            data: Vec::new(),
            forms: Vec::new(),
            insts: BTreeSet::new(),
            rules: BTreeSet::new(),
            reqs: BTreeSet::new(),
        }
    }

    /// How many data are admitted.
    pub fn n_data(&self) -> usize {
        self.data.len()
    }

    /// How many forms are admitted.
    pub fn n_forms(&self) -> usize {
        self.forms.len()
    }

    /// The admitted marks, in admission order.
    pub fn marks(&self) -> impl Iterator<Item = Mark> {
        (0..self.data.len()).map(Mark)
    }

    /// Whether `m` names an admitted datum.
    pub fn has_mark(&self, m: Mark) -> bool {
        m.0 < self.data.len()
    }
}

impl Default for Regime {
    fn default() -> Regime {
        Regime::genesis()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn genesis_admits_nothing() {
        let g = Regime::genesis();
        assert!(g.data().is_empty() && g.forms().is_empty());
        assert!(g.insts().is_empty() && g.rules().is_empty() && g.reqs().is_empty());
        assert_eq!(g.n_data(), 0);
        assert_eq!(g.n_forms(), 0);
        assert!(g.insts.is_empty() && g.rules.is_empty() && g.reqs.is_empty());
    }

    /// The projection law of §13.9: a projection that enumerates fields will
    /// drop one.  This destructuring fails to COMPILE if a field is added to
    /// `Regime` without being named here, which is the only kind of totality
    /// a type system hands out for free.
    #[test]
    fn every_field_is_named_by_the_destructuring() {
        let Regime { data, forms, insts, rules, reqs } = Regime::genesis();
        assert!(data.is_empty() && forms.is_empty());
        assert!(insts.is_empty() && rules.is_empty() && reqs.is_empty());
    }
}
