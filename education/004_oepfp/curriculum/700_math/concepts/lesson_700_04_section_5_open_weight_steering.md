# Lesson 700.04 -- Section 5: Deep Comparative Analysis: Open-Weight Steering vs. Closed Frontier Model Control

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_700_04_section_5_open_weight_steering.ipynb](../notebooks/lesson_700_04_section_5_open_weight_steering.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## Section 5: Deep Comparative Analysis: Open-Weight Steering vs. Closed Frontier Model Control

| Dimension | Open-Weight Model Manipulation (Internal) | Closed Frontier Model Control (External) |
|---|---|---|
| **Mechanism** | Layer 1 Attention Steering & Layer 2 Logit Masking | Layer 3 Discrete Boundary Filtering & Anti-Morphisms |
| **Intervention Point** | Pre-softmax query-key attention matrix; logits $z \in \mathbb{R}^V$ | Generated token strings; candidate payload deserialization |
| **Mathematical Nature** | Continuous, smooth deformation in $\mathbb{R}^d$ via softmax | Discrete set-theoretic interior operators on candidate lattice |
| **Carrier Enforcement** | Masking off-carrier logits to $-\infty$ forces 100% token mass | Fail-closed syntax & codepoint regex firewall (`FW-CARRIER`) |
| **Semantic Invariance** | Fails: model outputs on-carrier tokens that are mathematically false | Enforces exact arithmetic cycle sums via integer coboundaries |
| **Attention Concentration** | 4D additive mask raises carrier attention $0.058 \to 1.0$ | External host does not touch or depend on internal attention |
| **Manifold Reduction** | Soft probability shifts; prone to cancellation laundering | Monotone decreasing chain $A_{t+1} = A_t \cap \{x : p(x)\}$ to fixpoint |
| **Failure Mode** | Hallucinates plausible proofs; continuous errors cancel silently | Fail-closed rejection: returns `REFUSED_EMPTY` or `RESIDUAL` |
| **Cryptographic Receipt** | None: relies on floating-point activation traces | Full RFC-8785 JSON digest + SHA-256 deterministic receipt |

### The Empirical Finding
As benchmarked in `bench/mechanism/`:
1. Sweeping attention steering bias $\delta \in [0, 16]$ concentrates carrier attention to $1.0$, but generated reasoning **does not converge to correct answers**.
2. Masking off-carrier logits to $-\infty$ forces 100% carrier membership, but outputs degenerate tokens (e.g. `"555555"`) that are arithmetically false.
3. This cell asks the native calculator for Phi1 on one triangle before and after one claim change. It does not run a solver cascade, and it does not claim that every defect descends to zero.

> **Claim-typing legend**
> - **[Pinned]**: taken from a file this repository already has.
> - **[Proved]**: a finite check in this notebook. Not a general proof.
> - **[Declared]**: a carrier, rule, or heading chosen for this sitting.
> - **[Open]**: something this sitting does not decide.
## Anchors

- Former notebook: `00_advanced_discrete_deformation_algebra`
- The code checks one finite example. It is not a general proof.

## Exercise

Change one declared input in the code cell. The check should fail for the wrong object and pass for the finite example written here.

Tower files for this sitting:

- [research/mssn_sn_tower/math/symbol_game/readme.md](../../../../../research/mssn_sn_tower/math/symbol_game/readme.md)
