import ExactRat.Laws

/-!
# Determinants and leading minors over `QN`

Matrices are lists of rows. The determinant expands along the first row
(Laplace). The recursion is structural in a size bound, so the kernel
evaluates it on concrete matrices and `decide` can check a claim about one.

AuthorityEffect: None
-/

namespace ExactRat

abbrev Mat := List (List QN)

/-- The matrix without its first row and without column `j`. -/
def minorAt (rest : Mat) (j : Nat) : Mat := rest.map (fun r => r.eraseIdx j)

/-- Laplace expansion along the first row, with a size bound for recursion. -/
def detAux : Nat → Mat → QN
  | 0, _ => 1
  | _, [] => 1
  | n + 1, row :: rest =>
    (List.range row.length).foldl
      (fun acc j =>
        let t := row.getD j 0 * detAux n (minorAt rest j)
        if j % 2 = 0 then acc + t else acc - t)
      0

def det (m : Mat) : QN := detAux m.length m

/-- The leading principal `k` by `k` block. -/
def leading (m : Mat) (k : Nat) : Mat := (m.take k).map (fun r => r.take k)

/-- The leading principal minors, of orders 1 to the size of the matrix. -/
def leadingMinors (m : Mat) : List QN := (List.range m.length).map (fun k => det (leading m (k + 1)))

/-- The 1-based index of the first entry that is not positive, if any. -/
def firstNonpositive : List QN → Nat → Option Nat
  | [], _ => none
  | x :: rest, i => if QN.pos x then firstNonpositive rest (i + 1) else some i

/-- Every leading minor is positive (Sylvester's criterion for a symmetric
matrix; symmetry is checked separately where it is needed). -/
def minorsPositive (m : Mat) : Bool := (firstNonpositive (leadingMinors m) 1).isNone

def isSymmetric (m : Mat) : Bool :=
  (List.range m.length).all fun i =>
    (List.range m.length).all fun j =>
      decide ((m.getD i []).getD j 0 = (m.getD j []).getD i 0)

theorem det_one_by_one (x : QN) : det [[x]] = x := by
  show 0 + x * 1 = x
  rw [QN.zero_add, QN.mul_one]

theorem det_two_by_two (a b c d : QN) : det [[a, b], [c, d]] = a * d - b * c := by
  show 0 + a * (0 + d * 1) - b * (0 + c * 1) = a * d - b * c
  rw [QN.zero_add, QN.zero_add, QN.zero_add, QN.mul_one, QN.mul_one]

end ExactRat
