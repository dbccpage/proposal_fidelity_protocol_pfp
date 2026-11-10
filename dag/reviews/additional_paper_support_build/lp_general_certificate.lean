/- Review scope: integer finite fixtures and stated hypotheses; no general real Lp, Clarkson, or Schatten theorem. AuthorityEffect: None. -/
import Init.Omega
import «lp_cochains»

/-!
# LP-GENERAL-CERTIFICATE: General Finite Matrix Certificate Optimality Theorem

In the Finite Obstruction Calculus on an arbitrary finite cell complex or graph of dimension $m$,
let:
- $\omega \in \mathbb{Z}^m$ be an input 1-cochain,
- $D : \mathbb{Z}^k \to \mathbb{Z}^m$ be an arbitrary discrete coboundary operator,
- $w \in \mathbb{N}^m$ be positive edge/cell weights,
- $r \in \mathbb{Z}^m$ be a candidate primal residual,
- $z \in \mathbb{Z}^m$ be a candidate dual circulation certificate.

If the certificate satisfies:
1. Exact cycle condition / gauge annihilation: $\langle z, D p \rangle = 0$ for all potentials $p$,
2. Capacity bounds: $|z_e| \le w_e$ for all $e \in \{1, \dots, m\}$,
3. Zero duality gap: $\|r\|_{1, w} = \langle z, \omega \rangle$,

Then $r$ is guaranteed globally optimal across the entire infinite affine subspace:
  $\|r\|_{1, w} \le \|\omega + D p'\|_{1, w}$ for ALL alternative potentials $p' \in \mathbb{Z}^k$.

AuthorityEffect: None.
-/

theorem int_mul_le_weight_abs (z r : Int) (w : Nat) (hz : z.natAbs ≤ w) :
    z * r ≤ (w : Int) * (r.natAbs : Int) := by
  have h1 : z * r ≤ ((z * r).natAbs : Int) := by omega
  have h2 : (z * r).natAbs = z.natAbs * r.natAbs := Int.natAbs_mul z r
  have h3 : z.natAbs * r.natAbs ≤ w * r.natAbs := Nat.mul_le_mul_right r.natAbs hz
  have h4 : ((z.natAbs * r.natAbs : Nat) : Int) ≤ ((w * r.natAbs : Nat) : Int) := by omega
  rw [h2] at h1
  omega

/-- Dual capacity feasibility condition |z_e| ≤ w_e for all coordinates. -/
def satisfies_capacity : List Int → List Nat → Prop
  | [], [] => True
  | x :: xs, w :: ws => x.natAbs ≤ w ∧ satisfies_capacity xs ws
  | _, _ => False

theorem vec_add_length (u v : List Int) (h : u.length = v.length) :
    (vec_add u v).length = u.length := by
  induction u generalizing v with
  | nil =>
    cases v with
    | nil => rfl
    | cons => simp at h
  | cons u_hd u_tl ih =>
    cases v with
    | nil => simp at h
    | cons v_hd v_tl =>
      simp [vec_add]
      apply ih v_tl
      simp at h
      exact h

/-- Bilinearity / distributivity of dot product over vector addition. -/
theorem dot_vec_add (z u v : List Int) (hu : z.length = u.length) (hv : z.length = v.length) :
    dot z (vec_add u v) = dot z u + dot z v := by
  induction z generalizing u v with
  | nil =>
    cases u with
    | cons => simp at hu
    | nil =>
      cases v with
      | cons => simp at hv
      | nil => simp [dot]
  | cons z_hd z_tl ih =>
    cases u with
    | nil => simp at hu
    | cons u_hd u_tl =>
      cases v with
      | nil => simp at hv
      | cons v_hd v_tl =>
        simp [dot, vec_add]
        rw [Int.mul_add]
        have ih_step := ih u_tl v_tl (by simp at hu; exact hu) (by simp at hv; exact hv)
        omega

/-- Discrete Hölder / dual norm bound: ⟨z, r⟩ ≤ ‖r‖_{1, w} under capacity |z_e| ≤ w_e. -/
theorem dot_le_weighted_l1_norm (z : List Int) (w : List Nat) (r : List Int)
    (hcap : satisfies_capacity z w) (hlen1 : z.length = w.length) (hlen2 : z.length = r.length) :
    dot z r ≤ l1_norm w r := by
  induction z generalizing w r with
  | nil =>
    cases w with
    | cons => simp at hlen1
    | nil =>
      cases r with
      | cons => simp at hlen2
      | nil => simp [dot, l1_norm]
  | cons z_hd z_tl ih =>
    cases w with
    | nil => simp at hlen1
    | cons w_hd w_tl =>
      cases r with
      | nil => simp at hlen2
      | cons r_hd r_tl =>
        simp [satisfies_capacity] at hcap
        simp [dot, l1_norm]
        have h_head := int_mul_le_weight_abs z_hd r_hd w_hd hcap.1
        have h_tail := ih w_tl r_tl hcap.2 (by simp at hlen1; exact hlen1) (by simp at hlen2; exact hlen2)
        omega

/-- Theorem: General Finite Matrix Certificate Optimality Theorem:
    For any finite dimension m, any input cochain ω, any coboundary operator D,
    and any positive weights w:
    If a dual circulation z annihilates all gauge shifts (⟨z, D p⟩ = 0 for all p),
    satisfies coordinatewise capacity bounds (|z_e| ≤ w_e),
    and exhibits zero duality gap against candidate residual r (‖r‖_{1, w} = ⟨z, ω⟩),
    then r is globally optimal: for ALL alternative potentials p',
      ‖r‖_{1, w} ≤ ‖ω + D p'‖_{1, w}. -/
theorem general_finite_certificate_optimality
    (z : List Int) (w : List Nat) (omega : List Int) (r : List Int)
    (coboundary : List Int → List Int)
    (hlen_w : z.length = w.length)
    (hlen_omega : z.length = omega.length)
    (hcoboundary_len : ∀ p', (coboundary p').length = z.length)
    (hcirc : ∀ p', dot z (coboundary p') = 0)
    (hcap : satisfies_capacity z w)
    (hgap : l1_norm w r = dot z omega)
    (p' : List Int) :
    l1_norm w r ≤ l1_norm w (vec_add omega (coboundary p')) := by
  have hlen_cob : (coboundary p').length = omega.length := by
    rw [hcoboundary_len p', hlen_omega]
  have h_add : dot z (vec_add omega (coboundary p')) = dot z omega + dot z (coboundary p') := by
    apply dot_vec_add z omega (coboundary p') hlen_omega (by rw [hcoboundary_len p'])
  have h_circ_eval := hcirc p'
  have h_gauge : dot z (vec_add omega (coboundary p')) = dot z omega := by
    rw [h_add, h_circ_eval, Int.add_zero]
  have h_vec_add_len : (vec_add omega (coboundary p')).length = z.length := by
    have h1 : (vec_add omega (coboundary p')).length = omega.length := by
      apply vec_add_length omega (coboundary p') (by rw [hcoboundary_len p', hlen_omega])
    rw [h1, ← hlen_omega]
  have h_holder : dot z (vec_add omega (coboundary p')) ≤ l1_norm w (vec_add omega (coboundary p')) := by
    apply dot_le_weighted_l1_norm z w (vec_add omega (coboundary p')) hcap hlen_w (by rw [h_vec_add_len])
  rw [hgap]
  rw [← h_gauge]
  exact h_holder

#print axioms dot_vec_add
#print axioms dot_le_weighted_l1_norm
#print axioms general_finite_certificate_optimality
