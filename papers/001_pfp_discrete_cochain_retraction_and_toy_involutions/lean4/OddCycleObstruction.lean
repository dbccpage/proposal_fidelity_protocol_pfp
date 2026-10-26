/-
  The Symbol Game: Formal Proof of Odd-Cycle Sign Obstruction on C3.
  AuthorityEffect: None.
-/

namespace SymbolGame001

/-- Discrete gauge sign on a vertex. -/
inductive GaugeSign : Type
  | neg : GaugeSign
  | pos : GaugeSign
  deriving DecidableEq, Repr

def GaugeSign.toInt : GaugeSign → Int
  | GaugeSign.neg => -1
  | GaugeSign.pos => 1

/-- Gauge transformation on an edge (u, v): eta(u) * eta(v). -/
def edgeGaugeProduct (s_u s_v : GaugeSign) : Int :=
  s_u.toInt * s_v.toInt

/-- 
  Theorem: On a 3-cycle C3, no gauge assignment can flip the sign of all 3 edges simultaneously.
  Any alternating sign gauge requires product of edge signs to be (-1)^3 = -1,
  but (eta_0 * eta_1) * (eta_1 * eta_2) * (eta_2 * eta_0) = (eta_0)^2 * (eta_1)^2 * (eta_2)^2 = +1.
-/
theorem odd_cycle_c3_sign_obstruction
    (eta0 eta1 eta2 : GaugeSign) :
    ¬ (edgeGaugeProduct eta0 eta1 = -1 ∧ 
       edgeGaugeProduct eta1 eta2 = -1 ∧ 
       edgeGaugeProduct eta2 eta0 = -1) := by
  intro h
  rcases h with ⟨h01, h12, h20⟩
  have h_prod : (edgeGaugeProduct eta0 eta1) * (edgeGaugeProduct eta1 eta2) * (edgeGaugeProduct eta2 eta0) = -1 := by
    rw [h01, h12, h20]
    rfl
  dsimp [edgeGaugeProduct] at h_prod
  -- Evaluate by cases on eta0, eta1, eta2
  cases eta0 <;> cases eta1 <;> cases eta2 <;> revert h_prod <;> decide

end SymbolGame001
