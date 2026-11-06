import SecondIndex.Index

/-!
# Two countermodels, and the headline conjunction

This file is this rung's own object.  It exhibits two regimes and three
histories of the sealed grammar reconstructed in `Kernel.lean`, and reads
the first-demand index of `Index.lean` off them.

The first countermodel answers the question whether the index is a
function of the regime a prefix reaches: two histories from the empty
base reach ONE AND THE SAME regime with different first counts, so no
function of the regime returns the index.  This is the rung's entry in
the census of the seed's challenge five, at the row for succession, and
it is a negative entry.

The second countermodel answers the question whether a demand, once it
stands, stands thereafter: it does not.  A four-event history from the
empty base carries a demand at the prefix of length two and carries none
at the prefix of length four, because the admission of a judgment
instance separates the pair the stake labels apart, which HONOURS the
label.  So the first count is not the onset of a monotone property, and
the phrase "the first demand" is not the phrase "the demand from then
on".

Both are executable countermodels: every step is closed by kernel
computation over concrete regimes.  Neither is a statement about any
grammar but this one.

AuthorityEffect: None.
-/

namespace SecondIndex
namespace Countermodel

open SecondIndex.Sealed
open SecondIndex.Inherited
open SecondIndex.Index

/-! ## 1. The regimes and histories exhibited -/

/-- One datum admitted and nothing else. -/
def oneDatum : Regime := ⟨1, [], [], [], []⟩

/-- Two data admitted and nothing else.  No judgment form, so no
well-formed context, so the two data are not separable. -/
def twoData : Regime := ⟨2, [], [], [], []⟩

/-- Two data, one judgment form of arity one, and one admitted instance
naming the first datum.  The context with one hole separates the pair. -/
def separated : Regime := ⟨2, [1], [(0, [0])], [], []⟩

/-- Two datum admissions. -/
def historyA : List Event := [.admitDatum, .admitDatum]

/-- One supply, then the same two datum admissions.  The supply changes no
state, so this history reaches the regime `historyA` reaches, one count
later. -/
def historyB : List Event := [.supply 0, .admitDatum, .admitDatum]

/-- Two datum admissions, a form admission, an instance admission. -/
def ceaseHistory : List Event :=
  [.admitDatum, .admitDatum, .admitForm 1, .admitInst 0 [0]]

/-- **shared_regime_of_two_histories.**  The two histories reach one and
the same regime from the empty base.
AT THE LEVEL OF A DEFINITION: kernel computation over concrete
regimes. -/
theorem shared_regime_of_two_histories :
    replayE historyA genesis = some twoData ∧
      replayE historyB genesis = some twoData := by
  constructor <;> decide

/-! ## 2. Where a demand stands and where it does not -/

/-- The pair of held data is a demand under the stake that labels every
distinct pair apart: the regime admits no judgment form, so no context is
well formed, so the pair is not separable and the apart label is not
honoured.  Through the previous rung's pinned theorem. -/
theorem twoData_demand : Demand allApart twoData 0 1 :=
  apart_demand_of_no_forms allApart twoData rfl 0 1 (by decide) (by decide)
    (by decide)

theorem twoData_has_demand : HasDemand allApart twoData :=
  ⟨0, 1, twoData_demand⟩

/-- The context of one hole derives the first datum and not the second,
so the pair is separable at `separated`. -/
theorem separated_separates : separable separated 0 1 :=
  ⟨⟨0, [none]⟩, by decide, by decide⟩

/-- At `separated` the apart label is honoured, and the regime holds no
other pair, so no demand stands there under that stake. -/
theorem separated_has_no_demand : ¬ HasDemand allApart separated := by
  intro hd
  obtain ⟨i, j, hij, hj, _, hno⟩ := hd
  have hj2 : j < 2 := hj
  have hi0 : i = 0 := by omega
  have hj1 : j = 1 := by omega
  subst hi0
  subst hj1
  have hlab : allApart.label 0 1 = Label.apart := by decide
  rw [hlab] at hno
  exact hno separated_separates

/-! ## 3. The first counts of the three histories -/

/-- A prefix that reaches a regime holding at most one datum carries no
demand, whatever the stake.  The shape every quiet case below takes. -/
theorem no_demand_at_small_prefix (S : Stake) (h : List Event)
    (base : Regime) (m : Nat) (s : Regime) (hs : stateAt h base m = some s)
    (hsmall : s.data ≤ 1) (r : Regime) (hr : stateAt h base m = some r) :
    ¬ HasDemand S r := by
  have heq : some s = some r := by rw [← hs]; exact hr
  have hrs : r = s := (Option.some.inj heq).symm
  rw [hrs]
  exact no_demand_of_data_le_one S s hsmall

/-- **index_of_historyA.**  Two datum admissions from the empty base: the
first count is two. -/
theorem index_of_historyA : IsFirstDemand allApart genesis historyA 2 := by
  refine ⟨⟨twoData, by decide, twoData_has_demand⟩, ?_⟩
  intro m hm r hr
  have hcase : m = 0 ∨ m = 1 := by omega
  rcases hcase with h' | h' <;> subst h'
  · exact no_demand_at_small_prefix allApart historyA genesis 0 genesis
      (by decide) (by decide) r hr
  · exact no_demand_at_small_prefix allApart historyA genesis 1 oneDatum
      (by decide) (by decide) r hr

/-- **index_of_historyB.**  One supply and then the same two admissions:
the first count is three.  The supply is demand-inert, so it moves the
count without moving the regime. -/
theorem index_of_historyB : IsFirstDemand allApart genesis historyB 3 := by
  refine ⟨⟨twoData, by decide, twoData_has_demand⟩, ?_⟩
  intro m hm r hr
  have hcase : m = 0 ∨ m = 1 ∨ m = 2 := by omega
  rcases hcase with h' | h' | h' <;> subst h'
  · exact no_demand_at_small_prefix allApart historyB genesis 0 genesis
      (by decide) (by decide) r hr
  · exact no_demand_at_small_prefix allApart historyB genesis 1 genesis
      (by decide) (by decide) r hr
  · exact no_demand_at_small_prefix allApart historyB genesis 2 oneDatum
      (by decide) (by decide) r hr

/-- **index_of_ceaseHistory.**  The first count of the ceasing history is
two, the same count as `historyA`, of which it is an extension. -/
theorem index_of_ceaseHistory :
    IsFirstDemand allApart genesis ceaseHistory 2 := by
  refine ⟨⟨twoData, by decide, twoData_has_demand⟩, ?_⟩
  intro m hm r hr
  have hcase : m = 0 ∨ m = 1 := by omega
  rcases hcase with h' | h' <;> subst h'
  · exact no_demand_at_small_prefix allApart ceaseHistory genesis 0 genesis
      (by decide) (by decide) r hr
  · exact no_demand_at_small_prefix allApart ceaseHistory genesis 1 oneDatum
      (by decide) (by decide) r hr

/-! ## 4. The first countermodel: the index is not read off the state -/

/-- **index_is_not_a_function_of_the_reached_regime.**  In the sealed
grammar reconstructed here, extended by a declared two-sided stake: two
histories from the empty base reach one and the same regime and have
different first counts.  The counts are two and three. -/
theorem index_is_not_a_function_of_the_reached_regime :
    ∃ (h₁ h₂ : List Event) (r : Regime) (k₁ k₂ : Nat),
      replayE h₁ genesis = some r ∧ replayE h₂ genesis = some r ∧
        IsFirstDemand allApart genesis h₁ k₁ ∧
        IsFirstDemand allApart genesis h₂ k₂ ∧ k₁ ≠ k₂ :=
  ⟨historyA, historyB, twoData, 2, 3, by decide, by decide,
    index_of_historyA, index_of_historyB, by decide⟩

/-- **no_state_function_gives_the_index.**  The same fact in its negative
form: there is NO function from regimes to numbers that returns the first
count of every history reaching that regime from the empty base, under
the stake that labels every distinct pair apart.

This is the rung's census entry for succession.  It says that the count
of accepted events is not definable from the state's own observables --
not that it is undefinable from the state together with something else,
and not that some other notion of succession is undefinable.  The scope
is this grammar, this base, this stake, and the reading of the index
fixed in `Index.lean`. -/
theorem no_state_function_gives_the_index :
    ¬ ∃ f : Regime → Nat, ∀ (h : List Event) (r : Regime) (k : Nat),
        replayE h genesis = some r → IsFirstDemand allApart genesis h k →
        f r = k := by
  intro hex
  obtain ⟨f, hf⟩ := hex
  have h2 : f twoData = 2 :=
    hf historyA twoData 2 (by decide) index_of_historyA
  have h3 : f twoData = 3 :=
    hf historyB twoData 3 (by decide) index_of_historyB
  omega

/-! ## 5. The second countermodel: a demand can cease -/

/-- The event that ends the demand is an instance admission, which is not
one of the three demand-inert kinds.
AT THE LEVEL OF A DEFINITION: no constructor of `InertEvent` has an
instance admission in its conclusion. -/
theorem the_ceasing_event_is_not_inert : ¬ InertEvent (.admitInst 0 [0]) := by
  intro hinert
  cases hinert

/-- **demand_can_cease.**  In the sealed grammar reconstructed here,
extended by a declared two-sided stake: a demand standing at one prefix
need not stand at a longer one.  The exhibited history carries a demand
at the prefix of length two and carries none at the prefix of length
four.

What ends it is not a withdrawal of the stake, which is declared once and
never moves, but a change in what the regime OBSERVES: the admitted
instance separates the pair, and separability is exactly what honours an
apart label.  A regime carrying no demand is therefore reached after one
carrying a demand, so the index marks a first occurrence and not a
threshold. -/
theorem demand_can_cease :
    ∃ (h : List Event) (r₂ r₄ : Regime),
      stateAt h genesis 2 = some r₂ ∧ HasDemand allApart r₂ ∧
        stateAt h genesis 4 = some r₄ ∧ ¬ HasDemand allApart r₄ :=
  ⟨ceaseHistory, twoData, separated, by decide, twoData_has_demand,
    by decide, separated_has_no_demand⟩

/-! ## 6. The conjunction -/

/-- **first_demand_index.**  In the sealed grammar reconstructed in
`Kernel.lean`, extended by the declared two-sided stake reconstructed in
`Inherited.lean`, and in no other grammar:

1. at most one count is a first count, for one base, one history and one
   stake;
2. from a well-formed base, a first count that is a successor consumes
   last an event that is not demand-inert;
3. from the empty base, no count below two is a first count;
4. under the stake that labels every pair free, no count is a first
   count;
5. no function of the regime a prefix reaches returns the first count;
6. a demand standing at one prefix need not stand at a longer one.

SCOPE OF THE STATEMENT.  Clauses one to four are about every base,
history and stake in the stated range; clauses five and six are
countermodels, and they refute the corresponding positive statements
rather than establishing a general negative beyond the range quantified.
Nothing here asserts that a first count EXISTS: existence is conditional
on a decision for the demand predicate, is stated that way in
`Index.lean`, and the decision is a named leftover executed nowhere.  The
scope excludes every other grammar. -/
theorem first_demand_index :
    (∀ (S : Stake) (base : Regime) (h : List Event) (k k' : Nat),
        IsFirstDemand S base h k → IsFirstDemand S base h k' → k = k')
  ∧ (∀ (S : Stake) (base : Regime), base.wf → ∀ (h : List Event) (k : Nat)
        (hk : k < h.length), IsFirstDemand S base h (k + 1) → ¬ InertEvent h[k])
  ∧ (∀ (S : Stake) (h : List Event) (k : Nat),
        IsFirstDemand S genesis h k → 2 ≤ k)
  ∧ (∀ (base : Regime) (h : List Event) (k : Nat),
        ¬ IsFirstDemand freeStake base h k)
  ∧ (¬ ∃ f : Regime → Nat, ∀ (h : List Event) (r : Regime) (k : Nat),
        replayE h genesis = some r → IsFirstDemand allApart genesis h k →
        f r = k)
  ∧ (∃ (h : List Event) (r₂ r₄ : Regime),
        stateAt h genesis 2 = some r₂ ∧ HasDemand allApart r₂ ∧
          stateAt h genesis 4 = some r₄ ∧ ¬ HasDemand allApart r₄) :=
  ⟨fun S base h k k' hk hk' => first_demand_unique S base h k k' hk hk',
   fun S base hwf h k hk hfirst =>
     first_demand_follows_a_changing_event S base hwf h k hk hfirst,
   fun S h k hfirst => no_index_below_two_from_the_empty_base S h k hfirst,
   fun base h k => free_stake_has_no_index base h k,
   no_state_function_gives_the_index,
   demand_can_cease⟩

end Countermodel
end SecondIndex
