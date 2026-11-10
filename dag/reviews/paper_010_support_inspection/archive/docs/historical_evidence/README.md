# Retained historical evidence

These are byte copies of ten C045–C050 pilot reports, four C017 reports, and the
earlier formal-checker baseline record. `provenance.json` pins every source path,
commit, Git blob SHA and SHA-256. The copied reports keep their original content,
including any missing provider information, raw unfinished responses and author
annotations. Their historical dates are unchanged.

From the package root, run `python code/recount_pilots.py`. It checks these bytes,
compares all 25 extracted C017 entries with their source records, recounts Table 3
from per-case acceptance flags, and checks the partitions and counts behind Table 4.
The C017 certificates themselves are freshly checked by `code/replay_c017.py`.

Table 3 recount is an audit of recorded checker decisions. Table 4 uses the author's
identifier categories and a retained prior execution record; it neither independently
classifies leakage nor executes the historical C045–C050 checkers. Those checker
executions require the repository commits and collection-level script cited in
Section 4.4. No script here calls a provider or generates a new trial.
