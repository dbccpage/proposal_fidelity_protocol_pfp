---
name: glossa-claim-hygiene-linter
description: "Lint PRs, preprints, docstrings and artifacts for hype verbs and replace them with bounded wording."
families: [oecog, text_audit]
operad_source_colours: ["Paper", "Code"]
operad_target_colour: "Audit"
operad_arity: 2
operad_residual: neutral
---

# glossa-claim-hygiene-linter

**Status:** `CANDIDATE`
**AuthorityEffect:** `None`
**Council:** `L3_nous_glossa`

## When to use

Use before submitting pull requests, publishing preprint drafts, or emitting evidence
artifacts where claim discipline is required under repository governance.

## Inputs

- Candidate Markdown files, source code docstrings, commit messages, or PR bodies.
- The governance claim hygiene rule dictionary:
  - Banned hype verbs: `proves`, `guarantees`, `mathematically verifies`, `fundamentally`, `true intelligence`, `impossible`, `universal`, `flawless`, `perfectly`, `clearly`, `obviously`, `simply`, `merely`, `weaponized`.
  - Canonical replacement defaults:
    - `proves` -> `shows in this model` or `supports`
    - `guarantees` -> `guarantees under the declared assumptions`
    - `fundamental flaw` -> `failure mode`
    - `LLMs cannot` -> `this setup does not show that LLMs can`
    - `safe ASI` -> `bounded toy evaluator`
    - `mathematically verified` -> `checked by this oracle/test`

## Protocol

1. Read the target document stream without modifying encoding.
2. Scan for occurrences of banned lexical tokens and unsubstantiated generalization claims.
3. Compute structured diff suggestions replacing banned tokens with narrow, defensible phrasing.
4. Ensure artifact summaries explicitly declare:
   - What the artifact supports.
   - What the artifact does not support.
   - The narrowest defensible claim.
   - The next test needed.
5. Emit an audit report detailing match locations and replacement diffs.

## Terminals

`COMPLIANT`, `LINT_DIFF_PRODUCED`, `UNRESOLVED_VIOLATIONS`.

## Nonclaims

Linting for claim hygiene checks syntax and declared vocabulary against the rule table;
it does not evaluate underlying empirical truth or mathematical correctness beyond
the scanned text.

## Imported mathematical identities

Before transferring an identity, name its carrier, domain, codomain, degree shift,
orientation and hypotheses. Check one boundary example against those conventions.
For a full simplex of dimension `n` on `n+1` ordered vertices, with the empty
face at degree `-1`, the augmented complement uses degree `k -> n-k-1`.
The triangle edge returns
with sign `+1`, contradicting the historical geometric-sign substitution `-1`.
Do not silently repair the old source or call the augmented map a geometric Hodge
star. Distinguish a written argument, finite examples and a kernel-checked theorem.

[Motivating Hodge convention and counterexample](../../../_ic/nara/historical/oewas007/research/briefs/pfp_migration/hodge_companion_candidate/README.md).
