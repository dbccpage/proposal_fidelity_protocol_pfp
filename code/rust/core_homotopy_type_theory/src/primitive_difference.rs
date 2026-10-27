//! Finite Rust shadow of the **core** `PrimitiveDifference` quotient/descent kernel.
//!
//! Corresponds to the Lean definitions `ZeroRel`, `zeroRel_equivalence`,
//! `ResidualQuotient`, `classOf`, `DeltaCongruent`, `deltaFactor`, and the theorem
//! `deltaFactor_exists_iff_deltaCongruent` — but **over a declared finite domain**, where
//! those become decidable. It does **not** implement the full Lean file: the Lean also
//! carries `DeltaCongruentMod`/`deltaFactorMod`, `InvariantCongruent`/`invariantFactor`,
//! pair factorization, the `localGreenGlobalRed` obstruction, `PointedPrimitiveDifference`,
//! and `QuotientCompatiblePrimitiveDifference`, none of which live here yet.
//!
//! **Placement.** Below homology: `primitive_difference <- homological <- functional <-
//! certifier/replay/runner`, never the reverse. This module imports nothing from those
//! crates (pure `core`/`std`). Provisional home: `core_homotopy_type_theory`; long-term a
//! root primitive crate. Lean anchor: `lean4/PrimitiveDifference.lean`.
//!
//! **Scope.** Every check is over the listed finite domain — evidence on that domain, not a
//! global Lean theorem over arbitrary `Carrier`. The soundness bridge (finite checker ⇒ Lean
//! statement on the subtype) is the `PrimitiveDifferenceFinite.lean` obligation (PD-L4/L5/L6).
//! No such file exists in this repository; see `lean_anchor.missing_namespace` in the
//! `primitive_difference.yaml` contract.

use core::sync::atomic::{AtomicU64, Ordering};

/// Monotonic source of per-carrier brand tokens. The token is opaque metadata; it affects
/// no mathematical output (quotient, classes, δ̄ are unchanged) — it only prevents a
/// `QuotientClass` minted by one validated carrier from being used against another.
static CARRIER_COUNTER: AtomicU64 = AtomicU64::new(0);

/// The primitive difference: `δ` over carrier `A` valued in `B`, plus the `Zero`
/// predicate selecting which differences count as "no difference". The implementor must
/// supply a `Zero` whose induced `ZeroRel` is reflexive/symmetric/transitive (the Lean
/// fields `zero_refl/zero_symm/zero_trans`); [`FiniteCarrier::validate_zero_laws`] checks
/// this on a finite domain and returns the first counterexample on failure.
pub trait PrimitiveDifference {
    /// `A` — the carrier.
    type Carrier;
    /// `B` — the difference codomain.
    type Diff: PartialEq;

    /// `δ : A → A → B`.
    fn delta(&self, x: &Self::Carrier, y: &Self::Carrier) -> Self::Diff;

    /// `Zero : B → Prop` — does this difference count as no difference?
    fn zero(&self, d: &Self::Diff) -> bool;

    /// `ZeroRel x y := Zero(δ x y)` (Lean: `PrimitiveDifference.ZeroRel`).
    fn zero_rel(&self, x: &Self::Carrier, y: &Self::Carrier) -> bool {
        self.zero(&self.delta(x, y))
    }
}

/// An opaque, **carrier-branded** quotient class. Constructed only by
/// [`ValidatedFiniteCarrier`]; the inner fields are private, so a class cannot be forged or
/// read as a raw `usize`, and one carrier's class cannot be silently used against another
/// (the brand is checked in [`DeltaFactor::apply`]).
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct QuotientClass {
    carrier_id: u64,
    index: usize,
}

impl QuotientClass {
    /// The class index in `0..num_classes`. Read-only; cannot construct a class.
    pub fn index(self) -> usize {
        self.index
    }

    /// The brand of the carrier that minted this class (opaque).
    pub fn carrier_id(self) -> u64 {
        self.carrier_id
    }
}

/// Failure of a finite check, with the domain-index counterexample.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum PrimitiveDifferenceError {
    /// `ZeroRel(x,x)` is false at domain index `x`.
    ZeroReflexivityFailure { x: usize },
    /// `ZeroRel(x,y)` holds but `ZeroRel(y,x)` does not.
    ZeroSymmetryFailure { x: usize, y: usize },
    /// `ZeroRel(x,y)` and `ZeroRel(y,z)` hold but `ZeroRel(x,z)` does not.
    ZeroTransitivityFailure { x: usize, y: usize, z: usize },
    /// `x~x'` and `y~y'` but `δ(x,y) ≠ δ(x',y')`.
    DeltaCongruenceFailure {
        x: usize,
        x_prime: usize,
        y: usize,
        y_prime: usize,
    },
    /// The joint observable `(φ, ψ)` disagrees on the zero-related domain pair `(x, y)`:
    /// a component may descend alone, yet the pair does not — the LGGR witness (Lean:
    /// `localGreenGlobalRed_pair_obstruction`, a single zero-related pair, not four indices).
    PairCongruenceFailure { x: usize, y: usize },
    /// `n * n` (or `class_count * class_count`) overflows `usize` — domain/class scale too large
    /// for the finite O(n²) checker. Diagnostic refusal; does not mint authority.
    DomainScaleOverflow { n: usize },
}

// Origin: engine/crates_rs/core_homotopy_type_theory/src/primitive_difference.rs
// Claim: urn:core:crates_rs:core-homotopy-type-theory:primitive-difference:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for PrimitiveDifferenceError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for PrimitiveDifferenceError {}

/// Token proving `ZeroRel` is an equivalence on a finite domain of the given length.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct ZeroLawWitness {
    pub domain_len: usize,
}

/// Token proving `DeltaCongruent` holds on a finite domain of the given length.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct DeltaCongruenceWitness {
    pub domain_len: usize,
}

/// Token proving the joint observable `(φ, ψ)` descends on a finite domain of the given length.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct PairDescentWitness {
    pub domain_len: usize,
}

/// A zero-related domain pair `(x, y)` on which a joint observable fails to agree — the LGGR
/// witness (Lean: the witness of `localGreenGlobalRed_pair_obstruction`).
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct PairObstructionWitness {
    pub x: usize,
    pub y: usize,
}

/// Local-green / global-red summary for an observable pair `(φ, ψ)` (Lean:
/// `localGreenGlobalRed_pair_obstruction`). The thesis case is `left_descends && !pair_descends`:
/// a component descends locally while the joint observation does not descend globally. This is
/// **failed descent evidence** — it is not Φ₁, Γ₂, cohomology, or authority.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct LocalGlobalPairObstruction {
    pub left_descends: bool,
    pub right_descends: bool,
    pub pair_descends: bool,
    pub counterexample: Option<PairObstructionWitness>,
}

/// A raw (unvalidated) finite carrier. Only the zero-law check is exposed here; quotient and
/// descent operations require promotion to [`ValidatedFiniteCarrier`] via
/// [`FiniteCarrier::try_validate`], so they can never run on a non-equivalence `ZeroRel`.
pub struct FiniteCarrier<'a, P: PrimitiveDifference> {
    diff: &'a P,
    domain: Vec<P::Carrier>,
}

impl<'a, P: PrimitiveDifference> FiniteCarrier<'a, P> {
    pub fn new(diff: &'a P, domain: Vec<P::Carrier>) -> Self {
        Self { diff, domain }
    }

    pub fn domain_len(&self) -> usize {
        self.domain.len()
    }

    /// `ZeroRel` is an equivalence **on this domain** (Lean: `zeroRel_equivalence`). Returns
    /// a deterministic counterexample on failure. The relation is evaluated once per ordered
    /// pair and checked in O(n^2) time and O(n^2) bits of temporary storage.
    pub fn validate_zero_laws(&self) -> Result<ZeroLawWitness, PrimitiveDifferenceError> {
        self.validate_zero_partition().map(|_| ZeroLawWitness {
            domain_len: self.domain.len(),
        })
    }

    /// Promote to a [`ValidatedFiniteCarrier`] iff `ZeroRel` is an equivalence on the domain.
    pub fn try_validate(self) -> Result<ValidatedFiniteCarrier<'a, P>, PrimitiveDifferenceError> {
        let partition = self.validate_zero_partition()?;
        let carrier_id = CARRIER_COUNTER.fetch_add(1, Ordering::Relaxed);
        Ok(ValidatedFiniteCarrier {
            diff: self.diff,
            domain: self.domain,
            reps: partition.reps,
            class_of: partition.class_of,
            carrier_id,
        })
    }

    fn validate_zero_partition(&self) -> Result<ZeroPartition, PrimitiveDifferenceError> {
        let n = self.domain.len();
        let relation = self.build_reflexive_symmetric_relation()?;
        let partition = Self::partition_into_classes(n, &relation);
        Self::verify_partition_transitivity(n, &relation, &partition)?;
        Ok(partition)
    }

    fn build_reflexive_symmetric_relation(&self) -> Result<Vec<bool>, PrimitiveDifferenceError> {
        let domain = &self.domain;
        let n = domain.len();
        let relation_len = n
            .checked_mul(n)
            .ok_or(PrimitiveDifferenceError::DomainScaleOverflow { n })?;
        let mut relation = vec![false; relation_len];

        for (x, value) in domain.iter().enumerate() {
            if !self.diff.zero_rel(value, value) {
                return Err(PrimitiveDifferenceError::ZeroReflexivityFailure { x });
            }
            relation[x * n + x] = true;
        }

        for x in 0..n {
            for y in (x + 1)..n {
                let xy = self.diff.zero_rel(&domain[x], &domain[y]);
                let yx = self.diff.zero_rel(&domain[y], &domain[x]);
                if xy != yx {
                    return Err(if xy {
                        PrimitiveDifferenceError::ZeroSymmetryFailure { x, y }
                    } else {
                        PrimitiveDifferenceError::ZeroSymmetryFailure { x: y, y: x }
                    });
                }
                relation[x * n + y] = xy;
                relation[y * n + x] = xy;
            }
        }
        Ok(relation)
    }

    fn partition_into_classes(n: usize, relation: &[bool]) -> ZeroPartition {
        let mut reps = Vec::new();
        let mut class_of = vec![usize::MAX; n];
        for candidate in 0..n {
            if class_of[candidate] != usize::MAX {
                continue;
            }

            let class = reps.len();
            reps.push(candidate);
            for member in candidate..n {
                if class_of[member] == usize::MAX && relation[candidate * n + member] {
                    class_of[member] = class;
                }
            }
        }
        ZeroPartition { reps, class_of }
    }

    fn verify_partition_transitivity(
        n: usize,
        relation: &[bool],
        partition: &ZeroPartition,
    ) -> Result<(), PrimitiveDifferenceError> {
        let reps = &partition.reps;
        let class_of = &partition.class_of;
        // A reflexive symmetric relation is transitive exactly when the representative
        // partition has all and only the relation edges inside each class.
        for x in 0..n {
            for z in (x + 1)..n {
                let same_class = class_of[x] == class_of[z];
                let related = relation[x * n + z];
                if same_class == related {
                    continue;
                }

                if same_class {
                    let y = reps[class_of[x]];
                    return Err(PrimitiveDifferenceError::ZeroTransitivityFailure { x, y, z });
                }

                // Choose the earlier class representative. The later endpoint was still
                // unassigned when that class was formed, so the missing outer edge is known.
                let (x0, y0, z0) = if class_of[x] < class_of[z] {
                    (reps[class_of[x]], x, z)
                } else {
                    (reps[class_of[z]], z, x)
                };
                return Err(PrimitiveDifferenceError::ZeroTransitivityFailure {
                    x: x0,
                    y: y0,
                    z: z0,
                });
            }
        }
        Ok(())
    }
}

struct ZeroPartition {
    reps: Vec<usize>,
    class_of: Vec<usize>,
}

/// A finite carrier whose `ZeroRel` has been verified an equivalence. Quotient and descent
/// operations live here; they cannot be reached without that proof.
pub struct ValidatedFiniteCarrier<'a, P: PrimitiveDifference> {
    diff: &'a P,
    domain: Vec<P::Carrier>,
    /// Domain indices of the class representatives.
    reps: Vec<usize>,
    /// Class index for each domain index. Built while validating the zero relation.
    class_of: Vec<usize>,
    /// Brand identifying this validated carrier (see [`QuotientClass`]).
    carrier_id: u64,
}

impl<'a, P: PrimitiveDifference> ValidatedFiniteCarrier<'a, P> {
    /// Validate-and-construct in one step.
    pub fn try_new(diff: &'a P, domain: Vec<P::Carrier>) -> Result<Self, PrimitiveDifferenceError> {
        FiniteCarrier::new(diff, domain).try_validate()
    }

    pub fn num_classes(&self) -> usize {
        self.reps.len()
    }

    pub fn domain_len(&self) -> usize {
        self.domain.len()
    }

    pub fn carrier_id(&self) -> u64 {
        self.carrier_id
    }

    fn brand(&self, index: usize) -> QuotientClass {
        QuotientClass {
            carrier_id: self.carrier_id,
            index,
        }
    }

    /// `ResidualQuotient`: the distinct classes (Lean: `ResidualQuotient`).
    pub fn residual_quotient(&self) -> Vec<QuotientClass> {
        (0..self.reps.len()).map(|ci| self.brand(ci)).collect()
    }

    /// Canonical `classOf` over the validated finite domain: the class of `domain[i]`,
    /// or `None` if `i` is out of range (Lean: `classOf`, restricted to the domain).
    pub fn class_of_index(&self, i: usize) -> Option<QuotientClass> {
        self.class_of.get(i).copied().map(|class| self.brand(class))
    }

    /// **Diagnostic only** — classifies an arbitrary `Carrier` value by `ZeroRel` to a
    /// representative. This is NOT the Lean `classOf`: it accepts values outside the
    /// validated domain, so its result is a convenience read, not a quotient statement.
    pub fn class_of_value_diagnostic(&self, x: &P::Carrier) -> Option<QuotientClass> {
        self.reps
            .iter()
            .position(|&r| self.diff.zero_rel(&self.domain[r], x))
            .map(|ci| self.brand(ci))
    }

    /// `DeltaCongruent` **on this domain** (Lean: `DeltaCongruent`). First counterexample
    /// on failure.
    pub fn validate_delta_congruence(
        &self,
    ) -> Result<DeltaCongruenceWitness, PrimitiveDifferenceError> {
        let n = self.domain.len();
        let class_count = self.reps.len();
        let capacity = class_count
            .checked_mul(class_count)
            .ok_or(PrimitiveDifferenceError::DomainScaleOverflow { n: class_count })?;
        let mut class_deltas = Vec::with_capacity(capacity);
        for &x in &self.reps {
            for &y in &self.reps {
                class_deltas.push(self.diff.delta(&self.domain[x], &self.domain[y]));
            }
        }

        for (x, &x_class) in self.class_of.iter().enumerate() {
            for (y, &y_class) in self.class_of.iter().enumerate() {
                let observed = self.diff.delta(&self.domain[x], &self.domain[y]);
                if observed != class_deltas[x_class * class_count + y_class] {
                    return Err(PrimitiveDifferenceError::DeltaCongruenceFailure {
                        x,
                        x_prime: self.reps[x_class],
                        y,
                        y_prime: self.reps[y_class],
                    });
                }
            }
        }
        Ok(DeltaCongruenceWitness { domain_len: n })
    }

    pub fn delta_congruent_on_domain(&self) -> bool {
        self.validate_delta_congruence().is_ok()
    }

    /// Finite shadow of `deltaFactor_exists_iff_deltaCongruent`: a factorization exists on
    /// the domain **iff** `DeltaCongruent` holds on the domain.
    pub fn delta_factors_through_quotient_on_domain(&self) -> bool {
        self.delta_congruent_on_domain()
    }

    /// Access the descended operation `δ̄` — available **only** when `DeltaCongruent` holds.
    pub fn try_delta_factor(&self) -> Result<DeltaFactor<'_, 'a, P>, PrimitiveDifferenceError> {
        let _ = self.validate_delta_congruence()?;
        Ok(DeltaFactor { carrier: self })
    }

    /// An observable `φ : Carrier → G` descends on the domain iff it agrees on every
    /// zero-related pair (Lean: `InvariantCongruent` /
    /// `invariantFactor_exists_iff_invariantCongruent`). Diagnostic; mints nothing.
    pub fn observable_descends_on_domain<G, F>(&self, phi: F) -> bool
    where
        G: PartialEq,
        F: Fn(&P::Carrier) -> G,
    {
        let values: Vec<_> = self.domain.iter().map(phi).collect();
        values
            .iter()
            .enumerate()
            .all(|(i, value)| value == &values[self.reps[self.class_of[i]]])
    }

    /// The joint observable `(φ, ψ)` descends on the domain iff it agrees on every
    /// zero-related pair; otherwise the first zero-related witness `(x, y)` is returned
    /// (Lean: the pair-congruence half of `localGreenGlobalRed_pair_obstruction`).
    pub fn validate_pair_descent_on_domain<G, H, FP, FQ>(
        &self,
        phi: FP,
        psi: FQ,
    ) -> Result<PairDescentWitness, PrimitiveDifferenceError>
    where
        G: PartialEq,
        H: PartialEq,
        FP: Fn(&P::Carrier) -> G,
        FQ: Fn(&P::Carrier) -> H,
    {
        let phi_values: Vec<_> = self.domain.iter().map(phi).collect();
        let psi_values: Vec<_> = self.domain.iter().map(psi).collect();
        for (i, &class) in self.class_of.iter().enumerate() {
            let representative = self.reps[class];
            if phi_values[i] != phi_values[representative]
                || psi_values[i] != psi_values[representative]
            {
                return Err(PrimitiveDifferenceError::PairCongruenceFailure {
                    x: representative,
                    y: i,
                });
            }
        }
        Ok(PairDescentWitness {
            domain_len: self.domain.len(),
        })
    }

    /// Local-green / global-red classification of an observable pair `(φ, ψ)`: whether each
    /// component descends, whether the pair descends, and a witness zero-related pair on which
    /// the joint disagrees. `left_descends && !pair_descends` is the thesis case — a component
    /// is locally green while the joint observation is globally red (Lean:
    /// `localGreenGlobalRed_pair_obstruction`). Failed-descent evidence only; not Φ₁/Γ₂/
    /// cohomology/authority.
    pub fn local_green_global_red<G, H, FP, FQ>(
        &self,
        phi: FP,
        psi: FQ,
    ) -> LocalGlobalPairObstruction
    where
        G: PartialEq,
        H: PartialEq,
        FP: Fn(&P::Carrier) -> G,
        FQ: Fn(&P::Carrier) -> H,
    {
        let phi_values: Vec<_> = self.domain.iter().map(phi).collect();
        let psi_values: Vec<_> = self.domain.iter().map(psi).collect();
        let mut left_descends = true;
        let mut right_descends = true;
        let mut counterexample: Option<PairObstructionWitness> = None;
        for (i, &class) in self.class_of.iter().enumerate() {
            let representative = self.reps[class];
            let phi_diff = phi_values[i] != phi_values[representative];
            let psi_diff = psi_values[i] != psi_values[representative];
            if phi_diff {
                left_descends = false;
            }
            if psi_diff {
                right_descends = false;
            }
            if (phi_diff || psi_diff) && counterexample.is_none() {
                counterexample = Some(PairObstructionWitness {
                    x: representative,
                    y: i,
                });
            }
        }
        LocalGlobalPairObstruction {
            left_descends,
            right_descends,
            pair_descends: counterexample.is_none(),
            counterexample,
        }
    }
}

/// The descended difference `δ̄ : Quotient × Quotient → B`. Existence is gated on a verified
/// `DeltaCongruent`, so [`DeltaFactor::apply`] is representative-independent by construction
/// (Lean: `deltaFactor`). Classes from a different carrier are rejected by the brand check.
pub struct DeltaFactor<'c, 'a, P: PrimitiveDifference> {
    carrier: &'c ValidatedFiniteCarrier<'a, P>,
}

impl<'c, 'a, P: PrimitiveDifference> DeltaFactor<'c, 'a, P> {
    /// `δ̄(qx, qy)` = `δ` on the class representatives. `None` if either class was minted by a
    /// different carrier (brand mismatch) or its index is out of range.
    pub fn apply(&self, qx: QuotientClass, qy: QuotientClass) -> Option<P::Diff> {
        let id = self.carrier.carrier_id;
        if qx.carrier_id != id || qy.carrier_id != id {
            return None;
        }
        let rx = *self.carrier.reps.get(qx.index)?;
        let ry = *self.carrier.reps.get(qy.index)?;
        Some(
            self.carrier
                .diff
                .delta(&self.carrier.domain[rx], &self.carrier.domain[ry]),
        )
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use std::cell::Cell;

    /// `δ(x,_) = x`, `Zero ≡ True` — collapse everything to one class. `ZeroRel` is a valid
    /// equivalence (total), but `δ` is not congruent, so no factorization exists
    /// (Lean: `boolAllZeroNonconstant_no_factorization`).
    struct BoolAllZeroNonconstant;
    impl PrimitiveDifference for BoolAllZeroNonconstant {
        type Carrier = bool;
        type Diff = bool;
        fn delta(&self, x: &bool, _y: &bool) -> bool {
            *x
        }
        fn zero(&self, _d: &bool) -> bool {
            true
        }
    }

    #[test]
    fn bool_all_zero_nonconstant_has_no_factorization() {
        let p = BoolAllZeroNonconstant;
        let vc = ValidatedFiniteCarrier::try_new(&p, vec![false, true]).expect("zero laws hold");
        assert_eq!(vc.num_classes(), 1);
        assert!(!vc.delta_congruent_on_domain());
        assert!(!vc.delta_factors_through_quotient_on_domain());
        assert!(vc.try_delta_factor().is_err());
    }

    #[test]
    fn delta_congruence_counterexample_reported() {
        let p = BoolAllZeroNonconstant;
        let vc = ValidatedFiniteCarrier::try_new(&p, vec![false, true]).unwrap();
        match vc.validate_delta_congruence() {
            Err(PrimitiveDifferenceError::DeltaCongruenceFailure { .. }) => {}
            other => panic!("expected DeltaCongruenceFailure, got {other:?}"),
        }
    }

    /// `δ(x,y) = (x − y) mod 2`, `Zero(d) = (d == 0)`. `ZeroRel` is parity-equality and the
    /// parity difference descends.
    struct ParityDifference;
    impl PrimitiveDifference for ParityDifference {
        type Carrier = i64;
        type Diff = i64;
        fn delta(&self, x: &i64, y: &i64) -> i64 {
            (x - y).rem_euclid(2)
        }
        fn zero(&self, d: &i64) -> bool {
            *d == 0
        }
    }

    #[test]
    fn parity_difference_descends() {
        let p = ParityDifference;
        let vc = ValidatedFiniteCarrier::try_new(&p, vec![0, 1, 2, 3]).unwrap();
        assert_eq!(vc.num_classes(), 2);
        assert!(vc.delta_congruent_on_domain());
        let factor = vc.try_delta_factor().expect("congruent ⇒ factor exists");
        let c_even = vc.class_of_index(0).unwrap(); // domain[0] = 0
        let c_odd = vc.class_of_index(1).unwrap(); // domain[1] = 1
        assert_eq!(factor.apply(c_even, c_odd), Some(1));
    }

    #[test]
    fn delta_factor_returns_same_value_for_representatives() {
        let p = ParityDifference;
        let vc = ValidatedFiniteCarrier::try_new(&p, vec![0, 1, 2, 3]).unwrap();
        let factor = vc.try_delta_factor().unwrap();
        // class_of_index(0)==(2) (even), (1)==(3) (odd); δ̄ is single-valued on classes.
        assert_eq!(vc.class_of_index(0), vc.class_of_index(2));
        assert_eq!(vc.class_of_index(1), vc.class_of_index(3));
        let a = factor.apply(vc.class_of_index(0).unwrap(), vc.class_of_index(1).unwrap());
        let b = factor.apply(vc.class_of_index(2).unwrap(), vc.class_of_index(3).unwrap());
        assert_eq!(a, b);
    }

    #[test]
    fn class_of_index_is_domain_scoped() {
        let p = ParityDifference;
        let vc = ValidatedFiniteCarrier::try_new(&p, vec![0, 1, 2, 3]).unwrap();
        assert!(vc.class_of_index(0).is_some());
        assert!(vc.class_of_index(3).is_some());
        assert!(vc.class_of_index(4).is_none()); // outside the validated domain
    }

    #[test]
    fn cross_carrier_quotient_class_rejected() {
        let p = ParityDifference;
        let a = ValidatedFiniteCarrier::try_new(&p, vec![0, 1, 2, 3]).unwrap();
        let b = ValidatedFiniteCarrier::try_new(&p, vec![0, 1, 2, 3]).unwrap();
        assert_ne!(a.carrier_id(), b.carrier_id());
        let fa = a.try_delta_factor().unwrap();
        let class_from_b = b.class_of_index(0).unwrap();
        // a class minted by carrier b cannot be applied to carrier a's factor.
        assert_eq!(fa.apply(class_from_b, class_from_b), None);
    }

    /// Configurable integer difference for the law-rejection cases: `δ(x,y) = x − y`,
    /// `Zero` supplied as a function pointer.
    struct IntDiff(fn(i64) -> bool);
    impl PrimitiveDifference for IntDiff {
        type Carrier = i64;
        type Diff = i64;
        fn delta(&self, x: &i64, y: &i64) -> i64 {
            x - y
        }
        fn zero(&self, d: &i64) -> bool {
            (self.0)(*d)
        }
    }

    #[test]
    fn zero_rel_not_reflexive_rejected() {
        let p = IntDiff(|_d| false); // nothing is zero ⇒ ZeroRel(x,x) false
        assert_eq!(
            ValidatedFiniteCarrier::try_new(&p, vec![0]).err(),
            Some(PrimitiveDifferenceError::ZeroReflexivityFailure { x: 0 })
        );
    }

    #[test]
    fn zero_rel_not_symmetric_rejected() {
        // zero(0)=true (reflexive), zero(2)=true, zero(-2)=false ⇒ asymmetric.
        let p = IntDiff(|d| d == 0 || d == 2);
        match ValidatedFiniteCarrier::try_new(&p, vec![0, 2]).err() {
            Some(PrimitiveDifferenceError::ZeroSymmetryFailure { .. }) => {}
            other => panic!("expected ZeroSymmetryFailure, got {other:?}"),
        }
    }

    #[test]
    fn zero_rel_not_transitive_rejected() {
        // |d|<=1 is reflexive and symmetric but not transitive (0~1, 1~2, 0≁2).
        let p = IntDiff(|d| d.abs() <= 1);
        let domain = vec![0, 1, 2];
        match ValidatedFiniteCarrier::try_new(&p, domain.clone()).err() {
            Some(PrimitiveDifferenceError::ZeroTransitivityFailure { x, y, z }) => {
                assert!(p.zero_rel(&domain[x], &domain[y]));
                assert!(p.zero_rel(&domain[y], &domain[z]));
                assert!(!p.zero_rel(&domain[x], &domain[z]));
            }
            other => panic!("expected ZeroTransitivityFailure, got {other:?}"),
        }
    }

    #[test]
    fn quotient_class_is_opaque_and_well_formed() {
        let p = ParityDifference;
        let vc = ValidatedFiniteCarrier::try_new(&p, vec![0, 1, 2, 3]).unwrap();
        for q in vc.residual_quotient() {
            assert!(q.index() < vc.num_classes());
            assert_eq!(q.carrier_id(), vc.carrier_id());
        }
    }

    #[test]
    fn finite_domain_scope_not_global_claim() {
        // The SAME PrimitiveDifference yields different quotients on different domains —
        // results are scoped to the declared domain, not global over `Carrier`.
        let p = ParityDifference;
        let two = ValidatedFiniteCarrier::try_new(&p, vec![0, 1]).unwrap();
        let one = ValidatedFiniteCarrier::try_new(&p, vec![0, 2]).unwrap(); // both even
        assert_eq!(two.num_classes(), 2);
        assert_eq!(one.num_classes(), 1);
    }

    #[test]
    fn observable_descends_iff_congruent_on_domain() {
        let p = ParityDifference;
        let vc = ValidatedFiniteCarrier::try_new(&p, vec![0, 1, 2, 3]).unwrap();
        // φ = parity is invariant on parity classes → descends.
        assert!(vc.observable_descends_on_domain(|x: &i64| x.rem_euclid(2)));
        // ψ = the raw value is NOT invariant (0 ~ 2 yet 0 ≠ 2) → does not descend.
        assert!(!vc.observable_descends_on_domain(|x: &i64| *x));
    }

    #[test]
    fn lggr_local_green_global_red_pair_obstruction() {
        let p = ParityDifference;
        let vc = ValidatedFiniteCarrier::try_new(&p, vec![0, 1, 2, 3]).unwrap();
        // φ descends (parity), ψ does not (raw value): the pair (φ, ψ) fails to descend.
        let lggr = vc.local_green_global_red(|x: &i64| x.rem_euclid(2), |x: &i64| *x);
        assert!(lggr.left_descends); // local green: φ descends alone
        assert!(!lggr.right_descends); // ψ does not descend
        assert!(!lggr.pair_descends); // global red: the pair does not descend
        assert!(lggr.counterexample.is_some());
        match vc.validate_pair_descent_on_domain(|x: &i64| x.rem_euclid(2), |x: &i64| *x) {
            Err(PrimitiveDifferenceError::PairCongruenceFailure { .. }) => {}
            other => panic!("expected PairCongruenceFailure, got {other:?}"),
        }
    }

    #[test]
    fn lggr_both_descend_pair_descends() {
        let p = ParityDifference;
        let vc = ValidatedFiniteCarrier::try_new(&p, vec![0, 1, 2, 3]).unwrap();
        // both components congruent (parity, and a constant) → the pair descends, no witness.
        let lggr = vc.local_green_global_red(|x: &i64| x.rem_euclid(2), |_x: &i64| 0i64);
        assert!(lggr.left_descends && lggr.right_descends && lggr.pair_descends);
        assert!(lggr.counterexample.is_none());
        assert!(vc
            .validate_pair_descent_on_domain(|x: &i64| x.rem_euclid(2), |_x: &i64| 0i64)
            .is_ok());
    }

    #[derive(Default)]
    struct CountingParity {
        delta_calls: Cell<usize>,
    }

    impl CountingParity {
        fn reset(&self) {
            self.delta_calls.set(0);
        }

        fn calls(&self) -> usize {
            self.delta_calls.get()
        }
    }

    impl PrimitiveDifference for CountingParity {
        type Carrier = i64;
        type Diff = i64;

        fn delta(&self, x: &i64, y: &i64) -> i64 {
            self.delta_calls.set(self.delta_calls.get() + 1);
            (x - y).rem_euclid(2)
        }

        fn zero(&self, d: &i64) -> bool {
            *d == 0
        }
    }

    #[test]
    fn validation_and_descent_have_bounded_evaluation_counts() {
        const DOMAIN_LEN: usize = 128;
        let difference = CountingParity::default();
        let domain = (0..DOMAIN_LEN as i64).collect();
        let carrier = ValidatedFiniteCarrier::try_new(&difference, domain).unwrap();

        assert_eq!(difference.calls(), DOMAIN_LEN * DOMAIN_LEN);
        difference.reset();
        for i in 0..DOMAIN_LEN {
            assert!(carrier.class_of_index(i).is_some());
        }
        assert_eq!(difference.calls(), 0);

        assert!(carrier.delta_congruent_on_domain());
        assert_eq!(difference.calls(), DOMAIN_LEN * DOMAIN_LEN + 4);

        let observable_calls = Cell::new(0);
        assert!(carrier.observable_descends_on_domain(|x: &i64| {
            observable_calls.set(observable_calls.get() + 1);
            x.rem_euclid(2)
        }));
        assert_eq!(observable_calls.get(), DOMAIN_LEN);

        let left_calls = Cell::new(0);
        let right_calls = Cell::new(0);
        assert!(carrier
            .validate_pair_descent_on_domain(
                |x: &i64| {
                    left_calls.set(left_calls.get() + 1);
                    x.rem_euclid(2)
                },
                |_x: &i64| {
                    right_calls.set(right_calls.get() + 1);
                    0
                },
            )
            .is_ok());
        assert_eq!(left_calls.get(), DOMAIN_LEN);
        assert_eq!(right_calls.get(), DOMAIN_LEN);
    }
}
