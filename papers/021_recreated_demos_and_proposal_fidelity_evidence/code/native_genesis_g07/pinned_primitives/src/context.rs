//! Sort 7 — **Context**: a form plus a slot tuple with holes.
//!
//! Crate boundary: coda-observe.  Source: `observe.py::contexts`,
//! `slot_tuples`, `plug`.
//!
//! A context is the estate's unit of *looking*.  Plugging a datum `d` into a
//! context fills every hole with `d` and yields an instance; whether that
//! instance is derivable is the one bit the object language can see about
//! `d` at that context.  Everything observational — profiles, separability,
//! witnesses, the four readers — is built from this and nothing else.
//!
//! Order matters and is fixed: forms in admission order, then slot tuples
//! with the hole first and data by index.  `witness` returns the *first*
//! separating context in this order, so the order is part of the
//! definition, not a detail.

use crate::mark::Mark;
use crate::regime::{FormId, Inst, Regime};

/// A slot: a hole (`None`) or an admitted mark.
pub type Slot = Option<Mark>;

/// A judgment form together with a slot tuple in which at least one slot is
/// a hole.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Context {
    /// Which form.
    pub form: FormId,
    /// The slots; at least one is `None`.
    pub slots: Vec<Slot>,
}

/// All slot tuples of the given arity over `n_data` data, in the fixed
/// deterministic order: hole first, then data by index, varying the last
/// slot fastest.
pub fn slot_tuples(arity: usize, n_data: usize) -> Vec<Vec<Slot>> {
    let options: Vec<Slot> = std::iter::once(None)
        .chain((0..n_data).map(|d| Some(Mark(d))))
        .collect();
    let mut out: Vec<Vec<Slot>> = vec![Vec::new()];
    for _ in 0..arity {
        let mut next = Vec::with_capacity(out.len() * options.len());
        for prefix in &out {
            for o in &options {
                let mut t = prefix.clone();
                t.push(*o);
                next.push(t);
            }
        }
        out = next;
    }
    out
}

/// All contexts of the regime, deterministically ordered.
pub fn contexts(r: &Regime) -> Vec<Context> {
    let mut out = Vec::new();
    for (form, &arity) in r.forms.iter().enumerate() {
        for slots in slot_tuples(arity, r.n_data()) {
            if slots.iter().any(|s| s.is_none()) {
                out.push(Context { form, slots });
            }
        }
    }
    out
}

/// Fill every hole of the context with `d`.
pub fn plug(c: &Context, d: Mark) -> Inst {
    Inst::new(c.form, c.slots.iter().map(|s| s.unwrap_or(d)).collect())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::admission::step;
    use crate::event::Event;
    use crate::reading::READING_L;
    use crate::replay::replay;

    #[test]
    fn no_forms_means_no_contexts() {
        let base = replay(&READING_L.genesis).unwrap();
        assert!(contexts(&base).is_empty());
    }

    #[test]
    fn a_unary_form_over_two_data_has_one_context() {
        let base = replay(&READING_L.genesis).unwrap();
        let r = step(&base, &Event::AdmitForm(1)).unwrap();
        let cs = contexts(&r);
        assert_eq!(cs.len(), 1);
        assert_eq!(cs[0].slots, vec![None]);
        assert_eq!(plug(&cs[0], Mark(1)), Inst::new(0, vec![Mark(1)]));
    }

    /// Binary form over two data: 9 slot tuples, 5 contain a hole.
    #[test]
    fn a_binary_form_over_two_data_has_five_contexts() {
        let base = replay(&READING_L.genesis).unwrap();
        let r = step(&base, &Event::AdmitForm(2)).unwrap();
        assert_eq!(slot_tuples(2, 2).len(), 9);
        assert_eq!(contexts(&r).len(), 5);
        assert_eq!(contexts(&r)[0].slots, vec![None, None], "hole first");
    }
}
