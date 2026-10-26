//! Sort 8 — **Renaming**: a transformation the reading permits.
//!
//! Crate boundary: coda-iso.  Source: `iso.py::rename`, `serialize`; for the
//! boundary reading see `boundary.rs`, where the permitted set is *declared
//! by the reading* (mark permutations always, the side exchange under U only).
//!
//! In the sealed reading a renaming is a **bijection pair**: one permutation
//! of data indices, one of form indices.  Presentation tokens travel with
//! their data and are then forgotten by `serialize`, which is the whole
//! mechanism by which tokens fail to survive canonicalisation.
//!
//! `serialize` is a *total* serialisation: every field of the regime except
//! the tokens, under the bijection.  Two regimes are isomorphic exactly when
//! some bijection pair makes their serialisations equal — and `canonical.rs`
//! turns "some" into a computed minimum.

use crate::mark::{Mark, Pair};
use crate::regime::{Inst, Regime};

/// A bijection pair `pi` on data and `phi` on forms, as `pi[old] = new`.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Bijection {
    /// The data permutation.
    pub data: Vec<usize>,
    /// The form permutation.
    pub forms: Vec<usize>,
}

impl Bijection {
    /// The identity on `n` data and `nf` forms.
    pub fn identity(n: usize, nf: usize) -> Bijection {
        Bijection { data: (0..n).collect(), forms: (0..nf).collect() }
    }
}

/// The total serialisation of a regime under a bijection: everything but
/// the tokens.
pub type Key = (usize, Vec<usize>, Vec<(usize, Vec<usize>)>, Vec<usize>, Vec<(usize, usize)>);

/// All permutations of `0..n`, in lexicographic order.
pub fn permutations(n: usize) -> Vec<Vec<usize>> {
    fn go(rest: &mut Vec<usize>, cur: &mut Vec<usize>, out: &mut Vec<Vec<usize>>) {
        if rest.is_empty() {
            out.push(cur.clone());
            return;
        }
        for k in 0..rest.len() {
            let v = rest.remove(k);
            cur.push(v);
            go(rest, cur, out);
            cur.pop();
            rest.insert(k, v);
        }
    }
    let mut out = Vec::new();
    let mut rest: Vec<usize> = (0..n).collect();
    go(&mut rest, &mut Vec::new(), &mut out);
    out
}

/// The inverse of a permutation.
pub fn invert(perm: &[usize]) -> Vec<usize> {
    let mut out = vec![0; perm.len()];
    for (old, &new) in perm.iter().enumerate() {
        out[new] = old;
    }
    out
}

/// Serialize the regime under the bijection pair: tokens forgotten.
pub fn serialize(r: &Regime, b: &Bijection) -> Key {
    let pi = &b.data;
    let phi = &b.forms;
    let mut forms = vec![0; r.n_forms()];
    for (f, &arity) in r.forms.iter().enumerate() {
        forms[phi[f]] = arity;
    }
    let mut insts: Vec<(usize, Vec<usize>)> = r
        .insts
        .iter()
        .map(|i| (phi[i.form], i.args.iter().map(|m| pi[m.0]).collect()))
        .collect();
    insts.sort();
    let mut rules: Vec<usize> = r.rules.iter().map(|&f| phi[f]).collect();
    rules.sort();
    let mut reqs: Vec<(usize, usize)> = r
        .reqs
        .iter()
        .map(|p| {
            let (a, b) = (pi[p.i.0], pi[p.j.0]);
            (a.min(b), a.max(b))
        })
        .collect();
    reqs.sort();
    (r.n_data(), forms, insts, rules, reqs)
}

/// `π·` — apply the bijection pair, producing an isomorphic regime.  Tokens
/// travel with their data.
pub fn rename(r: &Regime, b: &Bijection) -> Regime {
    let pi = &b.data;
    let phi = &b.forms;
    let mut data = vec![crate::token::Token::new(""); r.n_data()];
    for (d, tok) in r.data.iter().enumerate() {
        data[pi[d]] = tok.clone();
    }
    let mut forms = vec![0; r.n_forms()];
    for (f, &arity) in r.forms.iter().enumerate() {
        forms[phi[f]] = arity;
    }
    let insts = r
        .insts
        .iter()
        .map(|i| Inst::new(phi[i.form], i.args.iter().map(|m| Mark(pi[m.0])).collect()))
        .collect();
    let rules = r.rules.iter().map(|&f| phi[f]).collect();
    let reqs = r.reqs.iter().map(|p| Pair::of(pi[p.i.0], pi[p.j.0])).collect();
    Regime { data, forms, insts, rules, reqs }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::admission::step;
    use crate::event::Event;
    use crate::reading::READING_F;
    use crate::replay::replay;

    #[test]
    fn permutations_are_complete_and_lexicographic() {
        let p = permutations(3);
        assert_eq!(p.len(), 6);
        assert_eq!(p[0], vec![0, 1, 2]);
        assert_eq!(p[5], vec![2, 1, 0]);
        assert_eq!(invert(&[2, 0, 1]), vec![1, 2, 0]);
    }

    #[test]
    fn rename_carries_tokens_and_serialize_forgets_them() {
        let base = replay(&READING_F.genesis).unwrap();
        let r = step(&base, &Event::AdmitForm(2)).unwrap();
        let r = step(&r, &crate::testkit::inst(0, &[0, 2])).unwrap();
        let b = Bijection { data: vec![2, 0, 1], forms: vec![0] };
        let s = rename(&r, &b);
        assert_eq!(s.data[2], r.data[0], "the token travelled with its datum");
        assert_eq!(serialize(&s, &Bijection::identity(3, 1)), serialize(&r, &b));
    }
}
