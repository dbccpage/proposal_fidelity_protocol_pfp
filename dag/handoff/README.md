# Continuation checkpoint — 10 November 2026

The user requested a stop to this session, publication of the work, and a long-horizon handoff to Claude and Gemini. This is an incomplete research checkpoint, not completion of the original every-file audit or evidence of general workflow superiority. No new paid campaign is authorized by this handoff itself.

Give Claude [CLAUDE_CONTINUATION_PROMPT.md](CLAUDE_CONTINUATION_PROMPT.md) and Gemini [GEMINI_CONTINUATION_PROMPT.md](GEMINI_CONTINUATION_PROMPT.md), with repository access. Both prompts require [CONTINUATION_BRIEF.md](CONTINUATION_BRIEF.md); that brief is controller/reviewer context and must never be forwarded to a benchmark solver. The prompts are prepared documents; neither external service was invoked to deliver them.

Start from the companion checkpoint branch, `codex/pfp-research-handoff-20261110`. It includes the benchmark branch as its ancestor. [PR #58](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/pull/58) isolates the executable benchmark. The companion PR targets that branch, so review/merge #58 first and then retarget the companion to main. See `publication.json` for final publication pointers and verification.

Current evidence: 12 runnable benchmark plans, 24 frozen and independently graded attempts, 23 attempts with paid dispatch, one zero-dispatch infrastructure refusal, USD 0.055614 settled provider charges, zero held liability, and no fully correct solution. Best observed score is 88/100 for one self-critique run, versus 83/100 for one direct run of the same model, with greater money, tokens and time. These are exploratory observations, not a demonstrated PFP/EIS/PCIV/OPERADS advantage.

The original census has 32,261 files: 9,576 full-reading receipts, 33 partial and 22,652 pending. A reading receipt is not proof of correctness. The 4,250 composition designs are not runnable workflows. All 38 primary manuscripts have an assessment; their supporting material is not fully audited. See `../WORK_PRIORITY.md`, `../FOUNDATIONS.md`, `../reviews/coverage.json`, and the brief for precise limitations.

The latest executable benchmark was checked in an isolated committed export: 249 tests plus 48 subtests passed, with an offline Windows/MSVC build of the isolated Rust wrapper. A subsequent pure wire normalizer has 12 passing tests plus 20 subtests; it is not integrated into a plan. No full monorepo test run or general theorem certification is claimed.

## Preserved material and working-tree hygiene

`publication_exclusions.json` inventories generated review PNGs and disposable test directories excluded from loose Git publication. Every listed file remains at its original local path, unchanged. Non-image scratch files are also available in `preserved_test_scratch.zip`, with original repository-relative member names and checked SHA-256 values. Rendered paper pages remain local; original source documents and substantive review reports are retained in the repository. This is an explicit publication boundary, not deletion or additional source-review credit.

Historical recovery archives for the checkout, retired pilots and moved originals remain at the locations already recorded in `../migrations/`. Those external archives are not silently replaced by this checkpoint. Follow their manifests before attempting recovery. Ignored migrated cache extras are additionally preserved in `../migrations/migrated_local_extras.zip`, with hashes in `migration_ignored_destinations.json`; none were originally Git-tracked in the source pilot census. Original secrets and the private answer key are not part of this publication.

Frozen paid run directories contain evaluator analyses as well as solver requests and responses. A controller may inspect them to design new experiments, but a solver must receive only its allowlisted request payload. Treat further experiments on this known seed as exploratory and use newly sealed holdouts before making generalization claims.
