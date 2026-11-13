import StrictCompletion
import CurvatureCochain
import PrimitiveDifferenceLggr
import CohomologyClass
import CurvedDerivation

/-!
Paper PO-001 Axiom Audit (v2.0).

Audits every theorem mechanized for Paper PO-001.
Prints each theorem's axiom dependencies for inspection.  This module does not
enforce an allowlist; the source tree contains no sorry/admit declarations.
-/

-- Strict Completion (Path A)
#print axioms Paper001a.strict_completion_from_covering_edges
#print axioms Paper001a.strict_completion_unique_from_chain
#print axioms Paper001a.diamond_path_independence_of_common_completion
#print axioms Paper001a.StrictCompletion.chain_law
#print axioms Paper001a.StrictCompletion.diamond_from_chain_law

-- Curvature Cochain (Path B)
#print axioms Paper001a.TripleRestriction.d1_d0_eq_curvature
#print axioms Paper001a.TripleRestriction.flat_iff_chainComposable
#print axioms Paper001a.TripleRestriction.d1_d0_zero_iff_flat
#print axioms Paper001a.TripleRestriction.nonzero_curvature_not_chainComposable
#print axioms Paper001a.scalar_diamond_curvature
#print axioms Paper001a.QuadRestriction.d2_curvature_eq_lower_curvature_difference
#print axioms Paper001a.QuadRestriction.d2_curvature_zero_of_lower_flat
#print axioms Paper001a.QuadRestriction.d2_curvature_zero_of_edge_compatible

-- Primitive Difference / LGGR
#print axioms Paper001a.payload_relation_ignores_curvature
#print axioms Paper001a.payload_classifier_factors
#print axioms Paper001a.curvature_classifier_not_invariant_when_curvature_differs
#print axioms Paper001a.curvature_not_factor_through_payload_quotient
#print axioms Paper001a.payload_green_curvature_red
#print axioms Paper001a.curvature_factors_when_preserved

-- Operator cocycle / declared coboundary-image relation
#print axioms Paper001a.QuadRestrictionOp.delta2_operator_curvature_identically_zero
#print axioms Paper001a.QuadRestrictionOp.curvature_is_cocycle
#print axioms Paper001a.QuadRestrictionOp.curvature_coboundary_related_zero_iff_isCoboundary

-- Curved Operator Derivation (Theorem 4.1)
#print axioms Paper001a.QuadRestrictionOp.delta2_delta1_eq_commutator
#print axioms Paper001a.QuadRestrictionOp.delta2_delta1_zero_of_flat
#print axioms Paper001a.QuadRestrictionOp.residual_identically_zero
