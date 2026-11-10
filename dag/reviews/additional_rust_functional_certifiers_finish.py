import json,pathlib,subprocess
H=pathlib.Path(__file__).parent;P='additional_rust_functional_certifiers'
n=json.loads((H/(P+'_notes.json')).read_text())
for p in ['code/rust/core_certifiers/src/phi1_certifier.rs','code/rust/core_functional/src/phi1.rs','code/rust/core_functional/src/binary_degree.rs']:
 n[p]=n[p].replace('probe pending','bounded probe reproduced; see final validation').replace('no fresh execution yet','full suite not executed; bounded direct-source controls recorded separately').replace('No fresh tests in this checkpoint.','No full suite executed; bounded direct-source controls recorded separately.').replace('No fresh execution yet.','No full suite executed; bounded direct-source controls recorded separately.')
(H/(P+'_notes.json')).write_text(json.dumps(n,indent=2)+'\n')
subprocess.run([str(H.parents[1]/'.venv/Scripts/python.exe'),'-B','-X','utf8',str(H/(P+'_checkpoint.py'))],check=True)
(H/(P+'.md')).write_text('''# Rust functional and certifier audit

Completed **64/64 files**, 31,002 lines and 1,098,251 bytes, pinned to `8050c66900899771766f33e8f5fdd200b7dd9120`. Every frozen crate, registered shared test and fixture has a full-source assessment, exact SHA-256 and reviewed line range in `additional_rust_functional_certifiers.json`. This completes this slice, not the original repository-wide audit. The report contains 11 claims and 19 findings; no source repairs were made.

The strongest implemented results are conditional finite checks: exact Phi1 primal-dual equality establishes an attained weighted rational quotient minimum; Gamma2 admits the supplied chain law and preserves the complete complex; higher quotient objectives and operator transports verify their supplied algebraic witnesses. None of these selects an external physical carrier or derives quantum mechanics. The factory recomputes typed records and preserves AuthorityEffect None. The Meron involution/Boolean-character cancellation argument is conditional on a fully supplied finite model, equal paired weights and the declared sign rule.

The main actionable findings are:

- **RFC-F011 (high):** the global Meron transport checker accepts temporal propagation that changes an off-support site's occupation. A two-row, three-site native counterexample passes global continuity and enables the independent-loop label. This breaks the claimed local-Hamiltonian transport admission, while the conditional orientation-character identity remains intact.
- **RFC-F001–F009, F012–F013:** malformed native rational values, negative/NaN diagnostics, wide splitting shapes and bounded-integer/resource overflows cause panics, nonfinite results or inconsistent execution. Phi2/3/4 certificates also fail their own serialized round trips. Exact witness checks, display diagnostics and authority effects are distinguished in each finding.
- **RFC-F014, F017–F018:** lexical Lean declaration matching accepts a comment-only file; registry content reverses the Meron cancellation sector and points to a Phi1-only harness; obsolete repository paths prevent current custody replay, while one absent-Lean-directory guard silently skips all source pins.
- **RFC-F019:** both independent factory fixture records fail current typed hash replay. Python reconstruction agrees with unchanged Rust owner source; the computed arithmetic values12 and1 agree, but both stored records correctly return RecordMismatch. Preserve the old vectors and repair encoding provenance before claiming conformance.

Validation used five small direct-source native programs with cached, hash-pinned dependencies. Four ran under both overflow modes; the fifth preserved its initial failed assertion, then recorded both fixture refusals. Independent exact arithmetic checked all six spectral and seven trace-distance examples. The complete Cargo test suites, Lean compilation, external fixtures and physical selection claims were not validated. No providers, downloads, private benchmark/seed/key, or pilot corpus were accessed.

`additional_rust_functional_certifiers_final_validation.json` records the 64-path bijection, all source hashes, complete emitted line coverage separately from manual semantic assessments, 64 evidence references, unique identifiers and Python/native fixture-hash agreement. The numbered validation receipts preserve commands, outputs, source/library hashes and limits. All fixes remain a repair backlog.
''',encoding='utf-8')
subprocess.run([str(H.parents[1]/'.venv/Scripts/python.exe'),'-B','-X','utf8',str(H/(P+'_validate.py'))],check=True)
