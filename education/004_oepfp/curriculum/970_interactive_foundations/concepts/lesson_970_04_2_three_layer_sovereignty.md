# Lesson 970.04 -- 2. Three-Layer Sovereignty

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_970_04_2_three_layer_sovereignty.ipynb](../notebooks/lesson_970_04_2_three_layer_sovereignty.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## 2. Three-Layer Sovereignty

To prevent LLMs from bluffing their way past errors, the Symbol Game enforces an architectural separation called **Three-Layer Sovereignty**:

1. **Layer 1: Continuous Model Weights (The Engine)**
   - Matrix multiplications, embeddings, transformer attention layers.
   - Fast, broad, heuristic pattern matching across enormous corpora.
   - *Cannot be trusted to referee itself.*

2. **Layer 2: Decoding and Sampling (The Actuator)**
   - Temperature, top-$p$, beam search, token generation strategies.
   - Explores proposals, generates candidate reasoning paths.

3. **Layer 3: Discrete External Host (The Sovereign Referee)**
   - Operates outside the neural network using exact rational arithmetic ($\mathbb{Q}$).
   - Evaluates constraints, checks cycle invariants, calculates boundary defects $\Phi_1$.
   - **Fail-Closed**: If the candidate violates any constraint, Layer 3 immediately halts and refuses.
   - It cannot be persuaded, sweet-talked, or distracted by fluent token sequences.

> **Claim-typing legend**
> - **[Pinned]**: taken from a file this repository already has.
> - **[Proved]**: a finite check in this notebook. Not a general proof.
> - **[Declared]**: a carrier, rule, or heading chosen for this sitting.
> - **[Open]**: something this sitting does not decide.
## Anchors

- Former notebook: `00_symbol_game_for_beginners`
- The code checks one finite example. It is not a general proof.

## Exercise

Change one declared input in the code cell. The check should fail for the wrong object and pass for the finite example written here.
