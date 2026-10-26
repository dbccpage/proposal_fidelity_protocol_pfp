import Derivation.FormRenaming

/-!
# Observational transport under a form renaming, and the combined data/form action

`CountTransport.lean` transports observational collapse under a **datum**
renaming (`renameRegime`, R6); `TransitionTransport.lean` lifts that to the
transition relation, both over datum bijections *with the identity on
forms* (its own scope note).  This module supplies the missing half: the
same observational transport under a **form** renaming (`renameForms`,
`FormRenaming.lean`), and then the two composed into a combined data+form
action.  This is an *action* -- an equality of renamed regimes -- and is
**not** the canonical regime isomorphism; see the scope note below.

The one new ingredient over the datum side is arity: a form renaming
permutes the form-arity list, so `wfCtx`'s arity lookup
`r.forms.getD c.form 0` must be shown to survive the permutation.  That is
exactly `permForms_getD` / `renameForms_arity`, already proved; everything
else mirrors the datum-side idioms, and is in fact simpler, because a form
renaming leaves a context's slots (which name data, not forms) untouched.

## What is proved here, and what is not

Proved: `collapsed` and its readers (`wfCtx`, `derivable`) transport under a
form renaming, and the combined data+form action transports `collapsed`
(datum pair moved by the datum map only, since a form renaming does not
touch datum indices).

Not yet: connecting this transport to the canonical isomorphism relation
`Iso` (already defined in `Minimality.lean`, mirroring `iso.py`).  That
relation states membership conditions between two regimes, not an action
equation, so collapse across it is a separate proof and is the next unit --
`collapsed_congr` below (collapse ignores `reqs`) is one of its pieces.
The action here and `Iso` are not the same relation, so the connection must
be proved, not assumed:
* `Iso` does not imply the action: `Iso` identifies regimes differing only
  by duplicate instances (`[p]` vs `[p, p]` -- equal as sets, unequal as
  lists), which no rename action can equate.
* the action is not an `Iso` witnessed by *its own* maps: the collapse-level
  action here uses `renameRegime`, which leaves `reqs` untouched, so with
  `dmap = σ.f` the `reqs_fwd` conjunct fails -- a `reqs` `[(0, 1)]` under
  `σ.f` sending `0, 1` to `1, 2` stays `[(0, 1)]`, but `reqs_fwd` for that
  map would need `(1, 2)`.  Since `Iso` chooses its maps existentially,
  ruling out *every* choice needs a forcing regime (distinct arities and
  instances pinning the bijection); that stronger claim is not asserted here.
Also not yet: `separable`, `respond`, `validResponse`, and `TransStep` under
the form (hence combined) action.  This does **not** compose "exactly as
collapse": collapse uses the `reqs`-free `renameRegime`, while the datum-side
`transStep` transport uses the requirement-carrying `renameRegimeR`
(`validResponse` reads `reqs`).  So the form lift needs additional work -- a
form action on `reqs` and its transport, and a bridge to `renameRegimeR` --
before it can compose with `transStep_rename_fwd` / `transStep_image_total`.

AuthorityEffect: None.  Parked module (not imported by `Derivation.lean`);
its axioms are within `{propext, Quot.sound}`, verified by hand, not by the
root axiom gate.
-/

namespace Derivation

/-- The record projections of `renameForms`, as rewrite rules. -/
@[simp] theorem renameForms_forms (φ g : Nat → Nat) (r : Regime) :
    (renameForms φ g r).forms = permForms g r.forms := rfl

@[simp] theorem renameForms_insts (φ g : Nat → Nat) (r : Regime) :
    (renameForms φ g r).insts = r.insts.map (mapInstForm φ) := rfl

@[simp] theorem renameForms_rules (φ g : Nat → Nat) (r : Regime) :
    (renameForms φ g r).rules = r.rules.map φ := rfl

/-! ## The form action on a context -/

/-- Relabel the form index of a context; its slots name data or holes, not
forms, so they are untouched -- the mirror of `mapCtx` for forms, and
simpler, since there is nothing to map inside the slots. -/
def mapCtxForm (φ : Nat → Nat) (c : Ctx) : Ctx := ⟨φ c.form, c.slots⟩

/-- Plugging commutes with the form action, definitionally: the form index
is relabelled and the slots (hence the plugged tuple) are identical. -/
theorem plug_mapCtxForm (φ : Nat → Nat) (c : Ctx) (d : Nat) :
    plug (mapCtxForm φ c) d = mapInstForm φ (plug c d) := rfl

/-- The context form action inverts, on the form index. -/
theorem mapCtxForm_f_g {n : Nat} (σ : DRen n) (c : Ctx) :
    mapCtxForm σ.f (mapCtxForm σ.g c) = c := by
  cases c with
  | mk form slots => simp only [mapCtxForm, σ.gf]

/-! ## Injectivity of the instance form action -/

theorem mapInstForm_inj {φ : Nat → Nat} (hφ : ∀ {x y}, φ x = φ y → x = y)
    {i j : Inst} (h : mapInstForm φ i = mapInstForm φ j) : i = j := by
  obtain ⟨a, l⟩ := i
  obtain ⟨b, m⟩ := j
  simp only [mapInstForm, Prod.mk.injEq] at h
  have h1 : a = b := hφ h.1
  have h2 : l = m := h.2
  subst h1; subst h2; rfl

/-! ## Derivability transports -/

theorem derivable_renameForms {φ : Nat → Nat} (hφ : ∀ {x y}, φ x = φ y → x = y)
    (g : Nat → Nat) (r : Regime) (i : Inst) :
    derivable (renameForms φ g r) (mapInstForm φ i) ↔ derivable r i := by
  simp only [derivable, renameForms_insts, renameForms_rules]
  constructor
  · rintro (hm | hr)
    · obtain ⟨j, hj, hij⟩ := List.mem_map.mp hm
      exact Or.inl (mapInstForm_inj hφ hij ▸ hj)
    · obtain ⟨f, hf, hfe⟩ := List.mem_map.mp hr
      exact Or.inr (hφ hfe ▸ hf)
  · rintro (hm | hr)
    · exact Or.inl (List.mem_map.mpr ⟨i, hm, rfl⟩)
    · exact Or.inr (List.mem_map.mpr ⟨i.1, hr, rfl⟩)

/-! ## Well-formed contexts transport (the arity step is the crux) -/

theorem wfCtx_renameForms (r : Regime) (σ : DRen r.forms.length) (c : Ctx) :
    wfCtx (renameForms σ.f σ.g r) (mapCtxForm σ.f c) ↔ wfCtx r c := by
  simp only [wfCtx, mapCtxForm, renameForms_forms, renameForms_data, permForms_length]
  constructor
  · rintro ⟨h1, h2, h3, h4⟩
    have hcf : c.form < r.forms.length := by
      have := σ.gbound _ h1
      rwa [σ.fg] at this
    refine ⟨hcf, ?_, h3, h4⟩
    rw [h2, permForms_getD σ.g r.forms (σ.fbound c.form hcf), σ.fg]
  · rintro ⟨h1, h2, h3, h4⟩
    refine ⟨σ.fbound c.form h1, ?_, h3, h4⟩
    rw [h2, permForms_getD σ.g r.forms (σ.fbound c.form h1), σ.fg]

/-! ## Collapse transports under a form renaming (datum pair unchanged) -/

/-- Observational collapse is invariant under a form renaming.  The datum
pair `d, d'` is untouched: a form renaming relabels judgment forms, not
data. -/
theorem collapsed_renameForms (r : Regime) (σ : DRen r.forms.length)
    (d d' : Nat) :
    collapsed (renameForms σ.f σ.g r) d d' ↔ collapsed r d d' := by
  constructor
  · intro h c hc
    have hwf := (wfCtx_renameForms r σ c).mpr hc
    have hh := h (mapCtxForm σ.f c) hwf
    rw [plug_mapCtxForm, plug_mapCtxForm] at hh
    rwa [derivable_renameForms σ.f_inj, derivable_renameForms σ.f_inj] at hh
  · intro h c' hc'
    have hc : mapCtxForm σ.f (mapCtxForm σ.g c') = c' := mapCtxForm_f_g σ c'
    have hwf : wfCtx r (mapCtxForm σ.g c') := by
      rw [← wfCtx_renameForms r σ (mapCtxForm σ.g c'), hc]; exact hc'
    have hh := h (mapCtxForm σ.g c') hwf
    have e1 : plug c' d = mapInstForm σ.f (plug (mapCtxForm σ.g c') d) := by
      rw [← plug_mapCtxForm, hc]
    have e2 : plug c' d' = mapInstForm σ.f (plug (mapCtxForm σ.g c') d') := by
      rw [← plug_mapCtxForm, hc]
    rw [e1, e2, derivable_renameForms σ.f_inj, derivable_renameForms σ.f_inj]
    exact hh

/-! ## Collapse depends only on data, forms, insts, rules -/

/-- Two regimes agreeing on every field `collapse` reads (all but `reqs`)
collapse the same pairs.  A future bridge, not yet called in this module:
connecting collapse transport to `Iso` (which renames `reqs`) will need to
pass between a `reqs`-carrying action and its `reqs`-free form, and this says
collapse cannot tell them apart. -/
theorem collapsed_congr {r s : Regime}
    (hf : r.forms = s.forms) (hd : r.data = s.data)
    (hi : r.insts = s.insts) (hru : r.rules = s.rules)
    (d d' : Nat) : collapsed r d d' ↔ collapsed s d d' := by
  have hwf : ∀ c, wfCtx r c ↔ wfCtx s c := fun c => by
    unfold wfCtx; rw [hf, hd]
  have hder : ∀ i, derivable r i ↔ derivable s i := fun i => by
    unfold derivable; rw [hi, hru]
  unfold collapsed
  constructor
  · intro h c hc
    have h2 := h c ((hwf c).mpr hc)
    exact ((hder (plug c d)).symm.trans h2).trans (hder (plug c d'))
  · intro h c hc
    have h2 := h c ((hwf c).mp hc)
    exact ((hder (plug c d)).trans h2).trans (hder (plug c d')).symm

/-! ## The combined data+form transport of collapse -/

/-- **Collapse transports under the combined action.**  Relabel datum
indices by `σ.f` and permute/relabel forms by `τ`; observational collapse
survives, with the datum pair carried by `σ.f` only (forms do not move
data).  Datum half: `collapsed_rename`; form half: `collapsed_renameForms`;
they compose because the two actions touch disjoint coordinates. -/
theorem collapsed_renameDataForm {n : Nat} (σ : DRen n) (r : Regime)
    (hn : r.data = n) (τ : DRen r.forms.length) (d d' : Nat) :
    collapsed (renameForms τ.f τ.g (renameRegime σ.f r)) (σ.f d) (σ.f d')
      ↔ collapsed r d d' := by
  rw [collapsed_renameForms (renameRegime σ.f r) τ (σ.f d) (σ.f d')]
  exact collapsed_rename σ r hn d d'

end Derivation
