---
pattern_id: HP_PY_007
name: rebuild_and_hash_pin
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_PY_007_committed_rebuildable_artifact
language: python
authority_effect: None
---

# Healthy Pattern: Rebuild And Hash-Pin (`HP_PY_007`)

## Description

Ship the generator and a hash manifest. Write the archive to a caller-chosen path or a CI artifact store. A test runs the generator and opens the bytes it just wrote.

## Structural Signature

```python
def rebuild(out_dir: Path) -> Path:
    archive = out_dir / "deposit.zip"
    archive.write_bytes(build_archive())
    (out_dir / "MANIFEST.sha256").write_text(sha256(archive), encoding="utf-8")
    return archive
```

The repository tracks `rebuild_release.py` and the manifest of source inputs. It does not track the zip.

## Remediation Applied

- Drop the committed zip or coverage database from the index.
- Point the manifest at the generator output.
- Add a test that rebuilds into a temporary directory and reads that file.
