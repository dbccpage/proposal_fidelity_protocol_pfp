# Semiotic Sign & Presentation Bullshit Detector

This reference document establishes the protocols for detecting semiotic sign drift, questioning presentation claims, and exposing rhetorical slop across estate documents, codebases, and design proposals.

---

## 1. Woland as Chief Presentation Questioner & BS Detector

When human teams or autonomous agents communicate, they frequently fall victim to **presentation bias**: confusing smooth rhetorical formatting, slide-deck polish, and authoritative vocabulary with verified substance.

Woland, presiding with the **Russian-American Delegation (Apartment 50 on Sadovaya)**, serves as the orthogonal interrogator:

- **Jeremy ($E_{\text{yankee\_solver}}$):** High-velocity math check. Demands concrete numbers, minimal working prototypes, and strips out hand-waving abstractions.
- **Liudmila ($E_{\text{luda\_resilience}}$):** Soviet pragmatic resilience. Asks: *"What happens when the network fails, the power is cut, and half the dependencies refuse to load?"* Zero panic, zero tolerance for fragile complexity.
- **Polina ($E_{\text{polina\_gauge\_breaker}}$):** Southern wit and overconfidence zinger. Swiftly punctures smug consensus and high-flown self-congratulation with a single sharp question.
- **Yaroslava ($E_{\text{yaroslava\_discipline}}$):** Punctual precision and punchlist custody. Verifies every line item against the actual ledger: *"Who owns this row, when was it delivered, and where is the proof receipt?"*

---

## 2. Triadic Semiotic Analysis (Peirce & Saussure)

A fundamental failure mode in evolving software and mathematical estates is **sign drift**: a token remains byte-identical while different subsystems develop conflicting behavioral interpretations.

```text
                  Signifier (The Token / String)
                               ▲
                              ╱ ╲
                             ╱   ╲
                            ╱     ╲
                           ▼       ▼
      Signified (Denotation) <───> Interpretant (Behavioral Effect)
```

### Definitions:
1. **Signifier (The Token):** The literal identifier, type name, keyword, or metadata string (e.g. `AuthorityEffect: None`, `Projector`, `Certificate`).
2. **Signified (Denotation):** The abstract conceptual definition declared in specifications, dictionaries, or design docs.
3. **Interpretant (Operational Meaning):** What the code, compiler, or human actually executes differently because of the signifier.

---

## 3. Sign-Drift Audit Protocol

1. **Token Collection:** Select a candidate semantic anchor and harvest every live occurrence across prose, YAML manifests, code headers, and test assertions.
2. **Triadic Decomposition:** For each site, separate:
   - What token is written (Signifier).
   - What the author claimed it means (Signified).
   - What actual downstream execution occurs (Interpretant).
3. **Drift Detection:** Drift occurs when the Signifier is stable across surfaces but the Interpretant has diverged:
   - Site A treats `AuthorityEffect: None` as an informative badge.
   - Site B treats `AuthorityEffect: None` as an assertion enforcing zero mutation permissions.
   - Site C ignores the field entirely.
4. **Boundary with Syntax Checkers:**
   - Syntax and parity linters check tokens and byte equality.
   - Semiotic audits inspect operational semantics and behavioral agreement.

---

## 4. Presentation Questioning & Rhetorical De-Slop

When auditing slides, proposals, or architecture decks, execute the following interrogation filter:

| Rhetorical Trap | Woland Interrogation | Remediation |
| :--- | :--- | :--- |
| **Ungrounded Jargon** | *"What does this word cause the program to do that it didn't do before?"* | Replace with standard, concrete nouns or remove. |
| **Cargo-Cult Consensus** | *"Has anyone tested the negative case, or are we nodding because the font is clean?"* | Demand a Landau Class 4-5 mutation test target. |
| **Unbounded Claims** | *"Does this apply under declared assumptions, or is it advertised universally?"* | Enforce strict Claim Hygiene Rule posturing. |
| **Pseudo-Depth** | *"Is this complex because the math is hard, or because the boundaries are sloppy?"* | Refactor into Clean Architecture single-responsibility layers. |

---

## 5. Audit Terminal Verdicts

Every semiotic audit concludes with one of four formal terminals:

| Terminal | Criterion | Action |
| :--- | :--- | :--- |
| `STABLE` | Signifier and interpretant agree across all audited sites. | Record verified anchor in lexicon. |
| `INTERPRETANT_DRIFT` | Signifier is identical but sites execute conflicting behavior. | Flag divergence; report earliest usage of each reading. |
| `HOMONYM` | Identical token intentionally denotes distinct domain concepts. | Require namespace prefixing or explicit renaming. |
| `INSUFFICIENT_USES` | Token appears too infrequently to determine behavioral consensus. | Defer until further usage sites emerge. |

### Nonclaims & Governance Fence
Detecting drift demonstrates that a divergence exists; it does not dictate which reading is canonical. Canonical resolution belongs exclusively to the governance council owning the term.
