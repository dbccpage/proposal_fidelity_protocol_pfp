# Lesson 700.03 -- Section 3: Sheaf Cohomology Obstruction Classes & Abramsky-Brandenburger Contextuality

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_700_03_section_3_sheaf_cohomology_obstruction_classes.ipynb](../notebooks/lesson_700_03_section_3_sheaf_cohomology_obstruction_classes.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## Section 3: Sheaf Cohomology Obstruction Classes & Abramsky-Brandenburger Contextuality

### [Declared] Cellular Sheaves on Cell Complexes
Following Hansen & Ghrist (2019), a cellular sheaf $\mathcal{F}$ on a cell complex $X$ associates:
- A vector space (stalk) $\mathcal{F}(\sigma)$ to each cell $\sigma \in X$.
- A linear restriction map $\mathcal{F}_{\sigma \unlhd \tau}: \mathcal{F}(\sigma) \to \mathcal{F}(\tau)$ whenever $\sigma \subseteq \overline{\tau}$, satisfying the functorial composition $\mathcal{F}_{\rho \unlhd \tau} = \mathcal{F}_{\sigma \unlhd \tau} \circ \mathcal{F}_{\rho \unlhd \sigma}$.

### [Declared] Contextuality as Non-Extendibility of Local Sections
In the Abramsky-Brandenburger sheaf-theoretic framework for quantum contextuality and non-locality:
- An open cover $\mathcal{U} = \{U_1, U_2, \dots, U_m\}$ represents distinct measurement or reasoning contexts.
- A collection of local sections $s_i \in \mathcal{F}(U_i)$ represents locally consistent evaluations.
- Compatibility on overlaps requires $s_i|_{U_i \cap U_j} = s_j|_{U_i \cap U_j}$.
- A system of local sections fails to extend to a global section $S \in \mathcal{F}(X)$ if and only if the system exhibits non-vanishing holonomy around non-contractible cycles.

In Čech cohomology, the pairwise transition differences define a 1-cocycle:
$$\omega_{ij} = s_j|_{U_{ij}} - s_i|_{U_{ij}} \in \mathcal{F}(U_i \cap U_j)$$
The obstruction class $[\omega] \in \check{H}^1(\mathcal{U}; \mathcal{F})$ is zero if and only if the local sections can be glued into a global section.

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

Tower files for this sitting:

- [research/mssn_sn_tower/math/symbol_game/readme.md](../../../../../research/mssn_sn_tower/math/symbol_game/readme.md)
- [research/mssn_sn_tower/math/symbol_game/4_math_context_categories_and_noncongruence.md](../../../../../research/mssn_sn_tower/math/symbol_game/4_math_context_categories_and_noncongruence.md)
