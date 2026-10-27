//! Exact finite Mermin–Peres parity assignments and their replayable F2 class.
//! AuthorityEffect: None.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_4504cc6c<T> {
    fn checked_invariant_4504cc6c(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_4504cc6c<T> for Option<T> {
    #[inline]
    fn checked_invariant_4504cc6c(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_4504cc6c<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_4504cc6c(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::parity_context_packet::{ImageCertificate, ParityContextPacket, ParityPacketError};
use core_homology::graph_f2::MAX_BITS;
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; finite declared parity carrier";
/// Refusals of the Mermin–Peres search and bridge.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum MerminPeresError {
    #[error("{products} context products were declared for {contexts} contexts")]
    UnpairedProducts { contexts: usize, products: usize },
    #[error("context {context} is empty")]
    EmptyContext { context: usize },
    #[error("context {context} names observable {name} twice")]
    RepeatedObservable { context: usize, name: String },
    #[error("context {context} has product {value}, which is not a sign")]
    NotASign { context: usize, value: i8 },
    #[error("{observables} observables exceed the search bound of {max}")]
    TooManyObservables { observables: usize, max: usize },
    #[error("parity packet: {0}")]
    Packet(#[from] ParityPacketError),
}

/// The exhaustive search visits `2^n` assignments of `n` observables and
/// refuses beyond this bound. It equals `binary_pattern_carrier::MAX_BITS`,
/// so `ParityContextPacket` decides every square the search accepts that has
/// at most that many contexts.
pub const MAX_SEARCH_OBSERVABLES: usize = MAX_BITS;

/// Mermin–Peres magic square: operator assignment obstruction.
///
/// Observables are named; each context lists observables and carries a
/// declared product `+1` or `-1`. A noncontextual assignment gives every
/// observable a value `+1` or `-1` so that each context multiplies to its
/// declared product. Whether one exists is computed by
/// [`MerminPeresSquare::find_noncontextual_assignment`].
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MerminPeresSquare {
    /// Context hypergraph edges (each row/column is a context of 3 observables).
    pub contexts: Vec<Vec<&'static str>>,
    /// Declared product of operators in each context (+1 or −1).
    pub context_products: Vec<i8>,
    /// Declared, not computed: whether the source says a noncontextual
    /// assignment exists (`false` for the magic square). No search in this
    /// crate reads it; [`MerminPeresSquare::verify_no_noncontextual_assignment`]
    /// decides the question from the contexts and products.
    pub noncontextual_assignment_exists: bool,
}

impl crate::parity_context_packet::SignedContextFamily for MerminPeresSquare {
    fn named_contexts(&self) -> &[Vec<&'static str>] {
        &self.contexts
    }
    fn context_signs(&self) -> &[i8] {
        &self.context_products
    }
}

/// A square in parity form: observables in order of first appearance, each
/// context as a bit mask over them, and each declared product as a bit
/// (`1` for `-1`).
struct ParityForm {
    observables: Vec<&'static str>,
    masks: Vec<u32>,
    targets: Vec<u32>,
}

impl MerminPeresSquare {
    /// Standard magic-square product pattern (last column product −1, others +1
    /// in the usual operator realization — here we encode the inconsistency
    /// of trying to assign ±1 with all row products +1 and column products
    /// forcing a contradiction).
    pub fn standard() -> Self {
        // Observables A11..A33
        let contexts = vec![
            vec!["A11", "A12", "A13"], // row1
            vec!["A21", "A22", "A23"], // row2
            vec!["A31", "A32", "A33"], // row3
            vec!["A11", "A21", "A31"], // col1
            vec!["A12", "A22", "A32"], // col2
            vec!["A13", "A23", "A33"], // col3
        ];
        // Operator quantum prediction: five contexts product +1, one −1 (col3).
        let context_products = vec![1, 1, 1, 1, 1, -1];
        Self {
            contexts,
            context_products,
            noncontextual_assignment_exists: false,
        }
    }

    /// The distinct observables, in order of first appearance.
    pub fn observables(&self) -> Vec<&'static str> {
        let mut names: Vec<&'static str> = Vec::new();
        for context in &self.contexts {
            for &name in context {
                if !names.contains(&name) {
                    names.push(name);
                }
            }
        }
        names
    }

    /// Validates the square and puts it in parity form. Refuses a product
    /// list whose length differs from the context count, an empty context, an
    /// observable named twice in one context, a product other than `+1` or
    /// `-1`, and more than [`MAX_SEARCH_OBSERVABLES`] observables.
    fn parity_form(&self) -> Result<ParityForm, MerminPeresError> {
        if self.context_products.len() != self.contexts.len() {
            return Err(MerminPeresError::UnpairedProducts {
                contexts: self.contexts.len(),
                products: self.context_products.len(),
            });
        }
        for (context, (names, &value)) in
            self.contexts.iter().zip(&self.context_products).enumerate()
        {
            if names.is_empty() {
                return Err(MerminPeresError::EmptyContext { context });
            }
            for (k, name) in names.iter().enumerate() {
                if names[..k].contains(name) {
                    return Err(MerminPeresError::RepeatedObservable {
                        context,
                        name: (*name).to_string(),
                    });
                }
            }
            if value != 1 && value != -1 {
                return Err(MerminPeresError::NotASign { context, value });
            }
        }
        let observables = self.observables();
        if observables.len() > MAX_SEARCH_OBSERVABLES {
            return Err(MerminPeresError::TooManyObservables {
                observables: observables.len(),
                max: MAX_SEARCH_OBSERVABLES,
            });
        }
        let masks = self
            .contexts
            .iter()
            .map(|names| {
                names.iter().fold(0u32, |mask, name| {
                    let index = observables
                        .iter()
                        .position(|o| o == name)
                        .checked_invariant_4504cc6c("every name was collected");
                    mask | (1 << index)
                })
            })
            .collect();
        let targets = self
            .context_products
            .iter()
            .map(|&value| u32::from(value == -1))
            .collect();
        Ok(ParityForm {
            observables,
            masks,
            targets,
        })
    }

    /// Exhaustive search over all `2^n` assignments of the `n` observables, in
    /// increasing order of the mask whose bit `k` is set when observable `k`
    /// (first-appearance order) takes the value `-1`. Returns the first
    /// assignment that meets every declared product, as values `+1`/`-1` in
    /// observable order, or `None` when there is none. The declared flag
    /// `noncontextual_assignment_exists` is not read.
    pub fn find_noncontextual_assignment(&self) -> Result<Option<Vec<i8>>, MerminPeresError> {
        let form = self.parity_form()?;
        let n = form.observables.len();
        for a in 0u32..(1u32 << n) {
            if form
                .masks
                .iter()
                .zip(&form.targets)
                .all(|(&mask, &target)| (a & mask).count_ones() % 2 == target)
            {
                return Ok(Some(
                    (0..n)
                        .map(|k| if (a >> k) & 1 == 1 { -1 } else { 1 })
                        .collect(),
                ));
            }
        }
        Ok(None)
    }

    /// `Ok(true)` when no noncontextual assignment exists, decided by
    /// [`MerminPeresSquare::find_noncontextual_assignment`]; refuses what it refuses.
    pub fn verify_no_noncontextual_assignment(&self) -> Result<bool, MerminPeresError> {
        Ok(self.find_noncontextual_assignment()?.is_none())
    }
}

/// The Mermin–Peres sign table as a degree-two class.
///
/// Read the observables as the 1-cells and the contexts as the 2-cells of a
/// 2-dimensional complex, with observable `o` on the boundary of face `c`
/// exactly when `o` lies in context `c`. The declared signs are a 2-cochain
/// `s` (`1` where the product is `-1`), and a noncontextual assignment is
/// exactly a 1-cochain `a` with `delta a = s`, where `(delta a)(c)` is the sum
/// of `a` over context `c` mod 2. With no 3-cells, `H^2 = C^2 / im delta`, so
/// the class of `s` is decided by membership in `im delta` alone. The bridge
/// decides it with [`ParityContextPacket`] (the same incidence, with the
/// observables as its variables) and keeps the certificate: a preimage when
/// the class vanishes, a separator (a mod-2 2-cycle that pairs to `1` with
/// `s`) when it does not.
///
/// Not computed here: vertices for such a complex. Without them the bridge
/// does not show that the faces close up into a surface;
/// `tests/synthesis/noncommutative_readout_algebra.rs` supplies three vertices
/// for the standard square and checks that it is a closed surface.
///
/// The product of all declared signs is the pairing of `s` with the sum of all
/// faces, which is a 2-cycle exactly when every observable lies in an even
/// number of contexts (`even_incidence`). Only then does a product of `-1`
/// certify a nonzero class, and a product of `+1` never shows that the class
/// vanishes.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MerminPeresCochainBridge {
    pub square: MerminPeresSquare,
    /// Degree of the sign cochain in the complex above.
    pub cochain_degree: u8,
    /// Product of the declared context signs.
    pub product_of_context_constraints: i8,
    /// Every observable lies in an even number of contexts, so the sum of all
    /// faces is a mod-2 2-cycle.
    pub even_incidence: bool,
    /// `1` when the computed class is nonzero, `0` when it vanishes.
    pub obstruction_mass: u8,
    /// The computed preimage or separator of the sign cochain.
    pub certificate: ImageCertificate,
    pub note: &'static str,
}

impl MerminPeresCochainBridge {
    /// Computes the class of the declared signs of `square`. Refuses what
    /// [`MerminPeresSquare::find_noncontextual_assignment`] refuses, and
    /// squares that [`ParityContextPacket::from_square`] refuses (more than
    /// `binary_pattern_carrier::MAX_BITS` contexts).
    pub fn from_square(square: MerminPeresSquare) -> Result<Self, MerminPeresError> {
        square.parity_form()?;
        let packet = ParityContextPacket::from_square(&square)?;
        let certificate = packet.certificate(packet.targets())?;
        let obstruction_mass = match certificate {
            ImageCertificate::Preimage(_) => 0,
            ImageCertificate::Separator(_) => 1,
        };
        let even_incidence = packet.incidence_counts().iter().all(|count| count % 2 == 0);
        let product_of_context_constraints = square.context_products.iter().product();
        Ok(Self {
            square,
            cochain_degree: 2,
            product_of_context_constraints,
            even_incidence,
            obstruction_mass,
            certificate,
            note: "Observables as 1-cells and contexts as 2-cells: the declared signs are a \
                   2-cochain, a noncontextual assignment is a 1-cochain with that coboundary, \
                   and with no 3-cells the class in H^2 = C^2 / im delta is decided by exact \
                   F_2 membership (ParityContextPacket), with a replayable preimage or \
                   separator. The vertices of the complex are not constructed here.",
        })
    }

    pub fn from_standard_square() -> Result<Self, MerminPeresError> {
        Self::from_square(MerminPeresSquare::standard())
    }

    /// The computed class of the declared signs is nonzero. Reads no declared flag.
    pub fn is_obstructed(&self) -> bool {
        self.obstruction_mass > 0
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/separating_predictions.rs
// Claim: urn:core:crates_rs:core-quantum-physics:separating-predictions:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn mermin_peres_no_noncontextual_assignment() {
        let sq = MerminPeresSquare::standard();
        assert_eq!(sq.verify_no_noncontextual_assignment(), Ok(true));
        assert_eq!(sq.find_noncontextual_assignment(), Ok(None));
    }

    #[test]
    fn mermin_peres_cochain_bridge_obstructed() {
        let b = MerminPeresCochainBridge::from_standard_square().unwrap();
        assert_eq!(b.product_of_context_constraints, -1);
        assert!(b.even_incidence);
        assert!(b.is_obstructed());
        assert!(matches!(b.certificate, ImageCertificate::Separator(_)));
        assert_eq!(b.cochain_degree, 2);
    }

    #[test]
    fn separating_authority_none() {
        assert!(AUTHORITY_FENCE.contains("AuthorityEffect None"));
    }
}
