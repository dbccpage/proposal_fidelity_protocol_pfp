import «l1c_t03_weak_duality»

/-!
# Theorem L1C-T4: Primal-Dual Complementary Slackness Certificate

In L1-native cohomology, an explicit primal residual r = ω + d₀ p and a dual
circulation z form a mutually certifying optimal pair if and only if they satisfy
the coordinatewise complementary slackness condition:
  z_e = w_e * sgn(r_e) whenever r_e ≠ 0, and |z_e| ≤ w_e when r_e = 0.

Consequence:
- The duality gap Δ = ‖r‖_{1,w} - ⟨z, ω⟩ vanishes identically (Δ = 0).
- r achieves the exact minimum L1 quotient norm: ‖r‖_{1,w} ≤ ‖ω + d₀ p'‖_{1,w} for ALL p'.
- z achieves the exact maximum circulation flux.

AuthorityEffect: None.
-/

/-- Coordinatewise complementary slackness on edge coordinate e:
    z_e * r_e = w_e * |r_e|. -/
def complementary_slackness_edge (z_e : Int) (r_e : Int) (w_e : Nat) : Prop :=
  z_e * r_e = (w_e : Int) * (r_e.natAbs : Int)

/-- Coordinatewise certificate for a 3-edge graph. -/
structure ComplementarySlackness3 (z : Cochain3) (r : Cochain3) (w : Weights3) : Prop where
  cs0 : complementary_slackness_edge z.e0 r.e0 w.w0
  cs1 : complementary_slackness_edge z.e1 r.e1 w.w1
  cs2 : complementary_slackness_edge z.e2 r.e2 w.w2

/-- Lemma: Under complementary slackness, the pairing ⟨z, r⟩ equals the L1 norm ‖r‖_{1, w}. -/
theorem pairing_eq_l1_norm_of_cs (z : Cochain3) (r : Cochain3) (w : Weights3)
    (hcs : ComplementarySlackness3 z r w) :
    pairing3 z r = l1_norm3 w r := by
  simp [pairing3, l1_norm3]
  rw [hcs.cs0, hcs.cs1, hcs.cs2]

/-- Theorem L1C-T4a (Zero Duality Gap Certificate):
    If z is a circulation and (z, r, w) satisfy complementary slackness,
    then the circulation pairing on ω exactly equals the primal L1 norm:
      ⟨z, ω⟩ = ‖r‖_{1, w}. -/
theorem l1c_t04_zero_duality_gap (omega : Cochain3) (p : Potential3) (z : Cochain3) (w : Weights3)
    (hcirc : is_cycle3_circulation z)
    (hcs : ComplementarySlackness3 z (residual3 omega p) w) :
    pairing3 z omega = l1_norm3 w (residual3 omega p) := by
  have hgauge : pairing3 z omega = pairing3 z (residual3 omega p) :=
    circulation_pairing_gauge_invariant z omega p hcirc
  rw [hgauge]
  exact pairing_eq_l1_norm_of_cs z (residual3 omega p) w hcs

/-- Theorem L1C-T4b (Certified Primal Optimality):
    Under the complementary slackness certificate, r = ω + d₀ p is globally optimal:
    for every other potential p', ‖r‖_{1, w} ≤ ‖ω + d₀ p'‖_{1, w}. -/
theorem l1c_t04_primal_optimality (omega : Cochain3) (p : Potential3) (z : Cochain3) (w : Weights3)
    (hcirc : is_cycle3_circulation z)
    (hcap : satisfies_capacity_bound z w)
    (hcs : ComplementarySlackness3 z (residual3 omega p) w)
    (p' : Potential3) :
    l1_norm3 w (residual3 omega p) ≤ l1_norm3 w (residual3 omega p') := by
  have hgap : l1_norm3 w (residual3 omega p) = pairing3 z omega := by
    rw [l1c_t04_zero_duality_gap omega p z w hcirc hcs]
  rw [hgap]
  exact l1c_t03_weak_duality omega p' z w hcirc hcap

#print axioms pairing_eq_l1_norm_of_cs
#print axioms l1c_t04_zero_duality_gap
#print axioms l1c_t04_primal_optimality
