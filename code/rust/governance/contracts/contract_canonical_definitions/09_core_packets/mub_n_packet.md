packet_type: schema
authority_effect: None
carrier: dimension n, basis index set, algebraic field, equivalence actions
primary_residual: non-removable MUB obstruction class (Q¹)
in_scope_repairs: rephasing, permutation, local gauge action (d₀)
deferred_residuals: none
seal_condition: pairwise local certificates glue globally into full set of n+1 bases

MUB(n) Construction (Obstruction Packet)
========================================

1. Carrier & 2-Window Definition
--------------------------------

**Carrier:** Finite dimension $n$, basis index set, phase/algebraic field, equivalence actions. The 2-window inspects the local unbiasedness certificates and their pairwise overlaps.

2. Declare $C^0$
----------------

**$C^0$ (Assignments):** Local basis gauges, phase choices, and row/column/unitary selections.

3. Declare $d_0$
----------------

**$d_0$ (Primitive Operator):** Permitted rephasing, permutation, or local gauge action producing equivalent configurations.

4. Emit $C^1$
-------------

**$C^1$ (Defects / Inconsistencies):** Unbiasedness defects, orthogonality defects, or normalization defects between candidate bases.

5. Declare ZeroRel
------------------

**ZeroRel (Gauge Relation):** Exact equality, certified interval zero, or algebraic zero.

6. Compute $Q^1$
----------------

**$Q^1$ (Quotient / Residuals):** Genuine non-removable MUB obstruction class (defects not removable by $d_0$ gauge transformations).

7. Declare $d_1$
----------------

**$d_1$ (Closure Operator):** Triple compatibility or cocycle closure across basis overlaps.

8. Compute $\Gamma_2$
---------------------

**$\Gamma_2$ (Closure Failure Mass):** Failure of pairwise local certificates to glue globally into a full set of $n+1$ bases.

9. Compute $\Phi_1$
-------------------

**$\Phi_1$ (Quotient Obstruction Mass):** Irreducible residual mass indicating the remaining deviation from perfect unbiasedness after all allowed repairs.

10. Classify System State
-------------------------

* [ ] Exact repair: no lift.
* [ ] Closed survivor: stabilize, terminalize, or request lift with preservation witness.
* [ ] Active closure failure: repair closure if possible; otherwise request higher-cell/lift with coherence witness.
* [ ] No rule: typed refusal or new packet-family request.

### MUB(6) Concrete Instance Specification

For the concrete dimension $n = 6$ instance, the packet fields map as:

* **carrier:** exact algebraic / interval-certified candidate bases in $\mathbb{C}^6$
* **C⁰:** monomial gauge actions, rephasing, permutation, field embeddings
* **C¹:** unbiasedness + orthogonality + normalization residuals
* **ZeroRel:** exact algebraic zero / certified interval zero
* **d₁:** triple or family compatibility across bases
* **Γ₂:** failure of pairwise certificates to glue into full family of 7 bases
* **Φ₁:** exact residual mass after gauge minimization
* **terminal:** candidate / obstruction / oracle-needed / refused (currently Packet-Refinement-Needed / Oracle-Needed)

### Readiness note

This packet is currently a schema, not an instantiated obstruction verdict. It does not assert that a non-prime-power dimension has active closure failure; that classification requires the exact carrier, field, gauges, ZeroRel, $d_1$, $\Gamma_2$, $\Phi_1$, and terminalizer.

11. Propose $\Meta$ (Lift Candidate)
------------------------------------

**$\Meta$ (Lift/Structural Extension):** Field extension, cover refinement, exact certificate upgrade, or introduction of a new algebraic witness type. Verified active closure failure $\Gamma_2 > 0$ may trigger lift consideration; policy and witnesses license lift.

12. Execute DDA
---------------

**DDC (Discrete Deformation Calculus):** Gauge repair ($E$), quotient projection ($R$), field lift ($\Meta$), certificate transport ($I$).

13. Terminal Status
-------------------

**Terminal:** Packet-Refinement-Needed / Oracle-Needed. No no-go certificate is claimed by this schema.
