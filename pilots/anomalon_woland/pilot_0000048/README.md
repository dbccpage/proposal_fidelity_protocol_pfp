# Pilot 000023: reversible glyph packets

New experiment 2/100. Can a declared glyph rewrite preserve exact task bytes
and a protected answer, and what does the complete packet cost?

Each byte becomes two symbols from a declared sixteen-symbol alphabet. A
permutation changes the body and its key together. The checker verifies exact
payload recovery and an integer polynomial answer. Equal answers alone are
insufficient: a changed task or payload is rejected even when its answer matches.

The default 99-byte payload becomes a 1,302-byte packet, including the alphabet,
key, legend and framing. It preserves the answer 17 but does not compress bytes.
Tokens are not measured. There are no model calls and no model-performance claim.
This local codec does not implement MSS, glyph-graph-v1 or a new external standard.

## Run

From this folder, with Python 3.12, Pydantic, PyYAML, pytest and coverage installed:

```powershell
py -3.12 -B run.py
py -3.12 -B check.py
```

`run.py --input examples/job.json` also accepts a JSON job; add `--format yaml`
for YAML. Strict models, schemas and example twins are included. Unknown fields,
invalid keys, corrupt payloads and wrong protected answers are refused. Hashes
bind bytes; they are not authentication or authority.

The focused check expects 77 tests, including CLI integration and 15 compiled
mutations, and requires at least 98% coverage of the complete `run.py` module.
A failed gate prints `{"status":"FAILED","reason":...}` and exits 1. Commands,
test/coverage reports, mutation results and a typed JSON/YAML summary go to a
temporary directory removed afterwards, or to a new directory named by `--out`;
the check writes nothing to `../pilot_output/`. Temporary test fixtures are scratch,
not a second publication package. The check script itself is not in that coverage
claim. Default `run.py` executions write their input, output and receipt under
`../pilot_output/pilot_0000048/`.

## Review

The existing deep-research run `PFP_20261007_NEW002_GLYPH_PACKET_01` finished
`Verified`, with no outstanding scoped critic objection. Its controller did not
perform semantic verification; executable tests supply that evidence. Original
candidate and review history remain under
`_intelligence/research/briefs/pfp_expansion/pilot23_glyph_packet/`, and host
records under the main checkout's `_intelligence/research/runs/`.
The sole production change at installation is the default output directory.
