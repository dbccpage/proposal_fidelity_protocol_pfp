# Lesson 970.17 -- 5. Compare with a real nontrivial host run

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_970_17_5_compare_with_real_nontrivial_host_run.ipynb](../notebooks/lesson_970_17_5_compare_with_real_nontrivial_host_run.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## 5. Compare with a real nontrivial host run

Paper 033 drives the Paper 032 governor on a weighted three-cycle.
The initial edge assertions have nonzero irreducible defect; a host
`CUT` replaces claims and checks zero. This is a *different declared
board* from the one-edge adapter, and that `CUT` changes claims. It
does not prove that Alpha observations always admit an Omega repair.

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
