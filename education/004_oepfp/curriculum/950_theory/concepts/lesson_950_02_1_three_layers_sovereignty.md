# Lesson 950.02 -- 1. The Three Layers of Sovereignty

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_950_02_1_three_layers_sovereignty.ipynb](../notebooks/lesson_950_02_1_three_layers_sovereignty.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

# 03 - Three-Layer Sovereignty: Train, Decode, Verify

> **Claim-typing legend**
> - **[Pinned]**: reproduced from a named local script, benchmark, or cryptographic receipt (`code/*.json`).
> - **[Proved]**: a finite check in this notebook. Not a general proof.
> - **[Declared]**: a grammar, carrier alphabet, cost, or objective chosen by the model.
> - **[Open]**: an obligation for which this package supplies no proof or exhaustive decision.

*Train-Time Weights Unreachable, Decode-Time Simplex Projection, and Verify-Time Host Oracle*

---

## 1. The Three Layers of Sovereignty

In standard LLM deployment, practitioners often attempt to enforce safety, truth, or logic entirely through **prompt engineering**. The Three-Layer Sovereignty principle establishes why this approach is mathematically insufficient.

```
+-------------------------------------------------------------+
| Layer 1: Train Time (Model Weights W, W_E)                  |
| Status: UNREACHABLE at inference.                           |
| Prompts enter as row lookups in W_E. Cannot alter weights.  |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
| Layer 2: Decode Time (Autoregressive Simplex Sampling)      |
| Status: CONDITIONAL.                                        |
| Logit masking -inf projects probabilities onto Delta(K).     |
| Finite temperature allows tail leakage; greedy lacks vision.|
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
| Layer 3: Verify Time (Independent Host Replay Oracle)       |
| Status: DECLARED & FAIL-CLOSED.                             |
| Independent Python/Lean host checks discrete invariants.   |
| Disallows unpriced rewrites and enforces total truth.       |
+-------------------------------------------------------------+
```

## Anchors

- Former notebook: `03_three_layer_sovereignty`
- The code checks one finite example. It is not a general proof.

## Exercise

Change one declared input in the code cell. The check should fail for the wrong object and pass for the finite example written here.

This cell compares one mock unfenced completion with one mock fenced completion. It does not train a model.
