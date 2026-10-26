# Existing-work commit scope — 2026-10-02

This commit publishes the current Paper 011 research draft, bounded reconstruction
code, recovered original dependencies, and retained execution evidence. The full
user goal remains active. The PR stays draft because the complete source snapshot
and isolated standalone release verification are unfinished.

The feature branch was fast-forwarded to remote `main` at
`3bec3e2dd5659b53c33889d967fcd2b09689043c` before staging. Earlier execution
receipts retain their original source revisions and runtime identities. This
integration does not relabel those executions as runs against the refreshed base.

## Evidence representation

The corrected G03 archive and its manifest preserve 69 original files and
1,682,042,010 raw bytes. Large raw members are represented by
`history_recovery/g03/evidence.tar.gz`; compact readers and receipts also remain
directly accessible. Run the documented `genesis_g03_pack.py verify` and `unpack`
commands before attempting a raw-member replay. Raw files remain in the working
directory. Their absence as separate Git blobs is deliberate.

The independently checked initial package and exact preregistration/first-run
tool records are preserved separately in `history_recovery/g03_package_v1`.
That initial package retains its original ordering defect; use the corrected
package for replay. The chronology records bind the actual declaration before
the first engine launch. They are scoped execution records, not a complete
conversation transcript.

Python caches, Lake build directories, compiler objects, debug symbols and
temporary build logs are excluded. Retained native executables are explicit
evidence artifacts; their source and original build receipts remain included.
Their presence does not establish portable execution on another operating system.

## Remaining obligations

- Automatic approval review rejected the 8,057-file source copy because direct
  authorization could not be confirmed. The pending copy approval remains open;
  this commit does not perform that copy.
- The G03 archive is a lossless local evidence representation. A complete
  standalone dependency closure, fresh isolated rebuild and whole-release
  envelope mutation audit remain outstanding.
- Historical receipts reference pinned tools, libraries and paths outside this
  package. Existing scoped custody and certificate checks do not make those
  external dependencies available in a fresh clone.
- G01's retained Lake-manifest custody exclusion, historical missing task packets,
  unperformed model arms, and missing physical interpretations remain explicit.
- The full challenge corpus, every Genesis task, complete model studies and
  external publication/deposit are not completed by this commit.

Unrelated Paper 008 changes and the workspace's `.artifacts` directory are outside
the commit. No production Rust evaluator or provider configuration is modified.
