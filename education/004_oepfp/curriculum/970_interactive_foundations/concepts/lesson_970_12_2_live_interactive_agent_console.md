# Lesson 970.12 -- 2. Live Interactive Agent Console

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_970_12_2_live_interactive_agent_console.ipynb](../notebooks/lesson_970_12_2_live_interactive_agent_console.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## 2. Live Interactive Agent Console

Use the interactive widget below to test custom reasoning queries with real-time firewall validation:

## 3. Scope: CAN-Show vs. CANNOT-Show

> **CAN-Show**:
> - Demonstrates how to wrap any OpenAI-compatible API or local model in a Layer 3 Governor.
> - Demonstrates automated telemetry collection (token support, fluff detection, unpriced rewrite density).
>
> **CANNOT-Show**:
> - Does not eliminate the need for domain-specific contract definitions.

## 4. Student Exercises

### Exercise 11.1: Building Custom Contracts
Suppose you want to restrict an LLM to proving Euclidean geometry theorems. What closed operator vocabulary would you declare in `CLOSED_OPERATORS`?

<details>
<summary><b>Click to reveal solution</b></summary>
A minimal closed operator vocabulary for Euclidean geometry could be:
`{CONSTRUCT, INTERSECT, CONGRUENT, PARALLEL, SIMILAR, ASSERT, VERIFY, REFUSE, QED}`.
Every statement must start with one of these verbs and reference previously constructed geometric entities.
</details>

## 5. Anchors

- **Paper 032 Sections**: §10
- **Ledger IDs**: `PO032-C71` through `PO032-C74`
- **Code**: `notebook_lib/governor_adapter.py`, `notebook_lib/llm_client.py`

> **Claim-typing legend**
> - **[Pinned]**: taken from a file this repository already has.
> - **[Proved]**: a finite check in this notebook. Not a general proof.
> - **[Declared]**: a carrier, rule, or heading chosen for this sitting.
> - **[Open]**: something this sitting does not decide.
