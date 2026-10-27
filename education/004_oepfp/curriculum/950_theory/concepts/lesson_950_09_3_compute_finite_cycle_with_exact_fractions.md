# Lesson 950.09 -- 3. Compute a finite cycle with exact fractions

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_950_09_3_compute_finite_cycle_with_exact_fractions.ipynb](../notebooks/lesson_950_09_3_compute_finite_cycle_with_exact_fractions.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## 3. Compute a finite cycle with exact fractions

This **newly declared** board has vertices `a,b,c` and edges
`a→b`, `b→c`, `c→a`. For a vertex potential `p`, set
`delta(p)[u→v] = p[v] - p[u]`. For edge target `w`, the residual is
`w - delta(p)`. The former fixed-section `phi1` scorer is retired: it was not the quotient minimum.
Retained outputs below are historical; rerunning the scorer now refuses until a native adapter exists. The module does not construct a general cochain complex or infer a physical
gauge field.

> **Claim-typing legend**
> - **[Pinned]**: taken from a file this repository already has.
> - **[Proved]**: a finite check in this notebook. Not a general proof.
> - **[Declared]**: a carrier, rule, or heading chosen for this sitting.
> - **[Open]**: something this sitting does not decide.
## Anchors

- Former notebook: `12_genesis_symbol_game_evidence`
- The code checks one finite example. It is not a general proof.

## Exercise

Change one declared input in the code cell. The check should fail for the wrong object and pass for the finite example written here.

Tower files for this sitting:

- [research/mssn_sn_tower/_theory/README.md](../../../../../research/mssn_sn_tower/_theory/README.md)
- [research/mssn_sn_tower/_theory/03_the_symbol_game.md](../../../../../research/mssn_sn_tower/_theory/03_the_symbol_game.md)
- [research/mssn_sn_tower/_theory/09_authority_fences.md](../../../../../research/mssn_sn_tower/_theory/09_authority_fences.md)
- [research/mssn_sn_tower/education_crosswalk_genesis_core.md](../../../../../research/mssn_sn_tower/education_crosswalk_genesis_core.md)

Frontier sitting already on disk: [N0_the_genesis_distinction.md](../../600_mssn_frontier/N0_the_genesis_distinction/N0_the_genesis_distinction.md). It is a different folder. This lesson does not replace it.
