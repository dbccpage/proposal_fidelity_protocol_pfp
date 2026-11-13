//! Primitive — **imposition**: an externally imposed requirement.
//!
//! Crate boundary: coda-carrier.  Source: `model.py::Impose` and
//! `Regime.reqs`.
//!
//! A requirement is *persistent*: once imposed it constrains every later
//! response (`response.rs` checks all of `reqs`, not only the newest).  It is
//! also *external*: the sealed derivation never derived a demand from inside
//! the object language — that is `OB-1`, the standing obstruction, and it is
//! why the Core engine takes its demands from `outside.rs` and nowhere else.
//!
//! A requirement is not yet an *active obstruction*.  Recording `(i, j)` says
//! the pair must become separable; an obstruction is that record **plus** the
//! exhaustive failure of the declared menu (`obstruction.rs`).  The estate
//! keeps the two apart because an engine that calls every failed check an
//! obstruction is guessing.

use crate::event::AdmissionError;
use crate::mark::Pair;
use crate::regime::Regime;

/// Impose the persistent requirement that `pair` be internally separable.
/// Both marks must be admitted.
pub fn impose(r: &Regime, pair: Pair) -> Result<Regime, AdmissionError> {
    if !r.has_mark(pair.j) {
        return Err(AdmissionError(format!("requirement out of range: {pair}")));
    }
    let mut out = r.clone();
    out.reqs.insert(pair);
    Ok(out)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::reading::READING_L;
    use crate::replay::replay;

    #[test]
    fn a_requirement_is_recorded_and_persists() {
        let base = replay(&READING_L.genesis).unwrap();
        let r = impose(&base, Pair::of(0, 1)).unwrap();
        assert!(r.reqs.contains(&Pair::of(0, 1)));
        let again = impose(&r, Pair::of(0, 1)).unwrap();
        assert_eq!(again, r, "imposing twice records once");
    }

    #[test]
    fn a_requirement_on_an_unadmitted_mark_is_refused() {
        let base = replay(&READING_L.genesis).unwrap();
        assert!(impose(&base, Pair::of(0, 2)).is_err());
    }
}
