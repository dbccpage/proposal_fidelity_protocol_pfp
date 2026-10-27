> [!WARNING]
> **LEGACY PILOT / superseded by [proof_obstruction_packet.md](../../../../../crates/core_contracts/src/contract_canonical_definitions/core/09_packets/proof_obstruction_packet.md)**
> This is a legacy pilot template and is not compliant with the current ODP standard (lacks per-defect reporting, A3 oracle discipline, A4 current/target/seal split, and A5 DDA-letter discipline). It is preserved here for historical reference only and must not be promoted.

Core Proofer Pilot (Obstruction Packet)
========================================

1. Carrier & 2-Window Definition
--------------------------------

**Carrier:** A Lean 4 formal mathematical derivation environment. The 2-window inspects the transition between sequential proof states.

2. Declare $C^0$
----------------

**$C^0$ (Assignments):** Current definitions, declared hypotheses, and available local lemmas in the context.

3. Declare $d_0$
----------------

**$d_0$ (Primitive Operator):** Allowed logical derivations, tactic applications (`simp`, `rw`), or deductions from existing definitions and hypotheses.

4. Emit $C^1$
-------------

**$C^1$ (Defects / Inconsistencies):** Unproven subgoals, type mismatches, claim defects, and unproven transitions.

5. Declare ZeroRel
------------------

**ZeroRel (Gauge Relation):** Definitional equality (`rfl`), alpha equivalence, or trivial syntactic renaming of bound variables.

6. Compute $Q^1$
----------------

**$Q^1$ (Quotient / Residuals):** Irreducible proof obligations. Defects that cannot be removed by existing local lemmas and basic tactic execution.

7. Declare $d_1$
----------------

**$d_1$ (Closure Operator):** Compatibility of proof obligations across different branches or cases of the proof.

8. Compute $\Gamma_2$
---------------------

**$\Gamma_2$ (Closure Failure Mass):** Contradiction, noncommuting proof squares, or incompatible variable bindings across branches.

9. Compute $\Phi_1$
-------------------

**$\Phi_1$ (Quotient Obstruction Mass):** The formal distance to completion (e.g. number of remaining open goals).

10. Classify System State
-------------------------

* [ ] Exact repair: no lift.
* [x] Closed survivor: stabilize, terminalize, or request lift with preservation witness.
* [ ] Active closure failure: repair closure if possible; otherwise request higher-cell/lift with coherence witness.
* [ ] No rule: typed refusal or new packet-family request.

(Assuming a valid but unproven open goal requiring a new lemma.)

11. Propose $\Meta$ (Lift Candidate)
------------------------------------

**$\Meta$ (Lift/Structural Extension):** Add a helper lemma or construct a specific witness. Closed survivor $\Phi_1 > 0$ may trigger lift consideration; proof library expansion policy and witnesses license the lift.

12. Execute DDA
---------------

**DDC (Discrete Deformation Calculus):** Exact repair on simple subgoals ($E$), lift via helper lemma ($\Meta$), terminalization of proof ($T$).

13. Terminal Status
-------------------

**Terminal:** Open Residual / Theorem Proven.
