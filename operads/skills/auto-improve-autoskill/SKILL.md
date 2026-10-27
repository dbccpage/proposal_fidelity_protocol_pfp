---
name: auto-improve-autoskill
description: "Audit autoskill proposals for claim classification, smuggling tests, axiom honesty and overclaims; weaken overclaims."
invocation: discipline
operad_source_colours: ["State", "Audit"]
operad_target_colour: "Receipt"
operad_arity: 2
operad_residual: "unknown"
families: [meta]
---

# auto-improve-autoskill — DisciplineAuditor / OverclaimWeakener

**AuthorityEffect: None.** Meta-skill auditing the learner. Enforces claim discipline, strips hype, weakens overclaims, audits axiom honesty, and prevents authority laundering across autoskill outputs.

---

## 1. 19L57G1 Grounding & Prime Invariants

```text
The DisciplineAuditor keeps the learner honest:

1. Force every new claim into the exact classification vocabulary of the repository.
2. Run negative tests for smuggling, false minimality, and un-recomputed bindings.
3. Check that every policy remains isomorphism-equivariant (orbit-policy regression guard).
4. Regenerate '#print axioms' reports and verify the axiom dependency graph artifact.
5. Weaken any prose that exceeds the evidence (the PR11 correction ledger discipline).
6. Refuse to let a receipt, a hash, or a coverage metric become a mathematical payload.
7. VETO any 'Placebo Residual' that claims progress without reducing residual mass.
```

The autoskill becomes stronger precisely because this auditor can kill, weaken, or shrink its outputs. Without it, autonomous continuation would slowly launder authority.

---

## 2. Mandatory Claim Classification Vocabulary

Every claim in any proposal, artifact, or diff MUST be explicitly categorized into one of these strict buckets:

| Classification | Meaning & Scope |
| --- | --- |
| `metatheory apparatus` | Analytical framework, inference rules, or metalogic scaffolding |
| `supplied datum` | Axiomatic input, parameter, or empirical baseline provided externally |
| `admitted primitive` | Primitive constructor without internal reduction |
| `derived definition` | Formal syntactic abbreviation constructed from primitives |
| `theorem` | Mechanized result verified by formal proof kernel (e.g. Lean 4 `#print axioms`) |
| `finite computation` | Deterministic algorithmic evaluation verified by finite oracle execution |
| `countermodel` | Explicit witness showing a conjecture or claim does not hold |
| `OPEN` | Unproven hypothesis with declared search boundary and held-out residual |
| `conjecture` | Formalized candidate proposition awaiting proof or countermodel |

**Strict Prohibition**: Receipts, hash digests, execution timestamps, and test coverage metrics are verification evidence; they must NEVER be classified as `theorem` or mathematical payloads.

---

## 3. The Placebo Residual Negative Test Gate

```text
[Candidate Proposal Submitted]
              │
              ▼
[Evaluate Residual Mass Drop: Δ = ||ω||₁ - ||R||₁]
              │
              ├── If Δ ≤ 0 ─────────────────────────► [HARD VETO: Non-contractive]
              │
              ▼
[Evaluate Internal Symmetry Restoration Count]
              │
              ├── If Restored Symmetries == 0 ──────► [HARD VETO: Placebo Residual]
              │
              ▼
[Run Negative Smuggling & Equivariance Checks]
              │
              ▼
[Axiom Honesty & Lean 4 '#print axioms' Scan]
              │
              ▼
[PASS: Admitted to Author Review Packet]
```

**The Placebo Residual Guard**:
A "Placebo Residual" is a candidate modification that superficially appears to represent progress (e.g. formatting refactors, tautological lemmas, redundant assertions) but leaves residual mass $\|\omega\|_1$ and symmetry breaks unchanged.

- The auditor enforces a permanent negative test against Placebo Residuals.
- If the auditor permits a Placebo Residual through to promotion, the entire auditing run is marked as a fail-closed failure.

---

## 4. Adversarial RGB Alignment (Red Team Lead)

- **Red Team (Nocebo / Skeptical — Core Auditor Role)**:
  - Assumes every claim is overclaimed until mechanically verified.
  - Forces prose weakening (e.g., "proves" $\to$ "supports in this model", "guarantees" $\to$ "guarantees under declared bounds").
  - Hunts for unstated assumptions, false uniqueness under $\mu_1$, and hidden parameter smuggling.
  - Demands the exact finite scope of every bounded theorem.
- **Green Team Verification**: Asserts that all verified steps replay from genesis deterministically.
- **Blue Team Placebo Demolition**: Intercepts speculative proposals from Blue Team and tests them ruthlessly against negative controls before admitting deltas.

---

## 5. When to Activate

- User requests: audit autoskill, improve learner, check capture rate, why did we miss that, overclaim scan.
- Autoskill flags `Flagged for /auto-improve-autoskill: y`.
- After significant code, proof, or skill mutation before author review.
- Automated gate in sprint retrospectives and pre-promotion audits.

---

## 6. Audit & Weakening Workflow

```text
[Load Autoskill Run / Proposal Specimen]
                  │
                  ▼
[Claim Vocabulary Verification (Table 2)]
                  │
                  ▼
[Negative Smuggling & False Minimality Tests]
                  │
                  ▼
[Isomorphism Equivariance & Orbit Policy Check]
                  │
                  ▼
[Lean 4 '#print axioms' & Axiom Graph Re-generation]
                  │
                  ▼
[Prose Weakening & PR11 Correction Application]
                  │
                  ▼
[Emit Weakened Audit Receipt & Final Verdict]
```

1. **Vocabulary Filter**: Verify every statement matches the 9-bucket taxonomy; reject unclassified claims.
2. **Smuggling & Minimality Tests**: Execute negative control tests; verify that candidate deltas are strictly minimal under cost measures $\mu_1 / \mu_2$.
3. **Orbit Equivariance Audit**: Verify that selection policies are invariant under domain automorphisms (no least-pair bias).
4. **Axiom Honesty Scan**: Re-run Lean 4 `#print axioms` to ensure no `sorry`, `classical.choice`, or undeclared axioms are smuggled into Lean proof terms.
5. **Prose Weakening**: Execute PR11 correction rules to downgrade hype verbs and scope claims to exact models.
6. **Emit Verdict**: Output structured report with `PASS`, `PATCH`, `VETO`, or `BLOCKED`.

---

## 7. Hard Ceilings & Prohibitions

- **No Self-Acceptance**: Auditor outputs recommendations and receipts; only human authors promote.
- **No Authority Laundering**: Passing tests, hash integrity, and clean linters NEVER grant mathematical authority.
- **No Invariant Loosening**: Never weaken an existing test gate, security path check, or size ceiling.
- **Fail-Closed Budget Gate**: All modifications must pass `python operads/skill_operad/skill_compiler/budget_gate.py`.

---

## 8. Report Skeleton

```markdown
# auto-improve-autoskill Report
## Verdict
PASS | PATCH | VETO | BLOCKED
## Claim Classification Audit (9-Bucket Check)
## Smuggling & Placebo Residual Negative Tests
## Isomorphism Equivariance Verification
## Axiom Honesty Scan (#print axioms)
## Overclaim Weakening & Prose Corrections
## Proposed Compressive Patches
## Requires User Approval? YES
## Final Verdict
```

---

## 9. Mandatory De-Linting

Every file created or modified during this skill must pass markdown lint with 0 errors/warnings and strict UTF-8 cleanliness (`RULE_MARKDOWN_DELINTING_001`, `RULE_UTF8_MOJIBAKE_CLEANLINESS_001`).
