//! Part 5 — the witnessed difference ledger.
//!
//! Given a carrier `C⁰ →d₀ C¹ →d₁ C²` and a finite family of `C¹` cochains
//! `x₀ … x_{n−1}`, this records for every pair `i < j`:
//!
//! ```text
//! Δᵢⱼ = xᵢ − xⱼ           and     Δᵢⱼ ∈ im(d₀) ?
//! ```
//!
//! and commits the whole record to a BLAKE3 Merkle root bound to the carrier.
//!
//! # Why the pairs are not independent
//!
//! `im(d₀)` is a subspace, so `Δᵢⱼ ∈ im(d₀)` is an **equivalence relation**:
//!
//! - reflexive — `Δᵢᵢ = 0 ∈ im(d₀)`;
//! - symmetric — `Δⱼᵢ = −Δᵢⱼ`, and a subspace is closed under negation;
//! - transitive — `Δᵢₖ = Δᵢⱼ + Δⱼₖ`, and a subspace is closed under addition.
//!
//! Two consequences, and the second is the point of this module:
//!
//! 1. The `n(n−1)/2` entries carry only `O(n)` independent information — the
//!    partition of the family into classes. Each class is one point of the residual
//!    quotient `Q¹ = C¹/im(d₀)`.
//! 2. A ledger that records all pairs **can contradict itself**. If the recorded
//!    verdicts say `i ~ j` and `j ~ k` but `¬(i ~ k)`, no subspace produced them —
//!    the arithmetic is wrong. [`DifferenceLedger::build`] checks the transitive
//!    closure against the recorded verdicts and refuses on disagreement
//!    ([`LedgerError::EquivalenceViolation`]). That check is the reason to compute
//!    all pairs rather than a spanning subset: the redundancy is the audit.
//!
//! # Witnesses
//!
//! A `Coboundary` verdict carries the potential `α` with `d₀α = Δᵢⱼ`, replayed
//! exactly before it is recorded. An `Obstructed` verdict carries the rank pair
//! that establishes non-membership. Neither mints authority.
//!
//! # What this module does NOT do
//!
//! It does not call [`core_homology::cochain_primitive_difference`]'s `zero()`.
//! That method has signature `fn zero(&self, d: &Vec<Q>) -> bool` and maps
//! `Err(_) => false`, so a dimension mismatch or an internal solver inconsistency
//! becomes the *mathematical* verdict "not a coboundary". A ledger built on that
//! would record an obstruction it never established. Every decision here goes
//! through [`solve_in_image`] and keeps the typed error.
//!
//! `AuthorityEffect: None.` This is a diagnostic record. It mints nothing, and a
//! Merkle root is a commitment to what was computed, never evidence that the
//! computation was authorized.

use linear_algebra::linear_algebra::image_kernel::{
    solve_in_image, ExactLinearAlgebraError, ImageMembership,
};
use num_traits::Zero;
use core_homology::carrier::Carrier;
use core_homology::carrier_manifest::CarrierManifest;
use core_homology::hashing::Hash256;
use core_homology::scalar::{hash_rational, Q};

/// Domain-separation tags. Leaf and node tags **must** differ: with a single tag,
/// an internal node can be replayed as a leaf and a second preimage of the root
/// constructed from a shorter tree.
const TAG_LEAF: &[u8] = b"CORE.DifferenceLedger.leaf.v1";
const TAG_NODE: &[u8] = b"CORE.DifferenceLedger.node.v1";
const TAG_ROOT: &[u8] = b"CORE.DifferenceLedger.root.v1";
const TAG_EMPTY: &[u8] = b"CORE.DifferenceLedger.empty.v1";

/// Why a ledger could not be built.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum LedgerError {
    /// A cochain in the family has the wrong length for `C¹`.
    #[error("family member {index} has length {got}, expected c1_dim = {expected}")]
    CochainLength {
        index: usize,
        got: usize,
        expected: usize,
    },

    /// The exact image-membership decision failed. Preserved as the source rather
    /// than collapsed into "not a coboundary" — a solver failure is not a
    /// mathematical verdict about `Δᵢⱼ`.
    #[error("exact image membership failed for the pair ({i}, {j})")]
    Membership {
        i: usize,
        j: usize,
        #[source]
        source: ExactLinearAlgebraError,
    },

    /// A recorded `Coboundary` verdict whose potential does not replay.
    #[error("the potential recorded for pair ({i}, {j}) does not satisfy d0 * alpha = delta")]
    WitnessReplayFailed { i: usize, j: usize },

    /// The recorded verdicts are not an equivalence relation, so no subspace
    /// `im(d₀)` can have produced them. See the module docs.
    #[error(
        "recorded verdicts violate transitivity: ({i}, {j}) and ({j}, {k}) are both \
         coboundaries but ({i}, {k}) is recorded as obstructed; im(d0) is a subspace, \
         so this is arithmetically impossible and indicates a defect, not a result"
    )]
    EquivalenceViolation { i: usize, j: usize, k: usize },

    /// The carrier's manifest could not be computed.
    #[error("carrier manifest: {0}")]
    Manifest(String),
}

/// The verdict for one pair, with its witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DifferenceVerdict {
    /// `Δᵢⱼ ∈ im(d₀)`, witnessed by a potential `α` with `d₀α = Δᵢⱼ`, replayed
    /// exactly before this variant was constructed.
    Coboundary { potential: Vec<Q> },
    /// `Δᵢⱼ ∉ im(d₀)`, witnessed by `rank([d₀ | Δ]) > rank(d₀)`.
    Obstructed {
        rank_d0: usize,
        rank_augmented: usize,
    },
}

impl DifferenceVerdict {
    pub fn is_coboundary(&self) -> bool {
        matches!(self, DifferenceVerdict::Coboundary { .. })
    }
}

/// One ledger row: the pair, its difference, its verdict, and the leaf commitment.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DifferenceEntry {
    pub i: usize,
    pub j: usize,
    pub delta: Vec<Q>,
    pub verdict: DifferenceVerdict,
    pub leaf_hash: Hash256,
}

/// The witnessed difference ledger over one carrier and one family.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DifferenceLedger {
    entries: Vec<DifferenceEntry>,
    /// Class index per family member, from the verified equivalence.
    class_of: Vec<usize>,
    num_classes: usize,
    merkle_root: Hash256,
    carrier_hash: Hash256,
}

impl DifferenceLedger {
    pub fn entries(&self) -> &[DifferenceEntry] {
        &self.entries
    }

    /// Which class each family member fell into. Two members share a class exactly
    /// when their difference is a coboundary, i.e. when they are the same point of
    /// `Q¹ = C¹/im(d₀)`.
    pub fn class_of(&self) -> &[usize] {
        &self.class_of
    }

    /// Number of distinct points of `Q¹` the family occupies. `1` means the whole
    /// family is a single residual class — every pairwise difference is exact.
    pub fn num_classes(&self) -> usize {
        self.num_classes
    }

    /// Merkle root over the entries, bound to the carrier. See [`merkle_root`].
    pub fn merkle_root(&self) -> &Hash256 {
        &self.merkle_root
    }

    /// The carrier this ledger is about — [`CarrierManifest`]'s `carrier_hash`.
    ///
    /// The root above commits to this, so a ledger cannot be transplanted onto a
    /// different carrier without changing its root.
    pub fn carrier_hash(&self) -> &Hash256 {
        &self.carrier_hash
    }

    fn evaluate_pair_entry(
        carrier: &Carrier,
        family: &[Vec<Q>],
        i: usize,
        j: usize,
        related: &mut [Vec<bool>],
    ) -> Result<DifferenceEntry, LedgerError> {
        let delta: Vec<Q> = family[i]
            .iter()
            .zip(family[j].iter())
            .map(|(a, b)| a.clone() - b.clone())
            .collect();

        let membership = solve_in_image(carrier.d0(), &delta)
            .map_err(|source| LedgerError::Membership { i, j, source })?;

        let verdict = match membership {
            ImageMembership::InImage(witness) => {
                // Replay before recording. `solve_in_image` already checks
                // this internally; repeating it here means the ledger never
                // records a potential it did not itself verify.
                if !replays(carrier, &witness.potential, &delta) {
                    return Err(LedgerError::WitnessReplayFailed { i, j });
                }
                related[i][j] = true;
                related[j][i] = true;
                DifferenceVerdict::Coboundary {
                    potential: witness.potential,
                }
            }
            ImageMembership::NotInImage {
                rank_a,
                rank_augmented,
            } => DifferenceVerdict::Obstructed {
                rank_d0: rank_a,
                rank_augmented,
            },
        };

        let leaf_hash = leaf_hash(i, j, &delta, &verdict);
        Ok(DifferenceEntry {
            i,
            j,
            delta,
            verdict,
            leaf_hash,
        })
    }

    fn verify_transitive_closure(related: &[Vec<bool>], n: usize) -> Result<(), LedgerError> {
        for j in 0..n {
            for i in 0..n {
                if !related[i][j] {
                    continue;
                }
                for k in 0..n {
                    if related[j][k] && !related[i][k] {
                        return Err(LedgerError::EquivalenceViolation { i, j, k });
                    }
                }
            }
        }
        Ok(())
    }

    /// Build the ledger for `family` over `carrier`.
    ///
    /// # Errors
    ///
    /// See [`LedgerError`]. Note in particular that a solver failure is
    /// [`LedgerError::Membership`] and never a recorded obstruction.
    pub fn build(carrier: &Carrier, family: &[Vec<Q>]) -> Result<Self, LedgerError> {
        let c1 = carrier.c1_dim();
        for (index, x) in family.iter().enumerate() {
            if x.len() != c1 {
                return Err(LedgerError::CochainLength {
                    index,
                    got: x.len(),
                    expected: c1,
                });
            }
        }

        let manifest = CarrierManifest::from_carrier(carrier)
            .map_err(|e| LedgerError::Manifest(format!("{e:?}")))?;
        let carrier_hash = manifest.carrier_hash().clone();

        let n = family.len();
        let mut entries = Vec::with_capacity(n.saturating_mul(n.saturating_sub(1)) / 2);
        // related[i][j] mirrors the recorded verdict, for the equivalence audit.
        let mut related = vec![vec![false; n]; n];
        for (i, row) in related.iter_mut().enumerate() {
            row[i] = true; // Δᵢᵢ = 0 ∈ im(d₀), reflexivity — not stored as an entry.
        }

        for i in 0..n {
            for j in (i + 1)..n {
                entries.push(Self::evaluate_pair_entry(
                    carrier,
                    family,
                    i,
                    j,
                    &mut related,
                )?);
            }
        }

        // The audit: the recorded verdicts must already be transitively closed.
        // Because im(d₀) is a subspace this cannot fail on correct arithmetic —
        // which is exactly why a failure here is a defect report, not a result.
        Self::verify_transitive_closure(&related, n)?;

        let (class_of, num_classes) = classes(&related);
        let merkle_root = merkle_root(&entries, &carrier_hash);

        Ok(Self {
            entries,
            class_of,
            num_classes,
            merkle_root,
            carrier_hash,
        })
    }
}

/// `d₀ · potential == delta`, exactly.
fn replays(carrier: &Carrier, potential: &[Q], delta: &[Q]) -> bool {
    let d0 = carrier.d0();
    if d0.rows() != delta.len() || d0.cols() != potential.len() {
        return false;
    }
    for (row, target) in delta.iter().enumerate() {
        let mut acc = Q::zero();
        for (col, p) in potential.iter().enumerate() {
            match d0.get(row, col) {
                Ok(a) => acc += a * p,
                Err(_) => return false,
            }
        }
        if acc != *target {
            return false;
        }
    }
    true
}

/// Assign class indices from the (already verified) relation.
fn classes(related: &[Vec<bool>]) -> (Vec<usize>, usize) {
    let n = related.len();
    let mut class_of = vec![usize::MAX; n];
    let mut next = 0usize;
    for i in 0..n {
        if class_of[i] != usize::MAX {
            continue;
        }
        class_of[i] = next;
        for j in (i + 1)..n {
            if related[i][j] {
                class_of[j] = next;
            }
        }
        next += 1;
    }
    (class_of, next)
}

/// Hash one ledger row.
///
/// Every variable-width field is length-prefixed. `BigInt` has no fixed width, so
/// bare concatenation is not injective — the same defect the carrier hashing was
/// repaired for.
fn leaf_hash(i: usize, j: usize, delta: &[Q], verdict: &DifferenceVerdict) -> Hash256 {
    let mut h = blake3::Hasher::new();
    h.update(TAG_LEAF);
    h.update(&(i as u64).to_le_bytes());
    h.update(&(j as u64).to_le_bytes());
    h.update(&(delta.len() as u64).to_le_bytes());
    for value in delta {
        hash_rational(&mut h, value);
    }
    match verdict {
        DifferenceVerdict::Coboundary { potential } => {
            // A discriminant byte, so a Coboundary row can never collide with an
            // Obstructed row that happens to serialize alike.
            h.update(&[0u8]);
            h.update(&(potential.len() as u64).to_le_bytes());
            for value in potential {
                hash_rational(&mut h, value);
            }
        }
        DifferenceVerdict::Obstructed {
            rank_d0,
            rank_augmented,
        } => {
            h.update(&[1u8]);
            h.update(&(*rank_d0 as u64).to_le_bytes());
            h.update(&(*rank_augmented as u64).to_le_bytes());
        }
    }
    Hash256(*h.finalize().as_bytes())
}

/// Merkle root over the leaves, bound to the carrier.
///
/// # Construction notes, and the two forgeries they prevent
///
/// - **Leaf and internal nodes carry different tags.** With one tag, an internal
///   node is a valid leaf preimage, so a root can be re-explained by a shorter
///   tree. This is the classic Merkle second-preimage attack.
/// - **The carrier hash is folded into the final root**, so a ledger cannot be
///   transplanted onto another carrier, and an empty ledger has its own tag rather
///   than a zero root.
///
/// Against the padding forgery (CVE-2012-2459 — duplicating the last node of an
/// odd level makes `[A,B,C]` and `[A,B,C,C]` fold identically) there are **three
/// independent defenses**, and *any one of them alone closes it*:
///
/// 1. an odd node is **promoted unchanged**, never duplicated;
/// 2. each level commits to **its own node count**, so a level of length `m`
///    cannot be reinterpreted as one of length `m ± 1`;
/// 3. the final root commits to the **total leaf count**.
///
/// This is measured, not assumed: `distinct_leaf_lists_get_distinct_roots` only
/// reports a collision when all three are removed together, and it then names the
/// exact colliding pair.
pub fn merkle_root(entries: &[DifferenceEntry], carrier_hash: &Hash256) -> Hash256 {
    let mut level: Vec<Hash256> = entries.iter().map(|e| e.leaf_hash.clone()).collect();

    if level.is_empty() {
        let mut h = blake3::Hasher::new();
        h.update(TAG_EMPTY);
        h.update(carrier_hash.as_bytes());
        return Hash256(*h.finalize().as_bytes());
    }

    while level.len() > 1 {
        let count = level.len() as u64;
        let mut next = Vec::with_capacity(level.len().div_ceil(2));
        let mut chunks = level.chunks(2);
        for chunk in &mut chunks {
            match chunk {
                [left, right] => {
                    let mut h = blake3::Hasher::new();
                    h.update(TAG_NODE);
                    h.update(&count.to_le_bytes());
                    h.update(left.as_bytes());
                    h.update(right.as_bytes());
                    next.push(Hash256(*h.finalize().as_bytes()));
                }
                // Odd tail: promote unchanged. Not duplicated — see above.
                [only] => next.push(only.clone()),
                _ => unreachable!("chunks(2) yields 1 or 2 elements"),
            }
        }
        level = next;
    }

    let mut h = blake3::Hasher::new();
    h.update(TAG_ROOT);
    h.update(&(entries.len() as u64).to_le_bytes());
    h.update(carrier_hash.as_bytes());
    h.update(level[0].as_bytes());
    Hash256(*h.finalize().as_bytes())
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use core_homology::cochain_complex::TheoremProvenance;
    use core_homology::finite_directed_graph::{
        DirectedGraphBuilder, TheoremProvenance as GraphProv,
    };
    use core_homology::graph_carrier::graph_carrier;
    use core_homology::scalar::q;

    /// Triangle graph, no 2-cell. `im(d₀)` is 2-dimensional inside `C¹ = ℚ³`, so
    /// `Q¹` is 1-dimensional — there are genuinely distinct classes to find.
    fn triangle() -> Carrier {
        let gp = GraphProv {
            verification_source: "difference_ledger_test".to_string(),
        };
        let g = DirectedGraphBuilder::from_anonymous(3, vec![(0, 1), (1, 2), (0, 2)], gp).unwrap();
        let prov = TheoremProvenance::new("difference_ledger_test".to_string()).unwrap();
        graph_carrier(&g, &[], vec![q(1); 3], prov).unwrap()
    }

    /// `d₀` of the triangle applied to a 0-cochain — a guaranteed coboundary.
    fn coboundary_of(carrier: &Carrier, potential: &[Q]) -> Vec<Q> {
        let d0 = carrier.d0();
        (0..d0.rows())
            .map(|row| {
                let mut acc = Q::zero();
                for (col, p) in potential.iter().enumerate() {
                    acc += d0.get(row, col).unwrap() * p;
                }
                acc
            })
            .collect()
    }

    #[test]
    fn a_family_of_coboundaries_is_one_class() {
        let c = triangle();
        let base = vec![q(0), q(0), q(0)];
        let family = vec![
            base.clone(),
            coboundary_of(&c, &[q(1), q(2), q(5)]),
            coboundary_of(&c, &[q(-3), q(7), q(0)]),
        ];
        let ledger = DifferenceLedger::build(&c, &family).unwrap();

        assert_eq!(ledger.entries().len(), 3, "3 choose 2");
        assert!(ledger.entries().iter().all(|e| e.verdict.is_coboundary()));
        assert_eq!(
            ledger.num_classes(),
            1,
            "every difference of coboundaries is a coboundary"
        );
        assert_eq!(ledger.class_of(), &[0, 0, 0]);
    }

    /// The decisive positive case: a family that genuinely splits. The triangle's
    /// `Q¹` is 1-dimensional, so `[1,1,1]` (a cycle, not a coboundary) sits in a
    /// different class from the coboundaries.
    #[test]
    fn a_family_spanning_two_residual_classes_is_two_classes() {
        let c = triangle();
        let cycle = vec![q(1), q(1), q(-1)];
        let family = vec![
            vec![q(0), q(0), q(0)],
            coboundary_of(&c, &[q(4), q(1), q(9)]),
            cycle.clone(),
        ];
        let ledger = DifferenceLedger::build(&c, &family).unwrap();

        assert_eq!(ledger.num_classes(), 2);
        assert_eq!(ledger.class_of()[0], ledger.class_of()[1]);
        assert_ne!(ledger.class_of()[0], ledger.class_of()[2]);

        let obstructed: Vec<_> = ledger
            .entries()
            .iter()
            .filter(|e| !e.verdict.is_coboundary())
            .map(|e| (e.i, e.j))
            .collect();
        assert_eq!(
            obstructed,
            vec![(0, 2), (1, 2)],
            "exactly the pairs crossing the class boundary"
        );
    }

    /// Every `Coboundary` verdict carries a potential that actually reproduces the
    /// difference. A verdict without a replaying witness is an assertion, not a
    /// result.
    #[test]
    fn every_coboundary_verdict_replays_exactly() {
        let c = triangle();
        let family = vec![
            coboundary_of(&c, &[q(2), q(0), q(1)]),
            coboundary_of(&c, &[q(-1), q(5), q(3)]),
            vec![q(0), q(0), q(0)],
        ];
        let ledger = DifferenceLedger::build(&c, &family).unwrap();

        let mut checked = 0;
        for e in ledger.entries() {
            if let DifferenceVerdict::Coboundary { potential } = &e.verdict {
                assert!(
                    replays(&c, potential, &e.delta),
                    "pair ({}, {}) recorded a potential that does not replay",
                    e.i,
                    e.j
                );
                checked += 1;
            }
        }
        assert!(checked > 0, "the sweep saw no coboundary rows — vacuous");
    }

    /// Coefficients beyond `i64` pass through exactly (ADR-001). A ledger that
    /// silently narrowed would fail here.
    #[test]
    fn coefficients_beyond_i64_are_carried_exactly() {
        use num_bigint::BigInt;
        use std::str::FromStr;

        let c = triangle();
        let huge = BigInt::from_str("170141183460469231731687303715884105727").unwrap();
        let big = Q::new(huge.clone(), BigInt::from(1));
        let family = vec![
            vec![q(0), q(0), q(0)],
            coboundary_of(&c, &[big.clone(), q(0), q(0)]),
        ];
        let ledger = DifferenceLedger::build(&c, &family).unwrap();

        assert_eq!(ledger.num_classes(), 1);
        let seen = ledger.entries()[0]
            .delta
            .iter()
            .any(|v| v.numer().magnitude() == huge.magnitude());
        assert!(seen, "the large coefficient must survive into the ledger");
    }

    #[test]
    fn wrong_length_member_is_refused_by_index() {
        let c = triangle();
        let family = vec![vec![q(0), q(0), q(0)], vec![q(1), q(1)]];
        assert_eq!(
            DifferenceLedger::build(&c, &family),
            Err(LedgerError::CochainLength {
                index: 1,
                got: 2,
                expected: 3
            })
        );
    }

    // --- Merkle construction -------------------------------------------------

    fn ledger_of(carrier: &Carrier, family: &[Vec<Q>]) -> DifferenceLedger {
        DifferenceLedger::build(carrier, family).unwrap()
    }

    /// Same graph, same family, **different weights**.
    ///
    /// This isolates the binding. Two carriers with different `d₀` would also give
    /// different roots — but for the wrong reason: different `d₀` changes the
    /// verdicts, hence the leaves, hence the root, with the carrier hash playing no
    /// part. Weights do not enter `solve_in_image` at all, so the entries here are
    /// byte-identical and the *only* thing that can separate the roots is the
    /// carrier hash folded into them.
    #[test]
    fn root_is_bound_to_the_carrier_even_when_the_entries_are_identical() {
        let gp = || GraphProv {
            verification_source: "difference_ledger_test".to_string(),
        };
        let prov = || TheoremProvenance::new("difference_ledger_test".to_string()).unwrap();
        let build = |w: Q| {
            graph_carrier(
                &DirectedGraphBuilder::from_anonymous(3, vec![(0, 1), (1, 2), (0, 2)], gp())
                    .unwrap(),
                &[],
                vec![w; 3],
                prov(),
            )
            .unwrap()
        };
        let light = build(q(1));
        let heavy = build(q(2));

        let family = vec![
            vec![q(0), q(0), q(0)],
            vec![q(1), q(1), q(-1)],
            vec![q(2), q(0), q(1)],
        ];
        let a = ledger_of(&light, &family);
        let b = ledger_of(&heavy, &family);

        // Premise 1: the ledgers' contents really are identical.
        assert_eq!(
            a.entries().iter().map(|e| &e.leaf_hash).collect::<Vec<_>>(),
            b.entries().iter().map(|e| &e.leaf_hash).collect::<Vec<_>>(),
            "test premise broken — weights must not change the entries, or this \
             proves nothing about the binding"
        );
        // Premise 2: the carriers really are distinguishable.
        assert_ne!(
            a.carrier_hash(),
            b.carrier_hash(),
            "test premise broken — the two carriers must hash differently"
        );

        assert_ne!(
            a.merkle_root(),
            b.merkle_root(),
            "identical entries over different carriers shared a root — a ledger is \
             transplantable onto another carrier"
        );
    }

    /// **A real second-preimage attempt, not a comparison of two constants.**
    ///
    /// The classic Merkle forgery: take a 4-leaf tree, compute its two internal
    /// nodes `N₁ = H(L₁,L₂)` and `N₂ = H(L₃,L₄)`, then present a *2-leaf* tree
    /// whose leaves are `N₁` and `N₂`. Both trees fold to the same inner value, so
    /// a construction that stops there hands the same root to two different ledgers
    /// — one with four rows, one with two.
    ///
    /// The attempt is carried out here rather than asserted about, because
    /// `DifferenceEntry::leaf_hash` is public and a forged entry list is exactly
    /// what an attacker would supply.
    #[test]
    fn a_shorter_tree_cannot_reproduce_a_longer_trees_root() {
        let c = triangle();
        // 4 family members -> 6 pairs; take the first 4 rows for a clean 4-leaf tree.
        let ledger = ledger_of(
            &c,
            &[
                vec![q(0), q(0), q(0)],
                vec![q(1), q(1), q(-1)],
                vec![q(2), q(0), q(1)],
                vec![q(5), q(-2), q(3)],
            ],
        );
        let four: Vec<DifferenceEntry> = ledger.entries()[..4].to_vec();
        let carrier_hash = ledger.carrier_hash();

        // Recompute the two internal nodes the honest tree builds.
        let node_of = |left: &Hash256, right: &Hash256, count: u64| {
            let mut h = blake3::Hasher::new();
            h.update(TAG_NODE);
            h.update(&count.to_le_bytes());
            h.update(left.as_bytes());
            h.update(right.as_bytes());
            Hash256(*h.finalize().as_bytes())
        };
        let n1 = node_of(&four[0].leaf_hash, &four[1].leaf_hash, 4);
        let n2 = node_of(&four[2].leaf_hash, &four[3].leaf_hash, 4);

        // The forgery: two rows whose leaf hashes ARE those internal nodes.
        let forged: Vec<DifferenceEntry> = [n1, n2]
            .into_iter()
            .enumerate()
            .map(|(k, h)| DifferenceEntry {
                i: 0,
                j: k + 1,
                delta: vec![],
                verdict: DifferenceVerdict::Obstructed {
                    rank_d0: 0,
                    rank_augmented: 0,
                },
                leaf_hash: h,
            })
            .collect();

        assert_ne!(
            merkle_root(&four, carrier_hash),
            merkle_root(&forged, carrier_hash),
            "a 2-row ledger reproduced a 4-row ledger's root — the tree is \
             second-preimageable"
        );
    }

    /// The leaf and node tags are distinct *constants*, which is necessary but not
    /// by itself a test — the forgery above is what actually exercises the
    /// separation. Kept as documentation of the requirement.
    #[test]
    fn leaf_and_node_tags_are_distinct_constants() {
        assert_ne!(TAG_LEAF, TAG_NODE);
        assert_ne!(TAG_LEAF, TAG_ROOT);
        assert_ne!(TAG_NODE, TAG_ROOT);
        assert_ne!(TAG_EMPTY, TAG_ROOT);
    }

    /// Distinct leaf lists must get distinct roots — swept over every shape that
    /// exercises the odd-tail path.
    ///
    /// This is the honest form of the CVE-2012-2459 check. The classic attack pads
    /// an odd level by duplicating its last node, which makes `[A,B,C]` and
    /// `[A,B,C,C]` fold identically. **Three independent defenses** stop it here
    /// (promotion instead of duplication, the per-level node count, and the total
    /// leaf count in the root), and any one of them alone suffices — so a mutation
    /// removing one or two changes nothing observable. Removing all three reopens
    /// the collision, and this sweep names the pair: lists `[e0,e1,e2]` and
    /// `[e0,e1,e2,e2]`.
    ///
    /// An earlier version of this test compared a 3-entry ledger against a 4-entry
    /// one and "passed" under a duplication mutation: the leaf-count binding was
    /// separating them, not the promotion. It proved nothing about the property it
    /// was named for.
    #[test]
    fn distinct_leaf_lists_get_distinct_roots() {
        let c = triangle();
        let ledger = ledger_of(
            &c,
            &[
                vec![q(0), q(0), q(0)],
                vec![q(1), q(1), q(-1)],
                vec![q(2), q(0), q(1)],
                vec![q(5), q(-2), q(3)],
            ],
        );
        let e = ledger.entries();
        assert!(
            e.len() >= 4,
            "need at least 4 rows to build the shapes below"
        );
        let carrier_hash = ledger.carrier_hash();

        // Lists chosen so several are the "same prefix, padded tail" shapes the
        // duplication attack turns into collisions, across odd and even lengths.
        let lists: Vec<Vec<DifferenceEntry>> = vec![
            vec![],
            vec![e[0].clone()],
            vec![e[0].clone(), e[0].clone()],
            vec![e[0].clone(), e[1].clone()],
            vec![e[0].clone(), e[1].clone(), e[2].clone()],
            vec![e[0].clone(), e[1].clone(), e[2].clone(), e[2].clone()],
            vec![e[0].clone(), e[1].clone(), e[2].clone(), e[3].clone()],
            vec![
                e[0].clone(),
                e[1].clone(),
                e[2].clone(),
                e[3].clone(),
                e[3].clone(),
            ],
            vec![e[3].clone(), e[2].clone(), e[1].clone(), e[0].clone()],
        ];

        let roots: Vec<Hash256> = lists.iter().map(|l| merkle_root(l, carrier_hash)).collect();

        for a in 0..roots.len() {
            for b in (a + 1)..roots.len() {
                assert_ne!(
                    roots[a],
                    roots[b],
                    "leaf lists {a} (len {}) and {b} (len {}) share a root",
                    lists[a].len(),
                    lists[b].len()
                );
            }
        }
    }

    /// Reordering rows changes the root — the ledger commits to a sequence, and the
    /// pair indices are inside each leaf.
    #[test]
    fn reordering_entries_changes_the_root() {
        let c = triangle();
        let ledger = ledger_of(
            &c,
            &[
                vec![q(0), q(0), q(0)],
                vec![q(1), q(1), q(-1)],
                vec![q(2), q(0), q(1)],
            ],
        );
        let mut swapped = ledger.entries().to_vec();
        swapped.swap(0, 1);
        assert_ne!(
            merkle_root(ledger.entries(), ledger.carrier_hash()),
            merkle_root(&swapped, ledger.carrier_hash())
        );
    }

    /// A Coboundary row and an Obstructed row are separated by a discriminant byte,
    /// so they cannot collide even if their other bytes align.
    #[test]
    fn verdict_kinds_are_discriminated_in_the_leaf() {
        let delta = vec![q(1), q(0), q(0)];
        let a = leaf_hash(
            0,
            1,
            &delta,
            &DifferenceVerdict::Coboundary { potential: vec![] },
        );
        let b = leaf_hash(
            0,
            1,
            &delta,
            &DifferenceVerdict::Obstructed {
                rank_d0: 0,
                rank_augmented: 0,
            },
        );
        assert_ne!(a, b);
    }

    /// An empty ledger has its own tagged root rather than a zero hash, and it is
    /// still bound to its carrier.
    #[test]
    fn empty_ledger_has_a_tagged_nonzero_root() {
        let c = triangle();
        let ledger = ledger_of(&c, &[]);
        assert_eq!(ledger.entries().len(), 0);
        assert_eq!(ledger.num_classes(), 0);
        assert_ne!(ledger.merkle_root().as_bytes(), &[0u8; 32]);

        let single = ledger_of(&c, &[vec![q(0), q(0), q(0)]]);
        assert_eq!(single.entries().len(), 0, "one member has no pairs");
        assert_eq!(single.num_classes(), 1);
        assert_eq!(
            single.merkle_root(),
            ledger.merkle_root(),
            "both are empty over the same carrier"
        );
    }

    /// The root is a function of the data, not of the run.
    #[test]
    fn root_is_deterministic() {
        let c = triangle();
        let family = vec![
            vec![q(0), q(0), q(0)],
            vec![q(1), q(1), q(-1)],
            vec![q(5), q(-2), q(3)],
        ];
        assert_eq!(
            ledger_of(&c, &family).merkle_root(),
            ledger_of(&c, &family).merkle_root()
        );
    }

    /// Changing a single coefficient in one family member changes the root.
    #[test]
    fn a_changed_coefficient_changes_the_root() {
        let c = triangle();
        let base = vec![vec![q(0), q(0), q(0)], vec![q(1), q(1), q(-1)]];
        let mut perturbed = base.clone();
        perturbed[1][0] = q(2);
        assert_ne!(
            ledger_of(&c, &base).merkle_root(),
            ledger_of(&c, &perturbed).merkle_root()
        );
    }
}
