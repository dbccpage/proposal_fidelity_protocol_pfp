> [!WARNING]
> **LEGACY PILOT / superseded by [rust_obstruction_packet.md](../../../../../crates/core_contracts/src/contract_canonical_definitions/core/09_packets/rust_obstruction_packet.md)**
> This is a legacy pilot template and is not compliant with the current ODP standard (lacks per-defect reporting, A3 oracle discipline, A4 current/target/seal split, and A5 DDA-letter discipline). It is preserved here for historical reference only and must not be promoted.

Rust Code Reviewer Pilot (Obstruction Packet)
=============================================

1. Carrier & 2-Window Definition
--------------------------------

**Carrier:** The executable Rust carrier representing a specific crate or module boundary. The 2-window inspects the trait contracts and their implementation integrity.

2. Declare $C^0$
----------------

**$C^0$ (Assignments):** Current structs, trait definitions, contracts, and schema fields in the crate.

3. Declare $d_0$
----------------

**$d_0$ (Primitive Operator):** Permitted code refactoring, bug fixes, or safe implementations that preserve external invariants.

4. Emit $C^1$
-------------

**$C^1$ (Defects / Inconsistencies):** Failing tests, compiler errors, missing invariants, or unimplemented methods.

5. Declare ZeroRel
------------------

**ZeroRel (Gauge Relation):** Code formatting, variable renaming, or safe internal refactoring without observable external change.

6. Compute $Q^1$
----------------

**$Q^1$ (Quotient / Residuals):** Code failures and missing features that cannot be resolved by trivial local refactoring within the existing trait boundaries.

7. Declare $d_1$
----------------

**$d_1$ (Closure Operator):** Integration coherence across crates, verifying that the new internal implementations do not violate public API constraints downstream.

8. Compute $\Gamma_2$
---------------------

**$\Gamma_2$ (Closure Failure Mass):** Cross-boundary breakage or integration test failures downstream.

9. Compute $\Phi_1$
-------------------

**$\Phi_1$ (Quotient Obstruction Mass):** The measure of remaining uncompilable or failing code paths.

10. Classify System State
-------------------------

* [ ] Exact repair: no lift.
* [ ] Closed survivor: stabilize, terminalize, or request lift with preservation witness.
* [x] Active closure failure: repair closure if possible; otherwise request higher-cell/lift with coherence witness.
* [ ] No rule: typed refusal or new packet-family request.

(Assuming a feature implementation that currently breaks downstream consumers, requiring a structural change to the public API.)

11. Propose $\Meta$ (Lift Candidate)
------------------------------------

**$\Meta$ (Lift/Structural Extension):** Bump a major version, introduce a new trait, or add a new parameter to the API boundary. Active closure failure $\Gamma_2 > 0$ may trigger lift consideration; architecture review policy and the backward compatibility preservation witness license the lift.

12. Execute DDA
---------------

**DDC (Discrete Deformation Calculus):** Quotient projection exposure ($R$), API lift ($\Meta$), descent to updated consumers ($D$).

13. Terminal Status
-------------------

**Terminal:** Lift-Needed / Repaired.
