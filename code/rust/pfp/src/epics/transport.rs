//! Functorial carrier transport with exact loss accounting.
//!
//! `EPIC-OE-SYMGAM-006` asks for `SimplicialMorphism`, functorial pushforward
//! and pullback, a `TransportCertificateV1`, and a `LossLedgerV1` whose loss is
//! exactly additive across chained transports.
//!
//! # Where this lives
//!
//! This algebra belongs to `pfp::epics`. The native host imports
//! it through the explicit `simplicial_transport` runtime action. Transport is
//! defined over the finite carriers `f2` already models; the host owns the
//! process seam and reports the actual map and loss certificate.
//!
//! The dependency direction settles it. A host that wants transport imports it;
//! a transport module does not need a host. Defining pure carrier mathematics
//! inside the seam-bearing crate would put a process boundary between a functor
//! and its own composition law.
//!
//! # Additivity is only true if each stage is measured on what it receives
//!
//! Criterion 3 requires `ΔI(G ∘ F) = ΔI(F) + ΔI(G)` exactly. That is **not**
//! true if `ΔI(G)` is measured over all of `G`'s domain: `G` may collapse
//! vertices that `F`'s image never reaches, and those collapses cost nothing
//! because nothing arrived there.
//!
//! Loss is therefore always measured **relative to a carrier that is actually
//! present**:
//!
//! ```text
//! DeltaI(F over S)  :=  |S|  -  |F(S)|
//! ```
//!
//! and the chain rule follows by telescoping:
//!
//! ```text
//! (|S| - |F(S)|) + (|F(S)| - |G(F(S))|)  =  |S| - |G(F(S))|
//! ```
//!
//! Every intermediate term cancels, so the sum is exact with no residual. This
//! is why [`LossLedgerV1::for_chain`] takes the *support* the transport starts
//! from rather than assuming the whole domain: the epic's additivity claim is
//! true of the first reading and false of the second, and the difference is
//! invisible until a fixture makes `G` lossy outside `F`'s image.
//!
//! # Loss is a rational, and no float can reach it
//!
//! Criterion 3 says the accumulation must be over `Q` "with no rounding term".
//! `ΔI` is carried as `Ratio<i64>` throughout, and a source-level gate asserts
//! the implementation half of this module contains neither Rust float type.
//! The gate is scoped above `#[cfg(test)]` and the prose here says "float"
//! rather than naming the types, because a text-scanning ban that includes the
//! sentence declaring it can never pass.
//!
//! # Orientation
//!
//! A simplicial map preserves orientation when its vertex map is monotone
//! non-decreasing: `v < w` implies `F(v) <= F(w)`. A map that inverts any pair
//! reverses orientation on the simplex spanning them, and is **refused** rather
//! than silently absorbed.
//!
//! `AuthorityEffect: None`. A transport certificate records what a map did to a
//! carrier. It does not license the map.

use num_rational::Ratio;
use serde::{Deserialize, Serialize};
use thiserror::Error;

/// The certificate schema this module emits.
pub const TRANSPORT_CERTIFICATE_SCHEMA_V1: &str = "core.symgam.transport-certificate.v1";

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum TransportError {
    #[error("vertex {vertex} maps to {image}, outside the target's {target_vertices} vertices")]
    ImageOutOfRange {
        vertex: usize,
        image: usize,
        target_vertices: usize,
    },

    #[error("the morphism has no vertices; an empty carrier transports nothing")]
    EmptyCarrier,

    #[error("the target declares no vertices")]
    EmptyTarget,

    #[error(
        "vertex {left} < {right} but maps to {left_image} > {right_image}; orientation reversed"
    )]
    OrientationReversed {
        left: usize,
        right: usize,
        left_image: usize,
        right_image: usize,
    },

    // `source` is a magic field name in `thiserror` -- it is taken as the error
    // cause and must implement `Error`. Named `starts_from` for that reason.
    #[error("cannot compose: the first map lands in {target} vertices, the second starts from {starts_from}")]
    CarrierMismatch { target: usize, starts_from: usize },

    #[error("chain has {actual} entries; the source carrier has {expected} vertices")]
    ChainLength { expected: usize, actual: usize },

    #[error("cochain has {actual} entries; the target carrier has {expected} vertices")]
    CochainLength { expected: usize, actual: usize },

    #[error("the ledger claims {claimed} lost, the carrier shows {measured}")]
    LedgerDisagreesWithCarrier { claimed: String, measured: String },

    #[error("support vertex {vertex} is outside the source's {source_vertices} vertices")]
    SupportOutOfRange {
        vertex: usize,
        source_vertices: usize,
    },
}

// ---------------------------------------------------------------------------
// Morphisms
// ---------------------------------------------------------------------------

/// An orientation-preserving simplicial map, given by its vertex map.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SimplicialMorphism {
    vertex_map: Vec<usize>,
    target_vertices: usize,
}

impl SimplicialMorphism {
    /// Build a map, refusing anything that leaves the target or reverses
    /// orientation.
    pub fn new(vertex_map: Vec<usize>, target_vertices: usize) -> Result<Self, TransportError> {
        if vertex_map.is_empty() {
            return Err(TransportError::EmptyCarrier);
        }
        if target_vertices == 0 {
            return Err(TransportError::EmptyTarget);
        }
        for (vertex, image) in vertex_map.iter().enumerate() {
            if *image >= target_vertices {
                return Err(TransportError::ImageOutOfRange {
                    vertex,
                    image: *image,
                    target_vertices,
                });
            }
        }
        for window in vertex_map.windows(2).enumerate() {
            let (left, pair) = window;
            if pair[0] > pair[1] {
                return Err(TransportError::OrientationReversed {
                    left,
                    right: left + 1,
                    left_image: pair[0],
                    right_image: pair[1],
                });
            }
        }
        Ok(Self {
            vertex_map,
            target_vertices,
        })
    }

    /// The identity on `vertices` vertices.
    pub fn identity(vertices: usize) -> Result<Self, TransportError> {
        Self::new((0..vertices).collect(), vertices.max(1))
    }

    pub fn source_vertices(&self) -> usize {
        self.vertex_map.len()
    }

    pub fn target_vertices(&self) -> usize {
        self.target_vertices
    }

    pub fn image_of(&self, vertex: usize) -> Option<usize> {
        self.vertex_map.get(vertex).copied()
    }

    pub fn is_identity(&self) -> bool {
        self.target_vertices == self.vertex_map.len()
            && self
                .vertex_map
                .iter()
                .enumerate()
                .all(|(vertex, image)| vertex == *image)
    }

    /// `G ∘ F`, defined when `F`'s target is `G`'s source.
    pub fn compose(&self, then: &SimplicialMorphism) -> Result<Self, TransportError> {
        if self.target_vertices != then.source_vertices() {
            return Err(TransportError::CarrierMismatch {
                target: self.target_vertices,
                starts_from: then.source_vertices(),
            });
        }
        let composed: Vec<usize> = self
            .vertex_map
            .iter()
            .map(|image| then.vertex_map[*image])
            .collect();
        Self::new(composed, then.target_vertices)
    }

    /// `F_*`: push a chain forward, summing over fibres.
    ///
    /// Over `F2` the fibre sum is an XOR, so two source vertices landing on one
    /// target vertex with equal coefficients cancel -- which is exactly the
    /// information the loss ledger has to account for.
    pub fn pushforward(&self, chain: &[bool]) -> Result<Vec<bool>, TransportError> {
        if chain.len() != self.vertex_map.len() {
            return Err(TransportError::ChainLength {
                expected: self.vertex_map.len(),
                actual: chain.len(),
            });
        }
        let mut out = vec![false; self.target_vertices];
        for (vertex, present) in chain.iter().enumerate() {
            if *present {
                out[self.vertex_map[vertex]] ^= true;
            }
        }
        Ok(out)
    }

    /// `F^*`: pull a cochain back. Contravariant by construction.
    pub fn pullback(&self, cochain: &[bool]) -> Result<Vec<bool>, TransportError> {
        if cochain.len() != self.target_vertices {
            return Err(TransportError::CochainLength {
                expected: self.target_vertices,
                actual: cochain.len(),
            });
        }
        Ok(self
            .vertex_map
            .iter()
            .map(|image| cochain[*image])
            .collect())
    }

    /// The vertices this map actually reaches from `support`.
    fn image_of_support(&self, support: &[usize]) -> Vec<usize> {
        let mut images: Vec<usize> = support
            .iter()
            .map(|vertex| self.vertex_map[*vertex])
            .collect();
        images.sort_unstable();
        images.dedup();
        images
    }
}

// ---------------------------------------------------------------------------
// Loss
// ---------------------------------------------------------------------------

/// Exact information loss across one transport, measured on a stated support.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct LossLedgerV1 {
    /// `|S|` -- how many distinct carrier vertices entered.
    pub support_size: usize,
    /// `|F(S)|` -- how many distinct vertices survived.
    pub image_size: usize,
    pub delta_i_numerator: i64,
    pub delta_i_denominator: i64,
}

impl LossLedgerV1 {
    /// `ΔI = |S| - |F(S)|`, measured on the support actually presented.
    ///
    /// Taking the support as an argument rather than assuming the whole domain
    /// is what makes additivity exact -- see the module docstring.
    pub fn measure(
        morphism: &SimplicialMorphism,
        support: &[usize],
    ) -> Result<Self, TransportError> {
        for vertex in support {
            if *vertex >= morphism.source_vertices() {
                return Err(TransportError::SupportOutOfRange {
                    vertex: *vertex,
                    source_vertices: morphism.source_vertices(),
                });
            }
        }
        let mut distinct = support.to_vec();
        distinct.sort_unstable();
        distinct.dedup();
        let image = morphism.image_of_support(&distinct);
        let delta = Ratio::new(distinct.len() as i64 - image.len() as i64, 1);
        Ok(Self {
            support_size: distinct.len(),
            image_size: image.len(),
            delta_i_numerator: *delta.numer(),
            delta_i_denominator: *delta.denom(),
        })
    }

    pub fn delta_i(&self) -> Ratio<i64> {
        Ratio::new(self.delta_i_numerator, self.delta_i_denominator)
    }

    pub fn is_lossless(&self) -> bool {
        self.delta_i() == Ratio::new(0, 1)
    }

    /// The per-stage ledgers for a chain, each measured on what it receives.
    pub fn for_chain(
        first: &SimplicialMorphism,
        then: &SimplicialMorphism,
        support: &[usize],
    ) -> Result<(Self, Self), TransportError> {
        let head = Self::measure(first, support)?;
        let mut distinct = support.to_vec();
        distinct.sort_unstable();
        distinct.dedup();
        let arrived = first.image_of_support(&distinct);
        let tail = Self::measure(then, &arrived)?;
        Ok((head, tail))
    }

    /// Re-measure and refuse a ledger the carrier does not support.
    ///
    /// Criterion 4: the ledger and the post-image are cross-checked rather than
    /// trusted. A transport claiming zero loss while collapsing a vertex is
    /// rejected here.
    pub fn verify(
        &self,
        morphism: &SimplicialMorphism,
        support: &[usize],
    ) -> Result<(), TransportError> {
        let measured = Self::measure(morphism, support)?;
        if measured != *self {
            return Err(TransportError::LedgerDisagreesWithCarrier {
                claimed: format!(
                    "{}/{} over {} vertices",
                    self.delta_i_numerator, self.delta_i_denominator, self.support_size
                ),
                measured: format!(
                    "{}/{} over {} vertices",
                    measured.delta_i_numerator, measured.delta_i_denominator, measured.support_size
                ),
            });
        }
        Ok(())
    }
}

// ---------------------------------------------------------------------------
// Certificate
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct TransportCertificateV1 {
    pub schema_version: String,
    pub source_vertices: usize,
    pub target_vertices: usize,
    /// `|F(S)| - |S|`: negative when the map collapses, zero when injective on
    /// the support. Recorded as a signed count, never as a ratio of sizes.
    pub dimensional_dilation: i64,
    /// How many support vertices changed index under the map.
    pub boundary_deformation: usize,
    pub ledger: LossLedgerV1,
    pub identity: bool,
    pub authority_effect: String,
}

impl TransportCertificateV1 {
    pub fn issue(morphism: &SimplicialMorphism, support: &[usize]) -> Result<Self, TransportError> {
        let ledger = LossLedgerV1::measure(morphism, support)?;
        let mut distinct = support.to_vec();
        distinct.sort_unstable();
        distinct.dedup();
        let moved = distinct
            .iter()
            .filter(|vertex| morphism.vertex_map[**vertex] != **vertex)
            .count();
        Ok(Self {
            schema_version: TRANSPORT_CERTIFICATE_SCHEMA_V1.to_string(),
            source_vertices: morphism.source_vertices(),
            target_vertices: morphism.target_vertices(),
            dimensional_dilation: ledger.image_size as i64 - ledger.support_size as i64,
            boundary_deformation: moved,
            ledger,
            identity: morphism.is_identity(),
            authority_effect: "None".to_string(),
        })
    }
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

// Origin: engine/crates_rs/pfp/src/epics/transport.rs
// Claim: urn:core:crates_rs:pfp:transport:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn morphism(map: &[usize], target: usize) -> SimplicialMorphism {
        SimplicialMorphism::new(map.to_vec(), target).expect("fixture must build")
    }

    fn bits(pattern: &[u8]) -> Vec<bool> {
        pattern.iter().map(|b| *b == 1).collect()
    }

    fn ratio(numerator: i64) -> Ratio<i64> {
        Ratio::new(numerator, 1)
    }

    /// F collapses {0,1} -> 0 on a 4-vertex source; G collapses {2,3} -> 2,
    /// which is **outside F's image**. That is what makes additivity
    /// non-trivial: measuring G over its whole domain would overcount.
    fn chain_where_g_is_lossy_outside_f() -> (SimplicialMorphism, SimplicialMorphism) {
        let f = morphism(&[0, 0, 1, 2], 4);
        let g = morphism(&[0, 1, 2, 2], 3);
        (f, g)
    }

    // -- AC1: functoriality -------------------------------------------------

    #[test]
    fn pushforward_is_covariant_over_a_chain() {
        let (f, g) = chain_where_g_is_lossy_outside_f();
        let composed = f.compose(&g).expect("must compose");
        for mask in 0..16u8 {
            let chain: Vec<bool> = (0..4).map(|bit| mask >> bit & 1 == 1).collect();
            let stepwise = g
                .pushforward(&f.pushforward(&chain).expect("ok"))
                .expect("ok");
            assert_eq!(
                composed.pushforward(&chain).expect("ok"),
                stepwise,
                "(G o F)_* disagreed with G_* o F_* on {chain:?}"
            );
        }
    }

    #[test]
    fn pullback_is_contravariant_over_a_chain() {
        let (f, g) = chain_where_g_is_lossy_outside_f();
        let composed = f.compose(&g).expect("must compose");
        for mask in 0..8u8 {
            let cochain: Vec<bool> = (0..3).map(|bit| mask >> bit & 1 == 1).collect();
            let stepwise = f.pullback(&g.pullback(&cochain).expect("ok")).expect("ok");
            assert_eq!(
                composed.pullback(&cochain).expect("ok"),
                stepwise,
                "(G o F)^* disagreed with F^* o G^* on {cochain:?}"
            );
        }
    }

    #[test]
    fn the_contravariance_fixture_actually_distinguishes_the_two_orders() {
        // Without this, reversing the pullback order could be invisible: on a
        // fixture where F and G happen to commute, both orders agree.
        let (f, g) = chain_where_g_is_lossy_outside_f();
        let cochain = bits(&[1, 0, 0]);
        let correct = f.pullback(&g.pullback(&cochain).expect("ok")).expect("ok");
        // The reversed order is not even well-typed here: g.pullback expects
        // 3 entries and f.pullback expects 4. That the shapes differ is itself
        // the guard, and it is asserted rather than assumed.
        assert_eq!(correct.len(), 4);
        assert_eq!(g.pullback(&cochain).expect("ok").len(), 4);
        assert!(f.pullback(&cochain).is_err(), "shapes must not coincide");
    }

    #[test]
    fn pushforward_cancels_over_a_collapsed_fibre() {
        // Two source vertices land on one target vertex; over F2 they cancel.
        // This is the information the ledger has to account for.
        let f = morphism(&[0, 0, 1], 2);
        assert_eq!(f.pushforward(&bits(&[1, 1, 0])).expect("ok"), bits(&[0, 0]));
        assert_eq!(f.pushforward(&bits(&[1, 0, 0])).expect("ok"), bits(&[1, 0]));
    }

    #[test]
    fn composition_refuses_mismatched_carriers() {
        let f = morphism(&[0, 1], 2);
        let g = morphism(&[0, 1, 2], 3);
        assert_eq!(
            f.compose(&g).expect_err("must refuse"),
            TransportError::CarrierMismatch {
                target: 2,
                starts_from: 3
            }
        );
    }

    // -- AC2: identity transports exactly -----------------------------------

    #[test]
    fn the_identity_pushes_a_chain_forward_unchanged() {
        let id = SimplicialMorphism::identity(4).expect("ok");
        for mask in 0..16u8 {
            let chain: Vec<bool> = (0..4).map(|bit| mask >> bit & 1 == 1).collect();
            assert_eq!(id.pushforward(&chain).expect("ok"), chain);
        }
    }

    #[test]
    fn the_identity_pulls_a_cochain_back_unchanged() {
        let id = SimplicialMorphism::identity(4).expect("ok");
        let cochain = bits(&[1, 0, 1, 1]);
        assert_eq!(id.pullback(&cochain).expect("ok"), cochain);
    }

    #[test]
    fn the_identity_records_no_loss_and_no_deformation() {
        let id = SimplicialMorphism::identity(4).expect("ok");
        let certificate = TransportCertificateV1::issue(&id, &[0, 1, 2, 3]).expect("ok");
        assert!(certificate.identity);
        assert!(certificate.ledger.is_lossless());
        assert_eq!(certificate.ledger.delta_i(), ratio(0));
        assert_eq!(certificate.dimensional_dilation, 0);
        assert_eq!(certificate.boundary_deformation, 0);
    }

    #[test]
    fn a_non_identity_map_is_not_reported_as_the_identity() {
        // The other side of `identity`, so the flag is not always false or
        // always true.
        let f = morphism(&[0, 0, 1], 2);
        assert!(!f.is_identity());
        let certificate = TransportCertificateV1::issue(&f, &[0, 1, 2]).expect("ok");
        assert!(!certificate.identity);
        assert!(certificate.boundary_deformation > 0);
    }

    // -- AC3: loss is exactly additive --------------------------------------

    #[test]
    fn loss_is_exactly_additive_across_a_chain() {
        let (f, g) = chain_where_g_is_lossy_outside_f();
        let support = vec![0, 1, 2, 3];
        let composed = f.compose(&g).expect("ok");

        let (head, tail) = LossLedgerV1::for_chain(&f, &g, &support).expect("ok");
        let whole = LossLedgerV1::measure(&composed, &support).expect("ok");

        assert!(!head.is_lossless(), "F must lose something");
        assert_eq!(
            head.delta_i() + tail.delta_i(),
            whole.delta_i(),
            "loss was not additive"
        );
        assert_eq!(whole.delta_i(), ratio(1));
    }

    #[test]
    fn measuring_the_second_stage_over_its_whole_domain_would_overcount() {
        // The finding, stated as a test. G collapses {2,3} -> 2, but F's image
        // is {0,1,2} and never reaches 3, so that collapse costs nothing.
        // Measuring G over its full domain inflates the chain's loss.
        let (f, g) = chain_where_g_is_lossy_outside_f();
        let support = vec![0, 1, 2, 3];
        let composed = f.compose(&g).expect("ok");

        let (head, tail) = LossLedgerV1::for_chain(&f, &g, &support).expect("ok");
        let naive_tail = LossLedgerV1::measure(&g, &[0, 1, 2, 3]).expect("ok");

        assert_ne!(
            tail.delta_i(),
            naive_tail.delta_i(),
            "the fixture must distinguish the two readings"
        );
        assert_eq!(
            head.delta_i() + tail.delta_i(),
            LossLedgerV1::measure(&composed, &support)
                .expect("ok")
                .delta_i()
        );
        assert_ne!(
            head.delta_i() + naive_tail.delta_i(),
            LossLedgerV1::measure(&composed, &support)
                .expect("ok")
                .delta_i(),
            "the naive reading must actually differ, or this proves nothing"
        );
    }

    #[test]
    fn loss_is_additive_over_every_support_of_a_four_vertex_carrier() {
        let (f, g) = chain_where_g_is_lossy_outside_f();
        let composed = f.compose(&g).expect("ok");
        let mut lossy_supports = 0usize;
        for mask in 1..16u8 {
            let support: Vec<usize> = (0..4).filter(|bit| mask >> bit & 1 == 1).collect();
            let (head, tail) = LossLedgerV1::for_chain(&f, &g, &support).expect("ok");
            let whole = LossLedgerV1::measure(&composed, &support).expect("ok");
            assert_eq!(
                head.delta_i() + tail.delta_i(),
                whole.delta_i(),
                "not additive on {support:?}"
            );
            if !whole.is_lossless() {
                lossy_supports += 1;
            }
        }
        assert!(
            lossy_supports > 0,
            "every support was lossless, so additivity was tested only at zero"
        );
    }

    #[test]
    fn loss_is_carried_as_an_exact_rational_pair() {
        let f = morphism(&[0, 0, 0], 1);
        let ledger = LossLedgerV1::measure(&f, &[0, 1, 2]).expect("ok");
        assert_eq!(ledger.delta_i(), ratio(2));
        assert_eq!(ledger.delta_i_denominator, 1);
        let encoded = serde_json::to_string(&ledger).expect("ok");
        assert!(!encoded.contains('.'), "no decimal may be written");
    }

    #[test]
    fn a_duplicated_support_vertex_is_counted_once() {
        let f = morphism(&[0, 0, 1], 2);
        let once = LossLedgerV1::measure(&f, &[0, 1]).expect("ok");
        let twice = LossLedgerV1::measure(&f, &[0, 1, 1, 0]).expect("ok");
        assert_eq!(once, twice);
    }

    #[test]
    fn an_empty_support_loses_nothing() {
        let f = morphism(&[0, 0, 1], 2);
        let ledger = LossLedgerV1::measure(&f, &[]).expect("ok");
        assert!(ledger.is_lossless());
        assert_eq!(ledger.support_size, 0);
    }

    #[test]
    fn a_support_vertex_outside_the_source_is_refused() {
        let f = morphism(&[0, 0, 1], 2);
        assert_eq!(
            LossLedgerV1::measure(&f, &[0, 9]).expect_err("must refuse"),
            TransportError::SupportOutOfRange {
                vertex: 9,
                source_vertices: 3
            }
        );
    }

    // -- AC4: the ledger is cross-checked -----------------------------------

    #[test]
    fn a_truthful_ledger_verifies() {
        let f = morphism(&[0, 0, 1], 2);
        let support = vec![0, 1, 2];
        let ledger = LossLedgerV1::measure(&f, &support).expect("ok");
        ledger
            .verify(&f, &support)
            .expect("a truthful ledger must verify");
    }

    #[test]
    fn a_ledger_claiming_zero_loss_on_a_lossy_map_is_refused() {
        let f = morphism(&[0, 0, 1], 2);
        let support = vec![0, 1, 2];
        let honest = LossLedgerV1::measure(&f, &support).expect("ok");
        assert!(!honest.is_lossless(), "the fixture must be lossy");

        let forged = LossLedgerV1 {
            support_size: honest.support_size,
            image_size: honest.support_size,
            delta_i_numerator: 0,
            delta_i_denominator: 1,
        };
        assert!(matches!(
            forged.verify(&f, &support),
            Err(TransportError::LedgerDisagreesWithCarrier { .. })
        ));
    }

    #[test]
    fn a_ledger_overstating_loss_is_also_refused() {
        // Both directions, so the check is not one-sided.
        let f = morphism(&[0, 1, 2], 3);
        let support = vec![0, 1, 2];
        let honest = LossLedgerV1::measure(&f, &support).expect("ok");
        assert!(honest.is_lossless(), "the fixture must be lossless");

        let forged = LossLedgerV1 {
            support_size: 3,
            image_size: 1,
            delta_i_numerator: 2,
            delta_i_denominator: 1,
        };
        assert!(matches!(
            forged.verify(&f, &support),
            Err(TransportError::LedgerDisagreesWithCarrier { .. })
        ));
    }

    #[test]
    fn a_ledger_measured_on_a_different_support_is_refused() {
        let f = morphism(&[0, 0, 1], 2);
        let ledger = LossLedgerV1::measure(&f, &[0, 1]).expect("ok");
        assert!(matches!(
            ledger.verify(&f, &[0, 1, 2]),
            Err(TransportError::LedgerDisagreesWithCarrier { .. })
        ));
    }

    // -- AC5: orientation reversal is refused --------------------------------

    #[test]
    fn an_orientation_reversing_map_is_refused_and_names_the_pair() {
        assert_eq!(
            SimplicialMorphism::new(vec![1, 0], 2).expect_err("must refuse"),
            TransportError::OrientationReversed {
                left: 0,
                right: 1,
                left_image: 1,
                right_image: 0,
            }
        );
    }

    #[test]
    fn a_reversal_deeper_in_the_map_is_also_refused() {
        // Not just the first pair.
        assert!(matches!(
            SimplicialMorphism::new(vec![0, 1, 3, 2], 4),
            Err(TransportError::OrientationReversed { left: 2, .. })
        ));
    }

    #[test]
    fn a_monotone_non_injective_map_is_admitted() {
        // Orientation-preserving does not mean injective; collapsing is legal
        // and is what the loss ledger exists to account for.
        SimplicialMorphism::new(vec![0, 0, 1, 1], 2).expect("must be admitted");
    }

    #[test]
    fn a_constant_map_is_admitted_and_maximally_lossy() {
        let f = morphism(&[0, 0, 0, 0], 1);
        let ledger = LossLedgerV1::measure(&f, &[0, 1, 2, 3]).expect("ok");
        assert_eq!(ledger.delta_i(), ratio(3));
        assert_eq!(ledger.image_size, 1);
    }

    // -- construction refusals ------------------------------------------------

    #[test]
    fn an_image_outside_the_target_is_refused() {
        assert_eq!(
            SimplicialMorphism::new(vec![0, 5], 2).expect_err("must refuse"),
            TransportError::ImageOutOfRange {
                vertex: 1,
                image: 5,
                target_vertices: 2
            }
        );
    }

    #[test]
    fn an_empty_vertex_map_is_refused() {
        assert_eq!(
            SimplicialMorphism::new(vec![], 2).expect_err("must refuse"),
            TransportError::EmptyCarrier
        );
    }

    #[test]
    fn an_empty_target_is_refused() {
        assert_eq!(
            SimplicialMorphism::new(vec![0], 0).expect_err("must refuse"),
            TransportError::EmptyTarget
        );
    }

    #[test]
    fn a_chain_of_the_wrong_length_is_refused() {
        let f = morphism(&[0, 0, 1], 2);
        assert_eq!(
            f.pushforward(&bits(&[1, 0])).expect_err("must refuse"),
            TransportError::ChainLength {
                expected: 3,
                actual: 2
            }
        );
    }

    #[test]
    fn a_cochain_of_the_wrong_length_is_refused() {
        let f = morphism(&[0, 0, 1], 2);
        assert_eq!(
            f.pullback(&bits(&[1, 0, 1])).expect_err("must refuse"),
            TransportError::CochainLength {
                expected: 2,
                actual: 3
            }
        );
    }

    // -- certificate ---------------------------------------------------------

    #[test]
    fn the_certificate_records_dilation_as_a_signed_count() {
        let f = morphism(&[0, 0, 1], 2);
        let certificate = TransportCertificateV1::issue(&f, &[0, 1, 2]).expect("ok");
        assert_eq!(certificate.dimensional_dilation, -1);
        assert_eq!(certificate.ledger.delta_i(), ratio(1));
    }

    #[test]
    fn the_certificate_carries_no_authority() {
        let f = morphism(&[0, 0, 1], 2);
        let certificate = TransportCertificateV1::issue(&f, &[0, 1, 2]).expect("ok");
        assert_eq!(certificate.authority_effect, "None");
        assert_eq!(certificate.schema_version, TRANSPORT_CERTIFICATE_SCHEMA_V1);
    }

    #[test]
    fn the_certificate_round_trips_through_json() {
        let f = morphism(&[0, 0, 1], 2);
        let certificate = TransportCertificateV1::issue(&f, &[0, 1, 2]).expect("ok");
        let encoded = serde_json::to_string(&certificate).expect("ok");
        let decoded: TransportCertificateV1 = serde_json::from_str(&encoded).expect("ok");
        assert_eq!(certificate, decoded);
    }

    // -- no floating-point type ----------------------------------------------

    #[test]
    fn the_transport_implementation_admits_no_floating_point_type() {
        let source = include_str!("transport.rs");
        let implementation = source
            .split("#[cfg(test)]")
            .next()
            .expect("the module must have a non-test half");
        assert!(
            implementation.len() > 1_000,
            "the split found no implementation; the marker moved"
        );
        for banned in ["f64", "f32"] {
            assert!(
                !implementation.contains(banned),
                "the transport implementation must admit no {banned}"
            );
        }
    }

    #[test]
    fn the_float_gate_would_report_a_float() {
        let contrived = "pub fn loss(x: i64) -> f64 { x as f64 }";
        assert!(["f64", "f32"].iter().any(|b| contrived.contains(b)));
    }
}
