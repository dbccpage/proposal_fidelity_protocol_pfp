import Derivation.CountTransport

/-!
# Transition-congruence transport under a datum renaming (R7)

Residual R7 in `paper.md` section 12 is kind (a): the mathematics is
certified exhaustively in Python
(`test_orbit_policy_transition_congruence_exhaustive`) and the Lean is
absent.  This module supplies the Lean for the relation-level content.

## What is transported, stated before the proofs

One engine round at a challenged pair `(i, j)` is: impose the
requirement, then apply a response delta — the exact event sequence the
implementation replays for each child.  Unlike observational collapse
(R6), this transition READS the requirement store: `validResponse`
quantifies over `r.reqs`, and the imposition step inserts into it.  So
the collapse-only action `renameRegime`, which deliberately leaves
`reqs` alone, is extended — not replaced — by `renameRegimeR`, which
also carries `reqs` along the renaming, renormalized to ordered pairs.

A response delta may introduce fresh data and then mention them, so the
renaming must act on indices the base regime does not yet have.  The
padding `padF` extends a bijection below `n` by the identity at and
above `n`; the fresh block is fixed, matching the implementation, where
fresh data receive the next indices in admission order on both sides of
the renaming.

## What is proved, and what is not

The congruence is a property of the transition RELATION: every
collapsed pair with every valid response, no selection applied.  That
relation-level fact is what makes a quotiented transition well defined
on isomorphism classes.  No selection function is claimed congruent,
and the index-least selection provably is not: on the regression regime
below, both the regime and its renaming have `(0, 1)` as index-least
collapsed pair, yet the renaming carries `(0, 1)` to `(2, 3)`.  The
further fact that the resulting children are non-isomorphic is
certified computationally and is not re-proved here.

Nothing here builds canonical keys or automorphism orbits; minima and
counts are phrased over caller-supplied candidate lists and deciders,
exactly as `collapsedCount_rename` does for R6: Python decides, Lean
states what the decision means.  The scope is datum bijections with
the identity on forms — the space the exhaustive test walks.
-/

namespace Derivation

/-! ## 1. Padding: acting across fresh admissions -/

/-- Extend a map below `n` by the identity at and above `n`. -/
def padF (n : Nat) (f : Nat → Nat) : Nat → Nat :=
  fun x => if x < n then f x else x

theorem padF_lt {n : Nat} (f : Nat → Nat) {x : Nat} (h : x < n) :
    padF n f x = f x := by
  simp [padF, h]

theorem padF_ge {n : Nat} (f : Nat → Nat) {x : Nat} (h : ¬ x < n) :
    padF n f x = x := by
  simp [padF, h]

/-- Two-sided inverse, padded. -/
theorem padF_fg {n : Nat} (σ : DRen n) :
    ∀ x, padF n σ.g (padF n σ.f x) = x := by
  intro x
  by_cases h : x < n
  · rw [padF_lt _ h, padF_lt _ (σ.fbound x h), σ.fg]
  · rw [padF_ge _ h, padF_ge _ h]

theorem padF_gf {n : Nat} (σ : DRen n) :
    ∀ x, padF n σ.f (padF n σ.g x) = x := by
  intro x
  by_cases h : x < n
  · rw [padF_lt _ h, padF_lt _ (σ.gbound x h), σ.gf]
  · rw [padF_ge _ h, padF_ge _ h]

theorem padF_inj {n : Nat} (σ : DRen n) :
    ∀ {x y}, padF n σ.f x = padF n σ.f y → x = y := by
  intro x y h
  have := congrArg (padF n σ.g) h
  rwa [padF_fg, padF_fg] at this

/-- Bounded at every level `n ≤ m`. -/
theorem padF_bound {n m : Nat} (σ : DRen n) (hm : n ≤ m) :
    ∀ x, x < m → padF n σ.f x < m := by
  intro x hx
  by_cases h : x < n
  · rw [padF_lt _ h]
    exact Nat.lt_of_lt_of_le (σ.fbound x h) hm
  · rwa [padF_ge _ h]

/-- Package the padding as a `DRen m` for any `n ≤ m`, so the
transports of `CountTransport` can be invoked at a CHILD regime,
whose datum count has grown. -/
def DRen.pad {n : Nat} (σ : DRen n) (m : Nat) (hm : n ≤ m) : DRen m where
  f := padF n σ.f
  g := padF n σ.g
  fg := padF_fg σ
  gf := padF_gf σ
  fbound := padF_bound σ hm
  gbound := padF_bound σ.inv hm

/-! ## 2. The full action: requirements included -/

/-- Rename an ordered requirement pair, renormalized to ordered form:
a bijection need not preserve the `q.1 < q.2` orientation. -/
def mapReq (f : Nat → Nat) (q : Nat × Nat) : Nat × Nat :=
  (min (f q.1) (f q.2), max (f q.1) (f q.2))

/-- The transition action.  `insts` via the existing collapse action
(`renameRegime`, reused, never redefined); `reqs` carried along.  The
extension is forced: `validResponse` quantifies over `r.reqs` and the
imposition step inserts into it, so the transition — unlike collapse —
reads the field `renameRegime` leaves alone. -/
def renameRegimeR (f : Nat → Nat) (r : Regime) : Regime :=
  { renameRegime f r with reqs := r.reqs.map (mapReq f) }

/-- The image is one of the two orders of the image pair. -/
theorem mapReq_cases (f : Nat → Nat) (p : Nat × Nat) :
    mapReq f p = (f p.1, f p.2) ∨ mapReq f p = (f p.2, f p.1) := by
  rcases Nat.le_total (f p.1) (f p.2) with h | h
  · exact Or.inl (by simp [mapReq, Nat.min_eq_left h, Nat.max_eq_right h])
  · exact Or.inr (by simp [mapReq, Nat.min_eq_right h, Nat.max_eq_left h])

/-- Ordered pairs stay ordered: an injective map separates `i < j`. -/
theorem mapReq_ordered {f : Nat → Nat}
    (hf : ∀ {x y}, f x = f y → x = y) {i j : Nat} (hij : i < j) :
    (mapReq f (i, j)).1 < (mapReq f (i, j)).2 := by
  have hne : f i ≠ f j := fun e => Nat.ne_of_lt hij (hf e)
  rcases Nat.le_total (f i) (f j) with h | h
  · simp only [mapReq, Nat.min_eq_left h, Nat.max_eq_right h]
    exact Nat.lt_of_le_of_ne h hne
  · simp only [mapReq, Nat.min_eq_right h, Nat.max_eq_left h]
    exact Nat.lt_of_le_of_ne h (fun e => hne e.symm)

/-- Injective on ordered pairs — the only pairs `Regime.wf` allows. -/
theorem mapReq_inj_ordered {f : Nat → Nat}
    (hf : ∀ {x y}, f x = f y → x = y) {p q : Nat × Nat}
    (hp : p.1 < p.2) (hq : q.1 < q.2)
    (h : mapReq f p = mapReq f q) : p = q := by
  obtain ⟨a, b⟩ := p
  obtain ⟨c, d⟩ := q
  simp only at hp hq
  rcases mapReq_cases f (a, b) with h1 | h1 <;>
    rcases mapReq_cases f (c, d) with h2 | h2 <;>
      rw [h1, h2] at h <;>
        simp only [Prod.mk.injEq] at h <;>
          obtain ⟨e1, e2⟩ := h
  · cases hf e1
    cases hf e2
    rfl
  · cases hf e1
    cases hf e2
    exact absurd (Nat.lt_trans hp hq) (Nat.lt_irrefl _)
  · cases hf e1
    cases hf e2
    exact absurd (Nat.lt_trans hp hq) (Nat.lt_irrefl _)
  · cases hf e1
    cases hf e2
    rfl

/-- Renormalization cancels through the inverse on ordered pairs. -/
theorem mapReq_g_f {n : Nat} (σ : DRen n) {i j : Nat} (hij : i < j) :
    mapReq σ.g (mapReq σ.f (i, j)) = (i, j) := by
  have key : ∀ a b : Nat, a < b →
      mapReq σ.g (min (σ.f a) (σ.f b), max (σ.f a) (σ.f b)) = (a, b) := by
    intro a b hab
    rcases Nat.le_total (σ.f a) (σ.f b) with h | h
    · rw [Nat.min_eq_left h, Nat.max_eq_right h]
      show (min (σ.g (σ.f a)) (σ.g (σ.f b)),
            max (σ.g (σ.f a)) (σ.g (σ.f b))) = (a, b)
      rw [σ.fg, σ.fg, Nat.min_eq_left (Nat.le_of_lt hab),
        Nat.max_eq_right (Nat.le_of_lt hab)]
    · rw [Nat.min_eq_right h, Nat.max_eq_left h]
      show (min (σ.g (σ.f b)) (σ.g (σ.f a)),
            max (σ.g (σ.f b)) (σ.g (σ.f a))) = (a, b)
      rw [σ.fg, σ.fg, Nat.min_eq_right (Nat.le_of_lt hab),
        Nat.max_eq_left (Nat.le_of_lt hab)]
  exact key i j hij

/-- The requirement conjunct of well-formedness survives the action —
the companion of `rename_insts_wf`, which covers `insts`. -/
theorem renameR_reqs_wf {n : Nat} (σ : DRen n) (r : Regime)
    (hn : r.data = n)
    (h : ∀ q ∈ r.reqs, q.1 < q.2 ∧ q.2 < r.data) :
    ∀ q ∈ (renameRegimeR σ.f r).reqs, q.1 < q.2 ∧ q.2 < r.data := by
  subst hn
  intro q hq
  obtain ⟨p, hp, hpq⟩ := List.mem_map.mp hq
  obtain ⟨h1, h2⟩ := h p hp
  subst hpq
  refine ⟨mapReq_ordered σ.f_inj h1, ?_⟩
  have ha : σ.f p.1 < r.data := σ.fbound _ (Nat.lt_trans h1 h2)
  have hb : σ.f p.2 < r.data := σ.fbound _ h2
  show max (σ.f p.1) (σ.f p.2) < r.data
  exact Nat.max_lt.mpr ⟨ha, hb⟩

/-! ## 3. Collapse and separability never read requirements -/

/-- `wfCtx`, `derivable`, `plug` touch `data`, `forms`, `insts`,
`rules` only, and structure-update projections compute, so this is
definitional. -/
theorem collapsed_reqs_irrel (r : Regime) (Q : List (Nat × Nat))
    (d d' : Nat) :
    collapsed { r with reqs := Q } d d' ↔ collapsed r d d' := Iff.rfl

theorem separable_reqs_irrel (r : Regime) (Q : List (Nat × Nat))
    (d d' : Nat) :
    separable { r with reqs := Q } d d' ↔ separable r d d' := Iff.rfl

/-- Collapse transports along the full action — the bridge to R6. -/
theorem collapsed_renameR {n : Nat} (σ : DRen n) (r : Regime)
    (hn : r.data = n) (d d' : Nat) :
    collapsed (renameRegimeR σ.f r) (σ.f d) (σ.f d')
      ↔ collapsed r d d' :=
  (collapsed_reqs_irrel (renameRegime σ.f r) _ _ _).trans
    (collapsed_rename σ r hn d d')

theorem collapsed_symm (r : Regime) (d d' : Nat) :
    collapsed r d d' ↔ collapsed r d' d :=
  ⟨fun h c hc => (h c hc).symm, fun h c hc => (h c hc).symm⟩

/-- Separability transports: the witness context is carried by
`mapCtx` — the technique of `collapsed_rename` applied to the
existential. -/
theorem separable_rename {n : Nat} (σ : DRen n) (r : Regime)
    (hn : r.data = n) (d d' : Nat) :
    separable (renameRegime σ.f r) (σ.f d) (σ.f d')
      ↔ separable r d d' := by
  constructor
  · rintro ⟨c', hc', hne⟩
    have hc : mapCtx σ.f (mapCtx σ.g c') = c' := mapCtx_f_g σ c'
    refine ⟨mapCtx σ.g c', ?_, ?_⟩
    · rw [← wfCtx_rename σ r hn (mapCtx σ.g c'), hc]
      exact hc'
    · intro hiff
      apply hne
      have e1 : plug c' (σ.f d) = mapInst σ.f (plug (mapCtx σ.g c') d) := by
        rw [← plug_mapCtx, hc]
      have e2 : plug c' (σ.f d') = mapInst σ.f (plug (mapCtx σ.g c') d') := by
        rw [← plug_mapCtx, hc]
      rw [e1, e2, derivable_rename σ.f_inj, derivable_rename σ.f_inj]
      exact hiff
  · rintro ⟨c, hc, hne⟩
    refine ⟨mapCtx σ.f c, (wfCtx_rename σ r hn c).mpr hc, ?_⟩
    intro hiff
    apply hne
    rw [plug_mapCtx, plug_mapCtx, derivable_rename σ.f_inj,
      derivable_rename σ.f_inj] at hiff
    exact hiff

theorem separable_renameR {n : Nat} (σ : DRen n) (r : Regime)
    (hn : r.data = n) (d d' : Nat) :
    separable (renameRegimeR σ.f r) (σ.f d) (σ.f d')
      ↔ separable r d d' :=
  (separable_reqs_irrel (renameRegime σ.f r) _ _ _).trans
    (separable_rename σ r hn d d')

theorem separable_symm (r : Regime) (d d' : Nat) :
    separable r d d' ↔ separable r d' d := by
  constructor <;>
    · rintro ⟨c, hc, hne⟩
      exact ⟨c, hc, fun hiff => hne hiff.symm⟩

/-! ## 4. The item action and its commutation -/

/-- Rename datum indices inside a candidate item.  Form indices stay
fixed: the certified congruence is over datum bijections with the
identity on forms, exactly the space the exhaustive test walks. -/
def mapItem (f : Nat → Nat) : Item → Item
  | .newDatum => .newDatum
  | .newForm a => .newForm a
  | .newInst fm args => .newInst fm (args.map f)
  | .newRuleAll fm => .newRuleAll fm

theorem mapItem_pad_f_g {n : Nat} (σ : DRen n) (it : Item) :
    mapItem (padF n σ.f) (mapItem (padF n σ.g) it) = it := by
  cases it with
  | newDatum => rfl
  | newForm a => rfl
  | newRuleAll fm => rfl
  | newInst fm args =>
    show Item.newInst fm ((args.map (padF n σ.g)).map (padF n σ.f))
        = Item.newInst fm args
    rw [List.map_map]
    have : (padF n σ.f ∘ padF n σ.g) = fun x => x := funext (padF_gf σ)
    rw [this, List.map_id']

/-- `insertNew` commutes with a map that separates the inserted
element from the members.  Stated with the pointwise hypothesis so it
serves `insts` (global injectivity) and `reqs` (injectivity on ordered
pairs only). -/
theorem insertNew_map_on {α β : Type} [DecidableEq α] [DecidableEq β]
    {h : α → β} (l : List α) (a : α)
    (hinj : ∀ x ∈ l, h x = h a → x = a) :
    (insertNew l a).map h = insertNew (l.map h) (h a) := by
  by_cases hm : a ∈ l
  · rw [insertNew_of_mem hm,
      insertNew_of_mem (List.mem_map.mpr ⟨a, hm, rfl⟩)]
  · have hm' : h a ∉ l.map h := by
      intro hmem
      obtain ⟨x, hx, hxe⟩ := List.mem_map.mp hmem
      exact hm (hinj x hx hxe ▸ hx)
    rw [insertNew_of_not_mem hm, insertNew_of_not_mem hm', List.map_append]
    rfl

/-- Admission can only grow the datum count. -/
theorem applyItem_data_mono {r s : Regime} {it : Item}
    (h : applyItem r it = some s) : r.data ≤ s.data := by
  cases it with
  | newDatum =>
    injection h with h
    subst h
    exact Nat.le_succ _
  | newForm a =>
    simp only [applyItem] at h
    split at h
    · injection h with h
      subst h
      exact Nat.le_refl _
    · exact nomatch h
  | newInst fm args =>
    simp only [applyItem] at h
    split at h
    · injection h with h
      subst h
      exact Nat.le_refl _
    · exact nomatch h
  | newRuleAll fm =>
    simp only [applyItem] at h
    split at h
    · injection h with h
      subst h
      exact Nat.le_refl _
    · exact nomatch h

/-- No item touches the requirement store: the `Item` grammar has no
imposition constructor.  This is the delta half of the round shape. -/
theorem applyItem_reqs {r s : Regime} {it : Item}
    (h : applyItem r it = some s) : s.reqs = r.reqs := by
  cases it with
  | newDatum =>
    injection h with h
    subst h
    rfl
  | newForm a =>
    simp only [applyItem] at h
    split at h
    · injection h with h
      subst h
      rfl
    · exact nomatch h
  | newInst fm args =>
    simp only [applyItem] at h
    split at h
    · injection h with h
      subst h
      rfl
    · exact nomatch h
  | newRuleAll fm =>
    simp only [applyItem] at h
    split at h
    · injection h with h
      subst h
      rfl
    · exact nomatch h

theorem applyDelta_nil (r : Regime) : applyDelta r [] = some r := rfl

theorem applyDelta_cons (r : Regime) (it : Item) (δ : List Item) :
    applyDelta r (it :: δ)
      = (applyItem r it).bind (fun s => applyDelta s δ) := rfl

theorem applyDelta_data_mono {δ : List Item} :
    ∀ {r s : Regime}, applyDelta r δ = some s → r.data ≤ s.data := by
  induction δ with
  | nil =>
    intro r s h
    injection h with h
    subst h
    exact Nat.le_refl _
  | cons it rest ih =>
    intro r s h
    rw [applyDelta_cons] at h
    cases happ : applyItem r it with
    | none => rw [happ] at h; exact nomatch h
    | some r1 =>
      rw [happ] at h
      exact Nat.le_trans (applyItem_data_mono happ) (ih h)

theorem applyDelta_reqs {δ : List Item} :
    ∀ {r s : Regime}, applyDelta r δ = some s → s.reqs = r.reqs := by
  induction δ with
  | nil =>
    intro r s h
    injection h with h
    subst h
    rfl
  | cons it rest ih =>
    intro r s h
    rw [applyDelta_cons] at h
    cases happ : applyItem r it with
    | none => rw [happ] at h; exact nomatch h
    | some r1 =>
      rw [happ] at h
      exact (ih h).trans (applyItem_reqs happ)

/-- One item commutes with the padded action.  The hypothesis is only
`n ≤ r.data`: below `n` the padding is the bijection; between `n` and
`r.data` — data introduced by earlier items of the same delta — it is
the identity; so an instance mentioning either kind is carried
correctly. -/
theorem applyItem_rename {n : Nat} (σ : DRen n) (r : Regime)
    (hn : n ≤ r.data) (it : Item) :
    applyItem (renameRegimeR (padF n σ.f) r) (mapItem (padF n σ.f) it)
      = Option.map (renameRegimeR (padF n σ.f)) (applyItem r it) := by
  cases it with
  | newDatum => rfl
  | newForm a =>
    show (if 1 ≤ a then
        some { renameRegimeR (padF n σ.f) r with
                forms := r.forms ++ [a] } else none)
      = Option.map (renameRegimeR (padF n σ.f))
          (if 1 ≤ a then some { r with forms := r.forms ++ [a] } else none)
    by_cases hg : 1 ≤ a
    · rw [if_pos hg, if_pos hg]
      rfl
    · rw [if_neg hg, if_neg hg]
      rfl
  | newRuleAll fm =>
    show (if fm < r.forms.length then
        some { renameRegimeR (padF n σ.f) r with
                rules := insertNew r.rules fm } else none)
      = Option.map (renameRegimeR (padF n σ.f))
          (if fm < r.forms.length then
            some { r with rules := insertNew r.rules fm } else none)
    by_cases hg : fm < r.forms.length
    · rw [if_pos hg, if_pos hg]
      rfl
    · rw [if_neg hg, if_neg hg]
      rfl
  | newInst fm args =>
    have hguard :
        (fm < r.forms.length ∧
          (args.map (padF n σ.f)).length = r.forms.getD fm 0 ∧
          ∀ x ∈ args.map (padF n σ.f), x < r.data)
        ↔ (fm < r.forms.length ∧ args.length = r.forms.getD fm 0 ∧
            ∀ x ∈ args, x < r.data) := by
      constructor
      · rintro ⟨h1, h2, h3⟩
        refine ⟨h1, by rwa [List.length_map] at h2, ?_⟩
        intro x hx
        have hFx := h3 _ (List.mem_map.mpr ⟨x, hx, rfl⟩)
        by_cases hxn : x < n
        · exact Nat.lt_of_lt_of_le hxn hn
        · rwa [padF_ge _ hxn] at hFx
      · rintro ⟨h1, h2, h3⟩
        refine ⟨h1, by rw [List.length_map]; exact h2, ?_⟩
        intro y hy
        obtain ⟨x, hx, hxy⟩ := List.mem_map.mp hy
        exact hxy ▸ padF_bound σ hn x (h3 x hx)
    show (if fm < r.forms.length ∧
          (args.map (padF n σ.f)).length = r.forms.getD fm 0 ∧
          (∀ x ∈ args.map (padF n σ.f), x < r.data) then
        some { renameRegimeR (padF n σ.f) r with
                insts := insertNew (r.insts.map (mapInst (padF n σ.f)))
                  (fm, args.map (padF n σ.f)) } else none)
      = Option.map (renameRegimeR (padF n σ.f))
          (if fm < r.forms.length ∧ args.length = r.forms.getD fm 0 ∧
              (∀ x ∈ args, x < r.data) then
            some { r with insts := insertNew r.insts (fm, args) } else none)
    by_cases hg : fm < r.forms.length ∧ args.length = r.forms.getD fm 0 ∧
        ∀ x ∈ args, x < r.data
    · rw [if_pos (hguard.mpr hg), if_pos hg]
      have e : (insertNew r.insts (fm, args)).map (mapInst (padF n σ.f))
          = insertNew (r.insts.map (mapInst (padF n σ.f)))
              (fm, args.map (padF n σ.f)) :=
        insertNew_map_on r.insts (fm, args)
          (fun x _ hx => mapInst_inj (padF_inj σ) hx)
      show some _ = some (renameRegimeR (padF n σ.f)
        { r with insts := insertNew r.insts (fm, args) })
      refine congrArg some ?_
      show ({ renameRegimeR (padF n σ.f) r with
        insts := insertNew (r.insts.map (mapInst (padF n σ.f)))
          (fm, args.map (padF n σ.f)) } : Regime) = _
      rw [← e]
      rfl
    · rw [if_neg (fun hg' => hg (hguard.mp hg')), if_neg hg]
      rfl

/-- Delta-level commutation: the invariant `n ≤ data` advances by
`applyItem_data_mono`; failure branches propagate through the map. -/
theorem applyDelta_rename {n : Nat} (σ : DRen n) {δ : List Item} :
    ∀ {r : Regime}, n ≤ r.data →
      applyDelta (renameRegimeR (padF n σ.f) r)
          (δ.map (mapItem (padF n σ.f)))
        = Option.map (renameRegimeR (padF n σ.f)) (applyDelta r δ) := by
  induction δ with
  | nil => intro r _; rfl
  | cons it rest ih =>
    intro r hn
    rw [List.map_cons, applyDelta_cons, applyDelta_cons,
      applyItem_rename σ r hn it]
    cases happ : applyItem r it with
    | none => rfl
    | some r1 =>
      show applyDelta (renameRegimeR (padF n σ.f) r1)
          (rest.map (mapItem (padF n σ.f)))
        = Option.map (renameRegimeR (padF n σ.f)) (applyDelta r1 rest)
      exact ih (Nat.le_trans hn (applyItem_data_mono happ))

/-! ## 5. Cancellation and agreement -/

theorem map_congr_mem {α β : Type} {f g : α → β} :
    ∀ (l : List α), (∀ a ∈ l, f a = g a) → l.map f = l.map g := by
  intro l
  induction l with
  | nil => intro _; rfl
  | cons a as ih =>
    intro h
    rw [List.map_cons, List.map_cons, h a (List.mem_cons_self),
      ih (fun x hx => h x (List.mem_cons_of_mem _ hx))]

theorem DRen.inv_f {n : Nat} (σ : DRen n) : σ.inv.f = σ.g := rfl
theorem DRen.inv_g {n : Nat} (σ : DRen n) : σ.inv.g = σ.f := rfl

/-- The renormalization argument, over any two-sided-inverse pair of
maps: it serves both the bijection itself and its padding. -/
theorem mapReq_inv_pair {f g : Nat → Nat} (hfg : ∀ x, g (f x) = x)
    {i j : Nat} (hij : i < j) :
    mapReq g (mapReq f (i, j)) = (i, j) := by
  rcases Nat.le_total (f i) (f j) with h | h
  · show mapReq g (min (f i) (f j), max (f i) (f j)) = (i, j)
    rw [Nat.min_eq_left h, Nat.max_eq_right h]
    show (min (g (f i)) (g (f j)), max (g (f i)) (g (f j))) = (i, j)
    rw [hfg, hfg, Nat.min_eq_left (Nat.le_of_lt hij),
      Nat.max_eq_right (Nat.le_of_lt hij)]
  · show mapReq g (min (f i) (f j), max (f i) (f j)) = (i, j)
    rw [Nat.min_eq_right h, Nat.max_eq_left h]
    show (min (g (f j)) (g (f i)), max (g (f j)) (g (f i))) = (i, j)
    rw [hfg, hfg, Nat.min_eq_right (Nat.le_of_lt hij),
      Nat.max_eq_left (Nat.le_of_lt hij)]

/-- Full-action cancellation over any two-sided-inverse pair, on
regimes with ordered requirements — the only regimes `Regime.wf`
allows.  The action is NOT injective on regimes with disordered
requirement pairs, which is exactly why the congruence below is
packaged as mapping plus image-totality rather than an equality-form
iff over an arbitrary child. -/
theorem renameRegimeR_inv_pair {f g : Nat → Nat}
    (hfg : ∀ x, g (f x) = x) (r : Regime)
    (hreq : ∀ q ∈ r.reqs, q.1 < q.2) :
    renameRegimeR g (renameRegimeR f r) = r := by
  cases r with
  | mk d fo ins ru rq =>
    have hi : (ins.map (mapInst f)).map (mapInst g) = ins := by
      rw [List.map_map]
      have hcomp : (mapInst g ∘ mapInst f) = fun p => p := by
        funext p
        obtain ⟨fm, args⟩ := p
        show (fm, (args.map f).map g) = (fm, args)
        rw [List.map_map]
        have : (g ∘ f) = fun x => x := funext hfg
        rw [this, List.map_id']
      rw [hcomp, List.map_id']
    have hq : (rq.map (mapReq f)).map (mapReq g) = rq := by
      rw [List.map_map]
      have := map_congr_mem (f := mapReq g ∘ mapReq f)
        (g := fun q => q) rq
        (fun q hq0 => by
          obtain ⟨a, b⟩ := q
          exact mapReq_inv_pair hfg (hreq _ hq0))
      rw [this, List.map_id']
    show Regime.mk d fo ((ins.map (mapInst f)).map (mapInst g)) ru
        ((rq.map (mapReq f)).map (mapReq g))
      = Regime.mk d fo ins ru rq
    rw [hi, hq]

theorem renameRegimeR_g_f {n : Nat} (σ : DRen n) (r : Regime)
    (hreq : ∀ q ∈ r.reqs, q.1 < q.2) :
    renameRegimeR σ.g (renameRegimeR σ.f r) = r :=
  renameRegimeR_inv_pair σ.fg r hreq

theorem renameRegimeR_pad_f_g {n : Nat} (σ : DRen n) (s : Regime)
    (hreq : ∀ q ∈ s.reqs, q.1 < q.2) :
    renameRegimeR (padF n σ.f) (renameRegimeR (padF n σ.g) s) = s :=
  renameRegimeR_inv_pair (padF_gf σ) s hreq

/-- On a regime whose indices are all below `n`, the padded and raw
spellings of the action agree. -/
theorem renameRegimeR_padF_agree {n : Nat} (σ : DRen n) (r : Regime)
    (hn : r.data = n)
    (hinst : ∀ p ∈ r.insts, ∀ a ∈ p.2, a < r.data)
    (hreq : ∀ q ∈ r.reqs, q.1 < q.2 ∧ q.2 < r.data) :
    renameRegimeR (padF n σ.f) r = renameRegimeR σ.f r := by
  subst hn
  cases r with
  | mk d fo ins ru rq =>
    have hi : ins.map (mapInst (padF d σ.f)) = ins.map (mapInst σ.f) :=
      map_congr_mem ins (fun p hp => by
        obtain ⟨fm, args⟩ := p
        show (fm, args.map (padF d σ.f)) = (fm, args.map σ.f)
        have : args.map (padF d σ.f) = args.map σ.f :=
          map_congr_mem args
            (fun a ha => padF_lt σ.f (hinst _ hp a ha))
        rw [this])
    have hq : rq.map (mapReq (padF d σ.f)) = rq.map (mapReq σ.f) :=
      map_congr_mem rq (fun q hq0 => by
        obtain ⟨h1, h2⟩ := hreq q hq0
        show (min (padF d σ.f q.1) (padF d σ.f q.2),
              max (padF d σ.f q.1) (padF d σ.f q.2))
          = (min (σ.f q.1) (σ.f q.2), max (σ.f q.1) (σ.f q.2))
        rw [padF_lt σ.f (Nat.lt_trans h1 h2), padF_lt σ.f h2])
    show Regime.mk d fo (ins.map (mapInst (padF d σ.f))) ru
        (rq.map (mapReq (padF d σ.f)))
      = Regime.mk d fo (ins.map (mapInst σ.f)) ru (rq.map (mapReq σ.f))
    rw [hi, hq]

/-- The datum-bound conjunct of well-formedness survives the action. -/
theorem rename_insts_bound {n : Nat} (σ : DRen n) (r : Regime)
    (hn : r.data = n)
    (h : ∀ p ∈ r.insts, ∀ a ∈ p.2, a < r.data) :
    ∀ p ∈ (renameRegimeR σ.f r).insts, ∀ a ∈ p.2, a < r.data := by
  subst hn
  intro p hp a ha
  obtain ⟨q, hq, hqp⟩ := List.mem_map.mp hp
  subst hqp
  obtain ⟨b, hb, hba⟩ := List.mem_map.mp ha
  exact hba ▸ σ.fbound b (h q hq b hb)

/-! ## 6. The imposition step commutes -/

theorem stepE_impose_rename {n : Nat} (σ : DRen n) (r : Regime)
    (hn : r.data = n)
    (hreq : ∀ q ∈ r.reqs, q.1 < q.2 ∧ q.2 < r.data)
    {i j : Nat} (hij : i < j) (hj : j < r.data) :
    stepE (renameRegimeR σ.f r)
        (.impose (mapReq σ.f (i, j)).1 (mapReq σ.f (i, j)).2)
      = Option.map (renameRegimeR σ.f) (stepE r (.impose i j)) := by
  subst hn
  have hg1 : (mapReq σ.f (i, j)).1 < (mapReq σ.f (i, j)).2 :=
    mapReq_ordered σ.f_inj hij
  have hg2 : (mapReq σ.f (i, j)).2 < r.data := by
    show max (σ.f i) (σ.f j) < r.data
    exact Nat.max_lt.mpr
      ⟨σ.fbound i (Nat.lt_trans hij hj), σ.fbound j hj⟩
  show (if (mapReq σ.f (i, j)).1 < (mapReq σ.f (i, j)).2 ∧
          (mapReq σ.f (i, j)).2 < r.data then
      some { renameRegimeR σ.f r with
              reqs := insertNew (r.reqs.map (mapReq σ.f))
                ((mapReq σ.f (i, j)).1, (mapReq σ.f (i, j)).2) }
    else none)
    = Option.map (renameRegimeR σ.f)
        (if i < j ∧ j < r.data then
          some { r with reqs := insertNew r.reqs (i, j) } else none)
  rw [if_pos ⟨hg1, hg2⟩, if_pos ⟨hij, hj⟩]
  refine congrArg some ?_
  have e : (insertNew r.reqs (i, j)).map (mapReq σ.f)
      = insertNew (r.reqs.map (mapReq σ.f)) (mapReq σ.f (i, j)) :=
    insertNew_map_on r.reqs (i, j)
      (fun q hq0 hq1 =>
        mapReq_inj_ordered σ.f_inj (hreq q hq0).1 hij hq1)
  show ({ renameRegimeR σ.f r with
      reqs := insertNew (r.reqs.map (mapReq σ.f)) (mapReq σ.f (i, j)) }
      : Regime)
    = renameRegimeR σ.f { r with reqs := insertNew r.reqs (i, j) }
  rw [← e]
  rfl

/-! ## 7. The transition object and validity transport -/

/-- One engine round: impose the challenged pair, then apply the
response delta.  This composite is the Lean-side transition object; it
did not previously exist — `stepE` and `applyDelta` are its parts. -/
def respond (r : Regime) (i j : Nat) (δ : List Item) : Option Regime :=
  (stepE r (.impose i j)).bind (fun s => applyDelta s δ)

/-- Ordered requirements survive a round: the impose guard inserts
only ordered pairs and no delta item touches `reqs`. -/
theorem respond_reqs_ordered {r s : Regime} {i j : Nat} {δ : List Item}
    (h : respond r i j δ = some s)
    (hr : ∀ q ∈ r.reqs, q.1 < q.2) :
    ∀ q ∈ s.reqs, q.1 < q.2 := by
  by_cases hg : i < j ∧ j < r.data
  · have hstep : stepE r (.impose i j)
        = some { r with reqs := insertNew r.reqs (i, j) } := by
      show (if i < j ∧ j < r.data then _ else _) = _
      rw [if_pos hg]
    unfold respond at h
    rw [hstep] at h
    have h' : applyDelta { r with reqs := insertNew r.reqs (i, j) } δ
        = some s := h
    have hsr := applyDelta_reqs h'
    intro q hq
    rw [hsr] at hq
    rcases mem_insertNew.mp hq with hin | he
    · exact hr q hin
    · subst he
      exact hg.1
  · have hstep : stepE r (.impose i j) = none := by
      show (if i < j ∧ j < r.data then _ else _) = _
      rw [if_neg hg]
    unfold respond at h
    rw [hstep] at h
    have h' : (none : Option Regime) = some s := h
    exact nomatch h'

/-- The round commutes with the action. -/
theorem respond_rename {n : Nat} (σ : DRen n) (r : Regime)
    (hn : r.data = n)
    (hinst : ∀ p ∈ r.insts, ∀ a ∈ p.2, a < r.data)
    (hreq : ∀ q ∈ r.reqs, q.1 < q.2 ∧ q.2 < r.data)
    {i j : Nat} (hij : i < j) (hj : j < r.data) (δ : List Item) :
    respond (renameRegimeR σ.f r)
        (mapReq σ.f (i, j)).1 (mapReq σ.f (i, j)).2
        (δ.map (mapItem (padF n σ.f)))
      = Option.map (renameRegimeR (padF n σ.f)) (respond r i j δ) := by
  unfold respond
  rw [stepE_impose_rename σ r hn hreq hij hj]
  have hstep : stepE r (.impose i j)
      = some { r with reqs := insertNew r.reqs (i, j) } := by
    show (if i < j ∧ j < r.data then _ else _) = _
    rw [if_pos ⟨hij, hj⟩]
  rw [hstep]
  show applyDelta (renameRegimeR σ.f { r with reqs := insertNew r.reqs (i, j) })
      (δ.map (mapItem (padF n σ.f)))
    = Option.map (renameRegimeR (padF n σ.f))
        (applyDelta { r with reqs := insertNew r.reqs (i, j) } δ)
  have hr1inst : ∀ p ∈ ({ r with reqs := insertNew r.reqs (i, j) }
      : Regime).insts, ∀ a ∈ p.2, a < r.data := hinst
  have hr1req : ∀ q ∈ ({ r with reqs := insertNew r.reqs (i, j) }
      : Regime).reqs, q.1 < q.2 ∧ q.2 < r.data := by
    intro q hq
    rcases mem_insertNew.mp hq with hin | he
    · exact hreq q hin
    · subst he
      exact ⟨hij, hj⟩
  rw [← renameRegimeR_padF_agree σ
    { r with reqs := insertNew r.reqs (i, j) } hn hr1inst hr1req]
  exact applyDelta_rename σ (Nat.le_of_eq hn.symm)

theorem validResponse_symm (r : Regime) (a b : Nat) (δ : List Item) :
    validResponse r a b δ ↔ validResponse r b a δ := by
  constructor <;>
    · rintro ⟨s, h1, h2, h3⟩
      exact ⟨s, h1, (separable_symm s _ _).mp h2, h3⟩

/-- Validity of a response transports along the action. -/
theorem validResponse_rename {n : Nat} (σ : DRen n) (r : Regime)
    (hn : r.data = n)
    (hinst : ∀ p ∈ r.insts, ∀ a ∈ p.2, a < r.data)
    (hreq : ∀ q ∈ r.reqs, q.1 < q.2 ∧ q.2 < r.data)
    {i j : Nat} (hi : i < r.data) (hj : j < r.data) (δ : List Item) :
    validResponse (renameRegimeR σ.f r) (σ.f i) (σ.f j)
        (δ.map (mapItem (padF n σ.f)))
      ↔ validResponse r i j δ := by
  have hAD : applyDelta (renameRegimeR σ.f r) (δ.map (mapItem (padF n σ.f)))
      = Option.map (renameRegimeR (padF n σ.f)) (applyDelta r δ) := by
    rw [← renameRegimeR_padF_agree σ r hn hinst hreq]
    exact applyDelta_rename σ (Nat.le_of_eq hn.symm)
  have key : ∀ (s : Regime), n ≤ s.data → ∀ a b : Nat, a < n → b < n →
      (separable (renameRegimeR (padF n σ.f) s) (σ.f a) (σ.f b)
        ↔ separable s a b) := by
    intro s hm a b ha hb
    have e1 : σ.f a = padF n σ.f a := (padF_lt _ ha).symm
    have e2 : σ.f b = padF n σ.f b := (padF_lt _ hb).symm
    rw [e1, e2]
    exact separable_renameR (σ.pad s.data hm) s rfl a b
  constructor
  · rintro ⟨s', hs', hsep', hall'⟩
    rw [hAD] at hs'
    cases h0 : applyDelta r δ with
    | none =>
      rw [h0] at hs'
      exact nomatch hs'
    | some s =>
      rw [h0] at hs'
      injection hs' with hs'
      subst hs'
      have hm : n ≤ s.data := hn ▸ applyDelta_data_mono h0
      refine ⟨s, h0, ?_, ?_⟩
      · exact (key s hm i j (hn ▸ hi) (hn ▸ hj)).mp hsep'
      · intro q hq0
        have hq' := hall' (mapReq σ.f q)
          (List.mem_map.mpr ⟨q, hq0, rfl⟩)
        obtain ⟨h1, h2⟩ := hreq q hq0
        have hqa : q.1 < n := hn ▸ Nat.lt_trans h1 h2
        have hqb : q.2 < n := hn ▸ h2
        rcases mapReq_cases σ.f q with hc | hc <;> rw [hc] at hq'
        · exact (key s hm q.1 q.2 hqa hqb).mp hq'
        · exact (separable_symm s q.2 q.1).mp
            ((key s hm q.2 q.1 hqb hqa).mp hq')
  · rintro ⟨s, hs, hsep, hall⟩
    have hm : n ≤ s.data := hn ▸ applyDelta_data_mono hs
    refine ⟨renameRegimeR (padF n σ.f) s, ?_, ?_, ?_⟩
    · rw [hAD, hs]
      rfl
    · exact (key s hm i j (hn ▸ hi) (hn ▸ hj)).mpr hsep
    · intro q' hq'
      obtain ⟨q, hq0, hqe⟩ := List.mem_map.mp hq'
      subst hqe
      obtain ⟨h1, h2⟩ := hreq q hq0
      have hqa : q.1 < n := hn ▸ Nat.lt_trans h1 h2
      have hqb : q.2 < n := hn ▸ h2
      rcases mapReq_cases σ.f q with hc | hc <;> rw [hc]
      · exact (key s hm q.1 q.2 hqa hqb).mpr (hall q hq0)
      · exact (key s hm q.2 q.1 hqb hqa).mpr
          ((separable_symm s q.1 q.2).mp (hall q hq0))

/-! ## 8. R7: the transition relation is congruent to the renaming -/

/-- One collapsed pair with one valid response and its child.  The
relation quantifies over EVERY collapsed pair and EVERY valid
response; no representative is selected.  That is the exact sense in
which a quotiented transition is well defined, and it is deliberately
weaker than any statement about a selection function (section 9
below). -/
def TransStep (r : Regime) (i j : Nat) (δ : List Item) (s : Regime) :
    Prop :=
  i < j ∧ j < r.data ∧ collapsed r i j ∧
  validResponse r i j δ ∧ respond r i j δ = some s

/-- **R7, the mapping direction.**  A datum renaming carries every
step onto a step: the renamed regime takes the renamed step, and the
children correspond under the same padded renaming. -/
theorem transStep_rename_fwd {n : Nat} (σ : DRen n) (r : Regime)
    (hn : r.data = n)
    (hinst : ∀ p ∈ r.insts, ∀ a ∈ p.2, a < r.data)
    (hreq : ∀ q ∈ r.reqs, q.1 < q.2 ∧ q.2 < r.data)
    {i j : Nat} {δ : List Item} {s : Regime}
    (h : TransStep r i j δ s) :
    TransStep (renameRegimeR σ.f r)
      (mapReq σ.f (i, j)).1 (mapReq σ.f (i, j)).2
      (δ.map (mapItem (padF n σ.f)))
      (renameRegimeR (padF n σ.f) s) := by
  obtain ⟨hij, hjd, hcol, hval, hresp⟩ := h
  refine ⟨mapReq_ordered σ.f_inj hij, ?_, ?_, ?_, ?_⟩
  · show max (σ.f i) (σ.f j) < (renameRegimeR σ.f r).data
    show max (σ.f i) (σ.f j) < r.data
    rw [hn]
    exact Nat.max_lt.mpr
      ⟨σ.fbound i (hn ▸ Nat.lt_trans hij hjd), σ.fbound j (hn ▸ hjd)⟩
  · rcases mapReq_cases σ.f (i, j) with hc | hc <;> rw [hc]
    · exact (collapsed_renameR σ r hn i j).mpr hcol
    · exact (collapsed_renameR σ r hn j i).mpr
        ((collapsed_symm r i j).mp hcol)
  · rcases mapReq_cases σ.f (i, j) with hc | hc <;> rw [hc]
    · exact (validResponse_rename σ r hn hinst hreq
        (Nat.lt_trans hij hjd) hjd δ).mpr hval
    · exact (validResponse_symm _ _ _ _).mp
        ((validResponse_rename σ r hn hinst hreq
          (Nat.lt_trans hij hjd) hjd δ).mpr hval)
  · rw [respond_rename σ r hn hinst hreq hij hjd δ, hresp]
    rfl

/-- **R7, image totality.**  Every step OF the renamed regime is the
image of a step of `r`: the renamed relation is exactly the image of
the original relation, not merely a superset.

An equality-form iff over an arbitrary child is NOT stated, and would
be false: `mapReq` renormalizes, so the action is not injective on
regimes with disordered requirement pairs.  Totality plus the mapping
direction is the honest packaging. -/
theorem transStep_image_total {n : Nat} (σ : DRen n) (r : Regime)
    (hn : r.data = n)
    (hinst : ∀ p ∈ r.insts, ∀ a ∈ p.2, a < r.data)
    (hreq : ∀ q ∈ r.reqs, q.1 < q.2 ∧ q.2 < r.data)
    {i' j' : Nat} {δ' : List Item} {s' : Regime}
    (h : TransStep (renameRegimeR σ.f r) i' j' δ' s') :
    ∃ i j δ s, TransStep r i j δ s ∧
      (i', j') = mapReq σ.f (i, j) ∧
      δ' = δ.map (mapItem (padF n σ.f)) ∧
      s' = renameRegimeR (padF n σ.f) s := by
  have hinst' : ∀ p ∈ (renameRegimeR σ.f r).insts, ∀ a ∈ p.2,
      a < (renameRegimeR σ.f r).data :=
    rename_insts_bound σ r hn hinst
  have hreq' : ∀ q ∈ (renameRegimeR σ.f r).reqs,
      q.1 < q.2 ∧ q.2 < (renameRegimeR σ.f r).data :=
    renameR_reqs_wf σ r hn hreq
  have hfwd := transStep_rename_fwd σ.inv (renameRegimeR σ.f r) hn
    hinst' hreq' h
  rw [DRen.inv_f] at hfwd
  rw [renameRegimeR_g_f σ r (fun q hq => (hreq q hq).1)] at hfwd
  have hij' : i' < j' := h.1
  refine ⟨(mapReq σ.g (i', j')).1, (mapReq σ.g (i', j')).2,
    δ'.map (mapItem (padF n σ.g)),
    renameRegimeR (padF n σ.g) s', hfwd, ?_, ?_, ?_⟩
  · exact (mapReq_inv_pair σ.gf hij').symm
  · rw [List.map_map]
    have hcomp : (mapItem (padF n σ.f) ∘ mapItem (padF n σ.g))
        = fun it => it := funext (mapItem_pad_f_g σ)
    rw [hcomp, List.map_id']
  · have hs'req : ∀ q ∈ s'.reqs, q.1 < q.2 := by
      obtain ⟨_, _, _, _, hresp'⟩ := h
      exact respond_reqs_ordered hresp'
        (fun q hq => (hreq' q hq).1)
    exact (renameRegimeR_pad_f_g σ s' hs'req).symm

/-! ## 9. Costs and minima transport: the R6 counting pattern -/

/-- The first declared cost measure is the item count; the item action
preserves it. -/
theorem mapItem_length (f : Nat → Nat) (δ : List Item) :
    (δ.map (mapItem f)).length = δ.length :=
  by rw [List.length_map]

/-- The second component of the second declared cost measure. -/
def formAritySum : List Item → Nat
  | [] => 0
  | .newForm a :: rest => a + formAritySum rest
  | .newDatum :: rest => formAritySum rest
  | .newInst _ _ :: rest => formAritySum rest
  | .newRuleAll _ :: rest => formAritySum rest

/-- The item action fixes `newForm`, so the sum is preserved. -/
theorem formAritySum_map (f : Nat → Nat) (δ : List Item) :
    formAritySum (δ.map (mapItem f)) = formAritySum δ := by
  induction δ with
  | nil => rfl
  | cons it rest ih =>
    cases it with
    | newDatum => exact ih
    | newForm a =>
      show a + formAritySum (rest.map (mapItem f)) = a + formAritySum rest
      rw [ih]
    | newInst fm args => exact ih
    | newRuleAll fm => exact ih

/-- Valid-response counts transport over any caller-supplied candidate
list, with caller-supplied deciders — the division of labour of
`collapsedCount_rename`: Python enumerates and decides, Lean states
what the decision means.  Together with `mapItem_length` and
`formAritySum_map` this carries the attained minimum cost and the
number of minima of both declared measures across the renaming. -/
theorem validCount_rename {n : Nat} (σ : DRen n) (r : Regime)
    (hn : r.data = n)
    (hinst : ∀ p ∈ r.insts, ∀ a ∈ p.2, a < r.data)
    (hreq : ∀ q ∈ r.reqs, q.1 < q.2 ∧ q.2 < r.data)
    {i j : Nat} (hi : i < r.data) (hj : j < r.data)
    (p q : List Item → Bool)
    (hp : ∀ δ, p δ = true ↔ validResponse r i j δ)
    (hq : ∀ δ, q δ = true ↔
      validResponse (renameRegimeR σ.f r) (σ.f i) (σ.f j) δ)
    (L : List (List Item)) :
    (L.map (fun δ => δ.map (mapItem (padF n σ.f)))).countP q
      = L.countP p := by
  induction L with
  | nil => rfl
  | cons δ rest ih =>
    have hstep : q (δ.map (mapItem (padF n σ.f))) = p δ := by
      apply Bool.eq_iff_iff.mpr
      rw [hq, hp]
      exact validResponse_rename σ r hn hinst hreq hi hj δ
    simp only [List.map_cons, List.countP_cons, ih, hstep]

/-! ## 10. The boundary: selection is NOT congruent

The congruence above is a property of the relation.  The index-least
selection is not congruent, and saying so here keeps this module from
appearing to contradict the recorded regression: on the regime below,
both the regime and its renaming have `(0, 1)` as their index-least
collapsed pair, yet the renaming carries `(0, 1)` to `(2, 3)`.  A
policy that challenges the least collapsed pair therefore challenges
pairs NOT related by the renaming.  The further fact that the
resulting children are non-isomorphic is certified computationally and
is not re-proved here. -/

/-- Four data, one unary form, instances marking data 2 and 3 — the
regression regime of the test suite. -/
def regRegime : Regime := ⟨4, [1], [(0, [2]), (0, [3])], [], []⟩

/-- The double transposition 0↔2, 1↔3, self-inverse. -/
def regSwapFun : Nat → Nat
  | 0 => 2
  | 1 => 3
  | 2 => 0
  | 3 => 1
  | x + 4 => x + 4

theorem regSwapFun_invol : ∀ x, regSwapFun (regSwapFun x) = x := by
  intro x
  match x with
  | 0 => rfl
  | 1 => rfl
  | 2 => rfl
  | 3 => rfl
  | _ + 4 => rfl

theorem regSwapFun_bound : ∀ x, x < 4 → regSwapFun x < 4 := by
  intro x hx
  match x with
  | 0 => decide
  | 1 => decide
  | 2 => decide
  | 3 => decide
  | y + 4 => exact absurd hx (Nat.not_lt.mpr (Nat.le_add_left 4 y))

def regSwap : DRen 4 where
  f := regSwapFun
  g := regSwapFun
  fg := regSwapFun_invol
  gf := regSwapFun_invol
  fbound := regSwapFun_bound
  gbound := regSwapFun_bound

/-- In a regime with one unary form, every well-formed context is the
single one-hole context. -/
theorem one_unary_form_ctx_char (r : Regime) (hf : r.forms = [1])
    (c : Ctx) : wfCtx r c ↔ c = ⟨0, [none]⟩ := by
  constructor
  · rintro ⟨h1, h2, h3, _⟩
    rw [hf] at h1 h2
    have hform : c.form = 0 := Nat.lt_one_iff.mp h1
    rw [hform] at h2
    have hlen : c.slots.length = 1 := h2
    have hslots : c.slots = [none] := by
      cases hs : c.slots with
      | nil => rw [hs] at hlen; exact nomatch hlen
      | cons a rest =>
        cases rest with
        | nil =>
          rw [hs] at h3
          have := List.mem_singleton.mp h3
          rw [← this]
        | cons b rest' =>
          rw [hs] at hlen
          exact nomatch hlen
    cases c with
    | mk form slots =>
      simp only at hform hslots
      rw [hform, hslots]
  · intro h
    subst h
    refine ⟨?_, ?_, ?_, ?_⟩
    · rw [hf]; exact Nat.zero_lt_one
    · rw [hf]; rfl
    · exact List.mem_singleton.mpr rfl
    · intro s hs
      have hsn := List.mem_singleton.mp hs
      subst hsn
      trivial

theorem reg_collapsed_01 : collapsed regRegime 0 1 := by
  intro c hc
  rw [one_unary_form_ctx_char regRegime rfl c] at hc
  subst hc
  decide

theorem reg_renamed_collapsed_01 :
    collapsed (renameRegimeR regSwap.f regRegime) 0 1 := by
  intro c hc
  rw [one_unary_form_ctx_char (renameRegimeR regSwap.f regRegime)
    rfl c] at hc
  subst hc
  decide

/-- **The boundary, witnessed.**  The index-least collapsed pair is
`(0, 1)` on both sides, but the renaming does not carry `(0, 1)` to
`(0, 1)`: a policy selecting the index-least pair challenges pairs not
related by the renaming.  The relation is congruent; the selection is
not. -/
theorem least_pair_selection_not_congruent :
    collapsed regRegime 0 1 ∧
    collapsed (renameRegimeR regSwap.f regRegime) 0 1 ∧
    mapReq regSwap.f (0, 1) ≠ (0, 1) :=
  ⟨reg_collapsed_01, reg_renamed_collapsed_01, by decide⟩

end Derivation
