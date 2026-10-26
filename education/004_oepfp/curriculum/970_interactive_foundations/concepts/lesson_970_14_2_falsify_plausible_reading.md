# Lesson 970.14 -- 2. Falsify a plausible reading

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_970_14_2_falsify_plausible_reading.ipynb](../notebooks/lesson_970_14_2_falsify_plausible_reading.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## 2. Falsify a plausible reading

The provided bad source admits a binary form but supplies one argument
to an instance. Predict the source line and refusal. Then make a second
mutant: remove the instance from the good source. The `check derives`
assertion should fail because the required positive instance is absent.

**Assessment B (3 points).** Change `learner_refusal` if your prediction
differed. Identify which failure is lexical/arity and which is an
unsatisfied host assertion. The CLI suppresses a success summary on
either failed run.

> **Claim-typing legend**
> - **[Pinned]**: taken from a file this repository already has.
> - **[Proved]**: a finite check in this notebook. Not a general proof.
> - **[Declared]**: a carrier, rule, or heading chosen for this sitting.
> - **[Open]**: something this sitting does not decide.
## Anchors

- Former notebook: `13_alpha_to_omega_execution`
- The code checks one finite example. It is not a general proof.

## Exercise

Change one declared input in the code cell. The check should fail for the wrong object and pass for the finite example written here.
