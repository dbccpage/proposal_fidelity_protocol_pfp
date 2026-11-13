//! Primitive — **declared bounds**: the finite candidate space.
//!
//! Crate boundary: coda-price.  Source: `candidates.py::Bounds`
//! (`max_items = 2`, `max_arity = 2`), the paper's declared resource bounds.
//!
//! ```text
//! L10  minimality is exhaustive over a declared finite space, or it is a
//!      conditional scope, and there is no third option
//! ```
//!
//! Every minimality claim in this crate is *relative to a `Bounds` value*,
//! and the value travels with the claim (`scope.rs`).  "Minimum cost two"
//! is a theorem over the item grammar; "three tied classes" is a bounded
//! theorem within `max_arity = 2`, and the sealed paper says so in clause
//! (d) of its terminal statement.  The Lean arity family shows the tie class
//! is infinite once the arity bound is lifted.  Bounds are not a limitation
//! to apologise for; they are what makes the count a count.

/// Declared finite bounds of the candidate space.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Bounds {
    /// The largest delta considered, in items.
    pub max_items: usize,
    /// The largest arity of a new form.
    pub max_arity: usize,
}

impl Default for Bounds {
    /// The sealed derivation's declared bounds.
    fn default() -> Bounds {
        Bounds { max_items: 2, max_arity: 2 }
    }
}

impl Bounds {
    /// Reject unsupported spaces before returning a scoped search result.
    pub fn validate(&self) -> Result<(), String> {
        if self.max_items > 2 {
            return Err("candidate enumeration supports max_items <= 2".into());
        }
        Ok(())
    }

    /// A one-line statement of the scope, for receipts.
    pub fn describe(&self) -> String {
        format!("max_items={} max_arity={}", self.max_items, self.max_arity)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn the_sealed_bounds_are_two_and_two() {
        let b = Bounds::default();
        assert_eq!((b.max_items, b.max_arity), (2, 2));
        assert_eq!(b.describe(), "max_items=2 max_arity=2");
    }
}
