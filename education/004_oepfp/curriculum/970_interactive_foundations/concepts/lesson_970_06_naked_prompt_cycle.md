# Lesson 970.06 -- The naked-prompt cycle sum

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_970_06_naked_prompt_cycle.ipynb](../notebooks/lesson_970_06_naked_prompt_cycle.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## The naked-prompt cycle sum

### The Vulnerability of Continuous Token Generation
Large language models operate by predicting the next token in a continuous embedding space. When tasked with strict logical or arithmetic consistency—such as circular dependencies:
$$\text{Task: } A \to B = +1, \quad B \to C = +1, \quad C \to A = +1$$
the accumulated holonomy around the loop is:
$$1 + 1 + 1 = 3 \neq 0$$
In a continuous generation setting, the model often claims:
> *"I have verified all constraints and the cycle is completely consistent! Sum = 0. Q.E.D."*

This is **self-certification**: the model asserts its own conclusion without an independent oracle.

Three-layer train/decode/verify is lesson 970.04. This page only checks the naked-prompt cycle sum.

## Exercise

Change one declared input in the code cell. The check should fail for the wrong object and pass for the finite example written here.
