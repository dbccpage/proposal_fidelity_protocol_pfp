# Release-Envelope Custody & PR Scope

**AuthorityEffect:** None

Detailed specifications for release-envelope custody pre-push gates and PR scope attribution.

## Release-Envelope Custody Pre-Push Gate

Apply this conditional gate before a push when the candidate touches checksum manifests, release archives, reproducibility receipts, generated-verification subprocesses, or their verifier/build code:

- Mutation-test the boundary after initial verification: replace each control file with a same-byte symlink, reparse point, or non-regular entry and require refusal. After every test, notebook, compiler, or other mutable subprocess, re-enumerate and re-hash the tree and controls; compare them with the initial verified snapshot before accepting an archive.
- Directory traversal errors are fatal. Exercise the traversal error callback and reject unreadable retained directories. Keep build/cache exclusions root-relative where practical so a generic basename such as `build`, `b`, or `p` cannot silently exempt unrelated payload.
- Bind the complete archive envelope, not only parsed members. Reject prepended/appended bytes, duplicate or case-colliding paths, symlinks, noncanonical compression/metadata, and inventory/order/byte drift; a deterministic rebuild must be byte-identical.
- On Windows, rerun Lean or other path-sensitive evidence from a short temporary path when the checkout path exceeds tool limits. If fresh evidence, manifests, or archives cannot be regenerated, keep the PR draft and describe the exact blocker; never present the candidate as complete or green.

## PR-Authored and Merge-Result Scope

- Define PR-authored paths from GitHub's PR-files response bound to the exact base and head SHAs, or from the merge-base three-dot delta (`git diff --name-status <base>...<head>`). Never attribute paths using a two-dot comparison from current main to a stale head; that endpoint-tree delta is reserved for prospective merge-result analysis.
- For a stacked PR, record both the declared-base PR delta and the stack-only semantic delta against the pinned parent head. After integrating current main, recompute the final three-dot semantic delta and inspect the merge commit's combined diff (`git show --cc`) separately for resolution-only changes. Do not collapse authored, inherited, and merge-resolution paths into one claim.
