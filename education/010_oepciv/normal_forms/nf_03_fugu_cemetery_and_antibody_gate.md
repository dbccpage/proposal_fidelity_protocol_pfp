---
documentation_contract: symbol-game-documentation/v1
title: "Normal Form 03: The Autophagous \"Fugu\" Cemetery & Pharmacy Antibody Gate"
kind: normal-form-specification
audience:
  - researchers
  - engineers
  - coding-agents
status: active
maturity: draft
claim_status: verified
authority_effect: "None"
source_paths:
  - omega_engine_woland/infrastructure/default_adapters.py
  - omega_engine_woland/use_cases/act_helpers.py
  - omega_engine_prompt_civilization/tests/integration/test_fugu_cemetery_blocking_loop.py
prerequisites:
  - ../01_v10rc_system_design_and_integration.md
  - nf_01_prompt_society_and_civilization.md
  - nf_02_lamarckian_pfp_woland_loop.md
related:
  - ../../120_the_woland_retinue_swarm/11_autophagous_fugu_cemetery_and_pharmacy_antibody_gates.md
last_verified: 2026-10-09
---

# Normal Form 03: The Autophagous "Fugu" Cemetery & Pharmacy Antibody Gate

**AuthorityEffect:** None.  
**Epistemic Posture:** Normative specification and verification contract; mints no operational or mathematical authority.

---

## 1. Intent & Problem Statement

In evolutionary prompt algorithms, random mutations and LLM proposals routinely drift into previously discovered failure modes, repeating invalid imports, broken type constraints, or known logical contradictions across generations.

The **Autophagous "Fugu" Gate** closes this loop:
1. Every failed candidate mutation in generation $g$ is interred as a typed `CemeteryHeadstoneV1` record within `_intelligence/_woland/cemetery/`.
2. Active failure witnesses are translated into structural lint rules and semantic antibodies within the epistemic pharmacy repertoire.
3. In generation $g+1$, candidate mutations are screened *prior to execution* at Act IV. If a mutation matches an interred casualty or an active antibody, the gate refuses execution with an immutable typed refusal.

---

## 2. Normative Data Contracts

### 2.1 Cemetery Headstone Schema (`CemeteryHeadstoneV1`)
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "CemeteryHeadstoneV1",
  "type": "object",
  "required": [
    "casualty_id",
    "failure_mode",
    "witness_summary",
    "candidate_sha256",
    "interred_at_utc"
  ],
  "properties": {
    "casualty_id": {
      "type": "string",
      "description": "Unique identifier prefixed with headstone:"
    },
    "failure_mode": {
      "type": "string",
      "enum": [
        "SYNTAX_ERROR",
        "AST_IMPORT_VIOLATION",
        "TEST_ASSERTION_FAILURE",
        "CIRCULAR_DEPENDENCY",
        "RAW_IO_ESCAPE",
        "COCHAIN_DEFECT"
      ]
    },
    "witness_summary": {
      "type": "string",
      "description": "Specific failure string, traceback, or defect diagnostic"
    },
    "candidate_sha256": {
      "type": "string",
      "pattern": "^[0-9a-f]{64}$"
    },
    "interred_at_utc": {
      "type": "string",
      "format": "date-time"
    }
  },
  "additionalProperties": false
}
```

### 2.2 Refusal Types
The gate defines two distinct refusal codes:
- **`REGRESSION_AGAINST_CEMETERY_REFUSED`**:
  Triggered when candidate mutation payload matches the text, AST digest, or exact defect string of an interred headstone.
- **`REGRESSION_AGAINST_ANTIBODY_REFUSED`**:
  Triggered when candidate mutation payload matches an active pharmacy antibody pattern or structural lint template.

---

## 3. Generational Lifecycle Sequence

```mermaid
sequenceDiagram
    autonumber
    participant Gen1 as Generation g = 1 (Proposer)
    participant Act4_1 as Act IV Sandbox Gate (g = 1)
    participant Cemetery as Cemetery Adapter (_intelligence/_woland/cemetery/)
    participant Pharmacy as Pharmacy Seeder
    participant Gen2 as Generation g = 2 (Proposer)
    participant Act4_2 as Act IV Sandbox Gate (g = 2)

    Gen1->>Act4_1: Submit candidate mutation M1
    Act4_1->>Act4_1: Execute challenge checker / pytest
    Act4_1-->>Gen1: Failure Witness W1 (e.g., forbidden raw socket)
    Act4_1->>Cemetery: inter_casualty(candidate=M1, witness=W1)
    Act4_1->>Pharmacy: seed_antibody(witness=W1)

    Note over Cemetery,Pharmacy: Failure is preserved; state reloaded dynamically

    Gen2->>Act4_2: Submit identical candidate mutation M1
    Act4_2->>Cemetery: load_headstones()
    Act4_2->>Act4_2: Screen candidate against headstones
    Act4_2-->>Gen2: FAIL-CLOSED REFUSAL (REGRESSION_AGAINST_CEMETERY_REFUSED)
    Note over Act4_2,Gen2: Execution halted BEFORE sandbox execution or seat turns
```

---

## 4. Controlled Ablation & Regression Sensitivity

To enable empirical benchmarking and measure the regression rate under raw conditions, the screening logic respects `ablation_flags`:

$$\text{ScreenCandidate}(C, \mathcal{H}, \mathcal{A}) = \begin{cases}
\text{PASS}, & \text{if } \text{ablation\_flags}[\text{"no\_cemetery\_defense"}] = \text{True} \\
\text{REFUSE}(\text{Cemetery}), & \text{if } \exists H \in \mathcal{H} : \text{Matches}(C, H) \\
\text{REFUSE}(\text{Antibody}), & \text{if } \exists A \in \mathcal{A} : \text{Matches}(C, A) \\
\text{PASS}, & \text{otherwise}
\end{cases}$$

---

## 5. Claim Discipline & Epistemic Boundaries

1. **What this document supports:**
   - Defines the normative schema for cemetery headstones and the pre-execution screening rules enforced at Act IV.
   - Formalizes the closed-loop generational lifecycle where failure witnesses from generation $g$ block identical regressions in generation $g+1$.

2. **What this document does not support:**
   - Does not support that string or pattern matching detects semantically transformed, refactored, or renamed regressions.
   - Does not support that cemetery defense alone guarantees evolutionary convergence toward optimal prompt fitness.

3. **Narrowest defensible claim:**
   - Within this model, the Act IV screening routines detect and refuse candidates matching previously buried cemetery casualties and active antibody templates prior to executing seat turns or external test suites.

4. **Next test needed:**
   - Benchmark cemetery gate resistance against AST perturbations (variable renaming, comment insertion) across automated mutation rounds.
