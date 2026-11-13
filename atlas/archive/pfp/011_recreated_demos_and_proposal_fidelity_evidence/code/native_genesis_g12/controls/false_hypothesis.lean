import Audit
open Lean Elab Command Meta Derivation

theorem G12.Poison (h : False) :
    ∀ (r : Regime) (π : DRen r.data) (φ : DRen r.forms.length),
      (∀ q ∈ r.reqs, q.1 ≤ q.2) → Nonempty (Iso r (relabel r π φ)) := False.elim h
run_cmd liftTermElabM <| G12.checkWrapper ``Derivation.relabel_iso ``G12.Poison
