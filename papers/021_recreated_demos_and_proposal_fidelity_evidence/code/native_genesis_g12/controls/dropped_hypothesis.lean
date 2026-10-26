import Audit
open Lean Elab Command Meta Derivation

theorem G12.Dropped (A B : Regime)
    (hdata : A.data = B.data) (hforms : A.forms = B.forms)
    (hInst : ∀ i, i ∈ A.insts ↔ i ∈ B.insts)
    (hRule : ∀ f, f ∈ A.rules ↔ f ∈ B.rules)
    (hReq : ∀ q, q ∈ A.reqs ↔ q ∈ B.reqs)
    (hAord : ∀ q ∈ A.reqs, q.1 ≤ q.2) : Nonempty (Iso A B) :=
  G12.Wrappers.Derivation_Iso_of_components A B hdata hforms hInst hRule hReq hAord
    (fun q hq => hAord q ((hReq q).mpr hq))
run_cmd liftTermElabM <| G12.checkWrapper ``Derivation.Iso.of_components ``G12.Dropped
