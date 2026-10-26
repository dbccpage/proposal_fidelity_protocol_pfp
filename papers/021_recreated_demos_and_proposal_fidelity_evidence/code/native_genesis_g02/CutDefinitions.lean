import Lean

namespace HigherStructure

def subsetsOf : List Nat → List (List Nat)
  | [] => [[]]
  | x :: xs => subsetsOf xs ++ (subsetsOf xs).map (fun s => x :: s)

def cutCensus (n a b : Nat) : Nat :=
  ((subsetsOf (List.range n)).filter
    (fun A => (decide (a ∈ A)) && !(decide (b ∈ A)))).length

end HigherStructure
