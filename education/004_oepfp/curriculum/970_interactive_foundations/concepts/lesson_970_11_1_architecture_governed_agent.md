# Lesson 970.11 -- 1. The Architecture of a Governed Agent

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_970_11_1_architecture_governed_agent.ipynb](../notebooks/lesson_970_11_1_architecture_governed_agent.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

# 11 - Build Your Own Symbol Game Agent

> **Claim-typing legend**
> - **[Pinned]**: reproduced from a named local script, benchmark, or cryptographic receipt (`code/*.json`).
> - **[Proved]**: established by a machine-checked Lean 4 theorem with reported kernel axioms.
> - **[Declared]**: a grammar, carrier alphabet, cost, or objective chosen by the model.
> - **[Open]**: an obligation for which this package supplies no proof or exhaustive decision.

*Capstone Interactive Workshop: Wrapping OpenRouter and Local LLMs in the Layer 3 Governor*

---

## 1. The Architecture of a Governed Agent

In this capstone workshop, you will assemble an end-to-end Symbol Game agent that interfaces with an LLM (via OpenRouter API, local Ollama/vLLM, or offline mock) and enforces discrete mathematical governance:

```
[User Query]
     |
     v
[SymbolGameLLMClient] --> Generate Fenced Prompt P_K: Delta(V) -> Delta(K)
     |
     v
[LLM Generation] (Layer 2)
     |
     v
[PacketFirewallHost] (Layer 3) --> Linter: Closed Operators + Whitelist
     |
     v
[GovernorAdapter] (Layer 3) --> Exact Rational Coboundary Defect Check
     |
     v
[Verified Deduction or Retraction Refusal]
```

## Anchors

- Former notebook: `11_build_your_own_symbol_game_agent`
- The code checks one finite example. It is not a general proof.

## Exercise

Change one declared input in the code cell. The check should fail for the wrong object and pass for the finite example written here.
