# Write a workflow people can use

**Start with one real task and one working path.** The library can grow to
hundreds of recipes if each one keeps a small, clear contract.

## Give the reader a place to stand

Open with the result they want, when to use the recipe, what they need and what
files they will keep. Use the [recipe template](workflow_recipe_template.md).
Put optional mathematics, large schemas and historical detail behind links or
an expandable section.

## Make each step resumable

- Give one action and its visible expected result at a time.
- Say where to run commands and name the shell. Use fresh run paths.
- Name the file to keep before the next action.
- Pair a failure message with a concrete next step.
- End with a stop point or one useful next page.

Use ordinary words before protocol terms. Preserve exact field names, status
labels, mathematical symbols and commands in the technical reference. Legibility
should not come from renaming the protocol differently on every page.

These are editorial design choices. We have not run a clinical attention study
or demonstrated that a reading style treats ADHD.

## Keep examples honest

Label fixtures, illustrations, model responses and actual measurements separately.
Keep an expected answer out of prompts and their schemas. Use independent task
checks. Preserve failed attempts and unknown values; report successful-path and
whole-development expense separately.

A grammar example needs a declared start and decoder. A five-agent example
needs a global query, shared accounting and actual concurrency evidence if
concurrency is claimed. A claimed code execution needs the executed command
and result, not a file-presence flag.

## Before adding the recipe to the library

1. Complete its purpose, source/recipe version, inputs, outputs and checker.
2. Run the copyable path in a clean intended environment. Record dependencies.
3. Run a counterexample that must fail for the advertised reason.
4. Check local links, code fences, registry references and implementation status.
5. Keep raw/derived evidence distinct and submit the source through a pull request.

Give a new recipe a real registry entry with an accurate status. Leave future
ideas out of the supported list until their working path exists. A page can
be useful while marked experimental; it should tell the reader so promptly.

## Completion and Wiki publication

Publish or update the workflow's Wiki entry as part of completing its working
implementation. Keep its registry/DAG ID and Wiki link together. Each entry needs:

- Purpose, exact implementation/version, inputs, outputs and execution steps.
- The mathematical property actually checked, checker identity and open obligations.
- Calls, token ceilings, whole-run cost cap, time limits and failure handling.
- Validation commands and pinned evidence; actual model results only when measured.
- Known limits, unresolved work and a resume point.

Update the workflow index and sidebar so readers can find it. Check local links
and compare the targeted pages with the live Wiki before publishing; preserve
unrelated live edits. Retain the published commit and page hashes in the
documentation receipt. Do not mark publication complete after only a local edit.

Keep **proposed**, **implemented/synthetic-tested** and **measured** distinct.
Update the results page after actual runs, including failures and unavailable
fields. A design enumeration is not a collection of completed runners. Never
publish a private benchmark answer, its derivation or its storage path.

The current QM documentation mapping is `dag/wiki/workflow_documentation.json`.
Its live pages start at the [QM benchmark](workflow_qm_benchmark.md).

[Workflow library](workflow_library.md) · [Recipe template](workflow_recipe_template.md)
