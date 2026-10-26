# Lesson 970.03 -- 1. The Core Problem: The "Naked Prompt" and Cancellation Laundering

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_970_03_naked_prompt_cancellation.ipynb](../notebooks/lesson_970_03_naked_prompt_cancellation.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

# Track 0: The Symbol Game for Beginners
## A Zero-Prerequisite Guide to Plain Prompts, Three-Layer Sovereignty, and Discrete Host Verification


---

### Claim Typing Legend
- `[Pinned]`: Directly verified against an explicit code fixture, local trace, or host receipt.
- `[Proved]`: Formally verified by an independent discrete oracle or decision procedure.
- `[Declared]`: Design policy, API schema, or operational contract.
- `[Open]`: Unresolved question or empirical edge case under active investigation.

---

### Anchors & Provenance
- **Paper 032 Anchor**: *The Symbol Game: Three-Layer Sovereignty and Discrete L1 Projection* (Section 1: Foundations and the Wager).
- **Paper 033 Anchor**: *The Symbol Game Practitioner's Field Manual* (Section 2: The Three-Cycle Play Demo).
- **Substrate Module**: `omega_engine_education.notebooks.scenes.three_cycle_phi1` (Exact rational cycle defect computation).

---

### Epistemic Bounds & Scope
- **What this notebook supports**: A transparent, runnable demonstration in Python showing why external discrete verification catches contradictions on directed cycles that conversational language models launder, how the Three-Layer Sovereignty architecture separates generation from verification, and how sealed packets detect tampering.
- **What this notebook does NOT support**:
  1. Does *not* claim that real-world reasoning tasks are limited to 3-cycles or simple networks.
  2. Does *not* claim that large language models lack fluent language generation capability.
  3. Does *not* claim that local green tests on toy examples imply universal mathematical correctness.
- **Narrowest Defensible Claim**: On any directed cycle of difference constraints, the integer coboundary sum around the cycle is an exact topological invariant whose non-zero value demonstrates contradiction without requiring model introspection.

## 1. The Core Problem: The "Naked Prompt" and Cancellation Laundering

When you ask a frontier language model a question in natural language (a "naked prompt"), the model produces a probabilistic stream of tokens. It predicts the most likely next token given previous tokens.

However, continuous probabilistic models have a well-known vulnerability: **cancellation laundering**. If a set of relationships contains an internal contradiction, the model will often weave a fluent explanation that sounds entirely plausible, effectively "canceling" or hiding the mathematical defect through persuasive prose.

Let us see this in the simplest possible setting: **a directed cycle of difference constraints**.

Imagine three items: $A$, $B$, and $C$. Suppose an agent claims:
1. $B$ exceeds $A$ by $1$: $x_B - x_A = 1$
2. $C$ exceeds $B$ by $1$: $x_C - x_B = 1$
3. $A$ exceeds $C$ by $1$: $x_A - x_C = 1$

If we sum these differences around the closed loop:
$$(x_B - x_A) + (x_C - x_B) + (x_A - x_C) = 0$$

The sum around any valid closed loop **must equal zero**.
Yet the agent claimed:
$$1 + 1 + 1 = 3 \neq 0$$

An LLM asked "can this arrangement exist?" might respond:
> *"In a cyclic priority scheme or non-transitive tournament (like Rock-Paper-Scissors), each item can indeed dominate the next..."*

While non-transitive preferences exist in game theory, for **metric quantities** ($x \in \mathbb{R}$), $3 \neq 0$ is a fatal contradiction. The Symbol Game exists to prevent language models from laundering such contradictions.

## Exercise

Change one declared input in the code cell. The check should fail for the wrong object and pass for the finite example written here.
