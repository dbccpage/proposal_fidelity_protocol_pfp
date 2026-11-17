# Historical PR Immunity Campaign Contract v1

**Status:** proposed shared contract
**AuthorityEffect:** None
**ExecutionAuthority:** None

This contract governs retrospective mining of pull requests, review discourse,
prompt/response records, and conversation DAGs. It produces replayable findings
and proposed skill or anti-skill morphisms. It cannot admit a skill, declare a
claim true, comment on a pull request, change code, or merge anything.

## 1. Purpose

The useful unit is not a pull request outcome and not an isolated bad answer. It
is a provenance-bound transition:

```text
prompt or claim -> response or change -> objection or failed check
                -> repair, refusal, revert, supersession, or unresolved residue
```

A wrong answer or consistent hallucination can be an excellent immune-system
specimen because it exposes a repeatable bad transformation. Repetition,
confidence, model agreement, review approval, and merge state are observations;
none of them certify truth.

## 2. Frozen corpus boundary

The frozen census uses `inventory_cutoff_at = 2026-08-13T23:28:14.710048Z`
and covers two GitHub repositories at that cutoff:

| Repository | Pull requests | Merged | Closed unmerged | Frozen main at census |
| --- | ---: | ---: | ---: | --- |
| `dbccpage/sentinel` | 2,053 | 2,014 | 39 | `0d67ec76fd45d2b0968d039ea28997172b737200` |
| `dbccpage/sentinelpy` | 62 | 62 | 0 | `6cb2af5607a7c7b3bf5aae523d018159cd3faf44` |

The exact frozen workload is 2,115 PR records. PRs created after this census,
including `sentinelpy` PR #63, are outside this v1 corpus unless a new manifest
is issued. The old PR number range has gaps, so a
campaign inventories returned PR identities rather than manufacturing a
contiguous number sequence.

Every historical PR head currently has a GitHub pull-ref. Those refs are not a
permanent archive. Before large-scale analysis, mirror the exact refs into an
explicit archival namespace or bundle and bind its digest. Do not treat
unreachable objects retained by a developer clone as durable custody.

The OE v0.0 corpus is a quarantined source, not authority. At the current
checkpoint it contains 4,565 files under the immutable Git object locator
`7ca9e2293792a4769404b3edaaaabe12a9fefa01:_ooutwire/epistemic_immunity`,
including 1,026 `_intelligence`
files, 3,526 `legacy_oe` files, and 13 textbooks. Inventory it by
Git blob identity and import bounded specimens. Never apply the stash or load
the archive wholesale merely to run this campaign. The object ID is not durable
custody by itself; archive it under an explicit ref or bundle before stash
cleanup or garbage collection.

The public OE v0.0 archive is a second, independently identified custody
source: [`dbccpage/archive`](https://github.com/dbccpage/archive/tree/1c98ea7b9bb1fd76a987dd29753973699e055cb5/v0.0.0).
At the frozen checkpoint, repository commit
`1c98ea7b9bb1fd76a987dd29753973699e055cb5` has commit-tree
`6c9b16530bb911a17e72f64cfafd1d54f672b129`; its
`v0.0.0` subtree is
`bc5567973b8e13d2bbda7789543035f8c03d12dc` and contains 3,555 blobs and
1,029 subtrees. The `.intelligence` subtree is
`cb542747052bb0494aed3f41f78bf7623f03acec`, with 476 blobs, including 28
conversation exports. One bounded conversation specimen,
`.intelligence/.conversations/2026-02-22_23-52_integration-audit-autopoiesis.md`,
is Git blob `944a197c39213d759e01ddeb3a366bc5a7632e45` (8,193 bytes). The prompt
genealogy is Git blob `9e5b45d5f28f92c9059505b90ae9e82aafe0e0f2` (62,195 bytes).

The public archive and the stash are separate snapshots even where content is
byte-identical. For example, the archived `morphism_pairs.jsonl` is Git blob
`66b36c2535e9567c82a2e0412048b52c129dcee2` in both observed lineages. Such
copies share one lineage cluster and never count as independent recurrence.
The archive's percentages, entropy, purity, recurrence, coherence, and other
scalar diagnostics remain observations. Implausible values are useful negative
controls; they are not correctness evidence or admission authority.

The v0.0 implementation already contains three important design witnesses:

| v0.0 witness | Frozen Git blob | v1 interpretation |
| --- | --- | --- |
| `core_core/src/prompt/immune.rs` | `87deb8d668e016079197aeafd482e81961b9ae2a` | A history of failure maps a problem into a forbidden reasoning region. Preserve this as a proposed anti-morphism, but count independent correction contexts rather than raw repetitions. |
| `core_core/src/prompt/trace.rs` | `08a663dfb31c63325dc5ae5f800888ef2992f72e` | The epistemic trace is the missing join table. Reconstruct it from exact prompt, response, review, check, repair, and disposition identities rather than a free-form narrative. |
| `core_core/src/prompt/hamiltonian_antibody.rs` | `2a26626a7f0e71229c091ab201c257d0e180c8a9` | Geometric failure modes may propose targeted constraints. The proposal remains inert until negative controls, independent replay, and human admission bind it. |

This campaign therefore repairs v0.0 by strengthening custody, independence,
counterexamples, and promotion separation; it does not discard the original
anti-morphism or trace insight.

## 3. Identity and custody

Use separate identities for custody and computation:

```text
custody_key  = (repository_node_id, pr_number)
snapshot_key = (repository_node_id, base_oid, head_oid, merge_oid_or_none)
compute_key  = (snapshot_key, detector_digest, policy_digest)
```

Base-sensitive PR analysis never shares computation by head OID alone. Only an
explicitly declared head-tree-intrinsic analyzer may use a separate head-only
cache key. Two PRs sharing a head commit still keep distinct comments, reviews,
checks, timelines, dispositions, and custody receipts.

Every remote page and historical artifact is stored as exact bytes in a
content-addressed store. Its receipt binds:

- repository and PR node identities;
- canonical request metadata with credentials removed;
- retrieval cutoff, endpoint, page/cursor, ETag, and selected response headers;
- raw-byte digest and ordered page-chain parents;
- base, head, and merge commit identities when present;
- implementation, detector, policy, and negative-control digests;
- typed residuals for unavailable or incomplete evidence;
- `AuthorityEffect: None`.

Missing pages, partial GraphQL errors, truncated patches, deleted forks, rate
limits, and unavailable artifacts are `DEFERRED` or `REFUSED` evidence. They are
never silently normalized to empty data or success.

## 4. Conversation graph

Canonical graph nodes are observations with exact source spans or JSON
pointers. At minimum the graph distinguishes:

- prompt, claim, response, proposed change, commit, and PR snapshot;
- review objection, issue comment, failed or passing check, and human decision;
- repair, refusal, revert, supersession, merge, closure, and open residue;
- archived OE trace, compost, antibody, and morphism records.

Canonical causal edges are typed. Core edges are `RESPONDS_TO`, `REVIEWS`,
`CORRECTS`, `REPAIRS`, `REFUSES`, `REVERTS`, `SUPERSEDES`, `MERGES`, `CLOSES`,
`SAME_LINEAGE`, and `CORRESPONDS_TO`.

Timestamps order observations but do not prove causality. A causal edge requires
an explicit reference, common bound artifact, patch relationship, check target,
or independently reviewed correspondence. Shuffling timestamps must destroy a
candidate that depends only on temporal order.

## 5. Skill and anti-skill morphisms

A skill morphism is a proposed repeatable transformation that preserves named
invariants across independently bound contexts.

An anti-skill morphism is a proposed repeatable bad transformation with:

- a bound domain and codomain;
- an earlier claim, answer, change, or action;
- a later bound correction, repair, refusal, revert, or supersession;
- the failed invariant and protected fields;
- witnesses, counterexamples, blind spots, and a proposed detector;
- an independence key and lineage cluster;
- status `PROPOSED` and `AuthorityEffect: None`.

Legacy verdicts, entropy, purity, recurrence scores, antibody counts, and free
text such as `PASS` or `promote me` are diagnostic inputs only. They cannot
construct an admitted anti-skill.

An unresolved obstruction remains an `OPEN` local finding until a separately
typed obstruction-to-candidate bridge exists; the v1 anti-morphism candidate
does not treat open residue as a corrective edge.

## 6. Independence law

Recurrence is counted over independent contexts, not rows. The following collapse
to one lineage cluster unless independently rebound:

- duplicate source bytes or copied conversation exports;
- repeated comments in one PR;
- one actor or evaluator repeating a template;
- bot-generated updates;
- cherry-picks, backports, copied patches, and duplicate PR heads;
- mirrored OE v0.0 archive layers.

Cross-context nomination requires at least three independent clusters. A single
bound correction may still yield a useful local finding, but not a generalized
anti-skill candidate.

## 7. Symmetry law

Symmetry comparison requires a correspondence map declared before detection.
Names, paths, PR numbers, or similar prose do not establish correspondence.

The detector may emit the existing classes `MISSING_PROPAGATION`,
`DANGEROUS_DRIFT`, `DUPLICATE_RULE`, `CONTRADICTION`, `AUTHORITY_COLLISION`, or
`UNLICENSED_EXTENSION`. It must preserve `INTENTIONAL_VARIANCE` and documented
counterexamples. Independently mismatching repository labels or correspondence
endpoints while observations remain fixed must destroy a result that depends on
that map. A consistent global renaming of repositories, observations, and the
correspondence map must preserve the result.

## 8. Resumable campaign

Campaign state lives under `runs/pr_audit/<campaign_id>/`:

```text
campaign.json
objects/sha256/<digest>.bin
inventory.json
queue.jsonl
receipts/<stage>/<item_digest>.json
findings/<detector>/<finding_digest>.json
controls/<detector_digest>.json
decisions/
summary/
```

Files are exclusive-create and content-addressed. Completion is derived from
verified per-item receipts; a checkpoint or summary is disposable cache.

Stages are finite:

1. `FREEZE` repositories, cutoff, endpoint set, correspondence maps, detectors,
   controls, and authority ceiling.
2. `INVENTORY` every PR identity through a complete page chain.
3. `CAPTURE` metadata, commits, reviews, comments, threads, timeline, checks,
   and file/diff custody.
4. `NORMALIZE` exact observations and typed graph edges offline.
5. `MINE` proposed skill, anti-skill, and symmetry candidates.
6. `REFUTE` by replaying evidence and the mandatory control bank.
7. `VERIFY` selected cases against exact local Git objects and a bound current
   evaluator, labelled `CURRENT_POLICY_REPLAY`.
8. `EXPORT` candidate bundles and reproducible summaries for human review.

There is no autonomous `PROMOTE`, `ADMIT`, `COMMENT`, `PATCH`, or `MERGE` stage.

### Implementation checkpoint (2026-08-13)

The first reviewed kernel implements strict authority-null contracts, an
exclusive-create content-addressed store, an injected credential-null GitHub
REST source for PR inventory/detail/files, and pure anti-morphism/symmetry
candidate detectors with content-bound policy/correspondence declarations and
declared negative-control identities. `MINE` does not prove those controls ran;
that proof belongs to later `REFUTE`/`VERIFY` receipts and stage-transition
policy. This is campaign machinery, not a completed historical audit.

The kernel has not yet captured the 2,115-PR corpus, archived the pull refs,
captured reviews/comments/timelines/checks, reconstructed mega-PR object diffs,
normalized the OE conversation DAG, or produced a human-reviewed candidate
bundle. Those remain resumable campaign stages. No current finding or skill is
admitted by landing the kernel.

## 9. Scaling plan

Use repository plus PR-number ranges of 50 with explicit manifests: 42 shards
for `sentinel` and 2 for `sentinelpy`. Start with the contrastive pilot:

1. the 39 closed-unmerged PRs;
2. the 15 duplicate-head pairs in the old repository;
3. known repair/revert sequences and current reviewed PRs;
4. the remaining ordinary PRs;
5. mega-PRs on a separate object-diff rail.

GitHub's PR-files endpoint cannot be custodial for mega-PRs. It stops at 3,000
files, while `sentinel` PR #1911 declares 9,008 changed files at the frozen
cutoff. Anything above 1,000 files enters the mega-PR rail; anything above 3,000
requires exact Git object diff reconstruction.

## 10. Mandatory controls

Every detector must pass all applicable controls:

1. shuffled timestamps destroy unsupported temporal claims;
2. mismatched labels/endpoints destroy cross-repo symmetry, while consistent
   global renaming preserves it;
3. same-name/path homonyms remain negative;
4. duplicating one source any number of times never crosses independence;
5. bot/template/cherry-pick repetitions count once;
6. intentional variation or a named counterexample blocks generalization;
7. an injected later correction/revert is detected as a known positive;
8. an all-positive detector fails the bank;
9. future-main information is withheld to prevent lookahead;
10. missing or partial custody yields a residual, not success;
11. candidate artifacts remain immutable `PROPOSED` forever; any future
    admission is a separate external decision/spec binding candidate,
    evidence-root, detector, policy, and control digests.

## 11. Admission and effects

Autoskill may capture an episode and route a candidate. Symmetry Hunter may
classify drift. Prompt Civilization may segment bounded dialogue and emit inert
candidates. None may self-evaluate or admit its own result.

Only a later, separately authenticated human admission process may create a
distinct admission decision and admitted spec that bind a candidate. It never
mutates or promotes the candidate artifact itself. The present Prompt
Civilization registry correctly refuses every non-empty admitted registry while
that validator is unavailable. This campaign must preserve that fail-closed
boundary.
