import Derivation.SeparationCapacity
import Derivation.Pigeonhole

/-!
# The coloured separation-capacity bound

`contact/analysis/separation_capacity_open.md` §2 recorded this as the
statement NOT in the repository:

> a view that factors through the depth-`d` colour ball, with at most
> `B` distinguishable encoded balls, fails to separate some deep pair
> once `n ≥ B + 2d + 2`.

§3 recorded the blocker as a choice-free pigeonhole, and §4 recorded
the trap: a capacity statement whose view is an unconstrained
`Nat → Fin A` proves nothing about depth-bounded observation, because
without a hypothesis forcing the view to factor through the ball the
radius plays no role and the result is ordinary global pigeonhole.

Both are addressed here.  The pigeonhole is `Pigeonhole.pigeonhole`,
whose enumerated axiom report is choice-free.  The locality hypothesis
is `ViewLocal`, and it is
load-bearing in a specific way worth stating up front: it is what turns
`B` from an ASSUMPTION into a CONSEQUENCE.  For a view factoring
through the radius-`d` ball over a `k`-colour alphabet, the number of
distinguishable balls is at most `k ^ (2 * d + 1)` — a function of the
radius and the alphabet, and of nothing else.  In particular it does
not grow with `n`, which is exactly why the threshold below is a
capacity statement rather than a restatement of pigeonhole.

The deep interior of `reflState n` holds the points `i` with `d < i`
and `i + d < n`, of which there are `n - 2 * d - 1`.  Taking
`B = k ^ (2 * d + 1)`, the threshold `n ≥ B + 2 * d + 2` is exactly the
point at which that interior holds `B + 1` points.

## What is NOT claimed

* No claim about views that do not factor through the ball.  For those
  the radius is inert and the statement below says nothing.
* No claim that `k ^ (2 * d + 1)` is TIGHT.  It is an upper bound on
  the number of distinct balls, obtained by counting colourings; no
  matching lower bound is proved, and none is claimed.
* No claim about the sealed `Generator.profile2` colouring in
  particular.  `colour` here is an arbitrary bounded colouring.
* Nothing here bears on `LocalStrategy`, repair strategies, or
  absolute interior, none of which exist in this repository.
-/

namespace CapacityBound

open SeparationCapacity Pigeonhole

/-! ## 1. Base-`k` encoding of a bounded list

A duplicate-free counting argument needs the balls carried into `Nat`.
Base-`k` positional encoding does that, and is injective on lists of
equal length whose entries are below `k`. -/

def encode (k : Nat) : List Nat → Nat
  | [] => 0
  | x :: t => x + k * encode k t

theorem encode_nil (k : Nat) : encode k [] = 0 := rfl

theorem encode_cons (k x : Nat) (t : List Nat) :
    encode k (x :: t) = x + k * encode k t := rfl

/-- **The counting bound.**  A length-`m` list of colours below `k`
encodes to a value below `k ^ m`. -/
theorem encode_lt (k : Nat) :
    ∀ l : List Nat, (∀ x ∈ l, x < k) → encode k l < k ^ l.length
  | [], _ => by
      show 0 < k ^ 0
      exact Nat.zero_lt_one
  | x :: t, h => by
      have hx : x < k := h x (List.mem_cons_self ..)
      have ht : encode k t < k ^ t.length :=
        encode_lt k t (fun y hy => h y (List.mem_cons_of_mem x hy))
      have hstep : k * (encode k t + 1) ≤ k * k ^ t.length :=
        Nat.mul_le_mul_left k ht
      have hmul : k * (encode k t + 1) = k * encode k t + k := Nat.mul_succ k _
      show x + k * encode k t < k ^ (t.length + 1)
      have hpow : k ^ (t.length + 1) = k * k ^ t.length := by
        rw [Nat.pow_succ, Nat.mul_comm]
      rw [hpow]
      omega

/-- **Injectivity at fixed length.**  Two colour lists of the same
length, both below `k`, with the same encoding, are the same list. -/
theorem encode_inj (k : Nat) :
    ∀ l m : List Nat, l.length = m.length →
      (∀ x ∈ l, x < k) → (∀ x ∈ m, x < k) →
      encode k l = encode k m → l = m
  | [], [], _, _, _, _ => rfl
  | [], _ :: _, hlen, _, _, _ => Nat.noConfusion hlen
  | _ :: _, [], hlen, _, _, _ => Nat.noConfusion hlen
  | x :: t, y :: u, hlen, hx, hy, henc => by
      have hxk : x < k := hx x (List.mem_cons_self ..)
      have hyk : y < k := hy y (List.mem_cons_self ..)
      have ht : ∀ z ∈ t, z < k := fun z hz => hx z (List.mem_cons_of_mem x hz)
      have hu : ∀ z ∈ u, z < k := fun z hz => hy z (List.mem_cons_of_mem y hz)
      have hlen' : t.length = u.length := by
        simp only [List.length_cons] at hlen
        omega
      have henc' : x + k * encode k t = y + k * encode k u := henc
      -- the tails agree, hence so do the heads
      have hkey : encode k t = encode k u := by
        rcases Nat.lt_trichotomy (encode k t) (encode k u) with hlt | heq | hgt
        · exfalso
          have : k * (encode k t + 1) ≤ k * encode k u :=
            Nat.mul_le_mul_left k hlt
          have hm : k * (encode k t + 1) = k * encode k t + k :=
            Nat.mul_succ k _
          omega
        · exact heq
        · exfalso
          have : k * (encode k u + 1) ≤ k * encode k t :=
            Nat.mul_le_mul_left k hgt
          have hm : k * (encode k u + 1) = k * encode k u + k :=
            Nat.mul_succ k _
          omega
      have hhead : x = y := by
        rw [hkey] at henc'
        omega
      have htail : t = u := encode_inj k t u hlen' ht hu hkey
      rw [hhead, htail]

/-! ## 2. Coloured balls and locality -/

/-- The radius-`d` colour ball at `i`: the colours along the ball. -/
def colourBall (colour : Nat → Nat) (i d : Nat) : List Nat :=
  (ball i d).map colour

theorem colourBall_length (colour : Nat → Nat) (i d : Nat) :
    (colourBall colour i d).length = 2 * d + 1 := by
  unfold colourBall
  rw [List.length_map, ball_length]

theorem colourBall_bounded (colour : Nat → Nat) (k : Nat)
    (hc : ∀ x, colour x < k) (i d : Nat) :
    ∀ z ∈ colourBall colour i d, z < k := by
  intro z hz
  obtain ⟨w, _, rfl⟩ := List.mem_map.mp hz
  exact hc w

/-- **The locality hypothesis.**  `v` factors through the radius-`d`
colour ball: its value at `i` is determined by the colours in that
ball and by nothing else.  This is the hypothesis §4 of the residual
document identified as missing; without it the radius below would play
no role. -/
def ViewLocal (v : Nat → Nat) (colour : Nat → Nat) (d : Nat) : Prop :=
  ∃ g : List Nat → Nat, ∀ i, v i = g (colourBall colour i d)

/-- A local view cannot separate two points with the same colour
ball.  Both the view and the ball are named. -/
theorem local_view_blind {v colour : Nat → Nat} {d : Nat}
    (hloc : ViewLocal v colour d) {i j : Nat}
    (hball : colourBall colour i d = colourBall colour j d) :
    v i = v j := by
  obtain ⟨g, hg⟩ := hloc
  rw [hg i, hg j, hball]

/-! ## 3. The capacity bound -/

/-- **The coloured separation-capacity bound.**  Let `colour` take
values below `k` and let `v` factor through the radius-`d` colour
ball.  Once

  `n ≥ k ^ (2 * d + 1) + 2 * d + 2`

the deep interior of `reflState n` holds two distinct points that `v`
does not separate.

The bound `B = k ^ (2 * d + 1)` is DERIVED from the locality
hypothesis, not assumed: it counts the colourings of a radius-`d` ball.
It does not grow with `n`, which is what makes this a capacity
statement rather than an instance of global pigeonhole. -/
theorem capacity_bound (colour v : Nat → Nat) (k d n : Nat)
    (hk : ∀ x, colour x < k)
    (hloc : ViewLocal v colour d)
    (hn : k ^ (2 * d + 1) + 2 * d + 2 ≤ n) :
    ∃ i j, i ≠ j ∧ d < i ∧ i + d < n ∧ d < j ∧ j + d < n ∧ v i = v j := by
  have hcode : ∀ t : Nat, t < k ^ (2 * d + 1) + 1 →
      encode k (colourBall colour (d + 1 + t) d) < k ^ (2 * d + 1) := by
    intro t _
    have hlen := colourBall_length colour (d + 1 + t) d
    have hbd := colourBall_bounded colour k hk (d + 1 + t) d
    have hlt := encode_lt k (colourBall colour (d + 1 + t) d) hbd
    rw [hlen] at hlt
    exact hlt
  obtain ⟨p, hp, q, hq, hpq, heq⟩ :=
    pigeonhole (k ^ (2 * d + 1))
      (fun t => encode k (colourBall colour (d + 1 + t) d)) hcode
  refine ⟨d + 1 + p, d + 1 + q, by omega, by omega, by omega, by omega,
    by omega, ?_⟩
  refine local_view_blind hloc ?_
  refine encode_inj k _ _ ?_ ?_ ?_ heq
  · rw [colourBall_length, colourBall_length]
  · exact colourBall_bounded colour k hk _ _
  · exact colourBall_bounded colour k hk _ _

/-! ## 4. Non-vacuity, both ways

The bound must not be an unfalsifiable refusal.  A local view that DOES
separate a deep pair below the threshold shows the threshold is doing
work; a constant colouring exhibits the degenerate one-colour case.
No threshold minimality or tightness is claimed. -/

/-- With one colour the bound is `1 ^ (2 * d + 1) = 1`, and indeed the
view is constant, so it separates nothing.  This is the degenerate end
of the bound, exhibited rather than assumed. -/
theorem capacity_at_one_colour (d n : Nat) (hn : 2 * d + 3 ≤ n) :
    ∃ i j, i ≠ j ∧ d < i ∧ i + d < n ∧ d < j ∧ j + d < n ∧
      (fun _ : Nat => 0) i = (fun _ : Nat => 0) j := by
  refine capacity_bound (fun _ => 0) (fun _ => 0) 1 d n (fun _ => Nat.zero_lt_one)
    ⟨fun _ => 0, fun _ => rfl⟩ ?_
  have : (1 : Nat) ^ (2 * d + 1) = 1 := Nat.one_pow _
  omega

/-- **The locality hypothesis is load-bearing.**  At exactly `k = 2`,
`d = 0`, and `n = 3`, the deep indices `1` and `2` lie strictly below
the threshold `2 ^ (2 * 0 + 1) + 2 * 0 + 2 = 4`, and the local parity
view separates every distinct deep pair (and, in particular, separates
`1` and `2`). Thus the forced-collision conclusion is false at this
below-threshold instance: `capacity_bound` is not vacuously true of
every local view, and its threshold is not decoration. -/
theorem local_view_can_separate :
    ∃ (colour v : Nat → Nat),
      (∀ x, colour x < 2) ∧
      ViewLocal v colour 0 ∧
      0 < 1 ∧ 1 + 0 < 3 ∧ 0 < 2 ∧ 2 + 0 < 3 ∧
      3 < 2 ^ (2 * 0 + 1) + 2 * 0 + 2 ∧
      v 1 ≠ v 2 ∧
      (∀ i j, 0 < i → i + 0 < 3 → 0 < j → j + 0 < 3 →
        i ≠ j → v i ≠ v j) := by
  refine ⟨fun x => x % 2, fun x => x % 2,
    fun x => Nat.mod_lt x (by decide),
    ⟨fun l => l.headD 0, ?_⟩, by decide, by decide, by decide, by decide,
    by decide, by decide, ?_⟩
  · intro i
    show i % 2 = (colourBall (fun x => x % 2) i 0).headD 0
    rfl
  · intro i j hi0 hi1 hj0 hj1 hij
    have hi : i = 1 ∨ i = 2 := by omega
    have hj : j = 1 ∨ j = 2 := by omega
    rcases hi with rfl | rfl
    · rcases hj with rfl | rfl
      · exact (hij rfl).elim
      · decide
    · rcases hj with rfl | rfl
      · decide
      · exact (hij rfl).elim

end CapacityBound
