# Reproduction

The current operator instruction selects Windows verification and excludes Linux
testing. Paid calls remain deferred. These commands perform offline verification;
they do not port the frozen Linux-only candidate runner to Windows. A future live
Windows campaign needs a separately reviewed containment adapter and protocol.

Use the retained source revision and source manifest, Python 3.12, and the existing
native `omega_symbol_game` executable for the budget and typed-operation tests.
The verification receipt identifies the actual executable bytes used locally;
it does not assert a fresh source-to-binary build. Live execution requires a
separate observed Linux container preflight.
That requirement describes the frozen runner, not work currently authorized.

The campaign is frozen independently of the latest repository checkout. Main
`e7420ae75737df9dbb0785cc102e8179fa6feb8c` changes twenty of its pinned files;
the original journal must not be rebound to those bytes. Reproduce the original
zero-call report from the retained archive with this offline command:

```powershell
py -3.12 omega_engine_woland/documentation/harness_evolution/replay_review_archive.py --output C:/temp/aide2-frozen-replay
```

Use a new destination. The helper authenticates the original archive digest,
rejects unsafe paths, checks the canonical package before and after replay, and
writes `replay_receipt.json` plus logs. Its child Python process excludes ambient
repository imports and credentials and refuses networking and child processes.
Existing installed dependencies are used explicitly; fresh installation and
Linux containment are separate, untested claims. The original archive remains
unchanged, including its earlier paper snapshots.

From the repository root, the following are focused offline tests. The direct
campaign replay/report commands require the original **frozen source tree**,
not current main:

```powershell
py -3.12 -m pytest omega_engine_woland/tests/research/test_harness_contracts.py omega_engine_woland/tests/providers/test_harness_anthropic_budget.py -q
py -3.12 -m pytest omega_engine_woland/tests/test_ddc_code_repair.py omega_engine_woland/tests/providers/test_completion_failure_bytes.py omega_engine_operads/tests/autopoiesis/test_learning_loop.py -q
py -3.12 -m omega_engine_woland.entrypoints.research.harness_cli replay --output omega_engine_woland/documentation/harness_evolution/campaign
py -3.12 -m omega_engine_woland.entrypoints.research.harness_cli report --output omega_engine_woland/documentation/harness_evolution/campaign
```

If Windows temporary-directory ACLs prevent pytest allocation, pass a new writable
`--basetemp` path. Do not change test semantics to suppress an allocation failure.
No API key is needed for these offline checks. No candidate code is executed
outside the rootless runner by the live campaign.

The report must remain NOT_RUN and all model effects NOT_MEASURED until actual
provider calls and evaluations have been retained. Historical traces in other
papers are not inputs to these empirical tables. The supplied PDF is identified
by exact file digest and page text digests in `source_manifest.json`; obtain the
same v1 bytes to re-extract page references.
The page-text digests specifically use `pypdf==6.10.0`, `page.extract_text()`,
and UTF-8 encoding without normalization. A newer extractor is not equivalent:
the offline follow-up observed differing page text under 6.19.0 despite identical
PDF bytes. Keep the original digests and use the pinned extractor for comparison.

Rebuild the selected author-review PDFs through the existing collection tool:

```powershell
py -3.12 omega_engine_atlas/coda_atlas/F004_papers/015_pfp/tools/build_publications.py --author-review --pdf
py -3.12 omega_engine_atlas/coda_atlas/F004_papers/015_pfp/tools/check_publications.py --author-review
```

This writes a separate dated review collection, without `--deposit`. Historical
release ZIPs, deposited metadata and package renderings keep their identities.
The standalone Paper 029 rendering includes this later reproduction clarification;
the initial all-paper archive remains the snapshot produced for PR #1330.
The review package has a source manifest and SHA-256 manifest. External deposit
is outside this work. Existing finite proof sources are unchanged; no new Lean
claim is introduced by the experimental extension.
