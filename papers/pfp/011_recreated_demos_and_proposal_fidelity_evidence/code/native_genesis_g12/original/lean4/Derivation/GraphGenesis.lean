import Derivation.Attachment

/-!
# Graph genesis: locating the true boundary of carrier growth

Where can a NEW occurrence, a new asserted difference, a new
retained difference, or a new protected demand come from?

The passage kernel answers negatively and exactly.  Its internal
response family — the represented next-event family
`PrimitivePassage.nextFamilyP`, whose members are the same-level
repairs (`refineCol`) and the structure-creating columns (`addCol`),
each carried by its own funding event — moves only the declared
observation and the budget.  The four graph stores (`occ`,
`asserted`, `wit`, `prot`) are invariant under every trace drawn
from that fragment (Part 1).  Carrier growth therefore never arrives
through the represented response family: it arrives through the supply
events of an external driver, or through the declared one-edge grammar
`Attachment.upFamily` (Part 2).  Whether `nextFamilyP` can *demand*
that grammar is settled in Part 3, by countermodel and a general
invariance theorem: it cannot.  Other response-family semantics remain
open.

Scope discipline.

* Part 1 is proved for every state and every event of the declared
  event type, and for every finite trace over the internal fragment.
  Nothing is claimed about events outside the declared type.
* Part 2's `ProposalRecord` is a PROPOSAL.  It names one branch and
  carries its membership proof in the complete family; that branch is
  not asserted canonical or unique, and other branches remain.  It
  also carries an embedding with its retraction, a
  freshness certificate, the preservation obligations, the new
  pair's provenance, and a declared cost — and no license, no
  execution, no activation.  Transport is proved exactly for the
  supply fragment the grammar uses (`Attachment.act_up_comm`);
  commutation for the full observation calculus is not claimed.
* Part 3 is a countermodel plus a general in-carrier resolution
  theorem.  It proves that the obstruction does not force the
  carrier-changing lift, and nothing stronger: the growth demand
  remains a separately declared premise.
-/

namespace GraphGenesis

open PrimitivePassage Attachment

/-! ## Part 1 — the negative theorems

The observation-side events touch the observation and the budget,
and nothing else.  Stated field by field over the whole state
record: what is NOT listed here is exactly `obs` and `budget`. -/

/-- **Refinement is observation-only.**  At every state, for every
declared column and every point, the same-level repair leaves the
occurrence carrier, the asserted store, the retained store, the
protected store, the refusal record, the license, and the terminal
flag untouched.  Only `obs` and `budget` are outside this list. -/
theorem refineCol_only_obs (s : PState) (v : List Nat) (p : Nat) :
    ((step s (.refineCol v p)).occ = s.occ) ∧
    ((step s (.refineCol v p)).asserted = s.asserted) ∧
    ((step s (.refineCol v p)).wit = s.wit) ∧
    ((step s (.refineCol v p)).prot = s.prot) ∧
    ((step s (.refineCol v p)).refusals = s.refusals) ∧
    ((step s (.refineCol v p)).licensed = s.licensed) ∧
    ((step s (.refineCol v p)).halted = s.halted) := by
  simp only [step]
  repeat' split
  all_goals exact ⟨rfl, rfl, rfl, rfl, rfl, rfl, rfl⟩

/-- **Structure creation is observation-only.**  Same statement for
the column-creating event: the created structure lands in the
declared observation and is paid for out of the budget; no graph
store, no refusal record, no license, no terminal flag moves. -/
theorem addCol_only_obs (s : PState) (c : List Nat) :
    ((step s (.addCol c)).occ = s.occ) ∧
    ((step s (.addCol c)).asserted = s.asserted) ∧
    ((step s (.addCol c)).wit = s.wit) ∧
    ((step s (.addCol c)).prot = s.prot) ∧
    ((step s (.addCol c)).refusals = s.refusals) ∧
    ((step s (.addCol c)).licensed = s.licensed) ∧
    ((step s (.addCol c)).halted = s.halted) := by
  simp only [step]
  repeat' split
  all_goals exact ⟨rfl, rfl, rfl, rfl, rfl, rfl, rfl⟩

/-! ### The proposal generators range over the existing carrier

`PrimitivePassage.extensionProposals` is the real generator of
created columns and `PrimitivePassage.repairFamily` is the real
generator of same-level moves; `PrimitivePassage.nextFamilyP` is
built from exactly these two by `PrimitivePassage.responseMenu` and
`PrimitivePassage.obstructedPairs`.  Every position either generator
mentions is already represented. -/

/-- **Created columns mention only existing positions.**  Every
column in the extension-proposal family of any pair at any state is
a set of positions strictly below the current carrier length. -/
theorem extensionProposals_range_over_existing (s : PState)
    (i j : Nat) :
    ∀ c ∈ extensionProposals s i j, ∀ x ∈ c, x < s.occ.length := by
  intro c hc x hx
  have hmem := (List.mem_filter.mp hc).1
  obtain ⟨q, hq, heq⟩ := List.mem_map.mp hmem
  have hqx : x = q := by
    rw [← heq] at hx
    exact List.mem_singleton.mp hx
  rw [hqx]
  exact List.mem_range.mp hq

/-- **Same-level repairs mention only existing positions.**  The
point a repair adds to a declared column is strictly below the
current carrier length.  (Nothing is claimed about the points
already inside the refined column: those entered the observation
earlier, and their own bound is the earlier state's.) -/
theorem repairFamily_range_over_existing (s : PState) (i j : Nat) :
    ∀ m ∈ repairFamily s i j, m.2 < s.occ.length := by
  intro m hm
  have hmem := (List.mem_filter.mp hm).1
  unfold responseMenu at hmem
  cases hobs : s.obs with
  | none =>
      rw [hobs] at hmem
      cases hmem
  | some cols =>
      rw [hobs] at hmem
      obtain ⟨v, _, hmm⟩ := List.mem_flatMap.mp hmem
      obtain ⟨q, hq, heq⟩ := List.mem_map.mp hmm
      rw [← heq]
      exact List.mem_range.mp hq

/-- The positions an event newly mentions, as a proposition on the
pre-state: the point of a refinement and every point of a created
column must already be represented.  Supply events and control
events are unconstrained here (they are not part of the internal
response family). -/
def MentionsOnlyExisting (s : PState) : PEvent → Prop
  | .refineCol _ p => p < s.occ.length
  | .addCol c => ∀ x ∈ c, x < s.occ.length
  | _ => True

/-- The shape of every block the represented next-event family
emits: a single same-level repair of some obstructed protected pair,
or a funding event followed by one created column for such a pair.
There is no third shape. -/
theorem nextFamilyP_block_shape (s : PState) (b : List PEvent)
    (hb : b ∈ nextFamilyP s) :
    (∃ r ∈ obstructedPairs s, ∃ m ∈ repairFamily s r.1 r.2,
        b = [PEvent.refineCol m.1 m.2]) ∨
    (∃ r ∈ obstructedPairs s, ∃ c ∈ extensionProposals s r.1 r.2,
        b = [PEvent.setBudget 1, PEvent.addCol c]) := by
  unfold nextFamilyP at hb
  obtain ⟨r, hr, hb'⟩ := List.mem_flatMap.mp hb
  rcases List.mem_append.mp hb' with hl | hl
  · obtain ⟨m, hm, heq⟩ := List.mem_map.mp hl
    exact Or.inl ⟨r, hr, m, hm, heq.symm⟩
  · obtain ⟨c, hc, heq⟩ := List.mem_map.mp hl
    exact Or.inr ⟨r, hr, c, hc, heq.symm⟩

/-- **The internal response family ranges over the existing
carrier.**  Every event of every block the family emits mentions
only positions that are already represented — the family cannot even
name a position outside the current carrier, let alone create
one. -/
theorem nextFamilyP_range_over_existing (s : PState) :
    ∀ b ∈ nextFamilyP s, ∀ e ∈ b, MentionsOnlyExisting s e := by
  intro b hb e he
  rcases nextFamilyP_block_shape s b hb with
    ⟨r, _, m, hm, heq⟩ | ⟨r, _, c, hc, heq⟩
  · subst heq
    rcases List.mem_cons.mp he with h | h
    · subst h
      exact repairFamily_range_over_existing s r.1 r.2 m hm
    · cases h
  · subst heq
    rcases List.mem_cons.mp he with h | h
    · subst h
      exact True.intro
    · rcases List.mem_cons.mp h with h | h
      · subst h
        exact extensionProposals_range_over_existing s r.1 r.2 c hc
      · cases h

/-! ### The internal fragment, as a decidable predicate on events -/

/-- The internal (observation-changing and record-only) fragment:
true exactly on the two response events, the observation
declaration, and the refusal record; false on every supply event and
on every control event. -/
def IsInternal : PEvent → Bool
  | .refineCol _ _ => true
  | .addCol _ => true
  | .declareObs => true
  | .refuse _ _ => true
  | .admitOcc _ => false
  | .assertWit _ _ => false
  | .admitWit _ _ => false
  | .protect _ _ => false
  | .setBudget _ => false
  | .setLicense _ => false
  | .halt => false

/-- The predicate is exactly as declared, on every constructor. -/
theorem IsInternal_exact :
    (∀ v p, IsInternal (.refineCol v p) = true) ∧
    (∀ c, IsInternal (.addCol c) = true) ∧
    (IsInternal .declareObs = true) ∧
    (∀ i j, IsInternal (.refuse i j) = true) ∧
    (∀ t, IsInternal (.admitOcc t) = false) ∧
    (∀ i j, IsInternal (.assertWit i j) = false) ∧
    (∀ i j, IsInternal (.admitWit i j) = false) ∧
    (∀ i j, IsInternal (.protect i j) = false) ∧
    (∀ n, IsInternal (.setBudget n) = false) ∧
    (∀ b, IsInternal (.setLicense b) = false) ∧
    (IsInternal .halt = false) :=
  ⟨fun _ _ => rfl, fun _ => rfl, rfl, fun _ _ => rfl, fun _ => rfl,
   fun _ _ => rfl, fun _ _ => rfl, fun _ _ => rfl, fun _ => rfl,
   fun _ => rfl, rfl⟩

/-- The internal fragment together with the funding event that the
represented family prefixes to a created column.  Funding moves the
budget only, so it is graph-inert as well; it is listed separately
because it is NOT internal — it is a control event. -/
def IsResponseEvent : PEvent → Bool
  | .refineCol _ _ => true
  | .addCol _ => true
  | .declareObs => true
  | .refuse _ _ => true
  | .setBudget _ => true
  | .admitOcc _ => false
  | .assertWit _ _ => false
  | .admitWit _ _ => false
  | .protect _ _ => false
  | .setLicense _ => false
  | .halt => false

theorem internal_is_response (e : PEvent) (h : IsInternal e = true) :
    IsResponseEvent e = true := by
  cases e <;> first | rfl | exact Bool.noConfusion h

/-- The four graph stores of the target state agree with those of
the source state: the occurrence carrier, the asserted store, the
retained store, and the protected store. -/
def GraphStoresFixed (s t : PState) : Prop :=
  t.occ = s.occ ∧ t.asserted = s.asserted ∧ t.wit = s.wit
    ∧ t.prot = s.prot

/-- One response event (internal or funding) fixes all four graph
stores, at every state. -/
theorem response_step_fixes_graph (s : PState) (e : PEvent)
    (h : IsResponseEvent e = true) : GraphStoresFixed s (step s e) := by
  cases e <;>
    first
      | (simp only [step]
         repeat' split
         all_goals exact ⟨rfl, rfl, rfl, rfl⟩)
      | exact Bool.noConfusion h

theorem internal_step_fixes_graph (s : PState) (e : PEvent)
    (h : IsInternal e = true) : GraphStoresFixed s (step s e) :=
  response_step_fixes_graph s e (internal_is_response e h)

/-- Trace-level closure of any graph-inert single-step predicate. -/
theorem replay_fixes_graph_of_all (P : PEvent → Bool)
    (hP : ∀ (s : PState) (e : PEvent), P e = true →
      GraphStoresFixed s (step s e)) (h : List PEvent) :
    ∀ (s : PState), (∀ e ∈ h, P e = true) →
      GraphStoresFixed s (replayP h s) := by
  induction h with
  | nil => intro s _; exact ⟨rfl, rfl, rfl, rfl⟩
  | cons e rest ih =>
      intro s hall
      obtain ⟨a1, a2, a3, a4⟩ := hP s e (hall e List.mem_cons_self)
      obtain ⟨b1, b2, b3, b4⟩ :=
        ih (step s e) (fun x hx => hall x (List.mem_cons_of_mem e hx))
      exact ⟨b1.trans a1, b2.trans a2, b3.trans a3, b4.trans a4⟩

/-- **The internal family cannot grow the carrier.**  Replaying ANY
finite list of events drawn only from the internal fragment leaves
the occurrence carrier, the asserted store, the retained store, and
the protected store exactly as they were — at every state, halted or
live, observed or pre-observational. -/
theorem internal_family_cannot_grow_carrier (h : List PEvent)
    (s : PState) (hint : ∀ e ∈ h, IsInternal e = true) :
    GraphStoresFixed s (replayP h s) :=
  replay_fixes_graph_of_all IsInternal internal_step_fixes_graph h s
    hint

/-- The same for the funded blocks the represented family actually
emits. -/
theorem response_replay_fixes_graph (h : List PEvent) (s : PState)
    (hall : ∀ e ∈ h, IsResponseEvent e = true) :
    GraphStoresFixed s (replayP h s) :=
  replay_fixes_graph_of_all IsResponseEvent response_step_fixes_graph
    h s hall

/-- Every block of the represented next-event family consists of
response events only. -/
theorem nextFamilyP_blocks_are_responses (s : PState) :
    ∀ b ∈ nextFamilyP s, ∀ e ∈ b, IsResponseEvent e = true := by
  intro b hb e he
  rcases nextFamilyP_block_shape s b hb with
    ⟨_, _, m, _, heq⟩ | ⟨_, _, c, _, heq⟩
  · subst heq
    rcases List.mem_cons.mp he with h | h
    · subst h; rfl
    · cases h
  · subst heq
    rcases List.mem_cons.mp he with h | h
    · subst h; rfl
    · rcases List.mem_cons.mp h with h | h
      · subst h; rfl
      · cases h

/-- Executing any block of the represented family fixes all four
graph stores. -/
theorem nextFamilyP_block_fixes_graph (s : PState) (b : List PEvent)
    (hb : b ∈ nextFamilyP s) : GraphStoresFixed s (replayP b s) :=
  response_replay_fixes_graph b s
    (nextFamilyP_blocks_are_responses s b hb)

/-- **Graph growth is supplied, not generated by `nextFamilyP`.**  In one
statement, at every store-bounded live state with a represented
parent position:

* every block the internal response family emits leaves the
  occurrence carrier, the asserted store, the retained store and the
  protected store fixed — this represented response family cannot
  produce a new occurrence, a new asserted difference, a new retained
  difference, or a new protected pair; while
* the declared one-edge grammar (`Attachment.upBlock`, executed by
  the external driver) grows the carrier and each relational store
  by exactly one.

Scope: the first clause quantifies over the complete represented
family at an arbitrary state; the second is the declared grammar's
execution theorem under its own hypotheses.  Nothing is claimed
about event types outside `PrimitivePassage.PEvent`, and nothing is
claimed about which grammar an external driver *ought* to run. -/
theorem graph_growth_is_supplied (s : PState) (hwf : WFStores s)
    (hh : s.halted = false) (p : Nat) (hp : p < s.occ.length) :
    (∀ b ∈ nextFamilyP s, GraphStoresFixed s (replayP b s)) ∧
    (replayP (upBlock s p) s).occ.length = s.occ.length + 1 ∧
    (replayP (upBlock s p) s).asserted.length = s.asserted.length + 1 ∧
    (replayP (upBlock s p) s).wit.length = s.wit.length + 1 ∧
    (replayP (upBlock s p) s).prot.length = s.prot.length + 1 := by
  obtain ⟨e1, e2, e3, e4, _⟩ := up_executes s hwf hh p hp
  exact ⟨fun b hb => nextFamilyP_block_fixes_graph s b hb,
    e1, e2, e3, e4⟩

/-! ## Part 2 — one explicit sufficient represented proposal schema

If the carrier is to grow, the growth must be represented by
something the state itself can carry.  One explicit sufficient schema
is a PROPOSAL record: a member of the complete Up family together with
the obligations that make it a lawful extension of the present state.
No minimality or universal property is proved for this schema.  It
confers no authority whatsoever. -/

/-- A represented growth proposal at the state `s`.

Fields, and nothing else:

* `block` with `block_complete`: the record names one block and proves
  it is a member of the COMPLETE family `Attachment.upFamily s`; this
  is a branch-local proposal, not a canonical or unique representative;
* `embed` / `retract` with `retract_embed`: an old-position
  embedding with a retraction on the represented positions;
* `token_fresh`: the token the block supplies is not already in the
  carrier;
* `preserves_asserted` / `preserves_wit` / `preserves_prot` /
  `preserves_separated`: every old asserted, retained, and protected
  pair, and every pair separated by the declared observation,
  survives execution, transported along `embed`;
* `newPair` with `parentPos`, `freshPos` and their provenance
  proofs;
* `cost`: the declared resource demand.

There is no license field, no execution field, and no activation
field. -/
structure ProposalRecord (s : PState) where
  /-- The proposed block. -/
  block : List PEvent
  /-- Membership in the COMPLETE declared family.  The record names
  one branch but supplies no canonicality or uniqueness claim. -/
  block_complete : block ∈ upFamily s
  /-- Embedding of old positions into the extended carrier. -/
  embed : Nat → Nat
  /-- Retraction of the embedding. -/
  retract : Nat → Nat
  /-- The retraction inverts the embedding on represented positions. -/
  retract_embed : ∀ x, x < s.occ.length → retract (embed x) = x
  /-- Freshness evidence for the token the block supplies. -/
  token_fresh : ∀ t : Nat, (PEvent.admitOcc t) ∈ block → ¬ (t ∈ s.occ)
  /-- Every old asserted pair survives, transported along `embed`. -/
  preserves_asserted : ∀ pr ∈ s.asserted,
    (embed pr.1, embed pr.2) ∈ (replayP block s).asserted
  /-- Every old retained pair survives, transported along `embed`. -/
  preserves_wit : ∀ pr ∈ s.wit,
    (embed pr.1, embed pr.2) ∈ (replayP block s).wit
  /-- Every old protected pair survives, transported along `embed`. -/
  preserves_prot : ∀ pr ∈ s.prot,
    (embed pr.1, embed pr.2) ∈ (replayP block s).prot
  /-- Every pair the declared observation separates stays separated,
  transported along `embed`. -/
  preserves_separated : ∀ cols, s.obs = some cols →
    ∀ cols', (replayP block s).obs = some cols' →
      ∀ i j, sepP cols i j = true →
        sepP cols' (embed i) (embed j) = true
  /-- The pair the proposal would create. -/
  newPair : Nat × Nat
  /-- Provenance: the parent position. -/
  parentPos : Nat
  /-- Provenance: the fresh position. -/
  freshPos : Nat
  /-- The new pair is exactly parent-to-fresh. -/
  newPair_provenance : newPair = (parentPos, freshPos)
  /-- The parent is represented in the pre-state. -/
  parent_represented : parentPos < s.occ.length
  /-- The fresh position is the next position of the carrier. -/
  freshPos_is_new : freshPos = s.occ.length
  /-- The declared resource demand. -/
  cost : Nat

/-! ### The record is a PROPOSAL and carries no authority

`ProposalRecord` has no license field, no execution field, and no
activation field.  Holding one changes nothing: it records a member
of the complete family, an embedding with its retraction, a
freshness certificate, the preservation obligations, the new pair's
provenance, and a declared cost.  Execution remains the separately
gated `PrimitivePassage.step`: on a terminal state the proposed
block is inert (`proposal_confers_no_execution`), and the
observation-side events keep their own license and budget gates
(`PrimitivePassage.proposal_not_execution`,
`PrimitivePassage.budget_gates_execution`). -/

/-- **A proposal is not an execution.**  On a terminal state a
proposal record can exist, and executing its block does nothing: the
record confers no authority to move the state. -/
theorem proposal_confers_no_execution (s : PState)
    (P : ProposalRecord s) (h : s.halted = true) :
    replayP P.block s = s := by
  obtain ⟨p, _, heq⟩ := (up_iff_legal s P.block).mp P.block_complete
  rw [heq]
  exact halted_up_inert s h p

/-- The canonical proposal at a represented parent position, with
the identity embedding: on a store-bounded live state the declared
one-edge grammar keeps every old position where it was, so every
obligation is discharged.  Cost is the declared block length. -/
def upProposal (s : PState) (hwf : WFStores s) (hh : s.halted = false)
    (p : Nat) (hp : p < s.occ.length) : ProposalRecord s where
  block := upBlock s p
  block_complete := (up_iff_legal s _).mpr ⟨p, hp, rfl⟩
  embed := fun x => x
  retract := fun x => x
  retract_embed := fun _ _ => rfl
  token_fresh := by
    intro t ht
    have hteq : t = freshTok s := by
      rcases List.mem_cons.mp ht with h | h
      · exact PEvent.admitOcc.inj h
      · rcases List.mem_cons.mp h with h | h
        · exact PEvent.noConfusion h
        · rcases List.mem_cons.mp h with h | h
          · exact PEvent.noConfusion h
          · rcases List.mem_cons.mp h with h | h
            · exact PEvent.noConfusion h
            · cases h
    rw [hteq]
    exact freshTok_fresh s
  preserves_asserted := by
    intro pr hpr
    rw [up_exec_eq s hwf hh p hp]
    show pr ∈ s.asserted ++ [(p, s.occ.length)]
    exact List.mem_append.mpr (Or.inl hpr)
  preserves_wit := by
    intro pr hpr
    rw [up_exec_eq s hwf hh p hp]
    show pr ∈ s.wit ++ [(p, s.occ.length)]
    exact List.mem_append.mpr (Or.inl hpr)
  preserves_prot := by
    intro pr hpr
    rw [up_exec_eq s hwf hh p hp]
    show pr ∈ s.prot ++ [(p, s.occ.length)]
    exact List.mem_append.mpr (Or.inl hpr)
  preserves_separated := by
    intro cols hcols cols' hcols' i j hsep
    rw [up_exec_eq s hwf hh p hp] at hcols'
    have hobs : (upS4 s p).obs = s.obs := rfl
    rw [hobs, hcols] at hcols'
    have hcc : cols = cols' := Option.some.inj hcols'
    rw [← hcc]
    exact hsep
  newPair := (p, s.occ.length)
  parentPos := p
  freshPos := s.occ.length
  newPair_provenance := rfl
  parent_represented := hp
  freshPos_is_new := rfl
  cost := (upBlock s p).length

/-- The canonical proposal's execution really is the declared
extension: the new pair is retained and protected, and the carrier
grew by exactly one. -/
theorem upProposal_executes (s : PState) (hwf : WFStores s)
    (hh : s.halted = false) (p : Nat) (hp : p < s.occ.length) :
    (upProposal s hwf hh p hp).newPair
        ∈ (replayP (upProposal s hwf hh p hp).block s).wit ∧
    (upProposal s hwf hh p hp).newPair
        ∈ (replayP (upProposal s hwf hh p hp).block s).prot ∧
    (replayP (upProposal s hwf hh p hp).block s).occ.length
      = s.occ.length + 1 := by
  refine ⟨?_, ?_, (up_executes s hwf hh p hp).1⟩
  · show (p, s.occ.length) ∈ (replayP (upBlock s p) s).wit
    rw [up_exec_eq s hwf hh p hp]
    show (p, s.occ.length) ∈ s.wit ++ [(p, s.occ.length)]
    exact List.mem_append.mpr (Or.inr List.mem_cons_self)
  · show (p, s.occ.length) ∈ (replayP (upBlock s p) s).prot
    rw [up_exec_eq s hwf hh p hp]
    show (p, s.occ.length) ∈ s.prot ++ [(p, s.occ.length)]
    exact List.mem_append.mpr (Or.inr List.mem_cons_self)

/-- **Proposals transport under renaming.**  Every proposal record
at a store-bounded live state is the Up block at some represented
parent; the renamed block is a member of the renamed state's
complete family, executing it on the renamed state gives exactly the
renamed execution, and the declared cost is unchanged.

Scope: exactly the supply fragment `Attachment.act_up_comm` covers —
commutation for the full observation calculus is not claimed. -/
theorem proposal_transports {n : Nat} (σ : Renaming n) (s : PState)
    (hn : n = s.occ.length) (hwf : WFStores s) (hh : s.halted = false)
    (P : ProposalRecord s) :
    ∃ p, p < s.occ.length ∧ P.block = upBlock s p ∧
      upBlock (act σ s) (σ.f p) ∈ upFamily (act σ s) ∧
      act σ (replayP P.block s)
        = replayP (upBlock (act σ s) (σ.f p)) (act σ s) ∧
      (upBlock (act σ s) (σ.f p)).length = P.block.length := by
  obtain ⟨p, hp, heq⟩ := (up_iff_legal s P.block).mp P.block_complete
  refine ⟨p, hp, heq, ?_, ?_, ?_⟩
  · exact (upFamily_transport σ s hn p).mp (heq ▸ P.block_complete)
  · rw [heq]
    exact act_up_comm σ s hn hwf hh p hp
  · rw [heq]
    rfl

/-! ### The family retains ties: no canonical selection occurs -/

/-- The three-occurrence oriented path: the sample pre-state. -/
def tri : PState := treeAt pathPolL 2

theorem tri_wf : WFStores tri := by
  refine ⟨?_, ?_, ?_⟩ <;> decide

theorem tri_live : tri.halted = false := by decide

theorem tri_parent1 : 1 < tri.occ.length := by decide

theorem tri_parent2 : 2 < tri.occ.length := by decide

/-- The proposal at parent position 1. -/
def triProp1 : ProposalRecord tri :=
  upProposal tri tri_wf tri_live 1 tri_parent1

/-- The proposal at parent position 2. -/
def triProp2 : ProposalRecord tri :=
  upProposal tri tri_wf tri_live 2 tri_parent2

/-- **The proposal family retains equal-cost, non-isomorphic
branches.**  Two proposals at the same state, with the same declared
cost, both members of the complete family, whose executions are not
carried onto each other by any carrier bijection.  The family
records both; neither record is certified as the canonical choice. -/
theorem proposal_family_retains_ties :
    triProp1.cost = triProp2.cost ∧
    triProp1.block ≠ triProp2.block ∧
    triProp1.block ∈ upFamily tri ∧
    triProp2.block ∈ upFamily tri ∧
    (tuples4.all fun t => !(isoMatch t
        (replayP triProp1.block tri).wit
        (replayP triProp2.block tri).wit)) = true := by
  refine ⟨rfl, ?_, triProp1.block_complete, triProp2.block_complete,
    ?_⟩
  · intro hc
    have h12 : (1 : Nat) = 2 :=
      upBlock_parent_inj tri (show upBlock tri 1 = upBlock tri 2 from hc)
    exact absurd h12 (by decide)
  · exact equal_cost_non_isomorphic_extensions.2.2.2

/-! ## Part 3 — does `nextFamilyP` request the lift at an obstruction?

The four obstruction conditions are: the pair is retained, the pair
is protected, an observation IS declared, and the declared
observation does not separate the pair.  The question is whether
their conjunction can force a carrier-changing response.

The answer is NO, and it is proved twice: generally (every
obstruction with a represented, distinct, protected endpoint pair on
a licensed live state is resolved by a block of the complete
internal family, and that block fixes every graph store), and by a
concrete decided witness. -/

/-- The funded state: budget one, nothing else moved. -/
def funded (s : PState) : PState := { s with budget := 1 }

/-- **Every obstruction is resolvable inside the current carrier.**
At an obstructed, protected, represented, distinct pair on a
licensed live state, the represented family contains the funded
column block on the first endpoint; executing it removes the
obstruction, and it changes no graph store.  So the obstruction is
answered without any carrier change. -/
theorem obstruction_resolved_in_carrier (s : PState) (i j : Nat)
    (hobst : obstP s i j = true) (hij : i ≠ j)
    (hi : i < s.occ.length) (hprot : (i, j) ∈ s.prot)
    (hlic : s.licensed = true) (hh : s.halted = false) :
    [PEvent.setBudget 1, PEvent.addCol [i]] ∈ nextFamilyP s ∧
    obstP (replayP [PEvent.setBudget 1, PEvent.addCol [i]] s) i j
      = false ∧
    GraphStoresFixed s
      (replayP [PEvent.setBudget 1, PEvent.addCol [i]] s) := by
  have hmem := nextFamilyP_nonempty s i j hobst hij hi hprot
  refine ⟨hmem, ?_, nextFamilyP_block_fixes_graph s _ hmem⟩
  have hstep1 : step s (.setBudget 1) = funded s :=
    HigherStructure.pstep_budget 1 hh
  have hobstF : obstP (funded s) i j = true := hobst
  have hiF : i < (funded s).occ.length := hi
  have hprotF : (i, j) ∈ (funded s).prot := hprot
  have havail :=
    extension_always_available (funded s) i j hobstF hij hiF hprotF
  have hfil := (List.mem_filter.mp havail).2
  simp only [Bool.and_eq_true] at hfil
  cases hobs : s.obs with
  | none =>
      rw [obst_requires_observation s i j hobs] at hobst
      exact Bool.noConfusion hobst
  | some cols =>
      have hres := extension_resolves (funded s) [i] i j cols
        (show (funded s).obs = some cols from hobs) hfil.1 hfil.2
        (show (funded s).licensed = true from hlic)
        (show 0 < (funded s).budget from Nat.zero_lt_one)
        (show (funded s).halted = false from hh)
      show obstP (step (step s (.setBudget 1)) (.addCol [i])) i j
        = false
      rw [hstep1]
      exact hres

/-- The demand that the represented response family grow the
carrier, as a proposition about a state. -/
def FamilyGrowsCarrier (s : PState) : Prop :=
  ∃ b ∈ nextFamilyP s, s.occ.length < (replayP b s).occ.length

/-- **No represented response, at any state, grows the carrier.** -/
theorem family_never_grows_carrier (s : PState) :
    ¬ FamilyGrowsCarrier s := by
  intro hgrow
  obtain ⟨b, hb, hlt⟩ := hgrow
  obtain ⟨h1, _, _, _⟩ := nextFamilyP_block_fixes_graph s b hb
  rw [h1] at hlt
  exact absurd hlt (Nat.lt_irrefl _)

/-- The concrete witness state: two occurrences, one asserted,
retained, protected difference, an observation declared but empty —
so all four obstruction conditions hold at the pair `(0, 1)`. -/
def blindPair : PState :=
  { occ := [0, 1], asserted := [(0, 1)], wit := [(0, 1)],
    prot := [(0, 1)], obs := some [], budget := 0, licensed := true,
    refusals := [], halted := false }

/-- **Part 3 verdict — growth is not entailed by the represented
response semantics.**  Decided witness plus general theorem:

1. all four obstruction conditions hold at `blindPair`;
2. the complete internal response family there is exactly two funded
   column blocks — nonempty, and computed, not chosen;
3. every one of them removes the obstruction;
4. none of them changes the occurrence carrier or any relational
   store; and
5. at NO state whatsoever does the represented family grow the
   carrier.

Therefore an active obstruction is not represented by `nextFamilyP`
as a request for a carrier-changing lift.  A carrier-growing step is a
SEPARATELY
DECLARED premise (Part 2's proposal record, executed by an external
driver), not a consequence of the represented `nextFamilyP` response
semantics.

What this does NOT claim: that no other declared response family
could grow the carrier; only that the family the passage kernel
computes from the represented state cannot. -/
theorem growth_demand_not_obstruction_consequence :
    obstP blindPair 0 1 = true ∧
    nextFamilyP blindPair
      = [[PEvent.setBudget 1, PEvent.addCol [0]],
         [PEvent.setBudget 1, PEvent.addCol [1]]] ∧
    (∀ b ∈ nextFamilyP blindPair,
      obstP (replayP b blindPair) 0 1 = false) ∧
    (∀ b ∈ nextFamilyP blindPair,
      GraphStoresFixed blindPair (replayP b blindPair)) ∧
    (∀ s : PState, ¬ FamilyGrowsCarrier s) := by
  refine ⟨by decide, by decide, by decide, ?_, family_never_grows_carrier⟩
  intro b hb
  exact nextFamilyP_block_fixes_graph blindPair b hb

/-- The other half of the honest statement: the obstruction at
`blindPair` is genuinely active (not a vacuous witness) and the
carrier is genuinely unchanged after the response — the resolved
state still has exactly two occurrences. -/
theorem blindPair_resolution_keeps_carrier :
    (replayP [PEvent.setBudget 1, PEvent.addCol [0]] blindPair).occ
      = [0, 1] ∧
    (replayP [PEvent.setBudget 1, PEvent.addCol [0]] blindPair).obs
      = some [[0]] ∧
    (replayP [PEvent.setBudget 1, PEvent.addCol [0]] blindPair).wit
      = [(0, 1)] := by
  refine ⟨?_, ?_, ?_⟩ <;> decide

end GraphGenesis
