import Derivation.Basic

/-!
# The mention lemma, and the two irrelevance corollaries (R1, R2, R3)

Residuals R1, R2 and R3 of `paper.md` section 12 are kind (a): certified
exhaustively in Python by
`test_pruned_cost2_contains_every_valid_full_delta`, cross-checked
against the *unpruned* candidate space, with the Lean absent.  They are
what license the cost-2 enumeration to prune, so they sit under the
minimality result rather than beside it.

They are one argument, not three.

**The mention lemma (R3).**  `derivable` is membership in `insts` or
coverage by a rule on the form.  A context has at least one hole
(`wfCtx` requires `none ∈ c.slots`), so `plug c d` always *mentions* `d`
at that hole.  Hence an instance that does not mention `d` can never be
`plug c d`.  Adding such instances therefore changes nothing about
whether `d` and `d'` are collapsed.

**The corollaries (R1, R2).**  A fresh datum or a fresh form enlarges
the space of well-formed contexts, so these are not instances of R3 —
new contexts genuinely appear.  But every new context mentions something
no instance mentions, so *both* plugs fail membership, and the iff in
`collapsed` holds for the same reason on both sides.  A context that
reaches outside the regime does not separate; it only fails twice.

The hypotheses of R1 and R2 are not extra assumptions: they are conjuncts
of `Regime.wf`.  A well-formed regime already has every instance argument
below `data` and every instance form below `forms.length`.
-/

namespace Derivation

/-! ## The hole makes the datum mentioned -/

/-- Every plugged instance mentions its datum, because every
well-formed context has a hole and the hole receives it. -/
theorem mem_plug_of_hole {c : Ctx} (h : none ∈ c.slots) (d : Nat) :
    d ∈ (plug c d).2 := by
  simp only [plug]
  exact List.mem_map.mpr ⟨none, h, rfl⟩

/-- An instance whose arguments are all below `n` is not a plug of a
datum that is not below `n`. -/
theorem not_mem_of_arg_out_of_range {r : Regime}
    (hwf : ∀ p ∈ r.insts, ∀ a ∈ p.2, a < r.data)
    {i : Inst} {a : Nat} (ha : a ∈ i.2) (hbig : ¬ a < r.data) :
    i ∉ r.insts := fun hmem => hbig (hwf i hmem a ha)

/-- A slot list that is not everywhere admissible has a slot naming a
datum out of range.  Proved by induction so that the witness is
extracted constructively; `by_contra` is a Mathlib tactic and this
development imports only core. -/
theorem exists_out_of_range_slot (n : Nat) :
    ∀ l : List (Option Nat), ¬ (∀ s ∈ l, slotOk n s) →
      ∃ x, some x ∈ l ∧ ¬ x < n := by
  intro l
  induction l with
  | nil => intro h; exact absurd (fun s hs => absurd hs List.not_mem_nil) h
  | cons a as ih =>
    intro h
    by_cases hall : ∀ s ∈ as, slotOk n s
    · cases a with
      | none =>
        refine absurd (fun s hs => ?_) h
        rcases List.mem_cons.mp hs with rfl | hs'
        · trivial
        · exact hall s hs'
      | some x =>
        by_cases hx : x < n
        · refine absurd (fun s hs => ?_) h
          rcases List.mem_cons.mp hs with rfl | hs'
          · exact hx
          · exact hall s hs'
        · exact ⟨x, List.mem_cons_self, hx⟩
    · obtain ⟨x, hx, hxn⟩ := ih hall
      exact ⟨x, List.mem_cons_of_mem _ hx, hxn⟩

/-! ## R3 — the mention lemma -/

/-- **R3.**  Adding instances that mention neither target datum leaves
the collapse of that pair exactly as it was.

This is the statement the pruning uses: an instance-only delta can only
change the target pair's profiles by mentioning a target datum. -/
theorem collapsed_append_unmentioning
    (r : Regime) (new : List Inst) (d d' : Nat)
    (hd : ∀ p ∈ new, d ∉ p.2) (hd' : ∀ p ∈ new, d' ∉ p.2) :
    collapsed { r with insts := r.insts ++ new } d d' ↔ collapsed r d d' := by
  have key : ∀ (e : Nat) (c : Ctx), none ∈ c.slots →
      (∀ p ∈ new, e ∉ p.2) →
      (derivable { r with insts := r.insts ++ new } (plug c e)
        ↔ derivable r (plug c e)) := by
    intro e c hhole hnew
    constructor
    · rintro (hm | hr)
      · rcases List.mem_append.mp hm with h | h
        · exact Or.inl h
        · exact absurd (mem_plug_of_hole hhole e) (hnew _ h)
      · exact Or.inr hr
    · rintro (hm | hr)
      · exact Or.inl (List.mem_append.mpr (Or.inl hm))
      · exact Or.inr hr
  constructor
  · intro h c hc
    have hhole : none ∈ c.slots := hc.2.2.1
    rw [← key d c hhole hd, ← key d' c hhole hd']
    exact h c hc
  · intro h c hc
    have hhole : none ∈ c.slots := hc.2.2.1
    rw [key d c hhole hd, key d' c hhole hd']
    exact h c hc

/-! ## R1 — a fresh datum is irrelevant -/

/-- **R1.**  Admitting a fresh datum that no instance mentions leaves the
collapse of every existing pair exactly as it was.

The new contexts are real — a slot may now name the fresh datum — but
such a context mentions something no instance mentions, so neither plug
is derivable by membership and the iff holds by failing on both sides. -/
theorem collapsed_fresh_datum (r : Regime) (d d' : Nat)
    (hwf : ∀ p ∈ r.insts, ∀ a ∈ p.2, a < r.data) :
    collapsed { r with data := r.data + 1 } d d' ↔ collapsed r d d' := by
  constructor
  · intro h c hc
    refine h c ⟨hc.1, hc.2.1, hc.2.2.1, ?_⟩
    intro s hs
    have := hc.2.2.2 s hs
    cases s with
    | none => trivial
    | some x => exact Nat.lt_succ_of_lt this
  · intro h c hc
    by_cases hin : ∀ s ∈ c.slots, slotOk r.data s
    · exact h c ⟨hc.1, hc.2.1, hc.2.2.1, hin⟩
    · -- some slot names the fresh datum: neither plug is an instance
      have hout := exists_out_of_range_slot r.data c.slots hin
      obtain ⟨x, hx, hxbig⟩ := hout
      have hmem : ∀ e : Nat, x ∈ (plug c e).2 := by
        intro e
        simp only [plug]
        exact List.mem_map.mpr ⟨some x, hx, rfl⟩
      have hnot : ∀ e : Nat, plug c e ∉ r.insts := fun e =>
        not_mem_of_arg_out_of_range hwf (hmem e) hxbig
      constructor
      · rintro (hm | hr)
        · exact absurd hm (hnot d)
        · exact Or.inr hr
      · rintro (hm | hr)
        · exact absurd hm (hnot d')
        · exact Or.inr hr

/-! ## R2 — a fresh form is irrelevant -/

theorem getD_append_left {α : Type} (l m : List α) (i : Nat) (dflt : α)
    (h : i < l.length) : (l ++ m).getD i dflt = l.getD i dflt := by
  simp only [List.getD]
  rw [List.getElem?_append_left h]

/-- **R2.**  Admitting a fresh form that no instance uses and no rule
names leaves the collapse of every pair exactly as it was.

Contexts of the new form genuinely appear.  None of them separates: its
form index is beyond every instance and beyond every rule, so both plugs
fail derivability for the same reason. -/
theorem collapsed_fresh_form (r : Regime) (d d' : Nat) (k : Nat)
    (hinst : ∀ p ∈ r.insts, p.1 < r.forms.length)
    (hrule : ∀ f ∈ r.rules, f < r.forms.length) :
    collapsed { r with forms := r.forms ++ [k] } d d' ↔ collapsed r d d' := by
  constructor
  · intro h c hc
    refine h c ⟨?_, ?_, hc.2.2.1, hc.2.2.2⟩
    · exact Nat.lt_of_lt_of_le hc.1 (by simp)
    · rw [getD_append_left _ _ _ _ hc.1]; exact hc.2.1
  · intro h c hc
    by_cases hold : c.form < r.forms.length
    · refine h c ⟨hold, ?_, hc.2.2.1, hc.2.2.2⟩
      have := hc.2.1
      rwa [getD_append_left _ _ _ _ hold] at this
    · -- the context uses the fresh form: nothing is derivable either side
      have hnot : ∀ e : Nat, ¬ derivable r (plug c e) := by
        intro e hd
        cases hd with
        | inl hm => exact hold (hinst _ hm)
        | inr hr => exact hold (hrule _ hr)
      exact ⟨fun hx => absurd hx (hnot d), fun hx => absurd hx (hnot d')⟩

/-! ## What these three do NOT say

Each lemma is an `iff` about `collapsed` for a pair that already exists.
None of them says a fresh datum or form is useless — a delta that
MENTIONS a target datum is exactly how separation is achieved, and R3 is
the precise statement of that boundary.  What is proved is only that the
unmentioning part of a candidate cannot contribute, which is what the
enumeration needs in order to prune it. -/

end Derivation
