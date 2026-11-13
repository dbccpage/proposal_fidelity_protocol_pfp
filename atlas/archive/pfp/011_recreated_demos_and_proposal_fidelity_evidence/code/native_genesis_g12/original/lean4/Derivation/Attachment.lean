import Derivation.HigherStructure

/-!
# One-edge attachment: lawful policies, typed refusal, the exact Up
family, and renaming equivariance

Review-pass rebuild.  Four repairs, each with its countermodel:

1. **No silent clamping.**  A `LawfulPolicy` carries the proof that
   every chosen parent is represented; an illegal choice meets a
   TYPED REFUSAL (`attachChecked`, `AttachOutcome.refusedParent`),
   never a rewrite into some other policy (`clamp_rewrote_input`
   records what the retired clamp used to do).
2. **Occurrence identity resolved.**  `PState.occ` stores TOKENS in
   admission order; POSITIONS (indices below `occ.length`) are the
   occurrence identities used by every relational store and by
   observation columns — the sealed kernel's convention.  Token
   freshness is a separate obligation: the canonical fresh token is
   `freshTok` (one past the maximum admitted token), fresh on EVERY
   occurrence list (`freshTok_fresh`); using `occ.length` as a token
   fails on non-initial lists (`length_not_fresh_countermodel`).
3. **Registry-relative completeness, as an iff**:
   `b ∈ upFamily s ↔ LegalOneEdgeExtension s b` (`up_iff_legal`) for
   the EXACT declared one-edge grammar — canonical fresh token, one
   asserted+retained+protected parent edge.  Nothing is claimed for
   other fresh-name policies, multi-edge attachment, relational or
   observation extensions.
4. **Equivariance is a renaming action, not a length count.**  A
   positional `Renaming` acts on states and events; the Up block and
   family transport along the action (`upBlock_transport`,
   `upFamily_transport`), and replay of an Up block commutes with it
   (`act_up_comm`) — proved for the supply fragment used by the
   grammar; commutation for the full observation calculus is not
   claimed here.  The old length-equality statement survives only as
   grammar uniformity over an identical carrier
   (`upFamily_grammar_uniform`), explicitly NOT presentation
   equivalence: equal-size states with literally equal families need
   not be related by any renaming
   (`equal_size_not_renaming_related`).

Everything else — trees from every lawful policy, `V − E = 1`,
global shape not forced, orbit demonstrations — is preserved on the
repaired foundations.

Imported (declared, not derived) inputs: fresh token supply (the
canonical next numeral past the maximum), protection, observer
transport (unused here — attachment is pre-observational), budget
and activation (no funded events in supply blocks), and the
metatheoretic iteration of any driver.
-/

namespace Attachment

open PrimitivePassage HigherStructure

/-! ## 1. Lawful policies and typed refusal -/

/-- A lawful attachment policy: the choice function together with
the PROOF that every chosen parent is represented (strictly below
its child).  No clamping happens anywhere downstream. -/
structure LawfulPolicy where
  choose : Nat → Nat
  lawful : ∀ k, choose (k + 1) ≤ k

/-- The parent of child `k + 1` under a lawful policy — the choice
itself, unrewritten. -/
def par (π : LawfulPolicy) (k : Nat) : Nat := π.choose (k + 1)

theorem par_le (π : LawfulPolicy) (k : Nat) : par π k ≤ k :=
  π.lawful k

/-- The retired clamp, kept only as the countermodel's exhibit. -/
def clampedPar (c : Nat → Nat) (k : Nat) : Nat := min (c (k + 1)) k

/-- An illegal, unclamped choice function: parent `i + 7` for child
`i` — never represented. -/
def badChoice : Nat → Nat := fun i => i + 7

/-- **Countermodel (retired clamp)**: the clamp silently rewrote the
illegal choice into the root — the choice of the all-root policy —
although the illegal choice is not that choice.  Rewritten input was
being presented as lawful; it is not, and now it is refused
instead (`unlawful_refused`). -/
theorem clamp_rewrote_input :
    clampedPar badChoice 0 = 0 ∧ badChoice 1 ≠ 0 := by
  constructor
  · decide
  · decide

/-- Outcome of a checked attachment: the extended state, or a typed
refusal naming the illegal parent and the position bound. -/
inductive AttachOutcome where
  | attached (s : PState)
  | refusedParent (p bound : Nat)
deriving Repr, DecidableEq

/-! ## 2. Occurrence identity: tokens, positions, freshness -/

def natMax (l : List Nat) : Nat := l.foldr max 0

theorem le_natMax_of_mem {l : List Nat} {x : Nat} (h : x ∈ l) :
    x ≤ natMax l := by
  induction l with
  | nil => cases h
  | cons b tl ih =>
      show x ≤ max b (natMax tl)
      rcases List.mem_cons.mp h with heq | ht
      · subst heq
        exact Nat.le_max_left x (natMax tl)
      · exact Nat.le_trans (ih ht) (Nat.le_max_right b (natMax tl))

/-- The canonical fresh token: one past the maximum admitted token
(zero on the empty list). -/
def freshTok (s : PState) : Nat :=
  if s.occ.isEmpty then 0 else natMax s.occ + 1

/-- Freshness, proved for EVERY occurrence list — not only initial
segments. -/
theorem freshTok_fresh (s : PState) : ¬ (freshTok s ∈ s.occ) := by
  intro hmem
  unfold freshTok at hmem
  cases hocc : s.occ with
  | nil => rw [hocc] at hmem; cases hmem
  | cons a t =>
      rw [hocc] at hmem
      have hne : (a :: t).isEmpty = false := rfl
      rw [hne] at hmem
      simp only [Bool.false_eq_true, if_false] at hmem
      have := le_natMax_of_mem hmem
      omega

/-! ## 3. The exact Up family and its execution theorem -/

/-- The declared one-edge extension block at parent position `p`:
admission of the canonical fresh token (creating position
`s.occ.length`),
then assert, retain, and protect the parent edge. -/
def upBlock (s : PState) (p : Nat) : List PEvent :=
  [.admitOcc (freshTok s), .assertWit p s.occ.length,
   .admitWit p s.occ.length, .protect p s.occ.length]

/-- `Up`: one block per represented parent position — the complete
family of the declared grammar, never a selected extension. -/
def upFamily (s : PState) : List (List PEvent) :=
  (List.range s.occ.length).map (upBlock s)

/-- The declared grammar, as a predicate. -/
def LegalOneEdgeExtension (s : PState) (b : List PEvent) : Prop :=
  ∃ p, p < s.occ.length ∧ b = upBlock s p

/-- **Registry-relative completeness, both directions**: membership
in `Up` is EXACTLY legality in the declared one-edge grammar. -/
theorem up_iff_legal (s : PState) (b : List PEvent) :
    b ∈ upFamily s ↔ LegalOneEdgeExtension s b := by
  constructor
  · intro hb
    obtain ⟨p, hp, heq⟩ := List.mem_map.mp hb
    exact ⟨p, List.mem_range.mp hp, heq.symm⟩
  · intro ⟨p, hp, heq⟩
    subst heq
    exact List.mem_map.mpr ⟨p, List.mem_range.mpr hp, rfl⟩

/-- Position-boundedness of the relational stores. -/
def WFStores (s : PState) : Prop :=
  (∀ pr ∈ s.asserted, pr.1 < s.occ.length ∧ pr.2 < s.occ.length) ∧
  (∀ pr ∈ s.wit, pr.1 < s.occ.length ∧ pr.2 < s.occ.length) ∧
  (∀ pr ∈ s.prot, pr.1 < s.occ.length ∧ pr.2 < s.occ.length)

/-- The four intermediate states of executing an `Up` block, named
so that every equation below relates named states — no inline
record literal appears in any proof-term type. -/
def upS1 (s : PState) : PState :=
  { s with occ := s.occ ++ [freshTok s] }

def upS2 (s : PState) (p : Nat) : PState :=
  { upS1 s with asserted := s.asserted ++ [(p, s.occ.length)] }

def upS3 (s : PState) (p : Nat) : PState :=
  { upS2 s p with wit := s.wit ++ [(p, s.occ.length)] }

def upS4 (s : PState) (p : Nat) : PState :=
  { upS3 s p with prot := s.prot ++ [(p, s.occ.length)] }

/-- Closed form of executing an `Up` block at a represented parent
on a live, store-bounded state: the replay IS the named final
state. -/
theorem up_exec_eq (s : PState) (hwf : WFStores s)
    (hh : s.halted = false) (p : Nat) (hp : p < s.occ.length) :
    replayP (upBlock s p) s = upS4 s p := by
  obtain ⟨hwa, hww, hwp⟩ := hwf
  have hlen1 : (s.occ ++ [freshTok s]).length = s.occ.length + 1 := by
    simp [List.length_append]
  have h1 : step s (.admitOcc (freshTok s)) = upS1 s :=
    pstep_admit hh (freshTok_fresh s)
  have h2 : step (upS1 s) (.assertWit p s.occ.length) = upS2 s p :=
    pstep_assert (show (upS1 s).halted = false from hh) (by
      show ((p != s.occ.length)
        && decide (p < (s.occ ++ [freshTok s]).length)
        && decide (s.occ.length < (s.occ ++ [freshTok s]).length)
        && !(decide ((p, s.occ.length) ∈ s.asserted))) = true
      rw [hlen1,
          decide_eq_true (show p < s.occ.length + 1 by omega),
          decide_eq_true (show s.occ.length < s.occ.length + 1
            by omega),
          bne_iff_ne.mpr (show p ≠ s.occ.length by omega),
          decide_eq_false (by
            intro hmem
            have := (hwa (p, s.occ.length) hmem).2
            omega)]
      rfl)
  have h3 : step (upS2 s p) (.admitWit p s.occ.length) = upS3 s p :=
    pstep_wit (show (upS2 s p).halted = false from hh) (by
      show ((p != s.occ.length)
        && decide (p < (s.occ ++ [freshTok s]).length)
        && decide (s.occ.length < (s.occ ++ [freshTok s]).length)
        && (decide ((p, s.occ.length) ∈ s.asserted
              ++ [(p, s.occ.length)]))
        && !(decide ((p, s.occ.length) ∈ s.wit))) = true
      rw [hlen1,
          decide_eq_true (show p < s.occ.length + 1 by omega),
          decide_eq_true (show s.occ.length < s.occ.length + 1
            by omega),
          bne_iff_ne.mpr (show p ≠ s.occ.length by omega),
          decide_eq_true (List.mem_append.mpr
            (Or.inr List.mem_cons_self)),
          decide_eq_false (by
            intro hmem
            have := (hww (p, s.occ.length) hmem).2
            omega)]
      rfl)
  have h4 : step (upS3 s p) (.protect p s.occ.length) = upS4 s p :=
    pstep_prot (show (upS3 s p).halted = false from hh) (by
      show ((decide ((p, s.occ.length) ∈ s.wit
            ++ [(p, s.occ.length)]))
        && !(decide ((p, s.occ.length) ∈ s.prot))) = true
      rw [decide_eq_true (List.mem_append.mpr
            (Or.inr List.mem_cons_self)),
          decide_eq_false (by
            intro hmem
            have := (hwp (p, s.occ.length) hmem).2
            omega)]
      rfl)
  show step (step (step (step s (.admitOcc (freshTok s)))
    (.assertWit p s.occ.length)) (.admitWit p s.occ.length))
    (.protect p s.occ.length) = _
  rw [h1, h2, h3, h4]

/-- **Every `Up` block executes to a strict legal extension** on any
live, store-bounded state: occurrences, asserted, retained, and
protected stores each grow by exactly one, and boundedness is
preserved. -/
theorem up_executes (s : PState) (hwf : WFStores s)
    (hh : s.halted = false) (p : Nat) (hp : p < s.occ.length) :
    (replayP (upBlock s p) s).occ.length = s.occ.length + 1 ∧
    (replayP (upBlock s p) s).asserted.length
      = s.asserted.length + 1 ∧
    (replayP (upBlock s p) s).wit.length = s.wit.length + 1 ∧
    (replayP (upBlock s p) s).prot.length = s.prot.length + 1 ∧
    WFStores (replayP (upBlock s p) s) := by
  have hlen1 : (s.occ ++ [freshTok s]).length = s.occ.length + 1 := by
    simp [List.length_append]
  rw [up_exec_eq s hwf hh p hp]
  obtain ⟨hwa, hww, hwp⟩ := hwf
  refine ⟨hlen1, ?_, ?_, ?_, ?_, ?_, ?_⟩
  · show (s.asserted ++ [(p, s.occ.length)]).length
      = s.asserted.length + 1
    simp [List.length_append]
  · show (s.wit ++ [(p, s.occ.length)]).length = s.wit.length + 1
    simp [List.length_append]
  · show (s.prot ++ [(p, s.occ.length)]).length = s.prot.length + 1
    simp [List.length_append]
  · intro pr hpr
    show pr.1 < (s.occ ++ [freshTok s]).length
      ∧ pr.2 < (s.occ ++ [freshTok s]).length
    rw [hlen1]
    rcases List.mem_append.mp hpr with hm | hm
    · obtain ⟨h1, h2⟩ := hwa pr hm
      constructor <;> omega
    · cases List.mem_singleton.mp hm
      show p < s.occ.length + 1 ∧ s.occ.length < s.occ.length + 1
      constructor <;> omega
  · intro pr hpr
    show pr.1 < (s.occ ++ [freshTok s]).length
      ∧ pr.2 < (s.occ ++ [freshTok s]).length
    rw [hlen1]
    rcases List.mem_append.mp hpr with hm | hm
    · obtain ⟨h1, h2⟩ := hww pr hm
      constructor <;> omega
    · cases List.mem_singleton.mp hm
      show p < s.occ.length + 1 ∧ s.occ.length < s.occ.length + 1
      constructor <;> omega
  · intro pr hpr
    show pr.1 < (s.occ ++ [freshTok s]).length
      ∧ pr.2 < (s.occ ++ [freshTok s]).length
    rw [hlen1]
    rcases List.mem_append.mp hpr with hm | hm
    · obtain ⟨h1, h2⟩ := hwp pr hm
      constructor <;> omega
    · cases List.mem_singleton.mp hm
      show p < s.occ.length + 1 ∧ s.occ.length < s.occ.length + 1
      constructor <;> omega

/-- The checked attachment: extend at a represented parent on a
live state, or return the typed refusal.  Illegal input is refused,
never rewritten. -/
def attachChecked (s : PState) (p : Nat) : AttachOutcome :=
  if (decide (p < s.occ.length)) && !s.halted then
    .attached (replayP (upBlock s p) s)
  else
    .refusedParent p s.occ.length

theorem attachChecked_refuses (s : PState) (p : Nat)
    (hp : ¬ (p < s.occ.length)) :
    attachChecked s p = .refusedParent p s.occ.length := by
  unfold attachChecked
  rw [if_neg (by
    intro hc
    simp only [Bool.and_eq_true, decide_eq_true_eq] at hc
    exact hp hc.1)]

/-- **Countermodel (illegal unclamped policy)**: at any
three-occurrence state, the illegal choice for child 2 is parent 9;
the outcome is the typed refusal record — not a silently rewritten
attachment. -/
theorem unlawful_refused (s : PState) (h3 : s.occ.length = 3) :
    attachChecked s (badChoice 2) = .refusedParent 9 3 := by
  have h9 : badChoice 2 = 9 := rfl
  rw [h9, attachChecked_refuses s 9 (by omega), h3]

/-! ### The length-as-token countermodel (required) -/

/-- A lawful non-initial occurrence list: tokens `[1, 2]` at
positions `0, 1`. -/
def s12 : PState :=
  { occ := [1, 2], asserted := [], wit := [], prot := [],
    obs := none, budget := 0, licensed := true, refusals := [],
    halted := false }

/-- **Countermodel (length is not a fresh token)**: on `[1, 2]` the
old grammar's `admitOcc occ.length = admitOcc 2` collides with the
admitted token 2 — dedup silences it and the old block fails to
extend the carrier, while its later events target position 2, which
the failed admission never created.  The canonical fresh token is 3
and the repaired block extends strictly. -/
theorem length_not_fresh_countermodel :
    (replayP [.admitOcc 2, .assertWit 0 2, .admitWit 0 2,
              .protect 0 2] s12).occ.length = 2 ∧
    freshTok s12 = 3 ∧
    (replayP (upBlock s12 0) s12).occ.length = 3 := by
  refine ⟨?_, ?_, ?_⟩ <;> decide

/-- On halted states every `Up` block is inert: iteration is not
unconditional — the terminal absorbs the grammar too. -/
theorem halted_up_inert (s : PState) (h : s.halted = true)
    (p : Nat) : replayP (upBlock s p) s = s := by
  show step (step (step (step s (.admitOcc (freshTok s)))
    (.assertWit p s.occ.length)) (.admitWit p s.occ.length))
    (.protect p s.occ.length) = s
  rw [step_halted s _ h, step_halted s _ h, step_halted s _ h,
      step_halted s _ h]

/-! ## 4. Renaming equivariance (the genuine action) -/

/-- A positional renaming at scale `n`: a global inverse pair that
permutes positions below `n` and fixes every position at or above
`n`. -/
structure Renaming (n : Nat) where
  f : Nat → Nat
  g : Nat → Nat
  fg : ∀ x, g (f x) = x
  gf : ∀ x, f (g x) = x
  fbound : ∀ x, x < n → f x < n
  ffix : ∀ x, n ≤ x → f x = x

theorem Renaming.f_inj {n : Nat} (σ : Renaming n) {x y : Nat}
    (h : σ.f x = σ.f y) : x = y := by
  have h2 := congrArg σ.g h
  rw [σ.fg, σ.fg] at h2
  exact h2

theorem Renaming.gbound {n : Nat} (σ : Renaming n) :
    ∀ x, x < n → σ.g x < n := by
  intro x hx
  by_cases h : σ.g x < n
  · exact h
  · exfalso
    have := σ.ffix (σ.g x) (by omega)
    rw [σ.gf] at this
    omega

theorem Renaming.gfix {n : Nat} (σ : Renaming n) :
    ∀ x, n ≤ x → σ.g x = x := by
  intro x hx
  by_cases h : σ.g x < n
  · exfalso
    have := σ.fbound (σ.g x) h
    rw [σ.gf] at this
    omega
  · have h1 := σ.ffix (σ.g x) (by omega)
    rw [σ.gf] at h1
    exact h1.symm

theorem Renaming.fbound_iff {n : Nat} (σ : Renaming n) (x : Nat) :
    (σ.f x < n) ↔ (x < n) := by
  constructor
  · intro hfx
    by_cases hx : x < n
    · exact hx
    · exfalso
      rw [σ.ffix x (by omega)] at hfx
      omega
  · exact σ.fbound x

theorem getD_lt {l : List Nat} {i : Nat} (h : i < l.length) :
    l.getD i 0 = l[i] := by
  rw [List.getD_eq_getElem?_getD, List.getElem?_eq_getElem h]
  rfl

theorem getD_append_lt {l l' : List Nat} {i : Nat}
    (h : i < l.length) :
    (l ++ l').getD i 0 = l.getD i 0 := by
  have h2 : i < (l ++ l').length := by
    rw [List.length_append]
    omega
  rw [getD_lt h2, getD_lt h, List.getElem_append_left h]

def renPair {n : Nat} (σ : Renaming n) (pr : Nat × Nat) :
    Nat × Nat := (σ.f pr.1, σ.f pr.2)

/-- The action on states: positions in every relational store and
column are renamed; the occurrence-token list is re-indexed so that
the token at old position `i` sits at new position `σ.f i`. -/
def act {n : Nat} (σ : Renaming n) (s : PState) : PState :=
  { occ := (List.range s.occ.length).map
      (fun j => s.occ.getD (σ.g j) 0),
    asserted := s.asserted.map (renPair σ),
    wit := s.wit.map (renPair σ),
    prot := s.prot.map (renPair σ),
    obs := s.obs.map (fun cols => cols.map (List.map σ.f)),
    budget := s.budget, licensed := s.licensed,
    refusals := s.refusals.map (renPair σ),
    halted := s.halted }

theorem act_occ_length {n : Nat} (σ : Renaming n) (s : PState) :
    (act σ s).occ.length = s.occ.length := by
  show ((List.range s.occ.length).map _).length = _
  rw [List.length_map, List.length_range]

/-- Membership in the re-indexed token list is unchanged: the
renamed carrier presents the same tokens. -/
theorem act_occ_mem {n : Nat} (σ : Renaming n) (s : PState)
    (hn : n = s.occ.length) (x : Nat) :
    (x ∈ (act σ s).occ) ↔ (x ∈ s.occ) := by
  subst hn
  constructor
  · intro hx
    obtain ⟨j, hj, hget⟩ := List.mem_map.mp hx
    have hjn := List.mem_range.mp hj
    have hg := σ.gbound j hjn
    rw [getD_lt hg] at hget
    rw [← hget]
    exact List.getElem_mem hg
  · intro hx
    obtain ⟨i, hi, hget⟩ := List.mem_iff_getElem.mp hx
    apply List.mem_map.mpr
    refine ⟨σ.f i, List.mem_range.mpr (σ.fbound i hi), ?_⟩
    rw [σ.fg, getD_lt hi]
    exact hget

/-- The canonical fresh token is renaming-invariant: it depends only
on which tokens are present. -/
theorem freshTok_act {n : Nat} (σ : Renaming n) (s : PState)
    (hn : n = s.occ.length) : freshTok (act σ s) = freshTok s := by
  have hlen := act_occ_length σ s
  have hmem := act_occ_mem σ s hn
  have hmax : natMax (act σ s).occ = natMax s.occ := by
    have hle : ∀ (l l' : List Nat),
        (∀ x, x ∈ l → x ∈ l') → natMax l ≤ natMax l' := by
      intro l l' hsub
      induction l with
      | nil => exact Nat.zero_le _
      | cons a t ih =>
          show max a (natMax t) ≤ natMax l'
          have ha := le_natMax_of_mem (hsub a List.mem_cons_self)
          have ht := ih (fun x hx =>
            hsub x (List.mem_cons_of_mem a hx))
          omega
    have h1 := hle (act σ s).occ s.occ (fun x hx => (hmem x).mp hx)
    have h2 := hle s.occ (act σ s).occ (fun x hx => (hmem x).mpr hx)
    omega
  unfold freshTok
  have hemp : (act σ s).occ.isEmpty = s.occ.isEmpty := by
    cases hocc : s.occ with
    | nil =>
        have : (act σ s).occ.length = 0 := by
          rw [hlen, hocc]
          rfl
        cases hocc' : (act σ s).occ with
        | nil => rfl
        | cons a t => rw [hocc'] at this; cases this
    | cons a t =>
        have : (act σ s).occ.length = t.length + 1 := by
          rw [hlen, hocc]
          rfl
        cases hocc' : (act σ s).occ with
        | nil => rw [hocc'] at this; cases this
        | cons a' t' => rfl
  rw [hemp, hmax]

/-- Up blocks transport along the action: the block at parent `p`
becomes the block at parent `σ.f p` — the endpoint position
`occ.length` is fixed by the renaming. -/
theorem upBlock_transport {n : Nat} (σ : Renaming n) (s : PState)
    (hn : n = s.occ.length) (p : Nat) :
    upBlock (act σ s) (σ.f p)
      = [.admitOcc (freshTok s), .assertWit (σ.f p) s.occ.length,
         .admitWit (σ.f p) s.occ.length,
         .protect (σ.f p) s.occ.length] := by
  unfold upBlock
  rw [freshTok_act σ s hn, act_occ_length]

/-- **Up-family transport (orbit form)**: the block at `p` is in the
family exactly when the transported block at `σ.f p` is in the
transported family. -/
theorem upBlock_parent_inj (s : PState) {p p' : Nat}
    (heq : upBlock s p = upBlock s p') : p = p' := by
  have h := congrArg (fun l : List PEvent =>
    match l with
    | _ :: .assertWit a _ :: _ => a
    | _ => 0) heq
  exact h

theorem upFamily_transport {n : Nat} (σ : Renaming n) (s : PState)
    (hn : n = s.occ.length) (p : Nat) :
    upBlock s p ∈ upFamily s
      ↔ upBlock (act σ s) (σ.f p) ∈ upFamily (act σ s) := by
  subst hn
  constructor
  · intro hb
    obtain ⟨p', hp', heq⟩ := (up_iff_legal s _).mp hb
    have hpe : p = p' := upBlock_parent_inj s heq
    subst hpe
    apply (up_iff_legal (act σ s) _).mpr
    refine ⟨σ.f p, ?_, rfl⟩
    rw [act_occ_length]
    exact (σ.fbound_iff p).mpr hp'
  · intro hb
    obtain ⟨p', hp', heq⟩ := (up_iff_legal (act σ s) _).mp hb
    have hpe : σ.f p = p' := upBlock_parent_inj (act σ s) heq
    have hfp : σ.f p < s.occ.length := by
      rw [hpe, ← act_occ_length σ s]
      exact hp'
    apply (up_iff_legal s _).mpr
    exact ⟨p, (σ.fbound_iff p).mp hfp, rfl⟩

/-- Replay of an Up block commutes with the action (supply
fragment): acting on the extended state equals extending the acted
state at the renamed parent.  Proved on well-formed live states —
the exact scope the grammar uses; commutation for the full
observation calculus is not claimed. -/
theorem act_up_comm {n : Nat} (σ : Renaming n) (s : PState)
    (hn : n = s.occ.length) (hwf : WFStores s)
    (hh : s.halted = false) (p : Nat) (hp : p < s.occ.length) :
    act σ (replayP (upBlock s p) s)
      = replayP (upBlock (act σ s) (σ.f p)) (act σ s) := by
  have hwfA : WFStores (act σ s) := by
    obtain ⟨hwa, hww, hwp⟩ := hwf
    refine ⟨?_, ?_, ?_⟩ <;>
      (intro pr hpr
       obtain ⟨q, hq, heq⟩ := List.mem_map.mp hpr
       subst heq
       rw [act_occ_length])
    · have := hwa q hq
      constructor
      · rw [← hn] at this ⊢
        exact (σ.fbound_iff q.1).mpr (by omega)
      · rw [← hn] at this ⊢
        exact (σ.fbound_iff q.2).mpr (by omega)
    · have := hww q hq
      constructor
      · rw [← hn] at this ⊢
        exact (σ.fbound_iff q.1).mpr (by omega)
      · rw [← hn] at this ⊢
        exact (σ.fbound_iff q.2).mpr (by omega)
    · have := hwp q hq
      constructor
      · rw [← hn] at this ⊢
        exact (σ.fbound_iff q.1).mpr (by omega)
      · rw [← hn] at this ⊢
        exact (σ.fbound_iff q.2).mpr (by omega)
  have hhA : (act σ s).halted = false := hh
  have hpA : σ.f p < (act σ s).occ.length := by
    rw [act_occ_length, ← hn]
    exact (σ.fbound_iff p).mpr (hn ▸ hp)
  rw [up_exec_eq s hwf hh p hp,
      up_exec_eq (act σ s) hwfA hhA (σ.f p) hpA]
  -- componentwise equality of the two named final states
  have hlenS : (s.occ ++ [freshTok s]).length = s.occ.length + 1 := by
    simp [List.length_append]
  show ({ occ := (List.range (s.occ ++ [freshTok s]).length).map
            (fun j => (s.occ ++ [freshTok s]).getD (σ.g j) 0),
          asserted := (s.asserted ++ [(p, s.occ.length)]).map
            (renPair σ),
          wit := (s.wit ++ [(p, s.occ.length)]).map (renPair σ),
          prot := (s.prot ++ [(p, s.occ.length)]).map (renPair σ),
          obs := s.obs.map (fun cols => cols.map (List.map σ.f)),
          budget := s.budget, licensed := s.licensed,
          refusals := s.refusals.map (renPair σ),
          halted := s.halted } : PState) = upS4 (act σ s) (σ.f p)
  have hocc : (List.range (s.occ ++ [freshTok s]).length).map
      (fun j => (s.occ ++ [freshTok s]).getD (σ.g j) 0)
      = (act σ s).occ ++ [freshTok (act σ s)] := by
    rw [hlenS, List.range_succ, List.map_append]
    congr 1
    · apply List.map_congr_left
      intro j hj
      have hjn := List.mem_range.mp hj
      have hg : σ.g j < s.occ.length := by
        rw [← hn] at hjn ⊢
        exact σ.gbound j hjn
      exact getD_append_lt hg
    · show [(s.occ ++ [freshTok s]).getD (σ.g s.occ.length) 0]
        = [freshTok (act σ s)]
      rw [σ.gfix s.occ.length (by omega),
          freshTok_act σ s hn]
      congr 1
      rw [getD_lt (show s.occ.length
        < (s.occ ++ [freshTok s]).length by rw [hlenS]; omega)]
      have : (s.occ ++ [freshTok s])[s.occ.length]'(by
          rw [hlenS]; omega) = freshTok s := by
        rw [List.getElem_append_right (Nat.le_refl _)]
        simp
      rw [this]
  have hpr : renPair σ (p, s.occ.length)
      = (σ.f p, (act σ s).occ.length) := by
    unfold renPair
    rw [act_occ_length, σ.ffix s.occ.length (by omega)]
  rw [hocc]
  rw [show (s.asserted ++ [(p, s.occ.length)]).map (renPair σ)
      = (act σ s).asserted ++ [(σ.f p, (act σ s).occ.length)] from by
    rw [List.map_append]
    show _ ++ [renPair σ (p, s.occ.length)] = _
    rw [hpr]
    rfl]
  rw [show (s.wit ++ [(p, s.occ.length)]).map (renPair σ)
      = (act σ s).wit ++ [(σ.f p, (act σ s).occ.length)] from by
    rw [List.map_append]
    show _ ++ [renPair σ (p, s.occ.length)] = _
    rw [hpr]
    rfl]
  rw [show (s.prot ++ [(p, s.occ.length)]).map (renPair σ)
      = (act σ s).prot ++ [(σ.f p, (act σ s).occ.length)] from by
    rw [List.map_append]
    show _ ++ [renPair σ (p, s.occ.length)] = _
    rw [hpr]
    rfl]
  rfl

/-- Grammar uniformity over an IDENTICAL carrier: states with the
same occurrence list have the same Up family.  This is a fact about
the declared grammar reading only the carrier — it is NOT
presentation equivalence (see the countermodel below). -/
theorem upFamily_grammar_uniform (s t : PState)
    (h : s.occ = t.occ) : upFamily s = upFamily t := by
  unfold upFamily upBlock freshTok
  rw [h]

/-! ## 5. Trees from every lawful policy -/

/-- One-edge attachment at stage `k`: glue a fresh walking edge
along the policy's chosen parent — supply side only (assert,
retain, protect).  On the canonical tree states below, tokens and
positions coincide and this IS the `Up` block at the chosen parent
(`attachBlock_is_upBlock`). -/
def attachBlock (π : LawfulPolicy) (k : Nat) : List PEvent :=
  [.admitOcc (k + 1), .assertWit (par π k) (k + 1),
   .admitWit (par π k) (k + 1), .protect (par π k) (k + 1)]

def attachHist (π : LawfulPolicy) : Nat → List PEvent
  | 0 => [.admitOcc 0]
  | n + 1 => attachHist π n ++ attachBlock π n

/-- The grown state of an arbitrary lawful attachment policy. -/
def treeAt (π : LawfulPolicy) (n : Nat) : PState :=
  replayP (attachHist π n) genesisP

/-- The characterized record: `n + 1` occurrences and one
parent-edge per non-root occurrence, pre-observational. -/
def treeState (π : LawfulPolicy) (n : Nat) : PState :=
  { occ := List.range (n + 1),
    asserted := (List.range n).map (fun k => (par π k, k + 1)),
    wit := (List.range n).map (fun k => (par π k, k + 1)),
    prot := (List.range n).map (fun k => (par π k, k + 1)),
    obs := none, budget := 0, licensed := true, refusals := [],
    halted := false }

/-! ### Guard facts, uniform in the policy -/

theorem attach_fresh (n : Nat) : ¬ (n + 1 ∈ List.range (n + 1)) := by
  intro h
  exact absurd (List.mem_range.mp h) (by omega)

theorem attach_pair_not_mem (π : LawfulPolicy) (n : Nat) :
    ¬ ((par π n, n + 1) ∈ (List.range n).map
      (fun k => (par π k, k + 1))) := by
  intro h
  obtain ⟨k, hk, heq⟩ := List.mem_map.mp h
  have h2 : k + 1 = n + 1 := congrArg Prod.snd heq
  have h3 : k < n := List.mem_range.mp hk
  omega

/-- Intermediate states of one attachment round. -/
def t1 (π : LawfulPolicy) (n : Nat) : PState :=
  { treeState π n with occ := List.range (n + 1) ++ [n + 1] }

def t2 (π : LawfulPolicy) (n : Nat) : PState :=
  { t1 π n with
    asserted := (List.range n).map (fun k => (par π k, k + 1))
      ++ [(par π n, n + 1)] }

def t3 (π : LawfulPolicy) (n : Nat) : PState :=
  { t2 π n with
    wit := (List.range n).map (fun k => (par π k, k + 1))
      ++ [(par π n, n + 1)] }

theorem attach_len (n : Nat) :
    (List.range (n + 1) ++ [n + 1]).length = n + 2 := by
  simp [List.length_append, List.length_range]

theorem attach_wf_guard (π : LawfulPolicy) (n : Nat) :
    (wfPair (t1 π n) (par π n) (n + 1)
      && !(decide ((par π n, n + 1) ∈ (t1 π n).asserted)))
      = true := by
  show ((par π n != n + 1)
      && decide (par π n < (List.range (n + 1) ++ [n + 1]).length)
      && decide (n + 1 < (List.range (n + 1) ++ [n + 1]).length)
      && !(decide ((par π n, n + 1) ∈ (List.range n).map
            (fun k => (par π k, k + 1))))) = true
  rw [attach_len]
  have hle := par_le π n
  simp only [Bool.and_eq_true, Bool.not_eq_true',
    decide_eq_false_iff_not]
  exact ⟨⟨⟨bne_iff_ne.mpr (by omega),
    decide_eq_true (by omega)⟩, decide_eq_true (by omega)⟩,
    attach_pair_not_mem π n⟩

theorem attach_wit_guard (π : LawfulPolicy) (n : Nat) :
    (wfPair (t2 π n) (par π n) (n + 1)
      && (decide ((par π n, n + 1) ∈ (t2 π n).asserted))
      && !(decide ((par π n, n + 1) ∈ (t2 π n).wit))) = true := by
  show ((par π n != n + 1)
      && decide (par π n < (List.range (n + 1) ++ [n + 1]).length)
      && decide (n + 1 < (List.range (n + 1) ++ [n + 1]).length)
      && (decide ((par π n, n + 1) ∈ (List.range n).map
            (fun k => (par π k, k + 1)) ++ [(par π n, n + 1)]))
      && !(decide ((par π n, n + 1) ∈ (List.range n).map
            (fun k => (par π k, k + 1))))) = true
  rw [attach_len]
  have hle := par_le π n
  simp only [Bool.and_eq_true, Bool.not_eq_true',
    decide_eq_false_iff_not]
  exact ⟨⟨⟨⟨bne_iff_ne.mpr (by omega),
    decide_eq_true (by omega)⟩, decide_eq_true (by omega)⟩,
    decide_eq_true
      (List.mem_append.mpr (Or.inr List.mem_cons_self))⟩,
    attach_pair_not_mem π n⟩

theorem attach_prot_guard (π : LawfulPolicy) (n : Nat) :
    ((decide ((par π n, n + 1) ∈ (t3 π n).wit))
      && !(decide ((par π n, n + 1) ∈ (t3 π n).prot))) = true := by
  show ((decide ((par π n, n + 1) ∈ (List.range n).map
        (fun k => (par π k, k + 1)) ++ [(par π n, n + 1)]))
    && !(decide ((par π n, n + 1) ∈ (List.range n).map
        (fun k => (par π k, k + 1))))) = true
  simp only [Bool.and_eq_true, Bool.not_eq_true',
    decide_eq_false_iff_not]
  exact ⟨decide_eq_true
    (List.mem_append.mpr (Or.inr List.mem_cons_self)),
    attach_pair_not_mem π n⟩

theorem range_map_succ (π : LawfulPolicy) (n : Nat) :
    (List.range (n + 1)).map (fun k => (par π k, k + 1))
      = (List.range n).map (fun k => (par π k, k + 1))
        ++ [(par π n, n + 1)] := by
  rw [List.range_succ, List.map_append]
  rfl

/-- **Every lawful attachment policy executes at every stage**: the
grown state is exactly the characterized tree record, by induction —
whatever the policy chooses. -/
theorem treeAt_spec (π : LawfulPolicy) (n : Nat) :
    treeAt π n = treeState π n := by
  induction n with
  | zero =>
      show replayP [.admitOcc 0] genesisP = treeState π 0
      have h : step genesisP (.admitOcc 0) =
          { genesisP with occ := [0] } := by
        rw [pstep_admit rfl (by intro h; cases h)]
        rfl
      show step genesisP (.admitOcc 0) = treeState π 0
      rw [h]
      rfl
  | succ m ih =>
      show replayP (attachHist π m ++ attachBlock π m) genesisP
        = treeState π (m + 1)
      rw [replay_append]
      show replayP (attachBlock π m) (treeAt π m)
        = treeState π (m + 1)
      rw [ih]
      show step (step (step (step (treeState π m)
        (.admitOcc (m + 1))) (.assertWit (par π m) (m + 1)))
        (.admitWit (par π m) (m + 1)))
        (.protect (par π m) (m + 1)) = treeState π (m + 1)
      rw [show step (treeState π m) (.admitOcc (m + 1)) = t1 π m
        from by
          rw [pstep_admit rfl (by exact attach_fresh m)]
          rfl]
      rw [show step (t1 π m) (.assertWit (par π m) (m + 1)) = t2 π m
        from by
          rw [pstep_assert rfl (attach_wf_guard π m)]
          rfl]
      rw [show step (t2 π m) (.admitWit (par π m) (m + 1)) = t3 π m
        from by
          rw [pstep_wit rfl (attach_wit_guard π m)]
          rfl]
      rw [pstep_prot rfl (attach_prot_guard π m)]
      show ({ t3 π m with
        prot := (List.range m).map (fun k => (par π k, k + 1))
          ++ [(par π m, m + 1)] } : PState) = treeState π (m + 1)
      unfold t3 t2 t1 treeState
      rw [show List.range (m + 1) ++ [m + 1] = List.range (m + 2)
        from (List.range_succ).symm,
        ← range_map_succ π m]

/-! ### Tokens and positions coincide on canonical tree states -/

theorem natMax_append_singleton (l : List Nat) (x : Nat) :
    natMax (l ++ [x]) = max (natMax l) x := by
  induction l with
  | nil =>
      show max x 0 = max 0 x
      omega
  | cons a t ih =>
      show max a (natMax (t ++ [x])) = max (max a (natMax t)) x
      rw [ih]
      omega

theorem natMax_range_le (n : Nat) : natMax (List.range n) ≤ n := by
  induction n with
  | zero => decide
  | succ m ih =>
      rw [List.range_succ, natMax_append_singleton]
      omega

theorem tree_occ_len (π : LawfulPolicy) (n : Nat) :
    (treeState π n).occ.length = n + 1 := by
  show (List.range (n + 1)).length = n + 1
  exact List.length_range

/-- On the canonical tree states the imported fresh supply picks
exactly the next numeral: token `n + 1` at position `n + 1`. -/
theorem freshTok_treeState (π : LawfulPolicy) (n : Nat) :
    freshTok (treeState π n) = n + 1 := by
  show (if (List.range (n + 1)).isEmpty then 0
    else natMax (List.range (n + 1)) + 1) = n + 1
  rw [List.range_succ,
      show (List.range n ++ [n]).isEmpty = false from by
        cases h : List.range n <;> rfl]
  simp only [Bool.false_eq_true, if_false]
  rw [natMax_append_singleton]
  have := natMax_range_le n
  omega

/-- **The tree grammar is the `Up` grammar**: on canonical tree
states, where tokens and positions provably coincide, the stage-`n`
attachment block IS the `Up` block at the chosen parent — so with
`up_iff_legal`, every round of every lawful policy is a legal
one-edge extension of the declared registry. -/
theorem attachBlock_is_upBlock (π : LawfulPolicy) (n : Nat) :
    attachBlock π n = upBlock (treeState π n) (par π n) := by
  unfold attachBlock upBlock
  rw [freshTok_treeState, tree_occ_len]

/-- Canonical tree states are store-bounded — `up_executes` applies
at every stage of every lawful policy. -/
theorem treeState_wf (π : LawfulPolicy) (n : Nat) :
    WFStores (treeState π n) := by
  refine ⟨?_, ?_, ?_⟩ <;>
    (intro pr hpr
     obtain ⟨k, hk, heq⟩ := List.mem_map.mp hpr
     subst heq
     have hkn := List.mem_range.mp hk
     have hple := par_le π k
     show par π k < (List.range (n + 1)).length
       ∧ k + 1 < (List.range (n + 1)).length
     rw [List.length_range]
     constructor <;> omega)

/-! ### The tree theorems, policy-uniform -/

/-- The connectivity residue `V − E = 1` at every stage, for every
lawful policy. -/
theorem attach_residue (π : LawfulPolicy) (n : Nat) :
    (treeAt π n).occ.length = n + 1 ∧
      (treeAt π n).wit.length = n := by
  rw [treeAt_spec]
  constructor
  · show (List.range (n + 1)).length = n + 1
    exact List.length_range
  · show ((List.range n).map (fun k => (par π k, k + 1))).length = n
    rw [List.length_map]
    exact List.length_range

/-- Edges ascend: every parent strictly precedes its child. -/
theorem parent_lt (π : LawfulPolicy) (n : Nat) :
    ∀ p ∈ (treeAt π n).wit, p.1 < p.2 := by
  rw [treeAt_spec]
  intro p hp
  obtain ⟨k, _, heq⟩ := List.mem_map.mp hp
  subst heq
  have := par_le π k
  omega

/-- Unique parent: two edges into the same child coincide. -/
theorem parent_unique (π : LawfulPolicy) (n : Nat) :
    ∀ p q, p ∈ (treeAt π n).wit → q ∈ (treeAt π n).wit →
      p.2 = q.2 → p = q := by
  rw [treeAt_spec]
  intro p q hp hq h2
  obtain ⟨k1, _, he1⟩ := List.mem_map.mp hp
  obtain ⟨k2, _, he2⟩ := List.mem_map.mp hq
  subst he1
  subst he2
  simp only at h2
  have : k1 = k2 := by omega
  subst this
  rfl

/-- Every non-root occurrence has a parent edge. -/
theorem parent_exists (π : LawfulPolicy) (n : Nat) :
    ∀ c, 1 ≤ c → c < n + 1 →
      ∃ p, (p, c) ∈ (treeAt π n).wit := by
  rw [treeAt_spec]
  intro c h1 h2
  refine ⟨par π (c - 1), ?_⟩
  have hc : c - 1 < n := by omega
  have : (par π (c - 1), (c - 1) + 1) ∈
      (List.range n).map (fun k => (par π k, k + 1)) :=
    List.mem_map.mpr ⟨c - 1, List.mem_range.mpr hc, rfl⟩
  have hcc : c - 1 + 1 = c := by omega
  rw [hcc] at this
  exact this

/-- Reachability along parent edges. -/
inductive Reaches (E : List (Nat × Nat)) : Nat → Prop where
  | root : Reaches E 0
  | step {p c : Nat} : Reaches E p → (p, c) ∈ E → Reaches E c

theorem all_reach_aux (π : LawfulPolicy) (n : Nat) :
    ∀ (bound v : Nat), v ≤ bound → v < n + 1 →
      Reaches ((treeState π n).wit) v := by
  intro bound
  induction bound with
  | zero =>
      intro v hv _
      have : v = 0 := by omega
      subst this
      exact .root
  | succ b ih =>
      intro v hv hn
      match v with
      | 0 => exact .root
      | Nat.succ k =>
          have hk : k < n := by omega
          have hmem : (par π k, k + 1) ∈ (treeState π n).wit := by
            show _ ∈ (List.range n).map (fun j => (par π j, j + 1))
            exact List.mem_map.mpr ⟨k, List.mem_range.mpr hk, rfl⟩
          have hple := par_le π k
          exact .step (ih (par π k) (by omega) (by omega)) hmem

/-- **Every lawful attachment policy produces a tree**: unique
ascending parent per non-root occurrence, and every occurrence
reaches the root along parent edges. -/
theorem all_reach (π : LawfulPolicy) (n : Nat) :
    ∀ v, v < n + 1 → Reaches ((treeState π n).wit) v :=
  fun v hv => all_reach_aux π n v v (Nat.le_refl v) hv

/-! ### Global shape is not forced: path versus star -/

def pathPolL : LawfulPolicy where
  choose := fun i => i - 1
  lawful := fun k => by
    show k + 1 - 1 ≤ k
    omega

def starPolL : LawfulPolicy where
  choose := fun _ => 0
  lawful := fun k => Nat.zero_le k

/-- A third, deterministic pseudo-shape policy — lawful without
clamping. -/
def zigzagL : LawfulPolicy where
  choose := fun i => (i * 7 + 3) % (max 1 i)
  lawful := fun k => by
    show ((k + 1) * 7 + 3) % (max 1 (k + 1)) ≤ k
    have h1 : max 1 (k + 1) = k + 1 := by omega
    rw [h1]
    have := Nat.mod_lt ((k + 1) * 7 + 3) (y := k + 1) (by omega)
    omega

theorem path_edges (n : Nat) :
    (treeAt pathPolL n).wit
      = (List.range n).map (fun k => (k, k + 1)) := by
  rw [treeAt_spec]
  show (List.range n).map (fun k => (par pathPolL k, k + 1)) = _
  have h : (fun k => (par pathPolL k, k + 1))
      = (fun k : Nat => (k, k + 1)) := by
    funext k
    show ((k + 1) - 1, k + 1) = (k, k + 1)
    rfl
  rw [h]

theorem star_edges (n : Nat) :
    (treeAt starPolL n).wit
      = (List.range n).map (fun k => (0, k + 1)) := by
  rw [treeAt_spec]
  show (List.range n).map (fun k => (par starPolL k, k + 1)) = _
  rfl

def path4E : List (Nat × Nat) := [(0, 1), (1, 2), (2, 3)]

def star4E : List (Nat × Nat) := [(0, 1), (0, 2), (0, 3)]

theorem tree4_concrete :
    (treeAt pathPolL 3).wit = path4E ∧
      (treeAt starPolL 3).wit = star4E := by
  constructor <;> decide

/-- All injective 4-tuples: the candidate carrier bijections. -/
def tuples4 : List (Nat × Nat × Nat × Nat) :=
  ((List.range 4).flatMap fun a => (List.range 4).flatMap fun b =>
    (List.range 4).flatMap fun c => (List.range 4).map fun d =>
      (a, b, c, d)).filter fun t =>
    (t.1 != t.2.1) && (t.1 != t.2.2.1) && (t.1 != t.2.2.2)
      && (t.2.1 != t.2.2.1) && (t.2.1 != t.2.2.2)
      && (t.2.2.1 != t.2.2.2)

def app4 (t : Nat × Nat × Nat × Nat) (x : Nat) : Nat :=
  if x = 0 then t.1 else if x = 1 then t.2.1
  else if x = 2 then t.2.2.1 else t.2.2.2

def edgeInU (E : List (Nat × Nat)) (a b : Nat) : Bool :=
  (decide ((a, b) ∈ E)) || (decide ((b, a) ∈ E))

def isoMatch (t : Nat × Nat × Nat × Nat)
    (E1 E2 : List (Nat × Nat)) : Bool :=
  E1.all fun e => edgeInU E2 (app4 t e.1) (app4 t e.2)

/-- **Global shape is not forced**: no carrier bijection carries the
path tree onto the star tree on four occurrences (undirected edge
reading; both have three edges, so forward preservation under an
injective map decides isomorphism). -/
theorem path4_star4_not_isomorphic :
    (tuples4.all fun t => !(isoMatch t path4E star4E)) = true := by
  decide

/-! ### Orbit-valued choices where symmetry remains -/

def swap12 : Nat → Nat := fun x =>
  if x = 1 then 2 else if x = 2 then 1 else x

def flip02 : Nat → Nat := fun x =>
  if x = 0 then 2 else if x = 2 then 0 else x

def renamePair (σ : Nat → Nat) (p : Nat × Nat) : Nat × Nat :=
  (σ p.1, σ p.2)

def blockAt (p n : Nat) : List PEvent :=
  [PEvent.admitOcc n, PEvent.assertWit p n, PEvent.admitWit p n,
   PEvent.protect p n]

/-- Star instance: attaching to leaf 1 and to leaf 2 are one orbit —
the leaf swap carries each store of the one extension exactly onto
the other's. -/
theorem star_orbit_swap :
    (((replayP (blockAt 1 3) (treeAt starPolL 2)).wit.map
        (renamePair swap12)).all
      (fun p => decide (p ∈ (replayP (blockAt 2 3)
        (treeAt starPolL 2)).wit)) = true) ∧
    (((replayP (blockAt 2 3) (treeAt starPolL 2)).wit.map
        (renamePair swap12)).all
      (fun p => decide (p ∈ (replayP (blockAt 1 3)
        (treeAt starPolL 2)).wit)) = true) := by
  constructor <;> decide

/-- Path instance: the ORIENTED path is rigid — the undirected flip
does NOT carry the end-attachment onto the other end's attachment,
because the oriented stores refuse the undirected symmetry (the
orientation residue at work: `Apartness.orientations_differ` one
level up).  So on the oriented path every parent is its own orbit,
while the star's leaves genuinely form one (`star_orbit_swap`). -/
theorem path_oriented_rigid :
    (((replayP (blockAt 0 3) (treeAt pathPolL 2)).wit.map
        (renamePair flip02)).all
      (fun p => decide (p ∈ (replayP (blockAt 2 3)
        (treeAt pathPolL 2)).wit)) = false) := by decide

/-- And the center is a separate orbit: neither the identity nor the
flip carries the end-attachment onto the center-attachment. -/
theorem path_center_separate :
    (((replayP (blockAt 0 3) (treeAt pathPolL 2)).wit.map
        (renamePair flip02)).all
      (fun p => decide (p ∈ (replayP (blockAt 1 3)
        (treeAt pathPolL 2)).wit)) = false) ∧
    (((replayP (blockAt 0 3) (treeAt pathPolL 2)).wit.map
        (renamePair id)).all
      (fun p => decide (p ∈ (replayP (blockAt 1 3)
        (treeAt pathPolL 2)).wit)) = false) := by
  constructor <;> decide

/-! ## 6. The two required countermodels on presentations -/

/-- **Countermodel (size is not presentation equivalence)**: the
three-occurrence star and path states have the SAME carrier
`[0, 1, 2]` — so the declared grammar gives them literally the same
`Up` family (`upFamily_grammar_uniform` in action, decided) — yet NO
positional renaming carries one onto the other: the renamed star
edges would force `σ 0 = 0` and `σ 0 = 1` at once.  Equal size, even
equal families, is NOT relatedness under the genuine action. -/
theorem equal_size_not_renaming_related :
    (upFamily (treeAt starPolL 2) = upFamily (treeAt pathPolL 2)) ∧
    ∀ (n : Nat) (σ : Renaming n),
      act σ (treeAt starPolL 2) ≠ treeAt pathPolL 2 := by
  constructor
  · decide
  · intro n σ h
    have hwit := congrArg PState.wit h
    have hw1 : (treeAt starPolL 2).wit = [(0, 1), (0, 2)] := by
      decide
    have hw2 : (treeAt pathPolL 2).wit = [(0, 1), (1, 2)] := by
      decide
    have hmap : (act σ (treeAt starPolL 2)).wit
        = [(σ.f 0, σ.f 1), (σ.f 0, σ.f 2)] := by
      show (treeAt starPolL 2).wit.map (renPair σ) = _
      rw [hw1]
      rfl
    rw [hmap, hw2] at hwit
    injection hwit with h1 htl
    injection htl with h2 _
    have h1a : σ.f 0 = 0 := congrArg Prod.fst h1
    have h2a : σ.f 0 = 1 := congrArg Prod.fst h2
    omega

/-- **Countermodel (legal equal-cost extensions diverge)**: at the
three-occurrence path, the `Up` blocks at parents 1 and 2 are BOTH
in the family — same grammar, same length, same cost — yet execute
to non-isomorphic shapes (degree-3 center versus four-path, decided
over all carrier bijections).  Completeness of the family never
selects: distinct legal extensions genuinely diverge. -/
theorem equal_cost_non_isomorphic_extensions :
    (upBlock (treeAt pathPolL 2) 1 ∈ upFamily (treeAt pathPolL 2)) ∧
    (upBlock (treeAt pathPolL 2) 2 ∈ upFamily (treeAt pathPolL 2)) ∧
    ((upBlock (treeAt pathPolL 2) 1).length
      = (upBlock (treeAt pathPolL 2) 2).length) ∧
    ((tuples4.all fun t => !(isoMatch t
        (replayP (upBlock (treeAt pathPolL 2) 1)
          (treeAt pathPolL 2)).wit
        (replayP (upBlock (treeAt pathPolL 2) 2)
          (treeAt pathPolL 2)).wit)) = true) := by
  refine ⟨?_, ?_, ?_, ?_⟩ <;> decide

end Attachment
