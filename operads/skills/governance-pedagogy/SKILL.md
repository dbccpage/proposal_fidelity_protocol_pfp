---
name: governance-pedagogy
description: "Gate lesson folders (prose, notebook, videos) and learning checks; a folder alone is not evidence of learning."
operad_source_colours: ["Code", "Paper"]
operad_target_colour: "Receipt"
operad_arity: 2
operad_residual: "unknown"
families: [governance, pedagogy, education]
---

# governance-pedagogy

AuthorityEffect: None.

## The single rule

> A numbered-track lesson is structured across four subdirectories (`concepts/`, `notebooks/`, `scripts/`, `videos/`). The prose page links to the companion notebook. A notebook run of a finite example is evidence that the example ran. It is not evidence that a person learned the idea, and it is not a proof of the general claim in the lesson title.

## What this gate owns

1. **4-Directory Lesson Architecture:** Within the checker's explicit curriculum-root allowlist, each directory whose name starts with three or four ASCII digits and an underscore (`NNN_*` or `NNNN_*`) is a track. Legacy roots remain declared, and `education/documentation/007_oelggr/curriculum` is included. Each track contains four subdirectories: `concepts/`, `notebooks/`, `scripts/`, and `videos/`. A lesson is defined by matching slugs across all four subdirectories. The concept document links directly to the companion notebook.
2. **Laboratory Engineering Standards (`LabEngineer`):**
   - **Environment Preflight:** Code cell asserting runtime environment (`sys.version`, Python >= 3.10).
   - **Prediction Gate:** Code cell committing `prediction = "..."` prior to test evaluation.
   - **Pilot Lab Execution:** Headless execution of target pilot labs must execute >= 4 code cells without exception.
   - **Zero Prose Bloat:** Markdown cells in notebooks must remain strictly <= 25 lines; theoretical exposition belongs in `concepts/`.
3. **Pedagogical Adversary Boundary (`PedagogicalAdversary`):**
   - **Prose Decoupling:** Word overlap between concept markdown and notebook markdown must not exceed 35%.
   - **Falsifiers & Counterexamples:** Notebooks must contain explicit negative/malformed counterexample tests (`try: ... except`, `pytest.raises`, or `rejected`/`illegal` assertions).
4. **Learning Check & Non-Learning Invariant:** Notebooks must contain executable `assert` statements. `--strict-checks` exits 1 if any notebook lacks assertions. An execution confirms code correctness on that host; it is not evidence that a person learned or that a general theorem holds.
5. **Cognitive Scaffolding & Expertise Reversal:**
   - Novice tracks (Tier 0–1: `000_beginners`, `100_novices`) require worked examples and completion steps before generative coding.
   - Intermediate and frontier tracks (Tier 2–3) deliberately fade scaffolding; over-guided step-by-step walkthroughs for experienced learners cause expertise reversal.
   - Productive failure is reserved for conceptual challenges in intermediate/advanced tracks, never for younger children (ages 5–11) or initial procedural syntax.
6. **Four-Tag Claim Legend:** Markdown in lessons must observe `[Pinned]`, `[Proved]`, `[Declared]`, and `[Open]`. Illustrative toys must be labeled illustrative and asserted equal to the pinned verifier.
7. **Age Floors Stay Separate:** Track `000_beginners` states ages 5 to 500. The how-to-play manual states ages 11 to 500. This gate does not merge those floors.

## What this gate does not own

- Packet envelopes, cemetery logs, and manifold retraction stay in `governance-pfp`.
- How to write one sitting stays in `pedagogy-lesson-sitting`.
- Paper engagement kits stay in `dianoia-dime`.
- Content-quality rubrics stay in `lib-pedagogy-improvement`.
- Declared attention and pass-rate targets stay in `governance-pfp/references/pedagogy_and_curriculum.md`. This gate does not treat those targets as a measured learner trial.

`how_to_play` and `system_integration` are not numbered-track lesson folders. This checker does not reshape them.

A concept-page supplement may declare one literal line such as
`supplement_for: lesson_1000_01_local_green_global_red_foundations` inside its
leading `---` header. The value is one bare local primary stem: no path, quotes
or filename suffix. The checker excludes that page from primary companion
requirements only after binding it to an existing unique local primary.
Malformed/duplicate, self, dangling, case-ambiguous, chained or cyclic bindings
refuse discovery. Body text and later header-like blocks do not declare a role.
Primary identities still come from the union of notebook, concept and script
stems, so a primary's missing companion is reported. Feedback filenames alone
grant no exclusion. Discovery does not recursively infer curriculum roots from
archives or unregistered documentation directories; a videos directory or
supplement role establishes no recording, mathematical result or learner outcome.


## References

- [Cognitive Scaffolding and Expertise Reversal Discipline](references/cognitive_scaffolding_and_fading.md)
- [Claim Tag Legend and Proof Discipline](references/claim_tag_legend_and_proof_discipline.md)
- [Learning Evidence Discipline](references/learning_evidence.md)
- [Lesson Sitting Discipline](references/lesson_sitting.md)

## Verification

```bash
python operads/skills/governance-pedagogy/scripts/check_lesson_folders.py
```

The script exits 0 when every numbered-track lesson folder has its prose page, notebook, `videos/` directory, and prose link. It prints `open_learning_checks` for notebooks with no `assert`. Exit 0 with a non-zero open count means the shape holds and those checks are still open.

```bash
python operads/skills/governance-pedagogy/scripts/check_lesson_folders.py --strict-checks
```

`--strict-checks` exits 1 when any numbered-track notebook has no `assert`.
