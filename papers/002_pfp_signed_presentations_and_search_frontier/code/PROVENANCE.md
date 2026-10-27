# Genesis finite sign-checker source and paper-local repair

**Captured:** 2026-09-23 from the author's local, non-Git Genesis waystation at `C:\Users\a343o\source\repos\genesis\0_genesis_alpha_papers_program`. All four files were initially copied byte-for-byte. On 2026-09-24, Paper 002 repaired the exact-matrix input snapshot and added one regression test; the graph checker and its tests retain their original bytes. Both original and current hashes are recorded so the paper-local version is not mistaken for the original Genesis source.

| Paper 002 file | Genesis source relative to `0_genesis_alpha_papers_program/` | Original SHA-256 | Current SHA-256 |
| --- | --- | --- | --- |
| [`code/genesis_alpha/sign_graph.py`](genesis_alpha/sign_graph.py) | `code/genesis_alpha/sign_graph.py` | `9488ED63C65089AF3086DAFA3E01A9AF948FB5D3C88505103E376F0590F0B3E1` | `9488ED63C65089AF3086DAFA3E01A9AF948FB5D3C88505103E376F0590F0B3E1` |
| [`code/genesis_alpha/frontier_search.py`](genesis_alpha/frontier_search.py) | `code/genesis_alpha/frontier_search.py` | `C42C6E40455A6F8485370A4953A9252D9AA6F91EBCFCF2D2484C8DC2AB15881B` | `6ED99C4E086AB0E3C7F4876E0E3BC09EBE410914FD5F74281DA6FCDAAB2FA7F8` |
| [`tests/test_sign_graph.py`](tests/test_sign_graph.py) | `tests/test_sign_graph.py` | `6BC61D3900CB217B8990ED63D55BF2E3649389DDA88801B1D335703B5851DF8B` | `6BC61D3900CB217B8990ED63D55BF2E3649389DDA88801B1D335703B5851DF8B` |
| [`tests/test_frontier_search.py`](tests/test_frontier_search.py) | `tests/test_frontier_search.py` | `456F4A43415F048ECADF8C172F92FE3013CB2A85BA0279AE891AE1AB54E382F9` | `ACCD534AFF3D0F5AF2C54BFC373194A6AF0A4FEB9E25780230E4CA557830E308` |

The original `exact_matrix_digest` traversed its input twice, and `search_exact_matrix` traversed it again. A one-shot iterator of a positive triangle could consequently be hashed and checked as an empty matrix. The paper-local repair first snapshots the matrix rows, then validates, hashes, and checks that same snapshot. The new regression checks both direct hashing and the search entry point.

From `atlas/coda_atlas/pfp/002_pfp_signed_presentations_and_search_frontier/`, run:

```powershell
py -3 -B -m unittest discover -s tests -p 'test_*.py' -v
```

The original copied suite passed **18/18** tests on 2026-09-23; the repaired paper-local suite passed **19/19** tests on 2026-09-24. It checks finite host-supplied signed graphs, exact real symmetric matrix gauges, presentation-keyed retrieval, bounded deterministic parallel candidate enumeration, receipt replay, and an honest `UNKNOWN` frontier. It is not an MCTS implementation, a physical Hamiltonian-to-path adapter, a general fermion-sign classifier, or a multicore performance result.


## 2026-09-27 documentation revision

The PFP manuscript now uses repository baseline
52cb5457f6c485ba548cfd292f6012a941ed22cf. The source and test bytes listed
above were preserved. The command path was corrected after atlas relocation.
The historical 18/18 and 19/19 counts are not new execution claims; the authoring
pass did not run tests. Full reproduction commands are in the current manuscript.


## 2026-09-28 publication review reconciliation

On 2026-09-28, the recorded current SHA-256 for `tests/test_frontier_search.py` was reconciled with the actual test bytes shipped in the package (`ACCD534AFF3D0F5AF2C54BFC373194A6AF0A4FEB9E25780230E4CA557830E308`). The historical Genesis alpha capture hash (`456F4A43415F048ECADF8C172F92FE3013CB2A85BA0279AE891AE1AB54E382F9`) and intermediate 2026-09-24 repair receipts are preserved in the historical log.

## 2026-09-28 reconciliation for version 1.1.0

The "Current SHA-256" column above is out of date for three files. Their later
changes are packaging changes, recorded here without altering the original
capture hashes:

- `code/genesis_alpha/frontier_search.py`: imports reordered and wrapped for
  the lint configuration (repository commit c7970e2b9). The checking code is
  unchanged.
- `code/tests/test_sign_graph.py` and `code/tests/test_frontier_search.py`:
  module lookup extended to find `code/genesis_alpha` from `code/tests`
  (relocation commit 64a2019de), then imports reordered for the lint
  configuration (repository commit c7970e2b9). The test functions are
  unchanged.
- The two test files now live in `code/tests/`; the table above names their
  earlier paper-local location `tests/`.

| Paper 002 file | SHA-256 on 2026-09-28 |
| --- | --- |
| [`code/genesis_alpha/sign_graph.py`](genesis_alpha/sign_graph.py) | `9488ED63C65089AF3086DAFA3E01A9AF948FB5D3C88505103E376F0590F0B3E1` |
| [`code/genesis_alpha/frontier_search.py`](genesis_alpha/frontier_search.py) | `D3529C2150F6B5D43BE46A34C46BCDE07EE2C082DC9F18AD522114977C417BC9` |
| [`code/tests/test_sign_graph.py`](tests/test_sign_graph.py) | `CDFC820E4A5D4C86650873FAEFC81DB6FBC49B119820B05C81E942A4D4007E1F` |
| [`code/tests/test_frontier_search.py`](tests/test_frontier_search.py) | `C6D174036A0D531EE8D98C917637A84AC2674DFB7B11CD3D5A5E50356B6680F3` |

The unittest command above predates the move to `code/tests/`. From the
package root, the current commands run one test file each:

```powershell
py -3.12 -m pytest code/tests/test_sign_graph.py -q
py -3.12 -m pytest code/tests/test_frontier_search.py -q
```

The historical 18/18 and 19/19 counts remain bound to their dates. Current
execution evidence is the dated review receipt for version 1.1.0.

## 2026-10-02 initial v0.1 preprint review

The four Genesis graph/frontier source and test files above keep their
2026-09-28 bytes. The current package review inspects repository baseline
e11c07ce90318309f058c8097ffd1c440a8ffb84 and records revised package inputs in
[the new execution receipt](../docs/preprint_review_validation_2026_10_02.json).
The separate native transport now validates witness payload shapes before
constructing objects and rejects malformed output with a typed error; this
does not replace a native answer with the Python classifier. Its regression
fixtures are described in [the review](../docs/preprint_review_2026_10_02.md).
Earlier hashes, version numbers, commands, and counts retain their historical
scope.
