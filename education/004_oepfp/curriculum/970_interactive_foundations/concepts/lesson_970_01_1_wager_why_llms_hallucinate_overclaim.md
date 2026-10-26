# Lesson 970.01 -- 1. The Wager: Why LLMs Hallucinate and Overclaim

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_970_01_1_wager_why_llms_hallucinate_overclaim.ipynb](../notebooks/lesson_970_01_1_wager_why_llms_hallucinate_overclaim.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

# 00 - How to Read & Play the Symbol Game Series

> **Claim-typing legend**
> - **[Pinned]**: reproduced from a named local script, benchmark, or cryptographic receipt (`code/*.json`).
> - **[Proved]**: established by a machine-checked Lean 4 theorem with reported kernel axioms.
> - **[Declared]**: a grammar, carrier alphabet, cost, or objective chosen by the model.
> - **[Open]**: an obligation for which this package supplies no proof or exhaustive decision.

*Orientation, the Wager, Three-Layer Sovereignty, and Gateway Configuration*

---

## 1. The Wager: Why LLMs Hallucinate and Overclaim

An autoregressive language model optimizes token likelihood under continuous softmax distribution $\text{Softmax}(W_U h_T / \tau)$. In standard dense generation, coordinate cancellation in continuous space $\mathbb{R}^d$ allows contradictory assertions to cancel out algebraically without triggering a syntax error.

The **Symbol Game** introduces an external, discrete, host-enforced discipline:
1. **No Unpriced Axioms**: *"An unpriced rewrite is a smuggled axiom."* (Woland Swarm Operational Axiom).
2. **Three-Layer Sovereignty**: Prompts cannot rewrite weights (Layer 1), logit masks are local and leaky (Layer 2), so truth must be enforced by an independent host replay oracle (Layer 3).
3. **Discrete $L_1$ Defect Preservation**: Coboundary defects $\Phi_1 = \|\delta c_0 - W_E\|_1$ cannot cancel out silently; they are explicitly counted and minimized.

## 2. Four Kinds of Achievement

These four grades answer different questions and must never be conflated:

| Grade | Question | What a successful result establishes |
|---|---|---|
| **Representation** | Is the state, operation, or claim explicitly encoded? | The object can be inspected and replayed under its schema. |
| **Derivation** | Does the proposition follow from the named premises? | The stated theorem holds under those premises. |
| **Recovery** | Does a fixed correspondence match an independently specified object? | The two constructions agree within the declared scope. |
| **Prediction** | Was a prospective claim stated before its test data? | A falsifiable claim has survived the stated test. |

### Two Golden Rules
1. **A receipt is never its payload.** A passing test proves the code ran and compared expected values; it does not prove universal validity.
2. **Ties remain ties.** If an objective leaves competing minima, keeping the class is honest; choosing a single favorite requires an explicit theorem.

## Anchors

- Former notebook: `00_how_to_read_and_play`
- The code checks one finite example. It is not a general proof.

## Exercise

Change one declared input in the code cell. The check should fail for the wrong object and pass for the finite example written here.
