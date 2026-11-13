# PAPER 011 source-copy provenance

**AuthorityEffect:** None.

**Capture status:** pending explicit approval of the bulk copy operation. The
custody machinery exists; this document does not claim that a source snapshot
has already been deposited. Replace this status only after the capture and its
independent source/copy replay have completed.

The requested snapshot includes every tracked file under the PFP demonstration
root and every tracked findings document. The source preflight census contains
8,037 PFP files and 20 findings files. No challenge package, fixture, test,
specification, demo, or retained receipt is selected out for convenience.
Untracked local state is outside the snapshot; preflight found no untracked,
non-ignored authored files in the two source roots. Original sources and sealed
pins are never rewritten by the capture.

The completed read-only preflight at source Git head
`526ffd1748941f1781c0ff584b7033b29088b405` measured 34,406,038 PFP bytes
and 316,828 findings bytes, for 34,722,866 bytes across 8,057 tracked files.
This is a source census, not proof that the destination copies exist.

After capture, [source_copy_manifest.json](source_copy_manifest.json) is the
authoritative file census and provenance record. Each entry preserves:

- the original repository-relative source path and its matching package path;
- the source Git head, Git blob identifier, and tracked regular-file mode;
- the SHA256 of the actual source bytes at capture;
- a separate expected SHA256 for the current archived copy; and
- the exact byte count.

The original capture hash and the current copy hash are equal for an archival
copy. Both fields remain recorded; repairing an active recreation never permits
rewriting this archive. Original line endings, encodings, timestamps embedded
in files, nested manifests, and historical execution receipts remain unchanged.
Git blob identifiers identify the tracked baseline; raw SHA256 values identify
the actual captured working-tree bytes, including any checkout line endings.
Paths are sorted by their ordinal UTF-8 bytes.

Imported receipts remain historical observations bound to their original bytes
and dates. A copied successful receipt establishes no fresh execution result,
no model performance, no new mathematical proof, and no publication or execution
authority. PAPER 011's recreated demonstrations have separate fresh evidence.

The standalone [source custody checker](../code/source_custody.py) is reproduction
machinery. Once the snapshot has been captured, it can be invoked from the paper
root:

```text
py -3.12 code/source_custody.py --manifest-sha256 <externally-pinned-manifest-sha256>
```

The release checksum verifier supplies the manifest's enclosing custody. An
optional `--source-repo` argument independently compares the complete pinned Git
inventory and every currently available original file. This optional check is
for development provenance; the deposited copy check requires no monorepo
imports, Git history, provider, credentials, or native build.

The checker refuses malformed or replaced manifests, duplicate or escaping
paths, missing or extra archive files, changed bytes, source/copy remapping,
nonregular entries, symlinks and Windows reparse metadata, and fatal traversal
errors. It rechecks the copy bytes after its optional mutable Git subprocess.
Its [targeted corruption controls](../code/tests/test_paper011_source_custody.py)
operate on synthetic temporary files rather than modifying the imported archive.
