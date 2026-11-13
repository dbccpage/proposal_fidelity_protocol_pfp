import Derivation.IsoCollapse
import Derivation.TransitionTransport
import Derivation.FormRenaming

/-!
# The relabelling action is an isomorphism, and canonical-key soundness

`code/derivation/iso.py` decides isomorphism, within its configured
permutation budget, by a **canonical key**: the minimum, over
color-class-preserving datum/form bijection pairs, of a total serialization of
the regime (`canonical`; the brute-force reference minimizes over all pairs).
Above the budget the API raises rather than deciding.  The two key computations
agree on the declared Challenge-3 representatives and the mixed-regime test
corpus -- finite test evidence, not a proved general agreement, and distinct
from the still-open general key-to-isomorphism bridge below.
`serialize(r, π, φ)` reads off the combined action of this development applied
under the bijection pair, then sorts `insts`, `rules`, and `reqs`
componentwise -- `mapReq` *is* `sortPair` of the mapped endpoints (proved
below), and arities move by `renameForms_arity`.  The action half of the key
machinery therefore rests on one fact: relabelling a regime by a bijection
pair yields a regime **isomorphic** to it, in the sense of the sealed
`Minimality.Iso`.  The sort half is scoped below.

This module proves that (`relabel_iso`), makes `Iso` an equivalence relation
on regimes with ordered requirement pairs -- as `Regime.wf` gives; reflexivity
is conditional on exactly that, via `isoRefl` -- by adding `Iso.trans`
(symmetry is `Iso.symm`), and derives the **soundness kernel**: two regimes
whose relabellings coincide *as regimes* are isomorphic (`iso_of_relabel_eq`).
That is the kernel of the direction that makes "dedup by canonical key" safe,
not yet that direction in full: equal keys give relabellings equal only up to
`serialize`'s componentwise sorts, and the list-reorder step from there to
`Iso` is not proved here -- it needs the same normalization hypotheses as the
converse below.

The converse (isomorphic ⇒ equal key, the non-redundancy half) is **not** here:
it needs a no-duplicate/normalization hypothesis, since `Minimality.Iso` is a
membership relation that also identifies e.g. `[p]` with `[p, p]`, which no
serialization equates.  That is the next unit.

`relabel_iso`'s `reqs_bwd` needs `r`'s requirements ordered (as `Regime.wf`
gives); everything else is unconditional in the bijection bounds.
`iso_of_relabel_eq` accordingly needs both regimes' requirements ordered
(`hr`, `hs`).

AuthorityEffect: None.  Parked module (not imported by `Derivation.lean`);
axioms within `{propext, Quot.sound}`, verified by hand, not by the root gate.
-/

namespace Derivation

/-! ## `sortPair` as min/max, and its interaction with a map -/

theorem sortPair_eq_minmax (x y : Nat) : sortPair (x, y) = (min x y, max x y) := by
  unfold sortPair
  by_cases h : x ≤ y
  · simp [h, Nat.min_eq_left h, Nat.max_eq_right h]
  · have h' : y ≤ x := Nat.le_of_not_le h
    simp [h, Nat.min_eq_right h', Nat.max_eq_left h']

theorem sortPair_comm (x y : Nat) : sortPair (x, y) = sortPair (y, x) := by
  rw [sortPair_eq_minmax, sortPair_eq_minmax, Nat.min_comm, Nat.max_comm]

/-- `mapReq` is `sortPair` of the mapped endpoints -- the bridge between the
transition action's requirement map and the isomorphism's `reqs` fields. -/
theorem mapReq_eq_sortPair (f : Nat → Nat) (q : Nat × Nat) :
    mapReq f q = sortPair (f q.1, f q.2) := by
  rw [sortPair_eq_minmax]; rfl

/-- Sorting the endpoints before mapping does not change the sorted image. -/
theorem sortPair_map_sortPair (f : Nat → Nat) (a b : Nat) :
    sortPair (f (sortPair (a, b)).1, f (sortPair (a, b)).2) = sortPair (f a, f b) := by
  rcases Nat.le_total a b with h | h
  · rw [sortPair_eq_minmax a b, Nat.min_eq_left h, Nat.max_eq_right h]
  · rw [sortPair_eq_minmax a b, Nat.min_eq_right h, Nat.max_eq_left h, sortPair_comm]

/-- An ordered pair is fixed by `sortPair`. -/
theorem sortPair_of_le {x y : Nat} (h : x ≤ y) : sortPair (x, y) = (x, y) := by
  rw [sortPair_eq_minmax, Nat.min_eq_left h, Nat.max_eq_right h]

namespace Iso

variable {r s t : Regime}

/-! ## `Iso` is transitive -/

/-- Compose two isomorphisms (unconditional).  With `isoRefl` -- whose
ordered-`reqs` hypothesis is genuinely needed: a regime with an unordered
requirement pair is not `Iso` to itself -- and `Iso.symm`, `Iso` is an
equivalence relation on regimes with ordered requirement pairs. -/
def trans (h : Iso r s) (k : Iso s t) : Iso r t where
  dmap := k.dmap ∘ h.dmap
  dinv := h.dinv ∘ k.dinv
  fmap := k.fmap ∘ h.fmap
  finv := h.finv ∘ k.finv
  dmap_lt := fun d hd => k.dmap_lt _ (List.mem_range.mpr (h.dmap_lt d hd))
  dinv_lt := fun d hd => h.dinv_lt _ (List.mem_range.mpr (k.dinv_lt d hd))
  dinv_dmap := fun d hd => by
    show h.dinv (k.dinv (k.dmap (h.dmap d))) = d
    rw [k.dinv_dmap (h.dmap d) (List.mem_range.mpr (h.dmap_lt d hd)), h.dinv_dmap d hd]
  dmap_dinv := fun d hd => by
    show k.dmap (h.dmap (h.dinv (k.dinv d))) = d
    rw [h.dmap_dinv (k.dinv d) (List.mem_range.mpr (k.dinv_lt d hd)), k.dmap_dinv d hd]
  fmap_lt := fun f hf => k.fmap_lt _ (List.mem_range.mpr (h.fmap_lt f hf))
  finv_lt := fun f hf => h.finv_lt _ (List.mem_range.mpr (k.finv_lt f hf))
  finv_fmap := fun f hf => by
    show h.finv (k.finv (k.fmap (h.fmap f))) = f
    rw [k.finv_fmap (h.fmap f) (List.mem_range.mpr (h.fmap_lt f hf)), h.finv_fmap f hf]
  fmap_finv := fun f hf => by
    show k.fmap (h.fmap (h.finv (k.finv f))) = f
    rw [h.fmap_finv (k.finv f) (List.mem_range.mpr (k.finv_lt f hf)), k.fmap_finv f hf]
  arity := fun f hf => by
    show t.forms.getD (k.fmap (h.fmap f)) 0 = r.forms.getD f 0
    rw [k.arity (h.fmap f) (List.mem_range.mpr (h.fmap_lt f hf)), h.arity f hf]
  insts_fwd := fun p hp => by
    have h2 := k.insts_fwd _ (h.insts_fwd p hp)
    rwa [List.map_map] at h2
  insts_bwd := fun p hp => by
    have h2 := h.insts_bwd _ (k.insts_bwd p hp)
    rwa [List.map_map] at h2
  rules_fwd := fun f hf => k.rules_fwd _ (h.rules_fwd f hf)
  rules_bwd := fun f hf => h.rules_bwd _ (k.rules_bwd f hf)
  reqs_fwd := fun q hq => by
    have h2 := k.reqs_fwd _ (h.reqs_fwd q hq)
    rwa [sortPair_map_sortPair] at h2
  reqs_bwd := fun q hq => by
    have h2 := h.reqs_bwd _ (k.reqs_bwd q hq)
    rwa [sortPair_map_sortPair] at h2

end Iso

/-! ## The relabelling action -/

/-- Relabel a regime by a datum bijection `π` and a form bijection `φ`: the
combined transition-and-form action.  This is the regime `serialize` reads
off before its componentwise sorts. -/
def relabel (r : Regime) (π : DRen r.data) (φ : DRen r.forms.length) : Regime :=
  renameForms φ.f φ.g (renameRegimeR π.f r)

@[simp] theorem relabel_data (r : Regime) (π : DRen r.data) (φ : DRen r.forms.length) :
    (relabel r π φ).data = r.data := rfl

@[simp] theorem relabel_forms (r : Regime) (π : DRen r.data) (φ : DRen r.forms.length) :
    (relabel r π φ).forms = permForms φ.g r.forms := rfl

@[simp] theorem relabel_insts (r : Regime) (π : DRen r.data) (φ : DRen r.forms.length) :
    (relabel r π φ).insts = (r.insts.map (mapInst π.f)).map (mapInstForm φ.f) := rfl

@[simp] theorem relabel_rules (r : Regime) (π : DRen r.data) (φ : DRen r.forms.length) :
    (relabel r π φ).rules = r.rules.map φ.f := rfl

@[simp] theorem relabel_reqs (r : Regime) (π : DRen r.data) (φ : DRen r.forms.length) :
    (relabel r π φ).reqs = r.reqs.map (mapReq π.f) := rfl

/-- **Relabelling is an isomorphism.**  A regime and its relabelling under a
bijection pair are `Minimality.Iso`, with the pair as the witnessing maps.
Needs `r`'s requirements ordered (from `Regime.wf`) for the backward
requirement condition. -/
def relabel_iso (r : Regime) (π : DRen r.data) (φ : DRen r.forms.length)
    (hord : ∀ q ∈ r.reqs, q.1 ≤ q.2) : Iso r (relabel r π φ) where
  dmap := π.f
  dinv := π.g
  fmap := φ.f
  finv := φ.g
  dmap_lt := fun d hd => by
    have : π.f d < r.data := π.fbound d (List.mem_range.mp hd)
    simpa using this
  dinv_lt := fun d hd => by
    have hd' : d < r.data := by simpa using hd
    exact π.gbound d hd'
  dinv_dmap := fun d _ => π.fg d
  dmap_dinv := fun d _ => π.gf d
  fmap_lt := fun f hf => by
    have : φ.f f < r.forms.length := φ.fbound f (List.mem_range.mp hf)
    simpa using this
  finv_lt := fun f hf => by
    have hf' : f < r.forms.length := by simpa using hf
    exact φ.gbound f hf'
  finv_fmap := fun f _ => φ.fg f
  fmap_finv := fun f _ => φ.gf f
  arity := fun f hf =>
    renameForms_arity φ.f φ.g (renameRegimeR π.f r)
      (φ.fbound f (List.mem_range.mp hf)) (φ.fg f)
  insts_fwd := fun p hp => by
    show (φ.f p.1, p.2.map π.f) ∈ (r.insts.map (mapInst π.f)).map (mapInstForm φ.f)
    exact List.mem_map.mpr ⟨mapInst π.f p, List.mem_map.mpr ⟨p, hp, rfl⟩, rfl⟩
  insts_bwd := fun p hp => by
    obtain ⟨p1, hp1, hp1e⟩ := List.mem_map.mp hp
    obtain ⟨p0, hp0, hp0e⟩ := List.mem_map.mp hp1
    subst hp1e; subst hp0e
    show (φ.g (mapInstForm φ.f (mapInst π.f p0)).1, (mapInstForm φ.f (mapInst π.f p0)).2.map π.g)
        ∈ r.insts
    have e : (φ.g (mapInstForm φ.f (mapInst π.f p0)).1,
        (mapInstForm φ.f (mapInst π.f p0)).2.map π.g) = p0 := by
      show (φ.g (φ.f p0.1), (p0.2.map π.f).map π.g) = p0
      rw [φ.fg, List.map_map]
      have : (p0.2.map (π.g ∘ π.f)) = p0.2 :=
        map_eq_self_of_mem (fun a _ => π.fg a)
      rw [this]
    rw [e]; exact hp0
  rules_fwd := fun f hf => List.mem_map.mpr ⟨f, hf, rfl⟩
  rules_bwd := fun f hf => by
    obtain ⟨f0, hf0, hf0e⟩ := List.mem_map.mp hf
    show φ.g f ∈ r.rules
    rw [← hf0e, φ.fg]; exact hf0
  reqs_fwd := fun q hq => by
    show sortPair (π.f q.1, π.f q.2) ∈ r.reqs.map (mapReq π.f)
    exact List.mem_map.mpr ⟨q, hq, mapReq_eq_sortPair π.f q⟩
  reqs_bwd := fun q hq => by
    obtain ⟨q0, hq0, hq0e⟩ := List.mem_map.mp hq
    show sortPair (π.g q.1, π.g q.2) ∈ r.reqs
    rw [← hq0e, mapReq_eq_sortPair, sortPair_map_sortPair, π.fg, π.fg,
        sortPair_of_le (hord q0 hq0)]
    exact hq0

/-! ## Soundness kernel -/

/-- **Soundness kernel.**  If two regimes relabel to the same regime -- with
both regimes' requirements ordered (`hr`, `hs`) -- they are isomorphic.  This
is the kernel of "equal canonical key ⇒ isomorphic", not the whole of it: the
key is the minimum of `serialize`, which sorts `insts`/`rules`/`reqs` after
the action, so equal keys yield relabellings that coincide only up to those
sorts, and as lists they may differ -- then `heq` is not available.  Closing
that list-reorder gap needs the same normalization hypotheses as the converse;
it belongs to the next unit. -/
def iso_of_relabel_eq {r s : Regime}
    (πr : DRen r.data) (φr : DRen r.forms.length)
    (πs : DRen s.data) (φs : DRen s.forms.length)
    (hr : ∀ q ∈ r.reqs, q.1 ≤ q.2) (hs : ∀ q ∈ s.reqs, q.1 ≤ q.2)
    (heq : relabel r πr φr = relabel s πs φs) : Iso r s :=
  (relabel_iso r πr φr hr).trans ((heq ▸ relabel_iso s πs φs hs).symm)

end Derivation
