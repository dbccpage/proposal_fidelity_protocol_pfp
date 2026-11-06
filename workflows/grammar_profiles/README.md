# Grammar Profiles

Recognizes a submitted packet under one named syntax profile without trimming, repairing or reinterpreting its bytes, and keeps syntax acceptance separate from meaning.

Offline and deterministic: no model calls, no network. Ported from an internal test suite.

## Run

From the repository root:

```
python -m pytest workflows/grammar_profiles/tests -q -p no:cacheprovider
python workflows/grammar_profiles/run.py --output-dir <scratch-dir>
```

Without `--output-dir`, results go to `workflows/pilot_output/pilot_0000028/`.

See the wiki page `Test-Grammar-Profiles`.
