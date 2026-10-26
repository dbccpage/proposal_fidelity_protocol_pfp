# Lesson 970.09 -- Section 4: Prompt Civilization & Anti-Morphism Hint-Injection

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_970_09_anti_morphism_hints.ipynb](../notebooks/lesson_970_09_anti_morphism_hints.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## Section 4: Prompt Civilization & Anti-Morphism Hint-Injection

In traditional prompting, when an LLM fails, engineers either:
1. Provide the direct answer in the prompt (which prompts sycophantic parroting).
2. Offer unconstrained rewrites (which simply hallucinates a different error).

### The Anti-Morphism Principle
An **anti-morphism** is an interior operator $P_p: \mathcal{P}(U) \to \mathcal{P}(U)$ on a candidate proposal universe $U$:
$$P_p(A) = \{ x \in A : p(x) \}$$
Every filter anti-morphism is:
- **Decreasing**: $P_p(A) \subseteq A$
- **Monotone**: $A \subseteq B \implies P_p(A) \subseteq P_p(B)$
- **Idempotent**: $P_p(P_p(A)) = P_p(A)$

Filters commute: $P_p \circ P_q = P_{p \wedge q}$. Thus, any finite collection of filters converges to a single order-independent fixpoint.

### The 5 Closed Anti-Morphism Operators:
1. `PIN(alphabet)`: Carrier codepoint firewall. Keeps candidates using only allowed tokens.
2. `SHAPE(arity)`: Structural grammar filter. Keeps candidates matching tuple length $k$.
3. `DEMAND(predicate)`: Residual-derived condition injected by the host.
4. `REFUSE(predicate)`: Fail-closed elimination of invalid states.
5. `LAND_ON_ZERO(phi_1)`: Retraction operator keeping zero-obstruction states.

### Three Typed Final Verdicts:
1. `LANDED(x)`: $|A_\infty| = 1$ — Exact witness landed.
2. `REFUSED_EMPTY`: $A_\infty = \emptyset$ — Host proves no admissible solution exists in the carrier. An honest refusal.
3. `RESIDUAL(A)`: $|A_\infty| > 1$ — Under-determined; requires a further demand.

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
