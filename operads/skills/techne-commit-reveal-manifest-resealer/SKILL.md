---
name: techne-commit-reveal-manifest-resealer
description: "Simulate commit-reveal cycles on test and judge manifests, recompute Merkle digests, and emit lossless diffs."
operad_source_colours:
  - State
  - Paper
operad_target_colour: Receipt
operad_arity: 2
operad_residual: diagnostic
families:
  - techne
  - packaging
  - verification
  - git
---

# Techne Commit-Reveal Manifest Resealer

**AuthorityEffect:** None.  
**Council:** `L3_logos_techne`  
**Status:** Active.

## Mission & Governance Invariants

The **Commit-Reveal Manifest Resealer** audits, verifies, and reseals cryptographic commitments across benchmark manifests, test case catalogs, and deposit packages. It prevents silent test vector drift, uncommitted benchmark changes, and hash desynchronization.

In accordance with cryptographic custody and deposit manifest standards:

1. **Deterministic Byte Commitment:** Case files and test vectors are hashed using pure SHA-256 over raw file bytes. Hashes must be computed without platform-dependent line-ending conversions or trailing whitespace modifications.
2. **Strict Ordinal Sorting:** Manifest entries, file lists, and case arrays must be ordered in strict ordinal UTF-8 byte order (`key=lambda s: s.encode('utf-8')`).
3. **Lossless Synchronization:** Resealing operations must recompute digests and output RFC 8785 canonical JSON diffs. The resealer must never truncate existing metadata, erase historical attribution, or alter test cases during a manifest update.

---

## Commit-Reveal Protocol Lifecycle

```text
[Phase 1: Commit Phase]
  Raw Case Files (*.json, *.txt, *.md)
        │
        ▼ (Compute SHA-256 in ordinal UTF-8 order)
  Manifest Commitment (manifest.json / MANIFEST.sha256)
        │
        ▼ (Cryptographic root hash / tape commitment)
  Root Digest Sealed (AuthorityEffect: None)

[Phase 2: Reveal & Verification Phase]
  Host Test Execution / Judge Ingestion
        │
        ▼ (Re-hash on-disk cases)
  Actual On-Disk Hashes == Manifest Hashes?
       ├── PASS: Proceed with verified evaluation
       └── FAIL: Emit ManifestDesyncDefect with exact diff
```

---

## Targeted Manifest Resealing Rules

| Rule ID | Surface | Invariant Checked | Remediation |
|---|---|---|---|
| `CRM-MAN-001` | Manifest Digest Parity | Every on-disk file matches recorded SHA-256 | Recompute hash and reseal manifest if authorized. |
| `CRM-MAN-002` | Unrecorded File Leak | Directory contains files absent from manifest | Add unrecorded files to manifest or move to excluded dirs. |
| `CRM-MAN-003` | Ordinal Path Sorting | Keys sorted by UTF-8 byte sequence | Sort path keys via `sorted(paths, key=lambda p: p.encode('utf-8'))`. |
| `CRM-MAN-004` | UTF-8 Cleanliness | Manifest encoded in UTF-8 without BOM | Strip BOM (`\xef\xbb\xbf`) and normalize line endings. |

---

## Operational Workflow

### 1. Verification Sweep

Verify manifest integrity against on-disk files without modifying state:

```console
# Check manifest against on-disk files
py -3.12 -c "
import hashlib, json
from pathlib import Path

manifest_path = Path('manifest.json')
if manifest_path.exists():
    data = json.loads(manifest_path.read_text(encoding='utf-8'))
    for entry in data.get('cases', []):
        p = Path(entry['file'])
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        assert h == entry['sha256'], f'Hash mismatch on {p}'
    print('Manifest verified: all hashes match.')
"
```

### 2. Resealing Manifest

When case files have been legitimately updated:
1. Stage changes to test case files.
2. Recompute cryptographic digests in ordinal byte order.
3. Emit updated `manifest.json` with new timestamp and root hash.
4. Verify diff with `git diff manifest.json`.
