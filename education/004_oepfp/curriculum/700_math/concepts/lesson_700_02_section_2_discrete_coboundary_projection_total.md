# Lesson 700.02 -- One weighted deviation on a triangle

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_700_02_section_2_discrete_coboundary_projection_total.ipynb](../notebooks/lesson_700_02_section_2_discrete_coboundary_projection_total.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## One weighted deviation on a triangle

The weighted absolute deviation at one potential is the sum inside Phi_1. Phi_1 itself is the minimum of that sum. This page's notebook evaluates the sum at one chosen potential on one triangle. It does not compute the minimum.

Claims on `AB`, `BC`, and `CA` are each 1. The potential is `A = 0`, `B = 1`, `C = 2`. The sum at that potential is 3.

Lesson 700.06 reads the native quotient. Lesson 700.10 checks subdeterminants of one incidence matrix. `domain.ddc.compute_phi1` refuses until a Rust adapter is wired, so this sitting does not call it and does not build a certificate.

The Poincaré / Hoffman-Kruskal statement for every directed graph is background. This sitting does not decide it.

> **Claim-typing legend**
> - **[Pinned]**: taken from a file this repository already has.
> - **[Proved]**: a finite check in this notebook. Not a general proof.
> - **[Declared]**: a carrier, rule, or heading chosen for this sitting.
> - **[Open]**: something this sitting does not decide.

## Anchors

- Former notebook: `00_advanced_discrete_deformation_algebra`
- The code checks one finite example. It is not a general proof.

## Exercise

Change one declared input in the code cell. The check should fail for the wrong object and pass for the finite example written here.

The loop sum in `research/mssn_sn_tower/math/symbol_game/2_math_cochains_repairs_and_quotients.md` is the background for this deviation. This cell does not decide that chapter's repair-versus-quotient question.

Frontier sitting already on disk: [N3_simplices_and_exact_betti_numbers.md](../../600_mssn_frontier/N3_simplices_and_exact_betti_numbers/N3_simplices_and_exact_betti_numbers.md). It is a different folder. This lesson does not replace it.
