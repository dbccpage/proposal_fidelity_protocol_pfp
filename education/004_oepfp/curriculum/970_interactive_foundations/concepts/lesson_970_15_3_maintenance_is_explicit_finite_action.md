# Lesson 970.15 -- 3. Maintenance is an explicit finite action

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_970_15_3_maintenance_is_explicit_finite_action.ipynb](../notebooks/lesson_970_15_3_maintenance_is_explicit_finite_action.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## 3. Maintenance is an explicit finite action

The Alpha maintenance example imposes a distinction, observes it
unmet, then admits a witness. A uniform rule later erases that
distinction under the active profile; the next *invoked* maintenance
step introduces another witness. Compare reports, states, and event
histories. Two matching report values need not mean identical states
or histories. The final maintenance checkpoint is inert when the
requirement is already met. This is a bounded host algorithm, not
a self-interpreter or continuous autonomous process.

**Assessment M (4 points).** Trace the eight events and distinguish
the two `emitted=2` repairs from the `emitted=0` checkpoint. Then test
a new presentation domain, cookies: two labels are supplied as data,
a requirement is imposed, and a witness is built. Nothing in the
interpreter validates claims about baking; the outside meaning of
these tokens is supplied by the lesson. Predict why deleting `impose`
must refuse maintenance.

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
