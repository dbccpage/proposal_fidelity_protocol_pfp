# The Symbol Game: A First Game with S(n), MSS-N, and Basic Packets

Jeremy H. Carroll. Version 0.1.0, 2026-10-02. Introductory preprint.

Read `paper.md` or `paper.pdf`. The body requires only marks, relations, S(n),
MSS-N, and packets. Appendix A previews advanced routes.

The self-contained teaching checker is distinct from the native host and does
not derive Genesis stages. It makes no network calls.

From this package directory with Python 3.12 or later, install the test and
notebook dependencies, then run the selected checks:

```sh
python -m pip install ".[dev]"
python code/basic_packets.py
python code/lesson_packets.py
python -m pytest code/tests/test_basic_packets.py -q
python -m pytest code/tests/test_lesson_packets.py -q
python verify_deposit.py
```

The two teaching scripts use only the standard library. On Windows, `py -3.12`
may replace `python`. The dependency extra supplies pytest, nbformat, nbclient,
and ipykernel; use your existing notebook interface to open the workbook.

`verify_deposit.py` verifies manifests by default; it runs tests only when
explicit `--test` arguments are supplied. The release-envelope check is an
optional maintainer check: put the original downloaded ZIP inside this package
directory before running `python tools/rebuild_release.py --check`. It checks
the supplied dated archive rather than reproducing the teaching mathematics.

Text is CC BY 4.0; code is PolyForm Noncommercial 1.0.0.
Zenodo Record: <https://zenodo.org/records/23108137> (DOI: `10.5281/zenodo.23108137`, v0.1.0 Preprint).
No external peer review or acceptance is claimed.

The current package-local execution record is
`docs/release_validation_2026_10_02_review_repairs.json`. It records the selected
checks after the 2026-10-02 review repairs. `docs/release_validation_2026_10_02.json`
and `docs/release_validation_2026_10_01.json` keep their original dates and hashes.

## Eight gradual examples and a standalone workbook

Open `jupyter_notebooks/000_from_marks_to_returned_packets.ipynb` from this
package root or its notebook directory. It demonstrates ground counts,
collapsed profiles, supplied separators, compact directed pairs, typed prompts
and answers, consistent renaming, returned-packet replay, bounded sessions,
and an illustrative up/down map. Each lesson includes changed-input checks.

The prompt text is retained as data. Its task and answer types select the
finite teaching contract; prompt text cannot override that checker. A returned
packet keeps the original problem, proposed value, reason, scope, and any
checked value. The notebook requires `nbformat` and `ipykernel`; regenerating
it with `python code/build_workbook.py` also requires `nbformat`.
