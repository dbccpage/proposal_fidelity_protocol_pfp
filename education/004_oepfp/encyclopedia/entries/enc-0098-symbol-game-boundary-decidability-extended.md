---
id: ENC-0098
kind: theorem
name: "Symbol Game Boundary Decidability, extended"
status: PROVED-PROSE
conditional_on: []
layer: symbol-game
tower_level: null
primitive: null
aliases: ["spine:VII.2", "po:PO-SGBD"]
sources:
  - "canonical_omega_math_spine.md v1.5.2 §VII.2 'Theorem VII.2'"
  - "proof_obligations.md v1.3.5 §13 PO-SGBD 'Theorem' (unnamed; variant with proof body)"
uses: []
lean_status: NOT-STARTED
lean_refs: []
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0098 — Symbol Game Boundary Decidability, extended

## Statement

Extends Theorem IV.2. If \(\mathrm{Parse}_\Gamma\), \(L_\Gamma\), \(V_\Gamma\),
\(F\) are total deterministic finite procedures over a finite typed grammar —
where \(V_\Gamma\) returns the four-way verdict
\(\{\mathsf{Valid},\mathsf{Irreducible},\mathsf{Repairable},\mathsf{OracleNeeded}\}\)
(the GTFOC trichotomy of §III.3 / PO-D3 plus the disjoint evidence-ceiling
case) and \(F\) is the fidelity functor (Theorem IV.6) — then the packet
**terminal status** is decidable into the six-status taxonomy
\(\{\mathsf{ParseError},\mathsf{LocalInvalid},\mathsf{LocalValidGlobalInvalid},
\mathsf{RepairRequired},\mathsf{OracleNeeded},\mathsf{GlobalValidVerifierScoped}\}\)
via the ordered pipeline **parse → local → boundary → fidelity → terminalizer**
(a finite first-match; cf. §VII.1).

Decidability is **verifier-scoped, not semantic**: by Theorem IV.4
(No-Free-Lunch from Syntax) and Theorem IV.8 (Unrestricted NL Fidelity
Undecidable), semantic truth/fidelity is undecidable for unrestricted
grammars — the finiteness hypothesis is the exact decidable/undecidable line.
\(\mathsf{GlobalValidVerifierScoped}\) is a verifier verdict, strictly weaker
than `Certified`, and feeds \(V^\sharp\) (§IV.4); it does not produce authority.
See `proof_obligations.md` §13 PO-SGBD. Done condition: every packet response
traverses the full pipeline. Enforcement: SG-GATE-001.

## Proof Pointer

The spine carries no separate *Proof.* block for this statement; the statement itself
directs to `proof_obligations.md` §13 PO-SGBD for the discharge. The base case is
Theorem IV.2 (which this extends) and the terminalizer step is §VII.1 (PO-TPC).

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| decidability of the six-status terminal taxonomy via the ordered finite first-match pipeline over a finite typed grammar | local | none identified | NOT-STARTED |

## Notes

- The source tag is `[PROVED]`; normalized to PROVED-PROSE (no mechanization exists).
- The PO-name PO-SGBD appears in the source section heading
  ("### VII.2 Symbol Game Boundary Decidability, Six-Status Form (PO-SGBD)") and in
  the statement body.
- Variant provenance (E3, 2026-06-09): `proof_obligations.md` v1.3.5 §13
  "PO-SGBD — Symbol Game Boundary Decidability Theorem (SG-GATE-001 schema
  half)" states the theorem as `**Theorem.** Under these hypotheses \(\tau\)
  is total, deterministic, and terminating, with statuses exhaustive and
  mutually exclusive.` with the component-procedure hypotheses
  (\(\mathrm{Parse}_\Gamma, L_\Gamma, V_\Gamma, F\)) spelled out and a FULL
  PROOF BODY (the ordered first-match pipeline displayed as pseudocode, the
  two-route \(\mathsf{RepairRequired}\) note, and the finite-DAG totality
  argument) that this entry's Proof Pointer only points to. Its status line:
  "Theorem: PROVED-PROSE, **self-contained**". Proof transfer is a later
  /math-prover job, not extraction.

## Provenance

- Extracted 2026-06-09 from `canonical_omega_math_spine.md` v1.5.2, §VII.2
  (statement copied verbatim). Original header line:
  `**Theorem VII.2 (Symbol Game Boundary Decidability, extended).** [PROVED]`

## Changelog

- 2026-06-09: ENC-0098 created (M2 E1 extraction).
- 2026-06-09: variant provenance appended (E3 proof_obligations.md v1.3.5 §13 PO-SGBD, full proof body); Statement unchanged.
