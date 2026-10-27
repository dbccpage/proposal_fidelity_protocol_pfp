# Genesis source replay fixture

AuthorityEffect: None.

`source_replay_receipt.json` is retained without changing its bytes from commit
`0100b5a1fabe06b1b8cb51aa20656c51bd9cbfec`, at the former path
`atlas/coda_atlas/F004_papers/001_finite_obstruction_calculus/000_witnessed_difference_programme/evidence/source_replay_receipt.json`.
Its Git blob is `0e10dc5fbb65df1c293355e7a25c1c440c744906`.

The native replay test consumes this historical fixture; retaining it does not
claim a new execution of the original Python implementation or extend its scope.

The two JSON files under `causal_certificates/` are also unchanged copies from
that commit, formerly under the same retired paper's `code/causal_certificates/`.
They retain the original schedule counts and descriptor-digest assertions.

The two `.py.txt` files under `coda_cs_q/reference/` preserve reviewed v2 source
bytes from that commit, formerly under the retired paper's
`docs/source_archive/coda_component_packages/cs_q/code/`. The unchanged test
hashes bind the exact bytes, including trailing newlines. These files are parsed
only for structural field-name parity and are never executed. Unavailable v1
source bytes remain unavailable; their historical hashes are not replaced.

The reference directory's Git attributes disable text conversion and permit the
historical trailing blank line. Existing SHA256 assertions still bind every byte.
