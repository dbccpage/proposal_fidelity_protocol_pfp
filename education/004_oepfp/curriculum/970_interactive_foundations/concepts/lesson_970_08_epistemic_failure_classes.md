# Lesson 970.08 -- Section 3: The Epistemic Immune System (12 Failure Classes)

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_970_08_epistemic_failure_classes.ipynb](../notebooks/lesson_970_08_epistemic_failure_classes.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## Section 3: The Epistemic Immune System (12 Failure Classes)

Mined directly from production experiments and codified in `omega_prompt_civilization/src/pharmacy.rs`, the **Epistemic Immune System** is an anti-skill pharmacy consisting of 12 mechanical, deterministic failure detectors.

### Two Cardinal Rules of the Pharmacy:
1. **Detection is separate from repair**: A `Finding` records what is wrong and nothing else. No detector proposes or applies a fix. Coupling detection with repair allows a detector to launder its own bypass.
2. **Passing tests proves only that those tests ran**: A clean `DetectorReport` is evidence that named detectors ran on named bytes; it is never an attestation that the candidate is correct.

### The 12 Mechanical Failure Classes & Routing Dispositions:

| # | Failure Class | Code | Default Disposition | Description |
|---|---|---|---|---|
| 1 | `SelfCertification` | `SELF_CERTIFICATION` | `REFUSE` | Model asserts its own verification, admission, or authorization. |
| 2 | `FakeReceipt` | `FAKE_RECEIPT` | `REFUSE` | Digest-shaped string (64-char hex) in a host-only key. |
| 3 | `ConclusionPreload` | `CONCLUSION_PRELOAD` | `FINDING` | Prompt fixes the conclusion the model was supposed to derive. |
| 4 | `SchemaSemanticLaundering`| `SCHEMA_SEMANTIC_LAUNDERING`| `HOLD` | Syntactically valid deltas with no semantic replay. |
| 5 | `TheoremNameLaundering` | `THEOREM_NAME_LAUNDERING` | `HOLD` | Invoking a theorem by name with no applicability obligations stated. |
| 6 | `OptimalityHallucination` | `OPTIMALITY_HALLUCINATION` | `FINDING` | Claiming 'optimal' or 'best' without cost function or lower bound. |
| 7 | `ComplexityHallucination` | `COMPLEXITY_HALLUCINATION` | `FINDING` | Claiming algorithmic complexity with no cost model or measurement. |
| 8 | `BranchDropExhaustion` | `BRANCH_DROP_EXHAUSTION` | `FINDING` | Claiming search exhaustion while branches remain unexplored. |
| 9 | `PersonaAuthorityLeak` | `PERSONA_AUTHORITY_LEAK` | `REFUSE` | Persona asserting authority its binding does not carry. |
| 10| `PrivateCotDependency` | `PRIVATE_COT_DEPENDENCY` | `HOLD` | Conclusions relying on hidden `<think>` or uninspected private tokens. |
| 11| `VersionDuplication` | `VERSION_DUPLICATION` | `FINDING` | Byte-identical payload presented under new version tags. |
| 12| `DetectRepairCoupling` | `DETECT_REPAIR_COUPLING` | `FINDING` | Single artifact carrying both an objection and its repair. |

> **Claim-typing legend**
> - **[Pinned]**: taken from a file this repository already has.
> - **[Proved]**: a finite check in this notebook. Not a general proof.
> - **[Declared]**: a carrier, rule, or heading chosen for this sitting.
> - **[Open]**: something this sitting does not decide.
## Anchors

- Former notebook: `00_agentic_symbol_game_quickstart`
- The code checks one finite example. It is not a general proof.

## Exercise

Change one declared input in the code cell. The check should fail for the wrong object and pass for the finite example written here.
