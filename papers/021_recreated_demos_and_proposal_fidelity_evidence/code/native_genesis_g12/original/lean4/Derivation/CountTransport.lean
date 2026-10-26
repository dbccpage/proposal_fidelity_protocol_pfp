import Derivation.Basic

/-!
# Transport of observational collapse under a datum renaming (R6)

Residual R6 in `paper.md` section 12 is kind (a): the mathematics is
certified exhaustively in Python (`test_canonical_invariant_under_rename`,
`test_closure_policy_is_token_blind`) and the Lean is absent.  This
module supplies the Lean.

The claim discharged here is `CL-COUNT-INVARIANCE`: the collapsed-pair
count is invariant under a renaming of the data indices.

## Why this is provable at all, stated before the proofs

`collapsed` quantifies over well-formed contexts and asks about
`derivable`.  Reading the definitions:

* `wfCtx` mentions `r.forms` and `r.data` and nothing else;
* `derivable` mentions `r.insts` and `r.rules` and nothing else.

So `r.reqs` **never enters observational collapse**.  A renaming need
not preserve the `q.1 < q.2` ordering that `Regime.wf` imposes on
requirements, and that would be an obstruction if collapse depended on
them.  It does not, so the action below leaves `reqs` alone and the
obstruction never arises.  This is a fact about the definitions, not a
convenience: it is recorded here because it is the reason the transport
is clean.

## What is proved, and what is not

`collapsed_rename` is an iff and is unconditional in the renaming's
bounds — it needs only that `σ` is a bijection on `Nat`.  The bound
fields are needed for `wfCtx_rename`, and only there.

Nothing here decides `collapsed`.  Its quantifier ranges over `Ctx`,
which is infinite, and although `wfCtx` cuts it to a finite set, that
enumeration is not built here.  The counting statement is therefore
phrased over a caller-supplied list of candidate pairs with the
decidability supplied by the caller — which is exactly how the Python
uses it, over `List.range r.data` squared.
-/

namespace Derivation

/-- A renaming of datum indices: a bijection on `Nat` that maps the
admitted range into itself in both directions.  Same shape as
`Attachment.Renaming`, restated here because that one acts on passage
states and this one acts on regimes. -/
structure DRen (n : Nat) where
  f : Nat → Nat
  g : Nat → Nat
  fg : ∀ x, g (f x) = x
  gf : ∀ x, f (g x) = x
  fbound : ∀ x, x < n → f x < n
  gbound : ∀ x, x < n → g x < n

namespace DRen

variable {n : Nat}

theorem f_inj (σ : DRen n) : ∀ {x y}, σ.f x = σ.f y → x = y := by
  intro x y h
  have := congrArg σ.g h
  rwa [σ.fg, σ.fg] at this

/-- The inverse renaming. -/
def inv (σ : DRen n) : DRen n where
  f := σ.g
  g := σ.f
  fg := σ.gf
  gf := σ.fg
  fbound := σ.gbound
  gbound := σ.fbound

end DRen

/-- Rename the datum indices inside an instance. -/
def mapInst (f : Nat → Nat) (i : Inst) : Inst := (i.1, i.2.map f)

/-- Rename the datum indices inside a context's filled slots.  Holes
stay holes: a hole is a position, not a datum. -/
def mapCtx (f : Nat → Nat) (c : Ctx) : Ctx :=
  ⟨c.form, c.slots.map (Option.map f)⟩

/-- The action on regimes.  `data`, `forms` and `rules` are index-free
or form-indexed and are untouched; `insts` carries datum indices and is
mapped; `reqs` is left alone because collapse does not read it (see the
module header). -/
def renameRegime (f : Nat → Nat) (r : Regime) : Regime :=
  { r with insts := r.insts.map (mapInst f) }

theorem list_map_inj {f : Nat → Nat} (hf : ∀ {x y}, f x = f y → x = y) :
    ∀ {l m : List Nat}, l.map f = m.map f → l = m := by
  intro l
  induction l with
  | nil => intro m h; cases m with
    | nil => rfl
    | cons b bs => exact absurd h (by simp)
  | cons a as ih =>
    intro m h
    cases m with
    | nil => exact absurd h (by simp)
    | cons b bs =>
      simp only [List.map_cons, List.cons.injEq] at h
      have h1 : a = b := hf h.1
      have h2 : as = bs := ih h.2
      subst h1; subst h2; rfl

theorem mapInst_inj {f : Nat → Nat} (hf : ∀ {x y}, f x = f y → x = y)
    {i j : Inst} (h : mapInst f i = mapInst f j) : i = j := by
  obtain ⟨a, l⟩ := i
  obtain ⟨b, m⟩ := j
  simp only [mapInst, Prod.mk.injEq] at h
  have h2 : l = m := list_map_inj hf h.2
  have h1 : a = b := h.1
  subst h1; subst h2; rfl

/-! ## Plugging commutes with renaming -/

/-- Renaming a context and plugging the renamed datum is the same as
plugging and then renaming.  The hole case is the one that matters: a
hole receives the datum, so it receives the RENAMED datum on the left
and is renamed after receiving on the right — and those agree. -/
theorem plug_mapCtx (f : Nat → Nat) (c : Ctx) (d : Nat) :
    plug (mapCtx f c) (f d) = mapInst f (plug c d) := by
  have hfun : (fun s : Option Nat => Option.getD (Option.map f s) (f d))
            = (fun s : Option Nat => f (Option.getD s d)) := by
    funext s; cases s <;> rfl
  simp only [plug, mapCtx, mapInst, List.map_map, Prod.mk.injEq, true_and]
  show List.map ((fun s => Option.getD s (f d)) ∘ Option.map f) c.slots
     = List.map (f ∘ (fun s => Option.getD s d)) c.slots
  exact congrArg (fun g => List.map g c.slots) hfun

/-! ## Derivability transports -/

theorem derivable_rename {f : Nat → Nat} (hf : ∀ {x y}, f x = f y → x = y)
    (r : Regime) (i : Inst) :
    derivable (renameRegime f r) (mapInst f i) ↔ derivable r i := by
  constructor
  · intro h
    cases h with
    | inl hm =>
      obtain ⟨j, hj, hij⟩ := List.mem_map.mp hm
      exact Or.inl (mapInst_inj hf hij ▸ hj)
    | inr hr => exact Or.inr hr
  · intro h
    cases h with
    | inl hm => exact Or.inl (List.mem_map.mpr ⟨i, hm, rfl⟩)
    | inr hr => exact Or.inr hr

/-! ## Well-formed contexts transport -/

theorem wfCtx_rename {n : Nat} (σ : DRen n) (r : Regime) (hn : r.data = n)
    (c : Ctx) :
    wfCtx (renameRegime σ.f r) (mapCtx σ.f c) ↔ wfCtx r c := by
  subst hn
  simp only [wfCtx, mapCtx, renameRegime, List.length_map]
  constructor
  · rintro ⟨h1, h2, h3, h4⟩
    refine ⟨h1, h2, ?_, ?_⟩
    · obtain ⟨s, hs, hse⟩ := List.mem_map.mp h3
      cases s with
      | none => exact hs
      | some x => exact absurd hse (by simp)
    · intro s hs
      have hm := h4 (Option.map σ.f s) (List.mem_map.mpr ⟨s, hs, rfl⟩)
      cases s with
      | none => trivial
      | some x =>
        show x < r.data
        have hx : σ.f x < r.data := hm
        have := σ.gbound _ hx
        rwa [σ.fg] at this
  · rintro ⟨h1, h2, h3, h4⟩
    refine ⟨h1, h2, List.mem_map.mpr ⟨none, h3, rfl⟩, ?_⟩
    intro s hs
    obtain ⟨t, ht, hte⟩ := List.mem_map.mp hs
    have hm := h4 t ht
    cases t with
    | none => exact hte ▸ trivial
    | some x =>
      have hx : x < r.data := hm
      have : σ.f x < r.data := σ.fbound _ hx
      exact hte ▸ this

/-! ## The transport theorem -/

theorem mapCtx_f_g {n : Nat} (σ : DRen n) (c : Ctx) :
    mapCtx σ.f (mapCtx σ.g c) = c := by
  simp only [mapCtx, List.map_map]
  have hfun : (Option.map σ.f ∘ Option.map σ.g) = (fun s : Option Nat => s) := by
    funext s; cases s with
    | none => rfl
    | some x => show Option.map σ.f (some (σ.g x)) = some x
                rw [Option.map]; exact congrArg some (σ.gf x)
  rw [hfun]
  simp

/-- **R6, the mathematical content.**  Observational collapse is
invariant under a renaming of the datum indices: the renamed regime
collapses the renamed pair exactly when the original collapses the
original pair. -/
theorem collapsed_rename {n : Nat} (σ : DRen n) (r : Regime) (hn : r.data = n)
    (d d' : Nat) :
    collapsed (renameRegime σ.f r) (σ.f d) (σ.f d') ↔ collapsed r d d' := by
  constructor
  · intro h c hc
    have hwf := (wfCtx_rename σ r hn c).mpr hc
    have hh := h (mapCtx σ.f c) hwf
    rw [plug_mapCtx, plug_mapCtx] at hh
    rwa [derivable_rename σ.f_inj, derivable_rename σ.f_inj] at hh
  · intro h c' hc'
    have hc : mapCtx σ.f (mapCtx σ.g c') = c' := mapCtx_f_g σ c'
    have hwf : wfCtx r (mapCtx σ.g c') := by
      rw [← wfCtx_rename σ r hn (mapCtx σ.g c'), hc]; exact hc'
    have hh := h (mapCtx σ.g c') hwf
    have e1 : plug c' (σ.f d) = mapInst σ.f (plug (mapCtx σ.g c') d) := by
      rw [← plug_mapCtx, hc]
    have e2 : plug c' (σ.f d') = mapInst σ.f (plug (mapCtx σ.g c') d') := by
      rw [← plug_mapCtx, hc]
    rw [e1, e2, derivable_rename σ.f_inj, derivable_rename σ.f_inj]
    exact hh

/-! ## The counting corollary: `CL-COUNT-INVARIANCE` -/

/-- **R6, as the paper states it.**  The collapsed-pair count is
invariant under renaming.

The decision procedure is a parameter, not a synthesized instance, and
that is deliberate.  `collapsed` quantifies over `Ctx`, which is
infinite; `wfCtx` cuts it to a finite set, but this module does not
build that enumeration.  So the caller supplies a Boolean test together
with a proof that it tracks `collapsed` — which is exactly the division
of labour the repository already runs on: Python decides, Lean states
what the decision means.  Given any candidate list (in practice
`List.range r.data` squared, which is what the implementation walks),
the two counts agree. -/
theorem collapsedCount_rename {n : Nat} (σ : DRen n) (r : Regime)
    (hn : r.data = n) (p q : Nat × Nat → Bool)
    (hp : ∀ x : Nat × Nat, p x = true ↔ collapsed r x.1 x.2)
    (hq : ∀ x : Nat × Nat, q x = true ↔ collapsed (renameRegime σ.f r) x.1 x.2)
    (L : List (Nat × Nat)) :
    (L.map (fun x => (σ.f x.1, σ.f x.2))).countP q = L.countP p := by
  induction L with
  | nil => rfl
  | cons a as ih =>
    have hstep : q (σ.f a.1, σ.f a.2) = p a := by
      apply Bool.eq_iff_iff.mpr
      rw [hq, hp]
      exact collapsed_rename σ r hn a.1 a.2
    simp only [List.map_cons, List.countP_cons, ih, hstep]

/-- Renaming preserves the instance conjunct of `Regime.wf`.  Recorded
so that a reader is not left wondering whether well-formedness survives
the action.  The requirement conjunct is NOT claimed: a bijection need
not preserve the `q.1 < q.2` ordering, and collapse never reads it. -/
theorem rename_insts_wf {n : Nat} (σ : DRen n) (r : Regime) (hn : r.data = n)
    (h : ∀ p ∈ r.insts, p.1 < r.forms.length ∧
          p.2.length = r.forms.getD p.1 0 ∧ ∀ a ∈ p.2, a < r.data) :
    ∀ p ∈ (renameRegime σ.f r).insts,
      p.1 < r.forms.length ∧
      p.2.length = r.forms.getD p.1 0 ∧
      ∀ a ∈ p.2, a < r.data := by
  subst hn
  intro p hp
  obtain ⟨q, hq, hqp⟩ := List.mem_map.mp hp
  obtain ⟨e1, e2, e3⟩ := h q hq
  subst hqp
  refine ⟨e1, ?_, ?_⟩
  · show (q.2.map σ.f).length = r.forms.getD q.1 0
    rw [List.length_map]; exact e2
  · intro a ha
    obtain ⟨b, hb, hba⟩ := List.mem_map.mp ha
    exact hba ▸ σ.fbound b (e3 b hb)

/-! ## The hypothesis is load-bearing: a countermodel

`collapsed_rename` assumes a bijection.  A theorem whose hypothesis is
never needed proves less than it appears to, so the hypothesis is shown
here to be doing work: for a NON-injective map the transport statement
is outright false, not merely unproved. -/

/-- Two data, one unary form, one instance naming datum `0`.  Datum `0`
is derivable in the one-hole context and datum `1` is not. -/
def cmRegime : Regime := ⟨2, [1], [(0, [0])], [], []⟩

theorem cmRegime_wf : cmRegime.wf := by
  refine ⟨?_, ?_, ?_, ?_⟩ <;> simp [cmRegime]

/-- The one-hole context separates the two data. -/
theorem cm_separable : separable cmRegime 0 1 :=
  ⟨⟨0, [none]⟩, by decide, by decide⟩

/-- **The countermodel.**  Under the constant map `fun _ => 0` the two
data are sent to the same index, so the renamed regime collapses them
trivially, while the original does not collapse them at all.  The iff of
`collapsed_rename` therefore fails for this map, and injectivity is not
decoration. -/
theorem non_injective_does_not_transport :
    collapsed (renameRegime (fun _ => 0) cmRegime)
        ((fun _ => 0) 0) ((fun _ => 0) 1)
      ∧ ¬ collapsed cmRegime 0 1 :=
  ⟨fun _ _ => Iff.rfl, separable_not_collapsed cm_separable⟩

end Derivation
