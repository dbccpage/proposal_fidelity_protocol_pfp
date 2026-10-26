//! Primitive — the **certification panel**: certifies up to the panel,
//! never up to correspondence.
//!
//! Crate boundary: represented.  Source: Lean `Represented.Evaluator`,
//! `verdictB`, `certPosB`, `certNegB`, `cert_scope`,
//! `cert_not_correspondence`, `cert_panel_relative`.
//!
//! An evaluator is *represented data*: the contexts it may consult.  The
//! panel certifies "separated" when every evaluator's own contexts separate,
//! and "equivalent" when none does.  `cert_scope` says that is exactly what
//! certification gives and no more.  `cert_not_correspondence` is the
//! countermodel: a unanimous panel certifies "equivalent" while a context
//! outside the panel separates.  Agreement among represented evaluators
//! reaches the panel's joint quotient and nothing beyond it.
//!
//! This is the *third* sense of evaluation (crosstab §3) and the one an
//! engine most wants to skip: All-Green is not All-Correct (E2).  The Omega
//! engine reports its panel's blind spot on demand for that reason, and the
//! `ObserverIncomplete` terminal exists for the case where the panel cannot
//! see what the metatheory sees.

use crate::context::{contexts, plug, Context};
use crate::mark::Pair;
use crate::profile::derivable;
use crate::regime::Regime;

/// A represented evaluator: the contexts it may use.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Evaluator {
    /// Its columns.
    pub contexts: Vec<Context>,
}

impl Evaluator {
    /// The evaluator that may use every context of the regime.
    pub fn full(r: &Regime) -> Evaluator {
        Evaluator { contexts: contexts(r) }
    }

    /// Its verdict on a pair: some column of its own separates.
    pub fn verdict(&self, r: &Regime, p: Pair) -> bool {
        self.contexts.iter().any(|c| derivable(r, &plug(c, p.i)) != derivable(r, &plug(c, p.j)))
    }
}

/// The panel closes positively: nonempty, and every evaluator says separated.
pub fn cert_pos(panel: &[Evaluator], r: &Regime, p: Pair) -> bool {
    !panel.is_empty() && panel.iter().all(|e| e.verdict(r, p))
}

/// The panel closes negatively: nonempty, and no evaluator separates.
pub fn cert_neg(panel: &[Evaluator], r: &Regime, p: Pair) -> bool {
    !panel.is_empty() && panel.iter().all(|e| !e.verdict(r, p))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::admission::step;
    use crate::event::Event;
    use crate::reading::READING_F;
    use crate::replay::replay;
    use crate::separability::separable;

    fn separated_world() -> Regime {
        let base = replay(&READING_F.genesis).unwrap();
        let r = step(&base, &Event::AdmitForm(1)).unwrap();
        step(&r, &crate::testkit::inst(0, &[0])).unwrap()
    }

    /// `cert_scope`: positive closure is exactly joint separation by every
    /// evaluator's own columns.
    #[test]
    fn cert_scope() {
        let r = separated_world();
        let p = Pair::of(0, 1);
        let full = Evaluator::full(&r);
        assert!(cert_pos(std::slice::from_ref(&full), &r, p));
        assert!(!cert_pos(&[], &r, p), "an empty panel certifies nothing");
        assert!(!cert_neg(&[], &r, p));
    }

    /// `cert_not_correspondence`: a unanimous panel of evaluators whose
    /// columns do not separate certifies "equivalent" while the regime
    /// separates the pair.
    #[test]
    fn cert_not_correspondence() {
        let r = separated_world();
        let p = Pair::of(0, 1);
        assert!(separable(&r, p.i, p.j));
        let blind = Evaluator { contexts: Vec::new() };
        assert!(cert_neg(&[blind.clone(), blind], &r, p));
    }

    /// `cert_panel_relative`: extending the panel can break closure.
    #[test]
    fn cert_panel_relative() {
        let r = separated_world();
        let p = Pair::of(0, 1);
        let full = Evaluator::full(&r);
        let blind = Evaluator { contexts: Vec::new() };
        assert!(cert_pos(std::slice::from_ref(&full), &r, p));
        assert!(!cert_pos(&[full, blind], &r, p));
    }
}
