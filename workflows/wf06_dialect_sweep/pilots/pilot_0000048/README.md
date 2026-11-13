# pilot_0000048: reversible glyph codec

Each byte becomes two symbols from a declared sixteen-symbol alphabet. A
permutation changes the body and its key together. The checker verifies exact
payload recovery and an integer polynomial answer; a changed task or payload is
rejected even when its answer matches.

The default 99-byte payload becomes a 1,302-byte packet, including the alphabet,
key, legend and framing. It preserves the answer but does not compress bytes.
Tokens are not measured. There are no model calls and no model-performance claim.

## Status

Copied from the imported pilot estate (old bytes are in git history at commit
`90228464`). Offline tests only. The schema files were renamed to lowercase;
no code opens them by name.

## Run

From the repository root:

```powershell
python -m pytest workflows/wf06_dialect_sweep/pilots/pilot_0000048 -q -p no:cacheprovider
```

From this folder, `python -B run.py` runs the default job and writes input,
output and receipt under `../pilot_output/pilot_0000048/` unless
`--output-root` names another folder. `run.py --input examples/job.json` takes
a JSON job; add `--format yaml` for YAML. `python -B check.py` runs the focused
tests, coverage and compiled mutations in a temporary folder (needs `coverage`).
Unknown fields, invalid keys, corrupt payloads and wrong protected answers are
refused. Hashes bind bytes; they are not authentication or authority.
