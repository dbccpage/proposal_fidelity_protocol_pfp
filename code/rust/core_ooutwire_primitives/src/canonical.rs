//! Primitive — **canonical key**: `⌊Γ⌋`, and `≅` defined as equal keys.
//!
//! Crate boundary: coda-iso.  Source: `iso.py::canonical`,
//! `canonical_witness`, `canonical_bruteforce`, `find_iso`, `_refine`,
//! `_class_perms`.
//!
//! The key is the minimum, over all colour-class-preserving bijection pairs,
//! of the total serialisation of the regime.  Colour classes come from an
//! iterated, isomorphism-invariant refinement, so the minimum over the
//! refined class is the minimum over all bijections *for the purpose of
//! equality*: equal keys hold exactly for isomorphic regimes.  That claim is
//! not trusted; it is cross-checked against `canonical_bruteforce`, the
//! minimum over every bijection pair with no refinement at all (L11).
//!
//! ```text
//! ≅  is DEFINED as  ⌊Γ₁⌋ = ⌊Γ₂⌋   and is never a separate predicate
//! ```
//!
//! Two implementations of isomorphism is how an estate acquires two answers.
//! `FW-JUDGE`: isomorphism is decided here, by this algorithm, and nowhere
//! by judgement.
//!
//! The permutation budget is declared and **raises**; it never truncates
//! silently.  A truncated search that reports a key is a hidden-input
//! countermodel (`hidden.rs`).


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_2334e088<T> {
    fn checked_invariant_2334e088(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_2334e088<T> for Option<T> {
    #[inline]
    fn checked_invariant_2334e088(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_2334e088<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_2334e088(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::collections::BTreeMap;
use std::fmt;

use crate::regime::Regime;
use crate::renaming::{invert, permutations, serialize, Bijection, Key};

/// The declared permutation budget of the sealed derivation.
pub const PERM_BUDGET: u64 = 100_000;

/// The declared permutation budget was exceeded.  Raised, never absorbed.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct IsoBudgetError {
    /// Candidate count, saturated at u64::MAX on arithmetic overflow.
    pub candidates: u64,
    /// The declared budget.
    pub budget: u64,
}

impl fmt::Display for IsoBudgetError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{} candidate bijections exceed the declared budget {}", self.candidates, self.budget)
    }
}

impl std::error::Error for IsoBudgetError {}

/// Compress orderable colour values to dense integer ranks.
fn rank<T: Ord + Clone>(values: &[T]) -> Vec<usize> {
    let mut sorted: Vec<T> = values.to_vec();
    sorted.sort();
    sorted.dedup();
    values.iter().map(|v| sorted.binary_search(v).checked_invariant_2334e088("present")).collect()
}

type Occurrence = (usize, Vec<usize>, Vec<(usize, usize)>);
type DSig = (usize, Vec<Occurrence>, Vec<usize>);
type FSig = (usize, Vec<Vec<usize>>);

/// Iterated isomorphism-invariant colouring of data and forms.
pub fn refine(r: &Regime) -> (Vec<usize>, Vec<usize>) {
    let n = r.n_data();
    let nf = r.n_forms();
    let mut dcol = vec![0usize; n];
    let fseed: Vec<(usize, bool)> = (0..nf).map(|f| (r.forms[f], r.rules.contains(&f))).collect();
    let mut fcol = rank(&fseed);
    let insts: Vec<_> = r.insts.iter().collect();
    let reqs: Vec<_> = r.reqs.iter().collect();
    for _ in 0..(n + nf + 2) {
        let mut dsig: Vec<DSig> = Vec::with_capacity(n);
        for d in 0..n {
            let mut occ: Vec<Occurrence> = insts
                .iter()
                .filter(|i| i.args.iter().any(|m| m.0 == d))
                .map(|i| {
                    let positions: Vec<usize> =
                        i.args.iter().enumerate().filter(|(_, m)| m.0 == d).map(|(k, _)| k).collect();
                    let mut cols: Vec<(usize, usize)> =
                        i.args.iter().enumerate().map(|(k, m)| (k, dcol[m.0])).collect();
                    cols.sort();
                    (fcol[i.form], positions, cols)
                })
                .collect();
            occ.sort();
            let mut partners: Vec<usize> = reqs
                .iter()
                .filter(|p| p.contains(crate::mark::Mark(d)))
                .map(|p| dcol[p.other(crate::mark::Mark(d)).checked_invariant_2334e088("checked invariant").0])
                .collect();
            partners.sort();
            dsig.push((dcol[d], occ, partners));
        }
        let mut fsig: Vec<FSig> = Vec::with_capacity(nf);
        for (f, &fc) in fcol.iter().enumerate().take(nf) {
            let mut rows: Vec<Vec<usize>> = insts
                .iter()
                .filter(|i| i.form == f)
                .map(|i| i.args.iter().map(|m| dcol[m.0]).collect())
                .collect();
            rows.sort();
            fsig.push((fc, rows));
        }
        let new_d = rank(&dsig);
        let new_f = rank(&fsig);
        if new_d == dcol && new_f == fcol {
            break;
        }
        dcol = new_d;
        fcol = new_f;
    }
    (dcol, fcol)
}

/// All bijections sending each element to a position in the contiguous
/// block its colour class occupies when classes are ordered by colour.
fn class_perms(colors: &[usize]) -> Vec<Vec<usize>> {
    let mut classes: BTreeMap<usize, Vec<usize>> = BTreeMap::new();
    for (idx, &c) in colors.iter().enumerate() {
        classes.entry(c).or_default().push(idx);
    }
    let mut offsets: BTreeMap<usize, usize> = BTreeMap::new();
    let mut off = 0;
    for (&c, members) in &classes {
        offsets.insert(c, off);
        off += members.len();
    }
    let mut out: Vec<Vec<usize>> = vec![vec![0; colors.len()]];
    for (&c, members) in &classes {
        let images = permutations(members.len());
        let mut next = Vec::with_capacity(out.len() * images.len());
        for base in &out {
            for image in &images {
                let mut pi = base.clone();
                for (member, &slot) in members.iter().zip(image.iter()) {
                    pi[*member] = offsets[&c] + slot;
                }
                next.push(pi);
            }
        }
        out = next;
    }
    out
}

fn perm_count(colors: &[usize]) -> u64 {
    let mut counts: BTreeMap<usize, u64> = BTreeMap::new();
    for &c in colors {
        *counts.entry(c).or_insert(0) += 1;
    }
    counts.values().fold(1u64, |total, &k| {
        (2..=k).fold(total, |n, factor| n.saturating_mul(factor))
    })
}

/// The canonical key together with a bijection pair attaining it.
pub fn canonical_witness(r: &Regime, budget: u64) -> Result<(Key, Bijection), IsoBudgetError> {
    let (dcol, fcol) = refine(r);
    let total = perm_count(&dcol).saturating_mul(perm_count(&fcol));
    if total == u64::MAX || total > budget {
        return Err(IsoBudgetError { candidates: total, budget });
    }
    let mut best: Option<(Key, Bijection)> = None;
    for pi in class_perms(&dcol) {
        for phi in class_perms(&fcol) {
            let b = Bijection { data: pi.clone(), forms: phi.clone() };
            let k = serialize(r, &b);
            if best.as_ref().is_none_or(|(bk, _)| k < *bk) {
                best = Some((k, b));
            }
        }
    }
    Ok(best.checked_invariant_2334e088("at least the identity bijection"))
}

/// `⌊ ⌋` — the canonical key under the declared budget.  Panics only on a
/// budget overrun, which is a declared bound being hit and not a silent
/// truncation; use `try_canonical` to handle it.
pub fn canonical(r: &Regime) -> Key {
    try_canonical(r).checked_invariant_2334e088("permutation budget")
}

/// The canonical key, or the budget error.
pub fn try_canonical(r: &Regime) -> Result<Key, IsoBudgetError> {
    canonical_witness(r, PERM_BUDGET).map(|(k, _)| k)
}

/// Reference key: the minimum over **all** bijection pairs, no refinement.
/// Test use only; factorial.
pub fn canonical_bruteforce(r: &Regime) -> Key {
    let mut best: Option<Key> = None;
    for pi in permutations(r.n_data()) {
        for phi in permutations(r.n_forms()) {
            let k = serialize(r, &Bijection { data: pi.clone(), forms: phi });
            if best.as_ref().is_none_or(|bk| k < *bk) {
                best = Some(k);
            }
        }
    }
    best.checked_invariant_2334e088("identity")
}

/// Interoperable key, version 1: exhaustive structural minimum followed by
/// an injective, length-prefixed encoding of unsigned 64-bit integers.
/// This is a separate protocol from the historical refined local key.
/// Its budget counts all datum/form bijection pairs, before allocating them.
pub fn portable_key_v1(r: &Regime, budget: u64) -> Result<Vec<u8>, IsoBudgetError> {
    let total = perm_count(&vec![0; r.n_data()])
        .saturating_mul(perm_count(&vec![0; r.n_forms()]));
    if total == u64::MAX || total > budget {
        return Err(IsoBudgetError { candidates: total, budget });
    }
    Ok(encode_structural_key_v1(&canonical_bruteforce(r))
        .checked_invariant_2334e088("admitted regime fields fit the portable protocol"))
}

const PORTABLE_PREFIX: &[u8] = b"GENESIS-KEY\x00\x01";

/// Invalid structure, unsupported integer range, or malformed wire data.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PortableKeyError(pub &'static str);

impl fmt::Display for PortableKeyError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result { f.write_str(self.0) }
}

impl std::error::Error for PortableKeyError {}

fn is_strictly_sorted<T: Ord>(slice: &[T]) -> bool {
    !slice.windows(2).any(|w| w[0] >= w[1])
}

fn is_valid_portable_instance(n: usize, forms: &[usize], f: usize, args: &[usize]) -> bool {
    f < forms.len() && args.len() == forms[f] && args.iter().all(|&d| d < n)
}

fn validate_portable_key(key: &Key) -> Result<(), PortableKeyError> {
    let (n, forms, insts, rules, reqs) = key;
    if forms.contains(&0) { return Err(PortableKeyError("form arities must be positive")); }
    if insts.iter().any(|(f, args)| !is_valid_portable_instance(*n, forms, *f, args)) {
        return Err(PortableKeyError("invalid instance form, arity, or datum"));
    }
    if rules.iter().any(|f| *f >= forms.len()) {
        return Err(PortableKeyError("uniform-rule form is out of range"));
    }
    if reqs.iter().any(|(i, j)| i >= j || j >= n) {
        return Err(PortableKeyError("invalid requirement endpoints"));
    }
    if !is_strictly_sorted(insts) || !is_strictly_sorted(rules) || !is_strictly_sorted(reqs) {
        return Err(PortableKeyError("collections must be strictly sorted and duplicate-free"));
    }
    Ok(())
}

fn write_portable_word(out: &mut Vec<u8>, value: usize) -> Result<(), PortableKeyError> {
    let value = u64::try_from(value).map_err(|_| PortableKeyError("integer exceeds unsigned 64-bit range"))?;
    out.extend_from_slice(&value.to_be_bytes());
    Ok(())
}

fn write_portable_slice(out: &mut Vec<u8>, values: &[usize]) -> Result<(), PortableKeyError> {
    write_portable_word(out, values.len())?;
    for &v in values {
        write_portable_word(out, v)?;
    }
    Ok(())
}

fn write_portable_insts(out: &mut Vec<u8>, insts: &[(usize, Vec<usize>)]) -> Result<(), PortableKeyError> {
    write_portable_word(out, insts.len())?;
    for (form, args) in insts {
        write_portable_word(out, *form)?;
        write_portable_slice(out, args)?;
    }
    Ok(())
}

fn write_portable_reqs(out: &mut Vec<u8>, reqs: &[(usize, usize)]) -> Result<(), PortableKeyError> {
    write_portable_word(out, reqs.len())?;
    for (i, j) in reqs {
        write_portable_word(out, *i)?;
        write_portable_word(out, *j)?;
    }
    Ok(())
}

/// Encode a sorted structural tuple, without performing orbit minimization.
pub fn encode_structural_key_v1(key: &Key) -> Result<Vec<u8>, PortableKeyError> {
    validate_portable_key(key)?;
    let (n, forms, insts, rules, reqs) = key;
    let mut out = PORTABLE_PREFIX.to_vec();
    write_portable_word(&mut out, *n)?;
    write_portable_slice(&mut out, forms)?;
    write_portable_insts(&mut out, insts)?;
    write_portable_slice(&mut out, rules)?;
    write_portable_reqs(&mut out, reqs)?;
    Ok(out)
}

struct PortableCursor {
    words: Vec<usize>,
    at: usize,
}

impl PortableCursor {
    fn from_input(input: &[u8]) -> Result<Self, PortableKeyError> {
        let payload = input.strip_prefix(PORTABLE_PREFIX)
            .ok_or(PortableKeyError("invalid portable-key prefix or version"))?;
        if payload.len() % 8 != 0 {
            return Err(PortableKeyError("truncated unsigned 64-bit word"));
        }
        let mut words = Vec::new();
        for bytes in payload.chunks_exact(8) {
            let value = u64::from_be_bytes(bytes.try_into().checked_invariant_2334e088("eight-byte chunk"));
            words.push(usize::try_from(value).map_err(|_| PortableKeyError("word exceeds host index range"))?);
        }
        let cursor = Self { words, at: 0 };
        Ok(cursor)
    }

    fn remaining(&self) -> usize {
        self.words.len() - self.at
    }

    fn word(&mut self) -> Result<usize, PortableKeyError> {
        if self.remaining() == 0 {
            return Err(PortableKeyError("truncated structural fields"));
        }
        let value = self.words[self.at];
        self.at += 1;
        Ok(value)
    }

    fn counted(&mut self) -> Result<Vec<usize>, PortableKeyError> {
        let count = self.word()?;
        if count > self.remaining() {
            return Err(PortableKeyError("length exceeds remaining input"));
        }
        let values = self.words[self.at..self.at + count].to_vec();
        self.at += count;
        Ok(values)
    }

    fn read_insts(&mut self) -> Result<Vec<(usize, Vec<usize>)>, PortableKeyError> {
        let count = self.word()?;
        if count > self.remaining() / 2 {
            return Err(PortableKeyError("instance count exceeds remaining input"));
        }
        let mut insts = Vec::new();
        for _ in 0..count {
            insts.push((self.word()?, self.counted()?));
        }
        Ok(insts)
    }

    fn read_reqs(&mut self) -> Result<Vec<(usize, usize)>, PortableKeyError> {
        let count = self.word()?;
        if count > self.remaining() / 2 {
            return Err(PortableKeyError("requirement count exceeds remaining input"));
        }
        let mut reqs = Vec::new();
        for _ in 0..count {
            reqs.push((self.word()?, self.word()?));
        }
        Ok(reqs)
    }
}

/// Decode with bounded reads. Acceptance establishes shape and well-formedness,
/// not that this labelled tuple is the minimum of its isomorphism orbit.
pub fn decode_portable_key_v1(input: &[u8]) -> Result<Key, PortableKeyError> {
    let mut cursor = PortableCursor::from_input(input)?;
    let n = cursor.word()?;
    let forms = cursor.counted()?;
    let insts = cursor.read_insts()?;
    let rules = cursor.counted()?;
    let reqs = cursor.read_reqs()?;
    if cursor.remaining() != 0 {
        return Err(PortableKeyError("trailing portable-key data"));
    }
    let key = (n, forms, insts, rules, reqs);
    validate_portable_key(&key)?;
    Ok(key)
}

/// `≅` — defined as equal keys.
pub fn isomorphic(a: &Regime, b: &Regime) -> bool {
    canonical(a) == canonical(b)
}

/// A bijection pair carrying `a` exactly onto `b`'s structure, tokens
/// excluded, or `None`.  The returned pair is re-verified before return.
pub fn find_iso(a: &Regime, b: &Regime) -> Option<Bijection> {
    try_find_iso(a, b).checked_invariant_2334e088("permutation budget")
}

/// A bounded isomorphism search: resource exhaustion is not non-isomorphism.
pub fn try_find_iso(a: &Regime, b: &Regime) -> Result<Option<Bijection>, IsoBudgetError> {
    let (ka, wa) = canonical_witness(a, PERM_BUDGET)?;
    let (kb, wb) = canonical_witness(b, PERM_BUDGET)?;
    if ka != kb {
        return Ok(None);
    }
    let inv_pi_b = invert(&wb.data);
    let inv_phi_b = invert(&wb.forms);
    let dmap: Vec<usize> = (0..a.n_data()).map(|d| inv_pi_b[wa.data[d]]).collect();
    let fmap: Vec<usize> = (0..a.n_forms()).map(|f| inv_phi_b[wa.forms[f]]).collect();
    let b_map = Bijection { data: dmap, forms: fmap };
    let identity = Bijection::identity(b.n_data(), b.n_forms());
    assert_eq!(serialize(a, &b_map), serialize(b, &identity), "isomorphism witness failed re-verification");
    Ok(Some(b_map))
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/canonical.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:canonical:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::admission::step;
    use crate::bounds::Bounds;
    use crate::candidate::apply_delta;
    use crate::enumeration::iter_full_deltas;
    use crate::event::Event;
    use crate::reading::{READING_F, READING_L};
    use crate::renaming::rename;
    use crate::replay::replay;

    /// A population: every regime reached from both readings by at most two
    /// items of the declared grammar, plus a renaming of each.
    fn population() -> Vec<Regime> {
        let bounds = Bounds::default();
        let mut out = Vec::new();
        for reading in [&READING_L, &READING_F] {
            let base = replay(&reading.genesis).unwrap();
            let base = step(&base, &Event::Impose(reading.target)).unwrap();
            for cost in 0..=2 {
                for delta in iter_full_deltas(&base, cost, &bounds) {
                    let child = apply_delta(&base, &delta).unwrap();
                    let n = child.n_data();
                    let nf = child.n_forms();
                    let mut pi: Vec<usize> = (0..n).collect();
                    pi.reverse();
                    let mut phi: Vec<usize> = (0..nf).collect();
                    phi.reverse();
                    out.push(rename(&child, &Bijection { data: pi, forms: phi }));
                    out.push(child);
                }
            }
        }
        out
    }

    #[test]
    fn the_key_is_invariant_under_every_renaming() {
        for r in population().iter().take(400) {
            let k = canonical(r);
            for pi in permutations(r.n_data()) {
                for phi in permutations(r.n_forms()) {
                    let s = rename(r, &Bijection { data: pi.clone(), forms: phi });
                    assert_eq!(canonical(&s), k);
                }
            }
        }
    }

    /// L11: the refined key agrees with the unrefined reference on equality.
    #[test]
    fn refined_key_equality_agrees_with_brute_force() {
        let pop = population();
        let keys: Vec<Key> = pop.iter().map(canonical).collect();
        let brute: Vec<Key> = pop.iter().map(canonical_bruteforce).collect();
        let mut agreements = 0;
        for a in 0..pop.len() {
            for b in (a + 1)..pop.len() {
                assert_eq!(keys[a] == keys[b], brute[a] == brute[b]);
                agreements += 1;
            }
        }
        assert!(agreements > 1000);
    }

    #[test]
    fn find_iso_returns_a_verified_witness_exactly_when_isomorphic() {
        let pop = population();
        let mut found = 0;
        for a in pop.iter().take(60) {
            for b in pop.iter().take(60) {
                match find_iso(a, b) {
                    Some(w) => {
                        assert!(isomorphic(a, b));
                        let identity = Bijection::identity(b.n_data(), b.n_forms());
                        assert_eq!(serialize(a, &w), serialize(b, &identity));
                        found += 1;
                    }
                    None => assert!(!isomorphic(a, b)),
                }
            }
        }
        assert!(found >= 60, "at least every regime is isomorphic to itself");
    }

    #[test]
    fn the_budget_raises_rather_than_truncating() {
        // Eight data, no structure: 8! = 40320 bijections, under budget.
        let mut r = Regime::genesis();
        for k in 0..8 {
            r = step(&r, &Event::AdmitDatum(crate::token::Token::new(format!("t{k}")))).unwrap();
        }
        assert!(try_canonical(&r).is_ok());
        // Nine data: 9! = 362880, over the declared 100000.
        r = step(&r, &Event::AdmitDatum(crate::token::Token::new("t8"))).unwrap();
        let err = try_canonical(&r).unwrap_err();
        assert_eq!(err.candidates, 362_880);
        assert!(try_find_iso(&r, &r).is_err());
        for k in 9..21 {
            r = step(&r, &Event::AdmitDatum(crate::token::Token::new(format!("t{k}")))).unwrap();
        }
        assert_eq!(canonical_witness(&r, u64::MAX).unwrap_err().candidates, u64::MAX);
    }

    #[test]
    fn portable_keys_preserve_renaming_and_refuse_exhaustion() {
        for r in population().iter().take(80) {
            let key = portable_key_v1(r, PERM_BUDGET).unwrap();
            assert_eq!(decode_portable_key_v1(&key).unwrap(), canonical_bruteforce(r));
            let mut b = Bijection::identity(r.n_data(), r.n_forms());
            b.data.reverse();
            b.forms.reverse();
            assert_eq!(key, portable_key_v1(&rename(r, &b), PERM_BUDGET).unwrap());
            assert!(portable_key_v1(r, 0).is_err());
        }
    }

    #[test]
    fn portable_wire_boundaries_and_malformed_inputs() {
        let empty: Key = (0, vec![], vec![], vec![], vec![]);
        let encoded = encode_structural_key_v1(&empty).unwrap();
        assert_eq!(encoded, [PORTABLE_PREFIX, &[0; 40]].concat());
        for length in 0..encoded.len() {
            assert!(decode_portable_key_v1(&encoded[..length]).is_err());
        }
        let mut trailing = encoded.clone();
        trailing.extend_from_slice(&[0; 8]);
        assert!(decode_portable_key_v1(&trailing).is_err());
        let mut oversized = encoded.clone();
        oversized[21..29].copy_from_slice(&u64::MAX.to_be_bytes());
        assert!(decode_portable_key_v1(&oversized).is_err());
        assert!(encode_structural_key_v1(&(0, vec![0], vec![], vec![], vec![])).is_err());
        assert!(encode_structural_key_v1(&(1, vec![1], vec![(0, vec![1])], vec![], vec![])).is_err());
        assert!(encode_structural_key_v1(&(2, vec![], vec![], vec![], vec![(1, 0)])).is_err());
        let maximum: Key = (usize::MAX, vec![usize::MAX], vec![], vec![], vec![]);
        assert_eq!(decode_portable_key_v1(&encode_structural_key_v1(&maximum).unwrap()).unwrap(), maximum);
    }
}
