# Paper011 core audit

Completed only the frozen **51-file partition** at `8050c66900899771766f33e8f5fdd200b7dd9120`: **50 full source reads /16,957lines**, **1 separately parsed data fixture**, **0 pending in this slice**. The repository-wide audit remains incomplete. All51current SHA256values match the original inventory;816,406source bytes were preserved.

All source bodies were read in numbered ranges before full-read credit. Per-file hashes, complete read ranges and substantive assessments are in `additional_paper_011_core.json`; automated parsing remains in `automated_reviews` with `full_source_read:false`. Scope and final reconciliation are separate immutable-input records.

The runners often preserve useful boundaries: finite demonstrations versus empirical claims, accepted refusal/negative labels versus positive capability, same-input native certificate replay versus topology labels, and historical hash integrity versus provider authenticity. The remaining defects below limit current execution or the advertised custody contracts.

## Findings

### P011CORE-F01

Optional source-repository verification does not establish that captured working-tree bytes are the pinned Git blob: Git checks only path/mode/OID metadata, while source bytes compare only to manifest SHA256. Synthetic different-blob metadata with mutually matching source/copy/manifest is accepted as VERIFIED_BYTE_COPIES with source_inventory_checked=true.

Evidence: `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/source_custody.py` L324–348 SHA256 `817b021bb317c202fdcf512488b896753206d2607f5dc200242bf748056b34af`.

Limit: The Git inventory call is stubbed with explicit metadata for different bytes; no false real Git response or mathematical false acceptance claimed. A trusted external manifest can still establish the stated copy integrity.

### P011CORE-F02

Findings auditor reports13 aggregate families for14rows containing one duplicate; its check enforces only13distinct identifiers, not exact row census or prescribed family identities.

Evidence: `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/audit_findings.py` L17–29 SHA256 `d73cf916197522183518de14607f7e44cb918e2a39293d4b5da302795326677c`.

Limit: Synthetic inventory has a recomputed pin; does not bypass an independently fixed external inventory digest.

### P011CORE-F03

The G02 mutation-custody supplement pins helper SHA187ba1c0..., but the current inventoried replay helper is25191e91...; its baseline check therefore refuses the audited current source before mutation replay. This is current replay unavailability, not proof that the historical run failed.

Evidence: `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/genesis_g02_mutation_custody.py` L16–45 SHA256 `72da7d915ac147f7b175ba8d34562d7cccc67bf4dcffc320810489a35a394dbb`; `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/genesis_g02_replay.py` L1–400 SHA256 `25191e914baf0290dc1cd091b962c48871c6f8545a99cfa6f09dfe5104eb8bfb`.

Limit: Historical receipts preserved; no repinning or repair performed.

### P011CORE-F04

G03 source verification requires G07 port SHAd14a646a..., but its current original-inventory SHA is3c5e466f...; the audited runner cannot pass G03_SOURCE_PORT_CHANGED. Historical evidence remains separate and was not repinned.

Evidence: `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/genesis_g03_replay.py` L62–74 SHA256 `0588b3f8a1625cec4579493154ba15cc9580df6773ca21edbc5c3ed816111fb5`.

Limit: Current replay unavailability, not a verdict about past successful runs.

### P011CORE-F05

G03 controls() overwrites its Path variable with a registered-file string and calls path.relative_to in the expected stale-script exception branch, raising AttributeError instead of recording the refusal.

Evidence: `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/genesis_g03_replay.py` L338–350 SHA256 `0588b3f8a1625cec4579493154ba15cc9580df6773ca21edbc5c3ed816111fb5`.

Limit: Actual unchanged function AST with synthetic native responses/serialization. Historical failure and later recovery are separate; no native binary or sealed oracle executed.

### P011CORE-F06

G04 relocation accepts removal of an entire computational top-level block whenever that block also mentions sys.path. Its inverse-import AST check applies only to retained nodes and cannot establish the advertised bootstrap-only change. Synthetic value7 becomes0.

Evidence: `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/genesis_g04_replay.py` L104–142 SHA256 `9a7f7adc495370094dc800f075a648927e0534833aacf879944026e0c7e710bf`.

Limit: Counterexample to the transformer boundary, not evidence that the pinned historical source contains this mixed block.

### P011CORE-F07

G07 quiet mutation controls treat every nonzero subprocess exit as successful rejection, without checking the expected typed reason. An unrelated process failure or crash satisfies this criterion, and the completion receipt can still declare its finite gate true.

Evidence: `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/genesis_g07_quiet.py` L96–105 SHA256 `8fc1c3fd6c956230f542a57da8795620f09251934c7a86799bd8fb627fd3249c`; `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/genesis_g07_quiet.py` L126–134 SHA256 `8fc1c3fd6c956230f542a57da8795620f09251934c7a86799bd8fb627fd3249c`; `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/tests/test_paper011_genesis_g07.py` L125–127 SHA256 `e6bae614d2b37f3a80c553cbae6e0c7bbbc55d4887d3e0b951fd09020a3a7d6e`.

Limit: Does not claim any retained mutation actually crashed. Identifies missing discrimination in the certification condition.

### P011CORE-F08

build_catalog sorts discovered dispatch IDs then compares them to an unsorted DEMO_IDS tuple, whose demo_adversary_tribunal entry is appended last. Therefore even the exact declared27-IDdispatch is refused before challenge discovery.

Evidence: `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/demo_catalog.py` L11–39 SHA256 `ba2cb37050fea0f1443e4a361edeb772a3aada3df82b9f2cfee0e97295a2dba7`; `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/demo_catalog.py` L151–160 SHA256 `ba2cb37050fea0f1443e4a361edeb772a3aada3df82b9f2cfee0e97295a2dba7`.

Limit: Synthetic source-only27entryrunner reproduced ValueError. No original demos, hidden cases or provider execution; a reconstruction prerequisite defect, not mathematical false acceptance.

### P011CORE-F09

parse_rounds captures speaker with (\w+) but requires an eight-role list containing multiword names. No matching group can equal Gauge Breaker or the other spaced names, so every nonempty round refuses COMPLETE_ORIGINAL_ROLE_ORDER_REQUIRED. This blocks baseline dialogue replay and progression replay that calls the same parser.

Evidence: `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/aggregate_original_recovery_v1.py` L288–324 SHA256 `70095795b0906b78563cf880aa96ffa332b87cfca0874a42bd58b73caf0db6d8`.

Limit: Actual parser refused a synthetic exact eight-role trace. No historical retained trace was accessed; no statement about past runner versions.

### P011CORE-F10

Generic relocation deletes whole top-level If/For/Expr nodes containing any sys.path attribute and whole If nodes whose test mentions __name__. Such nodes can contain ordinary computation, contradicting the unconditional never-math-nodes description. Actual relocation changed synthetic value7 to0 while journaling only bootstrap removal.

Evidence: `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/recreate_demos.py` L269–361 SHA256 `3e39167657e10575c3c0120af948523604cc4e23951e6418c76e8ce4d6fd8653`.

Limit: Synthetic counterexample establishes overbroad transformation contract; no claim that every historical source contains this pattern.

### P011CORE-F11

The worker network boundary replaces Python socket constructors but subprocess.run forwards every undeclared non-Cargo/Rust command to the original runner. Arbitrary subprocess capabilities are therefore outside the network guard; the implementation is not a process-wide offline sandbox.

Evidence: `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/recreate_demos.py` L434–580 SHA256 `3e39167657e10575c3c0120af948523604cc4e23951e6418c76e8ce4d6fd8653`.

Limit: A stubbed original runner observed an undeclared helper command. No real helper, network request, provider or credential access occurred; this does not allege historical external calls.

### P011CORE-F12

coverage_matrix checks primary run-list length87 but no exact or unique ID census, and overwrites selections by ID. A self-consistent synthetic batch with87copies of one C001receipt is accepted and returns one row while declaring87entries.

Evidence: `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/recreate_demos.py` L1977–2015 SHA256 `3e39167657e10575c3c0120af948523604cc4e23951e6418c76e8ce4d6fd8653`.

Limit: No trusted external digest bypass; artifact integrity remains internally consistent. all_recreations_completed remains false, but coverage census is not established.

## Validation and mathematical limits

**163focused pytest cases:162passed,1failed.** The failure is the existing positive catalog-discovery regression and independently confirmsF08. No source repair was made. The three batches are31/31,17/17and114/115. Ten independent synthetic boundary controls cover content/Git binding, census duplication, AST semantics, stale-variable failure, exact subset probability, catalog ordering, dialogue parsing and undeclared process forwarding. All actual native calls in the selected tests were stubbed.

The C041JSONfixture remains a bounded data disposition. Its false universal target has counterexample39+39=78; its true target follows from k<=49and k²<=2401<2600. The50admissible natural kvalues were checked exactly. Candidate Lean syntax was inspected but no kernel was run and original case hash references were not independently reauthenticated.

All checks used the available workspace Python3.14.2, not the declared Python3.12reproduction profile. No providers, paid models, credentials, private benchmark payloads, sealed QM key/seed/answer, broad native builds or unreviewed binary execution were used. Historical runner source was read; referenced historical data was not opened or executed. Parent-owned support/native/history partitions retain separate evidence.

Control artifacts:

| Artifact | SHA256 |
|---|---|
| `dag/reviews/additional_paper_011_core_custody_probes.json` | `e126667e991eea6f4db6d7feba841cf07dc65469b35c780cd28026253d211842` |
| `dag/reviews/additional_paper_011_core_boundary_probes.json` | `ad9faf43d7157a62fe0d2baf23b40395dcb66539f5ae4bffbe6bb226382d991d` |
| `dag/reviews/additional_paper_011_core_catalog_probes.json` | `30544175f84e935f61f19134eaf1a3ba67da32178a7ab8794feae98cefd688d4` |
| `dag/reviews/additional_paper_011_core_dialogue_probes.json` | `57abfb897aaba85319081a66a858c500ddeb90377613bed2eecf9557b690dcf7` |
| `dag/reviews/additional_paper_011_core_runner_probes.json` | `68a549da4a2e3c431152595d7c396d2e4d7fb8bcbe663614ea49599dd30f2c7a` |
| `dag/reviews/additional_paper_011_core_final_test_control.json` | `0506b4f71c7aaa970b8b64b8fe9139609baa34a8e54f82b2911335e0454e60bd` |

## Per-file dispositions

| Path | Disposition | Lines | SHA256 |
|---|---|---:|---|
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/__init__.py` | full_source_read | 1 | `58450686460b453e764070943ae67d07f5a8b6e2a0860228bc33a208e2faf12e` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/aggregate_original_recovery_obligations.py` | full_source_read | 66 | `3b47efb03880cd3dbdece1bc8925c6b81ea6c209aba62dad847ee2cca8d15c92` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/aggregate_original_recovery_progression_v1.py` | full_source_read | 350 | `acf096d225e552c4564e57b3f717124bf8b6bbf60a4837aa900664e1a6d6d917` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/aggregate_original_recovery_v1.py` | full_source_read | 701 | `70095795b0906b78563cf880aa96ffa332b87cfca0874a42bd58b73caf0db6d8` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/aggregate_recreations.py` | full_source_read | 2482 | `fa093ac0a9f61460a76142277bb4e93ec1f38552771b57baceea573e3c4681c2` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/audit_findings.py` | full_source_read | 124 | `d73cf916197522183518de14607f7e44cb918e2a39293d4b5da302795326677c` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/demo_catalog.py` | full_source_read | 300 | `ba2cb37050fea0f1443e4a361edeb772a3aada3df82b9f2cfee0e97295a2dba7` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/deposit_paths.py` | full_source_read | 146 | `0bfa9675bda5ed53f2f1a0dc3bdbe07ab8382098437d8efdcb8c5386bc03fc6e` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/fixtures/c041_supplemental_candidates.json` | bounded_data_assessment | 43 | `1c6a0a661246477468dd110be74774fa3c3379a6e53692dd8306892256433642` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/genesis_g01_lexical_supplement.py` | full_source_read | 63 | `22c4625ad2dd434fdcafb618d6a8bd6ee5076fc28c0241352d246b25434bd2f0` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/genesis_g01_replay.py` | full_source_read | 500 | `a7d9aa8141e86ff6910dea280479ac17754ebbf88f36e8285666328c58b3500f` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/genesis_g02_mutation_custody.py` | full_source_read | 117 | `72da7d915ac147f7b175ba8d34562d7cccc67bf4dcffc320810489a35a394dbb` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/genesis_g02_replay.py` | full_source_read | 400 | `25191e914baf0290dc1cd091b962c48871c6f8545a99cfa6f09dfe5104eb8bfb` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/genesis_g03_adapter.py` | full_source_read | 62 | `dacfa216af02e482d333e10a688f696a3aab7e0cb18f76d3444c2640a3b6838b` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/genesis_g03_finalize.py` | full_source_read | 134 | `837ae84fc60594b8b1dfbe9ebfa929e7840ca7bd89ee6cbaddcf5ca48d48ddc0` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/genesis_g03_key_bridge.py` | full_source_read | 328 | `e652c3a0871c81238701d371d7b285a63f5f8521b68c8cafd31f9de1820666d6` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/genesis_g03_pack.py` | full_source_read | 166 | `b3216c5c304009f4edeff0f6baa96166f26c56e8e912aea3659be64da3f896bf` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/genesis_g03_replay.py` | full_source_read | 460 | `0588b3f8a1625cec4579493154ba15cc9580df6773ca21edbc5c3ed816111fb5` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/genesis_g03_validate.py` | full_source_read | 36 | `8c0ece20343f175835bed3246196c304bc78dea36d00db8b2d7ec89c7abd4ee3` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/genesis_g04_poison.py` | full_source_read | 166 | `1d6aa403bef2e4253f755985234b98f6ebdaf8962f5d16e70b1240ad49568cff` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/genesis_g04_replay.py` | full_source_read | 572 | `9a7f7adc495370094dc800f075a648927e0534833aacf879944026e0c7e710bf` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/genesis_g07_quiet.py` | full_source_read | 147 | `8fc1c3fd6c956230f542a57da8795620f09251934c7a86799bd8fb627fd3249c` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/genesis_g07_replay.py` | full_source_read | 559 | `3c5e466f5dd9ffc7e75dd0b4b6fe9b4ecb2b74da13463acd361da00721159a70` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/genesis_g12_replay.py` | full_source_read | 362 | `81ec954f9f930e3a9cc7d74af086ded921900e279e858a2ac40f5f2800cd2735` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/history_recovery.py` | full_source_read | 416 | `6742c03ca797ab7e029c133a2f9e68bc3e7d64b357d141e1fc9afa96b2086808` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/mechanism_recreations.py` | full_source_read | 656 | `54d20602eb03cf0fa0caf4811e7ef73d0aa4eb6158acca37335521b0a81e1b1f` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/recreate_demos.py` | full_source_read | 2305 | `3e39167657e10575c3c0120af948523604cc4e23951e6418c76e8ce4d6fd8653` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/replay_dossier_homology.py` | full_source_read | 242 | `0ae6e6d8c04b4e2f7c64c72235b5d39348b76ab7545509e46c692898b612ff5a` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/replay_dossier_integral.py` | full_source_read | 240 | `c0d5efcf9118573d96751ccdc60a987a3d0d00e31ce70e5a1d96dc8b417366de` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/replay_native_mub.py` | full_source_read | 261 | `f8e10cea520b52b346cfc0f5893630961ffe962a064b6320ec03b01d5c818077` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/runtime_environment.py` | full_source_read | 142 | `c6f1c6be114e3a4c24e4a589acdf7411dbb98dc9a5d06ec6b92234c93e083500` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/source_custody.py` | full_source_read | 390 | `817b021bb317c202fdcf512488b896753206d2607f5dc200242bf748056b34af` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/tests/test_paper011_aggregates.py` | full_source_read | 412 | `d5abb50a1a7a6857e630126fd3d491d7eff76a61938ce74ebf83dd0b8d33d992` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/tests/test_paper011_dossier_homology.py` | full_source_read | 96 | `1f4d7f8977181adf0dd48b3a0b02c540d78a932aa12b4de24fa51f7fe08c71d4` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/tests/test_paper011_dossier_integral.py` | full_source_read | 204 | `4165ada0a5231b122c03cc88e1015c1f2978c9af4ed465f872b7b549715450e2` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/tests/test_paper011_findings_audit.py` | full_source_read | 84 | `4a951b03bebee4ee1d244c2fdf8e5f7b1c82c704c43e181cc94e01f472187f31` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/tests/test_paper011_genesis_g01.py` | full_source_read | 155 | `fbe0809892c878c66f596ab26a29a399fd66f33f7713aac6f4f9244acba18356` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/tests/test_paper011_genesis_g01_lexical.py` | full_source_read | 21 | `662f3fc15f66399efcfc086a374a1f8315194568dc6fa167c4f898e91f422266` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/tests/test_paper011_genesis_g02.py` | full_source_read | 186 | `0b49e30e2d5cd66cc09ce897145036f5678f886792ef62a3f6ceb7549c919631` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/tests/test_paper011_genesis_g03.py` | full_source_read | 301 | `3d37b3bcf625f1c8f8e1c8dd27fbb631d5b7a51d4477363d5791d2faf836b844` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/tests/test_paper011_genesis_g04.py` | full_source_read | 193 | `fec6ae71a957c6f2b4708ef9821037556e6c518b92f5123157a941f2fc9fd289` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/tests/test_paper011_genesis_g07.py` | full_source_read | 158 | `e6bae614d2b37f3a80c553cbae6e0c7bbbc55d4887d3e0b951fd09020a3a7d6e` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/tests/test_paper011_genesis_g12.py` | full_source_read | 157 | `8367dbea7d9bf7a72f99d2c1cec3d7612363e4d7364e4c40ec299d618dc885d2` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/tests/test_paper011_history_recovery.py` | full_source_read | 156 | `623d571ff992adea47a5d46c4b25f08a53448d49f7c02047b7127821fa2e4924` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/tests/test_paper011_mechanisms.py` | full_source_read | 227 | `3d3d3b862710b5281f73a109d826627b2d1ec29614cd3389c0b960c6d43cc82b` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/tests/test_paper011_native_mub.py` | full_source_read | 122 | `3cb97099dc90bb11689871b7e626b85e22a95bdaa63cae56097fafe6e381fc80` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/tests/test_paper011_original_recovery.py` | full_source_read | 130 | `d7bc1d608773b032c155a5b4591a53430ee1a0cef4096c5e9c5f920730a6b6e9` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/tests/test_paper011_recreations.py` | full_source_read | 1012 | `91ee75a22f7d46dca42ed856e598483d5da3c72050ea5230787f407c453051c5` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/tests/test_paper011_release_custody.py` | full_source_read | 156 | `f76a8c1dde4b2fe2428f321d925e7d47aacab831043014889ceb28a3655be0b5` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/tests/test_paper011_runtime_environment.py` | full_source_read | 72 | `bb474b89ef718f4fba2ec0fb8fa8d2e97d4966ad9ed167a880ca77ef693976f6` |
| `papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/tests/test_paper011_source_custody.py` | full_source_read | 221 | `41333551f15697f3506e8ee5c772a22f815c249e1bb6c29a736575ff91d982da` |
