import Derivation.Minimality

/-!
# Observational collapse transports across the canonical isomorphism

`FormTransport.lean` transported `collapsed` under an explicit form-and-datum
*action*.  This module does the harder, more useful thing: it transports
`collapsed` across the canonical isomorphism relation `Iso` of
`Minimality.lean` (the one that mirrors `iso.py`), which is stated by
*membership* conditions (`insts_fwd`/`insts_bwd`, `rules_*`, `arity`, and the
range-bounded bijections), not by an action equation.  The two notions are
distinct -- see the scope note in `FormTransport.lean` -- so this cannot be
routed through that action and is proved directly from `Iso`'s fields.

The proof mirrors the datum-side `collapsed_rename` idiom, but every inversion
step now carries a range bound, because `Iso`'s maps invert only on the
admitted ranges (`dinv_dmap` holds for `d ∈ range r.data`, not globally).
`Iso.symm` (built here) turns the two directions of the transport into one:
prove collapse maps forward, and the backward direction is the forward
direction of the inverse isomorphism.

`reqs` never enter `collapsed` (it reads `wfCtx` and `derivable` only), so the
requirement fields of `Iso` are not used here -- the same reason the datum
transport left `reqs` alone.

AuthorityEffect: None.  Parked module (not imported by `Derivation.lean`);
axioms within `{propext, Quot.sound}`, verified by hand, not by the root gate.
-/

namespace Derivation

/-- A list is fixed by a map that fixes each of its members. -/
theorem map_eq_self_of_mem {l : List Nat} {f : Nat → Nat}
    (hf : ∀ a ∈ l, f a = a) : l.map f = l := by
  induction l with
  | nil => rfl
  | cons a as ih =>
    simp only [List.map_cons]
    rw [hf a (List.mem_cons.mpr (Or.inl rfl)),
        ih (fun x hx => hf x (List.mem_cons.mpr (Or.inr hx)))]

/-- Every datum plugged into a well-formed context is admitted, provided the
plugged datum is. -/
theorem plug_args_lt {r : Regime} {c : Ctx} (hc : wfCtx r c)
    {d : Nat} (hd : d < r.data) : ∀ a ∈ (plug c d).2, a < r.data := by
  intro a ha
  obtain ⟨sl, hsl, hsle⟩ := List.mem_map.mp ha
  have h4 := hc.2.2.2 sl hsl
  cases sl with
  | none => exact hsle ▸ hd
  | some x => exact hsle ▸ h4

namespace Iso

variable {r s : Regime}

/-- The inverse isomorphism: swap the two half-bijections and the forward and
backward membership conditions.  Only `arity` needs a computation. -/
def symm (h : Iso r s) : Iso s r where
  dmap := h.dinv
  dinv := h.dmap
  fmap := h.finv
  finv := h.fmap
  dmap_lt := h.dinv_lt
  dinv_lt := h.dmap_lt
  dinv_dmap := h.dmap_dinv
  dmap_dinv := h.dinv_dmap
  fmap_lt := h.finv_lt
  finv_lt := h.fmap_lt
  finv_fmap := h.fmap_finv
  fmap_finv := h.finv_fmap
  arity := by
    intro f hf
    have hfr : h.finv f < r.forms.length := h.finv_lt f hf
    have hkey := h.arity (h.finv f) (List.mem_range.mpr hfr)
    rw [h.fmap_finv f hf] at hkey
    exact hkey.symm
  insts_fwd := h.insts_bwd
  insts_bwd := h.insts_fwd
  rules_fwd := h.rules_bwd
  rules_bwd := h.rules_fwd
  reqs_fwd := h.reqs_bwd
  reqs_bwd := h.reqs_fwd

@[simp] theorem symm_dmap (h : Iso r s) : h.symm.dmap = h.dinv := rfl

/-- The image of an instance under the isomorphism's maps. -/
def imap (h : Iso r s) (i : Inst) : Inst := (h.fmap i.1, i.2.map h.dmap)

/-- The image of a context: form index by `fmap`, filled slots by `dmap`. -/
def cmap (h : Iso r s) (c : Ctx) : Ctx :=
  ⟨h.fmap c.form, c.slots.map (Option.map h.dmap)⟩

/-- Plugging commutes with the context/instance image. -/
theorem plug_cmap (h : Iso r s) (c : Ctx) (d : Nat) :
    plug (h.cmap c) (h.dmap d) = h.imap (plug c d) := by
  have hfun : (fun sl : Option Nat => Option.getD (Option.map h.dmap sl) (h.dmap d))
            = (fun sl : Option Nat => h.dmap (Option.getD sl d)) := by
    funext sl; cases sl <;> rfl
  simp only [plug, Iso.cmap, Iso.imap, List.map_map]
  congr 1
  show List.map ((fun sl => Option.getD sl (h.dmap d)) ∘ Option.map h.dmap) c.slots
     = List.map (h.dmap ∘ (fun sl => Option.getD sl d)) c.slots
  exact congrArg (fun g => List.map g c.slots) hfun

/-- Well-formed contexts map forward under the isomorphism. -/
theorem wfCtx_cmap (h : Iso r s) {c : Ctx} (hc : wfCtx r c) :
    wfCtx s (h.cmap c) := by
  obtain ⟨h1, h2, h3, h4⟩ := hc
  refine ⟨?_, ?_, ?_, ?_⟩
  · exact h.fmap_lt c.form (List.mem_range.mpr h1)
  · show (c.slots.map (Option.map h.dmap)).length = s.forms.getD (h.fmap c.form) 0
    rw [List.length_map, h2, h.arity c.form (List.mem_range.mpr h1)]
  · show none ∈ c.slots.map (Option.map h.dmap)
    exact List.mem_map.mpr ⟨none, h3, rfl⟩
  · intro sl hsl
    obtain ⟨t, ht, hte⟩ := List.mem_map.mp hsl
    have h4t := h4 t ht
    cases t with
    | none => exact hte ▸ trivial
    | some x => exact hte ▸ h.dmap_lt x (List.mem_range.mpr h4t)

/-- Derivability transports across the isomorphism, on an instance whose form
index and data are admitted. -/
theorem derivable_imap (h : Iso r s) {i : Inst}
    (hf : i.1 < r.forms.length) (ha : ∀ a ∈ i.2, a < r.data) :
    derivable s (h.imap i) ↔ derivable r i := by
  constructor
  · intro hd
    cases hd with
    | inl hm =>
      have hb := h.insts_bwd (h.imap i) hm
      have e1 : h.finv (h.imap i).1 = i.1 := h.finv_fmap i.1 (List.mem_range.mpr hf)
      have e2 : (h.imap i).2.map h.dinv = i.2 := by
        show (i.2.map h.dmap).map h.dinv = i.2
        rw [List.map_map]
        exact map_eq_self_of_mem
          (fun a ha' => h.dinv_dmap a (List.mem_range.mpr (ha a ha')))
      rw [e1, e2] at hb
      exact Or.inl hb
    | inr hr =>
      have hb := h.rules_bwd (h.fmap i.1) hr
      rw [h.finv_fmap i.1 (List.mem_range.mpr hf)] at hb
      exact Or.inr hb
  · intro hd
    cases hd with
    | inl hm => exact Or.inl (h.insts_fwd i hm)
    | inr hr => exact Or.inr (h.rules_fwd i.1 hr)

/-- **Collapse maps forward** across the isomorphism, datum pair by `dmap`. -/
theorem collapsed_fwd (h : Iso r s) {d d' : Nat}
    (hd : d < r.data) (hd' : d' < r.data)
    (H : collapsed s (h.dmap d) (h.dmap d')) : collapsed r d d' := by
  intro c hc
  have hh := H (h.cmap c) (h.wfCtx_cmap hc)
  rw [h.plug_cmap, h.plug_cmap,
      h.derivable_imap (i := plug c d) hc.1 (plug_args_lt hc hd),
      h.derivable_imap (i := plug c d') hc.1 (plug_args_lt hc hd')] at hh
  exact hh

/-- **Collapse transports across a regime isomorphism.**  The datum pair is
carried by the isomorphism's datum bijection; forms, rules, and instances are
handled by its membership fields, and requirements never enter collapse. -/
theorem collapsed_transport (h : Iso r s) {d d' : Nat}
    (hd : d < r.data) (hd' : d' < r.data) :
    collapsed s (h.dmap d) (h.dmap d') ↔ collapsed r d d' := by
  constructor
  · exact h.collapsed_fwd hd hd'
  · intro Hr
    have key := h.symm.collapsed_fwd (d := h.dmap d) (d' := h.dmap d')
      (h.dmap_lt d (List.mem_range.mpr hd)) (h.dmap_lt d' (List.mem_range.mpr hd'))
    rw [symm_dmap, h.dinv_dmap d (List.mem_range.mpr hd),
        h.dinv_dmap d' (List.mem_range.mpr hd')] at key
    exact key Hr

end Iso
end Derivation
