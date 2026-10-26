# Learning Evidence Discipline

AuthorityEffect: None.

## The Principle

> A learning check is a task the learner can fail. A folder, a clip, and a declared rate are records that a teaching object exists. They are not that task.

## What Counts as a Learning Check

1. **Failable Notebook Assertions**: A notebook cell whose `assert` fails when the input is the wrong object, and which the learner runs.
2. **Interactive Diagnostic Questions**: A diagnostic question with a stated answer, where the runnable cell does not silently force that answer before the learner chooses.
3. **Recorded Restatements**: The learner writes the idea in one or two sentences after the sitting, and a reviewer can evaluate whether the sentence captured the idea.

Record which of the three was used. A notebook execution shows that the finite example ran on that machine. It does not show that a person learned, and it does not prove the general statement in the lesson title.

## What Does Not Count

- The lesson folder, the prose page, or an empty directory under `videos/`.
- A pass-rate target written in documentation or references.
- A headless run that executes cells the author already filled with the right answer, reported as a learner pass.

## Open Notebook Audit

`governance-pedagogy` prints `open_learning_checks` for numbered-track notebooks that contain no `assert`. That list is an active structural gap. Closing it means adding a fail-able check, not deleting the line from the report.
