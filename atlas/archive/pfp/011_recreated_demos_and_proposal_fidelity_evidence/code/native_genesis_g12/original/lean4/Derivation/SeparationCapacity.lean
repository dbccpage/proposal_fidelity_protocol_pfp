import Derivation.Generator

/-!
# Depth-`d` outrun on the reflective chain (G2)

The sealed generator proves that depth-1 observation is outrun by chain
growth (`Generator.generation_never_dries`) and exhibits the depth-2
instances `depth2_separates_near_ends_n4` and `depth2_obstruction_n5`.
This module generalizes the structural half to every fixed radius.

**Radius convention, stated exactly.**  Here `d` is the GRAPH RADIUS of
the observed ball.  The sealed `Generator.profile2` observes the centre
together with its in- and out-neighbour profiles, i.e. the ball
`{i-1, i, i+1}` — radius ONE, not two.  Under that reading sealed
"depth `k`" indexes radius `k-1`, and the threshold `2 * d + 3` at
`d = 1` gives `n = 5`, the length of the sealed `depth2_obstruction_n5`
instance.  §3 turns the reading into a typed correspondence for every
chain length: over interior indices, sealed `Generator.profile2`
equality and this module's radius-one `profileD` equality are the SAME
relation.  The two sealed instances are then carried across that general
theorem.

**What is proved here and what remains open.**  Proved here: for every fixed
radius, all deep-interior points share one depth-`d` profile
(`depth_d_outrun`), horizon-free — no bound on `n` beyond deepness of
the two points — and a colliding deep pair exists from `n ≥ 2d + 3`
(`depth_d_obstruction`); and the general radius-one correspondence of
§3.  The companion modules `Pigeonhole` and `CapacityBound` prove the
coloured finite-alphabet capacity bound, and `LocalStrategy` derives its
class-relative repair consequence.  Identity-grade observation outside
that declared class, absolute interior, and "no outside" remain outside
this module's statement language.  See the investigation record for the
exact boundary.
-/

namespace SeparationCapacity

open Generator RefusalFrontier

/-! ## List lemmas for the sealed successor relation -/

theorem filter_range_decide_eq (n i : Nat) :
    (List.range n).filter (fun k => decide (k = i)) =
      if i < n then [i] else [] := by
  induction n with
  | zero => simp
  | succ n ih =>
      rw [List.range_succ, List.filter_append, ih]
      rcases Nat.lt_trichotomy i n with hlt | heq | hgt
      · have hne : ¬n = i := by omega
        have hout : i < n + 1 := by omega
        simp [hlt, hne, hout]
      · subst i
        have hnot : ¬n < n := Nat.lt_irrefl n
        have hout : n < n + 1 := by omega
        simp [hnot, hout]
      · have hnot : ¬i < n := by omega
        have hne : ¬n = i := by omega
        have hout : ¬i < n + 1 := by omega
        simp [hnot, hne, hout]

theorem filter_range_succ_eq (n i : Nat) (hpos : 0 < i) (hle : i ≤ n) :
    (List.range n).filter (fun k => decide (k + 1 = i)) = [i - 1] := by
  have hpred : (fun k => decide (k + 1 = i)) =
      (fun k => decide (k = i - 1)) := by
    funext k
    by_cases h : k + 1 = i
    · have h' : k = i - 1 := by omega
      have hrestore : i - 1 + 1 = i := Nat.sub_add_cancel (by omega)
      simp [h', hrestore]
    · have h' : ¬k = i - 1 := by omega
      simp [h, h']
  rw [hpred, filter_range_decide_eq]
  simp [show i - 1 < n by omega]

theorem filter_range_eq (n i : Nat) (hlt : i < n) :
    (List.range n).filter (fun k => decide (k = i)) = [i] := by
  rw [filter_range_decide_eq]
  simp [hlt]

/-- Ordered radius-`d` ball around `i`: `[i-d, …, i+d]`.  Unclipped;
on the deep interior no clipping occurs, which is the content of
`profileD_deep`. -/
def ball (i d : Nat) : List Nat :=
  (List.range (2 * d + 1)).map (fun k => i - d + k)

theorem ball_length (i d : Nat) : (ball i d).length = 2 * d + 1 := by
  simp [ball]

/-- Depth-`d` structural profile: the SEALED depth-1 profiles along the
ball.  This is `Generator.profile1` on `Generator.reflState`, not a
private mirror, so every statement below is about the sealed chain. -/
def profileD (n i d : Nat) : List (Bool × Bool × Bool) :=
  (ball i d).map (profile1 (reflState n))

/-- Every point of a deep ball is interior, so the whole deep profile
is the constant `(true, true, true)` list.  This is the structural
uniformity the outrun rests on. -/
theorem profileD_deep (n i d : Nat) (hlo : d < i) (hhi : i + d < n) :
    profileD n i d
      = (List.range (2 * d + 1)).map (fun _ => (true, true, true)) := by
  unfold profileD ball
  rw [List.map_map]
  apply List.map_congr_left
  intro k hk
  have hkr := List.mem_range.mp hk
  show profile1 (reflState n) (i - d + k) = (true, true, true)
  apply middle_profile
  · omega
  · omega

/-- **G2 — the depth-`d` outrun.**  All deep-interior points share one
depth-`d` profile.  Horizon-free: the statement carries no threshold,
only deepness of the two points.

Scope: this is the STRUCTURAL profile.  A regime that also colours the
carrier is not covered; the constant-profile argument says nothing
about colours. -/
theorem depth_d_outrun (n i j d : Nat)
    (hi0 : d < i) (hi1 : i + d < n) (hj0 : d < j) (hj1 : j + d < n) :
    profileD n i d = profileD n j d := by
  rw [profileD_deep n i d hi0 hi1, profileD_deep n j d hj0 hj1]

/-- Obstruction form: a colliding deep pair exists from `n ≥ 2d + 3`.
The threshold is derived, not assumed — it is exactly the least `n`
at which the deep interior holds two distinct points. -/
theorem depth_d_obstruction (d n : Nat) (hn : 2 * d + 3 ≤ n) :
    ∃ i j, i ≠ j ∧ d < i ∧ i + d < n ∧ d < j ∧ j + d < n ∧
      profileD n i d = profileD n j d :=
  ⟨d + 1, d + 2, by omega, by omega, by omega, by omega, by omega,
   depth_d_outrun n (d + 1) (d + 2) d (by omega) (by omega)
     (by omega) (by omega)⟩

/-! ## General radius-one correspondence with sealed depth 2

Sealed `Generator.profile2` reads the radius-ONE ball.  On an interior
point its incoming and outgoing edge lists are singletons, so it carries
the centre, left, and right depth-one profiles.  `profileD · · 1` carries
the same three values in list order.  The lemmas below prove the exact
shapes and then the equality correspondence for arbitrary `n`.
-/

theorem incoming_edges_interior (n i : Nat) (hpos : 0 < i) (hle : i ≤ n) :
    (reflState n).rel.filter (fun p => decide (p.2 = i)) = [(i - 1, i)] := by
  rw [reflective_chain_successor_relation, List.filter_map]
  change List.map (fun k => (k, k + 1))
    ((List.range n).filter (fun k => decide (k + 1 = i))) = [(i - 1, i)]
  rw [filter_range_succ_eq n i hpos hle]
  simp [Nat.sub_add_cancel hpos]

theorem outgoing_edges_interior (n i : Nat) (hlt : i < n) :
    (reflState n).rel.filter (fun p => decide (p.1 = i)) = [(i, i + 1)] := by
  rw [reflective_chain_successor_relation, List.filter_map]
  change List.map (fun k => (k, k + 1))
    ((List.range n).filter (fun k => decide (k = i))) = [(i, i + 1)]
  rw [filter_range_eq n i hlt]
  rfl

theorem profile2_interior (n i : Nat) (hpos : 0 < i) (hlt : i < n) :
    profile2 (reflState n) i =
      (profile1 (reflState n) i,
       [profile1 (reflState n) (i - 1)],
       [profile1 (reflState n) (i + 1)]) := by
  unfold profile2
  rw [incoming_edges_interior n i hpos (by omega),
      outgoing_edges_interior n i hlt]
  rfl

theorem profileD_radius_one (n i : Nat) (hpos : 0 < i) :
    profileD n i 1 =
      [profile1 (reflState n) (i - 1),
       profile1 (reflState n) i,
       profile1 (reflState n) (i + 1)] := by
  have hcenter : i - 1 + 1 = i := Nat.sub_add_cancel (by omega)
  have hright : i - 1 + 2 = i + 1 := by omega
  simp [profileD, ball, List.range_succ, hcenter, hright]

/-- **T5 — general-`n` profile correspondence.**  On every pair of
interior indices, sealed depth-2 equality and radius-one structural
profile equality are equivalent. -/
theorem radius_one_agrees_with_sealed_depth2 (n i j : Nat)
    (hi0 : 0 < i) (hi1 : i < n) (hj0 : 0 < j) (hj1 : j < n) :
    (profile2 (reflState n) i = profile2 (reflState n) j ↔
      profileD n i 1 = profileD n j 1) := by
  rw [profile2_interior n i hi0 hi1, profile2_interior n j hj0 hj1,
      profileD_radius_one n i hi0, profileD_radius_one n j hj0]
  simp only [Prod.mk.injEq, List.cons.injEq, and_true]
  constructor
  · rintro ⟨hcenter, hleft, hright⟩
    exact ⟨hleft, hcenter, hright⟩
  · rintro ⟨hleft, hcenter, hright⟩
    exact ⟨hcenter, hleft, hright⟩

/-- **The `n = 5` correspondence, and the sealed collision carried
across it.**  First conjunct: over the interior indices `1, 2, 3, 4` of
`reflState 5`, sealed `Generator.profile2` equality and radius-one
`profileD` equality are the same relation.  Second and third conjuncts:
the deep pair `(2, 3)` of `Generator.depth2_obstruction_n5`, transported
— the proof consumes that sealed theorem and does not appeal to
`depth_d_obstruction`. -/
theorem radius_one_agrees_with_sealed_depth2_n5 :
    (∀ i ∈ [1, 2, 3, 4], ∀ j ∈ [1, 2, 3, 4],
        (profile2 (reflState 5) i = profile2 (reflState 5) j ↔
          profileD 5 i 1 = profileD 5 j 1))
      ∧ profileD 5 2 1 = profileD 5 3 1 ∧ (2 : Nat) ≠ 3 :=
  have corr : ∀ i ∈ [1, 2, 3, 4], ∀ j ∈ [1, 2, 3, 4],
      (profile2 (reflState 5) i = profile2 (reflState 5) j ↔
        profileD 5 i 1 = profileD 5 j 1) := by decide
  ⟨corr,
   (corr 2 (by decide) 3 (by decide)).mp depth2_obstruction_n5.1,
   depth2_obstruction_n5.2⟩

/-- **The `n = 4` correspondence, and the sealed separation carried
across it.**  First conjunct: the same equivalence over the interior
indices `1, 2, 3` of `reflState 4`.  Second conjunct: the pair `(1, 3)`
that `Generator.depth2_separates_near_ends_n4` separates is separated by
the radius-one profile too — again proved from the sealed theorem.
Third conjunct: the arithmetic reason this is consistent with
`depth_d_outrun` rather than a counterexample to it — at `n = 4` and
radius one the deepness side-conditions `1 < i` and `i + 1 < 4` hold
only at `i = 2`, so `(1, 3)` is not a deep pair.  That conjunct is
arithmetic and mentions no profile; it is stated inside this theorem so
the reason travels with the result it explains. -/
theorem radius_one_agrees_with_sealed_depth2_n4 :
    (∀ i ∈ [1, 2, 3], ∀ j ∈ [1, 2, 3],
        (profile2 (reflState 4) i = profile2 (reflState 4) j ↔
          profileD 4 i 1 = profileD 4 j 1))
      ∧ profileD 4 1 1 ≠ profileD 4 3 1
      ∧ ∀ i, 1 < i → i + 1 < 4 → i = 2 :=
  have corr : ∀ i ∈ [1, 2, 3], ∀ j ∈ [1, 2, 3],
      (profile2 (reflState 4) i = profile2 (reflState 4) j ↔
        profileD 4 i 1 = profileD 4 j 1) := by decide
  ⟨corr,
   fun h => depth2_separates_near_ends_n4
     ((corr 1 (by decide) 3 (by decide)).mpr h),
   fun i h0 h1 => by omega⟩

end SeparationCapacity
