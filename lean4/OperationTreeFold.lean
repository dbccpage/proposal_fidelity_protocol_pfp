import Sweeper
/-!
A genuinely recursive fold for the existing Symbol Game `OperationTree`.

The fold retains every child output and composes every child authority effect.
Its closure theorem is deliberately named *internal*: it concerns only the
finite operation table admitted below and is not a proof of the monograph's
universal authority firewall.
-/

namespace PaperER007

open SnSymbolGameAndPackets

def admittedOperationEffect (_op : SgOperation) : AuthorityEffect :=
  .none

def composeAuthorityEffect : AuthorityEffect → AuthorityEffect → AuthorityEffect
  | .none, .none => .none
  | _, _ => .claimed

structure OperationFold where
  outputs : List ExtendedColor
  authorityEffect : AuthorityEffect
  deriving Repr

def foldOperationTree : OperationTree → OperationFold
  | .node op none =>
      { outputs := [operationOutput op]
        authorityEffect := admittedOperationEffect op }
  | .node op (some child) =>
      let childFold := foldOperationTree child
      { outputs := operationOutput op :: childFold.outputs
        authorityEffect :=
          composeAuthorityEffect (admittedOperationEffect op) childFold.authorityEffect }

theorem recursive_fold_retains_child_outputs (op : SgOperation)
    (child : OperationTree) :
    (foldOperationTree (.node op (some child))).outputs =
      operationOutput op :: (foldOperationTree child).outputs :=
  rfl

theorem recursive_fold_composes_child_effect (op : SgOperation)
    (child : OperationTree) :
    (foldOperationTree (.node op (some child))).authorityEffect =
      composeAuthorityEffect (admittedOperationEffect op)
        (foldOperationTree child).authorityEffect :=
  rfl

theorem admitted_operation_effect_none (op : SgOperation) :
    admittedOperationEffect op = AuthorityEffect.none :=
  rfl

/--
Internal effect closure for the admitted `SgOperation` table only.  This does
not derive or replace the externally imposed universal authority firewall.
-/
theorem internal_operation_tree_effect_closure :
    ∀ tree : OperationTree,
      (foldOperationTree tree).authorityEffect = AuthorityEffect.none
  | .node _ none => rfl
  | .node op (some child) => by
      simp [foldOperationTree, admittedOperationEffect,
        internal_operation_tree_effect_closure child, composeAuthorityEffect]

theorem internal_operation_tree_outputs_not_authority :
    ∀ (tree : OperationTree) (output : ExtendedColor),
      output ∈ (foldOperationTree tree).outputs →
        output ≠ ExtendedColor.authority
  | .node op none, output => by
      simp only [foldOperationTree, List.mem_cons, List.not_mem_nil, or_false]
      intro hOutput
      subst output
      exact operation_output_not_authority op
  | .node op (some child), output => by
      simp only [foldOperationTree, List.mem_cons]
      intro hOutput
      rcases hOutput with hHere | hChild
      · subst output
        exact operation_output_not_authority op
      · exact internal_operation_tree_outputs_not_authority child output hChild

#print axioms PaperER007.recursive_fold_retains_child_outputs
#print axioms PaperER007.recursive_fold_composes_child_effect
#print axioms PaperER007.admitted_operation_effect_none
#print axioms PaperER007.internal_operation_tree_effect_closure
#print axioms PaperER007.internal_operation_tree_outputs_not_authority

end PaperER007
