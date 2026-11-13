-- Vendored for Companion 007 from lean4/GrammarDepthCeiling.lean at commit
-- 52cb5457f6c485ba548cfd292f6012a941ed22cf.
-- This comment is the only change from that source file.

/-!
PaperER007's narrow fixed-alphabet nesting lemma.

This file models only unary terms built from an already declared symbol type and
an already declared operator type.  It proves that repeatedly applying one
declared unary operator cannot introduce an undeclared symbol or operator.  It
does not formalize the monograph's full grammar ceiling, parser, typed operad,
or denotational semantics.
-/

namespace PaperER007

universe u v

inductive FixedAlphabetTerm (Symbol : Type u) (Operator : Type v) where
  | atom : Symbol → FixedAlphabetTerm Symbol Operator
  | unary : Operator → FixedAlphabetTerm Symbol Operator →
      FixedAlphabetTerm Symbol Operator

namespace FixedAlphabetTerm

variable {Symbol : Type u} {Operator : Type v}

def symbolsDeclared
    (allowedSymbol : Symbol → Prop) :
    FixedAlphabetTerm Symbol Operator → Prop
  | .atom symbol => allowedSymbol symbol
  | .unary _ body => symbolsDeclared allowedSymbol body

def operatorsDeclared
    (allowedOperator : Operator → Prop) :
    FixedAlphabetTerm Symbol Operator → Prop
  | .atom _ => True
  | .unary op body => allowedOperator op ∧ operatorsDeclared allowedOperator body

def declarationsPreserved
    (allowedSymbol : Symbol → Prop) (allowedOperator : Operator → Prop)
    (term : FixedAlphabetTerm Symbol Operator) : Prop :=
  symbolsDeclared allowedSymbol term ∧ operatorsDeclared allowedOperator term

def nest
    (op : Operator) : Nat → FixedAlphabetTerm Symbol Operator →
      FixedAlphabetTerm Symbol Operator
  | 0, term => term
  | depth + 1, term => .unary op (nest op depth term)

theorem fixed_alphabet_nesting_introduces_no_undeclared_symbols
    (allowedSymbol : Symbol → Prop) (op : Operator) (depth : Nat)
    (term : FixedAlphabetTerm Symbol Operator)
    (hTerm : symbolsDeclared allowedSymbol term) :
    symbolsDeclared allowedSymbol (nest op depth term) := by
  induction depth with
  | zero => exact hTerm
  | succ depth ih => exact ih

theorem fixed_alphabet_nesting_introduces_no_undeclared_operators
    (allowedOperator : Operator → Prop) (op : Operator) (depth : Nat)
    (term : FixedAlphabetTerm Symbol Operator)
    (hOp : allowedOperator op)
    (hTerm : operatorsDeclared allowedOperator term) :
    operatorsDeclared allowedOperator (nest op depth term) := by
  induction depth with
  | zero => exact hTerm
  | succ depth ih => exact ⟨hOp, ih⟩

/--
Internal fixed-alphabet closure for unary nesting.  The conclusion is only
about the two supplied declaration predicates; it is not the full PaperER007
grammar-ceiling claim.
-/
theorem fixed_alphabet_nesting_preserves_declarations
    (allowedSymbol : Symbol → Prop) (allowedOperator : Operator → Prop)
    (op : Operator) (depth : Nat) (term : FixedAlphabetTerm Symbol Operator)
    (hOp : allowedOperator op)
    (hTerm : declarationsPreserved allowedSymbol allowedOperator term) :
    declarationsPreserved allowedSymbol allowedOperator (nest op depth term) := by
  exact ⟨
    fixed_alphabet_nesting_introduces_no_undeclared_symbols
      allowedSymbol op depth term hTerm.1,
    fixed_alphabet_nesting_introduces_no_undeclared_operators
      allowedOperator op depth term hOp hTerm.2⟩

end FixedAlphabetTerm

#print axioms PaperER007.FixedAlphabetTerm.fixed_alphabet_nesting_introduces_no_undeclared_symbols
#print axioms PaperER007.FixedAlphabetTerm.fixed_alphabet_nesting_introduces_no_undeclared_operators
#print axioms PaperER007.FixedAlphabetTerm.fixed_alphabet_nesting_preserves_declarations

end PaperER007
