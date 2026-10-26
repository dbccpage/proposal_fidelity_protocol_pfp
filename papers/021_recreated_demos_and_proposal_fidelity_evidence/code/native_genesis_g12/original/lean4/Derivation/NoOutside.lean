import Derivation.Represented

/-!
# Ultra closure, Stage IV: the strongest form of Rule 2

"No observer from nowhere", settled for the fixed kernel constitution:

1. the one-step operational-support factorization extends to whole
   histories, to successor families, and to verdicts (quiescence);
2. the effectual-outside dichotomy is packaged as a corollary — a
   difference that changes an operational result already differs in
   the represented support; a difference that changes none has no
   operational authority.  No metaphysical claim is made or licensed;
3. the invariance ceiling is lifted to family-valued constructions;
4. the certification panel is integrated into a conservative extension
   kernel, so certification becomes replay-integrated, and the
   panel-induced non-separation is proved an equivalence relation —
   panel-relative warrant is exactly joint-quotient closure, never
   correspondence.
-/

namespace NoOutside

open Represented

/-! ## 7.1 — support factorization over histories, families, verdicts -/

/-- History form: support-agreeing worlds replay to support-agreeing
worlds under every event stream.  Same represented constitution + same
represented support + same represented history → same successor
support. -/
theorem support_replay (h : List Event) :
    ∀ {w w' : World}, supp w = supp w' →
      supp (replay h w) = supp (replay h w') := by
  induction h with
  | nil => intro w w' hs; exact hs
  | cons e rest ih =>
      intro w w' hs
      exact ih (support_determines w w' hs e)

/-- The successor family factors through the support: the notes field
never enters the internally determined family. -/
theorem support_repairFamily (w w' : World) (h : supp w = supp w')
    (r : Req) : repairFamily w r = repairFamily w' r := by
  cases w with
  | mk d v rq f b a nt =>
    cases w' with
    | mk d' v' rq' f' b' a' nt' =>
      simp only [supp, Supp.mk.injEq] at h
      obtain ⟨h1, h2, h3, h4, h5, h6⟩ := h
      subst h1; subst h2; subst h3; subst h4; subst h5; subst h6
      rfl

/-- Verdicts factor through the support: quiescence never reads the
notes field. -/
theorem support_quiescent (w w' : World) (h : supp w = supp w') :
    quiescentB w = quiescentB w' := by
  cases w with
  | mk d v rq f b a nt =>
    cases w' with
    | mk d' v' rq' f' b' a' nt' =>
      simp only [supp, Supp.mk.injEq] at h
      obtain ⟨h1, h2, h3, h4, h5, h6⟩ := h
      subst h1; subst h2; subst h3; subst h4; subst h5; subst h6
      rfl

/-- Obstruction certificates factor through the support. -/
theorem support_obstructed (w w' : World) (h : supp w = supp w')
    (r : Req) : obstructedB w r = obstructedB w' r := by
  cases w with
  | mk d v rq f b a nt =>
    cases w' with
    | mk d' v' rq' f' b' a' nt' =>
      simp only [supp, Supp.mk.injEq] at h
      obtain ⟨h1, h2, h3, h4, h5, h6⟩ := h
      subst h1; subst h2; subst h3; subst h4; subst h5; subst h6
      rfl

/-! ## 7.2 — the effectual-outside dichotomy -/

/-- **The effectual-outside dichotomy, bundled.**  For any two
configurations agreeing on represented support and fed the same
represented history: the replayed support, the successor family, the
obstruction certificate, and the quiescence verdict all agree.
Contrapositively, whatever changes any of these operational results
already differs inside the represented support — its "outside-ness"
has entered the books.  And a difference that changes none of them has
no operational authority in the kernel.  Scope: an operational theorem
about this fixed constitution; not a statement about unrepresented
existence. -/
theorem effectual_outside_dichotomy (w w' : World)
    (hs : supp w = supp w') (h : List Event) (r : Req) :
    supp (replay h w) = supp (replay h w') ∧
      repairFamily (replay h w) r = repairFamily (replay h w') r ∧
      obstructedB (replay h w) r = obstructedB (replay h w') r ∧
      quiescentB (replay h w) = quiescentB (replay h w') := by
  have hrep := support_replay h hs
  exact ⟨hrep, support_repairFamily _ _ hrep r,
    support_obstructed _ _ hrep r, support_quiescent _ _ hrep⟩

/-! ## 7.3 — the invariance ceiling for families -/

/-- Family form of the invariance ceiling: an equivariant
family-valued construction maps a symmetry-fixed input to a
symmetry-fixed family.  The single-output form is the earlier general
lemma; this is its lift to complete successor families, so the ceiling
constrains tied menus exactly as it constrains single results. -/
theorem equivariant_family_invariant {S R : Type} (actS : S → S)
    (actR : R → R) (F : S → List R)
    (hequiv : ∀ s, F (actS s) = (F s).map actR) :
    ∀ s, actS s = s → (F s).map actR = F s := by
  intro s hfix
  calc (F s).map actR = F (actS s) := (hequiv s).symm
    _ = F s := by rw [hfix]

/-! ## 7.4 — the certification panel, replay-integrated

The panel stops being a free function argument: `CWorld` extends the
kernel with a represented panel store and one admission event for
evaluators.  Base events are interpreted exactly as before
(conservativity is definitional and stated), so every sealed kernel
theorem transports; certification verdicts become functions of the
replayed state. -/

structure CWorld where
  base : World
  panel : List Evaluator
deriving Repr, DecidableEq

inductive CEvent where
  | base (e : Event)
  | admitEvaluator (E : Evaluator)
deriving Repr, DecidableEq

def stepC (cw : CWorld) : CEvent → CWorld
  | .base e => ⟨step cw.base e, cw.panel⟩
  | .admitEvaluator E =>
      if E ∈ cw.panel then cw
      else ⟨cw.base, cw.panel ++ [E]⟩

def replayC (h : List CEvent) (cw : CWorld) : CWorld :=
  h.foldl stepC cw

/-- Conservativity over the sealed kernel: base events act exactly as
the sealed step on the base component and never touch the panel. -/
theorem stepC_conservative (cw : CWorld) (e : Event) :
    (stepC cw (.base e)).base = step cw.base e ∧
      (stepC cw (.base e)).panel = cw.panel :=
  ⟨rfl, rfl⟩

/-- Evaluator admission never touches the kernel state: panels are
observation apparatus, not object-level structure. -/
theorem admitEvaluator_base_inert (cw : CWorld) (E : Evaluator) :
    (stepC cw (.admitEvaluator E)).base = cw.base := by
  simp only [stepC]
  split <;> rfl

/-- Certification is now replay-integrated: the verdict is a function
of the replayed represented state alone. -/
def certPosC (cw : CWorld) (i j : Nat) : Bool :=
  certPosB cw.panel i j

def certNegC (cw : CWorld) (i j : Nat) : Bool :=
  certNegB cw.panel i j

/-- The panel store is replay-deterministic in the extended kernel. -/
theorem replayC_deterministic (h : List CEvent) {cw cw' : CWorld}
    (hw : cw = cw') : replayC h cw = replayC h cw' := by rw [hw]

/-! ### The panel-induced non-separation is an equivalence -/

/-- Joint non-separation: no column of any evaluator of the panel
separates the pair.  This is the panel's joint quotient. -/
def PanelEquiv (panel : List Evaluator) (i j : Nat) : Prop :=
  ∀ E ∈ panel, ∀ c ∈ E, ((i ∈ c) ↔ (j ∈ c))

theorem panel_equiv (panel : List Evaluator) :
    Equivalence (PanelEquiv panel) := by
  refine ⟨?_, ?_, ?_⟩
  · intro x E hE c hc
    exact Iff.rfl
  · intro x y hxy E hE c hc
    exact (hxy E hE c hc).symm
  · intro x y z hxy hyz E hE c hc
    exact (hxy E hE c hc).trans (hyz E hE c hc)

/-- The negative certificate is exactly joint-quotient membership (for
a non-empty panel): panel-relative warrant, joint quotient closure,
and public replay agreement name one relation. -/
theorem certNeg_iff_panelEquiv (panel : List Evaluator) (i j : Nat) :
    certNegB panel i j = true ↔
      panel ≠ [] ∧ PanelEquiv panel i j := by
  unfold certNegB
  simp only [Bool.and_eq_true, List.all_eq_true]
  constructor
  · rintro ⟨hne, hall⟩
    constructor
    · intro hnil
      rw [hnil] at hne
      exact absurd hne (by decide)
    · intro E hE c hc
      have hv := hall E hE
      unfold verdictB at hv
      cases hd : (decide (i ∈ c)) <;> cases hd' : (decide (j ∈ c))
      · constructor <;> intro hmem <;>
          (exfalso
           first
             | exact absurd (decide_eq_true hmem) (by rw [hd]; decide)
             | exact absurd (decide_eq_true hmem) (by rw [hd']; decide))
      · exfalso
        have hsep : sepB c i j = true := by
          unfold sepB
          rw [hd, hd']
          rfl
        have : E.any (fun c => sepB c i j) = true := by
          simp only [List.any_eq_true]
          exact ⟨c, hc, hsep⟩
        rw [this] at hv
        exact absurd hv (by decide)
      · exfalso
        have hsep : sepB c i j = true := by
          unfold sepB
          rw [hd, hd']
          rfl
        have : E.any (fun c => sepB c i j) = true := by
          simp only [List.any_eq_true]
          exact ⟨c, hc, hsep⟩
        rw [this] at hv
        exact absurd hv (by decide)
      · constructor <;> intro _ <;>
          (exact of_decide_eq_true (by
            first | rw [hd'] | rw [hd]
            ))
  · rintro ⟨hne, heq⟩
    constructor
    · cases panel with
      | nil => exact absurd rfl hne
      | cons E rest => rfl
    · intro E hE
      unfold verdictB
      cases hv : E.any (fun c => sepB c i j) with
      | false => rfl
      | true =>
          exfalso
          simp only [List.any_eq_true] at hv
          obtain ⟨c, hc, hsep⟩ := hv
          have hiff := heq E hE c hc
          unfold sepB at hsep
          cases hd : (decide (i ∈ c)) <;>
            cases hd' : (decide (j ∈ c)) <;>
            rw [hd, hd'] at hsep
          · exact absurd hsep (by decide)
          · exact absurd
              (decide_eq_true (hiff.mpr (of_decide_eq_true hd')))
              (by rw [hd]; decide)
          · exact absurd
              (decide_eq_true (hiff.mp (of_decide_eq_true hd)))
              (by rw [hd']; decide)
          · exact absurd hsep (by decide)

/-- What certification does *not* establish is sealed evidence:
`Represented.cert_not_correspondence` — a unanimous panel certifies an
equivalence that a column outside the panel refutes.  The ceiling
carries over verbatim to the replay-integrated form, since `certNegC`
is `certNegB` of the replayed panel. -/
theorem certC_ceiling :
    certNegC ⟨genesis, [[[0, 1]], [[0, 1]]]⟩ 0 1 = true ∧
      sepB [0] 0 1 = true := cert_not_correspondence

end NoOutside
