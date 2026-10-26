---
name: auto-symmetry-hunter
description: "Detect directional residuals and symmetry breaks; score candidate coboundaries by residual drop without picking repairs."
invocation: discipline
operad_source_colours: ["State", "Audit"]
operad_target_colour: "Receipt"
operad_arity: 2
operad_residual: "unknown"
families: [meta]
---

# auto-symmetry-hunter

**AuthorityEffect: None.** Surfaces symmetry breaks and directional residuals across cross-skill, cross-agent, and historical PR boundaries. Does not mint authority, select repairs, or promote faces from nowhere.

---

## 1. 19L57G1 Grounding & Prime Directive

```text
The hunter's only job is to turn residual into symmetry break and back:

1. Given an attempted correspondence p → q on a represented domain D, detect directional residuals.
2. Construct the transposition of the residual pair: this is an involution leaving the p-face invariant and moving the q-face.
3. Report the three equivalent statements as a unified datum:
   (i)   The correspondence does not factor.
   (ii)  A directional residual exists.
   (iii) q loses invariance under an internal symmetry of p.
```

**Foundational Principle**: Residual mass and loss-of-invariance are the exact same datum.

---

## 2. Invariant & Coboundary Scoring Law

A candidate coboundary $\partial \omega$ is scored simultaneously on two dual axes:

1. **Residual Mass Drop ($\Delta$)**:
   $$\Delta = \|\omega\|_1 - \|R\|_1 + \text{survivor\_count\_reduction}$$
2. **Internal Symmetry Restoration**:
   Number of internal stabilizer symmetries of $p$ under which $q$ regains invariance.

```text
                      ┌───────────────────────────────────────┐
                      │    Directional Residual in Domain D   │
                      │         (p → q does not factor)       │
                      └──────────────────┬────────────────────┘
                                         │
                                         ▼
                      ┌───────────────────────────────────────┐
                      │    Transposition Involution τ = (x y) │
                      │    Leaves p invariant, moves q-face   │
                      └──────────────────┬────────────────────┘
                                         │
                                         ▼
                      ┌───────────────────────────────────────┐
                      │     Unified Triad Equivalence Report  │
                      │  Factorization Break ≡ Residual ≡     │
                      │         Loss of Invariance            │
                      └───────────────────────────────────────┘
```

---

## 3. Specialized Sibling Hunters

The Symmetry Hunter coordinates with specialized sub-hunters present across the working tree:

| Sibling Hunter | Analytical Domain | Specialization |
| --- | --- | --- |
| `AbsoluteInterior` | Topological & Category Interior | Detects components protected from boundary deformation |
| `RepairStrategy` | Deformation & Homotopy Paths | Identifies canonical repair fiber without choosing promotion |
| `SeparationCapacity` | Depth-$d$ Outrun Bounds | Computes explicit graph capacity bounds and outrun limits |
| `OrbitPolicyGuardian` | Automorphism Orbits | Guards against presentation-dependent pair selection bugs |
| `TokenBlindness` | Representation Layer | Ensures presentation tokens never leak across correspondence maps |

---

## 4. Adversarial RGB Alignment

- **Red Team Integration**: Provides raw symmetry break reports to Red Team to hunt countermodels, amplify residual survivors, and block false minimality.
- **Green Team Integration**: Supplies exact involution pairs to Green Team so that minimal contractive repairs can be formulated inside declared policies.
- **Blue Team Placebo Filtration**: Detects non-reducing "Placebo Residuals" (proposals claiming progress that leave residual mass $\|\omega\|_1$ and symmetry breaks unchanged) and marks them for immediate rejection.

---

## 5. When to Activate

- User requests symmetry hunting, drift detection, cross-skill invariant audit, or family comparison.
- Autoskill flags `/auto-symmetry-hunter` after partial family updates or incomplete six-host landings.
- Historical PR analysis requiring an explicit correspondence map prior to differential inspection.
- Gate verification requiring proof that candidate repairs restore declared stabilizer symmetries.

---

## 6. Detection Workflow

```text
[Declare Explicit Correspondence Map (p → q)]
                     │
                     ▼
[Directional Residual Extraction (Non-factoring pairs)]
                     │
                     ▼
[Construct Transposition Involution τ = (x y)]
                     │
                     ▼
[Verify Invariance Break on Target Face q]
                     │
                     ▼
[Score Residual Mass Drop & Restored Symmetries]
                     │
                     ▼
[Emit Triad Report & Recommendation]
```

1. **Declare Correspondence Map**:
   - Establish explicit domain map $p \to q$ before comparison.
   - PR numbers, filenames, symbol names, and temporal proximity do not by themselves establish symmetry.
2. **Extract Directional Residuals**:
   - Identify pairs $(x, y)$ in domain $D$ where $p(x) = p(y)$ but $q(x) \neq q(y)$.
3. **Construct Transposition Involution**:
   - Form $\tau = (x \, y)$ swapping $x$ and $y$.
   - Verify that $\tau$ is an internal symmetry of $p$ ($p \circ \tau = p$) while breaking $q$ ($q \circ \tau \neq q$).
4. **Score Coboundary Reduction**:
   - Evaluate $\Delta = \|\omega\|_1 - \|R\|_1$ and verify survivor count reduction.
   - Assert non-zero restored symmetry count; reject Placebo Residuals.
5. **Classify & Recommend**:
   - `PROPAGATE | COMPRESS | SPLIT | DOCUMENT_VARIANCE | QUARANTINE | ESCALATE_TO_BLACKROD | ESCALATE_TO_IMPROVE_AUTOSKILL`.

---

## 7. Severity & Break Classification

| Class | Meaning | Action |
| --- | --- | --- |
| `INTENTIONAL_VARIANCE` | Purposeful, documented domain divergence | Document & preserve |
| `BENIGN_VARIANCE` | Harmless local syntactic variance | Retain or compress |
| `MISSING_PROPAGATION` | Invariant present in origin, missing in target | Propagate to sibling |
| `DANGEROUS_DRIFT` | Weakens evidence, tests, or authority ceilings | Immediate patch / Quarantine |
| `DUPLICATE_RULE` | Re-hosted identical rule; violates DRY | Compress to shared contract |
| `CONTRADICTION` | Incompatible execution semantics | Escalate to Blackrod |
| `STALE_RULE` | Deprecated path, command, or concept | Remove & replace |
| `AUTHORITY_COLLISION` | Multiple roles claim final authority | Enforce AuthorityEffect: None |
| `UNLICENSED_EXTENSION` | Domain widened without license boundary | Strip extension |

---

## 8. Non-Negotiable Laws

- **Never Select a Repair**: The hunter surfaces the break and computes the residual; it never picks a preferred branch.
- **Never Promote One Face**: Both faces are analyzed symmetrically under the declared correspondence.
- **Never Survey from Nowhere**: Analysis must always be anchored to a declared domain $D$ and correspondence $p \to q$.
- **Cross-Host Parity**: Verified across active host roots (`.agents`, `.claude`, `.codex`, and `.grok`).

---

## 9. Mandatory De-Linting

Every file created or modified during this skill must pass markdown lint with 0 errors/warnings and strict UTF-8 cleanliness (`RULE_MARKDOWN_DELINTING_001`, `RULE_UTF8_MOJIBAKE_CLEANLINESS_001`).
