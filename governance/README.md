# Governance: the SCORING.md acceptance floor

AuthorityEffect: None. This folder states and enforces a process rule. It adds no result.

## The rule

Section 1.5 of [`SCORING.md`](../SCORING.md) accepts a source only with a
completed score at level L4 or L5 and composite grade D or better. Here every
governed source needs a companion `<stem>.contract.score.json` next to it that:

1. binds the source's path and the SHA-256 of its exact bytes, in both its
   contract and its score;
2. carries a completed score: all five gates graded, `composite_grade` equal to
   the weakest gate, `score_token` equal to level plus grade, and the reasoning
   for every gate in `basis`;
3. cites evidence by path and SHA-256, every file of which still exists with
   that hash; an evidence run record (`*.run.json`) must have hashed this
   source's current bytes, so stale evidence fails;
4. balances its mutation accounting, with
   R = killed / (killed + survived + inconclusive + unrun);
5. meets the floor of its category (below).

A pass shows that such a record exists and binds the bytes. Whether the grades
are deserved is for review, by reading the cited evidence.

## What is governed

[`policy.json`](policy.json) lists the populations: `pfp_lab/**/*.py`,
`governance/**/*.py` and `csharp/**/*.cs`, discovered with
`git ls-files --cached --others --exclude-standard`. Runtime sources must
reach L4D. Test sources are in the `test` support category (L2D or better,
still complete and byte-bound); Jeremy approved that category on 2026-10-26.

The imported trees (`pfp/`, `eis/`, `operads/`, `pciv/`, `ops/`, `papers/`,
`education/`, `code/`) are still listed as not yet governed. Jeremy approved
bringing them in; that happens once the rename of private names lands, by
adding them to the populations (Python, Rust and Lean 4) and recording a
[`baseline.json`](baseline.json) of their exact bytes with
`checker baseline --write --allow-add --reason ...`. A listed file is
grandfathered only while its bytes are unchanged. The screen of what scoring
them would find is in
[`docs/governance/imported_trees.md`](../docs/governance/imported_trees.md).

## Tools

| Command | What it does |
| --- | --- |
| `python -m governance.tools.checker check [--changed-since REF]` | Check every governed source (or only the changed ones); exit 1 on any failure |
| `python -m governance.tools.checker explain PATH` | Category, floor, hash, recorded score and problems for one file |
| `python -m governance.tools.checker record PATH --contract C --score S` | Make a contract and score current; the old ones move to history |
| `python -m governance.tools.checker baseline [--write] [--allow-add --reason TEXT]` | Recompute the grandfather list: keep entries that still fail with unchanged bytes, drop the rest; `--allow-add` (maintainer's call) adds the other failing sources |
| `python -m governance.tools.evidence NAME -- COMMAND ...` | Run a tool and keep `NAME.log` and `NAME.run.json` (command, versions, times, exit status, input hashes) |
| `python -m governance.tools.metrics OUT.json PATH ...` | Gate 5 metrics and ceilings: cyclomatic (lizard), cognitive (complexipy, Python), nesting (AST for Python, brace depth for C#) |
| `python -m governance.tools.mutation NAME --target FILE ... -- TESTS` | Six-outcome mutation campaign (AST for Python, lexical for C#) |

`governance/evidence/` holds the logs, run records, metrics and mutation
reports that the current scores cite.

## Scoring a changed file

1. Change the code and its tests; run the tests.
2. Re-run the evidence the score cites (tests, `mypy --strict`, Ruff, the
   import contracts, the mutation campaign for that file, metrics).
3. Assess the five gates against `SCORING.md`, write a contract and a score
   bound to the new bytes, and `record` them.
4. Run `checker check` before you commit.

## Relation to the sibling repository

This mirrors the companion-file rule of
`theory_of_finite_quantum_mechanics/governance/`, reimplemented as a small,
typed Python checker rather than copied, so that it could itself be held to
the floor. Its companion format is simpler (JSON with a history list) and is
not interchangeable with that repository's.

`SCORING.md` is the rubric Jeremy attached (SHA-256
`41f114724413adcc3c1dea465e027531a5665bbf65e748bc02f4005d2e90660f`) with one
line changed: the example schema's `$id` URL, so that no upstream product name
appears in this repository. No rule, grade or threshold differs.
