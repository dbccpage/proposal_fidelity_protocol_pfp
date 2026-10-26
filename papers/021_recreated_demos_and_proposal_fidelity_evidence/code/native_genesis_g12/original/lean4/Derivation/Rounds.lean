import Derivation.TransitionTransport
import Derivation.Counting

/-!
# The counting-law hypotheses, discharged for the transition system (R8)

Residual R8 in `paper.md` section 12 is kind (b):
`strict_bounded_length`, `no_supply_round_bound` and `allPairs_length`
are proved as conditional abstract laws, and the connection to the
transition system — that each accepted round imposes exactly one new
requirement over a fixed datum count — was discharged computationally,
for the exported runs only.  This module supplies the connection.

## The round shape, declared

No Lean object previously represented a run.  `ClosedRun` is the
minimal one: a round is an imposed target plus a response delta, the
engine's exact event sequence (`respond`, from the R7 module), under
two side conditions mirroring the engine's asserted invariants — the
imposed pair is fresh (targets are asserted disjoint from standing
requirements) and the response admits no fresh datum (the closed-system
baseline: the `Item` grammar has no imposition constructor, and datum
fixity is what "closed" means).

## What is proved, and what remains computational

Proved: under the declared round shape, the requirement count grows by
EXACTLY one per round over a FIXED datum count; requirements stay
ordered, bounded, and duplicate-free; and therefore any closed run from
an empty requirement store makes at most `n * (n - 1) / 2` rounds —
stated division-free as `2 * rounds ≤ n * (n - 1)`, the form
`allPairs_length` takes.  These are the hypotheses of
`strict_bounded_length` and `no_supply_round_bound`, discharged for
the transition system rather than assumed of it.

Still computational, and narrowed to exactly this: that each EXPORTED
round has the declared syntactic shape — one fresh imposition, no
fresh-datum item.  Discharging the freshness side condition from the
closure policy itself would require formalizing collapsed-pair
selection and acceptance semantics, which is beyond what the register
row asks.

## Counting infrastructure

The subset-counting lemma is proved with the decide-filter technique
recorded in `Pigeonhole.lean`: on this toolchain `List.nodup_range`,
`List.length_erase` and the `==`-routes carry `Classical.choice`, and
the `decide`-filter routes do not.  Everything below is core only.
-/

namespace Derivation

/-! ## 1. List counting, choice-free -/

theorem filter_length_split {α : Type} (p : α → Bool) :
    ∀ l : List α,
      (l.filter p).length + (l.filter (fun x => !(p x))).length
        = l.length := by
  intro l
  induction l with
  | nil => rfl
  | cons x t ih =>
    by_cases hp : p x = true
    · rw [List.filter_cons_of_pos hp,
        List.filter_cons_of_neg (by rw [hp]; decide)]
      show (x :: t.filter p).length
          + (t.filter (fun x => !(p x))).length = t.length + 1
      rw [List.length_cons]
      omega
    · have hp' : p x = false := Bool.eq_false_iff.mpr hp
      rw [List.filter_cons_of_neg (by rw [hp']; decide),
        List.filter_cons_of_pos (by rw [hp']; rfl)]
      show (t.filter p).length
          + (x :: t.filter (fun x => !(p x))).length = t.length + 1
      rw [List.length_cons]
      omega

theorem nodup_head' {α : Type} {x : α} {t : List α}
    (h : List.Nodup (x :: t)) : ∀ a ∈ t, x ≠ a := by
  cases h with
  | cons h1 _ => exact h1

theorem nodup_tail' {α : Type} {x : α} {t : List α}
    (h : List.Nodup (x :: t)) : List.Nodup t := by
  cases h with
  | cons _ h2 => exact h2

theorem filter_none_of_all_false {α : Type} {p : α → Bool} :
    ∀ {l : List α}, (∀ x ∈ l, p x = false) → l.filter p = [] := by
  intro l
  induction l with
  | nil => intro _; rfl
  | cons x t ih =>
    intro h
    rw [List.filter_cons_of_neg
      (by rw [h x (List.mem_cons_self)]; decide)]
    exact ih (fun y hy => h y (List.mem_cons_of_mem _ hy))

theorem filter_nodup' {α : Type} (p : α → Bool) :
    ∀ {l : List α}, l.Nodup → (l.filter p).Nodup := by
  intro l
  induction l with
  | nil => intro _; exact List.Pairwise.nil
  | cons x t ih =>
    intro h
    by_cases hp : p x = true
    · rw [List.filter_cons_of_pos hp]
      exact List.Pairwise.cons
        (fun y hy => nodup_head' h y (List.mem_filter.mp hy).1)
        (ih (nodup_tail' h))
    · rw [List.filter_cons_of_neg hp]
      exact ih (nodup_tail' h)

/-- In a duplicate-free list containing `a`, exactly one member equals
`a`. -/
theorem nodup_filter_self_length {α : Type} [DecidableEq α] (a : α) :
    ∀ (l : List α), l.Nodup → a ∈ l →
      (l.filter (fun x => decide (x = a))).length = 1 := by
  intro l
  induction l with
  | nil => intro _ h; exact nomatch h
  | cons x t ih =>
    intro hn hm
    by_cases hx : x = a
    · subst hx
      have hpos : List.filter (fun y => decide (y = x)) (x :: t)
          = x :: List.filter (fun y => decide (y = x)) t :=
        List.filter_cons_of_pos (decide_eq_true rfl)
      rw [hpos]
      have ht : t.filter (fun y => decide (y = x)) = [] :=
        filter_none_of_all_false
          (fun y hy => decide_eq_false
            (fun he => nodup_head' hn y hy he.symm))
      rw [ht]
      rfl
    · rw [List.filter_cons_of_neg (by rw [decide_eq_false hx]; decide)]
      have hm' : a ∈ t := by
        rcases List.mem_cons.mp hm with he | hmt
        · exact absurd he.symm hx
        · exact hmt
      exact ih (nodup_tail' hn) hm'

/-- **Choice-free subset counting**: a duplicate-free list included in
a duplicate-free list is no longer than it. -/
theorem nodup_subset_length {α : Type} [DecidableEq α] :
    ∀ (l L : List α), l.Nodup → L.Nodup →
      (∀ x ∈ l, x ∈ L) → l.length ≤ L.length := by
  intro l
  induction l with
  | nil => intro L _ _ _; exact Nat.zero_le _
  | cons a t ih =>
    intro L hln hLn hsub
    have haL : a ∈ L := hsub a (List.mem_cons_self)
    have hone : (L.filter (fun x => decide (x = a))).length = 1 :=
      nodup_filter_self_length a L hLn haL
    have hsplit := filter_length_split (fun x => decide (x = a)) L
    have ht : t.length
        ≤ (L.filter (fun x => !(decide (x = a)))).length := by
      refine ih (L.filter (fun x => !(decide (x = a))))
        (nodup_tail' hln)
        (filter_nodup' _ hLn) ?_
      intro x hx
      refine List.mem_filter.mpr ⟨hsub x (List.mem_cons_of_mem _ hx), ?_⟩
      rw [decide_eq_false (fun he => nodup_head' hln x hx he.symm)]
      rfl
    show t.length + 1 ≤ L.length
    omega

theorem nodup_append_singleton {α : Type} {a : α} :
    ∀ {l : List α}, a ∉ l → l.Nodup → (l ++ [a]).Nodup := by
  intro l
  induction l with
  | nil =>
    intro _ _
    exact List.Pairwise.cons (fun y hy => nomatch hy) List.Pairwise.nil
  | cons x t ih =>
    intro hna hn
    refine List.Pairwise.cons ?_ (ih
      (fun hm => hna (List.mem_cons_of_mem _ hm)) (nodup_tail' hn))
    intro y hy
    rcases List.mem_append.mp hy with hyt | hya
    · exact nodup_head' hn y hyt
    · have : y = a := List.mem_singleton.mp hya
      subst this
      exact fun he => hna (he ▸ List.mem_cons_self)

/-! ## 2. The requirement language contains every ordered bounded pair,
without duplicates -/

theorem allPairs_mem_bound :
    ∀ (n : Nat) (q : Nat × Nat), q ∈ allPairs n →
      q.1 < q.2 ∧ q.2 < n := by
  intro n
  induction n with
  | zero => intro q hq; exact nomatch hq
  | succ m ih =>
    intro q hq
    rcases List.mem_append.mp hq with hin | hnew
    · obtain ⟨h1, h2⟩ := ih q hin
      exact ⟨h1, Nat.lt_succ_of_lt h2⟩
    · obtain ⟨i, hi, hiq⟩ := List.mem_map.mp hnew
      subst hiq
      exact ⟨List.mem_range.mp hi, Nat.lt_succ_self m⟩

theorem mem_allPairs :
    ∀ (n : Nat) (q : Nat × Nat), q.1 < q.2 → q.2 < n →
      q ∈ allPairs n := by
  intro n
  induction n with
  | zero => intro q _ h2; exact nomatch h2
  | succ m ih =>
    intro q h1 h2
    rcases Nat.lt_or_ge q.2 m with hlt | hge
    · exact List.mem_append.mpr (Or.inl (ih q h1 hlt))
    · have h2m : q.2 = m := Nat.le_antisymm (Nat.le_of_lt_succ h2) hge
      refine List.mem_append.mpr (Or.inr ?_)
      refine List.mem_map.mpr ⟨q.1, List.mem_range.mpr (h2m ▸ h1), ?_⟩
      obtain ⟨a, b⟩ := q
      simp only at h2m
      rw [h2m]

theorem nodup_map_of_inj {α : Type} {g : Nat → α} :
    ∀ (l : List Nat), l.Nodup →
      (∀ i ∈ l, ∀ j ∈ l, g i = g j → i = j) → (l.map g).Nodup := by
  intro l
  induction l with
  | nil => intro _ _; exact List.Pairwise.nil
  | cons x t ih =>
    intro hn hinj
    refine List.Pairwise.cons ?_ (ih (nodup_tail' hn)
      (fun i hi j hj he =>
        hinj i (List.mem_cons_of_mem _ hi) j
          (List.mem_cons_of_mem _ hj) he))
    intro y hy he
    obtain ⟨i, hi, hie⟩ := List.mem_map.mp hy
    have : x = i := hinj x (List.mem_cons_self) i
      (List.mem_cons_of_mem _ hi) (hie ▸ he)
    exact nodup_head' hn i hi this

theorem range_nodup' : ∀ n : Nat, (List.range n).Nodup := by
  intro n
  induction n with
  | zero => exact List.Pairwise.nil
  | succ m ih =>
    rw [List.range_succ]
    exact nodup_append_singleton
      (fun hm => Nat.lt_irrefl m (List.mem_range.mp hm)) ih

theorem nodup_append_disjoint {α : Type} :
    ∀ {l1 l2 : List α}, l1.Nodup → l2.Nodup →
      (∀ x ∈ l1, x ∉ l2) → (l1 ++ l2).Nodup := by
  intro l1
  induction l1 with
  | nil => intro l2 _ h2 _; exact h2
  | cons x t ih =>
    intro l2 h1 h2 hdisj
    refine List.Pairwise.cons ?_ (ih (nodup_tail' h1) h2
      (fun y hy => hdisj y (List.mem_cons_of_mem _ hy)))
    intro y hy
    rcases List.mem_append.mp hy with hyt | hy2
    · exact nodup_head' h1 y hyt
    · exact fun he => hdisj x (List.mem_cons_self) (he ▸ hy2)

theorem allPairs_nodup : ∀ n : Nat, (allPairs n).Nodup := by
  intro n
  induction n with
  | zero => exact List.Pairwise.nil
  | succ m ih =>
    show (allPairs m ++ (List.range m).map (fun i => (i, m))).Nodup
    refine nodup_append_disjoint ih ?_ ?_
    · exact nodup_map_of_inj _ (range_nodup' m)
        (fun i _ j _ he => congrArg Prod.fst he)
    · intro q hq hmem
      obtain ⟨i, _, hie⟩ := List.mem_map.mp hmem
      have h2 := (allPairs_mem_bound m q hq).2
      rw [← hie] at h2
      exact Nat.lt_irrefl m h2

/-! ## 3. The round, and what one round provably does -/

/-- One accepted separation round: the challenged target and the
response delta. -/
structure Round where
  target : Nat × Nat
  response : List Item

/-- A closed run: each round imposes a FRESH target and responds with
a delta admitting NO fresh datum.  The two side conditions mirror the
engine's asserted invariants; that each exported round satisfies them
is the computational residual, stated in the module header. -/
inductive ClosedRun : Regime → List Round → Regime → Prop where
  | nil : ∀ r, ClosedRun r [] r
  | cons : ∀ (r : Regime) (rd : Round) (mid t : Regime)
      (rds : List Round),
      rd.target ∉ r.reqs →
      Item.newDatum ∉ rd.response →
      respond r rd.target.1 rd.target.2 rd.response = some mid →
      ClosedRun mid rds t →
      ClosedRun r (rd :: rds) t

theorem applyItem_data_eq {r s : Regime} {it : Item}
    (hne : it ≠ Item.newDatum) (h : applyItem r it = some s) :
    s.data = r.data := by
  cases it with
  | newDatum => exact absurd rfl hne
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
  | newRuleAll f =>
    simp only [applyItem] at h
    split at h
    · injection h with h
      subst h
      rfl
    · exact nomatch h

theorem applyDelta_data_eq {δ : List Item} :
    ∀ {r s : Regime}, Item.newDatum ∉ δ → applyDelta r δ = some s →
      s.data = r.data := by
  induction δ with
  | nil =>
    intro r s _ h
    injection h with h
    subst h
    rfl
  | cons it rest ih =>
    intro r s hnd h
    rw [applyDelta_cons] at h
    cases happ : applyItem r it with
    | none =>
      rw [happ] at h
      exact nomatch h
    | some r1 =>
      rw [happ] at h
      have hne : it ≠ Item.newDatum :=
        fun he => hnd (he ▸ List.mem_cons_self)
      have hrest : Item.newDatum ∉ rest :=
        fun hm => hnd (List.mem_cons_of_mem _ hm)
      exact (ih hrest h).trans (applyItem_data_eq hne happ)

/-- A successful round is a guarded imposition followed by the delta:
the target was ordered and bounded, and the requirement store after
the round is exactly the deduplicating insertion of the target. -/
theorem respond_anatomy {r s : Regime} {i j : Nat} {δ : List Item}
    (h : respond r i j δ = some s) :
    i < j ∧ j < r.data ∧ s.reqs = insertNew r.reqs (i, j) ∧
    applyDelta { r with reqs := insertNew r.reqs (i, j) } δ = some s := by
  by_cases hg : i < j ∧ j < r.data
  · have hstep : stepE r (.impose i j)
        = some { r with reqs := insertNew r.reqs (i, j) } := by
      show (if i < j ∧ j < r.data then _ else _) = _
      rw [if_pos hg]
    unfold respond at h
    rw [hstep] at h
    have h' : applyDelta { r with reqs := insertNew r.reqs (i, j) } δ
        = some s := h
    exact ⟨hg.1, hg.2, applyDelta_reqs h', h'⟩
  · have hstep : stepE r (.impose i j) = none := by
      show (if i < j ∧ j < r.data then _ else _) = _
      rw [if_neg hg]
    unfold respond at h
    rw [hstep] at h
    have h' : (none : Option Regime) = some s := h
    exact nomatch h'

/-- **One round grows the requirement count by exactly one** — the
strict-growth hypothesis of the counting laws, at the transition
system. -/
theorem round_reqs_succ {r s : Regime} {i j : Nat} {δ : List Item}
    (hfresh : (i, j) ∉ r.reqs) (h : respond r i j δ = some s) :
    s.reqs.length = r.reqs.length + 1 := by
  obtain ⟨_, _, hreqs, _⟩ := respond_anatomy h
  rw [hreqs, insertNew_of_not_mem hfresh, List.length_append]
  rfl

/-- **A datum-fixed round fixes the datum count** — the fixed-carrier
hypothesis of the counting laws, at the transition system. -/
theorem round_data_eq {r s : Regime} {i j : Nat} {δ : List Item}
    (hnd : Item.newDatum ∉ δ) (h : respond r i j δ = some s) :
    s.data = r.data := by
  obtain ⟨_, _, _, happ⟩ := respond_anatomy h
  exact applyDelta_data_eq
    (r := { r with reqs := insertNew r.reqs (i, j) }) hnd happ

/-! ## 4. The run-level invariants -/

theorem closedRun_data_eq {r t : Regime} {rds : List Round}
    (h : ClosedRun r rds t) : t.data = r.data := by
  induction h with
  | nil => rfl
  | cons r rd mid t rds _ hnd hresp _ ih =>
    exact ih.trans (round_data_eq hnd hresp)

theorem closedRun_reqs_length {r t : Regime} {rds : List Round}
    (h : ClosedRun r rds t) :
    t.reqs.length = r.reqs.length + rds.length := by
  induction h with
  | nil => rfl
  | cons r rd mid t rds hfresh _ hresp _ ih =>
    rw [ih, round_reqs_succ hfresh hresp]
    show r.reqs.length + 1 + rds.length = r.reqs.length + (rds.length + 1)
    omega

theorem closedRun_reqs_nodup {r t : Regime} {rds : List Round}
    (h : ClosedRun r rds t) (hn : r.reqs.Nodup) : t.reqs.Nodup := by
  induction h with
  | nil => exact hn
  | cons r rd mid t rds hfresh _ hresp _ ih =>
    refine ih ?_
    obtain ⟨_, _, hreqs, _⟩ := respond_anatomy hresp
    rw [hreqs, insertNew_of_not_mem hfresh]
    exact nodup_append_singleton hfresh hn

theorem closedRun_reqs_wf {r t : Regime} {rds : List Round}
    (h : ClosedRun r rds t)
    (hwf : ∀ q ∈ r.reqs, q.1 < q.2 ∧ q.2 < r.data) :
    ∀ q ∈ t.reqs, q.1 < q.2 ∧ q.2 < t.data := by
  induction h with
  | nil => exact hwf
  | cons r rd mid t rds _ hnd hresp _ ih =>
    refine ih ?_
    obtain ⟨h1, h2, hreqs, _⟩ := respond_anatomy hresp
    have hmid : mid.data = r.data := round_data_eq hnd hresp
    intro q hq
    rw [hreqs] at hq
    rcases mem_insertNew.mp hq with hin | he
    · obtain ⟨ha, hb⟩ := hwf q hin
      exact ⟨ha, hmid ▸ hb⟩
    · subst he
      exact ⟨h1, hmid ▸ h2⟩

/-! ## 5. R8: the round bound, discharged -/

/-- **R8.**  A closed run makes at most `n * (n - 1) / 2` rounds over
its starting requirement store — stated division-free, the form
`allPairs_length` takes.  The hypotheses of `strict_bounded_length`
and `no_supply_round_bound` are here proved of the transition system:
exact unit growth (`round_reqs_succ`), datum fixity (`round_data_eq`),
and the bound through the requirement language
(`nodup_subset_length` into `allPairs`). -/
theorem closedRun_round_bound {r t : Regime} {rds : List Round}
    (h : ClosedRun r rds t) (hn : r.reqs.Nodup)
    (hwf : ∀ q ∈ r.reqs, q.1 < q.2 ∧ q.2 < r.data) :
    2 * (r.reqs.length + rds.length) ≤ r.data * (r.data - 1) := by
  have hlen := closedRun_reqs_length h
  have hdata := closedRun_data_eq h
  have hnod := closedRun_reqs_nodup h hn
  have htwf := closedRun_reqs_wf h hwf
  have hsub : ∀ q ∈ t.reqs, q ∈ allPairs r.data := by
    intro q hq
    obtain ⟨h1, h2⟩ := htwf q hq
    exact mem_allPairs r.data q h1 (hdata ▸ h2)
  have hcount : t.reqs.length ≤ (allPairs r.data).length :=
    nodup_subset_length t.reqs (allPairs r.data) hnod
      (allPairs_nodup r.data) hsub
  have hAP := allPairs_length r.data
  omega

/-- The paper's instantiation: from an empty requirement store,
`2 * rounds ≤ n * (n - 1)`. -/
theorem closedRun_round_bound_from_empty {r t : Regime}
    {rds : List Round} (h : ClosedRun r rds t) (he : r.reqs = []) :
    2 * rds.length ≤ r.data * (r.data - 1) := by
  have hb := closedRun_round_bound h
    (he ▸ List.Pairwise.nil)
    (fun q hq => absurd hq (he ▸ fun h => nomatch h))
  rw [he] at hb
  simp only [List.length_nil, Nat.zero_add] at hb
  exact hb

end Derivation
