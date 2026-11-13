import Derivation.Attachment

/-!
# The renaming structure around `Up`: identity, inverse, composition

Goal 1.  `Attachment` proved that a single renaming transports the
`Up` grammar (`upBlock_transport`, `upFamily_transport`,
`act_up_comm`).  A single transported arrow is not an action, and an
action is not functoriality.  This module supplies the missing
structure and its laws, and ONLY at the end is the vocabulary
"equivariant" earned.

1. **The structure**: `idRen`, `invRen`, `compRen` on
   `Attachment.Renaming n`, with the group laws proved
   (`comp_id`, `id_comp`, `comp_assoc`, `inv_comp`, `comp_inv`) via a
   componentwise extensionality principle (`Renaming.ext`).
2. **The action**: `act_id` (unconditional) and `act_comp` (on the
   proved scope `n <= s.occ.length`; equality is used at the source
   of the `Up` naturality square and the weaker inequality also covers
   its one-token extension).
3. **Transport respects the structure**: block transport and
   `Up`-family transport each respect identity and composition.
4. **Coherence**: `act_up_comm` composes — replay of an `Up` block
   commutes with a COMPOSED renaming, and the two routes agree.
5. **No selected representative**: where a symmetry remains, the
   whole orbit of blocks sits inside the family; the family never
   picks one (`upFamily_orbit_closed`, `star_orbit_both_present`).
6. **Countermodels**: equal carrier size and equal cost do not supply
   relatedness, while an arbitrary NON-BIJECTIVE map does not supply
   a `Renaming`, its inverse, or the transport/equivariance laws proved
   for renamings.

Only after 1–5 does the closing section state the equivariance
summary, and it states exactly the scope proved: the supply fragment
of the declared one-edge grammar, on live store-bounded states.
Nothing is claimed for the observation calculus, for multi-edge
extensions, or for maps that are not renamings.
-/

namespace RenamingStructure

open PrimitivePassage Attachment

/-! ## 1. The structure and its laws -/

/-- Componentwise extensionality: the two proof-carrying fields are
propositions, so a renaming is determined by its two functions. -/
theorem Renaming.ext {n : Nat} (σ τ : Renaming n)
    (hf : σ.f = τ.f) (hg : σ.g = τ.g) : σ = τ := by
  cases σ
  cases τ
  cases hf
  cases hg
  rfl

/-- The identity renaming. -/
def idRen (n : Nat) : Renaming n where
  f := fun x => x
  g := fun x => x
  fg := fun _ => rfl
  gf := fun _ => rfl
  fbound := fun _ h => h
  ffix := fun _ _ => rfl

/-- The inverse renaming: swap the pair, and the derived bounds
(`gbound`, `gfix`) become the structural ones. -/
def invRen {n : Nat} (σ : Renaming n) : Renaming n where
  f := σ.g
  g := σ.f
  fg := σ.gf
  gf := σ.fg
  fbound := σ.gbound
  ffix := σ.gfix

/-- Composition: apply `τ` first, then `σ`. -/
def compRen {n : Nat} (σ τ : Renaming n) : Renaming n where
  f := fun x => σ.f (τ.f x)
  g := fun x => τ.g (σ.g x)
  fg := fun x => by
    show τ.g (σ.g (σ.f (τ.f x))) = x
    rw [σ.fg, τ.fg]
  gf := fun x => by
    show σ.f (τ.f (τ.g (σ.g x))) = x
    rw [τ.gf, σ.gf]
  fbound := fun x hx => σ.fbound (τ.f x) (τ.fbound x hx)
  ffix := fun x hx => by
    show σ.f (τ.f x) = x
    rw [τ.ffix x hx, σ.ffix x hx]

theorem comp_id {n : Nat} (σ : Renaming n) :
    compRen σ (idRen n) = σ :=
  Renaming.ext _ _ rfl rfl

theorem id_comp {n : Nat} (σ : Renaming n) :
    compRen (idRen n) σ = σ :=
  Renaming.ext _ _ rfl rfl

theorem comp_assoc {n : Nat} (σ τ ρ : Renaming n) :
    compRen (compRen σ τ) ρ = compRen σ (compRen τ ρ) :=
  Renaming.ext _ _ rfl rfl

theorem inv_comp {n : Nat} (σ : Renaming n) :
    compRen (invRen σ) σ = idRen n :=
  Renaming.ext _ _ (funext (fun x => σ.fg x))
    (funext (fun x => σ.fg x))

theorem comp_inv {n : Nat} (σ : Renaming n) :
    compRen σ (invRen σ) = idRen n :=
  Renaming.ext _ _ (funext (fun x => σ.gf x))
    (funext (fun x => σ.gf x))

theorem inv_inv {n : Nat} (σ : Renaming n) :
    invRen (invRen σ) = σ :=
  Renaming.ext _ _ rfl rfl

/-! ## 2. The action laws -/

theorem map_getD_range (l : List Nat) :
    (List.range l.length).map (fun j => l.getD j 0) = l := by
  apply List.ext_getElem
  · rw [List.length_map, List.length_range]
  · intro i h1 h2
    rw [List.getElem_map, List.getElem_range]
    exact getD_lt h2

/-- **Identity acts trivially** — and unconditionally: the carrier
re-indexing by the identity is the carrier itself, and every store
map is the identity map. -/
theorem act_id (n : Nat) (s : PState) : act (idRen n) s = s := by
  show ({ occ := (List.range s.occ.length).map
            (fun j => s.occ.getD ((idRen n).g j) 0),
          asserted := s.asserted.map (renPair (idRen n)),
          wit := s.wit.map (renPair (idRen n)),
          prot := s.prot.map (renPair (idRen n)),
          obs := s.obs.map (fun cols =>
            cols.map (List.map (idRen n).f)),
          budget := s.budget, licensed := s.licensed,
          refusals := s.refusals.map (renPair (idRen n)),
          halted := s.halted } : PState) = s
  have hpair : renPair (idRen n) = (fun pr : Nat × Nat => pr) := by
    funext pr
    show ((idRen n).f pr.1, (idRen n).f pr.2) = pr
    rfl
  have hmapid : ∀ l : List (Nat × Nat), l.map (renPair (idRen n)) = l := by
    intro l
    rw [hpair]
    exact List.map_id l
  have hobs : s.obs.map (fun cols =>
      cols.map (List.map (idRen n).f)) = s.obs := by
    cases hh : s.obs with
    | none => rfl
    | some cols =>
        show some (cols.map (List.map (idRen n).f)) = some cols
        congr 1
        have : (List.map (idRen n).f) = (fun c : List Nat => c) := by
          funext c
          exact List.map_id c
        rw [this]
        exact List.map_id cols
  have hidg : (fun j => s.occ.getD ((idRen n).g j) 0)
      = (fun j => s.occ.getD j 0) := rfl
  rw [hidg, map_getD_range, hmapid, hmapid, hmapid, hmapid, hobs]

/-- **Composition acts by composition**, on the exact well-formed
scope `n = s.occ.length` — the scope in which the positional
re-indexing of the carrier is meaningful.  Outside it the carrier
re-indexing reads positions the renaming does not govern. -/
theorem act_comp {n : Nat} (σ τ : Renaming n) (s : PState)
    (hn : n ≤ s.occ.length) :
    act (compRen σ τ) s = act σ (act τ s) := by
  have hlen := act_occ_length τ s
  have hocc : (List.range s.occ.length).map
      (fun j => s.occ.getD ((compRen σ τ).g j) 0)
      = (List.range (act τ s).occ.length).map
        (fun j => (act τ s).occ.getD (σ.g j) 0) := by
    rw [hlen]
    apply List.map_congr_left
    intro j hj
    have hjn : j < s.occ.length := List.mem_range.mp hj
    have hgj : σ.g j < s.occ.length := by
      by_cases hjlt : j < n
      · have := σ.gbound j hjlt
        omega
      · rw [σ.gfix j (by omega)]
        exact hjn
    show s.occ.getD (τ.g (σ.g j)) 0 = (act τ s).occ.getD (σ.g j) 0
    show s.occ.getD (τ.g (σ.g j)) 0
      = ((List.range s.occ.length).map
          (fun k => s.occ.getD (τ.g k) 0)).getD (σ.g j) 0
    rw [getD_lt (show σ.g j < ((List.range s.occ.length).map
        (fun k => s.occ.getD (τ.g k) 0)).length by
      rw [List.length_map, List.length_range]
      exact hgj)]
    rw [List.getElem_map, List.getElem_range]
  have hpair : ∀ l : List (Nat × Nat),
      l.map (renPair (compRen σ τ))
        = (l.map (renPair τ)).map (renPair σ) := by
    intro l
    rw [List.map_map]
    apply List.map_congr_left
    intro pr _
    rfl
  have hobs : s.obs.map (fun cols =>
        cols.map (List.map (compRen σ τ).f))
      = (s.obs.map (fun cols => cols.map (List.map τ.f))).map
        (fun cols => cols.map (List.map σ.f)) := by
    cases hh : s.obs with
    | none => rfl
    | some cols =>
        show some (cols.map (List.map (compRen σ τ).f))
          = some ((cols.map (List.map τ.f)).map (List.map σ.f))
        congr 1
        rw [List.map_map]
        apply List.map_congr_left
        intro c _
        show c.map (fun x => σ.f (τ.f x)) = (c.map τ.f).map σ.f
        rw [List.map_map]
        rfl
  show ({ occ := (List.range s.occ.length).map
            (fun j => s.occ.getD ((compRen σ τ).g j) 0),
          asserted := s.asserted.map (renPair (compRen σ τ)),
          wit := s.wit.map (renPair (compRen σ τ)),
          prot := s.prot.map (renPair (compRen σ τ)),
          obs := s.obs.map (fun cols =>
            cols.map (List.map (compRen σ τ).f)),
          budget := s.budget, licensed := s.licensed,
          refusals := s.refusals.map (renPair (compRen σ τ)),
          halted := s.halted } : PState) = act σ (act τ s)
  rw [hocc, hpair, hpair, hpair, hpair, hobs]
  rfl

/-- The action is invertible: acting by the inverse undoes it. -/
theorem act_inv {n : Nat} (σ : Renaming n) (s : PState)
    (hn : n ≤ s.occ.length) : act (invRen σ) (act σ s) = s := by
  rw [← act_comp (invRen σ) σ s hn, inv_comp, act_id]

/-! ## 3. Transport respects identity and composition -/

theorem upBlock_id (n : Nat) (s : PState) (p : Nat) :
    upBlock (act (idRen n) s) ((idRen n).f p) = upBlock s p := by
  rw [act_id]
  rfl

theorem upBlock_comp {n : Nat} (σ τ : Renaming n) (s : PState)
    (hn : n ≤ s.occ.length) (p : Nat) :
    upBlock (act (compRen σ τ) s) ((compRen σ τ).f p)
      = upBlock (act σ (act τ s)) (σ.f (τ.f p)) := by
  rw [act_comp σ τ s hn]
  rfl

theorem upFamily_id (n : Nat) (s : PState) :
    upFamily (act (idRen n) s) = upFamily s := by
  rw [act_id]

theorem upFamily_comp {n : Nat} (σ τ : Renaming n) (s : PState)
    (hn : n ≤ s.occ.length) :
    upFamily (act (compRen σ τ) s) = upFamily (act σ (act τ s)) := by
  rw [act_comp σ τ s hn]

/-- Membership transport respects composition: the two routes from
`s` to the doubly renamed family agree. -/
theorem upFamily_transport_comp {n : Nat} (σ τ : Renaming n)
    (s : PState) (hn : n = s.occ.length) (p : Nat) :
    (upBlock s p ∈ upFamily s
      ↔ upBlock (act (compRen σ τ) s) ((compRen σ τ).f p)
          ∈ upFamily (act (compRen σ τ) s)) := by
  have hnc : n = s.occ.length := hn
  exact upFamily_transport (compRen σ τ) s hnc p

theorem upFamily_transport_id (n : Nat) (s : PState)
    (p : Nat) :
    (upBlock s p ∈ upFamily s
      ↔ upBlock (act (idRen n) s) ((idRen n).f p)
          ∈ upFamily (act (idRen n) s)) := by
  rw [act_id]
  exact Iff.rfl

/-! ## 4. Coherence of `act_up_comm` under composition -/

theorem wf_act {n : Nat} (σ : Renaming n) (s : PState)
    (hn : n = s.occ.length) (hwf : WFStores s) :
    WFStores (act σ s) := by
  obtain ⟨hwa, hww, hwp⟩ := hwf
  refine ⟨?_, ?_, ?_⟩ <;>
    (intro pr hpr
     obtain ⟨q, hq, heq⟩ := List.mem_map.mp hpr
     subst heq
     rw [act_occ_length])
  · obtain ⟨h1, h2⟩ := hwa q hq
    constructor
    · rw [← hn] at h1 h2 ⊢
      exact (σ.fbound_iff q.1).mpr h1
    · rw [← hn] at h1 h2 ⊢
      exact (σ.fbound_iff q.2).mpr h2
  · obtain ⟨h1, h2⟩ := hww q hq
    constructor
    · rw [← hn] at h1 h2 ⊢
      exact (σ.fbound_iff q.1).mpr h1
    · rw [← hn] at h1 h2 ⊢
      exact (σ.fbound_iff q.2).mpr h2
  · obtain ⟨h1, h2⟩ := hwp q hq
    constructor
    · rw [← hn] at h1 h2 ⊢
      exact (σ.fbound_iff q.1).mpr h1
    · rw [← hn] at h1 h2 ⊢
      exact (σ.fbound_iff q.2).mpr h2

/-- **Coherence**: replay of an `Up` block commutes with a COMPOSED
renaming, and the composite route equals the two-step route.  This is
the naturality square closing under composition — the fact that makes
"equivariant" legitimate below. -/
theorem act_up_comm_comp {n : Nat} (σ τ : Renaming n) (s : PState)
    (hn : n = s.occ.length) (hwf : WFStores s)
    (hh : s.halted = false) (p : Nat) (hp : p < s.occ.length) :
    act (compRen σ τ) (replayP (upBlock s p) s)
      = replayP (upBlock (act σ (act τ s)) (σ.f (τ.f p)))
          (act σ (act τ s)) := by
  have hstep := act_up_comm (compRen σ τ) s hn hwf hh p hp
  rw [hstep, act_comp σ τ s (Nat.le_of_eq hn)]
  rfl

/-- The two-step route, spelled out: transport by `τ`, then by `σ`. -/
theorem act_up_comm_twostep {n : Nat} (σ τ : Renaming n) (s : PState)
    (hn : n = s.occ.length) (hwf : WFStores s)
    (hh : s.halted = false) (p : Nat) (hp : p < s.occ.length) :
    act σ (act τ (replayP (upBlock s p) s))
      = replayP (upBlock (act σ (act τ s)) (σ.f (τ.f p)))
          (act σ (act τ s)) := by
  have hext : (replayP (upBlock s p) s).occ.length
      = s.occ.length + 1 := (up_executes s hwf hh p hp).1
  rw [← act_comp σ τ (replayP (upBlock s p) s) (by
    rw [hext, hn]
    omega)]
  exact act_up_comm_comp σ τ s hn hwf hh p hp

/-! ## 5. No selected representative -/

/-- The family is closed under the action, with the transported member
named exactly.  Every source member is an `upBlock s p`, and its image
is the corresponding `upBlock (act sigma s) (sigma.f p)`.  Thus the
family carries the WHOLE orbit rather than merely remaining nonempty. -/
theorem upFamily_orbit_closed {n : Nat} (σ : Renaming n) (s : PState)
    (hn : n = s.occ.length) (b : List PEvent) (hb : b ∈ upFamily s) :
    ∃ p, p < s.occ.length ∧ b = upBlock s p ∧
      upBlock (act σ s) (σ.f p) ∈ upFamily (act σ s) := by
  obtain ⟨p, hp, heq⟩ := (up_iff_legal s b).mp hb
  refine ⟨p, hp, heq, ?_⟩
  exact (upFamily_transport σ s hn p).mp (heq ▸ hb)

/-- **Both orbit members are present**: at the three-occurrence star
the two leaves form one orbit, and the family contains the block at
EACH of them.  No representative is selected. -/
theorem star_orbit_both_present :
    upBlock (treeAt starPolL 2) 1 ∈ upFamily (treeAt starPolL 2) ∧
    upBlock (treeAt starPolL 2) 2 ∈ upFamily (treeAt starPolL 2) ∧
    upBlock (treeAt starPolL 2) 1 ≠ upBlock (treeAt starPolL 2) 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> decide

/-- The family's size is the number of represented parents: it is the
complete list, with no member dropped in favour of an orbit
representative. -/
theorem upFamily_length (s : PState) :
    (upFamily s).length = s.occ.length := by
  unfold upFamily
  rw [List.length_map]
  exact List.length_range

/-! ## 6. Countermodels: weaker data does not supply this structure -/

/-- An arbitrary NON-BIJECTIVE map: everything to the root. -/
def collapseMap : Nat → Nat := fun _ => 0

/-- **Countermodel (non-bijective map)**: `collapseMap` admits no
left inverse at all, so it cannot be the `f` of any renaming — the
`fg` field is unsatisfiable.  This rules out the inverse/group action
and the transport/equivariance results established above.  It does
not claim that non-bijective maps cannot form some different monoid
action under composition. -/
theorem collapse_not_a_renaming :
    ¬ ∃ g : Nat → Nat, ∀ x, g (collapseMap x) = x := by
  intro ⟨g, hg⟩
  have h0 : g 0 = 0 := hg 0
  have h1 : g 0 = 1 := hg 1
  omega

/-- A raw store rename by an arbitrary map — no inverse, so no
carrier re-indexing is even definable; only the relational stores can
be pushed forward. -/
def rawRenamePairs (f : Nat → Nat) (l : List (Nat × Nat)) :
    List (Nat × Nat) := l.map (fun pr => (f pr.1, f pr.2))

/-- **Countermodel (non-bijective pushforward destroys the stores)**:
pushing the three-occurrence path's retained store along
`collapseMap` produces self-pairs, which the well-formedness guard
`wfPair` refuses — the pushforward is not a state of the calculus at
all, so no transport law can hold for it. -/
theorem collapse_pushforward_ill_formed :
    rawRenamePairs collapseMap (treeAt pathPolL 2).wit
      = [(0, 0), (0, 0)] ∧
    (∀ pr ∈ rawRenamePairs collapseMap (treeAt pathPolL 2).wit,
      pr.1 = pr.2) ∧
    (∀ pr ∈ (treeAt pathPolL 2).wit, pr.1 ≠ pr.2) := by
  refine ⟨by decide, ?_, ?_⟩ <;> decide

/-- **Countermodel (equal carrier size supplies nothing)**: the star
and the path at three occurrences have the SAME carrier and hence
literally the same `Up` family, yet no renaming relates them — so
"equal size" is not a renaming, does not act, and satisfies none of
the laws above.  (Imported from `Attachment`, restated here as the
Goal-1 countermodel.) -/
theorem equal_size_supplies_no_law :
    (upFamily (treeAt starPolL 2) = upFamily (treeAt pathPolL 2)) ∧
    ∀ (n : Nat) (σ : Renaming n),
      act σ (treeAt starPolL 2) ≠ treeAt pathPolL 2 :=
  equal_size_not_renaming_related

/-- **Countermodel (equal cost supplies nothing)**: two blocks of the
same family with equal cost execute to non-isomorphic states, so
"equal cost" identifies nothing and induces no transport. -/
theorem equal_cost_supplies_no_law :
    (upBlock (treeAt pathPolL 2) 1 ∈ upFamily (treeAt pathPolL 2)) ∧
    (upBlock (treeAt pathPolL 2) 2 ∈ upFamily (treeAt pathPolL 2)) ∧
    ((upBlock (treeAt pathPolL 2) 1).length
      = (upBlock (treeAt pathPolL 2) 2).length) ∧
    ((tuples4.all fun t => !(isoMatch t
        (replayP (upBlock (treeAt pathPolL 2) 1)
          (treeAt pathPolL 2)).wit
        (replayP (upBlock (treeAt pathPolL 2) 2)
          (treeAt pathPolL 2)).wit)) = true) :=
  equal_cost_non_isomorphic_extensions

/-! ## 7. The equivariance summary — earned, and exactly scoped

Only now, with 1–5 proved, is the vocabulary legitimate.

`Renaming n` carries identity, inverse, and composition satisfying
the group laws (`comp_id`, `id_comp`, `comp_assoc`, `inv_comp`,
`comp_inv`).  `act` is an ACTION of that structure on states:
`act_id` unconditionally, `act_comp` on the well-formed scope
`n <= s.occ.length`, with `act_inv` as the consequence.  The `Up`
grammar is EQUIVARIANT for this action in the following exact sense
and no other: blocks transport (`upBlock_transport`), the family
transports (`upFamily_transport`), transport respects identity and
composition (`upBlock_id`, `upBlock_comp`, `upFamily_id`,
`upFamily_comp`, `upFamily_transport_id`,
`upFamily_transport_comp`), and replay of an `Up` block commutes with
the action coherently under composition (`act_up_comm`,
`act_up_comm_comp`, `act_up_comm_twostep`), on LIVE, STORE-BOUNDED
states.  Where a symmetry remains, the family carries the whole orbit
and selects no representative (`upFamily_orbit_closed`,
`star_orbit_both_present`, `upFamily_length`).

NOT claimed: equivariance of the observation calculus; transport for
multi-edge or relational extensions; any law for maps that are not
renamings — an arbitrary map has no inverse
(`collapse_not_a_renaming`) and its pushforward is not even a legal
store (`collapse_pushforward_ill_formed`); and any structure supplied
by equal carrier size (`equal_size_supplies_no_law`) or equal cost
(`equal_cost_supplies_no_law`), which supply none. -/

theorem equivariance_summary {n : Nat} (σ τ : Renaming n)
    (s : PState) (hn : n = s.occ.length) (hwf : WFStores s)
    (hh : s.halted = false) (p : Nat) (hp : p < s.occ.length) :
    -- group laws
    compRen σ (idRen n) = σ ∧
    compRen (invRen σ) σ = idRen n ∧
    -- action laws
    act (idRen n) s = s ∧
    act (compRen σ τ) s = act σ (act τ s) ∧
    -- transport respects the structure
    upFamily (act (idRen n) s) = upFamily s ∧
    upFamily (act (compRen σ τ) s) = upFamily (act σ (act τ s)) ∧
    -- coherence of replay commutation under composition
    act (compRen σ τ) (replayP (upBlock s p) s)
      = replayP (upBlock (act σ (act τ s)) (σ.f (τ.f p)))
          (act σ (act τ s)) :=
  ⟨comp_id σ, inv_comp σ, act_id n s,
   act_comp σ τ s (Nat.le_of_eq hn),
   upFamily_id n s, upFamily_comp σ τ s (Nat.le_of_eq hn),
   act_up_comm_comp σ τ s hn hwf hh p hp⟩

end RenamingStructure
