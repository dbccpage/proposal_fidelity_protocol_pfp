# Publication review: Paper 008, initial v0.1 preprint

Review date: 2026-10-02. Repository baseline:
`23893fc44162555fa12ceda3e1665982e3d7a14e`.
Candidate: version 0.1.0. No external deposit or DOI was made.

The revised paper is suitable for author review as a bounded methods and
evidence-audit preprint. Its contribution is a worked distinction between a
syntactic round trip, finite checked examples, and semantic or experimental
claims. Its statements do not establish a general tower, a new universal
graph theorem, an unassisted model effect, or an educational outcome.

## Findings and repairs

| Finding | Before | Revised behavior or wording |
| --- | --- | --- |
| Verdict parsing | A reply such as `VERDICT: INCONSISTENT` could match the substring CONSISTENT | Exact labels only; malformed and conflicting labels are UNKNOWN |
| Receipt custody | Different raw replies yielding the same verdict could share the minimal digest | Version-2 digest binds every recorded execution field except the digest itself, including graph, prompt, raw reply and declared runner source |
| Repeated proposals | Separate short runs could pool into a claimed consecutive loop | Counts the longest consecutive repeat run; the single-shot runner and historical K4 rule remain distinct |
| Optional Lean gate | Exit 0 with an empty or incomplete census could pass | Requires the complete expected names and axiom sets; rejects empty, missing, duplicate, extra, changed-dependency and stale-generated-census cases |
| JSON witnesses and labels | A valid tuple walk failed after JSON reload; an inconsistent fixture label could be used for scoring | JSON list steps are checked with strict integer indices/orientations; fixture labels are checked against the host before a proposer call |
| Historical census | C047 was described as having no test-named file and as checking hidden cases and mutations | Its one test-named script prints case scores without assertions or failing exit status and does not check mutations; filename counts do not imply pytest collection or execution |
| Evidence location | Relative historical paths and working-tree identity wording implied the old layout remained current | Full historical revisions are stated; parser/maps, reports and all eight K4 traces are archived with exact byte identities |
| Formal scope | Recent broad local census coverage was omitted; fresh and retained executions were mixed | Distinguishes 39 selected theorems, 576 local environment declarations and 52 external payloads; reports the review-host Lean startup failure |
| Model interpretation | Aggregate labels and working-report phrasing could be read as independent observations | Keeps C005 runs apart, computes exact descriptive p-values, states protocol deviations and missing paired rows; labels K4 prompts as answer-bearing assistance and terminal outcomes as historical replay |
| Live budget | Nominal ceiling wording suggested an actual charge guarantee | States that the implementation uses a fixed next-call estimate and reported costs |
| Study companion | Brief recall questions lacked worked calculations and source exercises | Sixteen questions, eight rungs, worked answers, changed-input checks and a 32-point self-study rubric |

The strict parser is an intentional scoring-contract change: prose containing
a verdict word is insufficient unless the whole reply is a valid bare label
or it contains a valid explicit verdict line. New execution receipts use
schema `pfp008.graph-consistency-receipt.v2`; older receipts remain historical.
A public digest is a custody comparison, not a provider signature.

## Mathematical and statistical review

- The actual archived upward/downward maps prove the singleton old-image
  round trip by their branches. A left inverse implies injectivity; semantic
  conservativity still needs a language, theory and preservation statement.
- The flow fixture has primal and dual objective 1 and zero gap while
  divergence is (−1, 1, 0). The balance condition cannot be omitted.
- Eight-wide integer opcode ranges are disjoint. An unsigned eight-bit
  encoding accommodates complete blocks only through stage 37; the loaded
  stage-100 block is 752–759.
- The four transcribed McNemar discordant-count pairs give exact two-sided
  values 145499/4194304, 1/32, 1/2048 and 2^−33. Arm 2 is 36/50 in one run and
  38/50 in the other; 37/50 was never an observed run. The arithmetic does
  not recover missing per-case rows or justify a general or
  multiplicity-adjusted effect.
- The historical tree inventory confirms 40 solver/two-checker packages,
  two specifications calling for model measurements, and eight other
  specifications within C001–C050. Checker independence is package-declared;
  folder membership and score-printing are not correctness receipts.
- All eight retained K4 trace SHA-256 values match the working report.
  Inspection confirms answer-bearing assisted prompts. The last raw rows
  lack post-move host results, so historical terminal defect values are not
  described as a fresh replay.
- All 13 protected local Lean source identities match the October 2 author
  receipt, as do the full census source, report and replay tool. The full
  report lists 576 declarations from ten local modules, including generated
  and private names. The separate named report lists 39 selected theorems;
  only stage_capacity_monotonic among those also uses Classical.choice.

Primary references were checked against the official Lean axioms chapter,
Git's object-reading documentation and Leroy's original arXiv/journal record.
No broader claim is inferred from their titles.

## Fresh validation

The [execution receipt](review_validation_2026_10_02.json) records commands,
outputs, revised source identities and scope. The three test files were run
separately: **34 + 7 + 11 = 52 passed**, no skips or failures in the final
runs. Ruff passes; mypy reports no issues in five code files. The canonical
named census source check passes.

Source-example checks import the actual archived initial grammar and maps
in an isolated namespace, recompute the flow and statistical examples, and
compare all 125 triangle edge assignments from −2 to 2 against an independent
bounded potential search. This bounded search is complete for that fixture
domain and is not a general algorithm proof.

Four offline CLI conditions give the expected 3/6, 6/6, 3/6 and 6/6 matches.
All 24 JSON-loaded receipts have valid complete digests, exact prompts and
checked host certificates. Exit 1 for baseline and scratchpad is the expected
negative control. No provider call was made.

The official Linux Lean 4.34.0 release archive was checked against its
published SHA-256
`caaa98356098c85dc0fcbbd28e1ec66f39eb6551829972b752ff20e1286b646b`.
The binary fails before startup with "failed to locate application";
the named replay fails at Lake installation configuration. This is a
**blocked fresh kernel replay**. The unchanged retained author-source
bindings above remain separate evidence. Mocked gate tests establish no
kernel elaboration, and the 52 external payloads were not rebuilt.

The revised standalone and collection PDFs are rebuilt using the existing
series renderer with three XeLaTeX passes and no overfull-line warnings.
Literal approximation signs in the original p-value table were missing in
this font; the exact values now use TeX math and the rounded approximations
have their own labeled column. The series renderer keeps current package
evidence links beside the canonical package, including files added after the
historical baseline. Its eight existing custody tests also pass.
Rendered pages are inspected for clipping, tables, mathematics and readable
headings. The collection's 008 mirrors and hashes are refreshed while other
publication entries retain their identities. The deposit manifests and
deterministic ZIP are rebuilt and checked separately.

## Publication and teaching limits

This package preserves the internal 1.2.0 history while designating the first
Zenodo preprint as 0.1.0. Retained reports remain verbatim working evidence;
archiving them does not adopt their withdrawn interpretations. New review
receipts replace older runner, teaching and PDF bindings only for the revised
candidate, without altering historical receipts.

The Landau-style rubric supports self-study. No learner data, calibrated
grading claim or equivalence to an MSS stage is reported. A future empirical
comparison needs unassisted prompts, repeated seeds, declared outcomes and
retained per-case data. An independent fresh Lean replay needs a host on which
the pinned toolchain starts.

Text and new documentation use the package's CC BY 4.0 terms. Source code,
Lean and archived repository evidence retain their existing rights; no
source is relicensed by this review.
