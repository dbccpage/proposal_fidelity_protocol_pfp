# Additional EIS/PCIV remaining-source review

Reviewed all 340 declared original paths (226 EIS, 114 PCIV) at pinned source `8050c66900899771766f33e8f5fdd200b7dd9120`. This is a complete disposition inventory with explicitly limited read depths, not a claim of 340 full body reads.

| Read depth | Files |
|---|---:|
| full_text_source_review | 181 |
| complete_parsed_values_or_reviewed_base_plus_all_differences_not_raw_body | 152 |
| automated_artifact_structure_with_selected_semantic_claims | 7 |

All 137 Python bodies and all 35 ordinary Markdown/text bodies are fully read. All 11 notebooks have every code cell and retained output inspected as parsed content; raw JSON coverage is separately labeled. Initial partial reviews and the original 17 probes remain preserved in the initial-report/read ledgers. One later pure architecture-helper probe brings the total to 18. Several expected observations are counterexamples. No existing test suite, native host, provider, full notebook or live stress run was executed. Source files remain unchanged.

## Findings

### EPR01: Precedent eligibility accepts missing admission/scope metadata and SUPPORTED placement, contrary to its hard-domain gate claim.

Evidence: `pciv/infrastructure/matching.py` lines 39–57 (SHA-256 `ee9ae61fba24dd3a8fd379c88cb41907bc9d176f9fe7267835213d36fd5a93d3`); `pciv/documentation/levels/level_06_precedent_retrieval_and_evaporation.md` lines 69–71 (SHA-256 `6ff9281bfdec790f59d43dd895bb3e0447aee71a019bc5f14a15fd41424ca63c`).

Method: full source + fresh synthetic probes. Limit: Local Python matcher only; no end-to-end admission bypass claimed.

Next action: Require explicit admitted placement and covering scope before retrieval; separately validate count/usage and preserve exact rank ordering.

### EPR02: Adversarial rank turn ignores a false verification result; sealed session unconditionally reports one verified rank certificate even when no ranking ran.

Evidence: `pciv/infrastructure/probes/adversarial_session_probe.py` lines 548–610 (SHA-256 `f379b9879001cc26fde48a97d14f950ea54d6c705c9c1920bd4e316436f6b4f1`); `pciv/infrastructure/probes/adversarial_session_probe.py` lines 650–669 (SHA-256 `f379b9879001cc26fde48a97d14f950ea54d6c705c9c1920bd4e316436f6b4f1`).

Method: full source + fresh fake-port control-flow probes. Limit: Injected verifier false tests composition, not the real rank solver.

Next action: Bind acceptance and receipt counts to actual successful verifier outcomes.

### EPR03: Attack methods always return QUARANTINED even when attack_caught is false; a valid carrier is counted as an attack, and an unknown host status preserves local ACCEPTED.

Evidence: `pciv/infrastructure/probes/adversarial_session_probe.py` lines 124–138 (SHA-256 `f379b9879001cc26fde48a97d14f950ea54d6c705c9c1920bd4e316436f6b4f1`); `pciv/infrastructure/probes/adversarial_session_probe.py` lines 421–466 (SHA-256 `f379b9879001cc26fde48a97d14f950ea54d6c705c9c1920bd4e316436f6b4f1`).

Method: full source + fresh synthetic probes. Limit: Counts are diagnostic labels, not measured detection success.

Next action: Record observed detector outcome separately; require explicit accepted host status for acceptance and calculate consistency from actual checks.

### EPR04: Farm no-hit disposition is GROUNDED_WITNESS for empty and irrelevant text although the classifier never compares ground truth.

Evidence: `eis/infrastructure/mssn_classifier.py` lines 79–85 (SHA-256 `29fa984e24d8da052748076661f569a28d2431287fcf47352829df4ec2811e5b`); `eis/infrastructure/mssn_classifier.py` lines 239–263 (SHA-256 `29fa984e24d8da052748076661f569a28d2431287fcf47352829df4ec2811e5b`); `eis/infrastructure/mssn_ports.py` lines 1–399 (SHA-256 `46821fa89230e43c8e0102dbb358026a0c37fd5f95607bfaa8c96de5742226dd`).

Method: full source + fresh synthetic probes. Limit: Farm caller remains diagnostic-only without independent danger; this is a misleading result label, not an observed activation bypass.

Next action: Use no-detection/inconclusive disposition and a separate task checker for mathematical claims.

### EPR05: The C5 ground-truth explanation calls a 5-cycle odd and assigns (-1)^5. A 5-cycle permutation has even parity: [1,2,3,4,0] has four inversions and sign +1.

Evidence: `eis/infrastructure/mssn_domains.py` lines 194–214 (SHA-256 `c5657ddf5c3a51f454fd149be78ffdf3a021bbf91cbb7491d2a671839af6c116`); `eis/antibodies/definitions/probing_domains.yaml` lines 1–225 (SHA-256 `d5c480f2510989f334b35e8519cb3b76d2dfddbd1d9e784218aa19e978be4b64`).

Method: full Python data + all YAML differences + fresh finite parity calculation. Limit: Only the permutation-parity assertion is disproved; no general Hubbard or sign-problem theorem is asserted. Other literature claims were not checked offline.

Next action: Correct the finite premise after owner review; rederive domain fixtures from explicit model assumptions and independent checkers.

### EPR06: All 973 catalog general_obstruction entries use literal template descriptions and place the same trigger in both failing and repaired fixtures. The corpus includes successful-test prose mislabeled as obstruction candidates.

Evidence: `eis/antibodies/pharmacy_catalog.json` lines 1–18313 (SHA-256 `d980f72dd696dccd8c5f7349cff3f6f6a085facdb85296629b7d02cdb39a3025`).

Method: whole parsed template arithmetic + inspected representative records. Limit: All 973 template identities checked; individual catalog-only prose claims and regex semantics were not all manually adjudicated.

Next action: Retain raw provenance; rebuild dual controls from witnessed failure/repair pairs before admitting any rule. Consolidate mechanism templates rather than counting each string as a learned mechanism.

### EPR07: The q40 unterminated-string negative fixture is valid Python syntax; compile accepts it.

Evidence: `eis/antibodies/ab_q40_unterminated_string_syntax.json` lines 1–17 (SHA-256 `10508526286e03d9cdf9a83082cefabb73a81602b525c242cc53ac08728740d7`).

Method: complete parsed fixture + fresh compile-only check. Limit: Parsing only, not execution or functional correctness.

Next action: Replace with an actual malformed-string counterexample and a matched valid control after approval to edit fixtures.

### EPR08: Daily digest claims verified SHA-bound records with intact hashes without validating supplied record hashes or provenance.

Evidence: `pciv/use_cases/intelligence_metabolism/digest.py` lines 19–29 (SHA-256 `1e9efdb4c5095f3520b9bbd1b19a5cf3a5c18a666ef28647d4fa220c672a7874`); `pciv/use_cases/intelligence_metabolism/digest.py` lines 59–73 (SHA-256 `1e9efdb4c5095f3520b9bbd1b19a5cf3a5c18a666ef28647d4fa220c672a7874`).

Method: full source + fresh invented-record probe. Limit: Miner may supply real file digests, but the public digest generator accepts arbitrary DTO-like objects.

Next action: Require a validated provenance receipt or qualify summaries as supplied-record statistics.

### EPR09: Genealogy reads can truncate malformed/torn tails, and cache invalidation by file size misses same-length external changes. Duplicate-sequence replay can skip digest checks when child payload matches.

Evidence: `pciv/infrastructure/genealogy_adapter.py` lines 104–205 (SHA-256 `3716adb98804baa21cd774b1631e0f52d4ee741eb8635f782a47823537c2ba7a`); `pciv/infrastructure/genealogy_adapter.py` lines 266–282 (SHA-256 `3716adb98804baa21cd774b1631e0f52d4ee741eb8635f782a47823537c2ba7a`).

Method: full source control-flow review. Limit: No retained ledger was opened through this adapter and no mutation probe ran.

Next action: Separate repair from read, preserve corrupted bytes, and bind cache/replay checks to content/chain identity.

### EPR10: Immune screening attributes quarantine to the first matching epitope rule and stimulates every active rule with the same epitope, even if only one rule matched.

Evidence: `eis/use_cases/mssn_immune.py` lines 121–144 (SHA-256 `822d63b905b0be2cb06bd4ede0fee4a9c4bad9c9ac8a243220ec7ab470253098`).

Method: full source control-flow review. Limit: Conditional on duplicate target_epitope entries; no global uniqueness guarantee is established at this function.

Next action: Carry detector/rule identity through matches, or enforce and test uniqueness at ingress.

### EPR11: The population notebook allocates cap 10 as [6,2,2] while Level 07 requires [6,3,1]; reverse tuple sorting gives the tie to Baseline instead of Unmeasured.

Evidence: `pciv/documentation/curriculum/420_population_reserves_persistence/notebooks/lesson_420_07_ecological_reserves_and_population.ipynb` lines 1–49 (SHA-256 `16c98c6d8e177a82d38f703aa2967add570d1de1f6c0f49c10ceffe232107237`); `pciv/documentation/levels/level_07_ecological_reserves_and_population.md` lines 77–87 (SHA-256 `bcb6be9877698ec6a2ad4bc87d462d69ba5fa8ee61dfa71bd0dff58bf1009b1d`).

Method: all notebook cells/outputs inspected + fresh extracted-function probe. Limit: No notebook execution history exists; this demonstrates the toy helper, not the production allocator.

Next action: Use exact integer remainders and declared tie order, then compare notebook against canonical owner.

### EPR12: Other notebooks advertise broader verification than their predicates: one damped sum is not PageRank, one payload hash is not crash replay, and scalar attenuation does not traverse a genealogy.

Evidence: `pciv/documentation/curriculum/410_selection_ranking_retrieval/notebooks/lesson_410_05_inverse_lineage_pagerank.ipynb` lines 1–42 (SHA-256 `0a225e298005d72c7be8c33743e0f3e347a7327f4f090ac606cdc5189bc2e0e0`); `pciv/documentation/curriculum/420_population_reserves_persistence/notebooks/lesson_420_09_durable_event_log_and_persistence.ipynb` lines 1–45 (SHA-256 `855f2d4c9a0e36e26ed7d7468bd0ecf06fb1a66ea1c448689100cb43cf131833`); `pciv/documentation/curriculum/400_prompt_civ_foundations/notebooks/lesson_400_03_lamarckian_retro_inheritance.ipynb` lines 1–41 (SHA-256 `98ec51a93137c8c7e3a9e91dbec82d493bd85ab64e16b8eaa64034bc57619daa`).

Method: all retained notebook cells/outputs inspected. Limit: Eleven notebooks retain no executed cell counts or outputs. Illustrations can be useful without certifying production behavior.

Next action: Label illustrations accurately and use canonical owner tests for execution claims.

### EPR13: In the boundary-repair validation artifact, 21 of 33 output_utf8/output_sha256 pairs disagree under exact UTF-8 hashing of the retained string.

Evidence: `eis/receipts/epic_boundary_repair_20261012/validation.json` lines 1–759 (SHA-256 `e576997ba7eef2625528f79b09064d263eb313ba56c234278c4d1771447e1b57`).

Method: whole-artifact automated hash recomputation. Limit: This identifies byte-binding inconsistency, not fabrication; relocation, normalization or postprocessing may explain it. Historical commands were not rerun.

Next action: Preserve the receipt, locate original raw logs/normalization provenance, and do not treat the embedded text as hash-verified output until reconciled.

### EPR14: Catalog has 29 admitted labels but only two embedded admission records; the repaired Pilot 035 pair explicitly supersedes older finite-to-unrestricted claim patterns.

Evidence: `eis/antibodies/pharmacy_catalog.json` lines 1–18313 (SHA-256 `d980f72dd696dccd8c5f7349cff3f6f6a085facdb85296629b7d02cdb39a3025`); `eis/antibodies/definitions/pilot035_candidates.json` lines 1–112 (SHA-256 `a24dd3cde4b486e659b620ec0b2c04d3ea7b7fc0415540318ff6880410683749`); `eis/antibodies/admissions/pilot035_owner_approval_20261015.json` lines 1–21 (SHA-256 `11e6451fe55135286cecc36f2a389f132a6c77c7aff6c54b5e83963286be469f`).

Method: whole parsed status inventory + complete parsed candidate/approval records. Limit: A missing embedded record does not prove no external authorization exists; legacy status alone is insufficient evidence of authenticated activation.

Next action: Consolidate through the explicit admission owner and exact scope; keep historical domain answers out of new workflow inputs.

### EPR15: Mined antiskill set contains 22 entries but 18 unique candidate IDs. Root/spec YAML copies also diverge in old import paths, native binding paths and one harmful-control test name.

Evidence: `eis/antiskills/ooutwire/evidence_mined_candidates.json` lines 1–640 (SHA-256 `8e2bd310332410495fd1e3a7d1a9028252e7afdbabc2a2df1f57b74bcfd78051`); `eis/antibodies/specs/anti_witness_certificate_desynchronization.yaml` lines 1–67 (SHA-256 `5baaaff2ff5eba0aaf99a56a86662b9320de4cd00e7ed3acc5519345d8b99cf6`); `eis/antibodies/specs/anti_implicit_credential_discovery.yaml` lines 1–67 (SHA-256 `4a71cd238c924381d6bab5d305b1b6b003e009d7b76afdee93f0781aae8ee175`).

Method: all candidate invariants + whole schema duplicate inventory + complete YAML field differences. Limit: Duplication is not a reason to delete historical evidence; no semantic theorem validated by byte equality.

Next action: Choose one authoritative definition with migration aliases; remove duplicate candidate counting only after provenance-preserving review.

### EPR16: Some anti-theorem fixtures still encode assumed answers: scalar-proxy repair returns hardcoded truth/negative-value fields, while target-fitting repair computes a sum in a field named 2S-minus-2P.

Evidence: `eis/antibodies/anti_scalar_proxy_theorem_substitution.yaml` lines 1–73 (SHA-256 `0a37d99f7d34a55e52e850a4e826bcc872751ef6256976d72ae7d687cd71e358`); `eis/antibodies/anti_target_fitting_constant_compensation.yaml` lines 1–83 (SHA-256 `0912c75376183c071608c56b118fa98a4537760256c24f13eef0e4920f1082ee`).

Method: complete parsed fixture bodies inspected. Limit: These are lexical examples, not independent PSD or atomic-physics verification. The arithmetic label mismatch is local; physical constants were not adjudicated.

Next action: Use explicit matrix/vector or independently pinned subchannel inputs and recompute the actual obligation; keep lexical examples diagnostic.

### EPR17: The EIS cross-context architecture helper recognizes only roots starting with engine; pciv, pfp, operads and operations imports are invisible to that predicate.

Evidence: `eis/tests/architecture/test_clean_architecture_ast_boundaries.py` lines 92–109 (SHA-256 `dfd252d34a021dc65f861b3341338399076eff01f9b6f88ff616ff9e9c95987f`); `eis/tests/architecture/test_clean_architecture_ast_boundaries.py` lines 123–144 (SHA-256 `dfd252d34a021dc65f861b3341338399076eff01f9b6f88ff616ff9e9c95987f`).

Method: full test body + one fresh pure extracted-helper probe. Limit: This demonstrates an underinclusive test predicate, not an actual forbidden production import or a failing full architecture suite.

Next action: Declare the canonical context roots and add representative renamed-root countercontrols before using this test as a cross-context coverage claim.

### EPR18: Two test files exercise a locally defined helper rather than the production operation: challenger decay and promoted-operand filtering.

Evidence: `eis/tests/unit/test_challenger_adversarial_stress.py` lines 716–740 (SHA-256 `e7f544cf7154f4187ecf5123494cd3b120096719f053eae89db1ed7537431f70`); `pciv/tests/intelligence_metabolism/test_operand_registry.py` lines 12–58 (SHA-256 `311b448e60152918506ed097155e03dbfd927d106a2801665d42051ac1c4f1a5`).

Method: full test-body source review. Limit: Local formula/filter examples can be useful; their passing would not constrain a separately implemented production path. No test was executed.

Next action: Keep pedagogical examples labeled as such and bind production regression claims to the owning production function and adversarial controls.

### EPR19: The qualification lifecycle test supplies closure.verified=True; the asserted DISCHARGED result does not independently verify the named formal qualification.

Evidence: `eis/tests/unit/test_qualification_ab_limit_honesty.py` lines 117–219 (SHA-256 `7edaa81b044e1e4b24fb26ee21edf48881f87d796082834068960a774c337e8d`).

Method: full fixture and assertion review. Limit: This is a premise-bound lifecycle transition test. The native kernel and actual qualification owner were not run here.

Next action: Separate evidence validation from lifecycle transitions and require a bound executed checker result before claiming the open obligation has been discharged.

### EPR20: Run U manually rewrites pharmacy_status to admitted before its antibody-blocking bout; the legacy file-store test similarly edits status to ACTIVE.

Evidence: `pciv/tests/integration/test_run_u_cemetery_blocking_loop.py` lines 236–295 (SHA-256 `10412238fbca027ad685a8cd297a3b6945c0411352530c6bba3379504a2244dd`); `pciv/tests/unit/test_cemetery_and_genealogy.py` lines 71–88 (SHA-256 `4ade9caff3817147980750c495690e9bf0f1eb43eafefeb41a873749c72311ad`).

Method: full test fixture/control-flow review. Limit: Finite blocking after supplied admission is not autonomous activation from harvested failures, and this is not a newly observed production bypass.

Next action: Describe the admission premise explicitly and keep authentication/admission-owner tests separate from downstream blocking tests.

### EPR21: Level 00 excludes protected_spans from the genome identity tuple, while the current ecology test requires span changes to change prompt_id.

Evidence: `pciv/documentation/levels/level_00_substrate_and_packaging.md` lines 61–73 (SHA-256 `f08786ca0e311368dbced2fd74c289662858fe0c80fc98428384ddf68355f020`); `pciv/tests/unit/test_prompt_ecology.py` lines 121–134 (SHA-256 `89a930d54c2c9141d2a9116c3d1ddda23f5c5ec454ca59414da4e1916414736e`).

Method: full prose and full test-body comparison. Limit: Documentation/test contract mismatch; no fresh canonical identity implementation run. SHA collision resistance is also an assumption, not an injectivity theorem.

Next action: Reconcile the documented identity envelope with its canonical owner, and distinguish derived metadata from identity-bound protected spans.

### EPR22: Level 07 declares reserve fractions 3/5, 1/4, 3/20, yielding 12/5/3 at cap 20, while the unit test expects 12/6/2.

Evidence: `pciv/documentation/levels/level_07_ecological_reserves_and_population.md` lines 71–89 (SHA-256 `bcb6be9877698ec6a2ad4bc87d462d69ba5fa8ee61dfa71bd0dff58bf1009b1d`); `pciv/tests/unit/test_backfill_and_coverage_gates.py` lines 643–656 (SHA-256 `e90330dbaa4699ea4c1c47bf517bb1ea044c2746290b53814c16bb59cc4abb66`); `pciv/tests/unit/test_prompt_ecology.py` lines 137–145 (SHA-256 `89a930d54c2c9141d2a9116c3d1ddda23f5c5ec454ca59414da4e1916414736e`).

Method: full prose/test comparison + direct exact arithmetic. Limit: Cap 10 happens to agree at 6/3/1. This is a policy inconsistency between artifacts, not a fresh allocator test or claim of optimal fractions.

Next action: Choose and version the actual quota policy; compare every curriculum and test vector at noncoincident caps before claiming parity.

### EPR23: Short lessons diverge from their fuller mathematical contracts: inverse rank says power iteration with duality-gap termination instead of Gaussian elimination, and retrieval decay omits floor(t/H).

Evidence: `pciv/documentation/curriculum/410_selection_ranking_retrieval/concepts/lesson_410_05_inverse_lineage_pagerank.md` lines 20–26 (SHA-256 `10849a7c0b6b335658b644b562d4e7704147461668e88b1bdccd1c9071ab8623`); `pciv/documentation/levels/level_05_inverse_lineage_pagerank.md` lines 73–86 (SHA-256 `43ca4e3c1a460c0eba818af6ef2e872bc14b7b3159c801717c0cc4f8c6ce2d9b`); `pciv/documentation/curriculum/410_selection_ranking_retrieval/concepts/lesson_410_06_precedent_retrieval_and_evaporation.md` lines 20–26 (SHA-256 `5e943c530ac3512524d27bff80b581ad486998c90af3f1378173fc3ddc4ade51`); `pciv/documentation/levels/level_06_precedent_retrieval_and_evaporation.md` lines 82–87 (SHA-256 `6ff9281bfdec790f59d43dd895bb3e0447aee71a019bc5f14a15fd41424ca63c`).

Method: complete prose-body comparison. Limit: These are different algorithms/decay policies, not harmless formatting differences. No convergence theorem or biological analogy was established here.

Next action: Align lesson equations and algorithm names with a pinned canonical implementation and preserve their finite assumptions.

### EPR24: The Level 02 half-open overlap formula does not cover zero-width insertion, although its later invariant and production fixture explicitly require refusing insertion inside a protected span.

Evidence: `pciv/documentation/levels/level_02_mutation_operators_and_forge.md` lines 66–72 (SHA-256 `d0a9dc0140619ff55af3b3b35f57371c04f40ffc0816fe958cea6b8d758e0bf5`); `pciv/documentation/levels/level_02_mutation_operators_and_forge.md` lines 109–113 (SHA-256 `d0a9dc0140619ff55af3b3b35f57371c04f40ffc0816fe958cea6b8d758e0bf5`); `pciv/tests/unit/test_backfill_and_coverage_gates.py` lines 622–630 (SHA-256 `e90330dbaa4699ea4c1c47bf517bb1ea044c2746290b53814c16bb59cc4abb66`).

Method: full prose/test comparison + empty-interval reasoning. Limit: For len=0 the edit interval is empty, so nonempty-intersection alone cannot enforce insertion protection. This is a specification gap, not a claim the production forge permits it.

Next action: Specify insertion-point containment separately from positive-width overlap and retain the zero-width regression control.

## Reusable mechanisms and evidence limits

Reusable mechanisms are bounded two-signal screening, explicit independent replay/admission, exact finite allocation/ranking, protected mutation, provenance-bound telemetry and candidate distillation. Task-domain prose and repeated wrappers are not new mechanisms. Previously audited domain/native owners remain authoritative; this review does not add new workflow families.

Fixture vector generators freeze the Python implementation as an oracle for a finite native overlap profile. They are useful regression/port tests but do not independently prove the Python predicates or all Unicode/platform behavior. Generators not run; no historical fixture regeneration.

The 50-generation stress entrypoint is an offline repeated-fixture experiment and live entrypoint is a refusal. Neither supplies live model learning or generalization evidence. Source inspection; scripts not executed.

The v2 truth-boundary specs implement predicates on declared typed fields. Transfer to a new task requires trusted claim/evidence scope and producer/verifier encodings plus the task checker; identity labels alone do not prove independent truth. Complete parsed records reviewed; historical receipt hashes are not fresh signatures or benchmark evaluations.

## Coverage and artifacts

The JSON report supplies one source-hash-bound assessment per path, exact reviewed line ranges, full/partial flags, parsed-value methods, assertion inventories and notebook limitations. The read/scan/view ledgers preserve how those assessments were obtained. Large catalog and validation artifacts receive automated structural dispositions; those dispositions do not prove their narrated claims.

The catalog has 1,069 records (973 general templates); 27 of 29 admitted labels lack an embedded admission record. All 60 reviewed root/candidate definitions were compared against it: 33 equal, 13 differ, 14 absent. The latter findings are consolidation leads, not deletion authorization.

All 11 notebooks are unexecuted retained JSON artifacts. No unsupported binary file is present in this assigned inventory. Public historical seed_candidates is included; the sealed benchmark and private material were never read.

No source fixes, deletions, new workflow families, new admissions or hidden benchmark inputs were introduced.
