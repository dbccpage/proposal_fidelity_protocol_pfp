import SecondIndex.Inherited

/-!
# The first-demand index over an arbitrary run

This file is this rung's own object.  What it consumes is the
reconstruction in `Kernel.lean` and `Inherited.lean`, each carrying its
own pin note; nothing in this file is reconstructed.

The previous rung's first track proved that a run built only from the
three demand-inert kinds carries no new demand.  The three remaining
kinds -- the admission of a datum, of a judgment instance, and of a
uniform rule -- do change demand sets, so a run of the whole grammar
needs an index over HISTORIES rather than a statement about one regime.
That index is defined here.

Three readings are kept apart throughout:

1. a PREFIX of a history, which is a list of events;
2. the regime a prefix REACHES, which is an `Option Regime`, because a
   prefix carrying an admission the grammar refuses reaches none;
3. the COUNT a prefix consumes, which is a natural number and is the
   index this file is about.

`IsFirstDemand` is a proposition, not a function.  Whether a regime
carries a demand is, in the sealed grammar, a statement over contexts,
and this rung does not decide it: the existence theorem below carries the
decidability as an explicit hypothesis, and the finite enumeration of
well-formed contexts that would discharge that hypothesis is a named
leftover, executed nowhere.

AuthorityEffect: None.
-/

namespace SecondIndex
namespace Index

open SecondIndex.Sealed
open SecondIndex.Inherited

/-! ## 1. Prefixes and the regimes they reach -/

/-- The regime the prefix of `h` of length `k` reaches from `base`.  For
`k` above the length of `h` this is the regime the whole history reaches;
the index statements below never need that case, and none of them assumes
it away. -/
def stateAt (h : List Event) (base : Regime) (k : Nat) : Option Regime :=
  replayE (h.take k) base

/-- **stateAt_zero.**  The count zero names the base itself.
AT THE LEVEL OF A DEFINITION: the prefix of length zero is the empty
list, which replays to the base by `rfl`. -/
theorem stateAt_zero (h : List Event) (base : Regime) :
    stateAt h base 0 = some base := rfl

/-- **stateAt_full.**  The count equal to the length of the history names
the regime the whole history reaches. -/
theorem stateAt_full (h : List Event) (base : Regime) :
    stateAt h base h.length = replayE h base := by
  unfold stateAt
  rw [List.take_length]

/-- **replayE_singleton.**  A one-event history replays by one step. -/
theorem replayE_singleton (e : Event) (base : Regime) :
    replayE [e] base = stepE base e := by
  rw [replayE_cons]
  cases stepE base e <;> rfl

/-- **stateAt_succ.**  A count one larger reaches what the smaller count
reaches, stepped by the one event the larger count consumes last.  This
is the statement that makes the index an index over a run rather than a
family of unrelated regimes; it uses the sealed compositionality of
replay, reconstructed in `Kernel.lean`. -/
theorem stateAt_succ (h : List Event) (base : Regime) (k : Nat)
    (hk : k < h.length) :
    stateAt h base (k + 1) = (stateAt h base k).bind (fun r => stepE r h[k]) := by
  unfold stateAt
  rw [List.take_add_one, List.getElem?_eq_getElem hk, Option.toList_some,
    replayE_append]

/-! ## 2. Carrying a demand, and being the first count that does -/

/-- A regime CARRIES A DEMAND under a stake when some ordered pair of its
held data is a demand.  Read off the stake and the regime's own
observables and off nothing else. -/
def HasDemand (S : Stake) (r : Regime) : Prop :=
  ∃ i j, Demand S r i j

/-- `k` is a FIRST COUNT for the base, the history and the stake when the
prefix of length `k` reaches a regime carrying a demand and no shorter
prefix reaches one.  A proposition, not a function: nothing here asserts
that such a `k` exists, and `first_demand_unique` is what makes the
phrase "the first count" legitimate when one does. -/
def IsFirstDemand (S : Stake) (base : Regime) (h : List Event) (k : Nat) : Prop :=
  (∃ r, stateAt h base k = some r ∧ HasDemand S r) ∧
    (∀ m, m < k → ∀ r, stateAt h base m = some r → ¬ HasDemand S r)

/-- **quiet_before_the_index.**  Every prefix shorter than a first count
reaches a regime carrying no demand.
AT THE LEVEL OF A DEFINITION: the second conjunct of `IsFirstDemand`,
projected. -/
theorem quiet_before_the_index (S : Stake) (base : Regime) (h : List Event)
    (k m : Nat) (hfirst : IsFirstDemand S base h k) (hm : m < k) (r : Regime)
    (hr : stateAt h base m = some r) : ¬ HasDemand S r :=
  hfirst.2 m hm r hr

/-- **first_demand_unique.**  For one base, one history and one stake, at
most one count is a first count.  No decidability hypothesis, no
hypothesis on the events, no hypothesis on the base.  This is what
licenses the phrase "the first-demand index". -/
theorem first_demand_unique (S : Stake) (base : Regime) (h : List Event)
    (k k' : Nat) (hk : IsFirstDemand S base h k)
    (hk' : IsFirstDemand S base h k') : k = k' := by
  by_cases hlt : k < k'
  · obtain ⟨r, hr, hd⟩ := hk.1
    exact absurd hd (hk'.2 k hlt r hr)
  · by_cases hgt : k' < k
    · obtain ⟨r, hr, hd⟩ := hk'.1
      exact absurd hd (hk.2 k' hgt r hr)
    · omega

/-- **first_demand_zero_iff_base_carries_one.**  The count zero is the
first count exactly when the base itself carries a demand. -/
theorem first_demand_zero_iff_base_carries_one (S : Stake) (base : Regime)
    (h : List Event) : IsFirstDemand S base h 0 ↔ HasDemand S base := by
  constructor
  · intro hfirst
    obtain ⟨r, hr, hd⟩ := hfirst.1
    rw [stateAt_zero] at hr
    rw [← Option.some.inj hr] at hd
    exact hd
  · intro hd
    exact ⟨⟨base, stateAt_zero h base, hd⟩,
      fun m hm => absurd hm (Nat.not_lt_zero m)⟩

/-- **free_stake_has_no_index.**  Under the stake that labels every pair
free, no count is a first count, at any base and along any history.
AT THE LEVEL OF A DEFINITION: the pinned theorem of the previous rung
says no regime whatever carries a demand under that stake. -/
theorem free_stake_has_no_index (base : Regime) (h : List Event) (k : Nat) :
    ¬ IsFirstDemand freeStake base h k := by
  intro hfirst
  obtain ⟨r, _, i, j, hd⟩ := hfirst.1
  exact free_stake_no_demand r i j hd

/-! ## 3. Well-formedness along an arbitrary run

The previous rung proved that a well-formed regime stays well formed
under a step of one of the three demand-inert kinds.  The index needs the
same for the other three kinds, because the regime a prefix reaches must
be known well formed before the inertia theorem can be applied to the
step that follows it. -/

/-- The regime a datum admission reaches. -/
def addDatum (r : Regime) : Regime := { r with data := r.data + 1 }

theorem stepE_admitDatum (r : Regime) :
    stepE r .admitDatum = some (addDatum r) := rfl

/-- The regime an instance admission reaches. -/
def addInst (r : Regime) (f : Nat) (args : List Nat) : Regime :=
  { r with insts := insertNew r.insts (f, args) }

theorem stepE_admitInst (r : Regime) (f : Nat) (args : List Nat)
    (h1 : f < r.forms.length) (h2 : args.length = r.forms.getD f 0)
    (h3 : ∀ x ∈ args, x < r.data) :
    stepE r (.admitInst f args) = some (addInst r f args) := by
  show (if f < r.forms.length ∧ args.length = r.forms.getD f 0 ∧
      (∀ x ∈ args, x < r.data) then some (addInst r f args) else none)
    = some (addInst r f args)
  rw [if_pos ⟨h1, h2, h3⟩]

/-- The regime a uniform-rule admission reaches. -/
def addRule (r : Regime) (f : Nat) : Regime :=
  { r with rules := insertNew r.rules f }

theorem stepE_admitRuleAll (r : Regime) (f : Nat) (h : f < r.forms.length) :
    stepE r (.admitRuleAll f) = some (addRule r f) := by
  show (if f < r.forms.length then some (addRule r f) else none)
    = some (addRule r f)
  rw [if_pos h]

/-- Admitting a datum to a well-formed regime leaves it well formed: every
bound well-formedness carries is a strict bound below the data count, and
the data count only grows. -/
theorem wf_addDatum (r : Regime) (hwf : r.wf) : (addDatum r).wf := by
  obtain ⟨hi, hr, hq, hf⟩ := hwf
  refine ⟨?_, hr, ?_, hf⟩
  · intro p hp
    have hp' : p ∈ r.insts := hp
    obtain ⟨h1, h2, h3⟩ := hi p hp'
    exact ⟨h1, h2, fun a ha => Nat.lt_succ_of_lt (h3 a ha)⟩
  · intro q hq'
    have hq'' : q ∈ r.reqs := hq'
    exact ⟨(hq q hq'').1, Nat.lt_succ_of_lt (hq q hq'').2⟩

/-- Admitting a judgment instance the grammar accepts leaves a well-formed
regime well formed: the accepted instance is exactly one satisfying the
three conditions well-formedness asks of an instance. -/
theorem wf_addInst (r : Regime) (hwf : r.wf) (f : Nat) (args : List Nat)
    (h1 : f < r.forms.length) (h2 : args.length = r.forms.getD f 0)
    (h3 : ∀ x ∈ args, x < r.data) : (addInst r f args).wf := by
  obtain ⟨hi, hr, hq, hf⟩ := hwf
  refine ⟨?_, hr, hq, hf⟩
  intro p hp
  have hp' : p ∈ insertNew r.insts (f, args) := hp
  rw [mem_insertNew] at hp'
  rcases hp' with h | h
  · exact hi p h
  · subst h
    exact ⟨h1, h2, h3⟩

/-- Admitting a uniform rule for an admitted form leaves a well-formed
regime well formed. -/
theorem wf_addRule (r : Regime) (hwf : r.wf) (f : Nat)
    (h : f < r.forms.length) : (addRule r f).wf := by
  obtain ⟨hi, hr, hq, hf⟩ := hwf
  refine ⟨hi, ?_, hq, hf⟩
  intro g hg
  have hg' : g ∈ insertNew r.rules f := hg
  rw [mem_insertNew] at hg'
  rcases hg' with h' | h'
  · exact hr g h'
  · subst h'
    exact h

/-- **wf_step_any.**  In the sealed grammar reconstructed here, every one
of the six event kinds carries a well-formed regime to a well-formed
regime, whenever the grammar admits the step at all.  The three
demand-inert kinds go through the previous rung's lemmas, reconstructed
under a pin; the other three are proved here. -/
theorem wf_step_any (r r' : Regime) (hwf : r.wf) (e : Event)
    (hstep : stepE r e = some r') : r'.wf := by
  cases e with
  | supply t =>
      rw [supply_no_op r t] at hstep
      rw [← Option.some.inj hstep]; exact hwf
  | admitDatum =>
      rw [stepE_admitDatum r] at hstep
      rw [← Option.some.inj hstep]; exact wf_addDatum r hwf
  | admitForm a =>
      by_cases ha : 1 ≤ a
      · rw [stepE_admitForm r a ha] at hstep
        rw [← Option.some.inj hstep]; exact wf_addForm r hwf a ha
      · exfalso
        have hn : stepE r (.admitForm a) = none := by
          show (if 1 ≤ a then _ else none) = none
          rw [if_neg ha]
        rw [hn] at hstep
        exact absurd hstep (by simp)
  | admitInst f args =>
      by_cases hg : f < r.forms.length ∧ args.length = r.forms.getD f 0 ∧
          (∀ x ∈ args, x < r.data)
      · rw [stepE_admitInst r f args hg.1 hg.2.1 hg.2.2] at hstep
        rw [← Option.some.inj hstep]
        exact wf_addInst r hwf f args hg.1 hg.2.1 hg.2.2
      · exfalso
        have hn : stepE r (.admitInst f args) = none := by
          show (if f < r.forms.length ∧ args.length = r.forms.getD f 0 ∧
            (∀ x ∈ args, x < r.data) then _ else none) = none
          rw [if_neg hg]
        rw [hn] at hstep
        exact absurd hstep (by simp)
  | admitRuleAll f =>
      by_cases hg : f < r.forms.length
      · rw [stepE_admitRuleAll r f hg] at hstep
        rw [← Option.some.inj hstep]; exact wf_addRule r hwf f hg
      · exfalso
        have hn : stepE r (.admitRuleAll f) = none := by
          show (if f < r.forms.length then _ else none) = none
          rw [if_neg hg]
        rw [hn] at hstep
        exact absurd hstep (by simp)
  | impose i j =>
      by_cases hg : i < j ∧ j < r.data
      · rw [stepE_impose r i j hg.1 hg.2] at hstep
        rw [← Option.some.inj hstep]
        exact wf_addReq r hwf i j hg.1 hg.2
      · exfalso
        have hn : stepE r (.impose i j) = none := by
          show (if i < j ∧ j < r.data then _ else none) = none
          rw [if_neg hg]
        rw [hn] at hstep
        exact absurd hstep (by simp)

/-- **wf_replayE.**  A whole history of any events carries a well-formed
base to a well-formed regime. -/
theorem wf_replayE : ∀ (h : List Event) (base r : Regime),
    base.wf → replayE h base = some r → r.wf
  | [], base, r, hwf, hr => by
      rw [replayE_nil base] at hr
      rw [← Option.some.inj hr]; exact hwf
  | e :: rest, base, r, hwf, hr => by
      rw [replayE_cons e rest base] at hr
      cases hse : stepE base e with
      | none => rw [hse] at hr; exact absurd hr (by simp)
      | some mid =>
          rw [hse] at hr
          exact wf_replayE rest mid r (wf_step_any base mid hwf e hse)
            (by simpa using hr)

/-- **wf_stateAt.**  Every prefix of every history from a well-formed base
reaches a well-formed regime. -/
theorem wf_stateAt (base : Regime) (hwf : base.wf) (h : List Event) (k : Nat)
    (r : Regime) (hk : stateAt h base k = some r) : r.wf :=
  wf_replayE (h.take k) base r hwf hk

/-! ## 4. What the index counts last -/

/-- **first_demand_follows_a_changing_event.**  In the sealed grammar
reconstructed here, extended by a declared two-sided stake, and in no
other grammar: from a well-formed base, when a first count is a
successor, the event that count consumes last is NOT one of the three
kinds the previous rung proved demand-inert.

The argument is the contrapositive of that rung's step theorem.  Were the
last event inert, the regime the shorter prefix reaches would carry the
same demands as the regime the longer one reaches, so the shorter prefix
would already carry a demand, and the longer count would not be first.

WHAT THIS DOES NOT SAY.  It does not say that the event is a datum, an
instance or a uniform-rule admission BY NAME; it says the event is not
inert, and the three inert kinds are exactly the ones named in the
previous rung's `InertEvent`.  It does not say a first count exists.  It
does not say the event CAUSED the demand: a demand is read off the state,
and the statement is about the order of two prefixes and nothing else. -/
theorem first_demand_follows_a_changing_event (S : Stake) (base : Regime)
    (hwf : base.wf) (h : List Event) (k : Nat) (hk : k < h.length)
    (hfirst : IsFirstDemand S base h (k + 1)) : ¬ InertEvent h[k] := by
  intro hinert
  obtain ⟨⟨r, hr, hd⟩, hmin⟩ := hfirst
  rw [stateAt_succ h base k hk] at hr
  cases hmid : stateAt h base k with
  | none => rw [hmid] at hr; exact absurd hr (by simp)
  | some mid =>
      rw [hmid] at hr
      have hstep : stepE mid h[k] = some r := by simpa using hr
      have hwfmid : mid.wf := wf_stateAt base hwf h k mid hmid
      obtain ⟨i, j, hij⟩ := hd
      exact (hmin k (Nat.lt_succ_self k) mid hmid)
        ⟨i, j, (demands_step_inert S mid r hwfmid h[k] hinert hstep i j).mp hij⟩

/-- **inert_run_carries_no_index.**  From a well-formed base carrying no
demand, a run built only from the three demand-inert kinds has no first
count at all.  A restatement of the previous rung's run theorem in the
vocabulary of the index. -/
theorem inert_run_carries_no_index (S : Stake) (base : Regime) (hwf : base.wf)
    (h : List Event) (hall : ∀ e ∈ h, InertEvent e)
    (hquiet : ¬ HasDemand S base) (k : Nat) : ¬ IsFirstDemand S base h k := by
  intro hfirst
  obtain ⟨r, hr, i, j, hd⟩ := hfirst.1
  have hsub : ∀ e ∈ h.take k, InertEvent e :=
    fun e he => hall e (List.mem_of_mem_take he)
  exact hquiet ⟨i, j,
    (demands_replay_inert S (h.take k) base r hsub hwf hr i j).mp hd⟩

/-! ## 5. How far down the index can be -/

/-- **demand_needs_two_data.**  A demand is at an ordered pair of held
data, so a regime carrying one holds at least two. -/
theorem demand_needs_two_data (S : Stake) (r : Regime) (i j : Nat)
    (h : Demand S r i j) : 2 ≤ r.data := by
  obtain ⟨hij, hj, _, _⟩ := h
  omega

/-- **no_demand_of_data_le_one.**  A regime holding at most one datum
carries no demand, under any stake. -/
theorem no_demand_of_data_le_one (S : Stake) (r : Regime) (hr : r.data ≤ 1) :
    ¬ HasDemand S r := by
  intro hd
  obtain ⟨i, j, hij⟩ := hd
  have := demand_needs_two_data S r i j hij
  omega

/-- **data_of_step.**  One event admits at most one datum. -/
theorem data_of_step (r r' : Regime) (e : Event) (h : stepE r e = some r') :
    r'.data = r.data ∨ r'.data = r.data + 1 := by
  cases e with
  | supply t =>
      left; rw [supply_no_op r t] at h; rw [← Option.some.inj h]
  | admitDatum =>
      right; rw [stepE_admitDatum r] at h; rw [← Option.some.inj h]; rfl
  | admitForm a =>
      left
      by_cases ha : 1 ≤ a
      · rw [stepE_admitForm r a ha] at h; rw [← Option.some.inj h]; rfl
      · exfalso
        have hn : stepE r (.admitForm a) = none := by
          show (if 1 ≤ a then _ else none) = none
          rw [if_neg ha]
        rw [hn] at h
        exact absurd h (by simp)
  | admitInst f args =>
      left
      by_cases hg : f < r.forms.length ∧ args.length = r.forms.getD f 0 ∧
          (∀ x ∈ args, x < r.data)
      · rw [stepE_admitInst r f args hg.1 hg.2.1 hg.2.2] at h
        rw [← Option.some.inj h]; rfl
      · exfalso
        have hn : stepE r (.admitInst f args) = none := by
          show (if f < r.forms.length ∧ args.length = r.forms.getD f 0 ∧
            (∀ x ∈ args, x < r.data) then _ else none) = none
          rw [if_neg hg]
        rw [hn] at h
        exact absurd h (by simp)
  | admitRuleAll f =>
      left
      by_cases hg : f < r.forms.length
      · rw [stepE_admitRuleAll r f hg] at h; rw [← Option.some.inj h]; rfl
      · exfalso
        have hn : stepE r (.admitRuleAll f) = none := by
          show (if f < r.forms.length then _ else none) = none
          rw [if_neg hg]
        rw [hn] at h
        exact absurd h (by simp)
  | impose i j =>
      left
      by_cases hg : i < j ∧ j < r.data
      · rw [stepE_impose r i j hg.1 hg.2] at h; rw [← Option.some.inj h]; rfl
      · exfalso
        have hn : stepE r (.impose i j) = none := by
          show (if i < j ∧ j < r.data then _ else none) = none
          rw [if_neg hg]
        rw [hn] at h
        exact absurd h (by simp)

/-- **data_le_step.**  One event leaves the data count at most one
larger. -/
theorem data_le_step (r r' : Regime) (e : Event) (h : stepE r e = some r') :
    r'.data ≤ r.data + 1 := by
  rcases data_of_step r r' e h with h' | h' <;> omega

/-- **data_le_replay.**  A history of `n` events reaches a regime holding
at most `n` data more than its base. -/
theorem data_le_replay : ∀ (h : List Event) (base r : Regime),
    replayE h base = some r → r.data ≤ base.data + h.length
  | [], base, r, hr => by
      rw [replayE_nil base] at hr
      rw [← Option.some.inj hr]
      simp
  | e :: rest, base, r, hr => by
      rw [replayE_cons e rest base] at hr
      cases hse : stepE base e with
      | none => rw [hse] at hr; exact absurd hr (by simp)
      | some mid =>
          rw [hse] at hr
          have hmid : mid.data ≤ base.data + 1 := data_le_step base mid e hse
          have hrest : r.data ≤ mid.data + rest.length :=
            data_le_replay rest mid r (by simpa using hr)
          have hlen : (e :: rest).length = rest.length + 1 := by simp
          omega

/-- **data_le_stateAt.**  The prefix of length `k` reaches a regime
holding at most `k` data more than the base. -/
theorem data_le_stateAt (h : List Event) (base r : Regime) (k : Nat)
    (hk : stateAt h base k = some r) : r.data ≤ base.data + k := by
  have hbound := data_le_replay (h.take k) base r hk
  have hlen : (h.take k).length ≤ k := by
    rw [List.length_take]
    exact Nat.min_le_left _ _
  omega

/-- **no_index_below_two_from_the_empty_base.**  In the sealed grammar
reconstructed here, extended by a declared two-sided stake: from the
regime with nothing admitted, no count below two is a first count, for
any stake and any history whatever.  Two events must be consumed before a
pair of held data exists at all, and a demand is at a pair of held data.

The bound is on the COUNT and not on the demand: it says nothing about
whether a first count exists, and nothing about any base other than the
empty one. -/
theorem no_index_below_two_from_the_empty_base (S : Stake) (h : List Event)
    (k : Nat) (hfirst : IsFirstDemand S genesis h k) : 2 ≤ k := by
  obtain ⟨r, hr, i, j, hij⟩ := hfirst.1
  have h2 := demand_needs_two_data S r i j hij
  have hle : r.data ≤ 0 + k := data_le_stateAt h genesis r k hr
  omega

/-! ## 6. Existence, and the decision it needs -/

/-- Least witness by upward search from a point known to be clear.  The
search is bounded by the witness itself, and the predicate must be
decidable: there is no classical extraction here, and the package's axiom
report shows none. -/
theorem least_witness_from (p : Nat → Prop) [DecidablePred p] :
    ∀ (n base : Nat), p (base + n) → (∀ k, k < base → ¬ p k) →
      ∃ m, p m ∧ ∀ k, k < m → ¬ p k
  | 0, base, hp, hlt => ⟨base, hp, hlt⟩
  | (n + 1), base, hp, hlt => by
      by_cases hb : p base
      · exact ⟨base, hb, hlt⟩
      · refine least_witness_from p n (base + 1) ?_ ?_
        · have hsum : base + 1 + n = base + (n + 1) := by omega
          rw [hsum]; exact hp
        · intro k hk
          have hcase : k < base ∨ k = base := by omega
          rcases hcase with h' | h'
          · exact hlt k h'
          · rw [h']; exact hb

/-- **least_witness.**  A decidable predicate with a witness has a least
witness. -/
theorem least_witness (p : Nat → Prop) [DecidablePred p] (n : Nat) (hp : p n) :
    ∃ m, p m ∧ ∀ k, k < m → ¬ p k :=
  least_witness_from p n 0 (by simpa using hp)
    (fun k hk => absurd hk (Nat.not_lt_zero k))

/-- **first_demand_exists_when_a_demand_is_decidable.**  In the sealed
grammar reconstructed here, extended by a declared two-sided stake: if
some prefix of a history reaches a regime carrying a demand, and whether
a regime carries a demand is DECIDABLE, then a first count exists.

THE HYPOTHESIS IS NOT DISCHARGED HERE.  Whether a regime carries a demand
is, in the sealed grammar, a statement over contexts: apart is honoured
by separability, which is stated existentially over the context type.
The well-formed contexts of a fixed regime are finitely many, so the
statement is decidable in principle; building that enumeration and
proving it complete is a named, priced leftover of this rung, executed
nowhere.  Until it is built, existence is conditional, and the ledger
records it as conditional. -/
theorem first_demand_exists_when_a_demand_is_decidable (S : Stake)
    (base : Regime) (h : List Event)
    (dec : ∀ r : Regime, Decidable (HasDemand S r)) (k : Nat) (r : Regime)
    (hk : stateAt h base k = some r) (hd : HasDemand S r) :
    ∃ m, IsFirstDemand S base h m := by
  have dP : DecidablePred
      (fun m => ∃ s, stateAt h base m = some s ∧ HasDemand S s) := by
    intro m
    cases hm : stateAt h base m with
    | none =>
        refine isFalse ?_
        intro hex
        obtain ⟨s, hs, _⟩ := hex
        rw [hm] at hs
        exact absurd hs (by simp)
    | some s =>
        cases dec s with
        | isTrue ht => exact isTrue ⟨s, hm, ht⟩
        | isFalse hf =>
            refine isFalse ?_
            intro hex
            obtain ⟨s', hs', hd'⟩ := hex
            rw [hm] at hs'
            rw [← Option.some.inj hs'] at hd'
            exact hf hd'
  obtain ⟨m, hm, hmin⟩ :=
    least_witness (fun m => ∃ s, stateAt h base m = some s ∧ HasDemand S s) k
      ⟨r, hk, hd⟩
  refine ⟨m, hm, ?_⟩
  intro n hn s hs hds
  exact hmin n hn ⟨s, hs, hds⟩

end Index
end SecondIndex
