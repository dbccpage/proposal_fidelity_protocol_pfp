import Derivation.ContactBridge
import Derivation.PrimitiveContact
import Derivation.PrimitivePassage

/-!
# The common replacement kernel: the meet of the two entry strata

The collision (`ObsDescent`, `ContactBridge`) established that the
native corpus and the arriving observer stratum are incomparable at
signature grade in one direction and reconstructible in the other.
This module constructs what both sides *can* share: the common
replacement kernel `WitnessedDiff` — a valued difference presentation
with designated endpoints, a diagonal-zero law, and a refutation-grade
non-zero witness at the designated pair.  Deliberately absent:
symmetry, transitivity, retention, protection, and any operation
family — each is a separately priced declaration on one side or the
other, never kernel content.

1. **The kernel and its induced apartness** (`WitnessedDiff`,
   `kernelApart`): irreflexivity of the induced apartness and
   metatheoretic endpoint distinctness are free
   (`kernelApart_irrefl`, `kernel_endpoints_ne`); no kernel lives on a
   subsingleton carrier (`no_kernel_on_subsingleton`); the canonical
   realization is the oriented two-element kernel (`boolKernel`).
2. **Both sides realize it** (`toSetting`, `toSetting_A`,
   `toNativeKernel`, `ofSetting`, `ofDiffObs`): the kernel meets the
   sealed pre-contact interface `PrimitiveContact.NativeKernel` by
   construction; a bare native candidate-A setting yields a kernel
   whose apartness is the double negation of the asserted relation —
   exact under an explicitly hypothesized pointwise decidability
   (`ofSetting_exact`, `open_kernel_grade`), blind to retention,
   protection, and operations (`ofSetting_ret_irrelevant`); an
   observer yields a kernel only *together with a chosen non-zero
   pair*, and the choice is genuine new data
   (`pair_choice_load_bearing`, `kernel_from_obs_iff_pair`,
   `eq_ofDiffObs_of_fields`, `kernel_no_witness_from_collapse`);
   in the other direction the kernel *plus the two law declarations*
   is an observer, field-for-field and losslessly (`toDiffObs`,
   `toDiffObs_fields`, `toDiffObs_apart`) — a record identity, not a
   derivation.
3. **What the kernel does not carry** (`kernel_not_observer`,
   `kernel_zero_not_trans`, `kernel_not_bs`, `kernel_not_bc`,
   `kernel_located_of_decidable`, `open_kernel_bl`, `kernel_not_c`,
   `kernel_not_f`, `kernel_to_w`, `kernel_to_d`, `kernel_to_e_empty`,
   `kernel_not_e_merged`, `no_kernel_over_allzero`): the two law
   fields the observer stratum carries (symmetry, transitivity of the
   zero side) are exactly the declarations separating observer from
   kernel, priced at carriers two and three — matching the sealed
   apartness pricing; protection and retention are never derivable;
   W, A, D, and E-at-empty-stores hold outright.
4. **Value grade is presentation** (`unitValKernel`, `twoValKernel`,
   `value_presentation_fork`, `VHom`, `vhom_not_unique`,
   `DeltaOnto`, `vhom_unique_of_onto`): distinct value assignments
   present the same apartness; valued kernel morphisms are not
   determined by their carrier map — off-image value freedom, the
   kernel echo of the sealed off-image factor non-uniqueness — and
   uniqueness is restored exactly under delta-surjectivity, the
   kernel echo of the sealed epi-scoped uniqueness.
5. **Universal status is inherited, not re-proved**
   (`boolKernel_apart_iff`, `apartObj`, `apartObj_irrefl`,
   `apartObj_sym_of_observer`, `kernel_gateway_unique`,
   `kernel_gateway_injective`, `kernel_gateways_not_identical`,
   `freeKernel`, `kernel_no_terminal`,
   `kernel_no_terminal_collector`): every kernel presents a pointed
   witnessed relation, so the sealed `PrimitiveCats.d2_initial` gives
   the unique gateway out of the two-element carrier unconditionally;
   observer-derived kernels land in the symmetric subcategory; there
   is provably no terminal collector of kernels — the free third
   point branches, the same mechanism as the sealed
   observer-branching theorems.
6. **Passage entry** (`passageObj`, `passage_gateway_unique`,
   `kernel_licenses_entry`, `entry_pre_observation`,
   `kernel_two_point_presentation`): the kernel enters the sealed
   passage at the pre-retention state — before retention, protection,
   and observation, each of which remains a separately priced event —
   and a total two-point presentation of the endpoints costs
   decidable equality of the carrier (sufficiency only).
7. **The machine-checkable matrix** (`contactCells`,
   `contactCells_length`): the 37 collision cells spanning the kernel
   stratum and the observer stratum, one literal row each.

Metatheory used (declared): structures, functions, propositional
logic, finite case analysis discharged by `decide`, case analysis on
explicitly hypothesized `Decidable` instances, and the sealed
theorems cited by name.  No choice or excluded middle is invoked, and
no quotient object occurs in these propositions or constructions.
The axiom report for the fixed-action result nevertheless includes
`Quot.sound`, because Lean core realizes its `funext` step through
that principle; “no quotient object” is not an axiom-freedom claim.
-/

namespace ContactKernel

open DiffInterface

variable {X R : Type}

/-! ## The common replacement kernel -/

/-- Common replacement kernel: a valued difference presentation with
designated endpoints, a diagonal-zero law, and a refutation-grade
non-zero witness at the designated pair.  No symmetry, no
transitivity, no retention, no protection, no operation family: the
witness is deliberately refutation-grade, the strongest form both
sides can supply. -/
structure WitnessedDiff (X R : Type) where
  delta : X → X → R
  Zero : R → Prop
  a : X
  b : X
  diag_zero : ∀ x, Zero (delta x x)
  apart_ab : ¬ Zero (delta a b)

/-- The apartness a kernel induces: non-zero difference value. -/
def kernelApart (K : WitnessedDiff X R) : X → X → Prop :=
  fun x y => ¬ K.Zero (K.delta x y)

/-- Irreflexivity of the induced apartness is free: the diagonal-zero
law, contraposed. -/
theorem kernelApart_irrefl (K : WitnessedDiff X R) :
    ∀ x, ¬ kernelApart K x x :=
  fun x h => h (K.diag_zero x)

/-- The designated endpoints are metatheoretically distinct: the
witness against the diagonal-zero law. -/
theorem kernel_endpoints_ne (K : WitnessedDiff X R) : K.a ≠ K.b :=
  fun he => K.apart_ab (by rw [he]; exact K.diag_zero K.b)

/-- No kernel lives on a subsingleton carrier: the kernel echo of the
sealed one-point exclusions (`PrimDiff.no_witness_on_subsingleton`;
native models `unitBare`, `unitFull` cited by the matrix rows W→K and
C→K). -/
theorem no_kernel_on_subsingleton {X R : Type} [Subsingleton X]
    (K : WitnessedDiff X R) : False :=
  kernel_endpoints_ne K (Subsingleton.elim K.a K.b)

/-- The canonical realization: the oriented two-element kernel.  Its
difference value marks exactly the ordered pair `(false, true)`; zero
is value-falsity. -/
def boolKernel : WitnessedDiff Bool Bool where
  delta x y := (!x) && y
  Zero v := v = false
  a := false
  b := true
  diag_zero := by decide
  apart_ab := by decide

/-! ## Translations: both sides realize the kernel -/

/-- The setting a kernel presents to the native candidate matrix:
carrier, induced apartness, the designated pair, and empty stores —
the kernel carries no retention, protection, or operation content. -/
def toSetting (K : WitnessedDiff X R) : PrimitiveCore.Setting where
  X := X
  r := kernelApart K
  a := K.a
  b := K.b
  ret := fun _ _ => False
  prot := fun _ _ => False
  Ops := fun _ => False

/-- Every kernel satisfies candidate A: witness from `apart_ab`, free
irreflexivity from the diagonal-zero law. -/
theorem toSetting_A (K : WitnessedDiff X R) :
    PrimitiveCore.A (toSetting K) :=
  ⟨K.apart_ab, kernelApart_irrefl K⟩

/-- **The kernel meets the sealed pre-contact interface** by
construction: the fixed interface promise of the pre-contact record
(`PrimitiveContact.NativeKernel`) is honored, not renegotiated. -/
def toNativeKernel (K : WitnessedDiff X R) :
    PrimitiveContact.NativeKernel :=
  ⟨toSetting K, toSetting_A K⟩

/-- The kernel a bare candidate-A setting realizes: the asserted
relation as a Prop-valued difference, zero as its negation, the
designated pair carried over.  Irreflexivity supplies the
diagonal-zero law; the witness supplies the non-zero witness. -/
def ofSetting (S : PrimitiveCore.Setting) (h : PrimitiveCore.A S) :
    WitnessedDiff S.X Prop where
  delta := S.r
  Zero p := ¬ p
  a := S.a
  b := S.b
  diag_zero := h.2
  apart_ab hn := hn h.1

/-- The read-back is exact under pointwise decidability of the
asserted relation: the induced apartness of the realized kernel is
the original relation.  Without the decidability admission the round
trip is double-negation-coarse (`open_kernel_grade`). -/
theorem ofSetting_exact (S : PrimitiveCore.Setting)
    (h : PrimitiveCore.A S) [inst : ∀ x y, Decidable (S.r x y)] :
    ∀ x y, kernelApart (ofSetting S h) x y ↔ S.r x y :=
  fun x y =>
    ⟨fun hnn =>
      match inst x y with
      | isTrue hr => hr
      | isFalse hn => absurd hn hnn,
     fun hr hn => hn hr⟩

/-- OPEN cell: the round-trip grade without decidability.  No
internal countermodel can exist; the exact price is recorded. -/
def open_kernel_grade : String :=
  "OPEN: without pointwise decidability of the asserted relation, the kernel read back from a candidate-A setting carries the double negation of that relation - the round trip is exact under an explicit Decidable hypothesis (ofSetting_exact) and the residual schema is priced at double-negation elimination (ContactBridge.stability_schema_iff_dne); no internal countermodel can exist because the gap schema is classically true"

/-- The kernel is blind to retention, protection, and operations:
realizing a setting with any replacement stores yields the same
kernel, definitionally. -/
theorem ofSetting_ret_irrelevant (S : PrimitiveCore.Setting)
    (h : PrimitiveCore.A S) (ret' prot' : S.X → S.X → Prop)
    (Ops' : (S.X → S.X) → Prop) :
    ofSetting { S with ret := ret', prot := prot', Ops := Ops' } h =
      ofSetting S h := rfl

/-- The kernel an observer realizes — only together with a *chosen*
non-zero pair: difference map and zero predicate carried over, the
reflexivity law field as the diagonal-zero law, the chosen pair as
endpoints. -/
def ofDiffObs (O : DiffObs X R) (a b : X)
    (hw : ¬ ZeroRel O a b) : WitnessedDiff X R where
  delta := O.delta
  Zero := O.Zero
  a := a
  b := b
  diag_zero := O.zero_refl
  apart_ab := hw

/-- **An arbitrary pair may fail the side condition**: one observer
offers both a non-zero pair and a zero pair, so a pair cannot simply
be picked without checking.

Exact scope: this is a statement about *pairs*, not about kernels.
It does NOT exhibit two valid choices, two distinct kernels, or an
equivariance obstruction.  Those are separate, and are proved below by
`transpose_kernel_ne`,
`kernel_not_unique_of_pair`, `pair_choice_not_unique` and
`no_equivariant_pair_valued_map`.  Cite this lemma only for the
weak claim it carries. -/
theorem pair_choice_load_bearing :
    ∃ (O : DiffObs Bool Bool) (a₁ b₁ a₂ b₂ : Bool),
      ¬ ZeroRel O a₁ b₁ ∧ ZeroRel O a₂ b₂ := by
  refine ⟨{ delta := fun x y => xor x y
            Zero := fun v => v = false
            zero_refl := by decide
            zero_symm := ?_
            zero_trans := ?_ }, false, true, false, false, ?_, ?_⟩
  · intro x y
    revert x y
    decide
  · intro x y z
    revert x y z
    decide
  · exact fun h => Bool.noConfusion h
  · rfl

/-- Existence of a kernel that carries an observer's difference and
zero data is equivalent to existence of a non-zero pair.  The pair is
therefore necessary for the observer→kernel map; it is not recovered
from the observer record alone (`pair_choice_load_bearing`). -/
theorem kernel_from_obs_iff_pair (O : DiffObs X R) :
    (∃ K : WitnessedDiff X R, K.delta = O.delta ∧ K.Zero = O.Zero) ↔
      (∃ a b : X, ¬ ZeroRel O a b) := by
  constructor
  · rintro ⟨K, hd, hz⟩
    refine ⟨K.a, K.b, ?_⟩
    change ¬ O.Zero (O.delta K.a K.b)
    rw [← hd, ← hz]
    exact K.apart_ab
  · rintro ⟨a, b, hw⟩
    exact ⟨ofDiffObs O a b hw, rfl, rfl⟩

/-- Any kernel with an observer's difference and zero data is
`ofDiffObs` at that kernel's own endpoints.  This is factorization
through an explicit pair, not uniqueness of the pair. -/
theorem eq_ofDiffObs_of_fields (O : DiffObs X R)
    (K : WitnessedDiff X R)
    (hd : K.delta = O.delta) (hz : K.Zero = O.Zero) :
    K = ofDiffObs O K.a K.b (by
      change ¬ O.Zero (O.delta K.a K.b)
      rw [← hd, ← hz]
      exact K.apart_ab) := by
  cases K
  cases O
  cases hd
  cases hz
  rfl

/-! ## The pair choice, exactly: correspondence, non-uniqueness, and
no relabelling-equivariant pair-valued map -/

/-- Two observers that agree on the difference map and the zero
predicate are equal: the three law fields are `Prop`-valued, so they
are recovered by definitional proof irrelevance. -/
theorem obs_eq_of_fields {X R : Type} (O₁ O₂ : DiffObs X R)
    (hd : O₁.delta = O₂.delta) (hz : O₁.Zero = O₂.Zero) : O₁ = O₂ := by
  cases O₁
  cases O₂
  cases hd
  cases hz
  rfl

/-- The admissible pairs of an observer: exactly the data `ofDiffObs`
consumes beyond the observer record. -/
abbrev NonZeroPair (O : DiffObs X R) : Type :=
  { p : X × X // ¬ ZeroRel O p.1 p.2 }

/-- The kernels that carry an observer's difference map and zero
predicate unchanged. -/
abbrev SameDataKernel (O : DiffObs X R) : Type :=
  { K : WitnessedDiff X R // K.delta = O.delta ∧ K.Zero = O.Zero }

/-- Forward leg: a same-data kernel yields its own designated pair,
admissible because the kernel's witness transports along the two
field equations. -/
def toPair (O : DiffObs X R) (K : SameDataKernel O) : NonZeroPair O :=
  ⟨(K.val.a, K.val.b), by
    have h := K.val.apart_ab
    rw [K.property.1, K.property.2] at h
    exact h⟩

/-- Backward leg: an admissible pair yields the kernel `ofDiffObs`
builds, whose two data fields are the observer's by construction. -/
def ofPair (O : DiffObs X R) (p : NonZeroPair O) : SameDataKernel O :=
  ⟨ofDiffObs O p.val.1 p.val.2 p.property, rfl, rfl⟩

/-- Round trip one: the pair is recovered exactly. -/
theorem toPair_ofPair (O : DiffObs X R) (p : NonZeroPair O) :
    toPair O (ofPair O p) = p := by
  apply Subtype.ext
  rfl

/-- Round trip two: the kernel is recovered exactly.  The two field
equations do the work (`eq_ofDiffObs_of_fields`); the `Prop`-valued
fields `diag_zero` and `apart_ab` are recovered by definitional proof
irrelevance, so nothing beyond the pair is ever chosen. -/
theorem ofPair_toPair (O : DiffObs X R) (K : SameDataKernel O) :
    ofPair O (toPair O K) = K := by
  apply Subtype.ext
  exact (eq_ofDiffObs_of_fields O K.val K.property.1 K.property.2).symm

/-- **Distinct admissible pairs build distinct kernels**: `ofPair` is
injective, by the first round trip.  With the two round trips this is
the exact upgrade of the inhabitation statement
`kernel_from_obs_iff_pair`: for a FIXED observer, admissible pairs
and same-data kernels correspond one for one, so the pair choice IS
the kernel choice. -/
theorem ofPair_injective (O : DiffObs X R) {p q : NonZeroPair O}
    (h : ofPair O p = ofPair O q) : p = q :=
  (toPair_ofPair O p).symm.trans
    ((congrArg (toPair O) h).trans (toPair_ofPair O q))

/-- **The transpose is always a second admissible pair**: the zero
side of an observer is symmetric, so an admissible pair has an
admissible transpose, and the two kernels differ in the designated
first endpoint.

Two scope declarations.  (1) PRESENTATION GRADE: the two kernels
carry the same difference map and the same zero predicate, hence
induce the SAME `kernelApart`; they differ only in the designated
endpoints.  Nothing is claimed up to isomorphism, up to `VHom`, or up
to observational equivalence — the same scope as
`kernel_gateways_not_identical`.  (2) The symmetry used here is the
ADMITTED `zero_symm` field of `DiffObs`, priced separately at carrier
two (`kernel_not_observer`), not a derived fact; the corresponding
statement fails for a bare `WitnessedDiff`, which carries no
symmetry. -/
theorem transpose_kernel_ne (O : DiffObs X R) (a b : X)
    (hw : ¬ ZeroRel O a b) :
    ofDiffObs O a b hw ≠
      ofDiffObs O b a (fun h => hw (O.zero_symm h)) := by
  intro he
  have hab : a = b := congrArg (fun K => K.a) he
  apply hw
  rw [hab]
  exact O.zero_refl b

/-- **An observer that determines a kernel at all never determines
only one**: whenever an observer has an admissible pair —
equivalently, by `kernel_from_obs_iff_pair`, whenever a kernel
carrying its difference map and zero predicate exists at all — there
are at least two distinct such kernels.  The hypothesis is
load-bearing: an observer with no admissible pair has no such kernel
whatsoever (`kernel_no_witness_from_collapse`).  Within the
hypothesis there is no carrier bound and no value-type bound.  Same
two scope declarations as `transpose_kernel_ne`: PRESENTATION GRADE,
and resting on the ADMITTED `zero_symm` field.  This is
non-uniqueness, NOT non-existence of a selector: no claim is made
that some function from observers to kernels fails to exist. -/
theorem kernel_not_unique_of_pair (O : DiffObs X R)
    (h : ∃ a b : X, ¬ ZeroRel O a b) :
    ∃ K₁ K₂ : WitnessedDiff X R,
      K₁.delta = O.delta ∧ K₁.Zero = O.Zero ∧
        K₂.delta = O.delta ∧ K₂.Zero = O.Zero ∧ K₁ ≠ K₂ := by
  obtain ⟨a, b, hw⟩ := h
  exact ⟨ofDiffObs O a b hw,
         ofDiffObs O b a (fun hz => hw (O.zero_symm hz)),
         rfl, rfl, rfl, rfl, transpose_kernel_ne O a b hw⟩

/-- The two-element observer whose zero relation is equality: both
ordered off-diagonal pairs are admissible. -/
def boolEqObs : DiffObs Bool Bool where
  delta x y := xor x y
  Zero v := v = false
  zero_refl := by decide
  zero_symm := by
    intro x y
    revert x y
    decide
  zero_trans := by
    intro x y z
    revert x y z
    decide

/-- The first ordered off-diagonal pair is admissible. -/
theorem boolEqObs_nonzero_ft : ¬ ZeroRel boolEqObs false true :=
  fun h => Bool.noConfusion h

/-- The second ordered off-diagonal pair is admissible. -/
theorem boolEqObs_nonzero_tf : ¬ ZeroRel boolEqObs true false :=
  fun h => Bool.noConfusion h

/-- **Two distinct kernels over one observer, concretely**: both
ordered off-diagonal pairs of `boolEqObs` are admissible, and the
kernels they build differ in the designated first endpoint.
PRESENTATION GRADE, as `transpose_kernel_ne`. -/
theorem two_kernels_from_one_observer :
    ofDiffObs boolEqObs false true boolEqObs_nonzero_ft ≠
      ofDiffObs boolEqObs true false boolEqObs_nonzero_tf :=
  fun he => Bool.noConfusion (congrArg (fun K => K.a) he)

/-- **One observer, two same-data kernels**, exhibited without a
hypothesis: `boolEqObs` carries two distinct kernels with its own
difference map and zero predicate.  This is the non-uniqueness
statement; `pair_choice_load_bearing` is strictly weaker — it says
only that some pair fails the side condition.  PRESENTATION GRADE, as
`transpose_kernel_ne`. -/
theorem pair_choice_not_unique :
    ∃ (O : DiffObs Bool Bool) (K₁ K₂ : WitnessedDiff Bool Bool),
      K₁.delta = O.delta ∧ K₁.Zero = O.Zero ∧
        K₂.delta = O.delta ∧ K₂.Zero = O.Zero ∧ K₁ ≠ K₂ :=
  ⟨boolEqObs,
   ofDiffObs boolEqObs false true boolEqObs_nonzero_ft,
   ofDiffObs boolEqObs true false boolEqObs_nonzero_tf,
   rfl, rfl, rfl, rfl, two_kernels_from_one_observer⟩

/-- The relabelling action on two-element observers: negate both
arguments of the difference map.  The zero predicate and the three
law fields are carried over unchanged. -/
def swapObs (O : DiffObs Bool R) : DiffObs Bool R where
  delta x y := O.delta (!x) (!y)
  Zero := O.Zero
  zero_refl := fun x => O.zero_refl (!x)
  zero_symm := fun h => O.zero_symm h
  zero_trans := fun h₁ h₂ => O.zero_trans h₁ h₂

/-- `boolEqObs` is a fixed point of the relabelling action: negating
both arguments leaves its difference map pointwise unchanged.  The
only non-definitional step is `funext`, which in Lean 4 core is
proved from `Quot.sound`; the report for this theorem records that
dependency. -/
theorem swapObs_boolEqObs : swapObs boolEqObs = boolEqObs := by
  refine obs_eq_of_fields _ _ ?_ rfl
  funext x y
  revert x y
  decide

/-- The obstruction, at the single fixed point.  Beyond `sel` being a
TOTAL pair-valued map on `DiffObs Bool Bool`, the only hypothesis is
one instance of the negation law, taken at `boolEqObs`.  Because the
proof consumes only `sel boolEqObs`, the same argument covers any
map whose domain contains `boolEqObs` and is closed under
`swapObs` — including maps restricted to observers that have an
admissible pair. -/
theorem no_equivariant_pair_at_fixed_point
    (sel : DiffObs Bool Bool → Bool × Bool)
    (heq : sel (swapObs boolEqObs) =
      (!((sel boolEqObs).1), !((sel boolEqObs).2))) : False := by
  rw [swapObs_boolEqObs] at heq
  have hfix : ∀ x : Bool, (!x) ≠ x := by decide
  have h1 : (!((sel boolEqObs).1)) = (sel boolEqObs).1 :=
    (congrArg (fun p : Bool × Bool => p.1) heq).symm
  exact hfix (sel boolEqObs).1 h1

/-- **No relabelling-equivariant pair-valued map**: no total map to an
ordered Boolean pair commutes with negation relabelling at every
observer; the contradiction already occurs at the fixed point
`boolEqObs`.  Exact scope: total maps
`DiffObs Bool Bool → Bool × Bool` satisfying the Bool-negation
equivariance law at `boolEqObs`; nothing about other carriers,
actions, or non-equivariant maps.  A non-equivariant map on
`DiffObs Bool Bool` trivially exists.  This is NOT a general
refutation of a preferred choice.  At the relation stratum the same
obstruction is already native (`Bridge.no_swap_fixed_offdiag_pair`,
`Bridge.equivariant_not_D2`); this transports it to the observer
stratum and claims no priority over it. -/
theorem no_equivariant_pair_valued_map :
    ¬ ∃ sel : DiffObs Bool Bool → Bool × Bool,
        ∀ O : DiffObs Bool Bool,
          sel (swapObs O) = (!((sel O).1), !((sel O).2)) := by
  rintro ⟨sel, heq⟩
  exact no_equivariant_pair_at_fixed_point sel (heq boolEqObs)

/-- A supplied-style structure alone can have no witness at all: over
the total collapse no pair is complement-witnessed, so no kernel
arises from it without further data. -/
theorem kernel_no_witness_from_collapse :
    ∀ a b : Bool,
      ¬ ContactBridge.obsApart ObsDescent.collapseAllObs a b :=
  fun _ _ h => h trivial

/-- **The kernel plus the two law declarations is an observer**: the
observer-side half of the replacement claim, stated as a record
identity rather than a derivation.  The two hypotheses are exactly
the declarations the kernel deliberately omits, each priced below at
carriers two and three (`kernel_not_observer`,
`kernel_zero_not_trans`); no other data is supplied. -/
def toDiffObs (K : WitnessedDiff X R)
    (hs : ∀ x y, K.Zero (K.delta x y) → K.Zero (K.delta y x))
    (ht : ∀ x y z, K.Zero (K.delta x y) → K.Zero (K.delta y z) →
      K.Zero (K.delta x z)) : DiffObs X R where
  delta := K.delta
  Zero := K.Zero
  zero_refl := K.diag_zero
  zero_symm := fun {x y} h => hs x y h
  zero_trans := fun {x y z} h₁ h₂ => ht x y z h₁ h₂

/-- The identification is field-for-field and lossless: difference
map and zero predicate are carried unchanged, and the kernel is
recovered from the observer it yields together with its own
designated pair. -/
theorem toDiffObs_fields (K : WitnessedDiff X R)
    (hs : ∀ x y, K.Zero (K.delta x y) → K.Zero (K.delta y x))
    (ht : ∀ x y z, K.Zero (K.delta x y) → K.Zero (K.delta y z) →
      K.Zero (K.delta x z)) :
    (toDiffObs K hs ht).delta = K.delta ∧
      (toDiffObs K hs ht).Zero = K.Zero ∧
      ofDiffObs (toDiffObs K hs ht) K.a K.b K.apart_ab = K :=
  ⟨rfl, rfl, rfl⟩

/-- The relation matches in both readings: the yielded observer's
complement is the kernel's induced apartness. -/
theorem toDiffObs_apart (K : WitnessedDiff X R)
    (hs : ∀ x y, K.Zero (K.delta x y) → K.Zero (K.delta y x))
    (ht : ∀ x y z, K.Zero (K.delta x y) → K.Zero (K.delta y z) →
      K.Zero (K.delta x z)) :
    ∀ x y, ContactBridge.obsApart (toDiffObs K hs ht) x y ↔
      kernelApart K x y :=
  fun _ _ => Iff.rfl

/-! ## What the kernel does not carry: the observer admissions
priced -/

/-- The kernel is not an observer: the oriented two-element kernel's
difference and zero data extend to no `DiffObs`, because the symmetry
law field would force symmetry of the zero relation and the oriented
data refuses it.  Minimum carrier two: METATHEORY, not proved here. -/
theorem kernel_not_observer :
    ∃ K : WitnessedDiff Bool Prop,
      ¬ ∃ O : DiffObs Bool Prop,
          O.delta = K.delta ∧ O.Zero = K.Zero := by
  refine ⟨{ delta := PrimDiff.D2, Zero := Not, a := false, b := true,
            diag_zero := PrimDiff.D2_irrefl,
            apart_ab := fun hn => hn PrimDiff.D2_witness }, ?_⟩
  rintro ⟨O, hd, hz⟩
  have h1 : O.Zero (O.delta true false) := by
    rw [hd, hz]
    exact fun h => Bool.noConfusion h.1
  have h2 : O.Zero (O.delta false true) := O.zero_symm h1
  rw [hd, hz] at h2
  exact h2 PrimDiff.D2_witness

/-- The kernel's zero side need not be transitive: the complement of
the symmetric three-point relation is a kernel whose zero chain
through the third point breaks — the sealed
`Apartness.symm_without_cotrans_breaks_trans` data replayed as kernel
content.  Minimum carrier three: INHERITED, not proved here. -/
theorem kernel_zero_not_trans :
    ∃ K : WitnessedDiff (Fin 3) Prop,
      K.Zero (K.delta 0 2) ∧ K.Zero (K.delta 2 1) ∧
        ¬ K.Zero (K.delta 0 1) := by
  refine ⟨{ delta := Apartness.triSymRel, Zero := Not, a := 0, b := 1,
            diag_zero := Apartness.triSymRel_irrefl,
            apart_ab := fun hn => hn (Or.inl ⟨rfl, rfl⟩) }, ?_⟩
  exact Apartness.symm_without_cotrans_breaks_trans

/-- The induced apartness need not be symmetric: the oriented two-element
kernel refuses Bs.  Minimum carrier two: METATHEORY, not proved here. -/
theorem kernel_not_bs :
    ∃ K : WitnessedDiff Bool Prop,
      ¬ ∀ x y, kernelApart K x y → kernelApart K y x := by
  refine ⟨{ delta := PrimDiff.D2, Zero := Not, a := false, b := true,
            diag_zero := PrimDiff.D2_irrefl,
            apart_ab := fun hn => hn PrimDiff.D2_witness }, ?_⟩
  intro hs
  exact hs false true (fun hn => hn PrimDiff.D2_witness)
    fun h => Bool.noConfusion h.1

/-- The induced apartness need not be cotransitive: the three-point
complement kernel refuses Bc at the third point.  Minimum carrier
three: INHERITED from the sealed `PrimitiveCore.cotrans_auto_on_two`
minimality, not proved here. -/
theorem kernel_not_bc :
    ∃ K : WitnessedDiff (Fin 3) Prop,
      ¬ PrimitiveCore.Cotrans (kernelApart K) := by
  refine ⟨{ delta := Apartness.triSymRel, Zero := Not, a := 0, b := 1,
            diag_zero := Apartness.triSymRel_irrefl,
            apart_ab := fun hn => hn (Or.inl ⟨rfl, rfl⟩) }, ?_⟩
  intro hc
  obtain ⟨h02, h21, _⟩ := Apartness.symm_without_cotrans_breaks_trans
  rcases hc 0 1 (fun hn => hn (Or.inl ⟨rfl, rfl⟩)) 2 with h | h
  · exact h h02
  · exact h h21

/-- Locatedness of the induced apartness under an explicitly
hypothesized decidable zero predicate — the honest price, exactly the
sealed `PrimitiveCore.located_of_decidable` discipline. -/
theorem kernel_located_of_decidable (K : WitnessedDiff X R)
    [inst : ∀ v, Decidable (K.Zero v)] :
    PrimitiveCore.Located (kernelApart K) :=
  PrimitiveCore.located_of_decidable (kernelApart K)
    (inst := fun x y =>
      inferInstanceAs (Decidable (¬ K.Zero (K.delta x y))))

/-- OPEN cell: kernel locatedness without the decidability
admission. -/
def open_kernel_bl : String :=
  "OPEN: no internal countermodel exists (every kernel with a pointwise-decidable zero predicate has a located apartness, kernel_located_of_decidable); underivability of Located from the kernel fields alone is metatheoretic; Located remains separate data, matching the sealed open_cell_*_bl discipline"

/-- C never holds at the kernel's empty-store translation: the kernel
carries no protected demand. -/
theorem kernel_not_c (K : WitnessedDiff X R) :
    ¬ PrimitiveCore.C (toSetting K) :=
  fun h => h.2

/-- F never holds at the kernel's empty-store translation: the kernel
carries no retention. -/
theorem kernel_not_f (K : WitnessedDiff X R) :
    ¬ PrimitiveCore.F (toSetting K) :=
  fun h => h.2.1

/-- W: the designated pair is the witness. -/
theorem kernel_to_w (K : WitnessedDiff X R) :
    PrimitiveCore.W (toSetting K) :=
  K.apart_ab

/-- D: endpoint inequality, through the sealed A → D implication. -/
theorem kernel_to_d (K : WitnessedDiff X R) :
    PrimitiveCore.D (toSetting K) :=
  PrimitiveCore.imp_a_d (toSetting K) (toSetting_A K)

/-- E at the empty admitted family — the only family the kernel
carries. -/
theorem kernel_to_e_empty (K : WitnessedDiff X R) :
    PrimitiveCore.E (toSetting K) :=
  (PrimitiveCore.e_empty_iff_d (toSetting K) rfl).mpr (kernel_to_d K)

/-- With one declared merger over the translation, E dies while the
kernel is unchanged: the sealed `PrimDiff.merger_erases` pattern (the
`d2Merged` shape) at the kernel stratum. -/
theorem kernel_not_e_merged :
    ∃ K : WitnessedDiff Bool Bool,
      PrimitiveCore.E (toSetting K) ∧
        ¬ PrimitiveCore.E
            { toSetting K with Ops := fun f => f = fun _ => false } := by
  refine ⟨boolKernel, kernel_to_e_empty boolKernel, ?_⟩
  exact PrimDiff.merger_erases
    (F := fun f => f = fun _ => false) (v := false) rfl false true

/-- No kernel lives over the total collapse: the all-zero observer's
difference and zero data support no non-zero witness anywhere.
Serves the matrix rows D→K and E→K (native models `boolEmpty_d`,
`boolEmpty_e` cited).  Minimum carrier two as stated; the content is
the witness gap, not the carrier. -/
theorem no_kernel_over_allzero :
    ¬ ∃ K : WitnessedDiff Bool Bool,
        K.delta = ObsDescent.collapseAllObs.delta ∧
          K.Zero = ObsDescent.collapseAllObs.Zero := by
  rintro ⟨K, _, hz⟩
  apply K.apart_ab
  rw [hz]
  trivial

/-! ## Value grade is presentation -/

/-- The two-element kernel with edge value one. -/
def unitValKernel : WitnessedDiff Bool Nat where
  delta x y := cond ((!x) && y) 1 0
  Zero v := v = 0
  a := false
  b := true
  diag_zero := by decide
  apart_ab := by decide

/-- The two-element kernel with edge value two, same zero
predicate. -/
def twoValKernel : WitnessedDiff Bool Nat where
  delta x y := cond ((!x) && y) 2 0
  Zero v := v = 0
  a := false
  b := true
  diag_zero := by decide
  apart_ab := by decide

/-- **The value fork**: two kernels with identical induced apartness
and distinct difference maps — value data is strictly finer than the
apartness it induces, the kernel echo of the sealed orientation
fork. -/
theorem value_presentation_fork :
    (∀ x y, kernelApart unitValKernel x y ↔
        kernelApart twoValKernel x y) ∧
      unitValKernel.delta ≠ twoValKernel.delta := by
  constructor
  · show ∀ x y : Bool,
      ¬ (cond ((!x) && y) 1 0 = 0) ↔ ¬ (cond ((!x) && y) 2 0 = 0)
    decide
  · intro he
    have h : (1 : Nat) = 2 := congrFun (congrFun he false) true
    exact absurd h (by decide)

/-- A valued kernel morphism: a carrier map and a value map,
preserving endpoints, intertwining the difference maps, and
preserving zero. -/
structure VHom {X R X' R' : Type} (K : WitnessedDiff X R)
    (K' : WitnessedDiff X' R') where
  f : X → X'
  g : R → R'
  ha : f K.a = K'.a
  hb : f K.b = K'.b
  hdelta : ∀ x y, K'.delta (f x) (f y) = g (K.delta x y)
  hzero : ∀ v, K.Zero v → K'.Zero (g v)

/-- Valued kernel morphisms are not determined by the carrier map:
off the image of the difference map the value map is free — the
kernel echo of the sealed off-image factor non-uniqueness
(`Compression.factor_not_unique_off_image`). -/
theorem vhom_not_unique :
    ∃ h₁ h₂ : VHom unitValKernel boolKernel,
      h₁.f = h₂.f ∧ h₁ ≠ h₂ := by
  refine ⟨⟨fun x => x, fun v => v == 1, rfl, rfl, by decide, ?_⟩,
          ⟨fun x => x, fun v => v != 0, rfl, rfl, by decide, ?_⟩,
          rfl, ?_⟩
  · intro v hv
    have hv' : v = 0 := hv
    subst hv'
    rfl
  · intro v hv
    have hv' : v = 0 := hv
    subst hv'
    rfl
  · intro he
    exact Bool.noConfusion (congrFun (congrArg VHom.g he) 2)

/-- Surjectivity of the difference map onto the value type. -/
def DeltaOnto (K : WitnessedDiff X R) : Prop :=
  ∀ v : R, ∃ x y, K.delta x y = v

/-- Under delta-surjectivity the carrier map determines the morphism:
uniqueness restored exactly at the epi grade — the kernel echo of the
sealed `PrimitiveCats.phom2_unique_of_epi`.  On the observer side the
corresponding uniqueness is global only because quotient projections
are epi by induction (`ObsDescent.obsQuotient_mk_surjective`). -/
theorem vhom_unique_of_onto {X R X' R' : Type} (K : WitnessedDiff X R)
    (K' : WitnessedDiff X' R') (hsurj : DeltaOnto K)
    (h₁ h₂ : VHom K K') (hf : h₁.f = h₂.f) : h₁ = h₂ := by
  have hg : h₁.g = h₂.g := by
    funext v
    obtain ⟨x, y, hxy⟩ := hsurj v
    calc h₁.g v = h₁.g (K.delta x y) := by rw [hxy]
      _ = K'.delta (h₁.f x) (h₁.f y) := (h₁.hdelta x y).symm
      _ = K'.delta (h₂.f x) (h₂.f y) := by rw [hf]
      _ = h₂.g v := by rw [h₂.hdelta x y, hxy]
  cases h₁ with
  | mk f₁ g₁ ha₁ hb₁ hd₁ hz₁ =>
    cases h₂ with
    | mk f₂ g₂ ha₂ hb₂ hd₂ hz₂ =>
      have hf' : f₁ = f₂ := hf
      have hg' : g₁ = g₂ := hg
      subst hf'
      subst hg'
      rfl

/-! ## Universal status: inherited from the sealed initiality -/

/-- The canonical kernel's induced apartness is exactly the sealed
oriented two-element relation. -/
theorem boolKernel_apart_iff :
    ∀ x y, kernelApart boolKernel x y ↔ PrimDiff.D2 x y := by
  show ∀ x y : Bool, ¬ (((!x) && y) = false) ↔ PrimDiff.D2 x y
  decide

/-- Every kernel presents a pointed witnessed relation: carrier,
induced apartness, designated pair, and the witness. -/
def apartObj (K : WitnessedDiff X R) : PrimitiveCats.PtdRel :=
  ⟨X, kernelApart K, K.a, K.b, K.apart_ab⟩

/-- The presented object is always irreflexive. -/
theorem apartObj_irrefl (K : WitnessedDiff X R) :
    PrimitiveCats.IrreflObj (apartObj K) :=
  kernelApart_irrefl K

/-- Observer-derived kernels land in the symmetric subcategory: the
zero symmetry law field, contraposed, symmetrizes the induced
apartness — where the sealed `PrimitiveCats.s2_initial_sym`
applies. -/
theorem apartObj_sym_of_observer (O : DiffObs X R) (a b : X)
    (hw : ¬ ZeroRel O a b) :
    PrimitiveCats.SymObj (apartObj (ofDiffObs O a b hw)) :=
  fun _ _ hxy hz => hxy (O.zero_symm hz)

/-- **The gateway is inherited unconditionally**: the sealed
two-element initial object has exactly one morphism into every
kernel's presented object — `PrimitiveCats.d2_initial`,
instantiated, never re-proved. -/
theorem kernel_gateway_unique (K : WitnessedDiff X R) :
    ∃ h : PrimitiveCats.Hom PrimitiveCats.d2Obj (apartObj K),
      ∀ h' : PrimitiveCats.Hom PrimitiveCats.d2Obj (apartObj K),
        h' = h :=
  PrimitiveCats.d2_initial (apartObj K)

/-- The gateway map is injective into every kernel: the sealed
`PrimitiveCats.d2_map_injective` at the always-irreflexive presented
object. -/
theorem kernel_gateway_injective (K : WitnessedDiff X R)
    (h : PrimitiveCats.Hom PrimitiveCats.d2Obj (apartObj K)) :
    ∀ x y : Bool, h.f x = h.f y → x = y :=
  PrimitiveCats.d2_map_injective (apartObj K) (apartObj_irrefl K) h

/-- The oppositely pointed canonical kernel: transposed difference
map, endpoints swapped. -/
def boolKernelSwap : WitnessedDiff Bool Bool where
  delta x y := x && (!y)
  Zero v := v = false
  a := true
  b := false
  diag_zero := by decide
  apart_ab := by decide

/-- Two canonical kernels that are not identical as presentations:
gateway uniqueness is up to isomorphism only (the sealed
`PrimitiveCats.initials_iso` / `two_initials_not_identical`
scope). -/
theorem kernel_gateways_not_identical : boolKernel ≠ boolKernelSwap :=
  fun he => Bool.noConfusion (congrArg (fun K => K.a) he)

/-- The three-point kernel with one oriented edge and a free third
point, Bool-valued so that its apartness computes outright. -/
def freeKernel : WitnessedDiff (Fin 3) Bool where
  delta i j := decide (PrimitiveCore.triR i j)
  Zero v := v = false
  a := 0
  b := 1
  diag_zero := by decide
  apart_ab := by decide

/-- Into every kernel the free kernel has two distinct morphisms: the
free third point maps to either endpoint, which differ by
`kernel_endpoints_ne` — the same branching mechanism as the sealed
`PrimitiveCats.no_terminal_pres2`. -/
theorem kernel_no_terminal {X' R' : Type} (K' : WitnessedDiff X' R') :
    ∃ h₁ h₂ : PrimitiveCats.Hom (apartObj freeKernel) (apartObj K'),
      h₁ ≠ h₂ := by
  have hedge : ∀ x y : Fin 3,
      (decide (PrimitiveCore.triR x y) = false) ∨
        (x = 0 ∧ y = 1) := by decide
  refine ⟨⟨fun i : Fin 3 => if i = 1 then K'.b else K'.a,
           rfl, rfl, ?_⟩,
          ⟨fun i : Fin 3 => if i = 0 then K'.a else K'.b,
           rfl, rfl, ?_⟩, ?_⟩
  · intro x y hxy
    rcases hedge x y with hz | ⟨hx, hy⟩
    · exact absurd hz hxy
    · subst hx
      subst hy
      exact K'.apart_ab
  · intro x y hxy
    rcases hedge x y with hz | ⟨hx, hy⟩
    · exact absurd hz hxy
    · subst hx
      subst hy
      exact K'.apart_ab
  · intro he
    have h2 : K'.a = K'.b :=
      congrFun (congrArg PrimitiveCats.Hom.f he) (2 : Fin 3)
    exact kernel_endpoints_ne K' h2

/-- **No terminal collector of kernels exists**: a collector would
give the free kernel a unique morphism, against the branching
above. -/
theorem kernel_no_terminal_collector :
    ¬ ∃ (X' R' : Type) (K' : WitnessedDiff X' R'),
        ∀ (X R : Type) (K : WitnessedDiff X R),
          ∃ h : PrimitiveCats.Hom (apartObj K) (apartObj K'),
            ∀ h', h' = h := by
  rintro ⟨X', R', K', hall⟩
  obtain ⟨h, hu⟩ := hall (Fin 3) Bool freeKernel
  obtain ⟨h₁, h₂, hne⟩ := kernel_no_terminal K'
  exact hne ((hu h₁).trans (hu h₂).symm)

/-! ## Passage entry -/

/-- The pre-retention passage state as a pointed witnessed relation:
the asserted store, pointed at the canonical pair. -/
def passageObj : PrimitiveCats.PtdRel :=
  ⟨Nat, fun i j => (i, j) ∈ PrimitivePassage.preRetained.asserted,
   0, 1, by decide⟩

/-- Entry into the passage factors through the same initial
presentation as entry into every kernel: the sealed
`PrimitiveCats.d2_initial`, instantiated at the passage object. -/
theorem passage_gateway_unique :
    ∃ h : PrimitiveCats.Hom PrimitiveCats.d2Obj passageObj,
      ∀ h' : PrimitiveCats.Hom PrimitiveCats.d2Obj passageObj,
        h' = h :=
  PrimitiveCats.d2_initial passageObj

/-- **The kernel licenses passage entry**: distinct endpoints, the
sealed pre-retention candidate-A entry
(`PrimitivePassage.kernel_enters_preretained`, reused not re-proved),
and the still-empty retention store. -/
theorem kernel_licenses_entry (K : WitnessedDiff X R) :
    K.a ≠ K.b ∧
      PrimitiveCore.A
        (PrimitivePassage.inducedSetting
          PrimitivePassage.preRetained 0 1) ∧
      PrimitivePassage.preRetained.wit = [] :=
  ⟨kernel_endpoints_ne K,
   PrimitivePassage.kernel_enters_preretained.1,
   PrimitivePassage.kernel_enters_preretained.2⟩

/-- The entry state precedes protection and observation, and nothing
is obstructed there: retention, protection, and observation each
remain separately priced events after entry — exactly the sealed
13-arrow discipline (`PrimitivePassage.obst_requires_observation`
spent on the third conjunct). -/
theorem entry_pre_observation :
    PrimitivePassage.preRetained.prot = [] ∧
      PrimitivePassage.preRetained.obs = none ∧
      PrimitivePassage.obstP PrimitivePassage.preRetained 0 1 =
        false :=
  ⟨by decide, by decide,
   PrimitivePassage.obst_requires_observation
     PrimitivePassage.preRetained 0 1 (by decide)⟩

/-- A total two-point presentation of the endpoints costs decidable
equality of the carrier — the honest price of totality.  Sufficiency
only: no converse is proved, so necessity is not claimed.  Without it
only the licensing form above is claimed. -/
theorem kernel_two_point_presentation {X R : Type} [DecidableEq X]
    (K : WitnessedDiff X R) : ∃ p : X → Nat, p K.a = 0 ∧ p K.b = 1 :=
  ⟨fun x => if x = K.a then 0 else 1, if_pos rfl,
   if_neg fun he => kernel_endpoints_ne K he.symm⟩

/-! ## The machine-checkable matrix -/

/-- The 37 collision cells: kernel stratum (K, against the nine
native candidate readings) and observer stratum (Obs and the
representability, dictionary, and placement rows).  Row format:
(id, status, evidence names). -/
def contactCells : List (String × String × String) :=
  [("K_to_W", "IMPLIES", "kernel_to_w"),
   ("W_to_K", "COUNTERMODEL size 1",
    "no_kernel_on_subsingleton (unitBare cited)"),
   ("K_to_A", "IMPLIES", "toSetting_A"),
   ("A_to_K", "EQUIV_UNDER_DEC (asserted relation S.r)",
    "ofSetting, ofSetting_exact, open_kernel_grade"),
   ("K_to_Bs", "COUNTERMODEL size 2", "kernel_not_bs"),
   ("Bs_to_K", "IMPLIES", "ofSetting (Bs within A)"),
   ("K_to_Bc", "COUNTERMODEL size 3", "kernel_not_bc"),
   ("Bc_to_K", "IMPLIES", "ofSetting (Bc within A)"),
   ("K_to_Bl", "CONDITIONAL_DEC + OPEN_PRICED",
    "kernel_located_of_decidable, open_kernel_bl"),
   ("Bl_to_K", "IMPLIES", "ofSetting (Bl within A)"),
   ("K_to_C", "COUNTERMODEL (never derivable, freely declarable)",
    "kernel_not_c, kernel_prot_independent"),
   ("C_to_K", "COUNTERMODEL size 1",
    "no_kernel_on_subsingleton (unitFull cited)"),
   ("K_to_D", "IMPLIES", "kernel_to_d"),
   ("D_to_K", "COUNTERMODEL size 2", "no_kernel_over_allzero"),
   ("K_to_E", "IMPLIES (empty Ops) / COUNTERMODEL (merged)",
    "kernel_to_e_empty, kernel_not_e_merged"),
   ("E_to_K", "COUNTERMODEL size 2",
    "no_kernel_over_allzero (boolEmpty_e cited)"),
   ("K_to_F", "COUNTERMODEL (never derivable)", "kernel_not_f"),
   ("F_to_K", "IMPLIES",
    "ofSetting via imp_f_a, ofSetting_ret_irrelevant"),
   ("Obs_to_Bs", "IMPLIES", "obsSetting_bs"),
   ("Obs_to_Bc", "CONDITIONAL_DEC + OPEN_PRICED",
    "obsApart_cotrans, cotrans_schema_iff_wlem, open_bridge_cotrans"),
   ("Obs_to_Bl", "CONDITIONAL_DEC + OPEN_PRICED",
    "obsSetting_bl, located_schema_implies_wlem, open_bridge_located"),
   ("repr_crown", "CHARACTERIZATION", "obsApart_repr_iff"),
   ("D2_repr (H3)", "COUNTERMODEL size 2", "d2_not_obs_complement"),
   ("Bs_repr", "COUNTERMODEL size 3, positive at 2",
    "triSym_not_obs_complement, bool_bs_repr"),
   ("total_repr (W/C)", "COUNTERMODEL size 1", "unit_total_not_repr"),
   ("witness_repr (D/E)", "COUNTERMODEL size 2",
    "d_not_witnessed_repr"),
   ("meet_roundtrip", "EQUIV_UNDER_DEC (apartness r one way, ZeroRel back)",
    "isApart_repr, obsApart_isApart, apartObs_roundtrip, indist_obsApart_iff"),
   ("stability_price", "OPEN_PRICED", "stability_schema_iff_dne"),
   ("descent_vs_factorsOn", "SAME_THIRD_NOTION",
    "descend_iff_factorsOn_all, classConstant_iff_fiberConstant_all"),
   ("fixed_D_strict", "COUNTERMODEL (D = [])",
    "fiberConstant_fixed_D_not_classConstant"),
   ("uniqueness_scope", "SAME_THIRD_NOTION",
    "obsQuotient_mk_surjective (+ sealed citations)"),
   ("quot_barrier", "NATIVE_MORE_GENERAL",
    "Derivation.quot_barrier (citation)"),
   ("pairing_dict", "SAME_THIRD_NOTION",
    "classConstant_pair_iff, sigEq_append_iff"),
   ("flagship_vs_obstP", "SAME_THIRD_NOTION (native finer)",
    "pair_blocked_is_collapse_collision (+ obst_conditions_independent cited)"),
   ("tail_subsumption", "SAME_THIRD_NOTION",
    "intDiffObs, int_sub_ne_zero_iff, int_sub_ne_zero_of_gt, int_shift_cancel, int_two_mul_eq_zero_iff, int_add_sub_cancel"),
   ("observer_placement (H1)",
    "IMPLIES (native proves what supplied fields declare)",
    "declared_zero_as_view, observation_stage_realizes_observer, kernelStage, kernel_stage_no_obstruction"),
   ("value_orientation", "INCOMPARABLE_SUBROW",
    "value_orientation_survives, value_presentation_fork")]

/-- The matrix is complete: exactly 37 cells. -/
theorem contactCells_length : contactCells.length = 37 := rfl

end ContactKernel
