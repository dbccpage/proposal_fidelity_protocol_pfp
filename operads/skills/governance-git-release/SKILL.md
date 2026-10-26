---
name: governance-git-release
description: "Consolidated Git staging safety, changeset shape, CAS atomic storage, and standalone release archive isolation gate."
operad_source_colours: ["State", "Receipt"]
operad_target_colour: "Receipt"
operad_arity: 2
operad_residual: "unknown"
families: [governance, git-release]
---

# governance-git-release

AuthorityEffect: None.

## The single rule

> Git staging must always name files explicitly without wildcards, release packages must be fully self-contained with verified SHA-256 digests, and destructive mutations must preserve pre-deletion snapshots.

## Consolidated Invariants

1. **Explicit Staging Safety**: Wildcard staging (`git add .`, `git add -A`) and untracked artifact inclusion (`target/**`) are strictly forbidden (`goo-git-explicit-staging-safety-gate`).
2. **Changeset Shape Preflight**: Commits must maintain clean branch shape and avoid unmerged prerequisite PR stacking (`goo-changeset-shape-preflight`).
3. **Standalone Release Archive Isolation**: Distribution ZIP archives must be self-contained upon extraction, matching SHA-256 manifests, passing tests without monorepo ambient dependencies (`goo-standalone-release-archive-isolation-gate`).
4. **Content Hash Honesty & CAS Integrity**: Council artifacts must carry real SHA-256 body digests (no 64-zero placeholders), and storage writes must use atomic staging (`.tmp` + rename) (`goo-sha256-content-hash-honesty-gate`, `goo-cas-atomic-writes-integrity-gate`).
5. **Pre-Deletion Preservation**: Deletion of research packages mandates automated ZIP snapshotting and SHA-256 manifest recording (`goo-research-pre-deletion-blob-preservation-gate`, `goo-source-disposition-sha256-witness-gate`).

## Verification Requirements

Run the release and staging checker:

```bash
python omega_engine_operads/skills/governance-git-release/scripts/check_git_release.py
```
