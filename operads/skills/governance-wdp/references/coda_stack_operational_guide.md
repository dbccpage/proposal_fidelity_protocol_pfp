# CODA Stack Operational Guide & Protocol Details

**AuthorityEffect:** None.  
**Domain Context:** `governance-wdp`

This reference documents the procedural workflows, 9-layer CODA pipeline contracts, Discrete Deformation Calculus (DDC) 8-letter operational alphabet, and Prime Triad execution sequences.

---

## 1. Nine-Layer CODA Stack Application Pipeline

The canonical 9-layer CODA application pipeline executes in strict dependency order:
1. **Layer 1: FOC (Finite Obstruction Calculus):** Primitive difference and carrier boundary initialization.
2. **Layer 2: MUR (Meta & Universal Re-Presentation):** Multi-carrier representation and equivalence maps.
3. **Layer 3: CS (Continuum Shadow):** Coarse-graining and finite shadow projections.
4. **Layer 4: CS-Q (Continuum Shadow / Continuum Bridge):** Discrete-to-continuum transition interfaces.
5. **Layer 5: Q (The Continuum):** Continuum representations via convex interval enclosures $[lo, hi]$ with $|x - \text{mid}| \le \text{width}/2$ and Cauchy completions. *Calling Layer 5 "Quantum Enclosure" is prohibited.*
6. **Layer 6: A (Sentinel):** Anomalous holonomy and discrete curvature metrics.
7. **Layer 7: OR (Omniversal Re-Presentation):** Universal factor uniqueness and quotient embeddings.
8. **Layer 8: FDA (Finite Descent Authority):** Descent verification, role split (proposer != authorizer), and dual witness certificates.
9. **Layer 9: GTLA (General Theory of Layered Authority):** Master normal forms, cryptographic authority gates (`AuthorityEffect: None`), and verified promotion.

---

## 2. Discrete Deformation Calculus (DDC) Operational Alphabet

State transitions on mathematical and computational obstructions execute using the 8-letter operational trace alphabet:
$$\mathcal{A}_{\mathrm{DDC}} = \{E, R, C, I, \Lambda, D, M, T\}$$
- **$E$ (Exact Repair):** Discharge the defect outright ($\Delta_E \in \mathrm{im}(d_0)$, residual $\to 0$).
- **$R$ (Residual Projection):** Project unresolved boundary tension into quotient tracking ($\Phi_1([x]) > 0$).
- **$C$ (Context Exposure):** Declare or split carrier, window, and boundary complex ($C^0 \xrightarrow{d_0} C^1 \xrightarrow{d_1} C^2$).
- **$I$ (Integration):** Append verified transition to Merkle tape with deterministic step receipt.
- **$\Lambda$ (Lift):** Lawful structural lift adjoining new operators to resolve saturation under Licensed Context Extension (LCE).
- **$D$ (Descent):** Scale descent lowering from rich to coarse carriers with declared loss ledger.
- **$M$ (Refusal / Mutation):** Typed refusal on unresolvable, out-of-bounds, or unverified transitions.
- **$T$ (Terminalization):** Terminal state commitment (`CheckPassed`, `Repair`, `Refusal`) without minting authority (`AuthorityEffect: None`).

---

## 3. Prime Triad Execution Lifecycle

- **Prime -1:** Candidate proposal (unassigned exploratory ideation; no crate owner).
- **Prime 000:** Local packet declaration order (admission then twelve-step fill: `oeprmalg0_admission.rs`, `oeprmalg0.rs`).
- **Prime 001:** Adapter descent soundness (`oeprmalg1.rs`).
- **Prime 002:** Continue-until-unauthorized control law (`oeprmalg2.rs`).
- Prime Triad stages remain behavioral protocol operations while domain types reside strictly in `crates/type/prime/` and `crates/type/trace/`.
